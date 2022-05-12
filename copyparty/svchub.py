# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import time
import shlex
import string
import signal
import socket
import threading
from datetime import datetime, timedelta
import calendar

from .__init__ import E, PY2, WINDOWS, ANYWIN, MACOS, VT100, unicode
from .util import mp, start_log_thrs, start_stackmon, min_ex, ansi_re
from .authsrv import AuthSrv
from .tcpsrv import TcpSrv
from .up2k import Up2k
from .th_srv import ThumbSrv, HAVE_PIL, HAVE_VIPS, HAVE_WEBP
from .mtag import HAVE_FFMPEG, HAVE_FFPROBE


class SvcHub(object):
    """
    Hosts all services which cannot be parallelized due to reliance on monolithic resources.
    Creates a Broker which does most of the heavy stuff; hosted services can use this to perform work:
        hub.broker.put(want_reply, destination, args_list).

    Either BrokerThr (plain threads) or BrokerMP (multiprocessing) is used depending on configuration.
    Nothing is returned synchronously; if you want any value returned from the call,
    put() can return a queue (if want_reply=True) which has a blocking get() with the response.
    """

    def __init__(self, args, argv, printed):
        self.args = args
        self.argv = argv
        self.logf = None
        self.stop_req = False
        self.reload_req = False
        self.stopping = False
        self.reloading = False
        self.stop_cond = threading.Condition()
        self.retcode = 0
        self.httpsrv_up = 0

        self.log_mutex = threading.Lock()
        self.next_day = 0

        self.log = self._log_disabled if args.q else self._log_enabled
        if args.lo:
            self._setup_logfile(printed)

        if args.stackmon:
            start_stackmon(args.stackmon, 0)

        if args.log_thrs:
            start_log_thrs(self.log, args.log_thrs, 0)

        if not args.use_fpool and args.j != 1:
            args.no_fpool = True
            m = "multithreading enabled with -j {}, so disabling fpool -- this can reduce upload performance on some filesystems"
            self.log("root", m.format(args.j))

        if not args.no_fpool and args.j != 1:
            m = "WARNING: --use-fpool combined with multithreading is untested and can probably cause undefined behavior"
            if ANYWIN:
                m = 'windows cannot do multithreading without --no-fpool, so enabling that -- note that upload performance will suffer if you have microsoft defender "real-time protection" enabled, so you probably want to use -j 1 instead'
                args.no_fpool = True

            self.log("root", m, c=3)

        bri = "zy"[args.theme % 2 :][:1]
        ch = "abcdefghijklmnopqrstuvwx"[int(args.theme / 2)]
        args.theme = "{0}{1} {0} {1}".format(ch, bri)

        if not args.hardlink and args.never_symlink:
            args.no_dedup = True

        # initiate all services to manage
        self.asrv = AuthSrv(self.args, self.log)
        if args.ls:
            self.asrv.dbg_ls()

        self.tcpsrv = TcpSrv(self)
        self.up2k = Up2k(self)

        decs = {k: 1 for k in self.args.th_dec.split(",")}
        if not HAVE_VIPS:
            decs.pop("vips", None)
        if not HAVE_PIL:
            decs.pop("pil", None)
        if not HAVE_FFMPEG or not HAVE_FFPROBE:
            decs.pop("ff", None)

        self.args.th_dec = list(decs.keys())
        self.thumbsrv = None
        if not args.no_thumb:
            m = "decoder preference: {}".format(", ".join(self.args.th_dec))
            self.log("thumb", m)

            if "pil" in self.args.th_dec and not HAVE_WEBP:
                msg = "disabling webp thumbnails because either libwebp is not available or your Pillow is too old"
                self.log("thumb", msg, c=3)

            if self.args.th_dec:
                self.thumbsrv = ThumbSrv(self)
            else:
                msg = "need either Pillow, pyvips, or FFmpeg to create thumbnails; for example:\n{0}{1} -m pip install --user Pillow\n{0}{1} -m pip install --user pyvips\n{0}apt install ffmpeg"
                msg = msg.format(" " * 37, os.path.basename(sys.executable))
                self.log("thumb", msg, c=3)

        if not args.no_acode and args.no_thumb:
            msg = "setting --no-acode because --no-thumb (sorry)"
            self.log("thumb", msg, c=6)
            args.no_acode = True

        if not args.no_acode and (not HAVE_FFMPEG or not HAVE_FFPROBE):
            msg = "setting --no-acode because either FFmpeg or FFprobe is not available"
            self.log("thumb", msg, c=6)
            args.no_acode = True

        args.th_poke = min(args.th_poke, args.th_maxage, args.ac_maxage)

        if args.ftp or args.ftps:
            from .ftpd import Ftpd

            self.ftpd = Ftpd(self)

        # decide which worker impl to use
        if self.check_mp_enable():
            from .broker_mp import BrokerMp as Broker
        else:
            from .broker_thr import BrokerThr as Broker

        self.broker = Broker(self)

    def thr_httpsrv_up(self):
        time.sleep(1 if self.args.ign_ebind_all else 5)
        expected = self.broker.num_workers * self.tcpsrv.nsrv
        failed = expected - self.httpsrv_up
        if not failed:
            return

        if self.args.ign_ebind_all:
            if not self.tcpsrv.srv:
                for _ in range(self.broker.num_workers):
                    self.broker.put(False, "cb_httpsrv_up")
            return

        if self.args.ign_ebind and self.tcpsrv.srv:
            return

        m = "{}/{} workers failed to start"
        m = m.format(failed, expected)
        self.log("root", m, 1)

        self.retcode = 1
        os.kill(os.getpid(), signal.SIGTERM)

    def cb_httpsrv_up(self):
        self.httpsrv_up += 1
        if self.httpsrv_up != self.broker.num_workers:
            return

        time.sleep(0.1)  # purely cosmetic dw
        self.log("root", "workers OK\n")
        self.up2k.init_vols()

        thr = threading.Thread(target=self.sd_notify, name="sd-notify")
        thr.daemon = True
        thr.start()

    def _logname(self):
        dt = datetime.utcnow()
        fn = self.args.lo
        for fs in "YmdHMS":
            fs = "%" + fs
            if fs in fn:
                fn = fn.replace(fs, dt.strftime(fs))

        return fn

    def _setup_logfile(self, printed):
        base_fn = fn = sel_fn = self._logname()
        if fn != self.args.lo:
            ctr = 0
            # yup this is a race; if started sufficiently concurrently, two
            # copyparties can grab the same logfile (considered and ignored)
            while os.path.exists(sel_fn):
                ctr += 1
                sel_fn = "{}.{}".format(fn, ctr)

        fn = sel_fn

        try:
            import lzma

            lh = lzma.open(fn, "wt", encoding="utf-8", errors="replace", preset=0)

        except:
            import codecs

            lh = codecs.open(fn, "w", encoding="utf-8", errors="replace")

        lh.base_fn = base_fn

        argv = [sys.executable] + self.argv
        if hasattr(shlex, "quote"):
            argv = [shlex.quote(x) for x in argv]
        else:
            argv = ['"{}"'.format(x) for x in argv]

        msg = "[+] opened logfile [{}]\n".format(fn)
        printed += msg
        lh.write("t0: {:.3f}\nargv: {}\n\n{}".format(E.t0, " ".join(argv), printed))
        self.logf = lh
        print(msg, end="")

    def run(self):
        self.tcpsrv.run()

        thr = threading.Thread(target=self.thr_httpsrv_up)
        thr.daemon = True
        thr.start()

        sigs = [signal.SIGINT, signal.SIGTERM]
        if not ANYWIN:
            sigs.append(signal.SIGUSR1)

        for sig in sigs:
            signal.signal(sig, self.signal_handler)

        # macos hangs after shutdown on sigterm with while-sleep,
        # windows cannot ^c stop_cond (and win10 does the macos thing but winxp is fine??)
        # linux is fine with both,
        # never lucky
        if ANYWIN:
            # msys-python probably fine but >msys-python
            thr = threading.Thread(target=self.stop_thr, name="svchub-sig")
            thr.daemon = True
            thr.start()

            try:
                while not self.stop_req:
                    time.sleep(1)
            except:
                pass

            self.shutdown()
            thr.join()
        else:
            self.stop_thr()

    def reload(self):
        if self.reloading:
            return "cannot reload; already in progress"

        self.reloading = True
        t = threading.Thread(target=self._reload)
        t.daemon = True
        t.start()
        return "reload initiated"

    def _reload(self):
        self.log("root", "reload scheduled")
        with self.up2k.mutex:
            self.asrv.reload()
            self.up2k.reload()
            self.broker.reload()

        self.reloading = False

    def stop_thr(self):
        while not self.stop_req:
            with self.stop_cond:
                self.stop_cond.wait(9001)

            if self.reload_req:
                self.reload_req = False
                self.reload()

        self.shutdown()

    def signal_handler(self, sig, frame):
        if self.stopping:
            return

        if sig == signal.SIGUSR1:
            self.reload_req = True
        else:
            self.stop_req = True

        with self.stop_cond:
            self.stop_cond.notify_all()

    def shutdown(self):
        if self.stopping:
            return

        # start_log_thrs(print, 0.1, 1)

        self.stopping = True
        self.stop_req = True
        with self.stop_cond:
            self.stop_cond.notify_all()

        ret = 1
        try:
            with self.log_mutex:
                print("OPYTHAT")

            self.tcpsrv.shutdown()
            self.broker.shutdown()
            self.up2k.shutdown()
            if self.thumbsrv:
                self.thumbsrv.shutdown()

                for n in range(200):  # 10s
                    time.sleep(0.05)
                    if self.thumbsrv.stopped():
                        break

                    if n == 3:
                        print("waiting for thumbsrv (10sec)...")

            print("nailed it", end="")
            ret = self.retcode
        finally:
            if self.args.wintitle:
                print("\033]0;\033\\", file=sys.stderr, end="")
                sys.stderr.flush()

            print("\033[0m")
            if self.logf:
                self.logf.close()

            sys.exit(ret)

    def _log_disabled(self, src, msg, c=0):
        if not self.logf:
            return

        with self.log_mutex:
            ts = datetime.utcnow().strftime("%Y-%m%d-%H%M%S.%f")[:-3]
            self.logf.write("@{} [{}] {}\n".format(ts, src, msg))

            now = time.time()
            if now >= self.next_day:
                self._set_next_day()

    def _set_next_day(self):
        if self.next_day and self.logf and self.logf.base_fn != self._logname():
            self.logf.close()
            self._setup_logfile("")

        dt = datetime.utcnow()

        # unix timestamp of next 00:00:00 (leap-seconds safe)
        day_now = dt.day
        while dt.day == day_now:
            dt += timedelta(hours=12)

        dt = dt.replace(hour=0, minute=0, second=0)
        self.next_day = calendar.timegm(dt.utctimetuple())

    def _log_enabled(self, src, msg, c=0):
        """handles logging from all components"""
        with self.log_mutex:
            now = time.time()
            if now >= self.next_day:
                dt = datetime.utcfromtimestamp(now)
                print("\033[36m{}\033[0m\n".format(dt.strftime("%Y-%m-%d")), end="")
                self._set_next_day()

            fmt = "\033[36m{} \033[33m{:21} \033[0m{}\n"
            if not VT100:
                fmt = "{} {:21} {}\n"
                if "\033" in msg:
                    msg = ansi_re.sub("", msg)
                if "\033" in src:
                    src = ansi_re.sub("", src)
            elif c:
                if isinstance(c, int):
                    msg = "\033[3{}m{}\033[0m".format(c, msg)
                elif "\033" not in c:
                    msg = "\033[{}m{}\033[0m".format(c, msg)
                else:
                    msg = "{}{}\033[0m".format(c, msg)

            ts = datetime.utcfromtimestamp(now).strftime("%H:%M:%S.%f")[:-3]
            msg = fmt.format(ts, src, msg)
            try:
                print(msg, end="")
            except UnicodeEncodeError:
                try:
                    print(msg.encode("utf-8", "replace").decode(), end="")
                except:
                    print(msg.encode("ascii", "replace").decode(), end="")

            if self.logf:
                self.logf.write(msg)

    def check_mp_support(self):
        vmin = sys.version_info[1]
        if WINDOWS:
            msg = "need python 3.3 or newer for multiprocessing;"
            if PY2 or vmin < 3:
                return msg
        elif MACOS:
            return "multiprocessing is wonky on mac osx;"
        else:
            msg = "need python 3.3+ for multiprocessing;"
            if PY2 or vmin < 3:
                return msg

        try:
            x = mp.Queue(1)
            x.put(["foo", "bar"])
            if x.get()[0] != "foo":
                raise Exception()
        except:
            return "multiprocessing is not supported on your platform;"

        return None

    def check_mp_enable(self):
        if self.args.j == 1:
            return False

        if mp.cpu_count() <= 1:
            self.log("svchub", "only one CPU detected; multiprocessing disabled")
            return False

        try:
            # support vscode debugger (bonus: same behavior as on windows)
            mp.set_start_method("spawn", True)
        except AttributeError:
            # py2.7 probably, anyways dontcare
            pass

        err = self.check_mp_support()
        if not err:
            return True
        else:
            self.log("svchub", err)
            self.log("svchub", "cannot efficiently use multiple CPU cores")
            return False

    def sd_notify(self):
        try:
            addr = os.getenv("NOTIFY_SOCKET")
            if not addr:
                return

            addr = unicode(addr)
            if addr.startswith("@"):
                addr = "\0" + addr[1:]

            m = "".join(x for x in addr if x in string.printable)
            self.log("sd_notify", m)

            sck = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sck.connect(addr)
            sck.sendall(b"READY=1")
        except:
            self.log("sd_notify", min_ex())

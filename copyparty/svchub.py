# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import sys
import time
import threading
from datetime import datetime, timedelta
import calendar

from .__init__ import PY2, WINDOWS, MACOS, VT100
from .util import mp
from .authsrv import AuthSrv
from .tcpsrv import TcpSrv
from .up2k import Up2k
from .th_srv import ThumbSrv, HAVE_PIL, HAVE_WEBP


class SvcHub(object):
    """
    Hosts all services which cannot be parallelized due to reliance on monolithic resources.
    Creates a Broker which does most of the heavy stuff; hosted services can use this to perform work:
        hub.broker.put(want_reply, destination, args_list).

    Either BrokerThr (plain threads) or BrokerMP (multiprocessing) is used depending on configuration.
    Nothing is returned synchronously; if you want any value returned from the call,
    put() can return a queue (if want_reply=True) which has a blocking get() with the response.
    """

    def __init__(self, args):
        self.args = args

        self.ansi_re = re.compile("\033\\[[^m]*m")
        self.log_mutex = threading.Lock()
        self.next_day = 0

        self.log = self._log_disabled if args.q else self._log_enabled

        # jank goes here
        auth = AuthSrv(self.args, self.log, False)

        # initiate all services to manage
        self.tcpsrv = TcpSrv(self)
        self.up2k = Up2k(self, auth.vfs.all_vols)

        self.thumbsrv = None
        if not args.no_thumb:
            if HAVE_PIL:
                if not HAVE_WEBP:
                    args.th_no_webp = True
                    msg = "setting --th-no-webp because either libwebp is not available or your Pillow is too old"
                    self.log("thumb", msg, c=3)

                self.thumbsrv = ThumbSrv(self, auth.vfs.all_vols)
            else:
                msg = "need Pillow to create thumbnails; for example:\n{}{} -m pip install --user Pillow\n"
                self.log(
                    "thumb", msg.format(" " * 37, os.path.basename(sys.executable)), c=3
                )

        # decide which worker impl to use
        if self.check_mp_enable():
            from .broker_mp import BrokerMp as Broker
        else:
            self.log("root", "cannot efficiently use multiple CPU cores")
            from .broker_thr import BrokerThr as Broker

        self.broker = Broker(self)

    def run(self):
        thr = threading.Thread(target=self.tcpsrv.run)
        thr.daemon = True
        thr.start()

        # winxp/py2.7 support: thr.join() kills signals
        try:
            while True:
                time.sleep(9001)

        except KeyboardInterrupt:
            with self.log_mutex:
                print("OPYTHAT")

            self.tcpsrv.shutdown()
            self.broker.shutdown()
            if self.thumbsrv:
                self.thumbsrv.shutdown()

                for n in range(200):  # 10s
                    time.sleep(0.05)
                    if self.thumbsrv.stopped():
                        break

                    if n == 3:
                        print("waiting for thumbsrv...")

            print("nailed it")

    def _log_disabled(self, src, msg, c=0):
        pass

    def _log_enabled(self, src, msg, c=0):
        """handles logging from all components"""
        with self.log_mutex:
            now = time.time()
            if now >= self.next_day:
                dt = datetime.utcfromtimestamp(now)
                print("\033[36m{}\033[0m\n".format(dt.strftime("%Y-%m-%d")), end="")

                # unix timestamp of next 00:00:00 (leap-seconds safe)
                day_now = dt.day
                while dt.day == day_now:
                    dt += timedelta(hours=12)

                dt = dt.replace(hour=0, minute=0, second=0)
                self.next_day = calendar.timegm(dt.utctimetuple())

            fmt = "\033[36m{} \033[33m{:21} \033[0m{}\n"
            if not VT100:
                fmt = "{} {:21} {}\n"
                if "\033" in msg:
                    msg = self.ansi_re.sub("", msg)
                if "\033" in src:
                    src = self.ansi_re.sub("", src)
            elif c:
                if isinstance(c, int):
                    msg = "\033[3{}m{}".format(c, msg)
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

    def check_mp_support(self):
        vmin = sys.version_info[1]
        if WINDOWS:
            msg = "need python 3.3 or newer for multiprocessing;"
            if PY2:
                # py2 pickler doesn't support winsock
                return msg
            elif vmin < 3:
                return msg
        elif MACOS:
            return "multiprocessing is wonky on mac osx;"
        else:
            msg = "need python 2.7 or 3.3+ for multiprocessing;"
            if not PY2 and vmin < 3:
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
            self.log("root", "multiprocessing disabled by argument -j 1;")
            return False

        if mp.cpu_count() <= 1:
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
            self.log("root", err)
            return False

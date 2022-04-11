# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import time
import math
import base64
import socket
import threading

try:
    import jinja2
except ImportError:
    print(
        """\033[1;31m
  you do not have jinja2 installed,\033[33m
  choose one of these:\033[0m
   * apt install python-jinja2
   * {} -m pip install --user jinja2
   * (try another python version, if you have one)
   * (try copyparty.sfx instead)
""".format(
            os.path.basename(sys.executable)
        )
    )
    sys.exit(1)

from .__init__ import E, PY2, MACOS
from .util import FHC, spack, min_ex, start_stackmon, start_log_thrs
from .bos import bos
from .httpconn import HttpConn

if PY2:
    import Queue as queue
else:
    import queue


class HttpSrv(object):
    """
    handles incoming connections using HttpConn to process http,
    relying on MpSrv for performance (HttpSrv is just plain threads)
    """

    def __init__(self, broker, nid):
        self.broker = broker
        self.nid = nid
        self.args = broker.args
        self.log = broker.log
        self.asrv = broker.asrv

        nsuf = "-n{}-i{:x}".format(nid, os.getpid()) if nid else ""

        self.name = "hsrv" + nsuf
        self.mutex = threading.Lock()
        self.stopping = False

        self.tp_nthr = 0  # actual
        self.tp_ncli = 0  # fading
        self.tp_time = None  # latest worker collect
        self.tp_q = None if self.args.no_htp else queue.LifoQueue()
        self.t_periodic = None

        self.u2fh = FHC()
        self.srvs = []
        self.ncli = 0  # exact
        self.clients = {}  # laggy
        self.nclimax = 0
        self.cb_ts = 0
        self.cb_v = 0

        try:
            x = self.broker.put(True, "thumbsrv.getcfg")
            self.th_cfg = x.get()
        except:
            pass

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(E.mod, "web"))
        self.j2 = {
            x: env.get_template(x + ".html")
            for x in ["splash", "browser", "browser2", "msg", "md", "mde"]
        }
        self.prism = os.path.exists(os.path.join(E.mod, "web", "deps", "prism.js.gz"))

        cert_path = os.path.join(E.cfg, "cert.pem")
        if bos.path.exists(cert_path):
            self.cert_path = cert_path
        else:
            self.cert_path = None

        if self.tp_q:
            self.start_threads(4)

        if nid:
            if self.args.stackmon:
                start_stackmon(self.args.stackmon, nid)

            if self.args.log_thrs:
                start_log_thrs(self.log, self.args.log_thrs, nid)

    def start_threads(self, n):
        self.tp_nthr += n
        if self.args.log_htp:
            self.log(self.name, "workers += {} = {}".format(n, self.tp_nthr), 6)

        for _ in range(n):
            thr = threading.Thread(
                target=self.thr_poolw,
                name=self.name + "-poolw",
            )
            thr.daemon = True
            thr.start()

    def stop_threads(self, n):
        self.tp_nthr -= n
        if self.args.log_htp:
            self.log(self.name, "workers -= {} = {}".format(n, self.tp_nthr), 6)

        for _ in range(n):
            self.tp_q.put(None)

    def periodic(self):
        while True:
            time.sleep(2 if self.tp_ncli or self.ncli else 10)
            with self.mutex:
                self.u2fh.clean()
                if self.tp_q:
                    self.tp_ncli = max(self.ncli, self.tp_ncli - 2)
                    if self.tp_nthr > self.tp_ncli + 8:
                        self.stop_threads(4)

                if not self.ncli and not self.u2fh.cache and self.tp_nthr <= 8:
                    self.t_periodic = None
                    return

    def listen(self, sck, nlisteners):
        ip, port = sck.getsockname()
        self.srvs.append(sck)
        self.nclimax = math.ceil(self.args.nc * 1.0 / nlisteners)
        t = threading.Thread(
            target=self.thr_listen,
            args=(sck,),
            name="httpsrv-n{}-listen-{}-{}".format(self.nid or "0", ip, port),
        )
        t.daemon = True
        t.start()

    def thr_listen(self, srv_sck):
        """listens on a shared tcp server"""
        ip, port = srv_sck.getsockname()
        fno = srv_sck.fileno()
        msg = "subscribed @ {}:{}  f{}".format(ip, port, fno)
        self.log(self.name, msg)

        def fun():
            self.broker.put(False, "cb_httpsrv_up")

        threading.Thread(target=fun).start()

        while not self.stopping:
            if self.args.log_conn:
                self.log(self.name, "|%sC-ncli" % ("-" * 1,), c="1;30")

            if self.ncli >= self.nclimax:
                self.log(self.name, "at connection limit; waiting", 3)
                while self.ncli >= self.nclimax:
                    time.sleep(0.1)

            if self.args.log_conn:
                self.log(self.name, "|%sC-acc1" % ("-" * 2,), c="1;30")

            try:
                sck, addr = srv_sck.accept()
            except (OSError, socket.error) as ex:
                self.log(self.name, "accept({}): {}".format(fno, ex), c=6)
                time.sleep(0.02)
                continue

            if self.args.log_conn:
                m = "|{}C-acc2 \033[0;36m{} \033[3{}m{}".format(
                    "-" * 3, ip, port % 8, port
                )
                self.log("%s %s" % addr, m, c="1;30")

            self.accept(sck, addr)

    def accept(self, sck, addr):
        """takes an incoming tcp connection and creates a thread to handle it"""
        now = time.time()

        if now - (self.tp_time or now) > 300:
            m = "httpserver threadpool died: tpt {:.2f}, now {:.2f}, nthr {}, ncli {}"
            self.log(self.name, m.format(self.tp_time, now, self.tp_nthr, self.ncli), 1)
            self.tp_time = None
            self.tp_q = None

        with self.mutex:
            self.ncli += 1
            if not self.t_periodic:
                name = "hsrv-pt"
                if self.nid:
                    name += "-{}".format(self.nid)

                t = threading.Thread(target=self.periodic, name=name)
                self.t_periodic = t
                t.daemon = True
                t.start()

            if self.tp_q:
                self.tp_time = self.tp_time or now
                self.tp_ncli = max(self.tp_ncli, self.ncli)
                if self.tp_nthr < self.ncli + 4:
                    self.start_threads(8)

                self.tp_q.put((sck, addr))
                return

        if not self.args.no_htp:
            m = "looks like the httpserver threadpool died; please make an issue on github and tell me the story of how you pulled that off, thanks and dog bless\n"
            self.log(self.name, m, 1)

        thr = threading.Thread(
            target=self.thr_client,
            args=(sck, addr),
            name="httpconn-{}-{}".format(addr[0].split(".", 2)[-1][-6:], addr[1]),
        )
        thr.daemon = True
        thr.start()

    def thr_poolw(self):
        while True:
            task = self.tp_q.get()
            if not task:
                break

            with self.mutex:
                self.tp_time = None

            try:
                sck, addr = task
                me = threading.current_thread()
                me.name = "httpconn-{}-{}".format(
                    addr[0].split(".", 2)[-1][-6:], addr[1]
                )
                self.thr_client(sck, addr)
                me.name = self.name + "-poolw"
            except:
                self.log(self.name, "thr_client: " + min_ex(), 3)

    def shutdown(self):
        self.stopping = True
        for srv in self.srvs:
            try:
                srv.close()
            except:
                pass

        clients = list(self.clients.keys())
        for cli in clients:
            try:
                cli.shutdown()
            except:
                pass

        if self.tp_q:
            self.stop_threads(self.tp_nthr)
            for _ in range(10):
                time.sleep(0.05)
                if self.tp_q.empty():
                    break

        self.log(self.name, "ok bye")

    def thr_client(self, sck, addr):
        """thread managing one tcp client"""
        sck.settimeout(120)

        cli = HttpConn(sck, addr, self)
        with self.mutex:
            self.clients[cli] = 0

        fno = sck.fileno()
        try:
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-crun" % ("-" * 4,), c="1;30")

            cli.run()

        except (OSError, socket.error) as ex:
            if ex.errno not in [10038, 10054, 107, 57, 49, 9]:
                self.log(
                    "%s %s" % addr,
                    "run({}): {}".format(fno, ex),
                    c=6,
                )

        finally:
            sck = cli.s
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-cdone" % ("-" * 5,), c="1;30")

            try:
                fno = sck.fileno()
                sck.shutdown(socket.SHUT_RDWR)
                sck.close()
            except (OSError, socket.error) as ex:
                if not MACOS:
                    self.log(
                        "%s %s" % addr,
                        "shut({}): {}".format(fno, ex),
                        c="1;30",
                    )
                if ex.errno not in [10038, 10054, 107, 57, 49, 9]:
                    # 10038 No longer considered a socket
                    # 10054 Foribly closed by remote
                    #   107 Transport endpoint not connected
                    #    57 Socket is not connected
                    #    49 Can't assign requested address (wifi down)
                    #     9 Bad file descriptor
                    raise
            finally:
                with self.mutex:
                    del self.clients[cli]
                    self.ncli -= 1

    def cachebuster(self):
        if time.time() - self.cb_ts < 1:
            return self.cb_v

        with self.mutex:
            if time.time() - self.cb_ts < 1:
                return self.cb_v

            v = E.t0
            try:
                with os.scandir(os.path.join(E.mod, "web")) as dh:
                    for fh in dh:
                        inf = fh.stat()
                        v = max(v, inf.st_mtime)
            except:
                pass

            v = base64.urlsafe_b64encode(spack(b">xxL", int(v)))
            self.cb_v = v.decode("ascii")[-4:]
            self.cb_ts = time.time()
            return self.cb_v

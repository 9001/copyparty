# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import time
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
from .util import spack, min_ex
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

    def __init__(self, broker, is_mp=False):
        self.broker = broker
        self.is_mp = is_mp
        self.args = broker.args
        self.log = broker.log
        self.asrv = broker.asrv

        self.disconnect_func = None
        self.mutex = threading.Lock()

        self.tp_nthr = 0  # actual
        self.tp_ncli = 0  # fading
        self.tp_time = None  # latest worker collect
        self.tp_q = None if self.args.no_htp else queue.LifoQueue()

        self.clients = {}
        self.workload = 0
        self.workload_thr_alive = False
        self.cb_ts = 0
        self.cb_v = 0

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(E.mod, "web"))
        self.j2 = {
            x: env.get_template(x + ".html")
            for x in ["splash", "browser", "browser2", "msg", "md", "mde"]
        }

        cert_path = os.path.join(E.cfg, "cert.pem")
        if os.path.exists(cert_path):
            self.cert_path = cert_path
        else:
            self.cert_path = None

        if self.tp_q:
            self.start_threads(4)

            t = threading.Thread(target=self.thr_scaler)
            t.daemon = True
            t.start()

    def start_threads(self, n):
        self.tp_nthr += n
        if self.args.log_htp:
            self.log("httpsrv", "workers += {} = {}".format(n, self.tp_nthr), 6)

        for _ in range(n):
            thr = threading.Thread(
                target=self.thr_poolw,
                name="httpsrv-poolw",
            )
            thr.daemon = True
            thr.start()

    def stop_threads(self, n):
        self.tp_nthr -= n
        if self.args.log_htp:
            self.log("httpsrv", "workers -= {} = {}".format(n, self.tp_nthr), 6)

        for _ in range(n):
            self.tp_q.put(None)

    def thr_scaler(self):
        while True:
            time.sleep(2 if self.tp_ncli else 30)
            with self.mutex:
                self.tp_ncli = max(len(self.clients), self.tp_ncli - 2)
                if self.tp_nthr > self.tp_ncli + 8:
                    self.stop_threads(4)

    def accept(self, sck, addr):
        """takes an incoming tcp connection and creates a thread to handle it"""
        if self.args.log_conn:
            self.log("%s %s" % addr, "|%sC-cthr" % ("-" * 5,), c="1;30")

        now = time.time()

        if self.tp_time and now - self.tp_time > 300:
            self.tp_q = None

        if self.tp_q:
            self.tp_q.put((sck, addr))
            with self.mutex:
                self.tp_time = self.tp_time or now
                self.tp_ncli = max(self.tp_ncli, len(self.clients) + 1)
                if self.tp_nthr < len(self.clients) + 4:
                    self.start_threads(8)
            return

        if not self.args.no_htp:
            m = "looks like the httpserver threadpool died; please make an issue on github and tell me the story of how you pulled that off, thanks and dog bless\n"
            self.log("httpsrv", m, 1)

        thr = threading.Thread(
            target=self.thr_client,
            args=(sck, addr),
            name="httpsrv-{}-{}".format(addr[0].split(".", 2)[-1][-6:], addr[1]),
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
                me.name = (
                    "httpsrv-{}-{}".format(addr[0].split(".", 2)[-1][-6:], addr[1]),
                )
                self.thr_client(sck, addr)
                me.name = "httpsrv-poolw"
            except:
                self.log("httpsrv", "thr_client: " + min_ex(), 3)

    def num_clients(self):
        with self.mutex:
            return len(self.clients)

    def shutdown(self):
        clients = list(self.clients.keys())
        for cli in clients:
            try:
                cli.shutdown()
            except:
                pass

        self.log("httpsrv-n", "ok bye")

    def thr_client(self, sck, addr):
        """thread managing one tcp client"""
        sck.settimeout(120)

        cli = HttpConn(sck, addr, self)
        with self.mutex:
            self.clients[cli] = 0

            if self.is_mp:
                self.workload += 50
                if not self.workload_thr_alive:
                    self.workload_thr_alive = True
                    thr = threading.Thread(
                        target=self.thr_workload, name="httpsrv-workload"
                    )
                    thr.daemon = True
                    thr.start()

        fno = sck.fileno()
        try:
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-crun" % ("-" * 6,), c="1;30")

            cli.run()

        except (OSError, socket.error) as ex:
            if ex.errno not in [10038, 10054, 107, 57, 9]:
                self.log(
                    "%s %s" % addr,
                    "run({}): {}".format(fno, ex),
                    c=6,
                )

        finally:
            sck = cli.s
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-cdone" % ("-" * 7,), c="1;30")

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

                if self.disconnect_func:
                    self.disconnect_func(addr)  # pylint: disable=not-callable

    def thr_workload(self):
        """indicates the python interpreter workload caused by this HttpSrv"""
        # avoid locking in extract_filedata by tracking difference here
        while True:
            time.sleep(0.2)
            with self.mutex:
                if not self.clients:
                    # no clients rn, termiante thread
                    self.workload_thr_alive = False
                    self.workload = 0
                    return

            total = 0
            with self.mutex:
                for cli in self.clients.keys():
                    now = cli.workload
                    delta = now - self.clients[cli]
                    if delta < 0:
                        # was reset in HttpCli to prevent overflow
                        delta = now

                    total += delta
                    self.clients[cli] = now

            self.workload = total

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
                        inf = fh.stat(follow_symlinks=False)
                        v = max(v, inf.st_mtime)
            except:
                pass

            v = base64.urlsafe_b64encode(spack(b">xxL", int(v)))
            self.cb_v = v.decode("ascii")[-4:]
            self.cb_ts = time.time()
            return self.cb_v

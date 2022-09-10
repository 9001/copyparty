# coding: utf-8
from __future__ import print_function, unicode_literals

import base64
import math
import os
import socket
import sys
import threading
import time

import queue

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

from .__init__ import MACOS, TYPE_CHECKING, EnvParams
from .bos import bos
from .httpconn import HttpConn
from .util import FHC, min_ex, shut_socket, spack, start_log_thrs, start_stackmon

if TYPE_CHECKING:
    from .broker_util import BrokerCli

try:
    from typing import Any, Optional
except:
    pass


class HttpSrv(object):
    """
    handles incoming connections using HttpConn to process http,
    relying on MpSrv for performance (HttpSrv is just plain threads)
    """

    def __init__(self, broker: "BrokerCli", nid: Optional[int]) -> None:
        self.broker = broker
        self.nid = nid
        self.args = broker.args
        self.E: EnvParams = self.args.E
        self.log = broker.log
        self.asrv = broker.asrv

        # redefine in case of multiprocessing
        socket.setdefaulttimeout(120)

        nsuf = "-n{}-i{:x}".format(nid, os.getpid()) if nid else ""

        self.name = "hsrv" + nsuf
        self.mutex = threading.Lock()
        self.stopping = False

        self.tp_nthr = 0  # actual
        self.tp_ncli = 0  # fading
        self.tp_time = 0.0  # latest worker collect
        self.tp_q: Optional[queue.LifoQueue[Any]] = (
            None if self.args.no_htp else queue.LifoQueue()
        )
        self.t_periodic: Optional[threading.Thread] = None

        self.u2fh = FHC()
        self.srvs: list[socket.socket] = []
        self.ncli = 0  # exact
        self.clients: set[HttpConn] = set()  # laggy
        self.nclimax = 0
        self.cb_ts = 0.0
        self.cb_v = ""

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(self.E.mod, "web"))
        self.j2 = {
            x: env.get_template(x + ".html")
            for x in ["splash", "browser", "browser2", "msg", "md", "mde", "cf"]
        }
        zs = os.path.join(self.E.mod, "web", "deps", "prism.js.gz")
        self.prism = os.path.exists(zs)

        cert_path = os.path.join(self.E.cfg, "cert.pem")
        if bos.path.exists(cert_path):
            self.cert_path = cert_path
        else:
            self.cert_path = ""

        if self.tp_q:
            self.start_threads(4)

        if nid:
            if self.args.stackmon:
                start_stackmon(self.args.stackmon, nid)

            if self.args.log_thrs:
                start_log_thrs(self.log, self.args.log_thrs, nid)

        self.th_cfg: dict[str, Any] = {}
        t = threading.Thread(target=self.post_init, name="hsrv-init2")
        t.daemon = True
        t.start()

    def post_init(self) -> None:
        try:
            x = self.broker.ask("thumbsrv.getcfg")
            self.th_cfg = x.get()
        except:
            pass

    def start_threads(self, n: int) -> None:
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

    def stop_threads(self, n: int) -> None:
        self.tp_nthr -= n
        if self.args.log_htp:
            self.log(self.name, "workers -= {} = {}".format(n, self.tp_nthr), 6)

        assert self.tp_q
        for _ in range(n):
            self.tp_q.put(None)

    def periodic(self) -> None:
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

    def listen(self, sck: socket.socket, nlisteners: int) -> None:
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

    def thr_listen(self, srv_sck: socket.socket) -> None:
        """listens on a shared tcp server"""
        ip, port = srv_sck.getsockname()
        fno = srv_sck.fileno()
        msg = "subscribed @ {}:{}  f{} p{}".format(ip, port, fno, os.getpid())
        self.log(self.name, msg)

        def fun() -> None:
            self.broker.say("cb_httpsrv_up")

        threading.Thread(target=fun, name="sig-hsrv-up1").start()

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
                t = "|{}C-acc2 \033[0;36m{} \033[3{}m{}".format(
                    "-" * 3, ip, port % 8, port
                )
                self.log("%s %s" % addr, t, c="1;30")

            self.accept(sck, addr)

    def accept(self, sck: socket.socket, addr: tuple[str, int]) -> None:
        """takes an incoming tcp connection and creates a thread to handle it"""
        now = time.time()

        if now - (self.tp_time or now) > 300:
            t = "httpserver threadpool died: tpt {:.2f}, now {:.2f}, nthr {}, ncli {}"
            self.log(self.name, t.format(self.tp_time, now, self.tp_nthr, self.ncli), 1)
            self.tp_time = 0
            self.tp_q = None

        with self.mutex:
            self.ncli += 1
            if not self.t_periodic:
                name = "hsrv-pt"
                if self.nid:
                    name += "-{}".format(self.nid)

                thr = threading.Thread(target=self.periodic, name=name)
                self.t_periodic = thr
                thr.daemon = True
                thr.start()

            if self.tp_q:
                self.tp_time = self.tp_time or now
                self.tp_ncli = max(self.tp_ncli, self.ncli)
                if self.tp_nthr < self.ncli + 4:
                    self.start_threads(8)

                self.tp_q.put((sck, addr))
                return

        if not self.args.no_htp:
            t = "looks like the httpserver threadpool died; please make an issue on github and tell me the story of how you pulled that off, thanks and dog bless\n"
            self.log(self.name, t, 1)

        thr = threading.Thread(
            target=self.thr_client,
            args=(sck, addr),
            name="httpconn-{}-{}".format(addr[0].split(".", 2)[-1][-6:], addr[1]),
        )
        thr.daemon = True
        thr.start()

    def thr_poolw(self) -> None:
        assert self.tp_q
        while True:
            task = self.tp_q.get()
            if not task:
                break

            with self.mutex:
                self.tp_time = 0

            try:
                sck, addr = task
                me = threading.current_thread()
                me.name = "httpconn-{}-{}".format(
                    addr[0].split(".", 2)[-1][-6:], addr[1]
                )
                self.thr_client(sck, addr)
                me.name = self.name + "-poolw"
            except Exception as ex:
                if str(ex).startswith("client d/c "):
                    self.log(self.name, "thr_client: " + str(ex), 6)
                else:
                    self.log(self.name, "thr_client: " + min_ex(), 3)

    def shutdown(self) -> None:
        self.stopping = True
        for srv in self.srvs:
            try:
                srv.close()
            except:
                pass

        thrs = []
        clients = list(self.clients)
        for cli in clients:
            t = threading.Thread(target=cli.shutdown)
            thrs.append(t)
            t.start()

        if self.tp_q:
            self.stop_threads(self.tp_nthr)
            for _ in range(10):
                time.sleep(0.05)
                if self.tp_q.empty():
                    break

        for t in thrs:
            t.join()

        self.log(self.name, "ok bye")

    def thr_client(self, sck: socket.socket, addr: tuple[str, int]) -> None:
        """thread managing one tcp client"""
        cli = HttpConn(sck, addr, self)
        with self.mutex:
            self.clients.add(cli)

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
                shut_socket(cli.log, sck)
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
                    self.clients.remove(cli)
                    self.ncli -= 1

    def cachebuster(self) -> str:
        if time.time() - self.cb_ts < 1:
            return self.cb_v

        with self.mutex:
            if time.time() - self.cb_ts < 1:
                return self.cb_v

            v = self.E.t0
            try:
                with os.scandir(os.path.join(self.E.mod, "web")) as dh:
                    for fh in dh:
                        inf = fh.stat()
                        v = max(v, inf.st_mtime)
            except:
                pass

            v = base64.urlsafe_b64encode(spack(b">xxL", int(v)))
            self.cb_v = v.decode("ascii")[-4:]
            self.cb_ts = time.time()
            return self.cb_v

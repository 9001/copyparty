# coding: utf-8
from __future__ import print_function, unicode_literals

import base64
import math
import os
import re
import socket
import sys
import threading
import time

import queue

from .__init__ import ANYWIN, CORES, EXE, MACOS, TYPE_CHECKING, EnvParams

try:
    MNFE = ModuleNotFoundError
except:
    MNFE = ImportError

try:
    import jinja2
except MNFE:
    if EXE:
        raise

    print(
        """\033[1;31m
  you do not have jinja2 installed,\033[33m
  choose one of these:\033[0m
   * apt install python-jinja2
   * {} -m pip install --user jinja2
   * (try another python version, if you have one)
   * (try copyparty.sfx instead)
""".format(
            sys.executable
        )
    )
    sys.exit(1)
except SyntaxError:
    if EXE:
        raise

    print(
        """\033[1;31m
  your jinja2 version is incompatible with your python version;\033[33m
  please try to replace it with an older version:\033[0m
   * {} -m pip install --user jinja2==2.11.3
   * (try another python version, if you have one)
   * (try copyparty.sfx instead)
""".format(
            sys.executable
        )
    )
    sys.exit(1)

from .bos import bos
from .httpconn import HttpConn
from .u2idx import U2idx
from .util import (
    E_SCK,
    FHC,
    Daemon,
    Garda,
    Magician,
    Netdev,
    NetMap,
    ipnorm,
    min_ex,
    shut_socket,
    spack,
    start_log_thrs,
    start_stackmon,
)

if TYPE_CHECKING:
    from .broker_util import BrokerCli
    from .ssdp import SSDPr

if True:  # pylint: disable=using-constant-test
    from typing import Any, Optional


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
        self.magician = Magician()
        self.nm = NetMap([], {})
        self.ssdp: Optional["SSDPr"] = None
        self.gpwd = Garda(self.args.ban_pw)
        self.g404 = Garda(self.args.ban_404)
        self.bans: dict[str, int] = {}
        self.aclose: dict[str, int] = {}

        self.bound: set[tuple[str, int]] = set()
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

        self.u2idx_free: dict[str, U2idx] = {}
        self.u2idx_n = 0

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(self.E.mod, "web"))
        jn = ["splash", "svcs", "browser", "browser2", "msg", "md", "mde", "cf"]
        self.j2 = {x: env.get_template(x + ".html") for x in jn}
        zs = os.path.join(self.E.mod, "web", "deps", "prism.js.gz")
        self.prism = os.path.exists(zs)

        self.ptn_cc = re.compile(r"[\x00-\x1f]")

        self.mallow = "GET HEAD POST PUT DELETE OPTIONS".split()
        if not self.args.no_dav:
            zs = "PROPFIND PROPPATCH LOCK UNLOCK MKCOL COPY MOVE"
            self.mallow += zs.split()

        if self.args.zs:
            from .ssdp import SSDPr

            self.ssdp = SSDPr(broker)

        if self.tp_q:
            self.start_threads(4)

        if nid:
            if self.args.stackmon:
                start_stackmon(self.args.stackmon, nid)

            if self.args.log_thrs:
                start_log_thrs(self.log, self.args.log_thrs, nid)

        self.th_cfg: dict[str, Any] = {}
        Daemon(self.post_init, "hsrv-init2")

    def post_init(self) -> None:
        try:
            x = self.broker.ask("thumbsrv.getcfg")
            self.th_cfg = x.get()
        except:
            pass

    def set_netdevs(self, netdevs: dict[str, Netdev]) -> None:
        ips = set()
        for ip, _ in self.bound:
            ips.add(ip)

        self.nm = NetMap(list(ips), netdevs)

    def start_threads(self, n: int) -> None:
        self.tp_nthr += n
        if self.args.log_htp:
            self.log(self.name, "workers += {} = {}".format(n, self.tp_nthr), 6)

        for _ in range(n):
            Daemon(self.thr_poolw, self.name + "-poolw")

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
        if self.args.j != 1:
            # lost in the pickle; redefine
            if not ANYWIN or self.args.reuseaddr:
                sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sck.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sck.settimeout(None)  # < does not inherit, ^ opts above do

        ip, port = sck.getsockname()[:2]
        self.srvs.append(sck)
        self.bound.add((ip, port))
        self.nclimax = math.ceil(self.args.nc * 1.0 / nlisteners)
        Daemon(
            self.thr_listen,
            "httpsrv-n{}-listen-{}-{}".format(self.nid or "0", ip, port),
            (sck,),
        )

    def thr_listen(self, srv_sck: socket.socket) -> None:
        """listens on a shared tcp server"""
        ip, port = srv_sck.getsockname()[:2]
        fno = srv_sck.fileno()
        hip = "[{}]".format(ip) if ":" in ip else ip
        msg = "subscribed @ {}:{}  f{} p{}".format(hip, port, fno, os.getpid())
        self.log(self.name, msg)

        def fun() -> None:
            self.broker.say("cb_httpsrv_up")

        threading.Thread(target=fun, name="sig-hsrv-up1").start()

        while not self.stopping:
            if self.args.log_conn:
                self.log(self.name, "|%sC-ncli" % ("-" * 1,), c="90")

            spins = 0
            while self.ncli >= self.nclimax:
                if not spins:
                    self.log(self.name, "at connection limit; waiting", 3)

                spins += 1
                time.sleep(0.1)
                if spins != 50 or not self.args.aclose:
                    continue

                ipfreq: dict[str, int] = {}
                with self.mutex:
                    for c in self.clients:
                        ip = ipnorm(c.ip)
                        try:
                            ipfreq[ip] += 1
                        except:
                            ipfreq[ip] = 1

                ip, n = sorted(ipfreq.items(), key=lambda x: x[1], reverse=True)[0]
                if n < self.nclimax / 2:
                    continue

                self.aclose[ip] = int(time.time() + self.args.aclose * 60)
                nclose = 0
                nloris = 0
                nconn = 0
                with self.mutex:
                    for c in self.clients:
                        cip = ipnorm(c.ip)
                        if ip != cip:
                            continue

                        nconn += 1
                        try:
                            if (
                                c.nreq >= 1
                                or not c.cli
                                or c.cli.in_hdr_recv
                                or c.cli.keepalive
                            ):
                                Daemon(c.shutdown)
                                nclose += 1
                                if c.nreq <= 0 and (not c.cli or c.cli.in_hdr_recv):
                                    nloris += 1
                        except:
                            pass

                t = "{} downgraded to connection:close for {} min; dropped {}/{} connections"
                self.log(self.name, t.format(ip, self.args.aclose, nclose, nconn), 1)

                if nloris < nconn / 2:
                    continue

                t = "slowloris (idle-conn): {} banned for {} min"
                self.log(self.name, t.format(ip, self.args.loris, nclose), 1)
                self.bans[ip] = int(time.time() + self.args.loris * 60)

            if self.args.log_conn:
                self.log(self.name, "|%sC-acc1" % ("-" * 2,), c="90")

            try:
                sck, saddr = srv_sck.accept()
                cip, cport = saddr[:2]
                if cip.startswith("::ffff:"):
                    cip = cip[7:]

                addr = (cip, cport)
            except (OSError, socket.error) as ex:
                if self.stopping:
                    break

                self.log(self.name, "accept({}): {}".format(fno, ex), c=6)
                time.sleep(0.02)
                continue

            if self.args.log_conn:
                t = "|{}C-acc2 \033[0;36m{} \033[3{}m{}".format(
                    "-" * 3, ip, port % 8, port
                )
                self.log("%s %s" % addr, t, c="90")

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

                self.t_periodic = Daemon(self.periodic, name)

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

        Daemon(
            self.thr_client,
            "httpconn-{}-{}".format(addr[0].split(".", 2)[-1][-6:], addr[1]),
            (sck, addr),
        )

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

        # print("{}\n".format(len(self.clients)), end="")
        fno = sck.fileno()
        try:
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-crun" % ("-" * 4,), c="90")

            cli.run()

        except (OSError, socket.error) as ex:
            if ex.errno not in E_SCK:
                self.log(
                    "%s %s" % addr,
                    "run({}): {}".format(fno, ex),
                    c=6,
                )

        finally:
            sck = cli.s
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-cdone" % ("-" * 5,), c="90")

            try:
                fno = sck.fileno()
                shut_socket(cli.log, sck)
            except (OSError, socket.error) as ex:
                if not MACOS:
                    self.log(
                        "%s %s" % addr,
                        "shut({}): {}".format(fno, ex),
                        c="90",
                    )
                if ex.errno not in E_SCK:
                    raise
            finally:
                with self.mutex:
                    self.clients.remove(cli)
                    self.ncli -= 1

                if cli.u2idx:
                    self.put_u2idx(str(addr), cli.u2idx)

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

    def get_u2idx(self, ident: str) -> Optional[U2idx]:
        utab = self.u2idx_free
        for _ in range(100):  # 5/0.05 = 5sec
            with self.mutex:
                if utab:
                    if ident in utab:
                        return utab.pop(ident)

                    return utab.pop(list(utab.keys())[0])

                if self.u2idx_n < CORES:
                    self.u2idx_n += 1
                    return U2idx(self)

            time.sleep(0.05)
            # not using conditional waits, on a hunch that
            # average performance will be faster like this
            # since most servers won't be fully saturated

        return None

    def put_u2idx(self, ident: str, u2idx: U2idx) -> None:
        with self.mutex:
            while ident in self.u2idx_free:
                ident += "a"

            self.u2idx_free[ident] = u2idx

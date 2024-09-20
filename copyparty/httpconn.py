# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse  # typechk
import os
import re
import socket
import threading  # typechk
import time

try:
    if os.environ.get("PRTY_NO_TLS"):
        raise Exception()

    HAVE_SSL = True
    import ssl
except:
    HAVE_SSL = False

from . import util as Util
from .__init__ import TYPE_CHECKING, EnvParams
from .authsrv import AuthSrv  # typechk
from .httpcli import HttpCli
from .ico import Ico
from .mtag import HAVE_FFMPEG
from .th_cli import ThumbCli
from .th_srv import HAVE_PIL, HAVE_VIPS
from .u2idx import U2idx
from .util import HMaccas, NetMap, shut_socket

if True:  # pylint: disable=using-constant-test
    from typing import Optional, Pattern, Union

if TYPE_CHECKING:
    from .httpsrv import HttpSrv


PTN_HTTP = re.compile(br"[A-Z]{3}[A-Z ]")


class HttpConn(object):
    """
    spawned by HttpSrv to handle an incoming client connection,
    creates an HttpCli for each request (Connection: Keep-Alive)
    """

    def __init__(
        self, sck: socket.socket, addr: tuple[str, int], hsrv: "HttpSrv"
    ) -> None:
        self.s = sck
        self.sr: Optional[Util._Unrecv] = None
        self.cli: Optional[HttpCli] = None
        self.addr = addr
        self.hsrv = hsrv

        self.u2mutex: threading.Lock = hsrv.u2mutex  # mypy404
        self.args: argparse.Namespace = hsrv.args  # mypy404
        self.E: EnvParams = self.args.E
        self.asrv: AuthSrv = hsrv.asrv  # mypy404
        self.u2fh: Util.FHC = hsrv.u2fh  # mypy404
        self.pipes: Util.CachedDict = hsrv.pipes  # mypy404
        self.ipa_nm: Optional[NetMap] = hsrv.ipa_nm
        self.xff_nm: Optional[NetMap] = hsrv.xff_nm
        self.xff_lan: NetMap = hsrv.xff_lan  # type: ignore
        self.iphash: HMaccas = hsrv.broker.iphash
        self.bans: dict[str, int] = hsrv.bans
        self.aclose: dict[str, int] = hsrv.aclose

        enth = (HAVE_PIL or HAVE_VIPS or HAVE_FFMPEG) and not self.args.no_thumb
        self.thumbcli: Optional[ThumbCli] = ThumbCli(hsrv) if enth else None  # mypy404
        self.ico: Ico = Ico(self.args)  # mypy404

        self.t0: float = time.time()  # mypy404
        self.freshen_pwd: float = 0.0
        self.stopping = False
        self.nreq: int = -1  # mypy404
        self.nbyte: int = 0  # mypy404
        self.u2idx: Optional[U2idx] = None
        self.log_func: "Util.RootLogger" = hsrv.log  # mypy404
        self.log_src: str = "httpconn"  # mypy404
        self.lf_url: Optional[Pattern[str]] = (
            re.compile(self.args.lf_url) if self.args.lf_url else None
        )  # mypy404
        self.set_rproxy()

    def shutdown(self) -> None:
        self.stopping = True
        try:
            shut_socket(self.log, self.s, 1)
        except:
            pass

    def set_rproxy(self, ip: Optional[str] = None) -> str:
        if ip is None:
            color = 36
            ip = self.addr[0]
            self.rproxy = None
        else:
            color = 34
            self.rproxy = ip

        self.ip = ip
        self.log_src = ("%s \033[%dm%d" % (ip, color, self.addr[1])).ljust(26)
        return self.log_src

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func(self.log_src, msg, c)

    def get_u2idx(self) -> Optional[U2idx]:
        # grab from a pool of u2idx instances;
        # sqlite3 fully parallelizes under python threads
        # but avoid running out of FDs by creating too many
        if not self.u2idx:
            self.u2idx = self.hsrv.get_u2idx(str(self.addr))

        return self.u2idx

    def _detect_https(self) -> bool:
        try:
            method = self.s.recv(4, socket.MSG_PEEK)
        except socket.timeout:
            return False
        except AttributeError:
            # jython does not support msg_peek; forget about https
            method = self.s.recv(4)
            self.sr = Util.Unrecv(self.s, self.log)
            self.sr.buf = method

            # jython used to do this, they stopped since it's broken
            # but reimplementing sendall is out of scope for now
            if not getattr(self.s, "sendall", None):
                self.s.sendall = self.s.send  # type: ignore

        if len(method) != 4:
            err = "need at least 4 bytes in the first packet; got {}".format(
                len(method)
            )
            if method:
                self.log(err)

            self.s.send(b"HTTP/1.1 400 Bad Request\r\n\r\n" + err.encode("utf-8"))
            return False

        return not method or not bool(PTN_HTTP.match(method))

    def run(self) -> None:
        self.s.settimeout(10)

        self.sr = None
        if self.args.https_only:
            is_https = True
        elif self.args.http_only:
            is_https = False
        else:
            # raise Exception("asdf")
            is_https = self._detect_https()

        if is_https:
            if self.sr:
                self.log("TODO: cannot do https in jython", c="1;31")
                return

            self.log_src = self.log_src.replace("[36m", "[35m")
            try:
                assert ssl  # type: ignore  # !rm
                ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ctx.load_cert_chain(self.args.cert)
                if self.args.ssl_ver:
                    ctx.options &= ~self.args.ssl_flags_en
                    ctx.options |= self.args.ssl_flags_de
                    # print(repr(ctx.options))

                if self.args.ssl_log:
                    try:
                        ctx.keylog_filename = self.args.ssl_log
                    except:
                        self.log("keylog failed; openssl or python too old")

                if self.args.ciphers:
                    ctx.set_ciphers(self.args.ciphers)

                self.s = ctx.wrap_socket(self.s, server_side=True)
                msg = [
                    "\033[1;3%dm%s" % (c, s)
                    for c, s in zip([0, 5, 0], self.s.cipher())  # type: ignore
                ]
                self.log(" ".join(msg) + "\033[0m")

                if self.args.ssl_dbg and hasattr(self.s, "shared_ciphers"):
                    ciphers = self.s.shared_ciphers()
                    assert ciphers  # !rm
                    overlap = [str(y[::-1]) for y in ciphers]
                    self.log("TLS cipher overlap:" + "\n".join(overlap))
                    for k, v in [
                        ["compression", self.s.compression()],
                        ["ALPN proto", self.s.selected_alpn_protocol()],
                        ["NPN proto", self.s.selected_npn_protocol()],
                    ]:
                        self.log("TLS {}: {}".format(k, v or "nah"))

            except Exception as ex:
                em = str(ex)

                if "ALERT_CERTIFICATE_UNKNOWN" in em:
                    # android-chrome keeps doing this
                    pass

                else:
                    self.log("handshake\033[0m " + em, c=5)

                return

        if not self.sr:
            self.sr = Util.Unrecv(self.s, self.log)

        while not self.stopping:
            self.nreq += 1
            self.cli = HttpCli(self)
            if not self.cli.run():
                return

            if self.u2idx:
                self.hsrv.put_u2idx(str(self.addr), self.u2idx)
                self.u2idx = None

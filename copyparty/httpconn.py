# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import time
import socket

HAVE_SSL = True
try:
    import ssl
except:
    HAVE_SSL = False

from .__init__ import E
from .util import Unrecv
from .httpcli import HttpCli
from .u2idx import U2idx


class HttpConn(object):
    """
    spawned by HttpSrv to handle an incoming client connection,
    creates an HttpCli for each request (Connection: Keep-Alive)
    """

    def __init__(self, sck, addr, hsrv):
        self.s = sck
        self.addr = addr
        self.hsrv = hsrv

        self.args = hsrv.args
        self.auth = hsrv.auth
        self.cert_path = hsrv.cert_path

        self.t0 = time.time()
        self.nbyte = 0
        self.workload = 0
        self.u2idx = None
        self.log_func = hsrv.log
        self.set_rproxy()

    def set_rproxy(self, ip=None):
        if ip is None:
            color = 36
            ip = self.addr[0]
            self.rproxy = None
        else:
            color = 34
            self.rproxy = ip

        self.ip = ip
        self.log_src = "{} \033[{}m{}".format(ip, color, self.addr[1]).ljust(26)
        return self.log_src

    def respath(self, res_name):
        return os.path.join(E.mod, "web", res_name)

    def log(self, msg, c=0):
        self.log_func(self.log_src, msg, c)

    def get_u2idx(self):
        if not self.u2idx:
            self.u2idx = U2idx(self.args, self.log_func)

        return self.u2idx

    def _detect_https(self):
        method = None
        if self.cert_path:
            try:
                method = self.s.recv(4, socket.MSG_PEEK)
            except socket.timeout:
                return
            except AttributeError:
                # jython does not support msg_peek; forget about https
                method = self.s.recv(4)
                self.sr = Unrecv(self.s)
                self.sr.buf = method

                # jython used to do this, they stopped since it's broken
                # but reimplementing sendall is out of scope for now
                if not getattr(self.s, "sendall", None):
                    self.s.sendall = self.s.send

            if len(method) != 4:
                err = "need at least 4 bytes in the first packet; got {}".format(
                    len(method)
                )
                if method:
                    self.log(err)

                self.s.send(b"HTTP/1.1 400 Bad Request\r\n\r\n" + err.encode("utf-8"))
                return

        return method not in [None, b"GET ", b"HEAD", b"POST", b"PUT ", b"OPTI"]

    def run(self):
        self.sr = None
        if self.args.https_only:
            is_https = True
        elif self.args.http_only or not HAVE_SSL:
            is_https = False
        else:
            is_https = self._detect_https()

        if is_https:
            if self.sr:
                self.log("TODO: cannot do https in jython", c="1;31")
                return

            self.log_src = self.log_src.replace("[36m", "[35m")
            try:
                ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ctx.load_cert_chain(self.cert_path)
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
                    "\033[1;3{:d}m{}".format(c, s)
                    for c, s in zip([0, 5, 0], self.s.cipher())
                ]
                self.log(" ".join(msg) + "\033[0m")

                if self.args.ssl_dbg and hasattr(self.s, "shared_ciphers"):
                    overlap = [y[::-1] for y in self.s.shared_ciphers()]
                    lines = [str(x) for x in (["TLS cipher overlap:"] + overlap)]
                    self.log("\n".join(lines))
                    for k, v in [
                        ["compression", self.s.compression()],
                        ["ALPN proto", self.s.selected_alpn_protocol()],
                        ["NPN proto", self.s.selected_npn_protocol()],
                    ]:
                        self.log("TLS {}: {}".format(k, v or "nah"))

            except Exception as ex:
                em = str(ex)

                if "ALERT_BAD_CERTIFICATE" in em:
                    # firefox-linux if there is no exception yet
                    self.log("client rejected our certificate (nice)")

                elif "ALERT_CERTIFICATE_UNKNOWN" in em:
                    # chrome-android keeps doing this
                    pass

                else:
                    self.log("handshake\033[0m " + em, c=5)

                return

        if not self.sr:
            self.sr = Unrecv(self.s)

        while True:
            cli = HttpCli(self)
            if not cli.run():
                return

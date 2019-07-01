# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import ssl
import socket
import jinja2

from .__init__ import E
from .util import Unrecv
from .httpcli import HttpCli


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

        self.workload = 0
        self.log_func = hsrv.log
        self.log_src = "{} \033[36m{}".format(addr[0], addr[1]).ljust(26)

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(E.mod, "web"))
        self.tpl_mounts = env.get_template("splash.html")
        self.tpl_browser = env.get_template("browser.html")
        self.tpl_msg = env.get_template("msg.html")

    def respath(self, res_name):
        return os.path.join(E.mod, "web", res_name)

    def log(self, msg):
        self.log_func(self.log_src, msg)

    def run(self):
        method = None
        if self.cert_path:
            method = self.s.recv(4, socket.MSG_PEEK)
            if len(method) != 4:
                err = "need at least 4 bytes in the first packet; got {}".format(
                    len(method)
                )
                self.log(err)
                self.s.send(b"HTTP/1.1 400 Bad Request\r\n\r\n" + err.encode("utf-8"))
                return

        if method not in [None, b"GET ", b"HEAD", b"POST"]:
            self.log_src = self.log_src.replace("[36m", "[35m")
            try:
                self.s = ssl.wrap_socket(
                    self.s, server_side=True, certfile=self.cert_path
                )
            except Exception as ex:
                em = str(ex)

                if "ALERT_BAD_CERTIFICATE" in em:
                    # firefox-linux if there is no exception yet
                    self.log("client rejected our certificate (nice)")

                elif "ALERT_CERTIFICATE_UNKNOWN" in em:
                    # chrome-android keeps doing this
                    pass

                else:
                    self.log("\033[35mhandshake\033[0m " + em)

                return

        self.sr = Unrecv(self.s)

        while True:
            cli = HttpCli(self)
            if not cli.run():
                return

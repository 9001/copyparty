# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import ssl
import time
import socket

try:
    import jinja2
except ImportError:
    print(
        """\033[1;31m
  you do not have jinja2 installed,\033[33m
  choose one of these:\033[0m
   * apt install python-jinja2
   * python3 -m pip install --user jinja2
   * (try another python version, if you have one)
   * (try copyparty.sfx instead)
"""
    )
    sys.exit(1)

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

        self.t0 = time.time()
        self.nbyte = 0
        self.workload = 0
        self.log_func = hsrv.log
        self.set_rproxy()

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(E.mod, "web"))
        self.tpl_mounts = env.get_template("splash.html")
        self.tpl_browser = env.get_template("browser.html")
        self.tpl_msg = env.get_template("msg.html")
        self.tpl_md = env.get_template("md.html")
        self.tpl_mde = env.get_template("mde.html")

    def set_rproxy(self, ip=None):
        if ip is None:
            color = 36
            ip = self.addr[0]
            self.rproxy = None
        else:
            color = 34
            self.rproxy = ip

        self.log_src = "{} \033[{}m{}".format(ip, color, self.addr[1]).ljust(26)
        return self.log_src

    def respath(self, res_name):
        return os.path.join(E.mod, "web", res_name)

    def log(self, msg):
        self.log_func(self.log_src, msg)

    def run(self):
        method = None
        self.sr = None
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
                self.log(err)
                self.s.send(b"HTTP/1.1 400 Bad Request\r\n\r\n" + err.encode("utf-8"))
                return

        if method not in [None, b"GET ", b"HEAD", b"POST", b"PUT ", b"OPTI"]:
            if self.sr:
                self.log("\033[1;31mTODO: cannot do https in jython\033[0m")
                return

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

        if not self.sr:
            self.sr = Unrecv(self.s)

        while True:
            cli = HttpCli(self)
            if not cli.run():
                return

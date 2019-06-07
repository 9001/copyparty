#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import os
import jinja2

from .__init__ import E
from .util import Unrecv
from .httpcli import HttpCli


class HttpConn(object):
    """
    spawned by HttpSrv to handle an incoming client connection,
    creates an HttpCli for each request (Connection: Keep-Alive)
    """

    def __init__(self, sck, addr, args, auth, log_func):
        self.s = sck
        self.addr = addr
        self.args = args
        self.auth = auth

        self.sr = Unrecv(sck)
        self.workload = 0
        self.ok = True

        self.log_func = log_func
        self.log_src = "{} \033[36m{}".format(addr[0], addr[1]).ljust(26)

        self.tpl_mounts = self.load_tpl("splash.html")
        self.tpl_browser = self.load_tpl("browser.html")

    def load_tpl(self, fn):
        with open(self.respath(fn), "rb") as f:
            return jinja2.Template(f.read().decode("utf-8"))

    def respath(self, res_name):
        return os.path.join(E.mod, "web", res_name)

    def run(self):
        while True:
            cli = HttpCli(self)
            if not cli.run():
                self.s.close()
                return

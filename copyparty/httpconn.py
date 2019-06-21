#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

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

        self.log_func = log_func
        self.log_src = "{} \033[36m{}".format(addr[0], addr[1]).ljust(26)

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(E.mod, "web"))
        self.tpl_mounts = env.get_template("splash.html")
        self.tpl_browser = env.get_template("browser.html")
        self.tpl_msg = env.get_template("msg.html")

    def respath(self, res_name):
        return os.path.join(E.mod, "web", res_name)

    def run(self):
        while True:
            cli = HttpCli(self)
            if not cli.run():
                self.s.close()
                return

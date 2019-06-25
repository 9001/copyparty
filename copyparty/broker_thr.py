#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import threading

from .httpsrv import HttpSrv


class BrokerThr(object):
    """external api; behaves like BrokerMP but using plain threads"""

    def __init__(self, hub):
        self.hub = hub
        self.log = hub.log
        self.args = hub.args

        self.mutex = threading.Lock()

        self.httpsrv = HttpSrv(self.args, self.log)
        self.httpsrv.disconnect_func = self.httpdrop

    def shutdown(self):
        # self.log("broker", "shutting down")
        pass

    def put(self, retq, act, *args):
        if act == "httpconn":
            sck, addr = args
            self.log(str(addr), "-" * 4 + "C-qpop")
            self.httpsrv.accept(sck, addr)

        else:
            raise Exception("what is " + str(act))

    def httpdrop(self, addr):
        self.hub.tcpsrv.num_clients.add(-1)

#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import threading

from .httpcli import *
from .authsrv import *


class HttpSrv(object):
    """
    handles incoming connections (parses http and produces responses)
    relying on MpSrv for performance (HttpSrv is just plain threads)
    """

    def __init__(self, args, log_func):
        self.log = log_func
        self.args = args

        self.disconnect_func = None
        self.mutex = threading.Lock()

        self.clients = {}
        self.workload = 0
        self.workload_thr_alive = False
        self.auth = AuthSrv(args, log_func)

    def accept(self, sck, addr):
        """takes an incoming tcp connection and creates a thread to handle it"""
        thr = threading.Thread(target=self.thr_client, args=(sck, addr, self.log))
        thr.daemon = True
        thr.start()

    def num_clients(self):
        with self.mutex:
            return len(self.clients)

    def shutdown(self):
        print("ok bye")

    def thr_client(self, sck, addr, log):
        """thread managing one tcp client"""
        try:
            cli = HttpCli(sck, addr, self.args, log)
            with self.mutex:
                self.clients[cli] = 0
                self.workload += 50

                if not self.workload_thr_alive:
                    self.workload_thr_alive = True
                    thr = threading.Thread(target=self.thr_workload)
                    thr.daemon = True
                    thr.start()

            cli.run()

        finally:
            with self.mutex:
                del self.clients[cli]

            if self.disconnect_func:
                self.disconnect_func(addr)

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

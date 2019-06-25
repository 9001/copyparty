#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import sys
import time
import signal
import threading

from .__init__ import PY2, WINDOWS
from .httpsrv import HttpSrv

if PY2 and not WINDOWS:
    import pickle  # nosec


class MpWorker(object):
    """one single mp instance"""

    def __init__(self, q_pend, q_yield, args, n):
        self.q_pend = q_pend
        self.q_yield = q_yield
        self.args = args
        self.n = n

        self.mutex = threading.Lock()
        self.workload_thr_active = False

        # we inherited signal_handler from parent,
        # replace it with something harmless
        signal.signal(signal.SIGINT, self.signal_handler)

        self.httpsrv = HttpSrv(self.args, self.log)
        self.httpsrv.disconnect_func = self.httpdrop

        # on winxp and some other platforms,
        # use thr.join() to block all signals
        thr = threading.Thread(target=self.main)
        thr.daemon = True
        thr.start()
        thr.join()

    def signal_handler(self, signal, frame):
        # print('k')
        pass

    def log(self, src, msg):
        self.q_yield.put(["log", src, msg])

    def logw(self, msg):
        self.log("mp{}".format(self.n), msg)

    def httpdrop(self, addr):
        self.q_yield.put(["httpdrop", addr])

    def main(self):
        while True:
            d = self.q_pend.get()

            # self.logw("work: [{}]".format(d[0]))
            if d[0] == "shutdown":
                self.logw("ok bye")
                sys.exit(0)
                return

            elif d[0] == "httpconn":
                sck = d[1]
                if PY2:
                    sck = pickle.loads(sck)  # nosec

                self.log(str(d[2]), "-" * 4 + "C-qpop")
                self.httpsrv.accept(sck, d[2])

                with self.mutex:
                    if not self.workload_thr_active:
                        self.workload_thr_alive = True
                        thr = threading.Thread(target=self.thr_workload)
                        thr.daemon = True
                        thr.start()

            else:
                raise Exception("what is " + str(d[0]))

    def thr_workload(self):
        """announce workloads to MpSrv (the mp controller / loadbalancer)"""
        # avoid locking in extract_filedata by tracking difference here
        while True:
            time.sleep(0.2)
            with self.mutex:
                if self.httpsrv.num_clients() == 0:
                    # no clients rn, termiante thread
                    self.workload_thr_alive = False
                    return

            self.q_yield.put(["workload", self.httpsrv.workload])

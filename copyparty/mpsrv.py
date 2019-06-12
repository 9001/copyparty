#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import sys
import time
import signal
import threading
import multiprocessing as mp

from .__init__ import PY2, WINDOWS
from .httpsrv import HttpSrv

if PY2 and not WINDOWS:
    from multiprocessing.reduction import ForkingPickler
    from StringIO import StringIO as MemesIO  # pylint: disable=import-error
    import pickle  # nosec


class MpWorker(object):
    """
    one single mp instance, wraps one HttpSrv,
    the HttpSrv api exposed to TcpSrv proxies like
    MpSrv -> (this) -> HttpSrv
    """

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

    def disconnect_cb(self, addr):
        self.q_yield.put(["dropclient", addr])

    def main(self):
        self.httpsrv = HttpSrv(self.args, self.log)
        self.httpsrv.disconnect_func = self.disconnect_cb

        while True:
            d = self.q_pend.get()

            # self.logw("work: [{}]".format(d[0]))
            if d[0] == "shutdown":
                self.logw("ok bye")
                sys.exit(0)
                return

            sck = d[1]
            if PY2:
                sck = pickle.loads(sck)  # nosec

            self.httpsrv.accept(sck, d[2])

            with self.mutex:
                if not self.workload_thr_active:
                    self.workload_thr_alive = True
                    thr = threading.Thread(target=self.thr_workload)
                    thr.daemon = True
                    thr.start()

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


class MpSrv(object):
    """
    same api as HttpSrv except uses multiprocessing to dodge gil,
    a collection of MpWorkers are made (one per subprocess)
    and each MpWorker creates one actual HttpSrv
    """

    def __init__(self, args, log_func):
        self.log = log_func
        self.args = args

        self.disconnect_func = None
        self.mutex = threading.Lock()

        self.procs = []

        cores = args.j
        if cores is None:
            cores = mp.cpu_count()

        self.log("mpsrv", "booting {} subprocesses".format(cores))
        for n in range(cores):
            q_pend = mp.Queue(1)
            q_yield = mp.Queue(64)

            proc = mp.Process(target=MpWorker, args=(q_pend, q_yield, args, n))
            proc.q_pend = q_pend
            proc.q_yield = q_yield
            proc.nid = n
            proc.clients = {}
            proc.workload = 0

            thr = threading.Thread(target=self.collector, args=(proc,))
            thr.daemon = True
            thr.start()

            self.procs.append(proc)
            proc.start()

        if True:
            thr = threading.Thread(target=self.debug_load_balancer)
            thr.daemon = True
            thr.start()

    def num_clients(self):
        with self.mutex:
            return sum(len(x.clients) for x in self.procs)

    def shutdown(self):
        self.log("mpsrv", "shutting down")
        for proc in self.procs:
            thr = threading.Thread(target=proc.q_pend.put(["shutdown"]))
            thr.start()

        with self.mutex:
            procs = self.procs
            self.procs = []

        while procs:
            if procs[-1].is_alive():
                time.sleep(0.1)
                continue

            procs.pop()

    def collector(self, proc):
        while True:
            msg = proc.q_yield.get()
            k = msg[0]

            if k == "log":
                self.log(*msg[1:])

            if k == "workload":
                with self.mutex:
                    proc.workload = msg[1]

            if k == "dropclient":
                addr = msg[1]

                with self.mutex:
                    del proc.clients[addr]
                    if not proc.clients:
                        proc.workload = 0

                if self.disconnect_func:
                    self.disconnect_func(addr)  # pylint: disable=not-callable

    def accept(self, sck, addr):
        proc = sorted(self.procs, key=lambda x: x.workload)[0]

        sck2 = sck
        if PY2:
            buf = MemesIO()
            ForkingPickler(buf).dump(sck)
            sck2 = buf.getvalue()

        proc.q_pend.put(["socket", sck2, addr])

        with self.mutex:
            proc.clients[addr] = 50
            proc.workload += 50

    def debug_load_balancer(self):
        last = ""
        while self.procs:
            msg = ""
            for proc in self.procs:
                msg += "\033[1m{}\033[0;36m{:4}\033[0m ".format(
                    len(proc.clients), proc.workload
                )

            if msg != last:
                last = msg
                print(msg)

            time.sleep(0.1)

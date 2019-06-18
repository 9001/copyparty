#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import time
import threading
import multiprocessing as mp

from .__init__ import PY2, WINDOWS
from .broker_mpw import MpWorker


if PY2 and not WINDOWS:
    from multiprocessing.reduction import ForkingPickler
    from StringIO import StringIO as MemesIO  # pylint: disable=import-error


class BrokerMp(object):
    """external api; manages MpWorkers"""

    def __init__(self, hub):
        self.hub = hub
        self.log = hub.log
        self.args = hub.args

        self.mutex = threading.Lock()

        self.procs = []

        cores = self.args.j
        if cores is None:
            cores = mp.cpu_count()

        self.log("broker", "booting {} subprocesses".format(cores))
        for n in range(cores):
            q_pend = mp.Queue(1)
            q_yield = mp.Queue(64)

            proc = mp.Process(target=MpWorker, args=(q_pend, q_yield, self.args, n))
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

    def shutdown(self):
        self.log("broker", "shutting down")
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

            elif k == "workload":
                with self.mutex:
                    proc.workload = msg[1]

            elif k == "httpdrop":
                addr = msg[1]

                with self.mutex:
                    del proc.clients[addr]
                    if not proc.clients:
                        proc.workload = 0

                self.hub.tcpsrv.num_clients.add(-1)

    def put(self, retq, act, *args):
        if act == "httpconn":
            sck, addr = args
            sck2 = sck
            if PY2:
                buf = MemesIO()
                ForkingPickler(buf).dump(sck)
                sck2 = buf.getvalue()

            proc = sorted(self.procs, key=lambda x: x.workload)[0]
            proc.q_pend.put(["httpconn", sck2, addr])

            with self.mutex:
                proc.clients[addr] = 50
                proc.workload += 50
        else:
            raise Exception("what is " + str(act))

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

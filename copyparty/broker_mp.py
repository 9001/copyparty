# coding: utf-8
from __future__ import print_function, unicode_literals

import time
import threading

from .__init__ import PY2, WINDOWS, VT100
from .broker_util import try_exec
from .broker_mpw import MpWorker
from .util import mp


if PY2 and not WINDOWS:
    from multiprocessing.reduction import ForkingPickler
    from StringIO import StringIO as MemesIO  # pylint: disable=import-error


class BrokerMp(object):
    """external api; manages MpWorkers"""

    def __init__(self, hub):
        self.hub = hub
        self.log = hub.log
        self.args = hub.args

        self.procs = []
        self.retpend = {}
        self.retpend_mutex = threading.Lock()
        self.mutex = threading.Lock()

        cores = self.args.j
        if not cores:
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
            thr = threading.Thread(target=proc.q_pend.put([0, "shutdown", []]))
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
        """receive message from hub in other process"""
        while True:
            msg = proc.q_yield.get()
            retq_id, dest, args = msg

            if dest == "log":
                self.log(*args)

            elif dest == "workload":
                with self.mutex:
                    proc.workload = args[0]

            elif dest == "httpdrop":
                addr = args[0]

                with self.mutex:
                    del proc.clients[addr]
                    if not proc.clients:
                        proc.workload = 0

                self.hub.tcpsrv.num_clients.add(-1)

            elif dest == "retq":
                # response from previous ipc call
                with self.retpend_mutex:
                    retq = self.retpend.pop(retq_id)

                retq.put(args)

            else:
                # new ipc invoking managed service in hub
                obj = self.hub
                for node in dest.split("."):
                    obj = getattr(obj, node)

                # TODO will deadlock if dest performs another ipc
                rv = try_exec(retq_id, obj, *args)

                if retq_id:
                    proc.q_pend.put([retq_id, "retq", rv])

    def put(self, want_retval, dest, *args):
        """
        send message to non-hub component in other process,
        returns a Queue object which eventually contains the response if want_retval
        (not-impl here since nothing uses it yet)
        """
        if dest == "httpconn":
            sck, addr = args
            sck2 = sck
            if PY2:
                buf = MemesIO()
                ForkingPickler(buf).dump(sck)
                sck2 = buf.getvalue()

            proc = sorted(self.procs, key=lambda x: x.workload)[0]
            proc.q_pend.put([0, dest, [sck2, addr]])

            with self.mutex:
                proc.clients[addr] = 50
                proc.workload += 50

        else:
            raise Exception("what is " + str(dest))

    def debug_load_balancer(self):
        fmt = "\033[1m{}\033[0;36m{:4}\033[0m "
        if not VT100:
            fmt = "({}{:4})"

        last = ""
        while self.procs:
            msg = ""
            for proc in self.procs:
                msg += fmt.format(len(proc.clients), proc.workload)

            if msg != last:
                last = msg
                with self.hub.log_mutex:
                    print(msg)

            time.sleep(0.1)

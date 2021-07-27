# coding: utf-8
from __future__ import print_function, unicode_literals

import time
import threading

from .broker_util import try_exec
from .broker_mpw import MpWorker
from .util import mp


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

        self.num_workers = self.args.j or mp.cpu_count()
        self.log("broker", "booting {} subprocesses".format(self.num_workers))
        for n in range(1, self.num_workers + 1):
            q_pend = mp.Queue(1)
            q_yield = mp.Queue(64)

            proc = mp.Process(target=MpWorker, args=(q_pend, q_yield, self.args, n))
            proc.q_pend = q_pend
            proc.q_yield = q_yield
            proc.clients = {}

            thr = threading.Thread(
                target=self.collector, args=(proc,), name="mp-sink-{}".format(n)
            )
            thr.daemon = True
            thr.start()

            self.procs.append(proc)
            proc.start()

    def shutdown(self):
        self.log("broker", "shutting down")
        for n, proc in enumerate(self.procs):
            thr = threading.Thread(
                target=proc.q_pend.put([0, "shutdown", []]),
                name="mp-shutdown-{}-{}".format(n, len(self.procs)),
            )
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
        if dest == "listen":
            for p in self.procs:
                p.q_pend.put([0, dest, [args[0], len(self.procs)]])

        elif dest == "cb_httpsrv_up":
            self.hub.cb_httpsrv_up()

        else:
            raise Exception("what is " + str(dest))

# coding: utf-8
from __future__ import print_function, unicode_literals

import threading
import time

import queue

from .__init__ import CORES, TYPE_CHECKING
from .broker_mpw import MpWorker
from .broker_util import try_exec
from .util import Daemon, mp

if TYPE_CHECKING:
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Any


class MProcess(mp.Process):
    def __init__(
        self,
        q_pend: queue.Queue[tuple[int, str, list[Any]]],
        q_yield: queue.Queue[tuple[int, str, list[Any]]],
        target: Any,
        args: Any,
    ) -> None:
        super(MProcess, self).__init__(target=target, args=args)
        self.q_pend = q_pend
        self.q_yield = q_yield


class BrokerMp(object):
    """external api; manages MpWorkers"""

    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.log = hub.log
        self.args = hub.args

        self.procs = []
        self.mutex = threading.Lock()

        self.num_workers = self.args.j or CORES
        self.log("broker", "booting {} subprocesses".format(self.num_workers))
        for n in range(1, self.num_workers + 1):
            q_pend: queue.Queue[tuple[int, str, list[Any]]] = mp.Queue(1)
            q_yield: queue.Queue[tuple[int, str, list[Any]]] = mp.Queue(64)

            proc = MProcess(q_pend, q_yield, MpWorker, (q_pend, q_yield, self.args, n))
            Daemon(self.collector, "mp-sink-{}".format(n), (proc,))
            self.procs.append(proc)
            proc.start()

    def shutdown(self) -> None:
        self.log("broker", "shutting down")
        for n, proc in enumerate(self.procs):
            thr = threading.Thread(
                target=proc.q_pend.put((0, "shutdown", [])),
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

    def reload(self) -> None:
        self.log("broker", "reloading")
        for _, proc in enumerate(self.procs):
            proc.q_pend.put((0, "reload", []))

    def collector(self, proc: MProcess) -> None:
        """receive message from hub in other process"""
        while True:
            msg = proc.q_yield.get()
            retq_id, dest, args = msg

            if dest == "log":
                self.log(*args)

            elif dest == "retq":
                # response from previous ipc call
                raise Exception("invalid broker_mp usage")

            else:
                # new ipc invoking managed service in hub
                obj = self.hub
                for node in dest.split("."):
                    obj = getattr(obj, node)

                # TODO will deadlock if dest performs another ipc
                rv = try_exec(retq_id, obj, *args)

                if retq_id:
                    proc.q_pend.put((retq_id, "retq", rv))

    def say(self, dest: str, *args: Any) -> None:
        """
        send message to non-hub component in other process,
        returns a Queue object which eventually contains the response if want_retval
        (not-impl here since nothing uses it yet)
        """
        if dest == "listen":
            for p in self.procs:
                p.q_pend.put((0, dest, [args[0], len(self.procs)]))

        elif dest == "cb_httpsrv_up":
            self.hub.cb_httpsrv_up()

        else:
            raise Exception("what is " + str(dest))

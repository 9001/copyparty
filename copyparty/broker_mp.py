# coding: utf-8
from __future__ import print_function, unicode_literals

import threading
import time
import traceback

import queue

from .__init__ import CORES, TYPE_CHECKING
from .broker_mpw import MpWorker
from .broker_util import ExceptionalQueue, NotExQueue, try_exec
from .util import Daemon, mp

if TYPE_CHECKING:
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Any, Union


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

        self.retpend: dict[int, Any] = {}
        self.retpend_mutex = threading.Lock()

        self.num_workers = self.args.j or CORES
        self.log("broker", "booting {} subprocesses".format(self.num_workers))
        for n in range(1, self.num_workers + 1):
            q_pend: queue.Queue[tuple[int, str, list[Any]]] = mp.Queue(1)  # type: ignore
            q_yield: queue.Queue[tuple[int, str, list[Any]]] = mp.Queue(64)  # type: ignore

            proc = MProcess(q_pend, q_yield, MpWorker, (q_pend, q_yield, self.args, n))
            Daemon(self.collector, "mp-sink-{}".format(n), (proc,))
            self.procs.append(proc)
            proc.start()

        Daemon(self.periodic, "mp-periodic")

    def shutdown(self) -> None:
        self.log("broker", "shutting down")
        for n, proc in enumerate(self.procs):
            name = "mp-shut-%d-%d" % (n, len(self.procs))
            Daemon(proc.q_pend.put, name, ((0, "shutdown", []),))

        with self.mutex:
            procs = self.procs
            self.procs = []

        while procs:
            if procs[-1].is_alive():
                time.sleep(0.05)
                continue

            procs.pop()

    def reload(self) -> None:
        self.log("broker", "reloading")
        for _, proc in enumerate(self.procs):
            proc.q_pend.put((0, "reload", []))

    def reload_sessions(self) -> None:
        for _, proc in enumerate(self.procs):
            proc.q_pend.put((0, "reload_sessions", []))

    def collector(self, proc: MProcess) -> None:
        """receive message from hub in other process"""
        while True:
            msg = proc.q_yield.get()
            retq_id, dest, args = msg

            if dest == "log":
                self.log(*args)

            elif dest == "retq":
                with self.retpend_mutex:
                    retq = self.retpend.pop(retq_id)

                retq.put(args[0])

            else:
                # new ipc invoking managed service in hub
                try:
                    obj = self.hub
                    for node in dest.split("."):
                        obj = getattr(obj, node)

                    # TODO will deadlock if dest performs another ipc
                    rv = try_exec(retq_id, obj, *args)
                except:
                    rv = ["exception", "stack", traceback.format_exc()]

                if retq_id:
                    proc.q_pend.put((retq_id, "retq", rv))

    def ask(self, dest: str, *args: Any) -> Union[ExceptionalQueue, NotExQueue]:
        # new non-ipc invoking managed service in hub
        obj = self.hub
        for node in dest.split("."):
            obj = getattr(obj, node)

        rv = try_exec(True, obj, *args)

        retq = ExceptionalQueue(1)
        retq.put(rv)
        return retq

    def wask(self, dest: str, *args: Any) -> list[Union[ExceptionalQueue, NotExQueue]]:
        # call from hub to workers
        ret = []
        for p in self.procs:
            retq = ExceptionalQueue(1)
            retq_id = id(retq)
            with self.retpend_mutex:
                self.retpend[retq_id] = retq

            p.q_pend.put((retq_id, dest, list(args)))
            ret.append(retq)
        return ret

    def say(self, dest: str, *args: Any) -> None:
        """
        send message to non-hub component in other process,
        returns a Queue object which eventually contains the response if want_retval
        (not-impl here since nothing uses it yet)
        """
        if dest == "httpsrv.listen":
            for p in self.procs:
                p.q_pend.put((0, dest, [args[0], len(self.procs)]))

        elif dest == "httpsrv.set_netdevs":
            for p in self.procs:
                p.q_pend.put((0, dest, list(args)))

        elif dest == "cb_httpsrv_up":
            self.hub.cb_httpsrv_up()

        elif dest == "httpsrv.set_bad_ver":
            for p in self.procs:
                p.q_pend.put((0, dest, list(args)))

        else:
            raise Exception("what is " + str(dest))

    def periodic(self) -> None:
        while True:
            time.sleep(1)

            tdli = {}
            tdls = {}
            qs = self.wask("httpsrv.read_dls")
            for q in qs:
                qr = q.get()
                dli, dls = qr
                tdli.update(dli)
                tdls.update(dls)
            tdl = (tdli, tdls)
            for p in self.procs:
                p.q_pend.put((0, "httpsrv.write_dls", tdl))

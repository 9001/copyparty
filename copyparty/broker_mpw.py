# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import os
import signal
import sys
import threading

import queue

from .__init__ import ANYWIN
from .authsrv import AuthSrv
from .broker_util import BrokerCli, ExceptionalQueue, NotExQueue
from .fsutil import ramdisk_chk
from .httpsrv import HttpSrv
from .util import FAKE_MP, Daemon, HMaccas

if True:  # pylint: disable=using-constant-test
    from types import FrameType

    from typing import Any, Optional, Union


class MpWorker(BrokerCli):
    """one single mp instance"""

    def __init__(
        self,
        q_pend: queue.Queue[tuple[int, str, list[Any]]],
        q_yield: queue.Queue[tuple[int, str, list[Any]]],
        args: argparse.Namespace,
        n: int,
    ) -> None:
        super(MpWorker, self).__init__()

        self.q_pend = q_pend
        self.q_yield = q_yield
        self.args = args
        self.n = n

        self.log = self._log_disabled if args.q and not args.lo else self._log_enabled

        self.retpend: dict[int, Any] = {}
        self.retpend_mutex = threading.Lock()
        self.mutex = threading.Lock()

        # we inherited signal_handler from parent,
        # replace it with something harmless
        if not FAKE_MP:
            sigs = [signal.SIGINT, signal.SIGTERM]
            if not ANYWIN:
                sigs.append(signal.SIGUSR1)

            for sig in sigs:
                signal.signal(sig, self.signal_handler)

        # starting to look like a good idea
        self.asrv = AuthSrv(args, None, False)
        ramdisk_chk(self.asrv)

        # instantiate all services here (TODO: inheritance?)
        self.iphash = HMaccas(os.path.join(self.args.E.cfg, "iphash"), 8)
        self.httpsrv = HttpSrv(self, n)

        # on winxp and some other platforms,
        # use thr.join() to block all signals
        Daemon(self.main, "mpw-main").join()

    def signal_handler(self, sig: Optional[int], frame: Optional[FrameType]) -> None:
        # print('k')
        pass

    def _log_enabled(self, src: str, msg: str, c: Union[int, str] = 0) -> None:
        self.q_yield.put((0, "log", [src, msg, c]))

    def _log_disabled(self, src: str, msg: str, c: Union[int, str] = 0) -> None:
        pass

    def logw(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log("mp%d" % (self.n,), msg, c)

    def main(self) -> None:
        while True:
            retq_id, dest, args = self.q_pend.get()

            if dest == "retq":
                # response from previous ipc call
                with self.retpend_mutex:
                    retq = self.retpend.pop(retq_id)

                retq.put(args)
                continue

            if dest == "shutdown":
                self.httpsrv.shutdown()
                self.logw("ok bye")
                sys.exit(0)
                return

            if dest == "reload":
                self.logw("mpw.asrv reloading")
                self.asrv.reload()
                ramdisk_chk(self.asrv)
                self.logw("mpw.asrv reloaded")
                continue

            if dest == "reload_sessions":
                with self.asrv.mutex:
                    self.asrv.load_sessions()
                continue

            obj = self
            for node in dest.split("."):
                obj = getattr(obj, node)

            rv = obj(*args)  # type: ignore
            if retq_id:
                self.say("retq", rv, retq_id=retq_id)

    def ask(self, dest: str, *args: Any) -> Union[ExceptionalQueue, NotExQueue]:
        retq = ExceptionalQueue(1)
        retq_id = id(retq)
        with self.retpend_mutex:
            self.retpend[retq_id] = retq

        self.q_yield.put((retq_id, dest, list(args)))
        return retq

    def say(self, dest: str, *args: Any, retq_id=0) -> None:
        self.q_yield.put((retq_id, dest, list(args)))

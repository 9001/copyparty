# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import threading

from .__init__ import TYPE_CHECKING
from .broker_util import BrokerCli, ExceptionalQueue, try_exec
from .httpsrv import HttpSrv
from .util import HMaccas

if TYPE_CHECKING:
    from .svchub import SvcHub

try:
    from typing import Any
except:
    pass


class BrokerThr(BrokerCli):
    """external api; behaves like BrokerMP but using plain threads"""

    def __init__(self, hub: "SvcHub") -> None:
        super(BrokerThr, self).__init__()

        self.hub = hub
        self.log = hub.log
        self.args = hub.args
        self.asrv = hub.asrv

        self.mutex = threading.Lock()
        self.num_workers = 1

        # instantiate all services here (TODO: inheritance?)
        self.iphash = HMaccas(os.path.join(self.args.E.cfg, "iphash"), 8)
        self.httpsrv = HttpSrv(self, None)
        self.reload = self.noop

    def shutdown(self) -> None:
        # self.log("broker", "shutting down")
        self.httpsrv.shutdown()

    def noop(self) -> None:
        pass

    def ask(self, dest: str, *args: Any) -> ExceptionalQueue:

        # new ipc invoking managed service in hub
        obj = self.hub
        for node in dest.split("."):
            obj = getattr(obj, node)

        rv = try_exec(True, obj, *args)

        # pretend we're broker_mp
        retq = ExceptionalQueue(1)
        retq.put(rv)
        return retq

    def say(self, dest: str, *args: Any) -> None:
        if dest == "listen":
            self.httpsrv.listen(args[0], 1)
            return

        # new ipc invoking managed service in hub
        obj = self.hub
        for node in dest.split("."):
            obj = getattr(obj, node)

        try_exec(False, obj, *args)

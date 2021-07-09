# coding: utf-8
from __future__ import print_function, unicode_literals

import threading

from .httpsrv import HttpSrv
from .broker_util import ExceptionalQueue, try_exec


class BrokerThr(object):
    """external api; behaves like BrokerMP but using plain threads"""

    def __init__(self, hub):
        self.hub = hub
        self.log = hub.log
        self.args = hub.args
        self.asrv = hub.asrv

        self.mutex = threading.Lock()

        # instantiate all services here (TODO: inheritance?)
        self.httpsrv = HttpSrv(self)

    def shutdown(self):
        # self.log("broker", "shutting down")
        self.httpsrv.shutdown()
        pass

    def put(self, want_retval, dest, *args):
        if dest == "listen":
            self.httpsrv.listen(args[0], 1)

        else:
            # new ipc invoking managed service in hub
            obj = self.hub
            for node in dest.split("."):
                obj = getattr(obj, node)

            # TODO will deadlock if dest performs another ipc
            rv = try_exec(want_retval, obj, *args)
            if not want_retval:
                return

            # pretend we're broker_mp
            retq = ExceptionalQueue(1)
            retq.put(rv)
            return retq

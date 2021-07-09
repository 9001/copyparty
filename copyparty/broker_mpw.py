# coding: utf-8
from __future__ import print_function, unicode_literals
from copyparty.authsrv import AuthSrv

import sys
import signal
import threading

from .broker_util import ExceptionalQueue
from .httpsrv import HttpSrv
from .util import FAKE_MP


class MpWorker(object):
    """one single mp instance"""

    def __init__(self, q_pend, q_yield, args, n):
        self.q_pend = q_pend
        self.q_yield = q_yield
        self.args = args
        self.n = n

        self.log = self._log_disabled if args.q and not args.lo else self._log_enabled

        self.retpend = {}
        self.retpend_mutex = threading.Lock()
        self.mutex = threading.Lock()

        # we inherited signal_handler from parent,
        # replace it with something harmless
        if not FAKE_MP:
            signal.signal(signal.SIGINT, self.signal_handler)

        # starting to look like a good idea
        self.asrv = AuthSrv(args, None, False)

        # instantiate all services here (TODO: inheritance?)
        self.httpsrv = HttpSrv(self, True)

        # on winxp and some other platforms,
        # use thr.join() to block all signals
        thr = threading.Thread(target=self.main, name="mpw-main")
        thr.daemon = True
        thr.start()
        thr.join()

    def signal_handler(self, signal, frame):
        # print('k')
        pass

    def _log_enabled(self, src, msg, c=0):
        self.q_yield.put([0, "log", [src, msg, c]])

    def _log_disabled(self, src, msg, c=0):
        pass

    def logw(self, msg, c=0):
        self.log("mp{}".format(self.n), msg, c)

    def main(self):
        while True:
            retq_id, dest, args = self.q_pend.get()

            # self.logw("work: [{}]".format(d[0]))
            if dest == "shutdown":
                self.httpsrv.shutdown()
                self.logw("ok bye")
                sys.exit(0)
                return

            elif dest == "listen":
                self.httpsrv.listen(args[0], args[1])

            elif dest == "retq":
                # response from previous ipc call
                with self.retpend_mutex:
                    retq = self.retpend.pop(retq_id)

                retq.put(args)

            else:
                raise Exception("what is " + str(dest))

    def put(self, want_retval, dest, *args):
        if want_retval:
            retq = ExceptionalQueue(1)
            retq_id = id(retq)
            with self.retpend_mutex:
                self.retpend[retq_id] = retq
        else:
            retq = None
            retq_id = 0

        self.q_yield.put([retq_id, dest, args])
        return retq

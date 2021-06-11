# coding: utf-8
from __future__ import print_function, unicode_literals
from copyparty.authsrv import AuthSrv

import sys
import time
import signal
import threading

from .__init__ import PY2, WINDOWS
from .broker_util import ExceptionalQueue
from .httpsrv import HttpSrv
from .util import FAKE_MP

if PY2 and not WINDOWS:
    import pickle  # nosec


class MpWorker(object):
    """one single mp instance"""

    def __init__(self, q_pend, q_yield, args, n):
        self.q_pend = q_pend
        self.q_yield = q_yield
        self.args = args
        self.n = n

        self.retpend = {}
        self.retpend_mutex = threading.Lock()
        self.mutex = threading.Lock()
        self.workload_thr_alive = False

        # we inherited signal_handler from parent,
        # replace it with something harmless
        if not FAKE_MP:
            signal.signal(signal.SIGINT, self.signal_handler)

        # starting to look like a good idea
        self.asrv = AuthSrv(args, None, False)

        # instantiate all services here (TODO: inheritance?)
        self.httpsrv = HttpSrv(self, True)
        self.httpsrv.disconnect_func = self.httpdrop

        # on winxp and some other platforms,
        # use thr.join() to block all signals
        thr = threading.Thread(target=self.main, name="mpw-main")
        thr.daemon = True
        thr.start()
        thr.join()

    def signal_handler(self, signal, frame):
        # print('k')
        pass

    def log(self, src, msg, c=0):
        self.q_yield.put([0, "log", [src, msg, c]])

    def logw(self, msg, c=0):
        self.log("mp{}".format(self.n), msg, c)

    def httpdrop(self, addr):
        self.q_yield.put([0, "httpdrop", [addr]])

    def main(self):
        while True:
            retq_id, dest, args = self.q_pend.get()

            # self.logw("work: [{}]".format(d[0]))
            if dest == "shutdown":
                self.logw("ok bye")
                sys.exit(0)
                return

            elif dest == "httpconn":
                sck, addr = args
                if PY2:
                    sck = pickle.loads(sck)  # nosec

                if self.args.log_conn:
                    self.log("%s %s" % addr, "|%sC-qpop" % ("-" * 4,), c="1;30")

                self.httpsrv.accept(sck, addr)

                with self.mutex:
                    if not self.workload_thr_alive:
                        self.workload_thr_alive = True
                        thr = threading.Thread(
                            target=self.thr_workload, name="mpw-workload"
                        )
                        thr.daemon = True
                        thr.start()

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

            self.q_yield.put([0, "workload", [self.httpsrv.workload]])

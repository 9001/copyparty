# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import time
import socket
import threading

from .__init__ import E, MACOS
from .httpconn import HttpConn
from .authsrv import AuthSrv


class HttpSrv(object):
    """
    handles incoming connections using HttpConn to process http,
    relying on MpSrv for performance (HttpSrv is just plain threads)
    """

    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args
        self.log = broker.log

        self.disconnect_func = None
        self.mutex = threading.Lock()

        self.clients = {}
        self.workload = 0
        self.workload_thr_alive = False
        self.auth = AuthSrv(self.args, self.log)

        cert_path = os.path.join(E.cfg, "cert.pem")
        if os.path.exists(cert_path):
            self.cert_path = cert_path
        else:
            self.cert_path = None

    def accept(self, sck, addr):
        """takes an incoming tcp connection and creates a thread to handle it"""
        self.log("%s %s" % addr, "\033[1;30m|%sC-cthr\033[0m" % ("-" * 5,))
        thr = threading.Thread(target=self.thr_client, args=(sck, addr))
        thr.daemon = True
        thr.start()

    def num_clients(self):
        with self.mutex:
            return len(self.clients)

    def shutdown(self):
        self.log("ok bye")

    def thr_client(self, sck, addr):
        """thread managing one tcp client"""
        sck.settimeout(120)

        cli = HttpConn(sck, addr, self)
        with self.mutex:
            self.clients[cli] = 0
            self.workload += 50

            if not self.workload_thr_alive:
                self.workload_thr_alive = True
                thr = threading.Thread(target=self.thr_workload)
                thr.daemon = True
                thr.start()

        try:
            self.log("%s %s" % addr, "\033[1;30m|%sC-crun\033[0m" % ("-" * 6,))
            cli.run()

        finally:
            self.log("%s %s" % addr, "\033[1;30m|%sC-cdone\033[0m" % ("-" * 7,))
            try:
                sck.shutdown(socket.SHUT_RDWR)
                sck.close()
            except (OSError, socket.error) as ex:
                if not MACOS:
                    self.log(
                        "%s %s" % addr,
                        "shut_rdwr err:\n  {}\n  {}".format(repr(sck), ex),
                    )
                if ex.errno not in [10038, 10054, 107, 57, 9]:
                    # 10038 No longer considered a socket
                    # 10054 Foribly closed by remote
                    #   107 Transport endpoint not connected
                    #    57 Socket is not connected
                    #     9 Bad file descriptor
                    raise
            finally:
                with self.mutex:
                    del self.clients[cli]

                if self.disconnect_func:
                    self.disconnect_func(addr)  # pylint: disable=not-callable

    def thr_workload(self):
        """indicates the python interpreter workload caused by this HttpSrv"""
        # avoid locking in extract_filedata by tracking difference here
        while True:
            time.sleep(0.2)
            with self.mutex:
                if not self.clients:
                    # no clients rn, termiante thread
                    self.workload_thr_alive = False
                    self.workload = 0
                    return

            total = 0
            with self.mutex:
                for cli in self.clients.keys():
                    now = cli.workload
                    delta = now - self.clients[cli]
                    if delta < 0:
                        # was reset in HttpCli to prevent overflow
                        delta = now

                    total += delta
                    self.clients[cli] = now

            self.workload = total

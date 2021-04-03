# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import time
import socket
import threading

try:
    import jinja2
except ImportError:
    print(
        """\033[1;31m
  you do not have jinja2 installed,\033[33m
  choose one of these:\033[0m
   * apt install python-jinja2
   * {} -m pip install --user jinja2
   * (try another python version, if you have one)
   * (try copyparty.sfx instead)
""".format(
            os.path.basename(sys.executable)
        )
    )
    sys.exit(1)

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

        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.join(E.mod, "web"))
        self.j2 = {
            x: env.get_template(x + ".html")
            for x in ["splash", "browser", "browser2", "msg", "md", "mde"]
        }

        cert_path = os.path.join(E.cfg, "cert.pem")
        if os.path.exists(cert_path):
            self.cert_path = cert_path
        else:
            self.cert_path = None

    def accept(self, sck, addr):
        """takes an incoming tcp connection and creates a thread to handle it"""
        if self.args.log_conn:
            self.log("%s %s" % addr, "|%sC-cthr" % ("-" * 5,), c="1;30")

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
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-crun" % ("-" * 6,), c="1;30")

            cli.run()

        finally:
            if self.args.log_conn:
                self.log("%s %s" % addr, "|%sC-cdone" % ("-" * 7,), c="1;30")

            try:
                sck.shutdown(socket.SHUT_RDWR)
                sck.close()
            except (OSError, socket.error) as ex:
                if not MACOS:
                    self.log(
                        "%s %s" % addr,
                        "shut({}): {}".format(sck.fileno(), ex),
                        c="1;30",
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

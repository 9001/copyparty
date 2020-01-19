# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import time
import socket

from .util import chkcmd, Counter


class TcpSrv(object):
    """
    tcplistener which forwards clients to Hub
    which then uses the least busy HttpSrv to handle it
    """

    def __init__(self, hub):
        self.hub = hub
        self.args = hub.args
        self.log = hub.log

        self.num_clients = Counter()

        ip = "127.0.0.1"
        eps = {ip: "local only"}
        if self.args.i != ip:
            eps = self.detect_interfaces(self.args.i) or eps

        for ip, desc in sorted(eps.items(), key=lambda x: x[1]):
            self.log(
                "tcpsrv",
                "available @ http://{}:{}/  (\033[33m{}\033[0m)".format(
                    ip, self.args.p, desc
                ),
            )

        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.srv.bind((self.args.i, self.args.p))
        except (OSError, socket.error) as ex:
            if ex.errno == 98:
                raise Exception(
                    "\033[1;31mport {} is busy on interface {}\033[0m".format(
                        self.args.p, self.args.i
                    )
                )

            if ex.errno == 99:
                raise Exception(
                    "\033[1;31minterface {} does not exist\033[0m".format(self.args.i)
                )

    def run(self):
        self.srv.listen(self.args.nc)

        self.log("tcpsrv", "listening @ {0}:{1}".format(self.args.i, self.args.p))

        while True:
            self.log("tcpsrv", "-" * 1 + "C-ncli")
            if self.num_clients.v >= self.args.nc:
                time.sleep(0.1)
                continue

            self.log("tcpsrv", "-" * 2 + "C-acc1")
            sck, addr = self.srv.accept()
            self.log(str(addr), "-" * 3 + "C-acc2")
            self.num_clients.add()
            self.hub.broker.put(False, "httpconn", sck, addr)

    def shutdown(self):
        self.log("tcpsrv", "ok bye")

    def detect_interfaces(self, ext_ip):
        eps = {}

        # get all ips and their interfaces
        try:
            ip_addr, _ = chkcmd("ip", "addr")
        except:
            ip_addr = None

        if ip_addr:
            r = re.compile(r"^\s+inet ([^ ]+)/.* (.*)")
            for ln in ip_addr.split("\n"):
                try:
                    ip, dev = r.match(ln.rstrip()).groups()
                    if ext_ip in ["0.0.0.0", ip]:
                        eps[ip] = dev
                except:
                    pass

        # get ip with default route
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        except (OSError, socket.error) as ex:
            if ex.errno not in [101, 10065]:
                raise

            return None

        s.close()

        if ext_ip in ["0.0.0.0", ip]:
            desc = "\033[32mexternal"
            try:
                eps[ip] += ", " + desc
            except:
                eps[ip] = desc

        return eps

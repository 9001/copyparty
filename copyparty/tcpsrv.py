# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import time
import socket
import select

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
        nonlocals = [x for x in self.args.i if x != ip]
        if nonlocals:
            eps = self.detect_interfaces(self.args.i)
            if not eps:
                for x in nonlocals:
                    eps[x] = "external"

        for ip, desc in sorted(eps.items(), key=lambda x: x[1]):
            for port in sorted(self.args.p):
                self.log(
                    "tcpsrv",
                    "available @ http://{}:{}/  (\033[33m{}\033[0m)".format(
                        ip, port, desc
                    ),
                )

        self.srv = []
        for ip in self.args.i:
            for port in self.args.p:
                self.srv.append(self._listen(ip, port))

    def _listen(self, ip, port):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            srv.bind((ip, port))
            return srv
        except (OSError, socket.error) as ex:
            if ex.errno in [98, 48]:
                e = "\033[1;31mport {} is busy on interface {}\033[0m".format(port, ip)
            elif ex.errno in [99, 49]:
                e = "\033[1;31minterface {} does not exist\033[0m".format(ip)
            else:
                raise
            raise Exception(e)

    def run(self):
        for srv in self.srv:
            srv.listen(self.args.nc)
            ip, port = srv.getsockname()
            self.log("tcpsrv", "listening @ {0}:{1}".format(ip, port))

        while True:
            self.log("tcpsrv", "\033[1;30m|%sC-ncli\033[0m" % ("-" * 1,))
            if self.num_clients.v >= self.args.nc:
                time.sleep(0.1)
                continue

            self.log("tcpsrv", "\033[1;30m|%sC-acc1\033[0m" % ("-" * 2,))
            ready, _, _ = select.select(self.srv, [], [])
            for srv in ready:
                sck, addr = srv.accept()
                sip, sport = srv.getsockname()
                self.log(
                    "%s %s" % addr,
                    "\033[1;30m|{}C-acc2 \033[0;36m{} \033[3{}m{}".format(
                        "-" * 3, sip, sport % 8, sport
                    ),
                )
                self.num_clients.add()
                self.hub.broker.put(False, "httpconn", sck, addr)

    def shutdown(self):
        self.log("tcpsrv", "ok bye")

    def detect_interfaces(self, listen_ips):
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
                    for lip in listen_ips:
                        if lip in ["0.0.0.0", ip]:
                            eps[ip] = dev
                except:
                    pass

        default_route = None
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for ip in [
            "10.255.255.255",
            "172.31.255.255",
            "192.168.255.255",
            "239.255.255.255",
            # could add 1.1.1.1 as a final fallback
            # but external connections is kinshi
        ]:
            try:
                s.connect((ip, 1))
                # raise OSError(13, "a")
                default_route = s.getsockname()[0]
                break
            except (OSError, socket.error) as ex:
                if ex.errno == 13:
                    self.log("tcpsrv", "eaccess {} (trying next)".format(ip))
                elif ex.errno not in [101, 10065, 10051]:
                    self.log("tcpsrv", "route lookup failed; err {}".format(ex.errno))

        s.close()

        for lip in listen_ips:
            if default_route and lip in ["0.0.0.0", default_route]:
                desc = "\033[32mexternal"
                try:
                    eps[default_route] += ", " + desc
                except:
                    eps[default_route] = desc

        return eps

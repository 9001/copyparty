# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import socket

from .__init__ import MACOS, ANYWIN
from .util import chkcmd


class TcpSrv(object):
    """
    tcplistener which forwards clients to Hub
    which then uses the least busy HttpSrv to handle it
    """

    def __init__(self, hub):
        self.hub = hub
        self.args = hub.args
        self.log = hub.log

        self.stopping = False

        ip = "127.0.0.1"
        eps = {ip: "local only"}
        nonlocals = [x for x in self.args.i if x != ip]
        if nonlocals:
            eps = self.detect_interfaces(self.args.i)
            if not eps:
                for x in nonlocals:
                    eps[x] = "external"

        msgs = []
        m = "available @ http://{}:{}/  (\033[33m{}\033[0m)"
        for ip, desc in sorted(eps.items(), key=lambda x: x[1]):
            for port in sorted(self.args.p):
                msgs.append(m.format(ip, port, desc))

        if msgs:
            msgs[-1] += "\n"
            for m in msgs:
                self.log("tcpsrv", m)

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
            fno = srv.fileno()
            msg = "listening @ {}:{}  f{}".format(ip, port, fno)
            self.log("tcpsrv", msg)
            if self.args.q:
                print(msg)

            self.hub.broker.put(False, "listen", srv)

    def shutdown(self):
        self.stopping = True
        try:
            for srv in self.srv:
                srv.close()
        except:
            pass

        self.log("tcpsrv", "ok bye")

    def ips_linux(self):
        eps = {}
        try:
            txt, _ = chkcmd(["ip", "addr"])
        except:
            return eps

        r = re.compile(r"^\s+inet ([^ ]+)/.* (.*)")
        for ln in txt.split("\n"):
            try:
                ip, dev = r.match(ln.rstrip()).groups()
                eps[ip] = dev
            except:
                pass

        return eps

    def ips_macos(self):
        eps = {}
        try:
            txt, _ = chkcmd(["ifconfig"])
        except:
            return eps

        rdev = re.compile(r"^([^ ]+):")
        rip = re.compile(r"^\tinet ([0-9\.]+) ")
        dev = None
        for ln in txt.split("\n"):
            m = rdev.match(ln)
            if m:
                dev = m.group(1)

            m = rip.match(ln)
            if m:
                eps[m.group(1)] = dev
                dev = None

        return eps

    def ips_windows_ipconfig(self):
        eps = {}
        try:
            txt, _ = chkcmd(["ipconfig"])
        except:
            return eps

        rdev = re.compile(r"(^[^ ].*):$")
        rip = re.compile(r"^ +IPv?4? [^:]+: *([0-9\.]{7,15})$")
        dev = None
        for ln in txt.replace("\r", "").split("\n"):
            m = rdev.match(ln)
            if m:
                dev = m.group(1).split(" adapter ", 1)[-1]

            m = rip.match(ln)
            if m and dev:
                eps[m.group(1)] = dev
                dev = None

        return eps

    def ips_windows_netsh(self):
        eps = {}
        try:
            txt, _ = chkcmd("netsh interface ip show address".split())
        except:
            return eps

        rdev = re.compile(r'.* "([^"]+)"$')
        rip = re.compile(r".* IP\b.*: +([0-9\.]{7,15})$")
        dev = None
        for ln in txt.replace("\r", "").split("\n"):
            m = rdev.match(ln)
            if m:
                dev = m.group(1)

            m = rip.match(ln)
            if m and dev:
                eps[m.group(1)] = dev
                dev = None

        return eps

    def detect_interfaces(self, listen_ips):
        if MACOS:
            eps = self.ips_macos()
        elif ANYWIN:
            eps = self.ips_windows_ipconfig()  # sees more interfaces
            eps.update(self.ips_windows_netsh())  # has better names
        else:
            eps = self.ips_linux()

        if "0.0.0.0" not in listen_ips:
            eps = {k: v for k, v in eps if k in listen_ips}

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

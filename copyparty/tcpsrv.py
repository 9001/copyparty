# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import sys
import socket

from .__init__ import MACOS, ANYWIN, unicode
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

        self.srv = []
        self.nsrv = 0
        ok = {}
        for ip in self.args.i:
            ok[ip] = []
            for port in self.args.p:
                self.nsrv += 1
                try:
                    self._listen(ip, port)
                    ok[ip].append(port)
                except Exception as ex:
                    if self.args.ign_ebind or self.args.ign_ebind_all:
                        m = "could not listen on {}:{}: {}"
                        self.log("tcpsrv", m.format(ip, port, ex), c=3)
                    else:
                        raise

        if not self.srv and not self.args.ign_ebind_all:
            raise Exception("could not listen on any of the given interfaces")

        if self.nsrv != len(self.srv):
            self.log("tcpsrv", "")

        ip = "127.0.0.1"
        eps = {ip: "local only"}
        nonlocals = [x for x in self.args.i if x != ip]
        if nonlocals:
            eps = self.detect_interfaces(self.args.i)
            if not eps:
                for x in nonlocals:
                    eps[x] = "external"

        msgs = []
        title_tab = {}
        title_vars = [x[1:] for x in self.args.wintitle.split(" ") if x.startswith("$")]
        m = "available @ http://{}:{}/  (\033[33m{}\033[0m)"
        for ip, desc in sorted(eps.items(), key=lambda x: x[1]):
            for port in sorted(self.args.p):
                if port not in ok.get(ip, ok.get("0.0.0.0", [])):
                    continue

                msgs.append(m.format(ip, port, desc))

                if not self.args.wintitle:
                    continue

                if port in [80, 443]:
                    ep = ip
                else:
                    ep = "{}:{}".format(ip, port)

                hits = []
                if "pub" in title_vars and "external" in unicode(desc):
                    hits.append(("pub", ep))

                if "pub" in title_vars or "all" in title_vars:
                    hits.append(("all", ep))

                for var in title_vars:
                    if var.startswith("ip-") and ep.startswith(var[3:]):
                        hits.append((var, ep))

                for tk, tv in hits:
                    try:
                        title_tab[tk][tv] = 1
                    except:
                        title_tab[tk] = {tv: 1}

        if msgs:
            msgs[-1] += "\n"
            for m in msgs:
                self.log("tcpsrv", m)

        if self.args.wintitle:
            self._set_wintitle(title_tab)

    def _listen(self, ip, port):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            srv.bind((ip, port))
            self.srv.append(srv)
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
            eps = {k: v for k, v in eps.items() if k in listen_ips}

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

    def _set_wintitle(self, vars):
        vars["all"] = vars.get("all", {"Local-Only": 1})
        vars["pub"] = vars.get("pub", vars["all"])

        vars2 = {}
        for k, eps in vars.items():
            vars2[k] = {
                ep: 1
                for ep in eps.keys()
                if ":" not in ep or ep.split(":")[0] not in eps
            }

        title = ""
        vars = vars2
        for p in self.args.wintitle.split(" "):
            if p.startswith("$"):
                p = " and ".join(sorted(vars.get(p[1:], {"(None)": 1}).keys()))

            title += "{} ".format(p)

        print("\033]0;{}\033\\".format(title), file=sys.stderr, end="")
        sys.stderr.flush()

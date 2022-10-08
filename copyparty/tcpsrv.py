# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import re
import socket
import sys

from .__init__ import ANYWIN, MACOS, PY2, TYPE_CHECKING, VT100, unicode
from .stolen.qrcodegen import QrCode
from .util import chkcmd, sunpack, termsize

if TYPE_CHECKING:
    from .svchub import SvcHub


class TcpSrv(object):
    """
    tcplistener which forwards clients to Hub
    which then uses the least busy HttpSrv to handle it
    """

    def __init__(self, hub: "SvcHub"):
        self.hub = hub
        self.args = hub.args
        self.log = hub.log

        # mp-safe since issue6056
        socket.setdefaulttimeout(120)

        self.stopping = False
        self.srv: list[socket.socket] = []
        self.nsrv = 0
        self.qr = ""
        ok: dict[str, list[int]] = {}
        for ip in self.args.i:
            ok[ip] = []
            for port in self.args.p:
                self.nsrv += 1
                try:
                    self._listen(ip, port)
                    ok[ip].append(port)
                except Exception as ex:
                    if self.args.ign_ebind or self.args.ign_ebind_all:
                        t = "could not listen on {}:{}: {}"
                        self.log("tcpsrv", t.format(ip, port, ex), c=3)
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

        qr1 = {}
        qr2 = {}
        msgs = []
        title_tab: dict[str, dict[str, int]] = {}
        title_vars = [x[1:] for x in self.args.wintitle.split(" ") if x.startswith("$")]
        t = "available @ {}://{}:{}/  (\033[33m{}\033[0m)"
        for ip, desc in sorted(eps.items(), key=lambda x: x[1]):
            for port in sorted(self.args.p):
                if port not in ok.get(ip, ok.get("0.0.0.0", [])):
                    continue

                proto = " http"
                if self.args.http_only:
                    pass
                elif self.args.https_only or port == 443:
                    proto = "https"

                msgs.append(t.format(proto, ip, port, desc))

                is_ext = "external" in unicode(desc)
                qrt = qr1 if is_ext else qr2
                try:
                    qrt[ip].append(port)
                except:
                    qrt[ip] = [port]

                if not self.args.wintitle:
                    continue

                if port in [80, 443]:
                    ep = ip
                else:
                    ep = "{}:{}".format(ip, port)

                hits = []
                if "pub" in title_vars and is_ext:
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
            for t in msgs:
                self.log("tcpsrv", t)

        if self.args.wintitle:
            self._set_wintitle(title_tab)

        if self.args.qr or self.args.qrs:
            self.qr = self._qr(qr1, qr2)

    def _listen(self, ip: str, port: int) -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        srv.settimeout(None)  # < does not inherit, ^ does
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

    def run(self) -> None:
        for srv in self.srv:
            srv.listen(self.args.nc)
            ip, port = srv.getsockname()
            fno = srv.fileno()
            msg = "listening @ {}:{}  f{} p{}".format(ip, port, fno, os.getpid())
            self.log("tcpsrv", msg)
            if self.args.q:
                print(msg)

            self.hub.broker.say("listen", srv)

    def shutdown(self) -> None:
        self.stopping = True
        try:
            for srv in self.srv:
                srv.close()
        except:
            pass

        self.log("tcpsrv", "ok bye")

    def ips_linux_ifconfig(self) -> dict[str, str]:
        # for termux
        try:
            txt, _ = chkcmd(["ifconfig"])
        except:
            return {}

        eps: dict[str, str] = {}
        dev = None
        ip = None
        up = None
        for ln in (txt + "\n").split("\n"):
            if not ln.strip() and dev and ip:
                eps[ip] = dev + ("" if up else ", \033[31mLINK-DOWN")
                dev = ip = up = None
                continue

            if ln == ln.lstrip():
                dev = re.split(r"[: ]", ln)[0]

            if "UP" in re.split(r"[<>, \t]", ln):
                up = True

            m = re.match(r"^\s+inet\s+([^ ]+)", ln)
            if m:
                ip = m.group(1)

        return eps

    def ips_linux(self) -> dict[str, str]:
        try:
            txt, _ = chkcmd(["ip", "addr"])
        except:
            return self.ips_linux_ifconfig()

        r = re.compile(r"^\s+inet ([^ ]+)/.* (.*)")
        ri = re.compile(r"^\s*[0-9]+\s*:.*")
        up = False
        eps: dict[str, str] = {}
        for ln in txt.split("\n"):
            if ri.match(ln):
                up = "UP" in re.split("[>,< ]", ln)

            try:
                ip, dev = r.match(ln.rstrip()).groups()  # type: ignore
                eps[ip] = dev + ("" if up else ", \033[31mLINK-DOWN")
            except:
                pass

        return eps

    def ips_macos(self) -> dict[str, str]:
        eps: dict[str, str] = {}
        try:
            txt, _ = chkcmd(["ifconfig"])
        except:
            return eps

        rdev = re.compile(r"^([^ ]+):")
        rip = re.compile(r"^\tinet ([0-9\.]+) ")
        dev = "UNKNOWN"
        for ln in txt.split("\n"):
            m = rdev.match(ln)
            if m:
                dev = m.group(1)

            m = rip.match(ln)
            if m:
                eps[m.group(1)] = dev
                dev = "UNKNOWN"

        return eps

    def ips_windows_ipconfig(self) -> tuple[dict[str, str], set[str]]:
        eps: dict[str, str] = {}
        offs: set[str] = set()
        try:
            txt, _ = chkcmd(["ipconfig"])
        except:
            return eps, offs

        rdev = re.compile(r"(^[^ ].*):$")
        rip = re.compile(r"^ +IPv?4? [^:]+: *([0-9\.]{7,15})$")
        roff = re.compile(r".*: Media disconnected$")
        dev = None
        for ln in txt.replace("\r", "").split("\n"):
            m = rdev.match(ln)
            if m:
                if dev and dev not in eps.values():
                    offs.add(dev)

                dev = m.group(1).split(" adapter ", 1)[-1]

            if dev and roff.match(ln):
                offs.add(dev)
                dev = None

            m = rip.match(ln)
            if m and dev:
                eps[m.group(1)] = dev
                dev = None

        if dev and dev not in eps.values():
            offs.add(dev)

        return eps, offs

    def ips_windows_netsh(self) -> dict[str, str]:
        eps: dict[str, str] = {}
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

        return eps

    def detect_interfaces(self, listen_ips: list[str]) -> dict[str, str]:
        if MACOS:
            eps = self.ips_macos()
        elif ANYWIN:
            eps, off = self.ips_windows_ipconfig()  # sees more interfaces + link state
            eps.update(self.ips_windows_netsh())  # has better names
            for k, v in eps.items():
                if v in off:
                    eps[k] += ", \033[31mLINK-DOWN"
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

    def _set_wintitle(self, vs: dict[str, dict[str, int]]) -> None:
        vs["all"] = vs.get("all", {"Local-Only": 1})
        vs["pub"] = vs.get("pub", vs["all"])

        vs2 = {}
        for k, eps in vs.items():
            vs2[k] = {
                ep: 1
                for ep in eps.keys()
                if ":" not in ep or ep.split(":")[0] not in eps
            }

        title = ""
        vs = vs2
        for p in self.args.wintitle.split(" "):
            if p.startswith("$"):
                p = " and ".join(sorted(vs.get(p[1:], {"(None)": 1}).keys()))

            title += "{} ".format(p)

        print("\033]0;{}\033\\".format(title), file=sys.stderr, end="")
        sys.stderr.flush()

    def _qr(self, t1: dict[str, list[int]], t2: dict[str, list[int]]) -> str:
        ip = None
        for ip in list(t1) + list(t2):
            if ip.startswith(self.args.qr_ip):
                break
            ip = ""

        if not ip:
            # maybe /bin/ip is missing or smth
            ip = self.args.qr_ip

        if not ip:
            return ""

        if self.args.http_only:
            https = ""
        elif self.args.https_only:
            https = "s"
        else:
            https = "s" if self.args.qrs else ""

        ports = t1.get(ip, t2.get(ip, []))
        dport = 443 if https else 80
        port = "" if dport in ports or not ports else ":{}".format(ports[0])
        txt = "http{}://{}{}/{}".format(https, ip, port, self.args.qrl)

        btxt = txt.encode("utf-8")
        if PY2:
            btxt = sunpack(b"B" * len(btxt), btxt)

        fg = self.args.qr_fg
        bg = self.args.qr_bg
        pad = self.args.qrp
        zoom = self.args.qrz
        qrc = QrCode.encode_binary(btxt)
        if zoom == 0:
            try:
                tw, th = termsize()
                tsz = min(tw // 2, th)
                zoom = 1 if qrc.size + pad * 2 >= tsz else 2
            except:
                zoom = 1

        qr = qrc.render(zoom, pad)
        if not VT100:
            return "{}\n{}".format(txt, qr)

        def ansify(m: re.Match) -> str:
            t = "\033[40;48;5;{}m{}\033[47;48;5;{}m"
            return t.format(fg, " " * len(m.group(1)), bg)

        if zoom > 1:
            qr = re.sub("(█+)", ansify, qr)

        qr = qr.replace("\n", "\033[K\n") + "\033[K"  # win10do
        t = "{} \033[0;38;5;{};48;5;{}m\033[J\n{}\033[999G\033[0m\033[J"
        return t.format(txt, fg, bg, qr)

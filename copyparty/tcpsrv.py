# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import re
import socket
import sys

from .__init__ import ANYWIN, MACOS, PY2, TYPE_CHECKING, VT100, unicode
from .stolen.qrcodegen import QrCode
from .util import (
    E_ACCESS,
    E_ADDR_IN_USE,
    E_ADDR_NOT_AVAIL,
    E_UNREACH,
    chkcmd,
    min_ex,
    sunpack,
    termsize,
)

if True:
    from typing import Generator

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
        pad = False
        ok: dict[str, list[int]] = {}
        for ip in self.args.i:
            if ip == "::":
                if socket.has_ipv6:
                    ips = ["::", "0.0.0.0"]
                    dual = True
                else:
                    ips = ["0.0.0.0"]
                    dual = False
            else:
                ips = [ip]
                dual = False

            for ipa in ips:
                ok[ipa] = []

            for port in self.args.p:
                successful_binds = 0
                try:
                    for ipa in ips:
                        try:
                            self._listen(ipa, port)
                            ok[ipa].append(port)
                            successful_binds += 1
                        except:
                            if dual and ":" in ipa:
                                t = "listen on IPv6 [{}] failed; trying IPv4 {}...\n{}"
                                self.log("tcpsrv", t.format(ipa, ips[1], min_ex()), 3)
                                pad = True
                                continue

                            # binding 0.0.0.0 after :: fails on dualstack
                            # but is necessary on non-dualstakc
                            if successful_binds:
                                continue

                            raise

                except Exception as ex:
                    if self.args.ign_ebind or self.args.ign_ebind_all:
                        t = "could not listen on {}:{}: {}"
                        self.log("tcpsrv", t.format(ip, port, ex), c=3)
                        pad = True
                    else:
                        raise

        if not self.srv and not self.args.ign_ebind_all:
            raise Exception("could not listen on any of the given interfaces")

        if pad:
            self.log("tcpsrv", "")

        ip = "127.0.0.1"
        eps = {ip: "local only"}
        nonlocals = [x for x in self.args.i if x != ip]
        if nonlocals:
            eps = self.detect_interfaces(self.args.i)
            if not eps:
                for x in nonlocals:
                    eps[x] = "external"

        qr1: dict[str, list[int]] = {}
        qr2: dict[str, list[int]] = {}
        msgs = []
        title_tab: dict[str, dict[str, int]] = {}
        title_vars = [x[1:] for x in self.args.wintitle.split(" ") if x.startswith("$")]
        t = "available @ {}://{}:{}/  (\033[33m{}\033[0m)"
        for ip, desc in sorted(eps.items(), key=lambda x: x[1]):
            for port in sorted(self.args.p):
                if (
                    port not in ok.get(ip, [])
                    and port not in ok.get("::", [])
                    and port not in ok.get("0.0.0.0", [])
                ):
                    continue

                proto = " http"
                if self.args.http_only:
                    pass
                elif self.args.https_only or port == 443:
                    proto = "https"

                hip = "[{}]".format(ip) if ":" in ip else ip
                msgs.append(t.format(proto, hip, port, desc))

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
            for t in msgs:
                self.log("tcpsrv", t)

        if self.args.wintitle:
            self._set_wintitle(title_tab)
        else:
            print("\n", end="")

        if self.args.qr or self.args.qrs:
            self.qr = self._qr(qr1, qr2)

    def _listen(self, ip: str, port: int) -> None:
        ipv = socket.AF_INET6 if ":" in ip else socket.AF_INET
        srv = socket.socket(ipv, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        srv.settimeout(None)  # < does not inherit, ^ does
        try:
            srv.bind((ip, port))
            self.srv.append(srv)
        except (OSError, socket.error) as ex:
            if ex.errno in E_ADDR_IN_USE:
                e = "\033[1;31mport {} is busy on interface {}\033[0m".format(port, ip)
            elif ex.errno in E_ADDR_NOT_AVAIL:
                e = "\033[1;31minterface {} does not exist\033[0m".format(ip)
            else:
                raise
            raise Exception(e)

    def run(self) -> None:
        all_eps = [x.getsockname()[:2] for x in self.srv]
        bound = []
        srvs = []
        for srv in self.srv:
            ip, port = srv.getsockname()[:2]
            try:
                srv.listen(self.args.nc)
            except:
                if ip == "0.0.0.0" and ("::", port) in bound:
                    # dualstack
                    srv.close()
                    continue

                if ip == "::" and ("0.0.0.0", port) in all_eps:
                    # no ipv6
                    srv.close()
                    continue

                raise

            bound.append((ip, port))
            srvs.append(srv)
            fno = srv.fileno()
            hip = "[{}]".format(ip) if ":" in ip else ip
            msg = "listening @ {}:{}  f{} p{}".format(hip, port, fno, os.getpid())
            self.log("tcpsrv", msg)
            if self.args.q:
                print(msg)

            self.hub.broker.say("listen", srv)

        self.srv = srvs
        self.nsrv = len(srvs)

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

        r = re.compile(r"^\s+inet6? ([^ ]+)/")
        ri = re.compile(r"^[0-9]+: ([^:]+): ")
        dev = ""
        up = False
        eps: dict[str, str] = {}
        for ln in txt.split("\n"):
            m = ri.match(ln)
            if m:
                dev = m.group(1)
                up = "UP" in re.split("[>,< ]", ln)

            m = r.match(ln.rstrip())
            if not m or not dev or " scope link" in ln:
                continue

            ip = m.group(1)
            eps[ip] = dev + ("" if up else ", \033[31mLINK-DOWN")

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

        if "0.0.0.0" not in listen_ips and "::" not in listen_ips:
            eps = {k: v for k, v in eps.items() if k in listen_ips}

        try:
            ext_devs = list(self._extdevs_nix())
            ext_ips = [k for k, v in eps.items() if v.split(",")[0] in ext_devs]
            if not ext_ips:
                raise Exception()
        except:
            rt = self._defroute()
            ext_ips = [rt] if rt else []

        for lip in listen_ips:
            if not ext_ips or lip not in ["0.0.0.0", "::"] + ext_ips:
                continue

            desc = "\033[32mexternal"
            ips = ext_ips if lip in ["0.0.0.0", "::"] else [lip]
            for ip in ips:
                try:
                    if "external" not in eps[ip]:
                        eps[ip] += ", " + desc
                except:
                    eps[ip] = desc

        return eps

    def _extdevs_nix(self) -> Generator[str, None, None]:
        with open("/proc/net/route", "rb") as f:
            next(f)
            for ln in f:
                r = ln.decode("utf-8").strip().split()
                if r[1] == "0" * 8 and int(r[3], 16) & 2:
                    yield r[0]

    def _defroute(self) -> str:
        ret = ""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for ip in [
            "10.254.39.23",
            "172.31.39.23",
            "192.168.39.23",
            "239.254.39.23",
            "169.254.39.23",
            # could add 1.1.1.1 as a final fallback
            # but external connections is kinshi
        ]:
            try:
                s.connect((ip, 1))
                ret = s.getsockname()[0]
                break
            except (OSError, socket.error) as ex:
                if ex.errno in E_ACCESS:
                    self.log("tcpsrv", "eaccess {} (trying next)".format(ip))
                elif ex.errno not in E_UNREACH:
                    self.log("tcpsrv", "route lookup failed; err {}".format(ex.errno))

        s.close()
        return ret

    def _set_wintitle(self, vs: dict[str, dict[str, int]]) -> None:
        vs["all"] = vs.get("all", {"Local-Only": 1})
        vs["pub"] = vs.get("pub", vs["all"])

        vs2 = {}
        for k, eps in vs.items():
            filt = {ep: 1 for ep in eps if ":" not in ep}
            have = set(filt)
            for ep in sorted(eps):
                ip = ep.split(":")[0]
                if ip not in have:
                    have.add(ip)
                    filt[ep] = 1

            lo = [x for x in filt if x.startswith("127.")]
            if len(filt) > 3 and lo:
                for ip in lo:
                    filt.pop(ip)

            vs2[k] = filt

        title = ""
        vs = vs2
        for p in self.args.wintitle.split(" "):
            if p.startswith("$"):
                seps = list(sorted(vs.get(p[1:], {"(None)": 1}).keys()))
                p = ", ".join(seps[:3])
                if len(seps) > 3:
                    p += ", ..."

            title += "{} ".format(p)

        print("\033]0;{}\033\\\n".format(title), file=sys.stderr, end="")
        sys.stderr.flush()

    def _qr(self, t1: dict[str, list[int]], t2: dict[str, list[int]]) -> str:
        ip = None
        for ip in list(t1) + list(t2):
            if ip.startswith(self.args.qri):
                break
            ip = ""

        if not ip:
            # maybe /bin/ip is missing or smth
            ip = self.args.qri

        if not ip:
            return ""

        if ":" in ip:
            ip = "[{}]".format(ip)

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

        halfc = "\033[40;48;5;{0}m{1}\033[47;48;5;{2}m"
        if not fg:
            halfc = "\033[0;40m{1}\033[0;47m"

        def ansify(m: re.Match) -> str:
            return halfc.format(fg, " " * len(m.group(1)), bg)

        if zoom > 1:
            qr = re.sub("(█+)", ansify, qr)

        qr = qr.replace("\n", "\033[K\n") + "\033[K"  # win10do
        cc = " \033[0;38;5;{0};47;48;5;{1}m" if fg else " \033[0;30;47m"
        t = cc + "\n{2}\033[999G\033[0m\033[J"
        return txt + t.format(fg, bg, qr)

# coding: utf-8
from __future__ import print_function, unicode_literals

import random
import select
import socket
import time
from ipaddress import IPv4Network, IPv6Network

from .__init__ import TYPE_CHECKING
from .__init__ import unicode as U
from .util import CachedSet, Daemon, min_ex
from .multicast import MC_Sck, MCast
from .stolen.dnslib import (
    RR,
    DNSHeader,
    DNSRecord,
    DNSQuestion,
    QTYPE,
    A,
    AAAA,
    SRV,
    PTR,
    TXT,
)
from .stolen.dnslib import CLASS as DC

if TYPE_CHECKING:
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Any, Optional, Union


MDNS4 = "224.0.0.251"
MDNS6 = "ff02::fb"


class MDNS_Sck(MC_Sck):
    def __init__(
        self,
        sck: socket.socket,
        idx: int,
        grp: str,
        ip: str,
        net: Union[IPv4Network, IPv6Network],
    ):
        super(MDNS_Sck, self).__init__(sck, idx, grp, ip, net)

        self.bp_probe = b""
        self.bp_ip = b""
        self.bp_svc = b""
        self.bp_bye = b""

        self.last_tx = 0.0


class MDNS(MCast):
    def __init__(self, hub: "SvcHub") -> None:
        grp4 = "" if hub.args.zm6 else MDNS4
        grp6 = "" if hub.args.zm4 else MDNS6
        super(MDNS, self).__init__(hub, MDNS_Sck, grp4, grp6, 5353)
        self.srv: dict[socket.socket, MDNS_Sck] = {}

        self.ttl = 300
        self.running = True

        zs = self.args.name.lower() + ".local."
        zs = zs.encode("ascii", "replace").decode("ascii", "replace")
        self.hn = zs.replace("?", "_")

        # requester ip -> (response deadline, srv, body):
        self.q: dict[str, tuple[float, MDNS_Sck, bytes]] = {}
        self.rx4 = CachedSet(0.42)  # 3 probes @ 250..500..750 => 500ms span
        self.rx6 = CachedSet(0.42)
        self.svcs, self.sfqdns = self.build_svcs()

        self.probing = 0.0
        self.unsolicited: list[float] = []  # scheduled announces on all nics
        self.defend: dict[MDNS_Sck, float] = {}  # server -> deadline

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func("mDNS", msg, c)

    def build_svcs(self) -> tuple[dict[str, dict[str, Any]], set[str]]:
        zms = self.args.zms
        http = {"port": 80 if 80 in self.args.p else self.args.p[0]}
        https = {"port": 443 if 443 in self.args.p else self.args.p[0]}
        webdav = http.copy()
        webdavs = https.copy()
        webdav["u"] = webdavs["u"] = "u"  # KDE requires username
        ftp = {"port": (self.args.ftp if "f" in zms else self.args.ftps)}
        smb = {"port": self.args.smb_port}

        # some gvfs require path
        zs = self.args.zm_ld or "/"
        if zs:
            webdav["path"] = zs
            webdavs["path"] = zs

        if self.args.zm_lh:
            http["path"] = self.args.zm_lh
            https["path"] = self.args.zm_lh

        if self.args.zm_lf:
            ftp["path"] = self.args.zm_lf

        if self.args.zm_ls:
            smb["path"] = self.args.zm_ls

        svcs: dict[str, dict[str, Any]] = {}

        if "d" in zms:
            svcs["_webdav._tcp.local."] = webdav

        if "D" in zms:
            svcs["_webdavs._tcp.local."] = webdavs

        if "h" in zms:
            svcs["_http._tcp.local."] = http

        if "H" in zms:
            svcs["_https._tcp.local."] = https

        if "f" in zms.lower():
            svcs["_ftp._tcp.local."] = ftp

        if "s" in zms.lower():
            svcs["_smb._tcp.local."] = smb

        sfqdns: set[str] = set()
        for k, v in svcs.items():
            name = "{}-c-{}".format(self.args.name, k.split(".")[0][1:])
            v["name"] = name
            sfqdns.add("{}.{}".format(name, k))

        return svcs, sfqdns

    def build_replies(self) -> None:
        for srv in self.srv.values():
            probe = DNSRecord(DNSHeader(0, 0), q=DNSQuestion(self.hn, QTYPE.ANY))
            areply = DNSRecord(DNSHeader(0, 0x8400))
            sreply = DNSRecord(DNSHeader(0, 0x8400))
            bye = DNSRecord(DNSHeader(0, 0x8400))

            for ip in srv.ips:
                if ":" in ip:
                    qt = QTYPE.AAAA
                    ar = {"rclass": DC.F_IN, "rdata": AAAA(ip)}
                else:
                    qt = QTYPE.A
                    ar = {"rclass": DC.F_IN, "rdata": A(ip)}

                r0 = RR(self.hn, qt, ttl=0, **ar)
                r120 = RR(self.hn, qt, ttl=120, **ar)
                # rfc-10:
                #   SHOULD rr ttl 120sec for A/AAAA/SRV
                #   (and recommend 75min for all others)

                probe.add_auth(r120)
                areply.add_answer(r120)
                sreply.add_answer(r120)
                bye.add_answer(r0)

            for sclass, props in self.svcs.items():
                sname = props["name"]
                sport = props["port"]
                sfqdn = sname + "." + sclass

                k = "_services._dns-sd._udp.local."
                r = RR(k, QTYPE.PTR, DC.IN, 4500, PTR(sclass))
                sreply.add_answer(r)

                r = RR(sclass, QTYPE.PTR, DC.IN, 4500, PTR(sfqdn))
                sreply.add_answer(r)

                r = RR(sfqdn, QTYPE.SRV, DC.F_IN, 120, SRV(0, 0, sport, self.hn))
                sreply.add_answer(r)
                areply.add_answer(r)

                r = RR(sfqdn, QTYPE.SRV, DC.F_IN, 0, SRV(0, 0, sport, self.hn))
                bye.add_answer(r)

                txts = []
                for k in ("u", "path"):
                    if k not in props:
                        continue

                    zb = "{}={}".format(k, props[k]).encode("utf-8")
                    if len(zb) > 255:
                        t = "value too long for mdns: [{}]"
                        raise Exception(t.format(props[k]))

                    txts.append(zb)

                # gvfs really wants txt even if they're empty
                r = RR(sfqdn, QTYPE.TXT, DC.F_IN, 4500, TXT(txts))
                sreply.add_answer(r)

            srv.bp_probe = probe.pack()
            srv.bp_ip = areply.pack()
            srv.bp_svc = sreply.pack()
            srv.bp_bye = bye.pack()

            # since all replies are small enough to fit in one packet,
            # always send full replies rather than just a/aaaa records
            srv.bp_ip = srv.bp_svc

    def send_probes(self) -> None:
        slp = random.random() * 0.25
        for _ in range(3):
            time.sleep(slp)
            slp = 0.25
            if not self.running:
                break

            if self.args.zmv:
                self.log("sending hostname probe...")

            # ipv4: need to probe each ip (each server)
            # ipv6: only need to probe each set of looped nics
            probed6: set[str] = set()
            for srv in self.srv.values():
                if srv.ip in probed6:
                    continue

                try:
                    srv.sck.sendto(srv.bp_probe, (srv.grp, 5353))
                    if srv.v6:
                        for ip in srv.ips:
                            probed6.add(ip)
                except Exception as ex:
                    self.log("sendto failed: {} ({})".format(srv.ip, ex), "90")

    def run(self) -> None:
        bound = self.create_servers()
        if not bound:
            self.log("failed to announce copyparty services on the network", 3)
            return

        self.build_replies()
        Daemon(self.send_probes)
        zf = time.time() + 2
        self.probing = zf  # cant unicast so give everyone an extra sec
        self.unsolicited = [zf, zf + 1, zf + 3, zf + 7]  # rfc-8.3
        last_hop = time.time()
        ihop = self.args.mc_hop
        while self.running:
            timeout = (
                0.02 + random.random() * 0.07
                if self.probing or self.q or self.defend or self.unsolicited
                else (last_hop + ihop if ihop else 180)
            )
            rdy = select.select(self.srv, [], [], timeout)
            rx: list[socket.socket] = rdy[0]  # type: ignore
            self.rx4.cln()
            self.rx6.cln()
            for srv in rx:
                buf, addr = srv.recvfrom(4096)
                try:
                    self.eat(buf, addr)
                except:
                    t = "{} \033[33m|{}| {}\n{}".format(
                        addr, len(buf), repr(buf)[2:-1], min_ex()
                    )
                    self.log(t, 6)

            if not self.probing:
                self.process()
                continue

            if self.probing < time.time():
                self.log("probe ok; starting announcements", 2)
                self.probing = 0

    def stop(self, panic=False) -> None:
        self.running = False
        if not panic:
            for srv in self.srv.values():
                srv.sck.sendto(srv.bp_bye, (srv.grp, 5353))

    def eat(self, buf: bytes, addr: tuple[str, int]):
        cip = addr[0]
        if cip.startswith("fe80") or cip.startswith("169.254"):
            return

        v6 = ":" in cip
        cache = self.rx6 if v6 else self.rx4
        if buf in cache.c:
            return

        cache.add(buf)
        srv: Optional[MDNS_Sck] = self.map_client(cip)  # type: ignore
        if not srv:
            return

        now = time.time()

        if self.args.zmv:
            self.log("[{}] \033[36m{} \033[0m|{}|".format(srv.ip, cip, len(buf)), "90")

        p = DNSRecord.parse(buf)
        if self.args.zmvv:
            self.log(str(p))

        # check for incoming probes for our hostname
        cips = [U(x.rdata) for x in p.auth if U(x.rname).lower() == self.hn]
        if cips and self.sips.isdisjoint(cips):
            if not [x for x in cips if x not in ("::1", "127.0.0.1")]:
                # avahi broadcasting 127.0.0.1-only packets
                return

            self.log("someone trying to steal our hostname: {}".format(cips), 3)
            # immediately unicast
            if not self.probing:
                srv.sck.sendto(srv.bp_ip, (cip, 5353))

            # and schedule multicast
            self.defend[srv] = self.defend.get(srv, now + 0.1)
            return

        # check for someone rejecting our probe / hijacking our hostname
        cips = [
            U(x.rdata)
            for x in p.rr
            if U(x.rname).lower() == self.hn and x.rclass == DC.F_IN
        ]
        if cips and self.sips.isdisjoint(cips):
            if not [x for x in cips if x not in ("::1", "127.0.0.1")]:
                # avahi broadcasting 127.0.0.1-only packets
                return

            t = "mdns zeroconf: "
            if self.probing:
                t += "Cannot start; hostname '{}' is occupied"
            else:
                t += "Emergency stop; hostname '{}' got stolen"

            t += "! Use --name to set another hostname.\n\nName taken by {}\n\nYour IPs: {}\n"
            self.log(t.format(self.args.name, cips, list(self.sips)), 1)
            self.stop(True)
            return

        # then a/aaaa records
        for r in p.questions:
            if U(r.qname).lower() != self.hn:
                continue

            # gvfs keeps repeating itself
            found = False
            for r in p.rr:
                rname = U(r.rname).lower()
                if rname == self.hn and r.ttl > 60:
                    found = True
                    break

            if not found:
                self.q[cip] = (0, srv, srv.bp_ip)
                return

        deadline = now + (0.5 if p.header.tc else 0.02)  # rfc-7.2

        # and service queries
        for r in p.questions:
            qname = U(r.qname).lower()
            if qname in self.svcs or qname == "_services._dns-sd._udp.local.":
                self.q[cip] = (deadline, srv, srv.bp_svc)
                break
        # heed rfc-7.1 if there was an announce in the past 12sec
        # (workaround gvfs race-condition where it occasionally
        #  doesn't read/decode the full response...)
        if now < srv.last_tx + 12:
            for r in p.rr:
                rdata = U(r.rdata).lower()
                if rdata in self.sfqdns:
                    if r.ttl > 2250:
                        self.q.pop(cip, None)
                    break

    def process(self) -> None:
        tx = set()
        now = time.time()
        cooldown = 0.9  # rfc-6: 1
        if self.unsolicited and self.unsolicited[0] < now:
            self.unsolicited.pop(0)
            cooldown = 0.1
            for srv in self.srv.values():
                tx.add(srv)

        for srv, deadline in list(self.defend.items()):
            if now < deadline:
                continue

            if self._tx(srv, srv.bp_ip, 0.02):  # rfc-6: 0.25
                self.defend.pop(srv)

        for cip, (deadline, srv, msg) in list(self.q.items()):
            if now < deadline:
                continue

            self.q.pop(cip)
            self._tx(srv, msg, cooldown)

        for srv in tx:
            self._tx(srv, srv.bp_svc, cooldown)

    def _tx(self, srv: MDNS_Sck, msg: bytes, cooldown: float) -> bool:
        now = time.time()
        if now < srv.last_tx + cooldown:
            return False

        srv.sck.sendto(msg, (srv.grp, 5353))
        srv.last_tx = now
        return True

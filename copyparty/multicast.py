# coding: utf-8
from __future__ import print_function, unicode_literals

import socket
import time

import ipaddress
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)

from .__init__ import TYPE_CHECKING
from .util import MACOS, Netdev, min_ex, spack

if TYPE_CHECKING:
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Optional, Union

if not hasattr(socket, "IPPROTO_IPV6"):
    setattr(socket, "IPPROTO_IPV6", 41)


class NoIPs(Exception):
    pass


class MC_Sck(object):
    """there is one socket for each server ip"""

    def __init__(
        self,
        sck: socket.socket,
        nd: Netdev,
        grp: str,
        ip: str,
        net: Union[IPv4Network, IPv6Network],
    ):
        self.sck = sck
        self.idx = nd.idx
        self.name = nd.name
        self.grp = grp
        self.mreq = b""
        self.ip = ip
        self.net = net
        self.ips = {ip: net}
        self.v6 = ":" in ip
        self.have4 = ":" not in ip
        self.have6 = ":" in ip


class MCast(object):
    def __init__(
        self,
        hub: "SvcHub",
        Srv: type[MC_Sck],
        on: list[str],
        off: list[str],
        mc_grp_4: str,
        mc_grp_6: str,
        port: int,
        vinit: bool,
    ) -> None:
        """disable ipv%d by setting mc_grp_%d empty"""
        self.hub = hub
        self.Srv = Srv
        self.args = hub.args
        self.asrv = hub.asrv
        self.log_func = hub.log
        self.on = on
        self.off = off
        self.grp4 = mc_grp_4
        self.grp6 = mc_grp_6
        self.port = port
        self.vinit = vinit

        self.srv: dict[socket.socket, MC_Sck] = {}  # listening sockets
        self.sips: set[str] = set()  # all listening ips (including failed attempts)
        self.b2srv: dict[bytes, MC_Sck] = {}  # binary-ip -> server socket
        self.b4: list[bytes] = []  # sorted list of binary-ips
        self.b6: list[bytes] = []  # sorted list of binary-ips
        self.cscache: dict[str, Optional[MC_Sck]] = {}  # client ip -> server cache

        self.running = True

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func("multicast", msg, c)

    def create_servers(self) -> list[str]:
        bound: list[str] = []
        netdevs = self.hub.tcpsrv.netdevs
        ips = [x[0] for x in self.hub.tcpsrv.bound]

        if "::" in ips:
            ips = [x for x in ips if x != "::"] + list(
                [x.split("/")[0] for x in netdevs if ":" in x]
            )
            ips.append("0.0.0.0")

        if "0.0.0.0" in ips:
            ips = [x for x in ips if x != "0.0.0.0"] + list(
                [x.split("/")[0] for x in netdevs if ":" not in x]
            )

        ips = [x for x in ips if x not in ("::1", "127.0.0.1")]

        # ip -> ip/prefix
        ips = [[x for x in netdevs if x.startswith(y + "/")][0] for y in ips]

        on = self.on[:]
        off = self.off[:]
        for lst in (on, off):
            for av in list(lst):
                try:
                    arg_net = ip_network(av, False)
                except:
                    arg_net = None

                for sk, sv in netdevs.items():
                    if arg_net:
                        net_ip = ip_address(sk.split("/")[0])
                        if net_ip in arg_net and sk not in lst:
                            lst.append(sk)

                    if (av == str(sv.idx) or av == sv.name) and sk not in lst:
                        lst.append(sk)

        if on:
            ips = [x for x in ips if x in on]
        elif off:
            ips = [x for x in ips if x not in off]

        if not self.grp4:
            ips = [x for x in ips if ":" in x]

        if not self.grp6:
            ips = [x for x in ips if ":" not in x]

        ips = list(set(ips))
        all_selected = ips[:]

        # discard non-linklocal ipv6
        ips = [x for x in ips if ":" not in x or x.startswith("fe80")]

        if not ips:
            raise NoIPs()

        for ip in ips:
            v6 = ":" in ip
            netdev = netdevs[ip]
            if not netdev.idx:
                t = "using INADDR_ANY for ip [{}], netdev [{}]"
                if not self.srv and ip not in ["::", "0.0.0.0"]:
                    self.log(t.format(ip, netdev), 3)

            ipv = socket.AF_INET6 if v6 else socket.AF_INET
            sck = socket.socket(ipv, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sck.settimeout(None)
            sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except:
                pass

            # most ipv6 clients expect multicast on linklocal ip only;
            # add a/aaaa records for the other nic IPs
            other_ips: set[str] = set()
            if v6:
                for nd in netdevs.values():
                    if nd.idx == netdev.idx and nd.ip in all_selected and ":" in nd.ip:
                        other_ips.add(nd.ip)

            net = ipaddress.ip_network(ip, False)
            ip = ip.split("/")[0]
            srv = self.Srv(sck, netdev, self.grp6 if ":" in ip else self.grp4, ip, net)
            for oth_ip in other_ips:
                srv.ips[oth_ip.split("/")[0]] = ipaddress.ip_network(oth_ip, False)

            # gvfs breaks if a linklocal ip appears in a dns reply
            if not self.args.ll:
                srv.ips = {k: v for k, v in srv.ips.items() if not k.startswith("fe80")}

            if not srv.ips:
                self.log("no routable IPs on {}; skipping [{}]".format(netdev, ip), 3)
                continue

            try:
                self.setup_socket(srv)
                self.srv[sck] = srv
                bound.append(ip)
            except:
                t = "announce failed on {} [{}]:\n{}"
                self.log(t.format(netdev, ip, min_ex()), 3)

        if self.args.zm_msub:
            for s1 in self.srv.values():
                for s2 in self.srv.values():
                    if s1.idx != s2.idx:
                        continue

                    if s1.ip not in s2.ips:
                        s2.ips[s1.ip] = s1.net

        if self.args.zm_mnic:
            for s1 in self.srv.values():
                for s2 in self.srv.values():
                    for ip1, net1 in list(s1.ips.items()):
                        for ip2, net2 in list(s2.ips.items()):
                            if net1 == net2 and ip1 != ip2:
                                s1.ips[ip2] = net2

        self.sips = set([x.split("/")[0] for x in all_selected])
        for srv in self.srv.values():
            assert srv.ip in self.sips

        return bound

    def setup_socket(self, srv: MC_Sck) -> None:
        sck = srv.sck
        if srv.v6:
            if self.vinit:
                zsl = list(srv.ips.keys())
                self.log("v6({}) idx({}) {}".format(srv.ip, srv.idx, zsl), 6)

            for ip in srv.ips:
                bip = socket.inet_pton(socket.AF_INET6, ip)
                self.b2srv[bip] = srv
                self.b6.append(bip)

            grp = self.grp6 if srv.idx else ""
            try:
                if MACOS:
                    raise Exception()

                sck.bind((grp, self.port, 0, srv.idx))
            except:
                sck.bind(("", self.port, 0, srv.idx))

            bgrp = socket.inet_pton(socket.AF_INET6, self.grp6)
            dev = spack(b"@I", srv.idx)
            srv.mreq = bgrp + dev
            if srv.idx != socket.INADDR_ANY:
                sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, dev)

            try:
                sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)
                sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
            except:
                # macos
                t = "failed to set IPv6 TTL/LOOP; announcements may not survive multiple switches/routers"
                self.log(t, 3)
        else:
            if self.vinit:
                self.log("v4({}) idx({})".format(srv.ip, srv.idx), 6)

            bip = socket.inet_aton(srv.ip)
            self.b2srv[bip] = srv
            self.b4.append(bip)

            grp = self.grp4 if srv.idx else ""
            try:
                if MACOS:
                    raise Exception()

                sck.bind((grp, self.port))
            except:
                sck.bind(("", self.port))

            bgrp = socket.inet_aton(self.grp4)
            dev = (
                spack(b"=I", socket.INADDR_ANY)
                if srv.idx == socket.INADDR_ANY
                else socket.inet_aton(srv.ip)
            )
            srv.mreq = bgrp + dev
            if srv.idx != socket.INADDR_ANY:
                sck.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, dev)

            try:
                sck.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
                sck.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
            except:
                # probably can't happen but dontcare if it does
                t = "failed to set IPv4 TTL/LOOP; announcements may not survive multiple switches/routers"
                self.log(t, 3)

        self.hop(srv)
        self.b4.sort(reverse=True)
        self.b6.sort(reverse=True)

    def hop(self, srv: MC_Sck) -> None:
        """rejoin to keepalive on routers/switches without igmp-snooping"""
        sck = srv.sck
        req = srv.mreq
        if ":" in srv.ip:
            try:
                sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_LEAVE_GROUP, req)
                # linux does leaves/joins twice with 0.2~1.05s spacing
                time.sleep(1.2)
            except:
                pass

            sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, req)
        else:
            try:
                sck.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, req)
                time.sleep(1.2)
            except:
                pass

            # t = "joining {} from ip {} idx {} with mreq {}"
            # self.log(t.format(srv.grp, srv.ip, srv.idx, repr(srv.mreq)), 6)
            sck.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)

    def map_client(self, cip: str) -> Optional[MC_Sck]:
        try:
            return self.cscache[cip]
        except:
            pass

        ret: Optional[MC_Sck] = None
        v6 = ":" in cip
        ci = IPv6Address(cip) if v6 else IPv4Address(cip)
        for x in self.b6 if v6 else self.b4:
            srv = self.b2srv[x]
            if any([x for x in srv.ips.values() if ci in x]):
                ret = srv
                break

        if not ret and cip in ("127.0.0.1", "::1"):
            # just give it something
            ret = list(self.srv.values())[0]

        if ret:
            t = "new client on {} ({}): {}"
            self.log(t.format(ret.name, ret.net, cip), 6)
        else:
            t = "could not map client {} to known subnet; maybe forwarded from another network?"
            self.log(t.format(cip), 3)

        if len(self.cscache) > 9000:
            self.cscache = {}

        self.cscache[cip] = ret
        return ret

# coding: utf-8
from __future__ import print_function, unicode_literals

import socket
import time
import ipaddress
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address

from .__init__ import TYPE_CHECKING
from .util import min_ex, spack

if TYPE_CHECKING:
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Optional, Union

if not hasattr(socket, "IPPROTO_IPV6"):
    setattr(socket, "IPPROTO_IPV6", 41)


class MC_Sck(object):
    """there is one socket for each server ip"""

    def __init__(
        self,
        sck: socket.socket,
        idx: int,
        grp: str,
        ip: str,
        net: Union[IPv4Network, IPv6Network],
    ):
        self.sck = sck
        self.idx = idx
        self.grp = grp
        self.mreq = b""
        self.ip = ip
        self.net = net
        self.ips = {ip: net}
        self.v6 = ":" in ip


class MCast(object):
    def __init__(
        self, hub: "SvcHub", Srv: type[MC_Sck], mc_grp_4: str, mc_grp_6: str, port: int
    ) -> None:
        """disable ipv%d by setting mc_grp_%d empty"""
        self.hub = hub
        self.Srv = Srv
        self.args = hub.args
        self.asrv = hub.asrv
        self.log_func = hub.log
        self.grp4 = mc_grp_4
        self.grp6 = mc_grp_6
        self.port = port

        self.srv: dict[socket.socket, MC_Sck] = {}  # listening sockets
        self.sips: set[str] = set()  # all listening ips
        self.b2srv: dict[bytes, MC_Sck] = {}  # binary-ip -> server socket
        self.b4: list[bytes] = []  # sorted list of binary-ips
        self.b6: list[bytes] = []  # sorted list of binary-ips
        self.cscache: dict[str, Optional[MC_Sck]] = {}  # client ip -> server cache

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func("multicast", msg, c)

    def create_servers(self) -> list[str]:
        bound: list[str] = []
        ips = [x[0] for x in self.hub.tcpsrv.bound]
        ips = list(set(ips))

        if "::" in ips:
            ips = [x for x in ips if x != "::"] + list(
                [x.split("/")[0] for x in self.hub.tcpsrv.netdevs if ":" in x]
            )
            ips.append("0.0.0.0")

        if "0.0.0.0" in ips:
            ips = [x for x in ips if x != "0.0.0.0"] + list(
                [x.split("/")[0] for x in self.hub.tcpsrv.netdevs if ":" not in x]
            )

        ips = [x for x in ips if x not in ("::1", "127.0.0.1")]

        ips = [
            [x for x in self.hub.tcpsrv.netdevs if x.startswith(y + "/")][0]
            for y in ips
        ]

        if not self.grp4:
            ips = [x for x in ips if ":" in x]

        if not self.grp6:
            ips = [x for x in ips if ":" not in x]

        if not ips:
            raise Exception("no server IP matches the mdns config")

        for ip in ips:
            v6 = ":" in ip
            netdev = "?"
            try:
                netdev = self.hub.tcpsrv.netdevs[ip].split(",")[0]
                idx = socket.if_nametoindex(netdev)
            except:
                idx = socket.INADDR_ANY
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

            net = ipaddress.ip_network(ip, False)
            ip = ip.split("/")[0]
            srv = self.Srv(sck, idx, self.grp6 if ":" in ip else self.grp4, ip, net)

            try:
                self.setup_socket(srv)
                self.srv[sck] = srv
                bound.append(ip)
            except:
                self.log("announce failed on [{}]:\n{}".format(ip, min_ex()))

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

        self.sips = set([x.ip for x in self.srv.values()])
        return bound

    def setup_socket(self, srv: MC_Sck) -> None:
        sck = srv.sck
        if srv.v6:
            if self.args.zmv:
                self.log("v6({}) idx({})".format(srv.ip, srv.idx), 6)

            bip = socket.inet_pton(socket.AF_INET6, srv.ip)
            self.b2srv[bip] = srv
            self.b6.append(bip)

            sck.bind((self.grp6 if srv.idx else "", self.port, 0, srv.idx))
            bgrp = socket.inet_pton(socket.AF_INET6, self.grp6)
            dev = spack(b"@I", srv.idx)
            srv.mreq = bgrp + dev
            if srv.idx != socket.INADDR_ANY:
                sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, dev)

            self.hop(srv)
            try:
                sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
                sck.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)
            except:
                pass  # macos
        else:
            if self.args.zmv:
                self.log("v4({}) idx({})".format(srv.ip, srv.idx), 6)

            bip = socket.inet_aton(srv.ip)
            self.b2srv[bip] = srv
            self.b4.append(bip)

            sck.bind((self.grp4 if srv.idx else "", self.port))
            bgrp = socket.inet_aton(self.grp4)
            dev = (
                spack(b"=I", socket.INADDR_ANY)
                if srv.idx == socket.INADDR_ANY
                else socket.inet_aton(srv.ip)
            )
            srv.mreq = bgrp + dev
            if srv.idx != socket.INADDR_ANY:
                sck.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, dev)

            self.hop(srv)
            try:
                sck.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
                sck.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
            except:
                pass

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

        if not ret:
            t = "could not map client {} to known subnet; maybe forwarded from another network?"
            self.log(t.format(cip), 3)

        self.cscache[cip] = ret
        if len(self.cscache) > 9000:
            self.cscache = {}

        return ret

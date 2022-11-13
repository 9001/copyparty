# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import ctypes.util
import ipaddress
import collections
import socket

if True:  # pylint: disable=using-constant-test
    from typing import Iterable, Optional

from . import _shared as shared
from ._shared import U


class ifaddrs(ctypes.Structure):
    pass


ifaddrs._fields_ = [
    ("ifa_next", ctypes.POINTER(ifaddrs)),
    ("ifa_name", ctypes.c_char_p),
    ("ifa_flags", ctypes.c_uint),
    ("ifa_addr", ctypes.POINTER(shared.sockaddr)),
    ("ifa_netmask", ctypes.POINTER(shared.sockaddr)),
]

libc = ctypes.CDLL(ctypes.util.find_library("socket" if os.uname()[0] == "SunOS" else "c"), use_errno=True)  # type: ignore


def get_adapters(include_unconfigured: bool = False) -> Iterable[shared.Adapter]:

    addr0 = addr = ctypes.POINTER(ifaddrs)()
    retval = libc.getifaddrs(ctypes.byref(addr))
    if retval != 0:
        eno = ctypes.get_errno()
        raise OSError(eno, os.strerror(eno))

    ips = collections.OrderedDict()

    def add_ip(adapter_name: str, ip: Optional[shared.IP]) -> None:
        if adapter_name not in ips:
            index = None  # type: Optional[int]
            try:
                # Mypy errors on this when the Windows CI runs:
                #     error: Module has no attribute "if_nametoindex"
                index = socket.if_nametoindex(adapter_name)  # type: ignore
            except (OSError, AttributeError):
                pass
            ips[adapter_name] = shared.Adapter(
                adapter_name, adapter_name, [], index=index
            )
        if ip is not None:
            ips[adapter_name].ips.append(ip)

    while addr:
        name = addr[0].ifa_name.decode(encoding="UTF-8")
        ip_addr = shared.sockaddr_to_ip(addr[0].ifa_addr)
        if ip_addr:
            if addr[0].ifa_netmask and not addr[0].ifa_netmask[0].sa_familiy:
                addr[0].ifa_netmask[0].sa_familiy = addr[0].ifa_addr[0].sa_familiy
            netmask = shared.sockaddr_to_ip(addr[0].ifa_netmask)
            if isinstance(netmask, tuple):
                netmaskStr = U(netmask[0])
                prefixlen = shared.ipv6_prefixlength(ipaddress.IPv6Address(netmaskStr))
            else:
                if netmask is None:
                    t = "sockaddr_to_ip({}) returned None"
                    raise Exception(t.format(addr[0].ifa_netmask))

                netmaskStr = U("0.0.0.0/" + netmask)
                prefixlen = ipaddress.IPv4Network(netmaskStr).prefixlen
            ip = shared.IP(ip_addr, prefixlen, name)
            add_ip(name, ip)
        else:
            if include_unconfigured:
                add_ip(name, None)
        addr = addr[0].ifa_next

    libc.freeifaddrs(addr0)

    return ips.values()

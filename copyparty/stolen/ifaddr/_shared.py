# coding: utf-8
from __future__ import print_function, unicode_literals

import ctypes
import platform
import socket
import sys

import ipaddress

if True:  # pylint: disable=using-constant-test
    from typing import Callable, List, Optional, Union


PY2 = sys.version_info < (3,)
if not PY2:
    U: Callable[[str], str] = str
else:
    U = unicode  # noqa: F821  # pylint: disable=undefined-variable,self-assigning-variable


class Adapter(object):
    """
    Represents a network interface device controller (NIC), such as a
    network card. An adapter can have multiple IPs.

    On Linux aliasing (multiple IPs per physical NIC) is implemented
    by creating 'virtual' adapters, each represented by an instance
    of this class. Each of those 'virtual' adapters can have both
    a IPv4 and an IPv6 IP address.
    """

    def __init__(
        self, name: str, nice_name: str, ips: List["IP"], index: Optional[int] = None
    ) -> None:

        #: Unique name that identifies the adapter in the system.
        #: On Linux this is of the form of `eth0` or `eth0:1`, on
        #: Windows it is a UUID in string representation, such as
        #: `{846EE342-7039-11DE-9D20-806E6F6E6963}`.
        self.name = name

        #: Human readable name of the adpater. On Linux this
        #: is currently the same as :attr:`name`. On Windows
        #: this is the name of the device.
        self.nice_name = nice_name

        #: List of :class:`ifaddr.IP` instances in the order they were
        #: reported by the system.
        self.ips = ips

        #: Adapter index as used by some API (e.g. IPv6 multicast group join).
        self.index = index

    def __repr__(self) -> str:
        return "Adapter(name={name}, nice_name={nice_name}, ips={ips}, index={index})".format(
            name=repr(self.name),
            nice_name=repr(self.nice_name),
            ips=repr(self.ips),
            index=repr(self.index),
        )


if True:
    # Type of an IPv4 address (a string in "xxx.xxx.xxx.xxx" format)
    _IPv4Address = str

    # Type of an IPv6 address (a three-tuple `(ip, flowinfo, scope_id)`)
    _IPv6Address = tuple[str, int, int]


class IP(object):
    """
    Represents an IP address of an adapter.
    """

    def __init__(
        self, ip: Union[_IPv4Address, _IPv6Address], network_prefix: int, nice_name: str
    ) -> None:

        #: IP address. For IPv4 addresses this is a string in
        #: "xxx.xxx.xxx.xxx" format. For IPv6 addresses this
        #: is a three-tuple `(ip, flowinfo, scope_id)`, where
        #: `ip` is a string in the usual collon separated
        #: hex format.
        self.ip = ip

        #: Number of bits of the IP that represent the
        #: network. For a `255.255.255.0` netmask, this
        #: number would be `24`.
        self.network_prefix = network_prefix

        #: Human readable name for this IP.
        #: On Linux is this currently the same as the adapter name.
        #: On Windows this is the name of the network connection
        #: as configured in the system control panel.
        self.nice_name = nice_name

    @property
    def is_IPv4(self) -> bool:
        """
        Returns `True` if this IP is an IPv4 address and `False`
        if it is an IPv6 address.
        """
        return not isinstance(self.ip, tuple)

    @property
    def is_IPv6(self) -> bool:
        """
        Returns `True` if this IP is an IPv6 address and `False`
        if it is an IPv4 address.
        """
        return isinstance(self.ip, tuple)

    def __repr__(self) -> str:
        return "IP(ip={ip}, network_prefix={network_prefix}, nice_name={nice_name})".format(
            ip=repr(self.ip),
            network_prefix=repr(self.network_prefix),
            nice_name=repr(self.nice_name),
        )


if platform.system() == "Darwin" or "BSD" in platform.system():

    # BSD derived systems use marginally different structures
    # than either Linux or Windows.
    # I still keep it in `shared` since we can use
    # both structures equally.

    class sockaddr(ctypes.Structure):
        _fields_ = [
            ("sa_len", ctypes.c_uint8),
            ("sa_familiy", ctypes.c_uint8),
            ("sa_data", ctypes.c_uint8 * 14),
        ]

    class sockaddr_in(ctypes.Structure):
        _fields_ = [
            ("sa_len", ctypes.c_uint8),
            ("sa_familiy", ctypes.c_uint8),
            ("sin_port", ctypes.c_uint16),
            ("sin_addr", ctypes.c_uint8 * 4),
            ("sin_zero", ctypes.c_uint8 * 8),
        ]

    class sockaddr_in6(ctypes.Structure):
        _fields_ = [
            ("sa_len", ctypes.c_uint8),
            ("sa_familiy", ctypes.c_uint8),
            ("sin6_port", ctypes.c_uint16),
            ("sin6_flowinfo", ctypes.c_uint32),
            ("sin6_addr", ctypes.c_uint8 * 16),
            ("sin6_scope_id", ctypes.c_uint32),
        ]

else:

    class sockaddr(ctypes.Structure):  # type: ignore
        _fields_ = [("sa_familiy", ctypes.c_uint16), ("sa_data", ctypes.c_uint8 * 14)]

    class sockaddr_in(ctypes.Structure):  # type: ignore
        _fields_ = [
            ("sin_familiy", ctypes.c_uint16),
            ("sin_port", ctypes.c_uint16),
            ("sin_addr", ctypes.c_uint8 * 4),
            ("sin_zero", ctypes.c_uint8 * 8),
        ]

    class sockaddr_in6(ctypes.Structure):  # type: ignore
        _fields_ = [
            ("sin6_familiy", ctypes.c_uint16),
            ("sin6_port", ctypes.c_uint16),
            ("sin6_flowinfo", ctypes.c_uint32),
            ("sin6_addr", ctypes.c_uint8 * 16),
            ("sin6_scope_id", ctypes.c_uint32),
        ]


def sockaddr_to_ip(
    sockaddr_ptr: "ctypes.pointer[sockaddr]",
) -> Optional[Union[_IPv4Address, _IPv6Address]]:
    if sockaddr_ptr:
        if sockaddr_ptr[0].sa_familiy == socket.AF_INET:
            ipv4 = ctypes.cast(sockaddr_ptr, ctypes.POINTER(sockaddr_in))
            ippacked = bytes(bytearray(ipv4[0].sin_addr))
            ip = U(ipaddress.ip_address(ippacked))
            return ip
        elif sockaddr_ptr[0].sa_familiy == socket.AF_INET6:
            ipv6 = ctypes.cast(sockaddr_ptr, ctypes.POINTER(sockaddr_in6))
            flowinfo = ipv6[0].sin6_flowinfo
            ippacked = bytes(bytearray(ipv6[0].sin6_addr))
            ip = U(ipaddress.ip_address(ippacked))
            scope_id = ipv6[0].sin6_scope_id
            return (ip, flowinfo, scope_id)
    return None


def ipv6_prefixlength(address: ipaddress.IPv6Address) -> int:
    prefix_length = 0
    for i in range(address.max_prefixlen):
        if int(address) >> i & 1:
            prefix_length = prefix_length + 1
    return prefix_length

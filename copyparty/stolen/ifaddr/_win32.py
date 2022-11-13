# coding: utf-8
from __future__ import print_function, unicode_literals

import ctypes
from ctypes import wintypes

if True:  # pylint: disable=using-constant-test
    from typing import Iterable, List

from . import _shared as shared

NO_ERROR = 0
ERROR_BUFFER_OVERFLOW = 111
MAX_ADAPTER_NAME_LENGTH = 256
MAX_ADAPTER_DESCRIPTION_LENGTH = 128
MAX_ADAPTER_ADDRESS_LENGTH = 8
AF_UNSPEC = 0


class SOCKET_ADDRESS(ctypes.Structure):
    _fields_ = [
        ("lpSockaddr", ctypes.POINTER(shared.sockaddr)),
        ("iSockaddrLength", wintypes.INT),
    ]


class IP_ADAPTER_UNICAST_ADDRESS(ctypes.Structure):
    pass


IP_ADAPTER_UNICAST_ADDRESS._fields_ = [
    ("Length", wintypes.ULONG),
    ("Flags", wintypes.DWORD),
    ("Next", ctypes.POINTER(IP_ADAPTER_UNICAST_ADDRESS)),
    ("Address", SOCKET_ADDRESS),
    ("PrefixOrigin", ctypes.c_uint),
    ("SuffixOrigin", ctypes.c_uint),
    ("DadState", ctypes.c_uint),
    ("ValidLifetime", wintypes.ULONG),
    ("PreferredLifetime", wintypes.ULONG),
    ("LeaseLifetime", wintypes.ULONG),
    ("OnLinkPrefixLength", ctypes.c_uint8),
]


class IP_ADAPTER_ADDRESSES(ctypes.Structure):
    pass


IP_ADAPTER_ADDRESSES._fields_ = [
    ("Length", wintypes.ULONG),
    ("IfIndex", wintypes.DWORD),
    ("Next", ctypes.POINTER(IP_ADAPTER_ADDRESSES)),
    ("AdapterName", ctypes.c_char_p),
    ("FirstUnicastAddress", ctypes.POINTER(IP_ADAPTER_UNICAST_ADDRESS)),
    ("FirstAnycastAddress", ctypes.c_void_p),
    ("FirstMulticastAddress", ctypes.c_void_p),
    ("FirstDnsServerAddress", ctypes.c_void_p),
    ("DnsSuffix", ctypes.c_wchar_p),
    ("Description", ctypes.c_wchar_p),
    ("FriendlyName", ctypes.c_wchar_p),
]


iphlpapi = ctypes.windll.LoadLibrary("Iphlpapi")  # type: ignore


def enumerate_interfaces_of_adapter(
    nice_name: str, address: IP_ADAPTER_UNICAST_ADDRESS
) -> Iterable[shared.IP]:

    # Iterate through linked list and fill list
    addresses = []  # type: List[IP_ADAPTER_UNICAST_ADDRESS]
    while True:
        addresses.append(address)
        if not address.Next:
            break
        address = address.Next[0]

    for address in addresses:
        ip = shared.sockaddr_to_ip(address.Address.lpSockaddr)
        if ip is None:
            t = "sockaddr_to_ip({}) returned None"
            raise Exception(t.format(address.Address.lpSockaddr))

        network_prefix = address.OnLinkPrefixLength
        yield shared.IP(ip, network_prefix, nice_name)


def get_adapters(include_unconfigured: bool = False) -> Iterable[shared.Adapter]:

    # Call GetAdaptersAddresses() with error and buffer size handling

    addressbuffersize = wintypes.ULONG(15 * 1024)
    retval = ERROR_BUFFER_OVERFLOW
    while retval == ERROR_BUFFER_OVERFLOW:
        addressbuffer = ctypes.create_string_buffer(addressbuffersize.value)
        retval = iphlpapi.GetAdaptersAddresses(
            wintypes.ULONG(AF_UNSPEC),
            wintypes.ULONG(0),
            None,
            ctypes.byref(addressbuffer),
            ctypes.byref(addressbuffersize),
        )
    if retval != NO_ERROR:
        raise ctypes.WinError()  # type: ignore

    # Iterate through adapters fill array
    address_infos = []  # type: List[IP_ADAPTER_ADDRESSES]
    address_info = IP_ADAPTER_ADDRESSES.from_buffer(addressbuffer)
    while True:
        address_infos.append(address_info)
        if not address_info.Next:
            break
        address_info = address_info.Next[0]

    # Iterate through unicast addresses
    result = []  # type: List[shared.Adapter]
    for adapter_info in address_infos:

        # We don't expect non-ascii characters here, so encoding shouldn't matter
        name = adapter_info.AdapterName.decode()
        nice_name = adapter_info.Description
        index = adapter_info.IfIndex

        if adapter_info.FirstUnicastAddress:
            ips = enumerate_interfaces_of_adapter(
                adapter_info.FriendlyName, adapter_info.FirstUnicastAddress[0]
            )
            ips = list(ips)
            result.append(shared.Adapter(name, nice_name, ips, index=index))
        elif include_unconfigured:
            result.append(shared.Adapter(name, nice_name, [], index=index))

    return result

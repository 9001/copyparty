# coding: utf-8
from __future__ import print_function, unicode_literals

"""
L: BSD-2-Clause
Copyright (c) 2014 Stefan C. Mueller
https://github.com/pydron/ifaddr/tree/0.2.0
"""

import os
import platform

from ._shared import IP, Adapter


def nope(include_unconfigured=False):
    return []


host_os = platform.system()
machine = platform.machine()
py_impl = platform.python_implementation()


if os.environ.get("PRTY_NO_IFADDR"):
    get_adapters = nope
elif machine in ("s390x",) or host_os in ("IRIX32",):
    # s390x deadlocks at libc.getifaddrs
    # irix libc does not have getifaddrs at all
    print("ifaddr unavailable; can't determine LAN IP: unsupported OS")
    get_adapters = nope
elif py_impl in ("GraalVM",):
    print("ifaddr unavailable; can't determine LAN IP: unsupported interpreter")
    get_adapters = nope
elif os.name == "nt":
    from ._win32 import get_adapters
elif os.name == "posix":
    from ._posix import get_adapters
else:
    print("ifaddr unavailable; can't determine LAN IP: unsupported OS")
    get_adapters = nope


__all__ = ["Adapter", "IP", "get_adapters"]

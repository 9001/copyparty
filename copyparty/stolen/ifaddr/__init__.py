# coding: utf-8
from __future__ import print_function, unicode_literals

"""
L: BSD-2-Clause
Copyright (c) 2014 Stefan C. Mueller
https://github.com/pydron/ifaddr/tree/0.2.0
"""

import os

from ._shared import IP, Adapter


def nope(include_unconfigured=False):
    return []


try:
    S390X = os.uname().machine == "s390x"
except:
    S390X = False


if os.environ.get("PRTY_NO_IFADDR") or S390X:
    # s390x deadlocks at libc.getifaddrs
    get_adapters = nope
elif os.name == "nt":
    from ._win32 import get_adapters
elif os.name == "posix":
    from ._posix import get_adapters
else:
    raise RuntimeError("Unsupported Operating System: %s" % os.name)

__all__ = ["Adapter", "IP", "get_adapters"]

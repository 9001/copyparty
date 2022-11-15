# coding: utf-8
from __future__ import print_function, unicode_literals

"""
L: BSD-2-Clause
Copyright (c) 2014 Stefan C. Mueller
https://github.com/pydron/ifaddr/tree/0.2.0
"""

import os

from ._shared import IP, Adapter

if os.name == "nt":
    from ._win32 import get_adapters
elif os.name == "posix":
    from ._posix import get_adapters
else:
    raise RuntimeError("Unsupported Operating System: %s" % os.name)

__all__ = ["Adapter", "IP", "get_adapters"]

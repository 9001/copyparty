# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import platform
import sys
import time

try:
    from typing import TYPE_CHECKING, Any
except:
    TYPE_CHECKING = False

PY2 = sys.version_info[0] == 2
if PY2:
    sys.dont_write_bytecode = True
    unicode = unicode  # noqa: F821  # pylint: disable=undefined-variable,self-assigning-variable
else:
    unicode = str

WINDOWS: Any = (
    [int(x) for x in platform.version().split(".")]
    if platform.system() == "Windows"
    else False
)

VT100 = not WINDOWS or WINDOWS >= [10, 0, 14393]
# introduced in anniversary update

ANYWIN = WINDOWS or sys.platform in ["msys", "cygwin"]

MACOS = platform.system() == "Darwin"

try:
    CORES = len(os.sched_getaffinity(0))
except:
    CORES = (os.cpu_count() if hasattr(os, "cpu_count") else 0) or 2


class EnvParams(object):
    def __init__(self) -> None:
        self.t0 = time.time()
        self.mod = None
        self.cfg = None
        try:
            self.ox = sys.oxidized
        except:
            self.ox = False


E = EnvParams()

# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import platform
import sys
import time

try:
    from typing import TYPE_CHECKING
except:
    TYPE_CHECKING = False

if True:
    from typing import Any, Callable

PY2 = sys.version_info < (3,)
if not PY2:
    unicode: Callable[[Any], str] = str
else:
    sys.dont_write_bytecode = True
    unicode = unicode  # noqa: F821  # pylint: disable=undefined-variable,self-assigning-variable

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
        self.mod = ""
        self.cfg = ""
        self.ox = getattr(sys, "oxidized", None)


E = EnvParams()

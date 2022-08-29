# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import platform
import sys
import time

try:
    from collections.abc import Callable

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


def get_unixdir() -> str:
    paths: list[tuple[Callable[..., str], str]] = [
        (os.environ.get, "XDG_CONFIG_HOME"),
        (os.path.expanduser, "~/.config"),
        (os.environ.get, "TMPDIR"),
        (os.environ.get, "TEMP"),
        (os.environ.get, "TMP"),
        (unicode, "/tmp"),
    ]
    for chk in [os.listdir, os.mkdir]:
        for pf, pa in paths:
            try:
                p = pf(pa)
                # print(chk.__name__, p, pa)
                if not p or p.startswith("~"):
                    continue

                p = os.path.normpath(p)
                chk(p)  # type: ignore
                p = os.path.join(p, "copyparty")
                if not os.path.isdir(p):
                    os.mkdir(p)

                return p
            except:
                pass

    raise Exception("could not find a writable path for config")


class EnvParams(object):
    def __init__(self) -> None:
        self.t0 = time.time()
        self.mod = os.path.dirname(os.path.realpath(__file__))
        if self.mod.endswith("__init__"):
            self.mod = os.path.dirname(self.mod)

        if sys.platform == "win32":
            self.cfg = os.path.normpath(os.environ["APPDATA"] + "/copyparty")
        elif sys.platform == "darwin":
            self.cfg = os.path.expanduser("~/Library/Preferences/copyparty")
        else:
            self.cfg = get_unixdir()

        self.cfg = self.cfg.replace("\\", "/")
        try:
            os.makedirs(self.cfg)
        except:
            if not os.path.isdir(self.cfg):
                raise


E = EnvParams()

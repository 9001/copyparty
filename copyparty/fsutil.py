# coding: utf-8
from __future__ import print_function, unicode_literals

import ctypes
import re
import time

from .__init__ import ANYWIN, MACOS
from .authsrv import AXS, VFS
from .util import chkcmd, min_ex

try:
    from typing import Optional, Union

    from .util import RootLogger
except:
    pass


class Fstab(object):
    def __init__(self, log: RootLogger):
        self.log_func = log

        self.no_sparse = set(
            [
                "fuse",  # termux-sdcard
                "vfat",  # linux-efi
                "fat32",
                "fat16",
                "fat12",
                "fat-32",
                "fat-16",
                "fat-12",
                "fat 32",
                "fat 16",
                "fat 12",
                "exfat",
                "ex-fat",
                "ex fat",
                "hpfs",  # macos
            ]
        )
        self.tab: Optional[VFS] = None
        self.cache: dict[str, str] = {}
        self.age = 0.0

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func("fstab", msg + "\033[K", c)

    def get(self, path: str):
        if time.time() - self.age > 600 or len(self.cache) > 9000:
            self.age = time.time()
            self.tab = None
            self.cache = {}

        fs = "ext4"
        msg = "failed to determine filesystem at [{}]; assuming {}\n{}"

        if ANYWIN:
            fs = "vfat"  # can smb do sparse files? gonna guess no
            try:
                # good enough
                disk = path.split(":", 1)[0]
                disk = "{}:\\".format(disk).lower()
                assert len(disk) == 3
                path = disk
            except:
                self.log(msg.format(path, fs, min_ex()), 3)
                return fs

        try:
            return self.cache[path]
        except:
            pass

        try:
            fs = self.get_w32(path) if ANYWIN else self.get_unix(path)
        except:
            self.log(msg.format(path, fs, min_ex()), 3)

        fs = fs.lower()
        self.cache[path] = fs
        self.log("found {} at {}".format(fs, path))
        return fs

    def build_tab(self):
        self.log("building tab")

        sptn = r"^.*? on (.*) type ([^ ]+) \(.*"
        if MACOS:
            sptn = r"^.*? on (.*) \(([^ ]+), .*"

        ptn = re.compile(sptn)
        so, _ = chkcmd(["mount"])
        tab1: list[tuple[str, str]] = []
        for ln in so.split("\n"):
            m = ptn.match(ln)
            if not m:
                continue

            tab1.append(m.groups())

        tab1.sort(key=lambda x: (len(x[0]), x[0]))
        path1, fs1 = tab1[0]
        tab = VFS(self.log_func, fs1, path1, AXS(), {})
        for path, fs in tab1[1:]:
            tab.add(fs, path.lstrip("/"))

        self.tab = tab

    def get_unix(self, path: str):
        if not self.tab:
            self.build_tab()

        return self.tab._find(path)[0].realpath.split("/")[0]

    def get_w32(self, path: str):
        # list mountpoints: fsutil fsinfo drives

        from ctypes.wintypes import BOOL, DWORD, LPCWSTR, LPDWORD, LPWSTR, MAX_PATH

        def echk(rc, fun, args):
            if not rc:
                raise ctypes.WinError(ctypes.get_last_error())
            return None

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetVolumeInformationW.errcheck = echk
        k32.GetVolumeInformationW.restype = BOOL
        k32.GetVolumeInformationW.argtypes = (
            LPCWSTR,
            LPWSTR,
            DWORD,
            LPDWORD,
            LPDWORD,
            LPDWORD,
            LPWSTR,
            DWORD,
        )

        bvolname = ctypes.create_unicode_buffer(MAX_PATH + 1)
        bfstype = ctypes.create_unicode_buffer(MAX_PATH + 1)
        serial = DWORD()
        max_name_len = DWORD()
        fs_flags = DWORD()

        k32.GetVolumeInformationW(
            path,
            bvolname,
            ctypes.sizeof(bvolname),
            ctypes.byref(serial),
            ctypes.byref(max_name_len),
            ctypes.byref(fs_flags),
            bfstype,
            ctypes.sizeof(bfstype),
        )
        return bfstype.value

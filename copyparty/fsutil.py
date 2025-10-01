# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import os
import re
import time

from .__init__ import ANYWIN, MACOS
from .authsrv import AXS, VFS, AuthSrv
from .bos import bos
from .util import chkcmd, min_ex, undot

if True:  # pylint: disable=using-constant-test
    from typing import Optional, Union

    from .util import RootLogger, undot


class Fstab(object):
    def __init__(self, log: "RootLogger", args: argparse.Namespace, verbose: bool):
        self.log_func = log
        self.verbose = verbose

        self.warned = False
        self.trusted = False
        self.tab: Optional[VFS] = None
        self.oldtab: Optional[VFS] = None
        self.srctab = "a"
        self.cache: dict[str, tuple[str, str]] = {}
        self.age = 0.0
        self.maxage = args.mtab_age

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        if not c or self.verbose:
            return
        self.log_func("fstab", msg, c)

    def get(self, path: str) -> tuple[str, str]:
        now = time.time()
        if now - self.age > self.maxage or len(self.cache) > 9000:
            self.age = now
            self.oldtab = self.tab or self.oldtab
            self.tab = None
            self.cache = {}

        mp = ""
        fs = "ext4"
        msg = "failed to determine filesystem at %r; assuming %s\n%s"

        if ANYWIN:
            fs = "vfat"
            try:
                path = self._winpath(path)
            except:
                self.log(msg % (path, fs, min_ex()), 3)
                return fs, ""

        path = undot(path)
        try:
            return self.cache[path]
        except:
            pass

        try:
            fs, mp = self.get_w32(path) if ANYWIN else self.get_unix(path)
        except:
            self.log(msg % (path, fs, min_ex()), 3)

        fs = fs.lower()
        self.cache[path] = (fs, mp)
        self.log("found %s at %r, %r" % (fs, mp, path))
        return fs, mp

    def _winpath(self, path: str) -> str:
        # try to combine volume-label + st_dev (vsn)
        path = path.replace("/", "\\")
        vid = path.split(":", 1)[0].strip("\\").split("\\", 1)[0]
        try:
            return "{}*{}".format(vid, bos.stat(path).st_dev)
        except:
            return vid

    def build_fallback(self) -> None:
        self.tab = VFS(self.log_func, "idk", "/", "/", AXS(), {})
        self.trusted = False

    def _from_sp_mount(self) -> dict[str, str]:
        sptn = r"^.*? on (.*) type ([^ ]+) \(.*"
        if MACOS:
            sptn = r"^.*? on (.*) \(([^ ]+), .*"

        ptn = re.compile(sptn)
        so, _ = chkcmd(["mount"])
        dtab: dict[str, str] = {}
        for ln in so.split("\n"):
            m = ptn.match(ln)
            if not m:
                continue

            zs1, zs2 = m.groups()
            dtab[str(zs1)] = str(zs2)

        return dtab

    def _from_proc(self) -> dict[str, str]:
        ret: dict[str, str] = {}
        with open("/proc/self/mounts", "rb", 262144) as f:
            src = f.read(262144).decode("utf-8", "replace").split("\n")
        for zsl in [x.split(" ") for x in src]:
            if len(zsl) < 3:
                continue
            zs = zsl[1]
            zs = zs.replace("\\011", "\t").replace("\\040", " ").replace("\\134", "\\")
            ret[zs] = zsl[2]
        return ret

    def build_tab(self) -> None:
        self.log("inspecting mtab for changes")
        dtab = self._from_sp_mount() if MACOS else self._from_proc()

        # keep empirically-correct values if mounttab unchanged
        srctab = str(sorted(dtab.items()))
        if srctab == self.srctab:
            self.tab = self.oldtab
            return

        self.log("mtab has changed; reevaluating support for sparse files")

        tab1 = list(dtab.items())
        tab1.sort(key=lambda x: (len(x[0]), x[0]))
        path1, fs1 = tab1[0]
        tab = VFS(self.log_func, fs1, path1, path1, AXS(), {})
        for path, fs in tab1[1:]:
            zs = path.lstrip("/")
            tab.add(fs, zs, zs)

        self.tab = tab
        self.srctab = srctab

    def relabel(self, path: str, nval: str) -> None:
        assert self.tab  # !rm
        self.cache = {}
        if ANYWIN:
            path = self._winpath(path)

        path = undot(path)
        ptn = re.compile(r"^[^\\/]*")
        vn, rem = self.tab._find(path)
        if not self.trusted:
            # no mtab access; have to build as we go
            if "/" in rem:
                zs = os.path.join(vn.vpath, rem.split("/")[0])
                self.tab.add("idk", zs, zs)
            if rem:
                self.tab.add(nval, path, path)
            else:
                vn.realpath = nval

            return

        visit = [vn]
        while visit:
            vn = visit.pop()
            vn.realpath = ptn.sub(nval, vn.realpath)
            visit.extend(list(vn.nodes.values()))

    def get_unix(self, path: str) -> tuple[str, str]:
        if not self.tab:
            try:
                self.build_tab()
                self.trusted = True
            except:
                # prisonparty or other restrictive environment
                if not self.warned:
                    self.warned = True
                    t = "failed to associate fs-mounts with the VFS (this is fine):\n%s"
                    self.log(t % (min_ex(),), 6)
                self.build_fallback()

        assert self.tab  # !rm
        ret = self.tab._find(path)[0]
        if self.trusted or path == ret.vpath:
            return ret.realpath.split("/")[0], ret.vpath
        else:
            return "idk", ""

    def get_w32(self, path: str) -> tuple[str, str]:
        if not self.tab:
            self.build_fallback()

        assert self.tab  # !rm
        ret = self.tab._find(path)[0]
        return ret.realpath, ""


def ramdisk_chk(asrv: AuthSrv) -> None:
    # should have been in authsrv but that's a circular import
    mods = []
    ramfs = ("tmpfs", "overlay")
    log = asrv.log_func or print
    fstab = Fstab(log, asrv.args, False)
    for vn in asrv.vfs.all_nodes.values():
        if not vn.axs.uwrite or "wram" in vn.flags:
            continue
        ap = vn.realpath
        if not ap or os.path.isfile(ap):
            continue
        fs, mp = fstab.get(ap)
        mp = "/" + mp.strip("/")
        if fs == "tmpfs" or (mp == "/" and fs in ramfs):
            mods.append((vn.vpath, ap, fs, mp))
            vn.axs.uwrite.clear()
    if mods:
        t = "WARNING: write-access was removed from the following volumes because they are not mapped to an actual HDD for storage! All uploaded data would live in RAM only, and all uploaded files would be LOST on next reboot. To allow uploading and ignore this hazard, enable the 'wram' option (global/volflag). List of affected volumes:"
        t2 = ["\n  volume=[/%s], abspath=%r, type=%s, root=%r" % x for x in mods]
        log("vfs", t + "".join(t2) + "\n", 1)

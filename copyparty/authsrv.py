# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import base64
import hashlib
import os
import re
import stat
import sys
import threading
import time
from datetime import datetime

from .__init__ import ANYWIN, TYPE_CHECKING, WINDOWS, E
from .bos import bos
from .cfg import flagdescs, permdescs, vf_bmap, vf_cmap, vf_vmap
from .pwhash import PWHash
from .util import (
    IMPLICATIONS,
    META_NOBOTS,
    SQLITE_VER,
    UNPLICATIONS,
    ODict,
    Pebkac,
    UTC,
    absreal,
    afsenc,
    get_df,
    humansize,
    odfusion,
    relchk,
    statdir,
    uncyg,
    undot,
    unhumanize,
)

if True:  # pylint: disable=using-constant-test
    from collections.abc import Iterable

    from typing import Any, Generator, Optional, Union

    from .util import NamedLogger, RootLogger

if TYPE_CHECKING:
    from .broker_mp import BrokerMp
    from .broker_thr import BrokerThr
    from .broker_util import BrokerCli

    # Vflags: TypeAlias = dict[str, str | bool | float | list[str]]
    # Vflags: TypeAlias = dict[str, Any]
    # Mflags: TypeAlias = dict[str, Vflags]


LEELOO_DALLAS = "leeloo_dallas"

SEE_LOG = "see log for details"
SSEELOG = " ({})".format(SEE_LOG)
BAD_CFG = "invalid config; {}".format(SEE_LOG)
SBADCFG = " ({})".format(BAD_CFG)


class AXS(object):
    def __init__(
        self,
        uread: Optional[Union[list[str], set[str]]] = None,
        uwrite: Optional[Union[list[str], set[str]]] = None,
        umove: Optional[Union[list[str], set[str]]] = None,
        udel: Optional[Union[list[str], set[str]]] = None,
        uget: Optional[Union[list[str], set[str]]] = None,
        upget: Optional[Union[list[str], set[str]]] = None,
        uhtml: Optional[Union[list[str], set[str]]] = None,
        uadmin: Optional[Union[list[str], set[str]]] = None,
    ) -> None:
        self.uread: set[str] = set(uread or [])
        self.uwrite: set[str] = set(uwrite or [])
        self.umove: set[str] = set(umove or [])
        self.udel: set[str] = set(udel or [])
        self.uget: set[str] = set(uget or [])
        self.upget: set[str] = set(upget or [])
        self.uhtml: set[str] = set(uhtml or [])
        self.uadmin: set[str] = set(uadmin or [])

    def __repr__(self) -> str:
        ks = "uread uwrite umove udel uget upget uhtml uadmin".split()
        return "AXS(%s)" % (", ".join("%s=%r" % (k, self.__dict__[k]) for k in ks),)


class Lim(object):
    def __init__(self, log_func: Optional["RootLogger"]) -> None:
        self.log_func = log_func

        self.reg: Optional[dict[str, dict[str, Any]]] = None  # up2k registry

        self.nups: dict[str, list[float]] = {}  # num tracker
        self.bups: dict[str, list[tuple[float, int]]] = {}  # byte tracker list
        self.bupc: dict[str, int] = {}  # byte tracker cache

        self.nosub = False  # disallow subdirectories

        self.dfl = 0  # free disk space limit
        self.dft = 0  # last-measured time
        self.dfv = 0  # currently free
        self.vbmax = 0  # volume bytes max
        self.vnmax = 0  # volume max num files

        self.smin = 0  # filesize min
        self.smax = 0  # filesize max

        self.bwin = 0  # bytes window
        self.bmax = 0  # bytes max
        self.nwin = 0  # num window
        self.nmax = 0  # num max

        self.rotn = 0  # rot num files
        self.rotl = 0  # rot depth
        self.rotf = ""  # rot datefmt
        self.rot_re = re.compile("")  # rotf check

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        if self.log_func:
            self.log_func("up-lim", msg, c)

    def set_rotf(self, fmt: str) -> None:
        self.rotf = fmt
        r = re.escape(fmt).replace("%Y", "[0-9]{4}").replace("%j", "[0-9]{3}")
        r = re.sub("%[mdHMSWU]", "[0-9]{2}", r)
        self.rot_re = re.compile("(^|/)" + r + "$")

    def all(
        self,
        ip: str,
        rem: str,
        sz: int,
        ptop: str,
        abspath: str,
        broker: Optional[Union["BrokerCli", "BrokerMp", "BrokerThr"]] = None,
        reg: Optional[dict[str, dict[str, Any]]] = None,
        volgetter: str = "up2k.get_volsize",
    ) -> tuple[str, str]:
        if reg is not None and self.reg is None:
            self.reg = reg
            self.dft = 0

        self.chk_nup(ip)
        self.chk_bup(ip)
        self.chk_rem(rem)
        if sz != -1:
            self.chk_sz(sz)
            self.chk_vsz(broker, ptop, sz, volgetter)
            self.chk_df(abspath, sz)  # side effects; keep last-ish

        ap2, vp2 = self.rot(abspath)
        if abspath == ap2:
            return ap2, rem

        return ap2, ("{}/{}".format(rem, vp2) if rem else vp2)

    def chk_sz(self, sz: int) -> None:
        if sz < self.smin:
            raise Pebkac(400, "file too small")

        if self.smax and sz > self.smax:
            raise Pebkac(400, "file too big")

    def chk_vsz(
        self,
        broker: Optional[Union["BrokerCli", "BrokerMp", "BrokerThr"]],
        ptop: str,
        sz: int,
        volgetter: str = "up2k.get_volsize",
    ) -> None:
        if not broker or not self.vbmax + self.vnmax:
            return

        x = broker.ask(volgetter, ptop)
        nbytes, nfiles = x.get()

        if self.vbmax and self.vbmax < nbytes + sz:
            raise Pebkac(400, "volume has exceeded max size")

        if self.vnmax and self.vnmax < nfiles + 1:
            raise Pebkac(400, "volume has exceeded max num.files")

    def chk_df(self, abspath: str, sz: int, already_written: bool = False) -> None:
        if not self.dfl:
            return

        if self.dft < time.time():
            self.dft = int(time.time()) + 300
            self.dfv = get_df(abspath)[0] or 0
            for j in list(self.reg.values()) if self.reg else []:
                self.dfv -= int(j["size"] / len(j["hash"]) * len(j["need"]))

            if already_written:
                sz = 0

        if self.dfv - sz < self.dfl:
            self.dft = min(self.dft, int(time.time()) + 10)
            t = "server HDD is full; {} free, need {}"
            raise Pebkac(500, t.format(humansize(self.dfv - self.dfl), humansize(sz)))

        self.dfv -= int(sz)

    def chk_rem(self, rem: str) -> None:
        if self.nosub and rem:
            raise Pebkac(500, "no subdirectories allowed")

    def rot(self, path: str) -> tuple[str, str]:
        if not self.rotf and not self.rotn:
            return path, ""

        if self.rotf:
            path = path.rstrip("/\\")
            if self.rot_re.search(path.replace("\\", "/")):
                return path, ""

            suf = datetime.now(UTC).strftime(self.rotf)
            if path:
                path += "/"

            return path + suf, suf

        ret = self.dive(path, self.rotl)
        if not ret:
            raise Pebkac(500, "no available slots in volume")

        d = ret[len(path) :].strip("/\\").replace("\\", "/")
        return ret, d

    def dive(self, path: str, lvs: int) -> Optional[str]:
        items = bos.listdir(path)

        if not lvs:
            # at leaf level
            return None if len(items) >= self.rotn else ""

        dirs = [int(x) for x in items if x and all(y in "1234567890" for y in x)]
        dirs.sort()

        if not dirs:
            # no branches yet; make one
            sub = os.path.join(path, "0")
            bos.mkdir(sub)
        else:
            # try newest branch only
            sub = os.path.join(path, str(dirs[-1]))

        ret = self.dive(sub, lvs - 1)
        if ret is not None:
            return os.path.join(sub, ret)

        if len(dirs) >= self.rotn:
            # full branch or root
            return None

        # make a branch
        sub = os.path.join(path, str(dirs[-1] + 1))
        bos.mkdir(sub)
        ret = self.dive(sub, lvs - 1)
        if ret is None:
            raise Pebkac(500, "rotation bug")

        return os.path.join(sub, ret)

    def nup(self, ip: str) -> None:
        try:
            self.nups[ip].append(time.time())
        except:
            self.nups[ip] = [time.time()]

    def bup(self, ip: str, nbytes: int) -> None:
        v = (time.time(), nbytes)
        try:
            self.bups[ip].append(v)
            self.bupc[ip] += nbytes
        except:
            self.bups[ip] = [v]
            self.bupc[ip] = nbytes

    def chk_nup(self, ip: str) -> None:
        if not self.nmax or ip not in self.nups:
            return

        nups = self.nups[ip]
        cutoff = time.time() - self.nwin
        while nups and nups[0] < cutoff:
            nups.pop(0)

        if len(nups) >= self.nmax:
            raise Pebkac(429, "too many uploads")

    def chk_bup(self, ip: str) -> None:
        if not self.bmax or ip not in self.bups:
            return

        bups = self.bups[ip]
        cutoff = time.time() - self.bwin
        mark = self.bupc[ip]
        while bups and bups[0][0] < cutoff:
            mark -= bups.pop(0)[1]

        self.bupc[ip] = mark
        if mark >= self.bmax:
            raise Pebkac(429, "upload size limit exceeded")


class VFS(object):
    """single level in the virtual fs"""

    def __init__(
        self,
        log: Optional["RootLogger"],
        realpath: str,
        vpath: str,
        axs: AXS,
        flags: dict[str, Any],
    ) -> None:
        self.log = log
        self.realpath = realpath  # absolute path on host filesystem
        self.vpath = vpath  # absolute path in the virtual filesystem
        self.axs = axs
        self.flags = flags  # config options
        self.root = self
        self.dev = 0  # st_dev
        self.nodes: dict[str, VFS] = {}  # child nodes
        self.histtab: dict[str, str] = {}  # all realpath->histpath
        self.dbv: Optional[VFS] = None  # closest full/non-jump parent
        self.lim: Optional[Lim] = None  # upload limits; only set for dbv
        self.aread: dict[str, list[str]] = {}
        self.awrite: dict[str, list[str]] = {}
        self.amove: dict[str, list[str]] = {}
        self.adel: dict[str, list[str]] = {}
        self.aget: dict[str, list[str]] = {}
        self.apget: dict[str, list[str]] = {}
        self.ahtml: dict[str, list[str]] = {}
        self.aadmin: dict[str, list[str]] = {}

        if realpath:
            rp = realpath + ("" if realpath.endswith(os.sep) else os.sep)
            vp = vpath + ("/" if vpath else "")
            self.histpath = os.path.join(realpath, ".hist")  # db / thumbcache
            self.all_vols = {vpath: self}  # flattened recursive
            self.all_aps = [(rp, self)]
            self.all_vps = [(vp, self)]
        else:
            self.histpath = ""
            self.all_vols = {}
            self.all_aps = []
            self.all_vps = []

    def __repr__(self) -> str:
        return "VFS(%s)" % (
            ", ".join(
                "%s=%r" % (k, self.__dict__[k])
                for k in "realpath vpath axs flags".split()
            )
        )

    def get_all_vols(
        self,
        vols: dict[str, "VFS"],
        aps: list[tuple[str, "VFS"]],
        vps: list[tuple[str, "VFS"]],
    ) -> None:
        if self.realpath:
            vols[self.vpath] = self
            rp = self.realpath
            rp += "" if rp.endswith(os.sep) else os.sep
            vp = self.vpath + ("/" if self.vpath else "")
            aps.append((rp, self))
            vps.append((vp, self))

        for v in self.nodes.values():
            v.get_all_vols(vols, aps, vps)

    def add(self, src: str, dst: str) -> "VFS":
        """get existing, or add new path to the vfs"""
        assert not src.endswith("/")  # nosec
        assert not dst.endswith("/")  # nosec

        if "/" in dst:
            # requires breadth-first population (permissions trickle down)
            name, dst = dst.split("/", 1)
            if name in self.nodes:
                # exists; do not manipulate permissions
                return self.nodes[name].add(src, dst)

            vn = VFS(
                self.log,
                os.path.join(self.realpath, name) if self.realpath else "",
                "{}/{}".format(self.vpath, name).lstrip("/"),
                self.axs,
                self._copy_flags(name),
            )
            vn.dbv = self.dbv or self
            self.nodes[name] = vn
            return vn.add(src, dst)

        if dst in self.nodes:
            # leaf exists; return as-is
            return self.nodes[dst]

        # leaf does not exist; create and keep permissions blank
        vp = "{}/{}".format(self.vpath, dst).lstrip("/")
        vn = VFS(self.log, src, vp, AXS(), {})
        vn.dbv = self.dbv or self
        self.nodes[dst] = vn
        return vn

    def _copy_flags(self, name: str) -> dict[str, Any]:
        flags = {k: v for k, v in self.flags.items()}
        hist = flags.get("hist")
        if hist and hist != "-":
            zs = "{}/{}".format(hist.rstrip("/"), name)
            flags["hist"] = os.path.expanduser(zs) if zs.startswith("~") else zs

        return flags

    def bubble_flags(self) -> None:
        if self.dbv:
            for k, v in self.dbv.flags.items():
                if k not in ["hist"]:
                    self.flags[k] = v

        for n in self.nodes.values():
            n.bubble_flags()

    def _find(self, vpath: str) -> tuple["VFS", str]:
        """return [vfs,remainder]"""
        if vpath == "":
            return self, ""

        if "/" in vpath:
            name, rem = vpath.split("/", 1)
        else:
            name = vpath
            rem = ""

        if name in self.nodes:
            return self.nodes[name]._find(undot(rem))

        return self, vpath

    def can_access(
        self, vpath: str, uname: str
    ) -> tuple[bool, bool, bool, bool, bool, bool, bool]:
        """can Read,Write,Move,Delete,Get,Upget,Admin"""
        if vpath:
            vn, _ = self._find(undot(vpath))
        else:
            vn = self

        c = vn.axs
        return (
            uname in c.uread or "*" in c.uread,
            uname in c.uwrite or "*" in c.uwrite,
            uname in c.umove or "*" in c.umove,
            uname in c.udel or "*" in c.udel,
            uname in c.uget or "*" in c.uget,
            uname in c.upget or "*" in c.upget,
            uname in c.uadmin or "*" in c.uadmin,
        )
        # skip uhtml because it's rarely needed

    def get(
        self,
        vpath: str,
        uname: str,
        will_read: bool,
        will_write: bool,
        will_move: bool = False,
        will_del: bool = False,
        will_get: bool = False,
        err: int = 403,
    ) -> tuple["VFS", str]:
        """returns [vfsnode,fs_remainder] if user has the requested permissions"""
        if relchk(vpath):
            if self.log:
                self.log("vfs", "invalid relpath [{}]".format(vpath))
            raise Pebkac(422)

        cvpath = undot(vpath)
        vn, rem = self._find(cvpath)
        c: AXS = vn.axs

        for req, d, msg in [
            (will_read, c.uread, "read"),
            (will_write, c.uwrite, "write"),
            (will_move, c.umove, "move"),
            (will_del, c.udel, "delete"),
            (will_get, c.uget, "get"),
        ]:
            if req and (uname not in d and "*" not in d) and uname != LEELOO_DALLAS:
                if vpath != cvpath and vpath != "." and self.log:
                    ap = vn.canonical(rem)
                    t = "{} has no {} in [{}] => [{}] => [{}]"
                    self.log("vfs", t.format(uname, msg, vpath, cvpath, ap), 6)

                t = "you don't have {}-access for this location"
                raise Pebkac(err, t.format(msg))

        return vn, rem

    def get_dbv(self, vrem: str) -> tuple["VFS", str]:
        dbv = self.dbv
        if not dbv:
            return self, vrem

        tv = [self.vpath[len(dbv.vpath) :].lstrip("/"), vrem]
        vrem = "/".join([x for x in tv if x])
        return dbv, vrem

    def canonical(self, rem: str, resolve: bool = True) -> str:
        """returns the canonical path (fully-resolved absolute fs path)"""
        ap = self.realpath
        if rem:
            ap += "/" + rem

        return absreal(ap) if resolve else ap

    def dcanonical(self, rem: str) -> str:
        """resolves until the final component (filename)"""
        ap = self.realpath
        if rem:
            ap += "/" + rem

        ad, fn = os.path.split(ap)
        return os.path.join(absreal(ad), fn)

    def ls(
        self,
        rem: str,
        uname: str,
        scandir: bool,
        permsets: list[list[bool]],
        lstat: bool = False,
    ) -> tuple[str, list[tuple[str, os.stat_result]], dict[str, "VFS"]]:
        """return user-readable [fsdir,real,virt] items at vpath"""
        virt_vis = {}  # nodes readable by user
        abspath = self.canonical(rem)
        real = list(statdir(self.log, scandir, lstat, abspath))
        real.sort()
        if not rem:
            # no vfs nodes in the list of real inodes
            real = [x for x in real if x[0] not in self.nodes]

            for name, vn2 in sorted(self.nodes.items()):
                ok = False
                zx = vn2.axs
                axs = [zx.uread, zx.uwrite, zx.umove, zx.udel, zx.uget]
                for pset in permsets:
                    ok = True
                    for req, lst in zip(pset, axs):
                        if req and uname not in lst and "*" not in lst:
                            ok = False
                    if ok:
                        break

                if ok:
                    virt_vis[name] = vn2

        if ".hist" in abspath:
            p = abspath.replace("\\", "/") if WINDOWS else abspath
            if p.endswith("/.hist"):
                real = [x for x in real if not x[0].startswith("up2k.")]
            elif "/.hist/th/" in p:
                real = [x for x in real if not x[0].endswith("dir.txt")]

        return abspath, real, virt_vis

    def walk(
        self,
        rel: str,
        rem: str,
        seen: list[str],
        uname: str,
        permsets: list[list[bool]],
        dots: bool,
        scandir: bool,
        lstat: bool,
        subvols: bool = True,
    ) -> Generator[
        tuple[
            "VFS",
            str,
            str,
            str,
            list[tuple[str, os.stat_result]],
            list[tuple[str, os.stat_result]],
            dict[str, "VFS"],
        ],
        None,
        None,
    ]:
        """
        recursively yields from ./rem;
        rel is a unix-style user-defined vpath (not vfs-related)
        """

        fsroot, vfs_ls, vfs_virt = self.ls(rem, uname, scandir, permsets, lstat=lstat)
        dbv, vrem = self.get_dbv(rem)

        if (
            seen
            and (not fsroot.startswith(seen[-1]) or fsroot == seen[-1])
            and fsroot in seen
        ):
            if self.log:
                t = "bailing from symlink loop,\n  prev: {}\n  curr: {}\n  from: {}/{}"
                self.log("vfs.walk", t.format(seen[-1], fsroot, self.vpath, rem), 3)
            return

        if "xdev" in self.flags or "xvol" in self.flags:
            rm1 = []
            for le in vfs_ls:
                ap = absreal(os.path.join(fsroot, le[0]))
                vn2 = self.chk_ap(ap)
                if not vn2 or not vn2.get("", uname, True, False):
                    rm1.append(le)
            _ = [vfs_ls.remove(x) for x in rm1]  # type: ignore

        seen = seen[:] + [fsroot]
        rfiles = [x for x in vfs_ls if not stat.S_ISDIR(x[1].st_mode)]
        rdirs = [x for x in vfs_ls if stat.S_ISDIR(x[1].st_mode)]
        # if lstat: ignore folder symlinks since copyparty will never make those
        #            (and we definitely don't want to descend into them)

        rfiles.sort()
        rdirs.sort()

        yield dbv, vrem, rel, fsroot, rfiles, rdirs, vfs_virt

        for rdir, _ in rdirs:
            if not dots and rdir.startswith("."):
                continue

            wrel = (rel + "/" + rdir).lstrip("/")
            wrem = (rem + "/" + rdir).lstrip("/")
            for x in self.walk(
                wrel, wrem, seen, uname, permsets, dots, scandir, lstat, subvols
            ):
                yield x

        if not subvols:
            return

        for n, vfs in sorted(vfs_virt.items()):
            if not dots and n.startswith("."):
                continue

            wrel = (rel + "/" + n).lstrip("/")
            for x in vfs.walk(wrel, "", seen, uname, permsets, dots, scandir, lstat):
                yield x

    def zipgen(
        self,
        vpath: str,
        vrem: str,
        flt: set[str],
        uname: str,
        dots: bool,
        dirs: bool,
        scandir: bool,
        wrap: bool = True,
    ) -> Generator[dict[str, Any], None, None]:

        # if multiselect: add all items to archive root
        # if single folder: the folder itself is the top-level item
        folder = "" if flt or not wrap else (vpath.split("/")[-1].lstrip(".") or "top")

        g = self.walk(folder, vrem, [], uname, [[True, False]], dots, scandir, False)
        for _, _, vpath, apath, files, rd, vd in g:
            if flt:
                files = [x for x in files if x[0] in flt]

                rm1 = [x for x in rd if x[0] not in flt]
                _ = [rd.remove(x) for x in rm1]  # type: ignore

                rm2 = [x for x in vd.keys() if x not in flt]
                _ = [vd.pop(x) for x in rm2]

                flt = set()

            # print(repr([vpath, apath, [x[0] for x in files]]))
            fnames = [n[0] for n in files]
            vpaths = [vpath + "/" + n for n in fnames] if vpath else fnames
            apaths = [os.path.join(apath, n) for n in fnames]
            ret = list(zip(vpaths, apaths, files))

            if not dots:
                # dotfile filtering based on vpath (intended visibility)
                ret = [x for x in ret if "/." not in "/" + x[0]]

                zel = [ze for ze in rd if ze[0].startswith(".")]
                for ze in zel:
                    rd.remove(ze)

                zsl = [zs for zs in vd.keys() if zs.startswith(".")]
                for zs in zsl:
                    del vd[zs]

            for f in [{"vp": v, "ap": a, "st": n[1]} for v, a, n in ret]:
                yield f

            if not dirs:
                continue

            ts = int(time.time())
            st = os.stat_result((16877, -1, -1, 1, 1000, 1000, 8, ts, ts, ts))
            dnames = [n[0] for n in rd]
            dstats = [n[1] for n in rd]
            dnames += list(vd.keys())
            dstats += [st] * len(vd)
            vpaths = [vpath + "/" + n for n in dnames] if vpath else dnames
            apaths = [os.path.join(apath, n) for n in dnames]
            ret2 = list(zip(vpaths, apaths, dstats))
            for d in [{"vp": v, "ap": a, "st": n} for v, a, n in ret2]:
                yield d

    def chk_ap(self, ap: str, st: Optional[os.stat_result] = None) -> Optional["VFS"]:
        aps = ap + os.sep
        if "xdev" in self.flags and not ANYWIN:
            if not st:
                ap2 = ap.replace("\\", "/") if ANYWIN else ap
                while ap2:
                    try:
                        st = bos.stat(ap2)
                        break
                    except:
                        if "/" not in ap2:
                            raise
                        ap2 = ap2.rsplit("/", 1)[0]
                assert st

            vdev = self.dev
            if not vdev:
                vdev = self.dev = bos.stat(self.realpath).st_dev

            if vdev != st.st_dev:
                if self.log:
                    t = "xdev: {}[{}] => {}[{}]"
                    self.log("vfs", t.format(vdev, self.realpath, st.st_dev, ap), 3)

                return None

        if "xvol" in self.flags:
            for vap, vn in self.root.all_aps:
                if aps.startswith(vap):
                    return vn

            if self.log:
                self.log("vfs", "xvol: [{}]".format(ap), 3)

            return None

        return self


if WINDOWS:
    re_vol = re.compile(r"^([a-zA-Z]:[\\/][^:]*|[^:]*):([^:]*):(.*)$")
else:
    re_vol = re.compile(r"^([^:]*):([^:]*):(.*)$")


class AuthSrv(object):
    """verifies users against given paths"""

    def __init__(
        self,
        args: argparse.Namespace,
        log_func: Optional["RootLogger"],
        warn_anonwrite: bool = True,
        dargs: Optional[argparse.Namespace] = None,
    ) -> None:
        self.ah = PWHash(args)
        self.args = args
        self.dargs = dargs or args
        self.log_func = log_func
        self.warn_anonwrite = warn_anonwrite
        self.line_ctr = 0
        self.indent = ""
        self.desc = []

        self.mutex = threading.Lock()
        self.reload()

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        if self.log_func:
            self.log_func("auth", msg, c)

    def laggy_iter(self, iterable: Iterable[Any]) -> Generator[Any, None, None]:
        """returns [value,isFinalValue]"""
        it = iter(iterable)
        prev = next(it)
        for x in it:
            yield prev, False
            prev = x

        yield prev, True

    def _map_volume(
        self,
        src: str,
        dst: str,
        mount: dict[str, str],
        daxs: dict[str, AXS],
        mflags: dict[str, dict[str, Any]],
    ) -> None:
        if dst in mount:
            t = "multiple filesystem-paths mounted at [/{}]:\n  [{}]\n  [{}]"
            self.log(t.format(dst, mount[dst], src), c=1)
            raise Exception(BAD_CFG)

        if src in mount.values():
            t = "filesystem-path [{}] mounted in multiple locations:"
            t = t.format(src)
            for v in [k for k, v in mount.items() if v == src] + [dst]:
                t += "\n  /{}".format(v)

            self.log(t, c=3)
            raise Exception(BAD_CFG)

        if not bos.path.isdir(src):
            self.log("warning: filesystem-path does not exist: {}".format(src), 3)

        mount[dst] = src
        daxs[dst] = AXS()
        mflags[dst] = {}

    def _e(self, desc: Optional[str] = None) -> None:
        if not self.args.vc or not self.line_ctr:
            return

        if not desc and not self.indent:
            self.log("")
            return

        desc = desc or ""
        desc = desc.replace("[", "[\033[0m").replace("]", "\033[90m]")
        self.log(" >>> {}{}".format(self.indent, desc), "90")

    def _l(self, ln: str, c: int, desc: str) -> None:
        if not self.args.vc or not self.line_ctr:
            return

        if c < 10:
            c += 30

        t = "\033[97m{:4} \033[{}m{}{}"
        if desc:
            t += "  \033[0;90m# {}\033[0m"
            desc = desc.replace("[", "[\033[0m").replace("]", "\033[90m]")

        self.log(t.format(self.line_ctr, c, self.indent, ln, desc))

    def _parse_config_file(
        self,
        fp: str,
        cfg_lines: list[str],
        acct: dict[str, str],
        daxs: dict[str, AXS],
        mflags: dict[str, dict[str, Any]],
        mount: dict[str, str],
    ) -> None:
        self.desc = []
        self.line_ctr = 0

        expand_config_file(cfg_lines, fp, "")
        if self.args.vc:
            lns = ["{:4}: {}".format(n, s) for n, s in enumerate(cfg_lines, 1)]
            self.log("expanded config file (unprocessed):\n" + "\n".join(lns))

        cfg_lines = upgrade_cfg_fmt(self.log, self.args, cfg_lines, fp)

        cat = ""
        catg = "[global]"
        cata = "[accounts]"
        catx = "accs:"
        catf = "flags:"
        ap: Optional[str] = None
        vp: Optional[str] = None
        for ln in cfg_lines:
            self.line_ctr += 1
            ln = ln.split("  #")[0].strip()
            if not ln.split("#")[0].strip():
                continue

            if re.match(r"^\[.*\]:$", ln):
                ln = ln[:-1]

            subsection = ln in (catx, catf)
            if ln.startswith("[") or subsection:
                self._e()
                if ap is None and vp is not None:
                    t = "the first line after [/{}] must be a filesystem path to share on that volume"
                    raise Exception(t.format(vp))

                cat = ln
                if not subsection:
                    ap = vp = None
                    self.indent = ""
                else:
                    self.indent = "  "

                if ln == catg:
                    t = "begin commandline-arguments (anything from --help; dashes are optional)"
                    self._l(ln, 6, t)
                elif ln == cata:
                    self._l(ln, 5, "begin user-accounts section")
                elif ln.startswith("[/"):
                    vp = ln[1:-1].strip("/")
                    self._l(ln, 2, "define volume at URL [/{}]".format(vp))
                elif subsection:
                    if ln == catx:
                        self._l(ln, 5, "volume access config:")
                    else:
                        t = "volume-specific config (anything from --help-flags)"
                        self._l(ln, 6, t)
                else:
                    raise Exception("invalid section header" + SBADCFG)

                self.indent = "    " if subsection else "  "
                continue

            if cat == catg:
                self._l(ln, 6, "")
                zt = split_cfg_ln(ln)
                for zs, za in zt.items():
                    zs = zs.lstrip("-")
                    if za is True:
                        self._e("└─argument [{}]".format(zs))
                    else:
                        self._e("└─argument [{}] with value [{}]".format(zs, za))
                continue

            if cat == cata:
                try:
                    u, p = [zs.strip() for zs in ln.split(":", 1)]
                    self._l(ln, 5, "account [{}], password [{}]".format(u, p))
                    acct[u] = p
                except:
                    t = 'lines inside the [accounts] section must be "username: password"'
                    raise Exception(t + SBADCFG)
                continue

            if vp is not None and ap is None:
                ap = ln
                if ap.startswith("~"):
                    ap = os.path.expanduser(ap)

                ap = absreal(ap)
                self._l(ln, 2, "bound to filesystem-path [{}]".format(ap))
                self._map_volume(ap, vp, mount, daxs, mflags)
                continue

            if cat == catx:
                err = ""
                try:
                    self._l(ln, 5, "volume access config:")
                    sk, sv = ln.split(":")
                    if re.sub("[rwmdgGha]", "", sk) or not sk:
                        err = "invalid accs permissions list; "
                        raise Exception(err)
                    if " " in re.sub(", *", "", sv).strip():
                        err = "list of users is not comma-separated; "
                        raise Exception(err)
                    self._read_vol_str(sk, sv.replace(" ", ""), daxs[vp], mflags[vp])
                    continue
                except:
                    err += "accs entries must be 'rwmdgGha: user1, user2, ...'"
                    raise Exception(err + SBADCFG)

            if cat == catf:
                err = ""
                try:
                    self._l(ln, 6, "volume-specific config:")
                    zd = split_cfg_ln(ln)
                    fstr = ""
                    for sk, sv in zd.items():
                        bad = re.sub(r"[a-z0-9_-]", "", sk).lstrip("-")
                        if bad:
                            err = "bad characters [{}] in volflag name [{}]; "
                            err = err.format(bad, sk)
                            raise Exception(err + SBADCFG)
                        if sv is True:
                            fstr += "," + sk
                        else:
                            fstr += ",{}={}".format(sk, sv)
                            self._read_vol_str("c", fstr[1:], daxs[vp], mflags[vp])
                            fstr = ""
                    if fstr:
                        self._read_vol_str("c", fstr[1:], daxs[vp], mflags[vp])
                    continue
                except:
                    err += "flags entries (volflags) must be one of the following:\n  'flag1, flag2, ...'\n  'key: value'\n  'flag1, flag2, key: value'"
                    raise Exception(err + SBADCFG)

            raise Exception("unprocessable line in config" + SBADCFG)

        self._e()
        self.line_ctr = 0

    def _read_vol_str(
        self, lvl: str, uname: str, axs: AXS, flags: dict[str, Any]
    ) -> None:
        if lvl.strip("crwmdgGha"):
            raise Exception("invalid volflag: {},{}".format(lvl, uname))

        if lvl == "c":
            cval: Union[bool, str] = True
            try:
                # volflag with arguments, possibly with a preceding list of bools
                uname, cval = uname.split("=", 1)
            except:
                # just one or more bools
                pass

            while "," in uname:
                # one or more bools before the final flag; eat them
                n1, uname = uname.split(",", 1)
                self._read_volflag(flags, n1, True, False)

            self._read_volflag(flags, uname, cval, False)
            return

        if uname == "":
            uname = "*"

        for un in uname.replace(",", " ").strip().split():
            for ch, al in [
                ("r", axs.uread),
                ("w", axs.uwrite),
                ("m", axs.umove),
                ("d", axs.udel),
                ("a", axs.uadmin),
                ("h", axs.uhtml),
                ("h", axs.uget),
                ("g", axs.uget),
                ("G", axs.uget),
                ("G", axs.upget),
            ]:  # b bb bbb
                if ch in lvl:
                    if un == "*":
                        t = "└─add permission [{0}] for [everyone] -- {2}"
                    else:
                        t = "└─add permission [{0}] for user [{1}] -- {2}"

                    desc = permdescs.get(ch, "?")
                    self._e(t.format(ch, un, desc))
                    al.add(un)

    def _read_volflag(
        self,
        flags: dict[str, Any],
        name: str,
        value: Union[str, bool, list[str]],
        is_list: bool,
    ) -> None:
        desc = flagdescs.get(name.lstrip("-"), "?").replace("\n", " ")

        if re.match("^-[^-]+$", name):
            t = "└─unset volflag [{}]  ({})"
            self._e(t.format(name[1:], desc))
            flags[name] = True
            return

        zs = "mtp on403 on404 xbu xau xiu xbr xar xbd xad xm xban"
        if name not in zs.split():
            if value is True:
                t = "└─add volflag [{}] = {}  ({})"
            else:
                t = "└─add volflag [{}] = [{}]  ({})"
            self._e(t.format(name, value, desc))
            flags[name] = value
            return

        vals = flags.get(name, [])
        if not value:
            return
        elif is_list:
            vals += value
        else:
            vals += [value]

        flags[name] = vals
        self._e("volflag [{}] += {}  ({})".format(name, vals, desc))

    def reload(self) -> None:
        """
        construct a flat list of mountpoints and usernames
        first from the commandline arguments
        then supplementing with config files
        before finally building the VFS
        """

        acct: dict[str, str] = {}  # username:password
        daxs: dict[str, AXS] = {}
        mflags: dict[str, dict[str, Any]] = {}  # moutpoint:flags
        mount: dict[str, str] = {}  # dst:src (mountpoint:realpath)

        if self.args.a:
            # list of username:password
            for x in self.args.a:
                try:
                    u, p = x.split(":", 1)
                    acct[u] = p
                except:
                    t = '\n  invalid value "{}" for argument -a, must be username:password'
                    raise Exception(t.format(x))

        if self.args.v:
            # list of src:dst:permset:permset:...
            # permset is <rwmdgGha>[,username][,username] or <c>,<flag>[=args]
            for v_str in self.args.v:
                m = re_vol.match(v_str)
                if not m:
                    raise Exception("invalid -v argument: [{}]".format(v_str))

                src, dst, perms = m.groups()
                if WINDOWS:
                    src = uncyg(src)

                # print("\n".join([src, dst, perms]))
                src = absreal(src)
                dst = dst.strip("/")
                self._map_volume(src, dst, mount, daxs, mflags)

                for x in perms.split(":"):
                    lvl, uname = x.split(",", 1) if "," in x else [x, ""]
                    self._read_vol_str(lvl, uname, daxs[dst], mflags[dst])

        if self.args.c:
            for cfg_fn in self.args.c:
                lns: list[str] = []
                try:
                    self._parse_config_file(cfg_fn, lns, acct, daxs, mflags, mount)

                    zs = "#\033[36m cfg files in "
                    zst = [x[len(zs) :] for x in lns if x.startswith(zs)]
                    for zs in list(set(zst)):
                        self.log("discovered config files in " + zs, 6)

                    zs = "#\033[36m opening cfg file"
                    zstt = [x.split(" -> ") for x in lns if x.startswith(zs)]
                    zst = [(max(0, len(x) - 2) * " ") + "└" + x[-1] for x in zstt]
                    t = "loaded {} config files:\n{}"
                    self.log(t.format(len(zst), "\n".join(zst)))

                except:
                    lns = lns[: self.line_ctr]
                    slns = ["{:4}: {}".format(n, s) for n, s in enumerate(lns, 1)]
                    t = "\033[1;31m\nerror @ line {}, included from {}\033[0m"
                    t = t.format(self.line_ctr, cfg_fn)
                    self.log("\n{0}\n{1}{0}".format(t, "\n".join(slns)))
                    raise

        self.setup_pwhash(acct)

        # case-insensitive; normalize
        if WINDOWS:
            cased = {}
            for k, v in mount.items():
                cased[k] = absreal(v)

            mount = cased

        if not mount:
            # -h says our defaults are CWD at root and read/write for everyone
            axs = AXS(["*"], ["*"], None, None)
            vfs = VFS(self.log_func, absreal("."), "", axs, {})
        elif "" not in mount:
            # there's volumes but no root; make root inaccessible
            vfs = VFS(self.log_func, "", "", AXS(), {})
            vfs.flags["d2d"] = True

        maxdepth = 0
        for dst in sorted(mount.keys(), key=lambda x: (x.count("/"), len(x))):
            depth = dst.count("/")
            assert maxdepth <= depth  # nosec
            maxdepth = depth

            if dst == "":
                # rootfs was mapped; fully replaces the default CWD vfs
                vfs = VFS(self.log_func, mount[dst], dst, daxs[dst], mflags[dst])
                continue

            zv = vfs.add(mount[dst], dst)
            zv.axs = daxs[dst]
            zv.flags = mflags[dst]
            zv.dbv = None

        assert vfs
        vfs.all_vols = {}
        vfs.all_aps = []
        vfs.all_vps = []
        vfs.get_all_vols(vfs.all_vols, vfs.all_aps, vfs.all_vps)
        for vol in vfs.all_vols.values():
            vol.all_aps.sort(key=lambda x: len(x[0]), reverse=True)
            vol.all_vps.sort(key=lambda x: len(x[0]), reverse=True)
            vol.root = vfs

        for perm in "read write move del get pget html admin".split():
            axs_key = "u" + perm
            unames = ["*"] + list(acct.keys())
            umap: dict[str, list[str]] = {x: [] for x in unames}
            for usr in unames:
                for vp, vol in vfs.all_vols.items():
                    zx = getattr(vol.axs, axs_key)
                    if usr in zx or "*" in zx:
                        umap[usr].append(vp)
                umap[usr].sort()
            setattr(vfs, "a" + perm, umap)

        all_users = {}
        missing_users = {}
        for axs in daxs.values():
            for d in [
                axs.uread,
                axs.uwrite,
                axs.umove,
                axs.udel,
                axs.uget,
                axs.upget,
                axs.uhtml,
                axs.uadmin,
            ]:
                for usr in d:
                    all_users[usr] = 1
                    if usr != "*" and usr not in acct:
                        missing_users[usr] = 1

        if missing_users:
            self.log(
                "you must -a the following users: "
                + ", ".join(k for k in sorted(missing_users)),
                c=1,
            )
            raise Exception(BAD_CFG)

        if LEELOO_DALLAS in all_users:
            raise Exception("sorry, reserved username: " + LEELOO_DALLAS)

        seenpwds = {}
        for usr, pwd in acct.items():
            if pwd in seenpwds:
                t = "accounts [{}] and [{}] have the same password; this is not supported"
                self.log(t.format(seenpwds[pwd], usr), 1)
                raise Exception(BAD_CFG)
            seenpwds[pwd] = usr

        promote = []
        demote = []
        for vol in vfs.all_vols.values():
            zb = hashlib.sha512(afsenc(vol.realpath)).digest()
            hid = base64.b32encode(zb).decode("ascii").lower()
            vflag = vol.flags.get("hist")
            if vflag == "-":
                pass
            elif vflag:
                if vflag.startswith("~"):
                    vflag = os.path.expanduser(vflag)

                vol.histpath = uncyg(vflag) if WINDOWS else vflag
            elif self.args.hist:
                for nch in range(len(hid)):
                    hpath = os.path.join(self.args.hist, hid[: nch + 1])
                    bos.makedirs(hpath)

                    powner = os.path.join(hpath, "owner.txt")
                    try:
                        with open(powner, "rb") as f:
                            owner = f.read().rstrip()
                    except:
                        owner = None

                    me = afsenc(vol.realpath).rstrip()
                    if owner not in [None, me]:
                        continue

                    if owner is None:
                        with open(powner, "wb") as f:
                            f.write(me)

                    vol.histpath = hpath
                    break

            vol.histpath = absreal(vol.histpath)
            if vol.dbv:
                if bos.path.exists(os.path.join(vol.histpath, "up2k.db")):
                    promote.append(vol)
                    vol.dbv = None
                else:
                    demote.append(vol)

        # discard jump-vols
        for zv in demote:
            vfs.all_vols.pop(zv.vpath)

        if promote:
            ta = [
                "\n  the following jump-volumes were generated to assist the vfs.\n  As they contain a database (probably from v0.11.11 or older),\n  they are promoted to full volumes:"
            ]
            for vol in promote:
                ta.append(
                    "  /{}  ({})  ({})".format(vol.vpath, vol.realpath, vol.histpath)
                )

            self.log("\n\n".join(ta) + "\n", c=3)

        vfs.histtab = {zv.realpath: zv.histpath for zv in vfs.all_vols.values()}

        for vol in vfs.all_vols.values():
            lim = Lim(self.log_func)
            use = False

            if vol.flags.get("nosub"):
                use = True
                lim.nosub = True

            zs = vol.flags.get("df") or (
                "{}g".format(self.args.df) if self.args.df else ""
            )
            if zs:
                use = True
                lim.dfl = unhumanize(zs)

            zs = vol.flags.get("sz")
            if zs:
                use = True
                lim.smin, lim.smax = [unhumanize(x) for x in zs.split("-")]

            zs = vol.flags.get("rotn")
            if zs:
                use = True
                lim.rotn, lim.rotl = [int(x) for x in zs.split(",")]

            zs = vol.flags.get("rotf")
            if zs:
                use = True
                lim.set_rotf(zs)

            zs = vol.flags.get("maxn")
            if zs:
                use = True
                lim.nmax, lim.nwin = [int(x) for x in zs.split(",")]

            zs = vol.flags.get("maxb")
            if zs:
                use = True
                lim.bmax, lim.bwin = [unhumanize(x) for x in zs.split(",")]

            zs = vol.flags.get("vmaxb")
            if zs:
                use = True
                lim.vbmax = unhumanize(zs)

            zs = vol.flags.get("vmaxn")
            if zs:
                use = True
                lim.vnmax = unhumanize(zs)

            if use:
                vol.lim = lim

        if self.args.no_robots:
            for vol in vfs.all_vols.values():
                # volflag "robots" overrides global "norobots", allowing indexing by search engines for this vol
                if not vol.flags.get("robots"):
                    vol.flags["norobots"] = True

        for vol in vfs.all_vols.values():
            h = [vol.flags.get("html_head", self.args.html_head)]
            if vol.flags.get("norobots"):
                h.insert(0, META_NOBOTS)

            vol.flags["html_head"] = "\n".join([x for x in h if x])

        for vol in vfs.all_vols.values():
            if self.args.no_vthumb:
                vol.flags["dvthumb"] = True
            if self.args.no_athumb:
                vol.flags["dathumb"] = True
            if self.args.no_thumb or vol.flags.get("dthumb", False):
                vol.flags["dthumb"] = True
                vol.flags["dvthumb"] = True
                vol.flags["dathumb"] = True
                vol.flags["dithumb"] = True

        have_fk = False
        for vol in vfs.all_vols.values():
            fk = vol.flags.get("fk")
            fka = vol.flags.get("fka")
            if fka and not fk:
                fk = fka
            if fk:
                vol.flags["fk"] = int(fk) if fk is not True else 8
                have_fk = True

        if have_fk and re.match(r"^[0-9\.]+$", self.args.fk_salt):
            self.log("filekey salt: {}".format(self.args.fk_salt))

        fk_len = len(self.args.fk_salt)
        if have_fk and fk_len < 14:
            t = "WARNING: filekeys are enabled, but the salt is only %d chars long; %d or longer is recommended. Either specify a stronger salt using --fk-salt or delete this file and restart copyparty: %s"
            zs = os.path.join(E.cfg, "fk-salt.txt")
            self.log(t % (fk_len, 16, zs), 3)

        for vol in vfs.all_vols.values():
            if "pk" in vol.flags and "gz" not in vol.flags and "xz" not in vol.flags:
                vol.flags["gz"] = False  # def.pk

            if "scan" in vol.flags:
                vol.flags["scan"] = int(vol.flags["scan"])
            elif self.args.re_maxage:
                vol.flags["scan"] = self.args.re_maxage

        all_mte = {}
        errors = False
        for vol in vfs.all_vols.values():
            if (self.args.e2ds and vol.axs.uwrite) or self.args.e2dsa:
                vol.flags["e2ds"] = True

            if self.args.e2d or "e2ds" in vol.flags:
                vol.flags["e2d"] = True

            for ga, vf in [["no_hash", "nohash"], ["no_idx", "noidx"]]:
                if vf in vol.flags:
                    ptn = re.compile(vol.flags.pop(vf))
                else:
                    ptn = getattr(self.args, ga)

                if ptn:
                    vol.flags[vf] = ptn

            for ga, vf in vf_bmap().items():
                if getattr(self.args, ga):
                    vol.flags[vf] = True

            for ve, vd in (
                ("nodotsrch", "dotsrch"),
                ("sb_lg", "no_sb_lg"),
                ("sb_md", "no_sb_md"),
            ):
                if ve in vol.flags:
                    vol.flags.pop(vd, None)

            for ga, vf in vf_vmap().items():
                if vf not in vol.flags:
                    vol.flags[vf] = getattr(self.args, ga)

            for k in ("nrand",):
                if k not in vol.flags:
                    vol.flags[k] = getattr(self.args, k)

            for k in ("nrand",):
                if k in vol.flags:
                    vol.flags[k] = int(vol.flags[k])

            for k in ("convt",):
                if k in vol.flags:
                    vol.flags[k] = float(vol.flags[k])

            for k1, k2 in IMPLICATIONS:
                if k1 in vol.flags:
                    vol.flags[k2] = True

            for k1, k2 in UNPLICATIONS:
                if k1 in vol.flags:
                    vol.flags[k2] = False

            dbds = "acid|swal|wal|yolo"
            vol.flags["dbd"] = dbd = vol.flags.get("dbd") or self.args.dbd
            if dbd not in dbds.split("|"):
                t = "invalid dbd [{}]; must be one of [{}]"
                raise Exception(t.format(dbd, dbds))

            # default tag cfgs if unset
            for k in ("mte", "mth", "exp_md", "exp_lg"):
                if k not in vol.flags:
                    vol.flags[k] = getattr(self.args, k).copy()
                else:
                    vol.flags[k] = odfusion(getattr(self.args, k), vol.flags[k])

            # append additive args from argv to volflags
            hooks = "xbu xau xiu xbr xar xbd xad xm xban".split()
            for name in "mtp on404 on403".split() + hooks:
                self._read_volflag(vol.flags, name, getattr(self.args, name), True)

            for hn in hooks:
                cmds = vol.flags.get(hn)
                if not cmds:
                    continue

                ncmds = []
                for cmd in cmds:
                    hfs = []
                    ocmd = cmd
                    while "," in cmd[:6]:
                        zs, cmd = cmd.split(",", 1)
                        hfs.append(zs)

                    if "c" in hfs and "f" in hfs:
                        t = "cannot combine flags c and f; removing f from eventhook [{}]"
                        self.log(t.format(ocmd), 1)
                        hfs = [x for x in hfs if x != "f"]
                        ocmd = ",".join(hfs + [cmd])

                    if "c" not in hfs and "f" not in hfs and hn == "xban":
                        hfs = ["c"] + hfs
                        ocmd = ",".join(hfs + [cmd])

                    ncmds.append(ocmd)
                vol.flags[hn] = ncmds

            # d2d drops all database features for a volume
            for grp, rm in [["d2d", "e2d"], ["d2t", "e2t"], ["d2d", "e2v"]]:
                if not vol.flags.get(grp, False):
                    continue

                vol.flags["d2t"] = True
                vol.flags = {k: v for k, v in vol.flags.items() if not k.startswith(rm)}

            # d2ds drops all onboot scans for a volume
            for grp, rm in [["d2ds", "e2ds"], ["d2ts", "e2ts"]]:
                if not vol.flags.get(grp, False):
                    continue

                vol.flags["d2ts"] = True
                vol.flags = {k: v for k, v in vol.flags.items() if not k.startswith(rm)}

            # mt* needs e2t so drop those too
            for grp, rm in [["e2t", "mt"]]:
                if vol.flags.get(grp, False):
                    continue

                vol.flags = {
                    k: v
                    for k, v in vol.flags.items()
                    if not k.startswith(rm) or k == "mte"
                }

            for grp, rm in [["d2v", "e2v"]]:
                if not vol.flags.get(grp, False):
                    continue

                vol.flags = {k: v for k, v in vol.flags.items() if not k.startswith(rm)}

            ints = ["lifetime"]
            for k in list(vol.flags):
                if k in ints:
                    vol.flags[k] = int(vol.flags[k])

            if "e2d" not in vol.flags:
                if "lifetime" in vol.flags:
                    t = 'removing lifetime config from volume "/{}" because e2d is disabled'
                    self.log(t.format(vol.vpath), 1)
                    del vol.flags["lifetime"]

                needs_e2d = [x for x in hooks if x != "xm"]
                drop = [x for x in needs_e2d if vol.flags.get(x)]
                if drop:
                    t = 'removing [{}] from volume "/{}" because e2d is disabled'
                    self.log(t.format(", ".join(drop), vol.vpath), 1)
                    for x in drop:
                        vol.flags.pop(x)

            if vol.flags.get("neversymlink") and not vol.flags.get("hardlink"):
                vol.flags["copydupes"] = True

            # verify tags mentioned by -mt[mp] are used by -mte
            local_mtp = {}
            local_only_mtp = {}
            tags = vol.flags.get("mtp", []) + vol.flags.get("mtm", [])
            tags = [x.split("=")[0] for x in tags]
            tags = [y for x in tags for y in x.split(",")]
            for a in tags:
                local_mtp[a] = True
                local = True
                for b in self.args.mtp or []:
                    b = b.split("=")[0]
                    if a == b:
                        local = False

                if local:
                    local_only_mtp[a] = True

            local_mte = ODict()
            for a in vol.flags.get("mte", {}).keys():
                local = True
                all_mte[a] = True
                local_mte[a] = True
                for b in self.args.mte.keys():
                    if not a or not b:
                        continue

                    if a == b:
                        local = False

            for mtp in local_only_mtp:
                if mtp not in local_mte:
                    t = 'volume "/{}" defines metadata tag "{}", but doesnt use it in "-mte" (or with "cmte" in its volflags)'
                    self.log(t.format(vol.vpath, mtp), 1)
                    errors = True

        tags = self.args.mtp or []
        tags = [x.split("=")[0] for x in tags]
        tags = [y for x in tags for y in x.split(",")]
        for mtp in tags:
            if mtp not in all_mte:
                t = 'metadata tag "{}" is defined by "-mtm" or "-mtp", but is not used by "-mte" (or by any "cmte" volflag)'
                self.log(t.format(mtp), 1)
                errors = True

        have_daw = False
        for vol in vfs.all_vols.values():
            daw = vol.flags.get("daw") or self.args.daw
            if daw:
                vol.flags["daw"] = True
                have_daw = True

        if have_daw and self.args.no_dav:
            t = 'volume "/{}" has volflag "daw" (webdav write-access), but --no-dav is set'
            self.log(t, 1)
            errors = True

        if self.args.smb and self.ah.on and acct:
            self.log("--smb can only be used when --ah-alg is none", 1)
            errors = True

        for vol in vfs.all_vols.values():
            for k in list(vol.flags.keys()):
                if re.match("^-[^-]+$", k):
                    vol.flags.pop(k[1:], None)
                    vol.flags.pop(k)

        if errors:
            sys.exit(1)

        vfs.bubble_flags()

        have_e2d = False
        have_e2t = False
        t = "volumes and permissions:\n"
        for zv in vfs.all_vols.values():
            if not self.warn_anonwrite:
                break

            t += '\n\033[36m"/{}"  \033[33m{}\033[0m'.format(zv.vpath, zv.realpath)
            for txt, attr in [
                ["  read", "uread"],
                [" write", "uwrite"],
                ["  move", "umove"],
                ["delete", "udel"],
                ["   get", "uget"],
                [" upget", "upget"],
                ["  html", "uhtml"],
                ["uadmin", "uadmin"],
            ]:
                u = list(sorted(getattr(zv.axs, attr)))
                u = ", ".join("\033[35meverybody\033[0m" if x == "*" else x for x in u)
                u = u if u else "\033[36m--none--\033[0m"
                t += "\n|  {}:  {}".format(txt, u)

            if "e2d" in zv.flags:
                have_e2d = True

            if "e2t" in zv.flags:
                have_e2t = True

            t += "\n"

        if self.warn_anonwrite:
            if not self.args.no_voldump:
                self.log(t)

            if have_e2d:
                t = self.chk_sqlite_threadsafe()
                if t:
                    self.log("\n\033[{}\033[0m\n".format(t))

                if not have_e2t:
                    t = "hint: argument -e2ts enables multimedia indexing (artist/title/...)"
                    self.log(t, 6)
            else:
                t = "hint: argument -e2dsa enables searching, upload-undo, and better deduplication"
                self.log(t, 6)

            zv, _ = vfs.get("/", "*", False, False)
            zs = zv.realpath.lower()
            if zs in ("/", "c:\\") or zs.startswith(r"c:\windows"):
                t = "you are sharing a system directory: {}\n"
                self.log(t.format(zv.realpath), c=1)

        try:
            zv, _ = vfs.get("", "*", False, True, err=999)
            if self.warn_anonwrite and os.getcwd() == zv.realpath:
                t = "anyone can write to the current directory: {}\n"
                self.log(t.format(zv.realpath), c=1)

            self.warn_anonwrite = False
        except Pebkac:
            self.warn_anonwrite = True

        with self.mutex:
            self.vfs = vfs
            self.acct = acct
            self.iacct = {v: k for k, v in acct.items()}

            self.re_pwd = None
            pwds = [re.escape(x) for x in self.iacct.keys()]
            if pwds:
                if self.ah.on:
                    zs = r"(\[H\] pw:.*|[?&]pw=)([^&]+)"
                else:
                    zs = r"(\[H\] pw:.*|=)(" + "|".join(pwds) + r")([]&; ]|$)"

                self.re_pwd = re.compile(zs)

    def setup_pwhash(self, acct: dict[str, str]) -> None:
        self.ah = PWHash(self.args)
        if not self.ah.on:
            if self.args.ah_cli or self.args.ah_gen:
                t = "\n  BAD CONFIG:\n    cannot --ah-cli or --ah-gen without --ah-alg"
                raise Exception(t)
            return

        if self.args.ah_cli:
            self.ah.cli()
            sys.exit()
        elif self.args.ah_gen == "-":
            self.ah.stdin()
            sys.exit()
        elif self.args.ah_gen:
            print(self.ah.hash(self.args.ah_gen))
            sys.exit()

        if not acct:
            return

        changed = False
        for uname, pw in list(acct.items())[:]:
            if pw.startswith("+") and len(pw) == 33:
                continue

            changed = True
            hpw = self.ah.hash(pw)
            acct[uname] = hpw
            t = "hashed password for account {}: {}"
            self.log(t.format(uname, hpw), 3)

        if not changed:
            return

        lns = []
        for uname, pw in acct.items():
            lns.append("  {}: {}".format(uname, pw))

        t = "please use the following hashed passwords in your config:\n{}"
        self.log(t.format("\n".join(lns)), 3)

    def chk_sqlite_threadsafe(self) -> str:
        v = SQLITE_VER[-1:]

        if v == "1":
            # threadsafe (linux, windows)
            return ""

        if v == "2":
            # module safe, connections unsafe (macos)
            return "33m  your sqlite3 was compiled with reduced thread-safety;\n   database features (-e2d, -e2t) SHOULD be fine\n    but MAY cause database-corruption and crashes"

        if v == "0":
            # everything unsafe
            return "31m  your sqlite3 was compiled WITHOUT thread-safety!\n   database features (-e2d, -e2t) will PROBABLY cause crashes!"

        return "36m  cannot verify sqlite3 thread-safety; strange but probably fine"

    def dbg_ls(self) -> None:
        users = self.args.ls
        vol = "*"
        flags: list[str] = []

        try:
            users, vol = users.split(",", 1)
        except:
            pass

        try:
            vol, zf = vol.split(",", 1)
            flags = zf.split(",")
        except:
            pass

        if users == "**":
            users = list(self.acct.keys()) + ["*"]
        else:
            users = [users]

        for u in users:
            if u not in self.acct and u != "*":
                raise Exception("user not found: " + u)

        if vol == "*":
            vols = ["/" + x for x in self.vfs.all_vols]
        else:
            vols = [vol]

        for zs in vols:
            if not zs.startswith("/"):
                raise Exception("volumes must start with /")

            if zs[1:] not in self.vfs.all_vols:
                raise Exception("volume not found: " + zs)

        self.log(str({"users": users, "vols": vols, "flags": flags}))
        t = "/{}: read({}) write({}) move({}) del({}) get({}) upget({}) uadmin({})"
        for k, zv in self.vfs.all_vols.items():
            vc = zv.axs
            vs = [
                k,
                vc.uread,
                vc.uwrite,
                vc.umove,
                vc.udel,
                vc.uget,
                vc.upget,
                vc.uhtml,
                vc.uadmin,
            ]
            self.log(t.format(*vs))

        flag_v = "v" in flags
        flag_ln = "ln" in flags
        flag_p = "p" in flags
        flag_r = "r" in flags

        bads = []
        for v in vols:
            v = v[1:]
            vtop = "/{}/".format(v) if v else "/"
            for u in users:
                self.log("checking /{} as {}".format(v, u))
                try:
                    vn, _ = self.vfs.get(v, u, True, False, False, False, False)
                except:
                    continue

                atop = vn.realpath
                safeabs = atop + os.sep
                g = vn.walk(
                    vn.vpath,
                    "",
                    [],
                    u,
                    [[True, False]],
                    True,
                    not self.args.no_scandir,
                    False,
                    False,
                )
                for _, _, vpath, apath, files1, dirs, _ in g:
                    fnames = [n[0] for n in files1]
                    zsl = [vpath + "/" + n for n in fnames] if vpath else fnames
                    vpaths = [vtop + x for x in zsl]
                    apaths = [os.path.join(apath, n) for n in fnames]
                    files = [(vpath + "/", apath + os.sep)] + list(
                        [(zs1, zs2) for zs1, zs2 in zip(vpaths, apaths)]
                    )

                    if flag_ln:
                        files = [x for x in files if not x[1].startswith(safeabs)]
                        if files:
                            dirs[:] = []  # stop recursion
                            bads.append(files[0][0])

                    if not files:
                        continue
                    elif flag_v:
                        ta = [""] + [
                            '# user "{}", vpath "{}"\n{}'.format(u, vp, ap)
                            for vp, ap in files
                        ]
                    else:
                        ta = ["user {}, vol {}: {} =>".format(u, vtop, files[0][0])]
                        ta += [x[1] for x in files]

                    self.log("\n".join(ta))

                if bads:
                    self.log("\n  ".join(["found symlinks leaving volume:"] + bads))

                if bads and flag_p:
                    raise Exception(
                        "\033[31m\n  [--ls] found a safety issue and prevented startup:\n    found symlinks leaving volume, and strict is set\n\033[0m"
                    )

        if not flag_r:
            sys.exit(0)

    def cgen(self) -> None:
        ret = [
            "## WARNING:",
            "##  there will probably be mistakes in",
            "##  commandline-args (and maybe volflags)",
            "",
        ]

        csv = set("i p".split())
        zs = "c ihead mtm mtp on403 on404 xad xar xau xiu xban xbd xbr xbu xm"
        lst = set(zs.split())
        askip = set("a v c vc cgen theme".split())

        # keymap from argv to vflag
        amap = vf_bmap()
        amap.update(vf_vmap())
        amap.update(vf_cmap())
        vmap = {v: k for k, v in amap.items()}

        args = {k: v for k, v in vars(self.args).items()}
        pops = []
        for k1, k2 in IMPLICATIONS:
            if args.get(k1):
                pops.append(k2)
        for pop in pops:
            args.pop(pop, None)

        if args:
            ret.append("[global]")
            for k, v in args.items():
                if k in askip:
                    continue
                if k in csv:
                    v = ", ".join([str(za) for za in v])
                try:
                    v2 = getattr(self.dargs, k)
                    if v == v2:
                        continue
                except:
                    continue

                dk = "  " + k.replace("_", "-")
                if k in lst:
                    for ve in v:
                        ret.append("{}: {}".format(dk, ve))
                else:
                    if v is True:
                        ret.append(dk)
                    elif v not in (False, None, ""):
                        ret.append("{}: {}".format(dk, v))
            ret.append("")

        if self.acct:
            ret.append("[accounts]")
            for u, p in self.acct.items():
                ret.append("  {}: {}".format(u, p))
            ret.append("")

        for vol in self.vfs.all_vols.values():
            ret.append("[/{}]".format(vol.vpath))
            ret.append("  " + vol.realpath)
            ret.append("  accs:")
            perms = {
                "r": "uread",
                "w": "uwrite",
                "m": "umove",
                "d": "udel",
                "g": "uget",
                "G": "upget",
                "h": "uhtml",
                "a": "uadmin",
            }
            users = {}
            for pkey in perms.values():
                for uname in getattr(vol.axs, pkey):
                    try:
                        users[uname] += 1
                    except:
                        users[uname] = 1
            lusers = [(v, k) for k, v in users.items()]
            vperms = {}
            for _, uname in sorted(lusers):
                pstr = ""
                for pchar, pkey in perms.items():
                    if uname in getattr(vol.axs, pkey):
                        pstr += pchar
                if "g" in pstr and "G" in pstr:
                    pstr = pstr.replace("g", "")
                try:
                    vperms[pstr].append(uname)
                except:
                    vperms[pstr] = [uname]
            for pstr, uname in vperms.items():
                ret.append("    {}: {}".format(pstr, ", ".join(uname)))
            trues = []
            vals = []
            for k, v in sorted(vol.flags.items()):
                try:
                    ak = vmap[k]
                    if getattr(self.args, ak) is v:
                        continue
                except:
                    pass

                if k in lst:
                    for ve in v:
                        vals.append("{}: {}".format(k, ve))
                elif v is True:
                    trues.append(k)
                elif v is not False:
                    try:
                        v = v.pattern
                    except:
                        pass

                    vals.append("{}: {}".format(k, v))
            pops = []
            for k1, k2 in IMPLICATIONS:
                if k1 in trues:
                    pops.append(k2)
            trues = [x for x in trues if x not in pops]
            if trues:
                vals.append(", ".join(trues))
            if vals:
                ret.append("  flags:")
                for zs in vals:
                    ret.append("    " + zs)
            ret.append("")

        self.log("generated config:\n\n" + "\n".join(ret))


def split_cfg_ln(ln: str) -> dict[str, Any]:
    # "a, b, c: 3" => {a:true, b:true, c:3}
    ret = {}
    while True:
        ln = ln.strip()
        if not ln:
            break
        ofs_sep = ln.find(",") + 1
        ofs_var = ln.find(":") + 1
        if not ofs_sep and not ofs_var:
            ret[ln] = True
            break
        if ofs_sep and (ofs_sep < ofs_var or not ofs_var):
            k, ln = ln.split(",", 1)
            ret[k.strip()] = True
        else:
            k, ln = ln.split(":", 1)
            ret[k.strip()] = ln.strip()
            break
    return ret


def expand_config_file(ret: list[str], fp: str, ipath: str) -> None:
    """expand all % file includes"""
    fp = absreal(fp)
    if len(ipath.split(" -> ")) > 64:
        raise Exception("hit max depth of 64 includes")

    if os.path.isdir(fp):
        names = os.listdir(fp)
        crumb = "#\033[36m cfg files in {} => {}\033[0m".format(fp, names)
        ret.append(crumb)
        for fn in sorted(names):
            fp2 = os.path.join(fp, fn)
            if not fp2.endswith(".conf") or fp2 in ipath:
                continue

            expand_config_file(ret, fp2, ipath)

        if ret[-1] == crumb:
            # no config files below; remove breadcrumb
            ret.pop()

        return

    ipath += " -> " + fp
    ret.append("#\033[36m opening cfg file{}\033[0m".format(ipath))

    with open(fp, "rb") as f:
        for oln in [x.decode("utf-8").rstrip() for x in f]:
            ln = oln.split("  #")[0].strip()
            if ln.startswith("% "):
                pad = " " * len(oln.split("%")[0])
                fp2 = ln[1:].strip()
                fp2 = os.path.join(os.path.dirname(fp), fp2)
                ofs = len(ret)
                expand_config_file(ret, fp2, ipath)
                for n in range(ofs, len(ret)):
                    ret[n] = pad + ret[n]
                continue

            ret.append(oln)

    ret.append("#\033[36m closed{}\033[0m".format(ipath))


def upgrade_cfg_fmt(
    log: Optional["NamedLogger"], args: argparse.Namespace, orig: list[str], cfg_fp: str
) -> list[str]:
    """convert from v1 to v2 format"""
    zst = [x.split("#")[0].strip() for x in orig]
    zst = [x for x in zst if x]
    if (
        "[global]" in zst
        or "[accounts]" in zst
        or "accs:" in zst
        or "flags:" in zst
        or [x for x in zst if x.startswith("[/")]
        or len(zst) == len([x for x in zst if x.startswith("%")])
    ):
        return orig

    zst = [x for x in orig if "#\033[36m opening cfg file" not in x]
    incl = len(zst) != len(orig) - 1

    t = "upgrading config file [{}] from v1 to v2"
    if not args.vc:
        t += ". Run with argument '--vc' to see the converted config if you want to upgrade"
    if incl:
        t += ". Please don't include v1 configs from v2 files or vice versa! Upgrade all of them at the same time."
    if log:
        log(t.format(cfg_fp), 3)

    ret = []
    vp = ""
    ap = ""
    cat = ""
    catg = "[global]"
    cata = "[accounts]"
    catx = "  accs:"
    catf = "  flags:"
    for ln in orig:
        sn = ln.strip()
        if not sn:
            cat = vp = ap = ""
        if not sn.split("#")[0]:
            ret.append(ln)
        elif sn.startswith("-") and cat in ("", catg):
            if cat != catg:
                cat = catg
                ret.append(cat)
            sn = sn.lstrip("-")
            zst = sn.split(" ", 1)
            if len(zst) > 1:
                sn = "{}: {}".format(zst[0], zst[1].strip())
            ret.append("  " + sn)
        elif sn.startswith("u ") and cat in ("", catg, cata):
            if cat != cata:
                cat = cata
                ret.append(cat)
            s1, s2 = sn[1:].split(":", 1)
            ret.append("  {}: {}".format(s1.strip(), s2.strip()))
        elif not ap:
            ap = sn
        elif not vp:
            vp = "/" + sn.strip("/")
            cat = "[{}]".format(vp)
            ret.append(cat)
            ret.append("  " + ap)
        elif sn.startswith("c "):
            if cat != catf:
                cat = catf
                ret.append(cat)
            sn = sn[1:].strip()
            if "=" in sn:
                zst = sn.split("=", 1)
                sn = zst[0].replace(",", ", ")
                sn += ": " + zst[1]
            else:
                sn = sn.replace(",", ", ")
            ret.append("    " + sn)
        elif sn[:1] in "rwmdgGha":
            if cat != catx:
                cat = catx
                ret.append(cat)
            zst = sn.split(" ")
            zst = [x for x in zst if x]
            if len(zst) == 1:
                zst.append("*")
            ret.append("    {}: {}".format(zst[0], ", ".join(zst[1:])))
        else:
            t = "did not understand line {} in the config"
            t1 = t
            n = 0
            for ln in orig:
                n += 1
                t += "\n{:4} {}".format(n, ln)
            if log:
                log(t, 1)
            else:
                print("\033[31m" + t)
            raise Exception(t1)

    if args.vc and log:
        t = "new config syntax (copy/paste this to upgrade your config):\n"
        t += "\n# ======================[ begin upgraded config ]======================\n\n"
        for ln in ret:
            t += ln + "\n"
        t += "\n# ======================[ end of upgraded config ]======================\n"
        log(t)

    return ret

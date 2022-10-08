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

from .__init__ import ANYWIN, TYPE_CHECKING, WINDOWS
from .bos import bos
from .util import (
    IMPLICATIONS,
    META_NOBOTS,
    SQLITE_VER,
    Pebkac,
    absreal,
    fsenc,
    get_df,
    humansize,
    relchk,
    statdir,
    uncyg,
    undot,
    unhumanize,
)

try:
    from collections.abc import Iterable

    import typing
    from typing import Any, Generator, Optional, Union

    from .util import RootLogger
except:
    pass

if TYPE_CHECKING:
    pass
    # Vflags: TypeAlias = dict[str, str | bool | float | list[str]]
    # Vflags: TypeAlias = dict[str, Any]
    # Mflags: TypeAlias = dict[str, Vflags]


LEELOO_DALLAS = "leeloo_dallas"


class AXS(object):
    def __init__(
        self,
        uread: Optional[Union[list[str], set[str]]] = None,
        uwrite: Optional[Union[list[str], set[str]]] = None,
        umove: Optional[Union[list[str], set[str]]] = None,
        udel: Optional[Union[list[str], set[str]]] = None,
        uget: Optional[Union[list[str], set[str]]] = None,
        upget: Optional[Union[list[str], set[str]]] = None,
    ) -> None:
        self.uread: set[str] = set(uread or [])
        self.uwrite: set[str] = set(uwrite or [])
        self.umove: set[str] = set(umove or [])
        self.udel: set[str] = set(udel or [])
        self.uget: set[str] = set(uget or [])
        self.upget: set[str] = set(upget or [])

    def __repr__(self) -> str:
        return "AXS({})".format(
            ", ".join(
                "{}={!r}".format(k, self.__dict__[k])
                for k in "uread uwrite umove udel uget upget".split()
            )
        )


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
        abspath: str,
        reg: Optional[dict[str, dict[str, Any]]] = None,
    ) -> tuple[str, str]:
        if reg is not None and self.reg is None:
            self.reg = reg
            self.dft = 0

        self.chk_nup(ip)
        self.chk_bup(ip)
        self.chk_rem(rem)
        if sz != -1:
            self.chk_sz(sz)
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

            suf = datetime.utcnow().strftime(self.rotf)
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
            raise Pebkac(429, "ingress saturated")


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

        if realpath:
            self.histpath = os.path.join(realpath, ".hist")  # db / thumbcache
            self.all_vols = {vpath: self}  # flattened recursive
        else:
            self.histpath = ""
            self.all_vols = {}

    def __repr__(self) -> str:
        return "VFS({})".format(
            ", ".join(
                "{}={!r}".format(k, self.__dict__[k])
                for k in "realpath vpath axs flags".split()
            )
        )

    def get_all_vols(self, outdict: dict[str, "VFS"]) -> None:
        if self.realpath:
            outdict[self.vpath] = self

        for v in self.nodes.values():
            v.get_all_vols(outdict)

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
            flags["hist"] = "{}/{}".format(hist.rstrip("/"), name)

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
        vpath = undot(vpath)
        if vpath == "":
            return self, ""

        if "/" in vpath:
            name, rem = vpath.split("/", 1)
        else:
            name = vpath
            rem = ""

        if name in self.nodes:
            return self.nodes[name]._find(rem)

        return self, vpath

    def can_access(
        self, vpath: str, uname: str
    ) -> tuple[bool, bool, bool, bool, bool, bool]:
        """can Read,Write,Move,Delete,Get,Upget"""
        vn, _ = self._find(vpath)
        c = vn.axs
        return (
            uname in c.uread or "*" in c.uread,
            uname in c.uwrite or "*" in c.uwrite,
            uname in c.umove or "*" in c.umove,
            uname in c.udel or "*" in c.udel,
            uname in c.uget or "*" in c.uget,
            uname in c.upget or "*" in c.upget,
        )

    def get(
        self,
        vpath: str,
        uname: str,
        will_read: bool,
        will_write: bool,
        will_move: bool = False,
        will_del: bool = False,
        will_get: bool = False,
    ) -> tuple["VFS", str]:
        """returns [vfsnode,fs_remainder] if user has the requested permissions"""
        if ANYWIN:
            mod = relchk(vpath)
            if mod:
                if self.log:
                    self.log("vfs", "invalid relpath [{}]".format(vpath))
                raise Pebkac(404)

        vn, rem = self._find(vpath)
        c: AXS = vn.axs

        for req, d, msg in [
            (will_read, c.uread, "read"),
            (will_write, c.uwrite, "write"),
            (will_move, c.umove, "move"),
            (will_del, c.udel, "delete"),
            (will_get, c.uget, "get"),
        ]:
            if req and (uname not in d and "*" not in d) and uname != LEELOO_DALLAS:
                t = "you don't have {}-access for this location"
                raise Pebkac(403, t.format(msg))

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

        seen = seen[:] + [fsroot]
        rfiles = [x for x in vfs_ls if not stat.S_ISDIR(x[1].st_mode)]
        rdirs = [x for x in vfs_ls if stat.S_ISDIR(x[1].st_mode)]

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
        self, vrem: str, flt: set[str], uname: str, dots: bool, scandir: bool
    ) -> Generator[dict[str, Any], None, None]:

        # if multiselect: add all items to archive root
        # if single folder: the folder itself is the top-level item
        folder = "" if flt else (vrem.split("/")[-1] or "top")

        g = self.walk(folder, vrem, [], uname, [[True]], dots, scandir, False)
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
    ) -> None:
        self.args = args
        self.log_func = log_func
        self.warn_anonwrite = warn_anonwrite
        self.line_ctr = 0

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
            raise Exception("invalid config")

        if src in mount.values():
            t = "warning: filesystem-path [{}] mounted in multiple locations:"
            t = t.format(src)
            for v in [k for k, v in mount.items() if v == src] + [dst]:
                t += "\n  /{}".format(v)

            self.log(t, c=3)

        mount[dst] = src
        daxs[dst] = AXS()
        mflags[dst] = {}

    def _parse_config_file(
        self,
        fd: typing.BinaryIO,
        acct: dict[str, str],
        daxs: dict[str, AXS],
        mflags: dict[str, dict[str, Any]],
        mount: dict[str, str],
    ) -> None:
        skip = False
        vol_src = None
        vol_dst = None
        self.line_ctr = 0
        for ln in [x.decode("utf-8").strip() for x in fd]:
            self.line_ctr += 1
            if not ln and vol_src is not None:
                vol_src = None
                vol_dst = None

            if skip:
                if not ln:
                    skip = False
                continue

            if not ln or ln.startswith("#"):
                continue

            if vol_src is None:
                if ln.startswith("u "):
                    u, p = ln[2:].split(":", 1)
                    acct[u] = p
                elif ln.startswith("-"):
                    skip = True  # argv
                else:
                    vol_src = ln
                continue

            if vol_src and vol_dst is None:
                vol_dst = ln
                if not vol_dst.startswith("/"):
                    raise Exception('invalid mountpoint "{}"'.format(vol_dst))

                # cfg files override arguments and previous files
                vol_src = absreal(vol_src)
                vol_dst = vol_dst.strip("/")
                self._map_volume(vol_src, vol_dst, mount, daxs, mflags)
                continue

            try:
                lvl, uname = ln.split(" ", 1)
            except:
                lvl = ln
                uname = "*"

            if lvl == "a":
                t = "WARNING (config-file): permission flag 'a' is deprecated; please use 'rw' instead"
                self.log(t, 1)

            self._read_vol_str(lvl, uname, daxs[vol_dst], mflags[vol_dst])

    def _read_vol_str(
        self, lvl: str, uname: str, axs: AXS, flags: dict[str, Any]
    ) -> None:
        if lvl.strip("crwmdgG"):
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
                ("g", axs.uget),
                ("G", axs.uget),
                ("G", axs.upget),
            ]:  # b bb bbb
                if ch in lvl:
                    al.add(un)

    def _read_volflag(
        self,
        flags: dict[str, Any],
        name: str,
        value: Union[str, bool, list[str]],
        is_list: bool,
    ) -> None:
        if name not in ["mtp"]:
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
            # permset is <rwmdgG>[,username][,username] or <c>,<flag>[=args]
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
                with open(cfg_fn, "rb") as f:
                    try:
                        self._parse_config_file(f, acct, daxs, mflags, mount)
                    except:
                        t = "\n\033[1;31m\nerror in config file {} on line {}:\n\033[0m"
                        self.log(t.format(cfg_fn, self.line_ctr), 1)
                        raise

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

        vfs.all_vols = {}
        vfs.get_all_vols(vfs.all_vols)

        for perm in "read write move del get pget".split():
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
            for d in [axs.uread, axs.uwrite, axs.umove, axs.udel, axs.uget, axs.upget]:
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
            raise Exception("invalid config")

        if LEELOO_DALLAS in all_users:
            raise Exception("sorry, reserved username: " + LEELOO_DALLAS)

        promote = []
        demote = []
        for vol in vfs.all_vols.values():
            zb = hashlib.sha512(fsenc(vol.realpath)).digest()
            hid = base64.b32encode(zb).decode("ascii").lower()
            vflag = vol.flags.get("hist")
            if vflag == "-":
                pass
            elif vflag:
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

                    me = fsenc(vol.realpath).rstrip()
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
            if fk:
                vol.flags["fk"] = int(fk) if fk is not True else 8
                have_fk = True

        if have_fk and re.match(r"^[0-9\.]+$", self.args.fk_salt):
            self.log("filekey salt: {}".format(self.args.fk_salt))

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
                    ptn = vol.flags.pop(vf)
                else:
                    ptn = getattr(self.args, ga)

                if ptn:
                    vol.flags[vf] = re.compile(ptn)

            for k in ["e2t", "e2ts", "e2tsr", "e2v", "e2vu", "e2vp", "xdev", "xvol"]:
                if getattr(self.args, k):
                    vol.flags[k] = True

            for ga, vf in [["no_forget", "noforget"], ["magic", "magic"]]:
                if getattr(self.args, ga):
                    vol.flags[vf] = True

            for k1, k2 in IMPLICATIONS:
                if k1 in vol.flags:
                    vol.flags[k2] = True

            # default tag cfgs if unset
            if "mte" not in vol.flags:
                vol.flags["mte"] = self.args.mte
            elif vol.flags["mte"].startswith("+"):
                vol.flags["mte"] = ",".join(
                    x for x in [self.args.mte, vol.flags["mte"][1:]] if x
                )
            if "mth" not in vol.flags:
                vol.flags["mth"] = self.args.mth

            # append parsers from argv to volflags
            self._read_volflag(vol.flags, "mtp", self.args.mtp, True)

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

                vol.flags = {k: v for k, v in vol.flags.items() if not k.startswith(rm)}

            for grp, rm in [["d2v", "e2v"]]:
                if not vol.flags.get(grp, False):
                    continue

                vol.flags = {k: v for k, v in vol.flags.items() if not k.startswith(rm)}

            ints = ["lifetime"]
            for k in list(vol.flags):
                if k in ints:
                    vol.flags[k] = int(vol.flags[k])

            if "lifetime" in vol.flags and "e2d" not in vol.flags:
                t = 'removing lifetime config from volume "/{}" because e2d is disabled'
                self.log(t.format(vol.vpath), 1)
                del vol.flags["lifetime"]

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

            local_mte = {}
            for a in vol.flags.get("mte", "").split(","):
                local = True
                all_mte[a] = True
                local_mte[a] = True
                for b in self.args.mte.split(","):
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

        if errors:
            sys.exit(1)

        vfs.bubble_flags()

        have_e2d = False
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
            ]:
                u = list(sorted(getattr(zv.axs, attr)))
                u = ", ".join("\033[35meverybody\033[0m" if x == "*" else x for x in u)
                u = u if u else "\033[36m--none--\033[0m"
                t += "\n|  {}:  {}".format(txt, u)

            if "e2d" in zv.flags:
                have_e2d = True

            t += "\n"

        if self.warn_anonwrite:
            if not self.args.no_voldump:
                self.log(t)

            if have_e2d:
                t = self.chk_sqlite_threadsafe()
                if t:
                    self.log("\n\033[{}\033[0m\n".format(t))

        try:
            zv, _ = vfs.get("/", "*", False, True)
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
                self.re_pwd = re.compile("=(" + "|".join(pwds) + ")([]&; ]|$)")

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
        t = "/{}: read({}) write({}) move({}) del({}) get({}) upget({})"
        for k, zv in self.vfs.all_vols.items():
            vc = zv.axs
            vs = [k, vc.uread, vc.uwrite, vc.umove, vc.udel, vc.uget, vc.upget]
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
                    [[True]],
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

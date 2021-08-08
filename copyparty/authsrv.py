# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import sys
import stat
import time
import base64
import hashlib
import threading
from datetime import datetime

from .__init__ import WINDOWS
from .util import (
    IMPLICATIONS,
    uncyg,
    undot,
    unhumanize,
    absreal,
    Pebkac,
    fsenc,
    statdir,
)
from .bos import bos


class AXS(object):
    def __init__(self, uread=None, uwrite=None, umove=None, udel=None):
        self.uread = {} if uread is None else {k: 1 for k in uread}
        self.uwrite = {} if uwrite is None else {k: 1 for k in uwrite}
        self.umove = {} if umove is None else {k: 1 for k in umove}
        self.udel = {} if udel is None else {k: 1 for k in udel}

    def __repr__(self):
        return "AXS({})".format(
            ", ".join(
                "{}={!r}".format(k, self.__dict__[k])
                for k in "uread uwrite umove udel".split()
            )
        )


class Lim(object):
    def __init__(self):
        self.nups = {}  # num tracker
        self.bups = {}  # byte tracker list
        self.bupc = {}  # byte tracker cache

        self.nosub = False  # disallow subdirectories

        self.smin = None  # filesize min
        self.smax = None  # filesize max

        self.bwin = None  # bytes window
        self.bmax = None  # bytes max
        self.nwin = None  # num window
        self.nmax = None  # num max

        self.rotn = None  # rot num files
        self.rotl = None  # rot depth
        self.rotf = None  # rot datefmt
        self.rot_re = None  # rotf check

    def set_rotf(self, fmt):
        self.rotf = fmt
        r = re.escape(fmt).replace("%Y", "[0-9]{4}").replace("%j", "[0-9]{3}")
        r = re.sub("%[mdHMSWU]", "[0-9]{2}", r)
        self.rot_re = re.compile("(^|/)" + r + "$")

    def all(self, ip, rem, sz, abspath):
        self.chk_nup(ip)
        self.chk_bup(ip)
        self.chk_rem(rem)
        if sz != -1:
            self.chk_sz(sz)

        ap2, vp2 = self.rot(abspath)
        if abspath == ap2:
            return ap2, rem

        return ap2, ("{}/{}".format(rem, vp2) if rem else vp2)

    def chk_sz(self, sz):
        if self.smin is not None and sz < self.smin:
            raise Pebkac(400, "file too small")

        if self.smax is not None and sz > self.smax:
            raise Pebkac(400, "file too big")

    def chk_rem(self, rem):
        if self.nosub and rem:
            raise Pebkac(500, "no subdirectories allowed")

    def rot(self, path):
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

    def dive(self, path, lvs):
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

    def nup(self, ip):
        try:
            self.nups[ip].append(time.time())
        except:
            self.nups[ip] = [time.time()]

    def bup(self, ip, nbytes):
        v = [time.time(), nbytes]
        try:
            self.bups[ip].append(v)
            self.bupc[ip] += nbytes
        except:
            self.bups[ip] = [v]
            self.bupc[ip] = nbytes

    def chk_nup(self, ip):
        if not self.nmax or ip not in self.nups:
            return

        nups = self.nups[ip]
        cutoff = time.time() - self.nwin
        while nups and nups[0] < cutoff:
            nups.pop(0)

        if len(nups) >= self.nmax:
            raise Pebkac(429, "too many uploads")

    def chk_bup(self, ip):
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

    def __init__(self, log, realpath, vpath, axs, flags):
        self.log = log
        self.realpath = realpath  # absolute path on host filesystem
        self.vpath = vpath  # absolute path in the virtual filesystem
        self.axs = axs  # type: AXS
        self.flags = flags  # config options
        self.nodes = {}  # child nodes
        self.histtab = None  # all realpath->histpath
        self.dbv = None  # closest full/non-jump parent
        self.lim = None  # type: Lim  # upload limits; only set for dbv

        if realpath:
            self.histpath = os.path.join(realpath, ".hist")  # db / thumbcache
            self.all_vols = {vpath: self}  # flattened recursive
            self.aread = {}
            self.awrite = {}
            self.amove = {}
            self.adel = {}
        else:
            self.histpath = None
            self.all_vols = None
            self.aread = None
            self.awrite = None
            self.amove = None
            self.adel = None

    def __repr__(self):
        return "VFS({})".format(
            ", ".join(
                "{}={!r}".format(k, self.__dict__[k])
                for k in "realpath vpath axs flags".split()
            )
        )

    def get_all_vols(self, outdict):
        if self.realpath:
            outdict[self.vpath] = self

        for v in self.nodes.values():
            v.get_all_vols(outdict)

    def add(self, src, dst):
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
                os.path.join(self.realpath, name) if self.realpath else None,
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

    def _copy_flags(self, name):
        flags = {k: v for k, v in self.flags.items()}
        hist = flags.get("hist")
        if hist and hist != "-":
            flags["hist"] = "{}/{}".format(hist.rstrip("/"), name)

        return flags

    def bubble_flags(self):
        if self.dbv:
            for k, v in self.dbv.flags.items():
                if k not in ["hist"]:
                    self.flags[k] = v

        for v in self.nodes.values():
            v.bubble_flags()

    def _find(self, vpath):
        """return [vfs,remainder]"""
        vpath = undot(vpath)
        if vpath == "":
            return [self, ""]

        if "/" in vpath:
            name, rem = vpath.split("/", 1)
        else:
            name = vpath
            rem = ""

        if name in self.nodes:
            return self.nodes[name]._find(rem)

        return [self, vpath]

    def can_access(self, vpath, uname):
        # type: (str, str) -> tuple[bool, bool, bool, bool]
        """can Read,Write,Move,Delete"""
        vn, _ = self._find(vpath)
        c = vn.axs
        return [
            uname in c.uread or "*" in c.uread,
            uname in c.uwrite or "*" in c.uwrite,
            uname in c.umove or "*" in c.umove,
            uname in c.udel or "*" in c.udel,
        ]

    def get(self, vpath, uname, will_read, will_write, will_move=False, will_del=False):
        # type: (str, str, bool, bool, bool, bool) -> tuple[VFS, str]
        """returns [vfsnode,fs_remainder] if user has the requested permissions"""
        vn, rem = self._find(vpath)
        c = vn.axs

        for req, d, msg in [
            [will_read, c.uread, "read"],
            [will_write, c.uwrite, "write"],
            [will_move, c.umove, "move"],
            [will_del, c.udel, "delete"],
        ]:
            if req and (uname not in d and "*" not in d):
                m = "you don't have {}-access for this location"
                raise Pebkac(403, m.format(msg))

        return vn, rem

    def get_dbv(self, vrem):
        # type: (str) -> tuple[VFS, str]
        dbv = self.dbv
        if not dbv:
            return self, vrem

        vrem = [self.vpath[len(dbv.vpath) + 1 :], vrem]
        vrem = "/".join([x for x in vrem if x])
        return dbv, vrem

    def canonical(self, rem, resolve=True):
        """returns the canonical path (fully-resolved absolute fs path)"""
        rp = self.realpath
        if rem:
            rp += "/" + rem

        return absreal(rp) if resolve else rp

    def ls(self, rem, uname, scandir, permsets, lstat=False):
        # type: (str, str, bool, list[list[bool]], bool) -> tuple[str, str, dict[str, VFS]]
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
                axs = vn2.axs
                axs = [axs.uread, axs.uwrite, axs.umove, axs.udel]
                for pset in permsets:
                    ok = True
                    for req, lst in zip(pset, axs):
                        if req and uname not in lst and "*" not in lst:
                            ok = False
                    if ok:
                        break

                if ok:
                    virt_vis[name] = vn2

        return [abspath, real, virt_vis]

    def walk(self, rel, rem, seen, uname, permsets, dots, scandir, lstat):
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
            m = "bailing from symlink loop,\n  prev: {}\n  curr: {}\n  from: {}/{}"
            self.log("vfs.walk", m.format(seen[-1], fsroot, self.vpath, rem), 3)
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
            for x in self.walk(wrel, wrem, seen, uname, permsets, dots, scandir, lstat):
                yield x

        for n, vfs in sorted(vfs_virt.items()):
            if not dots and n.startswith("."):
                continue

            wrel = (rel + "/" + n).lstrip("/")
            for x in vfs.walk(wrel, "", seen, uname, permsets, dots, scandir, lstat):
                yield x

    def zipgen(self, vrem, flt, uname, dots, scandir):
        if flt:
            flt = {k: True for k in flt}

        f1 = "{0}.hist{0}up2k.".format(os.sep)
        f2a = os.sep + "dir.txt"
        f2b = "{0}.hist{0}".format(os.sep)

        g = self.walk("", vrem, [], uname, [[True]], dots, scandir, False)
        for _, _, vpath, apath, files, rd, vd in g:
            if flt:
                files = [x for x in files if x[0] in flt]

                rm = [x for x in rd if x[0] not in flt]
                [rd.remove(x) for x in rm]

                rm = [x for x in vd.keys() if x not in flt]
                [vd.pop(x) for x in rm]

                flt = None

            # print(repr([vpath, apath, [x[0] for x in files]]))
            fnames = [n[0] for n in files]
            vpaths = [vpath + "/" + n for n in fnames] if vpath else fnames
            apaths = [os.path.join(apath, n) for n in fnames]
            files = list(zip(vpaths, apaths, files))

            if not dots:
                # dotfile filtering based on vpath (intended visibility)
                files = [x for x in files if "/." not in "/" + x[0]]

                rm = [x for x in rd if x[0].startswith(".")]
                for x in rm:
                    rd.remove(x)

                rm = [k for k in vd.keys() if k.startswith(".")]
                for x in rm:
                    del vd[x]

            # up2k filetring based on actual abspath
            files = [
                x
                for x in files
                if f1 not in x[1] and (not x[1].endswith(f2a) or f2b not in x[1])
            ]

            for f in [{"vp": v, "ap": a, "st": n[1]} for v, a, n in files]:
                yield f


if WINDOWS:
    re_vol = re.compile(r"^([a-zA-Z]:[\\/][^:]*|[^:]*):([^:]*):(.*)$")
else:
    re_vol = re.compile(r"^([^:]*):([^:]*):(.*)$")


class AuthSrv(object):
    """verifies users against given paths"""

    def __init__(self, args, log_func, warn_anonwrite=True):
        self.args = args
        self.log_func = log_func
        self.warn_anonwrite = warn_anonwrite
        self.line_ctr = 0

        self.mutex = threading.Lock()
        self.reload()

    def log(self, msg, c=0):
        if self.log_func:
            self.log_func("auth", msg, c)

    def laggy_iter(self, iterable):
        """returns [value,isFinalValue]"""
        it = iter(iterable)
        prev = next(it)
        for x in it:
            yield prev, False
            prev = x

        yield prev, True

    def _parse_config_file(self, fd, acct, daxs, mflags, mount):
        # type: (any, str, dict[str, AXS], any, str) -> None
        vol_src = None
        vol_dst = None
        self.line_ctr = 0
        for ln in [x.decode("utf-8").strip() for x in fd]:
            self.line_ctr += 1
            if not ln and vol_src is not None:
                vol_src = None
                vol_dst = None

            if not ln or ln.startswith("#"):
                continue

            if vol_src is None:
                if ln.startswith("u "):
                    u, p = ln[2:].split(":", 1)
                    acct[u] = p
                else:
                    vol_src = ln
                continue

            if vol_src and vol_dst is None:
                vol_dst = ln
                if not vol_dst.startswith("/"):
                    raise Exception('invalid mountpoint "{}"'.format(vol_dst))

                # cfg files override arguments and previous files
                vol_src = bos.path.abspath(vol_src)
                vol_dst = vol_dst.strip("/")
                mount[vol_dst] = vol_src
                daxs[vol_dst] = AXS()
                mflags[vol_dst] = {}
                continue

            try:
                lvl, uname = ln.split(" ", 1)
            except:
                lvl = ln
                uname = "*"

            if lvl == "a":
                m = "WARNING (config-file): permission flag 'a' is deprecated; please use 'rw' instead"
                self.log(m, 1)

            self._read_vol_str(lvl, uname, daxs[vol_dst], mflags[vol_dst])

    def _read_vol_str(self, lvl, uname, axs, flags):
        # type: (str, str, AXS, any) -> None
        if lvl == "c":
            cval = True
            if "=" in uname:
                uname, cval = uname.split("=", 1)

            self._read_volflag(flags, uname, cval, False)
            return

        if uname == "":
            uname = "*"

        for un in uname.split(","):
            if "r" in lvl:
                axs.uread[un] = 1

            if "w" in lvl:
                axs.uwrite[un] = 1

            if "m" in lvl:
                axs.umove[un] = 1

            if "d" in lvl:
                axs.udel[un] = 1

    def _read_volflag(self, flags, name, value, is_list):
        if name not in ["mtp"]:
            flags[name] = value
            return

        if not is_list:
            value = [value]
        elif not value:
            return

        flags[name] = flags.get(name, []) + value

    def reload(self):
        """
        construct a flat list of mountpoints and usernames
        first from the commandline arguments
        then supplementing with config files
        before finally building the VFS
        """

        acct = {}  # username:password
        daxs = {}  # type: dict[str, AXS]
        mflags = {}  # mountpoint:[flag]
        mount = {}  # dst:src (mountpoint:realpath)

        if self.args.a:
            # list of username:password
            for x in self.args.a:
                try:
                    u, p = x.split(":", 1)
                    acct[u] = p
                except:
                    m = '\n  invalid value "{}" for argument -a, must be username:password'
                    raise Exception(m.format(x))

        if self.args.v:
            # list of src:dst:permset:permset:...
            # permset is <rwmd>[,username][,username] or <c>,<flag>[=args]
            for v_str in self.args.v:
                m = re_vol.match(v_str)
                if not m:
                    raise Exception("invalid -v argument: [{}]".format(v_str))

                src, dst, perms = m.groups()
                if WINDOWS:
                    src = uncyg(src)

                # print("\n".join([src, dst, perms]))
                src = bos.path.abspath(src)
                dst = dst.strip("/")
                mount[dst] = src
                daxs[dst] = AXS()
                mflags[dst] = {}

                for x in perms.split(":"):
                    lvl, uname = x.split(",", 1) if "," in x else [x, ""]
                    self._read_vol_str(lvl, uname, daxs[dst], mflags[dst])

        if self.args.c:
            for cfg_fn in self.args.c:
                with open(cfg_fn, "rb") as f:
                    try:
                        self._parse_config_file(f, acct, daxs, mflags, mount)
                    except:
                        m = "\n\033[1;31m\nerror in config file {} on line {}:\n\033[0m"
                        self.log(m.format(cfg_fn, self.line_ctr), 1)
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
            vfs = VFS(self.log_func, bos.path.abspath("."), "", axs, {})
        elif "" not in mount:
            # there's volumes but no root; make root inaccessible
            vfs = VFS(self.log_func, None, "", AXS(), {})
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

            v = vfs.add(mount[dst], dst)
            v.axs = daxs[dst]
            v.flags = mflags[dst]
            v.dbv = None

        vfs.all_vols = {}
        vfs.get_all_vols(vfs.all_vols)

        for perm in "read write move del".split():
            axs_key = "u" + perm
            unames = ["*"] + list(acct.keys())
            umap = {x: [] for x in unames}
            for usr in unames:
                for mp, vol in vfs.all_vols.items():
                    if usr in getattr(vol.axs, axs_key):
                        umap[usr].append(mp)
            setattr(vfs, "a" + perm, umap)

        all_users = {}
        missing_users = {}
        for axs in daxs.values():
            for d in [axs.uread, axs.uwrite, axs.umove, axs.udel]:
                for usr in d.keys():
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

        promote = []
        demote = []
        for vol in vfs.all_vols.values():
            hid = hashlib.sha512(fsenc(vol.realpath)).digest()
            hid = base64.b32encode(hid).decode("ascii").lower()
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
        for v in demote:
            vfs.all_vols.pop(v.vpath)

        if promote:
            msg = [
                "\n  the following jump-volumes were generated to assist the vfs.\n  As they contain a database (probably from v0.11.11 or older),\n  they are promoted to full volumes:"
            ]
            for vol in promote:
                msg.append(
                    "  /{}  ({})  ({})".format(vol.vpath, vol.realpath, vol.histpath)
                )

            self.log("\n\n".join(msg) + "\n", c=3)

        vfs.histtab = {v.realpath: v.histpath for v in vfs.all_vols.values()}

        for vol in vfs.all_vols.values():
            lim = Lim()
            use = False

            if vol.flags.get("nosub"):
                use = True
                lim.nosub = True

            v = vol.flags.get("sz")
            if v:
                use = True
                lim.smin, lim.smax = [unhumanize(x) for x in v.split("-")]

            v = vol.flags.get("rotn")
            if v:
                use = True
                lim.rotn, lim.rotl = [int(x) for x in v.split(",")]

            v = vol.flags.get("rotf")
            if v:
                use = True
                lim.set_rotf(v)

            v = vol.flags.get("maxn")
            if v:
                use = True
                lim.nmax, lim.nwin = [int(x) for x in v.split(",")]

            v = vol.flags.get("maxb")
            if v:
                use = True
                lim.bmax, lim.bwin = [unhumanize(x) for x in v.split(",")]

            if use:
                vol.lim = lim

        for vol in vfs.all_vols.values():
            if "pk" in vol.flags and "gz" not in vol.flags and "xz" not in vol.flags:
                vol.flags["gz"] = False  # def.pk

        all_mte = {}
        errors = False
        for vol in vfs.all_vols.values():
            if (self.args.e2ds and vol.axs.uwrite) or self.args.e2dsa:
                vol.flags["e2ds"] = True

            if self.args.e2d or "e2ds" in vol.flags:
                vol.flags["e2d"] = True

            if self.args.no_hash:
                if "ehash" not in vol.flags:
                    vol.flags["dhash"] = True

            for k in ["e2t", "e2ts", "e2tsr"]:
                if getattr(self.args, k):
                    vol.flags[k] = True

            for k1, k2 in IMPLICATIONS:
                if k1 in vol.flags:
                    vol.flags[k2] = True

            # default tag cfgs if unset
            if "mte" not in vol.flags:
                vol.flags["mte"] = self.args.mte
            if "mth" not in vol.flags:
                vol.flags["mth"] = self.args.mth

            # append parsers from argv to volume-flags
            self._read_volflag(vol.flags, "mtp", self.args.mtp, True)

            # d2d drops all database features for a volume
            for grp, rm in [["d2d", "e2d"], ["d2t", "e2t"]]:
                if not vol.flags.get(grp, False):
                    continue

                vol.flags["d2t"] = True
                vol.flags = {k: v for k, v in vol.flags.items() if not k.startswith(rm)}

            # mt* needs e2t so drop those too
            for grp, rm in [["e2t", "mt"]]:
                if vol.flags.get(grp, False):
                    continue

                vol.flags = {k: v for k, v in vol.flags.items() if not k.startswith(rm)}

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

            for mtp in local_only_mtp.keys():
                if mtp not in local_mte:
                    m = 'volume "/{}" defines metadata tag "{}", but doesnt use it in "-mte" (or with "cmte" in its volume-flags)'
                    self.log(m.format(vol.vpath, mtp), 1)
                    errors = True

        tags = self.args.mtp or []
        tags = [x.split("=")[0] for x in tags]
        tags = [y for x in tags for y in x.split(",")]
        for mtp in tags:
            if mtp not in all_mte:
                m = 'metadata tag "{}" is defined by "-mtm" or "-mtp", but is not used by "-mte" (or by any "cmte" volume-flag)'
                self.log(m.format(mtp), 1)
                errors = True

        if errors:
            sys.exit(1)

        vfs.bubble_flags()

        m = "volumes and permissions:\n"
        for v in vfs.all_vols.values():
            if not self.warn_anonwrite:
                break

            m += '\n\033[36m"/{}"  \033[33m{}\033[0m'.format(v.vpath, v.realpath)
            for txt, attr in [
                ["  read", "uread"],
                [" write", "uwrite"],
                ["  move", "umove"],
                ["delete", "udel"],
            ]:
                u = list(sorted(getattr(v.axs, attr).keys()))
                u = ", ".join("\033[35meverybody\033[0m" if x == "*" else x for x in u)
                u = u if u else "\033[36m--none--\033[0m"
                m += "\n|  {}:  {}".format(txt, u)
            m += "\n"

        if self.warn_anonwrite and not self.args.no_voldump:
            self.log(m)

        try:
            v, _ = vfs.get("/", "*", False, True)
            if self.warn_anonwrite and os.getcwd() == v.realpath:
                self.warn_anonwrite = False
                msg = "anyone can read/write the current directory: {}"
                self.log(msg.format(v.realpath), c=1)
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

    def dbg_ls(self):
        users = self.args.ls
        vols = "*"
        flags = []

        try:
            users, vols = users.split(",", 1)
        except:
            pass

        try:
            vols, flags = vols.split(",", 1)
            flags = flags.split(",")
        except:
            pass

        if users == "**":
            users = list(self.acct.keys()) + ["*"]
        else:
            users = [users]

        for u in users:
            if u not in self.acct and u != "*":
                raise Exception("user not found: " + u)

        if vols == "*":
            vols = ["/" + x for x in self.vfs.all_vols.keys()]
        else:
            vols = [vols]

        for v in vols:
            if not v.startswith("/"):
                raise Exception("volumes must start with /")

            if v[1:] not in self.vfs.all_vols:
                raise Exception("volume not found: " + v)

        self.log({"users": users, "vols": vols, "flags": flags})
        m = "/{}: read({}) write({}) move({}) del({})"
        for k, v in self.vfs.all_vols.items():
            vc = v.axs
            self.log(m.format(k, vc.uread, vc.uwrite, vc.umove, vc.udel))

        flag_v = "v" in flags
        flag_ln = "ln" in flags
        flag_p = "p" in flags
        flag_r = "r" in flags

        n_bads = 0
        for v in vols:
            v = v[1:]
            vtop = "/{}/".format(v) if v else "/"
            for u in users:
                self.log("checking /{} as {}".format(v, u))
                try:
                    vn, _ = self.vfs.get(v, u, True, False, False, False)
                except:
                    continue

                atop = vn.realpath
                g = vn.walk(
                    vn.vpath, "", [], u, [[True]], True, not self.args.no_scandir, False
                )
                for _, _, vpath, apath, files, _, _ in g:
                    fnames = [n[0] for n in files]
                    vpaths = [vpath + "/" + n for n in fnames] if vpath else fnames
                    vpaths = [vtop + x for x in vpaths]
                    apaths = [os.path.join(apath, n) for n in fnames]
                    files = [[vpath + "/", apath + os.sep]] + list(zip(vpaths, apaths))

                    if flag_ln:
                        files = [x for x in files if not x[1].startswith(atop + os.sep)]
                        n_bads += len(files)

                    if flag_v:
                        msg = [
                            '# user "{}", vpath "{}"\n{}'.format(u, vp, ap)
                            for vp, ap in files
                        ]
                    else:
                        msg = [x[1] for x in files]

                    if msg:
                        self.log("\n" + "\n".join(msg))

                if n_bads and flag_p:
                    raise Exception("found symlink leaving volume, and strict is set")

        if not flag_r:
            sys.exit(0)

# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import sys
import stat
import threading

from .__init__ import PY2, WINDOWS
from .util import IMPLICATIONS, undot, Pebkac, fsdec, fsenc, statdir, nuprint


class VFS(object):
    """single level in the virtual fs"""

    def __init__(self, realpath, vpath, uread=[], uwrite=[], flags={}):
        self.realpath = realpath  # absolute path on host filesystem
        self.vpath = vpath  # absolute path in the virtual filesystem
        self.uread = uread  # users who can read this
        self.uwrite = uwrite  # users who can write this
        self.flags = flags  # config switches
        self.nodes = {}  # child nodes
        self.all_vols = {vpath: self}  # flattened recursive

    def __repr__(self):
        return "VFS({})".format(
            ", ".join(
                "{}={!r}".format(k, self.__dict__[k])
                for k in "realpath vpath uread uwrite flags".split()
            )
        )

    def _trk(self, vol):
        self.all_vols[vol.vpath] = vol
        return vol

    def add(self, src, dst):
        """get existing, or add new path to the vfs"""
        assert not src.endswith("/")  # nosec
        assert not dst.endswith("/")  # nosec

        if "/" in dst:
            # requires breadth-first population (permissions trickle down)
            name, dst = dst.split("/", 1)
            if name in self.nodes:
                # exists; do not manipulate permissions
                return self._trk(self.nodes[name].add(src, dst))

            vn = VFS(
                "{}/{}".format(self.realpath, name),
                "{}/{}".format(self.vpath, name).lstrip("/"),
                self.uread,
                self.uwrite,
                self.flags,
            )
            self._trk(vn)
            self.nodes[name] = vn
            return self._trk(vn.add(src, dst))

        if dst in self.nodes:
            # leaf exists; return as-is
            return self.nodes[dst]

        # leaf does not exist; create and keep permissions blank
        vp = "{}/{}".format(self.vpath, dst).lstrip("/")
        vn = VFS(src, vp)
        self.nodes[dst] = vn
        return self._trk(vn)

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
        """return [readable,writable]"""
        vn, _ = self._find(vpath)
        return [
            uname in vn.uread or "*" in vn.uread,
            uname in vn.uwrite or "*" in vn.uwrite,
        ]

    def get(self, vpath, uname, will_read, will_write):
        """returns [vfsnode,fs_remainder] if user has the requested permissions"""
        vn, rem = self._find(vpath)

        if will_read and (uname not in vn.uread and "*" not in vn.uread):
            raise Pebkac(403, "you don't have read-access for this location")

        if will_write and (uname not in vn.uwrite and "*" not in vn.uwrite):
            raise Pebkac(403, "you don't have write-access for this location")

        return vn, rem

    def canonical(self, rem):
        """returns the canonical path (fully-resolved absolute fs path)"""
        rp = self.realpath
        if rem:
            rp += "/" + rem

        return fsdec(os.path.realpath(fsenc(rp)))

    def ls(self, rem, uname, scandir, lstat=False):
        """return user-readable [fsdir,real,virt] items at vpath"""
        virt_vis = {}  # nodes readable by user
        abspath = self.canonical(rem)
        real = list(statdir(nuprint, scandir, lstat, abspath))
        real.sort()
        if not rem:
            for name, vn2 in sorted(self.nodes.items()):
                if uname in vn2.uread or "*" in vn2.uread:
                    virt_vis[name] = vn2

            # no vfs nodes in the list of real inodes
            real = [x for x in real if x[0] not in self.nodes]

        return [abspath, real, virt_vis]

    def walk(self, rel, rem, uname, dots, scandir, lstat=False):
        """
        recursively yields from ./rem;
        rel is a unix-style user-defined vpath (not vfs-related)
        """

        fsroot, vfs_ls, vfs_virt = self.ls(rem, uname, scandir, lstat)
        rfiles = [x for x in vfs_ls if not stat.S_ISDIR(x[1].st_mode)]
        rdirs = [x for x in vfs_ls if stat.S_ISDIR(x[1].st_mode)]

        rfiles.sort()
        rdirs.sort()

        yield rel, fsroot, rfiles, rdirs, vfs_virt

        for rdir, _ in rdirs:
            if not dots and rdir.startswith("."):
                continue

            wrel = (rel + "/" + rdir).lstrip("/")
            wrem = (rem + "/" + rdir).lstrip("/")
            for x in self.walk(wrel, wrem, uname, scandir, lstat):
                yield x

        for n, vfs in sorted(vfs_virt.items()):
            if not dots and n.startswith("."):
                continue

            wrel = (rel + "/" + n).lstrip("/")
            for x in vfs.walk(wrel, "", uname, scandir, lstat):
                yield x

    def zipgen(self, vrem, flt, uname, dots, scandir):
        if flt:
            flt = {k: True for k in flt}

        for vpath, apath, files, rd, vd in self.walk("", vrem, uname, dots, scandir):
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
            files = [x for x in files if "{0}.hist{0}up2k.".format(os.sep) not in x[1]]

            for f in [{"vp": v, "ap": a, "st": n[1]} for v, a, n in files]:
                yield f

    def user_tree(self, uname, readable=False, writable=False):
        ret = []
        opt1 = readable and (uname in self.uread or "*" in self.uread)
        opt2 = writable and (uname in self.uwrite or "*" in self.uwrite)
        if opt1 or opt2:
            ret.append(self.vpath)

        for _, vn in sorted(self.nodes.items()):
            ret.extend(vn.user_tree(uname, readable, writable))

        return ret


class AuthSrv(object):
    """verifies users against given paths"""

    def __init__(self, args, log_func, warn_anonwrite=True):
        self.args = args
        self.log_func = log_func
        self.warn_anonwrite = warn_anonwrite

        if WINDOWS:
            self.re_vol = re.compile(r"^([a-zA-Z]:[\\/][^:]*|[^:]*):([^:]*):(.*)$")
        else:
            self.re_vol = re.compile(r"^([^:]*):([^:]*):(.*)$")

        self.mutex = threading.Lock()
        self.reload()

    def log(self, msg, c=0):
        self.log_func("auth", msg, c)

    def invert(self, orig):
        if PY2:
            return {v: k for k, v in orig.iteritems()}
        else:
            return {v: k for k, v in orig.items()}

    def laggy_iter(self, iterable):
        """returns [value,isFinalValue]"""
        it = iter(iterable)
        prev = next(it)
        for x in it:
            yield prev, False
            prev = x

        yield prev, True

    def _parse_config_file(self, fd, user, mread, mwrite, mflags, mount):
        vol_src = None
        vol_dst = None
        for ln in [x.decode("utf-8").strip() for x in fd]:
            if not ln and vol_src is not None:
                vol_src = None
                vol_dst = None

            if not ln or ln.startswith("#"):
                continue

            if vol_src is None:
                if ln.startswith("u "):
                    u, p = ln[2:].split(":", 1)
                    user[u] = p
                else:
                    vol_src = ln
                continue

            if vol_src and vol_dst is None:
                vol_dst = ln
                if not vol_dst.startswith("/"):
                    raise Exception('invalid mountpoint "{}"'.format(vol_dst))

                # cfg files override arguments and previous files
                vol_src = fsdec(os.path.abspath(fsenc(vol_src)))
                vol_dst = vol_dst.strip("/")
                mount[vol_dst] = vol_src
                mread[vol_dst] = []
                mwrite[vol_dst] = []
                mflags[vol_dst] = {}
                continue

            lvl, uname = ln.split(" ")
            self._read_vol_str(
                lvl, uname, mread[vol_dst], mwrite[vol_dst], mflags[vol_dst]
            )

    def _read_vol_str(self, lvl, uname, mr, mw, mf):
        if lvl == "c":
            cval = True
            if "=" in uname:
                uname, cval = uname.split("=", 1)

            self._read_volflag(mf, uname, cval, False)
            return

        if uname == "":
            uname = "*"

        if lvl in "ra":
            mr.append(uname)

        if lvl in "wa":
            mw.append(uname)

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

        user = {}  # username:password
        mread = {}  # mountpoint:[username]
        mwrite = {}  # mountpoint:[username]
        mflags = {}  # mountpoint:[flag]
        mount = {}  # dst:src (mountpoint:realpath)

        if self.args.a:
            # list of username:password
            for u, p in [x.split(":", 1) for x in self.args.a]:
                user[u] = p

        if self.args.v:
            # list of src:dst:permset:permset:...
            # permset is [rwa]username or [c]flag
            for v_str in self.args.v:
                m = self.re_vol.match(v_str)
                if not m:
                    raise Exception("invalid -v argument: [{}]".format(v_str))

                src, dst, perms = m.groups()
                # print("\n".join([src, dst, perms]))
                src = fsdec(os.path.abspath(fsenc(src)))
                dst = dst.strip("/")
                mount[dst] = src
                mread[dst] = []
                mwrite[dst] = []
                mflags[dst] = {}

                perms = perms.split(":")
                for (lvl, uname) in [[x[0], x[1:]] for x in perms]:
                    self._read_vol_str(lvl, uname, mread[dst], mwrite[dst], mflags[dst])

        if self.args.c:
            for cfg_fn in self.args.c:
                with open(cfg_fn, "rb") as f:
                    self._parse_config_file(f, user, mread, mwrite, mflags, mount)

        if not mount:
            # -h says our defaults are CWD at root and read/write for everyone
            vfs = VFS(os.path.abspath("."), "", ["*"], ["*"])
        elif "" not in mount:
            # there's volumes but no root; make root inaccessible
            vfs = VFS(os.path.abspath("."), "")
            vfs.flags["d2d"] = True

        maxdepth = 0
        for dst in sorted(mount.keys(), key=lambda x: (x.count("/"), len(x))):
            depth = dst.count("/")
            assert maxdepth <= depth  # nosec
            maxdepth = depth

            if dst == "":
                # rootfs was mapped; fully replaces the default CWD vfs
                vfs = VFS(mount[dst], dst, mread[dst], mwrite[dst], mflags[dst])
                continue

            v = vfs.add(mount[dst], dst)
            v.uread = mread[dst]
            v.uwrite = mwrite[dst]
            v.flags = mflags[dst]

        missing_users = {}
        for d in [mread, mwrite]:
            for _, ul in d.items():
                for usr in ul:
                    if usr != "*" and usr not in user:
                        missing_users[usr] = 1

        if missing_users:
            self.log(
                "you must -a the following users: "
                + ", ".join(k for k in sorted(missing_users)),
                c=1,
            )
            raise Exception("invalid config")

        all_mte = {}
        errors = False
        for vol in vfs.all_vols.values():
            if (self.args.e2ds and vol.uwrite) or self.args.e2dsa:
                vol.flags["e2ds"] = True

            if self.args.e2d or "e2ds" in vol.flags:
                vol.flags["e2d"] = True

            for k in ["e2t", "e2ts", "e2tsr"]:
                if getattr(self.args, k):
                    vol.flags[k] = True

            for k1, k2 in IMPLICATIONS:
                if k1 in vol.flags:
                    vol.flags[k2] = True

            # default tag-list if unset
            if "mte" not in vol.flags:
                vol.flags["mte"] = self.args.mte

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
            for a in vol.flags.get("mtp", []) + vol.flags.get("mtm", []):
                a = a.split("=")[0]
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

        for mtp in self.args.mtp or []:
            mtp = mtp.split("=")[0]
            if mtp not in all_mte:
                m = 'metadata tag "{}" is defined by "-mtm" or "-mtp", but is not used by "-mte" (or by any "cmte" volume-flag)'
                self.log(m.format(mtp), 1)
                errors = True

        if errors:
            sys.exit(1)

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
            self.user = user
            self.iuser = self.invert(user)

        # import pprint
        # pprint.pprint({"usr": user, "rd": mread, "wr": mwrite, "mnt": mount})

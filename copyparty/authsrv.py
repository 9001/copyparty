# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import re
import threading

from .__init__ import PY2, WINDOWS
from .util import undot, Pebkac, fsdec, fsenc


class VFS(object):
    """single level in the virtual fs"""

    def __init__(self, realpath, vpath, uread=[], uwrite=[]):
        self.realpath = realpath  # absolute path on host filesystem
        self.vpath = vpath  # absolute path in the virtual filesystem
        self.uread = uread  # users who can read this
        self.uwrite = uwrite  # users who can write this
        self.nodes = {}  # child nodes

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
                "{}/{}".format(self.realpath, name),
                "{}/{}".format(self.vpath, name).lstrip("/"),
                self.uread,
                self.uwrite,
            )
            self.nodes[name] = vn
            return vn.add(src, dst)

        if dst in self.nodes:
            # leaf exists; return as-is
            return self.nodes[dst]

        # leaf does not exist; create and keep permissions blank
        vp = "{}/{}".format(self.vpath, dst).lstrip("/")
        vn = VFS(src, vp)
        self.nodes[dst] = vn
        return vn

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

    def ls(self, rem, uname):
        """return user-readable [fsdir,real,virt] items at vpath"""
        virt_vis = {}  # nodes readable by user
        abspath = self.canonical(rem)
        items = os.listdir(fsenc(abspath))
        real = [fsdec(x) for x in items]
        real.sort()
        if not rem:
            for name, vn2 in sorted(self.nodes.items()):
                if uname in vn2.uread:
                    virt_vis[name] = vn2

            # no vfs nodes in the list of real inodes
            real = [x for x in real if x not in self.nodes]

        return [abspath, real, virt_vis]

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

    def __init__(self, args, log_func):
        self.log_func = log_func
        self.args = args

        self.warn_anonwrite = True

        if WINDOWS:
            self.re_vol = re.compile(r"^([a-zA-Z]:[\\/][^:]*|[^:]*):([^:]*):(.*)$")
        else:
            self.re_vol = re.compile(r"^([^:]*):([^:]*):(.*)$")

        self.mutex = threading.Lock()
        self.reload()

    def log(self, msg):
        self.log_func("auth", msg)

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

    def _parse_config_file(self, fd, user, mread, mwrite, mount):
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
                continue

            lvl, uname = ln.split(" ")
            if lvl in "ra":
                mread[vol_dst].append(uname)
            if lvl in "wa":
                mwrite[vol_dst].append(uname)

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
        mount = {}  # dst:src (mountpoint:realpath)

        if self.args.a:
            # list of username:password
            for u, p in [x.split(":", 1) for x in self.args.a]:
                user[u] = p

        if self.args.v:
            # list of src:dst:permset:permset:...
            # permset is [rwa]username
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

                perms = perms.split(":")
                for (lvl, uname) in [[x[0], x[1:]] for x in perms]:
                    if uname == "":
                        uname = "*"
                    if lvl in "ra":
                        mread[dst].append(uname)
                    if lvl in "wa":
                        mwrite[dst].append(uname)

        if self.args.c:
            for cfg_fn in self.args.c:
                with open(cfg_fn, "rb") as f:
                    self._parse_config_file(f, user, mread, mwrite, mount)

        if not mount:
            # -h says our defaults are CWD at root and read/write for everyone
            vfs = VFS(os.path.abspath("."), "", ["*"], ["*"])
        elif "" not in mount:
            # there's volumes but no root; make root inaccessible
            vfs = VFS(os.path.abspath("."), "", [], [])

        maxdepth = 0
        for dst in sorted(mount.keys(), key=lambda x: (x.count("/"), len(x))):
            depth = dst.count("/")
            assert maxdepth <= depth  # nosec
            maxdepth = depth

            if dst == "":
                # rootfs was mapped; fully replaces the default CWD vfs
                vfs = VFS(mount[dst], dst, mread[dst], mwrite[dst])
                continue

            v = vfs.add(mount[dst], dst)
            v.uread = mread[dst]
            v.uwrite = mwrite[dst]

        missing_users = {}
        for d in [mread, mwrite]:
            for _, ul in d.items():
                for usr in ul:
                    if usr != "*" and usr not in user:
                        missing_users[usr] = 1

        if missing_users:
            self.log(
                "\033[31myou must -a the following users: "
                + ", ".join(k for k in sorted(missing_users))
                + "\033[0m"
            )
            raise Exception("invalid config")

        try:
            v, _ = vfs.get("/", "*", False, True)
            if self.warn_anonwrite and os.getcwd() == v.realpath:
                self.warn_anonwrite = False
                self.log(
                    "\033[31manyone can read/write the current directory: {}\033[0m".format(
                        v.realpath
                    )
                )
        except Pebkac:
            self.warn_anonwrite = True

        with self.mutex:
            self.vfs = vfs
            self.user = user
            self.iuser = self.invert(user)

        # import pprint
        # pprint.pprint({"usr": user, "rd": mread, "wr": mwrite, "mnt": mount})

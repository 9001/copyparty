# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import sys
import stat
import base64
import hashlib
import threading

from .__init__ import WINDOWS
from .util import IMPLICATIONS, uncyg, undot, Pebkac, fsdec, fsenc, statdir


class VFS(object):
    """single level in the virtual fs"""

    def __init__(self, log, realpath, vpath, uread, uwrite, uadm, flags):
        self.log = log
        self.realpath = realpath  # absolute path on host filesystem
        self.vpath = vpath  # absolute path in the virtual filesystem
        self.uread = uread  # users who can read this
        self.uwrite = uwrite  # users who can write this
        self.uadm = uadm  # users who are regular admins
        self.flags = flags  # config switches
        self.nodes = {}  # child nodes
        self.histtab = None  # all realpath->histpath
        self.dbv = None  # closest full/non-jump parent

        if realpath:
            self.histpath = os.path.join(realpath, ".hist")  # db / thumbcache
            self.all_vols = {vpath: self}  # flattened recursive
        else:
            self.histpath = None
            self.all_vols = None

    def __repr__(self):
        return "VFS({})".format(
            ", ".join(
                "{}={!r}".format(k, self.__dict__[k])
                for k in "realpath vpath uread uwrite uadm flags".split()
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
                self.uread,
                self.uwrite,
                self.uadm,
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
        vn = VFS(self.log, src, vp, [], [], [], {})
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
        """return [readable,writable]"""
        vn, _ = self._find(vpath)
        return [
            uname in vn.uread or "*" in vn.uread,
            uname in vn.uwrite or "*" in vn.uwrite,
        ]

    def get(self, vpath, uname, will_read, will_write):
        # type: (str, str, bool, bool) -> tuple[VFS, str]
        """returns [vfsnode,fs_remainder] if user has the requested permissions"""
        vn, rem = self._find(vpath)

        if will_read and (uname not in vn.uread and "*" not in vn.uread):
            raise Pebkac(403, "you don't have read-access for this location")

        if will_write and (uname not in vn.uwrite and "*" not in vn.uwrite):
            raise Pebkac(403, "you don't have write-access for this location")

        return vn, rem

    def get_dbv(self, vrem):
        dbv = self.dbv
        if not dbv:
            return self, vrem

        vrem = [self.vpath[len(dbv.vpath) + 1 :], vrem]
        vrem = "/".join([x for x in vrem if x])
        return dbv, vrem

    def canonical(self, rem):
        """returns the canonical path (fully-resolved absolute fs path)"""
        rp = self.realpath
        if rem:
            rp += "/" + rem

        try:
            return fsdec(os.path.realpath(fsenc(rp)))
        except:
            if not WINDOWS:
                raise

            # cpython bug introduced in 3.8, still exists in 3.9.1;
            # some win7sp1 and win10:20H2 boxes cannot realpath a
            # networked drive letter such as b"n:" or b"n:\\"
            #
            # requirements to trigger:
            #  * bytestring (not unicode str)
            #  * just the drive letter (subfolders are ok)
            #  * networked drive (regular disks and vmhgfs are ok)
            #  * on an enterprise network (idk, cannot repro with samba)
            #
            # hits the following exceptions in succession:
            #  * access denied at L601: "path = _getfinalpathname(path)"
            #  * "cant concat str to bytes" at L621: "return path + tail"
            #
            return os.path.realpath(rp)

    def ls(self, rem, uname, scandir, incl_wo=False, lstat=False):
        # type: (str, str, bool, bool, bool) -> tuple[str, str, dict[str, VFS]]
        """return user-readable [fsdir,real,virt] items at vpath"""
        virt_vis = {}  # nodes readable by user
        abspath = self.canonical(rem)
        real = list(statdir(self.log, scandir, lstat, abspath))
        real.sort()
        if not rem:
            for name, vn2 in sorted(self.nodes.items()):
                ok = uname in vn2.uread or "*" in vn2.uread

                if not ok and incl_wo:
                    ok = uname in vn2.uwrite or "*" in vn2.uwrite

                if ok:
                    virt_vis[name] = vn2

            # no vfs nodes in the list of real inodes
            real = [x for x in real if x[0] not in self.nodes]

        return [abspath, real, virt_vis]

    def walk(self, rel, rem, seen, uname, dots, scandir, lstat):
        """
        recursively yields from ./rem;
        rel is a unix-style user-defined vpath (not vfs-related)
        """

        fsroot, vfs_ls, vfs_virt = self.ls(
            rem, uname, scandir, incl_wo=False, lstat=lstat
        )

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

        yield rel, fsroot, rfiles, rdirs, vfs_virt

        for rdir, _ in rdirs:
            if not dots and rdir.startswith("."):
                continue

            wrel = (rel + "/" + rdir).lstrip("/")
            wrem = (rem + "/" + rdir).lstrip("/")
            for x in self.walk(wrel, wrem, seen, uname, dots, scandir, lstat):
                yield x

        for n, vfs in sorted(vfs_virt.items()):
            if not dots and n.startswith("."):
                continue

            wrel = (rel + "/" + n).lstrip("/")
            for x in vfs.walk(wrel, "", seen, uname, dots, scandir, lstat):
                yield x

    def zipgen(self, vrem, flt, uname, dots, scandir):
        if flt:
            flt = {k: True for k in flt}

        f1 = "{0}.hist{0}up2k.".format(os.sep)
        f2a = os.sep + "dir.txt"
        f2b = "{0}.hist{0}".format(os.sep)

        for vpath, apath, files, rd, vd in self.walk(
            "", vrem, [], uname, dots, scandir, False
        ):
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

    def user_tree(self, uname, readable, writable, admin):
        is_readable = False
        if uname in self.uread or "*" in self.uread:
            readable.append(self.vpath)
            is_readable = True

        if uname in self.uwrite or "*" in self.uwrite:
            writable.append(self.vpath)
            if is_readable:
                admin.append(self.vpath)

        for _, vn in sorted(self.nodes.items()):
            vn.user_tree(uname, readable, writable, admin)


class AuthSrv(object):
    """verifies users against given paths"""

    def __init__(self, args, log_func, warn_anonwrite=True):
        self.args = args
        self.log_func = log_func
        self.warn_anonwrite = warn_anonwrite
        self.line_ctr = 0

        if WINDOWS:
            self.re_vol = re.compile(r"^([a-zA-Z]:[\\/][^:]*|[^:]*):([^:]*):(.*)$")
        else:
            self.re_vol = re.compile(r"^([^:]*):([^:]*):(.*)$")

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

    def _parse_config_file(self, fd, user, mread, mwrite, madm, mflags, mount):
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
                madm[vol_dst] = []
                mflags[vol_dst] = {}
                continue

            if len(ln) > 1:
                lvl, uname = ln.split(" ")
            else:
                lvl = ln
                uname = "*"

            self._read_vol_str(
                lvl,
                uname,
                mread[vol_dst],
                mwrite[vol_dst],
                madm[vol_dst],
                mflags[vol_dst],
            )

    def _read_vol_str(self, lvl, uname, mr, mw, ma, mf):
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

        if lvl == "a":
            ma.append(uname)

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
        madm = {}  # mountpoint:[username]
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
                if WINDOWS:
                    src = uncyg(src)

                # print("\n".join([src, dst, perms]))
                src = fsdec(os.path.abspath(fsenc(src)))
                dst = dst.strip("/")
                mount[dst] = src
                mread[dst] = []
                mwrite[dst] = []
                madm[dst] = []
                mflags[dst] = {}

                perms = perms.split(":")
                for (lvl, uname) in [[x[0], x[1:]] for x in perms]:
                    self._read_vol_str(
                        lvl, uname, mread[dst], mwrite[dst], madm[dst], mflags[dst]
                    )

        if self.args.c:
            for cfg_fn in self.args.c:
                with open(cfg_fn, "rb") as f:
                    try:
                        self._parse_config_file(
                            f, user, mread, mwrite, madm, mflags, mount
                        )
                    except:
                        m = "\n\033[1;31m\nerror in config file {} on line {}:\n\033[0m"
                        self.log(m.format(cfg_fn, self.line_ctr), 1)
                        raise

        # case-insensitive; normalize
        if WINDOWS:
            cased = {}
            for k, v in mount.items():
                try:
                    cased[k] = fsdec(os.path.realpath(fsenc(v)))
                except:
                    cased[k] = v

            mount = cased

        if not mount:
            # -h says our defaults are CWD at root and read/write for everyone
            vfs = VFS(self.log_func, os.path.abspath("."), "", ["*"], ["*"], ["*"], {})
        elif "" not in mount:
            # there's volumes but no root; make root inaccessible
            vfs = VFS(self.log_func, None, "", [], [], [], {})
            vfs.flags["d2d"] = True

        maxdepth = 0
        for dst in sorted(mount.keys(), key=lambda x: (x.count("/"), len(x))):
            depth = dst.count("/")
            assert maxdepth <= depth  # nosec
            maxdepth = depth

            if dst == "":
                # rootfs was mapped; fully replaces the default CWD vfs
                vfs = VFS(
                    self.log_func,
                    mount[dst],
                    dst,
                    mread[dst],
                    mwrite[dst],
                    madm[dst],
                    mflags[dst],
                )
                continue

            v = vfs.add(mount[dst], dst)
            v.uread = mread[dst]
            v.uwrite = mwrite[dst]
            v.uadm = madm[dst]
            v.flags = mflags[dst]
            v.dbv = None

        vfs.all_vols = {}
        vfs.get_all_vols(vfs.all_vols)

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
                    try:
                        os.makedirs(hpath)
                    except:
                        pass

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

            vol.histpath = os.path.realpath(vol.histpath)
            if vol.dbv:
                if os.path.exists(os.path.join(vol.histpath, "up2k.db")):
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

        all_mte = {}
        errors = False
        for vol in vfs.all_vols.values():
            if (self.args.e2ds and vol.uwrite) or self.args.e2dsa:
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
            self.iuser = {v: k for k, v in user.items()}

            self.re_pwd = None
            pwds = [re.escape(x) for x in self.iuser.keys()]
            if pwds:
                self.re_pwd = re.compile("=(" + "|".join(pwds) + ")([]&; ]|$)")

        # import pprint
        # pprint.pprint({"usr": user, "rd": mread, "wr": mwrite, "mnt": mount})

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
            users = list(self.user.keys()) + ["*"]
        else:
            users = [users]

        for u in users:
            if u not in self.user and u != "*":
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
        for k, v in self.vfs.all_vols.items():
            self.log("/{}: read({}) write({})".format(k, v.uread, v.uwrite))

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
                    vn, _ = self.vfs.get(v, u, True, False)
                except:
                    continue

                atop = vn.realpath
                g = vn.walk("", "", [], u, True, not self.args.no_scandir, False)
                for vpath, apath, files, _, _ in g:
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

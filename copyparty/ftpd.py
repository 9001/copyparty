# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import errno
import logging
import os
import stat
import sys
import time

from pyftpdlib.authorizers import AuthenticationFailed, DummyAuthorizer
from pyftpdlib.filesystems import AbstractedFS, FilesystemError
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from .__init__ import ANYWIN, PY2, TYPE_CHECKING, E
from .authsrv import VFS
from .bos import bos
from .util import (
    Daemon,
    Pebkac,
    exclude_dotfiles,
    fsenc,
    ipnorm,
    pybin,
    relchk,
    runhook,
    sanitize_fn,
    vjoin,
)

try:
    from pyftpdlib.ioloop import IOLoop
except ImportError:
    p = os.path.join(E.mod, "vend")
    print("loading asynchat from " + p)
    sys.path.append(p)
    from pyftpdlib.ioloop import IOLoop


if TYPE_CHECKING:
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    import typing
    from typing import Any, Optional


class FSE(FilesystemError):
    def __init__(self, msg: str, severity: int = 0) -> None:
        super(FilesystemError, self).__init__(msg)
        self.severity = severity


class FtpAuth(DummyAuthorizer):
    def __init__(self, hub: "SvcHub") -> None:
        super(FtpAuth, self).__init__()
        self.hub = hub

    def validate_authentication(
        self, username: str, password: str, handler: Any
    ) -> None:
        handler.username = "{}:{}".format(username, password)
        handler.uname = "*"

        ip = handler.addr[0]
        if ip.startswith("::ffff:"):
            ip = ip[7:]

        ip = ipnorm(ip)
        bans = self.hub.bans
        if ip in bans:
            rt = bans[ip] - time.time()
            if rt < 0:
                logging.info("client unbanned")
                del bans[ip]
            else:
                raise AuthenticationFailed("banned")

        asrv = self.hub.asrv
        uname = "*"
        if username != "anonymous":
            for zs in (password, username):
                zs = asrv.iacct.get(asrv.ah.hash(zs), "")
                if zs:
                    uname = zs
                    break

        if not uname or not (asrv.vfs.aread.get(uname) or asrv.vfs.awrite.get(uname)):
            g = self.hub.gpwd
            if g.lim:
                bonk, ip = g.bonk(ip, handler.username)
                if bonk:
                    logging.warning("client banned: invalid passwords")
                    bans[ip] = bonk

            raise AuthenticationFailed("Authentication failed.")

        handler.uname = handler.username = uname

    def get_home_dir(self, username: str) -> str:
        return "/"

    def has_user(self, username: str) -> bool:
        asrv = self.hub.asrv
        return username in asrv.acct or username in asrv.iacct

    def has_perm(self, username: str, perm: int, path: Optional[str] = None) -> bool:
        return True  # handled at filesystem layer

    def get_perms(self, username: str) -> str:
        return "elradfmwMT"

    def get_msg_login(self, username: str) -> str:
        return "sup {}".format(username)

    def get_msg_quit(self, username: str) -> str:
        return "cya"


class FtpFs(AbstractedFS):
    def __init__(
        self, root: str, cmd_channel: Any
    ) -> None:  # pylint: disable=super-init-not-called
        self.h = cmd_channel  # type: FTPHandler
        self.cmd_channel = cmd_channel  # type: FTPHandler
        self.hub: "SvcHub" = cmd_channel.hub
        self.args = cmd_channel.args
        self.uname = cmd_channel.uname

        self.cwd = "/"  # pyftpdlib convention of leading slash
        self.root = "/var/lib/empty"

        self.can_read = self.can_write = self.can_move = False
        self.can_delete = self.can_get = self.can_upget = False
        self.can_admin = False

        self.listdirinfo = self.listdir
        self.chdir(".")

    def v2a(
        self,
        vpath: str,
        r: bool = False,
        w: bool = False,
        m: bool = False,
        d: bool = False,
    ) -> tuple[str, VFS, str]:
        try:
            vpath = vpath.replace("\\", "/").strip("/")
            rd, fn = os.path.split(vpath)
            if ANYWIN and relchk(rd):
                logging.warning("malicious vpath: %s", vpath)
                t = "Unsupported characters in [{}]"
                raise FSE(t.format(vpath), 1)

            fn = sanitize_fn(fn or "", "", [".prologue.html", ".epilogue.html"])
            vpath = vjoin(rd, fn)
            vfs, rem = self.hub.asrv.vfs.get(vpath, self.uname, r, w, m, d)
            if not vfs.realpath:
                t = "No filesystem mounted at [{}]"
                raise FSE(t.format(vpath))

            if "xdev" in vfs.flags or "xvol" in vfs.flags:
                ap = vfs.canonical(rem)
                avfs = vfs.chk_ap(ap)
                t = "Permission denied in [{}]"
                if not avfs:
                    raise FSE(t.format(vpath), 1)

                cr, cw, cm, cd, _, _, _ = avfs.can_access("", self.h.uname)
                if r and not cr or w and not cw or m and not cm or d and not cd:
                    raise FSE(t.format(vpath), 1)

            return os.path.join(vfs.realpath, rem), vfs, rem
        except Pebkac as ex:
            raise FSE(str(ex))

    def rv2a(
        self,
        vpath: str,
        r: bool = False,
        w: bool = False,
        m: bool = False,
        d: bool = False,
    ) -> tuple[str, VFS, str]:
        return self.v2a(os.path.join(self.cwd, vpath), r, w, m, d)

    def ftp2fs(self, ftppath: str) -> str:
        # return self.v2a(ftppath)
        return ftppath  # self.cwd must be vpath

    def fs2ftp(self, fspath: str) -> str:
        # raise NotImplementedError()
        return fspath

    def validpath(self, path: str) -> bool:
        if "/.hist/" in path:
            if "/up2k." in path or path.endswith("/dir.txt"):
                raise FSE("Access to this file is forbidden", 1)

        return True

    def open(self, filename: str, mode: str) -> typing.IO[Any]:
        r = "r" in mode
        w = "w" in mode or "a" in mode or "+" in mode

        ap = self.rv2a(filename, r, w)[0]
        if w:
            try:
                st = bos.stat(ap)
                td = time.time() - st.st_mtime
            except:
                td = 0

            if td < -1 or td > self.args.ftp_wt:
                raise FSE("Cannot open existing file for writing")

        self.validpath(ap)
        return open(fsenc(ap), mode)

    def chdir(self, path: str) -> None:
        nwd = join(self.cwd, path)
        vfs, rem = self.hub.asrv.vfs.get(nwd, self.uname, False, False)
        ap = vfs.canonical(rem)
        try:
            st = bos.stat(ap)
            if not stat.S_ISDIR(st.st_mode):
                raise Exception()
        except:
            # returning 550 is library-default and suitable
            raise FSE("No such file or directory")

        avfs = vfs.chk_ap(ap, st)
        if not avfs:
            raise FSE("Permission denied", 1)

        self.cwd = nwd
        (
            self.can_read,
            self.can_write,
            self.can_move,
            self.can_delete,
            self.can_get,
            self.can_upget,
            self.can_admin,
        ) = avfs.can_access("", self.h.uname)

    def mkdir(self, path: str) -> None:
        ap = self.rv2a(path, w=True)[0]
        bos.makedirs(ap)  # filezilla expects this

    def listdir(self, path: str) -> list[str]:
        vpath = join(self.cwd, path)
        try:
            ap, vfs, rem = self.v2a(vpath, True, False)
            if not bos.path.isdir(ap):
                raise FSE("No such file or directory", 1)

            fsroot, vfs_ls1, vfs_virt = vfs.ls(
                rem,
                self.uname,
                not self.args.no_scandir,
                [[True, False], [False, True]],
            )
            vfs_ls = [x[0] for x in vfs_ls1]
            vfs_ls.extend(vfs_virt.keys())

            if not self.args.ed:
                vfs_ls = exclude_dotfiles(vfs_ls)

            vfs_ls.sort()
            return vfs_ls
        except Exception as ex:
            # panic on malicious names
            if getattr(ex, "severity", 0):
                raise

            if vpath.strip("/"):
                # display write-only folders as empty
                return []

            # return list of volumes
            r = {x.split("/")[0]: 1 for x in self.hub.asrv.vfs.all_vols.keys()}
            return list(sorted(list(r.keys())))

    def rmdir(self, path: str) -> None:
        ap = self.rv2a(path, d=True)[0]
        try:
            bos.rmdir(ap)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def remove(self, path: str) -> None:
        if self.args.no_del:
            raise FSE("The delete feature is disabled in server config")

        vp = join(self.cwd, path).lstrip("/")
        try:
            self.hub.up2k.handle_rm(self.uname, self.h.cli_ip, [vp], [], False)
        except Exception as ex:
            raise FSE(str(ex))

    def rename(self, src: str, dst: str) -> None:
        if not self.can_move:
            raise FSE("Not allowed for user " + self.h.uname)

        if self.args.no_mv:
            raise FSE("The rename/move feature is disabled in server config")

        svp = join(self.cwd, src).lstrip("/")
        dvp = join(self.cwd, dst).lstrip("/")
        try:
            self.hub.up2k.handle_mv(self.uname, svp, dvp)
        except Exception as ex:
            raise FSE(str(ex))

    def chmod(self, path: str, mode: str) -> None:
        pass

    def stat(self, path: str) -> os.stat_result:
        try:
            ap = self.rv2a(path, r=True)[0]
            return bos.stat(ap)
        except FSE as ex:
            if ex.severity:
                raise

            ap = self.rv2a(path)[0]
            st = bos.stat(ap)
            if not stat.S_ISDIR(st.st_mode):
                raise

            return st

    def utime(self, path: str, timeval: float) -> None:
        ap = self.rv2a(path, w=True)[0]
        return bos.utime(ap, (timeval, timeval))

    def lstat(self, path: str) -> os.stat_result:
        ap = self.rv2a(path)[0]
        return bos.stat(ap)

    def isfile(self, path: str) -> bool:
        try:
            st = self.stat(path)
            return stat.S_ISREG(st.st_mode)
        except Exception as ex:
            if getattr(ex, "severity", 0):
                raise

            return False  # expected for mojibake in ftp_SIZE()

    def islink(self, path: str) -> bool:
        ap = self.rv2a(path)[0]
        return bos.path.islink(ap)

    def isdir(self, path: str) -> bool:
        try:
            st = self.stat(path)
            return stat.S_ISDIR(st.st_mode)
        except Exception as ex:
            if getattr(ex, "severity", 0):
                raise

            return True

    def getsize(self, path: str) -> int:
        ap = self.rv2a(path)[0]
        return bos.path.getsize(ap)

    def getmtime(self, path: str) -> float:
        ap = self.rv2a(path)[0]
        return bos.path.getmtime(ap)

    def realpath(self, path: str) -> str:
        return path

    def lexists(self, path: str) -> bool:
        ap = self.rv2a(path)[0]
        return bos.path.lexists(ap)

    def get_user_by_uid(self, uid: int) -> str:
        return "root"

    def get_group_by_uid(self, gid: int) -> str:
        return "root"


class FtpHandler(FTPHandler):
    abstracted_fs = FtpFs
    hub: "SvcHub"
    args: argparse.Namespace
    uname: str

    def __init__(self, conn: Any, server: Any, ioloop: Any = None) -> None:
        self.hub: "SvcHub" = FtpHandler.hub
        self.args: argparse.Namespace = FtpHandler.args
        self.uname = "*"

        if PY2:
            FTPHandler.__init__(self, conn, server, ioloop)
        else:
            super(FtpHandler, self).__init__(conn, server, ioloop)

        cip = self.remote_ip
        self.cli_ip = cip[7:] if cip.startswith("::ffff:") else cip

        # abspath->vpath mapping to resolve log_transfer paths
        self.vfs_map: dict[str, str] = {}

        # reduce non-debug logging
        self.log_cmds_list = [x for x in self.log_cmds_list if x not in ("CWD", "XCWD")]

    def ftp_STOR(self, file: str, mode: str = "w") -> Any:
        # Optional[str]
        vp = join(self.fs.cwd, file).lstrip("/")
        ap, vfs, rem = self.fs.v2a(vp, w=True)
        self.vfs_map[ap] = vp
        xbu = vfs.flags.get("xbu")
        if xbu and not runhook(
            None,
            xbu,
            ap,
            vfs.canonical(rem),
            "",
            self.uname,
            0,
            0,
            self.cli_ip,
            0,
            "",
        ):
            raise FSE("Upload blocked by xbu server config")

        # print("ftp_STOR: {} {} => {}".format(vp, mode, ap))
        ret = FTPHandler.ftp_STOR(self, file, mode)
        # print("ftp_STOR: {} {} OK".format(vp, mode))
        return ret

    def log_transfer(
        self,
        cmd: str,
        filename: bytes,
        receive: bool,
        completed: bool,
        elapsed: float,
        bytes: int,
    ) -> Any:
        # None
        ap = filename.decode("utf-8", "replace")
        vp = self.vfs_map.pop(ap, None)
        # print("xfer_end: {} => {}".format(ap, vp))
        if vp:
            vp, fn = os.path.split(vp)
            vfs, rem = self.hub.asrv.vfs.get(vp, self.uname, False, True)
            vfs, rem = vfs.get_dbv(rem)
            self.hub.up2k.hash_file(
                vfs.realpath,
                vfs.vpath,
                vfs.flags,
                rem,
                fn,
                self.cli_ip,
                time.time(),
                self.uname,
            )

        return FTPHandler.log_transfer(
            self, cmd, filename, receive, completed, elapsed, bytes
        )


try:
    from pyftpdlib.handlers import TLS_FTPHandler

    class SftpHandler(FtpHandler, TLS_FTPHandler):
        pass

except:
    pass


class Ftpd(object):
    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.args = hub.args

        hs = []
        if self.args.ftp:
            hs.append([FtpHandler, self.args.ftp])
        if self.args.ftps:
            try:
                h1 = SftpHandler
            except:
                t = "\nftps requires pyopenssl;\nplease run the following:\n\n  {} -m pip install --user pyopenssl\n"
                print(t.format(pybin))
                sys.exit(1)

            h1.certfile = self.args.cert
            h1.tls_control_required = True
            h1.tls_data_required = True

            hs.append([h1, self.args.ftps])

        for h_lp in hs:
            h2, lp = h_lp
            FtpHandler.hub = h2.hub = hub
            FtpHandler.args = h2.args = hub.args
            FtpHandler.authorizer = h2.authorizer = FtpAuth(hub)

            if self.args.ftp_pr:
                p1, p2 = [int(x) for x in self.args.ftp_pr.split("-")]
                if self.args.ftp and self.args.ftps:
                    # divide port range in half
                    d = int((p2 - p1) / 2)
                    if lp == self.args.ftp:
                        p2 = p1 + d
                    else:
                        p1 += d + 1

                h2.passive_ports = list(range(p1, p2 + 1))

            if self.args.ftp_nat:
                h2.masquerade_address = self.args.ftp_nat

        lgr = logging.getLogger("pyftpdlib")
        lgr.setLevel(logging.DEBUG if self.args.ftpv else logging.INFO)

        ips = self.args.i
        if "::" in ips:
            ips.append("0.0.0.0")

        if self.args.ftp4:
            ips = [x for x in ips if ":" not in x]

        ioloop = IOLoop()
        for ip in ips:
            for h, lp in hs:
                try:
                    FTPServer((ip, int(lp)), h, ioloop)
                except:
                    if ip != "0.0.0.0" or "::" not in ips:
                        raise

        Daemon(ioloop.loop, "ftp")


def join(p1: str, p2: str) -> str:
    w = os.path.join(p1, p2.replace("\\", "/"))
    return os.path.normpath(w).replace("\\", "/")

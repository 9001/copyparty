# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import stat
import time
import logging
import threading

from .__init__ import E, PY2
from .util import Pebkac, fsenc, exclude_dotfiles
from .bos import bos

try:
    from pyftpdlib.ioloop import IOLoop
except ImportError:
    p = os.path.join(E.mod, "vend")
    print("loading asynchat from " + p)
    sys.path.append(p)
    from pyftpdlib.ioloop import IOLoop

from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed
from pyftpdlib.filesystems import AbstractedFS, FilesystemError
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.log import config_logging


try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from .svchub import SvcHub
except ImportError:
    pass


class FtpAuth(DummyAuthorizer):
    def __init__(self):
        super(FtpAuth, self).__init__()
        self.hub = None  # type: SvcHub

    def validate_authentication(self, username, password, handler):
        asrv = self.hub.asrv
        if username == "anonymous":
            password = ""

        uname = "*"
        if password:
            uname = asrv.iacct.get(password, None)

        handler.username = uname

        if password and not uname:
            raise AuthenticationFailed("Authentication failed.")

    def get_home_dir(self, username):
        return "/"

    def has_user(self, username):
        asrv = self.hub.asrv
        return username in asrv.acct

    def has_perm(self, username, perm, path=None):
        return True  # handled at filesystem layer

    def get_perms(self, username):
        return "elradfmwMT"

    def get_msg_login(self, username):
        return "sup {}".format(username)

    def get_msg_quit(self, username):
        return "cya"


class FtpFs(AbstractedFS):
    def __init__(self, root, cmd_channel):
        self.h = self.cmd_channel = cmd_channel  # type: FTPHandler
        self.hub = cmd_channel.hub  # type: SvcHub
        self.args = cmd_channel.args

        self.uname = self.hub.asrv.iacct.get(cmd_channel.password, "*")

        self.cwd = "/"  # pyftpdlib convention of leading slash
        self.root = "/var/lib/empty"

        self.listdirinfo = self.listdir
        self.chdir(".")

    def v2a(self, vpath, r=False, w=False, m=False, d=False):
        try:
            vpath = vpath.replace("\\", "/").lstrip("/")
            vfs, rem = self.hub.asrv.vfs.get(vpath, self.uname, r, w, m, d)
            if not vfs.realpath:
                raise FilesystemError("no filesystem mounted at this path")

            return os.path.join(vfs.realpath, rem)
        except Pebkac as ex:
            raise FilesystemError(str(ex))

    def rv2a(self, vpath, r=False, w=False, m=False, d=False):
        return self.v2a(os.path.join(self.cwd, vpath), r, w, m, d)

    def ftp2fs(self, ftppath):
        # return self.v2a(ftppath)
        return ftppath  # self.cwd must be vpath

    def fs2ftp(self, fspath):
        # raise NotImplementedError()
        return fspath

    def validpath(self, path):
        if "/.hist/" in path:
            if "/up2k." in path or path.endswith("/dir.txt"):
                raise FilesystemError("access to this file is forbidden")

        return True

    def open(self, filename, mode):
        r = "r" in mode
        w = "w" in mode or "a" in mode or "+" in mode

        ap = self.rv2a(filename, r, w)
        if w and bos.path.exists(ap):
            raise FilesystemError("cannot open existing file for writing")

        self.validpath(ap)
        return open(fsenc(ap), mode)

    def chdir(self, path):
        self.cwd = join(self.cwd, path)
        x = self.hub.asrv.vfs.can_access(self.cwd.lstrip("/"), self.h.username)
        self.can_read, self.can_write, self.can_move, self.can_delete, self.can_get = x

    def mkdir(self, path):
        ap = self.rv2a(path, w=True)
        bos.mkdir(ap)

    def listdir(self, path):
        vpath = join(self.cwd, path).lstrip("/")
        try:
            vfs, rem = self.hub.asrv.vfs.get(vpath, self.uname, True, False)

            fsroot, vfs_ls, vfs_virt = vfs.ls(
                rem, self.uname, not self.args.no_scandir, [[True], [False, True]]
            )
            vfs_ls = [x[0] for x in vfs_ls]
            vfs_ls.extend(vfs_virt.keys())

            if not self.args.ed:
                vfs_ls = exclude_dotfiles(vfs_ls)

            vfs_ls.sort()
            return vfs_ls
        except Exception as ex:
            if vpath:
                # display write-only folders as empty
                return []

            # return list of volumes
            r = {x.split("/")[0]: 1 for x in self.hub.asrv.vfs.all_vols.keys()}
            return list(sorted(list(r.keys())))

    def rmdir(self, path):
        ap = self.rv2a(path, d=True)
        bos.rmdir(ap)

    def remove(self, path):
        if self.args.no_del:
            raise FilesystemError("the delete feature is disabled in server config")

        vp = join(self.cwd, path).lstrip("/")
        x = self.hub.broker.put(
            True, "up2k.handle_rm", self.uname, self.h.remote_ip, [vp]
        )

        try:
            x.get()
        except Exception as ex:
            raise FilesystemError(str(ex))

    def rename(self, src, dst):
        if not self.can_move:
            raise FilesystemError("not allowed for user " + self.h.username)

        if self.args.no_mv:
            m = "the rename/move feature is disabled in server config"
            raise FilesystemError(m)

        svp = join(self.cwd, src).lstrip("/")
        dvp = join(self.cwd, dst).lstrip("/")
        x = self.hub.broker.put(True, "up2k.handle_mv", self.uname, svp, dvp)
        try:
            x.get()
        except Exception as ex:
            raise FilesystemError(str(ex))

    def chmod(self, path, mode):
        pass

    def stat(self, path):
        try:
            ap = self.rv2a(path, r=True)
            return bos.stat(ap)
        except:
            ap = self.rv2a(path)
            st = bos.stat(ap)
            if not stat.S_ISDIR(st.st_mode):
                raise

            return st

    def utime(self, path, timeval):
        ap = self.rv2a(path, w=True)
        return bos.utime(ap, (timeval, timeval))

    def lstat(self, path):
        ap = self.rv2a(path)
        return bos.lstat(ap)

    def isfile(self, path):
        st = self.stat(path)
        return stat.S_ISREG(st.st_mode)

    def islink(self, path):
        ap = self.rv2a(path)
        return bos.path.islink(ap)

    def isdir(self, path):
        try:
            st = self.stat(path)
            return stat.S_ISDIR(st.st_mode)
        except:
            return True

    def getsize(self, path):
        ap = self.rv2a(path)
        return bos.path.getsize(ap)

    def getmtime(self, path):
        ap = self.rv2a(path)
        return bos.path.getmtime(ap)

    def realpath(self, path):
        return path

    def lexists(self, path):
        ap = self.rv2a(path)
        return bos.path.lexists(ap)

    def get_user_by_uid(self, uid):
        return "root"

    def get_group_by_uid(self, gid):
        return "root"


class FtpHandler(FTPHandler):
    abstracted_fs = FtpFs

    def __init__(self, conn, server, ioloop=None):
        if PY2:
            FTPHandler.__init__(self, conn, server, ioloop)
        else:
            super(FtpHandler, self).__init__(conn, server, ioloop)

        # abspath->vpath mapping to resolve log_transfer paths
        self.vfs_map = {}

    def ftp_STOR(self, file, mode="w"):
        vp = join(self.fs.cwd, file).lstrip("/")
        ap = self.fs.v2a(vp)
        self.vfs_map[ap] = vp
        # print("ftp_STOR: {} {} => {}".format(vp, mode, ap))
        ret = FTPHandler.ftp_STOR(self, file, mode)
        # print("ftp_STOR: {} {} OK".format(vp, mode))
        return ret

    def log_transfer(self, cmd, filename, receive, completed, elapsed, bytes):
        ap = filename.decode("utf-8", "replace")
        vp = self.vfs_map.pop(ap, None)
        # print("xfer_end: {} => {}".format(ap, vp))
        if vp:
            vp, fn = os.path.split(vp)
            vfs, rem = self.hub.asrv.vfs.get(vp, self.username, False, True)
            vfs, rem = vfs.get_dbv(rem)
            self.hub.broker.put(
                False,
                "up2k.hash_file",
                vfs.realpath,
                vfs.flags,
                rem,
                fn,
                self.remote_ip,
                time.time(),
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
    def __init__(self, hub):
        self.hub = hub
        self.args = hub.args

        hs = []
        if self.args.ftp:
            hs.append([FtpHandler, self.args.ftp])
        if self.args.ftps:
            try:
                h = SftpHandler
            except:
                m = "\nftps requires pyopenssl;\nplease run the following:\n\n  {} -m pip install --user pyopenssl\n"
                print(m.format(sys.executable))
                sys.exit(1)

            h.certfile = os.path.join(E.cfg, "cert.pem")
            h.tls_control_required = True
            h.tls_data_required = True

            hs.append([h, self.args.ftps])

        for h in hs:
            h, lp = h
            h.hub = hub
            h.args = hub.args
            h.authorizer = FtpAuth()
            h.authorizer.hub = hub

            if self.args.ftp_pr:
                p1, p2 = [int(x) for x in self.args.ftp_pr.split("-")]
                if self.args.ftp and self.args.ftps:
                    # divide port range in half
                    d = int((p2 - p1) / 2)
                    if lp == self.args.ftp:
                        p2 = p1 + d
                    else:
                        p1 += d + 1

                h.passive_ports = list(range(p1, p2 + 1))

            if self.args.ftp_nat:
                h.masquerade_address = self.args.ftp_nat

        if self.args.ftp_dbg:
            config_logging(level=logging.DEBUG)

        ioloop = IOLoop()
        for ip in self.args.i:
            for h, lp in hs:
                FTPServer((ip, int(lp)), h, ioloop)

        t = threading.Thread(target=ioloop.loop)
        t.daemon = True
        t.start()


def join(p1, p2):
    w = os.path.join(p1, p2.replace("\\", "/"))
    return os.path.normpath(w).replace("\\", "/")

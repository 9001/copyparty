# coding: utf-8
from __future__ import print_function, unicode_literals

try:
    from types import SimpleNamespace
except:
    class SimpleNamespace(object):
        def __init__(self, **attr):
            self.__dict__.update(attr)

import inspect
import logging
import os
import stat

from partftpy import TftpContexts, TftpServer, TftpStates
from partftpy.TftpShared import TftpException

from .__init__ import PY2, TYPE_CHECKING
from .authsrv import VFS
from .bos import bos
from .util import Daemon, min_ex, pybin, runhook, undot

if True:  # pylint: disable=using-constant-test
    from typing import Any, Union

if TYPE_CHECKING:
    from .svchub import SvcHub


lg = logging.getLogger("tftp")
debug, info, warning, error = (lg.debug, lg.info, lg.warning, lg.error)


def _serverInitial(self, pkt: Any, raddress: str, rport: int) -> bool:
    info("connection from %s:%s", raddress, rport)
    ret = _orig_serverInitial(self, pkt, raddress, rport)
    ptn = _hub[0].args.tftp_ipa_re
    if ptn and not ptn.match(raddress):
        yeet("client rejected (--tftp-ipa): %s" % (raddress,))
    return ret

# patch ipa-check into partftpd
_hub: list["SvcHub"] = []
_orig_serverInitial = TftpStates.TftpServerState.serverInitial
TftpStates.TftpServerState.serverInitial = _serverInitial


class Tftpd(object):
    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.args = hub.args
        self.asrv = hub.asrv
        self.log = hub.log

        _hub.clear()
        _hub.append(hub)

        lg.setLevel(logging.DEBUG if self.args.tftpv else logging.INFO)
        for x in ["partftpy", "partftpy.TftpStates", "partftpy.TftpServer"]:
            lgr = logging.getLogger(x)
            lgr.setLevel(logging.DEBUG if self.args.tftpv else logging.INFO)

        # patch vfs into partftpy
        TftpContexts.open = self._open
        TftpStates.open = self._open

        fos = SimpleNamespace()
        for k in os.__dict__:
            try:
                setattr(fos, k, getattr(os, k))
            except:
                pass
        fos.access = self._access
        fos.mkdir = self._mkdir
        fos.unlink = self._unlink
        fos.sep = "/"
        TftpContexts.os = fos
        TftpServer.os = fos
        TftpStates.os = fos

        fop = SimpleNamespace()
        for k in os.path.__dict__:
            try:
                setattr(fop, k, getattr(os.path, k))
            except:
                pass
        fop.abspath = self._p_abspath
        fop.exists = self._p_exists
        fop.isdir = self._p_isdir
        fop.normpath = self._p_normpath
        fos.path = fop

        self._disarm(fos)

        ip = next((x for x in self.args.i if ":" not in x), None)
        if not ip:
            self.log("tftp", "IPv6 not supported for tftp; listening on 0.0.0.0", 3)
            ip = "0.0.0.0"

        self.ip = ip
        self.port = int(self.args.tftp)
        self.srv = TftpServer.TftpServer("/", self._ls)
        self.stop = self.srv.stop

        ports = []
        if self.args.tftp_pr:
            p1, p2 = [int(x) for x in self.args.tftp_pr.split("-")]
            ports = list(range(p1, p2 + 1))

        Daemon(self.srv.listen, "tftp", [self.ip, self.port], ka={"ports": ports})

    def nlog(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log("tftp", msg, c)

    def _v2a(
        self, caller: str, vpath: str, perms: list, *a: Any
    ) -> tuple[VFS, str]:
        vpath = vpath.replace("\\", "/").lstrip("/")
        if not perms:
            perms = [True, True]

        debug('%s("%s", %s) %s\033[K\033[0m', caller, vpath, str(a), perms)
        vfs, rem = self.asrv.vfs.get(vpath, "*", *perms)
        return vfs, vfs.canonical(rem)

    def _ls(self, vpath: str, raddress: str, rport: int) -> Any:
        # generate file listing if vpath is dir.txt and return as file object
        return None

    def _open(self, vpath: str, mode: str, *a: Any, **ka: Any) -> Any:
        rd = wr = False
        if mode == "rb":
            rd = True
        elif mode == "wb":
            wr = True
        else:
            raise Exception("bad mode %s" % (mode,))

        vfs, ap = self._v2a("open", vpath, [rd, wr])
        if wr:
            if "*" not in vfs.axs.uwrite:
                yeet("blocked write; folder not world-writable: /%s" % (vpath,))

            if bos.path.exists(ap) and "*" not in vfs.axs.udel:
                yeet("blocked write; folder not world-deletable: /%s" % (vpath,))

            xbu = vfs.flags.get("xbu")
            if xbu and not runhook(
                self.nlog, xbu, ap, vpath, "", "", 0, 0, "8.3.8.7", 0, ""
            ):
                yeet("blocked by xbu server config: " + vpath)

        return open(ap, mode, *a, **ka)

    def _mkdir(self, vpath: str, *a) -> None:
        vfs, ap = self._v2a("mkdir", vpath, [])
        if "*" not in vfs.axs.uwrite:
            yeet("blocked mkdir; folder not world-writable: /%s" % (vpath,))

        return bos.mkdir(ap)

    def _unlink(self, vpath: str) -> None:
        # return bos.unlink(self._v2a("stat", vpath, *a)[1])
        vfs, ap = self._v2a(
            "delete", vpath, [True, False, False, True]
        )

        try:
            inf = bos.stat(ap)
        except:
            return

        if not stat.S_ISREG(inf.st_mode) or inf.st_size:
            yeet("attempted delete of non-empty file")

        vpath = vpath.replace("\\", "/").lstrip("/")
        self.hub.up2k.handle_rm("*", "8.3.8.7", [vpath], [], False)

    def _access(self, *a: Any) -> bool:
        return True

    def _p_abspath(self, vpath: str) -> str:
        return "/" + undot(vpath)

    def _p_normpath(self, *a: Any) -> str:
        return ""

    def _p_exists(self, vpath: str) -> bool:
        try:
            ap = self._v2a("p.exists", vpath, [False, False])[1]
            bos.stat(ap)
            return True
        except:
            return False

    def _p_isdir(self, vpath: str) -> bool:
        try:
            st = bos.stat(self._v2a("p.isdir", vpath, [False, False])[1])
            ret = stat.S_ISDIR(st.st_mode)
            return ret
        except:
            return False

    def _hook(self, *a: Any, **ka: Any) -> None:
        src = inspect.currentframe().f_back.f_code.co_name
        error("\033[31m%s:hook(%s)\033[0m", src, a)
        raise Exception("nope")

    def _disarm(self, fos: SimpleNamespace) -> None:
        fos.chmod = self._hook
        fos.chown = self._hook
        fos.close = self._hook
        fos.ftruncate = self._hook
        fos.lchown = self._hook
        fos.link = self._hook
        fos.listdir = self._hook
        fos.lstat = self._hook
        fos.open = self._hook
        fos.remove = self._hook
        fos.rename = self._hook
        fos.replace = self._hook
        fos.scandir = self._hook
        fos.stat = self._hook
        fos.symlink = self._hook
        fos.truncate = self._hook
        fos.utime = self._hook
        fos.walk = self._hook

        fos.path.expanduser = self._hook
        fos.path.expandvars = self._hook
        fos.path.getatime = self._hook
        fos.path.getctime = self._hook
        fos.path.getmtime = self._hook
        fos.path.getsize = self._hook
        fos.path.isabs = self._hook
        fos.path.isfile = self._hook
        fos.path.islink = self._hook
        fos.path.realpath = self._hook

def yeet(msg: str) -> None:
    warning(msg)
    raise TftpException(msg)

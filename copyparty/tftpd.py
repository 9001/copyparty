# coding: utf-8
from __future__ import print_function, unicode_literals

try:
    from types import SimpleNamespace
except:

    class SimpleNamespace(object):
        def __init__(self, **attr):
            self.__dict__.update(attr)


import logging
import os
import re
import socket
import stat
import threading
import time
from datetime import datetime

try:
    import inspect
except:
    pass

from partftpy import (
    TftpContexts,
    TftpPacketFactory,
    TftpPacketTypes,
    TftpServer,
    TftpStates,
)
from partftpy.TftpShared import TftpException

from .__init__ import EXE, TYPE_CHECKING
from .authsrv import VFS
from .bos import bos
from .util import BytesIO, Daemon, ODict, exclude_dotfiles, min_ex, runhook, undot

if True:  # pylint: disable=using-constant-test
    from typing import Any, Union

if TYPE_CHECKING:
    from .svchub import SvcHub


lg = logging.getLogger("tftp")
debug, info, warning, error = (lg.debug, lg.info, lg.warning, lg.error)


def noop(*a, **ka) -> None:
    pass


def _serverInitial(self, pkt: Any, raddress: str, rport: int) -> bool:
    info("connection from %s:%s", raddress, rport)
    ret = _sinitial[0](self, pkt, raddress, rport)
    nm = _hub[0].args.tftp_ipa_nm
    if nm and not nm.map(raddress):
        yeet("client rejected (--tftp-ipa): %s" % (raddress,))
    return ret


# patch ipa-check into partftpd (part 1/2)
_hub: list["SvcHub"] = []
_sinitial: list[Any] = []


class Tftpd(object):
    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.args = hub.args
        self.asrv = hub.asrv
        self.log = hub.log
        self.mutex = threading.Lock()

        _hub[:] = []
        _hub.append(hub)

        lg.setLevel(logging.DEBUG if self.args.tftpv else logging.INFO)
        for x in ["partftpy", "partftpy.TftpStates", "partftpy.TftpServer"]:
            lgr = logging.getLogger(x)
            lgr.setLevel(logging.DEBUG if self.args.tftpv else logging.INFO)

        if not self.args.tftpv and not self.args.tftpvv:
            # contexts -> states -> packettypes -> shared
            # contexts -> packetfactory
            # packetfactory -> packettypes
            Cs = [
                TftpPacketTypes,
                TftpPacketFactory,
                TftpStates,
                TftpContexts,
                TftpServer,
            ]
            cbak = []
            if not self.args.tftp_no_fast and not EXE:
                try:
                    ptn = re.compile(r"(^\s*)log\.debug\(.*\)$")
                    for C in Cs:
                        cbak.append(C.__dict__)
                        src1 = inspect.getsource(C).split("\n")
                        src2 = "\n".join([ptn.sub("\\1pass", ln) for ln in src1])
                        cfn = C.__spec__.origin
                        exec (compile(src2, filename=cfn, mode="exec"), C.__dict__)
                except Exception:
                    t = "failed to optimize tftp code; run with --tftp-noopt if there are issues:\n"
                    self.log("tftp", t + min_ex(), 3)
                    for n, zd in enumerate(cbak):
                        Cs[n].__dict__ = zd

            for C in Cs:
                C.log.debug = noop

        # patch ipa-check into partftpd (part 2/2)
        _sinitial[:] = []
        _sinitial.append(TftpStates.TftpServerState.serverInitial)
        TftpStates.TftpServerState.serverInitial = _serverInitial

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

        self.port = int(self.args.tftp)
        self.srv = []
        self.ips = []

        ports = []
        if self.args.tftp_pr:
            p1, p2 = [int(x) for x in self.args.tftp_pr.split("-")]
            ports = list(range(p1, p2 + 1))

        ips = self.args.i
        if "::" in ips:
            ips.append("0.0.0.0")

        if self.args.ftp4:
            ips = [x for x in ips if ":" not in x]

        ips = list(ODict.fromkeys(ips))  # dedup

        for ip in ips:
            name = "tftp_%s" % (ip,)
            Daemon(self._start, name, [ip, ports])
            time.sleep(0.2)  # give dualstack a chance

    def nlog(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log("tftp", msg, c)

    def _start(self, ip, ports):
        fam = socket.AF_INET6 if ":" in ip else socket.AF_INET
        have_been_alive = False
        while True:
            srv = TftpServer.TftpServer("/", self._ls)
            with self.mutex:
                self.srv.append(srv)
                self.ips.append(ip)

            try:
                # this is the listen loop; it should block forever
                srv.listen(ip, self.port, af_family=fam, ports=ports)
            except:
                with self.mutex:
                    self.srv.remove(srv)
                    self.ips.remove(ip)

                try:
                    srv.sock.close()
                except:
                    pass

                try:
                    bound = bool(srv.listenport)
                except:
                    bound = False

                if bound:
                    # this instance has managed to bind at least once
                    have_been_alive = True

                if have_been_alive:
                    t = "tftp server [%s]:%d crashed; restarting in 3 sec:\n%s"
                    error(t, ip, self.port, min_ex())
                    time.sleep(3)
                    continue

                # server failed to start; could be due to dualstack (ipv6 managed to bind and this is ipv4)
                if ip != "0.0.0.0" or "::" not in self.ips:
                    # nope, it's fatal
                    t = "tftp server [%s]:%d failed to start:\n%s"
                    error(t, ip, self.port, min_ex())

                # yep; ignore
                # (TODO: move the "listening @ ..." infolog in partftpy to
                #   after the bind attempt so it doesn't print twice)
                return

            info("tftp server [%s]:%d terminated", ip, self.port)
            break

    def stop(self):
        with self.mutex:
            srvs = self.srv[:]

        for srv in srvs:
            srv.stop()

    def _v2a(self, caller: str, vpath: str, perms: list, *a: Any) -> tuple[VFS, str]:
        vpath = vpath.replace("\\", "/").lstrip("/")
        if not perms:
            perms = [True, True]

        debug('%s("%s", %s) %s\033[K\033[0m', caller, vpath, str(a), perms)
        vfs, rem = self.asrv.vfs.get(vpath, "*", *perms)
        return vfs, vfs.canonical(rem)

    def _ls(self, vpath: str, raddress: str, rport: int, force=False) -> Any:
        # generate file listing if vpath is dir.txt and return as file object
        if not force:
            vpath, fn = os.path.split(vpath.replace("\\", "/"))
            ptn = self.args.tftp_lsf
            if not ptn or not ptn.match(fn.lower()):
                return None

        vn, rem = self.asrv.vfs.get(vpath, "*", True, False)
        fsroot, vfs_ls, vfs_virt = vn.ls(
            rem,
            "*",
            not self.args.no_scandir,
            [[True, False]],
        )
        dnames = set([x[0] for x in vfs_ls if stat.S_ISDIR(x[1].st_mode)])
        dirs1 = [(v.st_mtime, v.st_size, k + "/") for k, v in vfs_ls if k in dnames]
        fils1 = [(v.st_mtime, v.st_size, k) for k, v in vfs_ls if k not in dnames]
        real1 = dirs1 + fils1
        realt = [(datetime.fromtimestamp(mt), sz, fn) for mt, sz, fn in real1]
        reals = [
            (
                "%04d-%02d-%02d %02d:%02d:%02d"
                % (
                    zd.year,
                    zd.month,
                    zd.day,
                    zd.hour,
                    zd.minute,
                    zd.second,
                ),
                sz,
                fn,
            )
            for zd, sz, fn in realt
        ]
        virs = [("????-??-?? ??:??:??", 0, k + "/") for k in vfs_virt.keys()]
        ls = virs + reals

        if "*" not in vn.axs.udot:
            names = set(exclude_dotfiles([x[2] for x in ls]))
            ls = [x for x in ls if x[2] in names]

        try:
            biggest = max([x[1] for x in ls])
        except:
            biggest = 0

        perms = []
        if "*" in vn.axs.uread:
            perms.append("read")
        if "*" in vn.axs.udot:
            perms.append("hidden")
        if "*" in vn.axs.uwrite:
            if "*" in vn.axs.udel:
                perms.append("overwrite")
            else:
                perms.append("write")

        fmt = "{{}}  {{:{},}}  {{}}"
        fmt = fmt.format(len("{:,}".format(biggest)))
        retl = ["# permissions: %s" % (", ".join(perms),)]
        retl += [fmt.format(*x) for x in ls]
        ret = "\n".join(retl).encode("utf-8", "replace")
        return BytesIO(ret + b"\n")

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

        if not self.args.tftp_nols and bos.path.isdir(ap):
            return self._ls(vpath, "", 0, True)

        return open(ap, mode, *a, **ka)

    def _mkdir(self, vpath: str, *a) -> None:
        vfs, ap = self._v2a("mkdir", vpath, [])
        if "*" not in vfs.axs.uwrite:
            yeet("blocked mkdir; folder not world-writable: /%s" % (vpath,))

        return bos.mkdir(ap)

    def _unlink(self, vpath: str) -> None:
        # return bos.unlink(self._v2a("stat", vpath, *a)[1])
        vfs, ap = self._v2a("delete", vpath, [True, False, False, True])

        try:
            inf = bos.stat(ap)
        except:
            return

        if not stat.S_ISREG(inf.st_mode) or inf.st_size:
            yeet("attempted delete of non-empty file")

        vpath = vpath.replace("\\", "/").lstrip("/")
        self.hub.up2k.handle_rm("*", "8.3.8.7", [vpath], [], False, False)

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

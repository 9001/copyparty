# coding: utf-8

import inspect
import logging
import os
import random
import stat
import sys
import time
from types import SimpleNamespace

from .__init__ import ANYWIN, TYPE_CHECKING
from .authsrv import LEELOO_DALLAS, VFS
from .util import Daemon, min_ex
from .bos import bos

try:
    from typing import Any
except:
    pass

if TYPE_CHECKING:
    from .svchub import SvcHub


class HLog(logging.Handler):
    def __init__(self, log_func: Any) -> None:
        logging.Handler.__init__(self)
        self.log_func = log_func

    def __repr__(self) -> str:
        level = logging.getLevelName(self.level)
        return "<%s cpp(%s)>" % (self.__class__.__name__, level)

    def flush(self) -> None:
        pass

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.log_func("smb", msg)


class SMB(object):
    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.args = hub.args
        self.asrv = hub.asrv
        self.log_func = hub.log
        self.files: dict[int, tuple[float, str]] = {}

        handler = HLog(hub.log)
        lvl = logging.DEBUG if self.args.smb_dbg else logging.INFO
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(lvl)

        try:
            from impacket import smbserver
            from impacket.ntlm import compute_lmhash, compute_nthash
        except ImportError:
            m = "\033[36m\n{}\033[31m\n\nERROR: need 'impacket'; please run this command:\033[33m\n {} -m pip install --user impacket\n\033[0m"
            print(m.format(min_ex(), sys.executable))
            sys.exit(1)

        # patch vfs into smbserver.os
        fos = SimpleNamespace()
        for k in os.__dict__:
            try:
                setattr(fos, k, getattr(os, k))
            except:
                pass
        fos.close = self._close
        fos.listdir = self._listdir
        fos.mkdir = self._mkdir
        fos.open = self._open
        fos.remove = self._unlink
        fos.rename = self._rename
        fos.stat = self._stat
        fos.unlink = self._unlink
        fos.utime = self._utime
        smbserver.os = fos

        # ...and smbserver.os.path
        fop = SimpleNamespace()
        for k in os.path.__dict__:
            try:
                setattr(fop, k, getattr(os.path, k))
            except:
                pass
        fop.exists = self._p_exists
        fop.getsize = self._p_getsize
        fop.isdir = self._p_isdir
        smbserver.os.path = fop

        # other patches
        smbserver.isInFileJail = self._is_in_file_jail
        self._disarm()

        ip = self.args.i[0]
        port = int(self.args.smb_port)
        srv = smbserver.SimpleSMBServer(listenAddress=ip, listenPort=port)

        ro = "no" if self.args.smbw else "yes"  # (does nothing)
        srv.addShare("A", "/", readOnly=ro)
        srv.setSMB2Support(not self.args.smb1)

        for name, pwd in self.asrv.acct.items():
            for u, p in ((name, pwd), (pwd, "")):
                lmhash = compute_lmhash(p)
                nthash = compute_nthash(p)
                srv.addCredential(u, 0, lmhash, nthash)

        chi = [random.randint(0, 255) for x in range(8)]
        cha = "".join(["{:02x}".format(x) for x in chi])
        srv.setSMBChallenge(cha)

        self.srv = srv
        self.stop = srv.stop
        logging.info("listening @ %s:%s", ip, port)

    def start(self) -> None:
        Daemon(self.srv.start)

    def _v2a(self, caller: str, vpath: str, *a: Any) -> tuple[VFS, str]:
        vpath = vpath.replace("\\", "/").lstrip("/")
        # cf = inspect.currentframe().f_back
        # c1 = cf.f_back.f_code.co_name
        # c2 = cf.f_code.co_name
        logging.debug('%s("%s", %s)\033[K\033[0m', caller, vpath, str(a))

        # TODO find a way to grab `identity` in smbComSessionSetupAndX and smb2SessionSetup
        vfs, rem = self.asrv.vfs.get(vpath, LEELOO_DALLAS, True, True)
        return vfs, vfs.canonical(rem)

    def _listdir(self, vpath: str, *a: Any, **ka: Any) -> list[str]:
        vpath = vpath.replace("\\", "/").lstrip("/")
        # caller = inspect.currentframe().f_back.f_code.co_name
        logging.debug('listdir("%s", %s)\033[K\033[0m', vpath, str(a))
        vfs, rem = self.asrv.vfs.get(vpath, LEELOO_DALLAS, False, False)
        _, vfs_ls, vfs_virt = vfs.ls(
            rem, LEELOO_DALLAS, not self.args.no_scandir, [[False, False]]
        )
        ls = [x[0] for x in vfs_ls]
        ls.extend(vfs_virt.keys())
        return ls

    def _open(
        self, vpath: str, flags: int, chmod: int = 0o777, *a: Any, **ka: Any
    ) -> Any:
        f_ro = os.O_RDONLY
        if ANYWIN:
            f_ro |= os.O_BINARY

        wr = flags != f_ro
        if wr and not self.args.smbw:
            yeet("blocked write (no --smbw): " + vpath)

        vfs, ap = self._v2a("open", vpath, *a)
        if wr and not vfs.axs.uwrite:
            yeet("blocked write (no-write-acc): " + vpath)

        ret = bos.open(ap, flags, chmod, *a, **ka)
        if wr:
            now = time.time()
            nf = len(self.files)
            if nf > 9000:
                oldest = min([x[0] for x in self.files.values()])
                cutoff = oldest + (now - oldest) / 2
                self.files = {k: v for k, v in self.files.items() if v[0] > cutoff}
                logging.info("was tracking %d files, now %d", nf, len(self.files))

            vpath = vpath.replace("\\", "/").lstrip("/")
            self.files[ret] = (now, vpath)

        return ret

    def _close(self, fd: int) -> None:
        os.close(fd)
        if fd not in self.files:
            return

        _, vp = self.files.pop(fd)
        vp, fn = os.path.split(vp)
        vfs, rem = self.hub.asrv.vfs.get(vp, LEELOO_DALLAS, False, True)
        vfs, rem = vfs.get_dbv(rem)
        self.hub.up2k.hash_file(
            vfs.realpath,
            vfs.flags,
            rem,
            fn,
            "1.7.6.2",
            time.time(),
        )

    def _rename(self, vp1: str, vp2: str) -> None:
        if not self.args.smbw:
            yeet("blocked rename (no --smbw): " + vp1)

        vp1 = vp1.lstrip("/")
        vp2 = vp2.lstrip("/")

        vfs2, ap2 = self._v2a("rename", vp2, vp1)
        if not vfs2.axs.uwrite:
            yeet("blocked rename (no-write-acc): " + vp2)

        vfs1, _ = self.asrv.vfs.get(vp1, LEELOO_DALLAS, True, True)
        if not vfs1.axs.umove:
            yeet("blocked rename (no-move-acc): " + vp1)

        self.hub.up2k.handle_mv(LEELOO_DALLAS, vp1, vp2)
        try:
            bos.makedirs(ap2)
        except:
            pass

    def _mkdir(self, vpath: str) -> None:
        if not self.args.smbw:
            yeet("blocked mkdir (no --smbw): " + vpath)

        vfs, ap = self._v2a("mkdir", vpath)
        if not vfs.axs.uwrite:
            yeet("blocked mkdir (no-write-acc): " + vpath)

        return bos.mkdir(ap)

    def _stat(self, vpath: str, *a: Any, **ka: Any) -> os.stat_result:
        return bos.stat(self._v2a("stat", vpath, *a)[1], *a, **ka)

    def _unlink(self, vpath: str) -> None:
        if not self.args.smbw:
            yeet("blocked delete (no --smbw): " + vpath)

        # return bos.unlink(self._v2a("stat", vpath, *a)[1])
        vfs, ap = self._v2a("delete", vpath)
        if not vfs.axs.udel:
            yeet("blocked delete (no-del-acc): " + vpath)

        vpath = vpath.replace("\\", "/").lstrip("/")
        self.hub.up2k.handle_rm(LEELOO_DALLAS, "1.7.6.2", [vpath], [])

    def _utime(self, vpath: str, times: tuple[float, float]) -> None:
        if not self.args.smbw:
            yeet("blocked utime (no --smbw): " + vpath)

        vfs, ap = self._v2a("utime", vpath)
        if not vfs.axs.uwrite:
            yeet("blocked utime (no-write-acc): " + vpath)

        return bos.utime(ap, times)

    def _p_exists(self, vpath: str) -> bool:
        try:
            bos.stat(self._v2a("p.exists", vpath)[1])
            return True
        except:
            return False

    def _p_getsize(self, vpath: str) -> int:
        st = bos.stat(self._v2a("p.getsize", vpath)[1])
        return st.st_size

    def _p_isdir(self, vpath: str) -> bool:
        try:
            st = bos.stat(self._v2a("p.isdir", vpath)[1])
            return stat.S_ISDIR(st.st_mode)
        except:
            return False

    def _hook(self, *a: Any, **ka: Any) -> None:
        src = inspect.currentframe().f_back.f_code.co_name
        logging.error("\033[31m%s:hook(%s)\033[0m", src, a)
        raise Exception("nope")

    def _disarm(self) -> None:
        from impacket import smbserver

        smbserver.os.chmod = self._hook
        smbserver.os.chown = self._hook
        smbserver.os.ftruncate = self._hook
        smbserver.os.lchown = self._hook
        smbserver.os.link = self._hook
        smbserver.os.lstat = self._hook
        smbserver.os.replace = self._hook
        smbserver.os.scandir = self._hook
        smbserver.os.symlink = self._hook
        smbserver.os.truncate = self._hook
        smbserver.os.walk = self._hook

        smbserver.os.path.abspath = self._hook
        smbserver.os.path.expanduser = self._hook
        smbserver.os.path.getatime = self._hook
        smbserver.os.path.getctime = self._hook
        smbserver.os.path.getmtime = self._hook
        smbserver.os.path.isabs = self._hook
        smbserver.os.path.isfile = self._hook
        smbserver.os.path.islink = self._hook
        smbserver.os.path.realpath = self._hook

    def _is_in_file_jail(self, *a: Any) -> bool:
        # handled by vfs
        return True


def yeet(msg: str) -> None:
    logging.info(msg)
    raise Exception(msg)

# coding: utf-8
from __future__ import print_function, unicode_literals

import errno
import hashlib
import logging
import os
import select
import socket
import time
from threading import ExceptHookArgs

import paramiko
import paramiko.common
import paramiko.sftp_attr
from paramiko.common import AUTH_FAILED, AUTH_SUCCESSFUL
from paramiko.sftp import (
    SFTP_FAILURE,
    SFTP_NO_SUCH_FILE,
    SFTP_OK,
    SFTP_OP_UNSUPPORTED,
    SFTP_PERMISSION_DENIED,
)

from .__init__ import ANYWIN, TYPE_CHECKING
from .authsrv import LEELOO_DALLAS, VFS, AuthSrv
from .bos import bos
from .util import (
    VF_CAREFUL,
    Daemon,
    ODict,
    Pebkac,
    ipnorm,
    min_ex,
    read_utf8,
    relchk,
    runhook,
    sanitize_fn,
    ub64enc,
    undot,
    vjoin,
    wunlink,
)

if TYPE_CHECKING:
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Any, BinaryIO, Optional, Union

SATTR = paramiko.sftp_attr.SFTPAttributes


class SSH_Srv(paramiko.ServerInterface):
    def __init__(self, hub: "SvcHub", addr: Any):
        self.hub = hub
        self.args = args = hub.args
        self.log_func = hub.log
        self.uname = "*"

        self.addr = addr
        self.ip = addr[0]
        if self.ip.startswith("::ffff:"):
            self.ip = self.ip[7:]

        zsl = []
        if args.sftp_anon:
            zsl.append("none")
        if args.sftp_key2u:
            zsl.append("publickey")
        if args.sftp_pw or args.sftp_anon:
            zsl.append("password")
        self._auths = ",".join(zsl)

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.hub.log("sftp:%s" % (self.ip,), msg, c)

    def get_allowed_auths(self, username: str) -> str:
        return self._auths

    def get_banner(self) -> tuple[Optional[str], Optional[str]]:
        if self.args.sftpv:
            self.log("get_banner")
        t = self.args.sftp_banner
        if not t:
            return (None, None)
        if t.startswith("@"):
            t = read_utf8(self.log, t[1:], False)
        if t and not t.endswith("\n"):
            t += "\n"
        return (t, "en-US")

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if self.args.sftpv:
            self.log("channel-request: %r, %r" % (kind, chanid))
        if kind == "session":
            return paramiko.common.OPEN_SUCCEEDED
        return paramiko.common.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_none(self, username: str) -> int:
        try:
            return self._check_auth_none(username)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return AUTH_FAILED

    def _check_auth_none(self, uname: str) -> int:
        args = self.args
        if uname != args.sftp_anon or not uname:
            return AUTH_FAILED

        ipn = ipnorm(self.ip)
        bans = self.hub.bans
        if ipn in bans:
            rt = bans[ipn] - time.time()
            if rt < 0:
                self.log("client unbanned")
                del bans[ipn]
            else:
                self.log("client is banned")
                return AUTH_FAILED

        self.uname = "*"
        self.log("auth-none OK: *")
        return AUTH_SUCCESSFUL

    def check_auth_password(self, username: str, password: str) -> int:
        try:
            return self._check_auth_password(username, password)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return AUTH_FAILED

    def _check_auth_password(self, uname: str, pw: str) -> int:
        args = self.args
        if args.sftpv:
            logpw = pw
            if args.log_badpwd == 0:
                logpw = ""
            elif args.log_badpwd == 2:
                zb = hashlib.sha512(pw.encode("utf-8", "replace")).digest()
                logpw = "%" + ub64enc(zb[:12]).decode("ascii")
            self.log("auth-pw: %r, %r" % (uname, logpw))

        ipn = ipnorm(self.ip)
        bans = self.hub.bans
        if ipn in bans:
            rt = bans[ipn] - time.time()
            if rt < 0:
                self.log("client unbanned")
                del bans[ipn]
            else:
                self.log("client is banned")
                return AUTH_FAILED

        anon = args.sftp_anon
        if anon and uname == anon:
            self.uname = "*"
            self.log("auth-pw OK: *")
            return AUTH_SUCCESSFUL

        if not args.sftp_pw:
            return AUTH_FAILED

        if args.usernames:
            alts = ["%s:%s" % (uname, pw)]
        else:
            alts = [pw, uname]

        attempt = "%s:%s" % (uname, pw)
        uname = ""
        asrv = self.hub.asrv
        for zs in alts:
            zs = asrv.iacct.get(asrv.ah.hash(zs), "")
            if zs:
                uname = zs
                break

        if args.ipu and uname == "*":
            uname = args.ipu_iu[args.ipu_nm.map(self.ip)]
        if args.ipr and uname in args.ipr_u:
            if not args.ipr_u[uname].map(self.ip):
                logging.warning("username [%s] rejected by --ipr", uname)
                return AUTH_FAILED

        if not uname or not (asrv.vfs.aread.get(uname) or asrv.vfs.awrite.get(uname)):
            g = self.hub.gpwd
            if g.lim:
                bonk, ip = g.bonk(self.ip, attempt)
                if bonk:
                    logging.warning("client banned: invalid passwords")
                    bans[self.ip] = bonk
                    try:
                        # only possible if multiprocessing disabled
                        self.hub.broker.httpsrv.bans[ip] = bonk  # type: ignore
                        self.hub.broker.httpsrv.nban += 1  # type: ignore
                    except:
                        pass
            return AUTH_FAILED

        self.uname = uname
        self.log("auth-pw OK: %s" % (uname,))
        return AUTH_SUCCESSFUL

    def check_auth_publickey(self, username: str, key: paramiko.PKey) -> int:
        try:
            return self._check_auth_publickey(username, key)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return AUTH_FAILED

    def _check_auth_publickey(self, uname: str, key: paramiko.PKey) -> int:
        args = self.args
        if args.sftpv:
            zs = key.get_name() + "," + key.get_base64()[:32]
            self.log("auth-key: %r, %r" % (uname, zs))

        ipn = ipnorm(self.ip)
        bans = self.hub.bans
        if ipn in bans:
            rt = bans[ipn] - time.time()
            if rt < 0:
                self.log("client unbanned")
                del bans[ipn]
            else:
                self.log("client is banned")
                return AUTH_FAILED

        anon = args.sftp_anon
        if anon and uname == anon:
            self.uname = "*"
            self.log("auth-key OK: *")
            return AUTH_SUCCESSFUL

        attempt = "%s %s" % (key.get_name(), key.get_base64())
        ok = args.sftp_key2u.get(attempt) == uname

        if ok and args.ipr and uname in args.ipr_u:
            if not args.ipr_u[uname].map(self.ip):
                logging.warning("username [%s] rejected by --ipr", uname)
                return AUTH_FAILED

        asrv = self.hub.asrv
        if not ok or not (asrv.vfs.aread.get(uname) or asrv.vfs.awrite.get(uname)):
            self.log("auth-key REJECTED: %s" % (uname,))
            return AUTH_FAILED

        self.uname = uname
        self.log("auth-key OK: %s" % (uname,))
        return AUTH_SUCCESSFUL


class SFTP_FH(paramiko.SFTPHandle):
    def __init__(self, flags: int = 0) -> None:
        self.filename = ""
        self.readfile: Optional[BinaryIO] = None
        self.writefile: Optional[BinaryIO] = None
        super(SFTP_FH, self).__init__(flags)

    def stat(self):
        try:
            f = self.readfile or self.writefile
            return SATTR.from_stat(os.fstat(f.fileno()))
        except OSError as ex:
            return paramiko.SFTPServer.convert_errno(ex.errno)

    def chattr(self, attr):
        # python doesn't have equivalents to fchown or fchmod, so we have to
        # use the stored filename
        if not self.writefile:
            return SFTP_PERMISSION_DENIED
        try:
            paramiko.SFTPServer.set_file_attr(self.filename, attr)
            return SFTP_OK
        except OSError as ex:
            return paramiko.SFTPServer.convert_errno(ex.errno)


class SFTP_Srv(paramiko.SFTPServerInterface):
    def __init__(self, ssh: paramiko.ServerInterface, *a, **ka):
        super(SFTP_Srv, self).__init__(ssh, *a, **ka)
        self.ssh = ssh
        self.ip: str = ssh.ip  # type: ignore
        self.hub: "SvcHub" = ssh.hub  # type: ignore
        self.uname: str = ssh.uname  # type: ignore
        self.args = self.hub.args
        self.asrv: "AuthSrv" = self.hub.asrv
        self.v = self.args.sftpv
        self.vv = self.args.sftpvv

        if self.uname == LEELOO_DALLAS:
            raise Exception("send her back")

        self.vols = [
            vp
            for vp, vn in self.asrv.vfs.all_vols.items()
            if self.uname in vn.axs.uread
            or self.uname in vn.axs.uwrite
            or self.uname in vn.axs.uget
        ]
        self.vis = set()
        for zs in self.vols:
            self.vis.add(zs)
            while zs:
                zs = zs.rsplit("/", 1)[0] if "/" in zs else ""
                self.vis.add(zs)

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.hub.log("sftp:%s" % (self.ip,), msg, c)

    def v2a(
        self,
        vpath: str,
        r: bool = False,
        w: bool = False,
        m: bool = False,
        d: bool = False,
    ) -> tuple[str, VFS, str]:
        vpath = vpath.replace(os.sep, "/").strip("/")
        rd, fn = os.path.split(vpath)
        if relchk(rd):
            self.log("malicious vpath: %s", vpath)
            raise Exception("Unsupported characters in [%s]" % (vpath,))

        fn = sanitize_fn(fn or "")
        vpath = vjoin(rd, fn)
        vn, rem = self.hub.asrv.vfs.get(vpath, self.uname, r, w, m, d)
        if (
            w
            and fn.lower() in vn.flags["emb_all"]
            and self.uname not in vn.axs.uread
            and "wo_up_readme" not in vn.flags
        ):
            fn = "_wo_" + fn
            vpath = vjoin(rd, fn)
            vn, rem = self.hub.asrv.vfs.get(vpath, self.uname, r, w, m, d)

        if not vn.realpath:
            # return "", vn, rem
            raise OSError(errno.ENOENT, "no filesystem mounted at [/%s]" % (vpath,))

        if "xdev" in vn.flags or "xvol" in vn.flags:
            ap = vn.canonical(rem)
            avn = vn.chk_ap(ap)
            t = "Permission denied in [{}]"
            if not avn:
                raise OSError(errno.EPERM, "permission denied in [/%s]" % (vpath,))

            cr, cw, cm, cd, _, _, _, _, _ = avn.uaxs[self.uname]
            if r and not cr or w and not cw or m and not cm or d and not cd:
                raise OSError(errno.EPERM, "permission denied in [/%s]" % (vpath,))

        if "bcasechk" in vn.flags and not vn.casechk(rem, True):
            raise OSError(errno.ENOENT, "file does not exist case-sensitively")

        return os.path.join(vn.realpath, rem), vn, rem

    def list_folder(self, path: str) -> list[SATTR] | int:
        try:
            return self._list_folder(path)
        except Pebkac as ex:
            if ex.code == 404:
                self.log("folder 404: %s" % (path,))
                return SFTP_NO_SUCH_FILE
            return SFTP_PERMISSION_DENIED
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _list_folder(self, path: str) -> list[SATTR] | int:
        if self.v:
            self.log("ls(%s):" % (path,))
        path = path.strip("/")
        try:
            ap, vn, rem = self.v2a(path, r=True)
        except Pebkac:
            try:
                self.v2a(path, w=True)
                self.log("ls(%s): [] (write-only)" % (path,))
                return []  # display write-only folders as empty
            except:
                pass
            if path not in self.vis:
                self.log("ls(%s): EPERM" % (path,))
                return SFTP_PERMISSION_DENIED
            # list of accessible volumes
            ret = []
            zi = int(time.time())
            vst = os.stat_result((16877, -1, -1, 1, 1000, 1000, 8, zi, zi, zi))
            prefix = path + "/"
            for vn in self.asrv.vfs.all_nodes.values():
                if path and not vn.vpath.startswith(prefix):
                    continue  # vn is parent
                vname = vn.vpath[len(prefix) :]
                if "/" in vname or not vname:
                    continue  # only include vols at current level
                ret.append(SATTR.from_stat(vst, filename=vn.vpath))
            ret.sort(key=lambda x: x.filename)
            self.log("ls(%s): vfs-vols; |%d|" % (path, len(ret)))
            return ret

        _, vfs_ls, vfs_virt = vn.ls(
            rem,
            self.uname,
            not self.args.no_scandir,
            [[True, False], [False, True]],
            throw=True,
        )
        ret = [SATTR.from_stat(x[1], filename=x[0]) for x in vfs_ls]
        for zs, vn2 in vfs_virt.items():
            if not vn2.realpath:
                continue
            st = bos.stat(vn2.realpath)
            ret.append(SATTR.from_stat(st, filename=zs))
        if self.uname not in vn.axs.udot:
            ret = [x for x in ret if not x.filename.split("/")[-1].startswith(".")]
        ret.sort(key=lambda x: x.filename)
        self.log("ls(%s): |%d|" % (path, len(ret)))
        return ret

    def stat(self, path: str) -> SATTR | int:
        try:
            return self._stat(path)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def lstat(self, path: str) -> SATTR | int:
        try:
            return self._stat(path)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _stat(self, vp: str) -> SATTR | int:
        vp = vp.strip("/")
        try:
            ap, vn, _ = self.v2a(vp)
            if (
                self.uname not in vn.axs.uread
                and self.uname not in vn.axs.uwrite
                and self.uname not in vn.axs.uget
            ):
                self.log("stat(%s): EPERM" % (vp,))
                return SFTP_PERMISSION_DENIED
            st = bos.stat(ap)
            self.log("stat(%s): %s" % (vp, st))
        except:
            if vp not in self.vis:
                self.log("stat(%s): ENOENT" % (vp,))
                return SFTP_NO_SUCH_FILE
            zi = int(time.time())
            st = os.stat_result((16877, -1, -1, 1, 1000, 1000, 8, zi, zi, zi))
            self.log("stat(%s): vfs-vols")
        return SATTR.from_stat(st)

    def open(self, path: str, flags: int, attr: SATTR) -> paramiko.SFTPHandle | int:
        try:
            return self._open(path, flags, attr)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _open(self, vp: str, iflag: int, attr: SATTR) -> paramiko.SFTPHandle | int:
        if ANYWIN:
            iflag |= os.O_BINARY
        if iflag & os.O_WRONLY:
            rd = False
            wr = True
            if iflag & os.O_APPEND:
                smode = "ab"
            else:
                smode = "wb"
        elif iflag & os.O_RDWR:
            rd = wr = True
            if iflag & os.O_APPEND:
                smode = "a+b"
            else:
                smode = "r+b"
        else:
            rd = True
            wr = False
            smode = "rb"

        try:
            vn, rem = self.asrv.vfs.get(vp, self.uname, rd, wr)
            ap = os.path.join(vn.realpath, rem)
            vf = vn.flags
        except Pebkac as ex:
            t = "denied open file [%s], iflag=%s, read=%s, write=%s: %s"
            self.log(t % (vp, iflag, rd, wr, ex))
            return SFTP_PERMISSION_DENIED

        self.log("open(%s, %x, %s)" % (vp, iflag, smode))

        if wr:
            try:
                st = bos.stat(ap)
                td = time.time() - st.st_mtime
                need_unlink = True
            except:
                need_unlink = False
                td = 0

            xbu = vn.flags.get("xbu")
            if xbu:
                hr = runhook(
                    self.log,
                    None,
                    self.hub.up2k,
                    "xbu.sftp",
                    xbu,
                    ap,
                    vp,
                    "",
                    "",
                    "",
                    0,
                    0,
                    "7.3.8.7",
                    time.time(),
                    None,
                )
                t = hr.get("rejectmsg") or ""
                if t or hr.get("rc") != 0:
                    if not t:
                        t = "upload blocked by xbu server config: %r" % (vp,)
                    self.log(t, 3)
                    return SFTP_PERMISSION_DENIED

            self.log("writing to [%s] => [%s]" % (vp, ap))

        if wr and need_unlink:  # type: ignore  # !rm
            assert td  # type: ignore  # !rm
            if td >= -1 and td <= self.args.ftp_wt:
                # within permitted timeframe; allow overwrite or resume
                do_it = True
            elif self.args.no_del or self.args.ftp_no_ow:
                # file too old, or overwrite not allowed; reject
                do_it = False
            else:
                # allow overwrite if user has delete permission
                do_it = self.uname in vn.axs.udel

            if not do_it:
                t = "file already exists and no permission to overwrite: %s"
                self.log(t % (vp,))
                return SFTP_PERMISSION_DENIED

            # Don't unlink file for append mode
            elif "a" not in smode:
                wunlink(self.log, ap, VF_CAREFUL)

        chmod = getattr(attr, "st_mode", None)
        if chmod is None:
            chmod = vf.get("chmod_f", 0o644)
            self.log("open(%s, %x): client did not chmod" % (vp, iflag))
        else:
            self.log("open(%s, %x): client set chmod 0%o" % (vp, iflag, chmod))

        try:
            fd = os.open(ap, iflag, chmod)
        except OSError as ex:
            t = "failed to os.open [%s] -> [%s] with iflag [%s] and chmod [%s]: %r"
            self.log(t % (vp, ap, iflag, chmod, ex), 3)
            return paramiko.SFTPServer.convert_errno(ex.errno)

        if iflag & os.O_CREAT:
            paramiko.SFTPServer.set_file_attr(ap, attr)

        try:
            f = os.fdopen(fd, smode)
        except OSError as ex:
            t = "failed to os.fdpen [%s] -> [%s] with smode [%s]: %r"
            self.log(t % (vp, ap, smode, ex), 3)
            return paramiko.SFTPServer.convert_errno(ex.errno)

        ret = SFTP_FH(iflag)
        ret.filename = ap
        ret.readfile = f if rd else None
        ret.writefile = f if wr else None
        return ret

    def remove(self, path: str) -> int:
        try:
            return self._remove(path)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _remove(self, vp: str) -> int:
        self.log("rm(%s)" % (vp,))
        if self.args.no_del:
            self.log("The delete feature is disabled in server config")
            return SFTP_PERMISSION_DENIED
        try:
            self.hub.up2k.handle_rm(self.uname, self.ip, [vp], [], False, False)
            self.log("rm(%s): ok" % (vp,))
            return SFTP_OK
        except Pebkac as ex:
            t = "denied delete [%s]: %s"
            self.log(t % (vp, ex))
            if str(ex).startswith("file not found"):
                return SFTP_NO_SUCH_FILE
            try:
                # write-only client trying to rm before upload?
                ap, vn, _ = self.v2a(vp)
                if (
                    self.uname not in vn.axs.uread
                    and self.uname not in vn.axs.uwrite
                    and self.uname not in vn.axs.uget
                ):
                    self.log("rm(%s): EPERM" % (vp,))
                    return SFTP_PERMISSION_DENIED
                if not bos.path.exists(ap):
                    self.log(" `- file didn't exist; returning ENOENT")
                    return SFTP_NO_SUCH_FILE
            except:
                pass
            return SFTP_PERMISSION_DENIED
        except OSError as ex:
            self.log("failed: rm(%s): %r" % (vp, ex))
            return paramiko.SFTPServer.convert_errno(ex.errno)

    def rename(self, oldpath: str, newpath: str) -> int:
        try:
            return self._rename(oldpath, newpath)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _rename(self, svp: str, dvp: str) -> int:
        self.log("mv(%s, %s)" % (svp, dvp))
        if self.args.no_mv:
            self.log("The rename/move feature is disabled in server config")
        svp = svp.strip("/")
        dvp = dvp.strip("/")
        try:
            self.hub.up2k.handle_mv("", self.uname, self.ip, svp, dvp)
            return SFTP_OK
        except Pebkac as ex:
            t = "denied rename [%s] to [%s]: %s"
            self.log(t % (svp, dvp, ex))
            return SFTP_PERMISSION_DENIED
        except OSError as ex:
            self.log("mv(%s, %s): %r" % (svp, dvp, ex))
            return paramiko.SFTPServer.convert_errno(ex.errno)

    def mkdir(self, path: str, attr: SATTR) -> int:
        try:
            return self._mkdir(path, attr)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _mkdir(self, vp: str, attr: SATTR) -> int:
        self.log("mkdir(%s)" % (vp,))
        try:
            vn, rem = self.asrv.vfs.get(vp, self.uname, False, True)
            ap = os.path.join(vn.realpath, rem)
            bos.makedirs(ap, vf=vn.flags)  # filezilla expects this
            if attr is not None:
                paramiko.SFTPServer.set_file_attr(ap, attr)
            return SFTP_OK
        except Pebkac as ex:
            t = "denied mkdir [%s]: %s"
            self.log(t % (vp, ex))
            return SFTP_PERMISSION_DENIED
        except OSError as ex:
            self.log("mkdir(%s): %r" % (vp, ex))
            return paramiko.SFTPServer.convert_errno(ex.errno)

    def rmdir(self, path: str) -> int:
        try:
            return self._rmdir(path)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _rmdir(self, vp: str) -> int:
        self.log("rmdir(%s)" % (vp,))
        try:
            vn, rem = self.asrv.vfs.get(vp, self.uname, False, False, will_del=True)
            ap = os.path.join(vn.realpath, rem)
            bos.rmdir(ap)
            return SFTP_OK
        except Pebkac as ex:
            t = "denied rmdir [%s]: %s"
            self.log(t % (vp, ex))
            return SFTP_PERMISSION_DENIED
        except OSError as ex:
            self.log("rmdir(%s): %r" % (vp, ex))
            return paramiko.SFTPServer.convert_errno(ex.errno)

    def chattr(self, path: str, attr: SATTR) -> int:
        try:
            return self._chattr(path, attr)
        except:
            self.log("unhandled exception: %s" % (min_ex(),), 1)
            return SFTP_FAILURE

    def _chattr(self, vp: str, attr: SATTR) -> int:
        self.log("chattr(%s, %s)" % (vp, attr))
        try:
            vn, rem = self.asrv.vfs.get(vp, self.uname, False, True, will_del=True)
            ap = os.path.join(vn.realpath, rem)
            paramiko.SFTPServer.set_file_attr(ap, attr)
            return SFTP_OK
        except Pebkac as ex:
            t = "denied chattr [%s]: %s"
            self.log(t % (vp, ex))
            return SFTP_PERMISSION_DENIED
        except OSError as ex:
            self.log("chattr(%s): %r" % (vp, ex))
            return paramiko.SFTPServer.convert_errno(ex.errno)

    def symlink(self, target_path: str, path: str) -> int:
        return SFTP_OP_UNSUPPORTED

    def readlink(self, path: str) -> str | int:
        return path

    def canonicalize(self, path: str) -> str:
        return "/%s" % (undot(path),)


class Sftpd(object):
    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.args = args = hub.args
        self.log_func = hub.log
        self.srv: list[socket.socket] = []
        self.bound: list[str] = []
        self.sessions = {}

        ips = args.sftp_i
        if "::" in ips:
            ips.append("0.0.0.0")

        ips = [x for x in ips if not x.startswith(("unix:", "fd:"))]

        if args.sftp4:
            ips = [x for x in ips if ":" not in x]

        if not ips:
            self.log("cannot start sftp-server; no compatible IPs in -i", 1)
            return

        self.hostkeys = []
        hostkeytypes = (
            ("ed25519", "Ed25519Key", {}),  # best
            ("ecdsa", "ECDSAKey", {"bits": 384}),
            ("rsa", "RSAKey", {"bits": 4096}),
            ("dsa", "DSSKey", {}),  # worst
        )
        for fname, aname, opts in hostkeytypes:
            fpath = "%s/ssh_host_%s_key" % (args.sftp_hostk, fname.lower())
            try:
                pkey = getattr(paramiko, aname).from_private_key_file(fpath)
            except Exception as ex:
                try:
                    genfun = getattr(paramiko, aname).generate
                except Exception as ex2:
                    if args.sftpv or fname not in ("dsa", "ed25519"):
                        # dsa dropped in 4.0
                        # ed25519 not supported yet
                        self.log("cannot generate %s hostkey: %r" % (aname, ex2), 3)
                    continue
                self.log("generating hostkey [%s] due to %r" % (fpath, ex))
                pkey = genfun(**opts)
                pkey.write_private_key_file(fpath)
                pkey = getattr(paramiko, aname).from_private_key_file(fpath)
            self.hostkeys.append(pkey)
            if args.sftpv:
                self.log("loaded hostkey %r" % (pkey,))

        ips = list(ODict.fromkeys(ips))  # dedup

        for ip in ips:
            self._bind(ip)

        self.log("listening @ %s port %s" % (self.bound, args.sftp))

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.hub.log("sftp", msg, c)

    def _bind(self, ip: str) -> None:
        port = self.args.sftp
        try:
            ipv = socket.AF_INET6 if ":" in ip else socket.AF_INET
            srv = socket.socket(ipv, socket.SOCK_STREAM)
            if not ANYWIN or self.args.reuseaddr:
                srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            srv.settimeout(0)  # == srv.setblocking(False)
            try:
                srv.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
            except:
                pass  # will create another ipv4 socket instead
            if getattr(self.args, "freebind", False):
                srv.setsockopt(socket.SOL_IP, socket.IP_FREEBIND, 1)
            srv.bind((ip, port))
            srv.listen(10)
            self.srv.append(srv)
            self.bound.append(ip)
        except Exception as ex:
            if ip == "0.0.0.0" and "::" in self.bound:
                return  # dualstack
            self.log("could not listen on (%s,%s): %r" % (ip, port, ex), 3)

    def _accept(self, srv: socket.socket) -> None:
        cli, addr = srv.accept()
        # cli.settimeout(0)  # == srv.setblocking(False)
        self.log("%r is connecting" % (addr,))
        zs = "sftp-%s" % (addr[0],)
        # Daemon(self._accept2, zs, (cli, addr))
        self._accept2(cli, addr)

    def _accept2(self, cli, addr) -> None:
        tra = paramiko.Transport(cli)
        for hkey in self.hostkeys:
            tra.add_server_key(hkey)
        tra.set_subsystem_handler("sftp", paramiko.SFTPServer, SFTP_Srv)
        psrv = SSH_Srv(self.hub, addr)
        try:
            tra.start_server(server=psrv)
        except Exception as ex:
            self.log("%r could not establish connection: %r" % (addr, ex), 3)
            cli.close()
            return

        chan = tra.accept()
        if chan is None:
            self.log("%r did not open an sftp channel" % (addr,), 3)
            cli.close()
            return

        self.sessions[addr] = (chan, tra, psrv)
        # tra.join()
        # self.log("%r disconnected" % (addr,))

    def run(self):
        lgr = logging.getLogger("paramiko.transport")
        lgr.setLevel(logging.DEBUG if self.args.sftpvv else logging.INFO)

        if self.args.no_poll:
            fun = self._run_select
        else:
            fun = self._run_poll
        Daemon(fun, "sftpd")

    def _run_select(self):
        while not self.hub.stopping:
            rx, _, _ = select.select(self.srv, [], [], 180)
            for sck in rx:
                self._accept(sck)

    def _run_poll(self):
        fd2sck = {}
        poll = select.poll()
        for sck in self.srv:
            fd = sck.fileno()
            fd2sck[fd] = sck
            poll.register(fd, select.POLLIN)
        while not self.hub.stopping:
            pr = poll.poll(180 * 1000)
            rx = [fd2sck[x[0]] for x in pr if x[1] & select.POLLIN]
            for sck in rx:
                self._accept(sck)

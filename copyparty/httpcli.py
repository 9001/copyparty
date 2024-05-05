# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse  # typechk
import base64
import calendar
import copy
import errno
import gzip
import hashlib
import itertools
import json
import os
import random
import re
import stat
import string
import threading  # typechk
import time
import uuid
from datetime import datetime
from email.utils import formatdate, parsedate
from operator import itemgetter

import jinja2  # typechk

try:
    import lzma
except:
    pass

from .__init__ import ANYWIN, PY2, TYPE_CHECKING, EnvParams, unicode
from .__version__ import S_VERSION
from .authsrv import VFS  # typechk
from .bos import bos
from .star import StreamTar
from .sutil import StreamArc, gfilter
from .szip import StreamZip
from .up2k import up2k_chunksize
from .util import unquote  # type: ignore
from .util import (
    APPLESAN_RE,
    BITNESS,
    HTTPCODE,
    META_NOBOTS,
    UTC,
    Garda,
    MultipartParser,
    ODict,
    Pebkac,
    UnrecvEOF,
    WrongPostKey,
    absreal,
    alltrace,
    atomic_move,
    exclude_dotfiles,
    fsenc,
    gen_filekey,
    gen_filekey_dbg,
    gencookie,
    get_df,
    get_spd,
    guess_mime,
    gzip_orig_sz,
    hashcopy,
    hidedir,
    html_bescape,
    html_escape,
    humansize,
    ipnorm,
    loadpy,
    min_ex,
    quotep,
    rand_name,
    read_header,
    read_socket,
    read_socket_chunked,
    read_socket_unbounded,
    relchk,
    ren_open,
    runhook,
    s3enc,
    sanitize_fn,
    sanitize_vpath,
    sendfile_kern,
    sendfile_py,
    ub64dec,
    ub64enc,
    ujoin,
    undot,
    unescape_cookie,
    unquotep,
    vjoin,
    vol_san,
    vsplit,
    wrename,
    wunlink,
    yieldfile,
)

if True:  # pylint: disable=using-constant-test
    import typing
    from typing import Any, Generator, Match, Optional, Pattern, Type, Union

if TYPE_CHECKING:
    from .httpconn import HttpConn

_ = (argparse, threading)

NO_CACHE = {"Cache-Control": "no-cache"}


class HttpCli(object):
    """
    Spawned by HttpConn to process one http transaction
    """

    def __init__(self, conn: "HttpConn") -> None:
        assert conn.sr

        self.t0 = time.time()
        self.conn = conn
        self.u2mutex = conn.u2mutex  # mypy404
        self.s = conn.s
        self.sr = conn.sr
        self.ip = conn.addr[0]
        self.addr: tuple[str, int] = conn.addr
        self.args = conn.args  # mypy404
        self.E: EnvParams = self.args.E
        self.asrv = conn.asrv  # mypy404
        self.ico = conn.ico  # mypy404
        self.thumbcli = conn.thumbcli  # mypy404
        self.u2fh = conn.u2fh  # mypy404
        self.pipes = conn.pipes  # mypy404
        self.log_func = conn.log_func  # mypy404
        self.log_src = conn.log_src  # mypy404
        self.gen_fk = self._gen_fk if self.args.log_fk else gen_filekey
        self.tls: bool = hasattr(self.s, "cipher")

        # placeholders; assigned by run()
        self.keepalive = False
        self.is_https = False
        self.is_vproxied = False
        self.in_hdr_recv = True
        self.headers: dict[str, str] = {}
        self.mode = " "
        self.req = " "
        self.http_ver = ""
        self.hint = ""
        self.host = " "
        self.ua = " "
        self.is_rclone = False
        self.ouparam: dict[str, str] = {}
        self.uparam: dict[str, str] = {}
        self.cookies: dict[str, str] = {}
        self.avn: Optional[VFS] = None
        self.vn = self.asrv.vfs
        self.rem = " "
        self.vpath = " "
        self.vpaths = " "
        self.gctx = " "  # additional context for garda
        self.trailing_slash = True
        self.uname = " "
        self.pw = " "
        self.rvol = [" "]
        self.wvol = [" "]
        self.avol = [" "]
        self.do_log = True
        self.can_read = False
        self.can_write = False
        self.can_move = False
        self.can_delete = False
        self.can_get = False
        self.can_upget = False
        self.can_admin = False
        self.can_dot = False
        self.out_headerlist: list[tuple[str, str]] = []
        self.out_headers: dict[str, str] = {}
        # post
        self.parser: Optional[MultipartParser] = None
        # end placeholders

        self.html_head = ""

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        ptn = self.asrv.re_pwd
        if ptn and ptn.search(msg):
            if self.asrv.ah.on:
                msg = ptn.sub("\033[7m pw \033[27m", msg)
            else:
                msg = ptn.sub(self.unpwd, msg)

        self.log_func(self.log_src, msg, c)

    def unpwd(self, m: Match[str]) -> str:
        a, b, c = m.groups()
        return "%s\033[7m %s \033[27m%s" % (a, self.asrv.iacct[b], c)

    def _check_nonfatal(self, ex: Pebkac, post: bool) -> bool:
        if post:
            return ex.code < 300

        return ex.code < 400 or ex.code in [404, 429]

    def _assert_safe_rem(self, rem: str) -> None:
        # sanity check to prevent any disasters
        if rem.startswith("/") or rem.startswith("../") or "/../" in rem:
            raise Exception("that was close")

    def _gen_fk(self, alg: int, salt: str, fspath: str, fsize: int, inode: int) -> str:
        return gen_filekey_dbg(
            alg, salt, fspath, fsize, inode, self.log, self.args.log_fk
        )

    def j2s(self, name: str, **ka: Any) -> str:
        tpl = self.conn.hsrv.j2[name]
        ka["r"] = self.args.SR if self.is_vproxied else ""
        ka["ts"] = self.conn.hsrv.cachebuster()
        ka["lang"] = self.args.lang
        ka["favico"] = self.args.favico
        ka["s_name"] = self.args.bname
        ka["s_doctitle"] = self.args.doctitle
        ka["tcolor"] = self.vn.flags["tcolor"]

        zso = self.vn.flags.get("html_head")
        if zso:
            ka["this"] = self
            self._build_html_head(zso, ka)

        ka["html_head"] = self.html_head
        return tpl.render(**ka)  # type: ignore

    def j2j(self, name: str) -> jinja2.Template:
        return self.conn.hsrv.j2[name]

    def run(self) -> bool:
        """returns true if connection can be reused"""
        self.out_headers = {
            "Vary": "Origin, PW, Cookie",
            "Cache-Control": "no-store, max-age=0",
        }

        if self.args.early_ban and self.is_banned():
            return False

        if self.conn.ipa_nm and not self.conn.ipa_nm.map(self.conn.addr[0]):
            self.log("client rejected (--ipa)", 3)
            self.terse_reply(b"", 500)
            return False

        try:
            self.s.settimeout(2)
            headerlines = read_header(self.sr, self.args.s_thead, self.args.s_thead)
            self.in_hdr_recv = False
            if not headerlines:
                return False

            if not headerlines[0]:
                # seen after login with IE6.0.2900.5512.xpsp.080413-2111 (xp-sp3)
                self.log("BUG: trailing newline from previous request", c="1;31")
                headerlines.pop(0)

            try:
                self.mode, self.req, self.http_ver = headerlines[0].split(" ")

                # normalize incoming headers to lowercase;
                # outgoing headers however are Correct-Case
                for header_line in headerlines[1:]:
                    k, zs = header_line.split(":", 1)
                    self.headers[k.lower()] = zs.strip()
            except:
                msg = "#[ " + " ]\n#[ ".join(headerlines) + " ]"
                raise Pebkac(400, "bad headers", log=msg)

        except Pebkac as ex:
            self.mode = "GET"
            self.req = "[junk]"
            self.http_ver = "HTTP/1.1"
            # self.log("pebkac at httpcli.run #1: " + repr(ex))
            self.keepalive = False
            h = {"WWW-Authenticate": 'Basic realm="a"'} if ex.code == 401 else {}
            try:
                self.loud_reply(unicode(ex), status=ex.code, headers=h, volsan=True)
            except:
                pass

            if ex.log:
                self.log("additional error context:\n" + ex.log, 6)

            return False

        self.conn.hsrv.nreq += 1

        self.ua = self.headers.get("user-agent", "")
        self.is_rclone = self.ua.startswith("rclone/")

        zs = self.headers.get("connection", "").lower()
        self.keepalive = "close" not in zs and (
            self.http_ver != "HTTP/1.0" or zs == "keep-alive"
        )
        self.is_https = (
            self.headers.get("x-forwarded-proto", "").lower() == "https" or self.tls
        )
        self.host = self.headers.get("host") or ""
        if not self.host:
            zs = "%s:%s" % self.s.getsockname()[:2]
            self.host = zs[7:] if zs.startswith("::ffff:") else zs

        trusted_xff = False
        n = self.args.rproxy
        if n:
            zso = self.headers.get(self.args.xff_hdr)
            if zso:
                if n > 0:
                    n -= 1

                zsl = zso.split(",")
                try:
                    cli_ip = zsl[n].strip()
                except:
                    cli_ip = zsl[0].strip()
                    t = "rproxy={} oob x-fwd {}"
                    self.log(t.format(self.args.rproxy, zso), c=3)

                pip = self.conn.addr[0]
                xffs = self.conn.xff_nm
                if xffs and not xffs.map(pip):
                    t = 'got header "%s" from untrusted source "%s" claiming the true client ip is "%s" (raw value: "%s");  if you trust this, you must allowlist this proxy with "--xff-src=%s"%s'
                    if self.headers.get("cf-connecting-ip"):
                        t += '  Note: if you are behind cloudflare, then this default header is not a good choice; please first make sure your local reverse-proxy (if any) does not allow non-cloudflare IPs from providing cf-* headers, and then add this additional global setting: "--xff-hdr=cf-connecting-ip"'
                    else:
                        t += '  Note: depending on your reverse-proxy, and/or WAF, and/or other intermediates, you may want to read the true client IP from another header by also specifying "--xff-hdr=SomeOtherHeader"'
                    zs = (
                        ".".join(pip.split(".")[:2]) + "."
                        if "." in pip
                        else ":".join(pip.split(":")[:4]) + ":"
                    ) + "0.0/16"
                    zs2 = ' or "--xff-src=lan"' if self.conn.xff_lan.map(pip) else ""
                    self.log(t % (self.args.xff_hdr, pip, cli_ip, zso, zs, zs2), 3)
                else:
                    self.ip = cli_ip
                    self.is_vproxied = bool(self.args.R)
                    self.log_src = self.conn.set_rproxy(self.ip)
                    self.host = self.headers.get("x-forwarded-host") or self.host
                    trusted_xff = True

        if self.is_banned():
            return False

        if self.conn.aclose:
            nka = self.conn.aclose
            ip = ipnorm(self.ip)
            if ip in nka:
                rt = nka[ip] - time.time()
                if rt < 0:
                    self.log("client uncapped", 3)
                    del nka[ip]
                else:
                    self.keepalive = False

        ptn: Optional[Pattern[str]] = self.conn.lf_url  # mypy404
        self.do_log = not ptn or not ptn.search(self.req)

        if self.args.ihead and self.do_log:
            keys = self.args.ihead
            if "*" in keys:
                keys = list(sorted(self.headers.keys()))

            for k in keys:
                zso = self.headers.get(k)
                if zso is not None:
                    self.log("[H] {}: \033[33m[{}]".format(k, zso), 6)

        if "&" in self.req and "?" not in self.req:
            self.hint = "did you mean '?' instead of '&'"

        if self.args.uqe and "/.uqe/" in self.req:
            try:
                vpath, query = self.req.split("?")[0].split("/.uqe/")
                query = query.split("/")[0]  # discard trailing junk
                # (usually a "filename" to trick discord into behaving)
                query = ub64dec(query.encode("utf-8")).decode("utf-8", "replace")
                if query.startswith("/"):
                    self.req = "%s/?%s" % (vpath, query[1:])
                else:
                    self.req = "%s?%s" % (vpath, query)
            except Exception as ex:
                t = "bad uqe in request [%s]: %r" % (self.req, ex)
                self.loud_reply(t, status=400)
                return False

        # split req into vpath + uparam
        uparam = {}
        if "?" not in self.req:
            vpath = unquotep(self.req)  # not query, so + means +
            self.trailing_slash = vpath.endswith("/")
            vpath = undot(vpath)
        else:
            vpath, arglist = self.req.split("?", 1)
            vpath = unquotep(vpath)
            self.trailing_slash = vpath.endswith("/")
            vpath = undot(vpath)

            ptn = self.conn.hsrv.ptn_cc
            for k in arglist.split("&"):
                if "=" in k:
                    k, zs = k.split("=", 1)
                    # x-www-form-urlencoded (url query part) uses
                    # either + or %20 for 0x20 so handle both
                    sv = unquotep(zs.strip().replace("+", " "))
                else:
                    sv = ""

                k = k.lower()
                uparam[k] = sv

                if k in ("doc", "move", "tree"):
                    continue

                zs = "%s=%s" % (k, sv)
                m = ptn.search(zs)
                if not m:
                    continue

                hit = zs[m.span()[0] :]
                t = "malicious user; Cc in query [{}] => [{!r}]"
                self.log(t.format(self.req, hit), 1)
                self.cbonk(self.conn.hsrv.gmal, self.req, "cc_q", "Cc in query")
                self.terse_reply(b"", 500)
                return False

        if self.is_vproxied:
            if vpath.startswith(self.args.R):
                vpath = vpath[len(self.args.R) + 1 :]
            else:
                t = "incorrect --rp-loc or webserver config; expected vpath starting with [{}] but got [{}]"
                self.log(t.format(self.args.R, vpath), 1)

        self.ouparam = {k: zs for k, zs in uparam.items()}

        if self.args.rsp_slp:
            time.sleep(self.args.rsp_slp)
            if self.args.rsp_jtr:
                time.sleep(random.random() * self.args.rsp_jtr)

        zso = self.headers.get("cookie")
        if zso:
            zsll = [x.split("=", 1) for x in zso.split(";") if "=" in x]
            cookies = {k.strip(): unescape_cookie(zs) for k, zs in zsll}
            cookie_pw = cookies.get("cppws") or cookies.get("cppwd") or ""
            if "b" in cookies and "b" not in uparam:
                uparam["b"] = cookies["b"]
        else:
            cookies = {}
            cookie_pw = ""

        if len(uparam) > 10 or len(cookies) > 50:
            self.loud_reply("u wot m8", status=400)
            return False

        self.uparam = uparam
        self.cookies = cookies
        self.vpath = vpath
        self.vpaths = (
            self.vpath + "/" if self.trailing_slash and self.vpath else self.vpath
        )

        if relchk(self.vpath) and (self.vpath != "*" or self.mode != "OPTIONS"):
            self.log("invalid relpath [{}]".format(self.vpath))
            self.cbonk(self.conn.hsrv.gmal, self.req, "bad_vp", "invalid relpaths")
            return self.tx_404() and self.keepalive

        zso = self.headers.get("authorization")
        bauth = ""
        if (
            zso
            and not self.args.no_bauth
            and (not cookie_pw or not self.args.bauth_last)
        ):
            try:
                zb = zso.split(" ")[1].encode("ascii")
                zs = base64.b64decode(zb).decode("utf-8")
                # try "pwd", "x:pwd", "pwd:x"
                for bauth in [zs] + zs.split(":", 1)[::-1]:
                    hpw = self.asrv.ah.hash(bauth)
                    if self.asrv.iacct.get(hpw):
                        break
            except:
                pass

        if self.args.idp_h_usr:
            self.pw = ""
            idp_usr = self.headers.get(self.args.idp_h_usr) or ""
            if idp_usr:
                idp_grp = (
                    self.headers.get(self.args.idp_h_grp) or ""
                    if self.args.idp_h_grp
                    else ""
                )

                if not trusted_xff:
                    pip = self.conn.addr[0]
                    xffs = self.conn.xff_nm
                    trusted_xff = xffs and xffs.map(pip)

                trusted_key = (
                    not self.args.idp_h_key
                ) or self.args.idp_h_key in self.headers

                if trusted_key and trusted_xff:
                    self.asrv.idp_checkin(self.conn.hsrv.broker, idp_usr, idp_grp)
                else:
                    if not trusted_key:
                        t = 'the idp-h-key header ("%s") is not present in the request; will NOT trust the other headers saying that the client\'s username is "%s" and group is "%s"'
                        self.log(t % (self.args.idp_h_key, idp_usr, idp_grp), 3)

                    if not trusted_xff:
                        t = 'got IdP headers from untrusted source "%s" claiming the client\'s username is "%s" and group is "%s";  if you trust this, you must allowlist this proxy with "--xff-src=%s"%s'
                        if not self.args.idp_h_key:
                            t += "  Note: you probably also want to specify --idp-h-key <SECRET-HEADER-NAME> for additional security"

                        pip = self.conn.addr[0]
                        zs = (
                            ".".join(pip.split(".")[:2]) + "."
                            if "." in pip
                            else ":".join(pip.split(":")[:4]) + ":"
                        ) + "0.0/16"
                        zs2 = (
                            ' or "--xff-src=lan"' if self.conn.xff_lan.map(pip) else ""
                        )
                        self.log(t % (pip, idp_usr, idp_grp, zs, zs2), 3)

                    idp_usr = "*"
                    idp_grp = ""

                if idp_usr in self.asrv.vfs.aread:
                    self.uname = idp_usr
                    self.html_head += "<script>var is_idp=1</script>\n"
                else:
                    self.log("unknown username: [%s]" % (idp_usr), 1)
                    self.uname = "*"
            else:
                self.uname = "*"
        else:
            self.pw = uparam.get("pw") or self.headers.get("pw") or bauth or cookie_pw
            self.uname = self.asrv.iacct.get(self.asrv.ah.hash(self.pw)) or "*"

        self.rvol = self.asrv.vfs.aread[self.uname]
        self.wvol = self.asrv.vfs.awrite[self.uname]
        self.avol = self.asrv.vfs.aadmin[self.uname]

        if self.pw and (
            self.pw != cookie_pw or self.conn.freshen_pwd + 30 < time.time()
        ):
            self.conn.freshen_pwd = time.time()
            self.get_pwd_cookie(self.pw)

        if self.is_rclone:
            # dots: always include dotfiles if permitted
            # lt: probably more important showing the correct timestamps of any dupes it just uploaded rather than the lastmod time of any non-copyparty-managed symlinks
            # b: basic-browser if it tries to parse the html listing
            uparam["dots"] = ""
            uparam["lt"] = ""
            uparam["b"] = ""
            cookies["b"] = ""

        vn, rem = self.asrv.vfs.get(self.vpath, self.uname, False, False)
        if "xdev" in vn.flags or "xvol" in vn.flags:
            ap = vn.canonical(rem)
            avn = vn.chk_ap(ap)
        else:
            avn = vn

        (
            self.can_read,
            self.can_write,
            self.can_move,
            self.can_delete,
            self.can_get,
            self.can_upget,
            self.can_admin,
            self.can_dot,
        ) = (
            avn.can_access("", self.uname) if avn else [False] * 8
        )
        self.avn = avn
        self.vn = vn
        self.rem = rem

        self.s.settimeout(self.args.s_tbody or None)

        if "norobots" in vn.flags:
            self.html_head += META_NOBOTS
            self.out_headers["X-Robots-Tag"] = "noindex, nofollow"

        try:
            cors_k = self._cors()
            if self.mode in ("GET", "HEAD"):
                return self.handle_get() and self.keepalive
            if self.mode == "OPTIONS":
                return self.handle_options() and self.keepalive

            if not cors_k:
                host = self.headers.get("host", "<?>")
                origin = self.headers.get("origin", "<?>")
                proto = "https://" if self.is_https else "http://"
                guess = "modifying" if (origin and host) else "stripping"
                t = "cors-reject %s because request-header Origin='%s' does not match request-protocol '%s' and host '%s' based on request-header Host='%s' (note: if this request is not malicious, check if your reverse-proxy is accidentally %s request headers, in particular 'Origin', for example by running copyparty with --ihead='*' to show all request headers)"
                self.log(t % (self.mode, origin, proto, self.host, host, guess), 3)
                raise Pebkac(403, "rejected by cors-check")

            # getattr(self.mode) is not yet faster than this
            if self.mode == "POST":
                return self.handle_post() and self.keepalive
            elif self.mode == "PUT":
                return self.handle_put() and self.keepalive
            elif self.mode == "PROPFIND":
                return self.handle_propfind() and self.keepalive
            elif self.mode == "DELETE":
                return self.handle_delete() and self.keepalive
            elif self.mode == "PROPPATCH":
                return self.handle_proppatch() and self.keepalive
            elif self.mode == "LOCK":
                return self.handle_lock() and self.keepalive
            elif self.mode == "UNLOCK":
                return self.handle_unlock() and self.keepalive
            elif self.mode == "MKCOL":
                return self.handle_mkcol() and self.keepalive
            elif self.mode == "MOVE":
                return self.handle_move() and self.keepalive
            else:
                raise Pebkac(400, 'invalid HTTP mode "{0}"'.format(self.mode))

        except Exception as ex:
            if not isinstance(ex, Pebkac):
                pex = Pebkac(500)
            else:
                pex: Pebkac = ex  # type: ignore

            try:
                if pex.code == 999:
                    self.terse_reply(b"", 500)
                    return False

                post = self.mode in ["POST", "PUT"] or "content-length" in self.headers
                if not self._check_nonfatal(pex, post):
                    self.keepalive = False

                em = str(ex)
                msg = em if pex is ex else min_ex()
                if pex.code != 404 or self.do_log:
                    self.log(
                        "%s\033[0m, %s" % (msg, self.vpath),
                        6 if em.startswith("client d/c ") else 3,
                    )

                msg = "%s\r\nURL: %s\r\n" % (em, self.vpath)
                if self.hint:
                    msg += "hint: %s\r\n" % (self.hint,)

                if "database is locked" in em:
                    self.conn.hsrv.broker.say("log_stacks")
                    msg += "hint: important info in the server log\r\n"

                zb = b"<pre>" + html_escape(msg).encode("utf-8", "replace")
                h = {"WWW-Authenticate": 'Basic realm="a"'} if pex.code == 401 else {}
                self.reply(zb, status=pex.code, headers=h, volsan=True)
                if pex.log:
                    self.log("additional error context:\n" + pex.log, 6)

                return self.keepalive
            except Pebkac:
                return False

    def dip(self) -> str:
        if self.args.plain_ip:
            return self.ip.replace(":", ".")
        else:
            return self.conn.iphash.s(self.ip)

    def cbonk(self, g: Garda, v: str, reason: str, descr: str) -> bool:
        self.conn.hsrv.nsus += 1
        if not g.lim:
            return False

        bonk, ip = g.bonk(self.ip, v + self.gctx)
        if not bonk:
            return False

        xban = self.vn.flags.get("xban")
        if not xban or not runhook(
            self.log,
            xban,
            self.vn.canonical(self.rem),
            self.vpath,
            self.host,
            self.uname,
            time.time(),
            0,
            self.ip,
            time.time(),
            reason,
        ):
            self.log("client banned: %s" % (descr,), 1)
            self.conn.hsrv.bans[ip] = bonk
            self.conn.hsrv.nban += 1
            return True

        return False

    def is_banned(self) -> bool:
        if not self.conn.bans:
            return False

        bans = self.conn.bans
        ip = ipnorm(self.ip)
        if ip not in bans:
            return False

        rt = bans[ip] - time.time()
        if rt < 0:
            self.log("client unbanned", 3)
            del bans[ip]
            return False

        self.log("banned for {:.0f} sec".format(rt), 6)
        self.terse_reply(b"thank you for playing", 403)
        return True

    def permit_caching(self) -> None:
        cache = self.uparam.get("cache")
        if cache is None:
            self.out_headers.update(NO_CACHE)
            return

        n = 69 if not cache else 604869 if cache == "i" else int(cache)
        self.out_headers["Cache-Control"] = "max-age=" + str(n)

    def k304(self) -> bool:
        k304 = self.cookies.get("k304")
        return (
            k304 == "y"
            or (self.args.k304 == 2 and k304 != "n")
            or ("; Trident/" in self.ua and not k304)
        )

    def _build_html_head(self, maybe_html: Any, kv: dict[str, Any]) -> bool:
        html = str(maybe_html)
        is_jinja = html[:2] in "%@%"
        if is_jinja:
            html = html.replace("%", "", 1)

        if html.startswith("@"):
            with open(html[1:], "rb") as f:
                html = f.read().decode("utf-8")

        if html.startswith("%"):
            html = html[1:]
            is_jinja = True

        if is_jinja:
            print("applying jinja")
            with self.conn.hsrv.mutex:
                if html not in self.conn.hsrv.j2:
                    j2env = jinja2.Environment()
                    tpl = j2env.from_string(html)
                    self.conn.hsrv.j2[html] = tpl
                html = self.conn.hsrv.j2[html].render(**kv)

        self.html_head += html + "\n"

    def send_headers(
        self,
        length: Optional[int],
        status: int = 200,
        mime: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        response = ["%s %s %s" % (self.http_ver, status, HTTPCODE[status])]

        if length is not None:
            response.append("Content-Length: " + unicode(length))

        if status == 304 and self.k304():
            self.keepalive = False

        # close if unknown length, otherwise take client's preference
        response.append("Connection: " + ("Keep-Alive" if self.keepalive else "Close"))
        response.append("Date: " + formatdate(usegmt=True))

        # headers{} overrides anything set previously
        if headers:
            self.out_headers.update(headers)

        # default to utf8 html if no content-type is set
        if not mime:
            mime = self.out_headers.get("Content-Type") or "text/html; charset=utf-8"

        self.out_headers["Content-Type"] = mime

        for k, zs in list(self.out_headers.items()) + self.out_headerlist:
            response.append("%s: %s" % (k, zs))

        for zs in response:
            m = self.conn.hsrv.ptn_cc.search(zs)
            if m:
                hit = zs[m.span()[0] :]
                t = "malicious user; Cc in out-hdr {!r} => [{!r}]"
                self.log(t.format(zs, hit), 1)
                self.cbonk(self.conn.hsrv.gmal, zs, "cc_hdr", "Cc in out-hdr")
                raise Pebkac(999)

        try:
            # best practice to separate headers and body into different packets
            self.s.sendall("\r\n".join(response).encode("utf-8") + b"\r\n\r\n")
        except:
            raise Pebkac(400, "client d/c while replying headers")

    def reply(
        self,
        body: bytes,
        status: int = 200,
        mime: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        volsan: bool = False,
    ) -> bytes:
        if (
            status > 400
            and status in (403, 404, 422)
            and (
                status != 422
                or (
                    not body.startswith(b"<pre>partial upload exists")
                    and not body.startswith(b"<pre>source file busy")
                )
            )
            and (status != 404 or (self.can_get and not self.can_read))
        ):
            if status == 404:
                g = self.conn.hsrv.g404
            elif status == 403:
                g = self.conn.hsrv.g403
            else:
                g = self.conn.hsrv.g422

            gurl = self.conn.hsrv.gurl
            if (
                gurl.lim
                and (not g.lim or gurl.lim < g.lim)
                and self.args.sus_urls.search(self.vpath)
            ):
                g = self.conn.hsrv.gurl

            if g.lim and (
                g == self.conn.hsrv.g422
                or not self.args.nonsus_urls
                or not self.args.nonsus_urls.search(self.vpath)
            ):
                self.cbonk(g, self.vpath, str(status), "%ss" % (status,))

        if volsan:
            vols = list(self.asrv.vfs.all_vols.values())
            body = vol_san(vols, body)
            try:
                zs = absreal(__file__).rsplit(os.path.sep, 2)[0]
                body = body.replace(zs.encode("utf-8"), b"PP")
            except:
                pass

        self.send_headers(len(body), status, mime, headers)

        try:
            if self.mode != "HEAD":
                self.s.sendall(body)
        except:
            raise Pebkac(400, "client d/c while replying body")

        return body

    def loud_reply(self, body: str, *args: Any, **kwargs: Any) -> None:
        if not kwargs.get("mime"):
            kwargs["mime"] = "text/plain; charset=utf-8"

        self.log(body.rstrip())
        self.reply(body.encode("utf-8") + b"\r\n", *list(args), **kwargs)

    def terse_reply(self, body: bytes, status: int = 200) -> None:
        self.keepalive = False

        lines = [
            "%s %s %s" % (self.http_ver or "HTTP/1.1", status, HTTPCODE[status]),
            "Connection: Close",
        ]

        if body:
            lines.append("Content-Length: " + unicode(len(body)))

        self.s.sendall("\r\n".join(lines).encode("utf-8") + b"\r\n\r\n" + body)

    def urlq(self, add: dict[str, str], rm: list[str]) -> str:
        """
        generates url query based on uparam (b, pw, all others)
        removing anything in rm, adding pairs in add

        also list faster than set until ~20 items
        """

        if self.is_rclone:
            return ""

        kv = {k: zs for k, zs in self.uparam.items() if k not in rm}
        if "pw" in kv:
            pw = self.cookies.get("cppws") or self.cookies.get("cppwd")
            if kv["pw"] == pw:
                del kv["pw"]

        kv.update(add)
        if not kv:
            return ""

        r = ["%s=%s" % (k, quotep(zs)) if zs else k for k, zs in kv.items()]
        return "?" + "&amp;".join(r)

    def ourlq(self) -> str:
        skip = ("pw", "h", "k")
        ret = []
        for k, v in self.ouparam.items():
            if k in skip:
                continue

            t = "%s=%s" % (quotep(k), quotep(v))
            ret.append(t.replace(" ", "+").rstrip("="))

        if not ret:
            return ""

        return "?" + "&".join(ret)

    def redirect(
        self,
        vpath: str,
        suf: str = "",
        msg: str = "aight",
        flavor: str = "go to",
        click: bool = True,
        status: int = 200,
        use302: bool = False,
    ) -> bool:
        vp = self.args.RS + vpath
        html = self.j2s(
            "msg",
            h2='<a href="/{}">{} /{}</a>'.format(
                quotep(vp) + suf, flavor, html_escape(vp, crlf=True) + suf
            ),
            pre=msg,
            click=click,
        ).encode("utf-8", "replace")

        if use302:
            self.reply(html, status=302, headers={"Location": "/" + vpath})
        else:
            self.reply(html, status=status)

        return True

    def _cors(self) -> bool:
        ih = self.headers
        origin = ih.get("origin")
        if not origin:
            sfsite = ih.get("sec-fetch-site")
            if sfsite and sfsite.lower().startswith("cross"):
                origin = ":|"  # sandboxed iframe
            else:
                return True

        oh = self.out_headers
        origin = origin.lower()
        good_origins = self.args.acao + [
            "%s://%s"
            % (
                "https" if self.is_https else "http",
                self.host.lower().split(":")[0],
            )
        ]
        if "pw" in ih or re.sub(r"(:[0-9]{1,5})?/?$", "", origin) in good_origins:
            good_origin = True
            bad_hdrs = ("",)
        else:
            good_origin = False
            bad_hdrs = ("", "pw")

        # '*' blocks auth through cookies / WWW-Authenticate;
        # exact-match for Origin is necessary to unlock those,
        # but the ?pw= param and PW: header are always allowed
        acah = ih.get("access-control-request-headers", "")
        acao = (origin if good_origin else None) or (
            "*" if "*" in good_origins else None
        )
        if self.args.allow_csrf:
            acao = origin or acao or "*"  # explicitly permit impersonation
            acam = ", ".join(self.conn.hsrv.mallow)  # and all methods + headers
            oh["Access-Control-Allow-Credentials"] = "true"
            good_origin = True
        else:
            acam = ", ".join(self.args.acam)
            # wash client-requested headers and roll with that
            if "range" not in acah.lower():
                acah += ",Range"  # firefox
            req_h = acah.split(",")
            req_h = [x.strip() for x in req_h]
            req_h = [x for x in req_h if x.lower() not in bad_hdrs]
            acah = ", ".join(req_h)

        if not acao:
            return False

        oh["Access-Control-Allow-Origin"] = acao
        oh["Access-Control-Allow-Methods"] = acam.upper()
        if acah:
            oh["Access-Control-Allow-Headers"] = acah

        return good_origin

    def handle_get(self) -> bool:
        if self.do_log:
            logmsg = "%-4s %s @%s" % (self.mode, self.req, self.uname)

            if "range" in self.headers:
                try:
                    rval = self.headers["range"].split("=", 1)[1]
                except:
                    rval = self.headers["range"]

                logmsg += " [\033[36m" + rval + "\033[0m]"

            self.log(logmsg)

        # "embedded" resources
        if self.vpath.startswith(".cpr"):
            if self.vpath.startswith(".cpr/ico/"):
                return self.tx_ico(self.vpath.split("/")[-1], exact=True)

            if self.vpath.startswith(".cpr/ssdp"):
                if self.conn.hsrv.ssdp:
                    return self.conn.hsrv.ssdp.reply(self)
                else:
                    self.reply(b"ssdp is disabled in server config", 404)
                    return False

            if self.vpath.startswith(".cpr/dd/") and self.args.mpmc:
                if self.args.mpmc == ".":
                    raise Pebkac(404)

                loc = self.args.mpmc.rstrip("/") + self.vpath[self.vpath.rfind("/") :]
                h = {"Location": loc, "Cache-Control": "max-age=39"}
                self.reply(b"", 301, headers=h)
                return True

            if self.vpath == ".cpr/metrics":
                return self.conn.hsrv.metrics.tx(self)

            path_base = os.path.join(self.E.mod, "web")
            static_path = absreal(os.path.join(path_base, self.vpath[5:]))
            if static_path in self.conn.hsrv.statics:
                return self.tx_file(static_path)

            if not static_path.startswith(path_base):
                t = "malicious user; attempted path traversal [{}] => [{}]"
                self.log(t.format(self.vpath, static_path), 1)
                self.cbonk(self.conn.hsrv.gmal, self.req, "trav", "path traversal")

            self.tx_404()
            return False

        if "cf_challenge" in self.uparam:
            self.reply(self.j2s("cf").encode("utf-8", "replace"))
            return True

        if not self.can_read and not self.can_write and not self.can_get:
            t = "@{} has no access to [{}]"

            if "on403" in self.vn.flags:
                t += " (on403)"
                self.log(t.format(self.uname, self.vpath))
                ret = self.on40x(self.vn.flags["on403"], self.vn, self.rem)
                if ret == "true":
                    return True
                elif ret == "false":
                    return False
                elif ret == "home":
                    self.uparam["h"] = ""
                elif ret == "allow":
                    self.log("plugin override; access permitted")
                    self.can_read = self.can_write = self.can_move = True
                    self.can_delete = self.can_get = self.can_upget = True
                    self.can_admin = True
                else:
                    return self.tx_404(True)
            else:
                if self.vpath:
                    ptn = self.args.nonsus_urls
                    if not ptn or not ptn.search(self.vpath):
                        self.log(t.format(self.uname, self.vpath))

                    return self.tx_404(True)

                self.uparam["h"] = ""

        if "tree" in self.uparam:
            return self.tx_tree()

        if "scan" in self.uparam:
            return self.scanvol()

        if self.args.getmod:
            if "delete" in self.uparam:
                return self.handle_rm([])

            if "move" in self.uparam:
                return self.handle_mv()

        if not self.vpath:
            if "reload" in self.uparam:
                return self.handle_reload()

            if "stack" in self.uparam:
                return self.tx_stack()

            if "ups" in self.uparam:
                return self.tx_ups()

            if "k304" in self.uparam:
                return self.set_k304()

            if "setck" in self.uparam:
                return self.setck()

            if "reset" in self.uparam:
                return self.set_cfg_reset()

            if "hc" in self.uparam:
                return self.tx_svcs()

        if "h" in self.uparam:
            return self.tx_mounts()

        # conditional redirect to single volumes
        if self.vpath == "" and not self.ouparam:
            nread = len(self.rvol)
            nwrite = len(self.wvol)
            if nread + nwrite == 1 or (self.rvol == self.wvol and nread == 1):
                if nread == 1:
                    vpath = self.rvol[0]
                else:
                    vpath = self.wvol[0]

                if self.vpath != vpath:
                    self.redirect(vpath, flavor="redirecting to", use302=True)
                    return True

        return self.tx_browser()

    def handle_propfind(self) -> bool:
        if self.do_log:
            self.log("PFIND %s @%s" % (self.req, self.uname))

        if self.args.no_dav:
            raise Pebkac(405, "WebDAV is disabled in server config")

        vn, rem = self.asrv.vfs.get(self.vpath, self.uname, False, False, err=401)
        tap = vn.canonical(rem)

        if "davauth" in vn.flags and self.uname == "*":
            self.can_read = self.can_write = self.can_get = False

        if not self.can_read and not self.can_write and not self.can_get:
            self.log("inaccessible: [%s]" % (self.vpath,))
            raise Pebkac(401, "authenticate")

        from .dxml import parse_xml

        # enc = "windows-31j"
        # enc = "shift_jis"
        enc = "utf-8"
        uenc = enc.upper()

        clen = int(self.headers.get("content-length", 0))
        if clen:
            buf = b""
            for rbuf in self.get_body_reader()[0]:
                buf += rbuf
                if not rbuf or len(buf) >= 32768:
                    break

            xroot = parse_xml(buf.decode(enc, "replace"))
            xtag = next(x for x in xroot if x.tag.split("}")[-1] == "prop")
            props_lst = [y.tag.split("}")[-1] for y in xtag]
        else:
            props_lst = [
                "contentclass",
                "creationdate",
                "defaultdocument",
                "displayname",
                "getcontentlanguage",
                "getcontentlength",
                "getcontenttype",
                "getlastmodified",
                "href",
                "iscollection",
                "ishidden",
                "isreadonly",
                "isroot",
                "isstructureddocument",
                "lastaccessed",
                "name",
                "parentname",
                "resourcetype",
                "supportedlock",
            ]

        props = set(props_lst)
        depth = self.headers.get("depth", "infinity").lower()

        try:
            topdir = {"vp": "", "st": bos.stat(tap)}
        except OSError as ex:
            if ex.errno not in (errno.ENOENT, errno.ENOTDIR):
                raise
            raise Pebkac(404)

        if depth == "0" or not self.can_read or not stat.S_ISDIR(topdir["st"].st_mode):
            fgen = []

        elif depth == "infinity":
            if not self.args.dav_inf:
                self.log("client wants --dav-inf", 3)
                zb = b'<?xml version="1.0" encoding="utf-8"?>\n<D:error xmlns:D="DAV:"><D:propfind-finite-depth/></D:error>'
                self.reply(zb, 403, "application/xml; charset=utf-8")
                return True

            # this will return symlink-target timestamps
            # because lstat=true would not recurse into subfolders
            # and this is a rare case where we actually want that
            fgen = vn.zipgen(
                rem,
                rem,
                set(),
                self.uname,
                True,
                not self.args.no_scandir,
                wrap=False,
            )

        elif depth == "1":
            _, vfs_ls, vfs_virt = vn.ls(
                rem,
                self.uname,
                not self.args.no_scandir,
                [[True, False]],
                lstat="davrt" not in vn.flags,
            )
            if not self.can_dot:
                names = set(exclude_dotfiles([x[0] for x in vfs_ls]))
                vfs_ls = [x for x in vfs_ls if x[0] in names]

            zi = int(time.time())
            zsr = os.stat_result((16877, -1, -1, 1, 1000, 1000, 8, zi, zi, zi))
            ls = [{"vp": vp, "st": st} for vp, st in vfs_ls]
            ls += [{"vp": v, "st": zsr} for v in vfs_virt]
            fgen = ls  # type: ignore

        else:
            t = "invalid depth value '{}' (must be either '0' or '1'{})"
            t2 = " or 'infinity'" if self.args.dav_inf else ""
            raise Pebkac(412, t.format(depth, t2))

        fgen = itertools.chain([topdir], fgen)  # type: ignore
        vtop = vjoin(self.args.R, vjoin(vn.vpath, rem))

        chunksz = 0x7FF8  # preferred by nginx or cf (dunno which)

        self.send_headers(
            None, 207, "text/xml; charset=" + enc, {"Transfer-Encoding": "chunked"}
        )

        ret = '<?xml version="1.0" encoding="{}"?>\n<D:multistatus xmlns:D="DAV:">'
        ret = ret.format(uenc)
        for x in fgen:
            rp = vjoin(vtop, x["vp"])
            st: os.stat_result = x["st"]
            mtime = st.st_mtime
            if stat.S_ISLNK(st.st_mode):
                try:
                    st = bos.stat(os.path.join(tap, x["vp"]))
                except:
                    continue

            isdir = stat.S_ISDIR(st.st_mode)

            ret += "<D:response><D:href>/%s%s</D:href><D:propstat><D:prop>" % (
                quotep(rp),
                "/" if isdir and rp else "",
            )

            pvs: dict[str, str] = {
                "displayname": html_escape(rp.split("/")[-1]),
                "getlastmodified": formatdate(mtime, usegmt=True),
                "resourcetype": '<D:collection xmlns:D="DAV:"/>' if isdir else "",
                "supportedlock": '<D:lockentry xmlns:D="DAV:"><D:lockscope><D:exclusive/></D:lockscope><D:locktype><D:write/></D:locktype></D:lockentry>',
            }
            if not isdir:
                pvs["getcontenttype"] = html_escape(guess_mime(rp))
                pvs["getcontentlength"] = str(st.st_size)

            for k, v in pvs.items():
                if k not in props:
                    continue
                elif v:
                    ret += "<D:%s>%s</D:%s>" % (k, v, k)
                else:
                    ret += "<D:%s/>" % (k,)

            ret += "</D:prop><D:status>HTTP/1.1 200 OK</D:status></D:propstat>"

            missing = ["<D:%s/>" % (x,) for x in props if x not in pvs]
            if missing and clen:
                t = "<D:propstat><D:prop>{}</D:prop><D:status>HTTP/1.1 404 Not Found</D:status></D:propstat>"
                ret += t.format("".join(missing))

            ret += "</D:response>"
            while len(ret) >= chunksz:
                ret = self.send_chunk(ret, enc, chunksz)

        ret += "</D:multistatus>"
        while ret:
            ret = self.send_chunk(ret, enc, chunksz)

        self.send_chunk("", enc, chunksz)
        # self.reply(ret.encode(enc, "replace"),207, "text/xml; charset=" + enc)
        return True

    def handle_proppatch(self) -> bool:
        if self.do_log:
            self.log("PPATCH %s @%s" % (self.req, self.uname))

        if self.args.no_dav:
            raise Pebkac(405, "WebDAV is disabled in server config")

        if not self.can_write:
            self.log("{} tried to proppatch [{}]".format(self.uname, self.vpath))
            raise Pebkac(401, "authenticate")

        from xml.etree import ElementTree as ET

        from .dxml import mkenod, mktnod, parse_xml

        buf = b""
        for rbuf in self.get_body_reader()[0]:
            buf += rbuf
            if not rbuf or len(buf) >= 128 * 1024:
                break

        if self._applesan():
            return True

        txt = buf.decode("ascii", "replace").lower()
        enc = self.get_xml_enc(txt)
        uenc = enc.upper()

        txt = buf.decode(enc, "replace")
        ET.register_namespace("D", "DAV:")
        xroot = mkenod("D:orz")
        xroot.insert(0, parse_xml(txt))
        xprop = xroot.find(r"./{DAV:}propertyupdate/{DAV:}set/{DAV:}prop")
        assert xprop
        for ze in xprop:
            ze.clear()

        txt = """<multistatus xmlns="DAV:"><response><propstat><status>HTTP/1.1 403 Forbidden</status></propstat></response></multistatus>"""
        xroot = parse_xml(txt)

        el = xroot.find(r"./{DAV:}response")
        assert el
        e2 = mktnod("D:href", quotep(self.args.SRS + self.vpath))
        el.insert(0, e2)

        el = xroot.find(r"./{DAV:}response/{DAV:}propstat")
        assert el
        el.insert(0, xprop)

        ret = '<?xml version="1.0" encoding="{}"?>\n'.format(uenc)
        ret += ET.tostring(xroot).decode("utf-8")

        self.reply(ret.encode(enc, "replace"), 207, "text/xml; charset=" + enc)
        return True

    def handle_lock(self) -> bool:
        if self.do_log:
            self.log("LOCK %s @%s" % (self.req, self.uname))

        if self.args.no_dav:
            raise Pebkac(405, "WebDAV is disabled in server config")

        # win7+ deadlocks if we say no; just smile and nod
        if not self.can_write and "Microsoft-WebDAV" not in self.ua:
            self.log("{} tried to lock [{}]".format(self.uname, self.vpath))
            raise Pebkac(401, "authenticate")

        from xml.etree import ElementTree as ET

        from .dxml import mkenod, mktnod, parse_xml

        abspath = self.vn.dcanonical(self.rem)

        buf = b""
        for rbuf in self.get_body_reader()[0]:
            buf += rbuf
            if not rbuf or len(buf) >= 128 * 1024:
                break

        if self._applesan():
            return True

        txt = buf.decode("ascii", "replace").lower()
        enc = self.get_xml_enc(txt)
        uenc = enc.upper()

        txt = buf.decode(enc, "replace")
        ET.register_namespace("D", "DAV:")
        lk = parse_xml(txt)
        assert lk.tag == "{DAV:}lockinfo"

        token = str(uuid.uuid4())

        if not lk.find(r"./{DAV:}depth"):
            depth = self.headers.get("depth", "infinity")
            lk.append(mktnod("D:depth", depth))

        lk.append(mktnod("D:timeout", "Second-3310"))
        lk.append(mkenod("D:locktoken", mktnod("D:href", token)))
        lk.append(
            mkenod("D:lockroot", mktnod("D:href", quotep(self.args.SRS + self.vpath)))
        )

        lk2 = mkenod("D:activelock")
        xroot = mkenod("D:prop", mkenod("D:lockdiscovery", lk2))
        for a in lk:
            lk2.append(a)

        ret = '<?xml version="1.0" encoding="{}"?>\n'.format(uenc)
        ret += ET.tostring(xroot).decode("utf-8")

        rc = 200
        if self.can_write and not bos.path.isfile(abspath):
            with open(fsenc(abspath), "wb") as _:
                rc = 201

        self.out_headers["Lock-Token"] = "<{}>".format(token)
        self.reply(ret.encode(enc, "replace"), rc, "text/xml; charset=" + enc)
        return True

    def handle_unlock(self) -> bool:
        if self.do_log:
            self.log("UNLOCK %s @%s" % (self.req, self.uname))

        if self.args.no_dav:
            raise Pebkac(405, "WebDAV is disabled in server config")

        if not self.can_write and "Microsoft-WebDAV" not in self.ua:
            self.log("{} tried to lock [{}]".format(self.uname, self.vpath))
            raise Pebkac(401, "authenticate")

        self.send_headers(None, 204)
        return True

    def handle_mkcol(self) -> bool:
        if self._applesan():
            return True

        if self.do_log:
            self.log("MKCOL %s @%s" % (self.req, self.uname))

        try:
            return self._mkdir(self.vpath, True)
        except Pebkac as ex:
            if ex.code >= 500:
                raise

            self.reply(b"", ex.code)
            return True

    def handle_move(self) -> bool:
        dst = self.headers["destination"]
        dst = re.sub("^https?://[^/]+", "", dst).lstrip()
        dst = unquotep(dst)
        if not self._mv(self.vpath, dst.lstrip("/")):
            return False

        return True

    def _applesan(self) -> bool:
        if self.args.dav_mac or "Darwin/" not in self.ua:
            return False

        vp = "/" + self.vpath
        if re.search(APPLESAN_RE, vp):
            zt = '<?xml version="1.0" encoding="utf-8"?>\n<D:error xmlns:D="DAV:"><D:lock-token-submitted><D:href>{}</D:href></D:lock-token-submitted></D:error>'
            zb = zt.format(vp).encode("utf-8", "replace")
            self.reply(zb, 423, "text/xml; charset=utf-8")
            return True

        return False

    def send_chunk(self, txt: str, enc: str, bmax: int) -> str:
        orig_len = len(txt)
        buf = txt[:bmax].encode(enc, "replace")[:bmax]
        try:
            _ = buf.decode(enc)
        except UnicodeDecodeError as ude:
            buf = buf[: ude.start]

        txt = txt[len(buf.decode(enc)) :]
        if txt and len(txt) == orig_len:
            raise Pebkac(500, "chunk slicing failed")

        buf = ("%x\r\n" % (len(buf),)).encode(enc) + buf
        self.s.sendall(buf + b"\r\n")
        return txt

    def handle_options(self) -> bool:
        if self.do_log:
            self.log("OPTIONS %s @%s" % (self.req, self.uname))

        oh = self.out_headers
        oh["Allow"] = ", ".join(self.conn.hsrv.mallow)

        if not self.args.no_dav:
            # PROPPATCH, LOCK, UNLOCK, COPY: noop (spec-must)
            oh["Dav"] = "1, 2"
            oh["Ms-Author-Via"] = "DAV"

        # winxp-webdav doesnt know what 204 is
        self.send_headers(0, 200)
        return True

    def handle_delete(self) -> bool:
        self.log("DELETE %s @%s" % (self.req, self.uname))
        return self.handle_rm([])

    def handle_put(self) -> bool:
        self.log("PUT %s @%s" % (self.req, self.uname))

        if not self.can_write:
            t = "user {} does not have write-access here"
            raise Pebkac(403, t.format(self.uname))

        if not self.args.no_dav and self._applesan():
            return self.headers.get("content-length") == "0"

        if self.headers.get("expect", "").lower() == "100-continue":
            try:
                self.s.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")
            except:
                raise Pebkac(400, "client d/c before 100 continue")

        return self.handle_stash(True)

    def handle_post(self) -> bool:
        self.log("POST %s @%s" % (self.req, self.uname))

        if self.headers.get("expect", "").lower() == "100-continue":
            try:
                self.s.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")
            except:
                raise Pebkac(400, "client d/c before 100 continue")

        if "raw" in self.uparam:
            return self.handle_stash(False)

        ctype = self.headers.get("content-type", "").lower()

        if "multipart/form-data" in ctype:
            return self.handle_post_multipart()

        if (
            "application/json" in ctype
            or "text/plain" in ctype
            or "application/xml" in ctype
        ):
            return self.handle_post_json()

        if "move" in self.uparam:
            return self.handle_mv()

        if "delete" in self.uparam:
            return self.handle_rm([])

        if "application/octet-stream" in ctype:
            return self.handle_post_binary()

        if "application/x-www-form-urlencoded" in ctype:
            opt = self.args.urlform
            if "stash" in opt:
                return self.handle_stash(False)

            if "save" in opt:
                post_sz, _, _, _, path, _ = self.dump_to_file(False)
                self.log("urlform: {} bytes, {}".format(post_sz, path))
            elif "print" in opt:
                reader, _ = self.get_body_reader()
                buf = b""
                for rbuf in reader:
                    buf += rbuf
                    if not rbuf or len(buf) >= 32768:
                        break

                if buf:
                    orig = buf.decode("utf-8", "replace")
                    t = "urlform_raw {} @ {}\n  {}\n"
                    self.log(t.format(len(orig), self.vpath, orig))
                    try:
                        zb = unquote(buf.replace(b"+", b" "))
                        plain = zb.decode("utf-8", "replace")
                        if buf.startswith(b"msg="):
                            plain = plain[4:]
                            xm = self.vn.flags.get("xm")
                            if xm:
                                runhook(
                                    self.log,
                                    xm,
                                    self.vn.canonical(self.rem),
                                    self.vpath,
                                    self.host,
                                    self.uname,
                                    time.time(),
                                    len(buf),
                                    self.ip,
                                    time.time(),
                                    plain,
                                )

                        t = "urlform_dec {} @ {}\n  {}\n"
                        self.log(t.format(len(plain), self.vpath, plain))

                    except Exception as ex:
                        self.log(repr(ex))

            if "get" in opt:
                return self.handle_get()

            raise Pebkac(405, "POST({}) is disabled in server config".format(ctype))

        raise Pebkac(405, "don't know how to handle POST({})".format(ctype))

    def get_xml_enc(self, txt: str) -> str:
        ofs = txt[:512].find(' encoding="')
        enc = ""
        if ofs + 1:
            enc = txt[ofs + 6 :].split('"')[1]
        else:
            enc = self.headers.get("content-type", "").lower()
            ofs = enc.find("charset=")
            if ofs + 1:
                enc = enc[ofs + 4].split("=")[1].split(";")[0].strip("\"'")
            else:
                enc = ""

        return enc or "utf-8"

    def get_body_reader(self) -> tuple[Generator[bytes, None, None], int]:
        bufsz = self.args.s_rd_sz
        if "chunked" in self.headers.get("transfer-encoding", "").lower():
            return read_socket_chunked(self.sr, bufsz), -1

        remains = int(self.headers.get("content-length", -1))
        if remains == -1:
            self.keepalive = False
            return read_socket_unbounded(self.sr, bufsz), remains
        else:
            return read_socket(self.sr, bufsz, remains), remains

    def dump_to_file(self, is_put: bool) -> tuple[int, str, str, int, str, str]:
        # post_sz, sha_hex, sha_b64, remains, path, url
        reader, remains = self.get_body_reader()
        vfs, rem = self.asrv.vfs.get(self.vpath, self.uname, False, True)
        rnd, _, lifetime, xbu, xau = self.upload_flags(vfs)
        lim = vfs.get_dbv(rem)[0].lim
        fdir = vfs.canonical(rem)
        if lim:
            fdir, rem = lim.all(
                self.ip, rem, remains, vfs.realpath, fdir, self.conn.hsrv.broker
            )

        fn = None
        if rem and not self.trailing_slash and not bos.path.isdir(fdir):
            fdir, fn = os.path.split(fdir)
            rem, _ = vsplit(rem)

        bos.makedirs(fdir)

        open_ka: dict[str, Any] = {"fun": open}
        open_a = ["wb", self.args.iobuf]

        # user-request || config-force
        if ("gz" in vfs.flags or "xz" in vfs.flags) and (
            "pk" in vfs.flags
            or "pk" in self.uparam
            or "gz" in self.uparam
            or "xz" in self.uparam
        ):
            fb = {"gz": 9, "xz": 0}  # default/fallback level
            lv = {}  # selected level
            alg = ""  # selected algo (gz=preferred)

            # user-prefs first
            if "gz" in self.uparam or "pk" in self.uparam:  # def.pk
                alg = "gz"
            if "xz" in self.uparam:
                alg = "xz"
            if alg:
                zso = self.uparam.get(alg)
                lv[alg] = fb[alg] if zso is None else int(zso)

            if alg not in vfs.flags:
                alg = "gz" if "gz" in vfs.flags else "xz"

            # then server overrides
            pk = vfs.flags.get("pk")
            if pk is not None:
                # config-forced on
                alg = alg or "gz"  # def.pk
                try:
                    # config-forced opts
                    alg, nlv = pk.split(",")
                    lv[alg] = int(nlv)
                except:
                    pass

            lv[alg] = lv.get(alg) or fb.get(alg) or 0

            self.log("compressing with {} level {}".format(alg, lv.get(alg)))
            if alg == "gz":
                open_ka["fun"] = gzip.GzipFile
                open_a = ["wb", lv[alg], None, 0x5FEE6600]  # 2021-01-01
            elif alg == "xz":
                open_ka = {"fun": lzma.open, "preset": lv[alg]}
                open_a = ["wb"]
            else:
                self.log("fallthrough? thats a bug", 1)

        suffix = "-{:.6f}-{}".format(time.time(), self.dip())
        nameless = not fn
        if nameless:
            suffix += ".bin"
            fn = "put" + suffix

        params = {"suffix": suffix, "fdir": fdir}
        if self.args.nw:
            params = {}
            fn = os.devnull

        params.update(open_ka)
        assert fn

        if not self.args.nw:
            if rnd:
                fn = rand_name(fdir, fn, rnd)

            fn = sanitize_fn(fn or "", "", [".prologue.html", ".epilogue.html"])

        path = os.path.join(fdir, fn)

        if xbu:
            at = time.time() - lifetime
            if not runhook(
                self.log,
                xbu,
                path,
                self.vpath,
                self.host,
                self.uname,
                at,
                remains,
                self.ip,
                at,
                "",
            ):
                t = "upload blocked by xbu server config"
                self.log(t, 1)
                raise Pebkac(403, t)

        if is_put and not (self.args.no_dav or self.args.nw) and bos.path.exists(path):
            # allow overwrite if...
            #  * volflag 'daw' is set, or client is definitely webdav
            #  * and account has delete-access
            # or...
            #  * file exists, is empty, sufficiently new
            #  * and there is no .PARTIAL

            tnam = fn + ".PARTIAL"
            if self.args.dotpart:
                tnam = "." + tnam

            if (
                self.can_delete
                and (vfs.flags.get("daw") or "x-oc-mtime" in self.headers)
            ) or (
                not bos.path.exists(os.path.join(fdir, tnam))
                and not bos.path.getsize(path)
                and bos.path.getmtime(path) >= time.time() - self.args.blank_wt
            ):
                # small toctou, but better than clobbering a hardlink
                wunlink(self.log, path, vfs.flags)

        with ren_open(fn, *open_a, **params) as zfw:
            f, fn = zfw["orz"]
            path = os.path.join(fdir, fn)
            post_sz, sha_hex, sha_b64 = hashcopy(reader, f, self.args.s_wr_slp)

        if lim:
            lim.nup(self.ip)
            lim.bup(self.ip, post_sz)
            try:
                lim.chk_sz(post_sz)
                lim.chk_vsz(self.conn.hsrv.broker, vfs.realpath, post_sz)
            except:
                wunlink(self.log, path, vfs.flags)
                raise

        if self.args.nw:
            return post_sz, sha_hex, sha_b64, remains, path, ""

        at = mt = time.time() - lifetime
        cli_mt = self.headers.get("x-oc-mtime")
        if cli_mt:
            try:
                mt = int(cli_mt)
                times = (int(time.time()), mt)
                bos.utime(path, times, False)
            except:
                pass

        if nameless and "magic" in vfs.flags:
            try:
                ext = self.conn.hsrv.magician.ext(path)
            except Exception as ex:
                self.log("filetype detection failed for [{}]: {}".format(path, ex), 6)
                ext = None

            if ext:
                if rnd:
                    fn2 = rand_name(fdir, "a." + ext, rnd)
                else:
                    fn2 = fn.rsplit(".", 1)[0] + "." + ext

                params["suffix"] = suffix[:-4]
                with ren_open(fn, *open_a, **params) as zfw:
                    f, fn = zfw["orz"]

                path2 = os.path.join(fdir, fn2)
                atomic_move(self.log, path, path2, vfs.flags)
                fn = fn2
                path = path2

        if xau and not runhook(
            self.log,
            xau,
            path,
            self.vpath,
            self.host,
            self.uname,
            mt,
            post_sz,
            self.ip,
            at,
            "",
        ):
            t = "upload blocked by xau server config"
            self.log(t, 1)
            wunlink(self.log, path, vfs.flags)
            raise Pebkac(403, t)

        vfs, rem = vfs.get_dbv(rem)
        self.conn.hsrv.broker.say(
            "up2k.hash_file",
            vfs.realpath,
            vfs.vpath,
            vfs.flags,
            rem,
            fn,
            self.ip,
            at,
            self.uname,
            True,
        )

        vsuf = ""
        if (self.can_read or self.can_upget) and "fk" in vfs.flags:
            alg = 2 if "fka" in vfs.flags else 1
            vsuf = "?k=" + self.gen_fk(
                alg,
                self.args.fk_salt,
                path,
                post_sz,
                0 if ANYWIN else bos.stat(path).st_ino,
            )[: vfs.flags["fk"]]

        vpath = "/".join([x for x in [vfs.vpath, rem, fn] if x])
        vpath = quotep(vpath)

        url = "{}://{}/{}".format(
            "https" if self.is_https else "http",
            self.host,
            self.args.RS + vpath + vsuf,
        )

        return post_sz, sha_hex, sha_b64, remains, path, url

    def handle_stash(self, is_put: bool) -> bool:
        post_sz, sha_hex, sha_b64, remains, path, url = self.dump_to_file(is_put)
        spd = self._spd(post_sz)
        t = "{} wrote {}/{} bytes to {}  # {}"
        self.log(t.format(spd, post_sz, remains, path, sha_b64[:28]))  # 21

        ac = self.uparam.get(
            "want", self.headers.get("accept", "").lower().split(";")[-1]
        )
        if ac == "url":
            t = url
        else:
            t = "{}\n{}\n{}\n{}\n".format(post_sz, sha_b64, sha_hex[:56], url)

        h = {"Location": url} if is_put and url else {}

        if "x-oc-mtime" in self.headers:
            h["X-OC-MTime"] = "accepted"
            t = ""  # some webdav clients expect/prefer this

        self.reply(t.encode("utf-8"), 201, headers=h)
        return True

    def bakflip(
        self, f: typing.BinaryIO, ofs: int, sz: int, sha: str, flags: dict[str, Any]
    ) -> None:
        if not self.args.bak_flips or self.args.nw:
            return

        sdir = self.args.bf_dir
        fp = os.path.join(sdir, sha)
        if bos.path.exists(fp):
            return self.log("no bakflip; have it", 6)

        if not bos.path.isdir(sdir):
            bos.makedirs(sdir)

        if len(bos.listdir(sdir)) >= self.args.bf_nc:
            return self.log("no bakflip; too many", 3)

        nrem = sz
        f.seek(ofs)
        with open(fp, "wb") as fo:
            while nrem:
                buf = f.read(min(nrem, self.args.iobuf))
                if not buf:
                    break

                nrem -= len(buf)
                fo.write(buf)

        if nrem:
            self.log("bakflip truncated; {} remains".format(nrem), 1)
            atomic_move(self.log, fp, fp + ".trunc", flags)
        else:
            self.log("bakflip ok", 2)

    def _spd(self, nbytes: int, add: bool = True) -> str:
        if add:
            self.conn.nbyte += nbytes

        spd1 = get_spd(nbytes, self.t0)
        spd2 = get_spd(self.conn.nbyte, self.conn.t0)
        return "%s %s n%s" % (spd1, spd2, self.conn.nreq)

    def handle_post_multipart(self) -> bool:
        self.parser = MultipartParser(self.log, self.args, self.sr, self.headers)
        self.parser.parse()

        file0: list[tuple[str, Optional[str], Generator[bytes, None, None]]] = []
        try:
            act = self.parser.require("act", 64)
        except WrongPostKey as ex:
            if ex.got == "f" and ex.fname:
                self.log("missing 'act', but looks like an upload so assuming that")
                file0 = [(ex.got, ex.fname, ex.datagen)]
                act = "bput"
            else:
                raise

        if act == "login":
            return self.handle_login()

        if act == "mkdir":
            return self.handle_mkdir()

        if act == "new_md":
            # kinda silly but has the least side effects
            return self.handle_new_md()

        if act == "bput":
            return self.handle_plain_upload(file0)

        if act == "tput":
            return self.handle_text_upload()

        if act == "zip":
            return self.handle_zip_post()

        raise Pebkac(422, 'invalid action "{}"'.format(act))

    def handle_zip_post(self) -> bool:
        assert self.parser
        try:
            k = next(x for x in self.uparam if x in ("zip", "tar"))
        except:
            raise Pebkac(422, "need zip or tar keyword")

        v = self.uparam[k]

        if self._use_dirkey():
            vn = self.vn
            rem = self.rem
        else:
            vn, rem = self.asrv.vfs.get(self.vpath, self.uname, True, False)

        zs = self.parser.require("files", 1024 * 1024)
        if not zs:
            raise Pebkac(422, "need files list")

        items = zs.replace("\r", "").split("\n")
        items = [unquotep(x) for x in items if items]

        self.parser.drop()
        return self.tx_zip(k, v, "", vn, rem, items)

    def handle_post_json(self) -> bool:
        try:
            remains = int(self.headers["content-length"])
        except:
            raise Pebkac(411)

        if remains > 1024 * 1024:
            raise Pebkac(413, "json 2big")

        enc = "utf-8"
        ctype = self.headers.get("content-type", "").lower()
        if "charset" in ctype:
            enc = ctype.split("charset")[1].strip(" =").split(";")[0].strip()

        try:
            json_buf = self.sr.recv_ex(remains)
        except UnrecvEOF:
            raise Pebkac(422, "client disconnected while posting JSON")

        self.log("decoding {} bytes of {} json".format(len(json_buf), enc))
        try:
            body = json.loads(json_buf.decode(enc, "replace"))
        except:
            raise Pebkac(422, "you POSTed invalid json")

        # self.reply(b"cloudflare", 503)
        # return True

        if "srch" in self.uparam or "srch" in body:
            return self.handle_search(body)

        if "delete" in self.uparam:
            return self.handle_rm(body)

        name = undot(body["name"])
        if "/" in name:
            raise Pebkac(400, "your client is old; press CTRL-SHIFT-R and try again")

        vfs, rem = self.asrv.vfs.get(self.vpath, self.uname, False, True)
        dbv, vrem = vfs.get_dbv(rem)

        body["vtop"] = dbv.vpath
        body["ptop"] = dbv.realpath
        body["prel"] = vrem
        body["host"] = self.host
        body["user"] = self.uname
        body["addr"] = self.ip
        body["vcfg"] = dbv.flags

        if not self.can_delete:
            body.pop("replace", None)

        if rem:
            dst = vfs.canonical(rem)
            try:
                if not bos.path.isdir(dst):
                    bos.makedirs(dst)
            except OSError as ex:
                self.log("makedirs failed [{}]".format(dst))
                if not bos.path.isdir(dst):
                    if ex.errno == errno.EACCES:
                        raise Pebkac(500, "the server OS denied write-access")

                    if ex.errno == errno.EEXIST:
                        raise Pebkac(400, "some file got your folder name")

                    raise Pebkac(500, min_ex())
            except:
                raise Pebkac(500, min_ex())

        # not to protect u2fh, but to prevent handshakes while files are closing
        with self.u2mutex:
            x = self.conn.hsrv.broker.ask("up2k.handle_json", body, self.u2fh.aps)
            ret = x.get()

        if self.is_vproxied:
            if "purl" in ret:
                ret["purl"] = self.args.SR + ret["purl"]

        ret = json.dumps(ret)
        self.log(ret)
        self.reply(ret.encode("utf-8"), mime="application/json")
        return True

    def handle_search(self, body: dict[str, Any]) -> bool:
        idx = self.conn.get_u2idx()
        if not idx or not hasattr(idx, "p_end"):
            raise Pebkac(500, "server busy, or sqlite3 not available; cannot search")

        vols: list[VFS] = []
        seen: dict[VFS, bool] = {}
        for vtop in self.rvol:
            vfs, _ = self.asrv.vfs.get(vtop, self.uname, True, False)
            vfs = vfs.dbv or vfs
            if vfs in seen:
                continue

            seen[vfs] = True
            vols.append(vfs)

        t0 = time.time()
        if idx.p_end:
            penalty = 0.7
            t_idle = t0 - idx.p_end
            if idx.p_dur > 0.7 and t_idle < penalty:
                t = "rate-limit {:.1f} sec, cost {:.2f}, idle {:.2f}"
                raise Pebkac(429, t.format(penalty, idx.p_dur, t_idle))

        if "srch" in body:
            # search by up2k hashlist
            vbody = copy.deepcopy(body)
            vbody["hash"] = len(vbody["hash"])
            self.log("qj: " + repr(vbody))
            hits = idx.fsearch(self.uname, vols, body)
            msg: Any = repr(hits)
            taglist: list[str] = []
            trunc = False
        else:
            # search by query params
            q = body["q"]
            n = body.get("n", self.args.srch_hits)
            self.log("qj: {} |{}|".format(q, n))
            hits, taglist, trunc = idx.search(self.uname, vols, q, n)
            msg = len(hits)

        idx.p_end = time.time()
        idx.p_dur = idx.p_end - t0
        self.log("q#: {} ({:.2f}s)".format(msg, idx.p_dur))

        order = []
        for t in self.args.mte:
            if t in taglist:
                order.append(t)
        for t in taglist:
            if t not in order:
                order.append(t)

        if self.is_vproxied:
            for hit in hits:
                hit["rp"] = self.args.RS + hit["rp"]

        rj = {"hits": hits, "tag_order": order, "trunc": trunc}
        r = json.dumps(rj).encode("utf-8")
        self.reply(r, mime="application/json")
        return True

    def handle_post_binary(self) -> bool:
        try:
            remains = int(self.headers["content-length"])
        except:
            raise Pebkac(400, "you must supply a content-length for binary POST")

        try:
            chash = self.headers["x-up2k-hash"]
            wark = self.headers["x-up2k-wark"]
        except KeyError:
            raise Pebkac(400, "need hash and wark headers for binary POST")

        vfs, _ = self.asrv.vfs.get(self.vpath, self.uname, False, True)
        ptop = (vfs.dbv or vfs).realpath

        x = self.conn.hsrv.broker.ask("up2k.handle_chunk", ptop, wark, chash)
        response = x.get()
        chunksize, cstart, path, lastmod, sprs = response

        try:
            if self.args.nw:
                path = os.devnull

            if remains > chunksize:
                raise Pebkac(400, "your chunk is too big to fit")

            self.log("writing {} #{} @{} len {}".format(path, chash, cstart, remains))

            reader = read_socket(self.sr, self.args.s_rd_sz, remains)

            f = None
            fpool = not self.args.no_fpool and sprs
            if fpool:
                with self.u2mutex:
                    try:
                        f = self.u2fh.pop(path)
                    except:
                        pass

            f = f or open(fsenc(path), "rb+", self.args.iobuf)

            try:
                f.seek(cstart[0])
                post_sz, _, sha_b64 = hashcopy(reader, f, self.args.s_wr_slp)

                if sha_b64 != chash:
                    try:
                        self.bakflip(f, cstart[0], post_sz, sha_b64, vfs.flags)
                    except:
                        self.log("bakflip failed: " + min_ex())

                    t = "your chunk got corrupted somehow (received {} bytes); expected vs received hash:\n{}\n{}"
                    raise Pebkac(400, t.format(post_sz, chash, sha_b64))

                if len(cstart) > 1 and path != os.devnull:
                    self.log(
                        "clone {} to {}".format(
                            cstart[0], " & ".join(unicode(x) for x in cstart[1:])
                        )
                    )
                    ofs = 0
                    while ofs < chunksize:
                        bufsz = max(4 * 1024 * 1024, self.args.iobuf)
                        bufsz = min(chunksize - ofs, bufsz)
                        f.seek(cstart[0] + ofs)
                        buf = f.read(bufsz)
                        for wofs in cstart[1:]:
                            f.seek(wofs + ofs)
                            f.write(buf)

                        ofs += len(buf)

                    self.log("clone {} done".format(cstart[0]))

                if not fpool:
                    f.close()
                else:
                    with self.u2mutex:
                        self.u2fh.put(path, f)
            except:
                # maybe busted handle (eg. disk went full)
                f.close()
                raise
        finally:
            x = self.conn.hsrv.broker.ask("up2k.release_chunk", ptop, wark, chash)
            x.get()  # block client until released

        x = self.conn.hsrv.broker.ask("up2k.confirm_chunk", ptop, wark, chash)
        ztis = x.get()
        try:
            num_left, fin_path = ztis
        except:
            self.loud_reply(ztis, status=500)
            return False

        if not num_left and fpool:
            with self.u2mutex:
                self.u2fh.close(path)

        if not num_left and not self.args.nw:
            self.conn.hsrv.broker.ask(
                "up2k.finish_upload", ptop, wark, self.u2fh.aps
            ).get()

        cinf = self.headers.get("x-up2k-stat", "")

        spd = self._spd(post_sz)
        self.log("{:70} thank {}".format(spd, cinf))
        self.reply(b"thank")
        return True

    def handle_login(self) -> bool:
        assert self.parser
        pwd = self.parser.require("cppwd", 64)
        self.parser.drop()

        self.out_headerlist = [
            x for x in self.out_headerlist if x[0] != "Set-Cookie" or "cppw" != x[1][:4]
        ]

        dst = self.args.SRS
        if self.vpath:
            dst += quotep(self.vpaths)

        dst += self.ourlq()

        msg = self.get_pwd_cookie(pwd)
        html = self.j2s("msg", h1=msg, h2='<a href="' + dst + '">ack</a>', redir=dst)
        self.reply(html.encode("utf-8"))
        return True

    def get_pwd_cookie(self, pwd: str) -> str:
        hpwd = self.asrv.ah.hash(pwd)
        uname = self.asrv.iacct.get(hpwd)
        if uname:
            msg = "hi " + uname
            dur = int(60 * 60 * self.args.logout)
        else:
            logpwd = pwd
            if self.args.log_badpwd == 0:
                logpwd = ""
            elif self.args.log_badpwd == 2:
                zb = hashlib.sha512(pwd.encode("utf-8", "replace")).digest()
                logpwd = "%" + base64.b64encode(zb[:12]).decode("utf-8")

            self.log("invalid password: {}".format(logpwd), 3)
            self.cbonk(self.conn.hsrv.gpwd, pwd, "pw", "invalid passwords")

            msg = "naw dude"
            pwd = "x"  # nosec
            dur = 0

        if pwd == "x":
            # reset both plaintext and tls
            # (only affects active tls cookies when tls)
            for k in ("cppwd", "cppws") if self.is_https else ("cppwd",):
                ck = gencookie(k, pwd, self.args.R, False)
                self.out_headerlist.append(("Set-Cookie", ck))
        else:
            k = "cppws" if self.is_https else "cppwd"
            ck = gencookie(k, pwd, self.args.R, self.is_https, dur, "; HttpOnly")
            self.out_headerlist.append(("Set-Cookie", ck))

        return msg

    def handle_mkdir(self) -> bool:
        assert self.parser
        new_dir = self.parser.require("name", 512)
        self.parser.drop()

        return self._mkdir(vjoin(self.vpath, new_dir))

    def _mkdir(self, vpath: str, dav: bool = False) -> bool:
        nullwrite = self.args.nw
        self.gctx = vpath
        vpath = undot(vpath)
        vfs, rem = self.asrv.vfs.get(vpath, self.uname, False, True)
        rem = sanitize_vpath(rem, "/", [])
        fn = vfs.canonical(rem)
        if not fn.startswith(vfs.realpath):
            self.log("invalid mkdir [%s] [%s]" % (self.gctx, vpath), 1)
            raise Pebkac(422)

        if not nullwrite:
            fdir = os.path.dirname(fn)

            if dav and not bos.path.isdir(fdir):
                raise Pebkac(409, "parent folder does not exist")

            if bos.path.isdir(fn):
                raise Pebkac(405, 'folder "/%s" already exists' % (vpath,))

            try:
                bos.makedirs(fn)
            except OSError as ex:
                if ex.errno == errno.EACCES:
                    raise Pebkac(500, "the server OS denied write-access")

                raise Pebkac(500, "mkdir failed:\n" + min_ex())
            except:
                raise Pebkac(500, min_ex())

        self.out_headers["X-New-Dir"] = quotep(vpath)

        if dav:
            self.reply(b"", 201)
        else:
            self.redirect(vpath, status=201)

        return True

    def handle_new_md(self) -> bool:
        assert self.parser
        new_file = self.parser.require("name", 512)
        self.parser.drop()

        nullwrite = self.args.nw
        vfs, rem = self.asrv.vfs.get(self.vpath, self.uname, False, True)
        self._assert_safe_rem(rem)

        ext = "" if "." not in new_file else new_file.split(".")[-1]
        if not ext or len(ext) > 5 or not self.can_delete:
            new_file += ".md"

        sanitized = sanitize_fn(new_file, "", [])

        if not nullwrite:
            fdir = vfs.canonical(rem)
            fn = os.path.join(fdir, sanitized)

            if bos.path.exists(fn):
                raise Pebkac(500, "that file exists already")

            with open(fsenc(fn), "wb") as f:
                f.write(b"`GRUNNUR`\n")

        vpath = "{}/{}".format(self.vpath, sanitized).lstrip("/")
        self.redirect(vpath, "?edit")
        return True

    def upload_flags(self, vfs: VFS) -> tuple[int, bool, int, list[str], list[str]]:
        if self.args.nw:
            rnd = 0
        else:
            rnd = int(self.uparam.get("rand") or self.headers.get("rand") or 0)
            if vfs.flags.get("rand"):  # force-enable
                rnd = max(rnd, vfs.flags["nrand"])

        ac = self.uparam.get(
            "want", self.headers.get("accept", "").lower().split(";")[-1]
        )
        want_url = ac == "url"
        zs = self.uparam.get("life", self.headers.get("life", ""))
        if zs:
            vlife = vfs.flags.get("lifetime") or 0
            lifetime = max(0, int(vlife - int(zs)))
        else:
            lifetime = 0

        return (
            rnd,
            want_url,
            lifetime,
            vfs.flags.get("xbu") or [],
            vfs.flags.get("xau") or [],
        )

    def handle_plain_upload(
        self, file0: list[tuple[str, Optional[str], Generator[bytes, None, None]]]
    ) -> bool:
        assert self.parser
        nullwrite = self.args.nw
        vfs, rem = self.asrv.vfs.get(self.vpath, self.uname, False, True)
        self._assert_safe_rem(rem)

        upload_vpath = self.vpath
        lim = vfs.get_dbv(rem)[0].lim
        fdir_base = vfs.canonical(rem)
        if lim:
            fdir_base, rem = lim.all(
                self.ip, rem, -1, vfs.realpath, fdir_base, self.conn.hsrv.broker
            )
            upload_vpath = "{}/{}".format(vfs.vpath, rem).strip("/")
            if not nullwrite:
                bos.makedirs(fdir_base)

        rnd, want_url, lifetime, xbu, xau = self.upload_flags(vfs)

        files: list[tuple[int, str, str, str, str, str]] = []
        # sz, sha_hex, sha_b64, p_file, fname, abspath
        errmsg = ""
        tabspath = ""
        dip = self.dip()
        t0 = time.time()
        try:
            assert self.parser.gen
            gens = itertools.chain(file0, self.parser.gen)
            for nfile, (p_field, p_file, p_data) in enumerate(gens):
                if not p_file:
                    self.log("discarding incoming file without filename")
                    # fallthrough

                fdir = fdir_base
                fname = sanitize_fn(
                    p_file or "", "", [".prologue.html", ".epilogue.html"]
                )
                if p_file and not nullwrite:
                    if rnd:
                        fname = rand_name(fdir, fname, rnd)

                    if not bos.path.isdir(fdir):
                        raise Pebkac(404, "that folder does not exist")

                    suffix = "-{:.6f}-{}".format(time.time(), dip)
                    open_args = {"fdir": fdir, "suffix": suffix}

                    if "replace" in self.uparam:
                        abspath = os.path.join(fdir, fname)
                        if not self.can_delete:
                            self.log("user not allowed to overwrite with ?replace")
                        elif bos.path.exists(abspath):
                            try:
                                wunlink(self.log, abspath, vfs.flags)
                                t = "overwriting file with new upload: %s"
                            except:
                                t = "toctou while deleting for ?replace: %s"
                            self.log(t % (abspath,))

                    # reserve destination filename
                    with ren_open(fname, "wb", fdir=fdir, suffix=suffix) as zfw:
                        fname = zfw["orz"][1]

                    tnam = fname + ".PARTIAL"
                    if self.args.dotpart:
                        tnam = "." + tnam

                    abspath = os.path.join(fdir, fname)
                else:
                    open_args = {}
                    tnam = fname = os.devnull
                    fdir = abspath = ""

                if xbu:
                    at = time.time() - lifetime
                    if not runhook(
                        self.log,
                        xbu,
                        abspath,
                        self.vpath,
                        self.host,
                        self.uname,
                        at,
                        0,
                        self.ip,
                        at,
                        "",
                    ):
                        t = "upload blocked by xbu server config"
                        self.log(t, 1)
                        raise Pebkac(403, t)

                if lim:
                    lim.chk_bup(self.ip)
                    lim.chk_nup(self.ip)

                try:
                    max_sz = 0
                    if lim:
                        v1 = lim.smax
                        v2 = lim.dfv - lim.dfl
                        max_sz = min(v1, v2) if v1 and v2 else v1 or v2

                    with ren_open(tnam, "wb", self.args.iobuf, **open_args) as zfw:
                        f, tnam = zfw["orz"]
                        tabspath = os.path.join(fdir, tnam)
                        self.log("writing to {}".format(tabspath))
                        sz, sha_hex, sha_b64 = hashcopy(
                            p_data, f, self.args.s_wr_slp, max_sz
                        )
                        if sz == 0:
                            raise Pebkac(400, "empty files in post")

                    if lim:
                        lim.nup(self.ip)
                        lim.bup(self.ip, sz)
                        try:
                            lim.chk_df(tabspath, sz, True)
                            lim.chk_sz(sz)
                            lim.chk_vsz(self.conn.hsrv.broker, vfs.realpath, sz)
                            lim.chk_bup(self.ip)
                            lim.chk_nup(self.ip)
                        except:
                            if not nullwrite:
                                wunlink(self.log, tabspath, vfs.flags)
                                wunlink(self.log, abspath, vfs.flags)
                            fname = os.devnull
                            raise

                    if not nullwrite:
                        atomic_move(self.log, tabspath, abspath, vfs.flags)

                    tabspath = ""

                    files.append(
                        (sz, sha_hex, sha_b64, p_file or "(discarded)", fname, abspath)
                    )
                    at = time.time() - lifetime
                    if xau and not runhook(
                        self.log,
                        xau,
                        abspath,
                        self.vpath,
                        self.host,
                        self.uname,
                        at,
                        sz,
                        self.ip,
                        at,
                        "",
                    ):
                        t = "upload blocked by xau server config"
                        self.log(t, 1)
                        wunlink(self.log, abspath, vfs.flags)
                        raise Pebkac(403, t)

                    dbv, vrem = vfs.get_dbv(rem)
                    self.conn.hsrv.broker.say(
                        "up2k.hash_file",
                        dbv.realpath,
                        vfs.vpath,
                        dbv.flags,
                        vrem,
                        fname,
                        self.ip,
                        at,
                        self.uname,
                        True,
                    )
                    self.conn.nbyte += sz

                except Pebkac:
                    self.parser.drop()
                    raise

        except Pebkac as ex:
            errmsg = vol_san(
                list(self.asrv.vfs.all_vols.values()), unicode(ex).encode("utf-8")
            ).decode("utf-8")
            try:
                got = bos.path.getsize(tabspath)
                t = "connection lost after receiving %s of the file"
                self.log(t % (humansize(got),), 3)
            except:
                pass

        td = max(0.1, time.time() - t0)
        sz_total = sum(x[0] for x in files)
        spd = (sz_total / td) / (1024 * 1024)

        status = "OK"
        if errmsg:
            self.log(errmsg, 3)
            status = "ERROR"

        msg = "{} // {} bytes // {:.3f} MiB/s\n".format(status, sz_total, spd)
        jmsg: dict[str, Any] = {
            "status": status,
            "sz": sz_total,
            "mbps": round(spd, 3),
            "files": [],
        }

        if errmsg:
            msg += errmsg + "\n"
            jmsg["error"] = errmsg
            errmsg = "ERROR: " + errmsg

        for sz, sha_hex, sha_b64, ofn, lfn, ap in files:
            vsuf = ""
            if (self.can_read or self.can_upget) and "fk" in vfs.flags:
                alg = 2 if "fka" in vfs.flags else 1
                vsuf = "?k=" + self.gen_fk(
                    alg,
                    self.args.fk_salt,
                    ap,
                    sz,
                    0 if ANYWIN or not ap else bos.stat(ap).st_ino,
                )[: vfs.flags["fk"]]

            vpath = "{}/{}".format(upload_vpath, lfn).strip("/")
            rel_url = quotep(self.args.RS + vpath) + vsuf
            msg += 'sha512: {} // {} // {} bytes // <a href="/{}">{}</a> {}\n'.format(
                sha_hex[:56],
                sha_b64,
                sz,
                rel_url,
                html_escape(ofn, crlf=True),
                vsuf,
            )
            # truncated SHA-512 prevents length extension attacks;
            # using SHA-512/224, optionally SHA-512/256 = :64
            jpart = {
                "url": "{}://{}/{}".format(
                    "https" if self.is_https else "http",
                    self.host,
                    rel_url,
                ),
                "sha512": sha_hex[:56],
                "sha_b64": sha_b64,
                "sz": sz,
                "fn": lfn,
                "fn_orig": ofn,
                "path": rel_url,
            }
            jmsg["files"].append(jpart)

        vspd = self._spd(sz_total, False)
        self.log("{} {}".format(vspd, msg))

        suf = ""
        if not nullwrite and self.args.write_uplog:
            try:
                log_fn = "up.{:.6f}.txt".format(t0)
                with open(log_fn, "wb") as f:
                    ft = "{}:{}".format(self.ip, self.addr[1])
                    ft = "{}\n{}\n{}\n".format(ft, msg.rstrip(), errmsg)
                    f.write(ft.encode("utf-8"))
            except Exception as ex:
                suf = "\nfailed to write the upload report: {}".format(ex)

        sc = 400 if errmsg else 201
        if want_url:
            msg = "\n".join([x["url"] for x in jmsg["files"]])
            if errmsg:
                msg += "\n" + errmsg

            self.reply(msg.encode("utf-8", "replace"), status=sc)
        elif "j" in self.uparam:
            jtxt = json.dumps(jmsg, indent=2, sort_keys=True).encode("utf-8", "replace")
            self.reply(jtxt, mime="application/json", status=sc)
        else:
            self.redirect(
                self.vpath,
                msg=msg + suf,
                flavor="return to",
                click=False,
                status=sc,
            )

        if errmsg:
            return False

        self.parser.drop()
        return True

    def handle_text_upload(self) -> bool:
        assert self.parser
        try:
            cli_lastmod3 = int(self.parser.require("lastmod", 16))
        except:
            raise Pebkac(400, "could not read lastmod from request")

        nullwrite = self.args.nw
        vfs, rem = self.asrv.vfs.get(self.vpath, self.uname, True, True)
        self._assert_safe_rem(rem)

        clen = int(self.headers.get("content-length", -1))
        if clen == -1:
            raise Pebkac(411)

        rp, fn = vsplit(rem)
        fp = vfs.canonical(rp)
        lim = vfs.get_dbv(rem)[0].lim
        if lim:
            fp, rp = lim.all(self.ip, rp, clen, vfs.realpath, fp, self.conn.hsrv.broker)
            bos.makedirs(fp)

        fp = os.path.join(fp, fn)
        rem = "{}/{}".format(rp, fn).strip("/")

        if not rem.endswith(".md") and not self.can_delete:
            raise Pebkac(400, "only markdown pls")

        if nullwrite:
            response = json.dumps({"ok": True, "lastmod": 0})
            self.log(response)
            # TODO reply should parser.drop()
            self.parser.drop()
            self.reply(response.encode("utf-8"))
            return True

        srv_lastmod = -1.0
        srv_lastmod3 = -1
        try:
            st = bos.stat(fp)
            srv_lastmod = st.st_mtime
            srv_lastmod3 = int(srv_lastmod * 1000)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise

        # if file exists, chekc that timestamp matches the client's
        if srv_lastmod >= 0:
            same_lastmod = cli_lastmod3 in [-1, srv_lastmod3]
            if not same_lastmod:
                # some filesystems/transports limit precision to 1sec, hopefully floored
                same_lastmod = (
                    srv_lastmod == int(cli_lastmod3 / 1000)
                    and cli_lastmod3 > srv_lastmod3
                    and cli_lastmod3 - srv_lastmod3 < 1000
                )

            if not same_lastmod:
                response = json.dumps(
                    {
                        "ok": False,
                        "lastmod": srv_lastmod3,
                        "now": int(time.time() * 1000),
                    }
                )
                self.log(
                    "{} - {} = {}".format(
                        srv_lastmod3, cli_lastmod3, srv_lastmod3 - cli_lastmod3
                    )
                )
                self.log(response)
                self.parser.drop()
                self.reply(response.encode("utf-8"))
                return True

            mdir, mfile = os.path.split(fp)
            fname, fext = mfile.rsplit(".", 1) if "." in mfile else (mfile, "md")
            mfile2 = "{}.{:.3f}.{}".format(fname, srv_lastmod, fext)
            try:
                dp = os.path.join(mdir, ".hist")
                bos.mkdir(dp)
                hidedir(dp)
            except:
                pass
            wrename(self.log, fp, os.path.join(mdir, ".hist", mfile2), vfs.flags)

        assert self.parser.gen
        p_field, _, p_data = next(self.parser.gen)
        if p_field != "body":
            raise Pebkac(400, "expected body, got {}".format(p_field))

        xbu = vfs.flags.get("xbu")
        if xbu:
            if not runhook(
                self.log,
                xbu,
                fp,
                self.vpath,
                self.host,
                self.uname,
                time.time(),
                0,
                self.ip,
                time.time(),
                "",
            ):
                t = "save blocked by xbu server config"
                self.log(t, 1)
                raise Pebkac(403, t)

        if bos.path.exists(fp):
            wunlink(self.log, fp, vfs.flags)

        with open(fsenc(fp), "wb", self.args.iobuf) as f:
            sz, sha512, _ = hashcopy(p_data, f, self.args.s_wr_slp)

        if lim:
            lim.nup(self.ip)
            lim.bup(self.ip, sz)
            try:
                lim.chk_sz(sz)
                lim.chk_vsz(self.conn.hsrv.broker, vfs.realpath, sz)
            except:
                wunlink(self.log, fp, vfs.flags)
                raise

        new_lastmod = bos.stat(fp).st_mtime
        new_lastmod3 = int(new_lastmod * 1000)
        sha512 = sha512[:56]

        xau = vfs.flags.get("xau")
        if xau and not runhook(
            self.log,
            xau,
            fp,
            self.vpath,
            self.host,
            self.uname,
            new_lastmod,
            sz,
            self.ip,
            new_lastmod,
            "",
        ):
            t = "save blocked by xau server config"
            self.log(t, 1)
            wunlink(self.log, fp, vfs.flags)
            raise Pebkac(403, t)

        vfs, rem = vfs.get_dbv(rem)
        self.conn.hsrv.broker.say(
            "up2k.hash_file",
            vfs.realpath,
            vfs.vpath,
            vfs.flags,
            vsplit(rem)[0],
            fn,
            self.ip,
            new_lastmod,
            self.uname,
            True,
        )

        response = json.dumps(
            {"ok": True, "lastmod": new_lastmod3, "size": sz, "sha512": sha512}
        )
        self.log(response)
        self.parser.drop()
        self.reply(response.encode("utf-8"))
        return True

    def _chk_lastmod(self, file_ts: int) -> tuple[str, bool]:
        file_lastmod = formatdate(file_ts, usegmt=True)
        cli_lastmod = self.headers.get("if-modified-since")
        if cli_lastmod:
            try:
                # some browser append "; length=573"
                cli_lastmod = cli_lastmod.split(";")[0].strip()
                cli_dt = parsedate(cli_lastmod)
                assert cli_dt
                cli_ts = calendar.timegm(cli_dt)
                return file_lastmod, int(file_ts) > int(cli_ts)
            except Exception as ex:
                self.log(
                    "lastmod {}\nremote: [{}]\n local: [{}]".format(
                        repr(ex), cli_lastmod, file_lastmod
                    )
                )
                return file_lastmod, file_lastmod != cli_lastmod

        return file_lastmod, True

    def _use_dirkey(self, ap: str = "") -> bool:
        if self.can_read or not self.can_get:
            return False

        if self.vn.flags.get("dky"):
            return True

        req = self.uparam.get("k") or ""
        if not req:
            return False

        dk_len = self.vn.flags.get("dk")
        if not dk_len:
            return False

        ap = ap or self.vn.canonical(self.rem)
        zs = self.gen_fk(2, self.args.dk_salt, ap, 0, 0)[:dk_len]
        if req == zs:
            return True

        t = "wrong dirkey, want %s, got %s\n  vp: %s\n  ap: %s"
        self.log(t % (zs, req, self.req, ap), 6)
        return False

    def _expand(self, txt: str, phs: list[str]) -> str:
        for ph in phs:
            if ph.startswith("hdr."):
                sv = str(self.headers.get(ph[4:], ""))
            elif ph.startswith("self."):
                sv = str(getattr(self, ph[5:], ""))
            elif ph.startswith("cfg."):
                sv = str(getattr(self.args, ph[4:], ""))
            elif ph.startswith("vf."):
                sv = str(self.vn.flags.get(ph[3:]) or "")
            elif ph == "srv.itime":
                sv = str(int(time.time()))
            elif ph == "srv.htime":
                sv = datetime.now(UTC).strftime("%Y-%m-%d, %H:%M:%S")
            else:
                self.log("unknown placeholder in server config: [%s]" % (ph), 3)
                continue

            sv = self.conn.hsrv.ptn_hsafe.sub("_", sv)
            txt = txt.replace("{{%s}}" % (ph,), sv)

        return txt

    def tx_file(self, req_path: str, ptop: Optional[str] = None) -> bool:
        status = 200
        logmsg = "{:4} {} ".format("", self.req)
        logtail = ""

        if ptop is not None:
            try:
                dp, fn = os.path.split(req_path)
                tnam = fn + ".PARTIAL"
                if self.args.dotpart:
                    tnam = "." + tnam
                ap_data = os.path.join(dp, tnam)
                st_data = bos.stat(ap_data)
                if not st_data.st_size:
                    raise Exception("partial is empty")
                x = self.conn.hsrv.broker.ask("up2k.find_job_by_ap", ptop, req_path)
                job = json.loads(x.get())
                if not job:
                    raise Exception("not found in registry")
                self.pipes.set(req_path, job)
            except Exception as ex:
                self.log("will not pipe [%s]; %s" % (ap_data, ex), 6)
                ptop = None

        #
        # if request is for foo.js, check if we have foo.js.gz

        file_ts = 0.0
        editions: dict[str, tuple[str, int]] = {}
        for ext in ("", ".gz"):
            if ptop is not None:
                sz = job["size"]
                file_ts = job["lmod"]
                editions["plain"] = (ap_data, sz)
                break

            try:
                fs_path = req_path + ext
                st = bos.stat(fs_path)
                if stat.S_ISDIR(st.st_mode):
                    continue

                if stat.S_ISBLK(st.st_mode):
                    fd = bos.open(fs_path, os.O_RDONLY)
                    try:
                        sz = os.lseek(fd, 0, os.SEEK_END)
                    finally:
                        os.close(fd)
                else:
                    sz = st.st_size

                file_ts = max(file_ts, st.st_mtime)
                editions[ext or "plain"] = (fs_path, sz)
            except:
                pass
            if not self.vpath.startswith(".cpr/"):
                break

        if not editions:
            return self.tx_404()

        #
        # if-modified

        file_lastmod, do_send = self._chk_lastmod(int(file_ts))
        self.out_headers["Last-Modified"] = file_lastmod
        if not do_send:
            status = 304

        if self.can_write:
            self.out_headers["X-Lastmod3"] = str(int(file_ts * 1000))

        #
        # Accept-Encoding and UA decides which edition to send

        decompress = False
        supported_editions = [
            x.strip()
            for x in self.headers.get("accept-encoding", "").lower().split(",")
        ]
        if ".gz" in editions:
            is_compressed = True
            selected_edition = ".gz"
            fs_path, file_sz = editions[".gz"]
            if "gzip" not in supported_editions:
                decompress = True
            else:
                if re.match(r"MSIE [4-6]\.", self.ua) and " SV1" not in self.ua:
                    decompress = True

            if not decompress:
                self.out_headers["Content-Encoding"] = "gzip"
        else:
            is_compressed = False
            selected_edition = "plain"

        fs_path, file_sz = editions[selected_edition]
        logmsg += "{} ".format(selected_edition.lstrip("."))

        #
        # partial

        lower = 0
        upper = file_sz
        hrange = self.headers.get("range")

        # let's not support 206 with compression
        # and multirange / multipart is also not-impl (mostly because calculating contentlength is a pain)
        if do_send and not is_compressed and hrange and file_sz and "," not in hrange:
            try:
                if not hrange.lower().startswith("bytes"):
                    raise Exception()

                a, b = hrange.split("=", 1)[1].split("-")

                if a.strip():
                    lower = int(a.strip())
                else:
                    lower = 0

                if b.strip():
                    upper = int(b.strip()) + 1
                else:
                    upper = file_sz

                if upper > file_sz:
                    upper = file_sz

                if lower < 0 or lower >= upper:
                    raise Exception()

            except:
                err = "invalid range ({}), size={}".format(hrange, file_sz)
                self.loud_reply(
                    err,
                    status=416,
                    headers={"Content-Range": "bytes */{}".format(file_sz)},
                )
                return True

            status = 206
            self.out_headers["Content-Range"] = "bytes {}-{}/{}".format(
                lower, upper - 1, file_sz
            )

            logtail += " [\033[36m{}-{}\033[0m]".format(lower, upper)

        use_sendfile = False
        if decompress:
            open_func: Any = gzip.open
            open_args: list[Any] = [fsenc(fs_path), "rb"]
            # Content-Length := original file size
            upper = gzip_orig_sz(fs_path)
        else:
            open_func = open
            open_args = [fsenc(fs_path), "rb", self.args.iobuf]
            use_sendfile = (
                # fmt: off
                not self.tls
                and not self.args.no_sendfile
                and (BITNESS > 32 or file_sz < 0x7fffFFFF)
                # fmt: on
            )

        #
        # send reply

        if is_compressed:
            self.out_headers["Cache-Control"] = "max-age=604869"
        else:
            self.permit_caching()

        if "txt" in self.uparam:
            mime = "text/plain; charset={}".format(self.uparam["txt"] or "utf-8")
        elif "mime" in self.uparam:
            mime = str(self.uparam.get("mime"))
        else:
            mime = guess_mime(req_path)

        if "nohtml" in self.vn.flags and "html" in mime:
            mime = "text/plain; charset=utf-8"

        self.out_headers["Accept-Ranges"] = "bytes"
        logmsg += unicode(status) + logtail

        if self.mode == "HEAD" or not do_send:
            if self.do_log:
                self.log(logmsg)

            self.send_headers(length=upper - lower, status=status, mime=mime)
            return True

        if ptop is not None:
            return self.tx_pipe(
                ptop, req_path, ap_data, job, lower, upper, status, mime, logmsg
            )

        ret = True
        with open_func(*open_args) as f:
            self.send_headers(length=upper - lower, status=status, mime=mime)

            sendfun = sendfile_kern if use_sendfile else sendfile_py
            remains = sendfun(
                self.log, lower, upper, f, self.s, self.args.s_wr_sz, self.args.s_wr_slp
            )

        if remains > 0:
            logmsg += " \033[31m" + unicode(upper - remains) + "\033[0m"
            ret = False

        spd = self._spd((upper - lower) - remains)
        if self.do_log:
            self.log("{},  {}".format(logmsg, spd))

        return ret

    def tx_pipe(
        self,
        ptop: str,
        req_path: str,
        ap_data: str,
        job: dict[str, Any],
        lower: int,
        upper: int,
        status: int,
        mime: str,
        logmsg: str,
    ) -> bool:
        M = 1048576
        self.send_headers(length=upper - lower, status=status, mime=mime)
        wr_slp = self.args.s_wr_slp
        wr_sz = self.args.s_wr_sz
        file_size = job["size"]
        chunk_size = up2k_chunksize(file_size)
        num_need = -1
        data_end = 0
        remains = upper - lower
        broken = False
        spins = 0
        tier = 0
        tiers = ["uncapped", "reduced speed", "one byte per sec"]

        while lower < upper and not broken:
            with self.u2mutex:
                job = self.pipes.get(req_path)
                if not job:
                    x = self.conn.hsrv.broker.ask("up2k.find_job_by_ap", ptop, req_path)
                    job = json.loads(x.get())
                    if job:
                        self.pipes.set(req_path, job)

            if not job:
                t = "pipe: OK, upload has finished; yeeting remainder"
                self.log(t, 2)
                data_end = file_size
                break

            if num_need != len(job["need"]) and data_end - lower < 8 * M:
                num_need = len(job["need"])
                data_end = 0
                for cid in job["hash"]:
                    if cid in job["need"]:
                        break
                    data_end += chunk_size
                t = "pipe: can stream %.2f MiB; requested range is %.2f to %.2f"
                self.log(t % (data_end / M, lower / M, upper / M), 6)
                with self.u2mutex:
                    if data_end > self.u2fh.aps.get(ap_data, data_end):
                        try:
                            fhs = self.u2fh.cache[ap_data].all_fhs
                            for fh in fhs:
                                fh.flush()
                            self.u2fh.aps[ap_data] = data_end
                            self.log("pipe: flushed %d up2k-FDs" % (len(fhs),))
                        except Exception as ex:
                            self.log("pipe: u2fh flush failed: %r" % (ex,))

            if lower >= data_end:
                if data_end:
                    t = "pipe: uploader is too slow; aborting download at %.2f MiB"
                    self.log(t % (data_end / M))
                    raise Pebkac(416, "uploader is too slow")

                raise Pebkac(416, "no data available yet; please retry in a bit")

            slack = data_end - lower
            if slack >= 8 * M:
                ntier = 0
                winsz = M
                bufsz = wr_sz
                slp = wr_slp
            else:
                winsz = max(40, int(M * (slack / (12 * M))))
                base_rate = M if not wr_slp else wr_sz / wr_slp
                if winsz > base_rate:
                    ntier = 0
                    bufsz = wr_sz
                    slp = wr_slp
                elif winsz > 300:
                    ntier = 1
                    bufsz = winsz // 5
                    slp = 0.2
                else:
                    ntier = 2
                    bufsz = winsz = slp = 1

            if tier != ntier:
                tier = ntier
                self.log("moved to tier %d (%s)" % (tier, tiers[tier]))

            try:
                with open(ap_data, "rb", self.args.iobuf) as f:
                    f.seek(lower)
                    page = f.read(min(winsz, data_end - lower, upper - lower))
                if not page:
                    raise Exception("got 0 bytes (EOF?)")
            except Exception as ex:
                self.log("pipe: read failed at %.2f MiB: %s" % (lower / M, ex), 3)
                with self.u2mutex:
                    self.pipes.c.pop(req_path, None)
                spins += 1
                if spins > 3:
                    raise Pebkac(500, "file became unreadable")
                time.sleep(2)
                continue

            spins = 0
            pofs = 0
            while pofs < len(page):
                if slp:
                    time.sleep(slp)

                try:
                    buf = page[pofs : pofs + bufsz]
                    self.s.sendall(buf)
                    zi = len(buf)
                    remains -= zi
                    lower += zi
                    pofs += zi
                except:
                    broken = True
                    break

        if lower < upper and not broken:
            with open(req_path, "rb") as f:
                remains = sendfile_py(self.log, lower, upper, f, self.s, wr_sz, wr_slp)

        spd = self._spd((upper - lower) - remains)
        if self.do_log:
            self.log("{},  {}".format(logmsg, spd))

        return not broken

    def tx_zip(
        self,
        fmt: str,
        uarg: str,
        vpath: str,
        vn: VFS,
        rem: str,
        items: list[str],
    ) -> bool:
        if self.args.no_zip:
            raise Pebkac(400, "not enabled")

        logmsg = "{:4} {} ".format("", self.req)
        self.keepalive = False

        cancmp = not self.args.no_tarcmp

        if fmt == "tar":
            packer: Type[StreamArc] = StreamTar
            if cancmp and "gz" in uarg:
                mime = "application/gzip"
                ext = "tar.gz"
            elif cancmp and "bz2" in uarg:
                mime = "application/x-bzip"
                ext = "tar.bz2"
            elif cancmp and "xz" in uarg:
                mime = "application/x-xz"
                ext = "tar.xz"
            else:
                mime = "application/x-tar"
                ext = "tar"
        else:
            mime = "application/zip"
            packer = StreamZip
            ext = "zip"

        fn = items[0] if items and items[0] else self.vpath
        if fn:
            fn = fn.rstrip("/").split("/")[-1]
        else:
            fn = self.host.split(":")[0]

        safe = (string.ascii_letters + string.digits).replace("%", "")
        afn = "".join([x if x in safe.replace('"', "") else "_" for x in fn])
        bascii = unicode(safe).encode("utf-8")
        zb = fn.encode("utf-8", "xmlcharrefreplace")
        if not PY2:
            zbl = [
                chr(x).encode("utf-8")
                if x in bascii
                else "%{:02x}".format(x).encode("ascii")
                for x in zb
            ]
        else:
            zbl = [unicode(x) if x in bascii else "%{:02x}".format(ord(x)) for x in zb]

        ufn = b"".join(zbl).decode("ascii")

        cdis = "attachment; filename=\"{}.{}\"; filename*=UTF-8''{}.{}"
        cdis = cdis.format(afn, ext, ufn, ext)
        self.log(cdis)
        self.send_headers(None, mime=mime, headers={"Content-Disposition": cdis})

        fgen = vn.zipgen(
            vpath, rem, set(items), self.uname, False, not self.args.no_scandir
        )
        # for f in fgen: print(repr({k: f[k] for k in ["vp", "ap"]}))
        cfmt = ""
        if self.thumbcli and not self.args.no_bacode:
            for zs in ("opus", "mp3", "w", "j"):
                if zs in self.ouparam or uarg == zs:
                    cfmt = zs

            if cfmt:
                self.log("transcoding to [{}]".format(cfmt))
                fgen = gfilter(fgen, self.thumbcli, self.uname, vpath, cfmt)

        bgen = packer(
            self.log,
            self.args,
            fgen,
            utf8="utf" in uarg,
            pre_crc="crc" in uarg,
            cmp=uarg if cancmp or uarg == "pax" else "",
        )
        bsent = 0
        for buf in bgen.gen():
            if not buf:
                break

            try:
                self.s.sendall(buf)
                bsent += len(buf)
            except:
                logmsg += " \033[31m" + unicode(bsent) + "\033[0m"
                bgen.stop()
                break

        spd = self._spd(bsent)
        self.log("{},  {}".format(logmsg, spd))
        return True

    def tx_ico(self, ext: str, exact: bool = False) -> bool:
        self.permit_caching()
        if ext.endswith("/"):
            ext = "folder"
            exact = True

        bad = re.compile(r"[](){}/ []|^[0-9_-]*$")
        n = ext.split(".")[::-1]
        if not exact:
            n = n[:-1]

        ext = ""
        for v in n:
            if len(v) > 7 or bad.search(v):
                break

            ext = "{}.{}".format(v, ext)

        ext = ext.rstrip(".") or "unk"
        if len(ext) > 11:
            ext = "~" + ext[-9:]

        return self.tx_svg(ext, exact)

    def tx_svg(self, txt: str, small: bool = False) -> bool:
        # chrome cannot handle more than ~2000 unique SVGs
        # so url-param "raster" returns a png/webp instead
        # (useragent-sniffing kinshi due to caching proxies)
        mime, ico = self.ico.get(txt, not small, "raster" in self.uparam)

        lm = formatdate(self.E.t0, usegmt=True)
        self.reply(ico, mime=mime, headers={"Last-Modified": lm})
        return True

    def tx_md(self, vn: VFS, fs_path: str) -> bool:
        logmsg = "     %s @%s " % (self.req, self.uname)

        if not self.can_write:
            if "edit" in self.uparam or "edit2" in self.uparam:
                return self.tx_404(True)

        tpl = "mde" if "edit2" in self.uparam else "md"
        html_path = os.path.join(self.E.mod, "web", "{}.html".format(tpl))
        template = self.j2j(tpl)

        st = bos.stat(fs_path)
        ts_md = st.st_mtime

        st = bos.stat(html_path)
        ts_html = st.st_mtime

        max_sz = 1024 * self.args.txt_max
        sz_md = 0
        lead = b""
        fullfile = b""
        for buf in yieldfile(fs_path, self.args.iobuf):
            if sz_md < max_sz:
                fullfile += buf
            else:
                fullfile = b""

            if not sz_md and b"\n" in buf[:2]:
                lead = buf[: buf.find(b"\n") + 1]
                sz_md += len(lead)

            sz_md += len(buf)
            for c, v in [(b"&", 4), (b"<", 3), (b">", 3)]:
                sz_md += (len(buf) - len(buf.replace(c, b""))) * v

        if (
            fullfile
            and "exp" in vn.flags
            and "edit" not in self.uparam
            and "edit2" not in self.uparam
            and vn.flags.get("exp_md")
        ):
            fulltxt = fullfile.decode("utf-8", "replace")
            fulltxt = self._expand(fulltxt, vn.flags.get("exp_md") or [])
            fullfile = fulltxt.encode("utf-8", "replace")

        if fullfile:
            fullfile = html_bescape(fullfile)
            sz_md = len(lead) + len(fullfile)

        file_ts = int(max(ts_md, ts_html, self.E.t0))
        file_lastmod, do_send = self._chk_lastmod(file_ts)
        self.out_headers["Last-Modified"] = file_lastmod
        self.out_headers.update(NO_CACHE)
        status = 200 if do_send else 304

        arg_base = "?"
        if "k" in self.uparam:
            arg_base = "?k={}&".format(self.uparam["k"])

        boundary = "\roll\tide"
        targs = {
            "r": self.args.SR if self.is_vproxied else "",
            "ts": self.conn.hsrv.cachebuster(),
            "edit": "edit" in self.uparam,
            "title": html_escape(self.vpath, crlf=True),
            "lastmod": int(ts_md * 1000),
            "lang": self.args.lang,
            "favico": self.args.favico,
            "have_emp": self.args.emp,
            "md_chk_rate": self.args.mcr,
            "md": boundary,
            "arg_base": arg_base,
        }

        zfv = self.vn.flags.get("html_head")
        if zfv:
            targs["this"] = self
            self._build_html_head(zfv, targs)

        targs["html_head"] = self.html_head
        zs = template.render(**targs).encode("utf-8", "replace")
        html = zs.split(boundary.encode("utf-8"))
        if len(html) != 2:
            raise Exception("boundary appears in " + html_path)

        self.send_headers(sz_md + len(html[0]) + len(html[1]), status)

        logmsg += unicode(status)
        if self.mode == "HEAD" or not do_send:
            if self.do_log:
                self.log(logmsg)

            return True

        try:
            self.s.sendall(html[0] + lead)
            if fullfile:
                self.s.sendall(fullfile)
            else:
                for buf in yieldfile(fs_path, self.args.iobuf):
                    self.s.sendall(html_bescape(buf))

            self.s.sendall(html[1])

        except:
            self.log(logmsg + " \033[31md/c\033[0m")
            return False

        if self.do_log:
            self.log(logmsg + " " + unicode(len(html)))

        return True

    def tx_svcs(self) -> bool:
        aname = re.sub("[^0-9a-zA-Z]+", "", self.args.vname) or "a"
        ep = self.host
        host = ep.split(":")[0]
        hport = ep[ep.find(":") :] if ":" in ep else ""
        rip = (
            host
            if self.args.rclone_mdns or not self.args.zm
            else self.conn.hsrv.nm.map(self.ip) or host
        )
        # safer than html_escape/quotep since this avoids both XSS and shell-stuff
        pw = re.sub(r"[<>&$?`\"']", "_", self.pw or "pw")
        vp = re.sub(r"[<>&$?`\"']", "_", self.uparam["hc"] or "").lstrip("/")
        pw = pw.replace(" ", "%20")
        vp = vp.replace(" ", "%20")
        html = self.j2s(
            "svcs",
            args=self.args,
            accs=bool(self.asrv.acct),
            s="s" if self.is_https else "",
            rip=rip,
            ep=ep,
            vp=vp,
            rvp=vjoin(self.args.R, vp),
            host=host,
            hport=hport,
            aname=aname,
            pw=pw,
        )
        self.reply(html.encode("utf-8"))
        return True

    def tx_mounts(self) -> bool:
        suf = self.urlq({}, ["h"])
        rvol, wvol, avol = [
            [("/" + x).rstrip("/") + "/" for x in y]
            for y in [self.rvol, self.wvol, self.avol]
        ]

        if self.avol and not self.args.no_rescan:
            x = self.conn.hsrv.broker.ask("up2k.get_state")
            vs = json.loads(x.get())
            vstate = {("/" + k).rstrip("/") + "/": v for k, v in vs["volstate"].items()}
        else:
            vstate = {}
            vs = {
                "scanning": None,
                "hashq": None,
                "tagq": None,
                "mtpq": None,
                "dbwt": None,
            }

        fmt = self.uparam.get("ls", "")
        if not fmt and (self.ua.startswith("curl/") or self.ua.startswith("fetch")):
            fmt = "v"

        if fmt in ["v", "t", "txt"]:
            if self.uname == "*":
                txt = "howdy stranger (you're not logged in)"
            else:
                txt = "welcome back {}".format(self.uname)

            if vstate:
                txt += "\nstatus:"
                for k in ["scanning", "hashq", "tagq", "mtpq", "dbwt"]:
                    txt += " {}({})".format(k, vs[k])

            if rvol:
                txt += "\nyou can browse:"
                for v in rvol:
                    txt += "\n  " + v

            if wvol:
                txt += "\nyou can upload to:"
                for v in wvol:
                    txt += "\n  " + v

            zb = txt.encode("utf-8", "replace") + b"\n"
            self.reply(zb, mime="text/plain; charset=utf-8")
            return True

        html = self.j2s(
            "splash",
            this=self,
            qvpath=quotep(self.vpaths) + self.ourlq(),
            rvol=rvol,
            wvol=wvol,
            avol=avol,
            vstate=vstate,
            scanning=vs["scanning"],
            hashq=vs["hashq"],
            tagq=vs["tagq"],
            mtpq=vs["mtpq"],
            dbwt=vs["dbwt"],
            url_suf=suf,
            k304=self.k304(),
            k304vis=self.args.k304 > 0,
            ver=S_VERSION if self.args.ver else "",
            ahttps="" if self.is_https else "https://" + self.host + self.req,
        )
        self.reply(html.encode("utf-8"))
        return True

    def set_k304(self) -> bool:
        v = self.uparam["k304"].lower()
        if v in "yn":
            dur = 86400 * 299
        else:
            dur = 0
            v = "x"

        ck = gencookie("k304", v, self.args.R, False, dur)
        self.out_headerlist.append(("Set-Cookie", ck))
        self.redirect("", "?h#cc")
        return True

    def setck(self) -> bool:
        k, v = self.uparam["setck"].split("=", 1)
        t = 0 if v == "" else 86400 * 299
        ck = gencookie(k, v, self.args.R, False, t)
        self.out_headerlist.append(("Set-Cookie", ck))
        self.reply(b"o7\n")
        return True

    def set_cfg_reset(self) -> bool:
        for k in ("k304", "js", "idxh", "dots", "cppwd", "cppws"):
            cookie = gencookie(k, "x", self.args.R, False)
            self.out_headerlist.append(("Set-Cookie", cookie))

        self.redirect("", "?h#cc")
        return True

    def tx_404(self, is_403: bool = False) -> bool:
        rc = 404
        if self.args.vague_403:
            t = '<h1 id="n">404 not found &nbsp;┐( ´ -`)┌</h1><p id="o">or maybe you don\'t have access -- try logging in or <a href="{}/?h">go home</a></p>'
            pt = "404 not found  ┐( ´ -`)┌   (or maybe you don't have access -- try logging in)"
        elif is_403:
            t = '<h1 id="p">403 forbiddena &nbsp;~┻━┻</h1><p id="q">you\'ll have to log in or <a href="{}/?h">go home</a></p>'
            pt = "403 forbiddena ~┻━┻   (you'll have to log in)"
            rc = 403
        else:
            t = '<h1 id="n">404 not found &nbsp;┐( ´ -`)┌</h1><p><a id="r" href="{}/?h">go home</a></p>'
            pt = "404 not found  ┐( ´ -`)┌"

        if self.ua.startswith("curl/") or self.ua.startswith("fetch"):
            pt = "# acct: %s\n%s\n" % (self.uname, pt)
            self.reply(pt.encode("utf-8"), status=rc)
            return True

        if "th" in self.ouparam:
            return self.tx_svg("e" + pt[:3])

        t = t.format(self.args.SR)
        qv = quotep(self.vpaths) + self.ourlq()
        html = self.j2s("splash", this=self, qvpath=qv, msg=t)
        self.reply(html.encode("utf-8"), status=rc)
        return True

    def on40x(self, mods: list[str], vn: VFS, rem: str) -> str:
        for mpath in mods:
            try:
                mod = loadpy(mpath, self.args.hot_handlers)
            except Exception as ex:
                self.log("import failed: {!r}".format(ex))
                continue

            ret = mod.main(self, vn, rem)
            if ret:
                return ret.lower()

        return ""  # unhandled / fallthrough

    def scanvol(self) -> bool:
        if not self.can_admin:
            raise Pebkac(403, "not allowed for user " + self.uname)

        if self.args.no_rescan:
            raise Pebkac(403, "the rescan feature is disabled in server config")

        vn, _ = self.asrv.vfs.get(self.vpath, self.uname, True, True)

        args = [self.asrv.vfs.all_vols, [vn.vpath], False, True]

        x = self.conn.hsrv.broker.ask("up2k.rescan", *args)
        err = x.get()
        if not err:
            self.redirect("", "?h")
            return True

        raise Pebkac(500, err)

    def handle_reload(self) -> bool:
        act = self.uparam.get("reload")
        if act != "cfg":
            raise Pebkac(400, "only config files ('cfg') can be reloaded rn")

        if not self.avol:
            raise Pebkac(403, "not allowed for user " + self.uname)

        if self.args.no_reload:
            raise Pebkac(403, "the reload feature is disabled in server config")

        x = self.conn.hsrv.broker.ask("reload")
        return self.redirect("", "?h", x.get(), "return to", False)

    def tx_stack(self) -> bool:
        if not self.avol and not [x for x in self.wvol if x in self.rvol]:
            raise Pebkac(403, "not allowed for user " + self.uname)

        if self.args.no_stack:
            raise Pebkac(403, "the stackdump feature is disabled in server config")

        ret = "<pre>{}\n{}".format(time.time(), html_escape(alltrace()))
        self.reply(ret.encode("utf-8"))
        return True

    def tx_tree(self) -> bool:
        top = self.uparam["tree"] or ""
        dst = self.vpath
        if top in [".", ".."]:
            top = undot(self.vpath + "/" + top)

        if top == dst:
            dst = ""
        elif top:
            if not dst.startswith(top + "/"):
                raise Pebkac(422, "arg funk")

            dst = dst[len(top) + 1 :]

        ret = self.gen_tree(top, dst, self.uparam.get("k", ""))
        if self.is_vproxied:
            parents = self.args.R.split("/")
            for parent in reversed(parents):
                ret = {"k%s" % (parent,): ret, "a": []}

        zs = json.dumps(ret)
        self.reply(zs.encode("utf-8"), mime="application/json")
        return True

    def gen_tree(self, top: str, target: str, dk: str) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        excl = None
        if target:
            excl, target = (target.split("/", 1) + [""])[:2]
            sub = self.gen_tree("/".join([top, excl]).strip("/"), target, dk)
            ret["k" + quotep(excl)] = sub

        vfs = self.asrv.vfs
        dk_sz = False
        if dk:
            vn, rem = vfs.get(top, self.uname, False, False)
            if vn.flags.get("dks") and self._use_dirkey(vn.canonical(rem)):
                dk_sz = vn.flags.get("dk")

        dots = False
        fsroot = ""
        try:
            vn, rem = vfs.get(top, self.uname, not dk_sz, False)
            fsroot, vfs_ls, vfs_virt = vn.ls(
                rem,
                self.uname,
                not self.args.no_scandir,
                [[True, False], [False, True]],
            )
            dots = self.uname in vn.axs.udot
            dk_sz = vn.flags.get("dk")
        except:
            dk_sz = None
            vfs_ls = []
            vfs_virt = {}
            for v in self.rvol:
                d1, d2 = v.rsplit("/", 1) if "/" in v else ["", v]
                if d1 == top:
                    vfs_virt[d2] = vfs  # typechk, value never read

        dirs = [x[0] for x in vfs_ls if stat.S_ISDIR(x[1].st_mode)]

        if not dots or "dots" not in self.uparam:
            dirs = exclude_dotfiles(dirs)

        dirs = [quotep(x) for x in dirs if x != excl]

        if dk_sz and fsroot:
            kdirs = []
            for dn in dirs:
                ap = os.path.join(fsroot, dn)
                zs = self.gen_fk(2, self.args.dk_salt, ap, 0, 0)[:dk_sz]
                kdirs.append(dn + "?k=" + zs)
            dirs = kdirs

        for x in vfs_virt:
            if x != excl:
                try:
                    dvn, drem = vfs.get(vjoin(top, x), self.uname, True, False)
                    bos.stat(dvn.canonical(drem, False))
                except:
                    x += "\n"
                dirs.append(x)

        ret["a"] = dirs
        return ret

    def tx_ups(self) -> bool:
        idx = self.conn.get_u2idx()
        if not idx or not hasattr(idx, "p_end"):
            raise Pebkac(500, "sqlite3 is not available on the server; cannot unpost")

        filt = self.uparam.get("filter") or ""
        lm = "ups [{}]".format(filt)
        self.log(lm)

        ret: list[dict[str, Any]] = []
        t0 = time.time()
        lim = time.time() - self.args.unpost
        fk_vols = {
            vol: (vol.flags["fk"], 2 if "fka" in vol.flags else 1)
            for vp, vol in self.asrv.vfs.all_vols.items()
            if "fk" in vol.flags
            and (self.uname in vol.axs.uread or self.uname in vol.axs.upget)
        }

        x = self.conn.hsrv.broker.ask(
            "up2k.get_unfinished_by_user", self.uname, self.ip
        )
        uret = x.get()

        if not self.args.unpost:
            allvols = []
        else:
            allvols = list(self.asrv.vfs.all_vols.values())

        allvols = [x for x in allvols if "e2d" in x.flags]

        for vol in allvols:
            cur = idx.get_cur(vol)
            if not cur:
                continue

            nfk, fk_alg = fk_vols.get(vol) or (0, 0)

            q = "select sz, rd, fn, at from up where ip=? and at>?"
            for sz, rd, fn, at in cur.execute(q, (self.ip, lim)):
                vp = "/" + "/".join(x for x in [vol.vpath, rd, fn] if x)
                if filt and filt not in vp:
                    continue

                rv = {"vp": quotep(vp), "sz": sz, "at": at, "nfk": nfk}
                if nfk:
                    rv["ap"] = vol.canonical(vjoin(rd, fn))
                    rv["fk_alg"] = fk_alg

                ret.append(rv)
                if len(ret) > 3000:
                    ret.sort(key=lambda x: x["at"], reverse=True)  # type: ignore
                    ret = ret[:2000]

        ret.sort(key=lambda x: x["at"], reverse=True)  # type: ignore
        n = 0
        for rv in ret[:11000]:
            nfk = rv.pop("nfk")
            if not nfk:
                continue

            alg = rv.pop("fk_alg")
            ap = rv.pop("ap")
            try:
                st = bos.stat(ap)
            except:
                continue

            fk = self.gen_fk(
                alg, self.args.fk_salt, ap, st.st_size, 0 if ANYWIN else st.st_ino
            )
            rv["vp"] += "?k=" + fk[:nfk]

            n += 1
            if n > 2000:
                break

        ret = ret[:2000]

        if self.is_vproxied:
            for v in ret:
                v["vp"] = self.args.SR + v["vp"]

        if not allvols:
            ret = [{"kinshi": 1}]

        jtxt = '{"u":%s,"c":%s}' % (uret, json.dumps(ret, separators=(",\n", ": ")))
        zi = len(uret.split('\n"pd":')) - 1
        self.log("%s #%d+%d %.2fsec" % (lm, zi, len(ret), time.time() - t0))
        self.reply(jtxt.encode("utf-8", "replace"), mime="application/json")
        return True

    def handle_rm(self, req: list[str]) -> bool:
        if not req and not self.can_delete:
            raise Pebkac(403, "not allowed for user " + self.uname)

        if self.args.no_del:
            raise Pebkac(403, "the delete feature is disabled in server config")

        if not req:
            req = [self.vpath]
        elif self.is_vproxied:
            req = [x[len(self.args.SR) :] for x in req]

        unpost = "unpost" in self.uparam
        nlim = int(self.uparam.get("lim") or 0)
        lim = [nlim, nlim] if nlim else []

        x = self.conn.hsrv.broker.ask(
            "up2k.handle_rm", self.uname, self.ip, req, lim, False, unpost
        )
        self.loud_reply(x.get())
        return True

    def handle_mv(self) -> bool:
        # full path of new loc (incl filename)
        dst = self.uparam.get("move")

        if self.is_vproxied and dst and dst.startswith(self.args.SR):
            dst = dst[len(self.args.RS) :]

        if not dst:
            raise Pebkac(400, "need dst vpath")

        return self._mv(self.vpath, dst.lstrip("/"))

    def _mv(self, vsrc: str, vdst: str) -> bool:
        if not self.can_move:
            raise Pebkac(403, "not allowed for user " + self.uname)

        if self.args.no_mv:
            raise Pebkac(403, "the rename/move feature is disabled in server config")

        x = self.conn.hsrv.broker.ask("up2k.handle_mv", self.uname, vsrc, vdst)
        self.loud_reply(x.get(), status=201)
        return True

    def tx_ls(self, ls: dict[str, Any]) -> bool:
        dirs = ls["dirs"]
        files = ls["files"]
        arg = self.uparam["ls"]
        if arg in ["v", "t", "txt"]:
            try:
                biggest = max(ls["files"] + ls["dirs"], key=itemgetter("sz"))["sz"]
            except:
                biggest = 0

            if arg == "v":
                fmt = "\033[0;7;36m{{}}{{:>{}}}\033[0m {{}}"
                nfmt = "{}"
                biggest = 0
                f2 = "".join(
                    "{}{{}}".format(x)
                    for x in [
                        "\033[7m",
                        "\033[27m",
                        "",
                        "\033[0;1m",
                        "\033[0;36m",
                        "\033[0m",
                    ]
                )
                ctab = {"B": 6, "K": 5, "M": 1, "G": 3}
                for lst in [dirs, files]:
                    for x in lst:
                        a = x["dt"].replace("-", " ").replace(":", " ").split(" ")
                        x["dt"] = f2.format(*list(a))
                        sz = humansize(x["sz"], True)
                        x["sz"] = "\033[0;3{}m {:>5}".format(ctab.get(sz[-1:], 0), sz)
            else:
                fmt = "{{}}  {{:{},}}  {{}}"
                nfmt = "{:,}"

            for x in dirs:
                n = x["name"] + "/"
                if arg == "v":
                    n = "\033[94m" + n

                x["name"] = n

            fmt = fmt.format(len(nfmt.format(biggest)))
            retl = [
                "# {}: {}".format(x, ls[x])
                for x in ["acct", "perms", "srvinf"]
                if x in ls
            ]
            retl += [
                fmt.format(x["dt"], x["sz"], x["name"])
                for y in [dirs, files]
                for x in y
            ]
            ret = "\n".join(retl)
            mime = "text/plain; charset=utf-8"
        else:
            [x.pop(k) for k in ["name", "dt"] for y in [dirs, files] for x in y]

            ret = json.dumps(ls)
            mime = "application/json"

        ret += "\n\033[0m" if arg == "v" else "\n"
        self.reply(ret.encode("utf-8", "replace"), mime=mime)
        return True

    def tx_browser(self) -> bool:
        vpath = ""
        vpnodes = [["", "/"]]
        if self.vpath:
            for node in self.vpath.split("/"):
                if not vpath:
                    vpath = node
                else:
                    vpath += "/" + node

                vpnodes.append([quotep(vpath) + "/", html_escape(node, crlf=True)])

        vn = self.vn
        rem = self.rem
        abspath = vn.dcanonical(rem)
        dbv, vrem = vn.get_dbv(rem)

        try:
            st = bos.stat(abspath)
        except:
            if "on404" not in vn.flags:
                return self.tx_404()

            ret = self.on40x(vn.flags["on404"], vn, rem)
            if ret == "true":
                return True
            elif ret == "false":
                return False
            elif ret == "retry":
                try:
                    st = bos.stat(abspath)
                except:
                    return self.tx_404()
            else:
                return self.tx_404()

        if rem.startswith(".hist/up2k.") or (
            rem.endswith("/dir.txt") and rem.startswith(".hist/th/")
        ):
            raise Pebkac(403)

        e2d = "e2d" in vn.flags
        e2t = "e2t" in vn.flags

        add_og = "og" in vn.flags
        if add_og:
            if "th" in self.uparam or "raw" in self.uparam:
                og_ua = add_og = False
            elif self.args.og_ua:
                og_ua = add_og = self.args.og_ua.search(self.ua)
            else:
                og_ua = False
                add_og = True
            og_fn = ""

        if "b" in self.uparam:
            self.out_headers["X-Robots-Tag"] = "noindex, nofollow"

        is_dir = stat.S_ISDIR(st.st_mode)
        is_dk = False
        fk_pass = False
        icur = None
        if (e2t or e2d) and (is_dir or add_og):
            idx = self.conn.get_u2idx()
            if idx and hasattr(idx, "p_end"):
                icur = idx.get_cur(dbv)

        th_fmt = self.uparam.get("th")
        if self.can_read or (
            self.can_get and (vn.flags.get("dk") or "fk" not in vn.flags)
        ):
            if th_fmt is not None:
                nothumb = "dthumb" in dbv.flags
                if is_dir:
                    vrem = vrem.rstrip("/")
                    if nothumb:
                        pass
                    elif icur and vrem:
                        q = "select fn from cv where rd=? and dn=?"
                        crd, cdn = vrem.rsplit("/", 1) if "/" in vrem else ("", vrem)
                        # no mojibake support:
                        try:
                            cfn = icur.execute(q, (crd, cdn)).fetchone()
                            if cfn:
                                fn = cfn[0]
                                fp = os.path.join(abspath, fn)
                                if bos.path.exists(fp):
                                    vrem = "{}/{}".format(vrem, fn).strip("/")
                                    is_dir = False
                        except:
                            pass
                    else:
                        for fn in self.args.th_covers:
                            fp = os.path.join(abspath, fn)
                            if bos.path.exists(fp):
                                vrem = "{}/{}".format(vrem, fn).strip("/")
                                is_dir = False
                                break

                    if is_dir:
                        return self.tx_svg("folder")

                thp = None
                if self.thumbcli and not nothumb:
                    thp = self.thumbcli.get(dbv, vrem, int(st.st_mtime), th_fmt)

                if thp:
                    return self.tx_file(thp)

                if th_fmt == "p":
                    raise Pebkac(404)

                return self.tx_ico(rem)

        elif self.can_write and th_fmt is not None:
            return self.tx_svg("upload\nonly")

        if not self.can_read and self.can_get and self.avn:
            axs = self.avn.axs
            if self.uname not in axs.uhtml:
                pass
            elif is_dir:
                for fn in ("index.htm", "index.html"):
                    ap2 = os.path.join(abspath, fn)
                    try:
                        st2 = bos.stat(ap2)
                    except:
                        continue

                    # might as well be extra careful
                    if not stat.S_ISREG(st2.st_mode):
                        continue

                    if not self.trailing_slash:
                        return self.redirect(
                            self.vpath + "/", flavor="redirecting to", use302=True
                        )

                    fk_pass = True
                    is_dir = False
                    rem = vjoin(rem, fn)
                    vrem = vjoin(vrem, fn)
                    abspath = ap2
                    break
            elif self.vpath.rsplit("/", 1)[1] in ("index.htm", "index.html"):
                fk_pass = True

        if not is_dir and (self.can_read or self.can_get):
            if not self.can_read and not fk_pass and "fk" in vn.flags:
                alg = 2 if "fka" in vn.flags else 1
                correct = self.gen_fk(
                    alg,
                    self.args.fk_salt,
                    abspath,
                    st.st_size,
                    0 if ANYWIN else st.st_ino,
                )[: vn.flags["fk"]]
                got = self.uparam.get("k")
                if got != correct:
                    t = "wrong filekey, want %s, got %s\n  vp: %s\n  ap: %s"
                    self.log(t % (correct, got, self.req, abspath), 6)
                    return self.tx_404()

            if add_og:
                if og_ua or self.host not in self.headers.get("referer", ""):
                    self.vpath, og_fn = vsplit(self.vpath)
                    vpath = self.vpath
                    vn, rem = self.asrv.vfs.get(self.vpath, self.uname, False, False)
                    abspath = vn.dcanonical(rem)
                    dbv, vrem = vn.get_dbv(rem)
                    is_dir = stat.S_ISDIR(st.st_mode)
                    is_dk = True
                    vpnodes.pop()

            if (
                (abspath.endswith(".md") or self.can_delete)
                and "nohtml" not in vn.flags
                and (
                    "v" in self.uparam
                    or "edit" in self.uparam
                    or "edit2" in self.uparam
                )
            ):
                return self.tx_md(vn, abspath)

            if not add_og or not og_fn:
                return self.tx_file(
                    abspath, None if st.st_size or "nopipe" in vn.flags else vn.realpath
                )

        elif is_dir and not self.can_read:
            if self._use_dirkey(abspath):
                is_dk = True
            elif not self.can_write:
                return self.tx_404(True)

        srv_info = []

        try:
            if not self.args.nih:
                srv_info.append(self.args.name)
        except:
            self.log("#wow #whoa")

        if not self.args.nid:
            free, total = get_df(abspath)
            if total is not None:
                h1 = humansize(free or 0)
                h2 = humansize(total)
                srv_info.append("{} free of {}".format(h1, h2))
            elif free is not None:
                srv_info.append(humansize(free, True) + " free")

        srv_infot = "</span> // <span>".join(srv_info)

        perms = []
        if self.can_read or is_dk:
            perms.append("read")
        if self.can_write:
            perms.append("write")
        if self.can_move:
            perms.append("move")
        if self.can_delete:
            perms.append("delete")
        if self.can_get:
            perms.append("get")
        if self.can_upget:
            perms.append("upget")
        if self.can_admin:
            perms.append("admin")

        url_suf = self.urlq({}, ["k"])
        is_ls = "ls" in self.uparam
        is_js = self.args.force_js or self.cookies.get("js") == "y"

        if (
            not is_ls
            and not add_og
            and (self.ua.startswith("curl/") or self.ua.startswith("fetch"))
        ):
            self.uparam["ls"] = "v"
            is_ls = True

        tpl = "browser"
        if "b" in self.uparam:
            tpl = "browser2"
            is_js = False

        logues = ["", ""]
        if not self.args.no_logues:
            for n, fn in enumerate([".prologue.html", ".epilogue.html"]):
                fn = os.path.join(abspath, fn)
                if bos.path.exists(fn):
                    with open(fsenc(fn), "rb") as f:
                        logues[n] = f.read().decode("utf-8")
                    if "exp" in vn.flags:
                        logues[n] = self._expand(
                            logues[n], vn.flags.get("exp_lg") or []
                        )

        readme = ""
        if not self.args.no_readme and not logues[1]:
            for fn in ["README.md", "readme.md"]:
                fn = os.path.join(abspath, fn)
                if bos.path.isfile(fn):
                    with open(fsenc(fn), "rb") as f:
                        readme = f.read().decode("utf-8")
                        break
            if readme and "exp" in vn.flags:
                readme = self._expand(readme, vn.flags.get("exp_md") or [])

        vf = vn.flags
        unlist = vf.get("unlist", "")
        ls_ret = {
            "dirs": [],
            "files": [],
            "taglist": [],
            "srvinf": srv_infot,
            "acct": self.uname,
            "idx": e2d,
            "itag": e2t,
            "dsort": vf["sort"],
            "dcrop": vf["crop"],
            "dth3x": vf["th3x"],
            "u2ts": vf["u2ts"],
            "lifetime": vn.flags.get("lifetime") or 0,
            "frand": bool(vn.flags.get("rand")),
            "unlist": unlist,
            "perms": perms,
            "logues": logues,
            "readme": readme,
        }
        cgv = {
            "ls0": None,
            "acct": self.uname,
            "perms": perms,
            "u2ts": vf["u2ts"],
            "lifetime": ls_ret["lifetime"],
            "frand": bool(vn.flags.get("rand")),
            "def_hcols": [],
            "have_emp": self.args.emp,
            "have_up2k_idx": e2d,
            "have_acode": (not self.args.no_acode),
            "have_mv": (not self.args.no_mv),
            "have_del": (not self.args.no_del),
            "have_zip": (not self.args.no_zip),
            "have_unpost": int(self.args.unpost),
            "sb_md": "" if "no_sb_md" in vf else (vf.get("md_sbf") or "y"),
            "readme": readme,
            "dgrid": "grid" in vf,
            "dsort": vf["sort"],
            "dcrop": vf["crop"],
            "dth3x": vf["th3x"],
            "themes": self.args.themes,
            "turbolvl": self.args.turbo,
            "u2j": self.args.u2j,
            "idxh": int(self.args.ih),
            "u2sort": self.args.u2sort,
        }
        j2a = {
            "cgv": cgv,
            "vpnodes": vpnodes,
            "files": [],
            "ls0": None,
            "taglist": [],
            "have_tags_idx": e2t,
            "have_b_u": (self.can_write and self.uparam.get("b") == "u"),
            "sb_lg": "" if "no_sb_lg" in vf else (vf.get("lg_sbf") or "y"),
            "url_suf": url_suf,
            "logues": logues,
            "title": html_escape("%s %s" % (self.args.bname, self.vpath), crlf=True),
            "srv_info": srv_infot,
            "dtheme": self.args.theme,
        }

        if self.args.js_browser:
            zs = self.args.js_browser
            zs += "&" if "?" in zs else "?"
            j2a["js"] = zs

        if self.args.css_browser:
            zs = self.args.css_browser
            zs += "&" if "?" in zs else "?"
            j2a["css"] = zs

        if not self.conn.hsrv.prism:
            j2a["no_prism"] = True

        if not self.can_read and not is_dk:
            if is_ls:
                return self.tx_ls(ls_ret)

            if not stat.S_ISDIR(st.st_mode):
                return self.tx_404(True)

            if "zip" in self.uparam or "tar" in self.uparam:
                raise Pebkac(403)

            html = self.j2s(tpl, **j2a)
            self.reply(html.encode("utf-8", "replace"))
            return True

        for k in ["zip", "tar"]:
            v = self.uparam.get(k)
            if v is not None and (not add_og or not og_fn):
                return self.tx_zip(k, v, self.vpath, vn, rem, [])

        fsroot, vfs_ls, vfs_virt = vn.ls(
            rem,
            self.uname,
            not self.args.no_scandir,
            [[True, False], [False, True]],
            lstat="lt" in self.uparam,
        )
        stats = {k: v for k, v in vfs_ls}
        ls_names = [x[0] for x in vfs_ls]
        ls_names.extend(list(vfs_virt.keys()))

        if add_og and og_fn and not self.can_read:
            ls_names = [og_fn]
            is_js = True

        # check for old versions of files,
        # [num-backups, most-recent, hist-path]
        hist: dict[str, tuple[int, float, str]] = {}
        histdir = os.path.join(fsroot, ".hist")
        ptn = re.compile(r"(.*)\.([0-9]+\.[0-9]{3})(\.[^\.]+)$")
        try:
            for hfn in bos.listdir(histdir):
                m = ptn.match(hfn)
                if not m:
                    continue

                fn = m.group(1) + m.group(3)
                n, ts, _ = hist.get(fn, (0, 0, ""))
                hist[fn] = (n + 1, max(ts, float(m.group(2))), hfn)
        except:
            pass

        # show dotfiles if permitted and requested
        if not self.can_dot or (
            "dots" not in self.uparam and (is_ls or "dots" not in self.cookies)
        ):
            ls_names = exclude_dotfiles(ls_names)

        add_dk = vf.get("dk")
        add_fk = vf.get("fk")
        fk_alg = 2 if "fka" in vf else 1
        if add_dk:
            if vf.get("dky"):
                add_dk = False
            else:
                zs = self.gen_fk(2, self.args.dk_salt, abspath, 0, 0)[:add_dk]
                ls_ret["dk"] = cgv["dk"] = zs

        dirs = []
        files = []
        for fn in ls_names:
            base = ""
            href = fn
            if not is_ls and not is_js and not self.trailing_slash and vpath:
                base = "/" + vpath + "/"
                href = base + fn

            if fn in vfs_virt:
                fspath = vfs_virt[fn].realpath
            else:
                fspath = fsroot + "/" + fn

            try:
                linf = stats.get(fn) or bos.lstat(fspath)
                inf = bos.stat(fspath) if stat.S_ISLNK(linf.st_mode) else linf
            except:
                self.log("broken symlink: {}".format(repr(fspath)))
                continue

            is_dir = stat.S_ISDIR(inf.st_mode)
            if is_dir:
                href += "/"
                if self.args.no_zip:
                    margin = "DIR"
                elif add_dk:
                    zs = absreal(fspath)
                    margin = '<a href="%s?k=%s&zip" rel="nofollow">zip</a>' % (
                        quotep(href),
                        self.gen_fk(2, self.args.dk_salt, zs, 0, 0)[:add_dk],
                    )
                else:
                    margin = '<a href="%s?zip" rel="nofollow">zip</a>' % (quotep(href),)
            elif fn in hist:
                margin = '<a href="%s.hist/%s">#%s</a>' % (
                    base,
                    html_escape(hist[fn][2], quot=True, crlf=True),
                    hist[fn][0],
                )
            else:
                margin = "-"

            sz = inf.st_size
            zd = datetime.fromtimestamp(linf.st_mtime, UTC)
            dt = "%04d-%02d-%02d %02d:%02d:%02d" % (
                zd.year,
                zd.month,
                zd.day,
                zd.hour,
                zd.minute,
                zd.second,
            )

            try:
                ext = "---" if is_dir else fn.rsplit(".", 1)[1]
                if len(ext) > 16:
                    ext = ext[:16]
            except:
                ext = "%"

            if add_fk and not is_dir:
                href = "%s?k=%s" % (
                    quotep(href),
                    self.gen_fk(
                        fk_alg,
                        self.args.fk_salt,
                        fspath,
                        sz,
                        0 if ANYWIN else inf.st_ino,
                    )[:add_fk],
                )
            elif add_dk and is_dir:
                href = "%s?k=%s" % (
                    quotep(href),
                    self.gen_fk(2, self.args.dk_salt, fspath, 0, 0)[:add_dk],
                )
            else:
                href = quotep(href)

            item = {
                "lead": margin,
                "href": href,
                "name": fn,
                "sz": sz,
                "ext": ext,
                "dt": dt,
                "ts": int(linf.st_mtime),
            }
            if is_dir:
                dirs.append(item)
            else:
                files.append(item)
                item["rd"] = rem

        if is_dk and not vf.get("dks"):
            dirs = []

        if (
            self.cookies.get("idxh") == "y"
            and "ls" not in self.uparam
            and "v" not in self.uparam
        ):
            idx_html = set(["index.htm", "index.html"])
            for item in files:
                if item["name"] in idx_html:
                    # do full resolve in case of shadowed file
                    vp = vjoin(self.vpath.split("?")[0], item["name"])
                    vn, rem = self.asrv.vfs.get(vp, self.uname, True, False)
                    ap = vn.canonical(rem)
                    return self.tx_file(ap)  # is no-cache

        mte = vn.flags.get("mte", {})
        add_up_at = ".up_at" in mte
        is_admin = self.can_admin
        tagset: set[str] = set()
        for fe in files:
            fn = fe["name"]
            rd = fe["rd"]
            del fe["rd"]
            if not icur:
                continue

            if vn != dbv:
                _, rd = vn.get_dbv(rd)

            erd_efn = (rd, fn)
            q = "select mt.k, mt.v from up inner join mt on mt.w = substr(up.w,1,16) where up.rd = ? and up.fn = ? and +mt.k != 'x'"
            try:
                r = icur.execute(q, erd_efn)
            except Exception as ex:
                if "database is locked" in str(ex):
                    break

                try:
                    erd_efn = s3enc(idx.mem_cur, rd, fn)
                    r = icur.execute(q, erd_efn)
                except:
                    t = "tag read error, {}/{}\n{}"
                    self.log(t.format(rd, fn, min_ex()))
                    break

            tags = {k: v for k, v in r}

            if is_admin:
                q = "select ip, at from up where rd=? and fn=?"
                try:
                    zs1, zs2 = icur.execute(q, erd_efn).fetchone()
                    if zs1:
                        tags["up_ip"] = zs1
                    if zs2:
                        tags[".up_at"] = zs2
                except:
                    pass
            elif add_up_at:
                q = "select at from up where rd=? and fn=?"
                try:
                    (zs1,) = icur.execute(q, erd_efn).fetchone()
                    if zs1:
                        tags[".up_at"] = zs1
                except:
                    pass

            _ = [tagset.add(k) for k in tags]
            fe["tags"] = tags

        if icur:
            lmte = list(mte)
            if self.can_admin:
                lmte.extend(("up_ip", ".up_at"))

            taglist = [k for k in lmte if k in tagset]
            for fe in dirs:
                fe["tags"] = ODict()
        else:
            taglist = list(tagset)

        if is_ls:
            ls_ret["dirs"] = dirs
            ls_ret["files"] = files
            ls_ret["taglist"] = taglist
            return self.tx_ls(ls_ret)

        doc = self.uparam.get("doc") if self.can_read else None
        if doc:
            j2a["docname"] = doc
            doctxt = None
            if next((x for x in files if x["name"] == doc), None):
                docpath = os.path.join(abspath, doc)
                sz = bos.path.getsize(docpath)
                if sz < 1024 * self.args.txt_max:
                    with open(fsenc(docpath), "rb") as f:
                        doctxt = f.read().decode("utf-8", "replace")

                    if doc.lower().endswith(".md") and "exp" in vn.flags:
                        doctxt = self._expand(doctxt, vn.flags.get("exp_md") or [])
                else:
                    self.log("doc 2big: [{}]".format(doc), c=6)
                    doctxt = "( size of textfile exceeds serverside limit )"
            else:
                self.log("doc 404: [{}]".format(doc), c=6)
                doctxt = "( textfile not found )"

            if doctxt is not None:
                j2a["doc"] = doctxt

        for d in dirs:
            d["name"] += "/"

        dirs.sort(key=itemgetter("name"))

        if is_js:
            j2a["ls0"] = cgv["ls0"] = {
                "dirs": dirs,
                "files": files,
                "taglist": taglist,
                "unlist": unlist,
            }
            j2a["files"] = []
        else:
            j2a["files"] = dirs + files

        j2a["taglist"] = taglist
        j2a["txt_ext"] = self.args.textfiles.replace(",", " ")

        if "mth" in vn.flags:
            j2a["def_hcols"] = list(vn.flags["mth"])

        if add_og and "raw" not in self.uparam:
            j2a["this"] = self
            cgv["og_fn"] = og_fn
            if og_fn and vn.flags.get("og_tpl"):
                tpl = vn.flags["og_tpl"]
                if "EXT" in tpl:
                    zs = og_fn.split(".")[-1].lower()
                    tpl2 = tpl.replace("EXT", zs)
                    if os.path.exists(tpl2):
                        tpl = tpl2
                with self.conn.hsrv.mutex:
                    if tpl not in self.conn.hsrv.j2:
                        tdir, tname = os.path.split(tpl)
                        j2env = jinja2.Environment()
                        j2env.loader = jinja2.FileSystemLoader(tdir)
                        self.conn.hsrv.j2[tpl] = j2env.get_template(tname)
            thumb = ""
            is_pic = is_vid = is_au = False
            covernames = self.args.th_coversd
            for fn in ls_names:
                if fn.lower() in covernames:
                    thumb = fn
                    break
            if og_fn:
                ext = og_fn.split(".")[-1].lower()
                if ext in self.thumbcli.thumbable:
                    is_pic = (
                        ext in self.thumbcli.fmt_pil
                        or ext in self.thumbcli.fmt_vips
                        or ext in self.thumbcli.fmt_ffi
                    )
                    is_vid = ext in self.thumbcli.fmt_ffv
                    is_au = ext in self.thumbcli.fmt_ffa
                    if not thumb or not is_au:
                        thumb = og_fn
                file = next((x for x in files if x["name"] == og_fn), None)
            else:
                file = None

            url_base = "%s://%s/%s" % (
                "https" if self.is_https else "http",
                self.host,
                self.args.RS + quotep(vpath),
            )
            j2a["og_is_pic"] = is_pic
            j2a["og_is_vid"] = is_vid
            j2a["og_is_au"] = is_au
            if thumb:
                fmt = vn.flags.get("og_th", "j")
                th_base = ujoin(url_base, quotep(thumb))
                query = "th=%s&cache" % (fmt,)
                query = ub64enc(query.encode("utf-8")).decode("utf-8")
                # discord looks at file extension, not content-type...
                query += "/a.jpg" if "j" in fmt else "/a.webp"
                j2a["og_thumb"] = "%s/.uqe/%s" % (th_base, query)

            j2a["og_fn"] = og_fn
            j2a["og_file"] = file
            if og_fn:
                og_fn_q = quotep(og_fn)
                query = ub64enc(b"raw").decode("utf-8")
                if "." in og_fn:
                    query += "/a.%s" % (og_fn.split(".")[-1])

                j2a["og_url"] = ujoin(url_base, og_fn_q)
                j2a["og_raw"] = j2a["og_url"] + "/.uqe/" + query
            else:
                j2a["og_url"] = j2a["og_raw"] = url_base

            if not vn.flags.get("og_no_head"):
                ogh = {"twitter:card": "summary"}

                title = str(vn.flags.get("og_title") or "")

                if thumb:
                    ogh["og:image"] = j2a["og_thumb"]

                zso = vn.flags.get("og_desc") or ""
                if zso != "-":
                    ogh["og:description"] = str(zso)

                zs = vn.flags.get("og_site") or self.args.name
                if zs not in ("", "-"):
                    ogh["og:site_name"] = zs

                tagmap = {}
                if is_au:
                    title = str(vn.flags.get("og_title_a") or "")
                    ogh["og:type"] = "music.song"
                    ogh["og:audio"] = j2a["og_raw"]
                    tagmap = {
                        "artist": "og:music:musician",
                        "album": "og:music:album",
                        ".dur": "og:music:duration",
                    }
                elif is_vid:
                    title = str(vn.flags.get("og_title_v") or "")
                    ogh["og:type"] = "video.other"
                    ogh["og:video"] = j2a["og_raw"]
                    tagmap = {
                        "title": "og:title",
                        ".dur": "og:video:duration",
                    }
                elif is_pic:
                    title = str(vn.flags.get("og_title_i") or "")
                    ogh["og:type"] = "website"
                    ogh["twitter:card"] = "photo"
                    ogh["twitter:image:src"] = ogh["og:image"] = j2a["og_raw"]

                try:
                    for k, v in file["tags"].items():
                        zs = "{{ %s }}" % (k,)
                        title = title.replace(zs, str(v))
                except:
                    pass
                title = re.sub(r"\{\{ [^}]+ \}\}", "", title)
                while title.startswith(" - "):
                    title = title[3:]
                while title.endswith(" - "):
                    title = title[:3]

                if vn.flags.get("og_s_title") or not title:
                    title = str(vn.flags.get("og_title") or "")

                for tag, hname in tagmap.items():
                    try:
                        v = file["tags"][tag]
                        if not v:
                            continue
                        ogh[hname] = int(v) if tag == ".dur" else v
                    except:
                        pass

                ogh["og:title"] = title

                zs = '\t<meta property="%s" content="%s">'
                oghs = [zs % (k, html_escape(str(v))) for k, v in ogh.items()]
                zs = self.html_head + "\n%s\n" % ("\n".join(oghs),)
                self.html_head = zs.replace("\n\n", "\n")

        html = self.j2s(tpl, **j2a)
        self.reply(html.encode("utf-8", "replace"))
        return True

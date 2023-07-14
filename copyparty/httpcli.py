# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse  # typechk
import base64
import calendar
import copy
import errno
import gzip
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
from .sutil import StreamArc  # typechk
from .szip import StreamZip
from .util import (
    HTTPCODE,
    META_NOBOTS,
    MultipartParser,
    Pebkac,
    UnrecvEOF,
    alltrace,
    absreal,
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
    sendfile_kern,
    sendfile_py,
    undot,
    unescape_cookie,
    unquote,
    unquotep,
    vjoin,
    vol_san,
    vsplit,
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
        self.mutex = conn.mutex  # mypy404
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
        self.http_ver = " "
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
        self.uname = " "
        self.pw = " "
        self.rvol = [" "]
        self.wvol = [" "]
        self.mvol = [" "]
        self.dvol = [" "]
        self.gvol = [" "]
        self.upvol = [" "]
        self.do_log = True
        self.can_read = False
        self.can_write = False
        self.can_move = False
        self.can_delete = False
        self.can_get = False
        self.can_upget = False
        self.can_admin = False
        # post
        self.parser: Optional[MultipartParser] = None
        # end placeholders

        self.bufsz = 1024 * 32
        self.hint = ""
        self.trailing_slash = True
        self.out_headerlist: list[tuple[str, str]] = []
        self.out_headers = {
            "Vary": "Origin, PW, Cookie",
            "Cache-Control": "no-store, max-age=0",
        }
        h = self.args.html_head
        if self.args.no_robots:
            h = META_NOBOTS + (("\n" + h) if h else "")
            self.out_headers["X-Robots-Tag"] = "noindex, nofollow"
        self.html_head = h

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
        return "{}\033[7m {} \033[27m{}".format(a, self.asrv.iacct[b], c)

    def _check_nonfatal(self, ex: Pebkac, post: bool) -> bool:
        if post:
            return ex.code < 300

        return ex.code < 400 or ex.code in [404, 429]

    def _assert_safe_rem(self, rem: str) -> None:
        # sanity check to prevent any disasters
        if rem.startswith("/") or rem.startswith("../") or "/../" in rem:
            raise Exception("that was close")

    def _gen_fk(self, salt: str, fspath: str, fsize: int, inode: int) -> str:
        return gen_filekey_dbg(salt, fspath, fsize, inode, self.log, self.args.log_fk)

    def j2s(self, name: str, **ka: Any) -> str:
        tpl = self.conn.hsrv.j2[name]
        ka["r"] = self.args.SR if self.is_vproxied else ""
        ka["ts"] = self.conn.hsrv.cachebuster()
        ka["lang"] = self.args.lang
        ka["favico"] = self.args.favico
        ka["svcname"] = self.args.doctitle
        ka["html_head"] = self.html_head
        return tpl.render(**ka)  # type: ignore

    def j2j(self, name: str) -> jinja2.Template:
        return self.conn.hsrv.j2[name]

    def run(self) -> bool:
        """returns true if connection can be reused"""
        self.keepalive = False
        self.is_https = False
        self.headers = {}
        self.hint = ""

        if self.is_banned():
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
                msg = " ]\n#[ ".join(headerlines)
                raise Pebkac(400, "bad headers:\n#[ " + msg + " ]")

        except Pebkac as ex:
            self.mode = "GET"
            self.req = "[junk]"
            self.http_ver = "HTTP/1.1"
            # self.log("pebkac at httpcli.run #1: " + repr(ex))
            self.keepalive = False
            h = {"WWW-Authenticate": 'Basic realm="a"'} if ex.code == 401 else {}
            try:
                self.loud_reply(unicode(ex), status=ex.code, headers=h, volsan=True)
                return self.keepalive
            except:
                return False

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

        n = self.args.rproxy
        if n:
            zso = self.headers.get("x-forwarded-for")
            if zso and self.conn.addr[0] in ["127.0.0.1", "::1"]:
                if n > 0:
                    n -= 1

                zsl = zso.split(",")
                try:
                    self.ip = zsl[n].strip()
                except:
                    self.ip = zsl[0].strip()
                    t = "rproxy={} oob x-fwd {}"
                    self.log(t.format(self.args.rproxy, zso), c=3)

                self.log_src = self.conn.set_rproxy(self.ip)
                self.is_vproxied = bool(self.args.R)
                self.host = self.headers.get("x-forwarded-host") or self.host

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

        # split req into vpath + uparam
        uparam = {}
        if "?" not in self.req:
            self.trailing_slash = self.req.endswith("/")
            vpath = undot(self.req)
        else:
            vpath, arglist = self.req.split("?", 1)
            self.trailing_slash = vpath.endswith("/")
            vpath = undot(vpath)
            for k in arglist.split("&"):
                if "=" in k:
                    k, zs = k.split("=", 1)
                    uparam[k.lower()] = unquotep(zs.strip().replace("+", " "))
                else:
                    uparam[k.lower()] = ""

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
            raise Pebkac(400, "u wot m8")

        self.uparam = uparam
        self.cookies = cookies
        self.vpath = unquotep(vpath)  # not query, so + means +

        ok = "\x00" not in self.vpath
        if ANYWIN:
            ok = ok and not relchk(self.vpath)

        if not ok and (self.vpath != "*" or self.mode != "OPTIONS"):
            self.log("invalid relpath [{}]".format(self.vpath))
            return self.tx_404() and self.keepalive

        zso = self.headers.get("authorization")
        bauth = ""
        if zso:
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

        self.pw = uparam.get("pw") or self.headers.get("pw") or bauth or cookie_pw
        self.uname = self.asrv.iacct.get(self.asrv.ah.hash(self.pw)) or "*"
        self.rvol = self.asrv.vfs.aread[self.uname]
        self.wvol = self.asrv.vfs.awrite[self.uname]
        self.mvol = self.asrv.vfs.amove[self.uname]
        self.dvol = self.asrv.vfs.adel[self.uname]
        self.gvol = self.asrv.vfs.aget[self.uname]
        self.upvol = self.asrv.vfs.apget[self.uname]

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
        ) = (
            avn.can_access("", self.uname) if avn else [False] * 6
        )
        self.avn = avn
        self.vn = vn
        self.rem = rem

        self.s.settimeout(self.args.s_tbody or None)

        try:
            cors_k = self._cors()
            if self.mode in ("GET", "HEAD"):
                return self.handle_get() and self.keepalive
            if self.mode == "OPTIONS":
                return self.handle_options() and self.keepalive

            if not cors_k:
                origin = self.headers.get("origin", "<?>")
                self.log("cors-reject {} from {}".format(self.mode, origin), 3)
                raise Pebkac(403, "no surfing")

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
                post = self.mode in ["POST", "PUT"] or "content-length" in self.headers
                if not self._check_nonfatal(pex, post):
                    self.keepalive = False

                em = str(ex)
                msg = em if pex == ex else min_ex()
                if pex.code != 404 or self.do_log:
                    self.log(
                        "{}\033[0m, {}".format(msg, self.vpath),
                        6 if em.startswith("client d/c ") else 3,
                    )

                msg = "{}\r\nURL: {}\r\n".format(em, self.vpath)
                if self.hint:
                    msg += "hint: {}\r\n".format(self.hint)

                if "database is locked" in em:
                    self.conn.hsrv.broker.say("log_stacks")
                    msg += "hint: important info in the server log\r\n"

                zb = b"<pre>" + html_escape(msg).encode("utf-8", "replace")
                h = {"WWW-Authenticate": 'Basic realm="a"'} if pex.code == 401 else {}
                self.reply(zb, status=pex.code, headers=h, volsan=True)
                return self.keepalive
            except Pebkac:
                return False

    def dip(self) -> str:
        if self.args.plain_ip:
            return self.ip.replace(":", ".")
        else:
            return self.conn.iphash.s(self.ip)

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
        zb = b"HTTP/1.0 403 Forbidden\r\n\r\nthank you for playing"
        self.s.sendall(zb)
        return True

    def permit_caching(self) -> None:
        cache = self.uparam.get("cache")
        if cache is None:
            self.out_headers.update(NO_CACHE)
            return

        n = "604869" if cache == "i" else cache or "69"
        self.out_headers["Cache-Control"] = "max-age=" + n

    def k304(self) -> bool:
        k304 = self.cookies.get("k304")
        return k304 == "y" or ("; Trident/" in self.ua and not k304)

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
        if status == 404:
            g = self.conn.hsrv.g404
            if g.lim:
                bonk, ip = g.bonk(self.ip, self.vpath)
                if bonk:
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
                        "404",
                    ):
                        self.log("client banned: 404s", 1)
                        self.conn.hsrv.bans[ip] = bonk

        if volsan:
            vols = list(self.asrv.vfs.all_vols.values())
            body = vol_san(vols, body)

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
            "{}://{}".format(
                "https" if self.is_https else "http",
                self.host.lower().split(":")[0],
            )
        ]
        if re.sub(r"(:[0-9]{1,5})?/?$", "", origin) in good_origins:
            good_origin = True
            bad_hdrs = ("",)
        else:
            good_origin = False
            bad_hdrs = ("", "pw")

        # '*' blocks all credentials (cookies, http-auth);
        # exact-match for Origin is necessary to unlock those,
        # however yolo-requests (?pw=) are always allowed
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
                return self.conn.hsrv.ssdp.reply(self)

            if self.vpath.startswith(".cpr/dd/") and self.args.mpmc:
                if self.args.mpmc == ".":
                    raise Pebkac(404)

                loc = self.args.mpmc.rstrip("/") + self.vpath[self.vpath.rfind("/") :]
                h = {"Location": loc, "Cache-Control": "max-age=39"}
                self.reply(b"", 301, headers=h)
                return True

            path_base = os.path.join(self.E.mod, "web")
            static_path = absreal(os.path.join(path_base, self.vpath[5:]))
            if not static_path.startswith(path_base):
                t = "attempted path traversal [{}] => [{}]"
                self.log(t.format(self.vpath, static_path), 1)
                self.tx_404()
                return False

            return self.tx_file(static_path)

        if "cf_challenge" in self.uparam:
            self.reply(self.j2s("cf").encode("utf-8", "replace"))
            return True

        if not self.can_read and not self.can_write and not self.can_get:
            t = "@{} has no access to [{}]"
            self.log(t.format(self.uname, self.vpath))

            if "on403" in self.vn.flags:
                ret = self.on40x(self.vn.flags["on403"], self.vn, self.rem)
                if ret == "true":
                    return True
                elif ret == "false":
                    return False
                elif ret == "allow":
                    self.log("plugin override; access permitted")
                    self.can_read = self.can_write = self.can_move = True
                    self.can_delete = self.can_get = self.can_upget = True
                    self.can_admin = True
                else:
                    return self.tx_404(True)
            else:
                if self.vpath:
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
            self.log("inaccessible: [{}]".format(self.vpath))
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
                self.args.ed,
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
            if not self.args.ed:
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
        ptn = r"/\.(_|DS_Store|Spotlight-|fseventsd|Trashes|AppleDouble)|/__MACOS"
        if re.search(ptn, vp):
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

        buf = "{:x}\r\n".format(len(buf)).encode(enc) + buf
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
        if "chunked" in self.headers.get("transfer-encoding", "").lower():
            return read_socket_chunked(self.sr), -1

        remains = int(self.headers.get("content-length", -1))
        if remains == -1:
            self.keepalive = False
            return read_socket_unbounded(self.sr), remains
        else:
            return read_socket(self.sr, remains), remains

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
        open_a = ["wb", 512 * 1024]

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
                bos.unlink(path)

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
                bos.unlink(path)
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
                atomic_move(path, path2)
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
            os.unlink(path)
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
            vsuf = "?k=" + self.gen_fk(
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

    def bakflip(self, f: typing.BinaryIO, ofs: int, sz: int, sha: str) -> None:
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
                buf = f.read(min(nrem, 512 * 1024))
                if not buf:
                    break

                nrem -= len(buf)
                fo.write(buf)

        if nrem:
            self.log("bakflip truncated; {} remains".format(nrem), 1)
            atomic_move(fp, fp + ".trunc")
        else:
            self.log("bakflip ok", 2)

    def _spd(self, nbytes: int, add: bool = True) -> str:
        if add:
            self.conn.nbyte += nbytes

        spd1 = get_spd(nbytes, self.t0)
        spd2 = get_spd(self.conn.nbyte, self.conn.t0)
        return "%s %s n%s" % (spd1, spd2, self.conn.nreq)

    def handle_post_multipart(self) -> bool:
        self.parser = MultipartParser(self.log, self.sr, self.headers)
        self.parser.parse()

        act = self.parser.require("act", 64)

        if act == "login":
            return self.handle_login()

        if act == "mkdir":
            return self.handle_mkdir()

        if act == "new_md":
            # kinda silly but has the least side effects
            return self.handle_new_md()

        if act == "bput":
            return self.handle_plain_upload()

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

        vn, rem = self.asrv.vfs.get(self.vpath, self.uname, True, False)
        zs = self.parser.require("files", 1024 * 1024)
        if not zs:
            raise Pebkac(422, "need files list")

        items = zs.replace("\r", "").split("\n")
        items = [unquotep(x) for x in items if items]

        self.parser.drop()
        return self.tx_zip(k, v, "", vn, rem, items, self.args.ed)

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
            raise Pebkac(500, "sqlite3 is not available on the server; cannot search")

        vols = []
        seen = {}
        for vtop in self.rvol:
            vfs, _ = self.asrv.vfs.get(vtop, self.uname, True, False)
            vfs = vfs.dbv or vfs
            if vfs in seen:
                continue

            seen[vfs] = True
            vols.append((vfs.vpath, vfs.realpath, vfs.flags))

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
            hits = idx.fsearch(vols, body)
            msg: Any = repr(hits)
            taglist: list[str] = []
            trunc = False
        else:
            # search by query params
            q = body["q"]
            n = body.get("n", self.args.srch_hits)
            self.log("qj: {} |{}|".format(q, n))
            hits, taglist, trunc = idx.search(vols, q, n)
            msg = len(hits)

        idx.p_end = time.time()
        idx.p_dur = idx.p_end - t0
        self.log("q#: {} ({:.2f}s)".format(msg, idx.p_dur))

        order = []
        cfg = self.args.mte.split(",")
        for t in cfg:
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

            reader = read_socket(self.sr, remains)

            f = None
            fpool = not self.args.no_fpool and sprs
            if fpool:
                with self.mutex:
                    try:
                        f = self.u2fh.pop(path)
                    except:
                        pass

            f = f or open(fsenc(path), "rb+", 512 * 1024)

            try:
                f.seek(cstart[0])
                post_sz, _, sha_b64 = hashcopy(reader, f, self.args.s_wr_slp)

                if sha_b64 != chash:
                    try:
                        self.bakflip(f, cstart[0], post_sz, sha_b64)
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
                        bufsz = min(chunksize - ofs, 4 * 1024 * 1024)
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
                    with self.mutex:
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
            with self.mutex:
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
            dst += quotep(self.vpath)

        msg = self.get_pwd_cookie(pwd)
        html = self.j2s("msg", h1=msg, h2='<a href="' + dst + '">ack</a>', redir=dst)
        self.reply(html.encode("utf-8"))
        return True

    def get_pwd_cookie(self, pwd: str) -> str:
        if self.asrv.ah.hash(pwd) in self.asrv.iacct:
            msg = "login ok"
            dur = int(60 * 60 * self.args.logout)
        else:
            self.log("invalid password: {}".format(pwd), 3)
            g = self.conn.hsrv.gpwd
            if g.lim:
                bonk, ip = g.bonk(self.ip, pwd)
                if bonk:
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
                        "pw",
                    ):
                        self.log("client banned: invalid passwords", 1)
                        self.conn.hsrv.bans[ip] = bonk

            msg = "naw dude"
            pwd = "x"  # nosec
            dur = None

        if pwd == "x":
            # reset both plaintext and tls
            # (only affects active tls cookies when tls)
            for k in ("cppwd", "cppws") if self.is_https else ("cppwd",):
                ck = gencookie(k, pwd, self.args.R, False, dur)
                self.out_headerlist.append(("Set-Cookie", ck))
        else:
            k = "cppws" if self.is_https else "cppwd"
            ck = gencookie(k, pwd, self.args.R, self.is_https, dur)
            self.out_headerlist.append(("Set-Cookie", ck))

        return msg

    def handle_mkdir(self) -> bool:
        assert self.parser
        new_dir = self.parser.require("name", 512)
        self.parser.drop()

        sanitized = sanitize_fn(new_dir, "", [])
        return self._mkdir(vjoin(self.vpath, sanitized))

    def _mkdir(self, vpath: str, dav: bool = False) -> bool:
        nullwrite = self.args.nw
        vfs, rem = self.asrv.vfs.get(vpath, self.uname, False, True)
        self._assert_safe_rem(rem)
        fn = vfs.canonical(rem)

        if not nullwrite:
            fdir = os.path.dirname(fn)

            if not bos.path.isdir(fdir):
                raise Pebkac(409, "parent folder does not exist")

            if bos.path.isdir(fn):
                raise Pebkac(405, "that folder exists already")

            try:
                bos.mkdir(fn)
            except OSError as ex:
                if ex.errno == errno.EACCES:
                    raise Pebkac(500, "the server OS denied write-access")

                raise Pebkac(500, "mkdir failed:\n" + min_ex())
            except:
                raise Pebkac(500, min_ex())

        self.out_headers["X-New-Dir"] = quotep(vpath.split("/")[-1])

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

        if not new_file.endswith(".md"):
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

    def handle_plain_upload(self) -> bool:
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
        dip = self.dip()
        t0 = time.time()
        try:
            assert self.parser.gen
            for nfile, (p_field, p_file, p_data) in enumerate(self.parser.gen):
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

                    with ren_open(tnam, "wb", 512 * 1024, **open_args) as zfw:
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
                                bos.unlink(tabspath)
                                bos.unlink(abspath)
                            fname = os.devnull
                            raise

                    if not nullwrite:
                        atomic_move(tabspath, abspath)

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
                        os.unlink(abspath)
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
                vsuf = "?k=" + self.gen_fk(
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

        if not rem.endswith(".md"):
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
            mfile2 = "{}.{:.3f}.md".format(mfile[:-3], srv_lastmod)
            try:
                dp = os.path.join(mdir, ".hist")
                bos.mkdir(dp)
                hidedir(dp)
            except:
                pass
            bos.rename(fp, os.path.join(mdir, ".hist", mfile2))

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
            bos.unlink(fp)

        with open(fsenc(fp), "wb", 512 * 1024) as f:
            sz, sha512, _ = hashcopy(p_data, f, self.args.s_wr_slp)

        if lim:
            lim.nup(self.ip)
            lim.bup(self.ip, sz)
            try:
                lim.chk_sz(sz)
                lim.chk_vsz(self.conn.hsrv.broker, vfs.realpath, sz)
            except:
                bos.unlink(fp)
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
            os.unlink(fp)
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

    def tx_file(self, req_path: str) -> bool:
        status = 200
        logmsg = "{:4} {} ".format("", self.req)
        logtail = ""

        #
        # if request is for foo.js, check if we have foo.js.{gz,br}

        file_ts = 0
        editions: dict[str, tuple[str, int]] = {}
        for ext in ["", ".gz", ".br"]:
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

                file_ts = max(file_ts, int(st.st_mtime))
                editions[ext or "plain"] = (fs_path, sz)
            except:
                pass
            if not self.vpath.startswith(".cpr/"):
                break

        if not editions:
            return self.tx_404()

        #
        # if-modified

        file_lastmod, do_send = self._chk_lastmod(file_ts)
        self.out_headers["Last-Modified"] = file_lastmod
        if not do_send:
            status = 304

        #
        # Accept-Encoding and UA decides which edition to send

        decompress = False
        supported_editions = [
            x.strip()
            for x in self.headers.get("accept-encoding", "").lower().split(",")
        ]
        if ".br" in editions and "br" in supported_editions:
            is_compressed = True
            selected_edition = ".br"
            fs_path, file_sz = editions[".br"]
            self.out_headers["Content-Encoding"] = "br"
        elif ".gz" in editions:
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

        try:
            fs_path, file_sz = editions[selected_edition]
            logmsg += "{} ".format(selected_edition.lstrip("."))
        except:
            # client is old and we only have .br
            # (could make brotli a dep to fix this but it's not worth)
            raise Pebkac(404)

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
            # 512 kB is optimal for huge files, use 64k
            open_args = [fsenc(fs_path), "rb", 64 * 1024]
            use_sendfile = (
                not self.tls  #
                and not self.args.no_sendfile
                and hasattr(os, "sendfile")
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
        self.send_headers(length=upper - lower, status=status, mime=mime)

        logmsg += unicode(status) + logtail

        if self.mode == "HEAD" or not do_send:
            if self.do_log:
                self.log(logmsg)

            return True

        ret = True
        with open_func(*open_args) as f:
            sendfun = sendfile_kern if use_sendfile else sendfile_py
            remains = sendfun(
                self.log, lower, upper, f, self.s, self.args.s_wr_sz, self.args.s_wr_slp
            )

        if remains > 0:
            logmsg += " \033[31m" + unicode(upper - remains) + "\033[0m"
            self.keepalive = False

        spd = self._spd((upper - lower) - remains)
        if self.do_log:
            self.log("{},  {}".format(logmsg, spd))

        return ret

    def tx_zip(
        self,
        fmt: str,
        uarg: str,
        vpath: str,
        vn: VFS,
        rem: str,
        items: list[str],
        dots: bool,
    ) -> bool:
        if self.args.no_zip:
            raise Pebkac(400, "not enabled")

        logmsg = "{:4} {} ".format("", self.req)
        self.keepalive = False

        if fmt == "tar":
            mime = "application/x-tar"
            packer: Type[StreamArc] = StreamTar
        else:
            mime = "application/zip"
            packer = StreamZip

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
        cdis = cdis.format(afn, fmt, ufn, fmt)
        self.log(cdis)
        self.send_headers(None, mime=mime, headers={"Content-Disposition": cdis})

        fgen = vn.zipgen(
            vpath, rem, set(items), self.uname, dots, False, not self.args.no_scandir
        )
        # for f in fgen: print(repr({k: f[k] for k in ["vp", "ap"]}))
        bgen = packer(self.log, fgen, utf8="utf" in uarg, pre_crc="crc" in uarg)
        bsent = 0
        for buf in bgen.gen():
            if not buf:
                break

            try:
                self.s.sendall(buf)
                bsent += len(buf)
            except:
                logmsg += " \033[31m" + unicode(bsent) + "\033[0m"
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
            ext = "⋯" + ext[-9:]

        # chrome cannot handle more than ~2000 unique SVGs
        chrome = " rv:" not in self.ua
        mime, ico = self.ico.get(ext, not exact, chrome)

        lm = formatdate(self.E.t0, usegmt=True)
        self.reply(ico, mime=mime, headers={"Last-Modified": lm})
        return True

    def tx_md(self, fs_path: str) -> bool:
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

        sz_md = 0
        for buf in yieldfile(fs_path):
            sz_md += len(buf)
            for c, v in [(b"&", 4), (b"<", 3), (b">", 3)]:
                sz_md += (len(buf) - len(buf.replace(c, b""))) * v

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
            "svcname": self.args.doctitle,
            "html_head": self.html_head,
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
            self.s.sendall(html[0])
            for buf in yieldfile(fs_path):
                self.s.sendall(html_bescape(buf))

            self.s.sendall(html[1])

        except:
            self.log(logmsg + " \033[31md/c\033[0m")
            return False

        if self.do_log:
            self.log(logmsg + " " + unicode(len(html)))

        return True

    def tx_svcs(self) -> bool:
        aname = re.sub("[^0-9a-zA-Z]+", "", self.args.name) or "a"
        ep = self.host
        host = ep.split(":")[0]
        hport = ep[ep.find(":") :] if ":" in ep else ""
        rip = (
            host
            if self.args.rclone_mdns or not self.args.zm
            else self.conn.hsrv.nm.map(self.ip) or host
        )
        vp = (self.uparam["hc"] or "").lstrip("/")
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
            pw=self.pw or "pw",
        )
        self.reply(html.encode("utf-8"))
        return True

    def tx_mounts(self) -> bool:
        suf = self.urlq({}, ["h"])
        avol = [x for x in self.wvol if x in self.rvol]
        rvol, wvol, avol = [
            [("/" + x).rstrip("/") + "/" for x in y]
            for y in [self.rvol, self.wvol, avol]
        ]

        if avol and not self.args.no_rescan:
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
            qvpath=quotep(self.vpath),
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
            ver=S_VERSION if self.args.ver else "",
            ahttps="" if self.is_https else "https://" + self.host + self.req,
        )
        self.reply(html.encode("utf-8"))
        return True

    def set_k304(self) -> bool:
        ck = gencookie("k304", self.uparam["k304"], self.args.R, False, 86400 * 299)
        self.out_headerlist.append(("Set-Cookie", ck))
        self.redirect("", "?h#cc")
        return True

    def setck(self) -> bool:
        k, v = self.uparam["setck"].split("=", 1)
        t = None if v == "" else 86400 * 299
        ck = gencookie(k, v, self.args.R, False, t)
        self.out_headerlist.append(("Set-Cookie", ck))
        self.reply(b"o7\n")
        return True

    def set_cfg_reset(self) -> bool:
        for k in ("k304", "js", "idxh", "cppwd", "cppws"):
            cookie = gencookie(k, "x", self.args.R, False, None)
            self.out_headerlist.append(("Set-Cookie", cookie))

        self.redirect("", "?h#cc")
        return True

    def tx_404(self, is_403: bool = False) -> bool:
        rc = 404
        if self.args.vague_403:
            t = '<h1 id="n">404 not found &nbsp;┐( ´ -`)┌</h1><p id="o">or maybe you don\'t have access -- try logging in or <a href="{}/?h">go home</a></p>'
        elif is_403:
            t = '<h1 id="p">403 forbiddena &nbsp;~┻━┻</h1><p id="q">you\'ll have to log in or <a href="{}/?h">go home</a></p>'
            rc = 403
        else:
            t = '<h1 id="n">404 not found &nbsp;┐( ´ -`)┌</h1><p><a id="r" href="{}/?h">go home</a></p>'

        t = t.format(self.args.SR)
        html = self.j2s("splash", this=self, qvpath=quotep(self.vpath), msg=t)
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
        if not self.can_read or not self.can_write:
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

        if not [x for x in self.wvol if x in self.rvol]:
            raise Pebkac(403, "not allowed for user " + self.uname)

        if self.args.no_reload:
            raise Pebkac(403, "the reload feature is disabled in server config")

        x = self.conn.hsrv.broker.ask("reload")
        return self.redirect("", "?h", x.get(), "return to", False)

    def tx_stack(self) -> bool:
        if not [x for x in self.wvol if x in self.rvol]:
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
                raise Pebkac(400, "arg funk")

            dst = dst[len(top) + 1 :]

        ret = self.gen_tree(top, dst)
        if self.is_vproxied:
            parents = self.args.R.split("/")
            for parent in reversed(parents):
                ret = {"k%s" % (parent,): ret, "a": []}

        zs = json.dumps(ret)
        self.reply(zs.encode("utf-8"), mime="application/json")
        return True

    def gen_tree(self, top: str, target: str) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        excl = None
        if target:
            excl, target = (target.split("/", 1) + [""])[:2]
            sub = self.gen_tree("/".join([top, excl]).strip("/"), target)
            ret["k" + quotep(excl)] = sub

        try:
            vn, rem = self.asrv.vfs.get(top, self.uname, True, False)
            fsroot, vfs_ls, vfs_virt = vn.ls(
                rem,
                self.uname,
                not self.args.no_scandir,
                [[True, False], [False, True]],
            )
        except:
            vfs_ls = []
            vfs_virt = {}
            for v in self.rvol:
                d1, d2 = v.rsplit("/", 1) if "/" in v else ["", v]
                if d1 == top:
                    vfs_virt[d2] = self.asrv.vfs  # typechk, value never read

        dirs = []

        dirnames = [x[0] for x in vfs_ls if stat.S_ISDIR(x[1].st_mode)]

        if not self.args.ed or "dots" not in self.uparam:
            dirnames = exclude_dotfiles(dirnames)

        for fn in [x for x in dirnames if x != excl]:
            dirs.append(quotep(fn))

        for x in vfs_virt:
            if x != excl:
                dirs.append(x)

        ret["a"] = dirs
        return ret

    def tx_ups(self) -> bool:
        if not self.args.unpost:
            raise Pebkac(403, "the unpost feature is disabled in server config")

        idx = self.conn.get_u2idx()
        if not idx or not hasattr(idx, "p_end"):
            raise Pebkac(500, "sqlite3 is not available on the server; cannot unpost")

        filt = self.uparam.get("filter")
        filt = unquotep(filt or "")
        lm = "ups [{}]".format(filt)
        self.log(lm)

        ret: list[dict[str, Any]] = []
        t0 = time.time()
        lim = time.time() - self.args.unpost
        fk_vols = {
            vol: vol.flags["fk"]
            for vp, vol in self.asrv.vfs.all_vols.items()
            if "fk" in vol.flags and (vp in self.rvol or vp in self.upvol)
        }
        for vol in self.asrv.vfs.all_vols.values():
            cur = idx.get_cur(vol.realpath)
            if not cur:
                continue

            nfk = fk_vols.get(vol, 0)

            q = "select sz, rd, fn, at from up where ip=? and at>?"
            for sz, rd, fn, at in cur.execute(q, (self.ip, lim)):
                vp = "/" + "/".join(x for x in [vol.vpath, rd, fn] if x)
                if filt and filt not in vp:
                    continue

                rv = {"vp": quotep(vp), "sz": sz, "at": at, "nfk": nfk}
                if nfk:
                    rv["ap"] = vol.canonical(vjoin(rd, fn))

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

            ap = rv.pop("ap")
            try:
                st = bos.stat(ap)
            except:
                continue

            fk = self.gen_fk(
                self.args.fk_salt, ap, st.st_size, 0 if ANYWIN else st.st_ino
            )
            rv["vp"] += "?k=" + fk[:nfk]

            n += 1
            if n > 2000:
                break

        ret = ret[:2000]

        if self.is_vproxied:
            for v in ret:
                v["vp"] = self.args.SR + v["vp"]

        jtxt = json.dumps(ret, indent=2, sort_keys=True).encode("utf-8", "replace")
        self.log("{} #{} {:.2f}sec".format(lm, len(ret), time.time() - t0))
        self.reply(jtxt, mime="application/json")
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

        nlim = int(self.uparam.get("lim") or 0)
        lim = [nlim, nlim] if nlim else []

        x = self.conn.hsrv.broker.ask(
            "up2k.handle_rm", self.uname, self.ip, req, lim, False
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

        # x-www-form-urlencoded (url query part) uses
        # either + or %20 for 0x20 so handle both
        dst = unquotep(dst.replace("+", " "))
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

        self.html_head = vn.flags.get("html_head", "")
        if vn.flags.get("norobots") or "b" in self.uparam:
            self.out_headers["X-Robots-Tag"] = "noindex, nofollow"
        else:
            self.out_headers.pop("X-Robots-Tag", None)

        is_dir = stat.S_ISDIR(st.st_mode)
        icur = None
        if is_dir and (e2t or e2d):
            idx = self.conn.get_u2idx()
            if idx and hasattr(idx, "p_end"):
                icur = idx.get_cur(dbv.realpath)

        if self.can_read:
            th_fmt = self.uparam.get("th")
            if th_fmt is not None:
                if is_dir:
                    vrem = vrem.rstrip("/")
                    if icur and vrem:
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
                        return self.tx_ico("a.folder")

                thp = None
                if self.thumbcli:
                    thp = self.thumbcli.get(dbv, vrem, int(st.st_mtime), th_fmt)

                if thp:
                    return self.tx_file(thp)

                if th_fmt == "p":
                    raise Pebkac(404)

                return self.tx_ico(rem)

        if not is_dir and (self.can_read or self.can_get):
            if not self.can_read and "fk" in vn.flags:
                correct = self.gen_fk(
                    self.args.fk_salt, abspath, st.st_size, 0 if ANYWIN else st.st_ino
                )[: vn.flags["fk"]]
                got = self.uparam.get("k")
                if got != correct:
                    self.log("wrong filekey, want {}, got {}".format(correct, got))
                    return self.tx_404()

            if (
                abspath.endswith(".md")
                and "nohtml" not in vn.flags
                and (
                    "v" in self.uparam
                    or "edit" in self.uparam
                    or "edit2" in self.uparam
                )
            ):
                return self.tx_md(abspath)

            return self.tx_file(abspath)

        elif is_dir and not self.can_read and not self.can_write:
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
        if self.can_read:
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

        if not is_ls and (self.ua.startswith("curl/") or self.ua.startswith("fetch")):
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

        readme = ""
        if not self.args.no_readme and not logues[1]:
            for fn in ["README.md", "readme.md"]:
                fn = os.path.join(abspath, fn)
                if bos.path.isfile(fn):
                    with open(fsenc(fn), "rb") as f:
                        readme = f.read().decode("utf-8")
                        break

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
            "lifetime": vn.flags.get("lifetime") or 0,
            "frand": bool(vn.flags.get("rand")),
            "unlist": unlist,
            "perms": perms,
            "logues": logues,
            "readme": readme,
        }
        j2a = {
            "vdir": quotep(self.vpath),
            "vpnodes": vpnodes,
            "files": [],
            "ls0": None,
            "acct": self.uname,
            "perms": json.dumps(perms),
            "lifetime": ls_ret["lifetime"],
            "frand": bool(vn.flags.get("rand")),
            "taglist": [],
            "def_hcols": [],
            "have_emp": self.args.emp,
            "have_up2k_idx": e2d,
            "have_tags_idx": e2t,
            "have_acode": (not self.args.no_acode),
            "have_mv": (not self.args.no_mv),
            "have_del": (not self.args.no_del),
            "have_zip": (not self.args.no_zip),
            "have_unpost": int(self.args.unpost),
            "have_b_u": (self.can_write and self.uparam.get("b") == "u"),
            "sb_md": "" if "no_sb_md" in vf else (vf.get("md_sbf") or "y"),
            "sb_lg": "" if "no_sb_lg" in vf else (vf.get("lg_sbf") or "y"),
            "url_suf": url_suf,
            "logues": logues,
            "readme": readme,
            "title": html_escape(self.vpath, crlf=True) or "💾🎉",
            "srv_info": srv_infot,
            "dgrid": "grid" in vf,
            "unlist": unlist,
            "dtheme": self.args.theme,
            "themes": self.args.themes,
            "turbolvl": self.args.turbo,
            "idxh": int(self.args.ih),
            "u2sort": self.args.u2sort,
        }

        if self.args.js_browser:
            j2a["js"] = self.args.js_browser

        if self.args.css_browser:
            j2a["css"] = self.args.css_browser

        if not self.conn.hsrv.prism:
            j2a["no_prism"] = True

        if not self.can_read:
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
            if v is not None:
                return self.tx_zip(k, v, self.vpath, vn, rem, [], self.args.ed)

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
        if not self.args.ed or "dots" not in self.uparam:
            ls_names = exclude_dotfiles(ls_names)

        add_fk = vn.flags.get("fk")

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
            zd = datetime.utcfromtimestamp(linf.st_mtime)
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

            if add_fk:
                href = "%s?k=%s" % (
                    quotep(href),
                    self.gen_fk(
                        self.args.fk_salt, fspath, sz, 0 if ANYWIN else inf.st_ino
                    )[:add_fk],
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

            fe["tags"] = {k: v for k, v in r}

            if self.can_admin:
                q = "select ip, at from up where rd=? and fn=?"
                try:
                    zs1, zs2 = icur.execute(q, erd_efn).fetchone()
                    fe["tags"]["up_ip"] = zs1
                    fe["tags"][".up_at"] = zs2
                except:
                    pass

            _ = [tagset.add(k) for k in fe["tags"]]

        if icur:
            taglist = [k for k in vn.flags.get("mte", "").split(",") if k in tagset]
            for fe in dirs:
                fe["tags"] = {}
        else:
            taglist = list(tagset)

        if is_ls:
            ls_ret["dirs"] = dirs
            ls_ret["files"] = files
            ls_ret["taglist"] = taglist
            return self.tx_ls(ls_ret)

        doc = self.uparam.get("doc") if self.can_read else None
        if doc:
            doc = unquotep(doc.replace("+", " ").split("?")[0])
            j2a["docname"] = doc
            doctxt = None
            if next((x for x in files if x["name"] == doc), None):
                docpath = os.path.join(abspath, doc)
                sz = bos.path.getsize(docpath)
                if sz < 1024 * self.args.txt_max:
                    with open(fsenc(docpath), "rb") as f:
                        doctxt = f.read().decode("utf-8", "replace")
            else:
                self.log("doc 404: [{}]".format(doc), c=6)
                doctxt = "( textfile not found )"

            if doctxt is not None:
                j2a["doc"] = doctxt

        for d in dirs:
            d["name"] += "/"

        dirs.sort(key=itemgetter("name"))

        if is_js:
            j2a["ls0"] = {
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
            j2a["def_hcols"] = vn.flags["mth"].split(",")

        html = self.j2s(tpl, **j2a)
        self.reply(html.encode("utf-8", "replace"))
        return True

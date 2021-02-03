# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import stat
import gzip
import time
import json
import socket
import ctypes
from datetime import datetime
import calendar

from .__init__ import E, PY2, WINDOWS
from .util import *  # noqa  # pylint: disable=unused-wildcard-import

if not PY2:
    unicode = str


class HttpCli(object):
    """
    Spawned by HttpConn to process one http transaction
    """

    def __init__(self, conn):
        self.t0 = time.time()
        self.conn = conn
        self.s = conn.s
        self.sr = conn.sr
        self.ip = conn.addr[0]
        self.addr = conn.addr
        self.args = conn.args
        self.auth = conn.auth
        self.log_func = conn.log_func
        self.log_src = conn.log_src

        self.bufsz = 1024 * 32
        self.absolute_urls = False
        self.out_headers = {"Access-Control-Allow-Origin": "*"}

    def log(self, msg):
        self.log_func(self.log_src, msg)

    def _check_nonfatal(self, ex):
        return ex.code < 400 or ex.code == 404

    def _assert_safe_rem(self, rem):
        # sanity check to prevent any disasters
        if rem.startswith("/") or rem.startswith("../") or "/../" in rem:
            raise Exception("that was close")

    def run(self):
        """returns true if connection can be reused"""
        self.keepalive = False
        self.headers = {}
        try:
            headerlines = read_header(self.sr)
            if not headerlines:
                return False

            if not headerlines[0]:
                # seen after login with IE6.0.2900.5512.xpsp.080413-2111 (xp-sp3)
                self.log("\033[1;31mBUG: trailing newline from previous request\033[0m")
                headerlines.pop(0)

            try:
                self.mode, self.req, _ = headerlines[0].split(" ")
            except:
                raise Pebkac(400, "bad headers:\n" + "\n".join(headerlines))

        except Pebkac as ex:
            # self.log("pebkac at httpcli.run #1: " + repr(ex))
            self.keepalive = self._check_nonfatal(ex)
            self.loud_reply(str(ex), status=ex.code)
            return self.keepalive

        # normalize incoming headers to lowercase;
        # outgoing headers however are Correct-Case
        for header_line in headerlines[1:]:
            k, v = header_line.split(":", 1)
            self.headers[k.lower()] = v.strip()

        v = self.headers.get("connection", "").lower()
        self.keepalive = not v.startswith("close")

        v = self.headers.get("x-forwarded-for", None)
        if v is not None and self.conn.addr[0] in ["127.0.0.1", "::1"]:
            self.ip = v.split(",")[0]
            self.log_src = self.conn.set_rproxy(self.ip)

        self.uname = "*"
        if "cookie" in self.headers:
            cookies = self.headers["cookie"].split(";")
            for k, v in [x.split("=", 1) for x in cookies]:
                if k.strip() != "cppwd":
                    continue

                v = unescape_cookie(v)
                if v in self.auth.iuser:
                    self.uname = self.auth.iuser[v]

                break

        if self.uname:
            self.rvol = self.auth.vfs.user_tree(self.uname, readable=True)
            self.wvol = self.auth.vfs.user_tree(self.uname, writable=True)

        # split req into vpath + uparam
        uparam = {}
        if "?" not in self.req:
            if not self.req.endswith("/"):
                self.absolute_urls = True

            vpath = undot(self.req)
        else:
            vpath, arglist = self.req.split("?", 1)
            if not vpath.endswith("/"):
                self.absolute_urls = True

            vpath = undot(vpath)
            for k in arglist.split("&"):
                if "=" in k:
                    k, v = k.split("=", 1)
                    uparam[k.lower()] = v.strip()
                else:
                    uparam[k.lower()] = True

        self.uparam = uparam
        self.vpath = unquotep(vpath)

        ua = self.headers.get("user-agent", "")
        if ua.startswith("rclone/"):
            uparam["raw"] = True
            uparam["dots"] = True

        try:
            if self.mode in ["GET", "HEAD"]:
                return self.handle_get() and self.keepalive
            elif self.mode == "POST":
                return self.handle_post() and self.keepalive
            elif self.mode == "PUT":
                return self.handle_put() and self.keepalive
            elif self.mode == "OPTIONS":
                return self.handle_options() and self.keepalive
            else:
                raise Pebkac(400, 'invalid HTTP mode "{0}"'.format(self.mode))

        except Pebkac as ex:
            try:
                # self.log("pebkac at httpcli.run #2: " + repr(ex))
                self.keepalive = self._check_nonfatal(ex)
                self.loud_reply("{}: {}".format(str(ex), self.vpath), status=ex.code)
                return self.keepalive
            except Pebkac:
                return False

    def send_headers(self, length, status=200, mime=None, headers={}):
        response = ["HTTP/1.1 {} {}".format(status, HTTPCODE[status])]

        if length is not None:
            response.append("Content-Length: " + str(length))

        # close if unknown length, otherwise take client's preference
        response.append("Connection: " + ("Keep-Alive" if self.keepalive else "Close"))

        # headers{} overrides anything set previously
        self.out_headers.update(headers)

        # default to utf8 html if no content-type is set
        try:
            mime = mime or self.out_headers["Content-Type"]
        except KeyError:
            mime = "text/html; charset=UTF-8"

        self.out_headers["Content-Type"] = mime

        for k, v in self.out_headers.items():
            response.append("{}: {}".format(k, v))

        try:
            # best practice to separate headers and body into different packets
            self.s.sendall("\r\n".join(response).encode("utf-8") + b"\r\n\r\n")
        except:
            raise Pebkac(400, "client d/c while replying headers")

    def reply(self, body, status=200, mime=None, headers={}):
        # TODO something to reply with user-supplied values safely
        self.send_headers(len(body), status, mime, headers)

        try:
            if self.mode != "HEAD":
                self.s.sendall(body)
        except:
            raise Pebkac(400, "client d/c while replying body")

        return body

    def loud_reply(self, body, *args, **kwargs):
        self.log(body.rstrip())
        self.reply(b"<pre>" + body.encode("utf-8") + b"\r\n", *list(args), **kwargs)

    def handle_get(self):
        logmsg = "{:4} {}".format(self.mode, self.req)

        if "range" in self.headers:
            try:
                rval = self.headers["range"].split("=", 1)[1]
            except:
                rval = self.headers["range"]

            logmsg += " [\033[36m" + rval + "\033[0m]"

        self.log(logmsg)

        # "embedded" resources
        if self.vpath.startswith(".cpr"):
            static_path = os.path.join(E.mod, "web/", self.vpath[5:])
            return self.tx_file(static_path)

        # conditional redirect to single volumes
        if self.vpath == "" and not self.uparam:
            nread = len(self.rvol)
            nwrite = len(self.wvol)
            if nread + nwrite == 1 or (self.rvol == self.wvol and nread == 1):
                if nread == 1:
                    self.vpath = self.rvol[0]
                else:
                    self.vpath = self.wvol[0]

                self.absolute_urls = True

        # go home if verboten
        self.readable, self.writable = self.conn.auth.vfs.can_access(
            self.vpath, self.uname
        )
        if not self.readable and not self.writable:
            self.log("inaccessible: [{}]".format(self.vpath))
            self.uparam = {"h": True}

        if "h" in self.uparam:
            self.vpath = None
            return self.tx_mounts()

        return self.tx_browser()

    def handle_options(self):
        self.log("OPTIONS " + self.req)
        self.send_headers(
            None,
            204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )
        return True

    def handle_put(self):
        self.log("PUT " + self.req)

        if self.headers.get("expect", "").lower() == "100-continue":
            try:
                self.s.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")
            except:
                raise Pebkac(400, "client d/c before 100 continue")

        return self.handle_stash()

    def handle_post(self):
        self.log("POST " + self.req)

        if self.headers.get("expect", "").lower() == "100-continue":
            try:
                self.s.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")
            except:
                raise Pebkac(400, "client d/c before 100 continue")

        ctype = self.headers.get("content-type", "").lower()
        if not ctype:
            raise Pebkac(400, "you can't post without a content-type header")

        if "raw" in self.uparam:
            return self.handle_stash()

        if "multipart/form-data" in ctype:
            return self.handle_post_multipart()

        if "text/plain" in ctype or "application/xml" in ctype:
            # TODO this will be intredasting
            return self.handle_post_json()

        if "application/octet-stream" in ctype:
            return self.handle_post_binary()

        if "application/x-www-form-urlencoded" in ctype:
            opt = self.args.urlform
            if "stash" in opt:
                return self.handle_stash()

            if "save" in opt:
                post_sz, _, _, path = self.dump_to_file()
                self.log("urlform: {} bytes, {}".format(post_sz, path))
            elif "print" in opt:
                reader, _ = self.get_body_reader()
                for buf in reader:
                    buf = buf.decode("utf-8", "replace")
                    self.log("urlform:\n  {}\n".format(buf))

            if "get" in opt:
                return self.handle_get()

            raise Pebkac(405, "POST({}) is disabled".format(ctype))

        raise Pebkac(405, "don't know how to handle POST({})".format(ctype))

    def get_body_reader(self):
        remains = int(self.headers.get("content-length", None))
        if remains is None:
            self.keepalive = False
            return read_socket_unbounded(self.sr), remains
        else:
            return read_socket(self.sr, remains), remains

    def dump_to_file(self):
        reader, remains = self.get_body_reader()
        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)
        fdir = os.path.join(vfs.realpath, rem)

        addr = self.ip.replace(":", ".")
        fn = "put-{:.6f}-{}.bin".format(time.time(), addr)
        path = os.path.join(fdir, fn)

        with open(path, "wb", 512 * 1024) as f:
            post_sz, _, sha_b64 = hashcopy(self.conn, reader, f)

        return post_sz, sha_b64, remains, path

    def handle_stash(self):
        post_sz, sha_b64, remains, path = self.dump_to_file()
        spd = self._spd(post_sz)
        self.log("{} wrote {}/{} bytes to {}".format(spd, post_sz, remains, path))
        self.reply("{}\n{}\n".format(post_sz, sha_b64).encode("utf-8"))
        return True

    def _spd(self, nbytes, add=True):
        if add:
            self.conn.nbyte += nbytes

        spd1 = get_spd(nbytes, self.t0)
        spd2 = get_spd(self.conn.nbyte, self.conn.t0)
        return spd1 + " " + spd2

    def handle_post_multipart(self):
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

        raise Pebkac(422, 'invalid action "{}"'.format(act))

    def handle_post_json(self):
        try:
            remains = int(self.headers["content-length"])
        except:
            raise Pebkac(400, "you must supply a content-length for JSON POST")

        if remains > 1024 * 1024:
            raise Pebkac(413, "json 2big")

        enc = "utf-8"
        ctype = self.headers.get("content-type", "").lower()
        if "charset" in ctype:
            enc = ctype.split("charset")[1].strip(" =").split(";")[0].strip()

        json_buf = b""
        while len(json_buf) < remains:
            json_buf += self.sr.recv(32 * 1024)

        self.log("decoding {} bytes of {} json".format(len(json_buf), enc))
        try:
            body = json.loads(json_buf.decode(enc, "replace"))
        except:
            raise Pebkac(422, "you POSTed invalid json")

        # prefer this over undot; no reason to allow traversion
        if "/" in body["name"]:
            raise Pebkac(400, "folders verboten")

        # up2k-php compat
        for k in "chunkpit.php", "handshake.php":
            if self.vpath.endswith(k):
                self.vpath = self.vpath[: -len(k)]

        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)

        body["vtop"] = vfs.vpath
        body["ptop"] = vfs.realpath
        body["prel"] = rem
        body["addr"] = self.ip
        body["flag"] = vfs.flags

        x = self.conn.hsrv.broker.put(True, "up2k.handle_json", body)
        response = x.get()
        response = json.dumps(response)

        self.log(response)
        self.reply(response.encode("utf-8"), mime="application/json")
        return True

    def handle_post_binary(self):
        try:
            remains = int(self.headers["content-length"])
        except:
            raise Pebkac(400, "you must supply a content-length for binary POST")

        try:
            chash = self.headers["x-up2k-hash"]
            wark = self.headers["x-up2k-wark"]
        except KeyError:
            raise Pebkac(400, "need hash and wark headers for binary POST")

        vfs, _ = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)
        ptop = vfs.realpath

        x = self.conn.hsrv.broker.put(True, "up2k.handle_chunk", ptop, wark, chash)
        response = x.get()
        chunksize, cstart, path, lastmod = response

        if self.args.nw:
            path = os.devnull

        if remains > chunksize:
            raise Pebkac(400, "your chunk is too big to fit")

        self.log("writing {} #{} @{} len {}".format(path, chash, cstart, remains))

        reader = read_socket(self.sr, remains)

        with open(path, "rb+", 512 * 1024) as f:
            f.seek(cstart[0])
            post_sz, _, sha_b64 = hashcopy(self.conn, reader, f)

            if sha_b64 != chash:
                raise Pebkac(
                    400,
                    "your chunk got corrupted somehow (received {} bytes); expected vs received hash:\n{}\n{}".format(
                        post_sz, chash, sha_b64
                    ),
                )

            if len(cstart) > 1 and path != os.devnull:
                self.log(
                    "clone {} to {}".format(
                        cstart[0], " & ".join(str(x) for x in cstart[1:])
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

        x = self.conn.hsrv.broker.put(True, "up2k.confirm_chunk", ptop, wark, chash)
        num_left, path = x.get()

        if not WINDOWS and num_left == 0:
            times = (int(time.time()), int(lastmod))
            self.log("no more chunks, setting times {}".format(times))
            try:
                os.utime(path, times)
            except:
                self.log("failed to utime ({}, {})".format(path, times))

        spd = self._spd(post_sz)
        self.log("{} thank".format(spd))
        self.reply(b"thank")
        return True

    def handle_login(self):
        pwd = self.parser.require("cppwd", 64)
        self.parser.drop()

        if pwd in self.auth.iuser:
            msg = "login ok"
        else:
            msg = "naw dude"
            pwd = "x"  # nosec

        h = {"Set-Cookie": "cppwd={}; Path=/; SameSite=Lax".format(pwd)}
        html = self.conn.tpl_msg.render(h1=msg, h2='<a href="/">ack</a>', redir="/")
        self.reply(html.encode("utf-8"), headers=h)
        return True

    def handle_mkdir(self):
        new_dir = self.parser.require("name", 512)
        self.parser.drop()

        nullwrite = self.args.nw
        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)
        self._assert_safe_rem(rem)

        sanitized = sanitize_fn(new_dir)

        if not nullwrite:
            fdir = os.path.join(vfs.realpath, rem)
            fn = os.path.join(fdir, sanitized)

            if not os.path.isdir(fsenc(fdir)):
                raise Pebkac(500, "parent folder does not exist")

            if os.path.isdir(fsenc(fn)):
                raise Pebkac(500, "that folder exists already")

            try:
                os.mkdir(fsenc(fn))
            except:
                raise Pebkac(500, "mkdir failed, check the logs")

        vpath = "{}/{}".format(self.vpath, sanitized).lstrip("/")
        esc_paths = [quotep(vpath), html_escape(vpath)]
        html = self.conn.tpl_msg.render(
            h2='<a href="/{}">go to /{}</a>'.format(*esc_paths),
            pre="aight",
            click=True,
        )
        self.reply(html.encode("utf-8", "replace"))
        return True

    def handle_new_md(self):
        new_file = self.parser.require("name", 512)
        self.parser.drop()

        nullwrite = self.args.nw
        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)
        self._assert_safe_rem(rem)

        if not new_file.endswith(".md"):
            new_file += ".md"

        sanitized = sanitize_fn(new_file)

        if not nullwrite:
            fdir = os.path.join(vfs.realpath, rem)
            fn = os.path.join(fdir, sanitized)

            if os.path.exists(fsenc(fn)):
                raise Pebkac(500, "that file exists already")

            with open(fsenc(fn), "wb") as f:
                f.write(b"`GRUNNUR`\n")

        vpath = "{}/{}".format(self.vpath, sanitized).lstrip("/")
        html = self.conn.tpl_msg.render(
            h2='<a href="/{}?edit">go to /{}?edit</a>'.format(
                quotep(vpath), html_escape(vpath)
            ),
            pre="aight",
            click=True,
        )
        self.reply(html.encode("utf-8", "replace"))
        return True

    def handle_plain_upload(self):
        nullwrite = self.args.nw
        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)
        self._assert_safe_rem(rem)

        files = []
        errmsg = ""
        t0 = time.time()
        try:
            for nfile, (p_field, p_file, p_data) in enumerate(self.parser.gen):
                if not p_file:
                    self.log("discarding incoming file without filename")
                    # fallthrough

                if p_file and not nullwrite:
                    fdir = os.path.join(vfs.realpath, rem)
                    fname = sanitize_fn(p_file)

                    if not os.path.isdir(fsenc(fdir)):
                        raise Pebkac(404, "that folder does not exist")

                    suffix = ".{:.6f}-{}".format(time.time(), self.ip)
                    open_args = {"fdir": fdir, "suffix": suffix}
                else:
                    open_args = {}
                    fname = os.devnull
                    fdir = ""

                try:
                    with ren_open(fname, "wb", 512 * 1024, **open_args) as f:
                        f, fname = f["orz"]
                        self.log("writing to {}/{}".format(fdir, fname))
                        sz, sha512_hex, _ = hashcopy(self.conn, p_data, f)
                        if sz == 0:
                            raise Pebkac(400, "empty files in post")

                        files.append([sz, sha512_hex])
                        self.conn.nbyte += sz

                except Pebkac:
                    if fname != os.devnull:
                        fp = os.path.join(fdir, fname)
                        suffix = ".PARTIAL"
                        try:
                            os.rename(fsenc(fp), fsenc(fp + suffix))
                        except:
                            fp = fp[: -len(suffix)]
                            os.rename(fsenc(fp), fsenc(fp + suffix))

                    raise

        except Pebkac as ex:
            errmsg = str(ex)

        td = max(0.1, time.time() - t0)
        sz_total = sum(x[0] for x in files)
        spd = (sz_total / td) / (1024 * 1024)

        status = "OK"
        if errmsg:
            self.log(errmsg)
            errmsg = "ERROR: " + errmsg
            status = "ERROR"

        msg = "{0} // {1} bytes // {2:.3f} MiB/s\n".format(status, sz_total, spd)

        for sz, sha512 in files:
            msg += "sha512: {0} // {1} bytes\n".format(sha512[:56], sz)
            # truncated SHA-512 prevents length extension attacks;
            # using SHA-512/224, optionally SHA-512/256 = :64

        vspd = self._spd(sz_total, False)
        self.log("{} {}".format(vspd, msg))

        if not nullwrite:
            # TODO this is bad
            log_fn = "up.{:.6f}.txt".format(t0)
            with open(log_fn, "wb") as f:
                f.write(
                    (
                        "\n".join(
                            unicode(x)
                            for x in [
                                ":".join(unicode(x) for x in [self.ip, self.addr[1]]),
                                msg.rstrip(),
                            ]
                        )
                        + "\n"
                        + errmsg
                        + "\n"
                    ).encode("utf-8")
                )

        html = self.conn.tpl_msg.render(
            h2='<a href="/{}">return to /{}</a>'.format(
                quotep(self.vpath), html_escape(self.vpath)
            ),
            pre=msg,
        )
        self.reply(html.encode("utf-8", "replace"))
        self.parser.drop()
        return True

    def handle_text_upload(self):
        try:
            cli_lastmod3 = int(self.parser.require("lastmod", 16))
        except:
            raise Pebkac(400, "could not read lastmod from request")

        nullwrite = self.args.nw
        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)
        self._assert_safe_rem(rem)

        # TODO:
        #   the per-volume read/write permissions must be replaced with permission flags
        #   which would decide how to handle uploads to filenames which are taken,
        #   current behavior of creating a new name is a good default for binary files
        #   but should also offer a flag to takeover the filename and rename the old one
        #
        # stopgap:
        if not rem.endswith(".md"):
            raise Pebkac(400, "only markdown pls")

        if nullwrite:
            response = json.dumps({"ok": True, "lastmod": 0})
            self.log(response)
            # TODO reply should parser.drop()
            self.parser.drop()
            self.reply(response.encode("utf-8"))
            return True

        fp = os.path.join(vfs.realpath, rem)
        srv_lastmod = srv_lastmod3 = -1
        try:
            st = os.stat(fsenc(fp))
            srv_lastmod = st.st_mtime
            srv_lastmod3 = int(srv_lastmod * 1000)
        except OSError as ex:
            if ex.errno != 2:
                raise

        # if file exists, chekc that timestamp matches the client's
        if srv_lastmod >= 0:
            same_lastmod = cli_lastmod3 in [-1, srv_lastmod3]
            if not same_lastmod:
                # some filesystems/transports limit precision to 1sec, hopefully floored
                same_lastmod = (
                    srv_lastmod == int(srv_lastmod)
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

            # TODO another hack re: pending permissions rework
            mdir, mfile = os.path.split(fp)
            mfile2 = "{}.{:.3f}.md".format(mfile[:-3], srv_lastmod)
            try:
                os.mkdir(os.path.join(mdir, ".hist"))
            except:
                pass
            os.rename(fp, os.path.join(mdir, ".hist", mfile2))

        p_field, _, p_data = next(self.parser.gen)
        if p_field != "body":
            raise Pebkac(400, "expected body, got {}".format(p_field))

        with open(fp, "wb", 512 * 1024) as f:
            sz, sha512, _ = hashcopy(self.conn, p_data, f)

        new_lastmod = os.stat(fsenc(fp)).st_mtime
        new_lastmod3 = int(new_lastmod * 1000)
        sha512 = sha512[:56]

        response = json.dumps(
            {"ok": True, "lastmod": new_lastmod3, "size": sz, "sha512": sha512}
        )
        self.log(response)
        self.parser.drop()
        self.reply(response.encode("utf-8"))
        return True

    def _chk_lastmod(self, file_ts):
        file_dt = datetime.utcfromtimestamp(file_ts)
        file_lastmod = file_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

        cli_lastmod = self.headers.get("if-modified-since")
        if cli_lastmod:
            try:
                cli_dt = time.strptime(cli_lastmod, "%a, %d %b %Y %H:%M:%S GMT")
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

    def tx_file(self, req_path):
        status = 200
        logmsg = "{:4} {} ".format("", self.req)
        logtail = ""

        #
        # if request is for foo.js, check if we have foo.js.{gz,br}

        file_ts = 0
        editions = {}
        for ext in ["", ".gz", ".br"]:
            try:
                fs_path = req_path + ext
                st = os.stat(fsenc(fs_path))
                file_ts = max(file_ts, st.st_mtime)
                editions[ext or "plain"] = [fs_path, st.st_size]
            except:
                pass
            if not self.vpath.startswith(".cpr/"):
                break

        if not editions:
            raise Pebkac(404)

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
                ua = self.headers.get("user-agent", "")
                if re.match(r"MSIE [4-6]\.", ua) and " SV1" not in ua:
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
        if do_send and not is_compressed and hrange:
            try:
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
            open_func = gzip.open
            open_args = [fsenc(fs_path), "rb"]
            # Content-Length := original file size
            upper = gzip_orig_sz(fs_path)
        else:
            open_func = open
            # 512 kB is optimal for huge files, use 64k
            open_args = [fsenc(fs_path), "rb", 64 * 1024]
            if hasattr(os, "sendfile"):
                use_sendfile = not self.args.no_sendfile

        #
        # send reply

        if not is_compressed:
            self.out_headers["Cache-Control"] = "no-cache"

        self.out_headers["Accept-Ranges"] = "bytes"
        self.send_headers(
            length=upper - lower,
            status=status,
            mime=guess_mime(req_path)[0] or "application/octet-stream",
        )

        logmsg += str(status) + logtail

        if self.mode == "HEAD" or not do_send:
            self.log(logmsg)
            return True

        ret = True
        with open_func(*open_args) as f:
            if use_sendfile:
                remains = sendfile_kern(lower, upper, f, self.s)
            else:
                remains = sendfile_py(lower, upper, f, self.s)

        if remains > 0:
            logmsg += " \033[31m" + str(upper - remains) + "\033[0m"

        spd = self._spd((upper - lower) - remains)
        self.log("{},  {}".format(logmsg, spd))
        return ret

    def tx_md(self, fs_path):
        logmsg = "{:4} {} ".format("", self.req)
        if "edit2" in self.uparam:
            html_path = "web/mde.html"
            template = self.conn.tpl_mde
        else:
            html_path = "web/md.html"
            template = self.conn.tpl_md

        html_path = os.path.join(E.mod, html_path)

        st = os.stat(fsenc(fs_path))
        # sz_md = st.st_size
        ts_md = st.st_mtime

        st = os.stat(fsenc(html_path))
        ts_html = st.st_mtime

        # TODO dont load into memory ;_;
        #   (trivial fix, count the &'s)
        with open(fsenc(fs_path), "rb") as f:
            md = f.read().replace(b"&", b"&amp;")
            sz_md = len(md)

        file_ts = max(ts_md, ts_html)
        file_lastmod, do_send = self._chk_lastmod(file_ts)
        self.out_headers["Last-Modified"] = file_lastmod
        self.out_headers["Cache-Control"] = "no-cache"
        status = 200 if do_send else 304

        targs = {
            "edit": "edit" in self.uparam,
            "title": html_escape(self.vpath),
            "lastmod": int(ts_md * 1000),
            "md_plug": "true" if self.args.emp else "false",
            "md_chk_rate": self.args.mcr,
            "md": "",
        }
        sz_html = len(template.render(**targs).encode("utf-8"))
        self.send_headers(sz_html + sz_md, status)

        logmsg += str(status)
        if self.mode == "HEAD" or not do_send:
            self.log(logmsg)
            return True

        # TODO jinja2 can stream this right?
        targs["md"] = md.decode("utf-8", "replace")
        html = template.render(**targs).encode("utf-8")
        try:
            self.s.sendall(html)
        except:
            self.log(logmsg + " \033[31md/c\033[0m")
            return False

        self.log(logmsg + " " + str(len(html)))
        return True

    def tx_mounts(self):
        rvol = [x + "/" if x else x for x in self.rvol]
        wvol = [x + "/" if x else x for x in self.wvol]
        html = self.conn.tpl_mounts.render(this=self, rvol=rvol, wvol=wvol)
        self.reply(html.encode("utf-8"))
        return True

    def tx_browser(self):
        vpath = ""
        vpnodes = [["", "/"]]
        if self.vpath:
            for node in self.vpath.split("/"):
                if not vpath:
                    vpath = node
                else:
                    vpath += "/" + node

                vpnodes.append([quotep(vpath) + "/", html_escape(node)])

        vn, rem = self.auth.vfs.get(
            self.vpath, self.uname, self.readable, self.writable
        )
        abspath = vn.canonical(rem)

        if not os.path.exists(fsenc(abspath)):
            # print(abspath)
            raise Pebkac(404)

        if not os.path.isdir(fsenc(abspath)):
            if abspath.endswith(".md") and "raw" not in self.uparam:
                return self.tx_md(abspath)

            bad = "{0}.hist{0}up2k.".format(os.sep)
            if abspath.endswith(bad + "db") or abspath.endswith(bad + "snap"):
                raise Pebkac(403)

            return self.tx_file(abspath)

        fsroot, vfs_ls, vfs_virt = vn.ls(rem, self.uname)
        vfs_ls.extend(vfs_virt.keys())

        # check for old versions of files,
        hist = {}  # [num-backups, most-recent, hist-path]
        histdir = os.path.join(fsroot, ".hist")
        ptn = re.compile(r"(.*)\.([0-9]+\.[0-9]{3})(\.[^\.]+)$")
        try:
            for hfn in os.listdir(histdir):
                m = ptn.match(hfn)
                if not m:
                    continue

                fn = m.group(1) + m.group(3)
                n, ts, _ = hist.get(fn, [0, 0, ""])
                hist[fn] = [n + 1, max(ts, float(m.group(2))), hfn]
        except:
            pass

        # show dotfiles if permitted and requested
        if not self.args.ed or "dots" not in self.uparam:
            vfs_ls = exclude_dotfiles(vfs_ls)

        dirs = []
        files = []
        for fn in vfs_ls:
            base = ""
            href = fn
            if self.absolute_urls and vpath:
                base = "/" + vpath + "/"
                href = base + fn

            if fn in vfs_virt:
                fspath = vfs_virt[fn].realpath
            else:
                fspath = fsroot + "/" + fn

            try:
                inf = os.stat(fsenc(fspath))
            except:
                self.log("broken symlink: {}".format(repr(fspath)))
                continue

            is_dir = stat.S_ISDIR(inf.st_mode)
            if is_dir:
                margin = "DIR"
                href += "/"
            elif fn in hist:
                margin = '<a href="{}.hist/{}">#{}</a>'.format(
                    base, html_escape(hist[fn][2], quote=True), hist[fn][0]
                )
            else:
                margin = "-"

            sz = inf.st_size
            dt = datetime.utcfromtimestamp(inf.st_mtime)
            dt = dt.strftime("%Y-%m-%d %H:%M:%S")

            try:
                ext = "---" if is_dir else fn.rsplit(".", 1)[1]
            except:
                ext = "%"

            item = [margin, quotep(href), html_escape(fn), sz, ext, dt]
            if is_dir:
                dirs.append(item)
            else:
                files.append(item)

        logues = [None, None]
        for n, fn in enumerate([".prologue.html", ".epilogue.html"]):
            fn = os.path.join(abspath, fn)
            if os.path.exists(fsenc(fn)):
                with open(fsenc(fn), "rb") as f:
                    logues[n] = f.read().decode("utf-8")

        if False:
            # this is a mistake
            md = None
            for fn in [x[2] for x in files]:
                if fn.lower() == "readme.md":
                    fn = os.path.join(abspath, fn)
                    with open(fn, "rb") as f:
                        md = f.read().decode("utf-8")

                    break

        srv_info = []

        try:
            if not self.args.nih:
                srv_info.append(str(socket.gethostname()).split(".")[0])
        except:
            self.log("#wow #whoa")
            pass

        try:
            # some fuses misbehave
            if not self.args.nid:
                if WINDOWS:
                    bfree = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p(abspath), None, None, ctypes.pointer(bfree)
                    )
                    srv_info.append(humansize(bfree.value) + " free")
                else:
                    sv = os.statvfs(abspath)
                    free = humansize(sv.f_frsize * sv.f_bfree, True)
                    total = humansize(sv.f_frsize * sv.f_blocks, True)

                    srv_info.append(free + " free")
                    srv_info.append(total)
        except:
            pass

        ts = ""
        # ts = "?{}".format(time.time())

        dirs.extend(files)
        html = self.conn.tpl_browser.render(
            vdir=quotep(self.vpath),
            vpnodes=vpnodes,
            files=dirs,
            can_upload=self.writable,
            can_read=self.readable,
            ts=ts,
            prologue=logues[0],
            epilogue=logues[1],
            title=html_escape(self.vpath),
            srv_info="</span> /// <span>".join(srv_info),
        )
        self.reply(html.encode("utf-8", "replace"))
        return True

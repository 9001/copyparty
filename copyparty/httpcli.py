# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import stat
import gzip
import time
import json
from datetime import datetime
import calendar
import mimetypes

from .__init__ import E, PY2
from .util import *  # noqa  # pylint: disable=unused-wildcard-import

if not PY2:
    unicode = str
    from html import escape as html_escape
else:
    from cgi import escape as html_escape


class HttpCli(object):
    """
    Spawned by HttpConn to process one http transaction
    """

    def __init__(self, conn):
        self.conn = conn
        self.s = conn.s
        self.sr = conn.sr
        self.addr = conn.addr
        self.args = conn.args
        self.auth = conn.auth
        self.log_func = conn.log_func
        self.log_src = conn.log_src

        self.bufsz = 1024 * 32
        self.absolute_urls = False
        self.out_headers = {}

    def log(self, msg):
        self.log_func(self.log_src, msg)

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
            self.loud_reply(str(ex), status=ex.code)
            return False

        for header_line in headerlines[1:]:
            k, v = header_line.split(":", 1)
            self.headers[k.lower()] = v.strip()

        v = self.headers.get("connection", "").lower()
        self.keepalive = not v.startswith("close")

        self.uname = "*"
        if "cookie" in self.headers:
            cookies = self.headers["cookie"].split(";")
            for k, v in [x.split("=", 1) for x in cookies]:
                if k != "cppwd":
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

        try:
            if self.mode in ["GET", "HEAD"]:
                return self.handle_get() and self.keepalive
            elif self.mode == "POST":
                return self.handle_post() and self.keepalive
            else:
                raise Pebkac(400, 'invalid HTTP mode "{0}"'.format(self.mode))

        except Pebkac as ex:
            try:
                self.loud_reply(str(ex), status=ex.code)
            except Pebkac:
                pass

            return False

    def reply(self, body, status=200, mime="text/html", headers=[]):
        # TODO something to reply with user-supplied values safely
        response = [
            "HTTP/1.1 {} {}".format(status, HTTPCODE[status]),
            "Content-Type: " + mime,
            "Content-Length: " + str(len(body)),
            "Connection: " + ("Keep-Alive" if self.keepalive else "Close"),
        ]
        for k, v in self.out_headers.items():
            response.append("{}: {}".format(k, v))

        response.extend(headers)
        response_str = "\r\n".join(response).encode("utf-8")
        try:
            self.s.sendall(response_str + b"\r\n\r\n" + body)
        except:
            raise Pebkac(400, "client disconnected before http response")

        return body

    def loud_reply(self, body, *args, **kwargs):
        self.log(body.rstrip())
        self.reply(b"<pre>" + body.encode("utf-8"), *list(args), **kwargs)

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
        
    def handle_post(self):
        self.log("POST " + self.req)

        if self.headers.get("expect", "").lower() == "100-continue":
            self.s.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")

        ctype = self.headers.get("content-type", "").lower()
        if not ctype:
            raise Pebkac(400, "you can't post without a content-type header")

        if "multipart/form-data" in ctype:
            return self.handle_post_multipart()

        if "text/plain" in ctype or "application/xml" in ctype:
            # TODO this will be intredasting
            return self.handle_post_json()

        if "application/octet-stream" in ctype:
            return self.handle_post_binary()

        raise Pebkac(405, "don't know how to handle {} POST".format(ctype))

    def handle_post_multipart(self):
        self.parser = MultipartParser(self.log, self.sr, self.headers)
        self.parser.parse()

        act = self.parser.require("act", 64)

        if act == "bput":
            return self.handle_plain_upload()

        if act == "login":
            return self.handle_login()

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

        body["vdir"] = os.path.join(vfs.realpath, rem)
        body["addr"] = self.conn.addr[0]

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

        x = self.conn.hsrv.broker.put(True, "up2k.handle_chunk", wark, chash)
        response = x.get()
        chunksize, cstart, path = response

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

        x = self.conn.hsrv.broker.put(True, "up2k.confirm_chunk", wark, chash)
        response = x.get()

        self.loud_reply("thank")
        return True

    def handle_login(self):
        pwd = self.parser.require("cppwd", 64)
        self.parser.drop()

        if pwd in self.auth.iuser:
            msg = "login ok"
        else:
            msg = "naw dude"
            pwd = "x"  # nosec

        h = ["Set-Cookie: cppwd={}; Path=/".format(pwd)]
        html = self.conn.tpl_msg.render(h1=msg, h2='<a href="/">ack</a>', redir="/")
        self.reply(html.encode("utf-8"), headers=h)
        return True

    def handle_plain_upload(self):
        nullwrite = self.args.nw
        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)

        # rem is escaped at this point,
        # this is just a sanity check to prevent any disasters
        if rem.startswith("/") or rem.startswith("../") or "/../" in rem:
            raise Exception("that was close")

        files = []
        errmsg = ""
        t0 = time.time()
        try:
            for nfile, (p_field, p_file, p_data) in enumerate(self.parser.gen):
                if not p_file:
                    self.log("discarding incoming file without filename")
                    # fallthrough

                fn = os.devnull
                if p_file and not nullwrite:
                    fdir = os.path.join(vfs.realpath, rem)
                    fn = os.path.join(fdir, sanitize_fn(p_file))

                    if not os.path.isdir(fsenc(fdir)):
                        raise Pebkac(404, "that folder does not exist")

                    # TODO broker which avoid this race
                    # and provides a new filename if taken
                    if os.path.exists(fsenc(fn)):
                        fn += ".{:.6f}".format(time.time())

                try:
                    with open(fsenc(fn), "wb") as f:
                        self.log("writing to {0}".format(fn))
                        sz, sha512_hex, _ = hashcopy(self.conn, p_data, f)
                        if sz == 0:
                            raise Pebkac(400, "empty files in post")

                        files.append([sz, sha512_hex])

                except Pebkac:
                    if fn != os.devnull:
                        os.rename(fsenc(fn), fsenc(fn + ".PARTIAL"))

                    raise

        except Pebkac as ex:
            errmsg = str(ex)

        td = time.time() - t0
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

        self.log(msg)
        if not nullwrite:
            # TODO this is bad
            log_fn = "up.{:.6f}.txt".format(t0)
            with open(log_fn, "wb") as f:
                f.write(
                    (
                        "\n".join(
                            unicode(x)
                            for x in [
                                ":".join(unicode(x) for x in self.addr),
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
                quotep(self.vpath), html_escape(self.vpath, quote=False)
            ),
            pre=msg,
        )
        self.reply(html.encode("utf-8", "replace"))
        self.parser.drop()
        return True

    def tx_file(self, req_path):
        do_send = True
        status = 200
        extra_headers = []
        logmsg = "{:4} {} ".format("", self.req)
        logtail = ""

        #
        # if request is for foo.js, check if we have foo.js.gz

        is_gzip = False
        fs_path = req_path
        try:
            file_sz = os.path.getsize(fsenc(fs_path))
        except:
            is_gzip = True
            fs_path += ".gz"
            try:
                file_sz = os.path.getsize(fsenc(fs_path))
            except:
                raise Pebkac(404)

        #
        # if-modified

        file_ts = os.path.getmtime(fsenc(fs_path))
        file_dt = datetime.utcfromtimestamp(file_ts)
        file_lastmod = file_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

        cli_lastmod = self.headers.get("if-modified-since")
        if cli_lastmod:
            try:
                cli_dt = time.strptime(cli_lastmod, "%a, %d %b %Y %H:%M:%S GMT")
                cli_ts = calendar.timegm(cli_dt)
                do_send = int(file_ts) > int(cli_ts)
            except:
                self.log("bad lastmod format: {}".format(cli_lastmod))
                do_send = file_lastmod != cli_lastmod

        if not do_send:
            status = 304

        #
        # partial

        lower = 0
        upper = file_sz
        hrange = self.headers.get("range")

        if do_send and not is_gzip and hrange:
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

                if lower < 0 or lower >= file_sz or upper < 0 or upper > file_sz:
                    raise Exception()

            except:
                raise Pebkac(400, "invalid range requested: " + hrange)

            status = 206
            extra_headers.append(
                "Content-Range: bytes {}-{}/{}".format(lower, upper - 1, file_sz)
            )

            logtail += " [\033[36m{}-{}\033[0m]".format(lower, upper)

        #
        # Accept-Encoding and UA decides if we can send gzip as-is

        decompress = False
        if is_gzip:
            if "gzip" not in self.headers.get("accept-encoding", "").lower():
                decompress = True
            else:
                ua = self.headers.get("user-agent", "")
                if re.match(r"MSIE [4-6]\.", ua) and " SV1" not in ua:
                    decompress = True

            if not decompress:
                extra_headers.append("Content-Encoding: gzip")

        if decompress:
            open_func = gzip.open
            open_args = [fsenc(fs_path), "rb"]
            # Content-Length := original file size
            upper = gzip_orig_sz(fs_path)
        else:
            open_func = open
            # 512 kB is optimal for huge files, use 64k
            open_args = [fsenc(fs_path), "rb", 64 * 1024]

        #
        # send reply

        logmsg += str(status) + logtail

        mime = mimetypes.guess_type(req_path)[0] or "application/octet-stream"

        headers = [
            "HTTP/1.1 {} {}".format(status, HTTPCODE[status]),
            "Content-Type: " + mime,
            "Content-Length: " + str(upper - lower),
            "Accept-Ranges: bytes",
            "Last-Modified: " + file_lastmod,
            "Connection: " + ("Keep-Alive" if self.keepalive else "Close"),
        ]

        headers.extend(extra_headers)
        headers = "\r\n".join(headers).encode("utf-8") + b"\r\n\r\n"
        self.s.sendall(headers)

        if self.mode == "HEAD" or not do_send:
            self.log(logmsg)
            return True

        with open_func(*open_args) as f:
            remains = upper - lower
            f.seek(lower)
            while remains > 0:
                # time.sleep(0.01)
                buf = f.read(4096)
                if not buf:
                    break

                if remains < len(buf):
                    buf = buf[:remains]

                remains -= len(buf)

                try:
                    self.s.sendall(buf)
                except:
                    logmsg += " \033[31m" + str(upper - remains) + "\033[0m"
                    self.log(logmsg)
                    return False

        self.log(logmsg)
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

                vpnodes.append([quotep(vpath) + "/", html_escape(node, quote=False)])

        vn, rem = self.auth.vfs.get(self.vpath, self.uname, self.readable, self.writable)
        abspath = vn.canonical(rem)

        if not os.path.exists(fsenc(abspath)):
            # print(abspath)
            raise Pebkac(404)

        if not os.path.isdir(fsenc(abspath)):
            return self.tx_file(abspath)

        fsroot, vfs_ls, vfs_virt = vn.ls(rem, self.uname)
        vfs_ls.extend(vfs_virt)

        dirs = []
        files = []
        for fn in exclude_dotfiles(vfs_ls):
            href = fn
            if self.absolute_urls and vpath:
                href = "/" + vpath + "/" + fn

            fspath = fsroot + "/" + fn
            try:
                inf = os.stat(fsenc(fspath))
            except FileNotFoundError as ex:
                self.log("broken symlink: {}".format(fspath))
                continue

            is_dir = stat.S_ISDIR(inf.st_mode)
            if is_dir:
                margin = "DIR"
                href += "/"
            else:
                margin = "-"

            sz = inf.st_size
            dt = datetime.utcfromtimestamp(inf.st_mtime)
            dt = dt.strftime("%Y-%m-%d %H:%M:%S")

            item = [margin, quotep(href), html_escape(fn, quote=False), sz, dt]
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
        )
        self.reply(html.encode("utf-8", "replace"))
        return True


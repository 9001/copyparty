#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import stat
import time
from datetime import datetime
import mimetypes
import cgi

from .__init__ import E, PY2
from .util import *  # noqa  # pylint: disable=unused-wildcard-import

if not PY2:
    unicode = str


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

        self.ok = True
        self.bufsz = 1024 * 32
        self.absolute_urls = False
        self.out_headers = {}

    def log(self, msg):
        self.log_func(self.log_src, msg)

    def run(self):
        try:
            headerlines = read_header(self.sr)
        except:
            return False

        try:
            mode, self.req, _ = headerlines[0].split(" ")
        except:
            raise Pebkac("bad headers:\n" + "\n".join(headerlines))

        self.headers = {}
        for header_line in headerlines[1:]:
            k, v = header_line.split(":", 1)
            self.headers[k.lower()] = v.strip()

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
            if mode == "GET":
                self.handle_get()
            elif mode == "POST":
                self.handle_post()
            else:
                self.loud_reply('invalid HTTP mode "{0}"'.format(mode))

        except Pebkac as ex:
            self.loud_reply(str(ex))
            return False

        return self.ok

    def reply(self, body, status="200 OK", mime="text/html", headers=[]):
        # TODO something to reply with user-supplied values safely
        response = [
            "HTTP/1.1 " + status,
            "Connection: Keep-Alive",
            "Content-Type: " + mime,
            "Content-Length: " + str(len(body)),
        ]
        for k, v in self.out_headers.items():
            response.append("{}: {}".format(k, v))

        response.extend(headers)
        response_str = "\r\n".join(response).encode("utf-8")
        if self.ok:
            self.s.send(response_str + b"\r\n\r\n" + body)

        return body

    def loud_reply(self, body, *args, **kwargs):
        self.log(body.rstrip())
        self.reply(b"<pre>" + body.encode("utf-8"), *list(args), **kwargs)

    def handle_get(self):
        self.log("GET  " + self.req)

        # "embedded" resources
        if self.vpath.startswith(".cpr"):
            static_path = os.path.join(E.mod, "web/", self.vpath[5:])

            if os.path.isfile(static_path):
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
            self.log("inaccessible: {}".format(self.vpath))
            self.uparam = {"h": True}

        if "h" in self.uparam:
            self.vpath = None
            return self.tx_mounts()

        if self.readable:
            return self.tx_browser()
        else:
            return self.tx_upper()

    def handle_post(self):
        self.log("POST " + self.req)

        try:
            if self.headers["expect"].lower() == "100-continue":
                self.s.send(b"HTTP/1.1 100 Continue\r\n\r\n")
        except KeyError:
            pass

        self.parser = MultipartParser(self.log, self.sr, self.headers)
        self.parser.parse()

        act = self.parser.require("act", 64)

        if act == "bput":
            self.handle_plain_upload()
            return

        if act == "login":
            self.handle_login()
            return

        raise Pebkac('invalid action "{}"'.format(act))

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

    def handle_plain_upload(self):
        nullwrite = self.args.nw
        vfs, rem = self.conn.auth.vfs.get(self.vpath, self.uname, False, True)

        # rem is escaped at this point,
        # this is just a sanity check to prevent any disasters
        if rem.startswith("/") or rem.startswith("../") or "/../" in rem:
            raise Exception("that was close")

        files = []
        t0 = time.time()
        for nfile, (p_field, p_file, p_data) in enumerate(self.parser.gen):
            if not p_file:
                self.log("discarding incoming file without filename")

            fn = os.devnull
            if p_file and not nullwrite:
                fn = os.path.join(vfs.realpath, rem, sanitize_fn(p_file))

                # TODO broker which avoid this race
                # and provides a new filename if taken
                if os.path.exists(fsenc(fn)):
                    fn += ".{:.6f}".format(time.time())

            with open(fn, "wb") as f:
                self.log("writing to {0}".format(fn))
                sz, sha512 = hashcopy(self.conn, p_data, f)
                if sz == 0:
                    break

                files.append([sz, sha512])

        self.parser.drop()

        td = time.time() - t0
        sz_total = sum(x[0] for x in files)
        spd = (sz_total / td) / (1024 * 1024)

        status = "OK"
        if not self.ok:
            status = "ERROR"

        msg = "{0} // {1} bytes // {2:.3f} MiB/s\n".format(status, sz_total, spd)

        for sz, sha512 in files:
            msg += "sha512: {0} // {1} bytes\n".format(sha512[:56], sz)
            # truncated SHA-512 prevents length extension attacks;
            # using SHA-512/224, optionally SHA-512/256 = :64

        html = self.conn.tpl_msg.render(
            h2='<a href="/{}">return to /{}</a>'.format(
                quotep(self.vpath), cgi.escape(self.vpath, quote=True)
            ),
            pre=msg,
        )
        self.log(msg)
        self.reply(html.encode("utf-8"))

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
                    ).encode("utf-8")
                )

    def tx_file(self, path):
        sz = os.path.getsize(fsenc(path))
        mime = mimetypes.guess_type(path)[0]
        header = "HTTP/1.1 200 OK\r\nConnection: Keep-Alive\r\nContent-Type: {}\r\nContent-Length: {}\r\n\r\n".format(
            mime, sz
        ).encode(
            "utf-8"
        )

        if self.ok:
            self.s.send(header)

        with open(fsenc(path), "rb") as f:
            while self.ok:
                buf = f.read(4096)
                if not buf:
                    break

                try:
                    self.s.send(buf)
                except ConnectionResetError:
                    return False
                    # TODO propagate (self.ok or return)

    def tx_mounts(self):
        html = self.conn.tpl_mounts.render(this=self)
        self.reply(html.encode("utf-8"))

    def tx_upper(self):
        # return html for basic uploader;
        # js rewrites to up2k unless uparam['b']
        self.loud_reply("TODO jupper {}".format(self.vpath))

    def tx_browser(self):
        vpath = ""
        vpnodes = [["/", "/"]]
        for node in self.vpath.split("/"):
            if not vpath:
                vpath = node
            else:
                vpath += "/" + node

            vpnodes.append([quotep(vpath) + "/", cgi.escape(node)])

        vn, rem = self.auth.vfs.get(self.vpath, self.uname, True, False)
        abspath = vn.canonical(rem)

        if not os.path.exists(fsenc(abspath)):
            print(abspath)
            raise Pebkac("404 not found")

        if not os.path.isdir(fsenc(abspath)):
            return self.tx_file(abspath)

        fsroot, vfs_ls, vfs_virt = vn.ls(rem, self.uname)
        vfs_ls.extend(vfs_virt)

        dirs = []
        files = []
        for fn in vfs_ls:
            href = fn
            if self.absolute_urls:
                href = vpath + "/" + fn

            fspath = fsroot + "/" + fn
            inf = os.stat(fsenc(fspath))

            is_dir = stat.S_ISDIR(inf.st_mode)
            if is_dir:
                margin = "DIR"
                href += "/"
            else:
                margin = "-"

            sz = inf.st_size
            dt = datetime.utcfromtimestamp(inf.st_mtime)
            dt = dt.strftime("%Y-%m-%d %H:%M:%S")

            item = [margin, quotep(href), cgi.escape(fn, quote=True), sz, dt]
            if is_dir:
                dirs.append(item)
            else:
                files.append(item)

        dirs.extend(files)
        html = self.conn.tpl_browser.render(
            vdir=self.vpath, vpnodes=vpnodes, files=dirs, can_upload=self.writable
        )
        self.reply(html.encode("utf-8", "replace"))

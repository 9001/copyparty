#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import os
import time
import mimetypes

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
            self.log(self.rvol)
            self.log(self.wvol)

        # split req into vpath + args
        args = {}
        if "?" not in self.req:
            vpath = undot(self.req)
        else:
            vpath, arglist = self.req.split("?", 1)
            vpath = undot(vpath)
            for k in arglist.split("&"):
                if "=" in k:
                    k, v = k.split("=", 1)
                    args[k.lower()] = v.strip()
                else:
                    args[k.lower()] = True

        self.args = args
        self.vpath = vpath

        try:
            if mode == "GET":
                self.handle_get()
            elif mode == "POST":
                self.handle_post()
            else:
                self.loud_reply(u'invalid HTTP mode "{0}"'.format(mode))

        except Pebkac as ex:
            self.loud_reply(str(ex))
            return False

        return self.ok

    def reply(self, body, status="200 OK", mime="text/html", headers=[]):
        # TODO something to reply with user-supplied values safely
        response = [
            u"HTTP/1.1 " + status,
            u"Connection: Keep-Alive",
            u"Content-Type: " + mime,
            u"Content-Length: " + str(len(body)),
        ]
        response.extend(headers)
        response_str = u"\r\n".join(response).encode("utf-8")
        if self.ok:
            self.s.send(response_str + b"\r\n\r\n" + body)

        return body

    def loud_reply(self, body, *args, **kwargs):
        self.log(body.rstrip())
        self.reply(b"<pre>" + body.encode("utf-8"), *list(args), **kwargs)

    def handle_get(self):
        self.log("")
        self.log("GET  " + self.req)

        # "embedded" resources
        if self.vpath.startswith(u".cpr"):
            static_path = os.path.join(E.mod, "web/", self.vpath[5:])

            if os.path.isfile(static_path):
                return self.tx_file(static_path)

        # conditional redirect to single volumes
        if self.vpath == "" and not self.args:
            nread = len(self.rvol)
            nwrite = len(self.wvol)
            if nread + nwrite == 1:
                if nread == 1:
                    self.vpath = self.rvol[0]
                else:
                    self.vpath = self.wvol[0]

        # go home if verboten
        readable = self.vpath in self.rvol
        writable = self.vpath in self.wvol
        if not readable and not writable:
            self.log("inaccessible: {}".format(self.vpath))
            self.args = {"h": True}

        if "h" in self.args:
            self.vpath = None
            return self.tx_mounts()

        if readable:
            return self.tx_browser()
        else:
            return self.tx_jupper()

    def handle_post(self):
        self.log("")
        self.log("POST " + self.req)

        try:
            if self.headers["expect"].lower() == "100-continue":
                self.s.send(b"HTTP/1.1 100 Continue\r\n\r\n")
        except KeyError:
            pass

        self.parser = MultipartParser(self.log, self.sr, self.headers)
        self.parser.parse()

        act = self.parser.require("act", 64)

        if act == u"bput":
            self.handle_plain_upload()
            return

        if act == u"login":
            self.handle_login()
            return

        raise Pebkac('invalid action "{}"'.format(act))

    def handle_login(self):
        pwd = self.parser.require("cppwd", 64)
        self.parser.drop()

        if pwd in self.auth.iuser:
            msg = u"login ok"
        else:
            msg = u"naw dude"
            pwd = u"x"  # nosec

        h = ["Set-Cookie: cppwd={}; Path=/".format(pwd)]
        html = u'<h1>{}<h2><a href="/">ack'.format(msg)
        self.reply(html.encode("utf-8"), headers=h)

    def handle_plain_upload(self):
        nullwrite = self.args.nw

        files = []
        t0 = time.time()
        for nfile, (p_field, p_file, p_data) in enumerate(self.parser.gen):
            fn = os.devnull
            if not nullwrite:
                fn = sanitize_fn(p_file)
                # TODO broker which avoid this race
                # and provides a new filename if taken
                if os.path.exists(fn):
                    fn += ".{:.6f}".format(time.time())

            with open(fn, "wb") as f:
                self.log("writing to {0}".format(fn))
                sz, sha512 = hashcopy(self.conn, p_data, f)
                if sz == 0:
                    break

                files.append([sz, sha512])

        td = time.time() - t0
        sz_total = sum(x[0] for x in files)
        spd = (sz_total / td) / (1024 * 1024)

        status = "OK"
        if not self.ok:
            status = "ERROR"

        msg = u"{0} // {1} bytes // {2:.3f} MiB/s\n".format(status, sz_total, spd)

        for sz, sha512 in files:
            msg += u"sha512: {0} // {1} bytes\n".format(sha512[:56], sz)
            # truncated SHA-512 prevents length extension attacks;
            # using SHA-512/224, optionally SHA-512/256 = :64

        self.loud_reply(msg)

        if not nullwrite:
            # TODO this is bad
            log_fn = "up.{:.6f}.txt".format(t0)
            with open(log_fn, "wb") as f:
                f.write(
                    (
                        u"\n".join(
                            unicode(x)
                            for x in [
                                u":".join(unicode(x) for x in self.addr),
                                msg.rstrip(),
                            ]
                        )
                        + "\n"
                    ).encode("utf-8")
                )

    def tx_file(self, path):
        sz = os.path.getsize(path)
        mime = mimetypes.guess_type(path)[0]
        header = "HTTP/1.1 200 OK\r\nConnection: Keep-Alive\r\nContent-Type: {}\r\nContent-Length: {}\r\n\r\n".format(
            mime, sz
        ).encode(
            "utf-8"
        )

        if self.ok:
            self.s.send(header)

        with open(path, "rb") as f:
            while self.ok:
                buf = f.read(4096)
                if not buf:
                    break

                self.s.send(buf)

    def tx_mounts(self):
        html = self.conn.tpl_mounts.render(this=self)
        self.reply(html.encode("utf-8"))

    def tx_jupper(self):
        self.loud_reply("TODO jupper {}".format(self.vpath))

    def tx_browser(self):
        self.loud_reply("TODO browser {}".format(self.vpath))

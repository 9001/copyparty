#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import time
import hashlib

from .__init__ import *
from .util import *

if not PY2:
    unicode = str


class HttpCli(object):
    def __init__(self, sck, addr, args, log_func):
        self.s = sck
        self.addr = addr
        self.args = args

        self.sr = Unrecv(sck)
        self.bufsz = 1024 * 32
        self.workload = 0
        self.ok = True

        self.log_func = log_func
        self.log_src = "{} \033[36m{}".format(addr[0], addr[1]).ljust(26)

    def log(self, msg):
        self.log_func(self.log_src, msg)

    def run(self):
        headerlines = self.read_header()
        if not self.ok:
            return

        self.headers = {}
        mode, self.req, _ = headerlines[0].split(" ")

        for header_line in headerlines[1:]:
            k, v = header_line.split(":", 1)
            self.headers[k.lower()] = v.strip()

        # self.bufsz = int(self.req.split('/')[-1]) * 1024

        if mode == "GET":
            self.handle_get()
        elif mode == "POST":
            self.handle_post()
        else:
            self.loud_reply(u'invalid HTTP mode "{0}"'.format(mode))

    def panic(self, msg):
        self.log("client disconnected ({0})".format(msg).upper())
        self.ok = False
        self.s.close()

    def read_header(self):
        ret = b""
        while True:
            if ret.endswith(b"\r\n\r\n"):
                break
            elif ret.endswith(b"\r\n\r"):
                n = 1
            elif ret.endswith(b"\r\n"):
                n = 2
            elif ret.endswith(b"\r"):
                n = 3
            else:
                n = 4

            buf = self.sr.recv(n)
            if not buf:
                self.panic("headers")
                break

            ret += buf

        return ret[:-4].decode("utf-8", "replace").split("\r\n")

    def reply(self, body):
        header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {0}\r\n\r\n".format(
            len(body)
        ).encode(
            "utf-8"
        )
        if self.ok:
            self.s.send(header + body)

        self.s.close()
        return body

    def loud_reply(self, body):
        self.log(body.rstrip())
        self.reply(b"<pre>" + body.encode("utf-8"))

    def handle_get(self):
        self.log("")
        self.log("GET  {0} {1}".format(self.addr[0], self.req))
        self.reply(
            b'<form method="post" enctype="multipart/form-data"><h5><input type="file" name="f" multiple><h5><input type="submit" value="start upload">'
        )

    def handle_post(self):
        self.log("")
        self.log("POST {0} {1}".format(self.addr[0], self.req))

        nullwrite = self.args.nw

        try:
            if self.headers["expect"].lower() == "100-continue":
                self.s.send(b"HTTP/1.1 100 Continue\r\n\r\n")
        except:
            pass

        form_segm = self.read_header()
        if not self.ok:
            return

        self.boundary = b"\r\n" + form_segm[0].encode("utf-8")
        for ln in form_segm[1:]:
            self.log(ln)

        fn = "/dev/null"
        fn0 = "inc.{0:.6f}".format(time.time())

        files = []
        t0 = time.time()
        for nfile in range(99):
            if not nullwrite:
                fn = "{0}.{1}".format(fn0, nfile)

            with open(fn, "wb") as f:
                self.log("writing to {0}".format(fn))
                sz, sha512 = self.handle_multipart(f)
                if sz == 0:
                    break

                files.append([sz, sha512])

            buf = self.sr.recv(2)

            if buf == b"--":
                # end of multipart
                break

            if buf != b"\r\n":
                return self.loud_reply(u"protocol error")

            header = self.read_header()
            if not self.ok:
                break

            form_segm += header
            for ln in header:
                self.log(ln)

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
            with open(fn0 + ".txt", "wb") as f:
                f.write(
                    (
                        u"\n".join(
                            unicode(x)
                            for x in [
                                u":".join(unicode(x) for x in self.addr),
                                u"\n".join(form_segm),
                                msg.rstrip(),
                            ]
                        )
                        + "\n"
                    ).encode("utf-8")
                )

    def handle_multipart(self, ofd):
        tlen = 0
        hashobj = hashlib.sha512()
        for buf in self.extract_filedata():
            tlen += len(buf)
            hashobj.update(buf)
            ofd.write(buf)

        return tlen, hashobj.hexdigest()

    def extract_filedata(self):
        u32_lim = int((2 ** 31) * 0.9)
        blen = len(self.boundary)
        bufsz = self.bufsz
        while True:
            if self.workload > u32_lim:
                # reset to prevent overflow
                self.workload = 100

            buf = self.sr.recv(bufsz)
            self.workload += 1
            if not buf:
                # abort: client disconnected
                self.panic("outer")
                return

            while True:
                ofs = buf.find(self.boundary)
                if ofs != -1:
                    self.sr.unrecv(buf[ofs + blen :])
                    yield buf[:ofs]
                    return

                d = len(buf) - blen
                if d > 0:
                    # buffer growing large; yield everything except
                    # the part at the end (maybe start of boundary)
                    yield buf[:d]
                    buf = buf[d:]

                # look for boundary near the end of the buffer
                for n in range(1, len(buf) + 1):
                    if not buf[-n:] in self.boundary:
                        n -= 1
                        break

                if n == 0 or not self.boundary.startswith(buf[-n:]):
                    # no boundary contents near the buffer edge
                    break

                if blen == n:
                    # EOF: found boundary
                    yield buf[:-n]
                    return

                buf2 = self.sr.recv(bufsz)
                self.workload += 1
                if not buf2:
                    # abort: client disconnected
                    self.panic("inner")
                    return

                buf += buf2

            yield buf

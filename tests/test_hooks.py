#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import shutil
import tempfile
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg

try:
    from typing import Optional
except:
    pass


def hdr(query):
    h = "GET /{} HTTP/1.1\r\nPW: o\r\nConnection: close\r\n\r\n"
    return h.format(query).encode("utf-8")


class TestHooks(tu.TC):
    def setUp(self):
        self.conn: Optional[tu.VHttpConn] = None
        self.td = tu.get_ramdisk()

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def reset(self):
        td = os.path.join(self.td, "vfs")
        if os.path.exists(td):
            shutil.rmtree(td)
        os.mkdir(td)
        os.chdir(td)
        return td

    def cinit(self):
        if self.conn:
            self.conn.shutdown()
            self.conn = None
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

    def test(self):
        vcfg = ["a/b/c/d:c/d:A", "a:a:r"]

        scenarios = (
            ('{"vp":"x/y"}', "c/d/a.png", "c/d/x/y/a.png"),
            ('{"vp":"x/y"}', "c/d/e/a.png", "c/d/e/x/y/a.png"),
            ('{"vp":"../x/y"}', "c/d/e/a.png", "c/d/x/y/a.png"),
            ('{"ap":"x/y"}', "c/d/a.png", "c/d/x/y/a.png"),
            ('{"ap":"x/y"}', "c/d/e/a.png", "c/d/e/x/y/a.png"),
            ('{"ap":"../x/y"}', "c/d/e/a.png", "c/d/x/y/a.png"),
            ('{"ap":"../x/y"}', "c/d/a.png", "a/b/c/x/y/a.png"),
            ('{"fn":"b.png"}', "c/d/a.png", "c/d/b.png"),
            ('{"vp":"x","fn":"b.png"}', "c/d/a.png", "c/d/x/b.png"),
        )

        for x in scenarios:
            print("\n\n\n", x)
            hooktxt, url_up, url_dl = x
            for hooktype in ("xbu", "xau"):
                for upfun in (self.put, self.bup):
                    self.reset()
                    self.makehook("""print('{"reloc":%s}')""" % (hooktxt,))
                    ka = {hooktype: ["j,c1,h.py"]}
                    self.args = Cfg(v=vcfg, a=["o:o"], e2d=True, **ka)
                    self.asrv = AuthSrv(self.args, self.log)
                    self.cinit()

                    h, b = upfun(url_up)
                    self.assertStart("HTTP/1.1 201 Created\r", h)
                    h, b = self.curl(url_dl)
                    self.assertEqual(b, "ok %s\n" % (url_up))

    def test2(self):
        hooktxt = "import sys\nopen('h%d','wb').close()\nsys.exit(%d)\n"
        for hooktype in ("xbu", "xau"):
            for upfun in (self.put, self.bup):
                self.reset()
                for n in [0, 1, 100]:
                    with open("h%d.py" % (n,), "wb") as f:
                        f.write((hooktxt % (n, n)).encode("utf-8"))
                vcfg = [
                    "012:012:A:c,H=c,h0.py:c,H=c,h1.py:c,H=c,h100.py",
                    "021:021:A:c,H=c,h0.py:c,H=c,h100.py:c,H=c,h1.py",
                    "120:120:A:c,H=c,h1.py:c,H=c,h100.py:c,H=c,h0.py",
                    "30:30:A:c,H=c,enoent.py:c,H=c,h100.py",  # not-exist
                ]
                vcfg = [x.replace("H", hooktype) for x in vcfg]
                self.args = Cfg(v=vcfg, a=["o:o"], e2d=True)
                self.asrv = AuthSrv(self.args, self.log)
                self.cinit()
                scenarios = (
                    ("012", False, True, True, False),
                    ("021", True, True, False, True),
                    ("120", False, False, True, False),
                    ("30", False, False, False, False),
                )
                for (vp, ok, h0, h1, h2) in scenarios:
                    for zs in ("h0", "h1", "h100"):
                        if os.path.exists(zs):
                            os.unlink(zs)
                    vp = "%s/f" % (vp,)
                    h, b = upfun(vp)
                    self.assertEqual(ok, os.path.exists(vp))
                    self.assertEqual(h0, os.path.exists("h0"))
                    self.assertEqual(h1, os.path.exists("h1"))
                    self.assertEqual(h2, os.path.exists("h100"))

    def makehook(self, hs):
        with open("h.py", "wb") as f:
            f.write(hs.encode("utf-8"))

    def put(self, url):
        buf = "PUT /{0} HTTP/1.1\r\nPW: o\r\nConnection: close\r\nContent-Length: {1}\r\n\r\nok {0}\n"
        buf = buf.format(url, len(url) + 4).encode("utf-8")
        print("PUT -->", buf)
        conn = self.conn.setbuf(buf)
        HttpCli(conn).run()
        ret = conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("PUT <--", ret)
        return ret

    def bup(self, url):
        hdr = "POST /%s HTTP/1.1\r\nPW: o\r\nConnection: close\r\nContent-Type: multipart/form-data; boundary=XD\r\nContent-Length: %d\r\n\r\n"
        bdy = '--XD\r\nContent-Disposition: form-data; name="act"\r\n\r\nbput\r\n--XD\r\nContent-Disposition: form-data; name="f"; filename="%s"\r\n\r\n'
        ftr = "\r\n--XD--\r\n"
        try:
            url, fn = url.rsplit("/", 1)
        except:
            fn = url
            url = ""

        buf = (bdy % (fn,) + "ok %s/%s\n" % (url, fn) + ftr).encode("utf-8")
        buf = (hdr % (url, len(buf))).encode("utf-8") + buf
        print("PoST -->", buf)
        conn = self.conn.setbuf(buf)
        HttpCli(conn).run()
        ret = conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("POST <--", ret)
        return ret

    def curl(self, url, binary=False):
        conn = self.conn.setbuf(hdr(url))
        HttpCli(conn).run()
        if binary:
            h, b = conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

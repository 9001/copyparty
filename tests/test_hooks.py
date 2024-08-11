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


def hdr(query):
    h = "GET /{} HTTP/1.1\r\nPW: o\r\nConnection: close\r\n\r\n"
    return h.format(query).encode("utf-8")


class TestHooks(unittest.TestCase):
    def setUp(self):
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

                    h, b = upfun(url_up)
                    self.assertIn("201 Created", h)
                    h, b = self.curl(url_dl)
                    self.assertEqual(b, "ok %s\n" % (url_up))

    def makehook(self, hs):
        with open("h.py", "wb") as f:
            f.write(hs.encode("utf-8"))

    def put(self, url):
        buf = "PUT /{0} HTTP/1.1\r\nPW: o\r\nConnection: close\r\nContent-Length: {1}\r\n\r\nok {0}\n"
        buf = buf.format(url, len(url) + 4).encode("utf-8")
        print("PUT -->", buf)
        conn = tu.VHttpConn(self.args, self.asrv, self.log, buf)
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
        conn = tu.VHttpConn(self.args, self.asrv, self.log, buf)
        HttpCli(conn).run()
        ret = conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("POST <--", ret)
        return ret

    def curl(self, url, binary=False):
        conn = tu.VHttpConn(self.args, self.asrv, self.log, hdr(url))
        HttpCli(conn).run()
        if binary:
            h, b = conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

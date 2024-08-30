#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import json
import os
import shutil
import tempfile
import unittest
from itertools import product

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg


class TestDedup(unittest.TestCase):
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
        quick = True  # sufficient for regular smoketests
        # quick = False

        dirnames = ["d1", "d2"]
        filenames = ["f1", "f2"]
        files = [
            (
                "one",
                "BfcDQQeKz2oG1CPSFyD5ZD1flTYm2IoCY23DqeeVgq6w",
                "XMbpLRqVdtGmgggqjUI6uSoNMTqZVX4K6zr74XA1BRKc",
            ),
            (
                "two",
                "ko1Q0eJNq3zKYs_oT83Pn8aVFgonj5G1wK8itwnYL4qj",
                "fxvihWlnQIbVbUPr--TxyV41913kPLhXPD1ngXYxDfou",
            ),
        ]
        # (data, chash, wark)

        # 3072 uploads in total
        self.ctr = 3072
        self.conn = None
        for e2d in [True, False]:
            for dn1, fn1, f1 in product(dirnames, filenames, files):
                for dn2, fn2, f2 in product(dirnames, filenames, files):
                    for dn3, fn3, f3 in product(dirnames, filenames, files):
                        self.reset()
                        if self.conn:
                            self.conn.hsrv.hub.up2k.shutdown()
                        self.args = Cfg(v=[".::A"], a=[], e2d=e2d)
                        self.asrv = AuthSrv(self.args, self.log)
                        self.conn = tu.VHttpConn(
                            self.args, self.asrv, self.log, b"", True
                        )
                        self.do_post(dn1, fn1, f1, True)
                        self.do_post(dn2, fn2, f2, False)
                        self.do_post(dn3, fn3, f3, False)
                        if quick:
                            break

    def do_post(self, dn, fn, fi, first):
        print("\n\n# do_post", self.ctr, repr((dn, fn, fi, first)))
        self.ctr -= 1

        data, chash, wark = fi
        hs = self.handshake(dn, fn, fi)
        self.assertEqual(hs["wark"], wark)

        sfn = hs["name"]
        if sfn == fn:
            print("using original name " + fn)
        else:
            print(fn + " got renamed to " + sfn)
            if first:
                raise Exception("wait what")

        if hs["hash"]:
            self.assertEqual(hs["hash"][0], chash)
            self.put_chunk(dn, wark, chash, data)
        elif first:
            raise Exception("found first; %r, %r" % ((dn, fn, fi), hs))

        h, b = self.curl("%s/%s" % (dn, sfn))
        self.assertEqual(b, data)

    def handshake(self, dn, fn, fi):
        hdr = "POST /%s/ HTTP/1.1\r\nConnection: close\r\nContent-Type: text/plain\r\nContent-Length: %d\r\n\r\n"
        msg = {"name": fn, "size": 3, "lmod": 1234567890, "life": 0, "hash": [fi[1]]}
        buf = json.dumps(msg).encode("utf-8")
        buf = (hdr % (dn, len(buf))).encode("utf-8") + buf
        print("HS -->", buf)
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("HS <--", ret)
        return json.loads(ret[1])

    def put_chunk(self, dn, wark, chash, data):
        msg = [
            "POST /%s/ HTTP/1.1" % (dn,),
            "Connection: close",
            "Content-Type: application/octet-stream",
            "Content-Length: 3",
            "X-Up2k-Hash: " + chash,
            "X-Up2k-Wark: " + wark,
            "",
            data,
        ]
        buf = "\r\n".join(msg).encode("utf-8")
        print("PUT -->", buf)
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        self.assertEqual(ret[1], "thank")

    def curl(self, url, binary=False):
        h = "GET /%s HTTP/1.1\r\nConnection: close\r\n\r\n"
        HttpCli(self.conn.setbuf((h % (url,)).encode("utf-8"))).run()
        if binary:
            h, b = self.conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

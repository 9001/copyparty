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

        # (data, chash, wark)
        self.files = [
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
            self.fstab = self.conn.hsrv.hub.up2k.fstab
            self.conn.hsrv.hub.up2k.shutdown()
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)
        if self.fstab:
            self.conn.hsrv.hub.up2k.fstab = self.fstab

    def test_a(self):
        file404 = "\nJ2EOT"
        f1, f2 = self.files
        fns = ("f1", "f2", "f3")
        dn = "d"

        self.conn = None
        self.fstab = None
        for e2d in [True, False]:
            self.args = Cfg(v=[".::A"], a=[], e2d=e2d)
            self.reset()
            self.cinit()

            # dupes in parallel
            sfn, hs = self.do_post_hs(dn, fns[0], f1, True)
            for fn in fns[1:]:
                h, b = self.handshake(dn, fn, f1)
                self.assertIn(" 422 Unpro", h)
                self.assertIn("a different location;", b)
            self.do_post_data(dn, fns[0], f1, True, sfn, hs)
            if not e2d:
                # dupesched is e2d only; hs into existence
                for fn, data in zip(fns, (f1[0], file404, file404)):
                    h, b = self.curl("%s/%s" % ("d", fn))
                    self.assertEqual(b, data)
                for fn in fns[1:]:
                    h, b = self.do_post_hs(dn, fn, f1, False)
            for fn in fns:
                h, b = self.curl("%s/%s" % ("d", fn))
                self.assertEqual(b, f1[0])

            if not e2d:
                continue

            # overwrite file
            sfn, hs = self.do_post_hs(dn, fns[0], f2, True, replace=True)
            self.do_post_data(dn, fns[0], f2, True, sfn, hs)
            for fn, f in zip(fns, (f2, f1, f1)):
                h, b = self.curl("%s/%s" % ("d", fn))
                self.assertEqual(b, f[0])

    def test(self):
        quick = True  # sufficient for regular smoketests
        # quick = False

        dirnames = ["d1", "d2"]
        filenames = ["f1", "f2"]
        files = self.files

        self.ctr = 336 if quick else 2016  # estimated total num uploads
        self.conn = None
        self.fstab = None
        for e2d in [True, False]:
            self.args = Cfg(v=[".::A"], a=[], e2d=e2d)
            for cm1 in product(dirnames, filenames, files):
                for cm2 in product(dirnames, filenames, files):
                    if cm1 == cm2:
                        continue
                    for cm3 in product(dirnames, filenames, files):
                        if cm3 in (cm1, cm2):
                            continue

                        f1 = cm1[2]
                        f2 = cm2[2]
                        f3 = cm3[2]
                        if not e2d:
                            rms = [-1]
                        elif f1 == f2:
                            if f1 == f3:
                                rms = [0, 1, 2]
                            else:
                                rms = [0, 1]
                        elif f1 == f3:
                            rms = [0, 2]
                        else:
                            rms = [1, 2]

                        for rm in rms:
                            self.do_tc(cm1, cm2, cm3, rm)

                        if quick:
                            break

    def do_tc(self, cm1, cm2, cm3, irm):
        dn1, fn1, f1 = cm1
        dn2, fn2, f2 = cm2
        dn3, fn3, f3 = cm3

        self.reset()
        self.cinit()

        fn1 = self.do_post(dn1, fn1, f1, True)
        fn2 = self.do_post(dn2, fn2, f2, False)
        fn3 = self.do_post(dn3, fn3, f3, False)

        if irm < 0:
            return

        cms = [(dn1, fn1, f1), (dn2, fn2, f2), (dn3, fn3, f3)]
        rm = cms[irm]
        dn, fn, _ = rm
        h, b = self.curl("%s/%s?delete" % (dn, fn), meth="POST")
        self.assertIn(" 200 OK", h)
        self.assertIn("deleted 1 files", b)
        h, b = self.curl("%s/%s" % (dn, fn))
        self.assertIn(" 404 Not Fo", h)
        for cm in cms:
            if cm == rm:
                continue
            dn, fn, f = cm
            h, b = self.curl("%s/%s" % (dn, fn))
            self.assertEqual(b, f[0])

    def do_post(self, dn, fn, fi, first):
        print("\n\n# do_post", self.ctr, repr((dn, fn, fi, first)))
        self.ctr -= 1
        sfn, hs = self.do_post_hs(dn, fn, fi, first)
        return self.do_post_data(dn, fn, fi, first, sfn, hs)

    def do_post_hs(self, dn, fn, fi, first, replace=False):
        h, b = self.handshake(dn, fn, fi, replace=replace)
        hs = json.loads(b)
        self.assertEqual(hs["wark"], fi[2])

        sfn = hs["name"]
        if sfn == fn:
            print("using original name " + fn)
        else:
            print(fn + " got renamed to " + sfn)
            if first:
                raise Exception("wait what")

        return sfn, hs

    def do_post_data(self, dn, fn, fi, first, sfn, hs):
        data, chash, wark = fi
        if hs["hash"]:
            self.assertEqual(hs["hash"][0], chash)
            self.put_chunk(dn, wark, chash, data)
        elif first:
            raise Exception("found first; %r, %r" % ((dn, fn, fi), hs))

        h, b = self.curl("%s/%s" % (dn, sfn))
        self.assertEqual(b, data)
        return sfn

    def handshake(self, dn, fn, fi, replace=False):
        hdr = "POST /%s/ HTTP/1.1\r\nConnection: close\r\nContent-Type: text/plain\r\nContent-Length: %d\r\n\r\n"
        msg = {"name": fn, "size": 3, "lmod": 1234567890, "life": 0, "hash": [fi[1]]}
        if replace:
            msg["replace"] = True
        buf = json.dumps(msg).encode("utf-8")
        buf = (hdr % (dn, len(buf))).encode("utf-8") + buf
        # print("HS -->", buf)
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        # print("HS <--", ret)
        return ret

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
        # print("PUT -->", buf)
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        self.assertEqual(ret[1], "thank")

    def curl(self, url, binary=False, meth=None):
        h = "%s /%s HTTP/1.1\r\nConnection: close\r\n\r\n"
        h = h % (meth or "GET", url)
        # print("CURL -->", url)
        HttpCli(self.conn.setbuf(h.encode("utf-8"))).run()
        if binary:
            h, b = self.conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

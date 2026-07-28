#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

import os
import shutil
import tempfile
import unittest
from itertools import product

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg


class TestDedup(tu.TC):
    def setUp(self):
        self.td = tu.get_ramdisk()

    def tearDown(self):
        if self.conn:
            self.conn.shutdown()
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def reset(self):
        td = os.path.join(self.td, "vfs")
        if os.path.exists(td):
            shutil.rmtree(td)
        os.mkdir(td)
        os.chdir(td)
        for a in "abc":
            os.mkdir(a)
            for b in "fg":
                d = "%s/%s%s" % (a, a, b)
                os.mkdir(d)
                for fn in "x":
                    fp = "%s/%s%s%s" % (d, a, b, fn)
                    with open(fp, "wb") as f:
                        f.write(fp.encode("utf-8"))
        return td

    def cinit(self):
        if self.conn:
            self.fstab = self.conn.hsrv.hub.up2k.fstab
            self.conn.hsrv.hub.up2k.shutdown()
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)
        if self.fstab:
            self.conn.hsrv.hub.up2k.fstab = self.fstab

    def test(self):
        tc_dedup = ["sym", "no"]
        vols = [".::A", "a/af:a/af:r", "b:a/b:r"]
        tcs = [
            "/a?copy=/c/a /a/af/afx /a/ag/agx /a/b/bf/bfx /a/b/bg/bgx /b/bf/bfx /b/bg/bgx /c/a/af/afx /c/a/ag/agx /c/a/b/bf/bfx /c/a/b/bg/bgx /c/cf/cfx /c/cg/cgx",
            "/b?copy=/d /a/af/afx /a/ag/agx /a/b/bf/bfx /a/b/bg/bgx /b/bf/bfx /b/bg/bgx /c/cf/cfx /c/cg/cgx /d/bf/bfx /d/bg/bgx",
            "/b/bf?copy=/d /a/af/afx /a/ag/agx /a/b/bf/bfx /a/b/bg/bgx /b/bf/bfx /b/bg/bgx /c/cf/cfx /c/cg/cgx /d/bfx",
            "/a/af?copy=/d /a/af/afx /a/ag/agx /a/b/bf/bfx /a/b/bg/bgx /b/bf/bfx /b/bg/bgx /c/cf/cfx /c/cg/cgx /d/afx",
            "/a/af?copy=/ /a/af/afx /a/ag/agx /a/b/bf/bfx /a/b/bg/bgx /afx /b/bf/bfx /b/bg/bgx /c/cf/cfx /c/cg/cgx",
            "/a/af/afx?copy=/afx /a/af/afx /a/ag/agx /a/b/bf/bfx /a/b/bg/bgx /afx /b/bf/bfx /b/bg/bgx /c/cf/cfx /c/cg/cgx",
        ]

        self.conn = None
        self.fstab = None
        for dedup, act_exp in product(tc_dedup, tcs):
            action, expect = act_exp.split(" ", 1)
            t = "dedup:%s  action:%s" % (dedup, action)
            print("\n\n\033[0;7m# ", t, "\033[0m")

            ka = {"dav_inf": True}
            if dedup == "hard":
                ka["hardlink"] = True
            elif dedup == "no":
                ka["no_dedup"] = True

            self.args = Cfg(v=vols, a=[], **ka)
            self.reset()
            self.cinit()

            self.do_cp(action)
            zs = self.propfind()

            fns = " ".join(zs[1])
            self.assertEqual(expect, fns)

    def do_cp(self, action):
        hdr = "POST %s HTTP/1.1\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
        buf = (hdr % (action,)).encode("utf-8")
        print("CP [%s]" % (action,))
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("CP <-- ", ret)
        self.assertStart("HTTP/1.1 201 Created\r", ret[0])
        self.assertEqual("k\r\n", ret[1])
        return ret

    def propfind(self):
        h = "PROPFIND / HTTP/1.1\r\nConnection: close\r\n\r\n"
        HttpCli(self.conn.setbuf(h.encode("utf-8"))).run()
        h, t = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        fns = t.split("<D:response><D:href>")[1:]
        fns = [x.split("</D", 1)[0] for x in fns]
        fns = [x for x in fns if not x.endswith("/")]
        fns.sort()
        return h, fns

    def log(self, src, msg, c=0):
        print(msg)

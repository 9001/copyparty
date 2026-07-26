#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

import json
import os
import shutil
import sqlite3
import tempfile
import unittest

from copyparty.__init__ import ANYWIN
from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from copyparty.util import absreal
from tests import util as tu
from tests.util import Cfg


class TestShr(unittest.TestCase):
    def log(self, src, msg, c=0):
        m = "%s" % (msg,)
        if (
            "warning: filesystem-path does not exist:" in m
            or "you are sharing a system directory:" in m
            or "symlink-based deduplication is enabled" in m
            or m.startswith("hint: argument")
        ):
            return

        print(("[%s] %s" % (src, msg)).encode("ascii", "replace").decode("ascii"))

    def assertLD(self, url, auth, els, edl):
        ls = self.ls(url, auth)
        self.assertEqual(ls[0], len(els) == 2)
        if not ls[0]:
            return
        a = [list(sorted(els[0])), list(sorted(els[1]))]
        b = [list(sorted(ls[1])), list(sorted(ls[2]))]
        self.assertEqual(a, b)

        if edl is None:
            edl = els[1]
        can_dl = []
        for fn in b[1]:
            if fn == "a.db":
                continue
            furl = url + "/" + fn
            if auth:
                furl += "?pw=p1"
            h, zb = self.curl(furl, True)
            if h.startswith("HTTP/1.1 200 "):
                can_dl.append(fn)
        self.assertEqual(edl, can_dl)

    def setUp(self):
        self.td = tu.get_ramdisk()
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)
        os.mkdir("d1")
        os.mkdir("d2")
        os.mkdir("d2/d3")
        for zs in ("d1/f1", "d2/f2", "d2/d3/f3"):
            with open(zs, "wb") as f:
                f.write(zs.encode("utf-8"))
            for dst in ("d1", "d2", "d2/d3"):
                src, fn = zs.rsplit("/", 1)
                os.symlink(absreal(zs), dst + "/l" + fn[-1:])

        db = sqlite3.connect("a.db")
        with db:
            zs = r"create table sh (k text, pw text, vp text, pr text, st int, un text, t0 int, t1 int)"
            db.execute(zs)
        db.close()

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def cinit(self):
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)

    def test1(self):
        self.args = Cfg(
            a=["u1:p1"],
            v=["::A,u1", "d1:v1:A,u1", "d2/d3:d2/d3:A,u1"],
            shr="/shr/",
            shr1="shr/",
            shr_db="a.db",
            shr_v=False,
        )
        self.cinit()

        self.assertLD("", True, [["d1", "d2", "v1"], ["a.db"]], [])
        self.assertLD("d1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("v1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("d2", True, [["d3"], ["f2", "l1", "l2", "l3"]], None)
        self.assertLD("d2/d3", True, [[], ["f3", "l1", "l2", "l3"]], None)
        self.assertLD("d3", True, [], [])

        jt = {
            "k": "r",
            "vp": ["/"],
            "pw": "",
            "exp": "99",
            "perms": ["read"],
        }
        print(self.post_json("?pw=p1&share", jt)[1])
        jt = {
            "k": "d2",
            "vp": ["/d2/"],
            "pw": "",
            "exp": "99",
            "perms": ["read"],
        }
        print(self.post_json("?pw=p1&share", jt)[1])
        self.conn.shutdown()
        self.cinit()

        self.assertLD("", True, [["d1", "d2", "v1"], ["a.db"]], [])
        self.assertLD("d1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("v1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("d2", True, [["d3"], ["f2", "l1", "l2", "l3"]], None)
        self.assertLD("d2/d3", True, [[], ["f3", "l1", "l2", "l3"]], None)
        self.assertLD("d3", True, [], [])

        self.assertLD("shr/d2", False, [[], ["f2", "l1", "l2", "l3"]], None)
        self.assertLD("shr/d2/d3", False, [], None)

        self.assertLD("shr/r", False, [["d1"], ["a.db"]], [])
        self.assertLD("shr/r/d1", False, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("shr/r/d2", False, [], None)  # unfortunate
        self.assertLD("shr/r/d2/d3", False, [], None)

        self.conn.shutdown()

    def test2(self):
        self.args = Cfg(
            a=["u1:p1"],
            v=["::A,u1", "d1:v1:A,u1", "d2/d3:d2/d3:A,u1"],
            shr="/shr/",
            shr1="shr/",
            shr_db="a.db",
            shr_v=False,
            xvol=True,
        )
        self.cinit()

        self.assertLD("", True, [["d1", "d2", "v1"], ["a.db"]], [])
        self.assertLD("d1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("v1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("d2", True, [["d3"], ["f2", "l1", "l2", "l3"]], None)
        self.assertLD("d2/d3", True, [[], ["f3", "l1", "l2", "l3"]], None)
        self.assertLD("d3", True, [], [])

        jt = {
            "k": "r",
            "vp": ["/"],
            "pw": "",
            "exp": "99",
            "perms": ["read"],
        }
        print(self.post_json("?pw=p1&share", jt)[1])
        jt = {
            "k": "d2",
            "vp": ["/d2/"],
            "pw": "",
            "exp": "99",
            "perms": ["read"],
        }
        print(self.post_json("?pw=p1&share", jt)[1])
        self.conn.shutdown()
        self.cinit()

        self.assertLD("", True, [["d1", "d2", "v1"], ["a.db"]], [])
        self.assertLD("d1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("v1", True, [[], ["f1", "l1", "l2", "l3"]], None)
        self.assertLD("d2", True, [["d3"], ["f2", "l1", "l2", "l3"]], None)
        self.assertLD("d2/d3", True, [[], ["f3", "l1", "l2", "l3"]], None)
        self.assertLD("d3", True, [], [])

        self.assertLD("shr/d2", False, [[], ["f2", "l1", "l2", "l3"]], ["f2", "l2"])
        self.assertLD("shr/d2/d3", False, [], [])

        self.assertLD("shr/r", False, [["d1"], ["a.db"]], [])
        self.assertLD(
            "shr/r/d1", False, [[], ["f1", "l1", "l2", "l3"]], ["f1", "l1", "l2"]
        )
        self.assertLD("shr/r/d2", False, [], [])  # unfortunate
        self.assertLD("shr/r/d2/d3", False, [], [])

        self.conn.shutdown()

    def ls(self, url: str, auth: bool):
        zs = url + "?ls" + ("&pw=p1" if auth else "")
        h, b = self.curl(zs)
        if not h.startswith("HTTP/1.1 200 "):
            return (False, [], [])
        jo = json.loads(b)
        return (
            True,
            [x["href"].rstrip("/") for x in jo.get("dirs") or {}],
            [x["href"] for x in jo.get("files") or {}],
        )

    def curl(self, url: str, binary=False):
        h = "GET /%s HTTP/1.1\r\nConnection: close\r\n\r\n"
        HttpCli(self.conn.setbuf((h % (url,)).encode("utf-8"))).run()
        if binary:
            h, b = self.conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def post_json(self, url: str, data):
        buf = json.dumps(data).encode("utf-8")
        msg = [
            "POST /%s HTTP/1.1" % (url,),
            "Connection: close",
            "Content-Type: application/json",
            "Content-Length: %d" % (len(buf),),
            "\r\n",
        ]
        buf = "\r\n".join(msg).encode("utf-8") + buf
        print("PUT -->", buf)
        HttpCli(self.conn.setbuf(buf)).run()
        return self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

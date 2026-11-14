#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: a share link password equal to an account password must not break reloads

import json
import os
import shutil
import sqlite3
import tempfile
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg


class TestForkShrPw(unittest.TestCase):
    def log(self, src, msg, c=0):
        pass

    def setUp(self):
        self.td = tu.get_ramdisk()
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)
        os.mkdir("d1")
        with open("d1/f1", "wb") as f:
            f.write(b"f1")

        db = sqlite3.connect("a.db")
        with db:
            zs = "create table sh (k text, pw text, vp text, pr text, st int, un text, t0 int, t1 int)"
            db.execute(zs)
        db.close()

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def cinit(self):
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)

    def run_case(self, ah_alg):
        self.args = Cfg(
            a=["alice:P"],
            v=["::A,alice"],
            shr="/shr/",
            shr1="shr/",
            shr_db="a.db",
            shr_v=False,
            ah_alg=ah_alg,
            ah_salt="test-salt",
        )
        self.cinit()
        self.assertEqual(self.status("d1/f1"), 401)
        self.assertEqual(self.status("d1/f1?pw=P"), 200)

        jt = {"k": "k1", "vp": ["/d1/"], "pw": "P", "exp": "", "perms": ["read"]}
        h, b = self.post_json("?pw=P&share", jt)
        self.assertTrue(h.startswith("HTTP/1.1 201 "), h + b)

        # live reload (what share-creation / SIGUSR1 / ?reload=cfg do)
        self.asrv.reload()
        self.check_after()

        # fresh start
        self.conn.shutdown()
        self.cinit()
        self.check_after()
        self.conn.shutdown()

    def check_after(self):
        self.assertEqual(self.status("d1/f1?pw=P"), 200)  # alice still logs in
        self.assertEqual(self.status("shr/k1/f1?pw=P"), 200)  # share opens with P
        self.assertEqual(self.status("shr/k1/f1"), 401)  # and not without it
        self.assertEqual(self.status("shr/k1/f1?pw=nope"), 401)

    def test_ah_off(self):
        self.run_case("none")

    def test_ah_on(self):
        self.run_case("sha2")

    def test_ah_off_padded(self):
        # accounts get .strip()ed later in _reload; "P " must not collide either
        self.args = Cfg(
            a=["alice:P"],
            v=["::A,alice"],
            shr="/shr/",
            shr1="shr/",
            shr_db="a.db",
            shr_v=False,
        )
        self.cinit()
        jt = {"k": "k1", "vp": ["/d1/"], "pw": "P ", "exp": "", "perms": ["read"]}
        h, b = self.post_json("?pw=P&share", jt)
        self.assertTrue(h.startswith("HTTP/1.1 201 "), h + b)
        self.asrv.reload()
        self.assertEqual(self.status("d1/f1?pw=P"), 200)
        self.assertEqual(self.status("shr/k1/f1?pw=P"), 200)
        self.conn.shutdown()

    def status(self, url):
        h = "GET /%s HTTP/1.1\r\nConnection: close\r\n\r\n"
        HttpCli(self.conn.setbuf((h % (url,)).encode("utf-8"))).run()
        return int(self.conn.s._reply.split(b" ", 2)[1])

    def post_json(self, url, data):
        buf = json.dumps(data).encode("utf-8")
        msg = [
            "POST /%s HTTP/1.1" % (url,),
            "Connection: close",
            "Content-Type: application/json",
            "Content-Length: %d" % (len(buf),),
            "\r\n",
        ]
        buf = "\r\n".join(msg).encode("utf-8") + buf
        HttpCli(self.conn.setbuf(buf)).run()
        return self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

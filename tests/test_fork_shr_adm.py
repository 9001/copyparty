#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: --shr-adm must work as a comma-separated list of exact names

import json
import os
import shutil
import sqlite3
import tempfile
import time
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from copyparty.fork_util import split_names
from tests import util as tu
from tests.util import Cfg

ACCS = ["carol:pc", "alice:pa", "bob:pb", "adm:pd", "admin:pe"]
PWS = dict(x.split(":") for x in ACCS)


class TestForkShrAdm(unittest.TestCase):
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
            zs = r"create table sh (k text, pw text, vp text, pr text, st int, un text, t0 int, t1 int)"
            db.execute(zs)
            db.execute(r"create table sf (k text, vp text)")
        db.close()

    def tearDown(self):
        self.conn.shutdown()
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def cinit(self, shr_adm):
        self.args = Cfg(
            a=ACCS,
            v=[".::rw,carol,alice,bob,adm,admin"],
            shr="/shr/",
            shr1="shr/",
            shr_db="a.db",
            shr_v=False,
            shr_adm=split_names(shr_adm),
        )
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)
        # the stub template ignores rows; list the share keys the page would show
        zs = "{% for r in rows %}{{ r[0] }}\n{% endfor %}"
        self.conn.hsrv.j2["shares"] = tu.J2_ENV.from_string(zs)

    def req(self, method, url, un, body=b"", hdrs=()):
        url += ("&" if "?" in url else "?") + "pw=" + PWS[un]
        msg = ["%s /%s HTTP/1.1" % (method, url), "Connection: close"]
        msg += list(hdrs)
        msg += ["Content-Length: %d" % (len(body),), "\r\n"]
        buf = "\r\n".join(msg).encode("utf-8") + body
        HttpCli(self.conn.setbuf(buf)).run()
        h, b = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        return int(h.split(" ")[1]), b

    def mkshare(self, k):
        jt = {"k": k, "vp": ["/d1/"], "pw": "", "exp": "99", "perms": ["read"]}
        body = json.dumps(jt).encode("utf-8")
        hdr = ["Content-Type: application/json"]
        st, b = self.req("POST", "?share", "carol", body, hdr)
        self.assertEqual(st, 201, b)

    def test_every_listed_name_can_list_and_revoke(self):
        self.cinit("alice,bob")
        self.mkshare("kalice")
        self.mkshare("kbob")

        for un, k in (("alice", "kalice"), ("bob", "kbob")):
            st, b = self.req("GET", "?shares", un)
            self.assertEqual(st, 200)
            self.assertIn(k, b, "%s cannot see carol's share" % (un,))

            st, b = self.req("POST", "?eshare=rm&skey=" + k, un)
            self.assertEqual(st, 200, "%s cannot revoke: %s" % (un, b))
            self.assertNotIn(k, self.req("GET", "?shares", "carol")[1])

        # a name not in the list still sees nothing of carol's
        self.mkshare("kcarol")
        st, b = self.req("GET", "?shares", "adm")
        self.assertNotIn("kcarol", b)

    def test_substring_of_admin_is_not_share_admin(self):
        self.cinit("admin")
        vn = self.asrv.vfs
        t0 = time.time()
        self.conn.hsrv.tdli["1.2.3.4:5"] = (t0, 9, vn, "shr/k1/f1", "carol")
        self.conn.hsrv.tdls["1.2.3.4:5"] = (t0, 0)

        def dl_path(un):
            st, b = self.req("GET", "?dls", un)
            self.assertEqual(st, 200)
            return json.loads(b)[0]["path"]

        self.assertEqual(dl_path("admin"), "shr/k1/f1")
        self.assertEqual(dl_path("adm"), "")


if __name__ == "__main__":
    unittest.main()

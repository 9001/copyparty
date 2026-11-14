#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: grants, an owner gives a named account access to a folder (ticket 06)

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

ACCS = ["alice:alice", "bob:bob", "carol:carol"]


class TestForkGrants(unittest.TestCase):
    def log(self, src, msg, c=0):
        pass

    def setUp(self):
        self.conn = None
        self.td = tu.get_ramdisk()
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)
        for fp in ("a/proj/f.txt", "a/proj/.env", "a/proj/s/g.txt", "a/priv.txt"):
            dp = os.path.dirname(fp)
            if not os.path.isdir(dp):
                os.makedirs(dp)
            with open(fp, "wb") as f:
                f.write(fp.encode("utf-8"))

    def tearDown(self):
        if self.conn:
            self.conn.shutdown()
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def cinit(self, grants="/shared", v=None, **ka):
        self.args = Cfg(
            a=ACCS,
            v=v or ["a:home/alice:A,alice"],
            grants=grants,
            grants_db="g.db",
            **ka
        )
        self.reload()

    def reload(self):
        if self.conn:
            self.conn.shutdown()
            self.conn = None
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)

    def req(self, method, url, uname, extra="", body=b""):
        h = "%s /%s HTTP/1.1\r\nPW: %s\r\nConnection: close\r\n%s\r\n"
        buf = (h % (method, url, uname, extra)).encode("utf-8") + body
        HttpCli(self.conn.setbuf(buf)).run()
        h, b = self.conn.s._reply.split(b"\r\n\r\n", 1)
        return int(h.split(b" ", 2)[1]), b

    def get(self, url, uname):
        return self.req("GET", url, uname)

    def grant(self, vp="/home/alice/proj/", rcpt="bob", name="proj", uname="alice"):
        jt = {"vp": vp, "rcpt": rcpt, "name": name, "perms": ["read"]}
        buf = json.dumps(jt).encode("utf-8")
        hdr = "Content-Type: application/json\r\nContent-Length: %d\r\n" % (len(buf),)
        st, b = self.req("POST", "?grant", uname, hdr, buf)
        if st == 201:
            self.reload()  # what the broker's reload does in a real server
        return st, b

    def ls(self, url, uname):
        """names in a folder listing, folders with a trailing slash"""
        st, b = self.get(url + "?ls", uname)
        if st != 200:
            return st
        jo = json.loads(b)
        dirs = [x["href"] for x in jo["dirs"]]
        return sorted(dirs + [x["href"] for x in jo["files"]])

    def test_recipient_browses_and_downloads(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        self.assertEqual(self.ls("shared/", "bob"), ["alice/"])
        self.assertEqual(self.ls("shared/alice/", "bob"), ["proj/"])
        self.assertEqual(self.ls("shared/alice/proj/", "bob"), ["f.txt", "s/"])
        self.assertEqual(
            self.get("shared/alice/proj/f.txt", "bob"), (200, b"a/proj/f.txt")
        )
        self.assertEqual(
            self.get("shared/alice/proj/s/g.txt", "bob"), (200, b"a/proj/s/g.txt")
        )
        self.assertIn("shared/", self.ls("", "bob"))

    def test_others_see_nothing(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        for un in ("carol", "*"):
            self.assertNotIn("shared/", self.ls("", un) or [], un)
            self.assertIn(self.ls("shared/", un), (401, 403, 404), un)
            self.assertIn(self.ls("shared/alice/", un), (401, 403, 404), un)
            st, b = self.get("shared/alice/proj/f.txt", un)
            self.assertIn(st, (401, 403, 404), un)
            self.assertNotIn(b"a/proj", b, un)

    def test_webdav(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        hdr = "Depth: 1\r\n"
        for url, want in [
            ("", b"shared"),
            ("shared/", b"alice"),
            ("shared/alice/", b"proj"),
            ("shared/alice/proj/", b"f.txt"),
        ]:
            st, b = self.req("PROPFIND", url, "bob", hdr)
            self.assertEqual(st, 207, url)
            self.assertIn(want, b, url)
            self.assertNotIn(b".env", b, url)

        dav = "User-Agent: Microsoft-WebDAV-MiniRedir/10.0\r\n"
        st, b = self.req("GET", "shared/alice/proj/f.txt", "bob", dav)
        self.assertEqual((st, b), (200, b"a/proj/f.txt"))
        st, b = self.req("PROPFIND", "shared/alice/proj/", "carol", hdr)
        self.assertIn(st, (401, 403, 404))

    def test_same_name_to_two_recipients(self):
        # alice -> bob "proj" is one folder, alice -> carol "proj" another
        os.makedirs("a/other")
        with open("a/other/o.txt", "wb") as f:
            f.write(b"a/other/o.txt")
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        self.assertEqual(self.grant(vp="/home/alice/other/", rcpt="carol")[0], 201)

        self.assertEqual(self.ls("shared/alice/proj/", "bob"), ["f.txt", "s/"])
        self.assertEqual(self.ls("shared/alice/proj/", "carol"), ["o.txt"])
        url = "shared/alice/proj/"
        self.assertEqual(self.get(url + "f.txt", "bob"), (200, b"a/proj/f.txt"))
        self.assertEqual(self.get(url + "o.txt", "carol"), (200, b"a/other/o.txt"))
        self.assertIn(self.get(url + "o.txt", "bob")[0], (403, 404))
        self.assertIn(self.get(url + "f.txt", "carol")[0], (403, 404))
        for un in ("bob", "carol"):
            self.assertEqual(self.ls("shared/", un), ["alice/"], un)
            self.assertEqual(self.ls("shared/alice/", un), ["proj/"], un)
            self.assertIn("shared/", self.ls("", un), un)

        hdr = "Depth: 1\r\n"
        st, b = self.req("PROPFIND", url, "carol", hdr)
        self.assertEqual(st, 207)
        self.assertIn(b"o.txt", b)
        self.assertNotIn(b"f.txt", b)

        vfs = self.asrv.vfs
        self.assertEqual(vfs.get(url + "f.txt", "bob", True, False)[1], "f.txt")
        self.assertEqual(vfs.get(url + "o.txt", "carol", True, False)[1], "o.txt")
        self.assertEqual(vfs.get(url, "carol", True, False)[0].realpath, os.path.abspath("a/other"))
        with self.assertRaises(Exception):
            vfs.get(url + "f.txt", "guest", True, False)
        self.assertEqual(vfs.get_perms(url + "o.txt", "carol"), "rg")
        self.assertEqual(vfs.get_perms(url, "bob"), "rg")
        self.assertEqual(vfs.get_perms(url, "*"), "")

    def test_dotfiles_always_404(self):
        # harden off, and alice holds `.` (via A) on the source
        self.cinit()
        self.assertEqual(self.get("home/alice/proj/.env", "alice")[0], 200)
        self.assertEqual(self.grant()[0], 201)
        dav = "User-Agent: Microsoft-WebDAV-MiniRedir/10.0\r\n"
        self.assertEqual(self.get("shared/alice/proj/.env", "bob")[0], 404)
        self.assertEqual(self.req("GET", "shared/alice/proj/.env", "bob", dav)[0], 404)
        hdr = "Depth: 1\r\nCookie: dots=1\r\n"
        st, b = self.req("PROPFIND", "shared/alice/proj/", "bob", hdr)
        self.assertNotIn(b".env", b)
        _, b = self.get("shared/alice/proj/?ls&dots", "bob")
        self.assertNotIn(b".env", b)

    def test_dotfiles_404_with_harden(self):
        self.cinit(harden=True)
        self.assertEqual(self.grant()[0], 201)
        self.assertEqual(self.get("shared/alice/proj/.env", "bob")[0], 404)
        self.assertEqual(self.get("shared/alice/proj/f.txt", "bob")[0], 200)

    def test_dot_source_refused(self):
        # alice holds `.`, but a grant must never open a hidden folder
        os.makedirs("a/proj/.git")
        with open("a/proj/.git/config", "wb") as f:
            f.write(b"secret")
        self.cinit()
        st, b = self.grant(vp="/home/alice/proj/.git/", name="g")
        self.assertEqual(st, 400)
        self.assertIn(self.get("shared/alice/g/config", "bob")[0], (403, 404))

        # a row that got in some other way is not mounted either
        self.assertEqual(self.grant()[0], 201)
        db = sqlite3.connect("g.db")
        db.execute("update gr set vp='home/alice/proj/.git'")
        db.commit()
        db.close()
        self.reload()
        self.assertIn(self.get("shared/alice/proj/config", "bob")[0], (403, 404))

    def test_no_regrant_through_shared(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        st, _ = self.grant(vp="/shared/alice/proj/", rcpt="carol", uname="bob")
        self.assertEqual(st, 400)

    def test_grants_off(self):
        self.cinit(grants="")
        st, b = self.grant()
        self.assertEqual(st, 400)
        self.assertIn(b"grants are disabled", b)
        self.assertFalse(os.path.exists("g.db"))
        self.assertNotIn("shared/", self.ls("", "bob") or [])
        self.assertIn(self.get("shared/alice/proj/f.txt", "bob")[0], (403, 404))

    def test_without_share_links(self):
        self.cinit(shr="", shr1="")
        self.assertEqual(self.grant()[0], 201)
        self.assertEqual(
            self.get("shared/alice/proj/f.txt", "bob"), (200, b"a/proj/f.txt")
        )

    def test_with_share_links(self):
        db = sqlite3.connect("s.db")
        with db:
            db.execute(
                "create table sh (k text, pw text, vp text, pr text, st int, un text, t0 int, t1 int)"
            )
            db.execute("create table sf (k text, vp text)")
        db.close()
        self.cinit(shr="/shr/", shr1="shr/", shr_db="s.db", shr_v=False)
        self.assertEqual(self.grant()[0], 201)
        self.assertEqual(
            self.get("shared/alice/proj/f.txt", "bob"), (200, b"a/proj/f.txt")
        )

    def test_path_lookup(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        vfs = self.asrv.vfs
        vn, rem = vfs.get("shared/alice/proj/s/g.txt", "bob", True, False)
        self.assertEqual(vn.vpath, "shared/alice/proj")
        self.assertEqual(rem, "s/g.txt")
        with self.assertRaises(Exception) as cm:
            vfs.get("shared/alice/proj/s/g.txt", "carol", True, False)
        self.assertEqual(cm.exception.code, 403)
        with self.assertRaises(Exception) as cm:
            vfs.get("shared/alice/proj/.env", "bob", True, False)
        self.assertEqual(cm.exception.code, 404)
        with self.assertRaises(Exception) as cm:
            vfs.get("shared/alice/proj/f.txt", "bob", True, True)  # no upload
        self.assertEqual(cm.exception.code, 403)

    def test_under_a_readable_root(self):
        os.mkdir("pub")
        self.cinit(v=["pub::r", "a:home/alice:A,alice"])
        self.assertEqual(self.grant()[0], 201)
        # known gap: upstream leaves folders without a path on disk out of a
        # real folder's listing, so `/` doesn't show shared/ here
        self.assertEqual(self.ls("shared/", "bob"), ["alice/"])
        self.assertIn(self.ls("shared/", "carol"), (401, 403, 404))
        self.assertEqual(self.ls("shared/alice/proj/", "bob"), ["f.txt", "s/"])

    def test_db_has_a_version(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        db = sqlite3.connect("g.db")
        self.assertEqual(db.execute("select v from kv where k='sver'").fetchall(), [(1,)])
        db.execute("update kv set v=2 where k='sver'")
        db.commit()
        db.close()
        with self.assertRaises(Exception) as cm:
            self.reload()
        self.assertIn("grants-db v1 and older", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

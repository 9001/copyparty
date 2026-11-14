#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: grants, an owner gives a named account access to a folder (ticket 06)

import json
import os
import re
import shutil
import sqlite3
import tempfile
import time
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg

ACCS = ["alice:alice", "bob:bob", "carol:carol"]


class TestForkGrants(unittest.TestCase):
    def log(self, src, msg, c=0):
        self.logs.append(msg)

    def setUp(self):
        self.conn = None
        self.logs = []
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

    def grant(
        self, vp="/home/alice/proj/", rcpt="bob", name="proj", uname="alice", perms=("read",), **ka
    ):
        jt = {"vp": vp, "rcpt": rcpt, "name": name, "perms": list(perms)}
        jt.update(ka)
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

    def cinit_shr(self, **ka):
        db = sqlite3.connect("s.db")
        with db:
            db.execute(
                "create table sh (k text, pw text, vp text, pr text, st int, un text, t0 int, t1 int)"
            )
            db.execute("create table sf (k text, vp text)")
        db.close()
        self.cinit(shr="/shr/", shr1="shr/", shr_db="s.db", shr_v=False, **ka)

    def share(self, vp, uname="alice", key="abcdefghijkl", pw=""):
        jt = {"k": key, "vp": [vp], "pw": pw, "exp": "99", "perms": ["read"]}
        buf = json.dumps(jt).encode("utf-8")
        hdr = "Content-Type: application/json\r\nContent-Length: %d\r\n" % (len(buf),)
        st, b = self.req("POST", "?share", uname, hdr, buf)
        if st == 201:
            self.reload()
        return st, b

    def test_with_share_links(self):
        self.cinit_shr()
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

    # rights (ticket 07)

    def put(self, url, uname, buf=b"put"):
        hdr = "Content-Type: application/octet-stream\r\nContent-Length: %d\r\n" % (len(buf),)
        return self.req("PUT", url, uname, hdr, buf)

    def test_read_upload_grant(self):
        self.cinit()
        self.assertEqual(self.grant(perms=("read", "write"))[0], 201)
        self.assertEqual(self.put("shared/alice/proj/new.txt", "bob")[0], 201)
        with open("a/proj/new.txt", "rb") as f:
            self.assertEqual(f.read(), b"put")
        self.assertEqual(self.get("shared/alice/proj/new.txt", "bob"), (200, b"put"))

    def test_read_only_grant_refuses_uploads(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        self.assertIn(self.put("shared/alice/proj/new.txt", "bob")[0], (401, 403))
        self.assertFalse(os.path.exists("a/proj/new.txt"))

    def test_only_read_and_upload_can_be_granted(self):
        self.cinit()
        for perms in (
            (),
            ("write",),
            ("read", "move"),
            ("read", "delete"),
            ("read", "admin"),
            ("read", "write", "move", "delete"),
            ("read", "get"),
            ("read", "dot"),
            "read",
        ):
            st, b = self.grant(perms=perms)
            self.assertEqual(st, 400, perms)
            self.assertIn(b"read-only", b, perms)
        self.assertFalse(os.path.exists("g.db"))

    def test_no_move_or_delete_through_a_grant(self):
        self.cinit()
        self.assertEqual(self.grant(perms=("read", "write"))[0], 201)
        url = "shared/alice/proj/f.txt"
        dst = "Destination: /shared/alice/proj/g.txt\r\n"
        for method, u, hdr in [
            ("DELETE", url, ""),
            ("POST", url + "?delete", "Content-Length: 0\r\n"),
            ("POST", url + "?move=/shared/alice/proj/g.txt", "Content-Length: 0\r\n"),
            ("MOVE", url, dst),
        ]:
            st, b = self.req(method, u, "bob", hdr)
            self.assertIn(st, (401, 403, 404), (method, u, b))
            self.assertTrue(os.path.exists("a/proj/f.txt"), (method, u))
            self.assertFalse(os.path.exists("a/proj/g.txt"), (method, u))

        self.assertEqual(self.asrv.vfs.get_perms("shared/alice/proj/", "bob"), "rwg")
        for ka in ({"will_move": True}, {"will_del": True}):
            with self.assertRaises(Exception):
                self.asrv.vfs.get("shared/alice/proj/f.txt", "bob", True, False, **ka)

    # refusals at create (ticket 07)

    def n_grants(self):
        if not os.path.exists("g.db"):
            return 0
        db = sqlite3.connect("g.db")
        try:
            return db.execute("select count(*) from gr").fetchall()[0][0]
        finally:
            db.close()

    def refused(self, msg, **ka):
        n = self.n_grants()
        st, b = self.grant(**ka)
        self.assertEqual(st, 400, b)
        self.assertIn(msg, b)
        self.assertEqual(self.n_grants(), n)

    def test_refused_rights_the_owner_lacks(self):
        os.makedirs("ro/d")
        self.cinit(v=["a:home/alice:A,alice", "ro:ro:r,alice"])
        self.refused(b"you dont have all the perms", vp="/ro/d/", perms=("read", "write"))
        self.refused(b"you dont have all the perms", vp="/home/alice/proj/", uname="carol")
        self.assertEqual(self.grant(vp="/ro/d/", name="d")[0], 201)

    def test_refused_under_shared(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        for vp in ("/shared/alice/proj/", "/shared/alice/proj/s/", "/shared/", "shared", "/x/../shared/alice/proj/"):
            self.refused(b"granted folder", vp=vp, rcpt="carol", uname="bob", name="x")

    def test_refused_under_share_links(self):
        self.cinit_shr()
        self.assertEqual(self.share("/home/alice/proj/")[0], 201)
        self.assertEqual(self.get("shr/abcdefghijkl/f.txt", "*"), (200, b"a/proj/f.txt"))
        for vp in ("/shr/abcdefghijkl/", "/shr/abcdefghijkl/s/", "/shr/", "/home/../shr/abcdefghijkl/"):
            self.refused(b"share link", vp=vp, name="x")

    def test_no_share_link_of_a_grant(self):
        self.cinit_shr()
        self.assertEqual(self.grant()[0], 201)
        st, b = self.share("/shared/alice/proj/", uname="bob")
        self.assertEqual(st, 400, b)
        self.assertIn(self.get("shr/abcdefghijkl/f.txt", "*")[0], (401, 403, 404))

    def test_grant_who_no(self):
        # grants forbidden, share links allowed, on the same volume
        self.cinit_shr(v=["a:home/alice:A,alice:c,grant_who=no"])
        self.refused(b"perms to create grants from this volume")
        self.assertEqual(self.share("/home/alice/proj/")[0], 201)

    def test_grant_who_a(self):
        os.makedirs("t/d")
        self.cinit(v=["t:t:r,alice:A,carol:c,grant_who=a"])
        self.refused(b"perms to create grants from this volume", vp="/t/d/", name="d")
        self.assertEqual(self.grant(vp="/t/d/", name="d", uname="carol")[0], 201)
        self.assertEqual(self.ls("shared/carol/d/", "bob"), [])

    def test_grant_who_auth_is_the_default(self):
        os.makedirs("t/d")
        self.cinit(v=["t:t:r,alice:A,carol"])
        self.assertEqual(self.grant(vp="/t/d/", name="d")[0], 201)

    def test_grants_allowed_with_share_links_forbidden(self):
        self.cinit_shr(v=["a:home/alice:A,alice:c,shr_who=no"])
        st, b = self.share("/home/alice/proj/")
        self.assertEqual(st, 400, b)
        self.assertEqual(self.grant()[0], 201)
        self.assertEqual(self.get("shared/alice/proj/f.txt", "bob"), (200, b"a/proj/f.txt"))

    def test_grant_who_unknown_value_refuses(self):
        self.cinit(v=["a:home/alice:A,alice:c,grant_who=yes"])
        self.refused(b"perms to create grants from this volume")

    def test_refused_unknown_recipient(self):
        self.cinit()
        for rcpt in ("dave", "Bob", "", "bob ", "s_abc"):
            self.refused(b"no such recipient", rcpt=rcpt)

    def test_refused_to_self(self):
        self.cinit()
        self.refused(b"yourself", rcpt="alice")

    def test_refused_to_all_accounts(self):
        self.cinit()
        for rcpt in ("@acct", "*"):
            self.refused(b"every account", rcpt=rcpt)

    def test_refused_unsafe_name(self):
        self.cinit()
        for name in ("", ".", "..", ".x", "a/b", "/a", "a\\b", "a\x00b", "a\nb", " a", "a ", "x" * 256):
            self.refused(b"the name must be", name=name)
        for name in ("trip-2026", "a b", "\u00e6\u00f8\u00e5", "x" * 255):
            self.assertEqual(self.grant(name=name)[0], 201, name)

    def check_share_pw_refused(self, pw):
        # a share link with a password logs in as a made-up s_... account;
        # granting to it would hand the grant to everyone with that password
        self.cinit_shr()
        self.assertEqual(self.share("/home/alice/proj/s/", pw=pw)[0], 201)
        sun = [x for x in self.asrv.acct if x.startswith("s_")]
        self.assertEqual(len(sun), 1)
        self.refused(b"no such recipient", rcpt=sun[0])

        # nor is a row naming one mounted
        self.assertEqual(self.grant()[0], 201)
        db = sqlite3.connect("g.db")
        db.execute("update gr set rcpt=?", (sun[0],))
        db.commit()
        db.close()
        self.reload()
        url = "shared/alice/proj/f.txt?pw=%s" % (pw.strip(),)
        self.assertIn(self.get(url, "*")[0], (401, 403, 404))

    def test_refused_to_a_share_link_password(self):
        self.check_share_pw_refused("hunter2")

    def test_refused_to_a_padded_share_link_password(self):
        # the loader names the account from the raw password, then strips it
        self.check_share_pw_refused(" hunter2 ")

    def test_refused_single_file(self):
        self.cinit()
        self.refused(b"only folders", vp="/home/alice/priv.txt")
        self.refused(b"only folders", vp="/home/alice/nope/")

    def test_refused_file_selection(self):
        self.cinit()
        self.refused(b"only folders", files=["f.txt"])
        self.refused(b"only folders", vp=["/home/alice/proj/f.txt", "/home/alice/proj/s/g.txt"])
        self.refused(b"only folders", vp=["/home/alice/proj/"])

    def test_refused_same_owner_recipient_name(self):
        os.makedirs("a/other")
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        self.refused(b"already", vp="/home/alice/other/")
        self.refused(b"already", perms=("read", "write"))
        # another recipient, or another name, is fine
        self.assertEqual(self.grant(rcpt="carol")[0], 201)
        self.assertEqual(self.grant(vp="/home/alice/other/", name="other")[0], 201)
        self.assertEqual(self.ls("shared/alice/", "bob"), ["other/", "proj/"])

    # group grants (ticket 08)

    def ginit(self, *grp, **ka):
        self.cinit(grp=list(grp or ["family:alice,bob"]), **ka)

    def regroup(self, *grp):
        """edit [groups] in the config, then reload"""
        self.args.grp = list(grp)
        self.reload()

    def can_read(self, uname):
        return self.get("shared/alice/proj/f.txt", uname) == (200, b"a/proj/f.txt")

    def test_group_members_see_it(self):
        self.ginit("family:alice,bob,dave")
        self.assertEqual(self.grant(rcpt="@family")[0], 201)
        self.assertEqual(self.ls("shared/alice/", "bob"), ["proj/"])
        self.assertTrue(self.can_read("bob"))
        for un in ("carol", "*"):
            self.assertFalse(self.can_read(un), un)
            self.assertNotIn("shared/", self.ls("", un) or [], un)
        # the owner, though a member, gets no mount of their own folder
        self.assertNotIn("shared/", self.ls("", "alice"))

    def test_group_refusals(self):
        self.ginit()
        for rcpt in ("@nope", "@Family", "@", "@family ", "family"):
            self.assertEqual(self.grant(rcpt=rcpt)[0], 400, rcpt)
        self.refused(b"no such group", rcpt="@nope")
        self.refused(b"every account", rcpt="@acct")

    def test_renamed_all_accounts_group_refused(self):
        self.ginit()
        self.args.grp_all = "everyone"
        self.reload()
        self.refused(b"every account", rcpt="@everyone")
        self.refused(b"no such group", rcpt="@acct")

    def test_group_membership_follows_the_config(self):
        self.ginit()
        self.assertEqual(self.grant(rcpt="@family")[0], 201)
        self.assertTrue(self.can_read("bob"))
        self.assertFalse(self.can_read("carol"))

        self.regroup("family:alice,bob,carol")
        self.assertTrue(self.can_read("bob"))
        self.assertTrue(self.can_read("carol"))
        self.assertEqual(self.ls("shared/alice/", "carol"), ["proj/"])

        self.regroup("family:alice,carol")
        self.assertFalse(self.can_read("bob"))
        self.assertNotIn("shared/", self.ls("", "bob"))
        self.assertTrue(self.can_read("carol"))

    def test_group_removed_from_the_config(self):
        self.ginit()
        self.assertEqual(self.grant(rcpt="@family")[0], 201)
        self.regroup()
        self.assertFalse(self.can_read("bob"))
        self.assertNotIn("shared/", self.ls("", "bob"))
        # still on the owner's page
        self.assertEqual(self.states("alice"), {1: "no members"})

        # a group by that name later gets the grant, as the owner left it
        self.regroup("family:carol")
        self.assertTrue(self.can_read("carol"))
        self.assertFalse(self.can_read("bob"))

    def test_overlap_with_a_direct_grant_refused(self):
        # bob is in @family: a "proj" to both would be two folders in one place
        os.makedirs("a/other")
        self.ginit()
        self.assertEqual(self.grant()[0], 201)
        self.refused(b"already", vp="/home/alice/other/", rcpt="@family")
        self.assertEqual(self.grant(vp="/home/alice/other/", rcpt="@family", name="other")[0], 201)
        self.refused(b"already", rcpt="@family", name="other")
        self.refused(b"already", vp="/home/alice/other/", rcpt="bob", name="other")
        # carol is in no group with bob, so her "proj" is fine
        self.assertEqual(self.grant(vp="/home/alice/other/", rcpt="carol")[0], 201)

    def test_overlap_between_groups_refused(self):
        self.ginit("family:alice,bob", "friends:bob,carol", "work:carol")
        self.assertEqual(self.grant(rcpt="@family")[0], 201)
        self.refused(b"already", rcpt="@friends")
        self.assertEqual(self.grant(rcpt="@work")[0], 201)

    def test_groups_sharing_only_the_owner_dont_overlap(self):
        self.ginit("family:alice,bob", "work:alice,carol")
        self.assertEqual(self.grant(rcpt="@family")[0], 201)
        self.assertEqual(self.grant(rcpt="@work")[0], 201)

    def test_overlap_after_a_group_change_keeps_the_oldest(self):
        os.makedirs("a/other")
        with open("a/other/o.txt", "wb") as f:
            f.write(b"a/other/o.txt")
        self.ginit()
        self.assertEqual(self.grant(rcpt="@family")[0], 201)
        self.assertEqual(self.grant(vp="/home/alice/other/", rcpt="carol")[0], 201)
        self.regroup("family:alice,bob,carol")
        # carol's own "proj", named for her, beats the group's
        self.assertEqual(self.ls("shared/alice/", "carol"), ["proj/"])
        self.assertEqual(self.ls("shared/alice/proj/", "carol"), ["o.txt"])
        self.assertTrue(self.can_read("bob"))

    # upload rules inside a grant (ticket 07); the same ways in as
    # tests/test_fork_harden_shr.py, as bob

    UP2K_FILE = (
        "one",
        "BfcDQQeKz2oG1CPSFyD5ZD1flTYm2IoCY23DqeeVgq6w",
        "XMbpLRqVdtGmgggqjUI6uSoNMTqZVX4K6zr74XA1BRKc",
    )

    def body(self, method, url, uname, buf, ctype, extra=""):
        extra += "Content-Type: %s\r\nContent-Length: %d\r\n" % (ctype, len(buf))
        return self.req(method, url, uname, extra, buf)

    def form(self, url, uname, fields):
        buf = ""
        for name, fname, val in fields:
            cd = 'form-data; name="%s"' % (name,)
            if fname:
                cd += '; filename="%s"' % (fname,)
            buf += "--XD\r\nContent-Disposition: %s\r\n\r\n%s\r\n" % (cd, val)
        buf += "--XD--\r\n"
        return self.body("POST", url, uname, buf.encode("utf-8"), "multipart/form-data; boundary=XD")

    def up_put(self, dn, fn, un):
        return self.put(dn + "/" + fn, un)

    def up_bput(self, dn, fn, un):
        return self.form(dn + "/", un, [("act", None, "bput"), ("f", fn, "mp")])

    def up_new_md(self, dn, fn, un):
        return self.form(dn + "/", un, [("act", None, "new_md"), ("name", None, fn)])

    def up_tput(self, dn, fn, un):
        fields = [("act", None, "tput"), ("lastmod", None, "0"), ("body", None, "md")]
        return self.form(dn + "/" + fn, un, fields)

    def up_dav_copy(self, dn, fn, un):
        hdr = "Destination: /%s/%s\r\nContent-Length: 0\r\n" % (dn, fn)
        return self.req("COPY", dn + "/f.txt", un, hdr)

    def up_copy(self, dn, fn, un):
        url = "%s/f.txt?copy=/%s/%s" % (dn, dn, fn)
        return self.req("POST", url, un, "Content-Length: 0\r\n")

    def up_up2k(self, dn, fn, un):
        data, chash, wark = self.UP2K_FILE
        msg = {"name": fn, "size": 3, "lmod": 1234567890, "life": 0, "hash": [chash]}
        buf = json.dumps(msg).encode("utf-8")
        st, b = self.body("POST", dn + "/", un, buf, "text/plain")
        if st != 200:
            return st, b
        if json.loads(b)["hash"]:
            hdr = "X-Up2k-Hash: %s\r\nX-Up2k-Wark: %s\r\n" % (chash, wark)
            st, b = self.body("POST", dn + "/", un, data.encode(), "application/octet-stream", hdr)
        return st, b

    UPLOADS = ("put", "bput", "up2k", "new_md", "tput", "dav_copy", "copy")
    REFUSED = ("README.md", "readme.MD", "PREADME.md", "pReadMe.Md", "descript.ion", "DESCRIPT.ION", ".new", ".epilogue.html")

    def check_upload_names(self, **ka):
        self.cinit(**ka)
        self.assertEqual(self.grant(perms=("read", "write"))[0], 201)
        for way in self.UPLOADS:
            up = getattr(self, "up_" + way)
            for fn in self.REFUSED:
                st, b = up("shared/alice/proj", fn, "bob")
                self.assertGreaterEqual(st, 400, (way, fn, b))
                self.assertFalse(os.path.exists("a/proj/" + fn), (way, fn))

            fn = "ok-%s.md" % (way,)
            st, b = up("shared/alice/proj", fn, "bob")
            self.assertLess(st, 400, (way, b))
            self.assertTrue(os.path.exists("a/proj/" + fn), way)

        # alice, through her own volume, still can
        for fn in ("README.md", "descript.ion", ".new"):
            self.assertEqual(self.put("home/alice/proj/" + fn, "alice")[0], 201, fn)
            self.assertTrue(os.path.exists("a/proj/" + fn), fn)

    def test_upload_names_harden_off(self):
        self.check_upload_names()

    def test_upload_names_harden_on(self):
        self.check_upload_names(harden=True)


    # grant lifetime across reloads (ticket 09)

    def db_exec(self, q, *a):
        db = sqlite3.connect("g.db")
        try:
            db.execute(q, a)
            db.commit()
        finally:
            db.close()

    def test_expiry_ends_access(self):
        self.cinit()
        self.assertEqual(self.grant(exp=60)[0], 201)
        self.assertTrue(self.can_read("bob"))
        # half an hour later, as the server sees it
        self.db_exec("update gr set t1 = t1 - 1800")
        self.reload()
        self.assertTrue(self.can_read("bob"))
        # and past the hour
        self.db_exec("update gr set t1 = t1 - 1801")
        self.reload()
        self.assertFalse(self.can_read("bob"))
        self.assertNotIn("shared/", self.ls("", "bob"))

    def test_no_expiry_by_default(self):
        self.cinit()
        for exp in ({}, {"exp": None}, {"exp": ""}, {"exp": 0}, {"exp": "0"}):
            self.logs = []
            self.assertEqual(self.grant(**exp)[0], 201, exp)
            zsl = [x for x in self.logs if x.startswith("created grant ")]
            self.assertEqual(len(zsl), 1, exp)
            self.assertIn("expires never", zsl[0], exp)
            self.db_exec("delete from gr")

    def test_expiry_refusals(self):
        self.cinit()
        for exp in (-1, "x", 1.5, 0.0, False, True, [1], "1e3", 10**10):
            self.refused(b"expiry", exp=exp)


    def test_suspended_while_the_owner_lacks_rights(self):
        os.makedirs("fam/pics")
        with open("fam/pics/p.jpg", "wb") as f:
            f.write(b"fam/pics/p.jpg")
        v = ["a:home/alice:A,alice", "fam:family:r,@family"]
        self.ginit("family:alice,carol", v=v)
        self.assertEqual(self.grant(vp="/family/pics/", name="pics")[0], 201)
        url = "shared/alice/pics/p.jpg"
        self.assertEqual(self.get(url, "bob"), (200, b"fam/pics/p.jpg"))

        self.regroup("family:carol")
        self.assertIn(self.get(url, "bob")[0], (403, 404))
        self.assertNotIn("shared/", self.ls("", "bob"))
        self.assertEqual(self.n_grants(), 1)

        self.regroup("family:alice,carol")
        self.assertEqual(self.get(url, "bob"), (200, b"fam/pics/p.jpg"))

    def test_broken_while_the_source_is_gone(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        os.rename("a/proj", "a/proj2")
        self.reload()
        self.assertFalse(self.can_read("bob"))
        self.assertNotIn("shared/", self.ls("", "bob"))
        self.assertEqual(self.n_grants(), 1)

        os.rename("a/proj2", "a/proj")
        self.reload()
        self.assertTrue(self.can_read("bob"))


    def reaccount(self, *accs):
        """edit [accounts] in the config, then reload"""
        self.args.a = list(accs)
        self.reload()

    def test_deleted_with_the_owner_account(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        # the admin hands alice's folder to carol and removes alice
        self.args.v = ["a:home/alice:A,carol"]
        self.reaccount("bob:bob", "carol:carol")
        self.assertEqual(self.n_grants(), 0)
        self.assertFalse(self.can_read("bob"))

        # a new alice doesn't inherit the old one's grant
        self.args.v = ["a:home/alice:A,alice"]
        self.reaccount(*ACCS)
        self.assertFalse(self.can_read("bob"))
        self.assertNotIn("shared/", self.ls("", "bob"))

    def test_deleted_with_the_recipient_account(self):
        self.cinit()
        self.assertEqual(self.grant()[0], 201)
        self.assertEqual(self.grant(rcpt="carol")[0], 201)
        self.reaccount("alice:alice", "carol:carol")
        self.assertEqual(self.n_grants(), 1)
        self.assertTrue(self.can_read("carol"))

        # a new bob doesn't inherit the old one's grant
        self.reaccount(*ACCS)
        self.assertFalse(self.can_read("bob"))
        self.assertNotIn("shared/", self.ls("", "bob"))
        self.assertTrue(self.can_read("carol"))

    def test_group_grant_kept_when_a_member_account_is_gone(self):
        # only a named recipient's account going away deletes the grant
        self.ginit("family:alice,bob,carol")
        self.assertEqual(self.grant(rcpt="@family")[0], 201)
        self.reaccount("alice:alice", "carol:carol")
        self.assertEqual(self.n_grants(), 1)
        self.assertTrue(self.can_read("carol"))
        self.reaccount(*ACCS)
        self.assertTrue(self.can_read("bob"))


    def logged(self, word):
        """log lines since the last call that start with `word` and name a
        grant's owner, recipient, path and rights"""
        ret = [x for x in self.logs if x.startswith(word + " grant ")]
        self.logs = []
        for x in ret:
            for zs in ("[alice]", "[bob]", "[/home/alice/proj]", "(r,"):
                self.assertIn(zs, x)
        return ret

    def test_state_changes_are_logged(self):
        self.cinit()
        self.logs = []
        self.assertEqual(self.grant(exp=60)[0], 201)
        self.assertEqual(len(self.logged("created")), 1)

        self.db_exec("update gr set t1 = 1")
        self.reload()
        self.assertEqual(len(self.logged("expired")), 1)

        self.db_exec("update gr set t1 = 0")
        os.rename("a/proj", "a/proj2")
        self.reload()
        self.assertEqual(len(self.logged("broken")), 1)
        os.rename("a/proj2", "a/proj")

        self.args.v = ["a:home/alice:A,carol"]
        self.reload()
        self.assertEqual(len(self.logged("suspended")), 1)

        self.args.a = ["alice:alice", "carol:carol"]
        self.reload()
        zsl = self.logged("deleted")
        self.assertEqual(len(zsl), 1)
        self.assertIn("for good", zsl[0])

    # the grants page (ticket 10)

    def page(self, uname):
        """the rows on the grants page as {gid: {column: text}}"""
        st, b = self.get("?grants", uname)
        self.assertEqual(st, 200, b)
        html = b.decode("utf-8")
        ret = {}
        for gid, tr in re.findall(r'<tr gid="([0-9]+)">(.*?)</tr>', html, re.DOTALL):
            cells = re.findall(r'<td class="([a-z0-9]+)">(.*?)</td>', tr, re.DOTALL)
            ret[int(gid)] = {k: re.sub(r"<[^>]*>", "", v).strip() for k, v in cells}
        return ret

    def gid(self, **ka):
        st, b = self.grant(**ka)
        self.assertEqual(st, 201, b)
        return json.loads(b)["id"]

    def states(self, uname):
        return {k: v["state"] for k, v in self.page(uname).items()}

    def test_page_lists_own_grants_with_state(self):
        for dn in ("a/gone", "a/other", "a/later", "b/x"):
            os.makedirs(dn)
        v = ["a:home/alice:A,alice", "b:home/bob:A,bob", "fam:family:r,@family"]
        os.makedirs("fam/pics")
        self.ginit("family:alice,carol", v=v)
        active = self.gid()
        expired = self.gid(vp="/home/alice/other/", name="other", exp=60)
        broken = self.gid(vp="/home/alice/gone/", name="gone")
        susp = self.gid(vp="/family/pics/", name="pics")
        later = self.gid(vp="/home/alice/later/", name="later", rcpt="carol", exp=60)
        bobs = self.gid(vp="/home/bob/x/", name="x", uname="bob", rcpt="alice")
        self.db_exec("update gr set t1 = 1 where id = ?", expired)
        os.rmdir("a/gone")
        self.regroup("family:carol")

        rows = self.page("alice")
        self.assertEqual(
            {k: v["state"] for k, v in rows.items()},
            {
                active: "active",
                expired: "expired",
                broken: "broken",
                susp: "suspended",
                later: "active",
            },
        )
        self.assertNotIn(bobs, rows)
        zd = rows[active]
        self.assertEqual(zd["rcpt"], "bob")
        self.assertEqual(zd["src"], "/home/alice/proj/")
        self.assertEqual(zd["name"], "proj")
        self.assertEqual(zd["pr"], "read")
        self.assertEqual(zd["exp"], "never")
        self.assertEqual(rows[later]["rcpt"], "carol")
        self.assertNotEqual(rows[later]["exp"], "never")
        self.assertEqual(list(self.page("bob")), [bobs])
        self.assertEqual(self.page("carol"), {})
        self.assertIn(self.get("?grants", "*")[0], (401, 403))


    def egrant(self, gid, act, uname):
        st, b = self.req("POST", "?egrant=%s&gid=%s" % (act, gid), uname)
        if st == 200:
            self.reload()  # what the broker's reload does in a real server
        return st, b

    def test_revoke(self):
        self.cinit()
        gid = self.gid()
        self.assertTrue(self.can_read("bob"))
        self.assertEqual(self.egrant(gid, "rm", "alice")[0], 200)
        self.assertFalse(self.can_read("bob"))
        self.assertNotIn("shared/", self.ls("", "bob"))
        self.assertEqual(self.page("alice"), {})
        self.assertEqual(self.egrant(gid, "rm", "alice")[0], 400)

    def test_revoke_refused_for_others(self):
        self.cinit()
        gid = self.gid()
        for un in ("bob", "carol"):
            st, b = self.egrant(gid, "rm", un)
            self.assertEqual(st, 403, un)
            self.assertIn(b"not yours", b)
        self.assertIn(self.egrant(gid, "rm", "*")[0], (401, 403))
        self.assertEqual(list(self.page("alice")), [gid])
        self.assertTrue(self.can_read("bob"))

    def test_share_admin_revokes_any(self):
        self.cinit(shr_adm=["carol"])
        gid = self.gid()
        self.assertEqual(self.egrant(gid, "rm", "carol")[0], 200)
        self.assertFalse(self.can_read("bob"))
        self.assertEqual(self.page("alice"), {})

    def test_revoke_a_grant_to_a_removed_group(self):
        self.ginit()
        gid = self.gid(rcpt="@family")
        self.regroup()
        self.assertEqual(self.page("alice")[gid]["rcpt"], "@family")
        self.assertEqual(self.egrant(gid, "rm", "alice")[0], 200)
        self.assertEqual(self.page("alice"), {})
        # a group by that name later gets nothing
        self.regroup("family:alice,bob")
        self.assertFalse(self.can_read("bob"))

    def t1(self, gid):
        db = sqlite3.connect("g.db")
        try:
            return db.execute("select t1 from gr where id = ?", (gid,)).fetchall()[0][0]
        finally:
            db.close()

    def test_extend_an_expired_grant(self):
        self.cinit()
        gid = self.gid(exp=60)
        self.db_exec("update gr set t1 = 1")
        self.reload()
        self.assertFalse(self.can_read("bob"))
        self.assertEqual(self.states("alice"), {gid: "expired"})

        now = time.time()
        self.assertEqual(self.egrant(gid, 60, "alice")[0], 200)
        self.assertTrue(self.can_read("bob"))
        self.assertEqual(self.states("alice"), {gid: "active"})
        self.assertAlmostEqual(self.t1(gid), now + 3600, delta=5)

    def test_extend_an_active_grant(self):
        self.cinit()
        gid = self.gid(exp=60)
        t1 = self.t1(gid)
        self.assertEqual(self.egrant(gid, 1440, "alice")[0], 200)
        self.assertEqual(self.t1(gid), t1 + 86400)
        self.assertTrue(self.can_read("bob"))
        self.assertEqual(self.states("alice"), {gid: "active"})

    def test_extend_refusals(self):
        self.cinit(shr_adm=["carol"])
        gid = self.gid(exp=60)
        t1 = self.t1(gid)
        for act in ("0", "-5", "x", "1.5", ""):
            self.assertEqual(self.egrant(gid, act, "alice")[0], 400, act)
        # a share admin revokes, but only the owner extends
        for un in ("bob", "carol"):
            self.assertEqual(self.egrant(gid, 60, un)[0], 403, un)
        self.assertEqual(self.t1(gid), t1)
        # one without expiry stays that way
        gid = self.gid(rcpt="carol")
        st, b = self.egrant(gid, 60, "alice")
        self.assertEqual(st, 400)
        self.assertIn(b"never expires", b)
        self.assertEqual(self.page("alice")[gid]["exp"], "never")

    def test_share_admins_see_every_grant(self):
        from copyparty.fork_util import split_names

        os.makedirs("b/x")
        v = ["a:home/alice:A,alice", "b:home/bob:A,bob"]
        self.cinit(v=v, shr_adm=split_names("alice, admin"))
        self.reaccount(*(ACCS + ["admin:admin"]))
        mine = self.gid()
        bobs = self.gid(vp="/home/bob/x/", name="x", uname="bob", rcpt="carol")
        for un in ("alice", "admin"):
            rows = self.page(un)
            self.assertEqual(sorted(rows), [mine, bobs], un)
            self.assertEqual(rows[bobs]["owner"], "bob")
        self.assertEqual(list(self.page("bob")), [bobs])
        self.assertEqual(self.page("carol"), {})

    def rcpts(self, uname):
        st, b = self.get("?grants=rcpts", uname)
        return st, (json.loads(b) if st == 200 else b)

    def test_recipient_list(self):
        self.ginit("family:alice,bob", "friends:carol")
        st, jo = self.rcpts("alice")
        self.assertEqual(st, 200)
        self.assertEqual(jo, {"accounts": ["bob", "carol"], "groups": ["@family", "@friends"]})
        self.assertEqual(self.rcpts("bob")[1]["accounts"], ["alice", "carol"])
        self.assertIn(self.rcpts("*")[0], (401, 403))

    def test_recipient_list_without_share_link_passwords(self):
        self.cinit_shr()
        self.assertEqual(self.share("/home/alice/proj/", pw="sharepw")[0], 201)
        self.reload()
        self.assertEqual(self.rcpts("alice")[1]["accounts"], ["bob", "carol"])

    def test_page_and_list_need_grants_on(self):
        self.cinit(grants="")
        self.assertEqual(self.get("?grants", "alice")[0], 400)
        self.assertEqual(self.rcpts("alice")[0], 400)

    def test_page_escapes_names(self):
        os.makedirs("a/p<q>")
        self.cinit()
        self.reaccount(*(ACCS + ["<b>:pw"]))
        gid = self.gid(vp="/home/alice/p<q>/", rcpt="<b>", name="n<i>")
        st, b = self.get("?grants", "alice")
        self.assertEqual(st, 200)
        for zs in (b"<b>", b"<q>", b"<i>"):
            self.assertNotIn(zs, b)
        for zs in (b"&lt;b&gt;", b"p&lt;q&gt;", b"n&lt;i&gt;", b"p%3Cq%3E"):
            self.assertIn(zs, b)
        self.assertEqual(self.page("alice")[gid]["rcpt"], "&lt;b&gt;")


if __name__ == "__main__":
    unittest.main()

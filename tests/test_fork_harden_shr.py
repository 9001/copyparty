#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: with --harden, share links follow the fork's rules (ticket 05)

import io
import json
import os
import shutil
import sqlite3
import tarfile
import tempfile
import unittest
import zipfile

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg

KEY = "abcdefghijkl"  # 12 characters


class TestForkHardenShr(unittest.TestCase):
    def log(self, src, msg, c=0):
        pass

    def setUp(self):
        self.conn = None
        self.td = tu.get_ramdisk()
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)
        for fp in ("d/f.txt", "d/.env", "d/.git/config", "d/s/g.txt"):
            dp = os.path.dirname(fp)
            if not os.path.isdir(dp):
                os.makedirs(dp)
            with open(fp, "wb") as f:
                f.write(fp.encode("utf-8"))

        db = sqlite3.connect("a.db")
        with db:
            db.execute(
                "create table sh (k text, pw text, vp text, pr text, st int, un text, t0 int, t1 int)"
            )
            db.execute("create table sf (k text, vp text)")
        db.close()

    def tearDown(self):
        if self.conn:
            self.conn.shutdown()
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def cinit(self, harden=True, accs=None, v=None, **ka):
        if harden:
            ka["harden"] = True
        self.args = Cfg(
            a=accs or ["alice:pa"],
            v=v or ["::A,alice"],
            shr="/shr/",
            shr1="shr/",
            shr_db="a.db",
            shr_v=False,
            **ka
        )
        self.reload()

    def reload(self):
        if self.conn:
            self.conn.shutdown()
            self.conn = None
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)

    def req(self, method, url, extra="", body=b""):
        h = "%s /%s HTTP/1.1\r\nConnection: close\r\n%s\r\n"
        buf = (h % (method, url, extra)).encode("utf-8") + body
        HttpCli(self.conn.setbuf(buf)).run()
        h, b = self.conn.s._reply.split(b"\r\n\r\n", 1)
        return int(h.split(b" ", 2)[1]), b

    def get(self, url):
        return self.req("GET", url)

    def share(self, key=KEY, perms=("read",), vp="/d/"):
        jt = {"k": key, "vp": [vp], "pw": "", "exp": "", "perms": list(perms)}
        buf = json.dumps(jt).encode("utf-8")
        hdr = "Content-Type: application/json\r\nContent-Length: %d\r\n" % (len(buf),)
        st, b = self.req("POST", "?pw=pa&share", hdr, buf)
        if st == 201:
            self.reload()  # what the broker's reload does in a real server
        return st, b

    def test_guest_dotfile_404(self):
        self.cinit()
        self.assertEqual(self.share()[0], 201)
        self.check_dot_404()

    def test_guest_dotfile_404_even_with_dot_perm(self):
        # alice has `A` so upstream lets her give the link `.` too
        self.cinit()
        self.assertEqual(self.share(perms=("read", "dot"))[0], 201)
        self.check_dot_404()

    def archive(self, url):
        st, b = self.get(url)
        self.assertEqual(st, 200, b)
        if "zip" in url:
            return sorted(zipfile.ZipFile(io.BytesIO(b)).namelist())
        return sorted(tarfile.open(fileobj=io.BytesIO(b), mode="r|").getnames())

    def test_archive_has_no_dotfiles(self):
        self.cinit()
        self.assertEqual(self.share(perms=("read", "dot"))[0], 201)
        for fmt in ("tar", "zip"):
            names = self.archive("shr/%s/?%s&dots" % (KEY, fmt))
            self.assertIn("%s/f.txt" % (KEY,), names)
            self.assertIn("%s/s/g.txt" % (KEY,), names)
            self.assertEqual([x for x in names if "/." in x], [], fmt)
            self.assertEqual(self.get("shr/%s/.git?%s" % (KEY, fmt))[0], 404)

    def test_short_key_refused(self):
        self.cinit()
        st, b = self.share(key="abcdefghijk")  # 11
        self.assertEqual(st, 400)
        self.assertIn(b"at least 12 characters", b)
        self.assertGreaterEqual(self.get("shr/abcdefghijk/f.txt")[0], 400)
        self.assertEqual(self.share()[0], 201)  # 12

    def rows(self):
        db = sqlite3.connect("a.db")
        try:
            sh = [x[0] for x in db.execute("select k from sh")]
            sf = [x[0] for x in db.execute("select k from sf")]
            return sh, sf
        finally:
            db.close()

    def test_removed_owner_share_deleted_for_good(self):
        self.cinit(accs=["alice:pa", "bob:pb"])
        self.assertEqual(self.share()[0], 201)
        self.assertEqual(self.share("filesharekey", vp="/d/f.txt")[0], 201)
        self.assertEqual(self.get("shr/%s/f.txt" % (KEY,))[0], 200)
        self.assertEqual(self.rows(), ([KEY, "filesharekey"], ["filesharekey"]))

        # alice leaves the config; bob's reload must not keep her links
        self.cinit(accs=["bob:pb"], v=["::A,bob"])
        self.assertEqual(self.rows(), ([], []))
        self.assertGreaterEqual(self.get("shr/%s/f.txt" % (KEY,))[0], 400)

        # a new alice does not get the old links back
        self.cinit(accs=["alice:new", "bob:pb"], v=["::A,alice"])
        self.assertEqual(self.rows(), ([], []))
        self.assertGreaterEqual(self.get("shr/%s/f.txt" % (KEY,))[0], 400)

    def test_owner_without_rights_keeps_row(self):
        # owner still exists but lost access: upstream hides the link and
        # keeps the row, so it comes back if the access does
        self.cinit(accs=["alice:pa", "bob:pb"])
        self.assertEqual(self.share()[0], 201)
        self.args.v = ["::A,bob"]
        self.reload()
        self.assertEqual(self.rows()[0], [KEY])
        self.assertGreaterEqual(self.get("shr/%s/f.txt" % (KEY,))[0], 400)
        self.args.v = ["::A,alice"]
        self.reload()
        self.assertEqual(self.get("shr/%s/f.txt" % (KEY,))[0], 200)

    # uploads through a write share link

    # an up2k file: (data, chunk hash, wark), from tests/test_dedup.py
    UP2K_FILE = (
        "one",
        "BfcDQQeKz2oG1CPSFyD5ZD1flTYm2IoCY23DqeeVgq6w",
        "XMbpLRqVdtGmgggqjUI6uSoNMTqZVX4K6zr74XA1BRKc",
    )

    def body(self, method, url, buf, ctype, extra=""):
        extra += "Content-Type: %s\r\nContent-Length: %d\r\n" % (ctype, len(buf))
        return self.req(method, url, extra, buf)

    def put(self, dn, fn):
        return self.body("PUT", dn + "/" + fn, b"put", "application/octet-stream")

    def form(self, url, fields):
        """multipart POST; fields = [(name, filename or None, value)]"""
        buf = ""
        for name, fname, val in fields:
            cd = 'form-data; name="%s"' % (name,)
            if fname:
                cd += '; filename="%s"' % (fname,)
            buf += "--XD\r\nContent-Disposition: %s\r\n\r\n%s\r\n" % (cd, val)
        buf += "--XD--\r\n"
        ctype = "multipart/form-data; boundary=XD"
        return self.body("POST", url, buf.encode("utf-8"), ctype)

    def bput(self, dn, fn):
        return self.form(dn + "/", [("act", None, "bput"), ("f", fn, "mp")])

    def new_md(self, dn, fn):
        # the browser's "new file" button; names it fn (adds .md if missing)
        return self.form(dn + "/", [("act", None, "new_md"), ("name", None, fn)])

    def tput(self, dn, fn):
        # the markdown editor's save button
        fields = [("act", None, "tput"), ("lastmod", None, "0"), ("body", None, "md")]
        return self.form(dn + "/" + fn, fields)

    def dav_copy(self, dn, fn):
        hdr = "Destination: /%s/%s\r\nContent-Length: 0\r\n" % (dn, fn)
        return self.req("COPY", dn + "/f.txt", hdr)

    def copy(self, dn, fn):
        return self.req("POST", "%s/f.txt?copy=/%s/%s" % (dn, dn, fn), "Content-Length: 0\r\n")

    def up2k(self, dn, fn):
        data, chash, wark = self.UP2K_FILE
        msg = {"name": fn, "size": 3, "lmod": 1234567890, "life": 0, "hash": [chash]}
        buf = json.dumps(msg).encode("utf-8")
        st, b = self.body("POST", dn + "/", buf, "text/plain")
        if st != 200:
            return st, b
        if json.loads(b)["hash"]:
            hdr = "X-Up2k-Hash: %s\r\nX-Up2k-Wark: %s\r\n" % (chash, wark)
            ctype = "application/octet-stream"
            st, b = self.body("POST", dn + "/", data.encode(), ctype, hdr)
        return st, b

    REFUSED = ("README.md", "readme.MD", "PREADME.md", "pReadMe.Md", "descript.ion", "DESCRIPT.ION", ".new")

    def uploads(self):
        ret = [("put", self.put), ("bput", self.bput), ("up2k", self.up2k)]
        ret += [("new_md", self.new_md), ("tput", self.tput)]
        ret += [("dav_copy", self.dav_copy), ("copy", self.copy)]
        return ret

    def test_write_share_refuses_listing_names(self):
        self.cinit()
        self.assertEqual(self.share(perms=("read", "write", "dot"))[0], 201)
        dn = "shr/" + KEY
        for way, up in self.uploads():
            for fn in self.REFUSED:
                st, b = up(dn, fn)
                self.assertGreaterEqual(st, 400, (way, fn, b))
                self.assertFalse(os.path.exists("d/" + fn), (way, fn))

            fn = "ok-%s.md" % (way,)
            st, b = up(dn, fn)
            self.assertLess(st, 400, (way, b))
            self.assertTrue(os.path.exists("d/" + fn), way)

        # the owner, in their own volume, still can
        self.assertEqual(self.put("d", "README.md?pw=pa")[0], 201)
        self.assertTrue(os.path.exists("d/README.md"))

    # no-html (upstream's option; the deployment relies on it)

    PAGES = {
        "p.html": b"<script>alert(1)</script>",
        "p.htm": b"<script>alert(1)</script>",
        "p.xhtml": b'<html xmlns="http://www.w3.org/1999/xhtml"><script>alert(1)</script></html>',
        "p.svg": b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        "p.md": b"# hi\n<script>alert(1)</script>\n",
    }

    def get_hdrs(self, url):
        """GET; returns (status, headers, body)"""
        st, b = self.get(url)
        h = self.conn.s._reply.split(b"\r\n\r\n", 1)[0]
        lines = h.decode("utf-8").split("\r\n")
        return st, dict(x.split(": ", 1) for x in lines[1:]), b

    def mkpages(self):
        for fn, buf in self.PAGES.items():
            with open("d/" + fn, "wb") as f:
                f.write(buf)

    def urls(self):
        for fn in self.PAGES:
            yield "d/%s?pw=pa" % (fn,)  # the owner, logged in
            yield "shr/%s/%s" % (KEY, fn)  # a guest
        yield "d/p.md?v&pw=pa"  # markdown viewer
        yield "shr/%s/p.md?v" % (KEY,)

    def test_no_html(self):
        self.mkpages()
        self.cinit(no_html=True)
        self.assertEqual(self.share()[0], 201)
        for url in self.urls():
            st, h, _ = self.get_hdrs(url)
            self.assertEqual(st, 200, url)
            self.assertEqual(h["Content-Type"], "text/plain; charset=utf-8", url)
            self.assertIn("script-src 'none'", h.get("Content-Security-Policy", ""), url)

        # copyparty's own file browser is still html, with scripts allowed
        # (the test server renders stub templates, so the body can't show it)
        for url in ("d/?pw=pa", "shr/%s/" % (KEY,)):
            st, h, _ = self.get_hdrs(url)
            self.assertEqual(st, 200, url)
            self.assertTrue(h["Content-Type"].startswith("text/html"), url)
            self.assertNotIn("script-src 'none'", h.get("Content-Security-Policy", ""), url)

    # one refused name per upload way; distinct, as they share one folder
    UPSTREAM_NAMES = {
        "put": "README.md",
        "bput": "PREADME.md",
        "up2k": "descript.ion",
        "new_md": "readme.md",
        "tput": "Readme.md",
        "dav_copy": "README.MD",
        "copy": "preadme.MD",
    }

    def test_harden_off_is_upstream(self):
        self.cinit(harden=False, accs=["alice:pa", "bob:pb"])
        st, b = self.share(perms=("read", "write", "dot"))
        self.assertEqual(st, 201, b)
        self.assertEqual(self.get("shr/%s/.env" % (KEY,)), (200, b"d/.env"))
        # upstream's link archives skip dotfiles already, but a dot folder
        # can still be fetched as an archive by name
        self.assertEqual(self.archive("shr/%s/.git?tar" % (KEY,)), ["git/config"])

        dn = "shr/" + KEY
        for way, up in self.uploads():
            fn = self.UPSTREAM_NAMES[way]
            self.assertLess(up(dn, fn)[0], 400, way)
            self.assertTrue(os.path.exists("d/" + fn), way)

        self.assertEqual(self.share("abcdefghijk")[0], 201)  # 11

        self.cinit(harden=False, accs=["bob:pb"], v=["::A,bob"])
        self.assertEqual(sorted(self.rows()[0]), ["abcdefghijk", KEY])
        self.cinit(harden=False, accs=["alice:new", "bob:pb"])
        self.assertEqual(self.get("shr/%s/f.txt" % (KEY,))[0], 200)  # revived

    def test_guest_dotfile_404_with_ed(self):
        # --ed gives everyone `.`; the dots volflag then puts it on the link
        self.cinit(ed=True)
        self.assertEqual(self.share()[0], 201)
        self.check_dot_404()

    def check_dot_404(self):
        self.assertEqual(self.get("shr/%s/f.txt" % (KEY,)), (200, b"d/f.txt"))
        self.assertEqual(self.get("shr/%s/.env" % (KEY,))[0], 404)
        self.assertEqual(self.get("shr/%s/.git/config" % (KEY,))[0], 404)
        # the owner keeps their own dotfiles
        self.assertEqual(self.get("d/.env?pw=pa"), (200, b"d/.env"))


if __name__ == "__main__":
    unittest.main()

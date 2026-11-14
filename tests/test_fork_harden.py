#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: with --harden, dotfiles inside a volume are 404 without the `.` permission

import io
import os
import shutil
import tarfile
import tempfile
import unittest
import zipfile

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg


class TestForkHarden(unittest.TestCase):
    def log(self, src, msg, c=0):
        pass

    def setUp(self):
        self.conn = None
        self.td = tu.get_ramdisk()
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)
        for fp in (".env", ".git/config", "d/f.txt", "d/.secret", "f.txt", ".p.jpg"):
            dp = os.path.dirname(fp)
            if dp and not os.path.isdir(dp):
                os.makedirs(dp)
            with open(fp, "wb") as f:
                f.write(fp.encode("utf-8"))

    def tearDown(self):
        if self.conn:
            self.conn.shutdown()
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def cinit(self, harden=True, vcfg=None, up2k=False, **ka):
        if harden:
            ka["harden"] = True
        if up2k:
            # folder move/copy; upstream's test Cfg lacks the no_dot_* options
            ka.update(e2d=True, no_dot_mv=False, no_dot_ren=False)
        vcfg = vcfg or [".::r,u1:r.,u2"]
        self.args = Cfg(v=vcfg, a=["u1:u1", "u2:u2"], **ka)
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", up2k)

    def req(self, method, url, uname, extra=""):
        h = "%s /%s HTTP/1.1\r\nPW: %s\r\nConnection: close\r\n%s\r\n"
        buf = (h % (method, url, uname, extra)).encode("utf-8")
        HttpCli(self.conn.setbuf(buf)).run()
        h, b = self.conn.s._reply.split(b"\r\n\r\n", 1)
        return int(h.split(b" ", 2)[1]), b

    def get(self, url, uname):
        return self.req("GET", url, uname)

    def test_get_dotfile_without_dot_is_404(self):
        self.cinit()
        self.assertEqual(self.get(".env", "u1")[0], 404)
        self.assertEqual(self.get(".git/config", "u1")[0], 404)
        self.assertEqual(self.get("d/.secret", "u1")[0], 404)
        self.assertEqual(self.get("f.txt", "u1")[0], 200)

    def test_get_dotfile_with_dot_is_200(self):
        self.cinit()
        self.assertEqual(self.get(".env", "u2"), (200, b".env"))
        self.assertEqual(self.get(".git/config", "u2"), (200, b".git/config"))
        self.assertEqual(self.get("d/.secret", "u2"), (200, b"d/.secret"))

    def test_harden_off_is_upstream(self):
        self.cinit(harden=False)
        self.assertEqual(self.get(".env", "u1"), (200, b".env"))

    def test_web_resources_still_load(self):
        self.cinit()
        self.assertEqual(self.get(".cpr/ui.css", "u1")[0], 200)
        self.assertEqual(self.get(".cpr/ui.css", "*")[0], 200)

    def test_path_lookup(self):
        self.cinit()
        vfs = self.asrv.vfs
        for vp in (".env", ".git/config", "d/.secret", ".git"):
            with self.assertRaises(Exception) as cm:
                vfs.get(vp, "u1", True, False)
            self.assertEqual(cm.exception.code, 404, vp)
            self.assertIsNone(vfs.get(vp, "u1", True, False, err=0))

            _, rem = vfs.get(vp, "u2", True, False)
            self.assertEqual(rem, vp)

        self.assertEqual(vfs.get("d/f.txt", "u1", True, False)[1], "d/f.txt")

    def test_dot_named_mount(self):
        os.mkdir("b")
        with open("b/f", "wb") as f:
            f.write(b"bf")
        with open("b/.f", "wb") as f:
            f.write(b"b.f")
        self.cinit(vcfg=[".::r,u1:r.,u2", "b:.b:r,u1:r.,u2"])
        self.assertEqual(self.get(".b/f", "u1"), (200, b"bf"))
        self.assertEqual(self.get(".b/.f", "u1")[0], 404)
        self.assertEqual(self.get(".b/.f", "u2"), (200, b"b.f"))
        self.assertEqual(self.asrv.vfs.get(".b", "u1", True, False)[1], "")

    def test_webdav(self):
        self.cinit()
        dav = "User-Agent: Microsoft-WebDAV-MiniRedir/10.0\r\n"
        self.assertEqual(self.req("GET", ".env", "u1", dav)[0], 404)
        self.assertEqual(self.req("GET", ".env", "u2", dav)[0], 200)

        for depth in ("1", "infinity"):
            hdr = "Depth: %s\r\n" % (depth,)
            st, b = self.req("PROPFIND", "", "u1", hdr)
            self.assertEqual(st, 207)
            self.assertIn(b"f.txt", b)
            self.assertNotIn(b".env", b)
            self.assertNotIn(b".secret", b)
            self.assertEqual(self.req("PROPFIND", ".git", "u1", hdr)[0], 404)

            st, b = self.req("PROPFIND", "", "u2", hdr + "Cookie: dots=1\r\n")
            self.assertEqual(st, 207)
            self.assertIn(b".env", b)
            self.assertEqual(self.req("PROPFIND", ".git", "u2", hdr)[0], 207)

    def archive(self, url, uname):
        st, b = self.get(url, uname)
        self.assertEqual(st, 200)
        if "zip" in url:
            return sorted(zipfile.ZipFile(io.BytesIO(b)).namelist())
        return sorted(tarfile.open(fileobj=io.BytesIO(b), mode="r|").getnames())

    def test_archives(self):
        self.cinit()
        for fmt in ("tar", "zip"):
            names = self.archive("?" + fmt, "u1")
            self.assertEqual(names, ["top/d/f.txt", "top/f.txt"])
            names = self.archive("d?" + fmt, "u1")
            self.assertEqual(names, ["d/f.txt"])
            self.assertEqual(self.get(".git?" + fmt, "u1")[0], 404)

            names = self.archive("?%s&dots" % (fmt,), "u2")
            self.assertIn("top/.env", names)
            self.assertIn("top/.git/config", names)
            # the archive's top folder drops the leading dot
            self.assertEqual(self.archive(".git?" + fmt, "u2"), ["git/config"])

    def test_thumbnail(self):
        self.cinit()
        # upstream answers a refused thumbnail with an svg saying e404 / e403
        self.assertIn(b">e404</text>", self.get(".p.jpg?th=j", "u1")[1])
        self.assertIn(b">e404</text>", self.get(".git?th=j", "u1")[1])
        self.assertIn(b">p.jpg</text>", self.get(".p.jpg?th=j", "u2")[1])

    def test_hist_up2k_still_refused(self):
        self.cinit(e2d=True)
        if not os.path.isdir(".hist"):
            os.mkdir(".hist")
        with open(".hist/up2k.snap", "wb") as f:
            f.write(b"x")
        # .hist is its own permission-less node (a mount point), so 403 for all
        self.assertEqual(self.get(".hist/up2k.snap", "u1")[0], 403)
        self.assertEqual(self.get(".hist/up2k.snap", "u2")[0], 403)

    def mkfolder(self):
        for fp in ("m/a.txt", "m/.DS_Store", "m/s/b.txt"):
            dp = os.path.dirname(fp)
            if not os.path.isdir(dp):
                os.makedirs(dp)
            with open(fp, "wb") as f:
                f.write(b"x")

    def post(self, url, uname):
        return self.req("POST", url, uname, "Content-Length: 0\r\n")

    def tree(self, top):
        ret = []
        for dp, _, fns in os.walk(top):
            ret += [os.path.join(dp, fn) for fn in fns]
        return sorted(ret)

    def test_move_folder_with_dotfiles(self):
        # all-or-nothing: refused before any file moves
        self.mkfolder()
        self.cinit(vcfg=[".::rwm,u1:rwm.,u2"], up2k=True)
        st, b = self.post("m?move=/m2", "u1")
        self.assertEqual(st, 403, b)
        self.assertEqual(self.tree("m"), ["m/.DS_Store", "m/a.txt", "m/s/b.txt"])
        self.assertFalse(os.path.exists("m2"))

        self.assertEqual(self.post("m?move=/m2", "u2")[0], 201)
        self.assertEqual(self.tree("m2"), ["m2/.DS_Store", "m2/a.txt", "m2/s/b.txt"])

    def test_copy_folder_with_dotfiles(self):
        self.mkfolder()
        self.cinit(vcfg=[".::rw,u1:rw.,u2"], up2k=True)
        st, b = self.post("m?copy=/c", "u1")
        self.assertEqual(st, 403, b)
        self.assertFalse(os.path.exists("c"))

        self.assertEqual(self.post("m?copy=/c", "u2")[0], 201)
        self.assertEqual(self.tree("c"), ["c/.DS_Store", "c/a.txt", "c/s/b.txt"])

    def test_move_folder_harden_off(self):
        self.mkfolder()
        self.cinit(harden=False, vcfg=[".::rwm,u1"], up2k=True)
        self.assertEqual(self.post("m?move=/m2", "u1")[0], 201)
        self.assertEqual(self.tree("m2"), ["m2/.DS_Store", "m2/a.txt", "m2/s/b.txt"])


if __name__ == "__main__":
    unittest.main()

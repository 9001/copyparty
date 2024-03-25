#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import io
import os
import time
import json
import pprint
import shutil
import tarfile
import tempfile
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from copyparty.u2idx import U2idx
from copyparty.up2k import Up2k
from tests import util as tu
from tests.util import Cfg


def hdr(query, uname):
    h = "GET /%s HTTP/1.1\r\nPW: %s\r\nConnection: close\r\n\r\n"
    return (h % (query, uname)).encode("utf-8")


class TestHttpCli(unittest.TestCase):
    def setUp(self):
        self.td = tu.get_ramdisk()

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def test(self):
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        # topDir  volA  volA/*dirA  .volB  .volB/*dirB
        spaths = " t .t a a/da a/.da .b .b/db .b/.db"
        for n, dirpath in enumerate(spaths.split(" ")):
            if dirpath:
                os.makedirs(dirpath)

            for pfx in "f", ".f":
                filepath = pfx + str(n)
                if dirpath:
                    filepath = os.path.join(dirpath, filepath)

                with open(filepath, "wb") as f:
                    f.write(filepath.encode("utf-8"))

        vcfg = [".::r,u1:r.,u2", "a:a:r,u1:r,u2", ".b:.b:r.,u1:r,u2"]
        self.args = Cfg(v=vcfg, a=["u1:u1", "u2:u2"], e2dsa=True)
        self.asrv = AuthSrv(self.args, self.log)

        self.assertEqual(self.tardir("", "u1"), "f0 t/f1 a/f3 a/da/f4")
        self.assertEqual(self.tardir(".t", "u1"), "f2")
        self.assertEqual(self.tardir(".b", "u1"), ".f6 f6 .db/.f8 .db/f8 db/.f7 db/f7")

        zs = ".f0 f0 .t/.f2 .t/f2 t/.f1 t/f1 .b/f6 .b/db/f7 a/f3 a/da/f4"
        self.assertEqual(self.tardir("", "u2"), zs)

        self.assertEqual(self.curl("?tar", "x")[1][:17], "\nJ2EOT")

        ##
        ## search

        up2k = Up2k(self)
        u2idx = U2idx(self)
        allvols = list(self.asrv.vfs.all_vols.values())

        x = u2idx.search("u1", allvols, "", 999)
        x = " ".join(sorted([x["rp"] for x in x[0]]))
        # u1 can see dotfiles in volB so they should be included
        xe = ".b/.db/.f8 .b/.db/f8 .b/.f6 .b/db/.f7 .b/db/f7 .b/f6 a/da/f4 a/f3 f0 t/f1"
        self.assertEqual(x, xe)

        x = u2idx.search("u2", allvols, "", 999)
        x = " ".join(sorted([x["rp"] for x in x[0]]))
        self.assertEqual(x, ".f0 .t/.f2 .t/f2 a/da/f4 a/f3 f0 t/.f1 t/f1")

        self.args = Cfg(v=vcfg, a=["u1:u1", "u2:u2"], dotsrch=False)
        self.asrv = AuthSrv(self.args, self.log)
        u2idx = U2idx(self)

        x = u2idx.search("u1", self.asrv.vfs.all_vols.values(), "", 999)
        x = " ".join(sorted([x["rp"] for x in x[0]]))
        # u1 can see dotfiles in volB so they should be included
        xe = "a/da/f4 a/f3 f0 t/f1"
        self.assertEqual(x, xe)

        ##
        ## dirkeys

        os.mkdir("v")
        with open("v/f1.txt", "wb") as f:
            f.write(b"a")
        os.rename("a", "v/a")
        os.rename(".b", "v/.b")

        vcfg = [
            ".::r.,u1:g,u2:c,dk",
            "v/a:v/a:r.,u1:g,u2:c,dk",
            "v/.b:v/.b:r.,u1:g,u2:c,dk"
        ]
        self.args = Cfg(v=vcfg, a=["u1:u1", "u2:u2"])
        self.asrv = AuthSrv(self.args, self.log)
        zj = json.loads(self.curl("?ls", "u1")[1])
        url = "?k=" + zj["dk"]
        # should descend into folders, but not other volumes:
        self.assertEqual(self.tardir(url, "u2"), "f0 t/f1 v/f1.txt")

        zj = json.loads(self.curl("v?ls", "u1")[1])
        url = "v?k=" + zj["dk"]
        self.assertEqual(self.tarsel(url, "u2", ["f1.txt", "a", ".b"]), "f1.txt")

    def tardir(self, url, uname):
        top = url.split("?")[0]
        top = ("top" if not top else top.lstrip(".").split("/")[0]) + "/"
        url += ("&" if "?" in url else "?") + "tar"
        h, b = self.curl(url, uname, True)
        tar = tarfile.open(fileobj=io.BytesIO(b), mode="r|").getnames()
        if len(tar) != len([x for x in tar if x.startswith(top)]):
            raise Exception("bad-prefix:", tar)
        return " ".join([x[len(top) :] for x in tar])

    def tarsel(self, url, uname, sel):
        url += ("&" if "?" in url else "?") + "tar"
        zs = '--XD\r\nContent-Disposition: form-data; name="act"\r\n\r\nzip\r\n--XD\r\nContent-Disposition: form-data; name="files"\r\n\r\n'
        zs += "\r\n".join(sel) + '\r\n--XD--\r\n'
        zb = zs.encode("utf-8")
        hdr = "POST /%s HTTP/1.1\r\nPW: %s\r\nConnection: close\r\nContent-Type: multipart/form-data; boundary=XD\r\nContent-Length: %d\r\n\r\n"
        req = (hdr % (url, uname, len(zb))).encode("utf-8") + zb
        h, b = self.curl("/" + url, uname, True, req)
        tar = tarfile.open(fileobj=io.BytesIO(b), mode="r|").getnames()
        return " ".join(tar)

    def curl(self, url, uname, binary=False, req=b""):
        req = req or hdr(url, uname)
        conn = tu.VHttpConn(self.args, self.asrv, self.log, req)
        HttpCli(conn).run()
        if binary:
            h, b = conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

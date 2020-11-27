#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import time
import json
import shutil
import unittest
import subprocess as sp  # nosec

from textwrap import dedent
from argparse import Namespace
from copyparty.authsrv import AuthSrv
from copyparty import util


class TestVFS(unittest.TestCase):
    def dump(self, vfs):
        print(json.dumps(vfs, indent=4, sort_keys=True, default=lambda o: o.__dict__))

    def unfoo(self, foo):
        for k, v in {"foo": "a", "bar": "b", "baz": "c", "qux": "d"}.items():
            foo = foo.replace(k, v)

        return foo

    def undot(self, vfs, query, response):
        self.assertEqual(util.undot(query), response)
        query = self.unfoo(query)
        response = self.unfoo(response)
        self.assertEqual(util.undot(query), response)

    def absify(self, root, names):
        return ["{}/{}".format(root, x).replace("//", "/") for x in names]

    def ls(self, vfs, vpath, uname):
        """helper for resolving and listing a folder"""
        vn, rem = vfs.get(vpath, uname, True, False)
        return vn.ls(rem, uname)

    def runcmd(self, *argv):
        p = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE)
        stdout, stderr = p.communicate()
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
        return [p.returncode, stdout, stderr]

    def chkcmd(self, *argv):
        ok, sout, serr = self.runcmd(*argv)
        if ok != 0:
            raise Exception(serr)

        return sout, serr

    def get_ramdisk(self):
        for vol in ["/dev/shm", "/Volumes/cptd"]:  # nosec (singleton test)
            if os.path.exists(vol):
                return vol

        if os.path.exists("/Volumes"):
            devname, _ = self.chkcmd("hdiutil", "attach", "-nomount", "ram://8192")
            for _ in range(10):
                try:
                    _, _ = self.chkcmd("diskutil", "eraseVolume", "HFS+", "cptd", devname)
                    return "/Volumes/cptd"
                except:
                    print('lol macos')
                    time.sleep(0.25)
            
            raise Exception("ramdisk creation failed")

        raise Exception("TODO support windows")

    def log(self, src, msg):
        pass

    def test(self):
        td = self.get_ramdisk() + "/vfs"
        try:
            shutil.rmtree(td)
        except OSError:
            pass

        os.mkdir(td)
        os.chdir(td)

        for a in "abc":
            for b in "abc":
                for c in "abc":
                    folder = "{0}/{0}{1}/{0}{1}{2}".format(a, b, c)
                    os.makedirs(folder)
                    for d in "abc":
                        fn = "{}/{}{}{}{}".format(folder, a, b, c, d)
                        with open(fn, "w") as f:
                            f.write(fn)

        # defaults
        vfs = AuthSrv(Namespace(c=None, a=[], v=[]), self.log).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td)
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, ["*"])

        # single read-only rootfs (relative path)
        vfs = AuthSrv(Namespace(c=None, a=[], v=["a/ab/::r"]), self.log).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td + "/a/ab")
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, [])

        # single read-only rootfs (absolute path)
        vfs = AuthSrv(
            Namespace(c=None, a=[], v=[td + "//a/ac/../aa//::r"]), self.log
        ).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td + "/a/aa")
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, [])

        # read-only rootfs with write-only subdirectory (read-write for k)
        vfs = AuthSrv(
            Namespace(c=None, a=["k:k"], v=[".::r:ak", "a/ac/acb:a/ac/acb:w:ak"]),
            self.log,
        ).vfs
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td)
        self.assertEqual(vfs.uread, ["*", "k"])
        self.assertEqual(vfs.uwrite, ["k"])
        n = vfs.nodes["a"]
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(n.vpath, "a")
        self.assertEqual(n.realpath, td + "/a")
        self.assertEqual(n.uread, ["*", "k"])
        self.assertEqual(n.uwrite, ["k"])
        n = n.nodes["ac"]
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(n.vpath, "a/ac")
        self.assertEqual(n.realpath, td + "/a/ac")
        self.assertEqual(n.uread, ["*", "k"])
        self.assertEqual(n.uwrite, ["k"])
        n = n.nodes["acb"]
        self.assertEqual(n.nodes, {})
        self.assertEqual(n.vpath, "a/ac/acb")
        self.assertEqual(n.realpath, td + "/a/ac/acb")
        self.assertEqual(n.uread, ["k"])
        self.assertEqual(n.uwrite, ["*", "k"])

        fsdir, real, virt = self.ls(vfs, "/", "*")
        self.assertEqual(fsdir, td)
        self.assertEqual(real, ["b", "c"])
        self.assertEqual(list(virt), ["a"])

        fsdir, real, virt = self.ls(vfs, "a", "*")
        self.assertEqual(fsdir, td + "/a")
        self.assertEqual(real, ["aa", "ab"])
        self.assertEqual(list(virt), ["ac"])

        fsdir, real, virt = self.ls(vfs, "a/ab", "*")
        self.assertEqual(fsdir, td + "/a/ab")
        self.assertEqual(real, ["aba", "abb", "abc"])
        self.assertEqual(list(virt), [])

        fsdir, real, virt = self.ls(vfs, "a/ac", "*")
        self.assertEqual(fsdir, td + "/a/ac")
        self.assertEqual(real, ["aca", "acc"])
        self.assertEqual(list(virt), [])

        fsdir, real, virt = self.ls(vfs, "a/ac", "k")
        self.assertEqual(fsdir, td + "/a/ac")
        self.assertEqual(real, ["aca", "acc"])
        self.assertEqual(list(virt), ["acb"])

        self.assertRaises(util.Pebkac, vfs.get, "a/ac/acb", "*", True, False)

        fsdir, real, virt = self.ls(vfs, "a/ac/acb", "k")
        self.assertEqual(fsdir, td + "/a/ac/acb")
        self.assertEqual(real, ["acba", "acbb", "acbc"])
        self.assertEqual(list(virt), [])

        # breadth-first construction
        vfs = AuthSrv(
            Namespace(
                c=None,
                a=[],
                v=[
                    "a/ac/acb:a/ac/acb:w",
                    "a:a:w",
                    ".::r",
                    "abacdfasdq:abacdfasdq:w",
                    "a/ac:a/ac:w",
                ],
            ),
            self.log,
        ).vfs

        # sanitizing relative paths
        self.undot(vfs, "foo/bar/../baz/qux", "foo/baz/qux")
        self.undot(vfs, "foo/../bar", "bar")
        self.undot(vfs, "foo/../../bar", "bar")
        self.undot(vfs, "foo/../../", "")
        self.undot(vfs, "./.././foo/", "foo")
        self.undot(vfs, "./.././foo/..", "")

        # shadowing
        vfs = AuthSrv(Namespace(c=None, a=[], v=[".::r", "b:a/ac:r"]), self.log).vfs

        fsp, r1, v1 = self.ls(vfs, "", "*")
        self.assertEqual(fsp, td)
        self.assertEqual(r1, ["b", "c"])
        self.assertEqual(list(v1), ["a"])

        fsp, r1, v1 = self.ls(vfs, "a", "*")
        self.assertEqual(fsp, td + "/a")
        self.assertEqual(r1, ["aa", "ab"])
        self.assertEqual(list(v1), ["ac"])

        fsp1, r1, v1 = self.ls(vfs, "a/ac", "*")
        fsp2, r2, v2 = self.ls(vfs, "b", "*")
        self.assertEqual(fsp1, td + "/b")
        self.assertEqual(fsp2, td + "/b")
        self.assertEqual(r1, ["ba", "bb", "bc"])
        self.assertEqual(r1, r2)
        self.assertEqual(list(v1), list(v2))

        # config file parser
        cfg_path = self.get_ramdisk() + "/test.cfg"
        with open(cfg_path, "wb") as f:
            f.write(
                dedent(
                    """
                    u a:123
                    u asd:fgh:jkl
                    
                    ./src
                    /dst
                    r a
                    a asd
                    """
                ).encode("utf-8")
            )

        au = AuthSrv(Namespace(c=[cfg_path], a=[], v=[]), self.log)
        self.assertEqual(au.user["a"], "123")
        self.assertEqual(au.user["asd"], "fgh:jkl")
        n = au.vfs
        # root was not defined, so PWD with no access to anyone
        self.assertEqual(n.vpath, "")
        self.assertEqual(n.realpath, td)
        self.assertEqual(n.uread, [])
        self.assertEqual(n.uwrite, [])
        self.assertEqual(len(n.nodes), 1)
        n = n.nodes["dst"]
        self.assertEqual(n.vpath, "dst")
        self.assertEqual(n.realpath, td + "/src")
        self.assertEqual(n.uread, ["a", "asd"])
        self.assertEqual(n.uwrite, ["asd"])
        self.assertEqual(len(n.nodes), 0)

        shutil.rmtree(td)
        os.unlink(cfg_path)

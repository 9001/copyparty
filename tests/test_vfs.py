#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import json
import shutil
import tempfile
import unittest

from textwrap import dedent
from argparse import Namespace
from copyparty.authsrv import AuthSrv
from copyparty import util

from tests import util as tu


class Cfg(Namespace):
    def __init__(self, a=[], v=[], c=None):
        ex = {k: False for k in "e2d e2ds e2dsa e2t e2ts e2tsr".split()}
        ex["mtp"] = []
        ex["mte"] = "a"
        super(Cfg, self).__init__(a=a, v=v, c=c, **ex)


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

    def ls(self, vfs, vpath, uname):
        """helper for resolving and listing a folder"""
        vn, rem = vfs.get(vpath, uname, True, False)
        r1 = vn.ls(rem, uname, False)
        r2 = vn.ls(rem, uname, False)
        self.assertEqual(r1, r2)

        fsdir, real, virt = r1
        real = [x[0] for x in real]
        return fsdir, real, virt

    def log(self, src, msg, c=0):
        pass

    def test(self):
        td = os.path.join(tu.get_ramdisk(), "vfs")
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
        vfs = AuthSrv(Cfg(), self.log).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td)
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, ["*"])

        # single read-only rootfs (relative path)
        vfs = AuthSrv(Cfg(v=["a/ab/::r"]), self.log).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, os.path.join(td, "a", "ab"))
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, [])

        # single read-only rootfs (absolute path)
        vfs = AuthSrv(Cfg(v=[td + "//a/ac/../aa//::r"]), self.log).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, os.path.join(td, "a", "aa"))
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, [])

        # read-only rootfs with write-only subdirectory (read-write for k)
        vfs = AuthSrv(
            Cfg(a=["k:k"], v=[".::r:ak", "a/ac/acb:a/ac/acb:w:ak"]),
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
        self.assertEqual(n.realpath, os.path.join(td, "a", "ac", "acb"))
        self.assertEqual(n.uread, ["k"])
        self.assertEqual(n.uwrite, ["*", "k"])

        # something funky about the windows path normalization,
        # doesn't really matter but makes the test messy, TODO?

        fsdir, real, virt = self.ls(vfs, "/", "*")
        self.assertEqual(fsdir, td)
        self.assertEqual(real, ["b", "c"])
        self.assertEqual(list(virt), ["a"])

        fsdir, real, virt = self.ls(vfs, "a", "*")
        self.assertEqual(fsdir, os.path.join(td, "a"))
        self.assertEqual(real, ["aa", "ab"])
        self.assertEqual(list(virt), ["ac"])

        fsdir, real, virt = self.ls(vfs, "a/ab", "*")
        self.assertEqual(fsdir, os.path.join(td, "a", "ab"))
        self.assertEqual(real, ["aba", "abb", "abc"])
        self.assertEqual(list(virt), [])

        fsdir, real, virt = self.ls(vfs, "a/ac", "*")
        self.assertEqual(fsdir, os.path.join(td, "a", "ac"))
        self.assertEqual(real, ["aca", "acc"])
        self.assertEqual(list(virt), [])

        fsdir, real, virt = self.ls(vfs, "a/ac", "k")
        self.assertEqual(fsdir, os.path.join(td, "a", "ac"))
        self.assertEqual(real, ["aca", "acc"])
        self.assertEqual(list(virt), ["acb"])

        self.assertRaises(util.Pebkac, vfs.get, "a/ac/acb", "*", True, False)

        fsdir, real, virt = self.ls(vfs, "a/ac/acb", "k")
        self.assertEqual(fsdir, os.path.join(td, "a", "ac", "acb"))
        self.assertEqual(real, ["acba", "acbb", "acbc"])
        self.assertEqual(list(virt), [])

        # admin-only rootfs with all-read-only subfolder
        vfs = AuthSrv(
            Cfg(a=["k:k"], v=[".::ak", "a:a:r"]),
            self.log,
        ).vfs
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td)
        self.assertEqual(vfs.uread, ["k"])
        self.assertEqual(vfs.uwrite, ["k"])
        n = vfs.nodes["a"]
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(n.vpath, "a")
        self.assertEqual(n.realpath, os.path.join(td, "a"))
        self.assertEqual(n.uread, ["*"])
        self.assertEqual(n.uwrite, [])
        self.assertEqual(vfs.can_access("/", "*"), [False, False])
        self.assertEqual(vfs.can_access("/", "k"), [True, True])
        self.assertEqual(vfs.can_access("/a", "*"), [True, False])
        self.assertEqual(vfs.can_access("/a", "k"), [True, False])

        # breadth-first construction
        vfs = AuthSrv(
            Cfg(
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
        vfs = AuthSrv(Cfg(v=[".::r", "b:a/ac:r"]), self.log).vfs

        fsp, r1, v1 = self.ls(vfs, "", "*")
        self.assertEqual(fsp, td)
        self.assertEqual(r1, ["b", "c"])
        self.assertEqual(list(v1), ["a"])

        fsp, r1, v1 = self.ls(vfs, "a", "*")
        self.assertEqual(fsp, os.path.join(td, "a"))
        self.assertEqual(r1, ["aa", "ab"])
        self.assertEqual(list(v1), ["ac"])

        fsp1, r1, v1 = self.ls(vfs, "a/ac", "*")
        fsp2, r2, v2 = self.ls(vfs, "b", "*")
        self.assertEqual(fsp1, os.path.join(td, "b"))
        self.assertEqual(fsp2, os.path.join(td, "b"))
        self.assertEqual(r1, ["ba", "bb", "bc"])
        self.assertEqual(r1, r2)
        self.assertEqual(list(v1), list(v2))

        # config file parser
        cfg_path = os.path.join(tu.get_ramdisk(), "test.cfg")
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

        au = AuthSrv(Cfg(c=[cfg_path]), self.log)
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
        self.assertEqual(n.realpath, os.path.join(td, "src"))
        self.assertEqual(n.uread, ["a", "asd"])
        self.assertEqual(n.uwrite, ["asd"])
        self.assertEqual(len(n.nodes), 0)

        os.chdir(tempfile.gettempdir())
        shutil.rmtree(td)
        os.unlink(cfg_path)

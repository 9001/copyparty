#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import os
import json
import shutil
import unittest

from argparse import Namespace
from copyparty.authsrv import *


class TestVFS(unittest.TestCase):
    def dump(self, vfs):
        print(json.dumps(vfs, indent=4, sort_keys=True, default=lambda o: o.__dict__))

    def test(self):
        td = "/dev/shm/vfs"
        try:
            shutil.rmtree(td)
        except:
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
        vfs = AuthSrv(Namespace(c=None, a=[], v=[]), None).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td)
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, ["*"])

        # single read-only rootfs (relative path)
        vfs = AuthSrv(Namespace(c=None, a=[], v=["a/ab/::r"]), None).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td + "/a/ab")
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, [])

        # single read-only rootfs (absolute path)
        vfs = AuthSrv(Namespace(c=None, a=[], v=[td + "//a/ac/../aa//::r"]), None).vfs
        self.assertEqual(vfs.nodes, {})
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td + "/a/aa")
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, [])

        # read-only rootfs with write-only subdirectory
        vfs = AuthSrv(
            Namespace(c=None, a=[], v=[".::r", "a/ac/acb:a/ac/acb:w"]), None
        ).vfs
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(vfs.vpath, "")
        self.assertEqual(vfs.realpath, td)
        self.assertEqual(vfs.uread, ["*"])
        self.assertEqual(vfs.uwrite, [])
        n = vfs.nodes["a"]
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(n.vpath, "a")
        self.assertEqual(n.realpath, td + "/a")
        self.assertEqual(n.uread, ["*"])
        self.assertEqual(n.uwrite, [])
        n = n.nodes["ac"]
        self.assertEqual(len(vfs.nodes), 1)
        self.assertEqual(n.vpath, "a/ac")
        self.assertEqual(n.realpath, td + "/a/ac")
        self.assertEqual(n.uread, ["*"])
        self.assertEqual(n.uwrite, [])
        n = n.nodes["acb"]
        self.assertEqual(n.nodes, {})
        self.assertEqual(n.vpath, "a/ac/acb")
        self.assertEqual(n.realpath, td + "/a/ac/acb")
        self.assertEqual(n.uread, [])
        self.assertEqual(n.uwrite, ["*"])

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
            None,
        ).vfs

        # shadowing
        # crossreferences
        # loops
        # listdir mapping
        # access reduction

        shutil.rmtree(td)

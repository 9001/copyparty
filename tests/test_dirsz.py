#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

import os
import shutil
import unittest

from copyparty.authsrv import AuthSrv
from tests import util as tu
from tests.util import Cfg


class TestDirSize(unittest.TestCase):
    def setUp(self):
        self.td = tu.get_ramdisk()
        for dn, data in [("src", b"one"), ("dst", b"other")]:
            dn = os.path.join(self.td, dn)
            os.mkdir(dn)
            with open(os.path.join(dn, "file"), "wb") as f:
                f.write(data)

    def tearDown(self):
        self.up2k.shutdown()
        shutil.rmtree(self.td)

    def cinit(self):
        args = Cfg(v=[self.td + "::A"], e2dsa=True)
        asrv = AuthSrv(args, tu.nah)
        self.up2k = tu.VHub(args, asrv, tu.nah).up2k
        self.cur = next(iter(self.up2k.cur.values()))

    def assertStats(self, expected):
        rows = self.cur.execute("select rd,sz,nf from ds order by rd").fetchall()
        self.assertEqual(expected, rows)

    def test_move(self):
        self.cinit()
        self.up2k.handle_mv("", "*", "127.0.0.1", "src/file", "dst/new/file")
        self.assertStats([("", 8, 2), ("dst", 8, 2), ("dst/new", 3, 1), ("src", 0, 0)])

    def test_copy(self):
        self.cinit()
        self.up2k.handle_cp("", "*", "127.0.0.1", "src/file", "dst/new/file")
        self.assertStats([("", 11, 3), ("dst", 8, 2), ("dst/new", 3, 1), ("src", 3, 1)])

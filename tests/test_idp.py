#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import json
import os
import unittest

from copyparty.authsrv import AuthSrv
from tests.util import Cfg


class TestVFS(unittest.TestCase):
    def dump(self, vfs):
        print(json.dumps(vfs, indent=4, sort_keys=True, default=lambda o: o.__dict__))

    def log(self, src, msg, c=0):
        print(("[%s] %s" % (src, msg)).encode("ascii", "replace").decode("ascii"))

    def nav(self, au, vp):
        return au.vfs.get(vp, "", False, False)[0]

    def assertAxs(self, axs, expected):
        unpacked = []
        zs = "uread uwrite umove udel uget upget uhtml uadmin udot"
        for k in zs.split():
            unpacked.append(list(sorted(getattr(axs, k))))

        pad = len(unpacked) - len(expected)
        self.assertEqual(unpacked, expected + [[]] * pad)

    def assertAxsAt(self, au, vp, expected):
        self.assertAxs(self.nav(au, vp).axs, expected)

    def assertNodes(self, vfs, expected):
        got = list(sorted(vfs.nodes.keys()))
        self.assertEqual(got, expected)

    def assertNodesAt(self, au, vp, expected):
        self.assertNodes(self.nav(au, vp), expected)

    def prep(self):
        here = os.path.abspath(os.path.dirname(__file__))
        cfgdir = os.path.join(here, "res", "idp")

        # globals are applied by main so need to cheat a little
        xcfg = {"idp_h_usr": "x-idp-user", "idp_h_grp": "x-idp-group"}

        return here, cfgdir, xcfg

    # buckle up...

    def test_1(self):
        """
        trivial; volumes [/] and [/vb] with one user in [/] only
        """
        _, cfgdir, xcfg = self.prep()
        au = AuthSrv(Cfg(c=[cfgdir + "/1.conf"], **xcfg), self.log)

        self.assertEqual(au.vfs.vpath, "")
        self.assertEqual(au.vfs.realpath, "/")
        self.assertNodes(au.vfs, ["vb"])
        self.assertNodes(au.vfs.nodes["vb"], [])

        self.assertAxs(au.vfs.axs, [["ua"]])
        self.assertAxs(au.vfs.nodes["vb"].axs, [])

    def test_2(self):
        """
        users ua/ub/uc, group ga (ua+ub) in basic combinations
        """
        _, cfgdir, xcfg = self.prep()
        au = AuthSrv(Cfg(c=[cfgdir + "/2.conf"], **xcfg), self.log)

        self.assertEqual(au.vfs.vpath, "")
        self.assertEqual(au.vfs.realpath, "/")
        self.assertNodes(au.vfs, ["vb", "vc"])
        self.assertNodes(au.vfs.nodes["vb"], [])
        self.assertNodes(au.vfs.nodes["vc"], [])

        self.assertAxs(au.vfs.axs, [["ua", "ub"]])
        self.assertAxsAt(au, "vb", [["ua", "ub"]])  # same as:
        self.assertAxs(au.vfs.nodes["vb"].axs, [["ua", "ub"]])
        self.assertAxs(au.vfs.nodes["vc"].axs, [["ua", "ub", "uc"]])

    def test_3(self):
        """
        IdP-only; dynamically created volumes for users/groups
        """
        _, cfgdir, xcfg = self.prep()
        au = AuthSrv(Cfg(c=[cfgdir + "/3.conf"], **xcfg), self.log)

        self.assertEqual(au.vfs.vpath, "")
        self.assertEqual(au.vfs.realpath, "")
        self.assertNodes(au.vfs, [])
        self.assertAxs(au.vfs.axs, [])

        au.idp_checkin(None, "iua", "iga")
        self.assertNodes(au.vfs, ["vg", "vu"])
        self.assertNodesAt(au, "vu", ["iua"])  # same as:
        self.assertNodes(au.vfs.nodes["vu"], ["iua"])
        self.assertNodes(au.vfs.nodes["vg"], ["iga"])
        self.assertEqual(au.vfs.nodes["vu"].realpath, "")
        self.assertEqual(au.vfs.nodes["vg"].realpath, "")
        self.assertAxs(au.vfs.axs, [])
        self.assertAxsAt(au, "vu/iua", [["iua"]])  # same as:
        self.assertAxs(self.nav(au, "vu/iua").axs, [["iua"]])
        self.assertAxs(self.nav(au, "vg/iga").axs, [["iua"]])  # axs is unames

    def test_4(self):
        """
        IdP mixed with regular users
        """
        _, cfgdir, xcfg = self.prep()
        au = AuthSrv(Cfg(c=[cfgdir + "/4.conf"], **xcfg), self.log)

        self.assertEqual(au.vfs.vpath, "")
        self.assertEqual(au.vfs.realpath, "")
        self.assertNodes(au.vfs, ["vu"])
        self.assertNodesAt(au, "vu", ["ua", "ub"])
        self.assertAxs(au.vfs.axs, [])
        self.assertAxsAt(au, "vu", [])
        self.assertAxsAt(au, "vu/ua", [["ua"]])
        self.assertAxsAt(au, "vu/ub", [["ub"]])

        au.idp_checkin(None, "iua", "iga")
        self.assertNodes(au.vfs, ["vg", "vu"])
        self.assertNodesAt(au, "vu", ["iua", "ua", "ub"])
        self.assertNodesAt(au, "vg", ["iga1", "iga2"])
        self.assertAxs(au.vfs.axs, [])
        self.assertAxsAt(au, "vu", [])
        self.assertAxsAt(au, "vu/iua", [["iua"]])
        self.assertAxsAt(au, "vu/ua", [["ua"]])
        self.assertAxsAt(au, "vu/ub", [["ub"]])
        self.assertAxsAt(au, "vg", [])
        self.assertAxsAt(au, "vg/iga1", [["iua"]])
        self.assertAxsAt(au, "vg/iga2", [["iua", "ua"]])
        self.assertEqual(self.nav(au, "vu/ua").realpath, "/u-ua")
        self.assertEqual(self.nav(au, "vu/iua").realpath, "/u-iua")
        self.assertEqual(self.nav(au, "vg/iga1").realpath, "/g1-iga")
        self.assertEqual(self.nav(au, "vg/iga2").realpath, "/g2-iga")

    def test_5(self):
        """
        one IdP user in multiple groups
        """
        _, cfgdir, xcfg = self.prep()
        au = AuthSrv(Cfg(c=[cfgdir + "/5.conf"], **xcfg), self.log)

        self.assertEqual(au.vfs.vpath, "")
        self.assertEqual(au.vfs.realpath, "")
        self.assertNodes(au.vfs, ["g", "ga", "gb"])
        self.assertAxs(au.vfs.axs, [])

        au.idp_checkin(None, "iua", "ga")
        self.assertNodes(au.vfs, ["g", "ga", "gb"])
        self.assertAxsAt(au, "g", [["iua"]])
        self.assertAxsAt(au, "ga", [["iua"]])
        self.assertAxsAt(au, "gb", [])

        au.idp_checkin(None, "iua", "gb")
        self.assertNodes(au.vfs, ["g", "ga", "gb"])
        self.assertAxsAt(au, "g", [["iua"]])
        self.assertAxsAt(au, "ga", [])
        self.assertAxsAt(au, "gb", [["iua"]])

        au.idp_checkin(None, "iua", "ga|gb")
        self.assertNodes(au.vfs, ["g", "ga", "gb"])
        self.assertAxsAt(au, "g", [["iua"]])
        self.assertAxsAt(au, "ga", [["iua"]])
        self.assertAxsAt(au, "gb", [["iua"]])

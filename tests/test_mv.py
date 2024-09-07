#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import json
import os
import shutil
import tempfile
import unittest
from itertools import product

from copyparty.__init__ import PY2
from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg

"""
TODO inject tags into db and verify ls
"""


class TestDedup(unittest.TestCase):
    def setUp(self):
        self.td = tu.get_ramdisk()

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def reset(self):
        td = os.path.join(self.td, "vfs")
        if os.path.exists(td):
            shutil.rmtree(td)
        os.mkdir(td)
        os.chdir(td)
        return td

    def cinit(self):
        if self.conn:
            self.fstab = self.conn.hsrv.hub.up2k.fstab
            self.conn.hsrv.hub.up2k.shutdown()
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)
        if self.fstab:
            self.conn.hsrv.hub.up2k.fstab = self.fstab

    def test(self):
        if PY2:
            raise unittest.SkipTest()

        # tc_e2d = [True, False]  # maybe-TODO only known symlinks are translated
        tc_e2d = [True]
        tc_dedup = ["sym", "no", "sym-no"]
        tc_vols = [["::A"], ["::A", "d1:d1:A"]]
        dirs = ["d1", "d1/d2", "d1/d2/d3", "d1/d4"]
        files = [
            (
                "one",
                "BfcDQQeKz2oG1CPSFyD5ZD1flTYm2IoCY23DqeeVgq6w",
                "XMbpLRqVdtGmgggqjUI6uSoNMTqZVX4K6zr74XA1BRKc",
            )
        ]
        # (data, chash, wark)

        self.conn = None
        self.fstab = None
        self.ctr = 0  # 2304
        tcgen = product(tc_e2d, tc_dedup, tc_vols, dirs, ["d9", "../d9"])
        for e2d, dedup, vols, mv_from, dst in tcgen:
            if "/" not in mv_from and dst.startswith(".."):
                continue  # would move past top of fs
            if len(vols) > 1 and mv_from == "d1":
                continue  # cannot move a vol

            # print(e2d, dedup, vols, mv_from, dst)
            ka = {"e2d": e2d}
            if dedup == "hard":
                ka["hardlink"] = True
            elif dedup == "no":
                ka["no_dedup"] = True
            self.args = Cfg(v=vols[:], a=[], **ka)

            for u1, u2, u3, u4 in product(dirs, dirs, dirs, dirs):
                ups = (u1, u2, u3, u4)
                if len(set(ups)) < 4:
                    continue  # not unique

                t = "e2d:%s dedup:%s vols:%d from:%s to:%s"
                t = t % (e2d, dedup, len(vols), mv_from, dst)
                print("\n\n\033[0;7m# files:", ups, t, "\033[0m")

                self.reset()
                self.cinit()

                for up in [u1, u2, u3, u4]:
                    self.do_post(up, "fn", files[0], up == u1)

                restore_args = None
                if dedup == "sym-no":
                    restore_args = self.args
                    ka = {"e2d": e2d, "no_dedup": True}
                    self.args = Cfg(v=vols[:], a=[], **ka)
                    self.cinit()

                mv_to = mv_from
                for _ in range(2 if dst.startswith("../") else 1):
                    mv_to = mv_from.rsplit("/", 1)[0] if "/" in mv_from else ""
                mv_to += "/" + dst.lstrip("./")

                self.do_mv(mv_from, mv_to)

                for dirpath in [u1, u2, u3, u4]:
                    if dirpath == mv_from:
                        dirpath = mv_to
                    elif dirpath.startswith(mv_from):
                        dirpath = mv_to + dirpath[len(mv_from) :]
                    h, b = self.curl(dirpath + "/fn")
                    self.assertEqual(b, "one")

                if restore_args:
                    self.args = restore_args

    def do_mv(self, src, dst):
        hdr = "POST /%s?move=/%s HTTP/1.1\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
        buf = (hdr % (src, dst)).encode("utf-8")
        print("MV [%s] => [%s]" % (src, dst))
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("MV <-- ", ret)
        self.assertIn(" 201 Created", ret[0])
        self.assertEqual("k\r\n", ret[1])
        return ret

    def do_post(self, dn, fn, fi, first):
        print("\n# do_post", self.ctr, repr((dn, fn, fi, first)))
        self.ctr -= 1

        data, chash, wark = fi
        hs = self.handshake(dn, fn, fi)
        self.assertEqual(hs["wark"], wark)

        sfn = hs["name"]
        if sfn == fn:
            print("using original name " + fn)
        else:
            print(fn + " got renamed to " + sfn)
            if first:
                raise Exception("wait what")

        if hs["hash"]:
            self.assertEqual(hs["hash"][0], chash)
            self.put_chunk(dn, wark, chash, data)
        elif first:
            raise Exception("found first; %r, %r" % ((dn, fn, fi), hs))

        h, b = self.curl("%s/%s" % (dn, sfn))
        self.assertEqual(b, data)

    def handshake(self, dn, fn, fi):
        hdr = "POST /%s/ HTTP/1.1\r\nConnection: close\r\nContent-Type: text/plain\r\nContent-Length: %d\r\n\r\n"
        msg = {"name": fn, "size": 3, "lmod": 1234567890, "life": 0, "hash": [fi[1]]}
        buf = json.dumps(msg).encode("utf-8")
        buf = (hdr % (dn, len(buf))).encode("utf-8") + buf
        print("HS -->", buf)
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("HS <--", ret)
        return json.loads(ret[1])

    def put_chunk(self, dn, wark, chash, data):
        msg = [
            "POST /%s/ HTTP/1.1" % (dn,),
            "Connection: close",
            "Content-Type: application/octet-stream",
            "Content-Length: 3",
            "X-Up2k-Hash: " + chash,
            "X-Up2k-Wark: " + wark,
            "",
            data,
        ]
        buf = "\r\n".join(msg).encode("utf-8")
        print("PUT -->", buf)
        HttpCli(self.conn.setbuf(buf)).run()
        ret = self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        self.assertEqual(ret[1], "thank")

    def curl(self, url, binary=False):
        h = "GET /%s HTTP/1.1\r\nConnection: close\r\n\r\n"
        HttpCli(self.conn.setbuf((h % (url,)).encode("utf-8"))).run()
        if binary:
            h, b = self.conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

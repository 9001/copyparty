#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import io
import os
import time
import shutil
import pprint
import tarfile
import tempfile
import unittest
from argparse import Namespace

from tests import util as tu
from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli


def hdr(query):
    h = "GET /{} HTTP/1.1\r\nCookie: cppwd=o\r\nConnection: close\r\n\r\n"
    return h.format(query).encode("utf-8")


class Cfg(Namespace):
    def __init__(self, a=None, v=None, c=None):
        super(Cfg, self).__init__(
            a=a or [],
            v=v or [],
            c=c,
            rproxy=0,
            ed=False,
            nw=False,
            no_zip=False,
            no_scandir=False,
            no_sendfile=True,
            no_rescan=True,
            ihead=False,
            nih=True,
            mtp=[],
            mte="a",
            hist=None,
            no_hash=False,
            css_browser=None,
            **{k: False for k in "e2d e2ds e2dsa e2t e2ts e2tsr".split()}
        )


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

        self.dtypes = ["ra", "ro", "rx", "wa", "wo", "wx", "aa", "ao", "ax"]
        self.can_read = ["ra", "ro", "aa", "ao"]
        self.can_write = ["wa", "wo", "aa", "ao"]
        self.fn = "g{:x}g".format(int(time.time() * 3))

        allfiles = []
        allvols = []
        for top in self.dtypes:
            allvols.append(top)
            allfiles.append("/".join([top, self.fn]))
            for s1 in self.dtypes:
                p = "/".join([top, s1])
                allvols.append(p)
                allfiles.append(p + "/" + self.fn)
                allfiles.append(p + "/n/" + self.fn)
                for s2 in self.dtypes:
                    p = "/".join([top, s1, "n", s2])
                    os.makedirs(p)
                    allvols.append(p)
                    allfiles.append(p + "/" + self.fn)

        for fp in allfiles:
            with open(fp, "w") as f:
                f.write("ok {}\n".format(fp))

        for top in self.dtypes:
            vcfg = []
            for vol in allvols:
                if not vol.startswith(top):
                    continue

                mode = vol[-2]
                usr = vol[-1]
                if usr == "a":
                    usr = ""

                if "/" not in vol:
                    vol += "/"

                top, sub = vol.split("/", 1)
                vcfg.append("{0}/{1}:{1}:{2}{3}".format(top, sub, mode, usr))

            pprint.pprint(vcfg)

            self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
            self.asrv = AuthSrv(self.args, self.log)
            vfiles = [x for x in allfiles if x.startswith(top)]
            for fp in vfiles:
                rok, wok = self.can_rw(fp)
                furl = fp.split("/", 1)[1]
                durl = furl.rsplit("/", 1)[0] if "/" in furl else ""

                # file download
                h, ret = self.curl(furl)
                res = "ok " + fp in ret
                print("[{}] {} {} = {}".format(fp, rok, wok, res))
                if rok != res:
                    print("\033[33m{}\n# {}\033[0m".format(ret, furl))
                    self.fail()

                # file browser: html
                h, ret = self.curl(durl)
                res = "'{}'".format(self.fn) in ret
                print(res)
                if rok != res:
                    print("\033[33m{}\n# {}\033[0m".format(ret, durl))
                    self.fail()

                # file browser: json
                url = durl + "?ls"
                h, ret = self.curl(url)
                res = '"{}"'.format(self.fn) in ret
                print(res)
                if rok != res:
                    print("\033[33m{}\n# {}\033[0m".format(ret, url))
                    self.fail()

                # tar
                url = durl + "?tar"
                h, b = self.curl(url, True)
                # with open(os.path.join(td, "tar"), "wb") as f:
                #    f.write(b)
                try:
                    tar = tarfile.open(fileobj=io.BytesIO(b)).getnames()
                except:
                    tar = []
                tar = ["/".join([y for y in [top, durl, x] if y]) for x in tar]
                tar = [[x] + self.can_rw(x) for x in tar]
                tar_ok = [x[0] for x in tar if x[1]]
                tar_ng = [x[0] for x in tar if not x[1]]
                self.assertEqual([], tar_ng)

                if durl.split("/")[-1] in self.can_read:
                    ref = [x for x in vfiles if self.in_dive(top + "/" + durl, x)]
                    for f in ref:
                        print("{}: {}".format("ok" if f in tar_ok else "NG", f))
                    ref.sort()
                    tar_ok.sort()
                    self.assertEqual(ref, tar_ok)

                # stash
                h, ret = self.put(url)
                res = h.startswith("HTTP/1.1 200 ")
                self.assertEqual(res, wok)

    def can_rw(self, fp):
        # lowest non-neutral folder declares permissions
        expect = fp.split("/")[:-1]
        for x in reversed(expect):
            if x != "n":
                expect = x
                break

        return [expect in self.can_read, expect in self.can_write]

    def in_dive(self, top, fp):
        # archiver bails at first inaccessible subvolume
        top = top.strip("/").split("/")
        fp = fp.split("/")
        for f1, f2 in zip(top, fp):
            if f1 != f2:
                return False

        for f in fp[len(top) :]:
            if f == self.fn:
                return True
            if f not in self.can_read and f != "n":
                return False

        return True

    def put(self, url):
        buf = "PUT /{0} HTTP/1.1\r\nCookie: cppwd=o\r\nConnection: close\r\nContent-Length: {1}\r\n\r\nok {0}\n"
        buf = buf.format(url, len(url) + 4).encode("utf-8")
        conn = tu.VHttpConn(self.args, self.asrv, self.log, buf)
        HttpCli(conn).run()
        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def curl(self, url, binary=False):
        conn = tu.VHttpConn(self.args, self.asrv, self.log, hdr(url))
        HttpCli(conn).run()
        if binary:
            h, b = conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        # print(repr(msg))
        pass

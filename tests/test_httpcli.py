#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import io
import os
import pprint
import shutil
import tarfile
import tempfile
import time
import unittest
import zipfile

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg, eprint


def hdr(query):
    h = "GET /{} HTTP/1.1\r\nCookie: cppwd=o\r\nConnection: close\r\n\r\n"
    return h.format(query).encode("utf-8")


class TestHttpCli(unittest.TestCase):
    def setUp(self):
        self.td = tu.get_ramdisk()

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def test(self):
        test_tar = True
        test_zip = True

        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        self.dtypes = ["ra", "ro", "rx", "wa", "wo", "wx", "aa", "ao", "ax"]
        self.can_read = ["ra", "ro", "aa", "ao"]
        self.can_write = ["wa", "wo", "aa", "ao"]
        self.fn = "g{:x}g".format(int(time.time() * 3))

        tctr = 0
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

                mode = vol[-2].replace("a", "rw")
                usr = vol[-1]
                if usr == "a":
                    usr = ""

                if "/" not in vol:
                    vol += "/"

                top, sub = vol.split("/", 1)
                vcfg.append("{0}/{1}:{1}:{2},{3}".format(top, sub, mode, usr))

            pprint.pprint(vcfg)

            self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
            self.asrv = AuthSrv(self.args, self.log)
            vfiles = [x for x in allfiles if x.startswith(top)]
            for fp in vfiles:
                tctr += 1
                rok, wok = self.can_rw(fp)
                furl = fp.split("/", 1)[1]
                durl = furl.rsplit("/", 1)[0] if "/" in furl else ""

                # file download
                h, ret = self.curl(furl)
                res = "ok " + fp in ret
                print("[{}] {} {} = {}".format(fp, rok, wok, res))
                if rok != res:
                    eprint("\033[33m{}\n# {}\033[0m".format(ret, furl))
                    self.fail()

                # file browser: html
                h, ret = self.curl(durl)
                res = "'{}'".format(self.fn) in ret
                print(res)
                if rok != res:
                    eprint("\033[33m{}\n# {}\033[0m".format(ret, durl))
                    self.fail()

                # file browser: json
                url = durl + "?ls"
                h, ret = self.curl(url)
                res = '"{}"'.format(self.fn) in ret
                print(res)
                if rok != res:
                    eprint("\033[33m{}\n# {}\033[0m".format(ret, url))
                    self.fail()

                # expected files in archives
                if rok:
                    ref = [x for x in vfiles if self.in_dive(top + "/" + durl, x)]
                    ref.sort()
                else:
                    ref = []

                if test_tar:
                    url = durl + "?tar"
                    h, b = self.curl(url, True)
                    try:
                        tar = tarfile.open(fileobj=io.BytesIO(b), mode="r|").getnames()
                    except:
                        if "HTTP/1.1 403 Forbidden" not in h and b != b"\nJ2EOT":
                            eprint("bad tar?", url, h, b)
                            raise
                        tar = []
                    tar = [x.split("/", 1)[1] for x in tar]
                    tar = ["/".join([y for y in [top, durl, x] if y]) for x in tar]
                    tar = [[x] + self.can_rw(x) for x in tar]
                    tar_ok = [x[0] for x in tar if x[1]]
                    tar_ng = [x[0] for x in tar if not x[1]]
                    tar_ok.sort()
                    self.assertEqual(ref, tar_ok)
                    self.assertEqual([], tar_ng)

                if test_zip:
                    url = durl + "?zip"
                    h, b = self.curl(url, True)
                    try:
                        with zipfile.ZipFile(io.BytesIO(b), "r") as zf:
                            zfi = zf.infolist()
                    except:
                        if "HTTP/1.1 403 Forbidden" not in h and b != b"\nJ2EOT":
                            eprint("bad zip?", url, h, b)
                            raise
                        zfi = []
                    zfn = [x.filename.split("/", 1)[1] for x in zfi]
                    zfn = ["/".join([y for y in [top, durl, x] if y]) for x in zfn]
                    zfn = [[x] + self.can_rw(x) for x in zfn]
                    zf_ok = [x[0] for x in zfn if x[1]]
                    zf_ng = [x[0] for x in zfn if not x[1]]
                    zf_ok.sort()
                    self.assertEqual(ref, zf_ok)
                    self.assertEqual([], zf_ng)

                # stash
                h, ret = self.put(url)
                res = h.startswith("HTTP/1.1 201 ")
                self.assertEqual(res, wok)
                if wok:
                    vp = h.split("\nLocation: http://a:1/")[1].split("\r")[0]
                    vn, rem = self.asrv.vfs.get(vp, "*", False, False)
                    ap = os.path.join(vn.realpath, rem)
                    os.unlink(ap)

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
        print("PUT -->", buf)
        conn = tu.VHttpConn(self.args, self.asrv, self.log, buf)
        HttpCli(conn).run()
        ret = conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)
        print("PUT <--", ret)
        return ret

    def curl(self, url, binary=False):
        conn = tu.VHttpConn(self.args, self.asrv, self.log, hdr(url))
        HttpCli(conn).run()
        if binary:
            h, b = conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

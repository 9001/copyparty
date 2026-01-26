#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import shutil
import tempfile
import time
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import TC, Cfg, pfind2ls

# tcpdump of `rclone ls dav:`
RCLONE_PROPFIND = """PROPFIND /%s HTTP/1.1
Host: 127.0.0.1:3923
User-Agent: rclone/v1.67.0
Content-Length: 308
Authorization: Basic azp1
Depth: 1
Referer: http://127.0.0.1:3923/
Accept-Encoding: gzip

<?xml version="1.0"?>
<d:propfind  xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
 <d:prop>
  <d:displayname />
  <d:getlastmodified />
  <d:getcontentlength />
  <d:resourcetype />
  <d:getcontenttype />
  <oc:checksums />
  <oc:permissions />
 </d:prop>
</d:propfind>
"""


# tcpdump of `rclone copy fa dav:/a/`  (it does a mkcol first)
RCLONE_MKCOL = """MKCOL /%s HTTP/1.1
Host: 127.0.0.1:3923
User-Agent: rclone/v1.67.0
Authorization: Basic azp1
Referer: http://127.0.0.1:3923/
Accept-Encoding: gzip
\n"""


# tcpdump of `rclone copy fa dav:/a/`  (the actual upload)
RCLONE_PUT = """PUT /%s HTTP/1.1
Host: 127.0.0.1:3923
User-Agent: rclone/v1.67.0
Content-Length: 6
Authorization: Basic azp1
Content-Type: application/octet-stream
Oc-Checksum: SHA1:f5e3dc3fb27af53cd0005a1184e2df06481199e8
Referer: http://127.0.0.1:3923/
X-Oc-Mtime: 1689453578
Accept-Encoding: gzip

fgsfds"""


RCLONE_PUT_FLOAT = """PUT /%s HTTP/1.1
Host: 127.0.0.1:3923
User-Agent: rclone/v1.67.0
Content-Length: 6
Authorization: Basic azp1
Content-Type: application/octet-stream
Oc-Checksum: SHA1:f5e3dc3fb27af53cd0005a1184e2df06481199e8
Referer: http://127.0.0.1:3923/
X-Oc-Mtime: 1689453578.123
Accept-Encoding: gzip

fgsfds"""


# tcpdump of `rclone delete dav:/a/d1/`  (it does propfind recursively and then this on each file)
# (note: `rclone rmdirs dav:/a/d1/` does the same thing but just each folder after asserting they're empty)
RCLONE_DELETE = """DELETE /%s HTTP/1.1
Host: 127.0.0.1:3923
User-Agent: rclone/v1.67.0
Authorization: Basic azp1
Referer: http://127.0.0.1:3923/
Accept-Encoding: gzip
\n"""


# tcpdump of `rclone move dav:/a/d1/d2 /a/d1/d3`  (it does a lot of boilerplate propfinds/mkcols before)
RCLONE_MOVE = """MOVE /%s HTTP/1.1
Host: 127.0.0.1:3923
User-Agent: rclone/v1.67.0
Authorization: Basic azp1
Destination: http://127.0.0.1:3923/%s
Overwrite: T
Referer: http://127.0.0.1:3923/
Accept-Encoding: gzip
\n"""


class TestHttpCli(TC):
    def setUp(self):
        self.td = tu.get_ramdisk()
        self.maxDiff = 99999

    def tearDown(self):
        self.conn.shutdown()
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def test(self):
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        self.fn = "g{:x}g".format(int(time.time() * 3))
        vcfg = [
            "r:r:r,u",
            "w:w:w,u",
            "a:a:A,u",
            "x:x:r,u2",
            "x/r:x/r:r,u",
            "x/x:x/x:r,u2",
        ]
        self.args = Cfg(v=vcfg, a=["u:u", "u2:u2"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)

        self.fns = ["%s/%s" % (zs.split(":")[0], self.fn) for zs in vcfg]
        for fp in self.fns:
            try:
                os.makedirs(os.path.dirname(fp))
            except:
                pass
            with open(fp, "wb") as f:
                f.write(("ok %s\n" % (fp,)).encode("utf-8"))

        ##
        ## depth:1 (regular listing)

        # unmapped root; should return list of volumes
        h, b = self.req(RCLONE_PROPFIND % ("",))
        fns = pfind2ls(b)
        self.assertStart("HTTP/1.1 207 Multi-Status\r", h)
        self.assertListEqual(fns, ["/", "/a/", "/r/"])

        # toplevel of a volume; has one file
        h, b = self.req(RCLONE_PROPFIND % ("a",))
        fns = pfind2ls(b)
        self.assertStart("HTTP/1.1 207 Multi-Status\r", h)
        self.assertListEqual(fns, ["/a/", "/a/" + self.fn])

        # toplevel of a volume; has one file
        h, b = self.req(RCLONE_PROPFIND % ("r",))
        fns = pfind2ls(b)
        self.assertStart("HTTP/1.1 207 Multi-Status\r", h)
        self.assertListEqual(fns, ["/r/", "/r/" + self.fn])

        # toplevel of write-only volume; has one file, will not list
        h, b = self.req(RCLONE_PROPFIND % ("w",))
        fns = pfind2ls(b)
        self.assertStart("HTTP/1.1 207 Multi-Status\r", h)
        self.assertListEqual(fns, ["/w/"])

        ##
        ## auth challenge

        bad_pfind = RCLONE_PROPFIND.replace("Authorization: Basic azp1\n", "")
        bad_put = RCLONE_PUT.replace("Authorization: Basic azp1\n", "")
        urls = ["", "r", "w", "a"]
        urls += [x + "/" + self.fn for x in urls[1:]]
        for url in urls:
            for q in (bad_pfind, bad_put):
                h, b = self.req(q % (url,))
                self.assertStart("HTTP/1.1 401 Unauthorized\r", h)
                self.assertIn('\nWWW-Authenticate: Basic realm="a"\r', h)

        ##
        ## depth:0 (recursion)

        # depth:0 from unmapped root should work;
        # will NOT list contents of /x/r/ due to current limitations
        # (stops descending at first non-accessible volume)
        recursive = RCLONE_PROPFIND.replace("Depth: 1\n", "")
        h, b = self.req(recursive % ("",))
        fns = pfind2ls(b)
        expect = ["/", "/a/", "/r/"]
        expect += [x + self.fn for x in expect[1:]]
        self.assertListEqual(fns, expect)

        # same thing here...
        h, b = self.req(recursive % ("/x",))
        fns = pfind2ls(b)
        self.assertListEqual(fns, [])

        # but this obviously works
        h, b = self.req(recursive % ("/x/r",))
        fns = pfind2ls(b)
        self.assertListEqual(fns, ["/x/r/", "/x/r/" + self.fn])

        ##
        ## uploading

        # rclone does a propfind on the target file first; expects 404
        h, b = self.req(RCLONE_PROPFIND % ("a/fa",))
        self.assertStart("HTTP/1.1 404 Not Found\r", h)

        # then it does a mkcol (mkdir), expecting 405 (exists)
        h, b = self.req(RCLONE_MKCOL % ("a",))
        self.assertStart("HTTP/1.1 405 Method Not Allowed\r", h)

        # then it uploads the file
        h, b = self.req(RCLONE_PUT % ("a/fa",))
        self.assertStart("HTTP/1.1 201 Created\r", h)

        # float x-oc-mtime should be accepted
        h, b = self.req(RCLONE_PUT_FLOAT % ("a/fb",))
        self.assertStart("HTTP/1.1 201 Created\r", h)
        self.assertAlmostEqual(os.path.getmtime("a/fb"), 1689453578.123, places=3)

        # then it does a propfind to confirm
        h, b = self.req(RCLONE_PROPFIND % ("a/fa",))
        fns = pfind2ls(b)
        self.assertStart("HTTP/1.1 207 Multi-Status\r", h)
        self.assertListEqual(fns, ["/a/fa"])

        ##
        ## upload into set of subfolders that don't exist yet

        # rclone does this:
        # propfind /a/d1/d2/fa => 404
        # mkcol /a/d1/d2/ => 409
        # propfind /a/d1/d2/ => 404
        # mkcol /a/d1/ => 201
        # mkcol /a/d1/d2/ => 201
        # put /a/d1/d2/fa => 201
        # propfind /a/d1/d2/fa => 207
        # ...some of which already tested above;

        h, b = self.req(RCLONE_PROPFIND % ("/a/d1/d2/",))
        self.assertStart("HTTP/1.1 404 Not Found\r", h)

        h, b = self.req(RCLONE_PROPFIND % ("/a/d1/",))
        self.assertStart("HTTP/1.1 404 Not Found\r", h)

        h, b = self.req(RCLONE_MKCOL % ("/a/d1/d2/",))
        self.assertStart("HTTP/1.1 409 Conflict\r", h)

        h, b = self.req(RCLONE_MKCOL % ("/a/d1/",))
        self.assertStart("HTTP/1.1 201 Created\r", h)

        h, b = self.req(RCLONE_MKCOL % ("/a/d1/d2/",))
        self.assertStart("HTTP/1.1 201 Created\r", h)

        h, b = self.req(RCLONE_PUT % ("a/d1/d2/fa",))
        self.assertStart("HTTP/1.1 201 Created\r", h)

        ##
        ## rename

        h, b = self.req(RCLONE_MOVE % ("a/d1/d2/", "a/d1/d3/"))
        self.assertStart("HTTP/1.1 201 Created\r", h)
        self.assertListEqual(os.listdir("a/d1"), ["d3"])

        ##
        ## delete

        h, b = self.req(RCLONE_DELETE % ("a/d1",))
        self.assertStart("HTTP/1.1 200 OK\r", h)
        if os.path.exists("a/d1"):
            self.fail("a/d1 still exists")

    def req(self, q):
        h, b = q.split("\n\n", 1)
        q = h.replace("\n", "\r\n") + "\r\n\r\n" + b
        conn = self.conn.setbuf(q.encode("utf-8"))
        HttpCli(conn).run()
        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

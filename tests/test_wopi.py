#!/usr/bin/env python3
# coding: utf-8
from __future__ import division, print_function, unicode_literals

import io
import json
import os
import re
import shutil
import sqlite3
import tempfile

from copyparty import httpcli
from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import J2_ENV, Cfg


DISCOVERY_DOC = """<?xml version="1.0" encoding="utf-8"?>
<wopi-discovery><net-zone name="external-http">
<app name="writer">
<action default="true" ext="odt" name="edit" urlsrc="http://wc/edit?"/>
<action ext="odt" name="view" urlsrc="http://wc/view?"/>
</app>
<app name="calc">
<action default="true" ext="ods" name="edit" urlsrc="http://wc/edit?"/>
</app>
</net-zone></wopi-discovery>
"""


def get_request(path, password):
    """GET request for path; the test accounts use their username as password"""
    request = "GET /%s HTTP/1.1\r\nPW: %s\r\nConnection: close\r\n\r\n"
    return (request % (path, password)).encode("utf-8")


class TestWopi(tu.TC):
    def setUp(self):
        self.conn = None
        self.tmp_dir = tu.get_ramdisk()
        vfs_dir = os.path.join(self.tmp_dir, "vfs")
        os.mkdir(vfs_dir)
        os.chdir(vfs_dir)
        os.mkdir("priv")
        os.mkdir("pub")
        for path in ("priv/a.odt", "priv/b.ods", "pub/a.odt"):
            with open(path, "wb") as f:
                f.write(path.encode("utf-8"))

        db = sqlite3.connect("a.db")
        with db:
            schema = """create table sh(
                k text,
                pw text,
                vp text,
                pr text,
                st int,
                un text,
                t0 int,
                t1 int
            )"""
            db.execute(schema)
        db.close()

        self.real_urlopen = httpcli.urlopen
        discovery = DISCOVERY_DOC.encode("utf-8")
        httpcli.urlopen = lambda *args, **kwargs: io.BytesIO(discovery)

    def tearDown(self):
        httpcli.urlopen = self.real_urlopen
        if self.conn:
            self.conn.shutdown()
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.tmp_dir)

    def copyparty_init(
        self,
        anon_ro="",
        keep_sessions=False,
        wopi_accs="",
        revoke_write=False,
        wopi_wdel=False,
    ):
        """configure copyparty with the given parameters"""
        volumes = ["priv:priv:r,reader:rw,writer:g,getter", "pub:pub:r:rw,writer"]
        if revoke_write:
            volumes[0] = "priv:priv:r,reader,writer:g,getter"
        self.args = Cfg(
            v=volumes,
            a=["writer:writer", "reader:reader", "getter:getter"],
            shr="/shr/",
            shr1="shr/",
            shr_db="a.db",
            shr_v=False,
            wopi=True,
            wopi_accs=wopi_accs,
            wopi_api="",
            wopi_crt="",
            wopi_anon_ro=anon_ro,
            wopi_salt="hunter2",
            wopi_ttl=1800,
            wopi_url="http://wc",
            wopi_urls=None,
            wopi_wdel=wopi_wdel,
        )
        self.auth_srv = AuthSrv(self.args, self.log)
        sessions = self.conn.hsrv.wopi_files if keep_sessions else None
        if self.conn:
            self.conn.shutdown()
        self.conn = tu.VHttpConn(self.args, self.auth_srv, self.log, b"", True)
        if sessions is not None:
            self.conn.hsrv.wopi_files = sessions
        self.conn.hsrv.j2["wopi"] = J2_ENV.from_string("{{ url }} {{ atoken }}")

    def curl(self, request):
        HttpCli(self.conn.setbuf(request)).run()
        return self.conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def open(self, path, password):
        """open path as user; returns (url, file_id, token), or (status, None, None)"""
        folder, filename = path.rsplit("/", 1)
        headers, body = self.curl(
            get_request("%s/?wopi=%s" % (folder, filename), password)
        )
        if not headers.startswith("HTTP/1.1 200 "):
            return headers.split(" ")[1], None, None
        url, token = body.split(" ")
        file_id = re.search(r"/wopi/files/([^&]+)", url.replace("%2F", "/")).group(1)
        return url.split("?")[0], file_id, token

    def wopi_check_file_info(self, file_id, token):
        """WOPI client GETs file info from copyparty.

        returns the json response for further inspection, or the status code on error
        """
        path = "wopi/files/%s?access_token=%s" % (file_id, token)
        headers, body = self.curl(get_request(path, ""))
        if not headers.startswith("HTTP/1.1 200 "):
            return headers.split(" ")[1]
        return json.loads(body)

    def wopi_put_file(self, file_id, token, content):
        """WOPI client POSTs file to copyparty; returns the status code"""
        request = "POST /wopi/files/%s/contents?access_token=%s HTTP/1.1\r\n"
        request += "Content-Type: application/octet-stream\r\nContent-Length: %d\r\n"
        request += "Connection: close\r\n\r\n"
        request = request % (file_id, token, len(content))
        headers, _ = self.curl(request.encode("utf-8") + content)
        return headers.split(" ")[1]

    def share(self, name, password):
        """as writer user, create read-only share named name of /priv with password"""
        share_cfg = {
            "k": name,
            "vp": ["/priv/"],
            "pw": password,
            "exp": "99",
            "perms": ["read"],
        }
        payload = json.dumps(share_cfg).encode("utf-8")
        request = "POST /priv/?share HTTP/1.1\r\nPW: writer\r\nConnection: close\r\n"
        request += "Content-Type: application/json\r\nContent-Length: %d\r\n\r\n"
        request = (request % (len(payload),)).encode("utf-8") + payload
        headers, _ = self.curl(request)
        self.assertStart("HTTP/1.1 201 ", headers)

    def assertMode(self, path, password, writable, disk_path=None):
        """open path as user; check edit/read-only mode, download, and save"""
        disk_path = disk_path or path
        original = disk_path.encode("utf-8")
        url, file_id, token = self.open(path, password)
        self.assertEqual(url, "http://wc/edit" if writable else "http://wc/view")
        file_info = self.wopi_check_file_info(file_id, token)
        self.assertEqual(file_info["UserCanWrite"], writable)
        self.assertEqual(file_info["ReadOnly"], not writable)

        contents_path = "wopi/files/%s/contents?access_token=%s" % (file_id, token)
        headers, body = self.curl(get_request(contents_path, ""))
        self.assertStart("HTTP/1.1 200 ", headers)
        self.assertEqual(body, disk_path)

        status = self.wopi_put_file(file_id, token, b"new")
        self.assertEqual(status, "200" if writable else "404")
        with open(disk_path, "rb") as f:
            self.assertEqual(f.read(), b"new" if writable else original)
        with open(disk_path, "wb") as f:
            f.write(original)
        return file_id, token

    def test_wopi_ro(self):
        """read-only access in volumes"""
        # default: logged-in readers get read-only; anon and get-only are rejected
        self.copyparty_init()
        self.assertMode("priv/a.odt", "writer", True)
        self.assertMode("priv/a.odt", "reader", False)
        self.assertMode("pub/a.odt", "writer", True)
        self.assertEqual(self.open("pub/a.odt", "")[0], "403")
        self.assertEqual(self.open("priv/a.odt", "getter")[0], "403")
        _, body = self.curl(get_request("pub/?wopi=a.odt", ""))
        self.assertIn("permission to open this document in the office editor", body)

        # no view-action in discovery; fallback to edit
        url, file_id, token = self.open("priv/b.ods", "reader")
        self.assertEqual(url, "http://wc/edit")
        file_info = self.wopi_check_file_info(file_id, token)
        self.assertEqual(file_info["UserCanWrite"], False)
        self.assertEqual(self.wopi_put_file(file_id, token, b"new"), "404")

        # all: anonymous readers get read-only too
        self.copyparty_init("all")
        self.assertMode("pub/a.odt", "", False)
        self.assertMode("priv/a.odt", "reader", False)

        # --wopi-wdel: writers without delete-access can't edit, so they get read-only
        self.copyparty_init(wopi_wdel=True)
        self.assertMode("priv/a.odt", "writer", False)

        # --wopi-accs still applies on top of --wopi-anon-ro
        self.copyparty_init("all", wopi_accs="writer,reader")
        self.assertMode("priv/a.odt", "reader", False)
        self.assertEqual(self.open("pub/a.odt", "")[0], "403")

    def test_wopi_ro_shares(self):
        """read-only access in shares"""
        # writer creates a share without password (s1) and one with password (s2)
        self.copyparty_init()
        self.share("s1", "")
        self.share("s2", "supersecret")

        # default: logged-in users get read-only in shares; anonymous users don't
        self.copyparty_init()
        self.assertMode("shr/s1/a.odt", "writer", False, "priv/a.odt")
        self.assertEqual(self.open("shr/s1/a.odt", "")[0], "403")
        self.assertEqual(self.open("shr/s2/a.odt", "supersecret")[0], "403")

        # share: anonymous and share-password users get read-only, but only in shares
        self.copyparty_init("share")
        self.assertMode("shr/s1/a.odt", "", False, "priv/a.odt")
        self.assertMode("shr/s2/a.odt", "supersecret", False, "priv/a.odt")
        self.assertEqual(self.open("pub/a.odt", "supersecret")[0], "403")
        self.assertEqual(self.open("pub/a.odt", "")[0], "403")

        # what counts is where the path resolves to, not how it's spelled
        trick = get_request("shr/s1/?wopi=../../pub/a.odt", "")
        self.assertStart("HTTP/1.1 403 ", self.curl(trick)[0])
        trick = get_request("pub/?wopi=../shr/s1/a.odt", "")
        self.assertStart("HTTP/1.1 200 ", self.curl(trick)[0])

        # all: share-password users get read-only outside of shares too
        self.copyparty_init("all")
        self.assertMode("pub/a.odt", "supersecret", False)
        self.assertMode("shr/s2/a.odt", "supersecret", False, "priv/a.odt")

    def test_wopi_perm_change(self):
        """changed user permissions are reflected immediately"""
        # writers get an editing session, which is reused when reopening
        self.copyparty_init()
        file_id, edit_token = self.assertMode("priv/a.odt", "writer", True)
        self.assertEqual(self.open("priv/a.odt", "writer")[2], edit_token)

        # losing write-access gives a new read-only session; old token is rejected
        self.copyparty_init(keep_sessions=True, revoke_write=True)
        same_file_id, view_token = self.assertMode("priv/a.odt", "writer", False)
        self.assertEqual(same_file_id, file_id)
        self.assertNotEqual(view_token, edit_token)
        self.assertEqual(self.wopi_check_file_info(file_id, edit_token), "400")
        self.assertEqual(self.wopi_put_file(file_id, edit_token, b"new"), "400")

        # regaining write must not reuse the read-only session
        self.copyparty_init(keep_sessions=True)
        _, _, new_token = self.open("priv/a.odt", "writer")
        self.assertNotEqual(new_token, view_token)
        file_info = self.wopi_check_file_info(file_id, new_token)
        self.assertEqual(file_info["UserCanWrite"], True)

    def log(self, src, msg, c=0):
        text = "%s" % (msg,)
        if (
            "warning: filesystem-path does not exist:" in text
            or "you are sharing a system directory:" in text
            or "symlink-based deduplication is enabled" in text
            or text.startswith("hint: argument")
        ):
            return

        print(("[%s] %s" % (src, msg)).encode("ascii", "replace").decode("ascii"))

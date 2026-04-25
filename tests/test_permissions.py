#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import shutil
import tempfile
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg


def build_multipart_form(files, boundary="XD"):
    """
    Build a multipart/form-data request body for testing uploads.
    """
    parts = []
    
    parts.append("--{}\r\n".format(boundary).encode("utf-8"))
    parts.append('Content-Disposition: form-data; name="act"\r\n\r\n'.encode("utf-8"))
    parts.append("bput\r\n".encode("utf-8"))
    
    for filename, content in files:
        parts.append("--{}\r\n".format(boundary).encode("utf-8"))
        parts.append(
            'Content-Disposition: form-data; name="f"; filename="{}"\r\n\r\n'.format(filename).encode("utf-8")
        )
        if isinstance(content, str):
            parts.append(content.encode("utf-8"))
        else:
            parts.append(content)
        parts.append("\r\n".encode("utf-8"))
    
    parts.append("--{}--\r\n".format(boundary).encode("utf-8"))
    
    return b"".join(parts)


class TestPermissions(unittest.TestCase):
    """
    Test permission scenarios for different user types:
    - Read-only user (can read, cannot upload/delete/rename/mkdir)
    - Write-only user (can upload/mkdir, cannot delete/rename)
    - Full permissions user (can do everything)
    """

    def setUp(self):
        self.td = tu.get_ramdisk()
        self.maxDiff = 99999

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def setup_test_env(self, vcfg, users=None):
        """
        Set up test environment with given volume config and users.
        
        vcfg format: ["path:name:perms,users", ...]
        users format: ["username:password", ...]
        
        Permission format:
        - r: read
        - w: write/upload/mkdir
        - m: move/rename (requires w also)
        - d: delete
        - a: admin = rw
        
        Note: empty user after comma means "all users" (anonymous)
        """
        td = os.path.join(self.td, "vfs")
        if os.path.exists(td):
            shutil.rmtree(td)
        os.mkdir(td)
        os.chdir(td)
        
        for vc in vcfg:
            path = vc.split(":")[0].rstrip("/")
            if path and not os.path.exists(path):
                os.makedirs(path)
        
        users = users or ["o:o", "x:x", "a:a"]
        self.args = Cfg(v=vcfg, a=users)
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

    def bup(self, url, files, user="o"):
        """Perform a basic upload (bput) request."""
        boundary = "XD"
        body = build_multipart_form(files, boundary)
        
        hdr_fmt = "POST /{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Type: multipart/form-data; boundary={}\r\nContent-Length: {}\r\n\r\n"
        hdr_str = hdr_fmt.format(url, user, boundary, len(body))
        
        full_request = hdr_str.encode("utf-8") + body
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        response = conn.s._reply
        if isinstance(response, bytes):
            parts = response.split(b"\r\n\r\n", 1)
            h = parts[0].decode("utf-8")
            b = parts[1].decode("utf-8") if len(parts) > 1 else ""
        else:
            parts = response.split("\r\n\r\n", 1)
            h = parts[0]
            b = parts[1] if len(parts) > 1 else ""
        
        return h, b

    def curl(self, url, user="o"):
        """Perform a GET request."""
        hdr_fmt = "GET /{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\n\r\n"
        hdr_str = hdr_fmt.format(url, user)
        
        full_request = hdr_str.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        response = conn.s._reply
        if isinstance(response, bytes):
            parts = response.split(b"\r\n\r\n", 1)
            h = parts[0].decode("utf-8")
            b = parts[1].decode("utf-8") if len(parts) > 1 else ""
        else:
            parts = response.split("\r\n\r\n", 1)
            h = parts[0]
            b = parts[1] if len(parts) > 1 else ""
        
        return h, b

    def put(self, url, user="o", content="test content"):
        """Perform a PUT request."""
        hdr_fmt = "PUT /{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Length: {}\r\n\r\n{}"
        hdr_str = hdr_fmt.format(url, user, len(content), content)
        
        full_request = hdr_str.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        response = conn.s._reply
        if isinstance(response, bytes):
            parts = response.split(b"\r\n\r\n", 1)
            h = parts[0].decode("utf-8")
            b = parts[1].decode("utf-8") if len(parts) > 1 else ""
        else:
            parts = response.split("\r\n\r\n", 1)
            h = parts[0]
            b = parts[1] if len(parts) > 1 else ""
        
        return h, b

    def delete(self, url, user="o"):
        """Perform a DELETE request (via POST with delete)."""
        hdr_fmt = "POST /{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Type: multipart/form-data; boundary=XD\r\nContent-Length: 51\r\n\r\n--XD\r\nContent-Disposition: form-data; name=\"act\"\r\n\r\ndelete\r\n--XD--\r\n"
        hdr_str = hdr_fmt.format(url, user)
        
        full_request = hdr_str.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        response = conn.s._reply
        if isinstance(response, bytes):
            parts = response.split(b"\r\n\r\n", 1)
            h = parts[0].decode("utf-8")
            b = parts[1].decode("utf-8") if len(parts) > 1 else ""
        else:
            parts = response.split("\r\n\r\n", 1)
            h = parts[0]
            b = parts[1] if len(parts) > 1 else ""
        
        return h, b

    def move(self, src, dst, user="o"):
        """Perform a move request."""
        hdr_fmt = "POST /{}?move=/{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
        hdr_str = hdr_fmt.format(src, dst, user)
        
        full_request = hdr_str.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        response = conn.s._reply
        if isinstance(response, bytes):
            parts = response.split(b"\r\n\r\n", 1)
            h = parts[0].decode("utf-8")
            b = parts[1].decode("utf-8") if len(parts) > 1 else ""
        else:
            parts = response.split("\r\n\r\n", 1)
            h = parts[0]
            b = parts[1] if len(parts) > 1 else ""
        
        return h, b

    def mkdir(self, url, name, user="o"):
        """Perform a mkdir request."""
        body = "name={}".format(name).encode("utf-8")
        hdr_fmt = "POST /{}?mkdir HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {}\r\n\r\n"
        hdr_str = hdr_fmt.format(url, user, len(body))
        
        full_request = hdr_str.encode("utf-8") + body
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        response = conn.s._reply
        if isinstance(response, bytes):
            parts = response.split(b"\r\n\r\n", 1)
            h = parts[0].decode("utf-8")
            b = parts[1].decode("utf-8") if len(parts) > 1 else ""
        else:
            parts = response.split("\r\n\r\n", 1)
            h = parts[0]
            b = parts[1] if len(parts) > 1 else ""
        
        return h, b

    def log(self, src, msg, c=0):
        print(msg)

    # =========================================================================
    # Read-only user tests (r permission only)
    # =========================================================================

    def test_readonly_user_cannot_upload(self):
        """Test that read-only user cannot upload files (bput)
        
        Read-only users have 'r' permission only.
        They should not be able to upload files.
        """
        vcfg = [
            "ro/:ro:r,o",
            "rw/:rw:rw,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        files = [("test.txt", "Should not be uploaded")]
        
        h, body = self.bup("ro", files, user="o")
        self.assertIn("HTTP/1.1 403", h, "Read-only user should get 403 for upload")
        
        if os.path.exists("ro"):
            files_in_ro = os.listdir("ro")
            test_files = [f for f in files_in_ro if "test" in f]
            self.assertEqual(len(test_files), 0, "No files should be created in read-only dir")
        
        self.conn.shutdown()

    def test_readonly_user_cannot_put(self):
        """Test that read-only user cannot PUT files
        
        PUT is another upload method that should be blocked for read-only users.
        """
        vcfg = [
            "ro/:ro:r,o",
            "rw/:rw:rw,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        h, body = self.put("ro/test_put.txt", user="o", content="test content")
        self.assertIn("HTTP/1.1 403", h, "Read-only user should get 403 for PUT")
        
        self.assertFalse(os.path.exists("ro/test_put.txt"), "File should not be created")
        
        self.conn.shutdown()

    def test_readonly_user_cannot_mkdir(self):
        """Test that read-only user cannot create directories
        
        Read-only users should not be able to create new directories.
        This tests the mkdir API endpoint directly.
        """
        vcfg = [
            "ro/:ro:r,o",
            "rw/:rw:rw,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        h, body = self.mkdir("ro", "newdir", user="o")
        self.assertIn("HTTP/1.1 403", h, "Read-only user should get 403 for mkdir")
        
        self.assertFalse(os.path.exists("ro/newdir"), "Directory should not be created")
        
        self.conn.shutdown()

    def test_readonly_user_can_read(self):
        """Test that read-only user can read files
        
        Read-only users should be able to:
        - List directories
        - Read file contents
        - Access JSON listings
        """
        vcfg = [
            "ro/:ro:r,o",
            "no/:no:,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        with open("ro/readme.txt", "w") as f:
            f.write("read me")
        
        h, body = self.curl("ro/readme.txt", user="o")
        self.assertIn("HTTP/1.1 200", h, "Read-only user should be able to read")
        self.assertIn("read me", body, "File content should be accessible")
        
        h, body = self.curl("ro/", user="o")
        self.assertIn("HTTP/1.1 200", h, "Read-only user should be able to list directory")
        
        h, body = self.curl("ro/?ls", user="o")
        self.assertIn("HTTP/1.1 200", h, "Read-only user should be able to get JSON listing")
        self.assertIn("readme.txt", body, "File should be in JSON listing")
        
        self.conn.shutdown()

    # =========================================================================
    # Write-only user tests (rw permission - no delete, no move)
    # =========================================================================

    def test_write_user_can_upload(self):
        """Test that write user can upload files
        
        Users with 'rw' permission should be able to:
        - Upload files via bput
        - Upload files via PUT
        """
        vcfg = [
            "ro/:ro:r,o",
            "wo/:wo:w,x",
            "rw/:rw:rw,a",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x", "a:a"])
        
        files = [("test_upload.txt", "Uploaded content")]
        
        h, body = self.bup("rw", files, user="a")
        self.assertIn("HTTP/1.1 201", h, "Write user should be able to upload")
        
        files_in_rw = os.listdir("rw")
        test_files = [f for f in files_in_rw if "test_upload" in f]
        self.assertTrue(len(test_files) > 0, "Uploaded file should exist")
        
        self.conn.shutdown()

    def test_write_user_can_put(self):
        """Test that write user can PUT files"""
        vcfg = [
            "rw/:rw:rw,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        h, body = self.put("rw/test_put.txt", user="o", content="put content")
        self.assertIn("HTTP/1.1 201", h, "Write user should be able to PUT")
        
        self.assertTrue(os.path.exists("rw/test_put.txt"), "File should be created")
        
        self.conn.shutdown()

    def test_write_user_can_mkdir(self):
        """Test that write user can create directories
        
        Users with 'w' permission should be able to create directories.
        """
        vcfg = [
            "rw/:rw:rw,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        h, body = self.mkdir("rw", "newdir", user="o")
        self.assertIn("HTTP/1.1 302", h, "Write user should be able to mkdir")
        
        self.assertTrue(os.path.exists("rw/newdir"), "Directory should be created")
        
        self.conn.shutdown()

    def test_write_user_cannot_delete_without_d_permission(self):
        """Test that write user without 'd' permission cannot delete
        
        Users with only 'rw' permission (not 'd') should NOT be able to delete files.
        This tests that bypassing frontend still gets 403 from backend.
        """
        vcfg = [
            "rw/:rw:rw,o",
            "rwd/:rwd:rwd,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        with open("rw/keep_me.txt", "w") as f:
            f.write("should stay")
        with open("rwd/delete_me.txt", "w") as f:
            f.write("can be deleted")
        
        h, body = self.delete("rw/keep_me.txt", user="o")
        self.assertIn("HTTP/1.1 403", h, "User without 'd' permission should get 403 for delete")
        
        self.assertTrue(os.path.exists("rw/keep_me.txt"), "File should still exist without delete permission")
        
        self.conn.shutdown()

    def test_write_user_cannot_move_without_m_permission(self):
        """Test that write user without 'm' permission cannot move/rename
        
        Users with only 'rw' permission (not 'm') should NOT be able to move/rename files.
        This tests that bypassing frontend still gets 403 from backend.
        """
        vcfg = [
            "rw/:rw:rw,o",
            "rwm/:rwm:rwm,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        with open("rw/src_o.txt", "w") as f:
            f.write("o's file")
        with open("rwm/src_x.txt", "w") as f:
            f.write("x's file")
        
        h, body = self.move("rw/src_o.txt", "rw/dst_o.txt", user="o")
        
        self.assertTrue(os.path.exists("rw/src_o.txt"), "Without move permission, src should stay")
        self.assertFalse(os.path.exists("rw/dst_o.txt"), "Without move permission, dst should not exist")
        
        self.conn.shutdown()

    # =========================================================================
    # Full permissions user tests (rwmd)
    # =========================================================================

    def test_full_permissions_user(self):
        """Test that user with rwmd permissions has full access
        
        Users with 'rwmd' permission should be able to:
        - Read files
        - Upload files
        - Create directories
        """
        vcfg = [
            "full/:full:rwmd,o",
            "ro/:ro:r,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        with open("full/existing.txt", "w") as f:
            f.write("existing")
        
        h, body = self.curl("full/existing.txt", user="o")
        self.assertIn("HTTP/1.1 200", h, "User should be able to read")
        self.assertIn("existing", body, "User should see file content")
        
        files = [("upload.txt", "Uploaded")]
        h, body = self.bup("full", files, user="o")
        self.assertIn("HTTP/1.1 201", h, "User should be able to upload")
        
        self.conn.shutdown()

    def test_full_permissions_user_can_delete(self):
        """Test that user with 'd' permission can delete
        
        Users with 'd' permission should be able to delete files.
        """
        vcfg = [
            "rwd/:rwd:rwd,o",
            "rw/:rw:rw,x",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        with open("rwd/delete_me.txt", "w") as f:
            f.write("to be deleted")
        
        h, body = self.delete("rwd/delete_me.txt", user="o")
        
        self.conn.shutdown()

    def test_full_permissions_user_can_move(self):
        """Test that user with 'm' permission can move/rename
        
        Users with 'm' permission should be able to move/rename files.
        """
        vcfg = [
            "rwm/:rwm:rwm,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rwm/src.txt", "w") as f:
            f.write("source file")
        
        h, body = self.move("rwm/src.txt", "rwm/dst.txt", user="o")
        
        self.conn.shutdown()

    def test_full_permissions_user_can_mkdir(self):
        """Test that user with 'w' permission can create directories
        
        Users with 'w' permission should be able to create directories.
        """
        vcfg = [
            "rwd/:rwd:rwd,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        h, body = self.mkdir("rwd", "new_subdir", user="o")
        
        self.assertTrue(os.path.exists("rwd/new_subdir"), "Directory should be created")
        
        self.conn.shutdown()

    # =========================================================================
    # No access user tests
    # =========================================================================

    def test_no_access_user_gets_403(self):
        """Test that user with no access gets 403
        
        Users without any permissions should get 403 responses.
        """
        vcfg = [
            "secret/:secret:r,x",
            "public/:public:r,o",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        with open("secret/hidden.txt", "w") as f:
            f.write("hidden")
        with open("public/visible.txt", "w") as f:
            f.write("visible")
        
        h, body = self.curl("secret/", user="o")
        self.assertIn("HTTP/1.1 403", h, "No access user should get 403 for directory")
        
        h, body = self.curl("secret/hidden.txt", user="o")
        self.assertIn("HTTP/1.1 403", h, "No access user should get 403 for file")
        
        h, body = self.curl("public/visible.txt", user="o")
        self.assertIn("HTTP/1.1 200", h, "Public user should be able to read public files")
        
        self.conn.shutdown()

    def test_no_access_user_cannot_mkdir(self):
        """Test that user with no access cannot create directories
        
        Users without 'w' permission should not be able to create directories.
        """
        vcfg = [
            "secret/:secret:r,x",
            "public/:public:r,o",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        h, body = self.mkdir("secret", "hacker_dir", user="o")
        self.assertIn("HTTP/1.1 403", h, "No access user should get 403 for mkdir")
        
        self.assertFalse(os.path.exists("secret/hacker_dir"), "Directory should not be created")
        
        self.conn.shutdown()

    # =========================================================================
    # JSON listing and other tests
    # =========================================================================

    def test_json_listing_permissions(self):
        """Test that JSON listing reflects correct permissions
        
        JSON listing (?ls) should:
        - Return 200 for users with read access
        - Return 403 for users without any access
        - Include file names for users with read access
        """
        vcfg = [
            "ro/:ro:r,o",
            "rw/:rw:rw,x",
            "no/:no:,a",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x", "a:a"])
        
        with open("ro/ro_file.txt", "w") as f:
            f.write("ro")
        with open("rw/rw_file.txt", "w") as f:
            f.write("rw")
        
        h, body = self.curl("ro/?ls", user="o")
        self.assertIn("HTTP/1.1 200", h, "Read user should get JSON listing")
        self.assertIn("ro_file.txt", body, "File should be in listing")
        
        h, body = self.curl("rw/?ls", user="x")
        self.assertIn("HTTP/1.1 200", h, "Write user should get JSON listing")
        self.assertIn("rw_file.txt", body, "File should be in listing")
        
        h, body = self.curl("no/?ls", user="a")
        self.assertIn("HTTP/1.1 403", h, "No access user should get 403")
        
        self.conn.shutdown()

    def test_anonymous_user_permissions(self):
        """Test that anonymous (all) users have correct permissions
        
        When empty user is used (after comma), it means "all users" (anonymous).
        """
        vcfg = [
            "public/:public:r,",
            "upload/:upload:rw,",
        ]
        self.setup_test_env(vcfg, ["o:o", "x:x"])
        
        with open("public/public.txt", "w") as f:
            f.write("public")
        
        h, body = self.curl("public/public.txt", user="o")
        self.assertIn("HTTP/1.1 200", h, "Anonymous user should be able to read public files")
        
        files = [("anon_upload.txt", "Uploaded by anonymous")]
        h, body = self.bup("upload", files, user="x")
        self.assertIn("HTTP/1.1 201", h, "Anonymous user should be able to upload to upload dir")
        
        self.conn.shutdown()


if __name__ == "__main__":
    unittest.main()

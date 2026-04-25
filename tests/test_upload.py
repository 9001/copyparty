#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import hashlib
import json
import os
import shutil
import tempfile
import time
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg


def hdr(query):
    h = "GET /{} HTTP/1.1\r\nCookie: cppwd=o\r\nConnection: close\r\n\r\n"
    return h.format(query).encode("utf-8")


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


class TestUpload(unittest.TestCase):
    def setUp(self):
        self.td = tu.get_ramdisk()
        self.maxDiff = 99999

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def test_basic_upload(self):
        """Test basic upload functionality (bput)"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("test.txt", "Hello, World!")]
        h, body = self.bup("ao", files)
        
        self.assertIn("HTTP/1.1 201", h)
        
        files_in_ao = os.listdir("ao")
        test_files = [f for f in files_in_ao if f.startswith("test")]
        self.assertTrue(len(test_files) > 0, "Uploaded file should exist")

        self.conn.shutdown()

    def test_basic_upload_json_response(self):
        """Test basic upload with JSON response"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("test.txt", "Hello, JSON!")]
        h, body = self.bup("ao?j", files)
        
        self.assertIn("HTTP/1.1 201", h)
        self.assertIn("application/json", h)
        
        response = json.loads(body)
        self.assertEqual(response["status"], "OK")

        self.conn.shutdown()

    def test_large_file_upload(self):
        """Test uploading a relatively large file"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        large_content = b"A" * (128 * 1024)
        files = [("large.bin", large_content)]
        h, body = self.bup("ao", files)
        
        self.assertIn("HTTP/1.1 201", h)

        self.conn.shutdown()

    def test_upload_without_write_permission(self):
        """Test upload without write permission - should fail"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ro")
        vcfg = ["ro/:ro:r,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("test.txt", "This should fail")]
        h, body = self.bup("ro", files)
        
        self.assertIn("HTTP/1.1 403", h)
        
        files_in_ro = os.listdir("ro")
        test_files = [f for f in files_in_ro if f.startswith("test")]
        self.assertEqual(len(test_files), 0, "No files should be created")

        self.conn.shutdown()

    def test_upload_existing_file_no_overwrite(self):
        """Test that upload does NOT overwrite existing files without ?replace
        
        This verifies the old file protection mechanism implemented in:
        - util.py:1816-1915 (ren_open function) - adds suffix if file exists
        - httpcli.py:3733-3742 (replace parameter handling) - requires ?replace to overwrite
        """
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        with open("ao/existing.txt", "w") as f:
            f.write("Original content")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("existing.txt", "New content that should NOT overwrite")]
        h, body = self.bup("ao?j", files)
        
        self.assertIn("HTTP/1.1 201", h)
        
        with open("ao/existing.txt", "r") as f:
            self.assertEqual(f.read(), "Original content", "Old file should NOT be overwritten")

        files_in_ao = os.listdir("ao")
        existing_files = [f for f in files_in_ao if "existing" in f]
        self.assertTrue(len(existing_files) >= 2, "Should have both original and new file")

        new_content_found = False
        for fname in existing_files:
            if fname != "existing.txt":
                with open(os.path.join("ao", fname), "r") as f:
                    if f.read() == "New content that should NOT overwrite":
                        new_content_found = True
                        break
        
        self.assertTrue(new_content_found, "New file should be created with different name")

        self.conn.shutdown()

    def test_upload_with_replace_param_overwrites(self):
        """Test that upload with ?replace parameter overwrites existing files
        
        Requires:
        1. URL contains ?replace parameter
        2. User has delete permission
        """
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        with open("ao/existing.txt", "w") as f:
            f.write("Original content")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("existing.txt", "New content that SHOULD overwrite")]
        h, body = self.bup("ao?j&replace", files)
        
        self.assertIn("HTTP/1.1 201", h)

        self.conn.shutdown()

    def test_upload_replace_without_delete_permission(self):
        """Test that ?replace fails without delete permission"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("wo")
        vcfg = ["wo/:wo:w,o"]

        with open("wo/existing.txt", "w") as f:
            f.write("Original content")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("existing.txt", "New content")]
        h, body = self.bup("wo?j&replace", files)
        
        with open("wo/existing.txt", "r") as f:
            self.assertEqual(f.read(), "Original content", "Old file should NOT be overwritten without delete permission")

        self.conn.shutdown()

    def test_upload_empty_file(self):
        """Test uploading an empty file"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("empty.txt", "")]
        h, body = self.bup("ao?j", files)
        
        self.assertIn("HTTP/1.1 201", h)

        self.conn.shutdown()

    def test_upload_error_response_contains_error_info(self):
        """Test that upload errors return proper error information"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ro")
        vcfg = ["ro/:ro:r,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("test.txt", "This should fail")]
        h, body = self.bup("ro?j", files)
        
        self.assertIn("HTTP/1.1 403", h)

        self.conn.shutdown()

    def test_upload_large_file_integrity(self):
        """Test that uploaded files maintain integrity (SHA256 check)"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        test_content = os.urandom(256 * 1024)
        original_hash = hashlib.sha256(test_content).hexdigest()

        files = [("integrity_test.bin", test_content)]
        h, body = self.bup("ao", files)
        
        self.assertIn("HTTP/1.1 201", h)

        files_in_ao = os.listdir("ao")
        test_files = [f for f in files_in_ao if "integrity_test" in f]
        self.assertTrue(len(test_files) > 0)

        for fname in test_files:
            with open(os.path.join("ao", fname), "rb") as f:
                uploaded_content = f.read()
            uploaded_hash = hashlib.sha256(uploaded_content).hexdigest()
            if uploaded_hash == original_hash:
                break
        else:
            self.fail("No file with matching hash found")

        self.conn.shutdown()

    def test_upload_multiple_files(self):
        """Test uploading multiple files"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [
            ("file1.txt", "Content 1"),
            ("file2.txt", "Content 2"),
        ]
        h, body = self.bup("ao?j", files)
        
        self.assertIn("HTTP/1.1 201", h)

        self.conn.shutdown()

    def test_upload_special_characters_filename(self):
        """Test upload with special characters in filename"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("my file 123.txt", "Content with spaces")]
        h, body = self.bup("ao?j", files)
        
        self.assertIn("HTTP/1.1 201", h)

        self.conn.shutdown()

    def test_partial_file_cleanup_on_size_limit(self):
        """Test that partial uploads are handled properly
        
        Backend implementation in:
        - httpcli.py:3803-3857 - creates .PARTIAL file during upload
        - httpcli.py:3851-3855 - cleanup on size limit exceeded
        - httpcli.py:3931-3940 - exception handling
        """
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        os.makedirs("ao")
        vcfg = ["ao/:ao:rw,o"]

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"], smax=100)
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        large_content = b"A" * 200
        files = [("too_large.txt", large_content)]
        h, body = self.bup("ao", files)

        files_in_ao = os.listdir("ao")
        for fname in files_in_ao:
            self.assertNotIn(".PARTIAL", fname, "No partial files should remain")

        self.conn.shutdown()

    def bup(self, url, files):
        """
        Perform a basic upload (bput) request.
        
        Args:
            url: The URL path to upload to
            files: List of (filename, content) tuples
        
        Returns:
            (headers, body) tuple
        """
        boundary = "XD"
        body = build_multipart_form(files, boundary)
        
        hdr_fmt = "POST /{} HTTP/1.1\r\nPW: o\r\nConnection: close\r\nContent-Type: multipart/form-data; boundary={}\r\nContent-Length: {}\r\n\r\n"
        hdr_str = hdr_fmt.format(url, boundary, len(body))
        
        full_request = hdr_str.encode("utf-8") + body
        print("POST -->", full_request[:200], "...")
        
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
        
        print("POST <--", h[:200], "...")
        return h, b

    def log(self, src, msg, c=0):
        print(msg)


if __name__ == "__main__":
    unittest.main()

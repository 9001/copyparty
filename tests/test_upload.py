#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

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

        vcfg = ["up/::a"]
        os.makedirs("up")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("test.txt", "Hello, World!")]
        h, body = self.bup("up", files)
        
        self.assertIn("HTTP/1.1 201", h)
        
        self.assertTrue(os.path.exists("up/test.txt"))
        with open("up/test.txt", "r") as f:
            self.assertEqual(f.read(), "Hello, World!")

        self.conn.shutdown()

    def test_basic_upload_json_response(self):
        """Test basic upload with JSON response"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        vcfg = ["up/::a"]
        os.makedirs("up")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("test.txt", "Hello, JSON!")]
        h, body = self.bup("up?j", files)
        
        self.assertIn("HTTP/1.1 201", h)
        self.assertIn("application/json", h)
        
        response = json.loads(body)
        self.assertEqual(response["status"], "OK")
        self.assertEqual(response["sz"], len("Hello, JSON!"))
        self.assertEqual(len(response["files"]), 1)
        self.assertEqual(response["files"][0]["fn_orig"], "test.txt")

        self.conn.shutdown()

    def test_large_file_upload(self):
        """Test uploading a relatively large file (1MB)"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        vcfg = ["up/::a"]
        os.makedirs("up")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        large_content = b"A" * 1024 * 1024
        files = [("large.bin", large_content)]
        h, body = self.bup("up", files)
        
        self.assertIn("HTTP/1.1 201", h)
        
        self.assertTrue(os.path.exists("up/large.bin"))
        with open("up/large.bin", "rb") as f:
            self.assertEqual(f.read(), large_content)

        self.conn.shutdown()

    def test_multiple_files_upload(self):
        """Test uploading multiple files in one request"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        vcfg = ["up/::a"]
        os.makedirs("up")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [
            ("file1.txt", "Content 1"),
            ("file2.txt", "Content 2"),
            ("file3.txt", "Content 3"),
        ]
        h, body = self.bup("up?j", files)
        
        self.assertIn("HTTP/1.1 201", h)
        
        response = json.loads(body)
        self.assertEqual(response["status"], "OK")
        self.assertEqual(len(response["files"]), 3)
        
        filenames = [f["fn_orig"] for f in response["files"]]
        self.assertIn("file1.txt", filenames)
        self.assertIn("file2.txt", filenames)
        self.assertIn("file3.txt", filenames)

        self.conn.shutdown()

    def test_upload_without_write_permission(self):
        """Test upload without write permission - should fail"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        vcfg = ["ro/::r"]
        os.makedirs("ro")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("test.txt", "This should fail")]
        h, body = self.bup("ro", files)
        
        self.assertIn("HTTP/1.1 403", h)
        
        self.assertFalse(os.path.exists("ro/test.txt"))

        self.conn.shutdown()

    def test_upload_file_size_limit(self):
        """Test upload exceeding file size limit"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        vcfg = ["up/::a"]
        os.makedirs("up")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"], smax=100)
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        large_content = b"A" * 200
        files = [("too_large.txt", large_content)]
        h, body = self.bup("up", files)
        
        self.assertIn("HTTP/1.1 400", h) or self.assertIn("ERROR", body)
        
        self.assertFalse(os.path.exists("up/too_large.txt"))

        self.conn.shutdown()

    def test_upload_special_characters_filename(self):
        """Test upload with special characters in filename"""
        td = os.path.join(self.td, "vfs")
        os.mkdir(td)
        os.chdir(td)

        vcfg = ["up/::a"]
        os.makedirs("up")

        self.args = Cfg(v=vcfg, a=["o:o", "x:x"])
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"")

        files = [("my file 123.txt", "Content with spaces")]
        h, body = self.bup("up?j", files)
        
        self.assertIn("HTTP/1.1 201", h)
        
        response = json.loads(body)
        self.assertEqual(response["status"], "OK")

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

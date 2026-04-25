#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import json
import os
import shutil
import tempfile
import unittest

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from tests import util as tu
from tests.util import Cfg


def build_multipart_form(fields, files=None, boundary="XD"):
    """
    Build a multipart/form-data request body.
    
    fields: list of (name, value) tuples for form fields
    files: list of (field_name, filename, content) tuples for file uploads
    """
    parts = []
    files = files or []
    
    for name, value in fields:
        parts.append("--{}\r\n".format(boundary).encode("utf-8"))
        parts.append('Content-Disposition: form-data; name="{}"\r\n\r\n'.format(name).encode("utf-8"))
        if isinstance(value, str):
            parts.append(value.encode("utf-8"))
        else:
            parts.append(value)
        parts.append("\r\n".encode("utf-8"))
    
    for field_name, filename, content in files:
        parts.append("--{}\r\n".format(boundary).encode("utf-8"))
        parts.append(
            'Content-Disposition: form-data; name="{}"; filename="{}"\r\n\r\n'.format(field_name, filename).encode("utf-8")
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
    Test permission scenarios for different user types.
    
    Key test categories:
    1. JSON listing perms field validation - this is the data frontend uses to show/hide UI
    2. Backend API permission enforcement - testing that bypassing frontend still gets blocked
    3. File state verification - verifying files are actually protected/modified
    
    Permission mapping:
    - 'r' → perms: ["read"]
    - 'w' → perms: ["write"] (requires 'r' also)
    - 'm' → perms: ["move"] (requires 'w' also for rename)
    - 'd' → perms: ["delete"]
    
    Frontend UI visibility based on perms:
    - Upload buttons: needs 'write'
    - Mkdir button: needs 'write'
    - Delete button/menu: needs 'delete'
    - Rename button/menu: needs 'write' + 'move'
    - Cut: needs 'move'
    - Paste: needs 'write'
    
    Shortcuts blocked without perms:
    - Ctrl+K (delete): needs 'delete'
    - Ctrl+X (cut): needs 'move'
    - Ctrl+V (paste): needs 'write'
    - F2 (rename): needs 'write' + 'move'
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

    def post_multipart(self, url, fields, files=None, user="o"):
        """Perform a POST request with multipart/form-data body."""
        boundary = "XD"
        body = build_multipart_form(fields, files, boundary)
        
        hdr_fmt = "POST /{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Type: multipart/form-data; boundary={}\r\nContent-Length: {}\r\n\r\n"
        hdr_str = hdr_fmt.format(url, user, boundary, len(body))
        
        full_request = hdr_str.encode("utf-8") + body
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        return self._parse_response(conn.s._reply)

    def bup(self, url, files, user="o"):
        """Perform a basic upload (bput) request."""
        fields = [("act", "bput")]
        file_tuples = [("f", fname, content) for fname, content in files]
        return self.post_multipart(url, fields, file_tuples, user)

    def mkdir(self, url, name, user="o"):
        """Perform a mkdir request using multipart/form-data as frontend does."""
        fields = [("act", "mkdir"), ("name", name)]
        return self.post_multipart(url, fields, user=user)

    def curl(self, url, user="o"):
        """Perform a GET request."""
        hdr_fmt = "GET /{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\n\r\n"
        hdr_str = hdr_fmt.format(url, user)
        
        full_request = hdr_str.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        return self._parse_response(conn.s._reply)

    def delete(self, url, user="o"):
        """Perform a DELETE request via POST with ?delete URL parameter."""
        hdr_fmt = "POST /{}?delete HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
        hdr_str = hdr_fmt.format(url, user)
        
        full_request = hdr_str.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        return self._parse_response(conn.s._reply)

    def move(self, src, dst, user="o"):
        """Perform a move request."""
        hdr_fmt = "POST /{}?move=/{} HTTP/1.1\r\nPW: {}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
        hdr_str = hdr_fmt.format(src, dst, user)
        
        full_request = hdr_str.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        
        return self._parse_response(conn.s._reply)

    def _parse_response(self, response):
        """Parse HTTP response into (headers, body)."""
        if isinstance(response, bytes):
            parts = response.split(b"\r\n\r\n", 1)
            h = parts[0].decode("utf-8")
            b = parts[1].decode("utf-8") if len(parts) > 1 else ""
        else:
            parts = response.split("\r\n\r\n", 1)
            h = parts[0]
            b = parts[1] if len(parts) > 1 else ""
        
        return h, b

    def parse_json_response(self, body):
        """Parse JSON response body from ?ls request."""
        try:
            if body.startswith("j1 ") or body.startswith("j1\n"):
                json_str = body[3:].strip()
                return json.loads(json_str)
            elif body.startswith("j1") and len(body) > 2:
                json_str = body[2:].strip()
                return json.loads(json_str)
            return json.loads(body)
        except Exception as e:
            print(f"Failed to parse JSON: {body[:200]}... Error: {e}")
            return None

    def assert_status(self, headers, expected, msg=""):
        """Assert response status code."""
        status_line = headers.split("\r\n")[0]
        self.assertIn(f"HTTP/1.1 {expected}", status_line, msg)

    def get_status_code(self, headers):
        """Extract status code from response headers."""
        status_line = headers.split("\r\n")[0]
        parts = status_line.split()
        if len(parts) >= 2:
            return parts[1]
        return None

    def log(self, src, msg, c=0):
        print(msg)

    # =========================================================================
    # PART 1: JSON Listing Perms Field Tests (Frontend Permission Data Source)
    #
    # These tests verify that the JSON listing returns the correct 'perms' array.
    # This is the CRITICAL data that the frontend uses to:
    # - Show/hide toolbar buttons (via data-perm attribute)
    # - Show/hide right-click menu items
    # - Enable/disable shortcuts
    # =========================================================================

    def test_json_listing_perms_readonly_user(self):
        """Read-only user (r) should have perms: ["read"] only.
        
        Frontend behavior with perms=["read"]:
        - Upload buttons (data-perm="write"): HIDDEN
        - Mkdir button (data-perm="write"): HIDDEN  
        - Delete button/menu (needs 'delete'): HIDDEN
        - Rename (needs 'write' + 'move'): HIDDEN
        - Shortcuts: Ctrl+K, Ctrl+X, Ctrl+V, F2 all BLOCKED
        """
        vcfg = [
            "ro/:ro:r,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("ro/test.txt", "w") as f:
            f.write("test")
        
        h, body = self.curl("ro/?ls", user="o")
        self.assert_status(h, "200", "Read-only user should access listing")
        
        data = self.parse_json_response(body)
        self.assertIsNotNone(data, "JSON response should be parseable")
        
        perms = data.get("perms", [])
        print(f"[DEBUG] Read-only user perms: {perms}")
        
        self.assertIn("read", perms, "Read-only user should have 'read' permission")
        self.assertNotIn("write", perms, "Read-only user should NOT have 'write' permission")
        self.assertNotIn("move", perms, "Read-only user should NOT have 'move' permission")
        self.assertNotIn("delete", perms, "Read-only user should NOT have 'delete' permission")
        
        self.conn.shutdown()

    def test_json_listing_perms_write_user(self):
        """Upload-only user (rw) should have perms: ["read", "write"].
        
        Frontend behavior with perms=["read", "write"]:
        - Upload buttons (data-perm="write"): SHOWN
        - Mkdir button (data-perm="write"): SHOWN
        - Delete button/menu (needs 'delete'): HIDDEN
        - Rename (needs 'write' + 'move'): HIDDEN
        - Cut (needs 'move'): HIDDEN
        - Paste (needs 'write'): SHOWN (but nothing to paste without 'move')
        - Shortcuts:
          - Ctrl+K (delete): BLOCKED (no 'delete')
          - Ctrl+X (cut): BLOCKED (no 'move')
          - Ctrl+V (paste): ALLOWED (has 'write')
          - F2 (rename): BLOCKED (no 'move')
        """
        vcfg = [
            "rw/:rw:rw,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rw/test.txt", "w") as f:
            f.write("test")
        
        h, body = self.curl("rw/?ls", user="o")
        self.assert_status(h, "200", "Write user should access listing")
        
        data = self.parse_json_response(body)
        self.assertIsNotNone(data, "JSON response should be parseable")
        
        perms = data.get("perms", [])
        print(f"[DEBUG] Write user perms: {perms}")
        
        self.assertIn("read", perms, "Write user should have 'read' permission")
        self.assertIn("write", perms, "Write user should have 'write' permission")
        self.assertNotIn("move", perms, "Write user should NOT have 'move' permission (without 'm')")
        self.assertNotIn("delete", perms, "Write user should NOT have 'delete' permission (without 'd')")
        
        self.conn.shutdown()

    def test_json_listing_perms_full_user(self):
        """Full permission user (rwmd) should have perms: ["read", "write", "move", "delete"].
        
        Frontend behavior with all perms:
        - All buttons SHOWN
        - All right-click menu items SHOWN
        - All shortcuts ENABLED
        """
        vcfg = [
            "full/:full:rwmd,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("full/test.txt", "w") as f:
            f.write("test")
        
        h, body = self.curl("full/?ls", user="o")
        self.assert_status(h, "200", "Full user should access listing")
        
        data = self.parse_json_response(body)
        self.assertIsNotNone(data, "JSON response should be parseable")
        
        perms = data.get("perms", [])
        print(f"[DEBUG] Full permission user perms: {perms}")
        
        self.assertIn("read", perms, "Full user should have 'read' permission")
        self.assertIn("write", perms, "Full user should have 'write' permission")
        self.assertIn("move", perms, "Full user should have 'move' permission")
        self.assertIn("delete", perms, "Full user should have 'delete' permission")
        
        self.conn.shutdown()

    def test_json_listing_perms_rwm_user(self):
        """rwm user (read+write+move, no delete) should have perms: ["read", "write", "move"].
        
        Frontend behavior:
        - Can upload, mkdir, move/rename
        - Cannot delete (no 'delete' in perms)
        """
        vcfg = [
            "rwm/:rwm:rwm,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rwm/test.txt", "w") as f:
            f.write("test")
        
        h, body = self.curl("rwm/?ls", user="o")
        self.assert_status(h, "200", "rwm user should access listing")
        
        data = self.parse_json_response(body)
        self.assertIsNotNone(data, "JSON response should be parseable")
        
        perms = data.get("perms", [])
        print(f"[DEBUG] rwm user perms: {perms}")
        
        self.assertIn("read", perms, "rwm user should have 'read' permission")
        self.assertIn("write", perms, "rwm user should have 'write' permission")
        self.assertIn("move", perms, "rwm user should have 'move' permission")
        self.assertNotIn("delete", perms, "rwm user should NOT have 'delete' permission")
        
        self.conn.shutdown()

    def test_json_listing_perms_rwd_user(self):
        """rwd user (read+write+delete, no move) should have perms: ["read", "write", "delete"].
        
        Frontend behavior:
        - Can upload, mkdir, delete
        - Cannot move/rename (no 'move' in perms)
        """
        vcfg = [
            "rwd/:rwd:rwd,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rwd/test.txt", "w") as f:
            f.write("test")
        
        h, body = self.curl("rwd/?ls", user="o")
        self.assert_status(h, "200", "rwd user should access listing")
        
        data = self.parse_json_response(body)
        self.assertIsNotNone(data, "JSON response should be parseable")
        
        perms = data.get("perms", [])
        print(f"[DEBUG] rwd user perms: {perms}")
        
        self.assertIn("read", perms, "rwd user should have 'read' permission")
        self.assertIn("write", perms, "rwd user should have 'write' permission")
        self.assertIn("delete", perms, "rwd user should have 'delete' permission")
        self.assertNotIn("move", perms, "rwd user should NOT have 'move' permission")
        
        self.conn.shutdown()

    # =========================================================================
    # PART 2: Backend API Permission Enforcement Tests
    #
    # These tests verify that even if the frontend is bypassed (e.g., direct API calls),
    # the backend still enforces permissions.
    #
    # Test strategy:
    # - For NO permission: assert 403 response, verify file remains unchanged
    # - For HAVE permission: assert NOT 403 (may be 200/201/302 or 500 if needs broker)
    # =========================================================================

    def test_readonly_user_cannot_upload_bup(self):
        """Read-only user (no 'w') should get 403 when uploading via bput.
        
        Frontend: Upload buttons are hidden (no 'write' in perms)
        Backend: Returns 403 even if frontend is bypassed
        """
        vcfg = [
            "ro/:ro:r,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        files = [("test.txt", "Should not be uploaded")]
        
        h, body = self.bup("ro", files, user="o")
        print(f"[DEBUG] Read-only bup response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "403", "Read-only user should get 403 for upload")
        
        if os.path.exists("ro"):
            files_in_ro = os.listdir("ro")
            test_files = [f for f in files_in_ro if "test" in f.lower()]
            self.assertEqual(len(test_files), 0, "No files should be created in read-only dir")
        
        self.conn.shutdown()

    def test_readonly_user_cannot_upload_put(self):
        """Read-only user should get 403 for PUT upload."""
        vcfg = [
            "ro/:ro:r,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        hdr_fmt = "PUT /ro/test_put.txt HTTP/1.1\r\nPW: o\r\nConnection: close\r\nContent-Length: 12\r\n\r\ntest content"
        full_request = hdr_fmt.encode("utf-8")
        
        conn = self.conn.setbuf(full_request)
        HttpCli(conn).run()
        h, body = self._parse_response(conn.s._reply)
        
        print(f"[DEBUG] Read-only PUT response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "403", "Read-only user should get 403 for PUT")
        self.assertFalse(os.path.exists("ro/test_put.txt"), "File should not be created")
        
        self.conn.shutdown()

    def test_readonly_user_cannot_mkdir(self):
        """Read-only user (no 'w') should get 403 when trying to mkdir.
        
        Frontend: Mkdir button is hidden (no 'write' in perms)
        Backend: Returns 403 even if frontend is bypassed
        """
        vcfg = [
            "ro/:ro:r,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        h, body = self.mkdir("ro", "newdir", user="o")
        print(f"[DEBUG] Read-only mkdir response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "403", "Read-only user should get 403 for mkdir")
        self.assertFalse(os.path.exists("ro/newdir"), "Directory should not be created")
        
        self.conn.shutdown()

    def test_readonly_user_can_read(self):
        """Read-only user CAN read files and list directories."""
        vcfg = [
            "ro/:ro:r,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("ro/readme.txt", "w") as f:
            f.write("read me")
        
        h, body = self.curl("ro/readme.txt", user="o")
        self.assert_status(h, "200", "Read-only user should be able to read")
        self.assertIn("read me", body, "File content should be accessible")
        
        h, body = self.curl("ro/", user="o")
        self.assert_status(h, "200", "Read-only user should be able to list directory")
        
        self.conn.shutdown()

    def test_write_user_can_upload(self):
        """User with 'w' permission CAN upload files."""
        vcfg = [
            "rw/:rw:rw,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        files = [("test_upload.txt", "Uploaded content")]
        
        h, body = self.bup("rw", files, user="o")
        print(f"[DEBUG] Write user bup response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "201", "Write user should be able to upload")
        
        files_in_rw = os.listdir("rw")
        test_files = [f for f in files_in_rw if "test_upload" in f]
        self.assertTrue(len(test_files) > 0, "Uploaded file should exist")
        
        self.conn.shutdown()

    def test_write_user_can_mkdir(self):
        """User with 'w' permission CAN create directories."""
        vcfg = [
            "rw/:rw:rw,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        h, body = self.mkdir("rw", "newdir", user="o")
        print(f"[DEBUG] Write user mkdir response: {h.split(chr(10))[0]}")
        
        status = self.get_status_code(h)
        self.assertNotEqual(status, "403", "Write user should NOT get 403 for mkdir")
        
        self.assertTrue(os.path.exists("rw/newdir"), "Directory should be created")
        
        self.conn.shutdown()

    def test_write_user_cannot_delete_without_d(self):
        """User without 'd' permission should get 403 when trying to delete.
        
        Frontend: Delete button is hidden (no 'delete' in perms)
        Backend: Returns 403 even if frontend is bypassed
        """
        vcfg = [
            "rw/:rw:rw,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rw/keep_me.txt", "w") as f:
            f.write("should stay")
        
        h, body = self.delete("rw/keep_me.txt", user="o")
        print(f"[DEBUG] Write user (no d) delete response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "403", "User without 'd' permission should get 403 for delete")
        self.assertTrue(os.path.exists("rw/keep_me.txt"), "File should still exist without delete permission")
        
        self.conn.shutdown()

    def test_write_user_cannot_move_without_m(self):
        """User without 'm' permission should get 403 when trying to move.
        
        Frontend: Rename/cut buttons are hidden (no 'move' in perms)
        Backend: Returns 403 even if frontend is bypassed
        """
        vcfg = [
            "rw/:rw:rw,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rw/src.txt", "w") as f:
            f.write("source file")
        
        h, body = self.move("rw/src.txt", "rw/dst.txt", user="o")
        print(f"[DEBUG] Write user (no m) move response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "403", "User without 'm' permission should get 403 for move")
        self.assertTrue(os.path.exists("rw/src.txt"), "Without move permission, src should stay")
        self.assertFalse(os.path.exists("rw/dst.txt"), "Without move permission, dst should not exist")
        
        self.conn.shutdown()

    def test_rwm_user_cannot_delete(self):
        """rwm user (no 'd') should get 403 for delete, but CAN move.
        
        This tests that 'delete' is a separate permission from 'move'.
        """
        vcfg = [
            "rwm/:rwm:rwm,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rwm/cannot_delete.txt", "w") as f:
            f.write("protected")
        
        h, body = self.delete("rwm/cannot_delete.txt", user="o")
        print(f"[DEBUG] rwm user delete response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "403", "rwm user should get 403 for delete (no 'd' permission)")
        self.assertTrue(os.path.exists("rwm/cannot_delete.txt"), "File should be protected (no 'd')")
        
        self.conn.shutdown()

    def test_rwd_user_cannot_move(self):
        """rwd user (no 'm') should get 403 for move, but CAN delete.
        
        This tests that 'move' is a separate permission from 'delete'.
        """
        vcfg = [
            "rwd/:rwd:rwd,o",
        ]
        self.setup_test_env(vcfg, ["o:o"])
        
        with open("rwd/src.txt", "w") as f:
            f.write("source")
        
        h, body = self.move("rwd/src.txt", "rwd/dst.txt", user="o")
        print(f"[DEBUG] rwd user move response: {h.split(chr(10))[0]}")
        
        self.assert_status(h, "403", "rwd user should get 403 for move (no 'm' permission)")
        self.assertTrue(os.path.exists("rwd/src.txt"), "Source should stay (no 'm' permission)")
        self.assertFalse(os.path.exists("rwd/dst.txt"), "Dest should not exist (no 'm' permission)")
        
        self.conn.shutdown()

    def test_no_access_user_gets_403(self):
        """User with no access to a volume should get 403."""
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
        self.assert_status(h, "403", "No access user should get 403")
        
        h, body = self.curl("public/", user="o")
        self.assert_status(h, "200", "Public access user should get 200")
        
        self.conn.shutdown()

    # =========================================================================
    # PART 3: Summary Test - Frontend UI Behavior Mapping
    #
    # This test demonstrates how perms field maps to frontend UI behavior.
    # =========================================================================

    def test_permission_scenarios_summary(self):
        """Summary test demonstrating all permission scenarios and frontend UI behavior.
        
        Permission to Frontend UI mapping:
        
        | User Type   | perms from JSON | Buttons Shown                          | Right-click Menu        | Shortcuts Enabled
        |-------------|-----------------|----------------------------------------|-------------------------|-------------------
        | Read-only   | ["read"]        | Search only                            | None (no write/delete) | None
        | Upload-only | ["read","write"]| Search, Upload, Mkdir                  | New file/folder, Paste  | Ctrl+V only
        | Upload+Del  | ["read","write","delete"] | Search, Upload, Mkdir, Delete | New file/folder, Delete, Paste | Ctrl+K, Ctrl+V
        | Upload+Move | ["read","write","move"] | Search, Upload, Mkdir, Rename | New file/folder, Cut, Paste, Rename | Ctrl+X, Ctrl+V, F2
        | Full        | ["read","write","move","delete"] | All buttons | All menu items | All shortcuts
        
        Backend permission enforcement:
        - No 'write' → upload/mkdir returns 403
        - No 'delete' → delete returns 403  
        - No 'move' → move/rename returns 403
        """
        vcfg = [
            "ro/:ro:r,ro",
            "rw/:rw:rw,rw",
            "rwd/:rwd:rwd,rwd",
            "rwm/:rwm:rwm,rwm",
            "full/:full:rwmd,full",
        ]
        users = ["ro:ro", "rw:rw", "rwd:rwd", "rwm:rwm", "full:full"]
        self.setup_test_env(vcfg, users)
        
        with open("ro/ro_file.txt", "w") as f: f.write("ro")
        with open("rw/rw_file.txt", "w") as f: f.write("rw")
        with open("rwd/rwd_file.txt", "w") as f: f.write("rwd")
        with open("rwm/rwm_file.txt", "w") as f: f.write("rwm")
        with open("full/full_file.txt", "w") as f: f.write("full")
        
        print("\n" + "="*80)
        print("PERMISSION SCENARIOS SUMMARY - Frontend UI Data Source Validation")
        print("="*80)
        
        scenarios = [
            ("Read-only (r)", "ro", "ro", ["read"], False, False, False, False),
            ("Upload-only (rw)", "rw", "rw", ["read", "write"], True, True, False, False),
            ("Upload+Delete (rwd)", "rwd", "rwd", ["read", "write", "delete"], True, True, True, False),
            ("Upload+Move (rwm)", "rwm", "rwm", ["read", "write", "move"], True, True, False, True),
            ("Full (rwmd)", "full", "full", ["read", "write", "move", "delete"], True, True, True, True),
        ]
        
        all_passed = True
        for name, user, path, expected_perms, can_upload, can_mkdir, can_delete, can_move in scenarios:
            print(f"\n--- {name} User ---")
            
            h, body = self.curl(f"{path}/?ls", user=user)
            data = self.parse_json_response(body)
            perms = data.get("perms", []) if data else []
            print(f"  perms from JSON listing: {perms}")
            print(f"  expected perms: {expected_perms}")
            
            for p in expected_perms:
                if p not in perms:
                    print(f"  FAIL: Missing expected permission: {p}")
                    all_passed = False
            
            for p in perms:
                if p not in expected_perms:
                    print(f"  FAIL: Unexpected permission: {p}")
                    all_passed = False
            
            print(f"  -> Frontend button visibility based on perms:")
            print(f"     - Upload buttons (needs 'write'): {'[SHOWN]' if 'write' in perms else '[HIDDEN]'}")
            print(f"     - Mkdir button (needs 'write'): {'[SHOWN]' if 'write' in perms else '[HIDDEN]'}")
            print(f"     - Delete button (needs 'delete'): {'[SHOWN]' if 'delete' in perms else '[HIDDEN]'}")
            print(f"     - Rename button (needs 'write'+'move'): {'[SHOWN]' if 'write' in perms and 'move' in perms else '[HIDDEN]'}")
            
            print(f"  -> Shortcuts allowed:")
            print(f"     - Ctrl+K (delete): {'[ENABLED]' if 'delete' in perms else '[BLOCKED]'}")
            print(f"     - Ctrl+X (cut): {'[ENABLED]' if 'move' in perms else '[BLOCKED]'}")
            print(f"     - Ctrl+V (paste): {'[ENABLED]' if 'write' in perms else '[BLOCKED]'}")
            print(f"     - F2 (rename): {'[ENABLED]' if 'write' in perms and 'move' in perms else '[BLOCKED]'}")
            
            self.assertEqual(sorted(perms), sorted(expected_perms), f"{name} perms mismatch")
        
        print("\n" + "="*80)
        print("BACKEND PERMISSION ENFORCEMENT - Verifying 403 responses")
        print("="*80)
        
        print("\n--- Testing Read-only user (no 'w') ---")
        h, body = self.mkdir("ro", "should_fail", user="ro")
        status = self.get_status_code(h)
        print(f"  mkdir response: {status}")
        self.assertEqual(status, "403", "Read-only mkdir should be 403")
        
        h, body = self.delete("ro/ro_file.txt", user="ro")
        status = self.get_status_code(h)
        print(f"  delete response: {status}")
        self.assertEqual(status, "403", "Read-only delete should be 403")
        
        print("\n--- Testing Upload-only user (rw, no 'm' or 'd') ---")
        h, body = self.delete("rw/rw_file.txt", user="rw")
        status = self.get_status_code(h)
        print(f"  delete response: {status}")
        self.assertEqual(status, "403", "Upload-only delete should be 403")
        
        h, body = self.move("rw/rw_file.txt", "rw/renamed.txt", user="rw")
        status = self.get_status_code(h)
        print(f"  move response: {status}")
        self.assertEqual(status, "403", "Upload-only move should be 403")
        
        print("\n--- Testing rwd user (no 'm') ---")
        h, body = self.move("rwd/rwd_file.txt", "rwd/moved.txt", user="rwd")
        status = self.get_status_code(h)
        print(f"  move response: {status}")
        self.assertEqual(status, "403", "rwd move should be 403")
        
        print("\n--- Testing rwm user (no 'd') ---")
        h, body = self.delete("rwm/rwm_file.txt", user="rwm")
        status = self.get_status_code(h)
        print(f"  delete response: {status}")
        self.assertEqual(status, "403", "rwm delete should be 403")
        
        print("\n" + "="*80)
        if all_passed:
            print("[OK] ALL PERMISSION CHECKS PASSED")
        else:
            print("[FAIL] SOME CHECKS FAILED")
        print("="*80)
        
        self.conn.shutdown()


if __name__ == "__main__":
    unittest.main()

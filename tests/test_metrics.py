#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import re
import shutil
import tempfile
import unittest

from copyparty.__init__ import PY2
from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from copyparty.metrics import Metrics
from tests import util as tu
from tests.util import Cfg


def hdr(query):
    h = "GET /{} HTTP/1.1\r\nCookie: cppwd=o\r\nConnection: close\r\n\r\n"
    return h.format(query).encode("utf-8")


class TestMetrics(unittest.TestCase):
    def setUp(self):
        self.td = tu.get_ramdisk()
        os.chdir(self.td)

    def tearDown(self):
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(self.td)

    def cinit(self):
        if self.conn:
            self.fstab = self.conn.hsrv.hub.up2k.fstab
            self.conn.hsrv.hub.up2k.shutdown()
        self.asrv = AuthSrv(self.args, self.log)
        self.conn = tu.VHttpConn(self.args, self.asrv, self.log, b"", True)
        if self.fstab:
            self.conn.hsrv.hub.up2k.fstab = self.fstab

        if not self.metrics:
            self.metrics = Metrics(self.conn)
        self.conn.broker = self.conn.hsrv.broker
        self.conn.hsrv.metrics = self.metrics
        for k in "ncli nsus nban".split():
            setattr(self.conn, k, 9)

    def test(self):
        zs = "nos_dup nos_hdd nos_unf nos_vol nos_vst"
        opts = {x: False for x in zs.split()}
        self.args = Cfg(v=[".::A"], a=[], stats=True, **opts)
        self.conn = self.fstab = self.metrics = None
        self.cinit()
        h, b = self.curl(".cpr/metrics")
        self.assertIn(".1 200 OK", h)
        ptns = r"""
cpp_uptime_seconds [0-9]\.[0-9]{3}$
cpp_boot_unixtime_seconds [0-9]{7,10}\.[0-9]{3}$
cpp_http_reqs_created [0-9]{7,10}$
cpp_http_reqs_total -1$
cpp_http_conns 9$
cpp_total_bans 9$
cpp_sus_reqs_total 9$
cpp_active_bans 0$
cpp_idle_vols 0$
cpp_busy_vols 0$
cpp_offline_vols 0$
cpp_db_idle_seconds 86399999\.00$
cpp_db_act_seconds 0\.00$
cpp_hashing_files 0$
cpp_tagq_files 0$
cpp_disk_size_bytes\{vol="/"\} [0-9]+$
cpp_disk_free_bytes\{vol="/"\} [0-9]+$
cpp_vol_bytes\{vol="/"\} 0$
cpp_vol_files\{vol="/"\} 0$
cpp_vol_bytes\{vol="total"\} 0$
cpp_vol_files\{vol="total"\} 0$
cpp_dupe_bytes\{vol="total"\} 0$
cpp_dupe_files\{vol="total"\} 0$
"""
        if not PY2:
            ptns += r"""
cpp_mtpq_files 0$
cpp_unf_bytes\{vol="/"\} 0$
cpp_unf_files\{vol="/"\} 0$
cpp_unf_bytes\{vol="total"\} 0$
cpp_unf_files\{vol="total"\} 0$
"""
        for want in [x for x in ptns.split("\n") if x]:
            if not re.search("^" + want, b.replace("\r", ""), re.MULTILINE):
                raise Exception("server response:\n%s\n\nmissing item: %s" % (b, want))

    def curl(self, url, binary=False):
        conn = self.conn.setbuf(hdr(url))
        HttpCli(conn).run()
        if binary:
            h, b = conn.s._reply.split(b"\r\n\r\n", 1)
            return [h.decode("utf-8"), b]

        return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)

    def log(self, src, msg, c=0):
        print(msg)

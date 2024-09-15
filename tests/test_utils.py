#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import unittest

from copyparty.__main__ import PY2
from copyparty.util import w8enc
from tests import util as tu


class TestUtils(unittest.TestCase):
    def cmp(self, orig, t1, t2):
        if t1 != t2:
            raise Exception("\n%r\n%r\n%r\n" % (w8enc(orig), t1, t2))

    def test_quotep(self):
        if PY2:
            raise unittest.SkipTest()

        from copyparty.util import _quotep3, _quotep3b, w8dec

        txt = w8dec(tu.randbytes(8192))
        self.cmp(txt, _quotep3(txt), _quotep3b(txt))

    def test_unquote(self):
        if PY2:
            raise unittest.SkipTest()

        from urllib.parse import unquote_to_bytes as u2b

        from copyparty.util import unquote

        for btxt in (
            tu.randbytes(8192),
            br"%ed%91qw,er;ty%20as df?gh+jkl%zxc&vbn <qwe>\"rty'uio&asd&nbsp;fgh",
        ):
            self.cmp(btxt, unquote(btxt), u2b(btxt))

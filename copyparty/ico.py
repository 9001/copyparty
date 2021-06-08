# coding: utf-8
from __future__ import print_function, unicode_literals

import hashlib
import colorsys

from .__init__ import PY2


class Ico(object):
    def __init__(self, args):
        self.args = args

    def get(self, ext, as_thumb):
        """placeholder to make thumbnails not break"""

        h = hashlib.md5(ext.encode("utf-8")).digest()[:2]
        if PY2:
            h = [ord(x) for x in h]

        c1 = colorsys.hsv_to_rgb(h[0] / 256.0, 1, 0.3)
        c2 = colorsys.hsv_to_rgb(h[0] / 256.0, 1, 1)
        c = list(c1) + list(c2)
        c = [int(x * 255) for x in c]
        c = "".join(["{:02x}".format(x) for x in c])

        h = 30
        if not self.args.th_no_crop and as_thumb:
            w, h = self.args.th_size.split("x")
            h = int(100 / (float(w) / float(h)))

        svg = """\
<?xml version="1.0" encoding="UTF-8"?>
<svg version="1.1" viewBox="0 0 100 {}" xmlns="http://www.w3.org/2000/svg"><g>
<rect width="100%" height="100%" fill="#{}" />
<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" xml:space="preserve"
  fill="#{}" font-family="monospace" font-size="14px" style="letter-spacing:.5px">{}</text>
</g></svg>
"""
        svg = svg.format(h, c[:6], c[6:], ext).encode("utf-8")

        return ["image/svg+xml", svg]

# coding: utf-8
from __future__ import division, print_function, unicode_literals

import argparse  # typechk
import colorsys
import hashlib
import re

from .__init__ import PY2
from .th_srv import HAVE_PIL, HAVE_PILF
from .util import BytesIO, html_escape  # type: ignore


RE_CSS_COLOR = re.compile(r"[^a-zA-Z0-9#()%.,/-]")


class Ico(object):
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    def get(self, ext: str, as_thumb: bool, png: bool, accent: str) -> tuple[str, bytes]:
        """placeholder to make thumbnails not break"""

        bext = ext.encode("ascii", "replace")
        ext = bext.decode("utf-8")
        
        w = 100
        h = 30
        if as_thumb:
            sw, sh = self.args.th_size.split("x")
            h = int(100.0 / (float(sw) / float(sh)))

        if accent:
            accent = RE_CSS_COLOR.sub("", accent)

        svg = """\
<?xml version="1.0" encoding="UTF-8"?>
<svg version="1.1" viewBox="0 0 100 {}" xmlns="http://www.w3.org/2000/svg"><g>
<rect width="100%" height="100%" fill="#0000" />
<text x="50%" y="{}" dominant-baseline="middle" text-anchor="middle" xml:space="preserve"
  fill="{}" font-family="monospace" font-size="14px" style="letter-spacing:.5px">{}</text>
</g></svg>
"""

        txt = html_escape(ext, True)
        if "\n" in txt:
            lines = txt.split("\n")
            n = len(lines)
            y = "20%" if n == 2 else "10%" if n == 3 else "0"
            zs = '<tspan x="50%%" dy="1.2em">%s</tspan>'
            txt = "".join([zs % (x,) for x in lines])
        else:
            y = "50%"

        svg = svg.format(h, y, accent or '#000', txt)

        return "image/svg+xml", svg.encode("utf-8")

# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse  # typechk
import colorsys
import hashlib
import re

from .__init__ import PY2
from .th_srv import HAVE_PIL, HAVE_PILF
from .util import BytesIO, html_escape  # type: ignore


class Ico(object):
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    def get(self, ext: str, as_thumb: bool, chrome: bool, accent: str) -> tuple[str, bytes]:
        """placeholder to make thumbnails not break"""

        bext = ext.encode("ascii", "replace")
        ext = bext.decode("utf-8")
        
        w = 100
        h = 30
        if as_thumb:
            sw, sh = self.args.th_size.split("x")
            h = int(100.0 / (float(sw) / float(sh)))

        if chrome & 0:
            # cannot handle more than ~2000 unique SVGs
            if HAVE_PILF:
                # pillow 10.1 made this the default font;
                # svg: 3.7s, this: 36s
                try:
                    from PIL import Image, ImageDraw

                    # [.lt] are hard to see lowercase / unspaced
                    ext2 = re.sub("(.)", "\\1 ", ext).upper()

                    h = int(128.0 * h / w)
                    w = 128
                    img = Image.new("RGBA", (w, h), "#00000000")
                    pb = ImageDraw.Draw(img)
                    _, _, tw, th = pb.textbbox((0, 0), ext2, font_size=16)
                    xy = (int((w - tw) / 2), int((h - th) / 2))
                    pb.text(xy, ext2, fill=accent, font_size=16)

                    img = img.resize((w * 2, h * 2), Image.NEAREST)

                    buf = BytesIO()
                    img.save(buf, format="PNG", compress_level=1)
                    return "image/png", buf.getvalue()

                except:
                    pass

            if HAVE_PIL:
                # svg: 3s, cache: 6s, this: 8s
                from PIL import Image, ImageDraw

                h = int(64.0 * h / w)
                w = 64
                img = Image.new("RGBA", (w, h), "#00000000")
                pb = ImageDraw.Draw(img)
                try:
                    _, _, tw, th = pb.textbbox((0, 0), ext)
                except:
                    tw, th = pb.textsize(ext)  # type: ignore

                tw += len(ext)
                cw = tw // len(ext)
                x = ((w - tw) // 2) - (cw * 2) // 3
                fill = accent
                for ch in ext:
                    pb.text((x, (h - th) // 2), " %s " % (ch,), fill=fill)
                    x += cw

                img = img.resize((w * 3, h * 3), Image.NEAREST)

                buf = BytesIO()
                img.save(buf, format="PNG", compress_level=1)
                return "image/png", buf.getvalue()

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

        svg = svg.format(h, y, accent, txt)

        return "image/svg+xml", svg.encode("utf-8")

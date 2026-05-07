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
        zb = hashlib.sha1(bext).digest()[2:4]
        if PY2:
            zb = [ord(x) for x in zb]  # type: ignore

        c1 = colorsys.hsv_to_rgb(zb[0] / 256.0, 1, 1)
        c2 = colorsys.hsv_to_rgb(zb[0] / 256.0, 0.5 if HAVE_PILF else 1, 0.9)
        ci = [int(x * 255) for x in list(c1) + list(c2)]
        c = "".join(["%02x" % (x,) for x in ci])

        w = 100
        h = 30
        if as_thumb:
            sw, sh = self.args.th_size.split("x")
            h = int(100.0 / (float(sw) / float(sh)))

        if chrome:
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
                    img = Image.new("RGB", (w, h), "#" + c[:6])
                    pb = ImageDraw.Draw(img)
                    _, _, tw, th = pb.textbbox((0, 0), ext2, font_size=16)
                    xy = (int((w - tw) / 2), int((h - th) / 2))
                    pb.text(xy, ext2, fill="#" + c[6:], font_size=16)

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
                img = Image.new("RGB", (w, h), "#" + c[:6])
                pb = ImageDraw.Draw(img)
                try:
                    _, _, tw, th = pb.textbbox((0, 0), ext)
                except:
                    tw, th = pb.textsize(ext)  # type: ignore

                tw += len(ext)
                cw = tw // len(ext)
                x = ((w - tw) // 2) - (cw * 2) // 3
                fill = "#" + c[6:]
                for ch in ext:
                    pb.text((x, (h - th) // 2), " %s " % (ch,), fill=fill)
                    x += cw

                img = img.resize((w * 3, h * 3), Image.NEAREST)

                buf = BytesIO()
                img.save(buf, format="PNG", compress_level=1)
                return "image/png", buf.getvalue()

#         svg = """\
# <?xml version="1.0" encoding="UTF-8"?>
# <svg version="1.1" viewBox="0 0 100 {}" xmlns="http://www.w3.org/2000/svg"><g>
# <rect width="100%" height="100%" fill="#{}" />
# <text x="50%" y="{}" dominant-baseline="middle" text-anchor="middle" xml:space="preserve"
#   fill="#{}" font-family="monospace" font-size="14px" style="letter-spacing:.5px">{}</text>
# </g></svg>
# """

        txt = html_escape(ext, True)
        if "\n" in txt:
            lines = txt.split("\n")
            n = len(lines)
            y = "20%" if n == 2 else "10%" if n == 3 else "0"
            zs = '<tspan x="50%%" dy="1.2em">%s</tspan>'
            txt = "".join([zs % (x,) for x in lines])
        else:
            y = "55%"

        svg = svg.format(h, c[:6], y, c[6:], txt)

        if(len(ext) > 3):
            fontsz = 12 / len(ext) * 3
        else:
            fontsz = 12

        svg = """\
<?xml version="1.0" encoding="UTF-8"?>
<svg
    viewBox="0 0 48 48"
    version="1.1"
    xmlns="http://www.w3.org/2000/svg">
  <path
    fill="#{}aa"
    d="m 28.22643,3.6905246 0.0063,10.1096644 a 1.6331061,1.6331061 44.698111 0 0 1.649296,1.632007 l 9.339558,-0.09259 z"/>
  <path
    class="a"
    d="M39.5,15.5h-9a2,2,0,0,1-2-2v-9h-18a2,2,0,0,0-2,2v35a2,2,0,0,0,2,2h27a2,2,0,0,0,2-2Z"
    id="path1" 
    stroke-width="1" fill="none" stroke="{}" stroke-linecap="round" stroke-linejoin="round" />
  <line
    class="a"
    x1="28.5"
    y1="4.5"
    x2="39.5"
    y2="15.5"
    stroke-width="1" fill="none" stroke="{}" stroke-linecap="round" stroke-linejoin="round" />
  <text
    font-size="{}px" dominant-baseline="middle" text-anchor="middle" xml:space="preserve"
    fill="{}" font-family="monospace" style="letter-spacing:.5px"
    x="50%" y="{}">{}</text>
</svg>
"""
        svg = svg.format(c[:6], accent, accent, fontsz, accent, y, txt)

        if(txt == 'folder'):
            svg = """\
<?xml version="1.0" encoding="UTF-8"?>
<svg version="1.1" width="100%" height="100%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path fill-rule="evenodd" clip-rule="evenodd" d="M3 7C3 5.89543 3.89543 5 5 5L8.67157 5C9.20201 5 9.71071 5.21071 10.0858 5.58579L10.9142 6.41421C11.2893 6.78929 11.798 7 12.3284 7H19C20.1046 7 21 7.89543 21 9V17C21 18.1046 20.1046 19 19 19H5C3.89543 19 3 18.1046 3 17V7Z" 
    fill="{}"/>
</svg>
"""
            svg = svg.format(accent)

        return "image/svg+xml", svg.encode("utf-8")

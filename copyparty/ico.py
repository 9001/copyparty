import hashlib
import colorsys

from .__init__ import PY2


class Ico(object):
    def __init__(self):
        pass

    def get(self, ext):
        """placeholder to make thumbnails not break"""

        h = hashlib.md5(ext.encode("utf-8")).digest()[:2]
        if PY2:
            h = [ord(x) for x in h]

        c1 = colorsys.hsv_to_rgb(h[0] / 256.0, 1, 0.3)
        c2 = colorsys.hsv_to_rgb(h[0] / 256.0, 1, 1)
        c = list(c1) + list(c2)
        c = [int(x * 255) for x in c]
        c = "".join(["{:02x}".format(x) for x in c])

        svg = """\
<?xml version="1.0" encoding="UTF-8"?>
<svg version="1.1" viewBox="0 0 100 30" xmlns="http://www.w3.org/2000/svg"><g>
<rect width="100%" height="100%" fill="#{}" />
<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#{}" font-family="sans-serif" font-size="16px" xml:space="preserve">{}</text>
</g></svg>
"""
        svg = svg.format(c[:6], c[6:], ext).encode("utf-8")

        return ["image/svg+xml", svg]

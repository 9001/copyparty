#!/usr/bin/env python3

import sys
from fontTools.ttLib import TTFont, newTable


def main():
    woff = sys.argv[1]
    font = TTFont(woff)
    print(repr(font["hhea"].__dict__))
    print(repr(font["OS/2"].__dict__))
    # font["hhea"].ascent = round(base_asc * mul)
    # font["hhea"].descent = round(base_desc * mul)
    # font["OS/2"].usWinAscent = round(base_asc * mul)
    font["OS/2"].usWinDescent = round(font["OS/2"].usWinDescent * 1.1)
    font["OS/2"].sTypoDescender = round(font["OS/2"].sTypoDescender * 1.1)

    try:
        del font["post"].mapping["Delta#1"]
    except:
        pass

    font.save(woff + ".woff2")


if __name__ == "__main__":
    main()

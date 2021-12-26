#!/usr/bin/env python3

"""
use copyparty to xdg-open anything that is posted to it

example copyparty config to use this:
  --urlform save,get -v.::w:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,bin/mtag/very-bad-idea.py
"""

import os
import sys
import subprocess as sp
from urllib.parse import unquote_to_bytes as unquote


def main():
    with open(os.path.abspath(sys.argv[1]), "rb") as f:
        txt = f.read()

    txt = unquote(txt.replace(b"+", b" ")).decode("utf-8")[4:]

    sp.call(["notify-send", "", txt])
    sp.call(["xdotool", "key", "ctrl+w"])
    sp.call(["xdg-open", txt])


main()

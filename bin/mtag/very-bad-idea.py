#!/usr/bin/env python3

"""
use copyparty to xdg-open anything that is posted to it,
  and also xdg-open file uploads

HELLA DANGEROUS,
  GIVES RCE TO ANYONE WHO HAVE UPLOAD PERMISSIONS

example copyparty config to use this:
  --urlform save,get -v.::w:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,bin/mtag/very-bad-idea.py

recommended deps:
  apt install xdotool libnotify-bin
"""

import os
import sys
import subprocess as sp
from urllib.parse import unquote_to_bytes as unquote


def main():
    fp = os.path.abspath(sys.argv[1])
    with open(fp, "rb") as f:
        txt = f.read(4096)

    if txt.startswith(b"msg="):
        open_post(txt)
    else:
        open_url(fp)


def open_post(txt):
    txt = unquote(txt.replace(b"+", b" ")).decode("utf-8")[4:]
    open_url(txt)


def open_url(txt):
    sp.call(["notify-send", "", txt])
    sp.call(["xdotool", "key", "ctrl+w"])
    sp.call(["xdg-open", txt])


main()

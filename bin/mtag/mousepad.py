#!/usr/bin/env python3

import os
import sys
import subprocess as sp


"""
mtp test -- opens a texteditor

usage:
  -vsrv/v1:v1:r:c,mte=+x1:c,mtp=x1=ad,p,bin/mtag/mousepad.py

explained:
  c,mte: list of tags to index in this volume
  c,mtp: add new tag provider
     x1: dummy tag to provide
     ad: dontcare if audio or not
      p: priority 1 (run after initial tag-scan with ffprobe or mutagen)
"""


def main():
    env = os.environ.copy()
    env["DISPLAY"] = ":0.0"

    if False:
        # open the uploaded file
        fp = sys.argv[-1]
    else:
        # display stdin contents (`oth_tags`)
        fp = "/dev/stdin"

    p = sp.Popen(["/usr/bin/mousepad", fp])
    p.communicate()


main()

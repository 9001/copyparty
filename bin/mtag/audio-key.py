#!/usr/bin/env python

import os
import sys
import tempfile
import subprocess as sp
import keyfinder

from copyparty.util import fsenc

"""
dep: github/mixxxdj/libkeyfinder
dep: pypi/keyfinder
dep: ffmpeg
"""


# tried trimming the first/last 5th, bad idea,
# misdetects 9a law field (Sphere Caliber) as 10b,
# obvious when mixing 9a ghostly parapara ship


def det(tf):
    # fmt: off
    sp.check_call([
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-v", "fatal",
        "-y", "-i", fsenc(sys.argv[1]),
        "-t", "300",
        "-sample_fmt", "s16",
        tf
    ])
    # fmt: on

    print(keyfinder.key(tf).camelot())


def main():
    with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as f:
        f.write(b"h")
        tf = f.name

    try:
        det(tf)
    finally:
        os.unlink(tf)


if __name__ == "__main__":
    main()

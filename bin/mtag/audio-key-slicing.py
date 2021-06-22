#!/usr/bin/env python

import re
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

note: this is a janky edition of the regular audio-key.py,
  slicing the files at 20sec intervals and keeping 5sec from each,
  surprisingly accurate but still garbage (446 ok, 69 bad, 13% miss)

  it is fast tho
"""


def get_duration():
    # TODO provide ffprobe tags to mtp as json

    # fmt: off
    dur = sp.check_output([
        "ffprobe",
        "-hide_banner",
        "-v", "fatal",
        "-show_streams",
        "-show_format",
        fsenc(sys.argv[1])
    ])
    # fmt: on

    dur = dur.decode("ascii", "replace").split("\n")
    dur = [x.split("=")[1] for x in dur if x.startswith("duration=")]
    dur = [float(x) for x in dur if re.match(r"^[0-9\.,]+$", x)]
    return list(sorted(dur))[-1] if dur else None


def get_segs(dur):
    # keep first 5s of each 20s,
    # keep entire last segment
    ofs = 0
    segs = []
    while True:
        seg = [ofs, 5]
        segs.append(seg)
        if dur - ofs < 20:
            seg[-1] = int(dur - seg[0])
            break

        ofs += 20

    return segs


def slice(tf):
    dur = get_duration()
    dur = min(dur, 600)  # max 10min
    segs = get_segs(dur)

    # fmt: off
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-v", "fatal",
        "-y"
    ]

    for seg in segs:
        cmd.extend([
            "-ss", str(seg[0]),
            "-i", fsenc(sys.argv[1])
        ])
    
    filt = ""
    for n, seg in enumerate(segs):
        filt += "[{}:a:0]atrim=duration={}[a{}]; ".format(n, seg[1], n)
    
    prev = "a0"
    for n in range(1, len(segs)):
        nxt = "b{}".format(n)
        filt += "[{}][a{}]acrossfade=d=0.5[{}]; ".format(prev, n, nxt)
        prev = nxt

    cmd.extend([
        "-filter_complex", filt[:-2],
        "-map", "[{}]".format(nxt),
        "-sample_fmt", "s16",
        tf
    ])
    # fmt: on

    # print(cmd)
    sp.check_call(cmd)


def det(tf):
    slice(tf)
    print(keyfinder.key(tf).camelot())


def main():
    with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as f:
        f.write(b"h")
        tf = f.name

    try:
        det(tf)
    finally:
        os.unlink(tf)
        pass


if __name__ == "__main__":
    main()

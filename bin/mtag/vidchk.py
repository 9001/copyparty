#!/usr/bin/env python3

import sys
import subprocess as sp

from copyparty.util import fsenc
from copyparty.mtag import ffprobe


"""
inspects video files for errors and such
usage: -mtp vidchk=t600,ay,bin/mtag/vidchk.py
"""


FAST = True  # parse entire file at container level
# FAST = False  # fully decode audio and video streams


def main():
    fp = sys.argv[1]
    md, _ = ffprobe(fp)

    try:
        w = int(md[".resw"][1])
        h = int(md[".resh"][1])
        if not w + h:
            raise Exception()
    except:
        return "could not determine resolution"

    if min(w, h) < 720:
        return "resolution too small"

    zs = (
        "ffmpeg -y -hide_banner -nostdin -v warning"
        + " -err_detect +crccheck+bitstream+buffer+careful+compliant+aggressive+explode"
        " -xerror -i"
    )

    cmd = zs.encode("ascii").split(b" ") + [fsenc(fp)]

    if FAST:
        zs = "-c copy -f null -"
    else:
        zs = "-vcodec rawvideo -acodec pcm_s16le -f null -"

    cmd += zs.encode("ascii").split(b" ")

    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    so, se = p.communicate()
    rc = p.returncode
    if rc:
        err = (so + se).decode("utf-8", "replace").split("\n", 1)[0]
        return f"ERROR {rc}: {err}"

    if se:
        err = se.decode("utf-8", "replace").split("\n", 1)[0]
        return f"Warning: {err}"

    return None


if __name__ == "__main__":
    print(main() or "ok")

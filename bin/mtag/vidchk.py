#!/usr/bin/env python3

import json
import sys
import subprocess as sp

try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p.encode("utf-8")


_ = r"""
inspects video files for errors and such

usage:
  -mtp vidchk=t600,ay,p,bin/mtag/vidchk.py

explained:
t600: timeout 10min
  ay: only process files which contain audio (including video with audio)
   p: set priority 1 (lowest priority after initial ffprobe/mutagen for base tags),
       makes copyparty feed base tags into this script as json

if you wanna use this script standalone / separately from copyparty,
provide the video resolution on stdin as json:  {"res":"1920x1080"}
"""


FAST = True  # parse entire file at container level
# FAST = False  # fully decode audio and video streams


def main():
    fp = sys.argv[1]
    zb = sys.stdin.buffer.read()
    zs = zb.decode("utf-8", "replace")
    md = json.loads(zs)

    try:
        w, h = [int(x) for x in md["res"].split("x")]
        if not w + h:
            raise Exception()
    except:
        return "could not determine resolution"

    if min(w, h) < 1080:
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

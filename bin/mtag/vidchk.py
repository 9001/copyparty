#!/usr/bin/env python3

import json
import re
import sys
import subprocess as sp

try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p.encode("utf-8")


_ = r"""
inspects video files for errors and such
plus stores a bunch of metadata to filename.ff.json

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


# warnings to ignore
harmless = re.compile("^Unsupported codec with id ")


def wfilter(lines):
    return [x for x in lines if not harmless.search(x)]


def errchk(so, se, rc):
    if rc:
        err = (so + se).decode("utf-8", "replace").split("\n", 1)
        err = wfilter(err) or err
        return f"ERROR {rc}: {err[0]}"

    if se:
        err = se.decode("utf-8", "replace").split("\n", 1)
        err = wfilter(err)
        if err:
            return f"Warning: {err[0]}"

    return None


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

    # grab streams/format metadata + 2 seconds of frames at the start and end
    zs = "ffprobe -hide_banner -v warning -of json -show_streams -show_format -show_packets -show_data_hash crc32 -read_intervals %+2,999999%+2"
    cmd = zs.encode("ascii").split(b" ") + [fsenc(fp)]
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    so, se = p.communicate()

    # spaces to tabs, drops filesize from 69k to 48k
    so = b"\n".join(
        [
            b"\t" * int((len(x) - len(x.lstrip())) / 4) + x.lstrip()
            for x in (so or b"").split(b"\n")
        ]
    )
    with open(fsenc(f"{fp}.ff.json"), "wb") as f:
        f.write(so)

    err = errchk(so, se, p.returncode)
    if err:
        return err

    if min(w, h) < 1080:
        return "resolution too small"

    zs = (
        "ffmpeg -y -hide_banner -nostdin -v warning"
        + " -err_detect +crccheck+bitstream+buffer+careful+compliant+aggressive+explode"
        + " -xerror -i"
    )

    cmd = zs.encode("ascii").split(b" ") + [fsenc(fp)]

    if FAST:
        zs = "-c copy -f null -"
    else:
        zs = "-vcodec rawvideo -acodec pcm_s16le -f null -"

    cmd += zs.encode("ascii").split(b" ")

    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    so, se = p.communicate()
    return errchk(so, se, p.returncode)


if __name__ == "__main__":
    print(main() or "ok")

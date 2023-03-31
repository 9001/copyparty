#!/usr/bin/env python

import os
import sys
import vamp
import tempfile
import numpy as np
import subprocess as sp

from copyparty.util import fsenc

"""
dep: vamp
dep: beatroot-vamp
dep: ffmpeg
"""


# save beat timestamps to ".beats/filename.txt"
SAVE = False


def det(tf):
    # fmt: off
    sp.check_call([
        b"ffmpeg",
        b"-nostdin",
        b"-hide_banner",
        b"-v", b"fatal",
        b"-y", b"-i", fsenc(sys.argv[1]),
        b"-map", b"0:a:0",
        b"-ac", b"1",
        b"-ar", b"22050",
        b"-t", b"360",
        b"-f", b"f32le",
        fsenc(tf)
    ])
    # fmt: on

    with open(tf, "rb") as f:
        d = np.fromfile(f, dtype=np.float32)
        try:
            # 98% accuracy on jcore
            c = vamp.collect(d, 22050, "beatroot-vamp:beatroot")
            cl = c["list"]
        except:
            # fallback; 73% accuracy
            plug = "vamp-example-plugins:fixedtempo"
            c = vamp.collect(d, 22050, plug, parameters={"maxdflen": 40})
            print(c["list"][0]["label"].split(" ")[0])
            return

    # throws if detection failed:
    beats = [float(x["timestamp"]) for x in cl]
    bds = [b - a for a, b in zip(beats, beats[1:])]
    bds.sort()
    n0 = int(len(bds) * 0.2)
    n1 = int(len(bds) * 0.75) + 1
    bds = bds[n0:n1]
    bpm = sum(bds)
    bpm = round(60 * (len(bds) / bpm), 2)
    print(f"{bpm:.2f}")

    if SAVE:
        fdir, fname = os.path.split(sys.argv[1])
        bdir = os.path.join(fdir, ".beats")
        try:
            os.mkdir(fsenc(bdir))
        except:
            pass

        fp = os.path.join(bdir, fname) + ".txt"
        with open(fsenc(fp), "wb") as f:
            txt = "\n".join([f"{x:.2f}" for x in beats])
            f.write(txt.encode("utf-8"))


def main():
    with tempfile.NamedTemporaryFile(suffix=".pcm", delete=False) as f:
        f.write(b"h")
        tf = f.name

    try:
        det(tf)
    except:
        pass  # mute
    finally:
        os.unlink(tf)


if __name__ == "__main__":
    main()

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


def det(tf):
    # fmt: off
    sp.check_call([
        b"ffmpeg",
        b"-nostdin",
        b"-hide_banner",
        b"-v", b"fatal",
        b"-ss", b"13",
        b"-y", b"-i", fsenc(sys.argv[1]),
        b"-map", b"0:a:0",
        b"-ac", b"1",
        b"-ar", b"22050",
        b"-t", b"300",
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
        bpm = float(cl[-1]["timestamp"] - cl[1]["timestamp"])
        bpm = round(60 * ((len(cl) - 1) / bpm), 2)
        print(f"{bpm:.2f}")


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

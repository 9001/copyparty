#!/usr/bin/env python

import re
import sys
import json
import time
import base64
import hashlib
import subprocess as sp

try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p.encode("utf-8")


"""
dep: ffmpeg
"""


def det():
    # fmt: off
    cmd = [
        b"ffmpeg",
        b"-nostdin",
        b"-hide_banner",
        b"-v", b"fatal",
        b"-i", fsenc(sys.argv[1]),
        b"-f", b"framemd5",
        b"-"
    ]
    # fmt: on

    p = sp.Popen(cmd, stdout=sp.PIPE)
    # ps = io.TextIOWrapper(p.stdout, encoding="utf-8")
    ps = p.stdout

    chans = {}
    for ln in ps:
        if ln.startswith(b"#stream#"):
            break

        m = re.match(r"^#media_type ([0-9]): ([a-zA-Z])", ln.decode("utf-8"))
        if m:
            chans[m.group(1)] = m.group(2)

    hashers = [hashlib.sha512(), hashlib.sha512()]
    for ln in ps:
        n = int(ln[:1])
        v = ln.rsplit(b",", 1)[-1].strip()
        hashers[n].update(v)

    r = {}
    for k, v in chans.items():
        dg = hashers[int(k)].digest()[:12]
        dg = base64.urlsafe_b64encode(dg).decode("ascii")
        r[v[0].lower() + "hash"] = dg

    print(json.dumps(r, indent=4))


def main():
    try:
        det()
    except:
        pass  # mute


if __name__ == "__main__":
    main()

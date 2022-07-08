#!/usr/bin/env python

import json
import os
import subprocess as sp
import sys
import time

try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p.encode("utf-8")


_ = r"""
first checks the tag "vidchk" which must be "ok" to continue,
then uploads all files to some cloud storage (RCLONE_REMOTE)
and DELETES THE ORIGINAL FILES if rclone returns 0 ("success")

deps:
  rclone

usage:
  -mtp x2=t43200,ay,p2,bin/mtag/rclone-upload.py

explained:
t43200: timeout 12h
    ay: only process files which contain audio (including video with audio)
    p2: set priority 2 (after vidchk's suggested priority of 1),
          so the output of vidchk will be passed in here

complete usage example as vflags along with vidchk:
  -vsrv/vidchk:vidchk:r:rw,ed:c,e2dsa,e2ts,mtp=vidchk=t600,p,bin/mtag/vidchk.py:c,mtp=rupload=t43200,ay,p2,bin/mtag/rclone-upload.py:c,mte=+vidchk,rupload

setup: see https://rclone.org/drive/

if you wanna use this script standalone / separately from copyparty,
either set CONDITIONAL_UPLOAD False or provide the following stdin:
  {"vidchk":"ok"}
"""


RCLONE_REMOTE = "notmybox"
CONDITIONAL_UPLOAD = True


def main():
    if CONDITIONAL_UPLOAD:
        fp = sys.argv[1]
        zb = sys.stdin.buffer.read()
        zs = zb.decode("utf-8", "replace")
        md = json.loads(zs)

        chk = md.get("vidchk", None)
        if chk != "ok":
            print(f"vidchk={chk}", file=sys.stderr)
            sys.exit(1)

    dst = f"{RCLONE_REMOTE}:".encode("utf-8")
    cmd = [b"rclone", b"copy", b"--", fsenc(fp), dst]

    t0 = time.time()
    try:
        sp.check_call(cmd)
    except:
        print("rclone failed", file=sys.stderr)
        sys.exit(1)

    print(f"{time.time() - t0:.1f} sec")
    os.unlink(fsenc(fp))


if __name__ == "__main__":
    main()

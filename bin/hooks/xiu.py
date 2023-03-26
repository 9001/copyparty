#!/usr/bin/env python3

import json
import sys


_ = r"""
this hook prints absolute filepaths + total size

use this with --xiu, which makes copyparty buffer
uploads until server is idle, providing file infos
on stdin (filepaths or json)

example usage as global config:
    --xiu i1,j,bin/hooks/xiu.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xiu=i1,j,bin/hooks/xiu.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on batches of uploads with the params listed below)

parameters explained,
    xiu = execute after uploads...
    i1  = ...after volume has been idle for 1sec
    j   = provide json instead of filepath list

note the "f" (fork) flag is not set, so this xiu
will block other xiu hooks while it's running
"""


def main():
    zb = sys.stdin.buffer.read()
    zs = zb.decode("utf-8", "replace")
    inf = json.loads(zs)

    total_sz = 0
    for upload in inf:
        sz = upload["sz"]
        total_sz += sz
        print("{:9} {}".format(sz, upload["ap"]))

    print("{} files, {} bytes total".format(len(inf), total_sz))


if __name__ == "__main__":
    main()

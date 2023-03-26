#!/usr/bin/env python3

import hashlib
import json
import sys
from datetime import datetime


_ = r"""
this hook will produce a single sha512 file which
covers all recent uploads (plus metadata comments)

use this with --xiu, which makes copyparty buffer
uploads until server is idle, providing file infos
on stdin (filepaths or json)

example usage as global config:
    --xiu i5,j,bin/hooks/xiu-sha.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xiu=i5,j,bin/hooks/xiu-sha.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on batches of uploads with the params listed below)

parameters explained,
    xiu = execute after uploads...
    i5  = ...after volume has been idle for 5sec
    j   = provide json instead of filepath list

note the "f" (fork) flag is not set, so this xiu
will block other xiu hooks while it's running
"""


try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p


def humantime(ts):
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def find_files_root(inf):
    di = 9000
    for f1, f2 in zip(inf, inf[1:]):
        p1 = f1["ap"].replace("\\", "/").rsplit("/", 1)[0]
        p2 = f2["ap"].replace("\\", "/").rsplit("/", 1)[0]
        di = min(len(p1), len(p2), di)
        di = next((i for i in range(di) if p1[i] != p2[i]), di)

    return di + 1


def find_vol_root(inf):
    return len(inf[0]["ap"][: -len(inf[0]["vp"])])


def main():
    zb = sys.stdin.buffer.read()
    zs = zb.decode("utf-8", "replace")
    inf = json.loads(zs)

    # root directory (where to put the sha512 file);
    # di = find_files_root(inf)  # next to the file closest to volume root
    di = find_vol_root(inf)  # top of the entire volume

    ret = []
    total_sz = 0
    for md in inf:
        ap = md["ap"]
        rp = ap[di:]
        total_sz += md["sz"]
        fsize = "{:,}".format(md["sz"])
        mtime = humantime(md["mt"])
        up_ts = humantime(md["at"])

        h = hashlib.sha512()
        with open(fsenc(md["ap"]), "rb", 512 * 1024) as f:
            while True:
                buf = f.read(512 * 1024)
                if not buf:
                    break

                h.update(buf)

        cksum = h.hexdigest()
        meta = " | ".join([md["wark"], up_ts, mtime, fsize, md["ip"]])
        ret.append("# {}\n{} *{}".format(meta, cksum, rp))

    ret.append("# {} files, {} bytes total".format(len(inf), total_sz))
    ret.append("")
    ftime = datetime.utcnow().strftime("%Y-%m%d-%H%M%S.%f")
    fp = "{}xfer-{}.sha512".format(inf[0]["ap"][:di], ftime)
    with open(fsenc(fp), "wb") as f:
        f.write("\n".join(ret).encode("utf-8", "replace"))

    print("wrote checksums to {}".format(fp))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
unforget.py: rebuild db from logfiles
2022-09-07, v0.1, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/unforget.py

only makes sense if running copyparty with --no-forget
(e.g. immediately shifting uploads to other storage)

usage:
  xz -d < log | ./unforget.py .hist/up2k.db

"""

import re
import sys
import json
import base64
import sqlite3
import argparse


FS_ENCODING = sys.getfilesystemencoding()


class APF(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


mem_cur = sqlite3.connect(":memory:").cursor()
mem_cur.execute(r"create table a (b text)")


def s3enc(rd: str, fn: str) -> tuple[str, str]:
    ret: list[str] = []
    for v in [rd, fn]:
        try:
            mem_cur.execute("select * from a where b = ?", (v,))
            ret.append(v)
        except:
            wtf8 = v.encode(FS_ENCODING, "surrogateescape")
            ret.append("//" + base64.urlsafe_b64encode(wtf8).decode("ascii"))

    return ret[0], ret[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ar = ap.parse_args()

    db = sqlite3.connect(ar.db).cursor()
    ptn_times = re.compile(r"no more chunks, setting times \(([0-9]+)")
    at = 0
    ctr = 0

    for ln in [x.decode("utf-8", "replace").rstrip() for x in sys.stdin.buffer]:
        if "no more chunks, setting times (" in ln:
            m = ptn_times.search(ln)
            if m:
                at = int(m.group(1))

        if '"hash": []' in ln:
            try:
                ofs = ln.find("{")
                j = json.loads(ln[ofs:])
            except:
                continue

            w = j["wark"]
            if db.execute("select w from up where w = ?", (w,)).fetchone():
                continue

            # PYTHONPATH=/home/ed/dev/copyparty/ python3 -m copyparty -e2dsa  -v foo:foo:rwmd,ed -aed:wark --no-forget
            # 05:34:43.845 127.0.0.1 42496       no more chunks, setting times (1662528883, 1658001882)
            # 05:34:43.863 127.0.0.1 42496       {"name": "f\"2", "purl": "/foo/bar/baz/", "size": 1674, "lmod": 1658001882, "sprs": true, "hash": [], "wark": "LKIWpp2jEAh9dH3fu-DobuURFGEKlODXDGTpZ1otMhUg"}
            # |                      w                       |     mt     |  sz  |   rd    | fn  |    ip     |     at     |
            # | LKIWpp2jEAh9dH3fu-DobuURFGEKlODXDGTpZ1otMhUg | 1658001882 | 1674 | bar/baz | f"2 | 127.0.0.1 | 1662528883 |

            rd, fn = s3enc(j["purl"].strip("/"), j["name"])
            ip = ln.split(" ")[1].split("m")[-1]

            q = "insert into up values (?,?,?,?,?,?,?)"
            v = (w, int(j["lmod"]), int(j["size"]), rd, fn, ip, at)
            db.execute(q, v)
            ctr += 1
            if ctr % 1024 == 1023:
                print(f"{ctr} commit...")
                db.connection.commit()

    if ctr:
        db.connection.commit()

    print(f"unforgot {ctr} files")


if __name__ == "__main__":
    main()

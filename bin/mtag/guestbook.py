#!/usr/bin/env python3

"""
store messages from users in an sqlite database
which can be read from another mtp for example

takes input from application/x-www-form-urlencoded POSTs,
for example using the message/pager function on the website

example copyparty config to use this:
  --urlform save,get -vsrv/hello:hello:w:c,e2ts,mtp=xgb=ebin,t10,ad,p,bin/mtag/guestbook.py:mte=+xgb

explained:
  for realpath srv/hello (served at /hello),write-only for eveyrone,
  enable file analysis on upload (e2ts),
  use mtp plugin "bin/mtag/guestbook.py" to provide metadata tag "xgb",
  do this on all uploads with the file extension "bin",
  t300 = 300 seconds timeout for each dwonload,
  ad = parse file regardless if FFmpeg thinks it is audio or not
  p = request upload info as json on stdin
  mte=+xgb enabled indexing of that tag for this volume

PS: this requires e2ts to be functional,
  meaning you need to do at least one of these:
   * apt install ffmpeg
   * pip3 install mutagen
"""


import json
import os
import sqlite3
import sys
from urllib.parse import unquote_to_bytes as unquote


# set 0 to allow infinite msgs from one IP,
# other values delete older messages to make space,
# so 1 only keeps latest msg
NUM_MSGS_TO_KEEP = 1


def main():
    fp = os.path.abspath(sys.argv[1])
    fdir = os.path.dirname(fp)
    fname = os.path.basename(fp)
    if not fname.startswith("put-") or not fname.endswith(".bin"):
        raise Exception("not a post file")

    zb = sys.stdin.buffer.read()
    zs = zb.decode("utf-8", "replace")
    md = json.loads(zs)

    buf = b""
    with open(fp, "rb") as f:
        while True:
            b = f.read(4096)
            buf += b
            if len(buf) > 4096:
                raise Exception("too big")

            if not b:
                break

    if not buf:
        raise Exception("file is empty")

    buf = unquote(buf.replace(b"+", b" "))
    txt = buf.decode("utf-8")

    if not txt.startswith("msg="):
        raise Exception("does not start with msg=")

    ip = md["up_ip"]
    ts = md["up_at"]
    txt = txt[4:]

    # can put the database inside `fdir` if you'd like,
    # by default it saves to PWD:
    # os.chdir(fdir)

    db = sqlite3.connect("guestbook.db3")
    try:
        db.execute("select 1 from gb").fetchone()
    except:
        with db:
            db.execute("create table gb (ip text, ts real, msg text)")
            db.execute("create index gb_ip on gb(ip)")

    with db:
        if NUM_MSGS_TO_KEEP == 1:
            t = "delete from gb where ip = ?"
            db.execute(t, (ip,))

        t = "insert into gb values (?,?,?)"
        db.execute(t, (ip, ts, txt))

        if NUM_MSGS_TO_KEEP > 1:
            t = "select ts from gb where ip = ? order by ts desc"
            hits = db.execute(t, (ip,)).fetchall()

            if len(hits) > NUM_MSGS_TO_KEEP:
                lim = hits[NUM_MSGS_TO_KEEP][0]
                t = "delete from gb where ip = ? and ts <= ?"
                db.execute(t, (ip, lim))

    print(txt)


if __name__ == "__main__":
    main()

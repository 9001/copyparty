#!/usr/bin/env python3

"""
fetch latest msg from guestbook and return as tag

example copyparty config to use this:
  --urlform save,get -vsrv/hello:hello:w:c,e2ts,mtp=guestbook=t10,ad,p,bin/mtag/guestbook-read.py:mte=+guestbook

explained:
  for realpath srv/hello (served at /hello), write-only for eveyrone,
  enable file analysis on upload (e2ts),
  use mtp plugin "bin/mtag/guestbook-read.py" to provide metadata tag "guestbook",
  do this on all uploads regardless of extension,
  t10 = 10 seconds timeout for each dwonload,
  ad = parse file regardless if FFmpeg thinks it is audio or not
  p = request upload info as json on stdin (need ip)
  mte=+guestbook enabled indexing of that tag for this volume

PS: this requires e2ts to be functional,
  meaning you need to do at least one of these:
   * apt install ffmpeg
   * pip3 install mutagen
"""


import json
import os
import sqlite3
import sys


# set 0 to allow infinite msgs from one IP,
# other values delete older messages to make space,
# so 1 only keeps latest msg
NUM_MSGS_TO_KEEP = 1


def main():
    fp = os.path.abspath(sys.argv[1])
    fdir = os.path.dirname(fp)

    zb = sys.stdin.buffer.read()
    zs = zb.decode("utf-8", "replace")
    md = json.loads(zs)

    ip = md["up_ip"]

    # can put the database inside `fdir` if you'd like,
    # by default it saves to PWD:
    # os.chdir(fdir)

    db = sqlite3.connect("guestbook.db3")
    with db:
        t = "select msg from gb where ip = ? order by ts desc"
        r = db.execute(t, (ip,)).fetchone()
        if r:
            print(r[0])


if __name__ == "__main__":
    main()

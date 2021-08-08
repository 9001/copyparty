#!/usr/bin/env python

import re
import sys
import gzip
import json
from datetime import datetime

"""
youtube initial player response

example usage:
  -v srv/playerdata:playerdata:w
       :c,e2tsr:c,e2dsa
       :c,mtp=yt-id,yt-title,yt-author,yt-channel,yt-views,yt-private,yt-expires=bin/mtag/yt-ipr.py
       :c,mte=yt-id,yt-title,yt-author,yt-channel,yt-views,yt-private,yt-expires

see res/yt-ipr.user.js for the example userscript to go with this
"""


def main():
    try:
        with gzip.open(sys.argv[1], "rt", encoding="utf-8", errors="replace") as f:
            txt = f.read()
    except:
        with open(sys.argv[1], "r", encoding="utf-8", errors="replace") as f:
            txt = f.read()

    txt = "{" + txt.split("{", 1)[1]

    try:
        obj = json.loads(txt)
    except json.decoder.JSONDecodeError as ex:
        obj = json.loads(txt[: ex.pos])

    # print(json.dumps(obj, indent=2))

    vd = obj["videoDetails"]
    sd = obj["streamingData"]

    et = sd["adaptiveFormats"][0]["url"]
    et = re.search(r"[?&]expire=([0-9]+)", et).group(1)
    et = datetime.utcfromtimestamp(int(et))
    et = et.strftime("%Y-%m-%d, %H:%M")

    r = {
        "yt-id": vd["videoId"],
        "yt-title": vd["title"],
        "yt-author": vd["author"],
        "yt-channel": vd["channelId"],
        "yt-views": vd["viewCount"],
        "yt-private": vd["isPrivate"],
        # "yt-expires": sd["expiresInSeconds"],
        "yt-expires": et,
    }
    print(json.dumps(r))


if __name__ == "__main__":
    main()

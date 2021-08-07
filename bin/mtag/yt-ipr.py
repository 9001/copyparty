#!/usr/bin/env python

import re
import sys
import json
from datetime import datetime

"""
youtube initial player response

example usage:
  -v srv/playerdata:playerdata:w
       :c,e2tsr:c,e2dsa
       :c,mtp=yt-id,yt-title,yt-author,yt-channel,yt-views,yt-private,yt-expires=bin/mtag/yt-ipr.py
       :c,mte=yt-id,yt-title,yt-author,yt-channel,yt-views,yt-private,yt-expires

quick userscript to push them across:
  console.log('a');
  setTimeout(function() {
    for (var scr of document.querySelectorAll('script[nonce]'))
      if (scr.innerHTML.indexOf('manifest.googlevideo.com/api/manifest')>0)
        fetch('https://127.0.0.1:3923/playerdata', {method:"PUT", body: scr.innerHTML});
  }, 10*1000);

"""


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as f:
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

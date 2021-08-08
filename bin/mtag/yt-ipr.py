#!/usr/bin/env python

import re
import os
import sys
import gzip
import json
import base64
import string
import urllib.request
from datetime import datetime

"""
youtube initial player response

it's probably best to use this through a config file; see res/yt-ipr.conf

but if you want to use plain arguments instead then:
  -v srv/ytm:ytm:w:rw,ed
       :c,e2ts:c,e2dsa
       :c,sz=16k-1m:c,maxn=10,300:c,rotf=%Y-%m/%d-%H
       :c,mtp=yt-id,yt-title,yt-author,yt-channel,yt-views,yt-private,yt-manifest,yt-expires=bin/mtag/yt-ipr.py
       :c,mte=yt-id,yt-title,yt-author,yt-channel,yt-views,yt-private,yt-manifest,yt-expires

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
        pd = json.loads(txt)
    except json.decoder.JSONDecodeError as ex:
        pd = json.loads(txt[: ex.pos])

    # print(json.dumps(pd, indent=2))

    if "videoDetails" in pd:
        parse_youtube(pd)
    else:
        parse_freg(pd)


def get_expiration(url):
    et = re.search(r"[?&]expire=([0-9]+)", url).group(1)
    et = datetime.utcfromtimestamp(int(et))
    return et.strftime("%Y-%m-%d, %H:%M")


def parse_youtube(pd):
    vd = pd["videoDetails"]
    sd = pd["streamingData"]

    et = sd["adaptiveFormats"][0]["url"]
    et = get_expiration(et)

    mf = []
    if "dashManifestUrl" in sd:
        mf.append("dash")
    if "hlsManifestUrl" in sd:
        mf.append("hls")

    r = {
        "yt-id": vd["videoId"],
        "yt-title": vd["title"],
        "yt-author": vd["author"],
        "yt-channel": vd["channelId"],
        "yt-views": vd["viewCount"],
        "yt-private": vd["isPrivate"],
        # "yt-expires": sd["expiresInSeconds"],
        "yt-manifest": ",".join(mf),
        "yt-expires": et,
    }
    print(json.dumps(r))

    freg_conv(pd)


def parse_freg(pd):
    md = pd["metadata"]
    r = {
        "yt-id": md["id"],
        "yt-title": md["title"],
        "yt-author": md["channelName"],
        "yt-channel": md["channelURL"].strip("/").split("/")[-1],
        "yt-expires": get_expiration(list(pd["video"].values())[0]),
    }
    print(json.dumps(r))


def freg_conv(pd):
    # based on getURLs.js v1.5 (2021-08-07)
    # fmt: off
    priority = {
        "video": [
            337, 315, 266, 138,  # 2160p60
            313, 336,  # 2160p
            308,  # 1440p60
            271, 264,  # 1440p
            335, 303, 299,  # 1080p60
            248, 169, 137,  # 1080p
            334, 302, 298,  # 720p60
            247, 136  # 720p
        ],
        "audio": [
            251, 141, 171, 140, 250, 249, 139
        ]
    }

    vid_id = pd["videoDetails"]["videoId"]
    chan_id = pd["videoDetails"]["channelId"]

    try:
        thumb_url = pd["microformat"]["playerMicroformatRenderer"]["thumbnail"]["thumbnails"][0]["url"]
        start_ts = pd["microformat"]["playerMicroformatRenderer"]["liveBroadcastDetails"]["startTimestamp"]
    except:
        thumb_url = f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"
        start_ts = ""

    # fmt: on

    metadata = {
        "title": pd["videoDetails"]["title"],
        "id": vid_id,
        "channelName": pd["videoDetails"]["author"],
        "channelURL": "https://www.youtube.com/channel/" + chan_id,
        "description": pd["videoDetails"]["shortDescription"],
        "thumbnailUrl": thumb_url,
        "startTimestamp": start_ts,
    }

    if [x for x in vid_id if x not in string.ascii_letters + string.digits + "_-"]:
        print(f"malicious json", file=sys.stderr)
        return

    basepath = os.path.dirname(sys.argv[1])

    thumb_fn = f"{basepath}/{vid_id}.jpg"
    tmp_fn = f"{thumb_fn}.{os.getpid()}"
    if not os.path.exists(thumb_fn) and (
        thumb_url.startswith("https://img.youtube.com/vi/")
        or thumb_url.startswith("https://i.ytimg.com/vi/")
    ):
        try:
            with urllib.request.urlopen(thumb_url) as fi:
                with open(tmp_fn, "wb") as fo:
                    fo.write(fi.read())

            os.rename(tmp_fn, thumb_fn)
        except:
            if os.path.exists(tmp_fn):
                os.unlink(tmp_fn)

    try:
        with open(thumb_fn, "rb") as f:
            thumb = base64.b64encode(f.read()).decode("ascii")
    except:
        thumb = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k="

    metadata["thumbnail"] = "data:image/jpeg;base64," + thumb

    ret = {
        "metadata": metadata,
        "version": "1.5",
        "createTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    for stream, itags in priority.items():
        for itag in itags:
            url = None
            for afmt in pd["streamingData"]["adaptiveFormats"]:
                if itag == afmt["itag"]:
                    url = afmt["url"]
                    break

            if url:
                ret[stream] = {itag: url}
                break

    fn = f"{basepath}/{vid_id}.urls.json"
    with open(fn, "w", encoding="utf-8", errors="replace") as f:
        f.write(json.dumps(ret, indent=4))


if __name__ == "__main__":
    try:
        main()
    except:
        # raise
        pass

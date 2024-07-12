#!/usr/bin/env python3

import sys
import json
import requests
from copyparty.util import humansize, quotep


_ = r"""
announces a new upload on discord

example usage as global config:
    --xau f,t5,j,bin/hooks/discord-announce.py

parameters explained,
    xau = execute after upload
    f  = fork; don't delay other hooks while this is running
    t5 = timeout if it's still running after 5 sec
    j  = this hook needs upload information as json (not just the filename)

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xau=f,t5,j,bin/hooks/discord-announce.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all uploads with the params explained above)

example usage as a volflag in a copyparty config file:
    [/inc]
      srv/inc
      accs:
        r: *
        rw: ed
      flags:
        xau: f,t5,j,bin/hooks/discord-announce.py

replace "xau" with "xbu" to announce Before upload starts instead of After completion

# how to discord:
first create the webhook url; https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks
then use this to design your message: https://discohook.org/
"""


def main():
    WEBHOOK = "https://discord.com/api/webhooks/1234/base64"
    WEBHOOK = "https://discord.com/api/webhooks/1066830390280597718/M1TDD110hQA-meRLMRhdurych8iyG35LDoI1YhzbrjGP--BXNZodZFczNVwK4Ce7Yme5"

    # read info from copyparty
    inf = json.loads(sys.argv[1])
    vpath = inf["vp"]
    filename = vpath.split("/")[-1]
    url = f"https://{inf['host']}/{quotep(vpath)}"

    # compose the message to discord
    j = {
        "title": filename,
        "url": url,
        "description": url.rsplit("/", 1)[0],
        "color": 0x449900,
        "fields": [
            {"name": "Size", "value": humansize(inf["sz"])},
            {"name": "User", "value": inf["user"]},
            {"name": "IP", "value": inf["ip"]},
        ],
    }

    for v in j["fields"]:
        v["inline"] = True

    r = requests.post(WEBHOOK, json={"embeds": [j]})
    print(f"discord: {r}\n", end="")


if __name__ == "__main__":
    main()

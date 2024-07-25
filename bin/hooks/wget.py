#!/usr/bin/env python3

import os
import sys
import json
import subprocess as sp


_ = r"""
use copyparty as a file downloader by POSTing URLs as
application/x-www-form-urlencoded (for example using the
📟 message-to-server-log in the web-ui)

example usage as global config:
    --xm aw,f,j,t3600,bin/hooks/wget.py

parameters explained,
    xm = execute on message-to-server-log
    aw = only users with write-access can use this
    f = fork; don't delay other hooks while this is running
    j = provide message information as json (not just the text)
    c3 = mute all output
    t3600 = timeout and abort download after 1 hour

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xm=aw,f,j,t3600,bin/hooks/wget.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all messages with the params explained above)

example usage as a volflag in a copyparty config file:
    [/inc]
      srv/inc
      accs:
        r: *
        rw: ed
      flags:
        xm: aw,f,j,t3600,bin/hooks/wget.py

the volflag examples only kicks in if you send the message
while you're in the /inc folder (or any folder below there)
"""


def main():
    inf = json.loads(sys.argv[1])
    url = inf["txt"]
    if "://" not in url:
        url = "https://" + url

    proto = url.split("://")[0].lower()
    if proto not in ("http", "https", "ftp", "ftps"):
        raise Exception("bad proto {}".format(proto))

    os.chdir(inf["ap"])

    name = url.split("?")[0].split("/")[-1]
    tfn = "-- DOWNLOADING " + name
    print(f"{tfn}\n", end="")
    open(tfn, "wb").close()

    cmd = ["wget", "--trust-server-names", "-nv", "--", url]

    try:
        sp.check_call(cmd)
    except:
        t = "-- FAILED TO DONWLOAD " + name
        print(f"{t}\n", end="")
        open(t, "wb").close()

    os.unlink(tfn)


if __name__ == "__main__":
    main()

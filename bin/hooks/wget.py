#!/usr/bin/env python3

import os
import sys
import json
import subprocess as sp
from urllib.parse import urlparse
from shlex import quote

_ = r"""
use copyparty as a file downloader by POSTing URLs as
application/x-www-form-urlencoded (for example using the
message/pager function on the website)

example usage as global config:
    --xm f,j,t3600,bin/hooks/wget.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xm=f,j,t3600,bin/hooks/wget.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all messages with the params listed below)

parameters explained,
    xm = execute on message-to-server-log
    f = fork so it doesn't block uploads
    j = provide message information as json; not just the text
    c3 = mute all output
    t3600 = timeout and kill download after 1 hour
"""

def validate_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
        raise ValueError("Invalid URL")
    return url

def main():
    inf = json.loads(sys.argv[1])
    url = inf["txt"]
    if "://" not in url:
        url = "https://" + url

    # Validate the URL
    try:
        url = validate_url(url)
    except ValueError as e:
        print(str(e))
        return

    os.chdir(inf["ap"])

    name = url.split("?")[0].split("/")[-1]
    tfn = "-- DOWNLOADING " + name
    print(f"{tfn}\n", end="")
    open(tfn, "wb").close()

    # Quote the URL to prevent shell injection
    quoted_url = quote(url)
    cmd = ["wget", "--trust-server-names", "-nv", "--", quoted_url]

    try:
        sp.check_call(cmd)
    except:
        t = "-- FAILED TO DOWNLOAD " + name
        print(f"{t}\n", end="")
        open(t, "wb").close()

    os.unlink(tfn)


if __name__ == "__main__":
    main()

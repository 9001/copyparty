#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import json
import subprocess as sp


_ = r"""
start downloading a torrent by POSTing a magnet URL to copyparty,
for example using 📟 (message-to-server-log) in the web-ui

example usage as global config (not a good idea):
    python copyparty-sfx.py --xm f,j,t60,bin/hooks/qbittorrent-magnet.py

parameters explained,
    xm = execute on message (📟)
    f = fork; don't delay other hooks while this is running
    j = provide message information as json (not just the text)
    t60 = abort if qbittorrent has to think about it for more than 1 min

example usage as a volflag (per-volume config, much better):
    -v srv/qb:qb:A,ed:c,xm=f,j,t60,bin/hooks/qbittorrent-magnet.py
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/qb as volume /qb with Admin for user 'ed',
     running this plugin on all messages with the params explained above)

example usage as a volflag in a copyparty config file:
    [/qb]
      srv/qb
      accs:
        A: ed
      flags:
        xm: f,j,t60,bin/hooks/qbittorrent-magnet.py

the volflag examples only kicks in if you send the torrent magnet
while you're in the /qb folder (or any folder below there)
"""


# list of usernames to allow
ALLOWLIST = [ "ed", "morpheus" ]


def main():
    inf = json.loads(sys.argv[1])
    url = inf["txt"]
    if not url.lower().startswith("magnet:?"):
        # not a magnet, abort
        return

    if inf["user"] not in ALLOWLIST:
        print("🧲 denied for user", inf["user"])
        return

    # might as well run the command inside the filesystem folder
    # which matches the URL that the magnet message was sent to
    os.chdir(inf["ap"])

    # the command to add a new torrent, adjust if necessary
    cmd = ["qbittorrent-nox", url]

    # if copyparty and qbittorrent are running as different users
    # you may have to do something like the following
    # (assuming qbittorrent-nox* is nopasswd-allowed in sudoers):
    #
    # cmd = ["sudo", "-u", "qbitter", "qbittorrent-nox", url]

    print("🧲", cmd)

    try:
        sp.check_call(cmd)
    except:
        print("🧲 FAILED TO ADD", url)


if __name__ == "__main__":
    main()


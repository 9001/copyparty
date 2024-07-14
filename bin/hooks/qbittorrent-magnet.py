#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import json
import shutil
import subprocess as sp


_ = r"""
start downloading a torrent by POSTing a magnet URL to copyparty,
for example using 📟 (message-to-server-log) in the web-ui

by default it will download the torrent to the folder you were in
when you pasted the magnet into the message-to-server-log field

you can optionally specify another location by adding a whitespace
after the magnet URL followed by the name of the subfolder to DL into,
or for example "anime/airing" would download to /srv/media/anime/airing
because the keyword "anime" is in the DESTS config below

needs python3

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


# list of destination aliases to translate into full filesystem
# paths; takes effect if the first folder component in the
# custom download location matches anything in this dict
DESTS = {
    "iso": "/srv/pub/linux-isos",
    "anime": "/srv/media/anime",
}


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

    # is there is a custom download location in the url?
    dst = ""
    if " " in url:
        url, dst = url.split(" ", 1)

        # is the location in the predefined list of locations?
        parts = dst.replace("\\", "/").split("/")
        if parts[0] in DESTS:
            dst = os.path.join(DESTS[parts[0]], *(parts[1:]))

    else:
        # nope, so download to the current folder instead;
        # comment the dst line below to instead use the default
        # download location from your qbittorrent settings
        dst = inf["ap"]
        pass

    # archlinux has a -nox suffix for qbittorrent if headless
    # so check if we should be using that
    if shutil.which("qbittorrent-nox"):
        torrent_bin = "qbittorrent-nox"
    else:
        torrent_bin = "qbittorrent"

    # the command to add a new torrent, adjust if necessary
    cmd = [torrent_bin, url]
    if dst:
        cmd += ["--save-path=%s" % (dst,)]

    # if copyparty and qbittorrent are running as different users
    # you may have to do something like the following
    # (assuming qbittorrent* is nopasswd-allowed in sudoers):
    #
    # cmd = ["sudo", "-u", "qbitter"] + cmd

    print("🧲", cmd)

    try:
        sp.check_call(cmd)
    except:
        print("🧲 FAILED TO ADD", url)


if __name__ == "__main__":
    main()


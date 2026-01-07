#!/usr/bin/env python3

import os
import threading
import subprocess as sp


_ = r"""
use copyparty as a file downloader by POSTing URLs as
application/x-www-form-urlencoded (for example using the
📟 message-to-server-log in the web-ui)

this hook is a modified copy of wget.py, modified to
make it import-safe so it can be run with the 'I' flag,
which speeds up the startup time of the hook by 140x

example usage as global config:
    --xm aw,I,bin/hooks/wget-i.py

parameters explained,
    xm = execute on message-to-server-log
    aw = only users with write-access can use this
    I = import; do not fork / subprocess

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xm=aw,I,bin/hooks/wget.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
        xm: aw,I,bin/hooks/wget.py

the volflag examples only kicks in if you send the message
while you're in the /inc folder (or any folder below there)

IMPORTANT NOTE:
    because this hook uses the 'I' flag to run inside copyparty,
    many other flags will not work (f,j,c3,t3600 as seen in the
    original wget.py), and furthermore + more importantly we
    need to be EXCEPTIONALLY CAREFUL to avoid side-effects, so
    the os.chdir has been replaced with cwd=dirpath for example
"""


def do_stuff(inf):
    """
    worker function which is executed in another thread to
    avoid blocking copyparty while the download is running,
    since we cannot use the 'f,t3600' hook-flags with 'I'
    """

    # first things first; grab the logger-function which copyparty is letting us borrow
    log = inf["log"]

    url = inf["txt"]
    if url.startswith("upload-queue-empty;"):
        return

    if "://" not in url:
        url = "https://" + url

    proto = url.split("://")[0].lower()
    if proto not in ("http", "https", "ftp", "ftps"):
        raise Exception("bad proto {}".format(proto))

    dirpath = inf["ap"]

    name = url.split("?")[0].split("/")[-1]
    msg = "-- DOWNLOADING " + name
    log(msg)
    tfn = os.path.join(dirpath, msg)
    open(tfn, "wb").close()

    cmd = ["wget", "--trust-server-names", "-nv", "--", url]

    try:
        # two things to note here:
        # - cannot use the `c3` hook-flag with `I` so mute output with stdout=sp.DEVNULL instead;
        # - MUST NOT use os.chdir with 'I' so use cwd=dirpath instead 
        sp.check_call(cmd, cwd=dirpath, stdout=sp.DEVNULL)
    except:
        t = "-- FAILED TO DOWNLOAD " + name
        log(t, 3)  # 3=yellow=warning
        open(os.path.join(dirpath, t), "wb").close()
        raise  # have copyparty scream about the details in the log

    os.unlink(tfn)


def main(inf):
    threading.Thread(target=do_stuff, args=(inf,), daemon=True).start()

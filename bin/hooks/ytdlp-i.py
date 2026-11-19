#!/usr/bin/env python3

import os
import sys
import json
import subprocess as sp
import threading

from typing import Any


_ = r"""
yt-dlp hook for copyparty. Based on wget.py hook

use copyparty as a file downloader by POSTing URLs as
application/x-www-form-urlencoded (for example using the
📟 message-to-server-log in the web-ui)

this hook is a modified copy of wget.py, modified to
make use of yt-dlp + aria2 in an import-safe way, 
so it can be run with the 'I' flag, which speeds up 
the startup time of the hook by 140x

example usage as global config:
    --xm aw,I,bin/hooks/bin/hooks/ytdlp-i.py

parameters explained,
    xm = execute on message-to-server-log
    aw = only users with write-access can use this
    I = import; do not fork / subprocess

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xm=aw,I,bin/hooks/ytdlp-i.py
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
        xm: aw,I,bin/hooks/ytdlp-i.py

the volflag examples only kicks in if you send the message
while you're in the /inc folder (or any folder below there)

Dependencies:
    yt-dlp, aria2
    Example Dockerfile:
        FROM copyparty/ac

        ENV PYTHONUNBUFFERED=1
        RUN apk add --update --no-cache python3 py3-pip

        RUN python3 -m pip config set global.break-system-packages true
        RUN python3 -m pip install yt-dlp aria2

        RUN yt-dlp --version
        RUN aria2c --version

IMPORTANT NOTE:
    because this hook uses the 'I' flag to run inside copyparty,
    many other flags will not work (f,j,c3,t3600 as seen in the
    original wget.py), and furthermore + more importantly we
    need to be EXCEPTIONALLY CAREFUL to avoid side-effects, so
    the os.chdir has been replaced with cwd=dirpath for example
"""


def helper(ka: dict[str, Any]) -> dict[str, str]:
    logger = ka["log"]

    url = ka["txt"]
    if "://" not in url and url[:6] != "magnet":
        url = "https://" + url
        proto = url.split("://")[0].lower()
        if proto not in ("http", "https", "ftp", "ftps"):
            raise Exception(f"ytdlp_hook: Bad protocol {proto}")

    path = ka["ap"]

    name = url.split("?")[0].split("/")[-1] if '?' in url else "file"
    tfn = "ytdlp_hook: DOWNLOADING " + name
    logger(f"{tfn}\n", 2)
    open(tfn, "wb").close()

    cmd = [
        "yt-dlp",
        "-P",
        path,
        "-f",
        "bv*+ba/b",
        "--downloader",
        "aria2c",
        "--downloader-args",
        f"-j 16 -x 8 -s 16 -k 1M -d {path}",
        url,
    ]

    if url[:6] == "magnet":
        cmd = [cmd[4]] + [cmd[7]]

    else:
        if "." in (name[-3], name[-4]) and name.split(".")[-1] not in (
            "php",
            "htm",
            "aspx",
            "html",
        ):
            cmd += ["-o", name]

    logger(" ".join(cmd) + "\n", 2)

    try:
        result = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
        result.check_returncode()

        t = "ytdlp_hook: DOWNLOAD COMPLETED " + name
        logger(f"{t}\n", 2)
        stdout, stderr = result.stdout, result.stderr

    except sp.CalledProcessError as e:
        t = "ytdlp_hook: DOWNLOAD FAILED " + name
        logger(f"{t}\n", 4)
        open(t, "wb").close()
        logger(f"ytdlp_hook: Error: {e}", 4)
        stdout, stderr = e.stdout, e.stderr

    except sp.SubprocessError as e:
        t = "ytdlp_hook: DOWNLOAD FAILED " + name
        logger(f"{t}\n", 2)
        open(t, "wb").close()
        logger(f"ytdlp_hook: Error: {e}", 4)
        stdout, stderr = e.stdout, e.stderr

    finally:
        logger("ytdlp_hook: STDOUT:\n" + stdout, 1)
        logger("ytdlp_hook: STDERR:\n" + stderr, 1)
        os.unlink(tfn)


def main(inf: dict[str, Any]):
    threading.Thread(target=helper, name="ytdlp_hook", args=(inf,), daemon=True).start()

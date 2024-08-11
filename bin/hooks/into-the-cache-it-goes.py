#!/usr/bin/env python3

import sys
import json
import shutil
import platform
import subprocess as sp
from urllib.parse import quote


_ = r"""
try to avoid race conditions in caching proxies
(primarily cloudflare, but probably others too)
by means of the most obvious solution possible:

just as each file has finished uploading, use
the server's external URL to download the file
so that it ends up in the cache, warm and snug

this intentionally delays the upload response
as it waits for the file to finish downloading
before copyparty is allowed to return the URL

NOTE: you must edit this script before use,
  replacing https://example.com with your URL

NOTE: if the files are only accessible with a
  password and/or filekey, you must also add
  a cromulent password in the PASSWORD field

NOTE: needs either wget, curl, or "requests":
  python3 -m pip install --user -U requests


example usage as global config:
    --xau j,t10,bin/hooks/into-the-cache-it-goes.py

parameters explained,
    xau = execute after upload
    j   = this hook needs upload information as json (not just the filename)
    t10 = abort download and continue if it takes longer than 10sec

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xau=j,t10,bin/hooks/into-the-cache-it-goes.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all uploads with params explained above)

example usage as a volflag in a copyparty config file:
    [/inc]
      srv/inc
      accs:
        r: *
        rw: ed
      flags:
        xau: j,t10,bin/hooks/into-the-cache-it-goes.py
"""


# replace this with your site's external URL
# (including the :portnumber if necessary)
SITE_URL = "https://example.com"

# if downloading is protected by passwords or filekeys,
# specify a valid password between the quotes below:
PASSWORD = ""

# if file is larger than this, skip download
MAX_MEGABYTES = 8

# =============== END OF CONFIG ===============


WINDOWS = platform.system() == "Windows"


def main():
    fun = download_with_python
    if shutil.which("curl"):
        fun = download_with_curl
    elif shutil.which("wget"):
        fun = download_with_wget

    inf = json.loads(sys.argv[1])

    if inf["sz"] > 1024 * 1024 * MAX_MEGABYTES:
        print("[into-the-cache] file is too large; will not download")
        return

    file_url = "/"
    if inf["vp"]:
        file_url += inf["vp"] + "/"
    file_url += inf["ap"].replace("\\", "/").split("/")[-1]
    file_url = SITE_URL.rstrip("/") + quote(file_url, safe=b"/")

    print("[into-the-cache] %s(%s)" % (fun.__name__, file_url))
    fun(file_url, PASSWORD.strip())

    print("[into-the-cache] Download OK")


def download_with_curl(url, pw):
    cmd = ["curl"]

    if pw:
        cmd += ["-HPW:%s" % (pw,)]

    nah = sp.DEVNULL
    sp.check_call(cmd + [url], stdout=nah, stderr=nah)


def download_with_wget(url, pw):
    cmd = ["wget", "-O"]

    cmd += ["nul" if WINDOWS else "/dev/null"]

    if pw:
        cmd += ["--header=PW:%s" % (pw,)]

    nah = sp.DEVNULL
    sp.check_call(cmd + [url], stdout=nah, stderr=nah)


def download_with_python(url, pw):
    import requests

    headers = {}
    if pw:
        headers["PW"] = pw

    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        for _ in r.iter_content(chunk_size=1024 * 256):
            pass


if __name__ == "__main__":
    main()

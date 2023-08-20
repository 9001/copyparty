#!/usr/bin/env python3

"""
DEPRECATED -- replaced by event hooks;
https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/wget.py

---

use copyparty as a file downloader by POSTing URLs as
application/x-www-form-urlencoded (for example using the
message/pager function on the website)

example copyparty config to use this:
  --urlform save,get -vsrv/wget:wget:rwmd,ed:c,e2ts,mtp=title=ebin,t300,ad,bin/mtag/wget.py

explained:
  for realpath srv/wget (served at /wget) with read-write-modify-delete for ed,
  enable file analysis on upload (e2ts),
  use mtp plugin "bin/mtag/wget.py" to provide metadata tag "title",
  do this on all uploads with the file extension "bin",
  t300 = 300 seconds timeout for each dwonload,
  ad = parse file regardless if FFmpeg thinks it is audio or not

PS: this requires e2ts to be functional,
  meaning you need to do at least one of these:
   * apt install ffmpeg
   * pip3 install mutagen
"""


import os
import sys
import subprocess as sp
from urllib.parse import unquote_to_bytes as unquote


def main():
    fp = os.path.abspath(sys.argv[1])
    fdir = os.path.dirname(fp)
    fname = os.path.basename(fp)
    if not fname.startswith("put-") or not fname.endswith(".bin"):
        raise Exception("not a post file")

    buf = b""
    with open(fp, "rb") as f:
        while True:
            b = f.read(4096)
            buf += b
            if len(buf) > 4096:
                raise Exception("too big")

            if not b:
                break

    if not buf:
        raise Exception("file is empty")

    buf = unquote(buf.replace(b"+", b" "))
    url = buf.decode("utf-8")

    if not url.startswith("msg="):
        raise Exception("does not start with msg=")

    url = url[4:]
    if "://" not in url:
        url = "https://" + url

    proto = url.split("://")[0].lower()
    if proto not in ("http", "https", "ftp", "ftps"):
        raise Exception("bad proto {}".format(proto))

    os.chdir(fdir)

    name = url.split("?")[0].split("/")[-1]
    tfn = "-- DOWNLOADING " + name
    open(tfn, "wb").close()

    cmd = ["wget", "--trust-server-names", "--", url]

    try:
        sp.check_call(cmd)

        # OPTIONAL:
        #   on success, delete the .bin file which contains the URL
        os.unlink(fp)
    except:
        open("-- FAILED TO DONWLOAD " + name, "wb").close()

    os.unlink(tfn)
    print(url)


if __name__ == "__main__":
    main()

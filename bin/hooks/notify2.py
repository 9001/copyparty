#!/usr/bin/env python3

import json
import os
import sys
import subprocess as sp
from datetime import datetime
from plyer import notification


_ = r"""
same as notify.py but with additional info (uploader, ...)
and also supports --xm (notify on 📟 message)

example usages; either as global config (all volumes) or as volflag:
    --xm  f,j,bin/hooks/notify2.py
    --xau f,j,bin/hooks/notify2.py
    -v srv/inc:inc:c,xm=f,j,bin/hooks/notify2.py
    -v srv/inc:inc:c,xau=f,j,bin/hooks/notify2.py
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

parameters explained,
    xau = execute after upload
    f   = fork so it doesn't block uploads
    j   = provide json instead of filepath list
"""


try:
    from copyparty.util import humansize
except:

    def humansize(n):
        return n


def main():
    inf = json.loads(sys.argv[1])
    fp = inf["ap"]
    sz = humansize(inf["sz"])
    dp, fn = os.path.split(fp)
    mt = datetime.utcfromtimestamp(inf["mt"]).strftime("%Y-%m-%d %H:%M:%S")

    msg = f"{fn} ({sz})\n📁 {dp}"
    title = "File received"
    icon = "emblem-documents-symbolic" if sys.platform == "linux" else ""

    if inf.get("txt"):
        msg = inf["txt"]
        title = "Message received"
        icon = "mail-unread-symbolic" if sys.platform == "linux" else ""

    msg += f"\n👤 {inf['user']} ({inf['ip']})\n🕒 {mt}"

    if "com.termux" in sys.executable:
        sp.run(["termux-notification", "-t", title, "-c", msg])
        return

    notification.notify(
        title=title,
        message=msg,
        app_icon=icon,
        timeout=10,
    )


if __name__ == "__main__":
    main()

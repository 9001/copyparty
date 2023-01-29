#!/usr/bin/env python3

import os
import sys
import subprocess as sp
from plyer import notification


_ = r"""
show os notification on upload; works on windows, linux, macos, android

depdencies:
    windows: python3 -m pip install --user -U plyer
    linux:   python3 -m pip install --user -U plyer
    macos:   python3 -m pip install --user -U plyer pyobjus
    android: just termux and termux-api

example usages; either as global config (all volumes) or as volflag:
    --xau f,bin/hooks/notify.py
    -v srv/inc:inc:c,xau=f,bin/hooks/notify.py
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^

parameters explained,
    xau = execute after upload
    f   = fork so it doesn't block uploads
"""


def main():
    dp, fn = os.path.split(sys.argv[1])
    msg = "🏷️ {}\n📁 {}".format(fn, dp)
    title = "File received"

    if "com.termux" in sys.executable:
        sp.run(["termux-notification", "-t", title, "-c", msg])
        return

    icon = "emblem-documents-symbolic" if sys.platform == "linux" else ""
    notification.notify(
        title=title,
        message=msg,
        app_icon=icon,
        timeout=10,
    )


if __name__ == "__main__":
    main()

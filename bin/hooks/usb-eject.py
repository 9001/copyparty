#!/usr/bin/env python3

import os
import stat
import subprocess as sp
import sys
from urllib.parse import unquote_to_bytes as unquote


"""
if you've found yourself using copyparty to serve flashdrives on a LAN
and your only wish is that the web-UI had a button to unmount / safely
remove those flashdrives, then boy howdy are you in the right place :D

put usb-eject.js in the webroot (or somewhere else http-accessible)
then run copyparty with these args:

   -v /run/media/egon:/usb:A:c,hist=/tmp/junk
   --xm=c1,bin/hooks/usb-eject.py
   --js-browser=/usb-eject.js

which does the following respectively,

  * share all of /run/media/egon as /usb with admin for everyone
     and put the histpath somewhere it won't cause trouble
  * run the usb-eject hook with stdout redirect to the web-ui
  * add the complementary usb-eject.js to the browser

"""


MOUNT_BASE = b"/run/media/egon/"


def main():
    try:
        msg = sys.argv[1]
        if msg.startswith("upload-queue-empty;"):
            return
        label = msg.split(":usb-eject:")[1].split(":")[0]
        mp = MOUNT_BASE + unquote(label)
        # print("ejecting [%s]... " % (mp,), end="")
        mp = os.path.abspath(os.path.realpath(mp))
        st = os.lstat(mp)
        if not stat.S_ISDIR(st.st_mode) or not mp.startswith(MOUNT_BASE):
            raise Exception("not a regular directory")

        # if you're running copyparty as root (thx for the faith)
        # you'll need something like this to make dbus talkative
        cmd = b"sudo -u egon DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gio mount -e"

        # but if copyparty and the ui-session is running
        # as the same user (good) then this is plenty
        cmd = b"gio mount -e"

        cmd = cmd.split(b" ") + [mp]
        ret = sp.check_output(cmd).decode("utf-8", "replace")
        print(ret.strip() or (label + " can be safely unplugged"))

    except Exception as ex:
        print("unmount failed: %r" % (ex,))


if __name__ == "__main__":
    main()

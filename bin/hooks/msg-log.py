#!/usr/bin/env python
# coding: utf-8
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
from __future__ import print_function, unicode_literals

import json
import os
import sys
import time

try:
    from datetime import datetime, timezone
except:
    from datetime import datetime


_ = r"""
use copyparty as a dumb messaging server / guestbook thing;
accepts guestbook entries from 📟 (message-to-server-log) in the web-ui
initially contributed by @clach04 in https://github.com/9001/copyparty/issues/35 (thanks!)

example usage as global config:
    python copyparty-sfx.py --xm j,bin/hooks/msg-log.py

parameters explained,
    xm = execute on message (📟)
    j  = this hook needs message information as json (not just the message-text)

example usage as a volflag (per-volume config):
    python copyparty-sfx.py -v srv/log:log:r:c,xm=j,bin/hooks/msg-log.py
                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/log as volume /log, readable by everyone,
     running this plugin on all messages with the params explained above)

example usage as a volflag in a copyparty config file:
    [/log]
      srv/log
      accs:
        r: *
      flags:
        xm: j,bin/hooks/msg-log.py
"""


# output filename
FILENAME = os.environ.get("COPYPARTY_MESSAGE_FILENAME", "") or "README.md"

# set True to write in descending order (newest message at top of file);
# note that this becomes very slow/expensive as the file gets bigger
DESCENDING = True

# the message template; the following parameters are provided by copyparty and can be referenced below:
# 'ap' = absolute filesystem path where the message was posted
# 'vp' = virtual path (URL 'path') where the message was posted
# 'mt' = 'at' = unix-timestamp when the message was posted
# 'datetime' = ISO-8601 time when the message was posted
# 'sz' = message size in bytes
# 'host' = the server hostname which the user was accessing (URL 'host')
# 'user' = username (if logged in), otherwise '*'
# 'txt' = the message text itself
# (uncomment the print(msg_info) to see if additional information has been introduced by copyparty since this was written)
TEMPLATE = """
🕒 %(datetime)s, 👤 %(user)s @ %(ip)s
%(txt)s
"""


def write_ascending(filepath, msg_text):
    with open(filepath, "a", encoding="utf-8", errors="replace") as outfile:
        outfile.write(msg_text)


def write_descending(filepath, msg_text):
    lockpath = filepath + ".lock"
    got_it = False
    for _ in range(16):
        try:
            os.mkdir(lockpath)
            got_it = True
            break
        except:
            time.sleep(0.1)
            continue

    if not got_it:
        return sys.exit(1)

    try:
        oldpath = filepath + ".old"
        os.rename(filepath, oldpath)
        with open(oldpath, "r", encoding="utf-8", errors="replace") as infile, open(
            filepath, "w", encoding="utf-8", errors="replace"
        ) as outfile:
            outfile.write(msg_text)
            while True:
                buf = infile.read(4096)
                if not buf:
                    break
                outfile.write(buf)
    finally:
        try:
            os.unlink(oldpath)
        except:
            pass
        os.rmdir(lockpath)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    msg_info = json.loads(sys.argv[1])
    # print(msg_info)

    try:
        dt = datetime.fromtimestamp(msg_info["at"], timezone.utc)
    except:
        dt = datetime.utcfromtimestamp(msg_info["at"])

    msg_info["datetime"] = dt.strftime("%Y-%m-%d, %H:%M:%S")

    msg_text = TEMPLATE % msg_info

    filepath = os.path.join(msg_info["ap"], FILENAME)

    if DESCENDING and os.path.exists(filepath):
        write_descending(filepath, msg_text)
    else:
        write_ascending(filepath, msg_text)

    print(msg_text)


if __name__ == "__main__":
    main()

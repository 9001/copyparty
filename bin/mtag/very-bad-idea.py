#!/usr/bin/env python3

"""
use copyparty to xdg-open anything that is posted to it,
  and also xdg-open file uploads

HELLA DANGEROUS,
  GIVES RCE TO ANYONE WHO HAVE UPLOAD PERMISSIONS

example copyparty config to use this:
  --urlform save,get -v.::w:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,bin/mtag/very-bad-idea.py

recommended deps:
  apt install xdotool libnotify-bin

and you probably want `twitter-unmute.user.js` from the res folder


-----------------------------------------------------------------------
-- startup script:
-----------------------------------------------------------------------

#!/bin/bash
set -e

# create qr code
ip=$(ip r | awk '/^default/{print$(NF-2)}'); echo http://$ip:3923/ | qrencode -o - -s 4 >/dev/shm/cpp-qr.png
/usr/bin/feh -x /dev/shm/cpp-qr.png &

# reposition and make topmost (with janky raspbian support)
( sleep 0.5
xdotool search --name cpp-qr.png windowactivate --sync windowmove 1780 0
wmctrl -r :ACTIVE: -b toggle,above || true

ps aux | grep -E 'sleep[ ]7\.27' ||
while true; do
  w=$(xdotool getactivewindow)
  xdotool search --name cpp-qr.png windowactivate windowraise windowfocus
  xdotool windowactivate $w
  xdotool windowfocus $w
  sleep 7.27 || break
done &
xeyes  # distraction window to prevent ^w from closing the qr-code
) &

# bail if copyparty is already running
ps aux | grep -E '[3] copy[p]arty' && exit 0

# dumb chrome wrapper to allow autoplay
cat >/usr/local/bin/chromium-browser <<'EOF'
#!/bin/bash
set -e
/usr/bin/chromium-browser --autoplay-policy=no-user-gesture-required "$@"
EOF
chmod 755 /usr/local/bin/chromium-browser

# start the server  (note: replace `-v.::rw:` with `-v.::r:` to disallow retrieving uploaded stuff)
cd ~/Downloads; python3 copyparty-sfx.py --urlform save,get -v.::rw:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,very-bad-idea.py

"""


import os
import sys
import subprocess as sp
from urllib.parse import unquote_to_bytes as unquote


def main():
    fp = os.path.abspath(sys.argv[1])
    with open(fp, "rb") as f:
        txt = f.read(4096)

    if txt.startswith(b"msg="):
        open_post(txt)
    else:
        open_url(fp)


def open_post(txt):
    txt = unquote(txt.replace(b"+", b" ")).decode("utf-8")[4:]
    open_url(txt)


def open_url(txt):
    sp.call(["notify-send", "", txt])
    # sp.call(["wmctrl", "-c", ":ACTIVE:"])  # closes the active window correctly
    sp.call(["xdotool", "key", "ctrl+w"])  # closes the open tab correctly
    sp.call(["xdotool", "getactivewindow", "windowminimize"])
    # sp.call(["xdotool", "key", "ctrl+alt+d"])  # doesnt work at all
    sp.call(["killall", "vlc"])
    # sp.call(["xdotool", "keydown", "--delay", "100", "ctrl+alt+d"])
    # sp.call(["xdotool", "keyup", "ctrl+alt+d"])
    sp.call(["xdg-open", txt])


main()

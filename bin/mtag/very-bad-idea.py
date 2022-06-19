#!/usr/bin/env python3

"""
use copyparty as a chromecast replacement:
  * post a URL and it will open in the default browser
  * upload a file and it will open in the default application
  * the `key` command simulates keyboard input
  * the `x` command executes other xdotool commands
  * the `c` command executes arbitrary unix commands

the android app makes it a breeze to post pics and links:
  https://github.com/9001/party-up/releases
  (iOS devices have to rely on the web-UI)

goes without saying, but this is HELLA DANGEROUS,
  GIVES RCE TO ANYONE WHO HAVE UPLOAD PERMISSIONS

example copyparty config to use this:
  --urlform save,get -v.::w:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,bin/mtag/very-bad-idea.py

recommended deps:
  apt install xdotool libnotify-bin
  https://github.com/9001/copyparty/blob/hovudstraum/contrib/plugins/meadup.js

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

# start the server  (note: replace `-v.::rw:` with `-v.::w:` to disallow retrieving uploaded stuff)
cd ~/Downloads; python3 copyparty-sfx.py --urlform save,get -v.::rw:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,very-bad-idea.py

"""


import os
import sys
import time
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
    try:
        k, v = txt.split(" ", 1)
    except:
        open_url(txt)

    if k == "key":
        sp.call(["xdotool", "key"] + v.split(" "))
    elif k == "x":
        sp.call(["xdotool"] + v.split(" "))
    elif k == "c":
        env = os.environ.copy()
        while " " in v:
            v1, v2 = v.split(" ", 1)
            if "=" not in v1:
                break

            ek, ev = v1.split("=", 1)
            env[ek] = ev
            v = v2

        sp.call(v.split(" "), env=env)
    else:
        open_url(txt)


def open_url(txt):
    ext = txt.rsplit(".")[-1].lower()
    sp.call(["notify-send", "--", txt])
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        # sp.call(["wmctrl", "-c", ":ACTIVE:"])  # closes the active window correctly
        sp.call(["killall", "vlc"])
        sp.call(["killall", "mpv"])
        sp.call(["killall", "feh"])
        time.sleep(0.5)
        for _ in range(20):
            sp.call(["xdotool", "key", "ctrl+w"])  # closes the open tab correctly
    # else:
    #    sp.call(["xdotool", "getactivewindow", "windowminimize"])  # minimizes the focused windo

    # close any error messages:
    sp.call(["xdotool", "search", "--name", "Error", "windowclose"])
    # sp.call(["xdotool", "key", "ctrl+alt+d"])  # doesnt work at all
    # sp.call(["xdotool", "keydown", "--delay", "100", "ctrl+alt+d"])
    # sp.call(["xdotool", "keyup", "ctrl+alt+d"])
    sp.call(["xdg-open", txt])


main()

#!/usr/bin/env python3

"""
WARNING -- DANGEROUS PLUGIN --
  if someone is able to upload files to a copyparty which is
  running this plugin, they can execute malware on your machine
  so please keep this on a LAN and protect it with a password

use copyparty as a chromecast replacement:
  * post a URL and it will open in the default browser
  * upload a file and it will open in the default application
  * the `key` command simulates keyboard input
  * the `x` command executes other xdotool commands
  * the `c` command executes arbitrary unix commands

the android app makes it a breeze to post pics and links:
  https://github.com/9001/party-up/releases

iOS devices can use the web-UI or the shortcut instead:
  https://github.com/9001/copyparty#ios-shortcuts

example copyparty config to use this;
lets the user "kevin" with password "hunter2" use this plugin:
  -a kevin:hunter2 --urlform save,get -v.::w,kevin:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,kn,c0,bin/mtag/very-bad-idea.py

recommended deps:
  apt install xdotool libnotify-bin mpv
  python3 -m pip install --user -U streamlink yt-dlp
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

# start the server
# note 1: replace hunter2 with a better password to access the server
# note 2: replace `-v.::rw` with `-v.::w` to disallow retrieving uploaded stuff
cd ~/Downloads; python3 copyparty-sfx.py -a kevin:hunter2 --urlform save,get -v.::rw,kevin:c,e2d,e2t,mte=+a1:c,mtp=a1=ad,kn,very-bad-idea.py

"""


import os
import sys
import time
import shutil
import subprocess as sp
from urllib.parse import unquote_to_bytes as unquote
from urllib.parse import quote

have_mpv = shutil.which("mpv")
have_vlc = shutil.which("vlc")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "x":
        # invoked on commandline for testing;
        # python3 very-bad-idea.py x msg=https://youtu.be/dQw4w9WgXcQ
        txt = " ".join(sys.argv[2:])
        txt = quote(txt.replace(" ", "+"))
        return open_post(txt.encode("utf-8"))

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
        return open_url(txt)

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

    # mpv is probably smart enough to use streamlink automatically
    if try_mpv(txt):
        print("mpv got it")
        return

    # or maybe streamlink would be a good choice to open this
    if try_streamlink(txt):
        print("streamlink got it")
        return

    # nope,
    # close any error messages:
    sp.call(["xdotool", "search", "--name", "Error", "windowclose"])
    # sp.call(["xdotool", "key", "ctrl+alt+d"])  # doesnt work at all
    # sp.call(["xdotool", "keydown", "--delay", "100", "ctrl+alt+d"])
    # sp.call(["xdotool", "keyup", "ctrl+alt+d"])
    sp.call(["xdg-open", txt])


def try_mpv(url):
    t0 = time.time()
    try:
        print("trying mpv...")
        sp.check_call(["mpv", "--fs", url])
        return True
    except:
        # if it ran for 15 sec it probably succeeded and terminated
        t = time.time()
        return t - t0 > 15


def try_streamlink(url):
    t0 = time.time()
    try:
        import streamlink

        print("trying streamlink...")
        streamlink.Streamlink().resolve_url(url)

        if have_mpv:
            args = "-m streamlink -p mpv -a --fs"
        else:
            args = "-m streamlink"

        cmd = [sys.executable] + args.split() + [url, "best"]
        t0 = time.time()
        sp.check_call(cmd)
        return True
    except:
        # if it ran for 10 sec it probably succeeded and terminated
        t = time.time()
        return t - t0 > 10


main()

# ⇆🎉 copyparty

* http file sharing hub (py2/py3)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net

## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using IE6 or any other browser

* server runs on anything with `py2.7` or `py3.2+`
* *resumable* uploads need `firefox 12+` / `chrome 6+` / `safari 6+` / `IE 10+`
* code standard: `black`

## status

* [x] sanic multipart parser
* [x] load balancer (multiprocessing)
* [x] upload (plain multipart, ie6 support)
* [ ] upload (js, resumable, multithreaded)
* [x] download
* [x] browser
* [x] media player
* [ ] thumbnails
* [ ] download as zip
* [x] volumes
* [x] accounts

summary: it works


# dependencies

* `jinja2`
  * pulls in `markupsafe` as of v2.7; use jinja 2.6 on py3.2

optional, enables thumbnails:
* `Pillow` (requires py2.7 or py3.5+)


# install on android

install [Termux](https://termux.com/) (see [ocv.me/termux](https://ocv.me/termux/)) and then copy-paste this into Termux (long-tap) all at once:
```sh
apt update && apt -y full-upgrade && termux-setup-storage && apt -y install curl && cd && curl -L https://github.com/9001/copyparty/raw/master/scripts/copyparty-android.sh > copyparty-android.sh && chmod 755 copyparty-android.sh && ./copyparty-android.sh -h
echo $?
```

after the initial setup (and restarting bash), you can launch copyparty at any time by running "copyparty" in Termux


# dev env setup
```sh
python3 -m venv .env
. .env/bin/activate
pip install jinja2  # mandatory deps
pip install Pillow  # thumbnail deps
pip install black bandit pylint flake8  # vscode tooling
```


# immediate todo

roughly sorted by priority

* permissions break for `ed` on `-v /home/ed/vfs:moji:r -v /home/ed/inc:inc:r:aed`
* http error handling (conn.status or handler-retval)
* look into android thumbnail cache file format
* last-modified header
* support pillow-simd
* figure out the deal with pixel3a not being connectable as hotspot
  * pixel3a having unpredictable 3sec latency in general :||||

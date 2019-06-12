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


# install on android (fully automatic soon™)

install [Termux](https://termux.com/) (see [ocv.me/termux](https://ocv.me/termux/)) and then
```sh
apt install python
python3 -m venv ~/pe/ve.copyparty
. ~/pe/ve.copyparty/bin/activate
pip install jinja2
# download copyparty somehow, for example from git:
git clone https://github.com/9001/copyparty
cd copyparty
python3 -m copyparty
```

for image thumbnails, install optional dependency [Pillow](https://pypi.org/project/Pillow/):
```sh
apt install clang python-dev zlib-dev libjpeg-turbo-dev libcrypt-dev ndk-sysroot
CFLAGS=-I$HOME/../usr/include/ pip install Pillow
```


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

* deal with multiprocessing being busted on android
* permissions break for `ed` on `-v /home/ed/vfs:moji:r -v /home/ed/inc:inc:r:aed`
* http error handling (conn.status or handler-retval)
* look into android thumbnail cache file format
* run-script for android
* last-modified header
* support pillow-simd
* figure out the deal with pixel3a not being connectable as hotspot

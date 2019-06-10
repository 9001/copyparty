# ⇆🎉 copyparty

* http file sharing hub (py2/py3)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net

## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using IE6 or any other browser

* server runs on anything with `py2.7` or `py3.3+`
* *resumable* uploads need `firefox 12+` / `chrome 6+` / `safari 6+` / `IE 10+`
* code standard: `black`

## status

* [x] sanic multipart parser
* [x] load balancer (multiprocessing)
* [ ] upload (plain multipart, ie6 support)
* [ ] upload (js, resumable, multithreaded)
* [x] download
* [x] browser
* [x] media player
* [ ] thumbnails
* [ ] download as zip
* [x] volumes
* [x] accounts


# dependencies

* `jinja2`
  * pulls in `markupsafe`

optional, enables thumbnails:
* `Pillow` (requires py2.7 or py3.5+)


# install on android

install [Termux](https://termux.com/) (see [ocv.me/termux](https://ocv.me/termux/)) and then
```sh
apt install python
python3 -m venv ~/pe/ve.copyparty
. ~/pe/ve.copyparty/activate
pip install jinja2
# download copyparty somehow
python3 -m copyparty
```

for image thumbnails, install optional dependency [Pillow](https://pypi.org/project/Pillow/):
```sh
apt install clang python-dev zlib-dev libjpeg-turbo-dev libcrypt-dev ndk-sysroot
CFLAGS=-I$HOME/../usr/include/ pip install Pillow
```


# dev env setup
```sh
python3 -v venv .env
. .env/bin/activate
pip install jinja2  # mandatory deps
pip install Pillow  # thumbnail deps
pip install black bandit pylint flake8  # vscode tooling
```


# TODO

roughly sorted by priority

* last-modified header
* support pillow-simd

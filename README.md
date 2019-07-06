# ⇆🎉 copyparty

* http file sharing hub (py2/py3)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net


## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using IE6 or any other browser

* server runs on anything with `py2.7` or `py3.2+`
* *resumable* uploads need `firefox 12+` / `chrome 6+` / `safari 6+` / `IE 10+`
* code standard: `black`


## notes

* iPhone/iPad: use Firefox to download files
* Android-Chrome: set max "parallel uploads" for 200% upload speed (android bug)
* Android-Firefox: takes a while to select files (in order to avoid the above android-chrome issue)
* Desktop-Firefox: may use gigabytes of RAM if your connection is great and your files are massive


## status

* [x] sanic multipart parser
* [x] load balancer (multiprocessing)
* [x] upload (plain multipart, ie6 support)
* [x] upload (js, resumable, multithreaded)
* [x] download
* [x] browser
* [x] media player
* [ ] thumbnails
* [ ] download as zip
* [x] volumes
* [x] accounts

summary: close to beta


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


# how to release

in the `scripts` folder:

* run `make -C deps-docker` to build all dependencies
* create github release with `make-tgz-release.sh`
* upload to pypi with `make-pypi-release.(sh|bat)`


# todo

roughly sorted by priority

* look into android thumbnail cache file format
* support pillow-simd
* cache sha512 chunks on client
* symlink existing files on upload
* comment field
* figure out the deal with pixel3a not being connectable as hotspot
  * pixel3a having unpredictable 3sec latency in general :||||

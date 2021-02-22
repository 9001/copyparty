# ⇆🎉 copyparty

* http file sharing hub (py2/py3) [(on PyPI)](https://pypi.org/project/copyparty/)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net


## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using IE6 or any other browser

* server runs on anything with `py2.7` or `py3.3+`
* *resumable* uploads need `firefox 12+` / `chrome 6+` / `safari 6+` / `IE 10+`
* code standard: `black`


## quickstart

download [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) and you're all set!

running the sfx without arguments (for example doubleclicking it on Windows) will let anyone access the current folder; see `-h` for help if you want accounts and volumes etc

you may also want these, especially on servers:
* [contrib/systemd/copyparty.service](contrib/systemd/copyparty.service) to run copyparty as a systemd service
* [contrib/nginx/copyparty.conf](contrib/nginx/copyparty.conf) to reverse-proxy behind nginx (for legit https)


## notes

* iPhone/iPad: use Firefox to download files
* Android-Chrome: set max "parallel uploads" for 200% upload speed (android bug)
* Android-Firefox: takes a while to select files (in order to avoid the above android-chrome issue)
* Desktop-Firefox: may use gigabytes of RAM if your connection is great and your files are massive
* paper-printing is affected by dark/light-mode! use lightmode for color, darkmode for grayscale
  * because no browsers currently implement the media-query to do this properly orz


## status

* backend stuff
  * ☑ sanic multipart parser
  * ☑ load balancer (multiprocessing)
  * ☑ volumes (mountpoints)
  * ☑ accounts
* upload
  * ☑ basic: plain multipart, ie6 support
  * ☑ up2k: js, resumable, multithreaded
  * ☑ stash: simple PUT filedropper
  * ☑ symlink/discard existing files (content-matching)
* download
  * ☑ single files in browser
  * ✖ folders as zip files
  * ☑ FUSE client (read-only)
* browser
  * ☑ tree-view
  * ☑ media player
  * ✖ thumbnails
  * ✖ SPA (browse while uploading)
    * currently safe using the file-tree on the left only, not folders in the file list
* server indexing
  * ☑ locate files by contents
  * ☑ search by name/path/date/size
  * ✖ search by ID3-tags etc.
* markdown
  * ☑ viewer
  * ☑ editor (sure why not)

summary: it works! you can use it! (but technically not even close to beta)


# bugs

* probably, pls let me know


# searching

when started with `-e2dsa` copyparty will scan/index all your files. This avoids duplicates on upload, and also makes the volumes searchable through the web-ui:
* make search queries by `size`/`date`/`directory-path`/`filename`, or...
* drag/drop a local file to see if the same contents exist somewhere on the server (you get the URL if it does)

path/name queries are space-separated, AND'ed together, and words are negated with a `-` prefix, so for example:
* path: `shibayan -bossa` finds all files where one of the folders contain `shibayan` but filters out any results where `bossa` exists somewhere in the path
* name: `demetori styx` gives you [good stuff](https://www.youtube.com/watch?v=zGh0g14ZJ8I&list=PL3A147BD151EE5218&index=9)

other metadata (like song tags etc) are not yet indexed for searching


# client examples

* javascript: dump some state into a file (two separate examples)
  * `await fetch('https://127.0.0.1:3923/', {method:"PUT", body: JSON.stringify(foo)});`
  * `var xhr = new XMLHttpRequest(); xhr.open('POST', 'https://127.0.0.1:3923/msgs?raw'); xhr.send('foo');`

* FUSE: mount a copyparty server as a local filesystem
  * cross-platform python client available in [./bin/](bin/)
  * [rclone](https://rclone.org/) as client can give ~5x performance, see [./docs/rclone.md](docs/rclone.md)


# dependencies

* `jinja2`

optional, will eventually enable thumbnails:
* `Pillow` (requires py2.7 or py3.5+)


# sfx

currently there are two self-contained binaries:
* [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) -- pure python, works everywhere
* [copyparty-sfx.sh](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.sh) -- smaller, but only for linux and macos

launch either of them (**use sfx.py on systemd**) and it'll unpack and run copyparty, assuming you have python installed of course

pls note that `copyparty-sfx.sh` will fail if you rename `copyparty-sfx.py` to `copyparty.py` and keep it in the same folder because `sys.path` is funky


## sfx repack

if you don't need all the features you can repack the sfx and save a bunch of space; all you need is an sfx and a copy of this repo (nothing else to download or build, except for either msys2 or WSL if you're on windows)
* `724K` original size as of v0.4.0
* `256K` after `./scripts/make-sfx.sh re no-ogv`
* `164K` after `./scripts/make-sfx.sh re no-ogv no-cm`

the features you can opt to drop are
* `ogv`.js, the opus/vorbis decoder which is needed by apple devices to play foss audio files
* `cm`/easymde, the "fancy" markdown editor

for the `re`pack to work, first run one of the sfx'es once to unpack it

**note:** you can also just download and run [scripts/copyparty-repack.sh](scripts/copyparty-repack.sh) -- this will grab the latest copyparty release from github and do a `no-ogv no-cm` repack; works on linux/macos (and windows with msys2 or WSL)


# install on android

install [Termux](https://termux.com/) (see [ocv.me/termux](https://ocv.me/termux/)) and then copy-paste this into Termux (long-tap) all at once:
```sh
apt update && apt -y full-upgrade && termux-setup-storage && apt -y install python && python -m ensurepip && python -m pip install -U copyparty
echo $?
```

after the initial setup, you can launch copyparty at any time by running `copyparty` anywhere in Termux


# dev env setup

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install jinja2  # mandatory deps
pip install Pillow  # thumbnail deps
pip install black bandit pylint flake8  # vscode tooling
```


# how to release

in the `scripts` folder:

* run `make -C deps-docker` to build all dependencies
* create github release with `make-tgz-release.sh`
* upload to pypi with `make-pypi-release.(sh|bat)`
* create sfx with `make-sfx.sh`


# todo

roughly sorted by priority

* reduce up2k roundtrips
  * start from a chunk index and just go
  * terminate client on bad data
* drop onto folders
* `os.copy_file_range` for up2k cloning
* up2k partials ui
* support pillow-simd
* cache sha512 chunks on client
* comment field
* ~~look into android thumbnail cache file format~~ bad idea
* figure out the deal with pixel3a not being connectable as hotspot
  * pixel3a having unpredictable 3sec latency in general :||||

# ⇆🎉 copyparty

* http file sharing hub (py2/py3) [(on PyPI)](https://pypi.org/project/copyparty/)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net


## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using IE6 or any other browser

* server runs on anything with `py2.7` or `py3.3+`
* *resumable* uploads need `firefox 12+` / `chrome 6+` / `safari 6+` / `IE 10+`
* code standard: `black`


## readme toc

* top
    * [quickstart](#quickstart)
    * [notes](#notes)
    * [status](#status)
* [bugs](#bugs)
* [usage](#usage)
    * [zip downloads](#zip-downloads)
* [searching](#searching)
    * [search configuration](#search-configuration)
    * [metadata from audio files](#metadata-from-audio-files)
    * [file parser plugins](#file-parser-plugins)
    * [complete examples](#complete-examples)
* [browser support](#browser-support)
* [client examples](#client-examples)
* [dependencies](#dependencies)
    * [optional gpl stuff](#optional-gpl-stuff)
* [sfx](#sfx)
    * [sfx repack](#sfx-repack)
* [install on android](#install-on-android)
* [dev env setup](#dev-env-setup)
* [how to release](#how-to-release)
* [todo](#todo)


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
  * ☑ folders as zip / tar files
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
  * ☑ search by ID3-tags etc.
* markdown
  * ☑ viewer
  * ☑ editor (sure why not)

summary: it works! you can use it! (but technically not even close to beta)


# bugs

* Windows: python 3.7 and older cannot read tags with ffprobe, so use mutagen or upgrade
* Windows: python 2.7 cannot index non-ascii filenames with `-e2d`
* Windows: python 2.7 cannot handle filenames with mojibake
* hiding the contents at url `/d1/d2/d3` using `-v :d1/d2/d3:cd2d` has the side-effect of creating databases (for files/tags) inside folders d1 and d2, and those databases take precedence over the main db at the top of the vfs - this means all files in d2 and below will be reindexed unless you already had a vfs entry at or below d2
* probably more, pls let me know


# usage

the browser has the following hotkeys
* `0..9` jump to 10%..90%
* `U/O` skip 10sec back/forward
* `J/L` prev/next song
* `I/K` prev/next folder
* `P` parent folder

you can link a particular timestamp in an audio file by adding it to the URL, such as `&20` / `&20s` / `&1m20` / `&1:20` after the `.../#af-c8960dab`


## zip downloads

the `zip` link next to folders can produce various types of zip/tar files using these alternatives in the browser settings tab:

| name | url-suffix | description |
|--|--|--|
| `tar` | `?tar` | plain gnutar, works great with `curl \| tar -xv` |
| `zip` | `?zip=utf8` | works everywhere, glitchy filenames on win7 and older |
| `zip_dos` | `?zip` | traditional cp437 (no unicode) to fix glitchy filenames |
| `zip_crc` | `?zip=crc` | cp437 with crc32 computed early for truly ancient software |

* hidden files (dotfiles) are excluded unless `-ed`
  * the up2k.db is always excluded
* `zip_crc` will take longer to download since the server has to read each file twice
  * please let me know if you find a program old enough to actually need this


# searching

when started with `-e2dsa` copyparty will scan/index all your files. This avoids duplicates on upload, and also makes the volumes searchable through the web-ui:
* make search queries by `size`/`date`/`directory-path`/`filename`, or...
* drag/drop a local file to see if the same contents exist somewhere on the server (you get the URL if it does)

path/name queries are space-separated, AND'ed together, and words are negated with a `-` prefix, so for example:
* path: `shibayan -bossa` finds all files where one of the folders contain `shibayan` but filters out any results where `bossa` exists somewhere in the path
* name: `demetori styx` gives you [good stuff](https://www.youtube.com/watch?v=zGh0g14ZJ8I&list=PL3A147BD151EE5218&index=9)

add `-e2ts` to also scan/index tags from music files:


## search configuration

searching relies on two databases, the up2k filetree (`-e2d`) and the metadata tags (`-e2t`). Configuration can be done through arguments, volume flags, or a mix of both.

through arguments:
* `-e2d` enables file indexing on upload
* `-e2ds` scans writable folders on startup
* `-e2dsa` scans all mounted volumes (including readonly ones)
* `-e2t` enables metadata indexing on upload
* `-e2ts` scans for tags in all files that don't have tags yet
* `-e2tsr` deletes all existing tags, so a full reindex

the same arguments can be set as volume flags, in addition to `d2d` and `d2t` for disabling:
* `-v ~/music::r:ce2dsa:ce2tsr` does a full reindex of everything on startup
* `-v ~/music::r:cd2d` disables **all** indexing, even if any `-e2*` are on
* `-v ~/music::r:cd2t` disables all `-e2t*` (tags), does not affect `-e2d*`

`e2tsr` is probably always overkill, since `e2ds`/`e2dsa` would pick up any file modifications and cause `e2ts` to reindex those


## metadata from audio files

`-mte` decides which tags to index and display in the browser (and also the display order), this can be changed per-volume:
* `-v ~/music::r:cmte=title,artist` indexes and displays *title* followed by *artist*

if you add/remove a tag from `mte` you will need to run with `-e2tsr` once to rebuild the database, otherwise only new files will be affected

`-mtm` can be used to add or redefine a metadata mapping, say you have media files with `foo` and `bar` tags and you want them to display as `qux` in the browser (preferring `foo` if both are present), then do `-mtm qux=foo,bar` and now you can `-mte artist,title,qux`

tags that start with a `.` such as `.bpm` and `.dur`(ation) indicate numeric value

see the beautiful mess of a dictionary in [mtag.py](https://github.com/9001/copyparty/blob/master/copyparty/mtag.py) for the default mappings (should cover mp3,opus,flac,m4a,wav,aif,)

`--no-mutagen` disables mutagen and uses ffprobe instead, which...
* is about 20x slower than mutagen
* catches a few tags that mutagen doesn't
* avoids pulling any GPL code into copyparty
* more importantly runs ffprobe on incoming files which is bad if your ffmpeg has a cve


## file parser plugins

copyparty can invoke external programs to collect additional metadata for files using `mtp` (as argument or volume flag), there is a default timeout of 30sec

* `-mtp .bpm=~/bin/audio-bpm.py` will execute `~/bin/audio-bpm.py` with the audio file as argument 1 to provide the `.bpm` tag, if that does not exist in the audio metadata
* `-mtp key=f,t5,~/bin/audio-key.py` uses `~/bin/audio-key.py` to get the `key` tag, replacing any existing metadata tag (`f,`), aborting if it takes longer than 5sec (`t5,`)
* `-v ~/music::r:cmtp=.bpm=~/bin/audio-bpm.py:cmtp=key=f,t5,~/bin/audio-key.py` both as a per-volume config wow this is getting ugly


## complete examples

* read-only music server with bpm and key scanning  
  `python copyparty-sfx.py -v /mnt/nas/music:/music:r -e2dsa -e2ts -mtp .bpm=f,audio-bpm.py -mtp key=f,audio-key.py`


# browser support

`ie` = internet-explorer, `ff` = firefox, `c` = chrome, `iOS` = iPhone/iPad, `Andr` = Android

| feature         | ie6 | ie9 | ie10 | ie11 | ff 52 | c 49 | iOS | Andr |
| --------------- | --- | --- | ---- | ---- | ----- | ---- | --- | ---- |
| browse files    | yep | yep | yep  | yep  | yep   | yep  | yep | yep  |
| basic uploader  | yep | yep | yep  | yep  | yep   | yep  | yep | yep  |
| make directory  | yep | yep | yep  | yep  | yep   | yep  | yep | yep  |
| send message    | yep | yep | yep  | yep  | yep   | yep  | yep | yep  |
| set sort order  |  -  | yep | yep  | yep  | yep   | yep  | yep | yep  |
| zip selection   |  -  | yep | yep  | yep  | yep   | yep  | yep | yep  |
| directory tree  |  -  |  -  | `*1` | yep  | yep   | yep  | yep | yep  |
| up2k            |  -  |  -  | yep  | yep  | yep   | yep  | yep | yep  |
| icons work      |  -  |  -  | yep  | yep  | yep   | yep  | yep | yep  |
| markdown editor |  -  |  -  | yep  | yep  | yep   | yep  | yep | yep  |
| markdown viewer |  -  |  -  | yep  | yep  | yep   | yep  | yep | yep  |
| play mp3/m4a    |  -  | yep | yep  | yep  | yep   | yep  | yep | yep  |
| play ogg/opus   |  -  |  -  |  -   |  -   | yep   | yep  | `*2` | yep |

* internet explorer 6 to 8 behave the same
* firefox 52 and chrome 49 are the last winxp versions
* `*1` only public folders (login session is dropped) and no history / back-button
* `*2` using a wasm decoder which can sometimes get stuck and consumes a bit more power

quick summary of more eccentric web-browsers trying to view a directory index:
* safari (14.0.3/macos) is chrome with janky wasm, so playing opus can deadlock the javascript engine
* safari (14.0.1/iOS) same as macos, except it recovers from the deadlocks if you poke it a bit
* links (2.21/macports) can browse, login, upload/mkdir/msg
* lynx (2.8.9/macports) can browse, login, upload/mkdir/msg
* w3m (0.5.3/macports) can browse, login, upload at 100kB/s, mkdir/msg
* netsurf (3.10/arch) is basically ie6 with much better css (javascript has almost no effect)
* netscape 4.0 and 4.5 can browse (text is yellow on white), upload with `?b=u`
* SerenityOS (22d13d8) hits a page fault, works with `?b=u`, file input not-impl, url params are multiplying

# client examples

* javascript: dump some state into a file (two separate examples)
  * `await fetch('https://127.0.0.1:3923/', {method:"PUT", body: JSON.stringify(foo)});`
  * `var xhr = new XMLHttpRequest(); xhr.open('POST', 'https://127.0.0.1:3923/msgs?raw'); xhr.send('foo');`

* curl/wget: upload some files (post=file, chunk=stdin)
  * `post(){ curl -b cppwd=wark http://127.0.0.1:3923/ -F act=bput -F f=@"$1";}`  
    `post movie.mkv`
  * `post(){ wget --header='Cookie: cppwd=wark' http://127.0.0.1:3923/?raw --post-file="$1" -O-;}`  
    `post movie.mkv`
  * `chunk(){ curl -b cppwd=wark http://127.0.0.1:3923/ -T-;}`  
    `chunk <movie.mkv`

* FUSE: mount a copyparty server as a local filesystem
  * cross-platform python client available in [./bin/](bin/)
  * [rclone](https://rclone.org/) as client can give ~5x performance, see [./docs/rclone.md](docs/rclone.md)

copyparty returns a truncated sha512sum of your PUT/POST as base64; you can generate the same checksum locally to verify uplaods:

    b512(){ printf "$((sha512sum||shasum -a512)|sed -E 's/ .*//;s/(..)/\\x\1/g')"|base64|head -c43;}
    b512 <movie.mkv


# dependencies

* `jinja2` (is built into the SFX)

**optional,** enables music tags:
* either `mutagen` (fast, pure-python, skips a few tags, makes copyparty GPL? idk)
* or `FFprobe` (20x slower, more accurate, possibly dangerous depending on your distro and users)

**optional,** will eventually enable thumbnails:
* `Pillow` (requires py2.7 or py3.5+)


## optional gpl stuff

some bundled tools have copyleft dependencies, see [./bin/#mtag](bin/#mtag)

these are standalone and will never be imported / evaluated by copyparty


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
* `git tag v1.2.3 && git push origin --tags`
* create github release with `make-tgz-release.sh`
* upload to pypi with `make-pypi-release.(sh|bat)`
* create sfx with `make-sfx.sh`


# todo

roughly sorted by priority

* separate sqlite table per tag
* audio fingerprinting
* readme.md as epilogue
* reduce up2k roundtrips
  * start from a chunk index and just go
  * terminate client on bad data
* `os.copy_file_range` for up2k cloning
* support pillow-simd
* figure out the deal with pixel3a not being connectable as hotspot
  * pixel3a having unpredictable 3sec latency in general :||||

discarded ideas

* up2k partials ui
* cache sha512 chunks on client
* comment field
* look into android thumbnail cache file format

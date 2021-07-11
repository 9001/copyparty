# ⇆🎉 copyparty

* http file sharing hub (py2/py3) [(on PyPI)](https://pypi.org/project/copyparty/)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net


## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using IE6 or any other browser

* server runs on anything with `py2.7` or `py3.3+`
* browse/upload with IE4 / netscape4.0 on win3.11 (heh)
* *resumable* uploads need `firefox 34+` / `chrome 41+` / `safari 7+` for full speed
* code standard: `black`

📷 **screenshots:** [browser](#the-browser) // [upload](#uploading) // [thumbnails](#thumbnails) // [md-viewer](#markdown-viewer) // [search](#searching) // [fsearch](#file-search) // [zip-DL](#zip-downloads) // [ie4](#browser-support)


## readme toc

* top
    * [quickstart](#quickstart)
        * [on debian](#on-debian)
    * [notes](#notes)
    * [status](#status)
    * [testimonials](#testimonials)
* [bugs](#bugs)
    * [general bugs](#general-bugs)
    * [not my bugs](#not-my-bugs)
* [the browser](#the-browser)
    * [tabs](#tabs)
    * [hotkeys](#hotkeys)
    * [tree-mode](#tree-mode)
    * [thumbnails](#thumbnails)
    * [zip downloads](#zip-downloads)
    * [uploading](#uploading)
        * [file-search](#file-search)
    * [markdown viewer](#markdown-viewer)
    * [other tricks](#other-tricks)
* [searching](#searching)
    * [search configuration](#search-configuration)
    * [database location](#database-location)
    * [metadata from audio files](#metadata-from-audio-files)
    * [file parser plugins](#file-parser-plugins)
    * [complete examples](#complete-examples)
* [browser support](#browser-support)
* [client examples](#client-examples)
* [up2k](#up2k)
* [performance](#performance)
* [dependencies](#dependencies)
    * [optional dependencies](#optional-dependencies)
    * [install recommended deps](#install-recommended-deps)
    * [optional gpl stuff](#optional-gpl-stuff)
* [sfx](#sfx)
    * [sfx repack](#sfx-repack)
* [install on android](#install-on-android)
* [building](#building)
    * [dev env setup](#dev-env-setup)
    * [just the sfx](#just-the-sfx)
    * [complete release](#complete-release)
* [todo](#todo)


## quickstart

download [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) and you're all set!

running the sfx without arguments (for example doubleclicking it on Windows) will give everyone full access to the current folder; see `-h` for help if you want accounts and volumes etc

some recommended options:
* `-e2dsa` enables general file indexing, see [search configuration](#search-configuration)
* `-e2ts` enables audio metadata indexing (needs either FFprobe or mutagen), see [optional dependencies](#optional-dependencies)
* `-v /mnt/music:/music:r:afoo -a foo:bar` shares `/mnt/music` as `/music`, `r`eadable by anyone, with user `foo` as `a`dmin (read/write), password `bar`
  * the syntax is `-v src:dst:perm:perm:...` so local-path, url-path, and one or more permissions to set
  * replace `:r:afoo` with `:rfoo` to only make the folder readable by `foo` and nobody else
  * in addition to `r`ead and `a`dmin, `w`rite makes a folder write-only, so cannot list/access files in it
* `--ls '**,*,ln,p,r'` to crash on startup if any of the volumes contain a symlink which point outside the volume, as that could give users unintended access

you may also want these, especially on servers:
* [contrib/systemd/copyparty.service](contrib/systemd/copyparty.service) to run copyparty as a systemd service
* [contrib/nginx/copyparty.conf](contrib/nginx/copyparty.conf) to reverse-proxy behind nginx (for better https)


### on debian

recommended steps to enable audio metadata and thumbnails (from images and videos):

* as root, run the following:  
  `apt install python3 python3-pip python3-dev ffmpeg`

* then, as the user which will be running copyparty (so hopefully not root), run this:  
  `python3 -m pip install --user -U Pillow pillow-avif-plugin`

(skipped `pyheif-pillow-opener` because apparently debian is too old to build it)


## notes

general:
* paper-printing is affected by dark/light-mode! use lightmode for color, darkmode for grayscale
  * because no browsers currently implement the media-query to do this properly orz

browser-specific:
* iPhone/iPad: use Firefox to download files
* Android-Chrome: increase "parallel uploads" for higher speed (android bug)
* Android-Firefox: takes a while to select files (their fix for ☝️)
* Desktop-Firefox: ~~may use gigabytes of RAM if your files are massive~~ *seems to be OK now*
* Desktop-Firefox: may stop you from deleting folders you've uploaded until you visit `about:memory` and click `Minimize memory usage`


## status

summary: all planned features work! now please enjoy the bloatening

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
  * ☑ audio player (with OS media controls)
  * ☑ thumbnails
    * ☑ images using Pillow
    * ☑ videos using FFmpeg
    * ☑ cache eviction (max-age; maybe max-size eventually)
  * ☑ image gallery
  * ☑ SPA (browse while uploading)
    * if you use the file-tree on the left only, not folders in the file list
* server indexing
  * ☑ locate files by contents
  * ☑ search by name/path/date/size
  * ☑ search by ID3-tags etc.
* markdown
  * ☑ viewer
  * ☑ editor (sure why not)


## testimonials

small collection of user feedback

`good enough`, `surprisingly correct`, `certified good software`, `just works`, `why`


# bugs

* Windows: python 3.7 and older cannot read tags with ffprobe, so use mutagen or upgrade
* Windows: python 2.7 cannot index non-ascii filenames with `-e2d`
* Windows: python 2.7 cannot handle filenames with mojibake
* MacOS: `--th-ff-jpg` may fix thumbnails using macports-FFmpeg

## general bugs

* all volumes must exist / be available on startup; up2k (mtp especially) gets funky otherwise
* cannot mount something at `/d1/d2/d3` unless `d2` exists inside `d1`
* dupe files will not have metadata (audio tags etc) displayed in the file listing
  * because they don't get `up` entries in the db (probably best fix) and `tx_browser` does not `lstat`
* probably more, pls let me know

## not my bugs

* Windows: folders cannot be accessed if the name ends with `.`
  * python or windows bug

* Windows: msys2-python 3.8.6 occasionally throws "RuntimeError: release unlocked lock" when leaving a scoped mutex in up2k
  * this is an msys2 bug, the regular windows edition of python is fine


# the browser

![copyparty-browser-fs8](https://user-images.githubusercontent.com/241032/115978054-65106380-a57d-11eb-98f8-59e3dee73557.png)


## tabs

* `[🔎]` search by size, date, path/name, mp3-tags ... see [searching](#searching)
* `[🚀]` and `[🎈]` are the uploaders, see [uploading](#uploading)
* `[📂]` mkdir, create directories
* `[📝]` new-md, create a new markdown document
* `[📟]` send-msg, either to server-log or into textfiles if `--urlform save`
* `[⚙️]` client configuration options


## hotkeys

the browser has the following hotkeys
* `B` toggle breadcrumbs / directory tree
* `I/K` prev/next folder
* `M` parent folder
* `G` toggle list / grid view
* `T` toggle thumbnails / icons
* when playing audio:
  * `J/L` prev/next song
  * `U/O` skip 10sec back/forward
  * `0..9` jump to 10%..90%
  * `P` play/pause (also starts playing the folder)
* when viewing images / playing videos:
  * `J/L, Left/Right` prev/next file
  * `Home/End` first/last file
  * `U/O` skip 10sec back/forward
  * `P/K/Space` play/pause video
  * `Esc` close viewer
* when tree-sidebar is open:
  * `A/D` adjust tree width
* in the grid view:
  * `S` toggle multiselect
  * shift+`A/D` zoom


## tree-mode

by default there's a breadcrumbs path; you can replace this with a tree-browser sidebar thing by clicking the `🌲` or pressing the `B` hotkey

click `[-]` and `[+]` (or hotkeys `A`/`D`) to adjust the size, and the `[a]` toggles if the tree should widen dynamically as you go deeper or stay fixed-size


## thumbnails

![copyparty-thumbs-fs8](https://user-images.githubusercontent.com/241032/120070302-10836b00-c08a-11eb-8eb4-82004a34c342.png)

it does static images with Pillow and uses FFmpeg for video files, so you may want to `--no-thumb` or maybe just `--no-vthumb` depending on how destructive your users are

images named `folder.jpg` and `folder.png` become the thumbnail of the folder they're in

in the grid/thumbnail view, if the audio player panel is open, songs will start playing when clicked


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

you can also zip a selection of files or folders by clicking them in the browser, that brings up a selection editor and zip button in the bottom right

![copyparty-zipsel-fs8](https://user-images.githubusercontent.com/241032/116008321-372a2e00-a614-11eb-9a4a-4a1fd9074224.png)

## uploading

two upload methods are available in the html client:
* `🎈 bup`, the basic uploader, supports almost every browser since netscape 4.0
* `🚀 up2k`, the fancy one

up2k has several advantages:
* you can drop folders into the browser (files are added recursively)
* files are processed in chunks, and each chunk is checksummed
  * uploads resume if they are interrupted (for example by a reboot)
  * server detects any corruption; the client reuploads affected chunks
  * the client doesn't upload anything that already exists on the server
* the last-modified timestamp of the file is preserved

see [up2k](#up2k) for details on how it works

![copyparty-upload-fs8](https://user-images.githubusercontent.com/241032/115978061-680b5400-a57d-11eb-9ef6-cbb5f60aeccc.png)

**protip:** you can avoid scaring away users with [docs/minimal-up2k.html](docs/minimal-up2k.html) which makes it look [much simpler](https://user-images.githubusercontent.com/241032/118311195-dd6ca380-b4ef-11eb-86f3-75a3ff2e1332.png)

the up2k UI is the epitome of polished inutitive experiences:
* "parallel uploads" specifies how many chunks to upload at the same time
* `[🏃]` analysis of other files should continue while one is uploading
* `[💭]` ask for confirmation before files are added to the list
* `[💤]` sync uploading between other copyparty tabs so only one is active
* `[🔎]` switch between upload and file-search mode

and then theres the tabs below it,
* `[ok]` is uploads which completed successfully
* `[ng]` is the uploads which failed / got rejected (already exists, ...)
* `[done]` shows a combined list of `[ok]` and `[ng]`, chronological order
* `[busy]` files which are currently hashing, pending-upload, or uploading
  * plus up to 3 entries each from `[done]` and `[que]` for context
* `[que]` is all the files that are still queued

### file-search

![copyparty-fsearch-fs8](https://user-images.githubusercontent.com/241032/116008320-36919780-a614-11eb-803f-04162326a700.png)

in the `[🚀 up2k]` tab, after toggling the `[🔎]` switch green, any files/folders you drop onto the dropzone will be hashed on the client-side. Each hash is sent to the server which checks if that file exists somewhere already

files go into `[ok]` if they exist (and you get a link to where it is), otherwise they land in `[ng]`
* the main reason filesearch is combined with the uploader is cause the code was too spaghetti to separate it out somewhere else, this is no longer the case but now i've warmed up to the idea too much

adding the same file multiple times is blocked, so if you first search for a file and then decide to upload it, you have to click the `[cleanup]` button to discard `[done]` files

note that since up2k has to read the file twice, `[🎈 bup]` can be up to 2x faster in extreme cases (if your internet connection is faster than the read-speed of your HDD)

up2k has saved a few uploads from becoming corrupted in-transfer already; caught an android phone on wifi redhanded in wireshark with a bitflip, however bup with https would *probably* have noticed as well thanks to tls also functioning as an integrity check


## markdown viewer

![copyparty-md-read-fs8](https://user-images.githubusercontent.com/241032/115978057-66419080-a57d-11eb-8539-d2be843991aa.png)

* the document preview has a max-width which is the same as an A4 paper when printed


## other tricks

* you can link a particular timestamp in an audio file by adding it to the URL, such as `&20` / `&20s` / `&1m20` / `&t=1:20` after the `.../#af-c8960dab`

* if you are using media hotkeys to switch songs and are getting tired of seeing the OSD popup which Windows doesn't let you disable, consider https://ocv.me/dev/?media-osd-bgone.ps1


# searching

![copyparty-search-fs8](https://user-images.githubusercontent.com/241032/115978060-6772bd80-a57d-11eb-81d3-174e869b72c3.png)

when started with `-e2dsa` copyparty will scan/index all your files. This avoids duplicates on upload, and also makes the volumes searchable through the web-ui:
* make search queries by `size`/`date`/`directory-path`/`filename`, or...
* drag/drop a local file to see if the same contents exist somewhere on the server, see [file-search](#file-search)

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

note:
* `e2tsr` is probably always overkill, since `e2ds`/`e2dsa` would pick up any file modifications and `e2ts` would then reindex those
* the rescan button in the admin panel has no effect unless the volume has `-e2ds` or higher

you can choose to only index filename/path/size/last-modified (and not the hash of the file contents) by setting `--no-hash` or the volume-flag `cdhash`, this has the following consequences:
* initial indexing is way faster, especially when the volume is on a networked disk
* makes it impossible to [file-search](#file-search)
* if someone uploads the same file contents, the upload will not be detected as a dupe, so it will not get symlinked or rejected

if you set `--no-hash`, you can enable hashing for specific volumes using flag `cehash`


## database location

copyparty creates a subfolder named `.hist` inside each volume where it stores the database, thumbnails, and some other stuff

this can instead be kept in a single place using the `--hist` argument, or the `hist=` volume flag, or a mix of both:
* `--hist ~/.cache/copyparty -v ~/music::r:chist=-` sets `~/.cache/copyparty` as the default place to put volume info, but `~/music` gets the regular `.hist` subfolder (`-` restores default behavior)

note:
* markdown edits are always stored in a local `.hist` subdirectory
* on windows the volflag path is cyglike, so `/c/temp` means `C:\temp` but use regular paths for `--hist`
  * you can use cygpaths for volumes too, `-v C:\Users::r` and `-v /c/users::r` both work


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
  * melodic key, video resolution, framerate, pixfmt
* avoids pulling any GPL code into copyparty
* more importantly runs ffprobe on incoming files which is bad if your ffmpeg has a cve


## file parser plugins

copyparty can invoke external programs to collect additional metadata for files using `mtp` (as argument or volume flag), there is a default timeout of 30sec

* `-mtp .bpm=~/bin/audio-bpm.py` will execute `~/bin/audio-bpm.py` with the audio file as argument 1 to provide the `.bpm` tag, if that does not exist in the audio metadata
* `-mtp key=f,t5,~/bin/audio-key.py` uses `~/bin/audio-key.py` to get the `key` tag, replacing any existing metadata tag (`f,`), aborting if it takes longer than 5sec (`t5,`)
* `-v ~/music::r:cmtp=.bpm=~/bin/audio-bpm.py:cmtp=key=f,t5,~/bin/audio-key.py` both as a per-volume config wow this is getting ugly

*but wait, there's more!* `-mtp` can be used for non-audio files as well using the `a` flag: `ay` only do audio files, `an` only do non-audio files, or `ad` do all files (d as in dontcare) 

* `-mtp ext=an,~/bin/file-ext.py` runs `~/bin/file-ext.py` to get the `ext` tag only if file is not audio (`an`)
* `-mtp arch,built,ver,orig=an,eexe,edll,~/bin/exe.py` runs `~/bin/exe.py` to get properties about windows-binaries only if file is not audio (`an`) and file extension is exe or dll


## complete examples

* read-only music server with bpm and key scanning  
  `python copyparty-sfx.py -v /mnt/nas/music:/music:r -e2dsa -e2ts -mtp .bpm=f,audio-bpm.py -mtp key=f,audio-key.py`


# browser support

![copyparty-ie4-fs8](https://user-images.githubusercontent.com/241032/118192791-fb31fe00-b446-11eb-9647-898ea8efc1f7.png)

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

| browser | will it blend |
| ------- | ------------- |
| **safari** (14.0.3/macos) | is chrome with janky wasm, so playing opus can deadlock the javascript engine |
| **safari** (14.0.1/iOS)   | same as macos, except it recovers from the deadlocks if you poke it a bit |
| **links** (2.21/macports) | can browse, login, upload/mkdir/msg |
| **lynx** (2.8.9/macports) | can browse, login, upload/mkdir/msg |
| **w3m** (0.5.3/macports)  | can browse, login, upload at 100kB/s, mkdir/msg |
| **netsurf** (3.10/arch)   | is basically ie6 with much better css (javascript has almost no effect) | 
| **ie4** and **netscape** 4.0  | can browse (text is yellow on white), upload with `?b=u` |
| **SerenityOS** (22d13d8)  | hits a page fault, works with `?b=u`, file input not-impl, url params are multiplying |


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

* sharex (screenshot utility): see [./contrib/sharex.sxcu](contrib/#sharexsxcu)

copyparty returns a truncated sha512sum of your PUT/POST as base64; you can generate the same checksum locally to verify uplaods:

    b512(){ printf "$((sha512sum||shasum -a512)|sed -E 's/ .*//;s/(..)/\\x\1/g')"|base64|tr '+/' '-_'|head -c44;}
    b512 <movie.mkv


# up2k

quick outline of the up2k protocol, see [uploading](#uploading) for the web-client
* the up2k client splits a file into an "optimal" number of chunks
  * 1 MiB each, unless that becomes more than 256 chunks
  * tries 1.5M, 2M, 3, 4, 6, ... until <= 256 chunks or size >= 32M
* client posts the list of hashes, filename, size, last-modified
* server creates the `wark`, an identifier for this upload
  * `sha512( salt + filesize + chunk_hashes )`
  * and a sparse file is created for the chunks to drop into
* client uploads each chunk
  * header entries for the chunk-hash and wark
  * server writes chunks into place based on the hash
* client does another handshake with the hashlist; server replies with OK or a list of chunks to reupload


# performance

defaults are good for most cases, don't mind the `cannot efficiently use multiple CPU cores` message, it's very unlikely to be a problem

below are some tweaks roughly ordered by usefulness:

* `-q` disables logging and can help a bunch, even when combined with `-lo` to redirect logs to file
* `--http-only` or `--https-only` (unless you want to support both protocols) will reduce the delay before a new connection is established
* `--hist` pointing to a fast location (ssd) will make directory listings and searches faster when `-e2d` or `-e2t` is set
* `--no-hash` when indexing a networked disk if you don't care about the actual filehashes and only want the names/tags searchable
* `-j` enables multiprocessing (actual multithreading) and can make copyparty perform better in cpu-intensive workloads, for example:
  * huge amount of short-lived connections
  * really heavy traffic (downloads/uploads)
  
  ...however it adds an overhead to internal communication so it might be a net loss, see if it works 4 u


# dependencies

* `jinja2` (is built into the SFX)


## optional dependencies

enable music tags:
* either `mutagen` (fast, pure-python, skips a few tags, makes copyparty GPL? idk)
* or `FFprobe` (20x slower, more accurate, possibly dangerous depending on your distro and users)

enable image thumbnails:
* `Pillow` (requires py2.7 or py3.5+)

enable video thumbnails:
* `ffmpeg` and `ffprobe` somewhere in `$PATH`

enable reading HEIF pictures:
* `pyheif-pillow-opener` (requires Linux or a C compiler)

enable reading AVIF pictures:
* `pillow-avif-plugin`


## install recommended deps
```
python -m pip install --user -U jinja2 mutagen Pillow
```


## optional gpl stuff

some bundled tools have copyleft dependencies, see [./bin/#mtag](bin/#mtag)

these are standalone programs and will never be imported / evaluated by copyparty


# sfx

currently there are two self-contained "binaries":
* [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) -- pure python, works everywhere, **recommended**
* [copyparty-sfx.sh](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.sh) -- smaller, but only for linux and macos, kinda deprecated

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


# building

## dev env setup

mostly optional; if you need a working env for vscode or similar

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install jinja2  # mandatory
pip install mutagen  # audio metadata
pip install Pillow pyheif-pillow-opener pillow-avif-plugin  # thumbnails
pip install black bandit pylint flake8  # vscode tooling
```


## just the sfx

unless you need to modify something in the web-dependencies, it's faster to grab those from a previous release:

```sh
rm -rf copyparty/web/deps
curl -L https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py >x.py
python3 x.py -h
rm x.py
mv /tmp/pe-copyparty/copyparty/web/deps/ copyparty/web/
```

then build the sfx using any of the following examples:

```sh
./scripts/make-sfx.sh  # both python and sh editions
./scripts/make-sfx.sh no-sh gz  # just python with gzip
```


## complete release

also builds the sfx so disregard the sfx section above

in the `scripts` folder:

* run `make -C deps-docker` to build all dependencies
* `git tag v1.2.3 && git push origin --tags`
* create github release with `make-tgz-release.sh`
* upload to pypi with `make-pypi-release.(sh|bat)`
* create sfx with `make-sfx.sh`


# todo

roughly sorted by priority

* readme.md as epilogue
* reduce up2k roundtrips
  * start from a chunk index and just go
  * terminate client on bad data
* logging to file

discarded ideas

* single sha512 across all up2k chunks?
  * crypto.subtle cannot into streaming, would have to use hashwasm, expensive
* separate sqlite table per tag
  * performance fixed by skipping some indexes (`+mt.k`)
* audio fingerprinting
  * only makes sense if there can be a wasm client and that doesn't exist yet (except for olaf which is agpl hence counts as not existing)
* `os.copy_file_range` for up2k cloning
  * almost never hit this path anyways
* up2k partials ui
  * feels like there isn't much point
* cache sha512 chunks on client
  * too dangerous
* comment field
  * nah
* look into android thumbnail cache file format
  * absolutely not
* indexedDB for hashes, cfg enable/clear/sz, 2gb avail, ~9k for 1g, ~4k for 100m, 500k items before autoeviction
  * blank hashlist when up-ok to skip handshake
    * too many confusing side-effects

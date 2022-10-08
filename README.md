# ⇆🎉 copyparty

* http file sharing hub (py2/py3) [(on PyPI)](https://pypi.org/project/copyparty/)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net


## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using *any* web browser

* server only needs `py2.7` or `py3.3+`, all dependencies optional
* browse/upload with [IE4](#browser-support) / netscape4.0 on win3.11 (heh)
* *resumable* uploads need `firefox 34+` / `chrome 41+` / `safari 7+`

try the **[read-only demo server](https://a.ocv.me/pub/demo/)** 👀 running from a basement in finland

📷 **screenshots:** [browser](#the-browser) // [upload](#uploading) // [unpost](#unpost) // [thumbnails](#thumbnails) // [search](#searching) // [fsearch](#file-search) // [zip-DL](#zip-downloads) // [md-viewer](#markdown-viewer)


## get the app

<a href="https://f-droid.org/packages/me.ocv.partyup/"><img src="https://ocv.me/fdroid.png" alt="Get it on F-Droid" height="50" /> '' <img src="https://img.shields.io/f-droid/v/me.ocv.partyup.svg" alt="f-droid version info" /></a> '' <a href="https://github.com/9001/party-up"><img src="https://img.shields.io/github/release/9001/party-up.svg?logo=github" alt="github version info" /></a>

(the app is **NOT** the full copyparty server! just a basic upload client, nothing fancy yet)


## readme toc

* top
    * [quickstart](#quickstart) - download **[copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py)** and you're all set!
        * [on servers](#on-servers) - you may also want these, especially on servers
        * [on debian](#on-debian) - recommended additional steps on debian
    * [notes](#notes) - general notes
    * [status](#status) - feature summary
    * [testimonials](#testimonials) - small collection of user feedback
* [motivations](#motivations) - project goals / philosophy
    * [future plans](#future-plans) - some improvement ideas
* [bugs](#bugs)
    * [general bugs](#general-bugs)
    * [not my bugs](#not-my-bugs)
* [FAQ](#FAQ) - "frequently" asked questions
* [accounts and volumes](#accounts-and-volumes) - per-folder, per-user permissions
* [the browser](#the-browser) - accessing a copyparty server using a web-browser
    * [tabs](#tabs) - the main tabs in the ui
    * [hotkeys](#hotkeys) - the browser has the following hotkeys
    * [navpane](#navpane) - switching between breadcrumbs or navpane
    * [thumbnails](#thumbnails) - press `g` or `田` to toggle grid-view instead of the file listing
    * [zip downloads](#zip-downloads) - download folders (or file selections) as `zip` or `tar` files
    * [uploading](#uploading) - drag files/folders into the web-browser to upload
        * [file-search](#file-search) - dropping files into the browser also lets you see if they exist on the server
        * [unpost](#unpost) - undo/delete accidental uploads
        * [self-destruct](#self-destruct) - uploads can be given a lifetime
    * [file manager](#file-manager) - cut/paste, rename, and delete files/folders (if you have permission)
    * [batch rename](#batch-rename) - select some files and press `F2` to bring up the rename UI
    * [markdown viewer](#markdown-viewer) - and there are *two* editors
    * [other tricks](#other-tricks)
    * [searching](#searching) - search by size, date, path/name, mp3-tags, ...
* [server config](#server-config) - using arguments or config files, or a mix of both
    * [qr-code](#qr-code) - print a qr-code [(screenshot)](https://user-images.githubusercontent.com/241032/194728533-6f00849b-c6ac-43c6-9359-83e454d11e00.png) for quick access
    * [ftp-server](#ftp-server) - an FTP server can be started using `--ftp 3921`
    * [file indexing](#file-indexing) - enables dedup and music search ++
        * [exclude-patterns](#exclude-patterns) - to save some time
        * [filesystem guards](#filesystem-guards) - avoid traversing into other filesystems
        * [periodic rescan](#periodic-rescan) - filesystem monitoring
    * [upload rules](#upload-rules) - set upload rules using volflags
    * [compress uploads](#compress-uploads) - files can be autocompressed on upload
    * [other flags](#other-flags)
    * [database location](#database-location) - in-volume (`.hist/up2k.db`, default) or somewhere else
    * [metadata from audio files](#metadata-from-audio-files) - set `-e2t` to index tags on upload
    * [file parser plugins](#file-parser-plugins) - provide custom parsers to index additional tags
    * [upload events](#upload-events) - trigger a script/program on each upload
    * [hiding from google](#hiding-from-google) - tell search engines you dont wanna be indexed
    * [themes](#themes)
    * [complete examples](#complete-examples)
* [browser support](#browser-support) - TLDR: yes
* [client examples](#client-examples) - interact with copyparty using non-browser clients
* [up2k](#up2k) - quick outline of the up2k protocol, see [uploading](#uploading) for the web-client
    * [why chunk-hashes](#why-chunk-hashes) - a single sha512 would be better, right?
* [performance](#performance) - defaults are usually fine - expect `8 GiB/s` download, `1 GiB/s` upload
    * [client-side](#client-side) - when uploading files
* [security](#security) - some notes on hardening
    * [gotchas](#gotchas) - behavior that might be unexpected
* [recovering from crashes](#recovering-from-crashes)
    * [client crashes](#client-crashes)
        * [frefox wsod](#frefox-wsod) - firefox 87 can crash during uploads
* [HTTP API](#HTTP-API)
    * [read](#read)
    * [write](#write)
    * [admin](#admin)
    * [general](#general)
* [dependencies](#dependencies) - mandatory deps
    * [optional dependencies](#optional-dependencies) - install these to enable bonus features
    * [install recommended deps](#install-recommended-deps)
    * [optional gpl stuff](#optional-gpl-stuff)
* [sfx](#sfx) - the self-contained "binary"
    * [sfx repack](#sfx-repack) - reduce the size of an sfx by removing features
    * [copyparty.exe](#copypartyexe)
* [install on android](#install-on-android)
* [reporting bugs](#reporting-bugs) - ideas for context to include in bug reports
* [building](#building)
    * [dev env setup](#dev-env-setup)
    * [just the sfx](#just-the-sfx)
    * [complete release](#complete-release)
* [todo](#todo) - roughly sorted by priority
    * [discarded ideas](#discarded-ideas)


## quickstart

download **[copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py)** and you're all set!

if you cannot install python, you can use [copyparty.exe](#copypartyexe) instead

running the sfx without arguments (for example doubleclicking it on Windows) will give everyone read/write access to the current folder; you may want [accounts and volumes](#accounts-and-volumes)

some recommended options:
* `-e2dsa` enables general [file indexing](#file-indexing)
* `-e2ts` enables audio metadata indexing (needs either FFprobe or Mutagen), see [optional dependencies](#optional-dependencies)
* `-v /mnt/music:/music:r:rw,foo -a foo:bar` shares `/mnt/music` as `/music`, `r`eadable by anyone, and read-write for user `foo`, password `bar`
  * replace `:r:rw,foo` with `:r,foo` to only make the folder readable by `foo` and nobody else
  * see [accounts and volumes](#accounts-and-volumes) for the syntax and other permissions (`r`ead, `w`rite, `m`ove, `d`elete, `g`et, up`G`et)
* `--ls '**,*,ln,p,r'` to crash on startup if any of the volumes contain a symlink which point outside the volume, as that could give users unintended access (see `--help-ls`)


### on servers

you may also want these, especially on servers:

* [contrib/systemd/copyparty.service](contrib/systemd/copyparty.service) to run copyparty as a systemd service
* [contrib/systemd/prisonparty.service](contrib/systemd/prisonparty.service) to run it in a chroot (for extra security)
* [contrib/nginx/copyparty.conf](contrib/nginx/copyparty.conf) to reverse-proxy behind nginx (for better https)


### on debian

recommended additional steps on debian  which enable audio metadata and thumbnails (from images and videos):

* as root, run the following:  
  `apt install python3 python3-pip python3-dev ffmpeg`

* then, as the user which will be running copyparty (so hopefully not root), run this:  
  `python3 -m pip install --user -U Pillow pillow-avif-plugin`

(skipped `pyheif-pillow-opener` because apparently debian is too old to build it)


## notes

general notes:
* paper-printing is affected by dark/light-mode! use lightmode for color, darkmode for grayscale
  * because no browsers currently implement the media-query to do this properly orz

browser-specific:
* iPhone/iPad: use Firefox to download files
* Android-Chrome: increase "parallel uploads" for higher speed (android bug)
* Android-Firefox: takes a while to select files (their fix for ☝️)
* Desktop-Firefox: ~~may use gigabytes of RAM if your files are massive~~ *seems to be OK now*
* Desktop-Firefox: may stop you from deleting files you've uploaded until you visit `about:memory` and click `Minimize memory usage`


## status

feature summary

* backend stuff
  * ☑ sanic multipart parser
  * ☑ multiprocessing (actual multithreading)
  * ☑ volumes (mountpoints)
  * ☑ [accounts](#accounts-and-volumes)
  * ☑ [ftp-server](#ftp-server)
  * ☑ [qr-code](#qr-code) for quick access
* upload
  * ☑ basic: plain multipart, ie6 support
  * ☑ [up2k](#uploading): js, resumable, multithreaded
  * ☑ stash: simple PUT filedropper
  * ☑ [unpost](#unpost): undo/delete accidental uploads
  * ☑ [self-destruct](#self-destruct) (specified server-side or client-side)
  * ☑ symlink/discard existing files (content-matching)
* download
  * ☑ single files in browser
  * ☑ [folders as zip / tar files](#zip-downloads)
  * ☑ [FUSE client](https://github.com/9001/copyparty/tree/hovudstraum/bin#copyparty-fusepy) (read-only)
* browser
  * ☑ [navpane](#navpane) (directory tree sidebar)
  * ☑ file manager (cut/paste, delete, [batch-rename](#batch-rename))
  * ☑ audio player (with OS media controls and opus transcoding)
  * ☑ image gallery with webm player
  * ☑ textfile browser with syntax hilighting
  * ☑ [thumbnails](#thumbnails)
    * ☑ ...of images using Pillow, pyvips, or FFmpeg
    * ☑ ...of videos using FFmpeg
    * ☑ ...of audio (spectrograms) using FFmpeg
    * ☑ cache eviction (max-age; maybe max-size eventually)
  * ☑ SPA (browse while uploading)
* server indexing
  * ☑ [locate files by contents](#file-search)
  * ☑ search by name/path/date/size
  * ☑ [search by ID3-tags etc.](#searching)
* markdown
  * ☑ [viewer](#markdown-viewer)
  * ☑ editor (sure why not)


## testimonials

small collection of user feedback

`good enough`, `surprisingly correct`, `certified good software`, `just works`, `why`


# motivations

project goals / philosophy

* inverse linux philosophy -- do all the things, and do an *okay* job
  * quick drop-in service to get a lot of features in a pinch
  * there are probably [better alternatives](https://github.com/awesome-selfhosted/awesome-selfhosted) if you have specific/long-term needs
    * but the resumable multithreaded uploads are p slick ngl
* run anywhere, support everything
  * as many web-browsers and python versions as possible
    * every browser should at least be able to browse, download, upload files
    * be a good emergency solution for transferring stuff between ancient boxes
  * minimal dependencies
    * but optional dependencies adding bonus-features are ok
    * everything being plaintext makes it possible to proofread for malicious code
  * no preparations / setup necessary, just run the sfx (which is also plaintext)
* adaptable, malleable, hackable
  * no build steps; modify the js/python without needing node.js or anything like that


## future plans

some improvement ideas

* the JS is a mess -- a preact rewrite would be nice
  * preferably without build dependencies like webpack/babel/node.js, maybe a python thing to assemble js files into main.js
  * good excuse to look at using virtual lists (browsers start to struggle when folders contain over 5000 files)
* the UX is a mess -- a proper design would be nice
  * very organic (much like the python/js), everything was an afterthought
  * true for both the layout and the visual flair
  * something like the tron board-room ui (or most other hollywood ones, like ironman) would be :100:
* some of the python files are way too big
  * `up2k.py` ended up doing all the file indexing / db management
  * `httpcli.py` should be separated into modules in general


# bugs

* Windows: python 2.7 cannot index non-ascii filenames with `-e2d`
* Windows: python 2.7 cannot handle filenames with mojibake
* `--th-ff-jpg` may fix video thumbnails on some FFmpeg versions (macos, some linux)
* `--th-ff-swr` may fix audio thumbnails on some FFmpeg versions

## general bugs

* Windows: if the `up2k.db` (filesystem index) is on a samba-share or network disk, you'll get unpredictable behavior if the share is disconnected for a bit
  * use `--hist` or the `hist` volflag (`-v [...]:c,hist=/tmp/foo`) to place the db on a local disk instead
* all volumes must exist / be available on startup; up2k (mtp especially) gets funky otherwise
* [the database can get stuck](https://github.com/9001/copyparty/issues/10)
  * has only happened once but that is once too many
  * luckily not dangerous for file integrity and doesn't really stop uploads or anything like that
  * but would really appreciate some logs if anyone ever runs into it again
* probably more, pls let me know

## not my bugs

* [Chrome issue 1317069](https://bugs.chromium.org/p/chromium/issues/detail?id=1317069) -- if you try to upload a folder which contains symlinks by dragging it into the browser, the symlinked files will not get uploaded

* [Chrome issue 1354816](https://bugs.chromium.org/p/chromium/issues/detail?id=1354816) -- chrome may eat all RAM uploading over plaintext http with `mt` enabled

  * more amusingly, [Chrome issue 1354800](https://bugs.chromium.org/p/chromium/issues/detail?id=1354800) -- chrome may eat all RAM uploading in general (altho you probably won't run into this one)

* [Chrome issue 1352210](https://bugs.chromium.org/p/chromium/issues/detail?id=1352210) -- plaintext http may be faster at filehashing than https (but also extremely CPU-intensive and likely to run into the above gc bugs)

* [Firefox issue 1790500](https://bugzilla.mozilla.org/show_bug.cgi?id=1790500) -- sometimes forgets to close filedescriptors during upload so the browser can crash after ~4000 files

* iPhones: the volume control doesn't work because [apple doesn't want it to](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/Using_HTML5_Audio_Video/Device-SpecificConsiderations/Device-SpecificConsiderations.html#//apple_ref/doc/uid/TP40009523-CH5-SW11)
  * *future workaround:* enable the equalizer, make it all-zero, and set a negative boost to reduce the volume
    * "future" because `AudioContext` is broken in the current iOS version (15.1), maybe one day...

* Windows: folders cannot be accessed if the name ends with `.`
  * python or windows bug

* Windows: msys2-python 3.8.6 occasionally throws `RuntimeError: release unlocked lock` when leaving a scoped mutex in up2k
  * this is an msys2 bug, the regular windows edition of python is fine

* VirtualBox: sqlite throws `Disk I/O Error` when running in a VM and the up2k database is in a vboxsf
  * use `--hist` or the `hist` volflag (`-v [...]:c,hist=/tmp/foo`) to place the db inside the vm instead

* Ubuntu: dragging files from certain folders into firefox or chrome is impossible
  * due to snap security policies -- see `snap connections firefox` for the allowlist, `removable-media` permits all of `/mnt` and `/media` apparently


# FAQ

"frequently" asked questions

* is it possible to block read-access to folders unless you know the exact URL for a particular file inside?
  * yes, using the [`g` permission](#accounts-and-volumes), see the examples there
  * you can also do this with linux filesystem permissions; `chmod 111 music` will make it possible to access files and folders inside the `music` folder but not list the immediate contents -- also works with other software, not just copyparty

* can I make copyparty download a file to my server if I give it a URL?
  * not really, but there is a [terrible hack](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/wget.py) which makes it possible


# accounts and volumes

per-folder, per-user permissions  - if your setup is getting complex, consider making a [config file](./docs/example.conf) instead of using arguments
* much easier to manage, and you can modify the config at runtime with `systemctl reload copyparty` or more conveniently using the `[reload cfg]` button in the control-panel (if logged in as admin)

a quick summary can be seen using `--help-accounts`

configuring accounts/volumes with arguments:
* `-a usr:pwd` adds account `usr` with password `pwd`
* `-v .::r` adds current-folder `.` as the webroot, `r`eadable by anyone
  * the syntax is `-v src:dst:perm:perm:...` so local-path, url-path, and one or more permissions to set
  * granting the same permissions to multiple accounts:  
    `-v .::r,usr1,usr2:rw,usr3,usr4` = usr1/2 read-only, 3/4 read-write

permissions:
* `r` (read): browse folder contents, download files, download as zip/tar
* `w` (write): upload files, move files *into* this folder
* `m` (move): move files/folders *from* this folder
* `d` (delete): delete files/folders
* `g` (get): only download files, cannot see folder contents or zip/tar
* `G` (upget): same as `g` except uploaders get to see their own filekeys (see `fk` in examples below)

examples:
* add accounts named u1, u2, u3 with passwords p1, p2, p3: `-a u1:p1 -a u2:p2 -a u3:p3`
* make folder `/srv` the root of the filesystem, read-only by anyone: `-v /srv::r`
* make folder `/mnt/music` available at `/music`, read-only for u1 and u2, read-write for u3: `-v /mnt/music:music:r,u1,u2:rw,u3`
  * unauthorized users accessing the webroot can see that the `music` folder exists, but cannot open it
* make folder `/mnt/incoming` available at `/inc`, write-only for u1, read-move for u2: `-v /mnt/incoming:inc:w,u1:rm,u2`
  * unauthorized users accessing the webroot can see that the `inc` folder exists, but cannot open it
  * `u1` can open the `inc` folder, but cannot see the contents, only upload new files to it
  * `u2` can browse it and move files *from* `/inc` into any folder where `u2` has write-access
* make folder `/mnt/ss` available at `/i`, read-write for u1, get-only for everyone else, and enable filekeys: `-v /mnt/ss:i:rw,u1:g:c,fk=4`
  * `c,fk=4` sets the `fk` (filekey) volflag to 4, meaning each file gets a 4-character accesskey
  * `u1` can upload files, browse the folder, and see the generated filekeys
  * other users cannot browse the folder, but can access the files if they have the full file URL with the filekey
  * replacing the `g` permission with `wg` would let anonymous users upload files, but not see the required filekey to access it
  * replacing the `g` permission with `wG` would let anonymous users upload files, receiving a working direct link in return

anyone trying to bruteforce a password gets banned according to `--ban-pw`; default is 24h ban for 9 failed attempts in 1 hour


# the browser

accessing a copyparty server using a web-browser

![copyparty-browser-fs8](https://user-images.githubusercontent.com/241032/192042695-522b3ec7-6845-494a-abdb-d1c0d0e23801.png)


## tabs

the main tabs in the ui
* `[🔎]` [search](#searching) by size, date, path/name, mp3-tags ...
* `[🧯]` [unpost](#unpost): undo/delete accidental uploads
* `[🚀]` and `[🎈]` are the [uploaders](#uploading)
* `[📂]` mkdir: create directories
* `[📝]` new-md: create a new markdown document
* `[📟]` send-msg: either to server-log or into textfiles if `--urlform save`
* `[🎺]` audio-player config options
* `[⚙️]` general client config options


## hotkeys

the browser has the following hotkeys  (always qwerty)
* `B` toggle breadcrumbs / [navpane](#navpane)
* `I/K` prev/next folder
* `M` parent folder (or unexpand current)
* `V` toggle folders / textfiles in the navpane
* `G` toggle list / [grid view](#thumbnails) -- same as `田` bottom-right
* `T` toggle thumbnails / icons
* `ESC` close various things
* `ctrl-X` cut selected files/folders
* `ctrl-V` paste
* `F2` [rename](#batch-rename) selected file/folder
* when a file/folder is selected (in not-grid-view):
  * `Up/Down` move cursor
  * shift+`Up/Down` select and move cursor
  * ctrl+`Up/Down` move cursor and scroll viewport
  * `Space` toggle file selection
  * `Ctrl-A` toggle select all
* when a textfile is open:
  * `I/K` prev/next textfile
  * `S` toggle selection of open file
  * `M` close textfile
* when playing audio:
  * `J/L` prev/next song
  * `U/O` skip 10sec back/forward
  * `0..9` jump to 0%..90%
  * `P` play/pause (also starts playing the folder)
  * `Y` download file
* when viewing images / playing videos:
  * `J/L, Left/Right` prev/next file
  * `Home/End` first/last file
  * `F` toggle fullscreen
  * `S` toggle selection
  * `R` rotate clockwise (shift=ccw)
  * `Y` download file
  * `Esc` close viewer
  * videos:
    * `U/O` skip 10sec back/forward
    * `0..9` jump to 0%..90%
    * `P/K/Space` play/pause
    * `M` mute
    * `C` continue playing next video
    * `V` loop entire file
    * `[` loop range (start)
    * `]` loop range (end)
* when the navpane is open:
  * `A/D` adjust tree width
* in the [grid view](#thumbnails):
  * `S` toggle multiselect
  * shift+`A/D` zoom
* in the markdown editor:
  * `^s` save
  * `^h` header
  * `^k` autoformat table
  * `^u` jump to next unicode character
  * `^e` toggle editor / preview
  * `^up, ^down` jump paragraphs


## navpane

switching between breadcrumbs or navpane

click the `🌲` or pressing the `B` hotkey to toggle between breadcrumbs path (default), or a navpane (tree-browser sidebar thing)

* `[+]` and `[-]` (or hotkeys `A`/`D`) adjust the size
* `[🎯]` jumps to the currently open folder
* `[📃]` toggles between showing folders and textfiles
* `[📌]` shows the name of all parent folders in a docked panel
* `[a]` toggles automatic widening as you go deeper
* `[↵]` toggles wordwrap
* `[👀]` show full name on hover (if wordwrap is off)


## thumbnails

press `g` or `田` to toggle grid-view instead of the file listing  and `t` toggles icons / thumbnails

![copyparty-thumbs-fs8](https://user-images.githubusercontent.com/241032/129636211-abd20fa2-a953-4366-9423-1c88ebb96ba9.png)

it does static images with Pillow / pyvips / FFmpeg, and uses FFmpeg for video files, so you may want to `--no-thumb` or maybe just `--no-vthumb` depending on how dangerous your users are
* pyvips is 3x faster than Pillow, Pillow is 3x faster than FFmpeg
* disable thumbnails for specific volumes with volflag `dthumb` for all, or `dvthumb` / `dathumb` / `dithumb` for video/audio/images only

audio files are covnerted into spectrograms using FFmpeg unless you `--no-athumb` (and some FFmpeg builds may need `--th-ff-swr`)

images with the following names (see `--th-covers`) become the thumbnail of the folder they're in: `folder.png`, `folder.jpg`, `cover.png`, `cover.jpg`

in the grid/thumbnail view, if the audio player panel is open, songs will start playing when clicked
* indicated by the audio files having the ▶ icon instead of 💾


## zip downloads

download folders (or file selections) as `zip` or `tar` files

select which type of archive you want in the `[⚙️] config` tab:

| name | url-suffix | description |
|--|--|--|
| `tar` | `?tar` | plain gnutar, works great with `curl \| tar -xv` |
| `zip` | `?zip=utf8` | works everywhere, glitchy filenames on win7 and older |
| `zip_dos` | `?zip` | traditional cp437 (no unicode) to fix glitchy filenames |
| `zip_crc` | `?zip=crc` | cp437 with crc32 computed early for truly ancient software |

* hidden files (dotfiles) are excluded unless `-ed`
  * `up2k.db` and `dir.txt` is always excluded
* `zip_crc` will take longer to download since the server has to read each file twice
  * this is only to support MS-DOS PKZIP v2.04g (october 1993) and older
    * how are you accessing copyparty actually

you can also zip a selection of files or folders by clicking them in the browser, that brings up a selection editor and zip button in the bottom right

![copyparty-zipsel-fs8](https://user-images.githubusercontent.com/241032/129635374-e5136e01-470a-49b1-a762-848e8a4c9cdc.png)


## uploading

drag files/folders into the web-browser to upload  (or use the [command-line uploader](https://github.com/9001/copyparty/tree/hovudstraum/bin#up2kpy))

this initiates an upload using `up2k`; there are two uploaders available:
* `[🎈] bup`, the basic uploader, supports almost every browser since netscape 4.0
* `[🚀] up2k`, the good / fancy one

NB: you can undo/delete your own uploads with `[🧯]` [unpost](#unpost)

up2k has several advantages:
* you can drop folders into the browser (files are added recursively)
* files are processed in chunks, and each chunk is checksummed
  * uploads autoresume if they are interrupted by network issues
  * uploads resume if you reboot your browser or pc, just upload the same files again
  * server detects any corruption; the client reuploads affected chunks
  * the client doesn't upload anything that already exists on the server
* much higher speeds than ftp/scp/tarpipe on some internet connections (mainly american ones) thanks to parallel connections
* the last-modified timestamp of the file is preserved

see [up2k](#up2k) for details on how it works, or watch a [demo video](https://a.ocv.me/pub/demo/pics-vids/#gf-0f6f5c0d)

![copyparty-upload-fs8](https://user-images.githubusercontent.com/241032/129635371-48fc54ca-fa91-48e3-9b1d-ba413e4b68cb.png)

**protip:** you can avoid scaring away users with [contrib/plugins/minimal-up2k.html](contrib/plugins/minimal-up2k.html) which makes it look [much simpler](https://user-images.githubusercontent.com/241032/118311195-dd6ca380-b4ef-11eb-86f3-75a3ff2e1332.png)

**protip:** if you enable `favicon` in the `[⚙️] settings` tab (by typing something into the textbox), the icon in the browser tab will indicate upload progress -- also, the `[🔔]` and/or `[🔊]` switches enable visible and/or audible notifications on upload completion

the up2k UI is the epitome of polished inutitive experiences:
* "parallel uploads" specifies how many chunks to upload at the same time
* `[🏃]` analysis of other files should continue while one is uploading
* `[🥔]` shows a simpler UI for faster uploads from slow devices
* `[💭]` ask for confirmation before files are added to the queue
* `[🔎]` switch between upload and [file-search](#file-search) mode
  * ignore `[🔎]` if you add files by dragging them into the browser

and then theres the tabs below it,
* `[ok]` is the files which completed successfully
* `[ng]` is the ones that failed / got rejected (already exists, ...)
* `[done]` shows a combined list of `[ok]` and `[ng]`, chronological order
* `[busy]` files which are currently hashing, pending-upload, or uploading
  * plus up to 3 entries each from `[done]` and `[que]` for context
* `[que]` is all the files that are still queued

note that since up2k has to read each file twice, `[🎈] bup` can *theoretically* be up to 2x faster in some extreme cases (files bigger than your ram, combined with an internet connection faster than the read-speed of your HDD, or if you're uploading from a cuo2duo)

if you are resuming a massive upload and want to skip hashing the files which already finished, you can enable `turbo` in the `[⚙️] config` tab, but please read the tooltip on that button


### file-search

dropping files into the browser also lets you see if they exist on the server

![copyparty-fsearch-fs8](https://user-images.githubusercontent.com/241032/129635361-c79286f0-b8f1-440e-aaf4-6e929428fac9.png)

when you drag/drop files into the browser, you will see two dropzones: `Upload` and `Search`

> on a phone? toggle the `[🔎]` switch green before tapping the big yellow Search button to select your files

the files will be hashed on the client-side, and each hash is sent to the server, which checks if that file exists somewhere

files go into `[ok]` if they exist (and you get a link to where it is), otherwise they land in `[ng]`
* the main reason filesearch is combined with the uploader is cause the code was too spaghetti to separate it out somewhere else, this is no longer the case but now i've warmed up to the idea too much


### unpost

undo/delete accidental uploads

![copyparty-unpost-fs8](https://user-images.githubusercontent.com/241032/129635368-3afa6634-c20f-418c-90dc-ec411f3b3897.png)

you can unpost even if you don't have regular move/delete access, however only for files uploaded within the past `--unpost` seconds (default 12 hours) and the server must be running with `-e2d`


### self-destruct

uploads can be given a lifetime,  afer which they expire / self-destruct

the feature must be enabled per-volume with the `lifetime` [upload rule](#upload-rules) which sets the upper limit for how long a file gets to stay on the server

clients can specify a shorter expiration time using the [up2k ui](#uploading) -- the relevant options become visible upon navigating into a folder with `lifetimes` enabled -- or by using the `life` [upload modifier](#write)

specifying a custom expiration time client-side will affect the timespan in which unposts are permitted, so keep an eye on the estimates in the up2k ui


## file manager

cut/paste, rename, and delete files/folders (if you have permission)

file selection: click somewhere on the line (not the link itsef), then:
* `space` to toggle
* `up/down` to move
* `shift-up/down` to move-and-select
* `ctrl-shift-up/down` to also scroll

* cut: select some files and `ctrl-x`
* paste: `ctrl-v` in another folder
* rename: `F2`

you can move files across browser tabs (cut in one tab, paste in another)


## batch rename

select some files and press `F2` to bring up the rename UI

![batch-rename-fs8](https://user-images.githubusercontent.com/241032/128434204-eb136680-3c07-4ec7-92e0-ae86af20c241.png)

quick explanation of the buttons,  
* `[✅ apply rename]` confirms and begins renaming
* `[❌ cancel]` aborts and closes the rename window
* `[↺ reset]` reverts any filename changes back to the original name
* `[decode]` does a URL-decode on the filename, fixing stuff like `&amp;` and `%20`
* `[advanced]` toggles advanced mode

advanced mode: rename files based on rules to decide the new names, based on the original name (regex), or based on the tags collected from the file (artist/title/...), or a mix of both

in advanced mode,  
* `[case]` toggles case-sensitive regex
* `regex` is the regex pattern to apply to the original filename; any files which don't match will be skipped
* `format` is the new filename, taking values from regex capturing groups and/or from file tags
  * very loosely based on foobar2000 syntax
* `presets` lets you save rename rules for later

available functions:
* `$lpad(text, length, pad_char)`
* `$rpad(text, length, pad_char)`

so,

say you have a file named [`meganeko - Eclipse - 07 Sirius A.mp3`](https://www.youtube.com/watch?v=-dtb0vDPruI) (absolutely fantastic album btw) and the tags are: `Album:Eclipse`, `Artist:meganeko`, `Title:Sirius A`, `tn:7`

you could use just regex to rename it:
* `regex` = `(.*) - (.*) - ([0-9]{2}) (.*)`
* `format` = `(3). (1) - (4)`
* `output` = `07. meganeko - Sirius A.mp3`

or you could use just tags:
* `format` = `$lpad((tn),2,0). (artist) - (title).(ext)`
* `output` = `7. meganeko - Sirius A.mp3`

or a mix of both:
* `regex` = ` - ([0-9]{2}) `
* `format` = `(1). (artist) - (title).(ext)`
* `output` = `07. meganeko - Sirius A.mp3`

the metadata keys you can use in the format field are the ones in the file-browser table header (whatever is collected with `-mte` and `-mtp`)


## markdown viewer

and there are *two* editors

![copyparty-md-read-fs8](https://user-images.githubusercontent.com/241032/115978057-66419080-a57d-11eb-8539-d2be843991aa.png)

* the document preview has a max-width which is the same as an A4 paper when printed


## other tricks

* you can link a particular timestamp in an audio file by adding it to the URL, such as `&20` / `&20s` / `&1m20` / `&t=1:20` after the `.../#af-c8960dab`

* enabling the audio equalizer can help make gapless albums fully gapless in some browsers (chrome), so consider leaving it on with all the values at zero

* get a plaintext file listing by adding `?ls=t` to a URL, or a compact colored one with `?ls=v` (for unix terminals)

* if you are using media hotkeys to switch songs and are getting tired of seeing the OSD popup which Windows doesn't let you disable, consider [./contrib/media-osd-bgone.ps1](contrib/#media-osd-bgoneps1)

* click the bottom-left `π` to open a javascript prompt for debugging

* files named `.prologue.html` / `.epilogue.html` will be rendered before/after directory listings unless `--no-logues`

* files named `README.md` / `readme.md` will be rendered after directory listings unless `--no-readme` (but `.epilogue.html` takes precedence)


## searching

search by size, date, path/name, mp3-tags, ...

![copyparty-search-fs8](https://user-images.githubusercontent.com/241032/129635365-c0ff2a9f-0ee5-4fc3-8bb6-006033cf67b8.png)

when started with `-e2dsa` copyparty will scan/index all your files. This avoids duplicates on upload, and also makes the volumes searchable through the web-ui:
* make search queries by `size`/`date`/`directory-path`/`filename`, or...
* drag/drop a local file to see if the same contents exist somewhere on the server, see [file-search](#file-search)

path/name queries are space-separated, AND'ed together, and words are negated with a `-` prefix, so for example:
* path: `shibayan -bossa` finds all files where one of the folders contain `shibayan` but filters out any results where `bossa` exists somewhere in the path
* name: `demetori styx` gives you [good stuff](https://www.youtube.com/watch?v=zGh0g14ZJ8I&list=PL3A147BD151EE5218&index=9)

the `raw` field allows for more complex stuff such as `( tags like *nhato* or tags like *taishi* ) and ( not tags like *nhato* or not tags like *taishi* )` which finds all songs by either nhato or taishi, excluding collabs (terrible example, why would you do that)

for the above example to work, add the commandline argument `-e2ts` to also scan/index tags from music files, which brings us over to:


# server config

using arguments or config files, or a mix of both:
* config files (`-c some.conf`) can set additional commandline arguments; see [./docs/example.conf](docs/example.conf)
* `kill -s USR1` (same as `systemctl reload copyparty`) to reload accounts and volumes from config files without restarting
  * or click the `[reload cfg]` button in the control-panel when logged in as admin 


## qr-code

print a qr-code [(screenshot)](https://user-images.githubusercontent.com/241032/194728533-6f00849b-c6ac-43c6-9359-83e454d11e00.png) for quick access,  great between phones on android hotspots which keep changing the subnet

* `--qr` enables it
* `--qrs` does https instead of http
* `--qrl lootbox/?pw=hunter2` appends to the url, linking to the `lootbox` folder with password `hunter2`
* `--qrz 1` forces 1x zoom instead of autoscaling to fit the terminal size
  * 1x may render incorrectly on some terminals/fonts, but 2x should always work

it will use your external ip (default route) unless `--qri` specifies an ip-prefix or domain


## ftp-server

an FTP server can be started using `--ftp 3921`,  and/or `--ftps` for explicit TLS (ftpes)

* based on [pyftpdlib](https://github.com/giampaolo/pyftpdlib)
* needs a dedicated port (cannot share with the HTTP/HTTPS API)
* uploads are not resumable -- delete and restart if necessary
* runs in active mode by default, you probably want `--ftp-pr 12000-13000`
  * if you enable both `ftp` and `ftps`, the port-range will be divided in half
  * some older software (filezilla on debian-stable) cannot passive-mode with TLS


## file indexing

enables dedup and music search ++

file indexing relies on two database tables, the up2k filetree (`-e2d`) and the metadata tags (`-e2t`), stored in `.hist/up2k.db`. Configuration can be done through arguments, volflags, or a mix of both.

through arguments:
* `-e2d` enables file indexing on upload
* `-e2ds` also scans writable folders for new files on startup
* `-e2dsa` also scans all mounted volumes (including readonly ones)
* `-e2t` enables metadata indexing on upload
* `-e2ts` also scans for tags in all files that don't have tags yet
* `-e2tsr` also deletes all existing tags, doing a full reindex
* `-e2v` verfies file integrity at startup, comparing hashes from the db
* `-e2vu` patches the database with the new hashes from the filesystem
* `-e2vp` panics and kills copyparty instead

the same arguments can be set as volflags, in addition to `d2d`, `d2ds`, `d2t`, `d2ts`, `d2v` for disabling:
* `-v ~/music::r:c,e2dsa,e2tsr` does a full reindex of everything on startup
* `-v ~/music::r:c,d2d` disables **all** indexing, even if any `-e2*` are on
* `-v ~/music::r:c,d2t` disables all `-e2t*` (tags), does not affect `-e2d*`
* `-v ~/music::r:c,d2ds` disables on-boot scans; only index new uploads
* `-v ~/music::r:c,d2ts` same except only affecting tags

note:
* the parser can finally handle `c,e2dsa,e2tsr` so you no longer have to `c,e2dsa:c,e2tsr`
* `e2tsr` is probably always overkill, since `e2ds`/`e2dsa` would pick up any file modifications and `e2ts` would then reindex those, unless there is a new copyparty version with new parsers and the release note says otherwise
* the rescan button in the admin panel has no effect unless the volume has `-e2ds` or higher
* deduplication is possible on windows if you run copyparty as administrator (not saying you should!)

### exclude-patterns

to save some time,  you can provide a regex pattern for filepaths to only index by filename/path/size/last-modified (and not the hash of the file contents) by setting `--no-hash \.iso$` or the volflag `:c,nohash=\.iso$`, this has the following consequences:
* initial indexing is way faster, especially when the volume is on a network disk
* makes it impossible to [file-search](#file-search)
* if someone uploads the same file contents, the upload will not be detected as a dupe, so it will not get symlinked or rejected

similarly, you can fully ignore files/folders using `--no-idx [...]` and `:c,noidx=\.iso$`

if you set `--no-hash [...]` globally, you can enable hashing for specific volumes using flag `:c,nohash=`

### filesystem guards

avoid traversing into other filesystems  using `--xdev` / volflag `:c,xdev`, skipping any symlinks or bind-mounts to another HDD for example

and/or you can `--xvol` / `:c,xvol` to ignore all symlinks leaving the volume's top directory, but still allow bind-mounts pointing elsewhere

**NB: only affects the indexer** -- users can still access anything inside a volume, unless shadowed by another volume

### periodic rescan

filesystem monitoring;  if copyparty is not the only software doing stuff on your filesystem, you may want to enable periodic rescans to keep the index up to date

argument `--re-maxage 60` will rescan all volumes every 60 sec, same as volflag `:c,scan=60` to specify it per-volume

uploads are disabled while a rescan is happening, so rescans will be delayed by `--db-act` (default 10 sec) when there is write-activity going on (uploads, renames, ...)


## upload rules

set upload rules using volflags,  some examples:

* `:c,sz=1k-3m` sets allowed filesize between 1 KiB and 3 MiB inclusive (suffixes: `b`, `k`, `m`, `g`)
* `:c,df=4g` block uploads if there would be less than 4 GiB free disk space afterwards
* `:c,nosub` disallow uploading into subdirectories; goes well with `rotn` and `rotf`:
* `:c,rotn=1000,2` moves uploads into subfolders, up to 1000 files in each folder before making a new one, two levels deep (must be at least 1)
* `:c,rotf=%Y/%m/%d/%H` enforces files to be uploaded into a structure of subfolders according to that date format
  * if someone uploads to `/foo/bar` the path would be rewritten to `/foo/bar/2021/08/06/23` for example
  * but the actual value is not verified, just the structure, so the uploader can choose any values which conform to the format string
    * just to avoid additional complexity in up2k which is enough of a mess already
* `:c,lifetime=300` delete uploaded files when they become 5 minutes old

you can also set transaction limits which apply per-IP and per-volume, but these assume `-j 1` (default) otherwise the limits will be off, for example `-j 4` would allow anywhere between 1x and 4x the limits you set depending on which processing node the client gets routed to

* `:c,maxn=250,3600` allows 250 files over 1 hour from each IP (tracked per-volume)
* `:c,maxb=1g,300` allows 1 GiB total over 5 minutes from each IP (tracked per-volume)


## compress uploads

files can be autocompressed on upload,  either on user-request (if config allows) or forced by server-config

* volflag `gz` allows gz compression
* volflag `xz` allows lzma compression
* volflag `pk` **forces** compression on all files
* url parameter `pk` requests compression with server-default algorithm
* url parameter `gz` or `xz` requests compression with a specific algorithm
* url parameter `xz` requests xz compression

things to note,
* the `gz` and `xz` arguments take a single optional argument, the compression level (range 0 to 9)
* the `pk` volflag takes the optional argument `ALGORITHM,LEVEL` which will then be forced for all uploads, for example `gz,9` or `xz,0`
* default compression is gzip level 9
* all upload methods except up2k are supported
* the files will be indexed after compression, so dupe-detection and file-search will not work as expected

some examples,
* `-v inc:inc:w:c,pk=xz,0`  
  folder named inc, shared at inc, write-only for everyone, forces xz compression at level 0
* `-v inc:inc:w:c,pk`  
  same write-only inc, but forces gz compression (default) instead of xz
* `-v inc:inc:w:c,gz`  
  allows (but does not force) gz compression if client uploads to `/inc?pk` or `/inc?gz` or `/inc?gz=4`


## other flags

* `:c,magic` enables filetype detection for nameless uploads, same as `--magic`


## database location

in-volume (`.hist/up2k.db`, default) or somewhere else

copyparty creates a subfolder named `.hist` inside each volume where it stores the database, thumbnails, and some other stuff

this can instead be kept in a single place using the `--hist` argument, or the `hist=` volflag, or a mix of both:
* `--hist ~/.cache/copyparty -v ~/music::r:c,hist=-` sets `~/.cache/copyparty` as the default place to put volume info, but `~/music` gets the regular `.hist` subfolder (`-` restores default behavior)

note:
* markdown edits are always stored in a local `.hist` subdirectory
* on windows the volflag path is cyglike, so `/c/temp` means `C:\temp` but use regular paths for `--hist`
  * you can use cygpaths for volumes too, `-v C:\Users::r` and `-v /c/users::r` both work


## metadata from audio files

set `-e2t` to index tags on upload

`-mte` decides which tags to index and display in the browser (and also the display order), this can be changed per-volume:
* `-v ~/music::r:c,mte=title,artist` indexes and displays *title* followed by *artist*

if you add/remove a tag from `mte` you will need to run with `-e2tsr` once to rebuild the database, otherwise only new files will be affected

but instead of using `-mte`, `-mth` is a better way to hide tags in the browser: these tags will not be displayed by default, but they still get indexed and become searchable, and users can choose to unhide them in the `[⚙️] config` pane

`-mtm` can be used to add or redefine a metadata mapping, say you have media files with `foo` and `bar` tags and you want them to display as `qux` in the browser (preferring `foo` if both are present), then do `-mtm qux=foo,bar` and now you can `-mte artist,title,qux`

tags that start with a `.` such as `.bpm` and `.dur`(ation) indicate numeric value

see the beautiful mess of a dictionary in [mtag.py](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/mtag.py) for the default mappings (should cover mp3,opus,flac,m4a,wav,aif,)

`--no-mutagen` disables Mutagen and uses FFprobe instead, which...
* is about 20x slower than Mutagen
* catches a few tags that Mutagen doesn't
  * melodic key, video resolution, framerate, pixfmt
* avoids pulling any GPL code into copyparty
* more importantly runs FFprobe on incoming files which is bad if your FFmpeg has a cve

`--mtag-to` sets the tag-scan timeout; very high default (60 sec) to cater for zfs and other randomly-freezing filesystems. Lower values like 10 are usually safe, allowing for faster processing of tricky files


## file parser plugins

provide custom parsers to index additional tags,  also see [./bin/mtag/README.md](./bin/mtag/README.md)

copyparty can invoke external programs to collect additional metadata for files using `mtp` (either as argument or volflag), there is a default timeout of 60sec, and only files which contain audio get analyzed by default (see ay/an/ad below)

* `-mtp .bpm=~/bin/audio-bpm.py` will execute `~/bin/audio-bpm.py` with the audio file as argument 1 to provide the `.bpm` tag, if that does not exist in the audio metadata
* `-mtp key=f,t5,~/bin/audio-key.py` uses `~/bin/audio-key.py` to get the `key` tag, replacing any existing metadata tag (`f,`), aborting if it takes longer than 5sec (`t5,`)
* `-v ~/music::r:c,mtp=.bpm=~/bin/audio-bpm.py:c,mtp=key=f,t5,~/bin/audio-key.py` both as a per-volume config wow this is getting ugly

*but wait, there's more!* `-mtp` can be used for non-audio files as well using the `a` flag: `ay` only do audio files (default), `an` only do non-audio files, or `ad` do all files (d as in dontcare)

* "audio file" also means videos btw, as long as there is an audio stream
* `-mtp ext=an,~/bin/file-ext.py` runs `~/bin/file-ext.py` to get the `ext` tag only if file is not audio (`an`)
* `-mtp arch,built,ver,orig=an,eexe,edll,~/bin/exe.py` runs `~/bin/exe.py` to get properties about windows-binaries only if file is not audio (`an`) and file extension is exe or dll
* if you want to daisychain parsers, use the `p` flag to set processing order
  * `-mtp foo=p1,~/a.py` runs before `-mtp foo=p2,~/b.py` and will forward all the tags detected so far as json to the stdin of b.py
* option `c0` disables capturing of stdout/stderr, so copyparty will not receive any tags from the process at all -- instead the invoked program is free to print whatever to the console, just using copyparty as a launcher
  * `c1` captures stdout only, `c2` only stderr, and `c3` (default) captures both
* you can control how the parser is killed if it times out with option `kt` killing the entire process tree (default), `km` just the main process, or `kn` let it continue running until copyparty is terminated

if something doesn't work, try `--mtag-v` for verbose error messages


## upload events

trigger a script/program on each upload  like so:

```
-v /mnt/inc:inc:w:c,mte=+x1:c,mtp=x1=ad,kn,/usr/bin/notify-send
```

so filesystem location `/mnt/inc` shared at `/inc`, write-only for everyone, appending `x1` to the list of tags to index (`mte`), and using `/usr/bin/notify-send` to "provide" tag `x1` for any filetype (`ad`) with kill-on-timeout disabled (`kn`)

that'll run the command `notify-send` with the path to the uploaded file as the first and only argument (so on linux it'll show a notification on-screen)

note that it will only trigger on new unique files, not dupes

and it will occupy the parsing threads, so fork anything expensive (or set `kn` to have copyparty fork it for you) -- otoh if you want to intentionally queue/singlethread you can combine it with `--mtag-mt 1`

if this becomes popular maybe there should be a less janky way to do it actually


## hiding from google

tell search engines you dont wanna be indexed,  either using the good old [robots.txt](https://www.robotstxt.org/robotstxt.html) or through copyparty settings:

* `--no-robots` adds HTTP (`X-Robots-Tag`) and HTML (`<meta>`) headers with `noindex, nofollow` globally
* volflag `[...]:c,norobots` does the same thing for that single volume
* volflag `[...]:c,robots` ALLOWS search-engine crawling for that volume, even if `--no-robots` is set globally

also, `--force-js` disables the plain HTML folder listing, making things harder to parse for search engines


## themes

you can change the default theme with `--theme 2`, and add your own themes by modifying `browser.css` or providing your own css to `--css-browser`, then telling copyparty they exist by increasing `--themes`

<table><tr><td width="33%" align="center"><a href="https://user-images.githubusercontent.com/241032/165864907-17e2ac7d-319d-4f25-8718-2f376f614b51.png"><img src="https://user-images.githubusercontent.com/241032/165867551-fceb35dd-38f0-42bb-bef3-25ba651ca69b.png"></a>
0. classic dark</td><td width="33%" align="center"><a href="https://user-images.githubusercontent.com/241032/168644399-68938de5-da9b-445f-8d92-b51c74b5f345.png"><img src="https://user-images.githubusercontent.com/241032/168644404-8e1a2fdc-6e59-4c41-905e-ba5399ed686f.png"></a>
2. flat pm-monokai</td><td width="33%" align="center"><a href="https://user-images.githubusercontent.com/241032/165864901-db13a429-a5da-496d-8bc6-ce838547f69d.png"><img src="https://user-images.githubusercontent.com/241032/165867560-aa834aef-58dc-4abe-baef-7e562b647945.png"></a>
4. vice</td></tr><tr><td align="center"><a href="https://user-images.githubusercontent.com/241032/165864905-692682eb-6fb4-4d40-b6fe-27d2c7d3e2a7.png"><img src="https://user-images.githubusercontent.com/241032/165867555-080b73b6-6d85-41bb-a7c6-ad277c608365.png"></a>
1. classic light</td><td align="center"><a href="https://user-images.githubusercontent.com/241032/168645276-fb02fd19-190a-407a-b8d3-d58fee277e02.png"><img src="https://user-images.githubusercontent.com/241032/168645280-f0662b3c-9764-4875-a2e2-d91cc8199b23.png"></a>
3. flat light
</td><td align="center"><a href="https://user-images.githubusercontent.com/241032/165864898-10ce7052-a117-4fcf-845b-b56c91687908.png"><img src="https://user-images.githubusercontent.com/241032/165867562-f3003d45-dd2a-4564-8aae-fed44c1ae064.png"></a>
5. <a href="https://blog.codinghorror.com/a-tribute-to-the-windows-31-hot-dog-stand-color-scheme/">hotdog stand</a></td></tr></table>

the classname of the HTML tag is set according to the selected theme, which is used to set colors as css variables ++

* each theme *generally* has a dark theme (even numbers) and a light theme (odd numbers), showing in pairs
* the first theme (theme 0 and 1) is `html.a`, second theme (2 and 3) is `html.b`
* if a light theme is selected, `html.y` is set, otherwise `html.z` is
* so if the dark edition of the 2nd theme is selected, you use any of `html.b`, `html.z`, `html.bz` to specify rules

see the top of [./copyparty/web/browser.css](./copyparty/web/browser.css) where the color variables are set, and there's layout-specific stuff near the bottom


## complete examples

* read-only music server  
  `python copyparty-sfx.py -v /mnt/nas/music:/music:r -e2dsa -e2ts --no-robots --force-js --theme 2`
  
  * ...with bpm and key scanning  
    `-mtp .bpm=f,audio-bpm.py -mtp key=f,audio-key.py`
  
  * ...with a read-write folder for `kevin` whose password is `okgo`  
    `-a kevin:okgo -v /mnt/nas/inc:/inc:rw,kevin`
  
  * ...with logging to disk  
    `-lo log/cpp-%Y-%m%d-%H%M%S.txt.xz`


# browser support

TLDR: yes

![copyparty-ie4-fs8](https://user-images.githubusercontent.com/241032/118192791-fb31fe00-b446-11eb-9647-898ea8efc1f7.png)

`ie` = internet-explorer, `ff` = firefox, `c` = chrome, `iOS` = iPhone/iPad, `Andr` = Android

| feature         | ie6 | ie9  | ie10 | ie11 | ff 52 | c 49 | iOS | Andr |
| --------------- | --- | ---- | ---- | ---- | ----- | ---- | --- | ---- |
| browse files    | yep | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| thumbnail view  |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| basic uploader  | yep | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| up2k            |  -  |  -   | `*1` | `*1` |  yep  | yep  | yep | yep  |
| make directory  | yep | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| send message    | yep | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| set sort order  |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| zip selection   |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| file rename     |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| file cut/paste  |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| navpane         |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| image viewer    |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| video player    |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| markdown editor |  -  |  -   | yep  | yep  |  yep  | yep  | yep | yep  |
| markdown viewer |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| play mp3/m4a    |  -  | yep  | yep  | yep  |  yep  | yep  | yep | yep  |
| play ogg/opus   |  -  |  -   |  -   |  -   |  yep  | yep  | `*3` | yep |
| **= feature =** | ie6 | ie9  | ie10 | ie11 | ff 52 | c 49 | iOS | Andr |

* internet explorer 6 to 8 behave the same
* firefox 52 and chrome 49 are the final winxp versions
* `*1` yes, but extremely slow (ie10: `1 MiB/s`, ie11: `270 KiB/s`)
* `*3` iOS 11 and newer, opus only, and requires FFmpeg on the server

quick summary of more eccentric web-browsers trying to view a directory index:

| browser | will it blend |
| ------- | ------------- |
| **links** (2.21/macports) | can browse, login, upload/mkdir/msg |
| **lynx** (2.8.9/macports) | can browse, login, upload/mkdir/msg |
| **w3m** (0.5.3/macports)  | can browse, login, upload at 100kB/s, mkdir/msg |
| **netsurf** (3.10/arch)   | is basically ie6 with much better css (javascript has almost no effect) | 
| **opera** (11.60/winxp)   | OK: thumbnails, image-viewer, zip-selection, rename/cut/paste. NG: up2k, navpane, markdown, audio |
| **ie4** and **netscape** 4.0  | can browse, upload with `?b=u`, auth with `&pw=wark` |
| **ncsa mosaic** 2.7       | does not get a pass, [pic1](https://user-images.githubusercontent.com/241032/174189227-ae816026-cf6f-4be5-a26e-1b3b072c1b2f.png) - [pic2](https://user-images.githubusercontent.com/241032/174189225-5651c059-5152-46e9-ac26-7e98e497901b.png) |
| **SerenityOS** (7e98457)  | hits a page fault, works with `?b=u`, file upload not-impl |


# client examples

interact with copyparty using non-browser clients

* javascript: dump some state into a file (two separate examples)
  * `await fetch('//127.0.0.1:3923/', {method:"PUT", body: JSON.stringify(foo)});`
  * `var xhr = new XMLHttpRequest(); xhr.open('POST', '//127.0.0.1:3923/msgs?raw'); xhr.send('foo');`

* curl/wget: upload some files (post=file, chunk=stdin)
  * `post(){ curl -F act=bput -F f=@"$1" http://127.0.0.1:3923/?pw=wark;}`  
    `post movie.mkv`
  * `post(){ curl -b cppwd=wark -H rand:8 -T "$1" http://127.0.0.1:3923/;}`  
    `post movie.mkv`
  * `post(){ wget --header='Cookie: cppwd=wark' --post-file="$1" -O- http://127.0.0.1:3923/?raw;}`  
    `post movie.mkv`
  * `chunk(){ curl -b cppwd=wark -T- http://127.0.0.1:3923/;}`  
    `chunk <movie.mkv`

* bash: when curl and wget is not available or too boring
  * `(printf 'PUT /junk?pw=wark HTTP/1.1\r\n\r\n'; cat movie.mkv) | nc 127.0.0.1 3923`
  * `(printf 'PUT / HTTP/1.1\r\n\r\n'; cat movie.mkv) >/dev/tcp/127.0.0.1/3923`

* python: [up2k.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) is a command-line up2k client [(webm)](https://ocv.me/stuff/u2cli.webm)
  * file uploads, file-search, autoresume of aborted/broken uploads
  * see [./bin/README.md#up2kpy](bin/README.md#up2kpy)

* FUSE: mount a copyparty server as a local filesystem
  * cross-platform python client available in [./bin/](bin/)
  * [rclone](https://rclone.org/) as client can give ~5x performance, see [./docs/rclone.md](docs/rclone.md)

* sharex (screenshot utility): see [./contrib/sharex.sxcu](contrib/#sharexsxcu)

copyparty returns a truncated sha512sum of your PUT/POST as base64; you can generate the same checksum locally to verify uplaods:

    b512(){ printf "$((sha512sum||shasum -a512)|sed -E 's/ .*//;s/(..)/\\x\1/g')"|base64|tr '+/' '-_'|head -c44;}
    b512 <movie.mkv

you can provide passwords using cookie `cppwd=hunter2`, as a url-param `?pw=hunter2`, or with basic-authentication (either as the username or password)

NOTE: curl will not send the original filename if you use `-T` combined with url-params! Also, make sure to always leave a trailing slash in URLs unless you want to override the filename


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

up2k has saved a few uploads from becoming corrupted in-transfer already;
* caught an android phone on wifi redhanded in wireshark with a bitflip, however bup with https would *probably* have noticed as well (thanks to tls also functioning as an integrity check)
* also stopped someone from uploading because their ram was bad

regarding the frequent server log message during uploads;  
`6.0M 106M/s 2.77G 102.9M/s n948 thank 4/0/3/1 10042/7198 00:01:09`
* this chunk was `6 MiB`, uploaded at `106 MiB/s`
* on this http connection, `2.77 GiB` transferred, `102.9 MiB/s` average, `948` chunks handled
* client says `4` uploads OK, `0` failed, `3` busy, `1` queued, `10042 MiB` total size, `7198 MiB` and `00:01:09` left


## why chunk-hashes

a single sha512 would be better, right?

this is due to `crypto.subtle` [not yet](https://github.com/w3c/webcrypto/issues/73) providing a streaming api (or the option to seed the sha512 hasher with a starting hash)

as a result, the hashes are much less useful than they could have been (search the server by sha512, provide the sha512 in the response http headers, ...)

however it allows for hashing multiple chunks in parallel, greatly increasing upload speed from fast storage (NVMe, raid-0 and such)

* both the [browser uploader](#uploading) and the [commandline one](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) does this now, allowing for fast uploading even from plaintext http

hashwasm would solve the streaming issue but reduces hashing speed for sha512 (xxh128 does 6 GiB/s), and it would make old browsers and [iphones](https://bugs.webkit.org/show_bug.cgi?id=228552) unsupported

* blake2 might be a better choice since xxh is non-cryptographic, but that gets ~15 MiB/s on slower androids


# performance

defaults are usually fine - expect `8 GiB/s` download, `1 GiB/s` upload

below are some tweaks roughly ordered by usefulness:

* `-q` disables logging and can help a bunch, even when combined with `-lo` to redirect logs to file
* `--http-only` or `--https-only` (unless you want to support both protocols) will reduce the delay before a new connection is established
* `--hist` pointing to a fast location (ssd) will make directory listings and searches faster when `-e2d` or `-e2t` is set
* `--no-hash .` when indexing a network-disk if you don't care about the actual filehashes and only want the names/tags searchable
* `--no-htp --hash-mt=0 --th-mt=1` minimizes the number of threads; can help in some eccentric environments (like the vscode debugger)
* `-j` enables multiprocessing (actual multithreading) and can make copyparty perform better in cpu-intensive workloads, for example:
  * huge amount of short-lived connections
  * really heavy traffic (downloads/uploads)
  
  ...however it adds an overhead to internal communication so it might be a net loss, see if it works 4 u


## client-side

when uploading files,

* chrome is recommended, at least compared to firefox:
  * up to 90% faster when hashing, especially on SSDs
  * up to 40% faster when uploading over extremely fast internets
  * but [up2k.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) can be 40% faster than chrome again

* if you're cpu-bottlenecked, or the browser is maxing a cpu core:
  * up to 30% faster uploads if you hide the upload status list by switching away from the `[🚀]` up2k ui-tab (or closing it)
    * optionally you can switch to the lightweight potato ui by clicking the `[🥔]`
    * switching to another browser-tab also works, the favicon will update every 10 seconds in that case
  * unlikely to be a problem, but can happen when uploding many small files, or your internet is too fast, or PC too slow


# security

some notes on hardening

* option `-s` is a shortcut to set the following options:
  * `--no-thumb` disables thumbnails and audio transcoding to stop copyparty from running `FFmpeg`/`Pillow`/`VIPS` on uploaded files, which is a [good idea](https://www.cvedetails.com/vulnerability-list.php?vendor_id=3611) if anonymous upload is enabled
  * `--no-mtag-ff` uses `mutagen` to grab music tags instead of `FFmpeg`, which is safer and faster but less accurate
  * `--dotpart` hides uploads from directory listings while they're still incoming
  * `--no-robots` and `--force-js` makes life harder for crawlers, see [hiding from google](#hiding-from-google)

* option `-ss` is a shortcut for the above plus:
  * `--no-logues` and `--no-readme` disables support for readme's and prologues / epilogues in directory listings, which otherwise lets people upload arbitrary `<script>` tags
  * `--unpost 0`, `--no-del`, `--no-mv` disables all move/delete support
  * `--hardlink` creates hardlinks instead of symlinks when deduplicating uploads, which is less maintenance
    * however note if you edit one file it will also affect the other copies
  * `--vague-403` returns a "404 not found" instead of "403 forbidden" which is a common enterprise meme
  * `--ban-404=50,60,1440` ban client for 1440min (24h) if they hit 50 404's in 60min
    * **NB:** will ban anyone who enables up2k turbo
  * `--nih` removes the server hostname from directory listings

* option `-sss` is a shortcut for the above plus:
  * `-lo cpp-%Y-%m%d-%H%M%S.txt.xz` enables logging to disk
  * `-ls **,*,ln,p,r` does a scan on startup for any dangerous symlinks

other misc notes:

* you can disable directory listings by giving permission `g` instead of `r`, only accepting direct URLs to files
  * combine this with volflag `c,fk` to generate filekeys (per-file accesskeys); users which have full read-access will then see URLs with `?k=...` appended to the end, and `g` users must provide that URL including the correct key to avoid a 404
  * permissions `wG` lets users upload files and receive their own filekeys, still without being able to see other uploads


## gotchas

behavior that might be unexpected

* users without read-access to a folder can still see the `.prologue.html` / `.epilogue.html` / `README.md` contents, for the purpose of showing a description on how to use the uploader for example


# recovering from crashes

## client crashes

### frefox wsod

firefox 87 can crash during uploads  -- the entire browser goes, including all other browser tabs, everything turns white

however you can hit `F12` in the up2k tab and use the devtools to see how far you got in the uploads:

* get a complete list of all uploads, organized by statuts (ok / no-good / busy / queued):  
  `var tabs = { ok:[], ng:[], bz:[], q:[] }; for (var a of up2k.ui.tab) tabs[a.in].push(a); tabs`

* list of filenames which failed:  
  `​var ng = []; for (var a of up2k.ui.tab) if (a.in != 'ok') ng.push(a.hn.split('<a href=\"').slice(-1)[0].split('\">')[0]); ng`

* send the list of filenames to copyparty for safekeeping:  
  `await fetch('/inc', {method:'PUT', body:JSON.stringify(ng,null,1)})`


# HTTP API

* table-column `params` = URL parameters; `?foo=bar&qux=...`
* table-column `body` = POST payload
* method `jPOST` = json post
* method `mPOST` = multipart post
* method `uPOST` = url-encoded post
* `FILE` = conventional HTTP file upload entry (rfc1867 et al, filename in `Content-Disposition`)

authenticate using header `Cookie: cppwd=foo` or url param `&pw=foo`

## read

| method | params | result |
|--|--|--|
| GET | `?ls` | list files/folders at URL as JSON |
| GET | `?ls&dots` | list files/folders at URL as JSON, including dotfiles |
| GET | `?ls=t` | list files/folders at URL as plaintext |
| GET | `?ls=v` | list files/folders at URL, terminal-formatted |
| GET | `?b` | list files/folders at URL as simplified HTML |
| GET | `?tree=.` | list one level of subdirectories inside URL |
| GET | `?tree` | list one level of subdirectories for each level until URL |
| GET | `?tar` | download everything below URL as a tar file |
| GET | `?zip=utf-8` | download everything below URL as a zip file |
| GET | `?ups` | show recent uploads from your IP |
| GET | `?ups&filter=f` | ...where URL contains `f` |
| GET | `?mime=foo` | specify return mimetype `foo` |
| GET | `?raw` | get markdown file at URL as plaintext |
| GET | `?txt` | get file at URL as plaintext |
| GET | `?txt=iso-8859-1` | ...with specific charset |
| GET | `?th` | get image/video at URL as thumbnail |
| GET | `?th=opus` | convert audio file to 128kbps opus |
| GET | `?th=caf` | ...in the iOS-proprietary container |

| method | body | result |
|--|--|--|
| jPOST | `{"q":"foo"}` | do a server-wide search; see the `[🔎]` search tab `raw` field for syntax |

| method | params | body | result |
|--|--|--|--|
| jPOST | `?tar` | `["foo","bar"]` | download folders `foo` and `bar` inside URL as a tar file |

## write

| method | params | result |
|--|--|--|
| GET | `?move=/foo/bar` | move/rename the file/folder at URL to /foo/bar |

| method | params | body | result |
|--|--|--|--|
| PUT | | (binary data) | upload into file at URL |
| PUT | `?gz` | (binary data) | compress with gzip and write into file at URL |
| PUT | `?xz` | (binary data) | compress with xz and write into file at URL |
| mPOST | | `act=bput`, `f=FILE` | upload `FILE` into the folder at URL |
| mPOST | `?j` | `act=bput`, `f=FILE` | ...and reply with json |
| mPOST | | `act=mkdir`, `name=foo` | create directory `foo` at URL |
| GET | `?delete` | | delete URL recursively |
| jPOST | `?delete` | `["/foo","/bar"]` | delete `/foo` and `/bar` recursively |
| uPOST | | `msg=foo` | send message `foo` into server log |
| mPOST | | `act=tput`, `body=TEXT` | overwrite markdown document at URL |

upload modifiers:

| http-header | url-param | effect |
|--|--|--|
| `Accept: url` | `want=url` | return just the file URL |
| `Rand: 4` | `rand=4` | generate random filename with 4 characters |
| `Life: 30` | `life=30` | delete file after 30 seconds |

* `life` only has an effect if the volume has a lifetime, and the volume lifetime must be greater than the file's

* server behavior of `msg` can be reconfigured with `--urlform`

## admin

| method | params | result |
|--|--|--|
| GET | `?reload=cfg` | reload config files and rescan volumes |
| GET | `?scan` | initiate a rescan of the volume which provides URL |
| GET | `?stack` | show a stacktrace of all threads |

## general

| method | params | result |
|--|--|--|
| GET | `?pw=x` | logout |


# dependencies

mandatory deps:
* `jinja2` (is built into the SFX)


## optional dependencies

install these to enable bonus features

enable ftp-server:
* for just plaintext FTP, `pyftpdlib` (is built into the SFX)
* with TLS encryption, `pyftpdlib pyopenssl`

enable music tags:
* either `mutagen` (fast, pure-python, skips a few tags, makes copyparty GPL? idk)
* or `ffprobe` (20x slower, more accurate, possibly dangerous depending on your distro and users)

enable [thumbnails](#thumbnails) of...
* **images:** `Pillow` and/or `pyvips` and/or `ffmpeg` (requires py2.7 or py3.5+)
* **videos/audio:** `ffmpeg` and `ffprobe` somewhere in `$PATH`
* **HEIF pictures:** `pyvips` or `ffmpeg` or `pyheif-pillow-opener` (requires Linux or a C compiler)
* **AVIF pictures:** `pyvips` or `ffmpeg` or `pillow-avif-plugin`
* **JPEG XL pictures:** `pyvips` or `ffmpeg`

`pyvips` gives higher quality thumbnails than `Pillow` and is 320% faster, using 270% more ram: `sudo apt install libvips42 && python3 -m pip install --user -U pyvips`


## install recommended deps
```
python -m pip install --user -U jinja2 mutagen Pillow
```


## optional gpl stuff

some bundled tools have copyleft dependencies, see [./bin/#mtag](bin/#mtag)

these are standalone programs and will never be imported / evaluated by copyparty, and must be enabled through `-mtp` configs


# sfx

the self-contained "binary"  [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) will unpack itself and run copyparty, assuming you have python installed of course


## sfx repack

reduce the size of an sfx by removing features

if you don't need all the features, you can repack the sfx and save a bunch of space; all you need is an sfx and a copy of this repo (nothing else to download or build, except if you're on windows then you need msys2 or WSL)
* `393k` size of original sfx.py as of v1.1.3
* `310k` after `./scripts/make-sfx.sh re no-cm`
* `269k` after `./scripts/make-sfx.sh re no-cm no-hl`

the features you can opt to drop are
* `cm`/easymde, the "fancy" markdown editor, saves ~82k
* `hl`, prism, the syntax hilighter, saves ~41k
* `fnt`, source-code-pro, the monospace font, saves ~9k
* `dd`, the custom mouse cursor for the media player tray tab, saves ~2k

for the `re`pack to work, first run one of the sfx'es once to unpack it

**note:** you can also just download and run [scripts/copyparty-repack.sh](scripts/copyparty-repack.sh) -- this will grab the latest copyparty release from github and do a few repacks; works on linux/macos (and windows with msys2 or WSL)


## copyparty.exe

![copyparty-exe-fs8](https://user-images.githubusercontent.com/241032/194707422-cb7f66c9-41a2-4cb9-8dbc-2ab866cd4338.png)

[copyparty.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty.exe) can be convenient on old machines where installing python is problematic, however is **not recommended** and should be considered a last resort -- if possible, please use **[copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py)** instead

the exe is compatible with 32bit windows7, which means it uses an ancient copy of python (3.7.9) which cannot be upgraded and will definitely become a security hazard at some point

meanwhile [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) instead relies on your system python which gives better performance and will stay safe as long as you keep your python install up-to-date

then again, if you are already into downloading shady binaries from the internet, you may also want my [minimal builds](./scripts/pyinstaller#ffmpeg) of [ffmpeg](https://ocv.me/stuff/bin/ffmpeg.exe) and [ffprobe](https://ocv.me/stuff/bin/ffprobe.exe) which enables copyparty to extract multimedia-info, do audio-transcoding, and thumbnails/spectrograms/waveforms, however it's much better to instead grab a [recent official build](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) every once ina while if you can afford the size


# install on android

install [Termux](https://termux.com/) (see [ocv.me/termux](https://ocv.me/termux/)) and then copy-paste this into Termux (long-tap) all at once:
```sh
apt update && apt -y full-upgrade && apt update && termux-setup-storage && apt -y install python && python -m ensurepip && python -m pip install --user -U copyparty
echo $?
```

after the initial setup, you can launch copyparty at any time by running `copyparty` anywhere in Termux -- and if you run it with `--qr` you'll get a [neat qr-code](#qr-code) pointing to your external ip

if you want thumbnails, `apt -y install ffmpeg`

* or if you want to use vips instead, `apt -y install libvips && python -m pip install --user -U wheel && python -m pip install --user -U pyvips && (cd /data/data/com.termux/files/usr/lib/; ln -s libgobject-2.0.so{,.0}; ln -s libvips.so{,.42})`


# reporting bugs

ideas for context to include in bug reports

in general, commandline arguments (and config file if any)

if something broke during an upload (replacing FILENAME with a part of the filename that broke):
```
journalctl -aS '48 hour ago' -u copyparty | grep -C10 FILENAME | tee bug.log
```

if there's a wall of base64 in the log (thread stacks) then please include that, especially if you run into something freezing up or getting stuck, for example `OperationalError('database is locked')` -- alternatively you can visit `/?stack` to see the stacks live, so http://127.0.0.1:3923/?stack for example


# building

## dev env setup

you need python 3.9 or newer due to type hints

the rest is mostly optional; if you need a working env for vscode or similar

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install jinja2 strip_hints  # MANDATORY
pip install mutagen  # audio metadata
pip install pyftpdlib  # ftp server
pip install Pillow pyheif-pillow-opener pillow-avif-plugin  # thumbnails
pip install black==21.12b0 click==8.0.2 bandit pylint flake8 isort mypy  # vscode tooling
```


## just the sfx

first grab the web-dependencies from a previous sfx (assuming you don't need to modify something in those):

```sh
rm -rf copyparty/web/deps
curl -L https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py >x.py
python3 x.py -h
rm x.py
mv /tmp/pe-copyparty/copyparty/web/deps/ copyparty/web/deps/
```

then build the sfx using any of the following examples:

```sh
./scripts/make-sfx.sh           # regular edition
./scripts/make-sfx.sh gz no-cm  # gzip-compressed + no fancy markdown editor
```


## complete release

also builds the sfx so skip the sfx section above

in the `scripts` folder:

* run `make -C deps-docker` to build all dependencies
* run `./rls.sh 1.2.3` which uploads to pypi + creates github release + sfx


# todo

roughly sorted by priority

* nothing! currently


## discarded ideas

* reduce up2k roundtrips
  * start from a chunk index and just go
  * terminate client on bad data
    * not worth the effort, just throw enough conncetions at it
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
  * too dangerous -- overtaken by turbo mode
* comment field
  * nah
* look into android thumbnail cache file format
  * absolutely not
* indexedDB for hashes, cfg enable/clear/sz, 2gb avail, ~9k for 1g, ~4k for 100m, 500k items before autoeviction
  * blank hashlist when up-ok to skip handshake
    * too many confusing side-effects
* hls framework for Someone Else to drop code into :^)
  * probably not, too much stuff to consider -- seeking, start at offset, task stitching (probably np-hard), conditional passthru, rate-control (especially multi-consumer), session keepalive, cache mgmt...

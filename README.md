# 💾🎉 copyparty

turn almost any device into a file server with resumable uploads/downloads using [*any*](#browser-support) web browser

* server only needs Python (2 or 3), all dependencies optional
* 🔌 protocols: [http](#the-browser) // [ftp](#ftp-server) // [webdav](#webdav-server) // [smb/cifs](#smb-server)
* 📱 [android app](#android-app) // [iPhone shortcuts](#ios-shortcuts)

👉 **[Get started](#quickstart)!** or visit the **[read-only demo server](https://a.ocv.me/pub/demo/)** 👀 running from a basement in finland

📷 **screenshots:** [browser](#the-browser) // [upload](#uploading) // [unpost](#unpost) // [thumbnails](#thumbnails) // [search](#searching) // [fsearch](#file-search) // [zip-DL](#zip-downloads) // [md-viewer](#markdown-viewer)


## readme toc

* top
    * [quickstart](#quickstart) - just run **[copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py)** -- that's it! 🎉
        * [on servers](#on-servers) - you may also want these, especially on servers
    * [features](#features)
    * [testimonials](#testimonials) - small collection of user feedback
* [motivations](#motivations) - project goals / philosophy
    * [notes](#notes) - general notes
* [bugs](#bugs) - roughly sorted by chance of encounter
    * [not my bugs](#not-my-bugs) - same order here too
* [breaking changes](#breaking-changes) - upgrade notes
* [FAQ](#FAQ) - "frequently" asked questions
* [accounts and volumes](#accounts-and-volumes) - per-folder, per-user permissions
    * [shadowing](#shadowing) - hiding specific subfolders
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
    * [media player](#media-player) - plays almost every audio format there is
        * [audio equalizer](#audio-equalizer) - and [dynamic range compressor](https://en.wikipedia.org/wiki/Dynamic_range_compression)
        * [fix unreliable playback on android](#fix-unreliable-playback-on-android) - due to phone / app settings
    * [markdown viewer](#markdown-viewer) - and there are *two* editors
    * [other tricks](#other-tricks)
    * [searching](#searching) - search by size, date, path/name, mp3-tags, ...
* [server config](#server-config) - using arguments or config files, or a mix of both
    * [zeroconf](#zeroconf) - announce enabled services on the LAN ([pic](https://user-images.githubusercontent.com/241032/215344737-0eae8d98-9496-4256-9aa8-cd2f6971810d.png))
        * [mdns](#mdns) - LAN domain-name and feature announcer
        * [ssdp](#ssdp) - windows-explorer announcer
    * [qr-code](#qr-code) - print a qr-code [(screenshot)](https://user-images.githubusercontent.com/241032/194728533-6f00849b-c6ac-43c6-9359-83e454d11e00.png) for quick access
    * [ftp server](#ftp-server) - an FTP server can be started using `--ftp 3921`
    * [webdav server](#webdav-server) - with read-write support
        * [connecting to webdav from windows](#connecting-to-webdav-from-windows) - using the GUI
    * [smb server](#smb-server) - unsafe, slow, not recommended for wan
    * [browser ux](#browser-ux) - tweaking the ui
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
    * [event hooks](#event-hooks) - trigger a program on uploads, renames etc ([examples](./bin/hooks/))
        * [upload events](#upload-events) - the older, more powerful approach ([examples](./bin/mtag/))
    * [handlers](#handlers) - redefine behavior with plugins ([examples](./bin/handlers/))
    * [hiding from google](#hiding-from-google) - tell search engines you dont wanna be indexed
    * [themes](#themes)
    * [complete examples](#complete-examples)
    * [reverse-proxy](#reverse-proxy) - running copyparty next to other websites
    * [prometheus](#prometheus) - metrics/stats can be enabled
* [packages](#packages) - the party might be closer than you think
    * [arch package](#arch-package) - now [available on aur](https://aur.archlinux.org/packages/copyparty) maintained by [@icxes](https://github.com/icxes)
    * [fedora package](#fedora-package) - now [available on copr-pypi](https://copr.fedorainfracloud.org/coprs/g/copr/PyPI/)
    * [nix package](#nix-package) - `nix profile install github:9001/copyparty`
    * [nixos module](#nixos-module)
* [browser support](#browser-support) - TLDR: yes
* [client examples](#client-examples) - interact with copyparty using non-browser clients
    * [folder sync](#folder-sync) - sync folders to/from copyparty
    * [mount as drive](#mount-as-drive) - a remote copyparty server as a local filesystem
* [android app](#android-app) - upload to copyparty with one tap
* [iOS shortcuts](#iOS-shortcuts) - there is no iPhone app, but
* [performance](#performance) - defaults are usually fine - expect `8 GiB/s` download, `1 GiB/s` upload
    * [client-side](#client-side) - when uploading files
* [security](#security) - there is a [discord server](https://discord.gg/25J8CdTT6G)
    * [gotchas](#gotchas) - behavior that might be unexpected
    * [cors](#cors) - cross-site request config
    * [filekeys](#filekeys) - prevent filename bruteforcing
    * [password hashing](#password-hashing) - you can hash passwords
    * [https](#https) - both HTTP and HTTPS are accepted
* [recovering from crashes](#recovering-from-crashes)
    * [client crashes](#client-crashes)
        * [frefox wsod](#frefox-wsod) - firefox 87 can crash during uploads
* [HTTP API](#HTTP-API) - see [devnotes](./docs/devnotes.md#http-api)
* [dependencies](#dependencies) - mandatory deps
    * [optional dependencies](#optional-dependencies) - install these to enable bonus features
    * [optional gpl stuff](#optional-gpl-stuff)
* [sfx](#sfx) - the self-contained "binary"
    * [copyparty.exe](#copypartyexe) - download [copyparty.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty.exe) (win8+) or [copyparty32.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty32.exe) (win7+)
* [install on android](#install-on-android)
* [reporting bugs](#reporting-bugs) - ideas for context to include in bug reports
* [devnotes](#devnotes) - for build instructions etc, see [./docs/devnotes.md](./docs/devnotes.md)


## quickstart

just run **[copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py)** -- that's it! 🎉

* or install through pypi: `python3 -m pip install --user -U copyparty`
* or if you cannot install python, you can use [copyparty.exe](#copypartyexe) instead
* or install [on arch](#arch-package) ╱ [on fedora](#fedora-package) ╱ [on NixOS](#nixos-module) ╱ [through nix](#nix-package)
* or if you are on android, [install copyparty in termux](#install-on-android)
* or if you prefer to [use docker](./scripts/docker/) 🐋 you can do that too
  * docker has all deps built-in, so skip this step:

enable thumbnails (images/audio/video), media indexing, and audio transcoding by installing some recommended deps:

* **Alpine:** `apk add py3-pillow ffmpeg`
* **Debian:** `apt install --no-install-recommends python3-pil ffmpeg`
* **Fedora:** rpmfusion + `dnf install python3-pillow ffmpeg`
* **FreeBSD:** `pkg install py39-sqlite3 py39-pillow ffmpeg`
* **MacOS:** `port install py-Pillow ffmpeg`
* **MacOS** (alternative): `brew install pillow ffmpeg`
* **Windows:** `python -m pip install --user -U Pillow`
  * install python and ffmpeg manually; do not use `winget` or `Microsoft Store` (it breaks $PATH)
  * copyparty.exe comes with `Pillow` and only needs `ffmpeg`
* see [optional dependencies](#optional-dependencies) to enable even more features

running copyparty without arguments (for example doubleclicking it on Windows) will give everyone read/write access to the current folder; you may want [accounts and volumes](#accounts-and-volumes)

or see [some usage examples](#complete-examples) for inspiration, or the [complete windows example](./docs/examples/windows.md)

some recommended options:
* `-e2dsa` enables general [file indexing](#file-indexing)
* `-e2ts` enables audio metadata indexing (needs either FFprobe or Mutagen)
* `-v /mnt/music:/music:r:rw,foo -a foo:bar` shares `/mnt/music` as `/music`, `r`eadable by anyone, and read-write for user `foo`, password `bar`
  * replace `:r:rw,foo` with `:r,foo` to only make the folder readable by `foo` and nobody else
  * see [accounts and volumes](#accounts-and-volumes) (or `--help-accounts`) for the syntax and other permissions


### on servers

you may also want these, especially on servers:

* [contrib/systemd/copyparty.service](contrib/systemd/copyparty.service) to run copyparty as a systemd service (see guide inside)
* [contrib/systemd/prisonparty.service](contrib/systemd/prisonparty.service) to run it in a chroot (for extra security)
* [contrib/rc/copyparty](contrib/rc/copyparty) to run copyparty on FreeBSD
* [contrib/nginx/copyparty.conf](contrib/nginx/copyparty.conf) to [reverse-proxy](#reverse-proxy) behind nginx (for better https)
* [nixos module](#nixos-module) to run copyparty on NixOS hosts

and remember to open the ports you want; here's a complete example including every feature copyparty has to offer:
```
firewall-cmd --permanent --add-port={80,443,3921,3923,3945,3990}/tcp  # --zone=libvirt
firewall-cmd --permanent --add-port=12000-12099/tcp --permanent  # --zone=libvirt
firewall-cmd --permanent --add-port={1900,5353}/udp  # --zone=libvirt
firewall-cmd --reload
```
(1900:ssdp, 3921:ftp, 3923:http/https, 3945:smb, 3990:ftps, 5353:mdns, 12000:passive-ftp)


## features

* backend stuff
  * ☑ IPv6
  * ☑ [multiprocessing](#performance) (actual multithreading)
  * ☑ volumes (mountpoints)
  * ☑ [accounts](#accounts-and-volumes)
  * ☑ [ftp server](#ftp-server)
  * ☑ [webdav server](#webdav-server)
  * ☑ [smb/cifs server](#smb-server)
  * ☑ [qr-code](#qr-code) for quick access
  * ☑ [upnp / zeroconf / mdns / ssdp](#zeroconf)
  * ☑ [event hooks](#event-hooks) / script runner
  * ☑ [reverse-proxy support](https://github.com/9001/copyparty#reverse-proxy)
* upload
  * ☑ basic: plain multipart, ie6 support
  * ☑ [up2k](#uploading): js, resumable, multithreaded
    * unaffected by cloudflare's max-upload-size (100 MiB)
  * ☑ stash: simple PUT filedropper
  * ☑ filename randomizer
  * ☑ write-only folders
  * ☑ [unpost](#unpost): undo/delete accidental uploads
  * ☑ [self-destruct](#self-destruct) (specified server-side or client-side)
  * ☑ symlink/discard duplicates (content-matching)
* download
  * ☑ single files in browser
  * ☑ [folders as zip / tar files](#zip-downloads)
  * ☑ [FUSE client](https://github.com/9001/copyparty/tree/hovudstraum/bin#partyfusepy) (read-only)
* browser
  * ☑ [navpane](#navpane) (directory tree sidebar)
  * ☑ file manager (cut/paste, delete, [batch-rename](#batch-rename))
  * ☑ audio player (with [OS media controls](https://user-images.githubusercontent.com/241032/215347492-b4250797-6c90-4e09-9a4c-721edf2fb15c.png) and opus transcoding)
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
* client support
  * ☑ [folder sync](#folder-sync)
  * ☑ [curl-friendly](https://user-images.githubusercontent.com/241032/215322619-ea5fd606-3654-40ad-94ee-2bc058647bb2.png)
* markdown
  * ☑ [viewer](#markdown-viewer)
  * ☑ editor (sure why not)

PS: something missing? post any crazy ideas you've got as a [feature request](https://github.com/9001/copyparty/issues/new?assignees=9001&labels=enhancement&template=feature_request.md) or [discussion](https://github.com/9001/copyparty/discussions/new?category=ideas) 🤙


## testimonials

small collection of user feedback

`good enough`, `surprisingly correct`, `certified good software`, `just works`, `why`, `wow this is better than nextcloud`


# motivations

project goals / philosophy

* inverse linux philosophy -- do all the things, and do an *okay* job
  * quick drop-in service to get a lot of features in a pinch
  * some of [the alternatives](./docs/versus.md) might be a better fit for you
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


## notes

general notes:
* paper-printing is affected by dark/light-mode! use lightmode for color, darkmode for grayscale
  * because no browsers currently implement the media-query to do this properly orz

browser-specific:
* iPhone/iPad: use Firefox to download files
* Android-Chrome: increase "parallel uploads" for higher speed (android bug)
* Android-Firefox: takes a while to select files (their fix for ☝️)
* Desktop-Firefox: ~~may use gigabytes of RAM if your files are massive~~ *seems to be OK now*
* Desktop-Firefox: [may stop you from unplugging USB flashdrives](https://bugzilla.mozilla.org/show_bug.cgi?id=1792598) until you visit `about:memory` and click `Minimize memory usage`

server-os-specific:
* RHEL8 / Rocky8: you can run copyparty using `/usr/libexec/platform-python`

server notes:
* pypy is supported but regular cpython is faster if you enable the database


# bugs

roughly sorted by chance of encounter

* general:
  * `--th-ff-jpg` may fix video thumbnails on some FFmpeg versions (macos, some linux)
  * `--th-ff-swr` may fix audio thumbnails on some FFmpeg versions
  * if the `up2k.db` (filesystem index) is on a samba-share or network disk, you'll get unpredictable behavior if the share is disconnected for a bit
    * use `--hist` or the `hist` volflag (`-v [...]:c,hist=/tmp/foo`) to place the db on a local disk instead
  * all volumes must exist / be available on startup; up2k (mtp especially) gets funky otherwise
  * probably more, pls let me know

* python 3.4 and older (including 2.7):
  * many rare and exciting edge-cases because [python didn't handle EINTR yet](https://peps.python.org/pep-0475/)
    * downloads from copyparty may suddenly fail, but uploads *should* be fine

* python 2.7 on Windows:
  * cannot index non-ascii filenames with `-e2d`
  * cannot handle filenames with mojibake

## not my bugs

same order here too

* [Chrome issue 1317069](https://bugs.chromium.org/p/chromium/issues/detail?id=1317069) -- if you try to upload a folder which contains symlinks by dragging it into the browser, the symlinked files will not get uploaded

* [Chrome issue 1352210](https://bugs.chromium.org/p/chromium/issues/detail?id=1352210) -- plaintext http may be faster at filehashing than https (but also extremely CPU-intensive)

* [Firefox issue 1790500](https://bugzilla.mozilla.org/show_bug.cgi?id=1790500) -- entire browser can crash after uploading ~4000 small files

* Android: music playback randomly stops due to [battery usage settings](#fix-unreliable-playback-on-android)

* iPhones: the volume control doesn't work because [apple doesn't want it to](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/Using_HTML5_Audio_Video/Device-SpecificConsiderations/Device-SpecificConsiderations.html#//apple_ref/doc/uid/TP40009523-CH5-SW11)
  * `AudioContext` will probably never be a viable workaround as apple introduces new issues faster than they fix current ones

* iPhones: the preload feature (in the media-player-options tab) can cause a tiny audio glitch 20sec before the end of each song, but disabling it may cause worse iOS bugs to appear instead
  * just a hunch, but disabling preloading may cause playback to stop entirely, or possibly mess with bluetooth speakers
  * tried to add a tooltip regarding this but looks like apple broke my tooltips

* Windows: folders cannot be accessed if the name ends with `.`
  * python or windows bug

* Windows: msys2-python 3.8.6 occasionally throws `RuntimeError: release unlocked lock` when leaving a scoped mutex in up2k
  * this is an msys2 bug, the regular windows edition of python is fine

* VirtualBox: sqlite throws `Disk I/O Error` when running in a VM and the up2k database is in a vboxsf
  * use `--hist` or the `hist` volflag (`-v [...]:c,hist=/tmp/foo`) to place the db inside the vm instead
  * also happens on mergerfs, so put the db elsewhere

* Ubuntu: dragging files from certain folders into firefox or chrome is impossible
  * due to snap security policies -- see `snap connections firefox` for the allowlist, `removable-media` permits all of `/mnt` and `/media` apparently


# breaking changes

upgrade notes

* `1.9.16` (2023-11-04):
  * `--stats`/prometheus: `cpp_bans` renamed to `cpp_active_bans`, and that + `cpp_uptime` are gauges
* `1.6.0` (2023-01-29):
  * http-api: delete/move is now `POST` instead of `GET`
  * everything other than `GET` and `HEAD` must pass [cors validation](#cors)
* `1.5.0` (2022-12-03): [new chunksize formula](https://github.com/9001/copyparty/commit/54e1c8d261df) for files larger than 128 GiB
  * **users:** upgrade to the latest [cli uploader](https://github.com/9001/copyparty/blob/hovudstraum/bin/u2c.py) if you use that
  * **devs:** update third-party up2k clients (if those even exist)


# FAQ

"frequently" asked questions

* is it possible to block read-access to folders unless you know the exact URL for a particular file inside?
  * yes, using the [`g` permission](#accounts-and-volumes), see the examples there
  * you can also do this with linux filesystem permissions; `chmod 111 music` will make it possible to access files and folders inside the `music` folder but not list the immediate contents -- also works with other software, not just copyparty

* can I make copyparty download a file to my server if I give it a URL?
  * yes, using [hooks](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/wget.py)

* i want to learn python and/or programming and am considering looking at the copyparty source code in that occasion
    ```bash
     _|  _      __   _  _|_
    (_| (_)     | | (_)  |_
    ```


# accounts and volumes

per-folder, per-user permissions  - if your setup is getting complex, consider making a [config file](./docs/example.conf) instead of using arguments
* much easier to manage, and you can modify the config at runtime with `systemctl reload copyparty` or more conveniently using the `[reload cfg]` button in the control-panel (if the user has `a`/admin in any volume)
  * changes to the `[global]` config section requires a restart to take effect

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
* `G` (upget): same as `g` except uploaders get to see their own [filekeys](#filekeys) (see `fk` in examples below)
* `h` (html): same as `g` except folders return their index.html, and filekeys are not necessary for index.html
* `a` (admin): can see upload time, uploader IPs, config-reload

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
  * `c,fk=4` sets the `fk` ([filekey](#filekeys)) volflag to 4, meaning each file gets a 4-character accesskey
  * `u1` can upload files, browse the folder, and see the generated filekeys
  * other users cannot browse the folder, but can access the files if they have the full file URL with the filekey
  * replacing the `g` permission with `wg` would let anonymous users upload files, but not see the required filekey to access it
  * replacing the `g` permission with `wG` would let anonymous users upload files, receiving a working direct link in return

anyone trying to bruteforce a password gets banned according to `--ban-pw`; default is 24h ban for 9 failed attempts in 1 hour


## shadowing

hiding specific subfolders  by mounting another volume on top of them

for example `-v /mnt::r -v /var/empty:web/certs:r` mounts the server folder `/mnt` as the webroot, but another volume is mounted at `/web/certs` -- so visitors can only see the contents of `/mnt` and `/mnt/web` (at URLs `/` and `/web`), but not `/mnt/web/certs` because URL `/web/certs` is mapped to `/var/empty`


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
* `?` show hotkeys help
* `B` toggle breadcrumbs / [navpane](#navpane)
* `I/K` prev/next folder
* `M` parent folder (or unexpand current)
* `V` toggle folders / textfiles in the navpane
* `G` toggle list / [grid view](#thumbnails) -- same as `田` bottom-right
* `T` toggle thumbnails / icons
* `ESC` close various things
* `ctrl-K` delete selected files/folders
* `ctrl-X` cut selected files/folders
* `ctrl-V` paste
* `Y` download selected files
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
* can be made default globally with `--grid` or per-volume with volflag `grid`

![copyparty-thumbs-fs8](https://user-images.githubusercontent.com/241032/129636211-abd20fa2-a953-4366-9423-1c88ebb96ba9.png)

it does static images with Pillow / pyvips / FFmpeg, and uses FFmpeg for video files, so you may want to `--no-thumb` or maybe just `--no-vthumb` depending on how dangerous your users are
* pyvips is 3x faster than Pillow, Pillow is 3x faster than FFmpeg
* disable thumbnails for specific volumes with volflag `dthumb` for all, or `dvthumb` / `dathumb` / `dithumb` for video/audio/images only

audio files are covnerted into spectrograms using FFmpeg unless you `--no-athumb` (and some FFmpeg builds may need `--th-ff-swr`)

images with the following names (see `--th-covers`) become the thumbnail of the folder they're in: `folder.png`, `folder.jpg`, `cover.png`, `cover.jpg`
* and, if you enable [file indexing](#file-indexing), all remaining folders will also get thumbnails (as long as they contain any pics at all)

in the grid/thumbnail view, if the audio player panel is open, songs will start playing when clicked
* indicated by the audio files having the ▶ icon instead of 💾

enabling `multiselect` lets you click files to select them, and then shift-click another file for range-select
* `multiselect` is mostly intended for phones/tablets, but the `sel` option in the `[⚙️] settings` tab is better suited for desktop use, allowing selection by CTRL-clicking and range-selection with SHIFT-click, all without affecting regular clicking


## zip downloads

download folders (or file selections) as `zip` or `tar` files

select which type of archive you want in the `[⚙️] config` tab:

| name | url-suffix | description |
|--|--|--|
| `tar` | `?tar` | plain gnutar, works great with `curl \| tar -xv` |
| `pax` | `?tar=pax` | pax-format tar, futureproof, not as fast |
| `tgz` | `?tar=gz` | gzip compressed gnu-tar (slow), for `curl \| tar -xvz` |
| `txz` | `?tar=xz` | gnu-tar with xz / lzma compression (v.slow) |
| `zip` | `?zip=utf8` | works everywhere, glitchy filenames on win7 and older |
| `zip_dos` | `?zip` | traditional cp437 (no unicode) to fix glitchy filenames |
| `zip_crc` | `?zip=crc` | cp437 with crc32 computed early for truly ancient software |

* gzip default level is `3` (0=fast, 9=best), change with `?tar=gz:9`
* xz default level is `1` (0=fast, 9=best), change with `?tar=xz:9`
* bz2 default level is `2` (1=fast, 9=best), change with `?tar=bz2:9`
* hidden files (dotfiles) are excluded unless `-ed`
  * `up2k.db` and `dir.txt` is always excluded
* bsdtar supports streaming unzipping: `curl foo?zip=utf8 | bsdtar -xv`
  * good, because copyparty's zip is faster than tar on small files
* `zip_crc` will take longer to download since the server has to read each file twice
  * this is only to support MS-DOS PKZIP v2.04g (october 1993) and older
    * how are you accessing copyparty actually

you can also zip a selection of files or folders by clicking them in the browser, that brings up a selection editor and zip button in the bottom right

![copyparty-zipsel-fs8](https://user-images.githubusercontent.com/241032/129635374-e5136e01-470a-49b1-a762-848e8a4c9cdc.png)

cool trick: download a folder by appending url-params `?tar&opus` to transcode all audio files (except aac|m4a|mp3|ogg|opus|wma) to opus before they're added to the archive
* super useful if you're 5 minutes away from takeoff and realize you don't have any music on your phone but your server only has flac files and downloading those will burn through all your data + there wouldn't be enough time anyways
* and url-params `&j` / `&w` produce jpeg/webm thumbnails/spectrograms instead of the original audio/video/images
  * can also be used to pregenerate thumbnails; combine with `--th-maxage=9999999` or `--th-clean=0`


## uploading

drag files/folders into the web-browser to upload  (or use the [command-line uploader](https://github.com/9001/copyparty/tree/hovudstraum/bin#u2cpy))

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

> it is perfectly safe to restart / upgrade copyparty while someone is uploading to it!  
> all known up2k clients will resume just fine 💪

see [up2k](#up2k) for details on how it works, or watch a [demo video](https://a.ocv.me/pub/demo/pics-vids/#gf-0f6f5c0d)

![copyparty-upload-fs8](https://user-images.githubusercontent.com/241032/129635371-48fc54ca-fa91-48e3-9b1d-ba413e4b68cb.png)

**protip:** you can avoid scaring away users with [contrib/plugins/minimal-up2k.js](contrib/plugins/minimal-up2k.js) which makes it look [much simpler](https://user-images.githubusercontent.com/241032/118311195-dd6ca380-b4ef-11eb-86f3-75a3ff2e1332.png)

**protip:** if you enable `favicon` in the `[⚙️] settings` tab (by typing something into the textbox), the icon in the browser tab will indicate upload progress -- also, the `[🔔]` and/or `[🔊]` switches enable visible and/or audible notifications on upload completion

the up2k UI is the epitome of polished inutitive experiences:
* "parallel uploads" specifies how many chunks to upload at the same time
* `[🏃]` analysis of other files should continue while one is uploading
* `[🥔]` shows a simpler UI for faster uploads from slow devices
* `[🎲]` generate random filenames during upload
* `[📅]` preserve last-modified timestamps; server times will match yours
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
* shift-click another line for range-select

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


## media player

plays almost every audio format there is  (if the server has FFmpeg installed for on-demand transcoding)

the following audio formats are usually always playable, even without FFmpeg: `aac|flac|m4a|mp3|ogg|opus|wav`

some hilights:
* OS integration; control playback from your phone's lockscreen ([windows](https://user-images.githubusercontent.com/241032/233213022-298a98ba-721a-4cf1-a3d4-f62634bc53d5.png) // [iOS](https://user-images.githubusercontent.com/241032/142711926-0700be6c-3e31-47b3-9928-53722221f722.png) // [android](https://user-images.githubusercontent.com/241032/233212311-a7368590-08c7-4f9f-a1af-48ccf3f36fad.png))
* shows the audio waveform in the seekbar
* not perfectly gapless but can get really close (see settings + eq below); good enough to enjoy gapless albums as intended

click the `play` link next to an audio file, or copy the link target to [share it](https://a.ocv.me/pub/demo/music/Ubiktune%20-%20SOUNDSHOCK%202%20-%20FM%20FUNK%20TERRROR!!/#af-1fbfba61&t=18) (optionally with a timestamp to start playing from, like that example does)

open the `[🎺]` media-player-settings tab to configure it,
* switches:
  * `[preload]` starts loading the next track when it's about to end, reduces the silence between songs
  * `[full]` does a full preload by downloading the entire next file; good for unreliable connections, bad for slow connections
  * `[~s]` toggles the seekbar waveform display
  * `[/np]` enables buttons to copy the now-playing info as an irc message
  * `[os-ctl]` makes it possible to control audio playback from the lockscreen of your device (enables [mediasession](https://developer.mozilla.org/en-US/docs/Web/API/MediaSession))
  * `[seek]` allows seeking with lockscreen controls (buggy on some devices)
  * `[art]` shows album art on the lockscreen
  * `[🎯]` keeps the playing song scrolled into view (good when using the player as a taskbar dock)
  * `[⟎]` shrinks the playback controls
* playback mode:
  * `[loop]` keeps looping the folder
  * `[next]` plays into the next folder
* transcode:
  * `[flac]` converts `flac` and `wav` files into opus
  * `[aac]` converts `aac` and `m4a` files into opus
  * `[oth]` converts all other known formats into opus
    * `aac|ac3|aif|aiff|alac|alaw|amr|ape|au|dfpwm|dts|flac|gsm|it|m4a|mo3|mod|mp2|mp3|mpc|mptm|mt2|mulaw|ogg|okt|opus|ra|s3m|tak|tta|ulaw|wav|wma|wv|xm|xpk`
* "tint" reduces the contrast of the playback bar


### audio equalizer

and [dynamic range compressor](https://en.wikipedia.org/wiki/Dynamic_range_compression)

can also boost the volume in general, or increase/decrease stereo width (like [crossfeed](https://www.foobar2000.org/components/view/foo_dsp_meiercf) just worse)

has the convenient side-effect of reducing the pause between songs, so gapless albums play better with the eq enabled (just make it flat)

not available on iPhones / iPads because AudioContext currently breaks background audio playback on iOS (15.7.8)


### fix unreliable playback on android

due to phone / app settings,  android phones may randomly stop playing music when the power saver kicks in, especially at the end of an album -- you can fix it by [disabling power saving](https://user-images.githubusercontent.com/241032/235262123-c328cca9-3930-4948-bd18-3949b9fd3fcf.png) in the [app settings](https://user-images.githubusercontent.com/241032/235262121-2ffc51ae-7821-4310-a322-c3b7a507890c.png) of the browser you use for music streaming (preferably a dedicated one)


## markdown viewer

and there are *two* editors

![copyparty-md-read-fs8](https://user-images.githubusercontent.com/241032/115978057-66419080-a57d-11eb-8539-d2be843991aa.png)

there is a built-in extension for inline clickable thumbnails;
* enable it by adding `<!-- th -->` somewhere in the doc
* add thumbnails with `!th[l](your.jpg)` where `l` means left-align (`r` = right-align)
* a single line with `---` clears the float / inlining
* in the case of README.md being displayed below a file listing, thumbnails will open in the gallery viewer

other notes,
* the document preview has a max-width which is the same as an A4 paper when printed


## other tricks

* you can link a particular timestamp in an audio file by adding it to the URL, such as `&20` / `&20s` / `&1m20` / `&t=1:20` after the `.../#af-c8960dab`

* enabling the audio equalizer can help make gapless albums fully gapless in some browsers (chrome), so consider leaving it on with all the values at zero

* get a plaintext file listing by adding `?ls=t` to a URL, or a compact colored one with `?ls=v` (for unix terminals)

* if you are using media hotkeys to switch songs and are getting tired of seeing the OSD popup which Windows doesn't let you disable, consider [./contrib/media-osd-bgone.ps1](contrib/#media-osd-bgoneps1)

* click the bottom-left `π` to open a javascript prompt for debugging

* files named `.prologue.html` / `.epilogue.html` will be rendered before/after directory listings unless `--no-logues`

* files named `README.md` / `readme.md` will be rendered after directory listings unless `--no-readme` (but `.epilogue.html` takes precedence)

* `README.md` and `*logue.html` can contain placeholder values which are replaced server-side before embedding into directory listings; see `--help-exp`


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
* config files (`-c some.conf`) can set additional commandline arguments; see [./docs/example.conf](docs/example.conf) and [./docs/example2.conf](docs/example2.conf)
* `kill -s USR1` (same as `systemctl reload copyparty`) to reload accounts and volumes from config files without restarting
  * or click the `[reload cfg]` button in the control-panel if the user has `a`/admin in any volume
  * changes to the `[global]` config section requires a restart to take effect


## zeroconf

announce enabled services on the LAN ([pic](https://user-images.githubusercontent.com/241032/215344737-0eae8d98-9496-4256-9aa8-cd2f6971810d.png))  -- `-z` enables both [mdns](#mdns) and [ssdp](#ssdp)

* `--z-on` / `--z-off`' limits the feature to certain networks


### mdns

LAN domain-name and feature announcer

uses [multicast dns](https://en.wikipedia.org/wiki/Multicast_DNS) to give copyparty a domain which any machine on the LAN can use to access it

all enabled services ([webdav](#webdav-server), [ftp](#ftp-server), [smb](#smb-server)) will appear in mDNS-aware file managers (KDE, gnome, macOS, ...)

the domain will be http://partybox.local if the machine's hostname is `partybox` unless `--name` specifies soemthing else


### ssdp

windows-explorer announcer

uses [ssdp](https://en.wikipedia.org/wiki/Simple_Service_Discovery_Protocol) to make copyparty appear in the windows file explorer on all machines on the LAN

doubleclicking the icon opens the "connect" page which explains how to mount copyparty as a local filesystem

if copyparty does not appear in windows explorer, use `--zsv` to see why:

* maybe the discovery multicast was sent from an IP which does not intersect with the server subnets


## qr-code

print a qr-code [(screenshot)](https://user-images.githubusercontent.com/241032/194728533-6f00849b-c6ac-43c6-9359-83e454d11e00.png) for quick access,  great between phones on android hotspots which keep changing the subnet

* `--qr` enables it
* `--qrs` does https instead of http
* `--qrl lootbox/?pw=hunter2` appends to the url, linking to the `lootbox` folder with password `hunter2`
* `--qrz 1` forces 1x zoom instead of autoscaling to fit the terminal size
  * 1x may render incorrectly on some terminals/fonts, but 2x should always work

it uses the server hostname if [mdns](#mdns) is enbled, otherwise it'll use your external ip (default route) unless `--qri` specifies a specific ip-prefix or domain


## ftp server

an FTP server can be started using `--ftp 3921`,  and/or `--ftps` for explicit TLS (ftpes)

* based on [pyftpdlib](https://github.com/giampaolo/pyftpdlib)
* needs a dedicated port (cannot share with the HTTP/HTTPS API)
* uploads are not resumable -- delete and restart if necessary
* runs in active mode by default, you probably want `--ftp-pr 12000-13000`
  * if you enable both `ftp` and `ftps`, the port-range will be divided in half
  * some older software (filezilla on debian-stable) cannot passive-mode with TLS
* login with any username + your password, or put your password in the username field

some recommended FTP / FTPS clients; `wark` = example password:
* https://winscp.net/eng/download.php
* https://filezilla-project.org/ struggles a bit with ftps in active-mode, but is fine otherwise
* https://rclone.org/ does FTPS with `tls=false explicit_tls=true`
* `lftp -u k,wark -p 3921 127.0.0.1 -e ls`
* `lftp -u k,wark -p 3990 127.0.0.1 -e 'set ssl:verify-certificate no; ls'`


## webdav server

with read-write support,  supports winXP and later, macos, nautilus/gvfs

click the [connect](http://127.0.0.1:3923/?hc) button in the control-panel to see connection instructions for windows, linux, macos

general usage:
* login with any username + your password, or put your password in the username field (password field can be empty/whatever)

on macos, connect from finder:
* [Go] -> [Connect to Server...] -> http://192.168.123.1:3923/

in order to grant full write-access to webdav clients, the volflag `daw` must be set and the account must also have delete-access (otherwise the client won't be allowed to replace the contents of existing files, which is how webdav works)


### connecting to webdav from windows

using the GUI  (winXP or later):
* rightclick [my computer] -> [map network drive] -> Folder: `http://192.168.123.1:3923/`
  * on winXP only, click the `Sign up for online storage` hyperlink instead and put the URL there
  * providing your password as the username is recommended; the password field can be anything or empty

known client bugs:
* win7+ doesn't actually send the password to the server when reauthenticating after a reboot unless you first try to login with an incorrect password and then switch to the correct password
  * or just type your password into the username field instead to get around it entirely
* connecting to a folder which allows anonymous read will make writing impossible, as windows has decided it doesn't need to login
  * workaround: connect twice; first to a folder which requires auth, then to the folder you actually want, and leave both of those mounted
* win7+ may open a new tcp connection for every file and sometimes forgets to close them, eventually needing a reboot
  * maybe NIC-related (??), happens with win10-ltsc on e1000e but not virtio
* windows cannot access folders which contain filenames with invalid unicode or forbidden characters (`<>:"/\|?*`), or names ending with `.`
* winxp cannot show unicode characters outside of *some range*
  * latin-1 is fine, hiragana is not (not even as shift-jis on japanese xp)


## smb server

unsafe, slow, not recommended for wan,  enable with `--smb` for read-only or `--smbw` for read-write

click the [connect](http://127.0.0.1:3923/?hc) button in the control-panel to see connection instructions for windows, linux, macos

dependencies: `python3 -m pip install --user -U impacket==0.11.0`
* newer versions of impacket will hopefully work just fine but there is monkeypatching so maybe not

some **BIG WARNINGS** specific to SMB/CIFS, in decreasing importance:
* not entirely confident that read-only is read-only
* the smb backend is not fully integrated with vfs, meaning there could be security issues (path traversal). Please use `--smb-port` (see below) and [prisonparty](./bin/prisonparty.sh)
  * account passwords work per-volume as expected, and so does account permissions (read/write/move/delete), but `--smbw` must be given to allow write-access from smb
  * [shadowing](#shadowing) probably works as expected but no guarantees

and some minor issues,
* clients only see the first ~400 files in big folders; [impacket#1433](https://github.com/SecureAuthCorp/impacket/issues/1433)
* hot-reload of server config (`/?reload=cfg`) does not include the `[global]` section (commandline args)
* listens on the first IPv4 `-i` interface only (default = :: = 0.0.0.0 = all)
* login doesn't work on winxp, but anonymous access is ok -- remove all accounts from copyparty config for that to work
  * win10 onwards does not allow connecting anonymously / without accounts
* on windows, creating a new file through rightclick --> new --> textfile throws an error due to impacket limitations -- hit OK and F5 to get your file
* python3 only
* slow (the builtin webdav support in windows is 5x faster, and rclone-webdav is 30x faster)

known client bugs:
* on win7 only, `--smb1` is much faster than smb2 (default) because it keeps rescanning folders on smb2
  * however smb1 is buggy and is not enabled by default on win10 onwards
* windows cannot access folders which contain filenames with invalid unicode or forbidden characters (`<>:"/\|?*`), or names ending with `.`

the smb protocol listens on TCP port 445, which is a privileged port on linux and macos, which would require running copyparty as root. However, this can be avoided by listening on another port using `--smb-port 3945` and then using NAT to forward the traffic from 445 to there;
* on linux: `iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 445 -j REDIRECT --to-port 3945`

authenticate with one of the following:
* username `$username`, password `$password`
* username `$password`, password `k`


## browser ux

tweaking the ui

* set default sort order globally with `--sort` or per-volume with the `sort` volflag; specify one or more comma-separated columns to sort by, and prefix the column name with `-` for reverse sort
  * the column names you can use are visible as tooltips when hovering over the column headers in the directory listing, for example `href ext sz ts tags/.up_at tags/Cirle tags/.tn tags/Artist tags/Title`
  * to sort in music order (album, track, artist, title) with filename as fallback, you could `--sort tags/Cirle,tags/.tn,tags/Artist,tags/Title,href`
  * to sort by upload date, first enable showing the upload date in the listing with `-e2d -mte +.up_at` and then `--sort tags/.up_at`


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
* `--xlink` enables deduplication across volumes

the same arguments can be set as volflags, in addition to `d2d`, `d2ds`, `d2t`, `d2ts`, `d2v` for disabling:
* `-v ~/music::r:c,e2ds,e2tsr` does a full reindex of everything on startup
* `-v ~/music::r:c,d2d` disables **all** indexing, even if any `-e2*` are on
* `-v ~/music::r:c,d2t` disables all `-e2t*` (tags), does not affect `-e2d*`
* `-v ~/music::r:c,d2ds` disables on-boot scans; only index new uploads
* `-v ~/music::r:c,d2ts` same except only affecting tags

note:
* upload-times can be displayed in the file listing by enabling the `.up_at` metadata key, either globally with `-e2d -mte +.up_at` or per-volume with volflags `e2d,mte=+.up_at` (will have a ~17% performance impact on directory listings)
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

* symlinks are permitted with `xvol` if they point into another volume where the user has the same level of access

these options will reduce performance; unlikely worst-case estimates are 14% reduction for directory listings, 35% for download-as-tar

as of copyparty v1.7.0 these options also prevent file access at runtime -- in previous versions it was just hints for the indexer

### periodic rescan

filesystem monitoring;  if copyparty is not the only software doing stuff on your filesystem, you may want to enable periodic rescans to keep the index up to date

argument `--re-maxage 60` will rescan all volumes every 60 sec, same as volflag `:c,scan=60` to specify it per-volume

uploads are disabled while a rescan is happening, so rescans will be delayed by `--db-act` (default 10 sec) when there is write-activity going on (uploads, renames, ...)


## upload rules

set upload rules using volflags,  some examples:

* `:c,sz=1k-3m` sets allowed filesize between 1 KiB and 3 MiB inclusive (suffixes: `b`, `k`, `m`, `g`)
* `:c,df=4g` block uploads if there would be less than 4 GiB free disk space afterwards
* `:c,vmaxb=1g` block uploads if total volume size would exceed 1 GiB afterwards
* `:c,vmaxn=4k` block uploads if volume would contain more than 4096 files afterwards
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

notes:
* `vmaxb` and `vmaxn` requires either the `e2ds` volflag or `-e2dsa` global-option


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
  * needs https://pypi.org/project/python-magic/ `python3 -m pip install --user -U python-magic`
  * on windows grab this instead `python3 -m pip install --user -U python-magic-bin`


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


## event hooks

trigger a program on uploads, renames etc ([examples](./bin/hooks/))

you can set hooks before and/or after an event happens, and currently you can hook uploads, moves/renames, and deletes

there's a bunch of flags and stuff, see `--help-hooks`


### upload events

the older, more powerful approach ([examples](./bin/mtag/)):

```
-v /mnt/inc:inc:w:c,mte=+x1:c,mtp=x1=ad,kn,/usr/bin/notify-send
```

so filesystem location `/mnt/inc` shared at `/inc`, write-only for everyone, appending `x1` to the list of tags to index (`mte`), and using `/usr/bin/notify-send` to "provide" tag `x1` for any filetype (`ad`) with kill-on-timeout disabled (`kn`)

that'll run the command `notify-send` with the path to the uploaded file as the first and only argument (so on linux it'll show a notification on-screen)

note that this is way more complicated than the new [event hooks](#event-hooks) but this approach has the following advantages:
* non-blocking and multithreaded; doesn't hold other uploads back
* you get access to tags from FFmpeg and other mtp parsers
* only trigger on new unique files, not dupes

note that it will occupy the parsing threads, so fork anything expensive (or set `kn` to have copyparty fork it for you) -- otoh if you want to intentionally queue/singlethread you can combine it with `--mtag-mt 1`


## handlers

redefine behavior with plugins ([examples](./bin/handlers/))

replace 404 and 403 errors with something completely different (that's it for now)


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

* see [running on windows](./docs/examples/windows.md) for a fancy windows setup

  * or use any of the examples below, just replace `python copyparty-sfx.py` with `copyparty.exe` if you're using the exe edition

* allow anyone to download or upload files into the current folder:  
  `python copyparty-sfx.py`

  * enable searching and music indexing with `-e2dsa -e2ts`

  * start an FTP server on port 3921 with `--ftp 3921`

  * announce it on your LAN with `-z` so it appears in windows/Linux file managers

* anyone can upload, but nobody can see any files (even the uploader):  
  `python copyparty-sfx.py -e2dsa -v .::w`

  * block uploads if there's less than 4 GiB free disk space with `--df 4`

  * show a popup on new uploads with `--xau bin/hooks/notify.py`

* anyone can upload, and receive "secret" links for each upload they do:  
  `python copyparty-sfx.py -e2dsa -v .::wG:c,fk=8`

* anyone can browse, only `kevin` (password `okgo`) can upload/move/delete files:  
  `python copyparty-sfx.py -e2dsa -a kevin:okgo -v .::r:rwmd,kevin`

* read-only music server:  
  `python copyparty-sfx.py -v /mnt/nas/music:/music:r -e2dsa -e2ts --no-robots --force-js --theme 2`
  
  * ...with bpm and key scanning  
    `-mtp .bpm=f,audio-bpm.py -mtp key=f,audio-key.py`
  
  * ...with a read-write folder for `kevin` whose password is `okgo`  
    `-a kevin:okgo -v /mnt/nas/inc:/inc:rw,kevin`
  
  * ...with logging to disk  
    `-lo log/cpp-%Y-%m%d-%H%M%S.txt.xz`


## reverse-proxy

running copyparty next to other websites  hosted on an existing webserver such as nginx, caddy, or apache

you can either:
* give copyparty its own domain or subdomain (recommended)
* or do location-based proxying, using `--rp-loc=/stuff` to tell copyparty where it is mounted -- has a slight performance cost and higher chance of bugs
  * if copyparty says `incorrect --rp-loc or webserver config; expected vpath starting with [...]` it's likely because the webserver is stripping away the proxy location from the request URLs -- see the `ProxyPass` in the apache example below

some reverse proxies (such as [Caddy](https://caddyserver.com/)) can automatically obtain a valid https/tls certificate for you, and some support HTTP/2 and QUIC which could be a nice speed boost
* **warning:** nginx-QUIC is still experimental and can make uploads much slower, so HTTP/2 is recommended for now

example webserver configs:

* [nginx config](contrib/nginx/copyparty.conf) -- entire domain/subdomain
* [apache2 config](contrib/apache/copyparty.conf) -- location-based


## prometheus

metrics/stats can be enabled  at URL `/.cpr/metrics` for grafana / prometheus / etc (openmetrics 1.0.0)

must be enabled with `--stats` since it reduces startup time a tiny bit, and you probably want `-e2dsa` too

the endpoint is only accessible by `admin` accounts, meaning the `a` in `rwmda` in the following example commandline: `python3 -m copyparty -a ed:wark -v /mnt/nas::rwmda,ed --stats -e2dsa`

follow a guide for setting up `node_exporter` except have it read from copyparty instead; example `/etc/prometheus/prometheus.yml` below

```yaml
scrape_configs:
  - job_name: copyparty
    metrics_path: /.cpr/metrics
    basic_auth:
      password: wark
    static_configs:
      - targets: ['192.168.123.1:3923']
```

currently the following metrics are available,
* `cpp_uptime_seconds` time since last copyparty restart
* `cpp_boot_unixtime_seconds` same but as an absolute timestamp
* `cpp_http_conns` number of open http(s) connections
* `cpp_http_reqs` number of http(s) requests handled
* `cpp_sus_reqs` number of 403/422/malicious requests
* `cpp_active_bans` number of currently banned IPs
* `cpp_total_bans` number of IPs banned since last restart

these are available unless `--nos-vst` is specified:
* `cpp_db_idle_seconds` time since last database activity (upload/rename/delete)
* `cpp_db_act_seconds` same but as an absolute timestamp
* `cpp_idle_vols` number of volumes which are idle / ready
* `cpp_busy_vols` number of volumes which are busy / indexing
* `cpp_offline_vols` number of volumes which are offline / unavailable
* `cpp_hashing_files` number of files queued for hashing / indexing
* `cpp_tagq_files` number of files queued for metadata scanning
* `cpp_mtpq_files` number of files queued for plugin-based analysis

and these are available per-volume only:
* `cpp_disk_size_bytes` total HDD size
* `cpp_disk_free_bytes` free HDD space

and these are per-volume and `total`:
* `cpp_vol_bytes` size of all files in volume
* `cpp_vol_files` number of files
* `cpp_dupe_bytes` disk space presumably saved by deduplication
* `cpp_dupe_files` number of dupe files
* `cpp_unf_bytes` currently unfinished / incoming uploads

some of the metrics have additional requirements to function correctly,
* `cpp_vol_*` requires either the `e2ds` volflag or `-e2dsa` global-option

the following options are available to disable some of the metrics:
* `--nos-hdd` disables `cpp_disk_*` which can prevent spinning up HDDs
* `--nos-vol` disables `cpp_vol_*` which reduces server startup time
* `--nos-vst` disables volume state, reducing the worst-case prometheus query time by 0.5 sec
* `--nos-dup` disables `cpp_dupe_*` which reduces the server load caused by prometheus queries
* `--nos-unf` disables `cpp_unf_*` for no particular purpose

note: the following metrics are counted incorrectly if multiprocessing is enabled with `-j`: `cpp_http_conns`, `cpp_http_reqs`, `cpp_sus_reqs`, `cpp_active_bans`, `cpp_total_bans`


# packages

the party might be closer than you think


## arch package

now [available on aur](https://aur.archlinux.org/packages/copyparty) maintained by [@icxes](https://github.com/icxes)


## fedora package

now [available on copr-pypi](https://copr.fedorainfracloud.org/coprs/g/copr/PyPI/)  , maintained autonomously -- [track record](https://copr.fedorainfracloud.org/coprs/g/copr/PyPI/package/python-copyparty/) seems OK

```bash
dnf copr enable @copr/PyPI
dnf install python3-copyparty  # just a minimal install, or... 
dnf install python3-{copyparty,pillow,argon2-cffi,pyftpdlib,pyOpenSSL} ffmpeg  # with recommended deps
```

this *may* also work on RHEL but [I'm not paying IBM to verify that](https://www.jeffgeerling.com/blog/2023/dear-red-hat-are-you-dumb)


## nix package

`nix profile install github:9001/copyparty`

requires a [flake-enabled](https://nixos.wiki/wiki/Flakes) installation of nix

some recommended dependencies are enabled by default; [override the package](https://github.com/9001/copyparty/blob/hovudstraum/contrib/package/nix/copyparty/default.nix#L3-L22) if you want to add/remove some features/deps

`ffmpeg-full` was chosen over `ffmpeg-headless` mainly because we need `withWebp` (and `withOpenmpt` is also nice) and being able to use a cached build felt more important than optimizing for size at the time -- PRs welcome if you disagree 👍


## nixos module

for this setup, you will need a [flake-enabled](https://nixos.wiki/wiki/Flakes) installation of NixOS.

```nix
{
  # add copyparty flake to your inputs
  inputs.copyparty.url = "github:9001/copyparty";

  # ensure that copyparty is an allowed argument to the outputs function
  outputs = { self, nixpkgs, copyparty }: {
    nixosConfigurations.yourHostName = nixpkgs.lib.nixosSystem {
      modules = [
        # load the copyparty NixOS module
        copyparty.nixosModules.default
        ({ pkgs, ... }: {
          # add the copyparty overlay to expose the package to the module
          nixpkgs.overlays = [ copyparty.overlays.default ];
          # (optional) install the package globally
          environment.systemPackages = [ pkgs.copyparty ];
          # configure the copyparty module
          services.copyparty.enable = true;
        })
      ];
    };
  };
}
```

copyparty on NixOS is configured via `services.copyparty` options, for example:
```nix
services.copyparty = {
  enable = true;
  # directly maps to values in the [global] section of the copyparty config.
  # see `copyparty --help` for available options
  settings = {
    i = "0.0.0.0";
    # use lists to set multiple values
    p = [ 3210 3211 ];
    # use booleans to set binary flags
    no-reload = true;
    # using 'false' will do nothing and omit the value when generating a config
    ignored-flag = false;
  };

  # create users
  accounts = {
    # specify the account name as the key
    ed = {
      # provide the path to a file containing the password, keeping it out of /nix/store
      # must be readable by the copyparty service user
      passwordFile = "/run/keys/copyparty/ed_password";
    };
    # or do both in one go
    k.passwordFile = "/run/keys/copyparty/k_password";
  };

  # create a volume
  volumes = {
    # create a volume at "/" (the webroot), which will
    "/" = {
      # share the contents of "/srv/copyparty"
      path = "/srv/copyparty";
      # see `copyparty --help-accounts` for available options
      access = {
        # everyone gets read-access, but
        r = "*";
        # users "ed" and "k" get read-write
        rw = [ "ed" "k" ];
      };
      # see `copyparty --help-flags` for available options
      flags = {
        # "fk" enables filekeys (necessary for upget permission) (4 chars long)
        fk = 4;
        # scan for new files every 60sec
        scan = 60;
        # volflag "e2d" enables the uploads database
        e2d = true;
        # "d2t" disables multimedia parsers (in case the uploads are malicious)
        d2t = true;
        # skips hashing file contents if path matches *.iso
        nohash = "\.iso$";
      };
    };
  };
  # you may increase the open file limit for the process
  openFilesLimit = 8192;
};
```

the passwordFile at /run/keys/copyparty/ could for example be generated by [agenix](https://github.com/ryantm/agenix), or you could just dump it in the nix store instead if that's acceptable


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
  * `post(){ curl -H pw:wark -H rand:8 -T "$1" http://127.0.0.1:3923/;}`  
    `post movie.mkv`
  * `post(){ wget --header='pw: wark' --post-file="$1" -O- http://127.0.0.1:3923/?raw;}`  
    `post movie.mkv`
  * `chunk(){ curl -H pw:wark -T- http://127.0.0.1:3923/;}`  
    `chunk <movie.mkv`

* bash: when curl and wget is not available or too boring
  * `(printf 'PUT /junk?pw=wark HTTP/1.1\r\n\r\n'; cat movie.mkv) | nc 127.0.0.1 3923`
  * `(printf 'PUT / HTTP/1.1\r\n\r\n'; cat movie.mkv) >/dev/tcp/127.0.0.1/3923`

* python: [u2c.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/u2c.py) is a command-line up2k client [(webm)](https://ocv.me/stuff/u2cli.webm)
  * file uploads, file-search, [folder sync](#folder-sync), autoresume of aborted/broken uploads
  * can be downloaded from copyparty: controlpanel -> connect -> [u2c.py](http://127.0.0.1:3923/.cpr/a/u2c.py)
  * see [./bin/README.md#u2cpy](bin/README.md#u2cpy)

* FUSE: mount a copyparty server as a local filesystem
  * cross-platform python client available in [./bin/](bin/)
  * can be downloaded from copyparty: controlpanel -> connect -> [partyfuse.py](http://127.0.0.1:3923/.cpr/a/partyfuse.py)
  * [rclone](https://rclone.org/) as client can give ~5x performance, see [./docs/rclone.md](docs/rclone.md)

* sharex (screenshot utility): see [./contrib/sharex.sxcu](contrib/#sharexsxcu)

copyparty returns a truncated sha512sum of your PUT/POST as base64; you can generate the same checksum locally to verify uplaods:

    b512(){ printf "$((sha512sum||shasum -a512)|sed -E 's/ .*//;s/(..)/\\x\1/g')"|base64|tr '+/' '-_'|head -c44;}
    b512 <movie.mkv

you can provide passwords using header `PW: hunter2`, cookie `cppwd=hunter2`, url-param `?pw=hunter2`, or with basic-authentication (either as the username or password)

NOTE: curl will not send the original filename if you use `-T` combined with url-params! Also, make sure to always leave a trailing slash in URLs unless you want to override the filename


## folder sync

sync folders to/from copyparty

the commandline uploader [u2c.py](https://github.com/9001/copyparty/tree/hovudstraum/bin#u2cpy) with `--dr` is the best way to sync a folder to copyparty; verifies checksums and does files in parallel, and deletes unexpected files on the server after upload has finished which makes file-renames really cheap (it'll rename serverside and skip uploading)

alternatively there is [rclone](./docs/rclone.md) which allows for bidirectional sync and is *way* more flexible (stream files straight from sftp/s3/gcs to copyparty, ...), although there is no integrity check and it won't work with files over 100 MiB if copyparty is behind cloudflare

* starting from rclone v1.63 (currently [in beta](https://beta.rclone.org/?filter=latest)), rclone will also be faster than u2c.py


## mount as drive

a remote copyparty server as a local filesystem;  go to the control-panel and click `connect` to see a list of commands to do that

alternatively, some alternatives roughly sorted by speed (unreproducible benchmark), best first:

* [rclone-webdav](./docs/rclone.md) (25s), read/WRITE ([v1.63-beta](https://beta.rclone.org/?filter=latest))
* [rclone-http](./docs/rclone.md) (26s), read-only
* [partyfuse.py](./bin/#partyfusepy) (35s), read-only
* [rclone-ftp](./docs/rclone.md) (47s), read/WRITE
* davfs2 (103s), read/WRITE, *very fast* on small files
* [win10-webdav](#webdav-server) (138s), read/WRITE
* [win10-smb2](#smb-server) (387s), read/WRITE

most clients will fail to mount the root of a copyparty server unless there is a root volume (so you get the admin-panel instead of a browser when accessing it) -- in that case, mount a specific volume instead


# android app

upload to copyparty with one tap

<a href="https://f-droid.org/packages/me.ocv.partyup/"><img src="https://ocv.me/fdroid.png" alt="Get it on F-Droid" height="50" /> '' <img src="https://img.shields.io/f-droid/v/me.ocv.partyup.svg" alt="f-droid version info" /></a> '' <a href="https://github.com/9001/party-up"><img src="https://img.shields.io/github/release/9001/party-up.svg?logo=github" alt="github version info" /></a>

the app is **NOT** the full copyparty server! just a basic upload client, nothing fancy yet

if you want to run the copyparty server on your android device, see [install on android](#install-on-android)


# iOS shortcuts

there is no iPhone app, but  the following shortcuts are almost as good:

* [upload to copyparty](https://www.icloud.com/shortcuts/41e98dd985cb4d3bb433222bc1e9e770) ([offline](https://github.com/9001/copyparty/raw/hovudstraum/contrib/ios/upload-to-copyparty.shortcut)) ([png](https://user-images.githubusercontent.com/241032/226118053-78623554-b0ed-482e-98e4-6d57ada58ea4.png)) based on the [original](https://www.icloud.com/shortcuts/ab415d5b4de3467b9ce6f151b439a5d7) by [Daedren](https://github.com/Daedren) (thx!)
  * can strip exif, upload files, pics, vids, links, clipboard
  * can download links and rehost the target file on copyparty (see first comment inside the shortcut)
  * pics become lowres if you share from gallery to shortcut, so better to launch the shortcut and pick stuff from there


# performance

defaults are usually fine - expect `8 GiB/s` download, `1 GiB/s` upload

below are some tweaks roughly ordered by usefulness:

* `-q` disables logging and can help a bunch, even when combined with `-lo` to redirect logs to file
* `--hist` pointing to a fast location (ssd) will make directory listings and searches faster when `-e2d` or `-e2t` is set
* `--no-hash .` when indexing a network-disk if you don't care about the actual filehashes and only want the names/tags searchable
* `--no-htp --hash-mt=0 --mtag-mt=1 --th-mt=1` minimizes the number of threads; can help in some eccentric environments (like the vscode debugger)
* `-j0` enables multiprocessing (actual multithreading), can reduce latency to `20+80/numCores` percent and generally improve performance in cpu-intensive workloads, for example:
  * lots of connections (many users or heavy clients)
  * simultaneous downloads and uploads saturating a 20gbps connection
  * if `-e2d` is enabled, `-j2` gives 4x performance for directory listings; `-j4` gives 16x
  
  ...however it adds an overhead to internal communication so it might be a net loss, see if it works 4 u
* using [pypy](https://www.pypy.org/) instead of [cpython](https://www.python.org/) *can* be 70% faster for some workloads, but slower for many others
  * and pypy can sometimes crash on startup with `-j0` (TODO make issue)


## client-side

when uploading files,

* chrome is recommended, at least compared to firefox:
  * up to 90% faster when hashing, especially on SSDs
  * up to 40% faster when uploading over extremely fast internets
  * but [u2c.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/u2c.py) can be 40% faster than chrome again

* if you're cpu-bottlenecked, or the browser is maxing a cpu core:
  * up to 30% faster uploads if you hide the upload status list by switching away from the `[🚀]` up2k ui-tab (or closing it)
    * optionally you can switch to the lightweight potato ui by clicking the `[🥔]`
    * switching to another browser-tab also works, the favicon will update every 10 seconds in that case
  * unlikely to be a problem, but can happen when uploding many small files, or your internet is too fast, or PC too slow


# security

there is a [discord server](https://discord.gg/25J8CdTT6G)  with an `@everyone` for all important updates (at the lack of better ideas)

some notes on hardening

* set `--rproxy 0` if your copyparty is directly facing the internet (not through a reverse-proxy)
  * cors doesn't work right otherwise
* if you allow anonymous uploads or otherwise don't trust the contents of a volume, you can prevent XSS with volflag `nohtml`
  * this returns html documents as plaintext, and also disables markdown rendering

safety profiles:

* option `-s` is a shortcut to set the following options:
  * `--no-thumb` disables thumbnails and audio transcoding to stop copyparty from running `FFmpeg`/`Pillow`/`VIPS` on uploaded files, which is a [good idea](https://www.cvedetails.com/vulnerability-list.php?vendor_id=3611) if anonymous upload is enabled
  * `--no-mtag-ff` uses `mutagen` to grab music tags instead of `FFmpeg`, which is safer and faster but less accurate
  * `--dotpart` hides uploads from directory listings while they're still incoming
  * `--no-robots` and `--force-js` makes life harder for crawlers, see [hiding from google](#hiding-from-google)

* option `-ss` is a shortcut for the above plus:
  * `--unpost 0`, `--no-del`, `--no-mv` disables all move/delete support
  * `--hardlink` creates hardlinks instead of symlinks when deduplicating uploads, which is less maintenance
    * however note if you edit one file it will also affect the other copies
  * `--vague-403` returns a "404 not found" instead of "401 unauthorized" which is a common enterprise meme
  * `--nih` removes the server hostname from directory listings

* option `-sss` is a shortcut for the above plus:
  * `--no-dav` disables webdav support
  * `--no-logues` and `--no-readme` disables support for readme's and prologues / epilogues in directory listings, which otherwise lets people upload arbitrary (but sandboxed) `<script>` tags
  * `-lo cpp-%Y-%m%d-%H%M%S.txt.xz` enables logging to disk
  * `-ls **,*,ln,p,r` does a scan on startup for any dangerous symlinks

other misc notes:

* you can disable directory listings by giving permission `g` instead of `r`, only accepting direct URLs to files
  * you may want [filekeys](#filekeys) to prevent filename bruteforcing
  * permission `h` instead of `r` makes copyparty behave like a traditional webserver with directory listing/index disabled, returning index.html instead
    * compatibility with filekeys: index.html itself can be retrieved without the correct filekey, but all other files are protected


## gotchas

behavior that might be unexpected

* users without read-access to a folder can still see the `.prologue.html` / `.epilogue.html` / `README.md` contents, for the purpose of showing a description on how to use the uploader for example
* users can submit `<script>`s which autorun (in a sandbox) for other visitors in a few ways;
  * uploading a `README.md` -- avoid with `--no-readme`
  * renaming `some.html` to `.epilogue.html` -- avoid with either `--no-logues` or `--no-dot-ren`
  * the directory-listing embed is sandboxed (so any malicious scripts can't do any damage) but the markdown editor is not 100% safe, see below
* markdown documents can contain html and `<script>`s; attempts are made to prevent scripts from executing (unless `-emp` is specified) but this is not 100% bulletproof, so setting the `nohtml` volflag is still the safest choice
  * or eliminate the problem entirely by only giving write-access to trustworthy people :^)


## cors

cross-site request config

by default, except for `GET` and `HEAD` operations, all requests must either:
* not contain an `Origin` header at all
* or have an `Origin` matching the server domain
* or the header `PW` with your password as value

cors can be configured with `--acao` and `--acam`, or the protections entirely disabled with `--allow-csrf`


## filekeys

prevent filename bruteforcing

volflag `c,fk` generates filekeys (per-file accesskeys) for all files; users which have full read-access (permission `r`) will then see URLs with the correct filekey `?k=...` appended to the end, and `g` users must provide that URL including the correct key to avoid a 404

by default, filekeys are generated based on salt (`--fk-salt`) + filesystem-path + file-size + inode (if not windows); add volflag `fka` to generate slightly weaker filekeys which will not be invalidated if the file is edited (only salt + path)

permissions `wG` (write + upget) lets users upload files and receive their own filekeys, still without being able to see other uploads


## password hashing

you can hash passwords  before putting them into config files / providing them as arguments; see `--help-pwhash` for all the details

`--ah-alg argon2` enables it, and if you have any plaintext passwords then it'll print the hashed versions on startup so you can replace them

optionally also specify `--ah-cli` to enter an interactive mode where it will hash passwords without ever writing the plaintext ones to disk

the default configs take about 0.4 sec and 256 MiB RAM to process a new password on a decent laptop


## https

both HTTP and HTTPS are accepted  by default, but letting a [reverse proxy](#reverse-proxy) handle the https/tls/ssl would be better (probably more secure by default)

copyparty doesn't speak HTTP/2 or QUIC, so using a reverse proxy would solve that as well

if [cfssl](https://github.com/cloudflare/cfssl/releases/latest) is installed, copyparty will automatically create a CA and server-cert on startup
* the certs are written to `--crt-dir` for distribution, see `--help` for the other `--crt` options
* this will be a self-signed certificate so you must install your `ca.pem` into all your browsers/devices
* if you want to avoid the hassle of distributing certs manually, please consider using a reverse proxy


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

see [devnotes](./docs/devnotes.md#http-api)


# dependencies

mandatory deps:
* `jinja2` (is built into the SFX)


## optional dependencies

install these to enable bonus features

enable hashed passwords in config: `argon2-cffi`

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

enable [smb](#smb-server) support (**not** recommended):
* `impacket==0.11.0`

`pyvips` gives higher quality thumbnails than `Pillow` and is 320% faster, using 270% more ram: `sudo apt install libvips42 && python3 -m pip install --user -U pyvips`


## optional gpl stuff

some bundled tools have copyleft dependencies, see [./bin/#mtag](bin/#mtag)

these are standalone programs and will never be imported / evaluated by copyparty, and must be enabled through `-mtp` configs


# sfx

the self-contained "binary"  [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) will unpack itself and run copyparty, assuming you have python installed of course

you can reduce the sfx size by repacking it; see [./docs/devnotes.md#sfx-repack](./docs/devnotes.md#sfx-repack)


## copyparty.exe

download [copyparty.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty.exe) (win8+) or [copyparty32.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty32.exe) (win7+)

![copyparty-exe-fs8](https://user-images.githubusercontent.com/241032/221445946-1e328e56-8c5b-44a9-8b9f-dee84d942535.png)

can be convenient on machines where installing python is problematic, however is **not recommended** -- if possible, please use **[copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py)** instead

* [copyparty.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty.exe) runs on win8 or newer, was compiled on win10, does thumbnails + media tags, and is *currently* safe to use, but any future python/expat/pillow CVEs can only be remedied by downloading a newer version of the exe

  * on win8 it needs [vc redist 2015](https://www.microsoft.com/en-us/download/details.aspx?id=48145), on win10 it just works
  * some antivirus may freak out (false-positive), possibly [Avast, AVG, and McAfee](https://www.virustotal.com/gui/file/52391a1e9842cf70ad243ef83844d46d29c0044d101ee0138fcdd3c8de2237d6/detection)

* dangerous: [copyparty32.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty32.exe) is compatible with [windows7](https://user-images.githubusercontent.com/241032/221445944-ae85d1f4-d351-4837-b130-82cab57d6cca.png), which means it uses an ancient copy of python (3.7.9) which cannot be upgraded and should never be exposed to the internet (LAN is fine)

* dangerous and deprecated: [copyparty-winpe64.exe](https://github.com/9001/copyparty/releases/download/v1.8.7/copyparty-winpe64.exe) lets you [run copyparty in WinPE](https://user-images.githubusercontent.com/241032/205454984-e6b550df-3c49-486d-9267-1614078dd0dd.png) and is otherwise completely useless

meanwhile [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) instead relies on your system python which gives better performance and will stay safe as long as you keep your python install up-to-date

then again, if you are already into downloading shady binaries from the internet, you may also want my [minimal builds](./scripts/pyinstaller#ffmpeg) of [ffmpeg](https://ocv.me/stuff/bin/ffmpeg.exe) and [ffprobe](https://ocv.me/stuff/bin/ffprobe.exe) which enables copyparty to extract multimedia-info, do audio-transcoding, and thumbnails/spectrograms/waveforms, however it's much better to instead grab a [recent official build](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) every once ina while if you can afford the size


# install on android

install [Termux](https://termux.com/) + its companion app `Termux:API` (see [ocv.me/termux](https://ocv.me/termux/)) and then copy-paste this into Termux (long-tap) all at once:
```sh
yes | pkg upgrade && termux-setup-storage && yes | pkg install python termux-api && python -m ensurepip && python -m pip install --user -U copyparty && { grep -qE 'PATH=.*\.local/bin' ~/.bashrc 2>/dev/null || { echo 'PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && . ~/.bashrc; }; }
echo $?
```

after the initial setup, you can launch copyparty at any time by running `copyparty` anywhere in Termux -- and if you run it with `--qr` you'll get a [neat qr-code](#qr-code) pointing to your external ip

if you want thumbnails (photos+videos) and you're okay with spending another 132 MiB of storage, `pkg install ffmpeg && python3 -m pip install --user -U pillow`

* or if you want to use `vips` for photo-thumbs instead, `pkg install libvips && python -m pip install --user -U wheel && python -m pip install --user -U pyvips && (cd /data/data/com.termux/files/usr/lib/; ln -s libgobject-2.0.so{,.0}; ln -s libvips.so{,.42})`


# reporting bugs

ideas for context to include in bug reports

in general, commandline arguments (and config file if any)

if something broke during an upload (replacing FILENAME with a part of the filename that broke):
```
journalctl -aS '48 hour ago' -u copyparty | grep -C10 FILENAME | tee bug.log
```

if there's a wall of base64 in the log (thread stacks) then please include that, especially if you run into something freezing up or getting stuck, for example `OperationalError('database is locked')` -- alternatively you can visit `/?stack` to see the stacks live, so http://127.0.0.1:3923/?stack for example


# devnotes

for build instructions etc, see [./docs/devnotes.md](./docs/devnotes.md)

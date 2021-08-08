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
    * [navpane](#navpane)
    * [thumbnails](#thumbnails)
    * [zip downloads](#zip-downloads)
    * [uploading](#uploading)
        * [file-search](#file-search)
    * [file manager](#file-manager)
    * [batch rename](#batch-rename)
    * [markdown viewer](#markdown-viewer)
    * [other tricks](#other-tricks)
    * [searching](#searching)
* [server config](#server-config)
    * [upload rules](#upload-rules)
    * [database location](#database-location)upload rules
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
    * [discarded ideas](#discarded-ideas)


## quickstart

download [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) and you're all set!

running the sfx without arguments (for example doubleclicking it on Windows) will give everyone full access to the current folder; see `-h` for help if you want [accounts and volumes](#accounts-and-volumes) etc

some recommended options:
* `-e2dsa` enables general file indexing, see [search configuration](#search-configuration)
* `-e2ts` enables audio metadata indexing (needs either FFprobe or Mutagen), see [optional dependencies](#optional-dependencies)
* `-v /mnt/music:/music:r:rw,foo -a foo:bar` shares `/mnt/music` as `/music`, `r`eadable by anyone, and read-write for user `foo`, password `bar`
  * replace `:r:rw,foo` with `:r,foo` to only make the folder readable by `foo` and nobody else
  * see [accounts and volumes](#accounts-and-volumes) for the syntax and other access levels (`r`ead, `w`rite, `m`ove, `d`elete)
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
  * ☑ multiprocessing (actual multithreading)
  * ☑ volumes (mountpoints)
  * ☑ [accounts](#accounts-and-volumes)
* upload
  * ☑ basic: plain multipart, ie6 support
  * ☑ [up2k](#uploading): js, resumable, multithreaded
  * ☑ stash: simple PUT filedropper
  * ☑ unpost: undo/delete accidental uploads
  * ☑ symlink/discard existing files (content-matching)
* download
  * ☑ single files in browser
  * ☑ [folders as zip / tar files](#zip-downloads)
  * ☑ FUSE client (read-only)
* browser
  * ☑ navpane (directory tree sidebar)
  * ☑ file manager (cut/paste, delete, [batch-rename](#batch-rename))
  * ☑ audio player (with OS media controls)
  * ☑ image gallery with webm player
  * ☑ [thumbnails](#thumbnails)
    * ☑ ...of images using Pillow
    * ☑ ...of videos using FFmpeg
    * ☑ cache eviction (max-age; maybe max-size eventually)
  * ☑ SPA (browse while uploading)
    * if you use the navpane to navigate, not folders in the file list
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


# bugs

* Windows: python 3.7 and older cannot read tags with FFprobe, so use Mutagen or upgrade
* Windows: python 2.7 cannot index non-ascii filenames with `-e2d`
* Windows: python 2.7 cannot handle filenames with mojibake
* `--th-ff-jpg` may fix video thumbnails on some FFmpeg versions

## general bugs

* all volumes must exist / be available on startup; up2k (mtp especially) gets funky otherwise
* cannot mount something at `/d1/d2/d3` unless `d2` exists inside `d1`
* probably more, pls let me know

## not my bugs

* Windows: folders cannot be accessed if the name ends with `.`
  * python or windows bug

* Windows: msys2-python 3.8.6 occasionally throws `RuntimeError: release unlocked lock` when leaving a scoped mutex in up2k
  * this is an msys2 bug, the regular windows edition of python is fine

* VirtualBox: sqlite throws `Disk I/O Error` when running in a VM and the up2k database is in a vboxsf
  * use `--hist` or the `hist` volflag (`-v [...]:c,hist=/tmp/foo`) to place the db inside the vm instead


# accounts and volumes

* `-a usr:pwd` adds account `usr` with password `pwd`
* `-v .::r` adds current-folder `.` as the webroot, `r`eadable by anyone
  * the syntax is `-v src:dst:perm:perm:...` so local-path, url-path, and one or more permissions to set
  * when granting permissions to an account, the names are comma-separated: `-v .::r,usr1,usr2:rw,usr3,usr4`

permissions:
* `r` (read): browse folder contents, download files, download as zip/tar
* `w` (write): upload files, move files *into* folder
* `m` (move): move files/folders *from* folder
* `d` (delete): delete files/folders

example:
* add accounts named u1, u2, u3 with passwords p1, p2, p3: `-a u1:p1 -a u2:p2 -a u3:p3`
* make folder `/srv` the root of the filesystem, read-only by anyone: `-v /srv::r`
* make folder `/mnt/music` available at `/music`, read-only for u1 and u2, read-write for u3: `-v /mnt/music:music:r,u1,u2:rw,u3`
  * unauthorized users accessing the webroot can see that the `music` folder exists, but cannot open it
* make folder `/mnt/incoming` available at `/inc`, write-only for u1, read-move for u2: `-v /mnt/incoming:inc:w,u1:rm,u2`
  * unauthorized users accessing the webroot can see that the `inc` folder exists, but cannot open it
  * `u1` can open the `inc` folder, but cannot see the contents, only upload new files to it
  * `u2` can browse it and move files *from* `/inc` into any folder where `u2` has write-access


# the browser

![copyparty-browser-fs8](https://user-images.githubusercontent.com/241032/115978054-65106380-a57d-11eb-98f8-59e3dee73557.png)


## tabs

* `[🔎]` search by size, date, path/name, mp3-tags ... see [searching](#searching)
* `[🧯]` unpost: undo/delete accidental uploads
* `[🚀]` and `[🎈]` are the uploaders, see [uploading](#uploading)
* `[📂]` mkdir: create directories
* `[📝]` new-md: create a new markdown document
* `[📟]` send-msg: either to server-log or into textfiles if `--urlform save`
* `[🎺]` audio-player config options
* `[⚙️]` general client config options


## hotkeys

the browser has the following hotkeys (assumes qwerty, ignores actual layout)
* `B` toggle breadcrumbs / navpane
* `I/K` prev/next folder
* `M` parent folder (or unexpand current)
* `G` toggle list / grid view
* `T` toggle thumbnails / icons
* `ctrl-X` cut selected files/folders
* `ctrl-V` paste
* `F2` rename selected file/folder
* when a file/folder is selected (in not-grid-view):
  * `Up/Down` move cursor
  * shift+`Up/Down` select and move cursor
  * ctrl+`Up/Down` move cursor and scroll viewport
  * `Space` toggle file selection
  * `Ctrl-A` toggle select all
* when playing audio:
  * `J/L` prev/next song
  * `U/O` skip 10sec back/forward
  * `0..9` jump to 0%..90%
  * `P` play/pause (also starts playing the folder)
* when viewing images / playing videos:
  * `J/L, Left/Right` prev/next file
  * `Home/End` first/last file
  * `Esc` close viewer
  * videos:
    * `U/O` skip 10sec back/forward
    * `P/K/Space` play/pause
    * `F` fullscreen
    * `C` continue playing next video
    * `R` loop
    * `M` mute
* when the navpane is open:
  * `A/D` adjust tree width
* in the grid view:
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

by default there's a breadcrumbs path; you can replace this with a navpane (tree-browser sidebar thing) by clicking the `🌲` or pressing the `B` hotkey

click `[-]` and `[+]` (or hotkeys `A`/`D`) to adjust the size, and the `[a]` toggles if the tree should widen dynamically as you go deeper or stay fixed-size


## thumbnails

![copyparty-thumbs-fs8](https://user-images.githubusercontent.com/241032/120070302-10836b00-c08a-11eb-8eb4-82004a34c342.png)

it does static images with Pillow and uses FFmpeg for video files, so you may want to `--no-thumb` or maybe just `--no-vthumb` depending on how dangerous your users are

images with the following names (see `--th-covers`) become the thumbnail of the folder they're in: `folder.png`, `folder.jpg`, `cover.png`, `cover.jpg`

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
  * `up2k.db` and `dir.txt` is always excluded
* `zip_crc` will take longer to download since the server has to read each file twice
  * this is only to support MS-DOS PKZIP v2.04g (october 1993) and older
    * how are you accessing copyparty actually

you can also zip a selection of files or folders by clicking them in the browser, that brings up a selection editor and zip button in the bottom right

![copyparty-zipsel-fs8](https://user-images.githubusercontent.com/241032/116008321-372a2e00-a614-11eb-9a4a-4a1fd9074224.png)

## uploading

two upload methods are available in the html client:
* `[🎈] bup`, the basic uploader, supports almost every browser since netscape 4.0
* `[🚀] up2k`, the fancy one

you can undo/delete uploads using `[🧯] unpost` if the server is running with `-e2d`

up2k has several advantages:
* you can drop folders into the browser (files are added recursively)
* files are processed in chunks, and each chunk is checksummed
  * uploads autoresume if they are interrupted by network issues
  * uploads resume if you reboot your browser or pc, just upload the same files again
  * server detects any corruption; the client reuploads affected chunks
  * the client doesn't upload anything that already exists on the server
* much higher speeds than ftp/scp/tarpipe on some internet connections (mainly american ones) thanks to parallel connections
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

adding the same file multiple times is blocked, so if you first search for a file and then decide to upload it, you have to click the `[cleanup]` button to discard `[done]` files (or just refresh the page)

note that since up2k has to read the file twice, `[🎈 bup]` can be up to 2x faster in extreme cases (if your internet connection is faster than the read-speed of your HDD)

up2k has saved a few uploads from becoming corrupted in-transfer already; caught an android phone on wifi redhanded in wireshark with a bitflip, however bup with https would *probably* have noticed as well (thanks to tls also functioning as an integrity check)


## file manager

if you have the required permissions, you can cut/paste, rename, and delete files/folders

you can move files across browser tabs (cut in one tab, paste in another)


## batch rename

![batch-rename-fs8](https://user-images.githubusercontent.com/241032/128434204-eb136680-3c07-4ec7-92e0-ae86af20c241.png)

select some files and press F2 to bring up the rename UI

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

![copyparty-md-read-fs8](https://user-images.githubusercontent.com/241032/115978057-66419080-a57d-11eb-8539-d2be843991aa.png)

* the document preview has a max-width which is the same as an A4 paper when printed


## other tricks

* you can link a particular timestamp in an audio file by adding it to the URL, such as `&20` / `&20s` / `&1m20` / `&t=1:20` after the `.../#af-c8960dab`

* if you are using media hotkeys to switch songs and are getting tired of seeing the OSD popup which Windows doesn't let you disable, consider https://ocv.me/dev/?media-osd-bgone.ps1


## searching

![copyparty-search-fs8](https://user-images.githubusercontent.com/241032/115978060-6772bd80-a57d-11eb-81d3-174e869b72c3.png)

when started with `-e2dsa` copyparty will scan/index all your files. This avoids duplicates on upload, and also makes the volumes searchable through the web-ui:
* make search queries by `size`/`date`/`directory-path`/`filename`, or...
* drag/drop a local file to see if the same contents exist somewhere on the server, see [file-search](#file-search)

path/name queries are space-separated, AND'ed together, and words are negated with a `-` prefix, so for example:
* path: `shibayan -bossa` finds all files where one of the folders contain `shibayan` but filters out any results where `bossa` exists somewhere in the path
* name: `demetori styx` gives you [good stuff](https://www.youtube.com/watch?v=zGh0g14ZJ8I&list=PL3A147BD151EE5218&index=9)

add the argument `-e2ts` to also scan/index tags from music files, which brings us over to:


# server config

file indexing relies on two databases, the up2k filetree (`-e2d`) and the metadata tags (`-e2t`). Configuration can be done through arguments, volume flags, or a mix of both.

through arguments:
* `-e2d` enables file indexing on upload
* `-e2ds` scans writable folders for new files on startup
* `-e2dsa` scans all mounted volumes (including readonly ones)
* `-e2t` enables metadata indexing on upload
* `-e2ts` scans for tags in all files that don't have tags yet
* `-e2tsr` deletes all existing tags, does a full reindex

the same arguments can be set as volume flags, in addition to `d2d` and `d2t` for disabling:
* `-v ~/music::r:c,e2dsa:c,e2tsr` does a full reindex of everything on startup
* `-v ~/music::r:c,d2d` disables **all** indexing, even if any `-e2*` are on
* `-v ~/music::r:c,d2t` disables all `-e2t*` (tags), does not affect `-e2d*`

note:
* `e2tsr` is probably always overkill, since `e2ds`/`e2dsa` would pick up any file modifications and `e2ts` would then reindex those, unless there is a new copyparty version with new parsers and the release note says otherwise
* the rescan button in the admin panel has no effect unless the volume has `-e2ds` or higher

you can choose to only index filename/path/size/last-modified (and not the hash of the file contents) by setting `--no-hash` or the volume-flag `:c,dhash`, this has the following consequences:
* initial indexing is way faster, especially when the volume is on a network disk
* makes it impossible to [file-search](#file-search)
* if someone uploads the same file contents, the upload will not be detected as a dupe, so it will not get symlinked or rejected

if you set `--no-hash`, you can enable hashing for specific volumes using flag `:c,ehash`


## upload rules

you can set upload rules using volume flags, some examples:

* `:c,sz=1k-3m` sets allowed filesize between 1 KiB and 3 MiB inclusive (suffixes: b, k, m, g)
* `:c,nosub` disallow uploading into subdirectories; goes well with `rotn` and `rotf`:
* `:c,rotn=1000,2` moves uploads into subfolders, up to 1000 files in each folder before making a new one, two levels deep (must be at least 1)
* `:c,rotf=%Y/%m/%d/%H` enforces files to be uploaded into a structure of subfolders according to that date format
  * if someone uploads to `/foo/bar` the path would be rewritten to `/foo/bar/2021/08/06/23` for example
  * but the actual value is not verified, just the structure, so the uploader can choose any values which conform to the format string
    * just to avoid additional complexity in up2k which is enough of a mess already

you can also set transaction limits which apply per-IP and per-volume, but these assume `-j 1` (default) otherwise the limits will be off, for example `-j 4` would allow anywhere between 1x and 4x the limits you set depending on which processing node the client gets routed to

* `:c,maxn=250,3600` allows 250 files over 1 hour from each IP (tracked per-volume)
* `:c,maxb=1g,300` allows 1 GiB total over 5 minutes from each IP (tracked per-volume)


## compress uploads

files can be autocompressed on upload, either on user-request (if config allows) or forced by server-config

* volume flag `gz` allows gz compression
* volume flag `xz` allows lzma compression
* volume flag `pk` **forces** compression on all files
* url parameter `pk` requests compression with server-default algorithm
* url parameter `gz` or `xz` requests compression with a specific algorithm
* url parameter `xz` requests xz compression

things to note,
* the `gz` and `xz` arguments take a single optional argument, the compression level (range 0 to 9)
* the `pk` volume flag takes the optional argument `ALGORITHM,LEVEL` which will then be forced for all uploads, for example `gz,9` or `xz,0`
* default compression is gzip level 9
* all upload methods except up2k are supported
* the files will be indexed after compression, so dupe-detection and file-search will not work as expected

some examples,


## database location

copyparty creates a subfolder named `.hist` inside each volume where it stores the database, thumbnails, and some other stuff

this can instead be kept in a single place using the `--hist` argument, or the `hist=` volume flag, or a mix of both:
* `--hist ~/.cache/copyparty -v ~/music::r:c,hist=-` sets `~/.cache/copyparty` as the default place to put volume info, but `~/music` gets the regular `.hist` subfolder (`-` restores default behavior)

note:
* markdown edits are always stored in a local `.hist` subdirectory
* on windows the volflag path is cyglike, so `/c/temp` means `C:\temp` but use regular paths for `--hist`
  * you can use cygpaths for volumes too, `-v C:\Users::r` and `-v /c/users::r` both work


## metadata from audio files

`-mte` decides which tags to index and display in the browser (and also the display order), this can be changed per-volume:
* `-v ~/music::r:c,mte=title,artist` indexes and displays *title* followed by *artist*

if you add/remove a tag from `mte` you will need to run with `-e2tsr` once to rebuild the database, otherwise only new files will be affected

but instead of using `-mte`, `-mth` is a better way to hide tags in the browser: these tags will not be displayed by default, but they still get indexed and become searchable, and users can choose to unhide them in the settings pane

`-mtm` can be used to add or redefine a metadata mapping, say you have media files with `foo` and `bar` tags and you want them to display as `qux` in the browser (preferring `foo` if both are present), then do `-mtm qux=foo,bar` and now you can `-mte artist,title,qux`

tags that start with a `.` such as `.bpm` and `.dur`(ation) indicate numeric value

see the beautiful mess of a dictionary in [mtag.py](https://github.com/9001/copyparty/blob/master/copyparty/mtag.py) for the default mappings (should cover mp3,opus,flac,m4a,wav,aif,)

`--no-mutagen` disables Mutagen and uses FFprobe instead, which...
* is about 20x slower than Mutagen
* catches a few tags that Mutagen doesn't
  * melodic key, video resolution, framerate, pixfmt
* avoids pulling any GPL code into copyparty
* more importantly runs FFprobe on incoming files which is bad if your FFmpeg has a cve


## file parser plugins

copyparty can invoke external programs to collect additional metadata for files using `mtp` (either as argument or volume flag), there is a default timeout of 30sec

* `-mtp .bpm=~/bin/audio-bpm.py` will execute `~/bin/audio-bpm.py` with the audio file as argument 1 to provide the `.bpm` tag, if that does not exist in the audio metadata
* `-mtp key=f,t5,~/bin/audio-key.py` uses `~/bin/audio-key.py` to get the `key` tag, replacing any existing metadata tag (`f,`), aborting if it takes longer than 5sec (`t5,`)
* `-v ~/music::r:c,mtp=.bpm=~/bin/audio-bpm.py:c,mtp=key=f,t5,~/bin/audio-key.py` both as a per-volume config wow this is getting ugly

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
| navpane         |  -  |  -  | `*1` | yep  | yep   | yep  | yep | yep  |
| up2k            |  -  |  -  | yep  | yep  | yep   | yep  | yep | yep  |
| markdown editor |  -  |  -  | yep  | yep  | yep   | yep  | yep | yep  |
| markdown viewer |  -  |  -  | yep  | yep  | yep   | yep  | yep | yep  |
| play mp3/m4a    |  -  | yep | yep  | yep  | yep   | yep  | yep | yep  |
| play ogg/opus   |  -  |  -  |  -   |  -   | yep   | yep  | `*2` | yep |
| thumbnail view  |  -  |  -  | -    | -    | yep   | yep  | yep | yep  |
| image viewer    |  -  |  -  | -    | -    | yep   | yep  | yep | yep  |
| **= feature =** | ie6 | ie9 | ie10 | ie11 | ff 52 | c 49 | iOS | Andr |

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
| **SerenityOS** (7e98457)  | hits a page fault, works with `?b=u`, file upload not-impl |


# client examples

* javascript: dump some state into a file (two separate examples)
  * `await fetch('https://127.0.0.1:3923/', {method:"PUT", body: JSON.stringify(foo)});`
  * `var xhr = new XMLHttpRequest(); xhr.open('POST', 'https://127.0.0.1:3923/msgs?raw'); xhr.send('foo');`

* curl/wget: upload some files (post=file, chunk=stdin)
  * `post(){ curl -b cppwd=wark -F act=bput -F f=@"$1" http://127.0.0.1:3923/;}`  
    `post movie.mkv`
  * `post(){ wget --header='Cookie: cppwd=wark' --post-file="$1" -O- http://127.0.0.1:3923/?raw;}`  
    `post movie.mkv`
  * `chunk(){ curl -b cppwd=wark -T- http://127.0.0.1:3923/;}`  
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
* `--no-hash` when indexing a network-disk if you don't care about the actual filehashes and only want the names/tags searchable
* `-j` enables multiprocessing (actual multithreading) and can make copyparty perform better in cpu-intensive workloads, for example:
  * huge amount of short-lived connections
  * really heavy traffic (downloads/uploads)
  
  ...however it adds an overhead to internal communication so it might be a net loss, see if it works 4 u


# dependencies

* `jinja2` (is built into the SFX)


## optional dependencies

enable music tags:
* either `mutagen` (fast, pure-python, skips a few tags, makes copyparty GPL? idk)
* or `ffprobe` (20x slower, more accurate, possibly dangerous depending on your distro and users)

enable thumbnails of images:
* `Pillow` (requires py2.7 or py3.5+)

enable thumbnails of videos:
* `ffmpeg` and `ffprobe` somewhere in `$PATH`

enable thumbnails of HEIF pictures:
* `pyheif-pillow-opener` (requires Linux or a C compiler)

enable thumbnails of AVIF pictures:
* `pillow-avif-plugin`


## install recommended deps
```
python -m pip install --user -U jinja2 mutagen Pillow
```


## optional gpl stuff

some bundled tools have copyleft dependencies, see [./bin/#mtag](bin/#mtag)

these are standalone programs and will never be imported / evaluated by copyparty, and must be enabled through `-mtp` configs


# sfx

currently there are two self-contained "binaries":
* [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) -- pure python, works everywhere, **recommended**
* [copyparty-sfx.sh](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.sh) -- smaller, but only for linux and macos, kinda deprecated

launch either of them (**use sfx.py on systemd**) and it'll unpack and run copyparty, assuming you have python installed of course

pls note that `copyparty-sfx.sh` will fail if you rename `copyparty-sfx.py` to `copyparty.py` and keep it in the same folder because `sys.path` is funky


## sfx repack

if you don't need all the features, you can repack the sfx and save a bunch of space; all you need is an sfx and a copy of this repo (nothing else to download or build, except if you're on windows then you need msys2 or WSL)
* `525k` size of original sfx.py as of v0.11.30
* `315k` after `./scripts/make-sfx.sh re no-ogv`
* `223k` after `./scripts/make-sfx.sh re no-ogv no-cm`

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
mv /tmp/pe-copyparty/copyparty/web/deps/ copyparty/web/deps/
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

* hls framework for Someone Else to drop code into :^)
* readme.md as epilogue


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
  * too dangerous
* comment field
  * nah
* look into android thumbnail cache file format
  * absolutely not
* indexedDB for hashes, cfg enable/clear/sz, 2gb avail, ~9k for 1g, ~4k for 100m, 500k items before autoeviction
  * blank hashlist when up-ok to skip handshake
    * too many confusing side-effects

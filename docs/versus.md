# alternatives to copyparty

copyparty compared against all similar software i've bumped into

there is probably some unintentional bias so please submit corrections

currently up to date with [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) but that probably won't last


## toc

* top
* [recommendations](#recommendations)
* [feature comparisons](#feature-comparisons)
    * [general](#general)
    * [file transfer](#file-transfer)
    * [protocols and client support](#protocols-and-client-support)
    * [server configuration](#server-configuration)
    * [server capabilities](#server-capabilities)
    * [client features](#client-features)
    * [integration](#integration)
    * [another matrix](#another-matrix)
* [reviews](#reviews)
    * [copyparty](#copyparty)
    * [hfs2](#hfs2)
    * [hfs3](#hfs3)
    * [nextcloud](#nextcloud)
    * [seafile](#seafile)
    * [rclone](#rclone)
    * [dufs](#dufs)
    * [chibisafe](#chibisafe)
    * [kodbox](#kodbox)
    * [filebrowser](#filebrowser)
    * [filegator](#filegator)
    * [updog](#updog)
    * [goshs](#goshs)
    * [gimme-that](#gimme-that)
    * [ass](#ass)
    * [linx](#linx)
* [briefly considered](#briefly-considered)


# recommendations

* [kodbox](https://github.com/kalcaddle/kodbox) ([review](#kodbox)) appears to be a fantastic alternative if you're not worried about running chinese software, with several advantages over copyparty
  * but anything you want to share must be moved into the kodbox filesystem
* [seafile](https://github.com/haiwen/seafile) ([review](#seafile)) and [nextcloud](https://github.com/nextcloud/server) ([review](#nextcloud)) could be decent alternatives if you need something heavier than copyparty
  * but their [license](https://snyk.io/learn/agpl-license/) is [problematic](https://opensource.google/documentation/reference/using/agpl-policy)
  * and copyparty is way better at uploads in particular (resumable, accelerated)
  * and anything you want to share must be moved into the respective filesystems
* [filebrowser](https://github.com/filebrowser/filebrowser) ([review](#filebrowser)) and [dufs](https://github.com/sigoden/dufs) ([review](#dufs)) are simpler copyparties but with a settings gui
  * has some of the same strengths of copyparty, being portable and able to work with an existing folder structure
  * ...but copyparty is better at uploads + some other things


# feature comparisons

```
<&Kethsar> copyparty is very much bloat ed, so yeah
```

the table headers in the matrixes below are the different softwares, with a quick review of each software in the next section

the softwares,
* `a` = [copyparty](https://github.com/9001/copyparty)
* `b` = [hfs2](https://github.com/rejetto/hfs2)
* `c` = [hfs3](https://www.rejetto.com/hfs/)
* `d` = [nextcloud](https://github.com/nextcloud/server)
* `e` = [seafile](https://github.com/haiwen/seafile)
* `f` = [rclone](https://github.com/rclone/rclone), specifically `rclone serve webdav .`
* `g` = [dufs](https://github.com/sigoden/dufs)
* `h` = [chibisafe](https://github.com/chibisafe/chibisafe)
* `i` = [kodbox](https://github.com/kalcaddle/kodbox)
* `j` = [filebrowser](https://github.com/filebrowser/filebrowser)
* `k` = [filegator](https://github.com/filegator/filegator)

some softwares not in the matrixes,
* [updog](#updog)
* [goshs](#goshs)
* [gimme-that](#gimmethat)
* [ass](#ass)
* [linx](#linx)

symbol legend,
* `█` = absolutely
* `╱` = partially
* `•` = maybe?
* ` ` = nope


## general

| feature / software      | a | b | c | d | e | f | g | h | i | j | k |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - |
| intuitive UX            |   | ╱ | █ | █ | █ |   | █ | █ | █ | █ | █ | 
| config GUI              |   | █ | █ | █ | █ |   |   | █ | █ | █ |   | 
| good documentation      |   |   |   | █ | █ | █ | █ |   |   | █ | █ |
| runs on iOS             | ╱ |   |   |   |   | ╱ |   |   |   |   |   |
| runs on Android         | █ |   |   |   |   | █ |   |   |   |   |   |
| runs on WinXP           | █ | █ |   |   |   | █ |   |   |   |   |   |
| runs on Windows         | █ | █ | █ | █ | █ | █ | █ | ╱ | █ | █ | █ |
| runs on Linux           | █ | ╱ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| runs on Macos           | █ |   | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| runs on FreeBSD         | █ |   |   | • | █ | █ | █ | • | █ | █ |   |
| portable binary         | █ | █ | █ |   |   | █ | █ |   |   | █ |   |
| zero setup, just go     | █ | █ | █ |   |   | ╱ | █ |   |   | █ |   |
| android app             | ╱ |   |   | █ | █ |   |   |   |   |   |   |
| iOS app                 |   |   |   | █ | █ |   |   |   |   |   |   |

* `zero setup` = you can get a mostly working setup by just launching the app, without having to install any software or configure whatever
* `a`/copyparty remarks:
  * no gui for server settings; only for client-side stuff
  * can theoretically run on iOS / iPads using [iSH](https://ish.app/), but only the iPad will offer sufficient multitasking i think
  * [android app](https://f-droid.org/en/packages/me.ocv.partyup/) is for uploading only
* `b`/hfs2 runs on linux through wine
* `f`/rclone must be started with the command `rclone serve webdav .` or similar
* `h`/chibisafe has undocumented windows support


## file transfer

*the thing that copyparty is actually kinda good at*

| feature / software      | a | b | c | d | e | f | g | h | i | j | k |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - |
| download folder as zip  | █ | █ | █ | █ | █ |   | █ |   | █ | █ | ╱ |
| download folder as tar  | █ |   |   |   |   |   |   |   |   | █ |   |
| upload                  | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| parallel uploads        | █ |   |   | █ | █ |   | • |   | █ |   | █ |
| resumable uploads       | █ |   |   |   |   |   |   |   | █ |   | █ |
| upload segmenting       | █ |   |   |   |   |   |   | █ | █ |   | █ |
| upload acceleration     | █ |   |   |   |   |   |   |   | █ |   | █ |
| upload verification     | █ |   |   | █ | █ |   |   |   | █ |   |   |
| upload deduplication    | █ |   |   |   | █ |   |   |   | █ |   |   |
| upload a 999 TiB file   | █ |   |   |   | █ | █ | • |   | █ |   | █ |
| keep last-modified time | █ |   |   | █ | █ | █ |   |   |   |   |   |
| upload rules            | ╱ | ╱ | ╱ | ╱ | ╱ |   |   | ╱ | ╱ |   | ╱ |
| ┗ max disk usage        | █ | █ |   |   | █ |   |   |   | █ |   |   |
| ┗ max filesize          | █ |   |   |   |   |   |   | █ |   |   | █ |
| ┗ max items in folder   | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ max file age          | █ |   |   |   |   |   |   |   | █ |   |   |
| ┗ max uploads over time | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ compress before write | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ randomize filename    | █ |   |   |   |   |   |   | █ | █ |   |   |
| ┗ mimetype reject-list  | ╱ |   |   |   |   |   |   |   | • |   |   |
| ┗ extension reject-list | ╱ |   |   |   |   |   |   | █ | • |   |   |
| checksums provided      |   |   |   | █ | █ |   |   |   | █ | ╱ |   |
| cloud storage backend   | ╱ | ╱ | ╱ | █ | █ | █ | ╱ |   |   | ╱ | █ |

* `upload segmenting` = files are sliced into chunks, making it possible to upload files larger than 100 MiB on cloudflare for example

* `upload acceleration` = each file can be uploaded using several TCP connections, which can offer a huge speed boost over huge distances / on flaky connections -- like the good old [download accelerators](https://en.wikipedia.org/wiki/GetRight) except in reverse

* `upload verification` = uploads are checksummed or otherwise confirmed to have been transferred correctly

* `checksums provided` = when downloading a file from the server, the file's checksum is provided for verification client-side

* `cloud storage backend` = able to serve files from (and write to) s3 or similar cloud services; `╱` means the software can do this with some help from `rclone mount` as a bridge

* `a`/copyparty can reject uploaded files (based on complex conditions), for example [by extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) or [mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py)
* `j`/filebrowser can provide checksums for single files on request
* `k`/filegator download-as-zip is not streaming; it creates the full zipfile before download can start

## protocols and client support

| feature / software      | a | b | c | d | e | f | g | h | i | j | k |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - |
| serve https             | █ |   | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| serve webdav            | █ |   |   | █ | █ | █ | █ |   | █ |   |   |
| serve ftp               | █ |   |   |   |   | █ |   |   |   |   |   |
| serve ftps              | █ |   |   |   |   | █ |   |   |   |   |   |
| serve sftp              |   |   |   |   |   | █ |   |   |   |   |   |
| serve smb/cifs          | ╱ |   |   |   |   | █ |   |   |   |   |   |
| serve dlna              |   |   |   |   |   | █ |   |   |   |   |   |
| listen on unix-socket   |   |   |   | █ | █ |   | █ | █ | █ |   | █ |
| zeroconf                | █ |   |   |   |   |   |   |   |   |   |   |
| supports netscape 4     | ╱ |   |   |   |   | █ |   |   |   |   | • |
| ...internet explorer 6  | ╱ | █ |   | █ |   | █ |   |   |   |   | • |
| mojibake filenames      | █ |   |   | • | • | █ | █ | • | • | • |   |
| undecodable filenames   | █ |   |   | • | • | █ |   | • | • |   |   |

* `zeroconf` = the server announces itself on the LAN, automatically appearing on other zeroconf-capable devices
* `mojibake filenames` = filenames decoded with the wrong codec and then reencoded (usually to utf-8), so `宇多田ヒカル` might look like `ëFæ╜ôcâqâJâï`
* `undecodable filenames` = pure binary garbage which cannot be parsed as utf-8
  * you can successfully play `$'\355\221'` with mpv through mounting a remote copyparty server with rclone, pog
* `a`/copyparty remarks:
  * extremely minimal samba/cifs server
  * netscape 4 / ie6 support is mostly listed as a joke altho some people have actually found it useful


## server configuration

| feature / software      | a | b | c | d | e | f | g | h | i | j | k |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - |
| config from cmd args    | █ |   |   |   |   | █ | █ |   |   | █ |   |
| config files            | █ | █ | █ | ╱ | ╱ | █ |   | █ |   | █ | • |
| runtime config reload   | █ | █ | █ |   |   |   |   | █ | █ | █ | █ |
| same-port http / https  | █ |   |   |   |   |   |   |   |   |   |   |
| listen multiple ports   | █ |   |   |   |   |   |   |   |   |   |   |
| virtual file system     | █ | █ | █ |   |   |   | █ |   |   |   |   |
| reverse-proxy ok        | █ |   | █ | █ | █ | █ | █ | █ | • | • | • |
| folder-rproxy ok        | █ |   |   |   | █ | █ |   | • | • | • | • |

* `folder-rproxy` = reverse-proxying without dedicating an entire (sub)domain, using a subfolder instead


## server capabilities

| feature / software      | a | b | c | d | e | f | g | h | i | j | k |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - |
| accounts                | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| single-sign-on          |   |   |   | █ | █ |   |   |   | • |   |   |
| token auth              |   |   |   | █ | █ |   |   | █ |   |   |   |
| per-volume permissions  | █ | █ | █ | █ | █ | █ | █ |   | █ | █ | ╱ |
| per-folder permissions  | ╱ |   |   | █ | █ |   | █ |   | █ | █ | ╱ |
| per-file permissions    |   |   |   | █ | █ |   | █ |   | █ |   |   |
| per-file passwords      | █ |   |   | █ | █ |   | █ |   | █ |   |   |
| unmap subfolders        | █ |   |   |   |   |   | █ |   |   | █ | ╱ |
| index.html blocks list  |   |   |   |   |   |   | █ |   |   | • |   |
| write-only folders      | █ |   |   |   |   |   |   |   |   |   | █ |
| files stored as-is      | █ | █ | █ | █ |   | █ | █ |   |   | █ | █ |
| file versioning         |   |   |   | █ | █ |   |   |   |   |   |   |
| file encryption         |   |   |   | █ | █ | █ |   |   |   |   |   |
| file indexing           | █ |   | █ | █ | █ |   |   | █ | █ | █ |   |
| ┗ per-volume db         | █ |   | • | • | • |   |   | • | • |   |   |
| ┗ db stored in folder   | █ |   |   |   |   |   |   | • | • | █ |   |
| ┗ db stored out-of-tree | █ |   | █ | █ | █ |   |   | • | • | █ |   |
| ┗ existing file tree    | █ |   | █ |   |   |   |   |   |   | █ |   |
| file action event hooks | █ |   |   |   |   |   |   |   |   | █ |   |
| one-way folder sync     | █ |   |   | █ | █ | █ |   |   |   |   |   |
| full sync               |   |   |   | █ | █ |   |   |   |   |   |   |
| speed throttle          |   | █ | █ |   |   | █ |   |   | █ |   |   |
| anti-bruteforce         | █ | █ | █ | █ | █ |   |   |   | • |   |   |
| dyndns updater          |   | █ |   |   |   |   |   |   |   |   |   |
| self-updater            |   |   | █ |   |   |   |   |   |   |   |   |
| log rotation            | █ |   | █ | █ | █ |   |   | • | █ |   |   |
| upload tracking / log   | █ | █ | • | █ | █ |   |   | █ | █ |   |   |
| curl-friendly ls        | █ |   |   |   |   |   |   |   |   |   |   |
| curl-friendly upload    | █ |   |   |   |   | █ | █ | • |   |   |   |

* `unmap subfolders` = "shadowing"; mounting a local folder in the middle of an existing filesystem tree in order to disable access below that path
* `files stored as-is` = uploaded files are trivially readable from the server HDD, not sliced into chunks or in weird folder structures or anything like that
* `db stored in folder` = filesystem index can be written to a database file inside the folder itself
* `db stored out-of-tree` = filesystem index can be stored some place else, not necessarily inside the shared folders
* `existing file tree` = will index any existing files it finds
* `file action event hooks` = run script before/after upload, move, rename, ...
* `one-way folder sync` = like rsync, optionally deleting unexpected files at target
* `full sync` = stateful, dropbox-like sync
* `curl-friendly ls` = returns a plaintext folder listing when curled
* `curl-friendly upload` = uploading with curl is just `curl -T some.bin http://.../`
* `a`/copyparty remarks:
  * one-way folder sync from local to server can be done efficiently with [up2k.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py), or with webdav and conventional rsync
  * can hot-reload config files (with just a few exceptions)
  * can set per-folder permissions if that folder is made into a separate volume, so there is configuration overhead
  * upload history can be visualized using [partyjournal](https://github.com/9001/copyparty/blob/hovudstraum/bin/partyjournal.py)
* `k`/filegator remarks:
  * `per-* permissions` -- can limit a user to one folder and its subfolders
  * `unmap subfolders` -- can globally filter a list of paths


## client features

| feature / software      | a | b | c | d | e | f | g | h | i | j | k |
| ----------------------  | - | - | - | - | - | - | - | - | - | - | - |
| single-page app         | █ |   | █ | █ | █ |   |   | █ | █ | █ | █ |
| themes                  | █ | █ |   | █ |   |   |   |   | █ |   |   |
| directory tree nav      | █ | ╱ |   |   | █ |   |   |   | █ |   | ╱ |
| multi-column sorting    | █ |   |   |   |   |   |   |   |   |   |   |
| thumbnails              | █ |   |   | ╱ | ╱ |   |   | █ | █ | ╱ |   |
| ┗ image thumbnails      | █ |   |   | █ | █ |   |   | █ | █ | █ |   |
| ┗ video thumbnails      | █ |   |   | █ | █ |   |   |   | █ |   |   |
| ┗ audio spectrograms    | █ |   |   |   |   |   |   |   |   |   |   |
| audio player            | █ |   |   | █ | █ |   |   |   | █ | ╱ |   |
| ┗ gapless playback      | █ |   |   |   |   |   |   |   | • |   |   |
| ┗ audio equalizer       | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ waveform seekbar      | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ OS integration        | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ transcode to lossy    | █ |   |   |   |   |   |   |   |   |   |   |
| video player            | █ |   |   | █ | █ |   |   |   | █ | █ |   |
| ┗ video transcoding     |   |   |   |   |   |   |   |   | █ |   |   |
| audio BPM detector      | █ |   |   |   |   |   |   |   |   |   |   |
| audio key detector      | █ |   |   |   |   |   |   |   |   |   |   |
| search by path / name   | █ | █ | █ | █ | █ |   | █ |   | █ | █ | ╱ |
| search by date / size   | █ |   |   |   | █ |   |   | █ | █ |   |   |
| search by bpm / key     | █ |   |   |   |   |   |   |   |   |   |   |
| search by custom tags   |   |   |   |   |   |   |   | █ | █ |   |   |
| search in file contents |   |   |   | █ | █ |   |   |   | █ |   |   |
| search by custom parser | █ |   |   |   |   |   |   |   |   |   |   |
| find local file         | █ |   |   |   |   |   |   |   |   |   |   |
| undo recent uploads     | █ |   |   |   |   |   |   |   |   |   |   |
| create directories      | █ |   |   | █ | █ | ╱ | █ | █ | █ |   | █ |
| image viewer            | █ |   |   | █ | █ |   |   |   | █ |   | █ |
| markdown viewer         | █ |   |   |   | █ |   |   |   | █ | ╱ | ╱ |
| markdown editor         | █ |   |   |   | █ |   |   |   | █ | ╱ | ╱ |
| readme.md in listing    | █ |   |   | █ |   |   |   |   |   |   |   |
| rename files            | █ | █ | █ | █ | █ | ╱ | █ |   | █ | █ | █ |
| batch rename            | █ |   |   |   |   |   |   |   | █ |   |   |
| cut / paste files       | █ | █ |   | █ | █ |   |   |   | █ |   |   |
| move files              | █ | █ |   | █ | █ |   | █ |   | █ | █ | █ |
| delete files            | █ | █ |   | █ | █ | ╱ | █ | █ | █ | █ | █ |
| copy files              |   |   |   |   | █ |   |   |   | █ | █ | █ |

* `single-page app` = multitasking; possible to continue navigating while uploading
* `audio player » os-integration` = use the lockscreen to play/pause, prev/next song
* `find local file` = drop a file into the browser to see if it exists on the server
* `a`/copyparty has teeny-tiny skips playing gapless albums depending on audio codec (opus best)
* `b`/hfs2 has a very basic directory tree view, not showing sibling folders
* `f`/rclone can do some file management (mkdir, rename, delete) when hosting througn webdav
* `j`/filebrowser has a plaintext viewer/editor
* `k`/filegator directory tree is a modal window


## integration

| feature / software      | a | b | c | d | e | f | g | h | i | j | k |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - |
| OS alert on upload      | █ |   |   |   |   |   |   |   |   | ╱ |   |
| discord                 | █ |   |   |   |   |   |   |   |   | ╱ |   |
| ┗ announce uploads      | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ custom embeds         |   |   |   |   |   |   |   |   |   |   |   |
| sharex                  | █ |   |   | █ |   | █ | ╱ | █ |   |   |   |
| flameshot               |   |   |   |   |   | █ |   |   |   |   |   |

* sharex ╱ = yes, but does not provide example sharex config
* `a`/copyparty remarks:
  * `OS alert on upload` available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/notify.py)
  * `discord » announce uploads` available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/discord-announce.py)
* `j`/filebrowser can probably pull those off with command runners similar to copyparty


## another matrix

| software / feature | lang   | lic    | size   |
| ------------------ | ------ | ------ | ------ |
| copyparty          | python | █ mit  | 0.6 MB |
| hfs2               | delphi | ░ gpl3 |   2 MB |
| hfs3               | ts     | ░ gpl3 |  36 MB |
| nextcloud          | php    | ‼ agpl |    •   |
| seafile            | c      | ‼ agpl |    •   |
| rclone             | c      | █ mit  |  45 MB |
| dufs               | rust   | █ apl2 | 2.5 MB |
| chibisafe          | ts     | █ mit  |    •   |
| kodbox             | php    | ░ gpl3 |  92 MB |
| filebrowser        | go     | █ apl2 |  20 MB |
| filegator          | php    | █ mit  |    •   |
| updog              | python | █ mit  |  17 MB |
| goshs              | go     | █ mit  |  11 MB |
| gimme-that         | python | █ mit  | 4.8 MB |
| ass                | ts     | █ isc  |    •   |
| linx               | go     | ░ gpl3 |  20 MB |

* `size` = binary (if available) or installed size of program and its dependencies
  * copyparty size is for the standalone python file; the windows exe is **6 MiB**


# reviews

* ✅ are advantages over copyparty
* ⚠️ are disadvantages

## [copyparty](https://github.com/9001/copyparty)
* resumable uploads which are verified server-side
* upload segmenting allows for potentially much faster uploads on some connections, and terabyte-sized files even on cloudflare
  * both of the above are surprisingly uncommon features
* very cross-platform (python, no dependencies)

## [hfs2](https://github.com/rejetto/hfs2)
* the OG, the legend
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ windows-only
* ✅ config GUI
* vfs with gui config, per-volume permissions
* starting to show its age, hence the rewrite:

## [hfs3](https://www.rejetto.com/hfs/)
* nodejs; cross-platform
* vfs with gui config, per-volume permissions
* still early development, let's revisit later

## [nextcloud](https://github.com/nextcloud/server)
* php, mariadb
* ⚠️ [isolated on-disk file hierarchy] in per-user folders
  * not that bad, can probably be remedied with bindmounts or maybe symlinks
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ no write-only / upload-only folders
* ⚠️ http/webdav only; no ftp, zeroconf
* ⚠️ less awesome music player
* ⚠️ doesn't run on android or ipads
* ✅ great ui/ux
* ✅ config gui
* ✅ apps (android / iphone)
  * copyparty: android upload-only app
* ✅ more granular permissions (per-file)
* ✅ search: fulltext indexing of file contents
* ✅ webauthn passwordless authentication

## [seafile](https://github.com/haiwen/seafile)
* c, mariadb
* ⚠️ [isolated on-disk file hierarchy](https://manual.seafile.com/maintain/seafile_fsck/), incompatible with other software
  * *much worse than nextcloud* in that regard
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ no write-only / upload-only folders
* ⚠️ http/webdav only; no ftp, zeroconf
* ⚠️ less awesome music player
* ⚠️ doesn't run on android or ipads
* ✅ great ui/ux
* ✅ config gui
* ✅ apps (android / iphone)
  * copyparty: android upload-only app
* ✅ more granular permissions (per-file)
* ✅ search: fulltext indexing of file contents

## [rclone](https://github.com/rclone/rclone)
* nice standalone c program
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ no web-ui, just a server / downloader / uploader utility
* ✅ works with almost any protocol, cloud provider
  * ⚠️ copyparty's webdav server is slightly faster

## [dufs](https://github.com/sigoden/dufs)
* rust; cross-platform (windows, linux, macos)
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ doesn't support crazy filenames
* ✅ per-url access control (copyparty is per-volume)
* basic but really snappy ui
* upload, rename, delete, ... see feature matrix

## [chibisafe](https://github.com/chibisafe/chibisafe)
* nodejs; recommends docker
* *it has upload segmenting!*
  * ⚠️ but uploads are still not resumable / accelerated / integrity-checked
* ⚠️ not portable
* ⚠️ isolated on-disk file hierarchy, incompatible with other software
* ⚠️ http/webdav only; no ftp or zeroconf
* ✅ pretty ui
* ✅ control panel for server settings and user management
* ✅ user registration
* ✅ searchable image tags; delete by tag
* ✅ browser extension to upload files to the server
* ✅ reject uploads by file extension
  * copyparty: can reject uploads [by extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) or [mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py) using plugins
* ✅ token auth (api keys)

## [kodbox](https://github.com/kalcaddle/kodbox)
* this thing is insane
* php; [docker](https://hub.docker.com/r/kodcloud/kodbox)
* *upload segmenting, acceleration, and integrity checking!*
  * ⚠️ but uploads are not resumable(?)
* ⚠️ not portable
* ⚠️ isolated on-disk file hierarchy, incompatible with other software
* ⚠️ http/webdav only; no ftp or zeroconf
* ⚠️ some parts of the GUI are in chinese
* ✅ fantastic ui/ux
* ✅ control panel for server settings and user management
* ✅ file tags; file discussions!?
* ✅ video transcoding
* ✅ unzip uploaded archives
* ✅ IDE with syntax hilighting
* ✅ wysiwyg editor for openoffice files

## [filebrowser](https://github.com/filebrowser/filebrowser)
* go; cross-platform (windows, linux, mac)
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ http only; no webdav / ftp / zeroconf
* ⚠️ doesn't support crazy filenames
* ⚠️ limited file search
* ✅ settings gui
* ✅ good ui/ux
  * ⚠️ but no directory tree for navigation
* supposed to have write-only folders but couldn't get it to work

## [filegator](https://github.com/filegator/filegator)
* go; cross-platform (windows, linux, mac)
* ⚠️ http only; no webdav / ftp / zeroconf
* ⚠️ does not support symlinks
* ⚠️ expensive download-as-zip feature
* ⚠️ doesn't support crazy filenames
* ⚠️ limited file search
* *it has upload segmenting and acceleration*
  * ⚠️ but uploads are still not integrity-checked

## [updog](https://github.com/sc0tfree/updog)
* python; cross-platform
* basic directory listing with upload feature
* ⚠️ less portable
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ no vfs; single folder, single account

## [goshs](https://github.com/patrickhener/goshs)
* go; cross-platform (windows, linux, mac)
* ⚠️ no vfs; single folder, single account
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ✅ cool clipboard widget
  * copyparty: the markdown editor is an ok substitute
* read-only and upload-only modes (same as copyparty's write-only)
* https, webdav

## [gimme-that](https://github.com/nejdetckenobi/gimme-that)
* python, but with c dependencies
* ⚠️ no vfs; single folder, multiple accounts
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ weird folder structure for uploads
* ✅ clamav antivirus check on upload! neat
* optional max-filesize, os-notification on uploads
  * copyparty: os-notification available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/notify.py)

## [ass](https://github.com/tycrek/ass)
* nodejs; recommends docker
* ⚠️ not portable
* ⚠️ upload only; no browser
* ⚠️ upload through sharex only; no web-ui
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ✅ token auth
* ✅ gps metadata stripping
  * copyparty: possible with [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/image-noexif.py)
* ✅ discord integration (custom embeds, upload webhook)
  * copyparty: [upload webhook plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/discord-announce.py)
* ✅ reject uploads by mimetype
  * copyparty: can reject uploads [by extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) or [mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py) using plugins
* ✅ can use S3 as storage backend; copyparty relies on rclone-mount for that
* ✅ custom 404 pages

## [linx](https://github.com/ZizzyDizzyMC/linx-server/)
* originally [andreimarcu/linx-server](https://github.com/andreimarcu/linx-server) but development has ended
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* some of its unique features have been added to copyparty as former linx users have migrated
  * file expiration timers, filename randomization
* ✅ password-protected files
  * copyparty: password-protected folders and filekeys are 
* ✅ file deletion keys
* ✅ download files as torrents
* ✅ remote uploads (send a link to the server and it downloads it)
  * copyparty: available as a [terrible hack](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/wget.py)
* ✅ can use S3 as storage backend; copyparty relies on rclone-mount for that


# briefly considered
* [pydio](https://github.com/pydio/cells): python/agpl3, looks great, fantastic ux -- but needs mariadb, systemwide install
* [gossa](https://github.com/pldubouilh/gossa): go/mit, minimalistic, basic file upload, text editor, mkdir and rename (no delete/move)
* [h5ai](https://larsjung.de/h5ai/): php/mit, slick ui, image viewer, directory tree, no upload feature

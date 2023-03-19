# alternatives to copyparty

copyparty compared against all similar software i've bumped into

there is probably some unintentional bias so please submit corrections

currently up to date with [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) but that probably won't last


## symbol legends

### ...in feature matrices:
* `█` = absolutely
* `╱` = partially
* `•` = maybe?
* ` ` = nope

### ...in reviews:
* ✅ = advantages over copyparty
  * 💾 = what copyparty offers as an alternative
* 🔵 = similarities
* ⚠️ = disadvantages (something copyparty does "better")


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
    * [sftpgo](#sftpgo)
    * [updog](#updog)
    * [goshs](#goshs)
    * [gimme-that](#gimme-that)
    * [ass](#ass)
    * [linx](#linx)
    * [h5ai](#h5ai)
    * [autoindex](#autoindex)
    * [miniserve](#miniserve)
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
* `b` = [hfs2](https://rejetto.com/hfs/)
* `c` = [hfs3](https://github.com/rejetto/hfs)
* `d` = [nextcloud](https://github.com/nextcloud/server)
* `e` = [seafile](https://github.com/haiwen/seafile)
* `f` = [rclone](https://github.com/rclone/rclone), specifically `rclone serve webdav .`
* `g` = [dufs](https://github.com/sigoden/dufs)
* `h` = [chibisafe](https://github.com/chibisafe/chibisafe)
* `i` = [kodbox](https://github.com/kalcaddle/kodbox)
* `j` = [filebrowser](https://github.com/filebrowser/filebrowser)
* `k` = [filegator](https://github.com/filegator/filegator)
* `l` = [sftpgo](https://github.com/drakkan/sftpgo)

some softwares not in the matrixes,
* [updog](#updog)
* [goshs](#goshs)
* [gimme-that](#gimmethat)
* [ass](#ass)
* [linx](#linx)
* [h5ai](#h5ai)
* [autoindex](#autoindex)
* [miniserve](#miniserve)

symbol legend,
* `█` = absolutely
* `╱` = partially
* `•` = maybe?
* ` ` = nope


## general

| feature / software      | a | b | c | d | e | f | g | h | i | j | k | l |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - | - |
| intuitive UX            |   | ╱ | █ | █ | █ |   | █ | █ | █ | █ | █ | █ |
| config GUI              |   | █ | █ | █ | █ |   |   | █ | █ | █ |   | █ |
| good documentation      |   |   |   | █ | █ | █ | █ |   |   | █ | █ | ╱ |
| runs on iOS             | ╱ |   |   |   |   | ╱ |   |   |   |   |   |   |
| runs on Android         | █ |   |   |   |   | █ |   |   |   |   |   |   |
| runs on WinXP           | █ | █ |   |   |   | █ |   |   |   |   |   |   |
| runs on Windows         | █ | █ | █ | █ | █ | █ | █ | ╱ | █ | █ | █ | █ |
| runs on Linux           | █ | ╱ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| runs on Macos           | █ |   | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| runs on FreeBSD         | █ |   |   | • | █ | █ | █ | • | █ | █ |   | █ |
| portable binary         | █ | █ | █ |   |   | █ | █ |   |   | █ |   | █ |
| zero setup, just go     | █ | █ | █ |   |   | ╱ | █ |   |   | █ |   | ╱ |
| android app             | ╱ |   |   | █ | █ |   |   |   |   |   |   |   |
| iOS app                 | ╱ |   |   | █ | █ |   |   |   |   |   |   |   |

* `zero setup` = you can get a mostly working setup by just launching the app, without having to install any software or configure whatever
* `a`/copyparty remarks:
  * no gui for server settings; only for client-side stuff
  * can theoretically run on iOS / iPads using [iSH](https://ish.app/), but only the iPad will offer sufficient multitasking i think
  * [android app](https://f-droid.org/en/packages/me.ocv.partyup/) is for uploading only
  * no iOS app but has [shortcuts](https://github.com/9001/copyparty#ios-shortcuts) for easy uploading
* `b`/hfs2 runs on linux through wine
* `f`/rclone must be started with the command `rclone serve webdav .` or similar
* `h`/chibisafe has undocumented windows support
* `i`/sftpgo must be launched with a command


## file transfer

*the thing that copyparty is actually kinda good at*

| feature / software      | a | b | c | d | e | f | g | h | i | j | k | l |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - | - |
| download folder as zip  | █ | █ | █ | █ | █ |   | █ |   | █ | █ | ╱ | █ |
| download folder as tar  | █ |   |   |   |   |   |   |   |   | █ |   |   |
| upload                  | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| parallel uploads        | █ |   |   | █ | █ |   | • |   | █ |   | █ |   |
| resumable uploads       | █ |   |   |   |   |   |   |   | █ |   | █ | ╱ |
| upload segmenting       | █ |   |   |   |   |   |   | █ | █ |   | █ | ╱ |
| upload acceleration     | █ |   |   |   |   |   |   |   | █ |   | █ |   |
| upload verification     | █ |   |   | █ | █ |   |   |   | █ |   |   |   |
| upload deduplication    | █ |   |   |   | █ |   |   |   | █ |   |   |   |
| upload a 999 TiB file   | █ |   |   |   | █ | █ | • |   | █ |   | █ | ╱ |
| keep last-modified time | █ |   |   | █ | █ | █ |   |   |   |   |   | █ |
| upload rules            | ╱ | ╱ | ╱ | ╱ | ╱ |   |   | ╱ | ╱ |   | ╱ | ╱ |
| ┗ max disk usage        | █ | █ |   |   | █ |   |   |   | █ |   |   | █ |
| ┗ max filesize          | █ |   |   |   |   |   |   | █ |   |   | █ | █ |
| ┗ max items in folder   | █ |   |   |   |   |   |   |   |   |   |   | ╱ |
| ┗ max file age          | █ |   |   |   |   |   |   |   | █ |   |   |   |
| ┗ max uploads over time | █ |   |   |   |   |   |   |   |   |   |   | ╱ |
| ┗ compress before write | █ |   |   |   |   |   |   |   |   |   |   |   |
| ┗ randomize filename    | █ |   |   |   |   |   |   | █ | █ |   |   |   |
| ┗ mimetype reject-list  | ╱ |   |   |   |   |   |   |   | • | ╱ |   | ╱ |
| ┗ extension reject-list | ╱ |   |   |   |   |   |   | █ | • | ╱ |   | ╱ |
| checksums provided      |   |   |   | █ | █ |   |   |   | █ | ╱ |   |   |
| cloud storage backend   | ╱ | ╱ | ╱ | █ | █ | █ | ╱ |   |   | ╱ | █ | █ |

* `upload segmenting` = files are sliced into chunks, making it possible to upload files larger than 100 MiB on cloudflare for example

* `upload acceleration` = each file can be uploaded using several TCP connections, which can offer a huge speed boost over huge distances / on flaky connections -- like the good old [download accelerators](https://en.wikipedia.org/wiki/GetRight) except in reverse

* `upload verification` = uploads are checksummed or otherwise confirmed to have been transferred correctly

* `checksums provided` = when downloading a file from the server, the file's checksum is provided for verification client-side

* `cloud storage backend` = able to serve files from (and write to) s3 or similar cloud services; `╱` means the software can do this with some help from `rclone mount` as a bridge

* `a`/copyparty can reject uploaded files (based on complex conditions), for example [by extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) or [mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py)
* `j`/filebrowser remarks:
  * can provide checksums for single files on request
  * can probably do extension/mimetype rejection similar to copyparty
* `k`/filegator download-as-zip is not streaming; it creates the full zipfile before download can start
* `l`/sftpgo:
  * resumable/segmented uploads only over SFTP, not over HTTP
  * upload rules are totals only, not over time
  * can probably do extension/mimetype rejection similar to copyparty


## protocols and client support

| feature / software      | a | b | c | d | e | f | g | h | i | j | k | l |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - | - |
| serve https             | █ |   | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| serve webdav            | █ |   |   | █ | █ | █ | █ |   | █ |   |   | █ |
| serve ftp               | █ |   |   |   |   | █ |   |   |   |   |   | █ |
| serve ftps              | █ |   |   |   |   | █ |   |   |   |   |   | █ |
| serve sftp              |   |   |   |   |   | █ |   |   |   |   |   | █ |
| serve smb/cifs          | ╱ |   |   |   |   | █ |   |   |   |   |   |   |
| serve dlna              |   |   |   |   |   | █ |   |   |   |   |   |   |
| listen on unix-socket   |   |   |   | █ | █ |   | █ | █ | █ |   | █ | █ |
| zeroconf                | █ |   |   |   |   |   |   |   |   |   |   |   |
| supports netscape 4     | ╱ |   |   |   |   | █ |   |   |   |   | • |   |
| ...internet explorer 6  | ╱ | █ |   | █ |   | █ |   |   |   |   | • |   |
| mojibake filenames      | █ |   |   | • | • | █ | █ | • | • | • |   | ╱ |
| undecodable filenames   | █ |   |   | • | • | █ |   | • | • |   |   | ╱ |

* `webdav` = protocol convenient for mounting a remote server as a local filesystem; see zeroconf:
* `zeroconf` = the server announces itself on the LAN, [automatically appearing](https://user-images.githubusercontent.com/241032/215344737-0eae8d98-9496-4256-9aa8-cd2f6971810d.png) on other zeroconf-capable devices
* `mojibake filenames` = filenames decoded with the wrong codec and then reencoded (usually to utf-8), so `宇多田ヒカル` might look like `ëFæ╜ôcâqâJâï`
* `undecodable filenames` = pure binary garbage which cannot be parsed as utf-8
  * you can successfully play `$'\355\221'` with mpv through mounting a remote copyparty server with rclone, pog
* `a`/copyparty remarks:
  * extremely minimal samba/cifs server
  * netscape 4 / ie6 support is mostly listed as a joke altho some people have actually found it useful ([ie4 tho](https://user-images.githubusercontent.com/241032/118192791-fb31fe00-b446-11eb-9647-898ea8efc1f7.png))
* `l`/sftpgo translates mojibake filenames into valid utf-8 (information loss)


## server configuration

| feature / software      | a | b | c | d | e | f | g | h | i | j | k | l |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - | - |
| config from cmd args    | █ |   |   |   |   | █ | █ |   |   | █ |   | ╱ |
| config files            | █ | █ | █ | ╱ | ╱ | █ |   | █ |   | █ | • | ╱ |
| runtime config reload   | █ | █ | █ |   |   |   |   | █ | █ | █ | █ |   |
| same-port http / https  | █ |   |   |   |   |   |   |   |   |   |   |   |
| listen multiple ports   | █ |   |   |   |   |   |   |   |   |   |   | █ |
| virtual file system     | █ | █ | █ |   |   |   | █ |   |   |   |   | █ |
| reverse-proxy ok        | █ |   | █ | █ | █ | █ | █ | █ | • | • | • | █ |
| folder-rproxy ok        | █ |   |   |   | █ | █ |   | • | • | • | • |   |

* `folder-rproxy` = reverse-proxying without dedicating an entire (sub)domain, using a subfolder instead
* `l`/sftpgo:
  * config: users must be added through gui / api calls


## server capabilities

| feature / software      | a | b | c | d | e | f | g | h | i | j | k | l |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - | - |
| accounts                | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| per-account chroot      |   |   |   |   |   |   |   |   |   |   |   | █ |
| single-sign-on          |   |   |   | █ | █ |   |   |   | • |   |   |   |
| token auth              |   |   |   | █ | █ |   |   | █ |   |   |   |   |
| 2fa                     |   |   |   | █ | █ |   |   |   |   |   |   | █ |
| per-volume permissions  | █ | █ | █ | █ | █ | █ | █ |   | █ | █ | ╱ | █ |
| per-folder permissions  | ╱ |   |   | █ | █ |   | █ |   | █ | █ | ╱ | █ |
| per-file permissions    |   |   |   | █ | █ |   | █ |   | █ |   |   |   |
| per-file passwords      | █ |   |   | █ | █ |   | █ |   | █ |   |   |   |
| unmap subfolders        | █ |   |   |   |   |   | █ |   |   | █ | ╱ | • |
| index.html blocks list  |   |   |   |   |   |   | █ |   |   | • |   |   |
| write-only folders      | █ |   |   |   |   |   |   |   |   |   | █ | █ |
| files stored as-is      | █ | █ | █ | █ |   | █ | █ |   |   | █ | █ | █ |
| file versioning         |   |   |   | █ | █ |   |   |   |   |   |   |   |
| file encryption         |   |   |   | █ | █ | █ |   |   |   |   |   | █ |
| file indexing           | █ |   | █ | █ | █ |   |   | █ | █ | █ |   |   |
| ┗ per-volume db         | █ |   | • | • | • |   |   | • | • |   |   |   |
| ┗ db stored in folder   | █ |   |   |   |   |   |   | • | • | █ |   |   |
| ┗ db stored out-of-tree | █ |   | █ | █ | █ |   |   | • | • | █ |   |   |
| ┗ existing file tree    | █ |   | █ |   |   |   |   |   |   | █ |   |   |
| file action event hooks | █ |   |   |   |   |   |   |   |   | █ |   | █ |
| one-way folder sync     | █ |   |   | █ | █ | █ |   |   |   |   |   |   |
| full sync               |   |   |   | █ | █ |   |   |   |   |   |   |   |
| speed throttle          |   | █ | █ |   |   | █ |   |   | █ |   |   | █ |
| anti-bruteforce         | █ | █ | █ | █ | █ |   |   |   | • |   |   | █ |
| dyndns updater          |   | █ |   |   |   |   |   |   |   |   |   |   |
| self-updater            |   |   | █ |   |   |   |   |   |   |   |   |   |
| log rotation            | █ |   | █ | █ | █ |   |   | • | █ |   |   | █ |
| upload tracking / log   | █ | █ | • | █ | █ |   |   | █ | █ |   |   | ╱ |
| curl-friendly ls        | █ |   |   |   |   |   |   |   |   |   |   |   |
| curl-friendly upload    | █ |   |   |   |   | █ | █ | • |   |   |   |   |

* `unmap subfolders` = "shadowing"; mounting a local folder in the middle of an existing filesystem tree in order to disable access below that path
* `files stored as-is` = uploaded files are trivially readable from the server HDD, not sliced into chunks or in weird folder structures or anything like that
* `db stored in folder` = filesystem index can be written to a database file inside the folder itself
* `db stored out-of-tree` = filesystem index can be stored some place else, not necessarily inside the shared folders
* `existing file tree` = will index any existing files it finds
* `file action event hooks` = run script before/after upload, move, rename, ...
* `one-way folder sync` = like rsync, optionally deleting unexpected files at target
* `full sync` = stateful, dropbox-like sync
* `curl-friendly ls` = returns a [sortable plaintext folder listing](https://user-images.githubusercontent.com/241032/215322619-ea5fd606-3654-40ad-94ee-2bc058647bb2.png) when curled
* `curl-friendly upload` = uploading with curl is just `curl -T some.bin http://.../`
* `a`/copyparty remarks:
  * one-way folder sync from local to server can be done efficiently with [up2k.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py), or with webdav and conventional rsync
  * can hot-reload config files (with just a few exceptions)
  * can set per-folder permissions if that folder is made into a separate volume, so there is configuration overhead
  * [event hooks](https://github.com/9001/copyparty/tree/hovudstraum/bin/hooks) ([discord](https://user-images.githubusercontent.com/241032/215304439-1c1cb3c8-ec6f-4c17-9f27-81f969b1811a.png), [desktop](https://user-images.githubusercontent.com/241032/215335767-9c91ed24-d36e-4b6b-9766-fb95d12d163f.png)) inspired by filebrowser, as well as the more complex [media parser](https://github.com/9001/copyparty/tree/hovudstraum/bin/mtag) alternative
  * upload history can be visualized using [partyjournal](https://github.com/9001/copyparty/blob/hovudstraum/bin/partyjournal.py)
* `k`/filegator remarks:
  * `per-* permissions` -- can limit a user to one folder and its subfolders
  * `unmap subfolders` -- can globally filter a list of paths
* `l`/sftpgo:
  * `file action event hooks` also include on-download triggers
  * `upload tracking / log` in main logfile


## client features

| feature / software      | a | b | c | d | e | f | g | h | i | j | k | l |
| ----------------------  | - | - | - | - | - | - | - | - | - | - | - | - |
| single-page app         | █ |   | █ | █ | █ |   |   | █ | █ | █ | █ |   |
| themes                  | █ | █ |   | █ |   |   |   |   | █ |   |   |   |
| directory tree nav      | █ | ╱ |   |   | █ |   |   |   | █ |   | ╱ |   |
| multi-column sorting    | █ |   |   |   |   |   |   |   |   |   |   |   |
| thumbnails              | █ |   |   | ╱ | ╱ |   |   | █ | █ | ╱ |   |   |
| ┗ image thumbnails      | █ |   |   | █ | █ |   |   | █ | █ | █ |   |   |
| ┗ video thumbnails      | █ |   |   | █ | █ |   |   |   | █ |   |   |   |
| ┗ audio spectrograms    | █ |   |   |   |   |   |   |   |   |   |   |   |
| audio player            | █ |   |   | █ | █ |   |   |   | █ | ╱ |   |   |
| ┗ gapless playback      | █ |   |   |   |   |   |   |   | • |   |   |   |
| ┗ audio equalizer       | █ |   |   |   |   |   |   |   |   |   |   |   |
| ┗ waveform seekbar      | █ |   |   |   |   |   |   |   |   |   |   |   |
| ┗ OS integration        | █ |   |   |   |   |   |   |   |   |   |   |   |
| ┗ transcode to lossy    | █ |   |   |   |   |   |   |   |   |   |   |   |
| video player            | █ |   |   | █ | █ |   |   |   | █ | █ |   |   |
| ┗ video transcoding     |   |   |   |   |   |   |   |   | █ |   |   |   |
| audio BPM detector      | █ |   |   |   |   |   |   |   |   |   |   |   |
| audio key detector      | █ |   |   |   |   |   |   |   |   |   |   |   |
| search by path / name   | █ | █ | █ | █ | █ |   | █ |   | █ | █ | ╱ |   |
| search by date / size   | █ |   |   |   | █ |   |   | █ | █ |   |   |   |
| search by bpm / key     | █ |   |   |   |   |   |   |   |   |   |   |   |
| search by custom tags   |   |   |   |   |   |   |   | █ | █ |   |   |   |
| search in file contents |   |   |   | █ | █ |   |   |   | █ |   |   |   |
| search by custom parser | █ |   |   |   |   |   |   |   |   |   |   |   |
| find local file         | █ |   |   |   |   |   |   |   |   |   |   |   |
| undo recent uploads     | █ |   |   |   |   |   |   |   |   |   |   |   |
| create directories      | █ |   |   | █ | █ | ╱ | █ | █ | █ | █ | █ | █ |
| image viewer            | █ |   |   | █ | █ |   |   |   | █ | █ | █ |   |
| markdown viewer         | █ |   |   |   | █ |   |   |   | █ | ╱ | ╱ |   |
| markdown editor         | █ |   |   |   | █ |   |   |   | █ | ╱ | ╱ |   |
| readme.md in listing    | █ |   |   | █ |   |   |   |   |   |   |   |   |
| rename files            | █ | █ | █ | █ | █ | ╱ | █ |   | █ | █ | █ | █ |
| batch rename            | █ |   |   |   |   |   |   |   | █ |   |   |   |
| cut / paste files       | █ | █ |   | █ | █ |   |   |   | █ |   |   |   |
| move files              | █ | █ |   | █ | █ |   | █ |   | █ | █ | █ |   |
| delete files            | █ | █ |   | █ | █ | ╱ | █ | █ | █ | █ | █ | █ |
| copy files              |   |   |   |   | █ |   |   |   | █ | █ | █ |   |

* `single-page app` = multitasking; possible to continue navigating while uploading
* `audio player » os-integration` = use the [lockscreen](https://user-images.githubusercontent.com/241032/142711926-0700be6c-3e31-47b3-9928-53722221f722.png) or [media hotkeys](https://user-images.githubusercontent.com/241032/215347492-b4250797-6c90-4e09-9a4c-721edf2fb15c.png) to play/pause, prev/next song
* `search by custom tags` = ability to tag files through the UI and search by those
* `find local file` = drop a file into the browser to see if it exists on the server
* `undo recent uploads` = accounts without delete permissions have a time window where they can undo their own uploads
* `a`/copyparty has teeny-tiny skips playing gapless albums depending on audio codec (opus best)
* `b`/hfs2 has a very basic directory tree view, not showing sibling folders
* `f`/rclone can do some file management (mkdir, rename, delete) when hosting througn webdav
* `j`/filebrowser has a plaintext viewer/editor
* `k`/filegator directory tree is a modal window


## integration

| feature / software      | a | b | c | d | e | f | g | h | i | j | k | l |
| ----------------------- | - | - | - | - | - | - | - | - | - | - | - | - |
| OS alert on upload      | █ |   |   |   |   |   |   |   |   | ╱ |   | ╱ |
| discord                 | █ |   |   |   |   |   |   |   |   | ╱ |   | ╱ |
| ┗ announce uploads      | █ |   |   |   |   |   |   |   |   |   |   | ╱ |
| ┗ custom embeds         |   |   |   |   |   |   |   |   |   |   |   | ╱ |
| sharex                  | █ |   |   | █ |   | █ | ╱ | █ |   |   |   |   |
| flameshot               |   |   |   |   |   | █ |   |   |   |   |   |   |

* sharex `╱` = yes, but does not provide example sharex config
* `a`/copyparty remarks:
  * `OS alert on upload` available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/notify.py)
  * `discord » announce uploads` available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/discord-announce.py)
* `j`/filebrowser can probably pull those off with command runners similar to copyparty
* `l`/sftpgo has nothing built-in but is very extensible


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
| sftpgo             | go     | ‼ agpl |  44 MB |
| updog              | python | █ mit  |  17 MB |
| goshs              | go     | █ mit  |  11 MB |
| gimme-that         | python | █ mit  | 4.8 MB |
| ass                | ts     | █ isc  |    •   |
| linx               | go     | ░ gpl3 |  20 MB |

* `size` = binary (if available) or installed size of program and its dependencies
  * copyparty size is for the [standalone python](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) file; the [windows exe](https://github.com/9001/copyparty/releases/latest/download/copyparty.exe) is **6 MiB**


# reviews

* ✅ are advantages over copyparty
  * 💾 are what copyparty offers as an alternative
* 🔵 are similarities
* ⚠️ are disadvantages (something copyparty does "better")

## [copyparty](https://github.com/9001/copyparty)
* resumable uploads which are verified server-side
* upload segmenting allows for potentially much faster uploads on some connections, and terabyte-sized files even on cloudflare
  * both of the above are surprisingly uncommon features
* very cross-platform (python, no dependencies)

## [hfs2](https://rejetto.com/hfs/)
* the OG, the legend
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ windows-only
* ✅ config GUI
* vfs with gui config, per-volume permissions
* starting to show its age, hence the rewrite:

## [hfs3](https://github.com/rejetto/hfs)
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
* ⚠️ AGPL licensed
* ✅ great ui/ux
* ✅ config gui
* ✅ apps (android / iphone)
  * 💾 android upload-only app + iPhone upload shortcut
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
* ⚠️ AGPL licensed
* ✅ great ui/ux
* ✅ config gui
* ✅ apps (android / iphone)
  * 💾 android upload-only app + iPhone upload shortcut
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
* 🔵 basic but really snappy ui
* 🔵 upload, rename, delete, ... see feature matrix

## [chibisafe](https://github.com/chibisafe/chibisafe)
* nodejs; recommends docker
* 🔵 *it has upload segmenting!*
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
  * 💾 can reject uploads [by extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) or [mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py) using plugins
* ✅ token auth (api keys)

## [kodbox](https://github.com/kalcaddle/kodbox)
* this thing is insane
* php; [docker](https://hub.docker.com/r/kodcloud/kodbox)
* 🔵 *upload segmenting, acceleration, and integrity checking!*
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
* ⚠️ no directory tree nav
* ⚠️ limited file search
* ✅ settings gui
* ✅ good ui/ux
  * ⚠️ but no directory tree for navigation
* ✅ user signup
* ✅ command runner / remote shell
* 🔵 supposed to have write-only folders but couldn't get it to work

## [filegator](https://github.com/filegator/filegator)
* go; cross-platform (windows, linux, mac)
* 🔵 *it has upload segmenting and acceleration*
  * ⚠️ but uploads are still not integrity-checked
* ⚠️ http only; no webdav / ftp / zeroconf
* ⚠️ does not support symlinks
* ⚠️ expensive download-as-zip feature
* ⚠️ doesn't support crazy filenames
* ⚠️ limited file search

## [sftpgo](https://github.com/drakkan/sftpgo)
* go; cross-platform (windows, linux, mac)
* ⚠️ http uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
  * 🔵 sftp uploads are resumable
* ⚠️ web UI is very minimal + a bit slow
  * ⚠️ no thumbnails / image viewer / audio player
  * ⚠️ basic file manager (no cut/paste/move)
* ⚠️ no filesystem indexing / search
* ⚠️ doesn't run on phones, tablets
* ⚠️ no zeroconf (mdns/ssdp)
* ⚠️ AGPL licensed
* 🔵 ftp, ftps, webdav
* ✅ sftp server
* ✅ settings gui
* ✅ acme (automatic tls certs)
  * 💾 relies on caddy/certbot/acme.sh
* ✅ at-rest encryption
  * 💾 relies on LUKS/BitLocker
* ✅ can use S3/GCS as storage backend
  * 💾 relies on rclone-mount
* ✅ on-download event hook (otherwise same as copyparty)
* ✅ more extensive permissions control

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
  * 💾 the markdown editor is an ok substitute
* 🔵 read-only and upload-only modes (same as copyparty's write-only)
* 🔵 https, webdav, but no ftp

## [gimme-that](https://github.com/nejdetckenobi/gimme-that)
* python, but with c dependencies
* ⚠️ no vfs; single folder, multiple accounts
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ weird folder structure for uploads
* ✅ clamav antivirus check on upload! neat
* 🔵 optional max-filesize, os-notification on uploads
  * 💾 os-notification available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/notify.py)

## [ass](https://github.com/tycrek/ass)
* nodejs; recommends docker
* ⚠️ not portable
* ⚠️ upload only; no browser
* ⚠️ upload through sharex only; no web-ui
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ✅ token auth
* ✅ gps metadata stripping
  * 💾 possible with [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/image-noexif.py)
* ✅ discord integration (custom embeds, upload webhook)
  * 💾 [upload webhook plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/discord-announce.py)
* ✅ reject uploads by mimetype
  * 💾 can reject uploads [by extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) or [mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py) using plugins
* ✅ can use S3 as storage backend
  * 💾 relies on rclone-mount
* ✅ custom 404 pages

## [linx](https://github.com/ZizzyDizzyMC/linx-server/)
* originally [andreimarcu/linx-server](https://github.com/andreimarcu/linx-server) but development has ended
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* 🔵 some of its unique features have been added to copyparty as former linx users have migrated
  * file expiration timers, filename randomization
* ✅ password-protected files
  * 💾 password-protected folders + filekeys to skip the folder password seem to cover most usecases
* ✅ file deletion keys
* ✅ download files as torrents
* ✅ remote uploads (send a link to the server and it downloads it)
  * 💾 available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/wget.py)
* ✅ can use S3 as storage backend
  * 💾 relies on rclone-mount

## [h5ai](https://larsjung.de/h5ai/)
* ⚠️ read only; no upload/move/delete
* ⚠️ search hits the filesystem directly; not indexed/cached
* ✅ slick ui
* ✅ in-browser qr generator to share URLs
* 🔵 directory tree, image viewer, thumbnails, download-as-tar

## [autoindex](https://github.com/nielsAD/autoindex)
* ⚠️ read only; no upload/move/delete
* ✅ directory cache for faster browsing of cloud storage
  * 💾 local index/cache for recursive search (names/attrs/tags), but not for browsing

## [miniserve](https://github.com/svenstaro/miniserve)
* rust; cross-platform (windows, linux, mac)
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ no thumbnails / image viewer / audio player / file manager
* ⚠️ no filesystem indexing / search
* 🔵 upload, tar/zip download, qr-code
* ✅ faster at loading huge folders


# briefly considered
* [pydio](https://github.com/pydio/cells): python/agpl3, looks great, fantastic ux -- but needs mariadb, systemwide install
* [gossa](https://github.com/pldubouilh/gossa): go/mit, minimalistic, basic file upload, text editor, mkdir and rename (no delete/move)

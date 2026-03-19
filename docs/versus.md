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
* 🔥 = hazards


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
    * [hfs2](#hfs2) 🔥
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
    * [arozos](#arozos)
    * [updog](#updog)
    * [goshs](#goshs)
    * [gimme-that](#gimme-that)
    * [ass](#ass)
    * [linx](#linx)
    * [h5ai](#h5ai)
    * [autoindex](#autoindex)
    * [miniserve](#miniserve)
    * [pingvin-share](#pingvin-share)
* [briefly considered](#briefly-considered)
* [notes](#notes)


# recommendations

* [kodbox](https://github.com/kalcaddle/kodbox) ([review](#kodbox)) appears to be a fantastic alternative if you're not worried about running chinese software, with several advantages over copyparty
  * but anything you want to share must be moved into the kodbox filesystem
* [seafile](https://github.com/haiwen/seafile) ([review](#seafile)) and [nextcloud](https://github.com/nextcloud/server) ([review](#nextcloud)) could be decent alternatives if you need something heavier than copyparty
  * but their [license (AGPL)](https://snyk.io/learn/agpl-license/) is [thorny](https://opensource.google/documentation/reference/using/agpl-policy)
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

[C]: https://github.com/9001/copyparty "copyparty"
[h2]: https://github.com/rejetto/hfs2/ "hfs2"
[h3]: https://rejetto.com/hfs/ "hfs3"
[nc]: https://github.com/nextcloud/server "nextcloud"
[sf]: https://github.com/haiwen/seafile "seafile"
[rc]: https://github.com/rclone/rclone "rclone"
[df]: https://github.com/sigoden/dufs "dufs"
[cs]: https://github.com/chibisafe/chibisafe "chibisafe"
[kb]: https://github.com/kalcaddle/kodbox "kodbox"
[fb]: https://github.com/filebrowser/filebrowser "filebrowser"
[fg]: https://github.com/filegator/filegator "filegator"
[sg]: https://github.com/drakkan/sftpgo "sftpgo"
[az]: https://github.com/tobychui/arozos "arozos"

* `C` = [copyparty][C]
* `h2` = [hfs2][h2] 🔥
* `h3` = [hfs3][h3]
* `nc` = [nextcloud][nc]
* `sf` = [seafile][sf]
* `rc` = [rclone][rc], specifically `rclone serve webdav .`
* `df` = [dufs][df]
* `cs` = [chibisafe][cs]
* `kb` = [kodbox][kb]
* `fb` = [filebrowser][fb]
* `fg` = [filegator][fg]
* `sg` = [sftpgo][sg]
* `az` = [arozos][az]

some softwares not in the matrixes,
* [updog](#updog)
* [goshs](#goshs)
* [gimme-that](#gimmethat)
* [ass](#ass)
* [linx](#linx)
* [h5ai](#h5ai)
* [autoindex](#autoindex)
* [miniserve](#miniserve)
* [pingvin-share](#pingvin-share)

symbol legend,
* `█` = absolutely
* `╱` = partially
* `•` = maybe?
* ` ` = nope


## general

| feature / software      |[C]|[h2]|[h3]|[nc]|[sf]|[rc]|[df]|[cs]|[kb]|[fb]|[fg]|[sg]|[az]|
| ----------------------- |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| intuitive UX            |   | ╱ | █ | █ | █ |   | █ | █ | █ | █ | █ | █ | █ |
| config GUI              |   | █ | █ | █ | █ |   |   | █ | █ | █ |   | █ | █ |
| good documentation      |   |   | █ | █ | █ | █ | █ |   |   | █ | █ | ╱ | ╱ |
| runs on iOS             | ╱ |   |   |   |   | ╱ |   |   |   |   |   |   |   |
| runs on Android         | █ |   | █ |   |   | █ |   |   |   |   |   | █ |   |
| runs on WinXP           | █ | █ |   |   |   | █ |   |   |   |   |   |   |   |
| runs on Windows         | █ | █ | █ | █ | █ | █ | █ | ╱ | █ | █ | █ | █ | ╱ |
| runs on Linux           | █ | ╱ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| runs on Macos           | █ |   | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |   |
| runs on FreeBSD         | █ |   | █ | • | █ | █ | █ | • | █ | █ |   | █ |   |
| runs on Risc-V          | █ |   |   | █ | █ | █ |   | • |   | █ |   |   |   |
| runs on SGI IRIX        | █ |   |   | • |   |   |   |   |   |   |   |   |   |
| runs on aarch64-BE      | █ |   |   | • |   | • |   |   |   | • |   | • |   |
| portable binary         | █ | █ | █ |   |   | █ | █ |   |   | █ |   | █ | █ |
| zero setup, just go     | █ | █ | █ |   |   | ╱ | █ |   |   | █ |   | ╱ | █ |
| android app             | ╱ |   |   | █ | █ |   |   |   |   |   |   |   |   |
| iOS app                 | ╱ |   |   | █ | █ |   |   |   |   |   |   |   |   |

* `zero setup` = you can get a mostly working setup by just launching the app, without having to install any software or configure whatever
* `C`/copyparty remarks:
  * no gui for server settings; only for client-side stuff
  * runs on iOS / iPads using [a-Shell](https://holzschu.github.io/a-Shell_iOS/) (pretty good) or [iSH](https://ish.app/) (very slow) but cannot run in the background and is not able to share all of your phone storage (just a separate dedicated folder)
  * [android app](https://f-droid.org/en/packages/me.ocv.partyup/) is for uploading only
  * no iOS app but has [shortcuts](https://github.com/9001/copyparty#ios-shortcuts) for easy uploading
  * validated on aarch64-BE by [Øl Telecom](http://ol-tele.com/) during eth0:2025; [photo1](https://a.ocv.me/pub/g/nerd-stuff/cpp/servers/aallwinner.jpg?cache) and [diploma](https://a.ocv.me/pub/g/nerd-stuff/cpp/servers/be-ready.png?cache)
  * validated on [SGI IRIX](https://en.wikipedia.org/wiki/IRIX) ([an O2](https://en.wikipedia.org/wiki/SGI_O2)) by [Øl Telecom](http://ol-tele.com/) during 39c3; [photo1](https://a.ocv.me/pub/g/nerd-stuff/cpp/servers/sgi-o2.jpg?cache) and [screenshot](https://a.ocv.me/pub/g/nerd-stuff/cpp/servers/sgi-o2.png?cache)
* `h2`/hfs2 runs on linux through wine
* `rc`/rclone must be started with the command `rclone serve webdav .` or similar
* `cs`/chibisafe has undocumented windows support
* `sg`/sftpgo:
  * Must be launched with a command
  * On Termux, just run `pkg in sftpgo`
* `az`/arozos has partial windows support


## file transfer

*the thing that copyparty is actually kinda good at*

| feature / software      |[C]|[h2]|[h3]|[nc]|[sf]|[rc]|[df]|[cs]|[kb]|[fb]|[fg]|[sg]|[az]|
| ----------------------- |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| download folder as zip  | █ | █ | █ | █ | ╱ |   | █ |   | █ | █ | ╱ | █ | ╱ |
| download folder as tar  | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| upload                  | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | ╱ | █ | █ |
| parallel uploads        | █ |   |   | █ | █ |   | • |   | █ | █ | █ |   | █ |
| resumable uploads       | █ |   | █ |   |   |   |   |   | █ | █ | █ | ╱ |   |
| upload segmenting       | █ |   | █ | █ |   |   |   | █ | █ | █ | █ | ╱ | █ |
| upload acceleration     | █ |   |   |   |   |   |   |   | █ |   | █ |   |   |
| upload verification     | █ |   |   | █ | █ |   |   |   | █ |   |   |   |   |
| upload deduplication    | █ |   |   |   | █ |   |   |   | █ |   |   |   |   |
| upload a 999 TiB file   | █ |   |   |   | █ | █ | • |   | █ |   | █ | ╱ | ╱ |
| CTRL-V from device      | █ |   |   | █ |   |   |   |   |   |   |   |   |   |
| race the beam ("p2p")   | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| "tail -f" streaming     | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| keep last-modified time | █ |   | █ | █ | █ | █ |   |   |   |   |   | █ |   |
| upload rules            | ╱ | ╱ | ╱ | ╱ | ╱ |   |   | ╱ | ╱ |   | ╱ | ╱ | ╱ |
| ┗ max disk usage        | █ | █ | █ |   | █ |   |   |   | █ |   |   | █ | █ |
| ┗ max filesize          | █ |   |   |   |   |   |   | █ |   |   | █ | █ | █ |
| ┗ max items in folder   | █ |   |   |   |   |   |   |   |   |   |   | ╱ |   |
| ┗ max file age          | █ |   |   |   |   |   |   |   | █ |   |   |   |   |
| ┗ max uploads over time | █ |   |   |   |   |   |   |   |   |   |   | ╱ |   |
| ┗ compress before write | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| ┗ randomize filename    | █ |   |   |   |   |   |   | █ | █ |   |   |   |   |
| ┗ mimetype reject-list  | ╱ |   |   |   |   |   |   |   | • | ╱ |   | ╱ | • |
| ┗ extension reject-list | ╱ |   |   |   |   |   |   | █ | • | ╱ |   | ╱ | • |
| ┗ upload routing        | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| checksums provided      |   |   |   | █ | █ |   |   |   | █ | ╱ |   |   |   |
| cloud storage backend   | ╱ | ╱ | ╱ | █ | █ | █ | ╱ |   |   | ╱ | █ | █ | ╱ |

* `upload segmenting` = files are sliced into chunks, making it possible to upload files larger than 100 MiB on cloudflare for example

* `upload acceleration` = each file can be uploaded using several TCP connections, which can offer a huge speed boost over huge distances / on flaky connections -- like the good old [download accelerators](https://en.wikipedia.org/wiki/GetRight) except in reverse

* `upload verification` = uploads are checksummed or otherwise confirmed to have been transferred correctly

* `CTRL-V from device` = press CTRL-C in Windows Explorer (or whatever) and paste into the webbrowser to upload it

* `race the beam` = files can be downloaded while they're still uploading; downloaders are slowed down such that the uploader is always ahead

* `tail -f` = when viewing or downloading a logfile, the connection can remain open to keep showing new lines as they are added in real time

* `upload routing` = depending on filetype / contents / uploader etc., the file can be redirected to another location or otherwise transformed; mitigates limitations such as [sharex#3992](https://github.com/ShareX/ShareX/issues/3992)
  * copyparty example: [reloc-by-ext](https://github.com/9001/copyparty/tree/hovudstraum/bin/hooks#before-upload)

* `checksums provided` = when downloading a file from the server, the file's checksum is provided for verification client-side

* `cloud storage backend` = able to serve files from (and write to) s3 or similar cloud services; `╱` means the software can do this with some help from `rclone mount` as a bridge

* `C`/copyparty can reject uploaded files (based on complex conditions), for example [by extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) or [mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py)
* `sf`/seafile download-as-zip is not streaming; it creates the full zipfile before download can start, and fails on big folders
* `fg`/filebrowser remarks:
  * can provide checksums for single files on request
  * can probably do extension/mimetype rejection similar to copyparty
* `fg`/filegator download-as-zip is not streaming; it creates the full zipfile before download can start
* `sg`/sftpgo:
  * resumable/segmented uploads only over SFTP, not over HTTP
  * upload rules are totals only, not over time
  * can probably do extension/mimetype rejection similar to copyparty
* `az`/arozos download-as-zip is not streaming; it creates the full zipfile before download can start, and fails on big folders


## protocols and client support

| feature / software      |[C]|[h2]|[h3]|[nc]|[sf]|[rc]|[df]|[cs]|[kb]|[fb]|[fg]|[sg]|[az]|
| ----------------------- |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| serve https             | █ |   | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| serve webdav            | █ |   |   | █ | █ | █ | █ |   | █ |   |   | █ | █ |
| serve ftp  (tcp)        | █ |   |   |   |   | █ |   |   |   |   |   | █ | █ |
| serve ftps (tls)        | █ |   |   |   |   | █ |   |   |   |   |   | █ |   |
| serve tftp (udp)        | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| serve sftp (ssh)        | █ |   |   |   |   | █ |   |   |   |   |   | █ | █ |
| serve smb/cifs          | ╱ |   |   |   |   | █ |   |   |   |   |   |   |   |
| serve dlna              |   |   |   |   |   | █ |   |   |   |   |   |   |   |
| listen on unix-socket   | █ |   |   | █ | █ |   | █ | █ | █ | █ | █ | █ |   |
| zeroconf                | █ |   |   |   |   |   |   |   |   |   |   |   | █ |
| supports netscape 4     | ╱ |   |   |   |   | █ |   |   |   |   | • |   | ╱ |
| ...internet explorer 6  | ╱ | █ |   | █ |   | █ |   |   |   |   | • |   | ╱ |
| mojibake filenames      | █ |   |   | • | • | █ | █ | • | █ | • |   | ╱ |   |
| undecodable filenames   | █ |   |   | • | • | █ |   | • |   |   |   | ╱ |   |

* `webdav` = protocol convenient for mounting a remote server as a local filesystem; see zeroconf:
* `zeroconf` = the server announces itself on the LAN, [automatically appearing](https://user-images.githubusercontent.com/241032/215344737-0eae8d98-9496-4256-9aa8-cd2f6971810d.png) on other zeroconf-capable devices
* `mojibake filenames` = filenames decoded with the wrong codec and then reencoded (usually to utf-8), so `宇多田ヒカル` might look like `ëFæ╜ôcâqâJâï`
* `undecodable filenames` = pure binary garbage which cannot be parsed as utf-8
  * you can successfully play `$'\355\221'` with mpv through mounting a remote copyparty server with rclone, pog
* `C`/copyparty remarks:
  * extremely minimal samba/cifs server
  * netscape 4 / ie6 support is mostly listed as a joke altho some people have actually found it useful ([ie4 tho](https://user-images.githubusercontent.com/241032/118192791-fb31fe00-b446-11eb-9647-898ea8efc1f7.png))
* `sg`/sftpgo translates mojibake filenames into valid utf-8 (information loss)
* `az`/arozos has readonly-support for older browsers; no uploading


## server configuration

| feature / software      |[C]|[h2]|[h3]|[nc]|[sf]|[rc]|[df]|[cs]|[kb]|[fb]|[fg]|[sg]|[az]|
| ----------------------- |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| config from cmd args    | █ |   | █ |   |   | █ | █ |   |   | █ |   | ╱ | ╱ |
| config files            | █ | █ | █ | ╱ | ╱ | █ |   | █ |   | █ | • | ╱ | ╱ |
| runtime config reload   | █ | █ | █ |   |   |   |   | █ | █ | █ | █ |   | █ |
| same-port http / https  | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| listen multiple ports   | █ |   |   |   |   |   |   |   |   |   |   | █ |   |
| virtual file system     | █ | █ | █ |   |   |   | █ |   |   |   |   | █ |   |
| reverse-proxy ok        | █ |   | █ | █ | █ | █ | █ | █ | • | • | • | █ | ╱ |
| folder-rproxy ok        | █ |   | █ |   | █ | █ |   | • | • | █ | • |   | • |

* `folder-rproxy` = reverse-proxying without dedicating an entire (sub)domain, using a subfolder instead
* `sg`/sftpgo:
  * config: user can be added by cmd command in [Portable mode](https://docs.sftpgo.com/2.6/cli/#portable-mode); if not in  Portable mode users must be added through gui / api calls
* `az`/arozos:
  * configuration is primarily through GUI
  * reverse-proxy is not guaranteed to see the correct client IP


## server capabilities

| feature / software      |[C]|[h2]|[h3]|[nc]|[sf]|[rc]|[df]|[cs]|[kb]|[fb]|[fg]|[sg]|[az]|
| ----------------------- |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| accounts                | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ | █ |
| per-account chroot      |   |   |   |   |   |   |   |   |   |   |   | █ |   |
| single-sign-on          | ╱ |   |   | █ | █ |   |   |   | • |   |   |   |   |
| token auth              | ╱ |   |   | █ | █ |   |   | █ |   |   |   |   | █ |
| 2fa                     | ╱ |   | / | █ | █ |   |   |   |   |   |   | █ | ╱ |
| per-volume permissions  | █ | █ | █ | █ | █ | █ | █ |   | █ | █ | ╱ | █ | █ |
| per-folder permissions  | ╱ |   | █ | █ | █ |   | █ |   | █ | █ | ╱ | █ | █ |
| per-file permissions    |   |   | █ | █ | █ |   | █ |   | █ |   |   |   | █ |
| per-file passwords      | █ |   |   | █ | █ |   | █ |   | █ |   |   | █ | █ |
| unmap subfolders        | █ |   | █ |   |   |   | █ |   |   | █ | ╱ | • |   |
| index.html blocks list  | ╱ |   |   |   |   |   | █ |   |   | • |   |   |   |
| write-only folders      | █ |   | █ |   | █ |   |   |   |   |   | █ | █ |   |
| files stored as-is      | █ | █ | █ | █ |   | █ | █ |   |   | █ | █ | █ | █ |
| file versioning         |   |   |   | █ | █ |   |   |   |   |   |   |   |   |
| file encryption         |   |   |   | █ | █ | █ |   |   |   |   |   | █ |   |
| file indexing           | █ |   | █ | █ | █ |   |   | █ | █ | █ |   |   |   |
| ┗ per-volume db         | █ |   | • | • | • |   |   | • | • |   |   |   |   |
| ┗ db stored in folder   | █ |   |   |   |   |   |   | • | • | █ |   |   |   |
| ┗ db stored out-of-tree | █ |   | █ | █ | █ |   |   | • | • | █ |   |   |   |
| ┗ existing file tree    | █ |   | █ |   |   |   |   |   |   | █ |   |   |   |
| file action event hooks | █ |   |   |   |   |   |   |   |   | █ |   | █ | • |
| one-way folder sync     | █ |   |   | █ | █ | █ |   |   |   |   |   |   |   |
| full sync               |   |   |   | █ | █ |   |   |   |   |   |   |   |   |
| speed throttle          |   | █ | █ |   |   | █ |   |   | █ |   |   | █ |   |
| anti-bruteforce         | █ | █ | █ | █ | █ |   |   |   | • |   |   | █ | • |
| dyndns updater          |   | █ | █ |   |   |   |   |   |   |   |   |   |   |
| self-updater            | ╱ |   | █ |   |   |   |   |   |   |   |   |   | █ |
| log rotation            | █ |   | █ | █ | █ |   |   | • | █ |   |   | █ | • |
| upload tracking / log   | █ | █ | • | █ | █ |   |   | █ | █ |   |   | ╱ | █ |
| prometheus metrics      | █ |   |   | █ |   |   |   |   |   |   |   | █ |   |
| curl-friendly ls        | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| curl-friendly upload    | █ |   | █ |   |   | █ | █ | • |   |   |   |   |   |

* `unmap subfolders` = "shadowing"; mounting a local folder in the middle of an existing filesystem tree in order to disable access below that path
* `files stored as-is` = uploaded files are trivially readable from the server HDD, not sliced into chunks or in weird folder structures or anything like that
* `db stored in folder` = filesystem index can be written to a database file inside the folder itself
* `db stored out-of-tree` = filesystem index can be stored some place else, not necessarily inside the shared folders
* `existing file tree` = will index any existing files it finds
* `file action event hooks` = run script before/after upload, move, rename, ...
* `one-way folder sync` = like rsync, optionally deleting unexpected files at target
* `full sync` = stateful, dropbox-like sync
* `speed throttle` = rate limiting (per ip, per user, per connection, anything like that)
* `curl-friendly ls` = returns a [sortable plaintext folder listing](https://user-images.githubusercontent.com/241032/215322619-ea5fd606-3654-40ad-94ee-2bc058647bb2.png) when curled
* `curl-friendly upload` = uploading with curl is just `curl -T some.bin http://.../`
* `C`/copyparty remarks:
  * single-sign-on, token-auth, and 2fa is *possible* through authelia/authentik or similar, but nobody's made an example yet
  * one-way folder sync from local to server can be done efficiently with [u2c.py](https://github.com/9001/copyparty/tree/hovudstraum/bin#u2cpy), or with webdav and conventional rsync
  * can hot-reload config files (with just a few exceptions)
  * can set per-folder permissions if that folder is made into a separate volume, so there is configuration overhead
  * `index.html` on its own does not prevent directory listing, but permission `h` (instead of `r`) enforces index.html to be returned instead of folder contents
  * [version-checker](https://github.com/9001/copyparty/#version-checker) can check if the current version has a known vulnerability and immediately exit/shutdown, but automatic self-updating is **not** available
  * [event hooks](https://github.com/9001/copyparty/tree/hovudstraum/bin/hooks) ([discord](https://user-images.githubusercontent.com/241032/215304439-1c1cb3c8-ec6f-4c17-9f27-81f969b1811a.png), [desktop](https://user-images.githubusercontent.com/241032/215335767-9c91ed24-d36e-4b6b-9766-fb95d12d163f.png)) inspired by filebrowser, as well as the more complex [media parser](https://github.com/9001/copyparty/tree/hovudstraum/bin/mtag) alternative
  * upload history can be visualized using [partyjournal](https://github.com/9001/copyparty/blob/hovudstraum/bin/partyjournal.py)
* `fg`/filegator remarks:
  * `per-* permissions` -- can limit a user to one folder and its subfolders
  * `unmap subfolders` -- can globally filter a list of paths
* `sg`/sftpgo:
  * `file action event hooks` also include on-download triggers
  * `upload tracking / log` in main logfile
* `az`/arozos:
  * `2fa` maybe possible through LDAP/Oauth
* `h3`/hfs3
  * `2fa` available by installing a plugin

## client features

| feature / software      |[C]|[h2]|[h3]|[nc]|[sf]|[rc]|[df]|[cs]|[kb]|[fb]|[fg]|[sg]|[az]|
| ----------------------  |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| single-page app         | █ |   | █ | █ | █ |   |   | █ | █ | █ | █ |   | █ |
| themes                  | █ | █ | █ | █ |   |   |   |   | █ |   |   |   |   |
| directory tree nav      | █ | ╱ |   |   | █ |   |   |   | █ |   | ╱ |   |   |
| multi-column sorting    | █ |   |   |   |   |   |   |   |   |   |   | █ |   |
| thumbnails              | █ |   | / | ╱ | ╱ |   |   | █ | █ | ╱ |   |   | █ |
| ┗ image thumbnails      | █ |   | / | █ | █ |   |   | █ | █ | █ |   |   | █ |
| ┗ video thumbnails      | █ |   |   | █ | █ |   |   |   | █ |   |   |   | █ |
| ┗ audio spectrograms    | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| audio player            | █ |   | ╱ | █ | █ |   |   |   | █ | ╱ |   | ╱ | █ |
| ┗ gapless playback      | █ |   |   |   |   |   |   |   | • |   |   |   |   |
| ┗ audio equalizer       | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| ┗ waveform seekbar      | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| ┗ OS integration        | █ |   | █ |   |   |   |   |   |   |   |   |   |   |
| ┗ transcode to lossy    | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| video player            | █ |   | █ | █ | █ |   |   |   | █ | █ |   | ╱ | █ |
| ┗ video transcoding     |   |   | / |   |   |   |   |   | █ |   |   |   |   |
| audio BPM detector      | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| audio key detector      | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| search by path / name   | █ | █ | █ | █ | █ |   | █ |   | █ | █ | ╱ |   |   |
| search by date / size   | █ |   |   |   | █ |   |   | █ | █ |   |   |   |   |
| search by bpm / key     | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| search by custom tags   |   |   |   |   |   |   |   | █ | █ |   |   |   |   |
| search in file contents |   |   |   | █ | █ |   |   |   | █ |   |   |   |   |
| search by custom parser | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| find local file         | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| undo recent uploads     | █ |   |   |   |   |   |   |   |   |   |   |   |   |
| create directories      | █ |   | █ | █ | █ | ╱ | █ | █ | █ | █ | █ | █ | █ |
| image viewer            | █ |   | █ | █ | █ |   |   |   | █ | █ | █ | █ | █ |
| markdown viewer         | █ |   | / |   | █ |   |   |   | █ | ╱ | ╱ |   | █ |
| markdown editor         | █ |   |   |   | █ |   |   |   | █ | ╱ | ╱ | ╱ | █ |
| readme.md in listing    | █ |   | / | █ |   |   |   |   |   |   |   |   |   |
| rename files            | █ | █ | █ | █ | █ | ╱ | █ |   | █ | █ | █ | █ | █ |
| batch rename            | █ |   |   |   |   |   |   |   | █ |   |   |   |   |
| cut / paste files       | █ | █ | █ | █ | █ |   |   |   | █ |   |   |   | █ |
| move files              | █ | █ | █ | █ | █ |   | █ |   | █ | █ | █ | █ | █ |
| delete files            | █ | █ | █ | █ | █ | ╱ | █ | █ | █ | █ | █ | █ | █ |
| copy files              |   |   | / |   | █ |   |   |   | █ | █ | █ | █ | █ |

* `single-page app` = multitasking; possible to continue navigating while uploading
* `audio player » os-integration` = use the [lockscreen](https://user-images.githubusercontent.com/241032/142711926-0700be6c-3e31-47b3-9928-53722221f722.png) or [media hotkeys](https://user-images.githubusercontent.com/241032/215347492-b4250797-6c90-4e09-9a4c-721edf2fb15c.png) to play/pause, prev/next song
* `search by custom tags` = ability to tag files through the UI and search by those
* `find local file` = drop a file into the browser to see if it exists on the server
* `undo recent uploads` = accounts without delete permissions have a time window where they can undo their own uploads
* `C`/copyparty has teeny-tiny skips playing gapless albums depending on audio codec (opus best)
* `h2`/hfs2 has a very basic directory tree view, not showing sibling folders
* `rc`/rclone can do some file management (mkdir, rename, delete) when hosting througn webdav
* `fg`/filebrowser remarks:
  * audio playback does not continue into next song
  * plaintext viewer/editor
* `fg`/filegator directory tree is a modal window
* `sg`/sftpgo remarks:
  * audio/video playback does not continue into next song/video
  * plaintext viewer/editor


## integration

| feature / software      |[C]|[h2]|[h3]|[nc]|[sf]|[rc]|[df]|[cs]|[kb]|[fb]|[fg]|[sg]|[az]|
| ----------------------- |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| OS alert on upload      | ╱ |   |   |   |   |   |   |   |   | ╱ |   | ╱ |   |
| discord                 | ╱ |   |   |   |   |   |   |   |   | ╱ |   | ╱ |   |
| ┗ announce uploads      | ╱ |   |   |   |   |   |   |   |   |   |   | ╱ |   |
| ┗ custom embeds         |   |   |   |   |   |   |   |   |   |   |   | ╱ |   |
| sharex                  | █ |   |   | █ |   | █ | ╱ | █ |   |   |   |   |   |
| flameshot               |   |   |   |   |   | █ |   |   |   |   |   |   |   |

* sharex `╱` = yes, but does not provide example sharex config
* `C`/copyparty remarks:
  * `OS alert on upload` available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/notify.py)
  * `discord » announce uploads` available as [a plugin](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/discord-announce.py)
* `fg`/filebrowser can probably pull those off with command runners similar to copyparty
* `sg`/sftpgo has nothing built-in but is very extensible


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
| arozos             | go     | ░ gpl3 | 531 MB |
| updog              | python | █ mit  |  17 MB |
| goshs              | go     | █ mit  |  11 MB |
| gimme-that         | python | █ mit  | 4.8 MB |
| ass                | ts     | █ isc  |    •   |
| linx               | go     | ░ gpl3 |  20 MB |
| h5ai               | php    | █ mit  |    •   |
| autoindex          | go     | █ mpl2 |  11 MB |
| miniserve          | rust   | █ mit  |   2 MB |
| pingvin-share      | go     | █ bsd2 | 487 MB |

* `size` = binary (if available) or installed size of program and its dependencies
  * copyparty size is for the [standalone python](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) file; the [windows exe](https://github.com/9001/copyparty/releases/latest/download/copyparty.exe) is **6 MiB**


# reviews

* ✅ are advantages over copyparty
  * 💾 are what copyparty offers as an alternative
* 🔵 are similarities
* ⚠️ are disadvantages (something copyparty does "better")
* 🔥 are hazards

## [copyparty](https://github.com/9001/copyparty)
* resumable uploads which are verified server-side
* upload segmenting allows for potentially much faster uploads on some connections, and terabyte-sized files even on cloudflare
  * both of the above are surprisingly uncommon features
* very cross-platform (python, no dependencies)

## [hfs2](https://github.com/rejetto/hfs2/)
* the OG, the legend (now replaced by [hfs3](#hfs3))
* 🔥 hfs2 is dead and dangerous! unfixed RCE: [info](https://github.com/rejetto/hfs2/issues/44), [info](https://github.com/drapid/hfs/issues/3), [info](https://asec.ahnlab.com/en/67650/)
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ windows-only
* ✅ config GUI
* vfs with gui config, per-volume permissions
* starting to show its age, hence the rewrite:

## [hfs3](https://rejetto.com/hfs/)
* nodejs; cross-platform
* vfs with gui config, per-volume permissions
* tested locally, v0.53.2 on archlinux
* 🔵 uploads are resumable
* ⚠️ uploads are not accelerated (copyparty is 3x faster across the atlantic)
* ⚠️ uploads are not integrity-checked
* ⚠️ uploading small files is decent; `107` files per sec (copyparty does `670`/sec, 6x faster)
* ⚠️ doesn't support crazy filenames
* ✅ config GUI
* ✅ download counter
* ✅ watch active connections
* ✅ plugins

## [nextcloud](https://github.com/nextcloud/server)
* php, mariadb
* tested locally, [linuxserver/nextcloud](https://hub.docker.com/r/linuxserver/nextcloud) v30.0.2 (sqlite)
* ⚠️ [isolated on-disk file hierarchy] in per-user folders
  * not that bad, can probably be remedied with bindmounts or maybe symlinks
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * 🔵 uploads are segmented; no filesize limit, even on cloudflare
* ⚠️ uploading small files is slow; `4` files per sec (copyparty does `670`/sec, 160x faster)
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
* tested locally, [official container](https://manual.seafile.com/latest/docker/deploy_seafile_with_docker/) v11.0.13
* ⚠️ [isolated on-disk file hierarchy](https://manual.seafile.com/maintain/seafile_fsck/), incompatible with other software
  * *much worse than nextcloud* in that regard
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
* ⚠️ uploading small files is slow; `4.7` files per sec (copyparty does `670`/sec, 140x faster)
* ⚠️ big folders cannot be zip-downloaded
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
* tested locally, v0.43.0 on archlinux (plain binary)
* ⚠️ uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
  * ⚠️ across the atlantic, copyparty is 3x faster
* ⚠️ uploading small files is decent; `97` files per sec (copyparty does `670`/sec, 7x faster)
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
* this thing is insane (but is getting competition from [arozos](#arozos))
* php; [docker](https://hub.docker.com/r/kodcloud/kodbox)
* 🔵 *upload segmenting, acceleration, and integrity checking!*
  * ⚠️ but uploads are not resumable(?)
* ⚠️ not portable
* ⚠️ isolated on-disk file hierarchy, incompatible with other software
* ⚠️ uploading small files to copyparty is 16x faster
* ⚠️ uploading large files to copyparty is 3x faster
* ⚠️ http/webdav only; no ftp or zeroconf
* ⚠️ some parts of the GUI are in chinese
* ✅ fantastic ui/ux
* ✅ control panel for server settings and user management
* ✅ file tags; file discussions!?
* ✅ video transcoding
* ✅ unzip uploaded archives
* ✅ IDE with syntax highlighting
* ✅ wysiwyg editor for openoffice files

## [filebrowser](https://github.com/filebrowser/filebrowser)
* go; cross-platform (windows, linux, mac)
* tested locally, v2.31.2 on archlinux (plain binary)
* 🔵 uploads are resumable and segmented
* 🔵 multiple files are uploaded in parallel, but...
  * ⚠️ big files are not accelerated (copyparty is 5x faster across the atlantic)
* ⚠️ uploads are not integrity-checked
* ⚠️ uploading small files is decent; `69` files per sec (copyparty does `670`/sec, 9x faster)
* ⚠️ http only; no webdav / ftp / zeroconf
* ⚠️ doesn't support crazy filenames
* ⚠️ no directory tree nav
* ⚠️ limited file search
* ✅ settings gui
* ✅ good ui/ux
  * ⚠️ but no directory tree for navigation
* ✅ user signup
* ✅ command runner / remote shell
* ✅ more efficient; can handle around twice as much simultaneous traffic
* note: keep an eye on [gtsteffaniak's fork](https://github.com/gtsteffaniak/filebrowser)

## [filegator](https://github.com/filegator/filegator)
* php; cross-platform (windows, linux, mac)
* 🔵 *it has upload segmenting and acceleration*
  * ⚠️ but uploads are still not integrity-checked
  * ⚠️ on copyparty, uploads are 40x faster
    * compared to the official filegator docker example which might be bad
* ⚠️ http only; no webdav / ftp / zeroconf
* ⚠️ does not support symlinks
* ⚠️ expensive download-as-zip feature
* ⚠️ doesn't support crazy filenames
* ⚠️ limited file search

## [sftpgo](https://github.com/drakkan/sftpgo)
* go; cross-platform (windows, linux, mac)
* ⚠️ http uploads not resumable / accelerated / integrity-checked
  * ⚠️ on cloudflare: max upload size 100 MiB
  * ⚠️ across the atlantic, copyparty is 2.5x faster
  * 🔵 sftp uploads are resumable
* ⚠️ web UI is very minimal + a bit slow
  * ⚠️ no thumbnails
* ⚠️ no filesystem indexing / search
* ⚠️ no zeroconf (mdns/ssdp)
* ⚠️ impractical directory URLs
* ⚠️ AGPL licensed
* 🔵 uploading small files is fast; `340` files per sec (copyparty does `670`/sec)
* 🔵 sftp, ftp, ftps, webdav
* ✅ settings gui
* ✅ acme (automatic tls certs)
  * 💾 relies on caddy/certbot/acme.sh
* ✅ at-rest encryption
  * 💾 relies on LUKS/BitLocker
* ✅ can use S3/GCS as storage backend
  * 💾 relies on rclone-mount
* ✅ on-download event hook (otherwise same as copyparty)
* ✅ more extensive permissions control

## [arozos](https://github.com/tobychui/arozos)
* big suite of applications similar to [kodbox](#kodbox), copyparty is better at downloading/uploading/music/indexing but arozos has other advantages
* go; primarily linux (limited support for windows)
* ⚠️ needs root
* ⚠️ uploads not resumable / integrity-checked
* ⚠️ uploading small files to copyparty is 2.7x faster
* ⚠️ uploading large files to copyparty is at least 10% faster
  * arozos is websocket-based, 512 KiB chunks; writes each chunk to separate files and then merges
  * copyparty splices directly into the final file; faster and better for the HDD and filesystem
* ⚠️ across the atlantic, uploading to copyparty is 6x faster
* ⚠️ no directory tree navpane; not as easy to navigate
* ⚠️ download-as-zip is not streaming; creates a temp.file on the server
* ⚠️ not self-contained (pulls from jsdelivr)
* ⚠️ has an audio player, but supports less filetypes
* ⚠️ limited support for configuring real-ip detection
* ✅ settings gui
* ✅ good-looking gui
* ✅ an IDE, msoffice viewer, rich host integration, much more

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

## [pingvin-share](https://github.com/stonith404/pingvin-share)
* node; linux (docker)
* mainly for uploads, not a general file server
* 🔵 uploads are segmented (avoids cloudflare size limit)
* 🔵 segments are written directly to target file (HDD-friendly)
* ⚠️ uploads not resumable after a browser or laptop crash
* ⚠️ uploads are not accelerated / integrity-checked
  * ⚠️ across the atlantic, copyparty is 3x faster
    * measured with chunksize 96 MiB; pingvin's default 10 MiB is much slower
* ⚠️ can't upload folders with subfolders
* ⚠️ no upload ETA
* 🔵 expiration times, shares, upload-undo
* ✅ config + user-registration gui
* ✅ built-in OpenID and LDAP support
  * 💾 [IdP middleware](https://github.com/9001/copyparty#identity-providers) and config-files
* ✅ probably more than one person who understands the code



# briefly considered
* [pydio](https://github.com/pydio/cells): python/agpl3, looks great, fantastic ux -- but needs mariadb, systemwide install
* [gossa](https://github.com/pldubouilh/gossa): go/mit, minimalistic, basic file upload, text editor, mkdir and rename (no delete/move)



# notes

* high-latency connections (cross-atlantic uploads) can be accurately simulated with `tc qdisc add dev eth0 root netem delay 100ms`

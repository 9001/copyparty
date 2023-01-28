▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2023-0112-0515  `v1.5.6`  many hands

hello from warsaw airport (goodbye japan ;_;)
* read-only demo server at https://a.ocv.me/pub/demo/

## new features
* multiple upload handshakes in parallel
  * around **5x faster** when uploading small files
  * or **50x faster** if the server is on the other side of the planet
    * just crank up the `parallel uploads` like crazy (max is 64)
* upload ui: total time and average speed is shown on completion

## bugfixes
* browser ui didn't allow specifying number of threads for file search
* dont panic if a digit key is pressed while viewing an image
* workaround [linux kernel bug](https://utcc.utoronto.ca/~cks/space/blog/linux/KernelBindBugIn6016) causing log spam on dualstack
  * ~~related issue (also mostly harmless) will be fixed next relese 010770684db95bece206943768621f2c7c27bace~~ 
    * they fixed it in linux 6.1 so these workarounds will be gone too



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-1230-0754  `v1.5.5`  made in japan

hello from tokyo
* read-only demo server at https://a.ocv.me/pub/demo/

## new features
* image viewer now supports heif, avif, apng, svg
* [partyfuse and up2k.py](https://github.com/9001/copyparty/tree/hovudstraum/bin): option to read password from textfile

## bugfixes
* thumbnailing could fail if a primitive build of libvips is installed
* ssdp was wonky on dualstack ipv6
* mdns could crash on networks with invalid routes
* support fat32 timestamp precisions
  * fixes spurious file reindexing in volumes located on SD cards on android tablets which lie about timestamps until the next device reboot or filesystem remount



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-1213-1956  `v1.5.3`  folder-sync + turbo-rust

* read-only demo server at https://a.ocv.me/pub/demo/

## new features
* one-way folder sync (client to server) using [up2k.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/README.md#up2kpy) `-z --dr`
  * great rsync alternative when combined with `-e2ds --hardlink` deduplication on the server
* **50x faster** when uploading small files to HDD, especially SMR
  * by switching sqlite to WAL which carries a small chance of temporarily forgetting the ~200 most recent uploads if you have a power outage or your OS crashes; see `--help-dbd` if you have `-mtp` plugins which produces metadata you can't afford to lose
* location-based [reverse-proxying](https://github.com/9001/copyparty/#reverse-proxy) (but it's still recommended to use a dedicated domain/subdomain instead)
* IPv6 link-local automatically enabled for TCP and zeroconf on NICs without a routable IPv6
* zeroconf network filters now accept subnets too, for example `--z-on 192.168.0.0/16`
* `.hist` folders are hidden on windows
* ux:
  * more accurate total ETA on upload
  * sorting of batch-unpost links was unintuitive / dangerous
  * hotkey `Y` turns files into download links if nothing's selected
  * option to replace or disable the mediaplayer-toggle mouse cursor with `--mpmc`

## bugfixes
* WAL probably/hopefully fixes #10 (we'll know in 6 months roughly)
* repair db inconsistencies (which can happen if terminated during startup)
* [davfs2](https://wiki.archlinux.org/title/Davfs2) did not approve of the authentication prompt
* the `connect` button on the control-panel didn't work on phones
* couldn't specify windows NICs in arguments `--z-on` / `--z-off` and friends
* ssdp xml escaping for `--zsl` URL
* no longer possible to accidentally launch multiple copyparty instances on the same port on windows



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-1203-2048  `v1.5.1`  babel

named after [that other thing](https://en.wikipedia.org/wiki/Tower_of_Babel), not [the song](https://soundcloud.com/kanaze/babel-dimension-0-remix)
* read-only demo server at https://a.ocv.me/pub/demo/

## new features
* new protocols!
  * native IPv6 support, no longer requiring a reverse-proxy for that
  * [webdav server](https://github.com/9001/copyparty#webdav-server) -- read/write-access to copyparty straight from windows explorer, macos finder, kde/gnome
  * [smb/cifs server](https://github.com/9001/copyparty#smb-server) -- extremely buggy and unsafe, for when there is no other choice
  * [zeroconf](https://github.com/9001/copyparty#zeroconf) -- copyparty announces itself on the LAN, showing up in various file managers
    * [mdns](https://github.com/9001/copyparty#mdns) -- macos/kde/gnome + makes copyparty available at http://hostname.local/
    * [ssdp](https://github.com/9001/copyparty#ssdp) -- windows
  * commands to mount copyparty as a local disk are in the web-UI at control-panel --> `connect`
* detect buggy / malicious clients spamming the server with idle connections
  * first tries to be nice with `Connection: close` (enough to fix windows-webdav)
  * eventually bans the IP for `--loris` minutes (default: 1 hour)
* new arg `--xlink` for cross-volume detection of duplicate files on upload
* new arg `--no-snap` to disable upload tracking on restart
  * will not create `.hist` folders unless required for thumbnails or markdown backups
* [config includes](https://github.com/9001/copyparty/blob/hovudstraum/docs/example2.conf) -- split your config across multiple config files
* ux improvements
  * hotkey `?` shows a summary of all the hotkeys
  * hotkey `Y` to download selected files
  * position indicator when hovering over the audio scrubber
  * textlabel on the volume slider
  * placeholder values in textboxes
  * options to hide scrollbars, compact media player, follow playing song
  * phone-specific
    * buttons for prev/next folder
    * much better ui for hiding folder columns

## bugfixes
* now possible to upload files larger than 697 GiB
  * technically a [breaking change](https://github.com/9001/copyparty#breaking-changes) if you wrote your own up2k client
    * please let me know if you did because that's awesome
* several macos issues due to hardcoded syscall numbers
* sfx: fix python 3.12 support (forbids nullbytes in source code)
* use ctypes to discover network config -- fixes grapheneos, non-english windows
* detect firefox showing stale markdown documents in the editor
* detect+ban password bruteforcing on ftp too
* http 206 failing on empty files
* incorrect header timestamps on non-english locales
* remind ftp clients that you cannot cd into an image file -- fixes kde dolphin
* ux fixes
  * uploader survives running into inaccessible folders
  * middleclick documents in the textviewer sidebar to open in a new tab
  * playing really long audio files (1 week or more) would spinlock the browser

## other changes
* autodetect max number of clients based on OS limits
  * `-nc` is probably no longer necessary when running behind a reverse-proxy
* allow/try playing mkv files in chrome
* markdown documents returned as plaintext unless `?v`
* only compress `-lo` logfiles if filename ends with `.xz`
* changed sfx compression from bz2 to gz
  * startup is slightly faster
  * better compatibility with embedded linux
* copyparty64.exe -- 64bit edition for [running inside WinPE](https://user-images.githubusercontent.com/241032/205454984-e6b550df-3c49-486d-9267-1614078dd0dd.png)
  * which was an actual feature request, believe it or not!
* more attempts at avoiding the [firefox fd leak](https://bugzilla.mozilla.org/show_bug.cgi?id=1790500)
  * if you are uploading many small files and the browser keeps crashing, use chrome instead
    * or the commandline client, which is now available for download straight from copyparty
      * control-panel --> `connect` --> `up2k.py`



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-1013-1937  `v1.4.6`  wav2opus

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: *This version*

## bugfixes
* the option to transcode flac to opus while playing audio in the browser was supposed to transcode wav-files as well, instead of being extremely hazardous to mobile data plans (sorry)
* `--license` didn't work if copyparty was installed from `pip`



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-1009-0919  `v1.4.5`  qr-code

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* display a server [qr-code](https://github.com/9001/copyparty#qr-code) [(screenshot)](https://user-images.githubusercontent.com/241032/194728533-6f00849b-c6ac-43c6-9359-83e454d11e00.png) on startup
  * primarily for running copyparty on a phone and accessing it from another
  * optionally specify a path or password with `--qrl lootbox/?pw=hunter2`
  * uses the server's exteral ip (default route) unless `--qri` specifies a domain / ip-prefix
  * classic cp437 `▄` `▀` for space efficiency; some misbehaving terminals / fonts need `--qrz 2`
* new permission `G` returns the filekey of uploaded files for users without read-access
  * when combined with permission `w` and volflag `fk`, uploaded files will not be accessible unless the filekey is provided in the url, and `G` provides the filekey to the uploader unlike `g`
* filekeys are added to the unpost listing

## bugfixes
* renaming / moving folders is now **at least 120x faster**
  * and that's on nvme drives, so probably like 2000x on HDDs
* uploads to volumes with lifetimes could get instapurged depending on browser and browser settings
* ux fixes
  * FINALLY fixed messageboxes appearing offscreen on phones (and some other layout issues)
  * stop asking about folder-uploads on phones because they dont support it
  * on android-firefox, default to truncating huge folders with the load-more button due to ff onscroll being buggy
  * audioplayer looking funky if ffmpeg unavailable
* waveform-seekbar cache expiration (the thumbcleaner complaining about png files)
* ie11 panic when opening a folder which contains a file named `up2k`
  * turns out `<a name=foo>` becomes `window.foo` unless that's already declared somewhere in js -- luckily other browsers "only" do that with IDs



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0926-2037  `v1.4.3`  signal in the noise

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* `--bak-flips` saves a copy of corrupted / bitflipped up2k uploads
  * comparing against a good copy can help pinpoint the culprit
  * also see [tracking bitflips](https://github.com/9001/copyparty/blob/hovudstraum/docs/notes.sh#:~:text=tracking%20bitflips)

## bugfixes
* some edgecases where deleted files didn't get dropped from the db
  * can reduce performance over time, hitting the filesystem more than necessary



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0925-1236  `v1.4.2`  fuhgeddaboudit

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* forget incoming uploads by deleting the name-reservation
  * (the zerobyte file with the actual filename, not the .PARTIAL)
  * can take 5min to kick in

## bugfixes
* zfs on ubuntu 20.04 would reject files with big unicode names such as `148. Профессор Лебединский, Виктор Бондарюк, Дмитрий Нагиев - Я её хой (Я танцую пьяный на столе) (feat. Виктор Бондарюк & Дмитрий Нагиев).mp3`
  * usually not a problem since copyparty truncates names to fit filesystem limits, except zfs uses a nonstandard errorcode
* in the "print-message-to-serverlog" feature, a unicode message larger than one tcp-frame could decode incorrectly



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0924-1245  `v1.4.1`  fix api compat

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# bugfixes
* [v1.4.0](https://github.com/9001/copyparty/releases/tag/v1.4.0) accidentally required all clients to use the new up2k.js to continue uploading; support the old js too



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0923-2053  `v1.4.0`  mostly reliable

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* huge folders are lazily rendered for a massive speedup, #11
  * also reduces the number of `?tree` requests; helps a tiny bit on server load
* [selfdestruct timer](https://github.com/9001/copyparty#self-destruct) on uploaded files -- see link for howto and side-effects
* ban clients trying to bruteforce passwords
  * arg `--ban-pw`, default `9,60,1440`, bans for 1440min after 9 wrong passwords in 60min
  * clients repeatedly trying the same password (due to a bug or whatever) are not counted
  * does a `/64` range-ban for IPv6 offenders
  * arg `--ban-404`, disabled by default, bans for excessive 404s / directory-scanning
    * but that breaks up2k turbo-mode and probably some other eccentric usecases
* waveform seekbar [(screenshot)](https://user-images.githubusercontent.com/241032/192042695-522b3ec7-6845-494a-abdb-d1c0d0e23801.png)
* the up2k upload button can do folders recursively now
  * but only a single folder can be selected at a time, making drag-drop the obvious choice still
* gridview is now less jank, #12
* togglebuttons for desktop-notifications and audio-jingle when upload completes
* stop exposing uploader IPs when avoiding filename collisions
  * IPs are now HMAC'ed with urandom stored at `~/.config/copyparty/iphash`
* stop crashing chrome; generate PNGs rather than SVGs for filetype icons
* terminate connections with SHUT_WR and flush with siocoutq
  * makes buggy enterprise proxies behave less buggy
  * do a read-spin on windows for almost the same effect
* improved upload scheduling
  * unfortunately removes the `0.0%, NaN:aN, N.aN MB/s` easteregg
* arg `--magic` enables filetype detection on nameless uploads based on libmagic
* mtp modifiers to let tagparsers keep their stdout/stderr instead of capturing
  * `c0` disables all capturing, `c1` captures stdout only, `c2` only stderr, and `c3` (default) captures both
* arg `--write-uplog` enables the old default of writing upload reports on POSTs
  * kinda pointless and was causing issues in prisonparty
* [upload modifiers](https://github.com/9001/copyparty#write) for terse replies and to randomize filenames
* other optimizations
  * 30% faster tag collection on directory listings
  * 8x faster rendering of huge tagsets
* new mtps [guestbook](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/guestbook.py) and [guestbook-read](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/guestbook-read.py), for example for comment-fields on uploads
* arg `--stackmon` now takes dateformat filenames to produce multiple files
* arg `--mtag-vv` to debug tagparser configs
* arg `--version` shows copyparty version and exits
* arg `--license` shows a list of embedded dependencies + their licenses
* arg `--no-forget` and volflag `:c,noforget` keeps deleted files in the up2k db/index
  * useful if you're shuffling uploads to s3/gdrive/etc and still want deduplication

## bugfixes
* upload deduplication using symlinks on windows
* increase timeouts to run better on servers with extremely overloaded HDDs
  * arg `--mtag-to` (default 60 sec, was 10) can be reduced for faster tag scanning
* incorrect filekeys for files symlinked into another volume
* playback could start mid-song if skipping back and forth between songs
* use affinity mask to determine how many CPU cores are available
* restore .bin-suffix for nameless PUT/POSTs (disappeared in v1.0.11)
* fix glitch in uploader-UI when upload queue is bigger than 1 TiB
* avoid a firefox race-condition accessing the navigation history
* sfx tmpdir keepalive when flipflopping between unix users
* reject anon ftp if anon has no read/write
* improved autocorrect for poor ffmpeg builds
* patch popen on older pythons so collecting tags on windows is always possible
* misc ui/ux fixes
  * filesearch layout in read-only folders
  * more comfy fadein/fadeout on play/pause
  * total-ETA going crazy when an overloaded server drops requests
  * stop trying to play into the next folder while in search results
  * improve warnings/errors in the uploader ui
    * some errors which should have been warnings are now warnings
    * autohide warnings/errors when they are remedied
  * delay starting the audiocontext until necessary
    * reduces cpu-load by 0.2% and fixes chrome claiming the tab is playing audio

# copyparty.exe

now introducing [copyparty.exe](https://github.com/9001/copyparty/releases/download/v1.4.0/copyparty.exe)!   only suitable for the rainiest of days ™

[first thing you'll see](https://user-images.githubusercontent.com/241032/192070274-bfe0bfef-2293-40fc-8852-fcf4f7a90043.png) when you run it is a warning to **«please use the [python-sfx](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) instead»**,
* `copyparty.exe` was compiled using 32bit python3.7 to support windows7, meaning it won't receive any security patches
* `copyparty-sfx.py` uses your system libraries instead so it'll stay safe for much longer while also having better performance

so the exe might be super useful in a pinch on a secluded LAN but otherwise *Absolutely Not Recommended*

you can download [ffmpeg](https://ocv.me/stuff/bin/ffmpeg.exe) and [ffprobe](https://ocv.me/stuff/bin/ffprobe.exe) into the same folder if you want multimedia-info, audio-transcoding or thumbnails/spectrograms/waveforms -- those binaries were [built](https://github.com/9001/copyparty/tree/hovudstraum/scripts/pyinstaller#ffmpeg) with just enough features to cover what copyparty wants, but much like copyparty.exe itself (so due to security reasons) it is strongly recommended to instead grab a [recent official build](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) every once in a while

## and finally some good news

* the chrome memory leak will be [fixed in v107](https://bugs.chromium.org/p/chromium/issues/detail?id=1354816)
* and firefox may fix the crash in [v106 or so](https://bugzilla.mozilla.org/show_bug.cgi?id=1790500)
* and the release title / this season's codename stems from a cpp instance recently being slammed with terabytes of uploads running on a struggling server mostly without breaking a sweat 👍



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0818-1724  `v1.3.16`  gc kiting

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## bugfixes
* found a janky workaround for [the remaining chrome wasm gc bug](https://bugs.chromium.org/p/chromium/issues/detail?id=1354816)
  * worker-global typedarray holding on to the first and last byte of the filereader output while wasm chews on it
  * overhead is small enough, slows down firefox by 2~3%
  * seems to work on many chrome versions but no guarantees
    * still OOM's some 93 and 97 betas, probably way more 

## other changes
* disable `mt` by default on https-desktop-chrome
  * avoids the gc bug entirely (except for plaintext-http and phones)
  * chrome [doesn't parallelize](https://bugs.chromium.org/p/chromium/issues/detail?id=1352210) `crypto.subtle.digest` anyways



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0817-2302  `v1.3.15`  pls let me stop finding chrome bugs

two browser-bugs in two hours, man i just wanna play horizon
* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## bugfixes
* chrome randomly running out of memory while hashing files and `mt` is enabled
  * the gc suddenly gives up collecting the filereaders
  * fixed by reusing a pool of readers instead
* chrome failing to gc Any Buffers At All while hashing files and `mt` is enabled on plaintext http
  * this one's funkier, they've repeatedly fixed and broke it like 6 times between chrome 84 and 106
  * looks like it just forgets about everything that's passed into wasm
  * no way around it, just show a popup explaining how to disable multithreaded hashing



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0815-1825  `v1.3.14`  fix windows db

after two exciting releases, time for something boring
* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* upload-info (ip and timestamp) is provided to `mtp` tagparser plugins as json
* tagscanner will index `fmt` (file-format / container type) by default
  * and `description` can be enabled in `-mte`

## bugfixes
* [v1.3.12](https://github.com/9001/copyparty/releases/tag/v1.3.12) broke file-indexing on windows if an entire HDD was mounted as a volume



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0812-2258  `v1.3.12`  quickboot

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
*but wait, there's more!*   not only do you get the [multithreaded file hashing](https://github.com/9001/copyparty/releases/tag/v1.3.11) but also --
* faster bootup and volume reindexing when `-e2ds` (file indexing) is enabled
  * `3x` faster is probably the average on most instances; more files per folder = faster
  * `9x` faster on a 36 TiB zfs music/media nas with `-e2ts` (metadata indexing), dropping from 46sec to 5sec
  * and `34x` on another zfs box, 63sec -> 1.8sec
  * new arg `--no-dhash` disables the speedhax in case it's buggy (skipping files or audio tags)
* add option `--exit idx` to abort and shutdown after volume indexing has finished

## bugfixes
* [u2cli](https://github.com/9001/copyparty/tree/hovudstraum/bin#up2kpy): detect and skip uploading from recursive symlinks
* stop reindexing empty files on startup
* support fips-compliant cpython builds
  * replaces md5 with sha1, changing the filetype-associated colors in the gallery view



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0810-2135  `v1.3.11`  webworkers

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* multithreaded file hashing! **300%** average speed increase
  * when uploading files through the browser client, based on web-workers
    * `4.5x` faster on http from a laptop -- `146` -> `670` MiB/s
    * ` 30%` faster on https from a laptop -- `552` -> `716` MiB/s
    * `4.2x` faster on http from android -- `13.5` -> `57.1` MiB/s
    * `5.3x` faster on https from android -- `13.8` -> `73.3` MiB/s
    * can be disabled using the `mt` togglebtn in the settings pane, for example if your phone runs out of memory (it eats ~250 MiB extra RAM)
  * `2.3x` faster [u2cli](https://github.com/9001/copyparty/tree/hovudstraum/bin#up2kpy) (cmd-line client) -- `398` -> `930` MiB/s
  * `2.4x` faster filesystem indexing on the server
  * thx to @kipukun for the webworker suggestion!

## bugfixes
* ux: reset scroll when navigating into a new folder
* u2cli: better errormsg if the server's tls certificate got rejected
* js: more futureproof cloudflare-challenge detection (they got a new one recently)

## other changes
* print warning if the python interpreter was built with an unsafe sqlite
* u2cli: add helpful messages on how to make it run on python 2.6

**trivia:** due to a [chrome bug](https://bugs.chromium.org/p/chromium/issues/detail?id=1352210), http can sometimes be faster than https now ¯\\\_(ツ)\_/¯



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0803-2340  `v1.3.10`  folders first

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* faster
  * tag scanner
  * on windows: uploading to fat32 or smb
* toggle-button to sort folders before files (default-on)
  * almost the same as before, but now also when sorting by size / date
* repeatedly hit `ctrl-c` to force-quit if everything dies
* new file-indexing guards
  * `--xdev` / volflag `:c,xdev` stops if it hits another filesystem (bindmount/symlink)
  * `--xvol` / volflag `:c,xvol` does not follow symlinks pointing outside the volume
  * only affects file indexing -- does NOT prevent access!

## bugfixes
* forget uploads that failed to initialize (allows retry in another folder)
* wrong filekeys in upload response if volume path contained a symlink
* faster shutdown on `ctrl-c` while hashing huge files
* ux: fix navpane covering files on horizontal scroll

## other changes
* include version info in the base64 crash-message
* ux: make upload errors more visible on mobile



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0727-1407  `v1.3.8`  more async

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* new arg `--df 4` and volflag `:c,df=4g` to guarantee 4 GiB free disk space by rejecting uploads
* some features no longer block new uploads while they're processing
  * `-e2v` file integrity checker
  * `-e2ts` initial tag scanner
  * hopefully fixes a [deadlock](https://www.youtube.com/watch?v=DkKoMveT_jo&t=3s) someone ran into (but probably doesn't)
    * (the "deadlock" link is an addictive demoscene banger -- the actual issue is #10)
* reduced the impact of some features which still do
  * defer `--re-maxage` reindexing if there was a write (upload/rename/...) recently
    * `--db-act` sets minimum idle period before reindex can start (default 10sec)
* bbox / image-viewer: add video hotkeys 0..9 to seek 0%..90%
* audio-player: add audio crossfeed (left-right channel mixer / vocal isolation)
* splashpage (`/?h`) shows time since the most recent write

## bugfixes
* a11y:
  * enter-key should always trigger onclick
  * only focus password box if in-bounds
  * improve skip-to-files
* prisonparty: volume labeling in root folders
* other minor stuff
  * forget deleted shadowed files from the db
  * be less noisy if a client disconnects mid-reply
  * up2k.js less eager to thrash slow server HDDs

## other changes
* show client's upload ETA in server log
* dump stacks and issue `lsof` on the db if a transaction is stuck
  * will hopefully help if there's any more deadlocks
* [up2k-hook-ytid](https://github.com/9001/copyparty/blob/hovudstraum/contrib/plugins/up2k-hook-ytid.js) (the overengineered up2k.js plugin example) now has an mp4/webm/mkv metadata parser



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0716-1848  `v1.3.7`  faster

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* `up2k.js`: **improved upload speeds!**
  * **...when there's many small files** (or the browser is slow)
    * add [potato mode](https://user-images.githubusercontent.com/241032/179336639-8ecc01ea-2662-4cb6-8048-5be3ad599f33.png) -- lightweight UI for faster uploads from slow boxes
    * enables automatically if it detects a cpu bottleneck (not very accurate)
  * **...on really fast connections (LAN / fiber)**
    * batch progress updates to reduce repaints
  * **...when there is a mix of big and small files**
    * sort the uploads by size, smallest first, for optimal cpu/network usage
      * can be overridden to alphabetical order in the settings tab
      * new arg `--u2sort` changes the default + overrides the override button
    * improve upload pacing when alphabetical order is enabled
      * mainly affecting single files that are 300 GiB + 
* `up2k.js`: add [up2k hooks](https://github.com/9001/copyparty/blob/hovudstraum/contrib/plugins/up2k-hooks.js)
  * specify *client-side* rules to reject files as they are dropped into the browser
  * not a hard-reject since people can use [up2k.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) and whatnot, more like a hint
* `up2k.py`: add file integrity checker
  * new arg `-e2v` to scan volumes and verify file checksums on startup
  * `-e2vu` updates the db on mismatch, `-e2vp` panics
  * uploads are blocked while the scan is running -- might get fixed at some point
    * for now it prints a warning
* bbox / image-viewer: doubletap a picture to enter fullscreen mode
* md-editor: `ctrl-c/x` affects current line if no selection, and `ctrl-e` is fullscreen
* tag-parser plugins:
  * add support for passing metadata from one mtp to another (parser dependencies)
    * the `p` flag in [vidchk](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/vidchk.py) usage makes it run after the base parser, eating its output
  * add [rclone uploader](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/rclone-upload.py) which optionally and by default depends on vidchk

## bugfixes
* sfx would crash if it got the same PID as recently (for example across two reboots)
* audio equalizer on recent chromes
  * still can't figure out why chrome sometimes drops the mediasession
* bbox: don't attach click events to videos
* up2k.py:
  * more sensible behavior w/ blank files
  * avoid some extra directory scans when deleting files
  * faster shutdown on `ctrl-c` during volume indexing
* warning from the thumbnail cleaner if the volume has no thumbnails
* `>fixing py2 support` `>2022`

## other changes
* up2k.js:
  * sends a summary of the upload queue to [the server log](https://github.com/9001/copyparty#up2k)
  * shows a toast while loading huge filedrops to indicate it's still alive
* sfx: disable guru meditation unless running on windows
  * avoids hanging systemd on certain crashes
* logs the state of all threads if sqlite hits a timeout



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0706-0029  `v1.3.5`  sup cloudflare

* read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* detect + recover from cloudflare ddos-protection memes during upload
  * while carefully avoiding any mention of "DDoS" in the JS because enterprise firewalls do not enjoy that
* new option `--favico` to specify a default favicon
  * set to `🎉` by default, which also enables the fancy upload progress donut 👌
* baguettebox (image/video viewer):
  * toolbar button `⛶` to enter fullscreen mode (same as hotkey `F`)
  * tap middle of screen to show/hide toolbar
  * tap left/right-side of pics to navigate prev/next
  * hotkeys `[` and `]` to set A-B loop in videos
    * and [URL parameters](https://a.ocv.me/pub/demo/pics-vids/#gf-e2e482ae&t=4.2-6) for that + [initial seekpoint](https://a.ocv.me/pub/demo/pics-vids/#gf-c04bb0f6&t=26s) (same as the audio player)

## bugfixes
* when a tag-parser hits the timeout, `pkill` all its descendants too
  * and a [new mtp flag](https://github.com/9001/copyparty/#file-parser-plugins) to override that; `kt` (kill tree, default), `km` (kill main, old default), `kn` (kill none)
* cpu-wasting spin while waiting for the final handful of files to finish tag-scraping
* detection of sparse-files support inside [prisonparty](https://github.com/9001/copyparty/tree/hovudstraum/bin#prisonpartysh) and other strict jails
* baguettebox (image/video viewer):
  * crash on swipe during close
* didn't reset terminal color at the end of `?ls=v`
* don't try to thumbnail empty files (harmless but dumb)

## other changes
* ux improvements
  * hide the uploads table until something happens
* bump codemirror to 5.65.6



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0627-2057  `v1.3.3`  sdcardfs

* **new:** read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## bugfixes
* **upload:** downgrade filenames to ascii if the server filesystem requires it
  * **android fix:** external sdcard seems to be UCS-2 which can't into emojis
* **upload:** accurate detection of support for sparse files
  * now based on filesystem behavior rather than a list of known filesystems
    * **android fix:** all storage is `sdcardfs` so the list wasn't good enough
* **ux:** custom css/js did not apply to write-only folders



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0619-2331  `v1.3.2`  think im out of titles

* **new:** read-only demo server at https://a.ocv.me/pub/demo/
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* new option `--thickfs` to modify the list of filesystems that dont support sparse files
  * default should catch most usual cases but I probably missed some
* detect and warn if filesystem was expected to support sparse files yet doesn't

## bugfixes
* nonsparse: ensure chunks are flushed on linux as well
* switching between documents
* ctrl-clicking a breadcrumb entry didn't open a new tab as expected
* renaming files based on artist/title/etc tags would create subdirectories if tags contained `/`
  * not dangerous -- the server correctly prevented any path traversals -- just unexpected
* markdown stuff
  * numbered lists appeared as bullet-lists
  * don't crash if a plugin sets a buggy timer
  * plugins didn't run when viewing `README.md` inline

## other changes
* in the `-ss` safety preset, replace `no-dot-mv, no-dot-ren` with `no-logues, no-readme`
* audio player continues into the next folder by default




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0616-1956  `v1.3.1`  types

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* improved support for filesystems without sparse files (fat32, exfat, hpfs)
  * the server no longer preallocates the whole file with zeroes before upload can start
  * so you can now finally run copyparty on your android phone or tablet and upload to the sd-card instead of the internal storage
  * however upload speed will suffer a bit (limited to a single tcp connection doing one chunk at a time)
* safety profiles; arguments `-s`, `-ss`, and `-sss` are aliases/presets for other safety-related arguments
  * `-s` reduces attack surface from potentially dangerous software by disabling thumbnails, audio transcoding, ffmpeg, pillow, vips
  * `-ss` also prevents js-injection, accidental move/deletes, broken symlinks, and enables enterprise-grade security (return 404 on 403)
  * `-sss` also enables logging to disk and does a scan for dangerous symlinks at startup (possibly expensive)
* ux improvements
  * a11y jumpers -- hit tab + enter to jump straight to files/folders
  * hotkey `Y` to download currently playing song / vid / pic
  * button to reset the hidden columns
  * new themes "hacker" and "hi-con"

## bugfixes
* spinlock if a client disconnects in the middle of an up2k handshake
* ftp server couldn't persist metadata when multiprocessing was enabled (`-j 0`)
* cut/paste (move) files between filesystems
* allow `Connection: keep-alive` on HTTP/1.0
* stray `[` appeared at the start of logfiles in the textviewer
* misleading log message when a completed upload expires from registry and `-e2d` was not set

## other changes
* the basic uploader adds the `.PARTIAL` suffix while uploading (like up2k)
* added type hints / mypy checking
* upgrade deps (markedjs, codemirror)
* ux improvements
  * delay spinners a bit
  * instant feedback when switching folders
  * a11y outlines in up2k ui




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0522-1502  `v1.3.0`  god dag

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* i18n! multilingual client
  * new option `--lang nor` to set default language
  * english and norwegian
    * add your own language at the top of [browser.js](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/web/browser.js) and [splash.js](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/web/splash.js) and send a pr :^)
  * build an english-only sfx with `./scripts/make-sfx.sh lang eng` (or `eng|nor` for english and norwegian)
  * translation is incomplete but covers the most important / common stuff
* show download progress while opening huge textfiles
* add unix-extrafield to zipfiles for utc timestamps
  * zip spec says the regular timestamp is supposed to be localtime :||||
  * only helps on linux and will rollaround in 2038 but should be OK because the msdos field doesn't until 2100
  * couldn't get ntfs-extrafields to work (supposed to be utc but idgi), would have been better, oh well
* ux tweaks
  * remember videoplayer preferences
  * confirmation messages
    * hiding a column for the first time
    * opening a huge textfile
    * destination in upload msg

## bugfixes
* dont switch to treeview when playback continues into the next folder

## other changes
* updated deps (markedjs, codemirror, prismjs)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0513-1524  `v1.2.11`  big docs

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## bugfixes

this release fixes #9 (denial-of-service), thx to @chinponya for the report!

* large files no longer embed if you `?doc=some.mkv`
  * stops copyparty from eating all your RAM
  * js will stream the file afterwards instead
* disable selection of search results
  * didn't serve a purpose, was just confusing



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0512-2344  `v1.2.10`  in addition

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## bugfixes
* huge speed boost on huge databases (4'000'000+ files)
  * improves initial tag scans when indexing new files
  * should also improve directory listings, search results



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0512-2110  `v1.2.9`  monokai

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* automatic logout after `--logout` minutes of inactivity
* show originating path to dangerous symlinks during `--ls` validation

## bugfixes
* dont try to index nonregular files when scanning filesystem
* start filesystem indexing even if no interfaces could bind
* fix minor issues when using a symlink as webroot
* fix filekeys in the basic-html browser
* support login on ie4 / win3.11
* restore minimal support for browsers without css-variables [(makes ie11 look surprisingly dope)](https://user-images.githubusercontent.com/241032/166340135-c59b9ced-5dbe-45d9-9025-285f0ffb5a49.png)

## other changes
* redirect to webroot after login instead of the controlpanel
* improve readability of the upload dropzone for smaller screens
* complain loudly if FFmpeg segfaults on a file
  * grep your logs for `<Signals.SIG` to investigate
* safer systemd service example
* other minor ux fixes
  * change focus in modals between ok/cancel with left/right keys
  * removed the option to disable spa (nobody's mentioned any issues)
  * compensate for play/pause fades by rewinding a bit
  * focus the password field if not logged in
  * [theme 2 is now monokai](https://user-images.githubusercontent.com/241032/168170566-bf71c3e0-d068-43cd-a277-f797184a702e.png) (the protonmail edition)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0430-0016  `v1.2.8`  windows++

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## new features
* new themes `vice` and the windows 3.1 masterpiece `hotdog stand`

<table><tr><td width="33%" align="center"><a href="https://user-images.githubusercontent.com/241032/165864907-17e2ac7d-319d-4f25-8718-2f376f614b51.png"><img src="https://user-images.githubusercontent.com/241032/165867551-fceb35dd-38f0-42bb-bef3-25ba651ca69b.png"></a>
0. classic dark</td><td width="33%" align="center"><a href="https://user-images.githubusercontent.com/241032/165864904-c5b67ddd-f383-4b9e-9f5a-a3bde183d256.png"><img src="https://user-images.githubusercontent.com/241032/165867556-077b6068-2488-4fae-bf88-1fce40e719bc.png"></a>
2. flat dark</td><td width="33%" align="center"><a href="https://user-images.githubusercontent.com/241032/165864901-db13a429-a5da-496d-8bc6-ce838547f69d.png"><img src="https://user-images.githubusercontent.com/241032/165867560-aa834aef-58dc-4abe-baef-7e562b647945.png"></a>
4. vice</td></tr><tr><td align="center"><a href="https://user-images.githubusercontent.com/241032/165864905-692682eb-6fb4-4d40-b6fe-27d2c7d3e2a7.png"><img src="https://user-images.githubusercontent.com/241032/165867555-080b73b6-6d85-41bb-a7c6-ad277c608365.png"></a>
1. classic light</td><td align="center"><a href="https://user-images.githubusercontent.com/241032/165864903-7fba1cb9-036b-4f11-90d5-28b7c0724353.png"><img src="https://user-images.githubusercontent.com/241032/165867557-b5cc0010-d880-48b1-8156-9c84f7bbc521.png"></a>
3. flat light
</td><td align="center"><a href="https://user-images.githubusercontent.com/241032/165864898-10ce7052-a117-4fcf-845b-b56c91687908.png"><img src="https://user-images.githubusercontent.com/241032/165867562-f3003d45-dd2a-4564-8aae-fed44c1ae064.png"></a>
5. <a href="https://blog.codinghorror.com/a-tribute-to-the-windows-31-hot-dog-stand-color-scheme/">hotdog stand</a></td></tr></table>

* `search:` button to load more search results, starting at 125 instead of 1000, now much better on slow PCs
* `search:` immediately perform a search when the enter key is pressed
* `uploader:` optimal column sizing in the uploader depending on which tab is selected (done/busy/queued)
* `uploader:` new option `--turbo` to change the default settings of the turbo-mode in the uploader
  * `0` (default) is the old behavior, `1` disables the warning when enabling turbo, `2` enables turbo, `3` also disables the datecheck
  * see the tooltip in the settings tab for more info; basically it skips the file contents verification and instead relies on filesize and timestamp to guess if a file was uploaded already, useful for massive upload batches that got interrupted

## bugfixes
* `httpd:` a theoretical XSS opening -- copyparty would echo bad requests as html
  * it still does that, but now with plaintext content-type
  * was mostly-harmless -- can't really think of a way to exploit it since it'd only happen on invalid HTTP requests
* `httpd:` better errorhandling on invalid requests in general
* **windows-only:** `httpd:` deadlocks when trying to access files with illegal filenames on windows
  * files containing characters `:*<|>"/?\` or names starting with `con.`, `prn.`, `aux.`, `nul.`
  * for example `aux.c` when unpacking the linux source code on a flashdrive and plugging it into a windows rig
* **windows-only:** `database:` deadlock if a search was done during the initial filesystem scan
* `database:` deadlock if an upload was done during a filesystem scan (either initial or periodic rescan)
* `client:` javascript crash when linking someone an audio URL and they'd never visited before
* `client:` ignore bugs in the developer console (in future versions of chrome)
* `uploader:` timestamps of zero-byte uploads were not set
* `database:` skip busy files during a filesystem rescan
* `media player:` sending artist / title info to the OS broke at some point

## other changes
* changed the themes to use css variables for colors, making it way easier (hopefully) to make your own themes
* mention [chrome issue 1317069](https://bugs.chromium.org/p/chromium/issues/detail?id=1317069) in the readme
* improved the `--help` text




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0416-2144  `v1.2.7`  write-only unpost

fixed another dumdum, sorry for the spam
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# bugfixes
* allow unpost with write-only permissions




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0415-1809  `v1.2.6`  hardlink

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* new arg `--hardlink` tries to hardlink instead of symlink when receiving a duplicate file through up2k
* new arg `--never-symlink` disables the fallback to symlink if hardlink fails, making a full dupe
  * `--no-symlink` was renamed to `--no-dedup`

# bugfixes
* some css color issues introduced in v1.2.4, mainly in markdown documents
* setting mtimes / last-modified on up2k uploads when running on windows



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0414-1945  `v1.2.4`  the thumbs and themes update

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* gallery URLS -- copy the URL while viewing an image/video in the gallery
* option to change/disable the gallery animations in the UI
  * default from OS preferences through `prefers-reduced-motion`
* decode terminal colors when viewing `diz`, `ans`, `log` textfiles
* thumbnails:
  * option to use `pyvips` instead of (or in addition to) `pillow`, 3x faster than pillow
  * add `ffmpeg` as fallback for creating thumbnails of pictures too, 3x slower than pillow
    * so now it can read jpeg-xl files + a bunch more
      * including pdf which is disabled by default because scary
  * new args to specify which file formats to read using which backend
    * `--th-r-pil`, `--th-r-vips`, `--th-r-ffi`, `--th-r-ffv`, `--th-r-ffa`
  * new arg `--th-dec` specifies backend preference, default `pyvips` > `pillow` > `ffmpeg`
  * volflags to disallow thumbnails inside specific volumes
    * `dvthumb` for video, `dathumb` for audio, `dithumb` for pics, `dthumb` to disable all
  * try to detect and adjust for missing ffmpeg features
    * adds `--th-ff-jpg` and `--th-ff-swr` when necessary but it breaks the first few thumbs
* flat theme, selectable in the settings tab
  * new arg `--theme` sets default theme, default 0 = old dark theme
  * new arg `--themes` adds more theme buttons to the UI if you've included your own theme through `--css-browser`

# bugfixes
* more aggressively prevent systemd from deleting the sfx from `/tmp` while copyparty is running
* javascript crash if media player settings were changed without music playing

# other changes
* add `mpc`/musepack to known audio formats (for streaming and spectrogram thumbnails)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0324-0135  `v1.2.3`  the ancient ones

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* browser-client: never give up on a failed upload -- keep retrying every 30sec

# bugfixes
* files with last-modified older than 1980-01-01 didn't make it into zip downloads



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0320-0515  `v1.2.2`  dont crawl me bro

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* options to tell crawlers / search engines you dont wanna be indexed
  * either globally with `--no-robots` or single volumes using volflag `norobots`
  * allow crawlers inside a volume with volflag `robots`
  * or just use [robots.txt](https://www.robotstxt.org/robotstxt.html) like usual ( ´ w `)
* `--force-js` disables plain HTML folder listings, making things harder for crawlers who ignore the hints
  * internet explorer 9 is the oldest surviving browser
* `--html-head` to append additional HTML to the `<head>` section of all pages

# bugfixes
* inaccurate server URLs displayed on startup
  * correct protocol based on port / `--http-only` / `--https-only`
  * Windows: ignore interfaces with no ethernet cable connected
  * Windows: show URLs for all IPs on each interface
  * Linux: show link state next to URLs
* reset console color on exit

# other changes
* show name of open document in page title




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0303-0026  `v1.2.1`  ikke den men denja

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* plaintext volume listings at http://127.0.0.1:3923/?h&ls=v

# bugfixes
* search: support negative queries / subtracting tags from searches
  * you can put stuff like `gura -kagura` in the tags field
  * also the `raw` field supports `and/or/not` for more complex stuff such as
    ```
    ( tags like *nhato* or tags like *taishi* ) and ( not tags like *nhato* or not tags like *taishi* )
    ```
* [prisonparty](https://github.com/9001/copyparty/blob/hovudstraum/bin/prisonparty.sh): clean shutdown when used as a service
* ftp server now runs on python2 as well
  * ftps does not

# other changes
* higher debounce for searches
* slightly more padding in the files table
* added asyncore/asynchat into the sfx to (hopefully) support running the ftp server in python 3.12 when that releases late 2023



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0213-1558  `v1.2.0`  ftp btw

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* ftp server
  * built on [pyftpdlib](https://pypi.org/project/pyftpdlib/)
    * plaintext (`--ftp`), and/or...
    * FTPES / explicit-TLS (`--ftps`)
    * active or passive, as client prefers
  * upload, download, accounts (read / write / move / rename / delete)
  * does NOT have resumable uploads -- delete and reupload as necessary
  * integrated with up2k
    * uploaded files are indexed into the database
    * unpost is available (delete your own recent uploads)
* `--s-wr-slp` now rate-limits file uploads as well, in addition to downloads
* `--srch-hits` sets the max number of search results, defaults to 1000 (same as before)
* ctrl-click `-txt-` links to open the document viewer in a new tab
* log terse checksum of uploaded files

# bugfixes
* file-search: path queries didn't include the volume prefix/mountpoint
* ie11 could throw exceptions on keystrokes

# other changes
* finally deprecated `copyparty-sfx.sh`
* update some dependencies
  * marked `4.0.10` -> `4.0.12` fixes minor table formatting issues
  * easymde `2.15.0` -> `2.16.1`
  * codemirror `5.64.0` -> `5.65.1`

# notes
* the ftp server is not compatible with python 3.12 (releasing october 2023)
  * will be fixed in a [future version of pyftpdlib](https://github.com/giampaolo/pyftpdlib/issues/560)

the sfx was built from https://github.com/9001/copyparty/commit/39e7a7a2311ab8da43b2a9a18ae39d06202105e3



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0118-2128  `v1.1.12`  i should stop adding bugs

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# bugfixes
* fix PUT response in write-only folders (broke in v1.1.11)

# other changes
* [prisonparty](https://github.com/9001/copyparty/blob/hovudstraum/bin/prisonparty.sh):
  * fix examples 
  * support running from source
* [mtag-install-deps](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/install-deps.sh):
  * fix downloading tarballs from github (they stopped returning content-dispositions)
  * build vamp-sdk from source if unavailable
* forgot to mention [partyjournal](https://github.com/9001/copyparty/blob/hovudstraum/bin/partyjournal.py):
  * was a new feature in v1.1.11
  * shows a history of all uploads within a volume by reading the up2k db
  * can replace IPs with nicknames if provided as arguments



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2022-0114-2125  `v1.1.11`  chromecast?

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* include file-url in PUT responses
  * to support the [android app](https://github.com/9001/party-up/)
* main-tabs have links and are linkable which would have been a great help [before the android app existed](https://user-images.githubusercontent.com/241032/147699835-16101690-aab1-49da-a3cc-d16759808af5.jpg)

# new plugins (disabled by default)
* [very-bad-idea.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/very-bad-idea.py) and [meadup.js](https://github.com/9001/copyparty/blob/hovudstraum/contrib/plugins/meadup.js) which together turns a raspberry pi into a janky yet extremely flexible chromecast clone
  * anything uploaded through the app (files or links) are executed on the server
  * adds a virtual keyboard by @steinuil to the basic-upload tab
  * dedicated to extremely particular occasions where randomly evaluating code is A-OK
    * sweden-approved software

# bugfixes
* return own external ip as `Host:` if `Host:` is not provided by client
* correct clipboard actions available when jumping between permission levels
* markdown converter accidentally using a broken ie11 shim on all browsers
* changing the sort-order in the file listing didn't affect the thumbnail view

# other changes
* upgrade marked.js to 4.0.10
  * fixes misc rendering bugs




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1216-2305  `v1.1.10`  chill

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# bugfixes
* patiently wait when clients stop consuming data
  * fixes connections going bad when streaming movies or music
  * only affects sendfile, meaning reverse-proxied and non-https connections
* try FFmpeg when mutagen partially fails to parse a file (not just when it throws)

# other changes
* add [multisearch.html](https://github.com/9001/copyparty/blob/hovudstraum/docs/multisearch.html), applying a search template to a list of filenames
  * the currently only example grabs youtube-IDs and finds all related files for that ID



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1210-0144  `v1.1.8`  merry xmas

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* folders are colored blue when using `?ls=v` to list stuff in a terminal
* add folder breadcrumbs inside the textfile navpane

# bugfixes
* folder breadcrumbs (the non-navpane ones) glitching out while viewing textfiles
* give 404 instead of 500 when accessing `/.cpr`

# other changes
* expose some more state from the up2k client to ease debugging
  * for example to find out that firefox94 cannot read files bigger than 2 GiB when compiled with musl
* updated the [alternative fuse client](https://github.com/9001/copyparty/blob/hovudstraum/bin/copyparty-fuseb.py) so it kinda works again
  * still no reason to use that instead of the [main client](https://github.com/9001/copyparty/blob/hovudstraum/bin/copyparty-fuse.py)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1207-1819  `v1.1.7`  two wrongs

[v1.1.5](https://github.com/9001/copyparty/releases/tag/v1.1.5) and [v1.1.6](https://github.com/9001/copyparty/releases/tag/v1.1.6) were pretty busted, sorry bout that
(so much for stable eh)
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# known problems / todo
so far just mild annoyances, nothing bad
* clicking breadcrumbs with the textviewer open will navigate correctly but messes up the breadcrumbs
* server throws an exception when accessing `/.cpr`
* up2k should expose `st` for easier debugging

# bugfixes
* search-results ui
  * selecting / playing audio results broke in v1.1.5
  * and playing audio tracks in search results would clobber the search URL but that has always been a thing
* only show unique IPs in the window-title



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1207-0017  `v1.1.6`  not copyparty

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* option `--doctitle` changes the titles in the web-ui from "copyparty" to something else
* option `--wintitle` sets the console window-title, defaults to the primary/external IP
* volume-flags [`d2ds` and `d2ts`](https://github.com/9001/copyparty#file-indexing) to selectively disable on-boot indexing for some volumes
* support funky linux distros (with no `~/.config` and read-only `/tmp` such as recent Termux builds)

# bugfixes
* last release broke folder listings if you left off the trailing slash in the url
  * also fix the markdown-editor breadcrumbs which made that very obvious
* when running without `-e2d`, don't proactively create symlinks for dupe uploads
  * prevents the client from accidentally pushing superflous links
* ui didn't update correctly when navigating into a folder with indexing disabled

# other changes
* less indentation of outermost lists in the markdown viewer
* update some dependencies
  * marked `3.0.4` -> `4.0.6` fixes a performance regression in huge documents



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1204-0233  `v1.1.5`  certified spa

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* much faster navigation when the navpane is closed (no more full reloads)
* sort-order preference also applies to the initial listing now, #8 
* sort-order indicators in the grid and list views
* symlinks (duplicate uploads) now keep the uploader's timestamps
* panic-button in the control panel to reset all browser settings



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1128-0322  `v1.1.4`  enter the lab

* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* quoted searches, for stuff like "[more more more](https://www.youtube.com/watch?v=bgVRGmOK4SM)"
* upload ETA in the browser window title
* audio-player stays open on navigation
* thumbnails indicating whether clicking an audio file will start playing it (when the audio-player is open) or not
* mtp plugin [image-noexif](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/image-noexif.py) removes EXIF from uploaded images
* when running on windows; disable quickedit so cmd.exe doesn't pause the server if you accidentally click the console window
  * option `--keep-qem` disables disabling it

# bugfixes
* forcing specific compression levels using volume-flag `pk`
* mtp plugins [audio-bpm](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/audio-bpm.py) and [audio-key](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/audio-key.py) couldn't open files with mojibake / corrupt filenames

# other changes
* uploading files by dragging them into the browser using a computer from before 2009 should have zero delay now
* workaround for a chrome bug (appeared in chrome 96, fixed in 98) where dragging a link would activate the uploader
* mention in the readme that enabling the audio equalizer, with all values at zero, makes gapless albums fully gapless
* better error messages in the [standalone up2k upload client](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py)
* mirror at [gitlab](https://gitlab.com/9001/copyparty/-/releases) since github has been down a lot lately



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1120-0127  `v1.1.3`  CoreAudioFormat aight yeah okay

not super important but recommended
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# known problems
* **streaming compression of uploads:** optional arguments to volume-flag `pk` don't work, so you can only force-enable compression without specifying an exact algorithm (gz/xz) and level (0-9), instead letting the client choose a preference -- default is `gz,9`

# new features
* automatically enable transcoding for unsupported audio codecs (aac/m4a in some chromium builds)
* audio-player: gapless albums are even closer to gapless now
  * especially on iOS devices as they generally ignore preload hints
  * on all other browsers, opus appears to perform better than other codecs (noice)
* added a tooltip delay, and a hint next to the mouse-cursor for instant feedback
* new button in the control-panel, `enable k304` which kills the http connection on every `304 Not Modified` response
  * avoids a bug in some browsers (ie11) and webproxies (squid maybe?) which *sometimes* get stuck, expecting data after the header
* enable up2k-registry serialization when running without `-e2d` / sqlite, so incomplete uploads can be resumed after a server restart
* include both the hex and base64 sha512 representations in upload responses
* [standalone up2k upload client](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py): option `--ok` ignores any inaccessible files/folders and starts the upload anyways
* option `--rsp-slp` adds a synthetic delay to client responses

# bugfixes
* up2k-webclient: could crash if two browser-tabs uploaded the same chunk simultaneously
  * mostly harmless but you'd have to reload the tab to fix it + manually resume the upload
* buggy behavior when python was compiled without sqlite3 (default on freebsd)
  * memory usage would grow infinitely as more files were uploaded
  * exceptions sent to the client when trying to search
* add timeouts to FFmpeg operations, preventing invalid files from eating the `--th-mt` threads
  * 10 seconds for filetype / metadata parsing
  * 60 seconds (`--th-convt`) for thumbnails and audio transcoding
* up2k-webclient: fix an inconvenient priority inversion when turbo/yolo was enabled

# other changes
<table><tr><td><a alt="screenshot of an iPod displaying the lockscreen controls for the copyparty audio player" href="https://user-images.githubusercontent.com/241032/142711926-0700be6c-3e31-47b3-9928-53722221f722.png"><img src="https://user-images.githubusercontent.com/241032/142711927-3e554cc3-01d0-4b46-adb1-a3e82a0870ef.png" /></a></td><td>
<p>replaced <code>ogv.js</code> with serverside rewrapping of opus files into the appropriate apple-proprietary container</p>
<ul>
<li>sfx size is now 190 KiB smaller</li>
<li>feature-wise, this <b>only affects iOS devices</b> (iPhones, iPads, iPods)</li>
<li>no more opus decoding in javascript! now uses the native opus decoder instead</li>
<li>enables OS media controls since apple finally added <code>mediaSession</code> in iOS 15
	<ul><li>play/pause doesn't work too well, probably fixed in a future iOS version</li>
	<li>artist/title tags can suddenly become the filename (another iOS bug)</li></ul>
</li>
<li><b>disables</b> the in-browser volume control because <a href="https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/Using_HTML5_Audio_Video/Device-SpecificConsiderations/Device-SpecificConsiderations.html#//apple_ref/doc/uid/TP40009523-CH5-SW11">apple demands it</a>, can't be helped</li>
<li><b>disables</b> support for <code>ogg/vorbis</code>, only opus is playable without transcoding
	<ul><li>vorbis is transcoded to opus automatically, but this causes a quality loss</li></ul>
</li>
<li>audio-equalizer is broken for opus and all other 48khz audio files because apple made <code>AudioContext</code> hardcoded to 44100 hz
	<ul><li>makes the iPhone X buffer-overflow, all audio dies after ~2 minutes</li>
	<li>also ruins the common workaround for apple disabling volume controls</li></ul>
</li>
<li>gets rid of the silly sinewave generator which tricked iOS into letting the tab continue playing in the background</li>
</ul></td></tr></table>



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1112-2208  `v1.1.2`  mind the gap

* latest important update: **this one**? kind of
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

# new features
* navigate into textfiles using hotkeys (`v, k`)
* close various UI elements by repeatedly hitting the Escape key
* doubleclick files/folders to open them (in the grid view, when multiselect is enabled)
* `--s-wr-slp` sets a delay between socket writes, simulates a slow network during downloads
* `--s-wr-sz` sets socket write size, default 256 KiB (was hardcoded 32 KiB until now)
  * this increase download speed by ~50% (to around 3 GiB/s) when running on windows / where sendfile is unavailable

# bugfixes
* when uploading two files with the same name and size, only the first file got uploaded
  * so now it's also possible to upload the same files you just searched for without the refresh jank
  * discovered thanks to rockylinux serving the same package in multiple pools, nice
* when full-preload is enabled, also do regular preloading so the decoder has a chance to prepare (fixes gapless playback)
  * and kill the preloaders if they don't finish in time so free up network
* additional preloading fixes for ogv.js, only affecting **apple devices** when playing ogg/vorbis/opus audio:
  * disable full-preload since ogv skips the browser cache somehow
  * swap between the ogv instances to preserve cached audio
  * still a bit of silence left between tracks as the decoder boots up but that is the price you have to pay for using proprietary garbage
* `ctrl-a` now only selects the text within the focused codeblock in text documents
* minor correctness fix regarding chunked uploads
* avoid crc32 collisions in filenames
  * affected the media player and file selection, but [was unlikely to happen](https://i.stack.imgur.com/u4DeG.png)

# other changes
* prefer fpool on linux as well, since btrfs and zfs (and probably others) perform better with it



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1108-2139  `v1.1.1`  firefox v92 broke the clipboard

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## upgrade notes
* clipboard protocol changed -- `F5` your browser-tabs before moving any files with `ctrl-x` + `ctrl-v`

# new features
* option to preload the entire next song when approaching end-of-track
  * new button in the audioplayer options panel
  * should help with spotty but fast connections
  * *(probably does more harm than good on slow ones)*

# bugfixes
* [firefox v92 broke clipboard sync](https://bugzilla.mozilla.org/show_bug.cgi?id=1740144), so moving files between browser-tabs didn't work too well

# other changes
* adjusted the fallback spectrogram generator to better match the preferred one




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1106-2227  `v1.1.0`  opus

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: [v1.0.14](https://github.com/9001/copyparty/releases/tag/v1.0.14#:~:text=release-specific%20notes)

## upgrade notes
* you can use `--no-reload`, `--no-acode`, `--no-athumb` to disable the new features described below

# new features
* **audio transcoder**
  * hipster audio formats are transcoded to opus on-demand
    * `aac` `m4a` `flac` `alac` `mp2` `ac3` `dts` `wma` `ra` `wav` `aif` `aiff` `au` `alaw` `ulaw` `mulaw` `amr` `gsm` `ape` `tak` `tta` `wv`
  * because kipu wanted to play his `.au` bangers from 1993
  * needs FFmpeg and FFprobe, can be disabled with `--no-acode`
* **audio spectrograms**
  * are shown as thumbnails for audio files
  * supported formats: same as transcoder + `mp3` `ogg` `opus`
  * needs FFmpeg and FFprobe, can be disabled with `--no-athumb`
* **textfile viewer**
  * with syntax hilighting
    * can be disabled by deleting `web/deps/prism.js.gz` or building the sfx with `no-hl`
  * and list of textfiles in the navpane; toggle with hotkey `v`
* **navpane context dock**
  * snap parent folders into a panel to keep track in huge folders
  * toggle-button to disable it in the navpane toolbar
* **config reload**
  * SIGUSR1 reloads the config files
    * the [systemd example](https://github.com/9001/copyparty/blob/hovudstraum/contrib/systemd/copyparty.service) has been updated with `ExecReload`
  * only does accounts, volumes, and volflags -- so any changes to args still require a full restart
  * also available as a button in the control panel
    * can be disabled with `--no-reload`
* option to specify args (command-line arguments) in the config file
* url parameter `?txt` to return file as utf-8 text
  * or `?txt=iso-8859-1` to set a specific encoding
* url parameter `?mime=text/html;charset=shift_jis` to request a specific response mimetype
* [service script for freebsd](https://github.com/9001/copyparty/blob/hovudstraum/contrib/rc/copyparty), thx @kipukun 

# bugfixes
* [standalone up2k upload client](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) was showing https warnings with `-td`
* trailing newline missing in `?ls=t` and `?ls=v`
* add a bunch of known mimetypes to help ms-windows a bit
* lowercase all content-type charsets (firefox became case-sensitive at some point)
* example for giving multiple users the same permission-set using config files did not actually work

# other changes
* navpane is enabled by default on sufficiently large displays
* audio-player preload increased from 10 to 20 sec, giving the opus transcoder some time
* finally removed the deprecated `-e2s` option after 9 months (replaced by `-e2ds`)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1029-2237  `v1.0.14`  party donuts

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: **this ver!**

## argv changes
* `--th-mt 0` no longer means «*use all CPU cores*», however using all cores is (and was) the default when leaving it unset
* `--re-int` no longer serves a purpose and was removed (it is automatically inferred)
* `--no-mtag-mt` was replaced by `--mtag-mt 1` to allow setting exact core counts

## new features
![copyparty-donut](https://user-images.githubusercontent.com/241032/139513444-c22fc17a-6f44-4308-9cb0-ab191e40660b.png)
* up2k tab (and favicon) become a donut / progress-ring while uploading / searching
  * favicon becomes ETA when less than 99sec remains and ETA is sufficiently stable
* tag scanning is now multithreaded for recent uploads as well, like the initial scan is/was
* url parameter `?ls=t` returns a plaintext directory listing, and `?ls=v` adds terminal colors
* less cpu wakeups! *conserve electricity and be power smart :^)*
* add refresh and logout buttons to the control-panel
* try to catch and warn about some common config mistakes
* when launched without arguments: try to use port 80 and 443 by default on windows (and when running as root)

## bugfixes
* couldn't delete empty folders
* spacebar now triggers the OK/Cancel buttons in modal popups
* navpane didn't have locale-aware sorting like the file listing does
* uploading a blank file would glitch the browser tab until the next page refresh
* the [standalone up2k client](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) tried to mimic rsync behavior for source folder selection but had it the other way around
* if files were deleted while scanning for tags, the file hash was permanently marked as not having tags
* if some endpoints fail to bind, don't print them as "available" during startup
* navpane scroll glitch when loading new folders
* toast-positioning in ie11

## other changes
* truncate file "extensions" longer than 16 characters
* remove the multiprocessing warning on startup since it's mostly confusing
* mention selinux (fedora/centos/rhel-specific) setup steps in the systemd example
* new cheatcode in the javascript repl (bottom-left pi symbol) which turns all file links into download links

## release-specific notes
this release includes two additional sfx builds:
* [copyparty-enterprise.py](https://github.com/9001/copyparty/releases/download/v1.0.14/copyparty-enterprise.py) was built with `./scripts/make-sfx.sh re no-sh no-dd no-ogv`, removing `ogv` (the iOS ogg/opus/vorbis audio decoder) and `dd` (the audio-tray mouse cursor) to save some space
* [copyparty-sfx-gz.py](https://github.com/9001/copyparty/releases/download/v1.0.14/copyparty-sfx-gz.py) was built with `./scripts/make-sfx.sh re no-sh no-dd no-ogv no-cm gz`, also removing `cm` (the codemirror-based markdown editor), but more importantly using gzip compression rather than the usual bzip2, mostly useful for smoketests on feature-reduced python builds and embedded platforms

for future releases, you can use a script to automatically grab the latest sfx and create the two additional builds:
* download and run [copyparty-repack.sh](https://github.com/9001/copyparty/blob/hovudstraum/scripts/copyparty-repack.sh) on either linux, macos, or windows-msys2
* the two additional builds in this release are `sfx-ent/copyparty-sfx.py` and `sfx-lite/copyparty-sfx-gz.py` -- see [sfx-repack](https://github.com/9001/copyparty#sfx-repack) for more info



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1024-1906  `v1.0.13`  css fix

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* currently-playing song didn't hilight correctly



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1024-0112  `v1.0.12`  some polish

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## upgrade notes
* [minimal-up2k.html](https://github.com/9001/copyparty/blob/hovudstraum/docs/minimal-up2k.html) has changed slightly, [diff](https://github.com/9001/copyparty/commit/d77ec2200781cc1d381a074831c0bffc749e835d#diff-8b665a140ab1a0dde9b487df3b60ba38718253dddc3c7e3513eec5116ab6c11e)

## new features
* better thumbnail caching
  * 1 week expiration time
  * persist the webp-support test results for faster init
* add `--js-browser` to add custom javascript
* hop into subfolders from the file-list without doing full reloads
  * still does a full reload if navigating up to the parent folder, so use the navpane for that
* support searching on ie9

## bugfixes
* thumbnail toggle didn't take effect until the next navigation
* file indexing when mounting an entire disk on windows

## other changes
* general ux improvements
  * reflow the up2k panel for superwide screens
  * make the "close search results"  button more obvious
  * banner over inlined readme files
* some cleanup of the dark theme
  * visible panels (for the navpane etc)
  * thumbnail alignment

thx to @Bevinsky and @icxes for the ux suggestions



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1018-2310  `v1.0.11`  jeg fant jeg fant

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* search results are now shareable URLs
* optionally provide a filename when uploading with PUT or `?raw` POST
  * add a trailing slash to the URL to autogenerate a filename like before
  * and `?raw` POST without content-type is now allowed
* file-listing is refreshed when all up2k uploads complete
* new option `--ign-ebind` to continue startup even if one of the IPs / ports couldn't be listened on
* new option `--ign-ebind-all` to run even if copyparty can't receieve any connections at all
  * maybe useful for monitoring folders and hashing new files on a timer or something

## bugfixes
* unpost in jumpvols (inside `/foo/bar/` if `/foo/` and `/foo/bar/qux/` are volumes)
* u2cli: aggressive flushing to show uploaded files in realtime

## other changes
* replaced the "press button to play music" splashpage with a regular modal
* replace `:` with `.` in filenames from ipv6 clients
* volume listing on the frontpage is sorted alphabetically




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1011-2343  `v1.0.10`  favicon

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## breaking changes
* the argument `--no-hash` and volume-flags `dhash`, `ehash` (booleans) have been replaced with regex patterns; continue reading below

## new features
* optional favicon! configurable client-side in the `[⚙️]` config tab
  * the selected favicon is remembered per-server (good for keeping track of tabs)
* new argument `--no-idx '\.iso$'`, also available as volume-flag `[...]:c,noidx=\.iso$`
  * every filepath matching the given regex (`iso$`) will be ignored/skipped during indexing
  * uses OS-defined separators, so use `\\` as path-separator on windows
* "new" argument `--no-hash foo` and volume-flag `[...]:c,nohash=foo`
  * like `--no-idx`, but it only skips the file-contents indexing, so filename/path/size is still searchable
  * this replaces the boolean `--no-hash` and volume-flags `dhash`, `ehash`

## bugfixes
* fix ui race-condition (mkdir with navpane closed)
* mkdir was broken on python 2.7 since [v0.12.1 (july 28)](https://github.com/9001/copyparty/releases/tag/v0.12.1)
* try to support some buggy python builds (invalid ffi symbols)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1009-2029  `v1.0.9`  cirno reference

* latest important update: [v1.0.8](https://github.com/9001/copyparty/releases/tag/v1.0.8)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* readme: [run a program when a file is uploaded](https://github.com/9001/copyparty#upload-events)
  * add `-mtp` support for non-python programs
* better performance in the `-e2ds` filesystem indexer, particularly for samba/nfs shares
* support clients with read-only `localStorage` (private-browsing on certain iOS versions according to MDN)

## bugfixes
* a case of symlink-loops not being detected during `-e2ds` filesystem indexing
* #4 fixes incorrect protocol in the basic-upload response, thx Daedren
* flickering when refreshing the browser in lightmode
* sfx-repack: fix `no-dd` also disabling the loader animation by producing a bit of css with invalid syntax

## other news
* the [standalone up2k upload client](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) can detect and skip existing files much faster than the regular web client if you give it `-z`
  * (not part of this release, grab it from the link)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-1004-2050  `v1.0.8`  1.0.8 sketches

* latest important update: **this ver** (if you have non-https users)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* [portable / standalone up2k upload client](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) now included in the pypi package, [readme](https://github.com/9001/copyparty/tree/hovudstraum/bin#up2kpy) / [webm](https://ocv.me/stuff/u2cli.webm)
* empty / zero-byte files can now be uploaded
* up to 20 results are listed for filesearches, rather than just 1
* audio player progressbar now has textlabels next to the minute markers
* new argument `--vague-403` makes copyparty reply with 404 (not found) when it's actually a 403 (permission denied), which was the entirely-too-confusing default behavior for versions `1.0.3` through `1.0.7`
* new mtp plugin [cksum.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/cksum.py) generates various checksums

## bugfixes
* race-condition initializing the up2k-client when dropping files into the browser and you're not using https
* hilight active folder in the navpane even when the browser and copyparty disagrees on how to urlencode
* hide prologue/epilogue while search results are open
* toasts could redefine css

## other changes
* better focus outlines
* less verbose debug toasts
* dropzones more obvious at a glance / in a rush



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0926-1815  `v1.0.7`  pool party

* latest important update: [v1.0.3](https://github.com/9001/copyparty/releases/tag/v1.0.3)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* [portable / standalone up2k upload client](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py): early beta, apparently faster than browsers, [readme](https://github.com/9001/copyparty/tree/hovudstraum/bin#up2kpy) / [webm](https://ocv.me/stuff/u2cli.webm)
* up2k: fully parallelized handshakes and uploads
  * uploading smol files is way faster now
  * some files may temporarily display as "failed" until all uploads complete
* browser: `mkdir` and `msg` can be used during uploads (no longer does a full page reload)
* up2k: option to keep destination files open during uploads (fd pool)
  * on windows: default-ON, due to Microsoft Defender "real-time protection" being hella expensive
  * on linux/macos: default-OFF, but can be enabled with `--use-fpool` for things like nfs
* up2k: new option `--no-symlink` to fully dupe files instead of adding symlinks
* add minimal support for some more eccentric browsers (including Hv3)

## bugfixes
* up2k: check all dupes for a matching filesystem path
  * prevents duplicate symlinks if the same dupe is repeatedly uploaded to the same place
* don't crash the tag collector thread if there are invalid tags
* up2k-client: don't DDoS the server if the http response is invalid
* when running without `-e2d`, recently uploaded files could not be deleted
* on windows, absolute filesystem-paths could appear in exceptions sent to the client
* misc url escaping fixes, mostly regarding files/folders where name contains `?`
* sort-order being reset if you visit an empty folder

## other changes
* moved the up2k fence-toggle into the settings pane since probably nobody uses it
* readme: add a section on recovering from [client crashes](https://github.com/9001/copyparty#client-crashes)
  * firefox (the whole browser and all its tabs) can crash during upload




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0919-1311  `v1.0.5`  one more

* latest important update: [v1.0.3](https://github.com/9001/copyparty/releases/tag/v1.0.3)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## bugfixes
* basic-upload into `fk` (accesskey-enabled) folders
  * affected sharex, scripts, old browsers
  * files were uploaded correctly but the reply from copyparty was garbage



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0918-2241  `v1.0.4`  early bird gets the bugs

* latest important update: [v1.0.3](https://github.com/9001/copyparty/releases/tag/v1.0.3)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## bugfixes
* folders and volumes being out-of-order in the initial listing
* it was possible to shrink the navpane so much that the shrink/grow buttons disappeared
* a bunch of features stopped working in folders where `fk` (per-file accesskeys) was enabled

## other changes
* increased cache timeout for static resources
* can no longer open the markdown editor without write-access
* the argument parser can handle multiple volume flags in one group now, so `c,e2ds,dupe` instead of `c,e2ds:c,dupe`




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0918-1550  `v1.0.3`  unlisted

* latest important update: **this one**
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## known bugs
* on phones, it is *possible* to make the navpane so small that the resize buttons disappear
  * happens if you navigate into a folder 7+ levels deep, reduce the navpane size so the `a` button is barely visible, then disable `a`
  * **fix:** open the js prompt (click the bottom-left `π`) then execute `,.` (comma dot) and click `reset settings`

## new features
* new permission `g`: read-access only if you know the full URL to a file; folder contents are hidden, cannot download zip/tar
* new volume flag `fk`: generate per-file accesskeys, which are then required by `g` users to access files, making it harder to bruteforce URLs
  * users with full read-access can see the accesskeys appended to the URLs when browsing folders
* [wget.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/wget.py): download files to the copyparty server by POSTing file URLs in the web-UI
* show a login prompt on 404/403 pages
* option to disable wordwrap in the navpane

## bugfixes
* loss of access to anon-read/write folders after logging in
  * affected filesearch, regular searching, and volume listings
* more aggressively `no-cache`, preventing cloudflare from eating api calls
* after deleteing all files inside a folder, don't delete the folder itself
  * was intended behavior but fairly confusing
* don't reshow tooltips when alt-tabbing
* accessibility: always hilight focused things
* markdown-editor modification poller doesn't cause performance issues after having a document open for several months
* mtp plugins [audio-bpm.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/audio-bpm.py) and [audio-key.py](https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/audio-key.py) explicitly asks for just the first audio stream, which prevents ffmpeg from transcoding video (nice)

## other changes
* updated some web-deps
  * marked: `v1.1.0` -> `v3.0.4` (with modifications)
  * easymde: `v2.14.0` -> `v2.15.0` (with modifications)
  * codemirror: `v5.59.3` -> `v5.62.3` (with modifications)
  * hashwasm: `v4.7.0` -> `v4.9.0`
* easymde uses the external `marked.js` to save some space
* README.md has the same maxwidth as in the viewer/editor
* show a toast if there's an unhandled promise reject
* markdown-editor shows the current line number
* cfssl.sh (certificate generator) asks for fqdn instead of inventing something
* sfx binaries try to use python3 explicitly since a lot of distros don't have a /usr/bin/python at all




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0909-0721  `v1.0.2`  it is still 9/9

blessed by the strongest, *this will surely be the final version*
* latest important update: [v1.0.1](https://github.com/9001/copyparty/releases/tag/v1.0.1)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## bugfixes
* audio equalizer (broke in v1.0.1)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0908-2259  `v1.0.1`  happy 9/9

blessed by the strongest, this will surely be the final version
* latest important update: **this one**
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* click an open tab to close it (thx daniiooo)

## bugfixes
* multipart POSTs could get incorrectly rejected with `protocol error after field value`
  * had a `0.14%` chance of happening (worst-case; 1400 mtu, 2 offsets)
  * affected stuff like saving markdown documents, renaming files, ...
  * did **not** affect file uploads, and reverseproxy probably helped prevent it
* filedrop UI could let you try to upload/search without the necessary permissions
  * purely cosmetic, would immediately fail with a slightly cryptic error message
* apply a different equalizer tuning for some browsers
  * some permutations of chrome and win10, and also some phones, have incorrect Q scaling at higher frequencies, causing treble to be massively boosted
  * now tries to detect this by sampling the frequency response at 15khz and setting different gains (less dangerous than touching Q)

## other changes
* search ui does not initiate searches as eagerly if the textbox has a very short value
  * helps prevent overloading slow browsers with accidental wildcard searches




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0907-2118  `v1.0.0`  sufficient

we did it reddit 👉😎👉
* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## known bugs (all harmless)
* the website may let you attempt to upload stuff without write-access
  * fails gracefully with an error-message so it's all good

## new features
* separate dropzones for uploading and searching! no more confusing modeswitching
  * and the dropzone is global, so just drop files into the browser to upload / search 🚀🚀🚀
* add 10-minute indicators to the audio player seekbar
* make-sfx: argument `fast` reduces compression level

![2021-0908-010348-firefox-fs8](https://user-images.githubusercontent.com/241032/132421531-efdc1165-785b-422d-bb5f-8b551c335c39.png)

## bugfixes
* moving/deleting files when running without `-e2d` (thx ixces)
* zip/tar downloads: single folders are now the root element of the archive (not their contents)
  * not really a bug but sufficiently unexpected
* tiny lightmode fix + minor errormessage cleanups

## other changes
* crashpage: replace irc handle with new-github-issue link (i'm `+G` anyways heh)
* meta/github stuff
  * renamed `master` branch to `hovudstraum` ("primary river" in nynorsk)
  * add [CONTRIBUTING](https://github.com/9001/copyparty/blob/hovudstraum/CONTRIBUTING.md), [code of conduct](https://github.com/9001/copyparty/blob/hovudstraum/CODE_OF_CONDUCT.md), and [issue templates](https://github.com/9001/copyparty/tree/hovudstraum/.github/ISSUE_TEMPLATE)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0905-2306  `v0.13.14`  inline readme.md

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* `README.md` is shown below the directory listing
  * can be disabled with `--no-readme`
* new option `--no-logues` disables prologue/epilogues in directory listings
* new option `--no-dot-mv` disallows moving dotfiles (or folders containing them)
* new option `--no-dot-ren` disallows renaming dotfiles (or making something a dotfile)

## bugfixes
* fix upload ETA if there is some idle time between batches
* upload/filesearch with turbo enabled should be even faster now
* markdown-editor scroll desync if document contains offsite images
* better fix for the upload status list pushing the rest of the page around

## other changes
* sfx repacks with `no-fnt` will use `Consolas` instead which does not look terrible on windows




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0903-1921  `v0.13.13`  basic-auth

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

note: `copyparty-sfx.py` is https://github.com/9001/copyparty/commit/5955940b82adddb7149125a60463aba22f1c8c31 which fixes upload eta

## new features
* provide password using basic-authentication
  * useful for clients which don't support cookies or appending queries to the URL
  * order of precedence: `?pw=foo query` > `cppwd cookie` > `basic-auth`
* show OK/Cancel buttons in OS-defined order
  * Windows does OK/Cancel, everything else is Cancel/OK
* crashpage: include recent console messages
* js-repl: command history / presets

## bugfixes
* "fix" the file-list jumping around during uploads
  * ...by adding a massive padding to the uploads list
* make-sfx: set correct version-info on repack
* make-sfx: fix no-dd css modifier

## other changes
* move column-hider buttons above the header so they're not as easy to hit by accident
* jpeg thumbnails are slightly smaller




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0901-2148  `v0.13.12`  september

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* show useragent on the crashpage (plus some ui cleanup)

## bugfixes
* thumbnail-zoom hotkeys
* add vertical scrollbar to toasts if necessary
* cut/paste of more than roughly 30'000 files at once

## other changes
* replaced the video icon with a play button in the [browser-icons.css](https://github.com/9001/copyparty/tree/master/docs#example-browser-css) example:

![2021-0902-002101-firefox-fs8](https://user-images.githubusercontent.com/241032/131753177-6741d2af-6220-4f42-aaef-8439171cc0be.png)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0830-2032  `v0.13.11`  selective listening

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## bugfixes
* bind specific interfaces which are not `127.0.0.1`

## other changes
* sfx should be a tiny bit smaller



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0830-0102  `v0.13.10`  The Net reference

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* click the bottom-left `π` for a js eval prompt
  * good for debugging on phones (and a nice meme)

## bugfixes
* file uploads now happen in alphabetical order
* the default text is selected in prompts (text-input messageboxes)
* crash-page was slightly out-of-bounds on phones
* cheap performance fix when renaming >500 files
* minor ux fixes for old browsers / iOS ~10

## other changes
* return to volume listing after logging in
* fully drop support for playing ogg/vorbis/opus on iOS older than 14
  * final version where this *somewhat* worked was [v0.13.9](https://github.com/9001/copyparty/releases/tag/v0.13.9)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0829-0024  `v0.13.9`  the iOS update

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* iOS: play ogg/vorbis/opus files in the background and when the screen is off
  * but please don't touch the lockscreen play/pause button unless `os-ctl` is enabled in the `🎺 media player options` tab
    * safari 15 is rumored to support `MediaSession` so it should *magically work* when that is out

## bugfixes
* iOS: browsers no longer randomly crash when playing an ogg file

## other changes
* tray drawer is a bit smaller (the bottom right burger thing)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0828-0255  `v0.13.7`  dot-dot-dot

(throw more dots, more dots)

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* grid-view: filenames longer than 3 lines are truncated with `...`
  * the full filename appears as a tooltip on hover
  * use the `chop` buttons to adjust the limit

## bugfixes
* the 300 msec delay when tapping just about *anything* on phones
  * iphones got slightly better too (still needs the tooltip workaround)
* center tooltips horizontally + close on scroll + fix vertical margin

## other changes
* folder icons are now displayed top-left on thumbnails since it crashed with the ellipsis stuff
  * which also simplifies the [browser-icons.css](https://github.com/9001/copyparty/blob/master/docs/browser-icons.css) example



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0826-2209  `v0.13.6`  the final countdown

* latest important update: [v0.13.5](https://github.com/9001/copyparty/releases/tag/v0.13.5)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* total ETA until all the queued upload/searches are finished
* shows a toast notification with a summary after all uploads finish
* colored status indication for uploads/searches
* shows a warning if uploads/searches are blocked by the up2k flag/mutex
* replaced most monospace text with SourceCodePro
  * looks SO MUCH BETTER on windows

![nu_2-fs8](https://user-images.githubusercontent.com/241032/131047767-8844c829-d336-438e-b7db-c28f084c3397.png)

## bugfixes
* lock navigation focus inside popup messages, we proper modals now
* hashing didn't pause when `parallel uploads` was 0 (arguably a bug)
* navpane could scroll horizontally
* toggling file-search in the middle of an upload queue would affect the remainder of the queue
  * now the files are tagged with search/upload labels as they're added which makes much more sense
* top-level folder thumbnails could 404
* fix up2k-turbo for markdown documents
* fix files skipping the busy-list entirely with turbo enabled
* more predictable(?) file-search behavior when turbo is enabled
* the up2k flag/mutex could get stuck in limbo between two browser tabs if disabled while that tab holds it
* add missing hotkey hint (thumbnail toggle, bottom right)
* minor rice and html-escape fixes for modals and toasts
* avoid android-firefox bug where `number.toFixed(1)` returns `10.00` instead of `10.0` for certain values of 10




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0816-0640  `v0.13.5`  time-travelers friend

* latest important update: **this version**
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* button to scroll navpane to the open folder
  * also automatically does this on page load

## bugfixes
* unpost only worked for the `/` volume
* up2k-client could break on interesting folder-names
* moving more than 100 files at once across browser tabs
* basic-upload into folders with upload rules didn't really work
* ui indicated that renaming multiple files was impossible (but you still could tho)

## other changes
* tiny js optimizations
* even more ancient browsers (including opera 11, hipp hipp) can now use the thumbnail-view and image viewer




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0814-2046  `v0.13.3`  this side up

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* image-viewer: rotate images and videos (hotkeys `R` and `shift-R`)
* video-thumbnails: apply rotation hints from container
* image-thumbnails: apply rotation hints from exif
* image-thumbnails: higher quality AND slightly smaller
  * fix loss of detail on resize
* argument `--th-mt` specifices number of cores to use for thumbnailing
  * default is 0 which means all cores

## bugfixes
* image-viewer: fix pinch-zoom (broke in 0.11.19)
  * on the bright side: zoom is now less buggy than ever

## other changes
* (probably extremely minor) performance tweaks in the image-viewer




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0812-2042  `v0.13.2`  jet engine removal

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* toggle file-selection in the image viewer with hotkey `s` or using the `sel` button

## bugfixes
* chrome would max a cpu core (and consume even more ram than usual) after sitting idle in the browser for a few weeks due to recursive setTimeouts
  * just the `setTimeout` call itself took like 67 msec seriously
  * (firefox was completely fine)
* button placement in huge modals
* play videos in the gallery when clicked
* cut/paste files on ancient chrome versions




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0809-2028  `v0.13.1`  ephemeral

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* ephemeral uploads - set the volume flag `:c,lifetime=600` to delete files 10 minutes after upload
  * feature can be disabled with `--no-lifetime`
* volume flag `:c,rescan=60` to rescan a volume for new/modified files every 60 seconds 
  * same as the old `--re-maxage` except per-volume
* [prisonparty.sh](https://github.com/9001/copyparty/blob/master/bin/prisonparty.sh) - run copyparty in a chroot if you don't trust the volumes

## bugfixes
* handle more exceptions
* dont crash on startup if `XDG_CONFIG_HOME` is invalid
* up2k-ui: toggle button to continue hashing while uploading did nothing
* replace filesystem paths with vfs paths in exceptions returned to the user
* sfx.py: return 1 on exceptions




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0808-0214  `v0.13.0`  future-proof

* **latest stable release:** [v0.12.12](https://github.com/9001/copyparty/releases/tag/v0.12.12)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)

## new features
* reinvented `alert`/`confirm`/`prompt` because [google/whatwg is getting rid of them](https://github.com/whatwg/html/issues/6897#issuecomment-885773622)
* upload quotas (num.files, total bytes) and rotation, see [readme#upload-rules](https://github.com/9001/copyparty#upload-rules)
* streaming compression of uploads to gz or xz, see [readme#compress-uploads](https://github.com/9001/copyparty#compress-uploads)
  * not compatible with up2k and breaks file checksums (dupe-detection, file-search)
* another mtp example ([youtube manifest parser](https://github.com/9001/copyparty/blob/master/bin/mtag/yt-ipr.py))

## bugfixes
none! just new bugs this time

## other changes
* more accurate advice from the up2k searchmode explainer
* warning prompt if you try to open a massive transfer log in the up2k ui
* additional --help sections and early vt100 stripper
* chrome performance fixes in file selection




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0806-0910  `v0.12.12`  lock your doors

[terribly stable](https://www.youtube.com/watch?v=FAVR-FnWGjo)
* if upgrading from v0.11.x or before, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* forgot a mutex on renames/moves
* file metadata could persist after delete
* relative moves of relative symlinks could break/unlink



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0805-2253  `v0.12.11`  batch-rename

"stable"
* if upgrading from v0.11.x, see [v0.12.4](https://github.com/9001/copyparty/releases/tag/v0.12.4)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## known bugs
* mtp indexing can halt if files are renamed/moved in the middle of a rebuild
  * restart copyparty and it'll resume just fine

## new features
* batch-rename! inspired by foobar2000
  * rename multiple files based on regex and/or media tags
* [`media-hash.py`](https://github.com/9001/copyparty/tree/master/bin/mtag), new mtp module
  * generates `vhash` and `ahash` -- video and audio checksums which can help in spotting dupes
  * usage: `-mtp ahash,vhash=f,media-hash.py` or per-volume `:c,mtp=ahash,vhash=f,media-hash.py`

![batch-rename-fs8](https://user-images.githubusercontent.com/241032/128434204-eb136680-3c07-4ec7-92e0-ae86af20c241.png)

## bugfixes
* renaming single symlinks
* upgrading v0.11 volume arguments on windows
* thumbnails of files with multiple video tracks (theoretically)
* race in the httpd threadpool which could cause a tiny performance drop
* sfx-repack with `no-fnt` / `no-dd`
* funky padding in some browsers




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0801-2249  `v0.12.10`  mth

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47) (v0.12.x is almost there)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* `-mth`: list of tags to hide by default in the browser

## bugfixes
* better codec detection when using mutagen for tag parsing



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0731-2240  `v0.12.9`  ah yes lightmode

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47) (v0.12.x is almost there)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* lightmode rename ui



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0731-2217  `v0.12.8`  better rename ui

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47) (v0.12.x is almost there)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* better rename ui



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0731-1121  `v0.12.7`  preserve tags

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47) (v0.12.x is almost there)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* loss of tags when renaming / moving files within a volume, and when deleting dupes
  * restart copyparty (or rescan in the admin panel) to fix the missing tags




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0731-1038  `v0.12.6`  it keeps happening

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47) (v0.12.x is almost there)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* toggle-button to show dotfiles (hidden files)

## bugfixes
* renaming files which contain url-escaped characters
* access display (top-right) didn't include move permissions
* thumbnails aren't thumbnailed

## other changes
* move toasts bottom-right (next to the edit buttons) due to phones
* make-sfx is faster and better



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0730-1728  `v0.12.5`  rfc3986 2nd season

this release was made from all-natural, free-range code [PXL_20210730_160240244.jpg](https://ocv.me/i/PXL_20210730_160240244.jpg) (☞ﾟ∀ﾟ)☞ [PXL_20210730_174219083.jpg](https://ocv.me/i/PXL_20210730_174219083.jpg)

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47) (v0.12.x is almost there)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## upgrade notes
nothing new since v0.12.3 -- short summary of [v0.12.3](https://github.com/9001/copyparty/releases/tag/v0.12.3) and [v0.12.1](https://github.com/9001/copyparty/releases/tag/v0.12.1):
* `--no-mv` disables file/folder move ops
* `--no-del` disables file/folder delete and unpost
* `--unpost 0` disables unpost
* databases upgrade to v5; incompatible with v0.12.1 and older

## bugfixes
* multiselect zip download (broke in v0.12.1)
* filenames of multiselect zip downloads when first item contains " or % (was always broken)
* renaming files inside folders with url-escaped characters



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0730-0652  `v0.12.4`  fix permission groups

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47) (v0.12.x is almost there)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx: [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## upgrade notes
short summary of [v0.12.3](https://github.com/9001/copyparty/releases/tag/v0.12.3) and [v0.12.1](https://github.com/9001/copyparty/releases/tag/v0.12.1):
* `--no-mv` disables file/folder move ops
* `--no-del` disables file/folder delete and unpost
* `--unpost 0` disables just unpost
* databases upgrade to v5; incompatible with v0.12.1 and older

## bugfixes
* fix listing multiple users for the same permission-set
  * `-v .::rw,u1,u2,u3` now works, the workaround was `-v .::rw,u1:rw,u2:rw,u3`



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0729-2232  `v0.12.3`  unpost

1001GET (;_;)
* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

see [v0.12.1](https://github.com/9001/copyparty/releases/tag/v0.12.1) upgrade-notes regarding new opt-out features

## upgrade notes
* new argument `--unpost 0` (and/or `--no-del`) disables the new unpost feature
* your up2k databases will upgrade from v4 to v5; backups are made automatically
  * v5 DBs require copyparty v0.12.3 or newer, so use the backups for older versions

## new features
* unpost! uploaders can delete their uploads within `--unpost` seconds (default is 12 hours)
  * can be disabled by setting `--unpost 0` or with `--no-del`

## bugfixes
* deleting single files (metadata could persist in db)
* `--ls` broke in v0.12.1
* toasts with `<pre>` tags had massive margins
* hopefully fix a bug where malicious POSTs through an nginx reverse-proxy could put the connection in a bad state, causing the next legit request to fail with bad headers

## other changes
* uploader-ip and upload-time is stored in the database
  * but only viewable through an sqlite3 shell;
    `sqlite3 .hist/up2k.db 'select ip, rd, fn from up where ip'`




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0727-2355  `v0.12.1`  filed

```
 <&ed> copyparty became a file manager, trying to think of a release name
 <&ed> "far out", pun on far manager, there we go
<+des> ed: filed
<+des> fil-ed
```

* **latest stable release:** [v0.11.47](https://github.com/9001/copyparty/releases/tag/v0.11.47)
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to v0.11.47 or this version)
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## upgrade notes
* permission `a` no longer exists; is automatically translated to `r` + `w`
* new argument `--no-del` disables all delete operations
* new argument `--no-mv` disables all move/rename operations
* new argument `--no-voldump` disables the volume/permission summary on startup

## new features
* file manager! cut/paste, rename, delete files
  * new permission `m` (move) allows renaming files in (and moving files *out of*) that volume
  * new permission `d` (delete) allows deleting things in that volume
  * hotkeys `ctrl-X`, `ctrl-V` to cut/paste, `F2` to rename, `ctrl-K` to delete
  * tags follow the files when moved; thumbnails just regenerate
* select files/folders in the browser using the keyboard
  * click a file row and use cursor-keys to navigate
  * ctrl-cursor to also scroll the viewport
  * shift-cursors to expand selection
  * spacebar and `ctrl-A` toggles selection
* periodic volume rescan
  * detect and index files coming into volumes from the outside (sftp, rsync, ...)
  * will probably get an inotify alternative at some point but this is more reliable
* list all volumes and permissions on startup
* print server IPs on macos and windows too

## bugfixes
* tags are displayed for symlinked/dupe files
* mkdir defaults to 755, used to be the python-default 777, sorry
* ensure that the multiprocessing workers start correctly (and crash otherwise)
* more reliable db backups on upgrade, using the native sqlite3 backup feature
* signal handler; macos could get stuck on shutdown
* other minor stuff
  * centos7 support fixes
  * missing mojibake support (centralized most of it)
  * better support for buggy windows smb drives
  * edgecases with relative symlinks

## other changes
* replaced the md-editor toasts with the new general-purpose ones




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0722-0809  `v0.11.47`  On Error Resume Next

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.45](https://github.com/9001/copyparty/releases/tag/v0.11.45) if clients use up2k over plaintext http
  * [v0.11.43](https://github.com/9001/copyparty/releases/tag/v0.11.43) fixes stability in the uploader client
  * [v0.11.41](https://github.com/9001/copyparty/releases/tag/v0.11.41) if running as a service with `-lo`
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* crashpage: add option to ignore exceptions and continue
  * but please do report them so they can be fixed properly w



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0722-0642  `v0.11.46`  chrome friendly

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.45](https://github.com/9001/copyparty/releases/tag/v0.11.45) if clients use up2k over plaintext http
  * [v0.11.43](https://github.com/9001/copyparty/releases/tag/v0.11.43) fixes stability in the uploader client
  * [v0.11.41](https://github.com/9001/copyparty/releases/tag/v0.11.41) if running as a service with `-lo`
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* ignored `ResizeObserver loop limit exceeded` in the exception handler
  * chrome [randomly throws this](https://bugs.chromium.org/p/chromium/issues/detail?id=809574) from the `<video>` UI, nice
* logout link could 404



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0720-2123  `v0.11.45`  user friendly

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.45](https://github.com/9001/copyparty/releases/tag/v0.11.45) (this ver) if clients use up2k over plaintext http
  * [v0.11.43](https://github.com/9001/copyparty/releases/tag/v0.11.43) fixes stability in the uploader client
  * [v0.11.41](https://github.com/9001/copyparty/releases/tag/v0.11.41) if running as a service with `-lo`
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* login/logout link in the top-right corner
  * also shows account name + current access level (per-folder)

## bugfixes
* avoid loading the wasm hasher multiple times
  * it would reload every time the up2k tab was selected, probably dangerous
  * only affects clients using up2k with plaintext http (not https)
* tooltips on iphones, again

## other changes
* crashpage now includes localstore contents
* the up2k filesearch "explain" link now mentions lack of write permissions, if that is the case



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0719-2303  `v0.11.44`  smol fix

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.43](https://github.com/9001/copyparty/releases/tag/v0.11.43) fixes stability in the uploader client
  * [v0.11.41](https://github.com/9001/copyparty/releases/tag/v0.11.41) if running as a service with `-lo`
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* browser crash if the audio player runs into the next folder while the folder sidebar is closed (introduced in 0.11.42)

## other changes
* make-sfx.sh: `no-fnt` and `no-dd` shaves another ~10kB



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0718-2356  `v0.11.43`  ux is my passion

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.43](https://github.com/9001/copyparty/releases/tag/v0.11.43) (this ver) fixes stability in the uploader client
  * [v0.11.41](https://github.com/9001/copyparty/releases/tag/v0.11.41) if running as a service with `-lo`
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* explain the up2k modeswitch in filesearch results

## bugfixes
* up2k-ui coherence check was a bit too picky



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0718-2122  `v0.11.42`  in case of tags

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.42](https://github.com/9001/copyparty/releases/tag/v0.11.42) (this ver) if you have `-mtp` parsers *and* use Mutagen to read tags
  * [v0.11.41](https://github.com/9001/copyparty/releases/tag/v0.11.41) if running as a service with `-lo`
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* if Mutagen fails to read a file, it retries with FFprobe
* `--no-mtag-ff` bans all use of FFprobe to read tags
* hotkeys `i/k` now ensure the active folder stays in-view

## bugfixes
* tag search was case-sensitive in some cases (most importantly `key>=1a` did not work as intended)
* advanced-search would break if search terms were double-space separated
* the preferred key-notation did not apply to search results (did rekobo-alnum instead)
* tooltips for column headers didn't work for newly-hidden columns
* no more surprise tooltips when switching tabs

all these changelogs are sorted by importance btw so here's the least important bugfix (since it doesn't affect anyone i know)
* codec/format info was not collected from Mutagen when scanning audio files
  * this broke `mtp` (external metadata parsers)
  * you avoided this issue by not having Mutagen installed, and/or by using `--no-mutagen`
  * if you *were* using Mutagen to collect tags, you can do a single run with `-e2tsr` for a full rescan if you care




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0717-1553  `v0.11.41`  caas

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.41](https://github.com/9001/copyparty/releases/tag/v0.11.41) (this ver) if running as a service with `-lo`
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* add shortcut to toggle list/grid-view in the audio drawer
* combine the mkdir/newdoc/msg tabs on narrow screens
* sd-notify support to properly use copyparty as a systemd service
  * other units which `After=copyparty` will be delayed until copyparty is ready to accept connections
  * updated the [unit example](https://github.com/9001/copyparty/blob/master/contrib/systemd/copyparty.service) with the changes (`Type=notify` and `SyslogIdentifier=copyparty`)
* markdown editor hotkeys now work properly on dvorak keyboards
  * the hotkeys use the qwerty layout which seems to be preferred according to stackoverflow

## bugfixes
* clean shutdown on SIGINT and SIGTERM
  * previously, when running as a sysv/systemd service, a `service stop` would lose:
    * lots of log messages when using `-lo`
    * information about incomplete uploads for the past 30 seconds

## other changes
* lots of new tooltips with hotkeys info
  * also explains the cryptic codec/bitrate columns
  * and iphones can now hide tooltips by tapping them since safari is safari
* increased up2k snapshot interval from 30sec to 5min now that SIGTERM is a clean shutdown
* finally found something the `zip_crc` mode is good for: supporting PKZIP v2.04g from october 1993 (absolutely worth)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0714-2313  `v0.11.40`  video player tweaks

(commit #900, checkem)

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) (but skip right to this version)
* recent maybe-important updates:
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* see steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) if upgrading from something before that
* see steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* allow ctrl-clicking the main tabs to open other views in new tabs
* gallery (the image viewer / video player, accessible from the grid view):
  * when playing a video, the audio player will pause and autoresume
  * hotkey `r` to toggle video loop
  * hotkey `c` to toggle continue-playing-next-video
    * and added a toggle button for those two ^
  * remember the mute settings for the next videos
  * encourage browser to cache aggressively
  * dispose videos to stop them from buffering in the background

## bugfixes
* gallery: some keyboard hotkeys were buggy depending on focus

## other changes
* adjust the sfx text-editor warning to show it's OK to use hex editors
* minor ux tweaks
  * settings-reset link on the crashpage (underline, brightmode color)
  * brightmode: gallery filename / download link
  * main tabs unselectable




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0712-2254  `v0.11.39`  mob psycho

(get it? cause its the 100th release, at commit 888 even)

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* add `--log-thrs` which periodically logs a summary of active threads
* `--stackmon` also runs inside the worker forks when using `-j`
* video player: hotkeys `f` for fullscreen and `m` for mute
* add a link which clears the settings on the js crash page, in case someone gets stuck by enabling grid mode on ie11 for example

## bugfixes
* the `?stack` link in the controlpanel required `/` to be a volume
* image gallery: shrink the image a bit so the link doesn't overlap
* cheap race "fix" for pypy

## other changes
* better thread names



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0711-2251  `v0.11.37`  just 2b safe

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* log the list of files that couldn't be included in a tar/zip download

## bugfixes
* any potential cases of [surprising values in default arguments](https://user-images.githubusercontent.com/241032/125212304-bdb5e980-e2ac-11eb-962f-e1ee5cce510d.png), couldn't see anything bad luckily



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0711-0439  `v0.11.36`  foreshadowing

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* video player -- click a webm/mp4 in the grid-view to play it
  * only does formats/codecs supported by your browser for now (thats the foreshadowing part)
* `--th-clean 0` disables periodic cleanup of the thumbnail cache 

## bugfixes
* image viewer trying to display folders named `something.jpg`
* py2 could not list/access files with unicode filenames when using volumes
  * when is centos7 eol again

## other changes
* some more context in exceptions
* thumbnail-generator: `mts` added to list of video file extensions



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0709-1512  `v0.11.34`  multi-process drifting (at low latency)

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* faster http replies! reduced the time to establish new connections, so:
  * up to 25% faster round-trip time on short http requests with `-j1` (server-default), but more importantly...
  * up to 3.3x faster with `-j4` (now almost equal to `-j1`) and a single client doing stuff, but wait it gets better:
  * up to 6.6x faster with `-j4` and multiple clients hammering the server
  * but note that higher `-j` values adds more connection latency in exchange for processing power, https://en.wikipedia.org/wiki/Thundering_herd_problem
* discard log messages early when `-q` is set without `-lo`, giving better multiprocessing performance

## bugfixes
* fix general loss of centos7 support (TLnote: early 2.7 versions) introduced in [v0.11.30](https://github.com/9001/copyparty/releases/tag/v0.11.30)
  * also fixed downloading folders as zip-files which centos7 never could

## other changes
* `-j1` will be forced for python 2.7 because it cannot pickle tcp servers
* accessing `?stack` works on any url as long as you're admin *somewhere*
* the `-j` loadbalancer messages are gone because the loadbalancer is gone
  * should give a teeny-tiny performance boost to multiprocessing on uploads




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0707-0845  `v0.11.33`  moms spaghetti

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.33](https://github.com/9001/copyparty/releases/tag/v0.11.33) (this ver) fixes stability in the uploader client
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) fixes a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* *another* crash in the up2k UI
* separate turbo-warning for search mode
* stop running ahead with handshakes if something uploaded recently
  * reduces the odds of skipping an upload which should have become a symlink



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0706-1958  `v0.11.32`  turbo button

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.32](https://github.com/9001/copyparty/releases/tag/v0.11.32) (this ver) fixes stability in the uploader client + a case of filesystem paths being unmasked
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* `turbo button` in the settings panel for superfast resume of massive uploads 
  * good for when you were in the middle of uploading 100'000 files and had to restart for some reason
  * comes at a serious cost: files will be skipped as long as they exist on the server with the right filesize, even if they could be incomplete uploads or are otherwise different from your local files, so you should do a "verification pass" by disabling turbo + refreshing + redoing the upload once you make it through
  * when combined with the new `date-chk` button it *should* notice and resume incomplete uploads but please do the verification pass anyways
  * all of this is explained in the tooltip for the button so idk why im putting it here too
* `-lo` enables xz-compressed logging to file in addition to printing to the console
  * with logrotate if the filename contains date-format-strings (like `%Y-%m-%d`)
  * when combined with `-q` it disables console-logging and only logs to file, gives a tiny speed boost depending on OS
  * also cleans up a few places with plain prints instead of the threadsafe pretty ones
* the volume-flags summary on startup now also print *which* volume they're talking about

## bugfixes
* `dir.txt` inside the thumbnails folder could be downloaded; possibly bad since it contains absolute-paths from the host filesystem
* [v0.11.31](https://github.com/9001/copyparty/releases/tag/v0.11.31) added parallel handshakes which could cause files to checksum and upload out-of-order, fixed
  * this also uncovered another UI-crash in the up2k client (nice) which is now also fixed separately
* a few more cases of recursive symlinks are detected and defused
  * symlink pointing to its own folder when creating a tar/zip
  * initial directory scanning (`-e2ds`)
    * initial directory scanning is now a tiny bit slower, sorry
* `-nw` didn't apply to PUT uploads
* more invalid requests get a sensible-ish reply stating what the client did wrong




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0704-1444  `v0.11.31`  an extra pair of hands

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.30](https://github.com/9001/copyparty/releases/tag/v0.11.30) fixes stability in the uploader client
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* parallel handshakes
  * faster uploads and file-search, especially on tiny files / high-latency connections

## bugfixes
* send keepalive handshakes when an upload has been paused / idle for 5h 45min so it doesn't expire
  * fixes one of the v0.11.30 known-bugs but still no idea what that other thing was, something about "bad file descriptor" right before a power outage so the logs are lost, shoganai
* race conditions in the up2k-server which couldn't be hit before parallel handshakes was added



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0701-2027  `v0.11.30`  the up2k-client update

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.30](https://github.com/9001/copyparty/releases/tag/v0.11.30) (this ver) fixes stability in the uploader client
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## known bugs
* if an upload is paused by setting `parallel uploads` to `0` in the UI...
  * ...for "about an hour", it *might* be unable to resume
  * ...for 6 hours or more, it is **definitely** unable to resume

unless the upload was paused for 6 hours or more, it can probably be resumed by refreshing the website and restarting the upload ("probably" because haven't been able to reproduce)

## new features
* up2k-client: 100x faster initialization when adding lots of files
* cachebuster to force chrome to use the correct js/css files since it ignores the no-cache header
* make `-nw` apply to more stuff (up2k skips creating files)

## bugfixes
* up2k-client:
  * fix crash caused by parallel uploads running far ahead, ui trying to update stuff it already purged
    * mostly problematic when uploading lots of small files mixed with slightly-larger files
  * general robustness
    * recover from tcp/dns issues during chunk-uploads
    * recover from antivirus yanking files mid-read
    * ignore server complaining about duplicate chunks, it's fine
  * help chrome not get stuck when it sees a file named `aux.h` on windows
  * notice and panic on more errors
    * and stop trying to do things after something died to an unhandled exception
  * less confusing debug messages regarding sha512 library selection




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0629-2351  `v0.11.29`  thx kip

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features suggested by kipu
* pause uploads by setting `parallel uploads` to `0`
* increase max `parallel uploads` to 16 (using +/- buttons) and 64 (by manual text entry) to accomodate sad american internet connections
* also look for `cover.jpg` and `cover.png` as folder thumbnails by default, adjustable with `--th-covers`
* change the description in the sfx so the corruption warning is the first plaintext you see

## other new features
* search ui could be visibly confusing if the final text entry event happened in the middle of a search
* adjustable `tint` on the audio-player progressbar to make buffering updates less visually distracting
* per-http-connection request counter appended to the transfer speed summary

## bugfixes
* ctrl-clicking folders in the directory tree didn't open them in a new tab
* javascript panic-screen could display the wrong stack in some cases



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0628-1336  `v0.11.28`  fix no-accounts crash

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* recent maybe-important updates:
  * [v0.11.28](https://github.com/9001/copyparty/releases/tag/v0.11.28) (this version) fixes crash if no accounts are defined
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* adjust tree width with hotkeys `a/d`
  * thumbnail zoom is now shift+`a/d`
* control-panel link always points to the webroot (mostly cosmetic)

## bugfixes
* lost replies (http handler crash) if you're running without any accounts



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0625-2023  `v0.11.27`  audiogrid

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* additional steps for [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) apply to this version if upgrading from something before that
* additional steps for [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) apply to this version if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* seek in songs by scrollwheeling the seekbar (very popular request)
* in the gridview...
  * play audio files when the audio panel is open (press P to open it)
  * navigate into subfolders without doing a full-page reload
* when password is given in the URL (`?pw=wark`), copy into cookie for persistence

## bugfixes
* icon for the button to leave search results in grid-view




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0625-0110  `v0.11.26`  smooth

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* see [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) description if upgrading from something before that
* see [v0.11.24](https://github.com/9001/copyparty/releases/tag/v0.11.24) description if you ever used versions v0.11.20 through v0.11.23
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* play/pause makes audio volume fade in/out
* jump to start of song if previous-track button is pressed more than 3sec into it
* media-controls are now default-enabled
* censor user passwords in the server log

## bugfixes
* panic if pressing play/pause in a folder without music
* send utf-8 header for all css/js files (fixes unicode/emotes in custom css)
* when switching folders,
  * clear the mediasession (currently playing track info in the OS)
  * blank the audio seekbar 
* unlikely-to-encounter bugs:
  * retry filesearch if client hits a ratelimit
  * extremely-unlikely:
    * fix autoplay of audio in some buggy chrome installs (not any specific version; depends on win10 settings or something)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0622-1528  `v0.11.24`  no cover

* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* if upgrading from [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) or later and you use `-e2ts` to index audio tags:
  * do a single run with `-e2tsr` to wipe and reindex audio tags to fix songs with bad titles
  * if you have expensive `-mtp` parsers (bpm/key) and a huge database (or a slow server), then make a backup of the db before `-e2tsr` and use https://github.com/9001/copyparty/tree/master/bin#dbtoolpy to transfer your tags to the new db
* however if upgrading from something before that, then your database will be wiped anyways so forget the `-e2tsr` stuff above, check the [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) notes instead
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* don't pollute audio tags with metadata about embedded album covers (and other similar crosstalk)
* icon-generator: realize it's not a file extension when a whitespace appears
* discard and regenerate corrupted databases instead of giving up



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0621-1915  `v0.11.23`  in control, mk.II

* drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
  * but see the description in [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) if upgrading from something before that
* latest important update: [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20)
* latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
![copyparty-osctl-fs8](https://user-images.githubusercontent.com/241032/122821375-0e08df80-d2dd-11eb-9fd9-184e8aacf1d0.png)
* OS integration for the audio player
  * show media controls on the OS lock-screen
  * listen to media-hotkeys globally
    * play/pause, next/prev track, seek fwd/back
  * disabled by default; enable in the `🎺` tab

## bugfixes
* append current user's password to the cover URL so windows can actually display it
* disable scandir for python 3.5 and older (no contextmgr)
* disable u2idx (searching) if sqlite3 is not available
* skip blank tags on np-clip

## notes
when you get tired of seeing the OSD popup which Windows doesn't let you disable: https://ocv.me/dev/?media-osd-bgone.ps1



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0620-1925  `v0.11.21`  database.avi

* see [v0.11.20](https://github.com/9001/copyparty/releases/tag/v0.11.20) if upgrading from an older version
  * aside from that, no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* the latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## bugfixes
* more responsive browser during db rebuilds



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0620-1732  `v0.11.20`  database.rmvb

**this release will discard and rebuild your database** (`.hist/up2k.db`)
* no actions necessary, it just takes a while
* no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1) actually
* the old database will be backed up automatically just in case
* if you have expensive `-mtp` parsers (bpm/key) and a huge database (or a slow server), you can transfer your tags to the new db using https://github.com/9001/copyparty/tree/master/bin#dbtoolpy

reason: [v0.11.12](https://github.com/9001/copyparty/releases/tag/v0.11.12) changed the file checksum algorithm slightly, causing a mismatch between the server and client, and as a result:
* upload deduplication has been unpredictable
* filesearch could return false-negatives

## new features
* much faster filesearch in chrome
* skip hidden colums in the /np text
* support cygpaths when pointing to mtag tools

## bugfixes
* uploading folders through the up2k client would fail if the folder already existed on the server; now they merge
* change up2k hashlen to 33 bytes / 44 chars (mod24 bits) to fit base64 better, avoiding any padding bugs
* prefer client IP rater than proxy IP as fallback value when `--rproxy` is configured out of bounds
* correct indexing of files with names containing backslash on linux/macos

## other notes
* the latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0618-2332  `v0.11.19`  purely cosmetic

* drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* nothing big, no server fixes, just client tweaks
* recent important updates:
  * [v0.11.14](https://github.com/9001/copyparty/releases/tag/v0.11.14) fixed a deadlock in the thumbnails feature which was added in [v0.11.0](https://github.com/9001/copyparty/releases/tag/v0.11.0)
* summary of other recent updates:
  * [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18): audio preloading for near-gapless playback
  * [v0.11.17](https://github.com/9001/copyparty/releases/tag/v0.11.17): fix thumbnail cache eviction (*finally* something that broke in [v0.11.12](https://github.com/9001/copyparty/releases/tag/v0.11.12))
  * [v0.11.16](https://github.com/9001/copyparty/releases/tag/v0.11.16): more accurate audio equalizer
* the latest gzip edition of the sfx is [v0.11.18](https://github.com/9001/copyparty/releases/tag/v0.11.18)

## new features
* audio player: add some shadow to the timestamps in the progressbar
* audio player: silently stop playback if playing into a folder without music
* general ui: make radio selections more visible by using another text color
* general: smaller html responses by moving some stuff into the js (zopfli-compressed)

## bugfixes
* mobile devices: disable scrolling while viewing pictures in the lightbox
* mobile devices: tooltips in the toolbar
* android-chrome: text distortion in canvases when chrome decides to resize the viewport without invoking onresize like it should
* android-chrome: initial layout in up2k due to the viewport size taking some time to settle down
  * [totally appropriate fix](https://github.com/9001/copyparty/commit/57579b2fe5b86eaed062c050fb3c97d539db938f#diff-de02679bd0d9cdc88e772227cb23512033593913c128843e0bdf24810a786afaR1279-R1286)




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0617-2230  `v0.11.18`  seamless

* drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* no important fixes, mostly new features
* recent important updates:
  * [v0.11.14](https://github.com/9001/copyparty/releases/tag/v0.11.14) fixed a deadlock in the thumbnails feature which was added in [v0.11.0](https://github.com/9001/copyparty/releases/tag/v0.11.0)

## notes
this release includes [copyparty-sfx-gz.py](https://github.com/9001/copyparty/releases/download/v0.11.18/copyparty-sfx-gz.py), an additional sfx build which uses gzip compression rather than the usual bzip2; only useful for smoketests on minimal python builds. Note that both past and future releases can be converted from bzip2 to gzip by running [copyparty-repack.sh](https://github.com/9001/copyparty/blob/master/scripts/copyparty-repack.sh) on linux/macos/windows-msys2; this will produce the additional sfx in this release, `copyparty-extras/sfx-full/copyparty-sfx-gz.py` (see [sfx-repack](https://github.com/9001/copyparty#sfx-repack) for more info)

## new features
* **(almost) gapless audio playback!** partially powered by:
  * url suffix `?cache` to get a response without any `Cache-Control` directives
  * and using events for end-of-track instead of polling
* hotkey `b` to toggle breadcrumbs / directory tree sidebar
  * hotkey `p` is now play/pause
  * hotkey `m` is now parent-directory
* hilight the playing track in gallery mode too
* toggle to disable the now-playing clipboard buttons
* added lots of tooltips
  * threw aray the competing tooltip implementations and did a single ok one
* more accurate error-messages on upload failures due to filesystem permissions
* add another output to the sfx repacker (gzip-compressed python sfx)

## bugfixes
* file selection after switching from grid to list
* playback into next folder if the tree sidebar is closed
* show the link to exit search results even if columns are hidden
* make an effort to terminate clients cleanly on shutdown
* py2 volume listing with `-e2d`




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0616-2231  `v0.11.17`  another media update

* drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* recent important updates:
  * [v0.11.14](https://github.com/9001/copyparty/releases/tag/v0.11.14) fixed a deadlock in the thumbnails feature which was added in [v0.11.0](https://github.com/9001/copyparty/releases/tag/v0.11.0)

## new features
* hotkey `m` for play/pause
* make audio gain adjustable
  * cranking it way up behaves differently depending on browser; firefox adds a compressor, chrome just ***goes***
  * funfact, the base gain is `0.94` to avoid clipping due to imperfections in the equalizer curve
* responsive settings layout
* other minor ux tweaks
  * brightmode contrast and player widget
  * add gridlines to the files table
* print summary when thumbcache cleanup finishes

## bugfixes
* the audio-eq ui didn't handle leading/trailing decimals too well
* thumbcache-eviction mostly broke in [v0.11.12](https://github.com/9001/copyparty/releases/tag/v0.11.12) (and somehow nothing else so far)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0615-2351  `v0.11.16`  better eq

* drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* recent important updates:
  * [v0.11.14](https://github.com/9001/copyparty/releases/tag/v0.11.14) fixed a deadlock in the thumbnails feature which was added in [v0.11.0](https://github.com/9001/copyparty/releases/tag/v0.11.0)

## new features
* media player can now continue into the next folder
* eq curve supports both positive and negative values (and scales down to avoid clipping)
* browser columns now fully hide when hidden; reenable them in the settings tab
* other ux tweaks
  * add some icons
  * tree control buttons remain visible when scrolling

## bugfixes
* calibrated the eq for more correct frequency response




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0614-2201  `v0.11.15`  v for victory

* drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* recent important updates:
  * [v0.11.14](https://github.com/9001/copyparty/releases/tag/v0.11.14) fixed a deadlock in the thumbnails feature which was added in [v0.11.0](https://github.com/9001/copyparty/releases/tag/v0.11.0)

## new features
* audio equalizer (with a v-shaped default)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0614-0105  `v0.11.14`  frozen

* this release fixes a deadlock in the thumbnails feature introduced in [v0.11.0](https://github.com/9001/copyparty/releases/tag/v0.11.0)
  * if you cannot upgrade for some reason, use `--no-thumb` to avoid it
* drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)

## new features:
* `--rproxy` specifies which IP to display in logs when reverse-proxied
  * defaults to `1` which is the origin / actual client
* `--stackmon` periodically dumps a stacktrace to a file for debugging

## bugfixes:
* deadlock when converting thumbnails
* up2k-cli: recover from network errors during handshakes
  * have to fix chunks too eventually



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0612-1837  `v0.11.13`  image gallery

[v0.11.11](https://github.com/9001/copyparty/releases/tag/v0.11.11) is the latest well-tested version ("stable"), maybe keep that as a fallback
* otherwise a drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)

## recent updates
nothing really important happened since [v0.11.6](https://github.com/9001/copyparty/releases/tag/v0.11.6); quick summary:
* [v0.11.9](https://github.com/9001/copyparty/releases/tag/v0.11.9): fix zip/tar of recursive symlinks
* [v0.11.10](https://github.com/9001/copyparty/releases/tag/v0.11.10): fix direct tls connections
* [v0.11.11](https://github.com/9001/copyparty/releases/tag/v0.11.11): fix live-rescan without a root folder
* this ver only adds new features

## new features:
* image gallery / lightbox

## notes
if you want filetype icons on the thumbnails then check out [browser-icons.css](https://github.com/9001/copyparty/tree/master/docs#example-browser-css)



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0612-0228  `v0.11.12`  excuse the mess

big changes, **bugs likely**, keep [v0.11.11](https://github.com/9001/copyparty/releases/tag/v0.11.11) as a fallback and go whine in the irc
* otherwise a drop-in upgrade; no additional steps to consider since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)

nothing really important happened since [v0.11.6](https://github.com/9001/copyparty/releases/tag/v0.11.6); quick summary:
* [v0.11.9](https://github.com/9001/copyparty/releases/tag/v0.11.9): fix zip/tar of recursive symlinks
* [v0.11.10](https://github.com/9001/copyparty/releases/tag/v0.11.10): fix direct tls connections
* [v0.11.11](https://github.com/9001/copyparty/releases/tag/v0.11.11): fix live-rescan without a root folder
* this ver only fixes unlikely edge-cases

## new features:
* folder thumbnails if they contain `folder.jpg` or `folder.png`, good for music servers
* `--hist` stores the per-volume databases and thumbnails all in one place, instead of the `.hist` subfolders in each volume
* `--no-hash` disables file hashing, good for a simple searchable index, but keep in mind it disables file-search and dupe detection
  * both this and `--hist` can be adjusted per-volume with volflags, see readme
* thumbnails keep transparency
* `--th-ff-jpg` fixes video thumbnails if your FFmpeg is bad (macos)
* more info in the [admin panel](https://user-images.githubusercontent.com/241032/121763646-15422780-cb3e-11eb-8932-130af39acb48.png) (num.files queued for hashing or tags)
* `--css-browser` to set [custom CSS](https://user-images.githubusercontent.com/241032/121763647-15dabe00-cb3e-11eb-90a4-1628a072545c.png)
  * use `.prologue.html` or `.epilogue.html` to do this per-folder; that allows for javascript too
* cygpaths for windows, `-v c:\users::r` and `-v /c/users::r` both work now
* extremely minor (i think) performance improvements which probably drown in the new bloat

## bugfixes:
* mounting a volume deep inside another volume will no longer create additional databases, avoiding rescan of files in intermediate folders
  * backwards-compat so it will continue to use any intermediate databases made by v0.11.11 or older
* better error message on basic-upload into a folder that doesn't exist / without permission
* minor race introduced in 0.11.1 which could be triggered by an upload really early after starting the server




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0608-2143  `v0.11.11`  re:live

* drop-in upgrade, no additional steps since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* nothing really important since [v0.11.6](https://github.com/9001/copyparty/releases/tag/v0.11.6); quick summary:
  * [v0.11.9](https://github.com/9001/copyparty/releases/tag/v0.11.9): fix zip/tar of recursive symlinks
  * [v0.11.10](https://github.com/9001/copyparty/releases/tag/v0.11.10): fix direct tls connections
  * this ver: fix live-rescan without a root folder

## new features
* threadnames in the stackdump
  * also truncate/censor filepaths
  * most of the idle threads are indented + appear last
* up2k scans folders alphabetically (easier to eyeball progress)
* slightly better performance when sending files
  * and other minor performance tweaks
* sfx: all js/css files are zopfli-compressed
  * makes sfx bigger but resources are now 1/3 the size in transit

## bugfixes
* another live-rescan fix (for configs without a root-folder)
* fix janky load-balancing with `-jN`




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0608-0741  `v0.11.10`  dont leave me hangin

* drop-in upgrade, no additional steps since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)
* nothing really important since [v0.11.6](https://github.com/9001/copyparty/releases/tag/v0.11.6)
  * [v0.11.9](https://github.com/9001/copyparty/releases/tag/v0.11.9): fix zip/tar of recursive symlinks
  * this ver: fix direct tls connections

## bugfixes
* actually close tls connections
  * only affects direct https connections (no reverse-proxy between)
  * mainly problematic for zip/tar downloads



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0607-1822  `v0.11.9`  caught in a loop

* nothing too important (unless you have recursive symlinks somewhere)
* drop-in upgrade, no additional steps since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)

## new features
* `--ls` prints empty directories as well
  * so now links like that will be detected too

## bugfixes
* detect recursive symlinks when creating zip/tar files
  * the first iteration will be archived, then it bails
* support python 3.5 on windows by autosetting `--no-scandir`
* `sfx.sh` correctly disables bundled jinja2 when found on system




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0606-1709  `v0.11.8`  sharex

* nothing important
* drop-in upgrade, no additional steps since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)

## new features
* json replies from `bput` (basic uploader) by adding url parameter `j`
  * better sharex support, especially for interesting filenames
* append the filename extension when renaming uploads to avoid filename collisions



▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  
# 2021-0605-0133  `v0.11.7`  additional vtec

* nothing too important
* drop-in upgrade, no additional steps since [v0.11.1](https://github.com/9001/copyparty/releases/tag/v0.11.1)

## new features
* add [hash-wasm](https://github.com/Daninet/hash-wasm) as preferred fallback up2k hasher, does 250 MiB/s so like 7x faster
  * still keeping `asmCrypto` for older browsers but minified a bit
  * technically this allows for a single sha512 over the whole file rather than chunks...
* in gallery mode, open files in a new tab if there's a selection active
* `--ls`, which can be used to look for dangerous symlinks
  * `--ls '**,*,ln,p,r'` does a full scan of all volumes (as all users) and refuses to start if there are links leaving the vols (see `--help`)
* other minor optimizations

## bugfixes
* metadata indexing with single-threaded backends
* loader animation appears over thumbnails too
* restore support for firefox 12




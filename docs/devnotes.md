## devnotes toc

* top
* [future ideas](#future-ideas) - list of dreams which will probably never happen
* [design](#design)
    * [up2k](#up2k) - quick outline of the up2k protocol
        * [why not tus](#why-not-tus) - I didn't know about [tus](https://tus.io/)
        * [why chunk-hashes](#why-chunk-hashes) - a single sha512 would be better, right?
* [hashed passwords](#hashed-passwords) - regarding the curious decisions
* [http api](#http-api)
    * [read](#read)
    * [write](#write)
    * [admin](#admin)
    * [general](#general)
* [event hooks](#event-hooks) - on writing your own [hooks](../README.md#event-hooks)
    * [hook effects](#hook-effects) - hooks can cause intentional side-effects
* [assumptions](#assumptions)
    * [mdns](#mdns)
* [sfx repack](#sfx-repack) - reduce the size of an sfx by removing features
* [building](#building)
    * [dev env setup](#dev-env-setup)
    * [just the sfx](#just-the-sfx)
    * [build from release tarball](#build-from-release-tarball) - uses the included prebuilt webdeps
    * [complete release](#complete-release)
* [debugging](#debugging)
    * [music playback halting on phones](#music-playback-halting-on-phones) - mostly fine on android
    * [discarded ideas](#discarded-ideas)


# future ideas

list of dreams which will probably never happen

* the JS is a mess -- a ~~preact~~ rewrite would be nice
  * preferably without build dependencies like webpack/babel/node.js, maybe a python thing to assemble js files into main.js
  * good excuse to look at using virtual lists (browsers start to struggle when folders contain over 5000 files)
  * maybe preact / vdom isn't the best choice, could just wait for the Next Big Thing
* the UX is a mess -- a proper design would be nice
  * very organic (much like the python/js), everything was an afterthought
  * true for both the layout and the visual flair
  * something like the tron board-room ui (or most other hollywood ones, like ironman) would be :100:
    * would preferably keep the information density, just more organized yet [not too boring](https://blog.rachelbinx.com/2023/02/unbearable-sameness/)
* some of the python files are way too big
  * `up2k.py` ended up doing all the file indexing / db management
  * `httpcli.py` should be separated into modules in general


# design

## up2k

quick outline of the up2k protocol,  see [uploading](https://github.com/9001/copyparty#uploading) for the web-client
* the up2k client splits a file into an "optimal" number of chunks
  * 1 MiB each, unless that becomes more than 256 chunks
  * tries 1.5M, 2M, 3, 4, 6, ... until <= 256 chunks or size >= 32M
* client posts the list of hashes, filename, size, last-modified
* server creates the `wark`, an identifier for this upload
  * `sha512( salt + filesize + chunk_hashes )`
  * and a sparse file is created for the chunks to drop into
* client sends a series of POSTs, with one or more consecutive chunks in each
  * header entries for the chunk-hashes (comma-separated) and wark
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

### why not tus

I didn't know about [tus](https://tus.io/)  when I made this, but:
* up2k has the advantage that it supports parallel uploading of non-contiguous chunks straight into the final file -- [tus does a merge at the end](https://tus.io/protocols/resumable-upload.html#concatenation) which is slow and taxing on the server HDD / filesystem (unless i'm misunderstanding)
* up2k has the slight disadvantage of requiring the client to hash the entire file before an upload can begin, but this has the benefit of immediately skipping duplicate files
  * and the hashing happens in a separate thread anyways so it's usually not a bottleneck

### why chunk-hashes

a single sha512 would be better, right?

this was due to `crypto.subtle` [not yet](https://github.com/w3c/webcrypto/issues/73) providing a streaming api (or the option to seed the sha512 hasher with a starting hash)

as a result, the hashes are much less useful than they could have been (search the server by sha512, provide the sha512 in the response http headers, ...)

however it allows for hashing multiple chunks in parallel, greatly increasing upload speed from fast storage (NVMe, raid-0 and such)

* both the [browser uploader](https://github.com/9001/copyparty#uploading) and the [commandline one](https://github.com/9001/copyparty/tree/hovudstraum/bin#u2cpy) does this now, allowing for fast uploading even from plaintext http

hashwasm would solve the streaming issue but reduces hashing speed for sha512 (xxh128 does 6 GiB/s), and it would make old browsers and [iphones](https://bugs.webkit.org/show_bug.cgi?id=228552) unsupported

* blake2 might be a better choice since xxh is non-cryptographic, but that gets ~15 MiB/s on slower androids


# hashed passwords

regarding the curious decisions

there is a static salt for all passwords;
* because most copyparty APIs allow users to authenticate using only their password, making the username unknown, so impossible to do per-account salts
* the drawback of this is that an attacker can bruteforce all accounts in parallel, however most copyparty instances only have a handful of accounts in the first place, and it can be compensated by increasing the hashing cost anyways


# http api

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
| GET | `?lt` | in listings, use symlink timestamps rather than targets |
| GET | `?b` | list files/folders at URL as simplified HTML |
| GET | `?tree=.` | list one level of subdirectories inside URL |
| GET | `?tree` | list one level of subdirectories for each level until URL |
| GET | `?tar` | download everything below URL as a gnu-tar file |
| GET | `?tar=gz:9` | ...as a gzip-level-9 gnu-tar file |
| GET | `?tar=xz:9` | ...as an xz-level-9 gnu-tar file |
| GET | `?tar=pax` | ...as a pax-tar file |
| GET | `?tar=pax,xz` | ...as an xz-level-1 pax-tar file |
| GET | `?zip=utf-8` | ...as a zip file |
| GET | `?zip` | ...as a WinXP-compatible zip file |
| GET | `?zip=crc` | ...as an MSDOS-compatible zip file |
| GET | `?tar&w` | pregenerate webp thumbnails |
| GET | `?tar&j` | pregenerate jpg thumbnails |
| GET | `?tar&p` | pregenerate audio waveforms |
| GET | `?shares` | list your shared files/folders |
| GET | `?ups` | show recent uploads from your IP |
| GET | `?ups&filter=f` | ...where URL contains `f` |
| GET | `?mime=foo` | specify return mimetype `foo` |
| GET | `?v` | render markdown file at URL |
| GET | `?v` | open image/video/audio in mediaplayer |
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
| POST | `?move=/foo/bar` | move/rename the file/folder at URL to /foo/bar |

| method | params | body | result |
|--|--|--|--|
| PUT | | (binary data) | upload into file at URL |
| PUT | `?gz` | (binary data) | compress with gzip and write into file at URL |
| PUT | `?xz` | (binary data) | compress with xz and write into file at URL |
| mPOST | | `f=FILE` | upload `FILE` into the folder at URL |
| mPOST | `?j` | `f=FILE` | ...and reply with json |
| mPOST | `?replace` | `f=FILE` | ...and overwrite existing files |
| mPOST | `?media` | `f=FILE` | ...and return medialink (not hotlink) |
| mPOST | | `act=mkdir`, `name=foo` | create directory `foo` at URL |
| POST | `?delete` | | delete URL recursively |
| POST | `?eshare=rm` | | stop sharing a file/folder |
| POST | `?eshare=3` | | set expiration to 3 minutes |
| jPOST | `?share` | (complicated) | create temp URL for file/folder |
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


# event hooks

on writing your own [hooks](../README.md#event-hooks)

## hook effects

hooks can cause intentional side-effects,  such as redirecting an upload into another location, or creating+indexing additional files, or deleting existing files, by returning json on stdout

* `reloc` can redirect uploads before/after uploading has finished, based on filename, extension, file contents, uploader ip/name etc.
* `idx` informs copyparty about a new file to index as a consequence of this upload
* `del` tells copyparty to delete an unrelated file by vpath

for these to take effect, the hook must be defined with the `c1` flag; see example [reloc-by-ext](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reloc-by-ext.py)

a subset of effect types are available for a subset of hook types,

* most hook types (xbu/xau/xbr/xar/xbd/xad/xm) support `idx` and `del` for all http protocols (up2k / basic-uploader / webdav), but not ftp/tftp/smb
* most hook types will abort/reject the action if the hook returns nonzero, assuming flag `c` is given, see examples [reject-extension](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-extension.py) and [reject-mimetype](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/reject-mimetype.py)
* `xbu` supports `reloc` for all http protocols (up2k / basic-uploader / webdav), but not ftp/tftp/smb
* `xau` supports `reloc` for basic-uploader / webdav only, not up2k or ftp/tftp/smb
  * so clients like sharex are supported, but not dragdrop into browser

to trigger indexing of files `/foo/1.txt` and `/foo/bar/2.txt`, a hook can `print(json.dumps({"idx":{"vp":["/foo/1.txt","/foo/bar/2.txt"]}}))` (and replace "idx" with "del" to delete instead)
* note: paths starting with `/` are absolute URLs, but you can also do `../3.txt` relative to the destination folder of each uploaded file


# assumptions

## mdns

* outgoing replies will always fit in one packet
* if a client mentions any of our services, assume it's not missing any
* always answer with all services, even if the client only asked for a few
* not-impl: probe tiebreaking (too complicated)
* not-impl: unicast listen (assume avahi took it)


# sfx repack

reduce the size of an sfx by removing features

if you don't need all the features, you can repack the sfx and save a bunch of space; all you need is an sfx and a copy of this repo (nothing else to download or build, except if you're on windows then you need msys2 or WSL)
* `393k` size of original sfx.py as of v1.1.3
* `310k` after `./scripts/make-sfx.sh re no-cm`
* `269k` after `./scripts/make-sfx.sh re no-cm no-hl`

the features you can opt to drop are
* `cm`/easymde, the "fancy" markdown editor, saves ~89k
* `hl`, prism, the syntax hilighter, saves ~41k
* `fnt`, source-code-pro, the monospace font, saves ~9k
* `dd`, the custom mouse cursor for the media player tray tab, saves ~2k

for the `re`pack to work, first run one of the sfx'es once to unpack it

**note:** you can also just download and run [/scripts/copyparty-repack.sh](https://github.com/9001/copyparty/blob/hovudstraum/scripts/copyparty-repack.sh) -- this will grab the latest copyparty release from github and do a few repacks; works on linux/macos (and windows with msys2 or WSL)


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
pip install partftpy  # tftp server
pip install impacket  # smb server -- disable Windows Defender if you REALLY need this on windows
pip install Pillow pyheif-pillow-opener pillow-avif-plugin  # thumbnails
pip install pyvips  # faster thumbnails
pip install psutil  # better cleanup of stuck metadata parsers on windows 
pip install black==21.12b0 click==8.0.2 bandit pylint flake8 isort mypy  # vscode tooling
```


## just the sfx

if you just want to modify the copyparty source code (py/html/css/js) then this is the easiest approach

build the sfx using any of the following examples:

```sh
./scripts/make-sfx.sh           # regular edition
./scripts/make-sfx.sh fast      # build faster (worse js/css compression)
./scripts/make-sfx.sh gz no-cm  # gzip-compressed + no fancy markdown editor
```


## build from release tarball

uses the included prebuilt webdeps

if you downloaded a [release](https://github.com/9001/copyparty/releases) source tarball from github (for example [copyparty-1.6.15.tar.gz](https://github.com/9001/copyparty/releases/download/v1.6.15/copyparty-1.6.15.tar.gz) so not the autogenerated one) you can build it like so,

```bash
python3 -m pip install --user -U build setuptools wheel jinja2 strip_hints
bash scripts/run-tests.sh python3  # optional
python3 -m build
```

if you are unable to use `build`, you can use the old setuptools approach instead,

```bash
python3 setup.py install --user setuptools wheel jinja2
python3 setup.py build
# you now have a wheel which you can install. or extract and repackage:
python3 setup.py install --skip-build --prefix=/usr --root=$HOME/pe/copyparty
```


## complete release

also builds the sfx so skip the sfx section above

*WARNING: `rls.sh` has not yet been updated with the docker-images and arch/nix packaging*

does everything completely from scratch, straight from your local repo

in the `scripts` folder:

* run `make -C deps-docker` to build all dependencies
* run `./rls.sh 1.2.3` which uploads to pypi + creates github release + sfx


# debugging

## music playback halting on phones

mostly fine on android,  but still haven't find a way to massage iphones into behaving well

* conditionally starting/stopping mp.fau according to mp.au.readyState <3 or <4 doesn't help
* loop=true doesn't work, and manually looping mp.fau from an onended also doesn't work (it does nothing)
* assigning fau.currentTime in a timer doesn't work, as safari merely pretends to assign it
* on ios 16.7.7, mp.fau can sometimes make everything visibly work correctly, but no audio is actually hitting the speakers

can be reproduced with `--no-sendfile --s-wr-sz 8192 --s-wr-slp 0.3 --rsp-slp 6` and then play a collection of small audio files with the screen off, `ffmpeg -i track01.cdda.flac -c:a libopus -b:a 128k -segment_time 12 -f segment smol-%02d.opus`


## discarded ideas

* optimization attempts which didn't improve performance
  * remove brokers / multiprocessing stuff; https://github.com/9001/copyparty/tree/no-broker
  * reduce the nesting / indirections in `HttpCli` / `httpcli.py`
    * nearly zero benefit from stuff like replacing all the `self.conn.hsrv` with a local `hsrv` variable
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

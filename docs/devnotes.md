## devnotes toc

* top
* [future plans](#future-plans) - some improvement ideas
* [design](#design)
    * [up2k](#up2k) - quick outline of the up2k protocol
    * [why chunk-hashes](#why-chunk-hashes) - a single sha512 would be better, right?
* [http api](#http-api)
    * [read](#read)
    * [write](#write)
    * [admin](#admin)
    * [general](#general)
* [assumptions](#assumptions)
    * [mdns](#mdns)
* [sfx repack](#sfx-repack) - reduce the size of an sfx by removing features
* [building](#building)
    * [dev env setup](#dev-env-setup)
    * [just the sfx](#just-the-sfx)
    * [complete release](#complete-release)
* [todo](#todo) - roughly sorted by priority
    * [discarded ideas](#discarded-ideas)


# future plans

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

this was due to `crypto.subtle` [not yet](https://github.com/w3c/webcrypto/issues/73) providing a streaming api (or the option to seed the sha512 hasher with a starting hash)

as a result, the hashes are much less useful than they could have been (search the server by sha512, provide the sha512 in the response http headers, ...)

however it allows for hashing multiple chunks in parallel, greatly increasing upload speed from fast storage (NVMe, raid-0 and such)

* both the [browser uploader](https://github.com/9001/copyparty#uploading) and the [commandline one](https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py) does this now, allowing for fast uploading even from plaintext http

hashwasm would solve the streaming issue but reduces hashing speed for sha512 (xxh128 does 6 GiB/s), and it would make old browsers and [iphones](https://bugs.webkit.org/show_bug.cgi?id=228552) unsupported

* blake2 might be a better choice since xxh is non-cryptographic, but that gets ~15 MiB/s on slower androids


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
| GET | `?b` | list files/folders at URL as simplified HTML |
| GET | `?tree=.` | list one level of subdirectories inside URL |
| GET | `?tree` | list one level of subdirectories for each level until URL |
| GET | `?tar` | download everything below URL as a tar file |
| GET | `?zip=utf-8` | download everything below URL as a zip file |
| GET | `?ups` | show recent uploads from your IP |
| GET | `?ups&filter=f` | ...where URL contains `f` |
| GET | `?mime=foo` | specify return mimetype `foo` |
| GET | `?v` | render markdown file at URL |
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
| mPOST | | `act=bput`, `f=FILE` | upload `FILE` into the folder at URL |
| mPOST | `?j` | `act=bput`, `f=FILE` | ...and reply with json |
| mPOST | | `act=mkdir`, `name=foo` | create directory `foo` at URL |
| POST | `?delete` | | delete URL recursively |
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
* `cm`/easymde, the "fancy" markdown editor, saves ~82k
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
pip install impacket  # smb server -- disable Windows Defender if you REALLY need this on windows
pip install Pillow pyheif-pillow-opener pillow-avif-plugin  # thumbnails
pip install black==21.12b0 click==8.0.2 bandit pylint flake8 isort mypy  # vscode tooling
```


## just the sfx

first grab the web-dependencies from a previous sfx (assuming you don't need to modify something in those):

```sh
rm -rf copyparty/web/deps
curl -L https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py >x.py
python3 x.py --version
rm x.py
cp -R /tmp/pe-copyparty.$(id -u)/copyparty/web/deps copyparty/web/
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

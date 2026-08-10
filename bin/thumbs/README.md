# thumbnail extractors

extract (or generate) thumbnails for custom file formats or override default thumbnail extraction for standard media files


## usage

load plugins with `--th-extract pkg=~/dev/copyparty/bin/thumbs/ps4fpkg.py`
here `pkg` is the file extension (may be comma-separated list of extensions)
the `--th-extract` argument is repeatable

## api

### in

each plugin must define a function `main(abspath, **kwargs)`:
- `abspath` is the path to a file to extract thumbnail for
- `kwargs` currently receives these keyword arguments:
  - `vn` is the VFS which contains the requested file
  - `th_srv` is an instance of [copyparty/th_srv](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/th_srv.py)

### out

the `main()` function must
- return `None` or raise an `Exception` in case it is unable to extract thumbnail
- return tuple `fmt, stream, offset, whence, size` otherwise:
  - `fmt: str` – format (filename extension) of the thumbnail; should be one of the image formats supported by copyparty (see `--th-r-*` options)
  - `stream: IO[bytes]` – binary file-like object supporting `seek()`, `read()`, `close()` methods; should contain extracted thumbnail image
  - `offset: int, whence: int` – arguments to `stream.seek()`; copyparty will call `stream.seek(offset, whence)` once before starting reading the stream contents
  - `size: int | None` – number of bytes to read from the `stream`; if `size` is negative or `None`, copyparty will read until the end of the stream


### notes

it is possible to extract or generate custom thumbnails for standard media files too
e.g. run copyparty with `--th-extract mp3,m4a,aac,flac,opus=~/dev/copyparty/bin/thumbs/my_custom_mp3_th_extractor.py` and do your magic with audio file thumbnails

in case copyparty doesn't like the `fmt` option it will `close()` the `stream` without ever calling `seek()` or `read()`
if your scenario involves heavy computation or i/o, it is better to defer the heavy parts until the first `seek()` or `read()` to avoid redundant work in case the result gets rejected based on `fmt` value

if you provide custom `stream` object:
copyparty performs buffered reading, so expect multiple `read()` calls, respect `size` argument in `read(size)` calls, and maintain correct seek position


## examples

- [ps4fpkg.py](ps4fpkg.py) extracts cover images from playstation4 [fake package](https://www.psdevwiki.com/ps4/PKG_files) files; `pkg` is typical extension for these files; examples of how it looks can be found in these PRs: #1502 #1602

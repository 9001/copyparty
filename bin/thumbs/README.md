# thumbnail extractors

extract (or generate) thumbnails for custom file formats or override default thumbnail extraction for standard media files


## usage

* load plugins with `--th-extract baz=~/dev/copyparty/bin/thumbs/randomcolor.py`
  * `baz` is the file extension (may be comma-separated list of extensions)
  * add multiple different extractor plugins by repeating the `--th-extract` argument


## api

### in

each plugin must define a function `main(abspath, **kwargs)`:
* `abspath` is the path to a file to extract thumbnail for
* `kwargs` currently receives these keyword arguments:
  * `vn` is the VFS which contains the requested file
  * `th_srv` is an instance of [copyparty/th_srv](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/th_srv.py)

### out

the `main()` function must
* return `None` or raise an `Exception` in case it is unable to extract thumbnail
* return tuple `fmt, stream, offset, whence, size` otherwise:
  * `fmt: str` – format (filename extension) of the thumbnail; should be one of the image formats supported by copyparty (see `--th-r-*` options)
  * `stream: IO[bytes]` – binary file-like object supporting `seek()`, `read()`, `close()` methods; should contain extracted thumbnail image
  * `offset: int, whence: int` – arguments to `stream.seek()`; copyparty will call `stream.seek(offset, whence)` once before starting reading the stream contents
  * `size: int | None` – number of bytes to read from the `stream`; if `size` is negative or `None`, copyparty will read until the end of the stream


### notes

it is possible to extract or generate custom thumbnails for standard media files too,
e.g. run copyparty with `--th-extract mp3,m4a,aac,flac,opus=~/dev/copyparty/bin/thumbs/my_custom_mp3_th_extractor.py` and do your magic with audio file thumbnails

in case copyparty doesn't like the `fmt` option, it will `close()` the `stream` without ever calling `seek()` or `read()`

if your scenario involves heavy computation or i/o, it is better to defer the heavy parts until the first `seek()` or `read()` to avoid redundant work in case the result gets rejected based on `fmt` value

if you provide custom `stream` object:
copyparty performs buffered reading, so expect multiple `read()` calls, respect `size` argument in `read(size)` calls, and maintain correct seek position


## examples

* [randomcolor](https://github.com/9001/copyparty/blob/hovudstraum/bin/thumbs/randomcolor.py) generates a random .gif image
* [collabora](https://github.com/9001/copyparty/blob/hovudstraum/bin/thumbs/collabora.py) uses external self-hosted service (collabora online) to generate previews for various office documents, pdf and fb2 books, html, markdown, text files and some image formats; collabora is also supported as office editor in copyparty, see [wopi](https://github.com/9001/copyparty#wopi-server)


## some other known plugins seen on the internets

* [fpkg_thumb](https://github.com/kamaeff/copyparty-dumb-fpkgi-handler/blob/master/fpkg_thumb.py) extracts cover images from playstation4 software installation packages ("pkg" and "fpkg" files)

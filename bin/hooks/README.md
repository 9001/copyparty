standalone programs which are executed by copyparty when an event happens (upload, file rename, delete, ...)

these programs either take zero arguments, or a filepath (the affected file), or a json message with filepath + additional info

run copyparty with `--help-hooks` for usage details / hook type explanations (xm/xbu/xau/xiu/xbc/xac/xbr/xar/xbd/xad/xban)

in particular, if a hook is loaded into copyparty with the hook-flag `c` ("check") then its exit-code controls the action that launched the hook:
* exit-code `0` = allow the action, and/or continue running the next hook
* exit-code `100` = allow the action, and stop running any remaining consecutive hooks
* anything else = reject/prevent the original action, and don't run the remaining hooks

> **note:** in addition to event hooks (the stuff described here), copyparty has another api to run your programs/scripts while providing way more information such as audio tags / video codecs / etc and optionally daisychaining data between scripts in a processing pipeline; if that's what you want then see [mtp plugins](../mtag/) instead


# after upload
* [notify.py](notify.py) shows a desktop notification ([example](https://user-images.githubusercontent.com/241032/215335767-9c91ed24-d36e-4b6b-9766-fb95d12d163f.png))
  * [notify2.py](notify2.py) uses the json API to show more context
* [image-noexif.py](image-noexif.py) removes image exif by overwriting / directly editing the uploaded file
* [discord-announce.py](discord-announce.py) announces new uploads on discord using webhooks ([example](https://user-images.githubusercontent.com/241032/215304439-1c1cb3c8-ec6f-4c17-9f27-81f969b1811a.png))
* [reject-mimetype.py](reject-mimetype.py) rejects uploads unless the mimetype is acceptable
* [into-the-cache-it-goes.py](into-the-cache-it-goes.py) avoids bugs in caching proxies by immediately downloading each file that is uploaded
* [podcast-normalizer.py](podcast-normalizer.py) creates a second file with dynamic-range-compression whenever an audio file is uploaded
  * good example of the `idx` [hook effect](https://github.com/9001/copyparty/blob/hovudstraum/docs/devnotes.md#hook-effects) to tell copyparty about additional files to scan/index


# upload batches
these are `--xiu` hooks; unlike `xbu` and `xau` (which get executed on every single file), `xiu` hooks are given a list of recent uploads on STDIN after the server has gone idle for N seconds, reducing server load + providing more context
* [xiu.py](xiu.py) is a "minimal" example showing a list of filenames + total filesize
* [xiu-sha.py](xiu-sha.py) produces a sha512 checksum list in the volume root


# before upload
* [reject-extension.py](reject-extension.py) rejects uploads if they match a list of file extensions
* [reloc-by-ext.py](reloc-by-ext.py) redirects an upload to another destination based on the file extension
  * good example of the `reloc` [hook effect](https://github.com/9001/copyparty/blob/hovudstraum/docs/devnotes.md#hook-effects)
* [reject-and-explain.py](reject-and-explain.py) shows a custom error-message when it rejects an upload
* [reject-ramdisk.py](reject-ramdisk.py) rejects the upload if the destination is a ramdisk
  * this hook uses the `I` flag which makes it 140x faster, but if the plugin has a bug it may crash copyparty


# on message
* [wget.py](wget.py) lets you download files by POSTing URLs to copyparty
  * [wget-i.py](wget-i.py) is an import-safe modification of this hook (starts 140x faster, but higher chance of bugs)
* [qbittorrent-magnet.py](qbittorrent-magnet.py) starts downloading a torrent if you post a magnet url
* [usb-eject.py](usb-eject.py) adds web-UI buttons to safe-remove usb flashdrives shared through copyparty
* [msg-log.py](msg-log.py) is a guestbook; logs messages to a doc in the same folder


# general concept demos
* [import-me.py](import-me.py) shows how the `I` flag makes the hook 140x faster (but you need to be Very Careful when writing the plugin)
  * [wget-i.py](wget-i.py) is an import-safe modification of [wget.py](wget.py)

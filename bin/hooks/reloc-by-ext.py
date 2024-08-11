#!/usr/bin/env python3

import json
import os
import sys


_ = r"""
relocate/redirect incoming uploads according to file extension

example usage as global config:
    --xbu j,c1,bin/hooks/reloc-by-ext.py

parameters explained,
    xbu = execute before upload
    j   = this hook needs upload information as json (not just the filename)
    c1  = this hook returns json on stdout, so tell copyparty to read that

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xbu=j,c1,bin/hooks/reloc-by-ext.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all uploads with the params explained above)

example usage as a volflag in a copyparty config file:
    [/inc]
      srv/inc
      accs:
        r: *
        rw: ed
      flags:
        xbu: j,c1,bin/hooks/reloc-by-ext.py

note: this only works with the basic uploader (sharex and such),
  does not work with up2k / dragdrop into browser

note: this could also work as an xau hook (after-upload), but
  because it doesn't need to read the file contents its better
  as xbu (before-upload) since that's safer / less buggy
"""


PICS = "avif bmp gif heic heif jpeg jpg jxl png psd qoi tga tif tiff webp"
VIDS = "3gp asf avi flv mkv mov mp4 mpeg mpeg2 mpegts mpg mpg2 nut ogm ogv rm ts vob webm wmv"
MUSIC = "aac aif aiff alac amr ape dfpwm flac m4a mp3 ogg opus ra tak tta wav wma wv"


def main():
    inf = json.loads(sys.argv[1])
    vdir, fn = os.path.split(inf["vp"])

    try:
        fn, ext = fn.rsplit(".", 1)
    except:
        # no file extension; abort
        return

    ext = ext.lower()

    ##
    ## some example actions to take; pick one by
    ## selecting it inside the print at the end:
    ##

    # create a subfolder named after the filetype and move it into there
    into_subfolder = {"vp": ext}

    # move it into a toplevel folder named after the filetype
    into_toplevel = {"vp": "/" + ext}

    # move it into a filetype-named folder next to the target folder
    into_sibling = {"vp": "../" + ext}

    # move images into "/just/pics", vids into "/just/vids",
    # music into "/just/tunes", and anything else as-is
    if ext in PICS.split():
        by_category = {"vp": "/just/pics"}
    elif ext in VIDS.split():
        by_category = {"vp": "/just/vids"}
    elif ext in MUSIC.split():
        by_category = {"vp": "/just/tunes"}
    else:
        by_category = {}

    # now choose the effect to apply; can be any of these:
    # into_subfolder  into_toplevel  into_sibling  by_category
    effect = into_subfolder
    print(json.dumps({"reloc": effect}))


if __name__ == "__main__":
    main()

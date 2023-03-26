#!/usr/bin/env python3

import os
import sys
import subprocess as sp


_ = r"""
remove exif tags from uploaded images; the eventhook edition of
https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/image-noexif.py

dependencies:
    exiftool / perl-Image-ExifTool

being an upload hook, this will take effect after upload completion
    but before copyparty has hashed/indexed the file, which means that
    copyparty will never index the original file, so deduplication will
    not work as expected... which is mostly OK but ehhh

note: modifies the file in-place, so don't set the `f` (fork) flag

example usages; either as global config (all volumes) or as volflag:
    --xau bin/hooks/image-noexif.py
    -v srv/inc:inc:r:rw,ed:c,xau=bin/hooks/image-noexif.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

explained:
    share fs-path srv/inc at /inc (readable by all, read-write for user ed)
    running this xau (execute-after-upload) plugin for all uploaded files
"""


# filetypes to process; ignores everything else
EXTS = ("jpg", "jpeg", "avif", "heif", "heic")


try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p.encode("utf-8")


def main():
    fp = sys.argv[1]
    ext = fp.lower().split(".")[-1]
    if ext not in EXTS:
        return

    cwd, fn = os.path.split(fp)
    os.chdir(cwd)
    f1 = fsenc(fn)
    cmd = [
        b"exiftool",
        b"-exif:all=",
        b"-iptc:all=",
        b"-xmp:all=",
        b"-P",
        b"-overwrite_original",
        b"--",
        f1,
    ]
    sp.check_output(cmd)
    print("image-noexif: stripped")


if __name__ == "__main__":
    try:
        main()
    except:
        pass

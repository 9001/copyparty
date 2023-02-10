#!/usr/bin/env python3

"""
remove exif tags from uploaded images

dependencies:
  exiftool

about:
  creates a "noexif" subfolder and puts exif-stripped copies of each image there,
  the reason for the subfolder is to avoid issues with the up2k.db / deduplication:

  if the original image is modified in-place, then copyparty will keep the original
  hash in up2k.db for a while (until the next volume rescan), so if the image is
  reuploaded after a rescan then the upload will be renamed and kept as a dupe

  alternatively you could switch the logic around, making a copy of the original
  image into a subfolder named "exif" and modify the original in-place, but then
  up2k.db will be out of sync until the next rescan, so any additional uploads
  of the same image will get symlinked (deduplicated) to the modified copy
  instead of the original in "exif"

  or maybe delete the original image after processing, that would kinda work too

example copyparty config to use this:
  -v/mnt/nas/pics:pics:rwmd,ed:c,e2ts,mte=+noexif:c,mtp=noexif=ejpg,ejpeg,ad,bin/mtag/image-noexif.py

explained:
  for realpath /mnt/nas/pics (served at /pics) with read-write-modify-delete for ed,
  enable file analysis on upload (e2ts),
  append "noexif" to the list of known tags (mtp),
  and use mtp plugin "bin/mtag/image-noexif.py" to provide that tag,
  do this on all uploads with the file extension "jpg" or "jpeg",
  ad = parse file regardless if FFmpeg thinks it is audio or not

PS: this requires e2ts to be functional,
  meaning you need to do at least one of these:
   * apt install ffmpeg
   * pip3 install mutagen
  and your python must have sqlite3 support compiled in
"""


import os
import sys
import filecmp
import subprocess as sp

try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p.encode("utf-8")


def main():
    cwd, fn = os.path.split(sys.argv[1])
    if os.path.basename(cwd) == "noexif":
        return

    os.chdir(cwd)
    f1 = fsenc(fn)
    f2 = fsenc(os.path.join(b"noexif", fn))
    cmd = [
        b"exiftool",
        b"-exif:all=",
        b"-iptc:all=",
        b"-xmp:all=",
        b"-P",
        b"-o",
        b"noexif/",
        b"--",
        f1,
    ]
    sp.check_output(cmd)
    if not os.path.exists(f2):
        print("failed")
        return

    if filecmp.cmp(f1, f2, shallow=False):
        print("clean")
    else:
        print("exif")

    # lastmod = os.path.getmtime(f1)
    # times = (int(time.time()), int(lastmod))
    # os.utime(f2, times)


if __name__ == "__main__":
    try:
        main()
    except:
        pass

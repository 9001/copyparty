#!/usr/bin/env python3

import os


_ = r"""
rename incoming uploads according to the "wark" (the file identifier)
which is basically but not exactly a sha512 hash of the file contents

NOTE: this only works for up2k uploads (dragdrop into browser);
  combine this with reloc-by-wark-xau.py to cover the other protocols

example usage as global config:
    -e2d --xbu I,c,bin/hooks/reloc-by-wark-xbu.py

parameters explained,
    e2d = enable up2k database (mandatory for xbu hooks)
    xbu = execute before upload
    I   = import this hook for performance; do not fork / subprocess
    c   = "check"; reject upload if this hook crashes due to a bug

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,e2d,xbu=I,c,bin/hooks/reloc-by-wark-xbu.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
        e2d, xbu: I,c,bin/hooks/reloc-by-wark-xbu.py
"""


def main(inf):
    wark = inf.get("wark")
    if not wark:
        # not an up2k upload, so we don't have the hash;

        # option 1: let upload proceed with original filename
        return {}

        # option 2: reject the upload
        return {"rejectmsg": "only up2k uploads are allowed in this volume"}

    # grab the original filename from the vpath...
    vdir, fn = os.path.split(inf["vp"])

    # ...to retain the original file extension, if any
    try:
        fn, ext = fn.rsplit(".", 1)
    except:
        ext = ""

    # use the first 16 characters; 12 bytes of entropy,
    # roughly one collision for every 26 million files
    fn = wark[:16]

    if ext:
        ext = ext.lower()
        fn += "." + ext

    return {"reloc": {"fn": fn}}

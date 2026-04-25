#!/usr/bin/env python3

import os
import sys


_ = r"""
rename incoming uploads according to the "wark" (the file identifier)
which is basically but not exactly a sha512 hash of the file contents

NOTE: this does NOT work with up2k uploads (dragdrop into browser);
  combine this hook with reloc-by-wark-xbu.py to fix that

example usage as global config:
    -e2d --xau I,c,bin/hooks/reloc-by-wark-xau.py

parameters explained,
    e2d = enable up2k database (mandatory for xau hooks)
    xau = execute before upload
    I   = import this hook for performance; do not fork / subprocess
    c   = "check"; reject upload if this hook crashes due to a bug

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,e2d,xau=I,c,bin/hooks/reloc-by-wark-xau.py
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
        e2d, xau: I,c,bin/hooks/reloc-by-wark-xau.py
"""


def main(inf):
    if inf.get("wark"):
        # this is an up2k upload; nothing to be done, just bail
        return {}

    abspath = inf["ap"]  # filesystem path to the uploaded file

    # we don't have the wark yet so need to calculate it;
    # generating a regular sha512 would of course be much easier,
    # but then filenames would be different depending on how the
    # file was uploaded (laaame) so let's do it the hard way

    # use the standard up2k-salt which nobody ever changes:
    salt = "hunter2"

    # to generate the wark we'll need some functions from copyparty;
    # follow the trail to the copyparty module and grab them from there:

    import inspect

    libpath = inspect.getfile(inf["log"])
    libpath = os.path.dirname(os.path.dirname(libpath))
    sys.path.insert(0, libpath)

    from copyparty.up2k import up2k_hashlist_from_file, up2k_wark_from_hashlist

    chunklist, st = up2k_hashlist_from_file(abspath)
    wark = up2k_wark_from_hashlist(salt, st.st_size, chunklist)

    # okay nice
    # the rest of the code below is just copied from reloc-by-wark-xbu.py
    # -------------------------------------------------------------------------

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

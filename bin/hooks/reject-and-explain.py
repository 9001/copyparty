#!/usr/bin/env python3

import json
import os
import re
import sys


_ = r"""
reject file upload (with a nice explanation why)

example usage as global config:
    --xbu j,c1,bin/hooks/reject-and-explain.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xbu=j,c1,bin/hooks/reject-and-explain.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all uploads with the params listed below)

example usage as a volflag in a copyparty config file:
    [/inc]
      srv/inc
      accs:
        r: *
        rw: ed
      flags:
        xbu: j,c1,bin/hooks/reject-and-explain.py

parameters explained,
    xbu = execute-before-upload  (can also be xau, execute-after-upload)
    j   = this hook needs upload information as json (not just the filename)
    c1  = this hook returns json on stdout, so tell copyparty to read that
"""


def main():
    inf = json.loads(sys.argv[1])
    vdir, fn = os.path.split(inf["vp"])
    print("inf[vp] = %r" % (inf["vp"],), file=sys.stderr)

    # the following is what decides if we'll accept the upload or reject it:
    # we check if the upload-folder url matches the following regex-pattern:
    ok = re.search(r"(^|/)day[0-9]+$", vdir, re.IGNORECASE)

    if ok:
        # allow the upload
        print("{}")
        return

    # the upload was rejected; display the following errortext:
    errmsg = "Files can only be uploaded into a folder named 'DayN' where N is a number, for example 'Day573'. This file was REJECTED: "
    errmsg += inf["vp"]  # if you want to mention the file's url
    print(json.dumps({"rejectmsg": errmsg}))


if __name__ == "__main__":
    main()

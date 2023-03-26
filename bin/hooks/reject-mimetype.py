#!/usr/bin/env python3

import sys
import magic


_ = r"""
reject file uploads by mimetype

dependencies (linux, macos):
    python3 -m pip install --user -U python-magic

dependencies (windows):
    python3 -m pip install --user -U python-magic-bin

example usage as global config:
    --xau c,bin/hooks/reject-mimetype.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xau=c,bin/hooks/reject-mimetype.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all uploads with the params listed below)

parameters explained,
    xau = execute after upload
    c   = check result, reject upload if error
"""


def main():
    ok = ["image/jpeg", "image/png"]

    mt = magic.from_file(sys.argv[1], mime=True)

    print(mt)

    sys.exit(1 if mt not in ok else 0)


if __name__ == "__main__":
    main()

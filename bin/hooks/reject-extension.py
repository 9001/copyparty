#!/usr/bin/env python3

import sys


_ = r"""
reject file uploads by file extension

example usage as global config:
    --xbu c,bin/hooks/reject-extension.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xbu=c,bin/hooks/reject-extension.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all uploads with the params listed below)

parameters explained,
    xbu = execute before upload
    c   = check result, reject upload if error
"""


def main():
    bad = "exe scr com pif bat ps1 jar msi"

    ext = sys.argv[1].split(".")[-1]

    sys.exit(1 if ext in bad.split() else 0)


if __name__ == "__main__":
    main()

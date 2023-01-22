#!/usr/bin/env python3

import sys
from plyer import notification


_ = r"""
show os notification on upload; works on windows, linux, macos

depdencies:
    python3 -m pip install --user -U plyer

example usage as global config:
    --xau f,bin/hooks/notify.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:c,xau=f,bin/hooks/notify.py

parameters explained,
    xau = execute after upload
    f   = fork so it doesn't block uploads
"""


def main():
    notification.notify(title="new file uploaded", message=sys.argv[1], timeout=10)


if __name__ == "__main__":
    main()

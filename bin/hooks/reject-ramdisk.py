#!/usr/bin/env python3

import os
import threading
from argparse import Namespace

from jinja2.nodes import Name
from copyparty.fsutil import Fstab
from typing import Any, Optional


_ = r"""
reject an upload if the target folder is on a ramdisk; useful when you
have a volume where some folders inside are ramdisks but others aren't

example usage as global config:
    --xbu I,bin/hooks/reject-ramdisk.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xbu=I,bin/hooks/reject-ramdisk.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
        xbu: I,bin/hooks/reject-ramdisk.py

parameters explained,
    I = import; do not fork / subprocess

IMPORTANT NOTE:
    because this hook is imported inside copyparty, you need to
    be EXCEPTIONALLY CAREFUL to avoid side-effects, for example
    DO NOT os.chdir() or anything like that, and also make sure
    that the name of this file is unique (cannot be the same as
    an existing python module/library)
"""


mutex = threading.Lock()
fstab: Optional[Fstab] = None


def main(ka: dict[str, Any]) -> dict[str, Any]:
    global fstab
    with mutex:
        log = ka["log"]  # this is a copyparty NamedLogger function
        if not fstab:
            log("<HOOK:RAMDISK> creating fstab", 6)
            args = Namespace()
            args.mtab_age = 1  # cache the filesystem info for 1 sec
            fstab = Fstab(log, args, False)

        ap = ka["ap"]  # abspath the upload is going to
        fs, mp = fstab.get(ap)  # figure out what the filesystem is
        ramdisk = fs in ("tmpfs", "overlay")  # looks like a ramdisk?

        # log("<HOOK:RAMDISK> fs=%r" % (fs,))

        if ramdisk:
            t = "Upload REJECTED because destination is a ramdisk"
            return {"rc": 1, "rejectmsg": t}

        return {"rc": 0}

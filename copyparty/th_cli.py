# coding: utf-8
from __future__ import print_function, unicode_literals

import os

from .util import Cooldown
from .th_srv import thumb_path, THUMBABLE, FMT_FF
from .bos import bos


class ThumbCli(object):
    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args
        self.asrv = broker.asrv

        # cache on both sides for less broker spam
        self.cooldown = Cooldown(self.args.th_poke)

    def get(self, ptop, rem, mtime, fmt):
        ext = rem.rsplit(".")[-1].lower()
        if ext not in THUMBABLE:
            return None

        is_vid = ext in FMT_FF
        if is_vid and self.args.no_vthumb:
            return None

        if rem.startswith(".hist/th/") and rem.split(".")[-1] in ["webp", "jpg"]:
            return os.path.join(ptop, rem)

        if fmt == "j" and self.args.th_no_jpg:
            fmt = "w"

        if fmt == "w":
            if self.args.th_no_webp or (is_vid and self.args.th_ff_jpg):
                fmt = "j"

        histpath = self.asrv.vfs.histtab[ptop]
        tpath = thumb_path(histpath, rem, mtime, fmt)
        ret = None
        try:
            st = bos.stat(tpath)
            if st.st_size:
                ret = tpath
            else:
                return None
        except:
            pass

        if ret:
            tdir = os.path.dirname(tpath)
            if self.cooldown.poke(tdir):
                self.broker.put(False, "thumbsrv.poke", tdir)

            return ret

        x = self.broker.put(True, "thumbsrv.get", ptop, rem, mtime, fmt)
        return x.get()

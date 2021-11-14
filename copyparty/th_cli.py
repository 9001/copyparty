# coding: utf-8
from __future__ import print_function, unicode_literals

import os

from .util import Cooldown
from .th_srv import thumb_path, THUMBABLE, FMT_FFV, FMT_FFA
from .bos import bos


class ThumbCli(object):
    def __init__(self, hsrv):
        self.broker = hsrv.broker
        self.log_func = hsrv.log
        self.args = hsrv.args
        self.asrv = hsrv.asrv

        # cache on both sides for less broker spam
        self.cooldown = Cooldown(self.args.th_poke)

    def log(self, msg, c=0):
        self.log_func("thumbcli", msg, c)

    def get(self, ptop, rem, mtime, fmt):
        ext = rem.rsplit(".")[-1].lower()
        if ext not in THUMBABLE:
            return None

        is_vid = ext in FMT_FFV
        if is_vid and self.args.no_vthumb:
            return None

        want_opus = fmt in ("opus", "caf")
        is_au = ext in FMT_FFA
        if is_au:
            if want_opus:
                if self.args.no_acode:
                    return None
            else:
                if self.args.no_athumb:
                    return None
        elif want_opus:
            return None

        if rem.startswith(".hist/th/") and rem.split(".")[-1] in ["webp", "jpg"]:
            return os.path.join(ptop, rem)

        if fmt == "j" and self.args.th_no_jpg:
            fmt = "w"

        if fmt == "w":
            if self.args.th_no_webp or ((is_vid or is_au) and self.args.th_ff_jpg):
                fmt = "j"

        histpath = self.asrv.vfs.histtab.get(ptop)
        if not histpath:
            self.log("no histpath for [{}]".format(ptop))
            return None

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

            if want_opus:
                # audio files expire individually
                if self.cooldown.poke(tpath):
                    self.broker.put(False, "thumbsrv.poke", tpath)

            return ret

        x = self.broker.put(True, "thumbsrv.get", ptop, rem, mtime, fmt)
        return x.get()

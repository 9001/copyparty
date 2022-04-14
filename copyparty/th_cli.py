# coding: utf-8
from __future__ import print_function, unicode_literals

import os

from .util import Cooldown
from .th_srv import thumb_path, HAVE_WEBP
from .bos import bos


class ThumbCli(object):
    def __init__(self, hsrv):
        self.broker = hsrv.broker
        self.log_func = hsrv.log
        self.args = hsrv.args
        self.asrv = hsrv.asrv

        # cache on both sides for less broker spam
        self.cooldown = Cooldown(self.args.th_poke)

        try:
            c = hsrv.th_cfg
        except:
            c = {k: {} for k in ["thumbable", "pil", "vips", "ffi", "ffv", "ffa"]}

        self.thumbable = c["thumbable"]
        self.fmt_pil = c["pil"]
        self.fmt_vips = c["vips"]
        self.fmt_ffi = c["ffi"]
        self.fmt_ffv = c["ffv"]
        self.fmt_ffa = c["ffa"]

        # defer args.th_ff_jpg, can change at runtime
        d = next((x for x in self.args.th_dec if x in ("vips", "pil")), None)
        self.can_webp = HAVE_WEBP or d == "vips"

    def log(self, msg, c=0):
        self.log_func("thumbcli", msg, c)

    def get(self, dbv, rem, mtime, fmt):
        ptop = dbv.realpath
        ext = rem.rsplit(".")[-1].lower()
        if ext not in self.thumbable or "dthumb" in dbv.flags:
            return None

        is_vid = ext in self.fmt_ffv
        if is_vid and "dvthumb" in dbv.flags:
            return None

        want_opus = fmt in ("opus", "caf")
        is_au = ext in self.fmt_ffa
        if is_au:
            if want_opus:
                if self.args.no_acode:
                    return None
            else:
                if "dathumb" in dbv.flags:
                    return None
        elif want_opus:
            return None

        is_img = not is_vid and not is_au
        if is_img and "dithumb" in dbv.flags:
            return None

        preferred = self.args.th_dec[0] if self.args.th_dec else ""

        if rem.startswith(".hist/th/") and rem.split(".")[-1] in ["webp", "jpg"]:
            return os.path.join(ptop, rem)

        if fmt == "j" and self.args.th_no_jpg:
            fmt = "w"

        if fmt == "w":
            if (
                self.args.th_no_webp
                or (is_img and not self.can_webp)
                or (self.args.th_ff_jpg and (not is_img or preferred == "ff"))
            ):
                fmt = "j"

        histpath = self.asrv.vfs.histtab.get(ptop)
        if not histpath:
            self.log("no histpath for [{}]".format(ptop))
            return None

        tpath = thumb_path(histpath, rem, mtime, fmt)
        tpaths = [tpath]
        if fmt == "w":
            # also check for jpg (maybe webp is unavailable)
            tpaths.append(tpath.rsplit(".", 1)[0] + ".jpg")

        ret = None
        abort = False
        for tp in tpaths:
            try:
                st = bos.stat(tp)
                if st.st_size:
                    ret = tpath = tp
                    fmt = ret.rsplit(".")[1]
                else:
                    abort = True
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

        if abort:
            return None

        x = self.broker.put(True, "thumbsrv.get", ptop, rem, mtime, fmt)
        return x.get()

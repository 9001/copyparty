import os
import time

from .util import Cooldown
from .th_srv import thumb_path, THUMBABLE, FMT_FF


class ThumbCli(object):
    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args

        # cache on both sides for less broker spam
        self.cooldown = Cooldown(self.args.th_poke)

    def get(self, ptop, rem, mtime):
        ext = rem.rsplit(".")[-1].lower()
        if ext not in THUMBABLE:
            return None

        if self.args.no_vthumb and ext in FMT_FF:
            return None

        tpath = thumb_path(ptop, rem, mtime)
        ret = None
        try:
            st = os.stat(tpath)
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

        x = self.broker.put(True, "thumbsrv.get", ptop, rem, mtime)
        return x.get()

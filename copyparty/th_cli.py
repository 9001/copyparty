import os

from .th_srv import thumb_path, THUMBABLE, FMT_FF


class ThumbCli(object):
    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args

    def get(self, ptop, rem, mtime):
        ext = rem.rsplit(".")[-1].lower()
        if ext not in THUMBABLE:
            return None

        if self.args.no_vthumb and ext in FMT_FF:
            return None

        tpath = thumb_path(ptop, rem, mtime)
        try:
            st = os.stat(tpath)
            if st.st_size:
                return tpath
            return None
        except:
            pass

        x = self.broker.put(True, "thumbsrv.get", ptop, rem, mtime)
        return x.get()

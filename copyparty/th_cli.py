import os

from .th_srv import thumb_path, THUMBABLE


class ThumbCli(object):
    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args

    def get(self, ptop, rem, mtime):
        ext = rem.rsplit(".")[-1].lower()
        if ext not in THUMBABLE:
            return None

        tpath = thumb_path(ptop, rem, mtime)
        if os.path.exists(tpath):
            return tpath

        x = self.broker.put(True, "thumbsrv.get", ptop, rem, mtime)
        return x.get()

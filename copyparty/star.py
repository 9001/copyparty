# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import tarfile
import threading

from .sutil import errdesc
from .util import Queue, fsenc


class QFile(object):
    """file-like object which buffers writes into a queue"""

    def __init__(self):
        self.q = Queue(64)
        self.bq = []
        self.nq = 0

    def write(self, buf):
        if buf is None or self.nq >= 240 * 1024:
            self.q.put(b"".join(self.bq))
            self.bq = []
            self.nq = 0

        if buf is None:
            self.q.put(None)
        else:
            self.bq.append(buf)
            self.nq += len(buf)


class StreamTar(object):
    """construct in-memory tar file from the given path"""

    def __init__(self, fgen, **kwargs):
        self.ci = 0
        self.co = 0
        self.qfile = QFile()
        self.fgen = fgen
        self.errf = None

        # python 3.8 changed to PAX_FORMAT as default,
        # waste of space and don't care about the new features
        fmt = tarfile.GNU_FORMAT
        self.tar = tarfile.open(fileobj=self.qfile, mode="w|", format=fmt)

        w = threading.Thread(target=self._gen, name="star-gen")
        w.daemon = True
        w.start()

    def gen(self):
        while True:
            buf = self.qfile.q.get()
            if not buf:
                break

            self.co += len(buf)
            yield buf

        yield None
        if self.errf:
            os.unlink(self.errf["ap"])

    def ser(self, f):
        name = f["vp"]
        src = f["ap"]
        fsi = f["st"]

        inf = tarfile.TarInfo(name=name)
        inf.mode = fsi.st_mode
        inf.size = fsi.st_size
        inf.mtime = fsi.st_mtime
        inf.uid = 0
        inf.gid = 0

        self.ci += inf.size
        with open(fsenc(src), "rb", 512 * 1024) as f:
            self.tar.addfile(inf, f)

    def _gen(self):
        errors = []
        for f in self.fgen:
            if "err" in f:
                errors.append([f["vp"], f["err"]])
                continue

            try:
                self.ser(f)
            except Exception as ex:
                errors.append([f["vp"], repr(ex)])

        if errors:
            self.errf = errdesc(errors)
            self.ser(self.errf)

        self.tar.close()
        self.qfile.write(None)

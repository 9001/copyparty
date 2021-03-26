import tarfile
import threading

from .util import Queue, fsenc


class QFile(object):
    """file-like object which buffers writes into a queue"""

    def __init__(self):
        self.q = Queue(64)

    def write(self, buf):
        self.q.put(buf)


class StreamTar(object):
    """construct in-memory tar file from the given path"""

    def __init__(self, top, fgen):
        self.ci = 0
        self.co = 0
        self.qfile = QFile()
        self.srcfiles = fgen

        # python 3.8 changed to PAX_FORMAT as default,
        # waste of space and don't care about the new features
        fmt = tarfile.GNU_FORMAT
        self.tar = tarfile.open(fileobj=self.qfile, mode="w|", format=fmt)

        w = threading.Thread(target=self._gen)
        w.daemon = True
        w.start()

    def gen(self):
        while True:
            buf = self.qfile.q.get()
            if buf is None:
                break

            self.co += len(buf)
            yield buf

        yield None

    def _gen(self):
        for f in self.fgen:
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

        self.tar.close()
        self.qfile.q.put(None)

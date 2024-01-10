# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import stat
import tarfile

from queue import Queue

from .bos import bos
from .sutil import StreamArc, errdesc
from .util import Daemon, fsenc, min_ex

if True:  # pylint: disable=using-constant-test
    from typing import Any, Generator, Optional

    from .util import NamedLogger


class QFile(object):  # inherit io.StringIO for painful typing
    """file-like object which buffers writes into a queue"""

    def __init__(self) -> None:
        self.q: Queue[Optional[bytes]] = Queue(64)
        self.bq: list[bytes] = []
        self.nq = 0

    def write(self, buf: Optional[bytes]) -> None:
        if buf is None or self.nq >= 240 * 1024:
            self.q.put(b"".join(self.bq))
            self.bq = []
            self.nq = 0

        if buf is None:
            self.q.put(None)
        else:
            self.bq.append(buf)
            self.nq += len(buf)


class StreamTar(StreamArc):
    """construct in-memory tar file from the given path"""

    def __init__(
        self,
        log: "NamedLogger",
        fgen: Generator[dict[str, Any], None, None],
        cmp: str = "",
        **kwargs: Any
    ):
        super(StreamTar, self).__init__(log, fgen)

        self.ci = 0
        self.co = 0
        self.qfile = QFile()
        self.errf: dict[str, Any] = {}

        # python 3.8 changed to PAX_FORMAT as default;
        # slower, bigger, and no particular advantage
        fmt = tarfile.GNU_FORMAT
        if "pax" in cmp:
            # unless a client asks for it (currently
            # gnu-tar has wider support than pax-tar)
            fmt = tarfile.PAX_FORMAT
            cmp = re.sub(r"[^a-z0-9]*pax[^a-z0-9]*", "", cmp)

        try:
            cmp, zs = cmp.replace(":", ",").split(",")
            lv = int(zs)
        except:
            lv = -1

        arg = {"name": None, "fileobj": self.qfile, "mode": "w", "format": fmt}
        if cmp == "gz":
            fun = tarfile.TarFile.gzopen
            arg["compresslevel"] = lv if lv >= 0 else 3
        elif cmp == "bz2":
            fun = tarfile.TarFile.bz2open
            arg["compresslevel"] = lv if lv >= 0 else 2
        elif cmp == "xz":
            fun = tarfile.TarFile.xzopen
            arg["preset"] = lv if lv >= 0 else 1
        else:
            fun = tarfile.open
            arg["mode"] = "w|"

        self.tar = fun(**arg)

        Daemon(self._gen, "star-gen")

    def gen(self) -> Generator[Optional[bytes], None, None]:
        buf = b""
        try:
            while True:
                buf = self.qfile.q.get()
                if not buf:
                    break

                self.co += len(buf)
                yield buf

            yield None
        finally:
            while buf:
                try:
                    buf = self.qfile.q.get()
                except:
                    pass

            if self.errf:
                bos.unlink(self.errf["ap"])

    def ser(self, f: dict[str, Any]) -> None:
        name = f["vp"]
        src = f["ap"]
        fsi = f["st"]

        if stat.S_ISDIR(fsi.st_mode):
            return

        inf = tarfile.TarInfo(name=name)
        inf.mode = fsi.st_mode
        inf.size = fsi.st_size
        inf.mtime = fsi.st_mtime
        inf.uid = 0
        inf.gid = 0

        self.ci += inf.size
        with open(fsenc(src), "rb", 512 * 1024) as fo:
            self.tar.addfile(inf, fo)

    def _gen(self) -> None:
        errors = []
        for f in self.fgen:
            if "err" in f:
                errors.append((f["vp"], f["err"]))
                continue

            if self.stopped:
                break

            try:
                self.ser(f)
            except:
                ex = min_ex(5, True).replace("\n", "\n-- ")
                errors.append((f["vp"], ex))

        if errors:
            self.errf, txt = errdesc(errors)
            self.log("\n".join(([repr(self.errf)] + txt[1:])))
            self.ser(self.errf)

        self.tar.close()
        self.qfile.write(None)

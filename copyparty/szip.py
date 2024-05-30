# coding: utf-8
from __future__ import print_function, unicode_literals

import calendar
import stat
import time
import zlib

from .authsrv import AuthSrv
from .bos import bos
from .sutil import StreamArc, errdesc
from .util import min_ex, sanitize_fn, spack, sunpack, yieldfile

if True:  # pylint: disable=using-constant-test
    from typing import Any, Generator, Optional

    from .util import NamedLogger


def dostime2unix(buf: bytes) -> int:
    t, d = sunpack(b"<HH", buf)

    ts = (t & 0x1F) * 2
    tm = (t >> 5) & 0x3F
    th = t >> 11

    dd = d & 0x1F
    dm = (d >> 5) & 0xF
    dy = (d >> 9) + 1980

    tt = (dy, dm, dd, th, tm, ts)
    tf = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}"
    iso = tf.format(*tt)

    dt = time.strptime(iso, "%Y-%m-%d %H:%M:%S")
    return int(calendar.timegm(dt))


def unixtime2dos(ts: int) -> bytes:
    tt = time.gmtime(ts + 1)
    dy, dm, dd, th, tm, ts = list(tt)[:6]

    bd = ((dy - 1980) << 9) + (dm << 5) + dd
    bt = (th << 11) + (tm << 5) + ts // 2
    try:
        return spack(b"<HH", bt, bd)
    except:
        return b"\x00\x00\x21\x00"


def gen_fdesc(sz: int, crc32: int, z64: bool) -> bytes:
    ret = b"\x50\x4b\x07\x08"
    fmt = b"<LQQ" if z64 else b"<LLL"
    ret += spack(fmt, crc32, sz, sz)
    return ret


def gen_hdr(
    h_pos: Optional[int],
    fn: str,
    sz: int,
    lastmod: int,
    utf8: bool,
    icrc32: int,
    pre_crc: bool,
) -> bytes:
    """
    does regular file headers
    and the central directory meme if h_pos is set
    (h_pos = absolute position of the regular header)
    """

    # appnote 4.5 / zip 3.0 (2008) / unzip 6.0 (2009) says to add z64
    # extinfo for values which exceed H, but that becomes an off-by-one
    # (can't tell if it was clamped or exactly maxval), make it obvious
    z64 = sz >= 0xFFFFFFFF
    z64v = [sz, sz] if z64 else []
    if h_pos and h_pos >= 0xFFFFFFFF:
        # central, also consider ptr to original header
        z64v.append(h_pos)

    # confusingly this doesn't bump if h_pos
    req_ver = b"\x2d\x00" if z64 else b"\x0a\x00"

    if icrc32:
        crc32 = spack(b"<L", icrc32)
    else:
        crc32 = b"\x00" * 4

    if h_pos is None:
        # 4b magic, 2b min-ver
        ret = b"\x50\x4b\x03\x04" + req_ver
    else:
        # 4b magic, 2b spec-ver (1b compat, 1b os (00 dos, 03 unix)), 2b min-ver
        ret = b"\x50\x4b\x01\x02\x1e\x03" + req_ver

    ret += b"\x00" if pre_crc else b"\x08"  # streaming
    ret += b"\x08" if utf8 else b"\x00"  # appnote 6.3.2 (2007)

    # 2b compression, 4b time, 4b crc
    ret += b"\x00\x00" + unixtime2dos(lastmod) + crc32

    # spec says to put zeros when !crc if bit3 (streaming)
    # however infozip does actual sz and it even works on winxp
    # (same reasning for z64 extradata later)
    vsz = 0xFFFFFFFF if z64 else sz
    ret += spack(b"<LL", vsz, vsz)

    # windows support (the "?" replace below too)
    fn = sanitize_fn(fn, "/", [])
    bfn = fn.encode("utf-8" if utf8 else "cp437", "replace").replace(b"?", b"_")

    # add ntfs (0x24) and/or unix (0x10) extrafields for utc, add z64 if requested
    z64_len = len(z64v) * 8 + 4 if z64v else 0
    ret += spack(b"<HH", len(bfn), 0x10 + z64_len)

    if h_pos is not None:
        # 2b comment, 2b diskno
        ret += b"\x00" * 4

        # 2b internal.attr, 4b external.attr
        # infozip-macos: 0100 0000 a481 (spec-ver 1e03) file:644
        # infozip-macos: 0100 0100 0080 (spec-ver 1e03) file:000
        #     win10-zip: 0000 2000 0000 (spec-ver xx00) FILE_ATTRIBUTE_ARCHIVE
        ret += b"\x00\x00\x00\x00\xa4\x81"  # unx
        # ret += b"\x00\x00\x20\x00\x00\x00"  # fat

        # 4b local-header-ofs
        ret += spack(b"<L", min(h_pos, 0xFFFFFFFF))

    ret += bfn

    # ntfs: type 0a, size 20, rsvd, attr1, len 18, mtime, atime, ctime
    # b"\xa3\x2f\x82\x41\x55\x68\xd8\x01"  1652616838.798941100  ~5.861518  132970904387989411  ~58615181
    # nt = int((lastmod + 11644473600) * 10000000)
    # ret += spack(b"<HHLHHQQQ", 0xA, 0x20, 0, 1, 0x18, nt, nt, nt)

    # unix: type 0d, size 0c, atime, mtime, uid, gid
    ret += spack(b"<HHLLHH", 0xD, 0xC, int(lastmod), int(lastmod), 1000, 1000)

    if z64v:
        ret += spack(b"<HH" + b"Q" * len(z64v), 1, len(z64v) * 8, *z64v)

    return ret


def gen_ecdr(
    items: list[tuple[str, int, int, int, int]], cdir_pos: int, cdir_end: int
) -> tuple[bytes, bool]:
    """
    summary of all file headers,
    usually the zipfile footer unless something clamps
    """

    ret = b"\x50\x4b\x05\x06"

    # 2b ndisk, 2b disk0
    ret += b"\x00" * 4

    cdir_sz = cdir_end - cdir_pos

    nitems = min(0xFFFF, len(items))
    csz = min(0xFFFFFFFF, cdir_sz)
    cpos = min(0xFFFFFFFF, cdir_pos)

    need_64 = nitems == 0xFFFF or 0xFFFFFFFF in [csz, cpos]

    # 2b tnfiles, 2b dnfiles, 4b dir sz, 4b dir pos
    ret += spack(b"<HHLL", nitems, nitems, csz, cpos)

    # 2b comment length
    ret += b"\x00\x00"

    return ret, need_64


def gen_ecdr64(
    items: list[tuple[str, int, int, int, int]], cdir_pos: int, cdir_end: int
) -> bytes:
    """
    z64 end of central directory
    added when numfiles or a headerptr clamps
    """

    ret = b"\x50\x4b\x06\x06"

    # 8b own length from hereon
    ret += b"\x2c" + b"\x00" * 7

    # 2b spec-ver, 2b min-ver
    ret += b"\x1e\x03\x2d\x00"

    # 4b ndisk, 4b disk0
    ret += b"\x00" * 8

    # 8b tnfiles, 8b dnfiles, 8b dir sz, 8b dir pos
    cdir_sz = cdir_end - cdir_pos
    ret += spack(b"<QQQQ", len(items), len(items), cdir_sz, cdir_pos)

    return ret


def gen_ecdr64_loc(ecdr64_pos: int) -> bytes:
    """
    z64 end of central directory locator
    points to ecdr64
    why
    """

    ret = b"\x50\x4b\x06\x07"

    # 4b cdisk, 8b start of ecdr64, 4b ndisks
    ret += spack(b"<LQL", 0, ecdr64_pos, 1)

    return ret


class StreamZip(StreamArc):
    def __init__(
        self,
        log: "NamedLogger",
        asrv: AuthSrv,
        fgen: Generator[dict[str, Any], None, None],
        utf8: bool = False,
        pre_crc: bool = False,
        **kwargs: Any
    ) -> None:
        super(StreamZip, self).__init__(log, asrv, fgen)

        self.utf8 = utf8
        self.pre_crc = pre_crc

        self.pos = 0
        self.items: list[tuple[str, int, int, int, int]] = []

    def _ct(self, buf: bytes) -> bytes:
        self.pos += len(buf)
        return buf

    def ser(self, f: dict[str, Any]) -> Generator[bytes, None, None]:
        name = f["vp"]
        src = f["ap"]
        st = f["st"]

        if stat.S_ISDIR(st.st_mode):
            return

        sz = st.st_size
        ts = st.st_mtime

        crc = 0
        if self.pre_crc:
            for buf in yieldfile(src, self.args.iobuf):
                crc = zlib.crc32(buf, crc)

            crc &= 0xFFFFFFFF

        h_pos = self.pos
        buf = gen_hdr(None, name, sz, ts, self.utf8, crc, self.pre_crc)
        yield self._ct(buf)

        for buf in yieldfile(src, self.args.iobuf):
            if not self.pre_crc:
                crc = zlib.crc32(buf, crc)

            yield self._ct(buf)

        crc &= 0xFFFFFFFF

        self.items.append((name, sz, ts, crc, h_pos))

        z64 = sz >= 4 * 1024 * 1024 * 1024

        if z64 or not self.pre_crc:
            buf = gen_fdesc(sz, crc, z64)
            yield self._ct(buf)

    def gen(self) -> Generator[bytes, None, None]:
        errf: dict[str, Any] = {}
        errors = []
        mbuf = b""
        try:
            for f in self.fgen:
                if "err" in f:
                    errors.append((f["vp"], f["err"]))
                    continue

                try:
                    for x in self.ser(f):
                        mbuf += x
                        if len(mbuf) >= 16384:
                            yield mbuf
                            mbuf = b""
                except GeneratorExit:
                    raise
                except:
                    ex = min_ex(5, True).replace("\n", "\n-- ")
                    errors.append((f["vp"], ex))

            if mbuf:
                yield mbuf
                mbuf = b""

            if errors:
                errf, txt = errdesc(self.asrv.vfs, errors)
                self.log("\n".join(([repr(errf)] + txt[1:])))
                for x in self.ser(errf):
                    yield x

            cdir_pos = self.pos
            for name, sz, ts, crc, h_pos in self.items:
                buf = gen_hdr(h_pos, name, sz, ts, self.utf8, crc, self.pre_crc)
                mbuf += self._ct(buf)
                if len(mbuf) >= 16384:
                    yield mbuf
                    mbuf = b""
            cdir_end = self.pos

            _, need_64 = gen_ecdr(self.items, cdir_pos, cdir_end)
            if need_64:
                ecdir64_pos = self.pos
                buf = gen_ecdr64(self.items, cdir_pos, cdir_end)
                mbuf += self._ct(buf)

                buf = gen_ecdr64_loc(ecdir64_pos)
                mbuf += self._ct(buf)

            ecdr, _ = gen_ecdr(self.items, cdir_pos, cdir_end)
            yield mbuf + self._ct(ecdr)
        finally:
            if errf:
                bos.unlink(errf["ap"])

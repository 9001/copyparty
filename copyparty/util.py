# coding: utf-8
from __future__ import print_function, unicode_literals

import base64
import contextlib
import errno
import hashlib
import hmac
import json
import logging
import math
import mimetypes
import os
import platform
import re
import select
import shutil
import signal
import socket
import stat
import struct
import subprocess as sp  # nosec
import sys
import threading
import time
import traceback
from collections import Counter
from datetime import datetime
from email.utils import formatdate

from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from queue import Queue

from .__init__ import ANYWIN, EXE, MACOS, PY2, TYPE_CHECKING, VT100, WINDOWS
from .__version__ import S_BUILD_DT, S_VERSION
from .stolen import surrogateescape


def _ens(want: str) -> tuple[int, ...]:
    ret: list[int] = []
    for v in want.split():
        try:
            ret.append(getattr(errno, v))
        except:
            pass

    return tuple(ret)


# WSAECONNRESET - foribly closed by remote
# WSAENOTSOCK - no longer a socket
# EUNATCH - can't assign requested address (wifi down)
E_SCK = _ens("ENOTCONN EUNATCH EBADF WSAENOTSOCK WSAECONNRESET")
E_ADDR_NOT_AVAIL = _ens("EADDRNOTAVAIL WSAEADDRNOTAVAIL")
E_ADDR_IN_USE = _ens("EADDRINUSE WSAEADDRINUSE")
E_ACCESS = _ens("EACCES WSAEACCES")
E_UNREACH = _ens("EHOSTUNREACH WSAEHOSTUNREACH ENETUNREACH WSAENETUNREACH")


try:
    import ctypes
    import fcntl
    import termios
except:
    pass

try:
    HAVE_SQLITE3 = True
    import sqlite3  # pylint: disable=unused-import  # typechk
except:
    HAVE_SQLITE3 = False

try:
    HAVE_PSUTIL = True
    import psutil
except:
    HAVE_PSUTIL = False

if True:  # pylint: disable=using-constant-test
    import types
    from collections.abc import Callable, Iterable

    import typing
    from typing import Any, Generator, Optional, Pattern, Protocol, Union

    class RootLogger(Protocol):
        def __call__(self, src: str, msg: str, c: Union[int, str] = 0) -> None:
            return None

    class NamedLogger(Protocol):
        def __call__(self, msg: str, c: Union[int, str] = 0) -> None:
            return None


if TYPE_CHECKING:
    import magic

    from .authsrv import VFS

FAKE_MP = False

try:
    import multiprocessing as mp

    # import multiprocessing.dummy as mp
except ImportError:
    # support jython
    mp = None  # type: ignore

if not PY2:
    from io import BytesIO
    from urllib.parse import quote_from_bytes as quote
    from urllib.parse import unquote_to_bytes as unquote
else:
    from StringIO import StringIO as BytesIO
    from urllib import quote  # pylint: disable=no-name-in-module
    from urllib import unquote  # pylint: disable=no-name-in-module


try:
    struct.unpack(b">i", b"idgi")
    spack = struct.pack
    sunpack = struct.unpack
except:

    def spack(fmt: bytes, *a: Any) -> bytes:
        return struct.pack(fmt.decode("ascii"), *a)

    def sunpack(fmt: bytes, a: bytes) -> tuple[Any, ...]:
        return struct.unpack(fmt.decode("ascii"), a)


ansi_re = re.compile("\033\\[[^mK]*[mK]")


surrogateescape.register_surrogateescape()
if WINDOWS and PY2:
    FS_ENCODING = "utf-8"
else:
    FS_ENCODING = sys.getfilesystemencoding()


SYMTIME = sys.version_info > (3, 6) and os.utime in os.supports_follow_symlinks

META_NOBOTS = '<meta name="robots" content="noindex, nofollow">'

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z"

HTTPCODE = {
    200: "OK",
    201: "Created",
    204: "No Content",
    206: "Partial Content",
    207: "Multi-Status",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    416: "Requested Range Not Satisfiable",
    422: "Unprocessable Entity",
    423: "Locked",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    503: "Service Unavailable",
}


IMPLICATIONS = [
    ["e2dsa", "e2ds"],
    ["e2ds", "e2d"],
    ["e2tsr", "e2ts"],
    ["e2ts", "e2t"],
    ["e2t", "e2d"],
    ["e2vu", "e2v"],
    ["e2vp", "e2v"],
    ["e2v", "e2d"],
    ["smbw", "smb"],
    ["smb1", "smb"],
    ["smbvvv", "smbvv"],
    ["smbvv", "smbv"],
    ["smbv", "smb"],
    ["zv", "zmv"],
    ["zv", "zsv"],
    ["z", "zm"],
    ["z", "zs"],
    ["zmvv", "zmv"],
    ["zm4", "zm"],
    ["zm6", "zm"],
    ["zmv", "zm"],
    ["zms", "zm"],
    ["zsv", "zs"],
]
if ANYWIN:
    IMPLICATIONS.extend([["z", "zm4"]])


UNPLICATIONS = [["no_dav", "daw"]]


MIMES = {
    "opus": "audio/ogg; codecs=opus",
}


def _add_mimes() -> None:
    # `mimetypes` is woefully unpopulated on windows
    # but will be used as fallback on linux

    for ln in """text css html csv
application json wasm xml pdf rtf zip jar fits wasm
image webp jpeg png gif bmp jxl jp2 jxs jxr tiff bpg heic heif avif
audio aac ogg wav flac ape amr
video webm mp4 mpeg
font woff woff2 otf ttf
""".splitlines():
        k, vs = ln.split(" ", 1)
        for v in vs.strip().split():
            MIMES[v] = "{}/{}".format(k, v)

    for ln in """text md=plain txt=plain js=javascript
application 7z=x-7z-compressed tar=x-tar bz2=x-bzip2 gz=gzip rar=x-rar-compressed zst=zstd xz=x-xz lz=lzip cpio=x-cpio
application msi=x-ms-installer cab=vnd.ms-cab-compressed rpm=x-rpm crx=x-chrome-extension
application epub=epub+zip mobi=x-mobipocket-ebook lit=x-ms-reader rss=rss+xml atom=atom+xml torrent=x-bittorrent
application p7s=pkcs7-signature dcm=dicom shx=vnd.shx shp=vnd.shp dbf=x-dbf gml=gml+xml gpx=gpx+xml amf=x-amf
application swf=x-shockwave-flash m3u=vnd.apple.mpegurl db3=vnd.sqlite3 sqlite=vnd.sqlite3
text ass=plain ssa=plain
image jpg=jpeg xpm=x-xpixmap psd=vnd.adobe.photoshop jpf=jpx tif=tiff ico=x-icon djvu=vnd.djvu
image heic=heic-sequence heif=heif-sequence hdr=vnd.radiance svg=svg+xml
audio caf=x-caf mp3=mpeg m4a=mp4 mid=midi mpc=musepack aif=aiff au=basic qcp=qcelp
video mkv=x-matroska mov=quicktime avi=x-msvideo m4v=x-m4v ts=mp2t
video asf=x-ms-asf flv=x-flv 3gp=3gpp 3g2=3gpp2 rmvb=vnd.rn-realmedia-vbr
font ttc=collection
""".splitlines():
        k, ems = ln.split(" ", 1)
        for em in ems.strip().split():
            ext, mime = em.split("=")
            MIMES[ext] = "{}/{}".format(k, mime)


_add_mimes()


EXTS: dict[str, str] = {v: k for k, v in MIMES.items()}

EXTS["vnd.mozilla.apng"] = "png"

MAGIC_MAP = {"jpeg": "jpg"}


REKOBO_KEY = {
    v: ln.split(" ", 1)[0]
    for ln in """
1B 6d B
2B 7d Gb F#
3B 8d Db C#
4B 9d Ab G#
5B 10d Eb D#
6B 11d Bb A#
7B 12d F
8B 1d C
9B 2d G
10B 3d D
11B 4d A
12B 5d E
1A 6m Abm G#m
2A 7m Ebm D#m
3A 8m Bbm A#m
4A 9m Fm
5A 10m Cm
6A 11m Gm
7A 12m Dm
8A 1m Am
9A 2m Em
10A 3m Bm
11A 4m Gbm F#m
12A 5m Dbm C#m
""".strip().split(
        "\n"
    )
    for v in ln.strip().split(" ")[1:]
    if v
}

REKOBO_LKEY = {k.lower(): v for k, v in REKOBO_KEY.items()}


pybin = sys.executable or ""
if EXE:
    pybin = ""
    for zsg in "python3 python".split():
        try:
            zsg = shutil.which(zsg)
            if zsg:
                pybin = zsg
                break
        except:
            pass


def py_desc() -> str:
    interp = platform.python_implementation()
    py_ver = ".".join([str(x) for x in sys.version_info])
    ofs = py_ver.find(".final.")
    if ofs > 0:
        py_ver = py_ver[:ofs]

    try:
        bitness = struct.calcsize(b"P") * 8
    except:
        bitness = struct.calcsize("P") * 8

    host_os = platform.system()
    compiler = platform.python_compiler().split("http")[0]

    m = re.search(r"([0-9]+\.[0-9\.]+)", platform.version())
    os_ver = m.group(1) if m else ""

    return "{:>9} v{} on {}{} {} [{}]".format(
        interp, py_ver, host_os, bitness, os_ver, compiler
    )


def _sqlite_ver() -> str:
    try:
        co = sqlite3.connect(":memory:")
        cur = co.cursor()
        try:
            vs = cur.execute("select * from pragma_compile_options").fetchall()
        except:
            vs = cur.execute("pragma compile_options").fetchall()

        v = next(x[0].split("=")[1] for x in vs if x[0].startswith("THREADSAFE="))
        cur.close()
        co.close()
    except:
        v = "W"

    return "{}*{}".format(sqlite3.sqlite_version, v)


try:
    SQLITE_VER = _sqlite_ver()
except:
    SQLITE_VER = "(None)"

try:
    from jinja2 import __version__ as JINJA_VER
except:
    JINJA_VER = "(None)"

try:
    from pyftpdlib.__init__ import __ver__ as PYFTPD_VER
except:
    PYFTPD_VER = "(None)"


VERSIONS = "copyparty v{} ({})\n{}\n   sqlite v{} | jinja v{} | pyftpd v{}".format(
    S_VERSION, S_BUILD_DT, py_desc(), SQLITE_VER, JINJA_VER, PYFTPD_VER
)


_: Any = (mp, BytesIO, quote, unquote, SQLITE_VER, JINJA_VER, PYFTPD_VER)
__all__ = ["mp", "BytesIO", "quote", "unquote", "SQLITE_VER", "JINJA_VER", "PYFTPD_VER"]


class Daemon(threading.Thread):
    def __init__(
        self,
        target: Any,
        name: Optional[str] = None,
        a: Optional[Iterable[Any]] = None,
        r: bool = True,
        ka: Optional[dict[Any, Any]] = None,
    ) -> None:
        threading.Thread.__init__(
            self, target=target, name=name, args=a or (), kwargs=ka
        )
        self.daemon = True
        if r:
            self.start()


class Netdev(object):
    def __init__(self, ip: str, idx: int, name: str, desc: str):
        self.ip = ip
        self.idx = idx
        self.name = name
        self.desc = desc

    def __str__(self):
        return "{}-{}{}".format(self.idx, self.name, self.desc)

    def __repr__(self):
        return "'{}-{}'".format(self.idx, self.name)

    def __lt__(self, rhs):
        return str(self) < str(rhs)

    def __eq__(self, rhs):
        return str(self) == str(rhs)


class Cooldown(object):
    def __init__(self, maxage: float) -> None:
        self.maxage = maxage
        self.mutex = threading.Lock()
        self.hist: dict[str, float] = {}
        self.oldest = 0.0

    def poke(self, key: str) -> bool:
        with self.mutex:
            now = time.time()

            ret = False
            pv: float = self.hist.get(key, 0)
            if now - pv > self.maxage:
                self.hist[key] = now
                ret = True

            if self.oldest - now > self.maxage * 2:
                self.hist = {
                    k: v for k, v in self.hist.items() if now - v < self.maxage
                }
                self.oldest = sorted(self.hist.values())[0]

            return ret


class HLog(logging.Handler):
    def __init__(self, log_func: "RootLogger") -> None:
        logging.Handler.__init__(self)
        self.log_func = log_func
        self.ptn_ftp = re.compile(r"^([0-9a-f:\.]+:[0-9]{1,5})-\[")
        self.ptn_smb_ign = re.compile(r"^(Callback added|Config file parsed)")

    def __repr__(self) -> str:
        level = logging.getLevelName(self.level)
        return "<%s cpp(%s)>" % (self.__class__.__name__, level)

    def flush(self) -> None:
        pass

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        lv = record.levelno
        if lv < logging.INFO:
            c = 6
        elif lv < logging.WARNING:
            c = 0
        elif lv < logging.ERROR:
            c = 3
        else:
            c = 1

        if record.name == "pyftpdlib":
            m = self.ptn_ftp.match(msg)
            if m:
                ip = m.group(1)
                msg = msg[len(ip) + 1 :]
                if ip.startswith("::ffff:"):
                    record.name = ip[7:]
                else:
                    record.name = ip
        elif record.name.startswith("impacket"):
            if self.ptn_smb_ign.match(msg):
                return

        self.log_func(record.name[-21:], msg, c)


class NetMap(object):
    def __init__(self, ips: list[str], netdevs: dict[str, Netdev]) -> None:
        if "::" in ips:
            ips = [x for x in ips if x != "::"] + list(
                [x.split("/")[0] for x in netdevs if ":" in x]
            )
            ips.append("0.0.0.0")

        if "0.0.0.0" in ips:
            ips = [x for x in ips if x != "0.0.0.0"] + list(
                [x.split("/")[0] for x in netdevs if ":" not in x]
            )

        ips = [x for x in ips if x not in ("::1", "127.0.0.1")]
        ips = find_prefix(ips, netdevs)

        self.cache: dict[str, str] = {}
        self.b2sip: dict[bytes, str] = {}
        self.b2net: dict[bytes, Union[IPv4Network, IPv6Network]] = {}
        self.bip: list[bytes] = []
        for ip in ips:
            v6 = ":" in ip
            fam = socket.AF_INET6 if v6 else socket.AF_INET
            bip = socket.inet_pton(fam, ip.split("/")[0])
            self.bip.append(bip)
            self.b2sip[bip] = ip.split("/")[0]
            self.b2net[bip] = (IPv6Network if v6 else IPv4Network)(ip, False)

        self.bip.sort(reverse=True)

    def map(self, ip: str) -> str:
        try:
            return self.cache[ip]
        except:
            pass

        v6 = ":" in ip
        ci = IPv6Address(ip) if v6 else IPv4Address(ip)
        bip = next((x for x in self.bip if ci in self.b2net[x]), None)
        ret = self.b2sip[bip] if bip else ""
        if len(self.cache) > 9000:
            self.cache = {}
        self.cache[ip] = ret
        return ret


class UnrecvEOF(OSError):
    pass


class _Unrecv(object):
    """
    undo any number of socket recv ops
    """

    def __init__(self, s: socket.socket, log: Optional["NamedLogger"]) -> None:
        self.s = s
        self.log = log
        self.buf: bytes = b""

    def recv(self, nbytes: int, spins: int = 1) -> bytes:
        if self.buf:
            ret = self.buf[:nbytes]
            self.buf = self.buf[nbytes:]
            return ret

        while True:
            try:
                ret = self.s.recv(nbytes)
                break
            except socket.timeout:
                spins -= 1
                if spins <= 0:
                    ret = b""
                    break
                continue
            except:
                ret = b""
                break

        if not ret:
            raise UnrecvEOF("client stopped sending data")

        return ret

    def recv_ex(self, nbytes: int, raise_on_trunc: bool = True) -> bytes:
        """read an exact number of bytes"""
        ret = b""
        try:
            while nbytes > len(ret):
                ret += self.recv(nbytes - len(ret))
        except OSError:
            t = "client only sent {} of {} expected bytes".format(len(ret), nbytes)
            if len(ret) <= 16:
                t += "; got {!r}".format(ret)

            if raise_on_trunc:
                raise UnrecvEOF(5, t)
            elif self.log:
                self.log(t, 3)

        return ret

    def unrecv(self, buf: bytes) -> None:
        self.buf = buf + self.buf


class _LUnrecv(object):
    """
    with expensive debug logging
    """

    def __init__(self, s: socket.socket, log: Optional["NamedLogger"]) -> None:
        self.s = s
        self.log = log
        self.buf = b""

    def recv(self, nbytes: int, spins: int) -> bytes:
        if self.buf:
            ret = self.buf[:nbytes]
            self.buf = self.buf[nbytes:]
            t = "\033[0;7mur:pop:\033[0;1;32m {}\n\033[0;7mur:rem:\033[0;1;35m {}\033[0m"
            print(t.format(ret, self.buf))
            return ret

        ret = self.s.recv(nbytes)
        t = "\033[0;7mur:recv\033[0;1;33m {}\033[0m"
        print(t.format(ret))
        if not ret:
            raise UnrecvEOF("client stopped sending data")

        return ret

    def recv_ex(self, nbytes: int, raise_on_trunc: bool = True) -> bytes:
        """read an exact number of bytes"""
        try:
            ret = self.recv(nbytes, 1)
            err = False
        except:
            ret = b""
            err = True

        while not err and len(ret) < nbytes:
            try:
                ret += self.recv(nbytes - len(ret), 1)
            except OSError:
                err = True

        if err:
            t = "client only sent {} of {} expected bytes".format(len(ret), nbytes)
            if raise_on_trunc:
                raise UnrecvEOF(t)
            elif self.log:
                self.log(t, 3)

        return ret

    def unrecv(self, buf: bytes) -> None:
        self.buf = buf + self.buf
        t = "\033[0;7mur:push\033[0;1;31m {}\n\033[0;7mur:rem:\033[0;1;35m {}\033[0m"
        print(t.format(buf, self.buf))


Unrecv = _Unrecv


class CachedSet(object):
    def __init__(self, maxage: float) -> None:
        self.c: dict[Any, float] = {}
        self.maxage = maxage
        self.oldest = 0.0

    def add(self, v: Any) -> None:
        self.c[v] = time.time()

    def cln(self) -> None:
        now = time.time()
        if now - self.oldest < self.maxage:
            return

        c = self.c = {k: v for k, v in self.c.items() if now - v < self.maxage}
        try:
            self.oldest = c[min(c, key=c.get)]
        except:
            self.oldest = now


class FHC(object):
    class CE(object):
        def __init__(self, fh: typing.BinaryIO) -> None:
            self.ts: float = 0
            self.fhs = [fh]

    def __init__(self) -> None:
        self.cache: dict[str, FHC.CE] = {}
        self.aps: set[str] = set()

    def close(self, path: str) -> None:
        try:
            ce = self.cache[path]
        except:
            return

        for fh in ce.fhs:
            fh.close()

        del self.cache[path]
        self.aps.remove(path)

    def clean(self) -> None:
        if not self.cache:
            return

        keep = {}
        now = time.time()
        for path, ce in self.cache.items():
            if now < ce.ts + 5:
                keep[path] = ce
            else:
                for fh in ce.fhs:
                    fh.close()

        self.cache = keep

    def pop(self, path: str) -> typing.BinaryIO:
        return self.cache[path].fhs.pop()

    def put(self, path: str, fh: typing.BinaryIO) -> None:
        self.aps.add(path)
        try:
            ce = self.cache[path]
            ce.fhs.append(fh)
        except:
            ce = self.CE(fh)
            self.cache[path] = ce

        ce.ts = time.time()


class ProgressPrinter(threading.Thread):
    """
    periodically print progress info without linefeeds
    """

    def __init__(self) -> None:
        threading.Thread.__init__(self, name="pp")
        self.daemon = True
        self.msg = ""
        self.end = False
        self.n = -1
        self.start()

    def run(self) -> None:
        msg = None
        fmt = " {}\033[K\r" if VT100 else " {} $\r"
        while not self.end:
            time.sleep(0.1)
            if msg == self.msg or self.end:
                continue

            msg = self.msg
            uprint(fmt.format(msg))
            if PY2:
                sys.stdout.flush()

        if VT100:
            print("\033[K", end="")
        elif msg:
            print("------------------------")

        sys.stdout.flush()  # necessary on win10 even w/ stderr btw


class MTHash(object):
    def __init__(self, cores: int):
        self.pp: Optional[ProgressPrinter] = None
        self.f: Optional[typing.BinaryIO] = None
        self.sz = 0
        self.csz = 0
        self.stop = False
        self.omutex = threading.Lock()
        self.imutex = threading.Lock()
        self.work_q: Queue[int] = Queue()
        self.done_q: Queue[tuple[int, str, int, int]] = Queue()
        self.thrs = []
        for n in range(cores):
            t = Daemon(self.worker, "mth-" + str(n))
            self.thrs.append(t)

    def hash(
        self,
        f: typing.BinaryIO,
        fsz: int,
        chunksz: int,
        pp: Optional[ProgressPrinter] = None,
        prefix: str = "",
        suffix: str = "",
    ) -> list[tuple[str, int, int]]:
        with self.omutex:
            self.f = f
            self.sz = fsz
            self.csz = chunksz

            chunks: dict[int, tuple[str, int, int]] = {}
            nchunks = int(math.ceil(fsz / chunksz))
            for nch in range(nchunks):
                self.work_q.put(nch)

            ex = ""
            for nch in range(nchunks):
                qe = self.done_q.get()
                try:
                    nch, dig, ofs, csz = qe
                    chunks[nch] = (dig, ofs, csz)
                except:
                    ex = ex or str(qe)

                if pp:
                    mb = int((fsz - nch * chunksz) / 1024 / 1024)
                    pp.msg = prefix + str(mb) + suffix

            if ex:
                raise Exception(ex)

            ret = []
            for n in range(nchunks):
                ret.append(chunks[n])

            self.f = None
            self.csz = 0
            self.sz = 0
            return ret

    def worker(self) -> None:
        while True:
            ofs = self.work_q.get()
            try:
                v = self.hash_at(ofs)
            except Exception as ex:
                v = str(ex)  # type: ignore

            self.done_q.put(v)

    def hash_at(self, nch: int) -> tuple[int, str, int, int]:
        f = self.f
        ofs = ofs0 = nch * self.csz
        chunk_sz = chunk_rem = min(self.csz, self.sz - ofs)
        if self.stop:
            return nch, "", ofs0, chunk_sz

        assert f
        hashobj = hashlib.sha512()
        while chunk_rem > 0:
            with self.imutex:
                f.seek(ofs)
                buf = f.read(min(chunk_rem, 1024 * 1024 * 12))

            if not buf:
                raise Exception("EOF at " + str(ofs))

            hashobj.update(buf)
            chunk_rem -= len(buf)
            ofs += len(buf)

        bdig = hashobj.digest()[:33]
        udig = base64.urlsafe_b64encode(bdig).decode("utf-8")
        return nch, udig, ofs0, chunk_sz


class HMaccas(object):
    def __init__(self, keypath: str, retlen: int) -> None:
        self.retlen = retlen
        self.cache: dict[bytes, str] = {}
        try:
            with open(keypath, "rb") as f:
                self.key = f.read()
                if len(self.key) != 64:
                    raise Exception()
        except:
            self.key = os.urandom(64)
            with open(keypath, "wb") as f:
                f.write(self.key)

    def b(self, msg: bytes) -> str:
        try:
            return self.cache[msg]
        except:
            if len(self.cache) > 9000:
                self.cache = {}

            zb = hmac.new(self.key, msg, hashlib.sha512).digest()
            zs = base64.urlsafe_b64encode(zb)[: self.retlen].decode("utf-8")
            self.cache[msg] = zs
            return zs

    def s(self, msg: str) -> str:
        return self.b(msg.encode("utf-8", "replace"))


class Magician(object):
    def __init__(self) -> None:
        self.bad_magic = False
        self.mutex = threading.Lock()
        self.magic: Optional["magic.Magic"] = None

    def ext(self, fpath: str) -> str:
        import magic

        try:
            if self.bad_magic:
                raise Exception()

            if not self.magic:
                try:
                    with self.mutex:
                        if not self.magic:
                            self.magic = magic.Magic(uncompress=False, extension=True)
                except:
                    self.bad_magic = True
                    raise

            with self.mutex:
                ret = self.magic.from_file(fpath)
        except:
            ret = "?"

        ret = ret.split("/")[0]
        ret = MAGIC_MAP.get(ret, ret)
        if "?" not in ret:
            return ret

        mime = magic.from_file(fpath, mime=True)
        mime = re.split("[; ]", mime, 1)[0]
        try:
            return EXTS[mime]
        except:
            pass

        mg = mimetypes.guess_extension(mime)
        if mg:
            return mg[1:]
        else:
            raise Exception()


class Garda(object):
    """ban clients for repeated offenses"""

    def __init__(self, cfg: str) -> None:
        try:
            a, b, c = cfg.strip().split(",")
            self.lim = int(a)
            self.win = int(b) * 60
            self.pen = int(c) * 60
        except:
            self.lim = self.win = self.pen = 0

        self.ct: dict[str, list[int]] = {}
        self.prev: dict[str, str] = {}
        self.last_cln = 0

    def cln(self, ip: str) -> None:
        n = 0
        ok = int(time.time() - self.win)
        for v in self.ct[ip]:
            if v < ok:
                n += 1
            else:
                break
        if n:
            te = self.ct[ip][n:]
            if te:
                self.ct[ip] = te
            else:
                del self.ct[ip]
                try:
                    del self.prev[ip]
                except:
                    pass

    def allcln(self) -> None:
        for k in list(self.ct):
            self.cln(k)

        self.last_cln = int(time.time())

    def bonk(self, ip: str, prev: str) -> tuple[int, str]:
        if not self.lim:
            return 0, ip

        if ":" in ip:
            # assume /64 clients; drop 4 groups
            ip = IPv6Address(ip).exploded[:-20]

        if prev:
            if self.prev.get(ip) == prev:
                return 0, ip

            self.prev[ip] = prev

        now = int(time.time())
        try:
            self.ct[ip].append(now)
        except:
            self.ct[ip] = [now]

        if now - self.last_cln > 300:
            self.allcln()
        else:
            self.cln(ip)

        if len(self.ct[ip]) >= self.lim:
            return now + self.pen, ip
        else:
            return 0, ip


if WINDOWS and sys.version_info < (3, 8):
    _popen = sp.Popen

    def _spopen(c, *a, **ka):
        enc = sys.getfilesystemencoding()
        c = [x.decode(enc, "replace") if hasattr(x, "decode") else x for x in c]
        return _popen(c, *a, **ka)

    sp.Popen = _spopen


def uprint(msg: str) -> None:
    try:
        print(msg, end="")
    except UnicodeEncodeError:
        try:
            print(msg.encode("utf-8", "replace").decode(), end="")
        except:
            print(msg.encode("ascii", "replace").decode(), end="")


def nuprint(msg: str) -> None:
    uprint("{}\n".format(msg))


def rice_tid() -> str:
    tid = threading.current_thread().ident
    c = sunpack(b"B" * 5, spack(b">Q", tid)[-5:])
    return "".join("\033[1;37;48;5;{0}m{0:02x}".format(x) for x in c) + "\033[0m"


def trace(*args: Any, **kwargs: Any) -> None:
    t = time.time()
    stack = "".join(
        "\033[36m{}\033[33m{}".format(x[0].split(os.sep)[-1][:-3], x[1])
        for x in traceback.extract_stack()[3:-1]
    )
    parts = ["{:.6f}".format(t), rice_tid(), stack]

    if args:
        parts.append(repr(args))

    if kwargs:
        parts.append(repr(kwargs))

    msg = "\033[0m ".join(parts)
    # _tracebuf.append(msg)
    nuprint(msg)


def alltrace() -> str:
    threads: dict[str, types.FrameType] = {}
    names = dict([(t.ident, t.name) for t in threading.enumerate()])
    for tid, stack in sys._current_frames().items():
        name = "{} ({:x})".format(names.get(tid), tid)
        threads[name] = stack

    rret: list[str] = []
    bret: list[str] = []
    for name, stack in sorted(threads.items()):
        ret = ["\n\n# {}".format(name)]
        pad = None
        for fn, lno, name, line in traceback.extract_stack(stack):
            fn = os.sep.join(fn.split(os.sep)[-3:])
            ret.append('File: "{}", line {}, in {}'.format(fn, lno, name))
            if line:
                ret.append("  " + str(line.strip()))
                if "self.not_empty.wait()" in line:
                    pad = " " * 4

        if pad:
            bret += [ret[0]] + [pad + x for x in ret[1:]]
        else:
            rret += ret

    return "\n".join(rret + bret) + "\n"


def start_stackmon(arg_str: str, nid: int) -> None:
    suffix = "-{}".format(nid) if nid else ""
    fp, f = arg_str.rsplit(",", 1)
    zi = int(f)
    Daemon(stackmon, "stackmon" + suffix, (fp, zi, suffix))


def stackmon(fp: str, ival: float, suffix: str) -> None:
    ctr = 0
    fp0 = fp
    while True:
        ctr += 1
        fp = fp0
        time.sleep(ival)
        st = "{}, {}\n{}".format(ctr, time.time(), alltrace())
        buf = st.encode("utf-8", "replace")

        if fp.endswith(".gz"):
            import gzip

            # 2459b 2304b 2241b 2202b 2194b 2191b lv3..8
            # 0.06s 0.08s 0.11s 0.13s 0.16s 0.19s
            buf = gzip.compress(buf, compresslevel=6)

        elif fp.endswith(".xz"):
            import lzma

            # 2276b 2216b 2200b 2192b 2168b lv0..4
            # 0.04s 0.10s 0.22s 0.41s 0.70s
            buf = lzma.compress(buf, preset=0)

        if "%" in fp:
            dt = datetime.utcnow()
            for fs in "YmdHMS":
                fs = "%" + fs
                if fs in fp:
                    fp = fp.replace(fs, dt.strftime(fs))

        if "/" in fp:
            try:
                os.makedirs(fp.rsplit("/", 1)[0])
            except:
                pass

        with open(fp + suffix, "wb") as f:
            f.write(buf)


def start_log_thrs(
    logger: Callable[[str, str, int], None], ival: float, nid: int
) -> None:
    ival = float(ival)
    tname = lname = "log-thrs"
    if nid:
        tname = "logthr-n{}-i{:x}".format(nid, os.getpid())
        lname = tname[3:]

    Daemon(log_thrs, tname, (logger, ival, lname))


def log_thrs(log: Callable[[str, str, int], None], ival: float, name: str) -> None:
    while True:
        time.sleep(ival)
        tv = [x.name for x in threading.enumerate()]
        tv = [
            x.split("-")[0]
            if x.split("-")[0] in ["httpconn", "thumb", "tagger"]
            else "listen"
            if "-listen-" in x
            else x
            for x in tv
            if not x.startswith("pydevd.")
        ]
        tv = ["{}\033[36m{}".format(v, k) for k, v in sorted(Counter(tv).items())]
        log(name, "\033[0m \033[33m".join(tv), 3)


def vol_san(vols: list["VFS"], txt: bytes) -> bytes:
    for vol in vols:
        txt = txt.replace(vol.realpath.encode("utf-8"), vol.vpath.encode("utf-8"))
        txt = txt.replace(
            vol.realpath.encode("utf-8").replace(b"\\", b"\\\\"),
            vol.vpath.encode("utf-8"),
        )

    return txt


def min_ex(max_lines: int = 8, reverse: bool = False) -> str:
    et, ev, tb = sys.exc_info()
    stb = traceback.extract_tb(tb)
    fmt = "{} @ {} <{}>: {}"
    ex = [fmt.format(fp.split(os.sep)[-1], ln, fun, txt) for fp, ln, fun, txt in stb]
    ex.append("[{}] {}".format(et.__name__ if et else "(anonymous)", ev))
    return "\n".join(ex[-max_lines:][:: -1 if reverse else 1])


@contextlib.contextmanager
def ren_open(
    fname: str, *args: Any, **kwargs: Any
) -> Generator[dict[str, tuple[typing.IO[Any], str]], None, None]:
    fun = kwargs.pop("fun", open)
    fdir = kwargs.pop("fdir", None)
    suffix = kwargs.pop("suffix", None)

    if fname == os.devnull:
        with fun(fname, *args, **kwargs) as f:
            yield {"orz": (f, fname)}
            return

    if suffix:
        ext = fname.split(".")[-1]
        if len(ext) < 7:
            suffix += "." + ext

    orig_name = fname
    bname = fname
    ext = ""
    while True:
        ofs = bname.rfind(".")
        if ofs < 0 or ofs < len(bname) - 7:
            # doesn't look like an extension anymore
            break

        ext = bname[ofs:] + ext
        bname = bname[:ofs]

    asciified = False
    b64 = ""
    while True:
        try:
            if fdir:
                fpath = os.path.join(fdir, fname)
            else:
                fpath = fname

            if suffix and os.path.lexists(fsenc(fpath)):
                fpath += suffix
                fname += suffix
                ext += suffix

            with fun(fsenc(fpath), *args, **kwargs) as f:
                if b64:
                    assert fdir
                    fp2 = "fn-trunc.{}.txt".format(b64)
                    fp2 = os.path.join(fdir, fp2)
                    with open(fsenc(fp2), "wb") as f2:
                        f2.write(orig_name.encode("utf-8"))

                yield {"orz": (f, fname)}
                return

        except OSError as ex_:
            ex = ex_

            if ex.errno == errno.EINVAL and not asciified:
                asciified = True
                bname, fname = [
                    zs.encode("ascii", "replace").decode("ascii").replace("?", "_")
                    for zs in [bname, fname]
                ]
                continue

            # ENOTSUP: zfs on ubuntu 20.04
            if ex.errno not in (errno.ENAMETOOLONG, errno.ENOSR, errno.ENOTSUP) and (
                not WINDOWS or ex.errno != errno.EINVAL
            ):
                raise

        if not b64:
            zs = "{}\n{}".format(orig_name, suffix).encode("utf-8", "replace")
            zs = hashlib.sha512(zs).digest()[:12]
            b64 = base64.urlsafe_b64encode(zs).decode("utf-8")

        badlen = len(fname)
        while len(fname) >= badlen:
            if len(bname) < 8:
                raise ex

            if len(bname) > len(ext):
                # drop the last letter of the filename
                bname = bname[:-1]
            else:
                try:
                    # drop the leftmost sub-extension
                    _, ext = ext.split(".", 1)
                except:
                    # okay do the first letter then
                    ext = "." + ext[2:]

            fname = "{}~{}{}".format(bname, b64, ext)


class MultipartParser(object):
    def __init__(
        self, log_func: "NamedLogger", sr: Unrecv, http_headers: dict[str, str]
    ):
        self.sr = sr
        self.log = log_func
        self.headers = http_headers

        self.re_ctype = re.compile(r"^content-type: *([^; ]+)", re.IGNORECASE)
        self.re_cdisp = re.compile(r"^content-disposition: *([^; ]+)", re.IGNORECASE)
        self.re_cdisp_field = re.compile(
            r'^content-disposition:(?: *|.*; *)name="([^"]+)"', re.IGNORECASE
        )
        self.re_cdisp_file = re.compile(
            r'^content-disposition:(?: *|.*; *)filename="(.*)"', re.IGNORECASE
        )

        self.boundary = b""
        self.gen: Optional[
            Generator[
                tuple[str, Optional[str], Generator[bytes, None, None]], None, None
            ]
        ] = None

    def _read_header(self) -> tuple[str, Optional[str]]:
        """
        returns [fieldname, filename] after eating a block of multipart headers
        while doing a decent job at dealing with the absolute mess that is
        rfc1341/rfc1521/rfc2047/rfc2231/rfc2388/rfc6266/the-real-world
        (only the fallback non-js uploader relies on these filenames)
        """
        for ln in read_header(self.sr, 2, 2592000):
            self.log(ln)

            m = self.re_ctype.match(ln)
            if m:
                if m.group(1).lower() == "multipart/mixed":
                    # rfc-7578 overrides rfc-2388 so this is not-impl
                    # (opera >=9 <11.10 is the only thing i've ever seen use it)
                    raise Pebkac(
                        400,
                        "you can't use that browser to upload multiple files at once",
                    )

                continue

            # the only other header we care about is content-disposition
            m = self.re_cdisp.match(ln)
            if not m:
                continue

            if m.group(1).lower() != "form-data":
                raise Pebkac(400, "not form-data: {}".format(ln))

            try:
                field = self.re_cdisp_field.match(ln).group(1)  # type: ignore
            except:
                raise Pebkac(400, "missing field name: {}".format(ln))

            try:
                fn = self.re_cdisp_file.match(ln).group(1)  # type: ignore
            except:
                # this is not a file upload, we're done
                return field, None

            try:
                is_webkit = "applewebkit" in self.headers["user-agent"].lower()
            except:
                is_webkit = False

            # chromes ignore the spec and makes this real easy
            if is_webkit:
                # quotes become %22 but they don't escape the %
                # so unescaping the quotes could turn messi
                return field, fn.split('"')[0]

            # also ez if filename doesn't contain "
            if not fn.split('"')[0].endswith("\\"):
                return field, fn.split('"')[0]

            # this breaks on firefox uploads that contain \"
            # since firefox escapes " but forgets to escape \
            # so it'll truncate after the \
            ret = ""
            esc = False
            for ch in fn:
                if esc:
                    esc = False
                    if ch not in ['"', "\\"]:
                        ret += "\\"
                    ret += ch
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    break
                else:
                    ret += ch

            return field, ret

        raise Pebkac(400, "server expected a multipart header but you never sent one")

    def _read_data(self) -> Generator[bytes, None, None]:
        blen = len(self.boundary)
        bufsz = 32 * 1024
        while True:
            try:
                buf = self.sr.recv(bufsz)
            except:
                # abort: client disconnected
                raise Pebkac(400, "client d/c during multipart post")

            while True:
                ofs = buf.find(self.boundary)
                if ofs != -1:
                    self.sr.unrecv(buf[ofs + blen :])
                    yield buf[:ofs]
                    return

                d = len(buf) - blen
                if d > 0:
                    # buffer growing large; yield everything except
                    # the part at the end (maybe start of boundary)
                    yield buf[:d]
                    buf = buf[d:]

                # look for boundary near the end of the buffer
                n = 0
                for n in range(1, len(buf) + 1):
                    if not buf[-n:] in self.boundary:
                        n -= 1
                        break

                if n == 0 or not self.boundary.startswith(buf[-n:]):
                    # no boundary contents near the buffer edge
                    break

                if blen == n:
                    # EOF: found boundary
                    yield buf[:-n]
                    return

                try:
                    buf += self.sr.recv(bufsz)
                except:
                    # abort: client disconnected
                    raise Pebkac(400, "client d/c during multipart post")

            yield buf

    def _run_gen(
        self,
    ) -> Generator[tuple[str, Optional[str], Generator[bytes, None, None]], None, None]:
        """
        yields [fieldname, unsanitized_filename, fieldvalue]
        where fieldvalue yields chunks of data
        """
        run = True
        while run:
            fieldname, filename = self._read_header()
            yield (fieldname, filename, self._read_data())

            tail = self.sr.recv_ex(2, False)

            if tail == b"--":
                # EOF indicated by this immediately after final boundary
                tail = self.sr.recv_ex(2, False)
                run = False

            if tail != b"\r\n":
                t = "protocol error after field value: want b'\\r\\n', got {!r}"
                raise Pebkac(400, t.format(tail))

    def _read_value(self, iterable: Iterable[bytes], max_len: int) -> bytes:
        ret = b""
        for buf in iterable:
            ret += buf
            if len(ret) > max_len:
                raise Pebkac(400, "field length is too long")

        return ret

    def parse(self) -> None:
        # spec says there might be junk before the first boundary,
        # can't have the leading \r\n if that's not the case
        self.boundary = b"--" + get_boundary(self.headers).encode("utf-8")

        # discard junk before the first boundary
        for junk in self._read_data():
            self.log(
                "discarding preamble: [{}]".format(junk.decode("utf-8", "replace"))
            )

        # nice, now make it fast
        self.boundary = b"\r\n" + self.boundary
        self.gen = self._run_gen()

    def require(self, field_name: str, max_len: int) -> str:
        """
        returns the value of the next field in the multipart body,
        raises if the field name is not as expected
        """
        assert self.gen
        p_field, _, p_data = next(self.gen)
        if p_field != field_name:
            raise Pebkac(
                422, 'expected field "{}", got "{}"'.format(field_name, p_field)
            )

        return self._read_value(p_data, max_len).decode("utf-8", "surrogateescape")

    def drop(self) -> None:
        """discards the remaining multipart body"""
        assert self.gen
        for _, _, data in self.gen:
            for _ in data:
                pass


def get_boundary(headers: dict[str, str]) -> str:
    # boundaries contain a-z A-Z 0-9 ' ( ) + _ , - . / : = ?
    # (whitespace allowed except as the last char)
    ptn = r"^multipart/form-data *; *(.*; *)?boundary=([^;]+)"
    ct = headers["content-type"]
    m = re.match(ptn, ct, re.IGNORECASE)
    if not m:
        raise Pebkac(400, "invalid content-type for a multipart post: {}".format(ct))

    return m.group(2)


def read_header(sr: Unrecv, t_idle: int, t_tot: int) -> list[str]:
    t0 = time.time()
    ret = b""
    while True:
        if time.time() - t0 >= t_tot:
            return []

        try:
            ret += sr.recv(1024, t_idle // 2)
        except:
            if not ret:
                return []

            raise Pebkac(
                400,
                "protocol error while reading headers:\n"
                + ret.decode("utf-8", "replace"),
            )

        ofs = ret.find(b"\r\n\r\n")
        if ofs < 0:
            if len(ret) > 1024 * 64:
                raise Pebkac(400, "header 2big")
            else:
                continue

        if len(ret) > ofs + 4:
            sr.unrecv(ret[ofs + 4 :])

        return ret[:ofs].decode("utf-8", "surrogateescape").lstrip("\r\n").split("\r\n")


def rand_name(fdir: str, fn: str, rnd: int) -> str:
    ok = False
    try:
        ext = "." + fn.rsplit(".", 1)[1]
    except:
        ext = ""

    for extra in range(16):
        for _ in range(16):
            if ok:
                break

            nc = rnd + extra
            nb = int((6 + 6 * nc) / 8)
            zb = os.urandom(nb)
            zb = base64.urlsafe_b64encode(zb)
            fn = zb[:nc].decode("utf-8") + ext
            ok = not os.path.exists(fsenc(os.path.join(fdir, fn)))

    return fn


def gen_filekey(salt: str, fspath: str, fsize: int, inode: int) -> str:
    return base64.urlsafe_b64encode(
        hashlib.sha512(
            ("%s %s %s %s" % (salt, fspath, fsize, inode)).encode("utf-8", "replace")
        ).digest()
    ).decode("ascii")


def gen_filekey_dbg(
    salt: str,
    fspath: str,
    fsize: int,
    inode: int,
    log: "NamedLogger",
    log_ptn: Optional[Pattern[str]],
) -> str:
    ret = gen_filekey(salt, fspath, fsize, inode)

    assert log_ptn
    if log_ptn.search(fspath):
        try:
            import inspect

            ctx = ",".join(inspect.stack()[n].function for n in range(2, 5))
        except:
            ctx = ""

        p2 = "a"
        try:
            p2 = absreal(fspath)
            if p2 != fspath:
                raise Exception()
        except:
            t = "maybe wrong abspath for filekey;\norig: {}\nreal: {}"
            log(t.format(fspath, p2), 1)

        t = "fk({}) salt({}) size({}) inode({}) fspath({}) at({})"
        log(t.format(ret[:8], salt, fsize, inode, fspath, ctx), 5)

    return ret


def gencookie(k: str, v: str, r: str, tls: bool, dur: Optional[int]) -> str:
    v = v.replace("%", "%25").replace(";", "%3B")
    if dur:
        exp = formatdate(time.time() + dur, usegmt=True)
    else:
        exp = "Fri, 15 Aug 1997 01:00:00 GMT"

    return "{}={}; Path=/{}; Expires={}{}; SameSite=Lax".format(
        k, v, r, exp, "; Secure" if tls else ""
    )


def humansize(sz: float, terse: bool = False) -> str:
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if sz < 1024:
            break

        sz /= 1024.0

    ret = " ".join([str(sz)[:4].rstrip("."), unit])

    if not terse:
        return ret

    return ret.replace("iB", "").replace(" ", "")


def unhumanize(sz: str) -> int:
    try:
        return int(sz)
    except:
        pass

    mc = sz[-1:].lower()
    mi = {
        "k": 1024,
        "m": 1024 * 1024,
        "g": 1024 * 1024 * 1024,
        "t": 1024 * 1024 * 1024 * 1024,
    }.get(mc, 1)
    return int(float(sz[:-1]) * mi)


def get_spd(nbyte: int, t0: float, t: Optional[float] = None) -> str:
    if t is None:
        t = time.time()

    bps = nbyte / ((t - t0) + 0.001)
    s1 = humansize(nbyte).replace(" ", "\033[33m").replace("iB", "")
    s2 = humansize(bps).replace(" ", "\033[35m").replace("iB", "")
    return "{} \033[0m{}/s\033[0m".format(s1, s2)


def s2hms(s: float, optional_h: bool = False) -> str:
    s = int(s)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if not h and optional_h:
        return "{}:{:02}".format(m, s)

    return "{}:{:02}:{:02}".format(h, m, s)


def djoin(*paths: str) -> str:
    """joins without adding a trailing slash on blank args"""
    return os.path.join(*[x for x in paths if x])


def uncyg(path: str) -> str:
    if len(path) < 2 or not path.startswith("/"):
        return path

    if len(path) > 2 and path[2] != "/":
        return path

    return "%s:\\%s" % (path[1], path[3:])


def undot(path: str) -> str:
    ret: list[str] = []
    for node in path.split("/"):
        if node in ["", "."]:
            continue

        if node == "..":
            if ret:
                ret.pop()
            continue

        ret.append(node)

    return "/".join(ret)


def sanitize_fn(fn: str, ok: str, bad: list[str]) -> str:
    if "/" not in ok:
        fn = fn.replace("\\", "/").split("/")[-1]

    if fn.lower() in bad:
        fn = "_" + fn

    if ANYWIN:
        remap = [
            ["<", "＜"],
            [">", "＞"],
            [":", "："],
            ['"', "＂"],
            ["/", "／"],
            ["\\", "＼"],
            ["|", "｜"],
            ["?", "？"],
            ["*", "＊"],
        ]
        for a, b in [x for x in remap if x[0] not in ok]:
            fn = fn.replace(a, b)

        bad = ["con", "prn", "aux", "nul"]
        for n in range(1, 10):
            bad += ("com%s lpt%s" % (n, n)).split(" ")

        if fn.lower().split(".")[0] in bad:
            fn = "_" + fn

    return fn.strip()


def relchk(rp: str) -> str:
    if ANYWIN:
        if "\n" in rp or "\r" in rp:
            return "x\nx"

        p = re.sub(r'[\\:*?"<>|]', "", rp)
        if p != rp:
            return "[{}]".format(p)

    return ""


def absreal(fpath: str) -> str:
    try:
        return fsdec(os.path.abspath(os.path.realpath(afsenc(fpath))))
    except:
        if not WINDOWS:
            raise

        # cpython bug introduced in 3.8, still exists in 3.9.1,
        # some win7sp1 and win10:20H2 boxes cannot realpath a
        # networked drive letter such as b"n:" or b"n:\\"
        return os.path.abspath(os.path.realpath(fpath))


def u8safe(txt: str) -> str:
    try:
        return txt.encode("utf-8", "xmlcharrefreplace").decode("utf-8", "replace")
    except:
        return txt.encode("utf-8", "replace").decode("utf-8", "replace")


def exclude_dotfiles(filepaths: list[str]) -> list[str]:
    return [x for x in filepaths if not x.split("/")[-1].startswith(".")]


def ipnorm(ip: str) -> str:
    if ":" in ip:
        # assume /64 clients; drop 4 groups
        return IPv6Address(ip).exploded[:-20]

    return ip


def find_prefix(ips: list[str], netdevs: dict[str, Netdev]) -> list[str]:
    ret = []
    for ip in ips:
        hit = next((x for x in netdevs if x.startswith(ip + "/")), None)
        if hit:
            ret.append(hit)
    return ret


def html_escape(s: str, quot: bool = False, crlf: bool = False) -> str:
    """html.escape but also newlines"""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if quot:
        s = s.replace('"', "&quot;").replace("'", "&#x27;")
    if crlf:
        s = s.replace("\r", "&#13;").replace("\n", "&#10;")

    return s


def html_bescape(s: bytes, quot: bool = False, crlf: bool = False) -> bytes:
    """html.escape but bytestrings"""
    s = s.replace(b"&", b"&amp;").replace(b"<", b"&lt;").replace(b">", b"&gt;")
    if quot:
        s = s.replace(b'"', b"&quot;").replace(b"'", b"&#x27;")
    if crlf:
        s = s.replace(b"\r", b"&#13;").replace(b"\n", b"&#10;")

    return s


def _quotep2(txt: str) -> str:
    """url quoter which deals with bytes correctly"""
    btxt = w8enc(txt)
    quot = quote(btxt, safe=b"/")
    return w8dec(quot.replace(b" ", b"+"))


def _quotep3(txt: str) -> str:
    """url quoter which deals with bytes correctly"""
    btxt = w8enc(txt)
    quot = quote(btxt, safe=b"/").encode("utf-8")
    return w8dec(quot.replace(b" ", b"+"))


quotep = _quotep3 if not PY2 else _quotep2


def unquotep(txt: str) -> str:
    """url unquoter which deals with bytes correctly"""
    btxt = w8enc(txt)
    # btxt = btxt.replace(b"+", b" ")
    unq2 = unquote(btxt)
    return w8dec(unq2)


def vsplit(vpath: str) -> tuple[str, str]:
    if "/" not in vpath:
        return "", vpath

    return vpath.rsplit("/", 1)  # type: ignore


def vjoin(rd: str, fn: str) -> str:
    if rd and fn:
        return rd + "/" + fn
    else:
        return rd or fn


def _w8dec2(txt: bytes) -> str:
    """decodes filesystem-bytes to wtf8"""
    return surrogateescape.decodefilename(txt)


def _w8enc2(txt: str) -> bytes:
    """encodes wtf8 to filesystem-bytes"""
    return surrogateescape.encodefilename(txt)


def _w8dec3(txt: bytes) -> str:
    """decodes filesystem-bytes to wtf8"""
    return txt.decode(FS_ENCODING, "surrogateescape")


def _w8enc3(txt: str) -> bytes:
    """encodes wtf8 to filesystem-bytes"""
    return txt.encode(FS_ENCODING, "surrogateescape")


def _msdec(txt: bytes) -> str:
    ret = txt.decode(FS_ENCODING, "surrogateescape")
    return ret[4:] if ret.startswith("\\\\?\\") else ret


def _msaenc(txt: str) -> bytes:
    return txt.replace("/", "\\").encode(FS_ENCODING, "surrogateescape")


def _uncify(txt: str) -> str:
    txt = txt.replace("/", "\\")
    if ":" not in txt and not txt.startswith("\\\\"):
        txt = absreal(txt)

    return txt if txt.startswith("\\\\") else "\\\\?\\" + txt


def _msenc(txt: str) -> bytes:
    txt = txt.replace("/", "\\")
    if ":" not in txt and not txt.startswith("\\\\"):
        txt = absreal(txt)

    ret = txt.encode(FS_ENCODING, "surrogateescape")
    return ret if ret.startswith(b"\\\\") else b"\\\\?\\" + ret


w8dec = _w8dec3 if not PY2 else _w8dec2
w8enc = _w8enc3 if not PY2 else _w8enc2


def w8b64dec(txt: str) -> str:
    """decodes base64(filesystem-bytes) to wtf8"""
    return w8dec(base64.urlsafe_b64decode(txt.encode("ascii")))


def w8b64enc(txt: str) -> str:
    """encodes wtf8 to base64(filesystem-bytes)"""
    return base64.urlsafe_b64encode(w8enc(txt)).decode("ascii")


if not PY2 and WINDOWS:
    sfsenc = w8enc
    afsenc = _msaenc
    fsenc = _msenc
    fsdec = _msdec
    uncify = _uncify
elif not PY2 or not WINDOWS:
    fsenc = afsenc = sfsenc = w8enc
    fsdec = w8dec
    uncify = str
else:
    # moonrunes become \x3f with bytestrings,
    # losing mojibake support is worth
    def _not_actually_mbcs_enc(txt: str) -> bytes:
        return txt

    def _not_actually_mbcs_dec(txt: bytes) -> str:
        return txt

    fsenc = afsenc = sfsenc = _not_actually_mbcs_enc
    fsdec = _not_actually_mbcs_dec
    uncify = str


def s3enc(mem_cur: "sqlite3.Cursor", rd: str, fn: str) -> tuple[str, str]:
    ret: list[str] = []
    for v in [rd, fn]:
        try:
            mem_cur.execute("select * from a where b = ?", (v,))
            ret.append(v)
        except:
            ret.append("//" + w8b64enc(v))
            # self.log("mojien [{}] {}".format(v, ret[-1][2:]))

    return ret[0], ret[1]


def s3dec(rd: str, fn: str) -> tuple[str, str]:
    return (
        w8b64dec(rd[2:]) if rd.startswith("//") else rd,
        w8b64dec(fn[2:]) if fn.startswith("//") else fn,
    )


def db_ex_chk(log: "NamedLogger", ex: Exception, db_path: str) -> bool:
    if str(ex) != "database is locked":
        return False

    Daemon(lsof, "dbex", (log, db_path))
    return True


def lsof(log: "NamedLogger", abspath: str) -> None:
    try:
        rc, so, se = runcmd([b"lsof", b"-R", fsenc(abspath)], timeout=45)
        zs = (so.strip() + "\n" + se.strip()).strip()
        log("lsof {} = {}\n{}".format(abspath, rc, zs), 3)
    except:
        log("lsof failed; " + min_ex(), 3)


def atomic_move(usrc: str, udst: str) -> None:
    src = fsenc(usrc)
    dst = fsenc(udst)
    if not PY2:
        os.replace(src, dst)
    else:
        if os.path.exists(dst):
            os.unlink(dst)

        os.rename(src, dst)


def get_df(abspath: str) -> tuple[Optional[int], Optional[int]]:
    try:
        # some fuses misbehave
        if ANYWIN:
            bfree = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore
                ctypes.c_wchar_p(abspath), None, None, ctypes.pointer(bfree)
            )
            return (bfree.value, None)
        else:
            sv = os.statvfs(fsenc(abspath))
            free = sv.f_frsize * sv.f_bfree
            total = sv.f_frsize * sv.f_blocks
            return (free, total)
    except:
        return (None, None)


if not ANYWIN and not MACOS:

    def siocoutq(sck: socket.socket) -> int:
        # SIOCOUTQ^sockios.h == TIOCOUTQ^ioctl.h
        try:
            zb = fcntl.ioctl(sck.fileno(), termios.TIOCOUTQ, b"AAAA")
            return sunpack(b"I", zb)[0]  # type: ignore
        except:
            return 1

else:
    # macos: getsockopt(fd, SOL_SOCKET, SO_NWRITE, ...)
    # windows: TcpConnectionEstatsSendBuff

    def siocoutq(sck: socket.socket) -> int:
        return 1


def shut_socket(log: "NamedLogger", sck: socket.socket, timeout: int = 3) -> None:
    t0 = time.time()
    fd = sck.fileno()
    if fd == -1:
        sck.close()
        return

    try:
        sck.settimeout(timeout)
        sck.shutdown(socket.SHUT_WR)
        try:
            while time.time() - t0 < timeout:
                if not siocoutq(sck):
                    # kernel says tx queue empty, we good
                    break

                # on windows in particular, drain rx until client shuts
                if not sck.recv(32 * 1024):
                    break

            sck.shutdown(socket.SHUT_RDWR)
        except:
            pass
    except Exception as ex:
        log("shut({}): {}".format(fd, ex), "90")
    finally:
        td = time.time() - t0
        if td >= 1:
            log("shut({}) in {:.3f} sec".format(fd, td), "90")

        sck.close()


def read_socket(sr: Unrecv, total_size: int) -> Generator[bytes, None, None]:
    remains = total_size
    while remains > 0:
        bufsz = 32 * 1024
        if bufsz > remains:
            bufsz = remains

        try:
            buf = sr.recv(bufsz)
        except OSError:
            t = "client d/c during binary post after {} bytes, {} bytes remaining"
            raise Pebkac(400, t.format(total_size - remains, remains))

        remains -= len(buf)
        yield buf


def read_socket_unbounded(sr: Unrecv) -> Generator[bytes, None, None]:
    try:
        while True:
            yield sr.recv(32 * 1024)
    except:
        return


def read_socket_chunked(
    sr: Unrecv, log: Optional["NamedLogger"] = None
) -> Generator[bytes, None, None]:
    err = "upload aborted: expected chunk length, got [{}] |{}| instead"
    while True:
        buf = b""
        while b"\r" not in buf:
            try:
                buf += sr.recv(2)
                if len(buf) > 16:
                    raise Exception()
            except:
                err = err.format(buf.decode("utf-8", "replace"), len(buf))
                raise Pebkac(400, err)

        if not buf.endswith(b"\n"):
            sr.recv(1)

        try:
            chunklen = int(buf.rstrip(b"\r\n"), 16)
        except:
            err = err.format(buf.decode("utf-8", "replace"), len(buf))
            raise Pebkac(400, err)

        if chunklen == 0:
            x = sr.recv_ex(2, False)
            if x == b"\r\n":
                return

            t = "protocol error after final chunk: want b'\\r\\n', got {!r}"
            raise Pebkac(400, t.format(x))

        if log:
            log("receiving {} byte chunk".format(chunklen))

        for chunk in read_socket(sr, chunklen):
            yield chunk

        x = sr.recv_ex(2, False)
        if x != b"\r\n":
            t = "protocol error in chunk separator: want b'\\r\\n', got {!r}"
            raise Pebkac(400, t.format(x))


def list_ips() -> list[str]:
    from .stolen.ifaddr import get_adapters

    ret: set[str] = set()
    for nic in get_adapters():
        for ipo in nic.ips:
            if len(ipo.ip) < 7:
                ret.add(ipo.ip[0])  # ipv6 is (ip,0,0)
            else:
                ret.add(ipo.ip)

    return list(ret)


def yieldfile(fn: str) -> Generator[bytes, None, None]:
    with open(fsenc(fn), "rb", 512 * 1024) as f:
        while True:
            buf = f.read(64 * 1024)
            if not buf:
                break

            yield buf


def hashcopy(
    fin: Generator[bytes, None, None],
    fout: Union[typing.BinaryIO, typing.IO[Any]],
    slp: int = 0,
    max_sz: int = 0,
) -> tuple[int, str, str]:
    hashobj = hashlib.sha512()
    tlen = 0
    for buf in fin:
        tlen += len(buf)
        if max_sz and tlen > max_sz:
            continue

        hashobj.update(buf)
        fout.write(buf)
        if slp:
            time.sleep(slp)

    digest = hashobj.digest()[:33]
    digest_b64 = base64.urlsafe_b64encode(digest).decode("utf-8")

    return tlen, hashobj.hexdigest(), digest_b64


def sendfile_py(
    log: "NamedLogger",
    lower: int,
    upper: int,
    f: typing.BinaryIO,
    s: socket.socket,
    bufsz: int,
    slp: int,
) -> int:
    remains = upper - lower
    f.seek(lower)
    while remains > 0:
        if slp:
            time.sleep(slp)

        buf = f.read(min(bufsz, remains))
        if not buf:
            return remains

        try:
            s.sendall(buf)
            remains -= len(buf)
        except:
            return remains

    return 0


def sendfile_kern(
    log: "NamedLogger",
    lower: int,
    upper: int,
    f: typing.BinaryIO,
    s: socket.socket,
    bufsz: int,
    slp: int,
) -> int:
    out_fd = s.fileno()
    in_fd = f.fileno()
    ofs = lower
    stuck = 0.0
    while ofs < upper:
        stuck = stuck or time.time()
        try:
            req = min(2 ** 30, upper - ofs)
            select.select([], [out_fd], [], 10)
            n = os.sendfile(out_fd, in_fd, ofs, req)
            stuck = 0
        except OSError as ex:
            # client stopped reading; do another select
            d = time.time() - stuck
            if d < 3600 and ex.errno == errno.EWOULDBLOCK:
                continue

            n = 0
        except Exception as ex:
            n = 0
            d = time.time() - stuck
            log("sendfile failed after {:.3f} sec: {!r}".format(d, ex))

        if n <= 0:
            return upper - ofs

        ofs += n
        # print("sendfile: ok, sent {} now, {} total, {} remains".format(n, ofs - lower, upper - ofs))

    return 0


def statdir(
    logger: Optional["RootLogger"], scandir: bool, lstat: bool, top: str
) -> Generator[tuple[str, os.stat_result], None, None]:
    if lstat and ANYWIN:
        lstat = False

    if lstat and (PY2 or os.stat not in os.supports_follow_symlinks):
        scandir = False

    src = "statdir"
    try:
        btop = fsenc(top)
        if scandir and hasattr(os, "scandir"):
            src = "scandir"
            with os.scandir(btop) as dh:
                for fh in dh:
                    try:
                        yield (fsdec(fh.name), fh.stat(follow_symlinks=not lstat))
                    except Exception as ex:
                        if not logger:
                            continue

                        logger(src, "[s] {} @ {}".format(repr(ex), fsdec(fh.path)), 6)
        else:
            src = "listdir"
            fun: Any = os.lstat if lstat else os.stat
            for name in os.listdir(btop):
                abspath = os.path.join(btop, name)
                try:
                    yield (fsdec(name), fun(abspath))
                except Exception as ex:
                    if not logger:
                        continue

                    logger(src, "[s] {} @ {}".format(repr(ex), fsdec(abspath)), 6)

    except Exception as ex:
        t = "{} @ {}".format(repr(ex), top)
        if logger:
            logger(src, t, 1)
        else:
            print(t)


def rmdirs(
    logger: "RootLogger", scandir: bool, lstat: bool, top: str, depth: int
) -> tuple[list[str], list[str]]:
    """rmdir all descendants, then self"""
    if not os.path.isdir(fsenc(top)):
        top = os.path.dirname(top)
        depth -= 1

    stats = statdir(logger, scandir, lstat, top)
    dirs = [x[0] for x in stats if stat.S_ISDIR(x[1].st_mode)]
    dirs = [os.path.join(top, x) for x in dirs]
    ok = []
    ng = []
    for d in reversed(dirs):
        a, b = rmdirs(logger, scandir, lstat, d, depth + 1)
        ok += a
        ng += b

    if depth:
        try:
            os.rmdir(fsenc(top))
            ok.append(top)
        except:
            ng.append(top)

    return ok, ng


def rmdirs_up(top: str, stop: str) -> tuple[list[str], list[str]]:
    """rmdir on self, then all parents"""
    if top == stop:
        return [], [top]

    try:
        os.rmdir(fsenc(top))
    except:
        return [], [top]

    par = os.path.dirname(top)
    if not par or par == stop:
        return [top], []

    ok, ng = rmdirs_up(par, stop)
    return [top] + ok, ng


def unescape_cookie(orig: str) -> str:
    # mw=idk; doot=qwe%2Crty%3Basd+fgh%2Bjkl%25zxc%26vbn  # qwe,rty;asd fgh+jkl%zxc&vbn
    ret = ""
    esc = ""
    for ch in orig:
        if ch == "%":
            if len(esc) > 0:
                ret += esc
            esc = ch

        elif len(esc) > 0:
            esc += ch
            if len(esc) == 3:
                try:
                    ret += chr(int(esc[1:], 16))
                except:
                    ret += esc
                esc = ""

        else:
            ret += ch

    if len(esc) > 0:
        ret += esc

    return ret


def guess_mime(url: str, fallback: str = "application/octet-stream") -> str:
    try:
        _, ext = url.rsplit(".", 1)
    except:
        return fallback

    ret = MIMES.get(ext)

    if not ret:
        x = mimetypes.guess_type(url)
        ret = "application/{}".format(x[1]) if x[1] else x[0]

    if not ret:
        ret = fallback

    if ";" not in ret:
        if ret.startswith("text/") or ret.endswith("/javascript"):
            ret += "; charset=utf-8"

    return ret


def getalive(pids: list[int], pgid: int) -> list[int]:
    alive = []
    for pid in pids:
        try:
            if pgid:
                # check if still one of ours
                if os.getpgid(pid) == pgid:
                    alive.append(pid)
            else:
                # windows doesn't have pgroups; assume
                psutil.Process(pid)
                alive.append(pid)
        except:
            pass

    return alive


def killtree(root: int) -> None:
    """still racy but i tried"""
    try:
        # limit the damage where possible (unixes)
        pgid = os.getpgid(os.getpid())
    except:
        pgid = 0

    if HAVE_PSUTIL:
        pids = [root]
        parent = psutil.Process(root)
        for child in parent.children(recursive=True):
            pids.append(child.pid)
            child.terminate()
        parent.terminate()
        parent = None
    elif pgid:
        # linux-only
        pids = []
        chk = [root]
        while chk:
            pid = chk[0]
            chk = chk[1:]
            pids.append(pid)
            _, t, _ = runcmd(["pgrep", "-P", str(pid)])
            chk += [int(x) for x in t.strip().split("\n") if x]

        pids = getalive(pids, pgid)  # filter to our pgroup
        for pid in pids:
            os.kill(pid, signal.SIGTERM)
    else:
        # windows gets minimal effort sorry
        os.kill(root, signal.SIGTERM)
        return

    for n in range(10):
        time.sleep(0.1)
        pids = getalive(pids, pgid)
        if not pids or n > 3 and pids == [root]:
            break

    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except:
            pass


def runcmd(
    argv: Union[list[bytes], list[str]], timeout: Optional[float] = None, **ka: Any
) -> tuple[int, str, str]:
    kill = ka.pop("kill", "t")  # [t]ree [m]ain [n]one
    capture = ka.pop("capture", 3)  # 0=none 1=stdout 2=stderr 3=both

    sin: Optional[bytes] = ka.pop("sin", None)
    if sin:
        ka["stdin"] = sp.PIPE

    cout = sp.PIPE if capture in [1, 3] else None
    cerr = sp.PIPE if capture in [2, 3] else None
    bout: bytes
    berr: bytes

    p = sp.Popen(argv, stdout=cout, stderr=cerr, **ka)
    if not timeout or PY2:
        bout, berr = p.communicate(sin)
    else:
        try:
            bout, berr = p.communicate(sin, timeout=timeout)
        except sp.TimeoutExpired:
            if kill == "n":
                return -18, "", ""  # SIGCONT; leave it be
            elif kill == "m":
                p.kill()
            else:
                killtree(p.pid)

            try:
                bout, berr = p.communicate(timeout=1)
            except:
                bout = b""
                berr = b""

    stdout = bout.decode("utf-8", "replace") if cout else ""
    stderr = berr.decode("utf-8", "replace") if cerr else ""

    rc: int = p.returncode
    if rc is None:
        rc = -14  # SIGALRM; failed to kill

    return rc, stdout, stderr


def chkcmd(argv: Union[list[bytes], list[str]], **ka: Any) -> tuple[str, str]:
    ok, sout, serr = runcmd(argv, **ka)
    if ok != 0:
        retchk(ok, argv, serr)
        raise Exception(serr)

    return sout, serr


def mchkcmd(argv: Union[list[bytes], list[str]], timeout: float = 10) -> None:
    if PY2:
        with open(os.devnull, "wb") as f:
            rv = sp.call(argv, stdout=f, stderr=f)
    else:
        rv = sp.call(argv, stdout=sp.DEVNULL, stderr=sp.DEVNULL, timeout=timeout)

    if rv:
        raise sp.CalledProcessError(rv, (argv[0], b"...", argv[-1]))


def retchk(
    rc: int,
    cmd: Union[list[bytes], list[str]],
    serr: str,
    logger: Optional["NamedLogger"] = None,
    color: Union[int, str] = 0,
    verbose: bool = False,
) -> None:
    if rc < 0:
        rc = 128 - rc

    if not rc or rc < 126 and not verbose:
        return

    s = None
    if rc > 128:
        try:
            s = str(signal.Signals(rc - 128))
        except:
            pass
    elif rc == 126:
        s = "invalid program"
    elif rc == 127:
        s = "program not found"
    elif verbose:
        s = "unknown"
    else:
        s = "invalid retcode"

    if s:
        t = "{} <{}>".format(rc, s)
    else:
        t = str(rc)

    try:
        c = " ".join([fsdec(x) for x in cmd])  # type: ignore
    except:
        c = str(cmd)

    t = "error {} from [{}]".format(t, c)
    if serr:
        t += "\n" + serr

    if logger:
        logger(t, color)
    else:
        raise Exception(t)


def _parsehook(
    log: Optional["NamedLogger"], cmd: str
) -> tuple[bool, bool, bool, float, dict[str, Any], str]:
    chk = False
    fork = False
    jtxt = False
    wait = 0.0
    tout = 0.0
    kill = "t"
    cap = 0
    ocmd = cmd
    while "," in cmd[:6]:
        arg, cmd = cmd.split(",", 1)
        if arg == "c":
            chk = True
        elif arg == "f":
            fork = True
        elif arg == "j":
            jtxt = True
        elif arg.startswith("w"):
            wait = float(arg[1:])
        elif arg.startswith("t"):
            tout = float(arg[1:])
        elif arg.startswith("c"):
            cap = int(arg[1:])  # 0=none 1=stdout 2=stderr 3=both
        elif arg.startswith("k"):
            kill = arg[1:]  # [t]ree [m]ain [n]one
        elif arg.startswith("i"):
            pass
        else:
            t = "hook: invalid flag {} in {}"
            (log or print)(t.format(arg, ocmd))

    env = os.environ.copy()
    try:
        if EXE:
            raise Exception()

        pypath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        zsl = [str(pypath)] + [str(x) for x in sys.path if x]
        pypath = str(os.pathsep.join(zsl))
        env["PYTHONPATH"] = pypath
    except:
        if not EXE:
            raise

    sp_ka = {
        "env": env,
        "timeout": tout,
        "kill": kill,
        "capture": cap,
    }

    if cmd.startswith("~"):
        cmd = os.path.expanduser(cmd)

    return chk, fork, jtxt, wait, sp_ka, cmd


def runihook(
    log: Optional["NamedLogger"],
    cmd: str,
    vol: "VFS",
    ups: list[tuple[str, int, int, str, str, str, int]],
) -> bool:
    ocmd = cmd
    chk, fork, jtxt, wait, sp_ka, cmd = _parsehook(log, cmd)
    bcmd = [sfsenc(cmd)]
    if cmd.endswith(".py"):
        bcmd = [sfsenc(pybin)] + bcmd

    vps = [vjoin(*list(s3dec(x[3], x[4]))) for x in ups]
    aps = [djoin(vol.realpath, x) for x in vps]
    if jtxt:
        # 0w 1mt 2sz 3rd 4fn 5ip 6at
        ja = [
            {
                "ap": uncify(ap),  # utf8 for json
                "vp": vp,
                "wark": x[0][:16],
                "mt": x[1],
                "sz": x[2],
                "ip": x[5],
                "at": x[6],
            }
            for x, vp, ap in zip(ups, vps, aps)
        ]
        sp_ka["sin"] = json.dumps(ja).encode("utf-8", "replace")
    else:
        sp_ka["sin"] = b"\n".join(fsenc(x) for x in aps)

    t0 = time.time()
    if fork:
        Daemon(runcmd, ocmd, [bcmd], ka=sp_ka)
    else:
        rc, v, err = runcmd(bcmd, **sp_ka)  # type: ignore
        if chk and rc:
            retchk(rc, bcmd, err, log, 5)
            return False

    wait -= time.time() - t0
    if wait > 0:
        time.sleep(wait)

    return True


def _runhook(
    log: Optional["NamedLogger"],
    cmd: str,
    ap: str,
    vp: str,
    host: str,
    uname: str,
    mt: float,
    sz: int,
    ip: str,
    at: float,
    txt: str,
) -> bool:
    ocmd = cmd
    chk, fork, jtxt, wait, sp_ka, cmd = _parsehook(log, cmd)
    if jtxt:
        ja = {
            "ap": ap,
            "vp": vp,
            "mt": mt,
            "sz": sz,
            "ip": ip,
            "at": at or time.time(),
            "host": host,
            "user": uname,
            "txt": txt,
        }
        arg = json.dumps(ja)
    else:
        arg = txt or ap

    acmd = [cmd, arg]
    if cmd.endswith(".py"):
        acmd = [pybin] + acmd

    bcmd = [fsenc(x) if x == ap else sfsenc(x) for x in acmd]

    t0 = time.time()
    if fork:
        Daemon(runcmd, ocmd, [bcmd], ka=sp_ka)
    else:
        rc, v, err = runcmd(bcmd, **sp_ka)  # type: ignore
        if chk and rc:
            retchk(rc, bcmd, err, log, 5)
            return False

    wait -= time.time() - t0
    if wait > 0:
        time.sleep(wait)

    return True


def runhook(
    log: Optional["NamedLogger"],
    cmds: list[str],
    ap: str,
    vp: str,
    host: str,
    uname: str,
    mt: float,
    sz: int,
    ip: str,
    at: float,
    txt: str,
) -> bool:
    vp = vp.replace("\\", "/")
    for cmd in cmds:
        try:
            if not _runhook(log, cmd, ap, vp, host, uname, mt, sz, ip, at, txt):
                return False
        except Exception as ex:
            (log or print)("hook: {}".format(ex))
            if ",c," in "," + cmd:
                return False
            break

    return True


def loadpy(ap: str, hot: bool) -> Any:
    """
    a nice can of worms capable of causing all sorts of bugs
    depending on what other inconveniently named files happen
    to be in the same folder
    """
    if ap.startswith("~"):
        ap = os.path.expanduser(ap)

    mdir, mfile = os.path.split(absreal(ap))
    mname = mfile.rsplit(".", 1)[0]
    sys.path.insert(0, mdir)

    if PY2:
        mod = __import__(mname)
        if hot:
            reload(mod)
    else:
        import importlib

        mod = importlib.import_module(mname)
        if hot:
            importlib.reload(mod)

    sys.path.remove(mdir)
    return mod


def gzip_orig_sz(fn: str) -> int:
    with open(fsenc(fn), "rb") as f:
        f.seek(-4, 2)
        rv = f.read(4)
        return sunpack(b"I", rv)[0]  # type: ignore


def align_tab(lines: list[str]) -> list[str]:
    rows = []
    ncols = 0
    for ln in lines:
        row = [x for x in ln.split(" ") if x]
        ncols = max(ncols, len(row))
        rows.append(row)

    lens = [0] * ncols
    for row in rows:
        for n, col in enumerate(row):
            lens[n] = max(lens[n], len(col))

    return ["".join(x.ljust(y + 2) for x, y in zip(row, lens)) for row in rows]


def visual_length(txt: str) -> int:
    # from r0c
    eoc = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    clen = 0
    pend = None
    counting = True
    for ch in txt:

        # escape sequences can never contain ESC;
        # treat pend as regular text if so
        if ch == "\033" and pend:
            clen += len(pend)
            counting = True
            pend = None

        if not counting:
            if ch in eoc:
                counting = True
        else:
            if pend:
                pend += ch
                if pend.startswith("\033["):
                    counting = False
                else:
                    clen += len(pend)
                    counting = True
                pend = None
            else:
                if ch == "\033":
                    pend = "{0}".format(ch)
                else:
                    co = ord(ch)
                    # the safe parts of latin1 and cp437 (no greek stuff)
                    if (
                        co < 0x100  # ascii + lower half of latin1
                        or (co >= 0x2500 and co <= 0x25A0)  # box drawings
                        or (co >= 0x2800 and co <= 0x28FF)  # braille
                    ):
                        clen += 1
                    else:
                        # assume moonrunes or other double-width
                        clen += 2
    return clen


def wrap(txt: str, maxlen: int, maxlen2: int) -> list[str]:
    # from r0c
    words = re.sub(r"([, ])", r"\1\n", txt.rstrip()).split("\n")
    pad = maxlen - maxlen2
    ret = []
    for word in words:
        if len(word) * 2 < maxlen or visual_length(word) < maxlen:
            ret.append(word)
        else:
            while visual_length(word) >= maxlen:
                ret.append(word[: maxlen - 1] + "-")
                word = word[maxlen - 1 :]
            if word:
                ret.append(word)

    words = ret
    ret = []
    ln = ""
    spent = 0
    for word in words:
        wl = visual_length(word)
        if spent + wl > maxlen:
            ret.append(ln)
            maxlen = maxlen2
            spent = 0
            ln = " " * pad
        ln += word
        spent += wl
    if ln:
        ret.append(ln)

    return ret


def termsize() -> tuple[int, int]:
    # from hashwalk
    env = os.environ

    def ioctl_GWINSZ(fd: int) -> Optional[tuple[int, int]]:
        try:
            cr = sunpack(b"hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, b"AAAA"))
            return cr[::-1]
        except:
            return None

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass

    try:
        return cr or (int(env["COLUMNS"]), int(env["LINES"]))
    except:
        return 80, 25


def hidedir(dp) -> None:
    if ANYWIN:
        try:
            k32 = ctypes.WinDLL("kernel32")
            attrs = k32.GetFileAttributesW(dp)
            if attrs >= 0:
                k32.SetFileAttributesW(dp, attrs | 2)
        except:
            pass


class Pebkac(Exception):
    def __init__(self, code: int, msg: Optional[str] = None) -> None:
        super(Pebkac, self).__init__(msg or HTTPCODE[code])
        self.code = code

    def __repr__(self) -> str:
        return "Pebkac({}, {})".format(self.code, repr(self.args))

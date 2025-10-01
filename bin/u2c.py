#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

S_VERSION = "2.13"
S_BUILD_DT = "2025-09-05"

"""
u2c.py: upload to copyparty
2021, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/u2c.py

- dependencies: no
- supports python 2.6, 2.7, and 3.3 through 3.14
- if something breaks just try again and it'll autoresume
"""

import atexit
import base64
import binascii
import datetime
import hashlib
import json
import math
import os
import platform
import re
import signal
import socket
import stat
import sys
import threading
import time

EXE = bool(getattr(sys, "frozen", False))

try:
    import argparse
except:
    m = "\n  ERROR: need 'argparse'; download it here:\n   https://github.com/ThomasWaldmann/argparse/raw/master/argparse.py\n"
    print(m)
    raise


PY2 = sys.version_info < (3,)
PY27 = sys.version_info > (2, 7) and PY2
PY37 = sys.version_info > (3, 7)
if PY2:
    import httplib as http_client
    from Queue import Queue
    from urllib import quote, unquote
    from urlparse import urlsplit, urlunsplit

    sys.dont_write_bytecode = True
    bytes = str
    files_decoder = lambda s: unicode(s, "utf8")
else:
    from urllib.parse import quote_from_bytes as quote
    from urllib.parse import unquote_to_bytes as unquote
    from urllib.parse import urlsplit, urlunsplit

    import http.client as http_client
    from queue import Queue

    unicode = str
    files_decoder = unicode


WTF8 = "replace" if PY2 else "surrogateescape"

VT100 = platform.system() != "Windows"


try:
    UTC = datetime.timezone.utc
except:
    TD_ZERO = datetime.timedelta(0)

    class _UTC(datetime.tzinfo):
        def utcoffset(self, dt):
            return TD_ZERO

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return TD_ZERO

    UTC = _UTC()


try:
    _b64etl = bytes.maketrans(b"+/", b"-_")

    def ub64enc(bs):
        x = binascii.b2a_base64(bs, newline=False)
        return x.translate(_b64etl)

    ub64enc(b"a")
except:
    ub64enc = base64.urlsafe_b64encode


class BadAuth(Exception):
    pass


class Daemon(threading.Thread):
    def __init__(self, target, name=None, a=None):
        threading.Thread.__init__(self, name=name)
        self.a = a or ()
        self.fun = target
        self.daemon = True
        self.start()

    def run(self):
        try:
            signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGINT, signal.SIGTERM])
        except:
            pass

        self.fun(*self.a)


class HSQueue(Queue):
    def _init(self, maxsize):
        from collections import deque

        self.q = deque()

    def _qsize(self):
        return len(self.q)

    def _put(self, item):
        if item and item.nhs:
            self.q.appendleft(item)
        else:
            self.q.append(item)

    def _get(self):
        return self.q.popleft()


class HCli(object):
    def __init__(self, ar):
        self.ar = ar
        url = urlsplit(ar.url)
        tls = url.scheme.lower() == "https"
        try:
            addr, port = url.netloc.split(":")
        except:
            addr = url.netloc
            port = 443 if tls else 80

        self.addr = addr
        self.port = int(port)
        self.tls = tls
        self.verify = ar.te or not ar.td
        self.conns = []
        self.hconns = []
        if tls:
            import ssl

            if not self.verify:
                self.ctx = ssl._create_unverified_context()
            elif self.verify is True:
                self.ctx = None
            else:
                self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                self.ctx.load_verify_locations(self.verify)

        self.base_hdrs = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Host": url.netloc,
            "Origin": self.ar.burl,
            "User-Agent": "u2c/%s" % (S_VERSION,),
        }

    def _connect(self, timeout):
        args = {}
        if PY37:
            args["blocksize"] = 1048576

        if not self.tls:
            C = http_client.HTTPConnection
        else:
            C = http_client.HTTPSConnection
            if self.ctx:
                args = {"context": self.ctx}

        return C(self.addr, self.port, timeout=timeout, **args)

    def req(self, meth, vpath, hdrs, body=None, ctype=None):
        now = time.time()

        hdrs.update(self.base_hdrs)
        if self.ar.a:
            hdrs["PW"] = self.ar.a
        if ctype:
            hdrs["Content-Type"] = ctype
        if meth == "POST" and CLEN not in hdrs:
            hdrs[CLEN] = (
                0 if not body else body.len if hasattr(body, "len") else len(body)
            )

        # large timeout for handshakes (safededup)
        conns = self.hconns if ctype == MJ else self.conns
        while conns and self.ar.cxp < now - conns[0][0]:
            conns.pop(0)[1].close()
        c = conns.pop()[1] if conns else self._connect(999 if ctype == MJ else 128)
        try:
            c.request(meth, vpath, body, hdrs)
            if PY27:
                rsp = c.getresponse(buffering=True)
            else:
                rsp = c.getresponse()

            data = rsp.read()
            conns.append((time.time(), c))
            return rsp.status, data.decode("utf-8")
        except http_client.BadStatusLine:
            if self.ar.cxp > 4:
                t = "\nWARNING: --cxp probably too high; reducing from %d to 4"
                print(t % (self.ar.cxp,))
                self.ar.cxp = 4
            c.close()
            raise
        except:
            c.close()
            raise


MJ = "application/json"
MO = "application/octet-stream"
CLEN = "Content-Length"

web = None  # type: HCli

links = []  # type: list[str]
linkmtx = threading.Lock()
linkfile = None


class File(object):
    """an up2k upload task; represents a single file"""

    def __init__(self, top, rel, size, lmod):
        self.top = top  # type: bytes
        self.rel = rel.replace(b"\\", b"/")  # type: bytes
        self.size = size  # type: int
        self.lmod = lmod  # type: float

        self.abs = os.path.join(top, rel)  # type: bytes
        self.name = self.rel.split(b"/")[-1].decode("utf-8", WTF8)  # type: str

        # set by get_hashlist
        self.cids = []  # type: list[tuple[str, int, int]]  # [ hash, ofs, sz ]
        self.kchunks = {}  # type: dict[str, tuple[int, int]]  # hash: [ ofs, sz ]
        self.t_hash = 0.0  # type: float

        # set by handshake
        self.recheck = False  # duplicate; redo handshake after all files done
        self.ucids = []  # type: list[str]  # chunks which need to be uploaded
        self.wark = ""  # type: str
        self.url = ""  # type: str
        self.nhs = 0  # type: int

        # set by upload
        self.t0_up = 0.0  # type: float
        self.t1_up = 0.0  # type: float
        self.nojoin = 0  # type: int
        self.up_b = 0  # type: int
        self.up_c = 0  # type: int
        self.cd = 0  # type: int


class FileSlice(object):
    """file-like object providing a fixed window into a file"""

    def __init__(self, file, cids):
        # type: (File, str) -> None

        self.file = file
        self.cids = cids

        self.car, tlen = file.kchunks[cids[0]]
        for cid in cids[1:]:
            ofs, clen = file.kchunks[cid]
            if ofs != self.car + tlen:
                raise Exception(9)
            tlen += clen

        self.len = self.tlen = tlen
        self.cdr = self.car + self.len
        self.ofs = 0  # type: int

        self.f = None
        self.seek = self._seek0
        self.read = self._read0

    def subchunk(self, maxsz, nth):
        if self.tlen <= maxsz:
            return -1

        if not nth:
            self.car0 = self.car
            self.cdr0 = self.cdr

        self.car = self.car0 + maxsz * nth
        if self.car >= self.cdr0:
            return -2

        self.cdr = self.car + min(self.cdr0 - self.car, maxsz)
        self.len = self.cdr - self.car
        self.seek(0)
        return nth

    def unsub(self):
        self.car = self.car0
        self.cdr = self.cdr0
        self.len = self.tlen

    def _open(self):
        self.seek = self._seek
        self.read = self._read

        self.f = open(self.file.abs, "rb", 512 * 1024)
        self.f.seek(self.car)

        # https://stackoverflow.com/questions/4359495/what-is-exactly-a-file-like-object-in-python
        # IOBase, RawIOBase, BufferedIOBase
        funs = "close closed __enter__ __exit__ __iter__ isatty __next__ readable seekable writable"
        try:
            for fun in funs.split():
                setattr(self, fun, getattr(self.f, fun))
        except:
            pass  # py27 probably

    def close(self, *a, **ka):
        return  # until _open

    def tell(self):
        return self.ofs

    def _seek(self, ofs, wh=0):
        assert self.f  # !rm

        if wh == 1:
            ofs = self.ofs + ofs
        elif wh == 2:
            ofs = self.len + ofs  # provided ofs is negative

        if ofs < 0:
            ofs = 0
        elif ofs >= self.len:
            ofs = self.len - 1

        self.ofs = ofs
        self.f.seek(self.car + ofs)

    def _read(self, sz):
        assert self.f  # !rm

        sz = min(sz, self.len - self.ofs)
        ret = self.f.read(sz)
        self.ofs += len(ret)
        return ret

    def _seek0(self, ofs, wh=0):
        self._open()
        return self.seek(ofs, wh)

    def _read0(self, sz):
        self._open()
        return self.read(sz)


class MTHash(object):
    def __init__(self, cores):
        self.f = None
        self.sz = 0
        self.csz = 0
        self.omutex = threading.Lock()
        self.imutex = threading.Lock()
        self.work_q = Queue()
        self.done_q = Queue()
        self.thrs = []
        for _ in range(cores):
            self.thrs.append(Daemon(self.worker))

    def hash(self, f, fsz, chunksz, pcb=None, pcb_opaque=None):
        with self.omutex:
            self.f = f
            self.sz = fsz
            self.csz = chunksz

            chunks = {}
            nchunks = int(math.ceil(fsz / chunksz))
            for nch in range(nchunks):
                self.work_q.put(nch)

            ex = ""
            for nch in range(nchunks):
                qe = self.done_q.get()
                try:
                    nch, dig, ofs, csz = qe
                    chunks[nch] = [dig, ofs, csz]
                except:
                    ex = ex or qe

                if pcb:
                    pcb(pcb_opaque, chunksz * nch)

            if ex:
                raise Exception(ex)

            ret = []
            for n in range(nchunks):
                ret.append(chunks[n])

            self.f = None
            self.csz = 0
            self.sz = 0
            return ret

    def worker(self):
        while True:
            ofs = self.work_q.get()
            try:
                v = self.hash_at(ofs)
            except Exception as ex:
                v = str(ex)

            self.done_q.put(v)

    def hash_at(self, nch):
        f = self.f
        assert f
        ofs = ofs0 = nch * self.csz
        hashobj = hashlib.sha512()
        chunk_sz = chunk_rem = min(self.csz, self.sz - ofs)
        while chunk_rem > 0:
            with self.imutex:
                f.seek(ofs)
                buf = f.read(min(chunk_rem, 1024 * 1024 * 12))

            if not buf:
                raise Exception("EOF at " + str(ofs))

            hashobj.update(buf)
            chunk_rem -= len(buf)
            ofs += len(buf)

        digest = ub64enc(hashobj.digest()[:33]).decode("utf-8")
        return nch, digest, ofs0, chunk_sz


_print = print


def safe_print(*a, **ka):
    ka["end"] = ""
    zs = " ".join([unicode(x) for x in a])
    _print(zs + "\n", **ka)


def eprint(*a, **ka):
    ka["file"] = sys.stderr
    ka["end"] = ""
    if not PY2:
        ka["flush"] = True

    _print(*a, **ka)
    if PY2 or not VT100:
        sys.stderr.flush()


def flushing_print(*a, **ka):
    try:
        safe_print(*a, **ka)
    except:
        v = " ".join(str(x) for x in a)
        v = v.encode("ascii", "replace").decode("ascii")
        safe_print(v, **ka)

    if "flush" not in ka:
        sys.stdout.flush()


print = safe_print if VT100 else flushing_print


def termsize():
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import struct
            import termios

            r = struct.unpack(b"hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, b"AAAA"))
            return r[::-1]
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


class CTermsize(object):
    def __init__(self):
        self.ev = False
        self.margin = None
        self.g = None
        self.w, self.h = termsize()

        try:
            signal.signal(signal.SIGWINCH, self.ev_sig)
        except:
            return

        Daemon(self.worker)

    def worker(self):
        while True:
            time.sleep(0.5)
            if not self.ev:
                continue

            self.ev = False
            self.w, self.h = termsize()

            if self.margin is not None:
                self.scroll_region(self.margin)

    def ev_sig(self, *a, **ka):
        self.ev = True

    def scroll_region(self, margin):
        self.margin = margin
        if margin is None:
            self.g = None
            eprint("\033[s\033[r\033[u")
        else:
            self.g = 1 + self.h - margin
            t = "%s\033[%dA" % ("\n" * margin, margin)
            eprint("%s\033[s\033[1;%dr\033[u" % (t, self.g - 1))


ss = CTermsize()


def undns(url):
    usp = urlsplit(url)
    hn = usp.hostname
    gai = None
    eprint("resolving host [%s] ..." % (hn,))
    try:
        gai = socket.getaddrinfo(hn, None)
        hn = gai[0][4][0]
    except KeyboardInterrupt:
        raise
    except:
        t = "\n\033[31mfailed to resolve upload destination host;\033[0m\ngai=%r\n"
        eprint(t % (gai,))
        raise

    if usp.port:
        hn = "%s:%s" % (hn, usp.port)
    if usp.username or usp.password:
        hn = "%s:%s@%s" % (usp.username, usp.password, hn)

    usp = usp._replace(netloc=hn)
    url = urlunsplit(usp)
    eprint(" %s\n" % (url,))
    return url


def _scd(err, top):
    """non-recursive listing of directory contents, along with stat() info"""
    top_ = os.path.join(top, b"")
    with os.scandir(top) as dh:
        for fh in dh:
            abspath = top_ + fh.name
            try:
                yield [abspath, fh.stat()]
            except Exception as ex:
                err.append((abspath, str(ex)))


def _lsd(err, top):
    """non-recursive listing of directory contents, along with stat() info"""
    top_ = os.path.join(top, b"")
    for name in os.listdir(top):
        abspath = top_ + name
        try:
            yield [abspath, os.stat(abspath)]
        except Exception as ex:
            err.append((abspath, str(ex)))


if hasattr(os, "scandir") and sys.version_info > (3, 6):
    statdir = _scd
else:
    statdir = _lsd


def walkdir(err, top, excl, seen):
    """recursive statdir"""
    atop = os.path.abspath(os.path.realpath(top))
    if atop in seen:
        err.append((top, "recursive-symlink"))
        return

    seen = seen[:] + [atop]
    for ap, inf in sorted(statdir(err, top)):
        if excl.match(ap):
            continue
        if stat.S_ISDIR(inf.st_mode):
            yield ap, inf
            try:
                for x in walkdir(err, ap, excl, seen):
                    yield x
            except Exception as ex:
                err.append((ap, str(ex)))
        elif stat.S_ISREG(inf.st_mode):
            yield ap, inf
        else:
            err.append((ap, "irregular filetype 0%o" % (inf.st_mode,)))


def walkdirs(err, tops, excl):
    """recursive statdir for a list of tops, yields [top, relpath, stat]"""
    sep = "{0}".format(os.sep).encode("ascii")
    if not VT100:
        excl = excl.replace("/", r"\\")
        za = []
        for td in tops:
            try:
                ap = os.path.abspath(os.path.realpath(td))
                if td[-1:] in (b"\\", b"/"):
                    ap += sep
            except:
                # maybe cpython #88013 (ok)
                ap = td

            za.append(ap)

        za = [x if x.startswith(b"\\\\") else b"\\\\?\\" + x for x in za]
        za = [x.replace(b"/", b"\\") for x in za]
        tops = za

    ptn = re.compile(excl.encode("utf-8") or b"\n", re.I)

    for top in tops:
        isdir = os.path.isdir(top)
        if top[-1:] == sep:
            stop = top.rstrip(sep)
            yield stop, b"", os.stat(stop)
        else:
            stop, dn = os.path.split(top)
            if isdir:
                yield stop, dn, os.stat(stop)

        if isdir:
            for ap, inf in walkdir(err, top, ptn, []):
                yield stop, ap[len(stop) :].lstrip(sep), inf
        else:
            d, n = top.rsplit(sep, 1)
            yield d or b"/", n, os.stat(top)


# mostly from copyparty/util.py
def quotep(btxt):
    # type: (bytes) -> bytes
    quot1 = quote(btxt, safe=b"/")
    if not PY2:
        quot1 = quot1.encode("ascii")

    return quot1.replace(b" ", b"%20")  # type: ignore


# from copyparty/util.py
def humansize(sz, terse=False):
    """picks a sensible unit for the given extent"""
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if sz < 1024:
            break

        sz /= 1024.0

    ret = " ".join([str(sz)[:4].rstrip("."), unit])

    if not terse:
        return ret

    return ret.replace("iB", "").replace(" ", "")


# from copyparty/up2k.py
def up2k_chunksize(filesize):
    """gives The correct chunksize for up2k hashing"""
    chunksize = 1024 * 1024
    stepsize = 512 * 1024
    while True:
        for mul in [1, 2]:
            nchunks = math.ceil(filesize * 1.0 / chunksize)
            if nchunks <= 256 or (chunksize >= 32 * 1024 * 1024 and nchunks <= 4096):
                return chunksize

            chunksize += stepsize
            stepsize *= mul


# mostly from copyparty/up2k.py
def get_hashlist(file, pcb, mth):
    # type: (File, Any, Any) -> None
    """generates the up2k hashlist from file contents, inserts it into `file`"""

    chunk_sz = up2k_chunksize(file.size)
    file_rem = file.size
    file_ofs = 0
    ret = []
    with open(file.abs, "rb", 512 * 1024) as f:
        t0 = time.time()

        if mth and file.size >= 1024 * 512:
            ret = mth.hash(f, file.size, chunk_sz, pcb, file)
            file_rem = 0

        while file_rem > 0:
            # same as `hash_at` except for `imutex` / bufsz
            hashobj = hashlib.sha512()
            chunk_sz = chunk_rem = min(chunk_sz, file_rem)
            while chunk_rem > 0:
                buf = f.read(min(chunk_rem, 64 * 1024))
                if not buf:
                    raise Exception("EOF at " + str(f.tell()))

                hashobj.update(buf)
                chunk_rem -= len(buf)

            digest = ub64enc(hashobj.digest()[:33]).decode("utf-8")

            ret.append([digest, file_ofs, chunk_sz])
            file_ofs += chunk_sz
            file_rem -= chunk_sz

            if pcb:
                pcb(file, file_ofs)

    file.t_hash = time.time() - t0
    file.cids = ret
    file.kchunks = {}
    for k, v1, v2 in ret:
        if k not in file.kchunks:
            file.kchunks[k] = [v1, v2]


def printlink(ar, purl, name, fk):
    if not name:
        url = purl  # srch
    else:
        name = quotep(name.encode("utf-8", WTF8)).decode("utf-8")
        if fk:
            url = "%s%s?k=%s" % (purl, name, fk)
        else:
            url = "%s%s" % (purl, name)

    url = "%s/%s" % (ar.burl, url.lstrip("/"))

    with linkmtx:
        if ar.u:
            links.append(url)
        if ar.ud:
            print(url)
        if linkfile:
            zs = "%s\n" % (url,)
            zb = zs.encode("utf-8", "replace")
            linkfile.write(zb)


def handshake(ar, file, search):
    # type: (argparse.Namespace, File, bool) -> tuple[list[str], bool]
    """
    performs a handshake with the server; reply is:
      if search, a list of search results
      otherwise, a list of chunks to upload
    """

    req = {
        "hash": [x[0] for x in file.cids],
        "name": file.name,
        "lmod": file.lmod,
        "size": file.size,
    }
    if search:
        req["srch"] = 1
    else:
        if ar.touch:
            req["umod"] = True
        if ar.owo:
            req["replace"] = "mt"
        elif ar.ow:
            req["replace"] = True

    file.recheck = False
    if file.url:
        url = file.url
    else:
        if b"/" in file.rel:
            url = quotep(file.rel.rsplit(b"/", 1)[0]).decode("utf-8")
        else:
            url = ""
        url = ar.vtop + url

    while True:
        sc = 600
        txt = ""
        t0 = time.time()
        try:
            zs = json.dumps(req, separators=(",\n", ": "))
            sc, txt = web.req("POST", url, {}, zs.encode("utf-8"), MJ)
            if sc < 400:
                break

            raise Exception("http %d: %s" % (sc, txt))

        except Exception as ex:
            em = str(ex).split("SSLError(")[-1].split("\nURL: ")[0].strip()

            if (
                sc == 422
                or "<pre>partial upload exists at a different" in txt
                or "<pre>source file busy; please try again" in txt
            ):
                file.recheck = True
                return [], False
            elif sc == 409 or "<pre>upload rejected, file already exists" in txt:
                return [], False
            elif sc == 403:
                print("\nERROR: login required, or wrong password:\n%s" % (txt,))
                raise BadAuth()

            t = "handshake failed, retrying: %s\n  t0=%.3f t1=%.3f td=%.3f\n  %s\n\n"
            now = time.time()
            eprint(t % (file.name, t0, now, now - t0, em))
            time.sleep(ar.cd)

    try:
        r = json.loads(txt)
    except:
        raise Exception(txt)

    if search:
        if ar.uon and r["hits"]:
            printlink(ar, r["hits"][0]["rp"], "", "")
        return r["hits"], False

    file.url = quotep(r["purl"].encode("utf-8", WTF8)).decode("utf-8")
    file.name = r["name"]
    file.wark = r["wark"]

    if ar.uon and not r["hash"]:
        printlink(ar, file.url, r["name"], r.get("fk"))

    return r["hash"], r["sprs"]


def upload(fsl, stats, maxsz):
    # type: (FileSlice, str, int) -> None
    """upload a range of file data, defined by one or more `cid` (chunk-hash)"""

    ctxt = fsl.cids[0]
    if len(fsl.cids) > 1:
        n = 192 // len(fsl.cids)
        n = 9 if n > 9 else 2 if n < 2 else n
        zsl = [zs[:n] for zs in fsl.cids[1:]]
        ctxt += ",%d,%s" % (n, "".join(zsl))

    headers = {
        "X-Up2k-Hash": ctxt,
        "X-Up2k-Wark": fsl.file.wark,
    }

    if stats:
        headers["X-Up2k-Stat"] = stats

    nsub = 0
    try:
        while nsub != -1:
            nsub = fsl.subchunk(maxsz, nsub)
            if nsub == -2:
                return
            if nsub >= 0:
                headers["X-Up2k-Subc"] = str(maxsz * nsub)
                headers.pop(CLEN, None)
                nsub += 1

            sc, txt = web.req("POST", fsl.file.url, headers, fsl, MO)

            if sc == 400:
                if (
                    "already being written" in txt
                    or "already got that" in txt
                    or "only sibling chunks" in txt
                ):
                    fsl.file.nojoin = 1

            if sc >= 400:
                raise Exception("http %s: %s" % (sc, txt))
    finally:
        if fsl.f:
            fsl.f.close()
            if nsub != -1:
                fsl.unsub()


class Ctl(object):
    """
    the coordinator which runs everything in parallel
    (hashing, handshakes, uploads)
    """

    def _scan(self):
        ar = self.ar
        eprint("\nscanning %d locations\n" % (len(ar.files),))
        nfiles = 0
        nbytes = 0
        err = []
        for _, _, inf in walkdirs(err, ar.files, ar.x):
            if stat.S_ISDIR(inf.st_mode):
                continue

            nfiles += 1
            nbytes += inf.st_size

        if err:
            eprint("\n# failed to access %d paths:\n" % (len(err),))
            for ap, msg in err:
                if ar.v:
                    eprint("%s\n `-%s\n\n" % (ap.decode("utf-8", "replace"), msg))
                else:
                    eprint(ap.decode("utf-8", "replace") + "\n")

            eprint("^ failed to access those %d paths ^\n\n" % (len(err),))

            if not ar.v:
                eprint("hint: set -v for detailed error messages\n")

            if not ar.ok:
                eprint("hint: aborting because --ok is not set\n")
                return

        eprint("found %d files, %s\n\n" % (nfiles, humansize(nbytes)))
        return nfiles, nbytes

    def __init__(self, ar, stats=None):
        self.ok = False
        self.panik = 0
        self.errs = 0
        self.ar = ar
        self.stats = stats or self._scan()
        if not self.stats:
            return

        self.nfiles, self.nbytes = self.stats
        self.filegen = walkdirs([], ar.files, ar.x)
        self.recheck = []  # type: list[File]

        if ar.safe:
            self._safe()
        else:
            self.at_hash = 0.0
            self.at_up = 0.0
            self.at_upr = 0.0
            self.hash_f = 0
            self.hash_c = 0
            self.hash_b = 0
            self.up_f = 0
            self.up_c = 0
            self.up_b = 0  # num bytes handled
            self.up_br = 0  # num bytes actually transferred
            self.uploader_busy = 0
            self.serialized = False

            self.t0 = time.time()
            self.t0_up = None
            self.spd = None
            self.eta = "99:99:99"

            self.mutex = threading.Lock()
            self.exit_cond = threading.Condition()
            self.uploader_alive = ar.j
            self.handshaker_alive = ar.j
            self.q_handshake = HSQueue()  # type: Queue[File]
            self.q_upload = Queue()  # type: Queue[FileSlice]

            self.st_hash = [None, "(idle, starting...)"]  # type: tuple[File, int]
            self.st_up = [None, "(idle, starting...)"]  # type: tuple[File, int]

            self.mth = MTHash(ar.J) if ar.J > 1 else None

            self._fancy()

        self.ok = not self.errs

    def _safe(self):
        """minimal basic slow boring fallback codepath"""
        search = self.ar.s
        nf = 0
        for top, rel, inf in self.filegen:
            if stat.S_ISDIR(inf.st_mode) or not rel:
                continue

            nf += 1
            file = File(top, rel, inf.st_size, inf.st_mtime)
            upath = file.abs.decode("utf-8", "replace")

            print("%d %s\n  hash..." % (self.nfiles - nf, upath))
            get_hashlist(file, None, None)

            while True:
                print("  hs...")
                try:
                    hs, _ = handshake(self.ar, file, search)
                except BadAuth:
                    sys.exit(1)

                if search:
                    if hs:
                        for hit in hs:
                            print("  found: %s/%s" % (self.ar.burl, hit["rp"]))
                    else:
                        print("  NOT found")
                    break

                file.ucids = hs
                if not hs:
                    break

                print("%d %s" % (self.nfiles - nf, upath))
                ncs = len(hs)
                for nc, cid in enumerate(hs):
                    print("  %d up %s" % (ncs - nc, cid))
                    stats = "%d/0/0/%d" % (nf, self.nfiles - nf)
                    fslice = FileSlice(file, [cid])
                    upload(fslice, stats, self.ar.szm)

            print("  ok!")
            if file.recheck:
                self.recheck.append(file)

        if not self.recheck:
            return

        eprint("finalizing %d duplicate files\n" % (len(self.recheck),))
        for file in self.recheck:
            handshake(self.ar, file, False)

    def _fancy(self):
        atexit.register(self.cleanup_vt100)
        if VT100 and not self.ar.ns:
            ss.scroll_region(3)

        Daemon(self.hasher)
        for _ in range(self.ar.j):
            Daemon(self.handshaker)
            Daemon(self.uploader)

        last_sp = -1
        while True:
            with self.exit_cond:
                self.exit_cond.wait(0.07)
            if self.panik:
                sys.exit(1)
            with self.mutex:
                if not self.handshaker_alive and not self.uploader_alive:
                    break
                st_hash = self.st_hash[:]
                st_up = self.st_up[:]

            if VT100 and not self.ar.ns:
                maxlen = ss.w - len(str(self.nfiles)) - 14
                txt = "\033[s\033[%dH" % (ss.g,)
                for y, k, st, f in [
                    [0, "hash", st_hash, self.hash_f],
                    [1, "send", st_up, self.up_f],
                ]:
                    txt += "\033[%dH%s:" % (ss.g + y, k)
                    file, arg = st
                    if not file:
                        txt += " %s\033[K" % (arg,)
                    else:
                        if y:
                            p = 100 * file.up_b / file.size
                        else:
                            p = 100 * arg / file.size

                        name = file.abs.decode("utf-8", "replace")[-maxlen:]
                        if "/" in name:
                            name = "\033[36m%s\033[0m/%s" % tuple(name.rsplit("/", 1))

                        txt += "%6.1f%% %d %s\033[K" % (p, self.nfiles - f, name)

                txt += "\033[%dH " % (ss.g + 2,)
            else:
                txt = " "

            if not VT100:  # OSC9;4 (taskbar-progress)
                sp = int(self.up_b * 100 / self.nbytes) or 1
                if last_sp != sp:
                    last_sp = sp
                    txt += "\033]9;4;1;%d\033\\" % (sp,)

            if not self.up_br:
                spd = self.hash_b / ((time.time() - self.t0) or 1)
                eta = (self.nbytes - self.hash_b) / (spd or 1)
            else:
                spd = self.up_br / ((time.time() - self.t0_up) or 1)
                spd = self.spd = (self.spd or spd) * 0.9 + spd * 0.1
                eta = (self.nbytes - self.up_b) / (spd or 1)

            spd = humansize(spd)
            self.eta = str(datetime.timedelta(seconds=int(eta)))
            if eta > 2591999:
                self.eta = self.eta.split(",")[0]  # truncate HH:MM:SS
            sleft = humansize(self.nbytes - self.up_b)
            nleft = self.nfiles - self.up_f
            tail = "\033[K\033[u" if VT100 and not self.ar.ns else "\r"

            t = "%s eta @ %s/s, %s, %d# left" % (self.eta, spd, sleft, nleft)
            if not self.hash_b:
                t = " now hashing..."
            eprint(txt + "\033]0;{0}\033\\\r{0}{1}".format(t, tail))

        if self.ar.wlist:
            self.at_hash = time.time() - self.t0

        if self.hash_b and self.at_hash:
            spd = humansize(self.hash_b / self.at_hash)
            eprint("\nhasher: %.2f sec, %s/s\n" % (self.at_hash, spd))
        if self.up_br and self.at_up:
            spd = humansize(self.up_br / self.at_up)
            eprint("upload: %.2f sec, %s/s\n" % (self.at_up, spd))

        if not self.recheck:
            return

        eprint("finalizing %d duplicate files\n" % (len(self.recheck),))
        for file in self.recheck:
            handshake(self.ar, file, False)

    def cleanup_vt100(self):
        if VT100:
            ss.scroll_region(None)
        else:
            eprint("\033]9;4;0\033\\")
        eprint("\033[J\033]0;\033\\")

    def cb_hasher(self, file, ofs):
        self.st_hash = [file, ofs]

    def hasher(self):
        ptn = re.compile(self.ar.x.encode("utf-8"), re.I) if self.ar.x else None
        sep = "{0}".format(os.sep).encode("ascii")
        prd = None
        ls = {}
        for top, rel, inf in self.filegen:
            isdir = stat.S_ISDIR(inf.st_mode)
            if self.ar.z or self.ar.drd:
                rd = rel if isdir else os.path.dirname(rel)
                srd = rd.decode("utf-8", "replace").replace("\\", "/").rstrip("/")
                if srd:
                    srd += "/"
                if prd != rd:
                    prd = rd
                    ls = {}
                    try:
                        print("      ls ~{0}".format(srd))
                        zt = (
                            self.ar.vtop,
                            quotep(rd.replace(b"\\", b"/")).decode("utf-8"),
                        )
                        sc, txt = web.req("GET", "%s%s?ls&lt&dots" % zt, {})
                        if sc >= 400:
                            raise Exception("http %s" % (sc,))

                        j = json.loads(txt)
                        for f in j["dirs"] + j["files"]:
                            rfn = f["href"].split("?")[0].rstrip("/")
                            ls[unquote(rfn.encode("utf-8", WTF8))] = f
                    except Exception as ex:
                        print("   mkdir ~{0}  ({1})".format(srd, ex))

                    if self.ar.drd:
                        dp = os.path.join(top, rd)
                        try:
                            lnodes = set(os.listdir(dp))
                        except:
                            lnodes = list(ls)  # fs eio; don't delete
                        if ptn:
                            zs = dp.replace(sep, b"/").rstrip(b"/") + b"/"
                            zls = [zs + x for x in lnodes]
                            zls = [x for x in zls if not ptn.match(x)]
                            lnodes = [x.split(b"/")[-1] for x in zls]
                        bnames = [x for x in ls if x not in lnodes and x != b".hist"]
                        vpath = self.ar.url.split("://")[-1].split("/", 1)[-1]
                        names = [x.decode("utf-8", WTF8) for x in bnames]
                        locs = [vpath + srd + x for x in names]
                        while locs:
                            req = locs
                            while req:
                                print("DELETING ~%s#%s" % (srd, len(req)))
                                body = json.dumps(req).encode("utf-8")
                                sc, txt = web.req(
                                    "POST", self.ar.url + "?delete", {}, body, MJ
                                )
                                if sc == 413 and "json 2big" in txt:
                                    print(" (delete request too big; slicing...)")
                                    req = req[: len(req) // 2]
                                    continue
                                elif sc >= 400:
                                    t = "delete request failed: %s %s"
                                    raise Exception(t % (sc, txt))
                                break
                            locs = locs[len(req) :]

            if isdir:
                continue

            if self.ar.z:
                rf = ls.get(os.path.basename(rel), None)
                if rf and rf["sz"] == inf.st_size and abs(rf["ts"] - inf.st_mtime) <= 2:
                    self.nfiles -= 1
                    self.nbytes -= inf.st_size
                    continue

            file = File(top, rel, inf.st_size, inf.st_mtime)
            while True:
                with self.mutex:
                    if (
                        self.hash_f - self.up_f == 1
                        or (
                            self.hash_b - self.up_b < 1024 * 1024 * 1024
                            and self.hash_c - self.up_c < 512
                        )
                    ) and (
                        not self.ar.nh
                        or (
                            self.q_upload.empty()
                            and self.q_handshake.empty()
                            and not self.uploader_busy
                        )
                    ):
                        break

                time.sleep(0.05)

            get_hashlist(file, self.cb_hasher, self.mth)
            with self.mutex:
                self.hash_f += 1
                self.hash_c += len(file.cids)
                self.hash_b += file.size
                if self.ar.wlist:
                    self.up_f = self.hash_f
                    self.up_c = self.hash_c
                    self.up_b = self.hash_b

            if self.ar.wlist:
                vp = file.rel.decode("utf-8")
                if self.ar.chs:
                    zsl = [
                        "%s %d %d" % (zsii[0], n, zsii[1])
                        for n, zsii in enumerate(file.cids)
                    ]
                    print("chs: %s\n%s" % (vp, "\n".join(zsl)))
                zsl = [self.ar.wsalt, str(file.size)] + [x[0] for x in file.cids]
                zb = hashlib.sha512("\n".join(zsl).encode("utf-8")).digest()[:33]
                wark = ub64enc(zb).decode("utf-8")
                if self.ar.jw:
                    print("%s  %s" % (wark, vp))
                else:
                    zd = datetime.datetime.fromtimestamp(max(0, file.lmod), UTC)
                    dt = "%04d-%02d-%02d %02d:%02d:%02d" % (
                        zd.year,
                        zd.month,
                        zd.day,
                        zd.hour,
                        zd.minute,
                        zd.second,
                    )
                    print("%s %12d %s %s" % (dt, file.size, wark, vp))
                continue

            self.q_handshake.put(file)

        self.st_hash = [None, "(finished)"]
        self._check_if_done()

    def _check_if_done(self):
        with self.mutex:
            if self.nfiles - self.up_f:
                return
        for _ in range(self.ar.j):
            self.q_handshake.put(None)

    def handshaker(self):
        search = self.ar.s
        while True:
            file = self.q_handshake.get()
            if not file:
                with self.mutex:
                    self.handshaker_alive -= 1
                self.q_upload.put(None)
                return

            chunksz = up2k_chunksize(file.size)
            upath = file.abs.decode("utf-8", "replace")
            if not VT100:
                upath = upath.lstrip("\\?")

            file.nhs += 1
            if file.nhs > 32:
                print("ERROR: giving up on file %s" % (upath))
                self.errs += 1
                continue

            while time.time() < file.cd:
                time.sleep(0.1)

            try:
                hs, sprs = handshake(self.ar, file, search)
            except BadAuth:
                self.panik = 1
                break

            if search:
                if hs:
                    for hit in hs:
                        print("found: %s\n  %s/%s" % (upath, self.ar.burl, hit["rp"]))
                else:
                    print("NOT found: {0}".format(upath))

                with self.mutex:
                    self.up_f += 1
                    self.up_c += len(file.cids)
                    self.up_b += file.size

                self._check_if_done()
                continue

            if file.recheck:
                self.recheck.append(file)

            with self.mutex:
                if hs and not sprs and not self.serialized:
                    t = "server filesystem does not support sparse files; serializing uploads\n"
                    eprint(t)
                    self.serialized = True
                    for _ in range(self.ar.j - 1):
                        self.q_upload.put(None)
                if not hs:
                    # all chunks done
                    self.up_f += 1
                    self.up_c += len(file.cids) - file.up_c
                    self.up_b += file.size - file.up_b

                    if not file.recheck:
                        self.up_done(file)

                if hs and file.up_c:
                    # some chunks failed
                    self.up_c -= len(hs)
                    file.up_c -= len(hs)
                    for cid in hs:
                        sz = file.kchunks[cid][1]
                        self.up_br -= sz
                        self.up_b -= sz
                        file.up_b -= sz

                if hs and not file.up_b:
                    # first hs of this file; is this an upload resume?
                    file.up_b = chunksz * max(0, len(file.kchunks) - len(hs))

                file.ucids = hs

            if not hs:
                self.at_hash += file.t_hash

                if self.ar.spd:
                    if VT100:
                        c1 = "\033[36m"
                        c2 = "\033[0m"
                    else:
                        c1 = c2 = ""

                    spd_h = humansize(file.size / file.t_hash, True)
                    if file.up_c:
                        t_up = file.t1_up - file.t0_up
                        spd_u = humansize(file.size / t_up, True)

                        t = "uploaded %s %s(h:%.2fs,%s/s,up:%.2fs,%s/s)%s"
                        print(t % (upath, c1, file.t_hash, spd_h, t_up, spd_u, c2))
                    else:
                        t = "   found %s %s(%.2fs,%s/s)%s"
                        print(t % (upath, c1, file.t_hash, spd_h, c2))
                else:
                    kw = "uploaded" if file.up_c else "   found"
                    print("{0} {1}".format(kw, upath))

                self._check_if_done()
                continue

            njoin = self.ar.sz // chunksz
            cs = hs[:]
            while cs:
                fsl = FileSlice(file, cs[:1])
                try:
                    if file.nojoin:
                        raise Exception()
                    for n in range(2, min(len(cs), njoin + 1)):
                        fsl = FileSlice(file, cs[:n])
                except:
                    pass
                cs = cs[len(fsl.cids) :]
                self.q_upload.put(fsl)

    def uploader(self):
        while True:
            fsl = self.q_upload.get()
            if not fsl:
                done = False
                with self.mutex:
                    self.uploader_alive -= 1
                    if not self.uploader_alive:
                        done = not self.handshaker_alive
                        self.st_up = [None, "(finished)"]
                if done:
                    with self.exit_cond:
                        self.exit_cond.notify_all()
                return

            file = fsl.file
            cids = fsl.cids

            with self.mutex:
                if not self.uploader_busy:
                    self.at_upr = time.time()
                self.uploader_busy += 1
                if not file.t0_up:
                    file.t0_up = time.time()
                    if not self.t0_up:
                        self.t0_up = file.t0_up

            stats = "%d/%d/%d/%d %d/%d %s" % (
                self.up_f,
                len(self.recheck),
                self.uploader_busy,
                self.nfiles - self.up_f,
                self.nbytes // (1024 * 1024),
                (self.nbytes - self.up_b) // (1024 * 1024),
                self.eta,
            )

            try:
                upload(fsl, stats, self.ar.szm)
            except Exception as ex:
                t = "upload failed, retrying: %s #%s+%d (%s)\n"
                eprint(t % (file.name, cids[0][:8], len(cids) - 1, ex))
                file.cd = time.time() + self.ar.cd
                # handshake will fix it

            with self.mutex:
                sz = fsl.len
                file.ucids = [x for x in file.ucids if x not in cids]
                if not file.ucids:
                    file.t1_up = time.time()
                    self.q_handshake.put(file)

                self.st_up = [file, cids[0]]
                file.up_b += sz
                self.up_b += sz
                self.up_br += sz
                file.up_c += 1
                self.up_c += 1
                self.uploader_busy -= 1
                if not self.uploader_busy:
                    self.at_up += time.time() - self.at_upr

    def up_done(self, file):
        if self.ar.dl:
            os.unlink(file.abs)


class APF(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


def main():
    global web, linkfile

    time.strptime("19970815", "%Y%m%d")  # python#7980
    "".encode("idna")  # python#29288
    if not VT100:
        os.system("rem")  # enables colors

    cores = (os.cpu_count() if hasattr(os, "cpu_count") else 0) or 2
    hcores = min(cores, 3)  # 4% faster than 4+ on py3.9 @ r5-4500U

    ver = "{0}, v{1}".format(S_BUILD_DT, S_VERSION)
    if "--version" in sys.argv:
        print(ver)
        return

    sys.argv = [x for x in sys.argv if x != "--ws"]

    # fmt: off
    ap = app = argparse.ArgumentParser(formatter_class=APF, description="copyparty up2k uploader / filesearch tool  " + ver, epilog="""
NOTE: source file/folder selection uses rsync syntax, meaning that:
  "foo" uploads the entire folder to URL/foo/
  "foo/" uploads the CONTENTS of the folder into URL/
NOTE: if server has --usernames enabled, then password is "username:password"
""")

    ap.add_argument("url", type=unicode, help="server url, including destination folder")
    ap.add_argument("files", type=files_decoder, nargs="+", help="files and/or folders to process")
    ap.add_argument("-v", action="store_true", help="verbose")
    ap.add_argument("-a", metavar="PASSWD", help="password or $filepath")
    ap.add_argument("-s", action="store_true", help="file-search (disables upload)")
    ap.add_argument("-x", type=unicode, metavar="REGEX", action="append", help="skip file if filesystem-abspath matches REGEX (option can be repeated), example: '.*/\\.hist/.*'")
    ap.add_argument("--ok", action="store_true", help="continue even if some local files are inaccessible")
    ap.add_argument("--touch", action="store_true", help="if last-modified timestamps differ, push local to server (need write+delete perms)")
    ap.add_argument("--ow", action="store_true", help="overwrite existing files instead of autorenaming")
    ap.add_argument("--owo", action="store_true", help="overwrite existing files if server-file is older")
    ap.add_argument("--spd", action="store_true", help="print speeds for each file")
    ap.add_argument("--version", action="store_true", help="show version and exit")

    ap = app.add_argument_group("print links")
    ap.add_argument("-u", action="store_true", help="print list of download-links after all uploads finished")
    ap.add_argument("-ud", action="store_true", help="print download-link after each upload finishes")
    ap.add_argument("-uf", type=unicode, metavar="PATH", help="print list of download-links to file")

    ap = app.add_argument_group("compatibility")
    ap.add_argument("--cls", action="store_true", help="clear screen before start")
    ap.add_argument("--rh", type=int, metavar="TRIES", default=0, help="resolve server hostname before upload (good for buggy networks, but TLS certs will break)")

    ap = app.add_argument_group("folder sync")
    ap.add_argument("--dl", action="store_true", help="delete local files after uploading")
    ap.add_argument("--dr", action="store_true", help="delete remote files which don't exist locally (implies --ow)")
    ap.add_argument("--drd", action="store_true", help="delete remote files during upload instead of afterwards; reduces peak disk space usage, but will reupload instead of detecting renames")

    ap = app.add_argument_group("file-ID calculator; enable with url '-' to list warks (file identifiers) instead of upload/search")
    ap.add_argument("--wsalt", type=unicode, metavar="S", default="hunter2", help="salt to use when creating warks; must match server config")
    ap.add_argument("--chs", action="store_true", help="verbose (print the hash/offset of each chunk in each file)")
    ap.add_argument("--jw", action="store_true", help="just identifier+filepath, not mtime/size too")

    ap = app.add_argument_group("performance tweaks")
    ap.add_argument("-j", type=int, metavar="CONNS", default=2, help="parallel connections")
    ap.add_argument("-J", type=int, metavar="CORES", default=hcores, help="num cpu-cores to use for hashing; set 0 or 1 for single-core hashing")
    ap.add_argument("--sz", type=int, metavar="MiB", default=64, help="try to make each POST this big")
    ap.add_argument("--szm", type=int, metavar="MiB", default=96, help="max size of each POST (default is cloudflare max)")
    ap.add_argument("-nh", action="store_true", help="disable hashing while uploading")
    ap.add_argument("-ns", action="store_true", help="no status panel (for slow consoles and macos)")
    ap.add_argument("--cxp", type=float, metavar="SEC", default=57, help="assume http connections expired after SEConds")
    ap.add_argument("--cd", type=float, metavar="SEC", default=5, help="delay before reattempting a failed handshake/upload")
    ap.add_argument("--safe", action="store_true", help="use simple fallback approach")
    ap.add_argument("-z", action="store_true", help="ZOOMIN' (skip uploading files if they exist at the destination with the ~same last-modified timestamp, so same as yolo / turbo with date-chk but even faster)")

    ap = app.add_argument_group("tls")
    ap.add_argument("-te", metavar="PATH", help="path to ca.pem or cert.pem to expect/verify")
    ap.add_argument("-td", action="store_true", help="disable certificate check")
    # fmt: on

    try:
        ar = app.parse_args()
    finally:
        if EXE and not sys.argv[1:]:
            eprint("*** hit enter to exit ***")
            try:
                input()
            except:
                pass

    # msys2 doesn't uncygpath absolute paths with whitespace
    if not VT100:
        zsl = []
        for fn in ar.files:
            if re.search("^/[a-z]/", fn):
                fn = r"%s:\%s" % (fn[1:2], fn[3:])
            zsl.append(fn.replace("/", "\\"))
        ar.files = zsl

    fok = []
    fng = []
    for fn in ar.files:
        if os.path.exists(fn):
            fok.append(fn)
        elif VT100:
            fng.append(fn)
        else:
            # windows leaves glob-expansion to the invoked process... okayyy let's get to work
            from glob import glob

            fns = glob(fn)
            if fns:
                fok.extend(fns)
            else:
                fng.append(fn)

    if fng:
        t = "some files/folders were not found:\n  %s"
        raise Exception(t % ("\n  ".join(fng),))

    ar.files = fok

    if ar.drd:
        ar.dr = True

    if ar.dr:
        ar.ow = True

    ar.sz *= 1024 * 1024
    ar.szm *= 1024 * 1024

    ar.x = "|".join(ar.x or [])

    setattr(ar, "wlist", ar.url == "-")
    setattr(ar, "uon", ar.u or ar.ud or ar.uf)

    if ar.uf:
        linkfile = open(ar.uf, "wb")

    for k in "dl dr drd wlist".split():
        errs = []
        if ar.safe and getattr(ar, k):
            errs.append(k)

        if errs:
            raise Exception("--safe is incompatible with " + str(errs))

    ar.files = [
        os.path.abspath(os.path.realpath(x.encode("utf-8")))
        + (x[-1:] if x[-1:] in ("\\", "/") else "").encode("utf-8")
        for x in ar.files
    ]

    # urlsplit needs scheme;
    zs = ar.url.rstrip("/") + "/"
    if "://" not in zs:
        zs = "http://" + zs
    ar.url = zs

    url = urlsplit(zs)
    ar.burl = "%s://%s" % (url.scheme, url.netloc)
    ar.vtop = url.path

    if "https://" in ar.url.lower():
        try:
            import ssl
            import zipfile
        except:
            t = "ERROR: https is not available for some reason; please use http"
            print("\n\n   %s\n\n" % (t,))
            raise

    if ar.a and ar.a.startswith("$"):
        fn = ar.a[1:]
        print("reading password from file [{0}]".format(fn))
        with open(fn, "rb") as f:
            ar.a = f.read().decode("utf-8").strip()

    for n in range(ar.rh):
        try:
            ar.url = undns(ar.url)
            break
        except KeyboardInterrupt:
            raise
        except:
            if n > ar.rh - 2:
                raise

    if ar.cls:
        eprint("\033[H\033[2J\033[3J", end="")

    web = HCli(ar)
    ctl = Ctl(ar)

    if ar.dr and not ar.drd and ctl.ok:
        print("\npass 2/2: delete")
        ar.drd = True
        ar.z = True
        ctl = Ctl(ar, ctl.stats)

    if links:
        print()
        print("\n".join(links))
    if linkfile:
        linkfile.close()

    if ctl.errs:
        print("WARNING: %d errors" % (ctl.errs))

    sys.exit(0 if ctl.ok else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

S_VERSION = "1.10"
S_BUILD_DT = "2023-08-15"

"""
u2c.py: upload to copyparty
2021, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/u2c.py

- dependencies: requests
- supports python 2.6, 2.7, and 3.3 through 3.12
- if something breaks just try again and it'll autoresume
"""

import re
import os
import sys
import stat
import math
import time
import atexit
import signal
import socket
import base64
import hashlib
import platform
import threading
import datetime

EXE = sys.executable.endswith("exe")

try:
    import argparse
except:
    m = "\n  ERROR: need 'argparse'; download it here:\n   https://github.com/ThomasWaldmann/argparse/raw/master/argparse.py\n"
    print(m)
    raise

try:
    import requests
except ImportError as ex:
    if EXE:
        raise
    elif sys.version_info > (2, 7):
        m = "\nERROR: need 'requests'; please run this command:\n {0} -m pip install --user requests\n"
    else:
        m = "requests/2.18.4 urllib3/1.23 chardet/3.0.4 certifi/2020.4.5.1 idna/2.7"
        m = ["   https://pypi.org/project/" + x + "/#files" for x in m.split()]
        m = "\n  ERROR: need these:\n" + "\n".join(m) + "\n"
        m += "\n  for f in *.whl; do unzip $f; done; rm -r *.dist-info\n"

    print(m.format(sys.executable), "\nspecifically,", ex)
    sys.exit(1)


# from copyparty/__init__.py
PY2 = sys.version_info < (3,)
if PY2:
    from Queue import Queue
    from urllib import quote, unquote
    from urlparse import urlsplit, urlunsplit

    sys.dont_write_bytecode = True
    bytes = str
else:
    from queue import Queue
    from urllib.parse import unquote_to_bytes as unquote
    from urllib.parse import quote_from_bytes as quote
    from urllib.parse import urlsplit, urlunsplit

    unicode = str

VT100 = platform.system() != "Windows"


req_ses = requests.Session()


class Daemon(threading.Thread):
    def __init__(self, target, name=None, a=None):
        # type: (Any, Any, Any) -> None
        threading.Thread.__init__(self, target=target, args=a or (), name=name)
        self.daemon = True
        self.start()


class File(object):
    """an up2k upload task; represents a single file"""

    def __init__(self, top, rel, size, lmod):
        self.top = top  # type: bytes
        self.rel = rel.replace(b"\\", b"/")  # type: bytes
        self.size = size  # type: int
        self.lmod = lmod  # type: float

        self.abs = os.path.join(top, rel)  # type: bytes
        self.name = self.rel.split(b"/")[-1].decode("utf-8", "replace")  # type: str

        # set by get_hashlist
        self.cids = []  # type: list[tuple[str, int, int]]  # [ hash, ofs, sz ]
        self.kchunks = {}  # type: dict[str, tuple[int, int]]  # hash: [ ofs, sz ]

        # set by handshake
        self.recheck = False  # duplicate; redo handshake after all files done
        self.ucids = []  # type: list[str]  # chunks which need to be uploaded
        self.wark = None  # type: str
        self.url = None  # type: str

        # set by upload
        self.up_b = 0  # type: int
        self.up_c = 0  # type: int

        # t = "size({}) lmod({}) top({}) rel({}) abs({}) name({})\n"
        # eprint(t.format(self.size, self.lmod, self.top, self.rel, self.abs, self.name))


class FileSlice(object):
    """file-like object providing a fixed window into a file"""

    def __init__(self, file, cid):
        # type: (File, str) -> None

        self.car, self.len = file.kchunks[cid]
        self.cdr = self.car + self.len
        self.ofs = 0  # type: int
        self.f = open(file.abs, "rb", 512 * 1024)
        self.f.seek(self.car)

        # https://stackoverflow.com/questions/4359495/what-is-exactly-a-file-like-object-in-python
        # IOBase, RawIOBase, BufferedIOBase
        funs = "close closed __enter__ __exit__ __iter__ isatty __next__ readable seekable writable"
        try:
            for fun in funs.split():
                setattr(self, fun, getattr(self.f, fun))
        except:
            pass  # py27 probably

    def tell(self):
        return self.ofs

    def seek(self, ofs, wh=0):
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

    def read(self, sz):
        sz = min(sz, self.len - self.ofs)
        ret = self.f.read(sz)
        self.ofs += len(ret)
        return ret


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

        digest = hashobj.digest()[:33]
        digest = base64.urlsafe_b64encode(digest).decode("utf-8")
        return nch, digest, ofs0, chunk_sz


_print = print


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
        _print(*a, **ka)
    except:
        v = " ".join(str(x) for x in a)
        v = v.encode("ascii", "replace").decode("ascii")
        _print(v, **ka)

    if "flush" not in ka:
        sys.stdout.flush()


if not VT100:
    print = flushing_print


def termsize():
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct

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
            t = "{0}\033[{1}A".format("\n" * margin, margin)
            eprint("{0}\033[s\033[1;{1}r\033[u".format(t, self.g - 1))


ss = CTermsize()


def undns(url):
    usp = urlsplit(url)
    hn = usp.hostname
    gai = None
    eprint("resolving host [{0}] ...".format(hn), end="")
    try:
        gai = socket.getaddrinfo(hn, None)
        hn = gai[0][4][0]
    except KeyboardInterrupt:
        raise
    except:
        t = "\n\033[31mfailed to resolve upload destination host;\033[0m\ngai={0}\n"
        eprint(t.format(repr(gai)))
        raise

    if usp.port:
        hn = "{0}:{1}".format(hn, usp.port)
    if usp.username or usp.password:
        hn = "{0}:{1}@{2}".format(usp.username, usp.password, hn)

    usp = usp._replace(netloc=hn)
    url = urlunsplit(usp)
    eprint(" {0}".format(url))
    return url


def _scd(err, top):
    """non-recursive listing of directory contents, along with stat() info"""
    with os.scandir(top) as dh:
        for fh in dh:
            abspath = os.path.join(top, fh.name)
            try:
                yield [abspath, fh.stat()]
            except Exception as ex:
                err.append((abspath, str(ex)))


def _lsd(err, top):
    """non-recursive listing of directory contents, along with stat() info"""
    for name in os.listdir(top):
        abspath = os.path.join(top, name)
        try:
            yield [abspath, os.stat(abspath)]
        except Exception as ex:
            err.append((abspath, str(ex)))


if hasattr(os, "scandir") and sys.version_info > (3, 6):
    statdir = _scd
else:
    statdir = _lsd


def walkdir(err, top, seen):
    """recursive statdir"""
    atop = os.path.abspath(os.path.realpath(top))
    if atop in seen:
        err.append((top, "recursive-symlink"))
        return

    seen = seen[:] + [atop]
    for ap, inf in sorted(statdir(err, top)):
        yield ap, inf
        if stat.S_ISDIR(inf.st_mode):
            try:
                for x in walkdir(err, ap, seen):
                    yield x
            except Exception as ex:
                err.append((ap, str(ex)))


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

    ptn = re.compile(excl.encode("utf-8") or b"\n")

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
            for ap, inf in walkdir(err, top, []):
                if ptn.match(ap):
                    continue
                yield stop, ap[len(stop) :].lstrip(sep), inf
        else:
            d, n = top.rsplit(sep, 1)
            yield d, n, os.stat(top)


# mostly from copyparty/util.py
def quotep(btxt):
    quot1 = quote(btxt, safe=b"/")
    if not PY2:
        quot1 = quot1.encode("ascii")

    return quot1.replace(b" ", b"+")


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
            if nchunks <= 256 or (chunksize >= 32 * 1024 * 1024 and nchunks < 4096):
                return chunksize

            chunksize += stepsize
            stepsize *= mul


# mostly from copyparty/up2k.py
def get_hashlist(file, pcb, mth):
    # type: (File, any, any) -> None
    """generates the up2k hashlist from file contents, inserts it into `file`"""

    chunk_sz = up2k_chunksize(file.size)
    file_rem = file.size
    file_ofs = 0
    ret = []
    with open(file.abs, "rb", 512 * 1024) as f:
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

            digest = hashobj.digest()[:33]
            digest = base64.urlsafe_b64encode(digest).decode("utf-8")

            ret.append([digest, file_ofs, chunk_sz])
            file_ofs += chunk_sz
            file_rem -= chunk_sz

            if pcb:
                pcb(file, file_ofs)

    file.cids = ret
    file.kchunks = {}
    for k, v1, v2 in ret:
        file.kchunks[k] = [v1, v2]


def handshake(ar, file, search):
    # type: (argparse.Namespace, File, bool) -> tuple[list[str], bool]
    """
    performs a handshake with the server; reply is:
      if search, a list of search results
      otherwise, a list of chunks to upload
    """

    url = ar.url
    pw = ar.a

    req = {
        "hash": [x[0] for x in file.cids],
        "name": file.name,
        "lmod": file.lmod,
        "size": file.size,
    }
    if search:
        req["srch"] = 1
    elif ar.dr:
        req["replace"] = True

    headers = {"Content-Type": "text/plain"}  # <=1.5.1 compat
    if pw:
        headers["Cookie"] = "=".join(["cppwd", pw])

    file.recheck = False
    if file.url:
        url = file.url
    elif b"/" in file.rel:
        url += quotep(file.rel.rsplit(b"/", 1)[0]).decode("utf-8", "replace")

    while True:
        sc = 600
        txt = ""
        try:
            r = req_ses.post(url, headers=headers, json=req)
            sc = r.status_code
            txt = r.text
            if sc < 400:
                break

            raise Exception("http {0}: {1}".format(sc, txt))

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
            elif "<pre>you don't have " in txt:
                raise

            eprint("handshake failed, retrying: {0}\n  {1}\n\n".format(file.name, em))
            time.sleep(1)

    try:
        r = r.json()
    except:
        raise Exception(r.text)

    if search:
        return r["hits"], False

    try:
        pre, url = url.split("://")
        pre += "://"
    except:
        pre = ""

    file.url = pre + url.split("/")[0] + r["purl"]
    file.name = r["name"]
    file.wark = r["wark"]

    return r["hash"], r["sprs"]


def upload(file, cid, pw, stats):
    # type: (File, str, str, str) -> None
    """upload one specific chunk, `cid` (a chunk-hash)"""

    headers = {
        "X-Up2k-Hash": cid,
        "X-Up2k-Wark": file.wark,
        "Content-Type": "application/octet-stream",
    }

    if stats:
        headers["X-Up2k-Stat"] = stats

    if pw:
        headers["Cookie"] = "=".join(["cppwd", pw])

    f = FileSlice(file, cid)
    try:
        r = req_ses.post(file.url, headers=headers, data=f)
        if not r:
            raise Exception(repr(r))

        _ = r.content
    finally:
        f.f.close()


class Ctl(object):
    """
    the coordinator which runs everything in parallel
    (hashing, handshakes, uploads)
    """

    def _scan(self):
        ar = self.ar
        eprint("\nscanning {0} locations\n".format(len(ar.files)))
        nfiles = 0
        nbytes = 0
        err = []
        for _, _, inf in walkdirs(err, ar.files, ar.x):
            if stat.S_ISDIR(inf.st_mode):
                continue

            nfiles += 1
            nbytes += inf.st_size

        if err:
            eprint("\n# failed to access {0} paths:\n".format(len(err)))
            for ap, msg in err:
                if ar.v:
                    eprint("{0}\n `-{1}\n\n".format(ap.decode("utf-8", "replace"), msg))
                else:
                    eprint(ap.decode("utf-8", "replace") + "\n")

            eprint("^ failed to access those {0} paths ^\n\n".format(len(err)))

            if not ar.v:
                eprint("hint: set -v for detailed error messages\n")

            if not ar.ok:
                eprint("hint: aborting because --ok is not set\n")
                return

        eprint("found {0} files, {1}\n\n".format(nfiles, humansize(nbytes)))
        return nfiles, nbytes

    def __init__(self, ar, stats=None):
        self.ok = False
        self.ar = ar
        self.stats = stats or self._scan()
        if not self.stats:
            return

        self.nfiles, self.nbytes = self.stats

        if ar.td:
            requests.packages.urllib3.disable_warnings()
            req_ses.verify = False
        if ar.te:
            req_ses.verify = ar.te

        self.filegen = walkdirs([], ar.files, ar.x)
        self.recheck = []  # type: list[File]

        if ar.safe:
            self._safe()
        else:
            self.hash_f = 0
            self.hash_c = 0
            self.hash_b = 0
            self.up_f = 0
            self.up_c = 0
            self.up_b = 0
            self.up_br = 0
            self.hasher_busy = 1
            self.handshaker_busy = 0
            self.uploader_busy = 0
            self.serialized = False

            self.t0 = time.time()
            self.t0_up = None
            self.spd = None
            self.eta = "99:99:99"

            self.mutex = threading.Lock()
            self.q_handshake = Queue()  # type: Queue[File]
            self.q_upload = Queue()  # type: Queue[tuple[File, str]]

            self.st_hash = [None, "(idle, starting...)"]  # type: tuple[File, int]
            self.st_up = [None, "(idle, starting...)"]  # type: tuple[File, int]

            self.mth = MTHash(ar.J) if ar.J > 1 else None

            self._fancy()

        self.ok = True

    def _safe(self):
        """minimal basic slow boring fallback codepath"""
        search = self.ar.s
        for nf, (top, rel, inf) in enumerate(self.filegen):
            if stat.S_ISDIR(inf.st_mode) or not rel:
                continue

            file = File(top, rel, inf.st_size, inf.st_mtime)
            upath = file.abs.decode("utf-8", "replace")

            print("{0} {1}\n  hash...".format(self.nfiles - nf, upath))
            get_hashlist(file, None, None)

            burl = self.ar.url[:12] + self.ar.url[8:].split("/")[0] + "/"
            while True:
                print("  hs...")
                hs, _ = handshake(self.ar, file, search)
                if search:
                    if hs:
                        for hit in hs:
                            print("  found: {0}{1}".format(burl, hit["rp"]))
                    else:
                        print("  NOT found")
                    break

                file.ucids = hs
                if not hs:
                    break

                print("{0} {1}".format(self.nfiles - nf, upath))
                ncs = len(hs)
                for nc, cid in enumerate(hs):
                    print("  {0} up {1}".format(ncs - nc, cid))
                    stats = "{0}/0/0/{1}".format(nf, self.nfiles - nf)
                    upload(file, cid, self.ar.a, stats)

            print("  ok!")
            if file.recheck:
                self.recheck.append(file)

        if not self.recheck:
            return

        eprint("finalizing {0} duplicate files".format(len(self.recheck)))
        for file in self.recheck:
            handshake(self.ar, file, search)

    def _fancy(self):
        if VT100 and not self.ar.ns:
            atexit.register(self.cleanup_vt100)
            ss.scroll_region(3)

        Daemon(self.hasher)
        for _ in range(self.ar.j):
            Daemon(self.handshaker)
            Daemon(self.uploader)

        idles = 0
        while idles < 3:
            time.sleep(0.07)
            with self.mutex:
                if (
                    self.q_handshake.empty()
                    and self.q_upload.empty()
                    and not self.hasher_busy
                    and not self.handshaker_busy
                    and not self.uploader_busy
                ):
                    idles += 1
                else:
                    idles = 0

            if VT100 and not self.ar.ns:
                maxlen = ss.w - len(str(self.nfiles)) - 14
                txt = "\033[s\033[{0}H".format(ss.g)
                for y, k, st, f in [
                    [0, "hash", self.st_hash, self.hash_f],
                    [1, "send", self.st_up, self.up_f],
                ]:
                    txt += "\033[{0}H{1}:".format(ss.g + y, k)
                    file, arg = st
                    if not file:
                        txt += " {0}\033[K".format(arg)
                    else:
                        if y:
                            p = 100 * file.up_b / file.size
                        else:
                            p = 100 * arg / file.size

                        name = file.abs.decode("utf-8", "replace")[-maxlen:]
                        if "/" in name:
                            name = "\033[36m{0}\033[0m/{1}".format(*name.rsplit("/", 1))

                        t = "{0:6.1f}% {1} {2}\033[K"
                        txt += t.format(p, self.nfiles - f, name)

                txt += "\033[{0}H ".format(ss.g + 2)
            else:
                txt = " "

            if not self.up_br:
                spd = self.hash_b / (time.time() - self.t0)
                eta = (self.nbytes - self.hash_b) / (spd + 1)
            else:
                spd = self.up_br / (time.time() - self.t0_up)
                spd = self.spd = (self.spd or spd) * 0.9 + spd * 0.1
                eta = (self.nbytes - self.up_b) / (spd + 1)

            spd = humansize(spd)
            self.eta = str(datetime.timedelta(seconds=int(eta)))
            sleft = humansize(self.nbytes - self.up_b)
            nleft = self.nfiles - self.up_f
            tail = "\033[K\033[u" if VT100 and not self.ar.ns else "\r"

            t = "{0} eta @ {1}/s, {2}, {3}# left".format(self.eta, spd, sleft, nleft)
            eprint(txt + "\033]0;{0}\033\\\r{0}{1}".format(t, tail))

        if not self.recheck:
            return

        eprint("finalizing {0} duplicate files".format(len(self.recheck)))
        for file in self.recheck:
            handshake(self.ar, file, False)

    def cleanup_vt100(self):
        ss.scroll_region(None)
        eprint("\033[J\033]0;\033\\")

    def cb_hasher(self, file, ofs):
        self.st_hash = [file, ofs]

    def hasher(self):
        prd = None
        ls = {}
        for top, rel, inf in self.filegen:
            isdir = stat.S_ISDIR(inf.st_mode)
            if self.ar.z or self.ar.drd:
                rd = rel if isdir else os.path.dirname(rel)
                srd = rd.decode("utf-8", "replace").replace("\\", "/")
                if prd != rd:
                    prd = rd
                    headers = {}
                    if self.ar.a:
                        headers["Cookie"] = "=".join(["cppwd", self.ar.a])

                    ls = {}
                    try:
                        print("      ls ~{0}".format(srd))
                        zb = self.ar.url.encode("utf-8")
                        zb += quotep(rd.replace(b"\\", b"/"))
                        r = req_ses.get(zb + b"?ls&lt&dots", headers=headers)
                        if not r:
                            raise Exception("HTTP {0}".format(r.status_code))

                        j = r.json()
                        for f in j["dirs"] + j["files"]:
                            rfn = f["href"].split("?")[0].rstrip("/")
                            ls[unquote(rfn.encode("utf-8", "replace"))] = f
                    except Exception as ex:
                        print("   mkdir ~{0}  ({1})".format(srd, ex))

                    if self.ar.drd:
                        dp = os.path.join(top, rd)
                        lnodes = set(os.listdir(dp))
                        bnames = [x for x in ls if x not in lnodes]
                        if bnames:
                            vpath = self.ar.url.split("://")[-1].split("/", 1)[-1]
                            names = [x.decode("utf-8", "replace") for x in bnames]
                            locs = [vpath + srd + "/" + x for x in names]
                            print("DELETING ~{0}/#{1}".format(srd, len(names)))
                            req_ses.post(self.ar.url + "?delete", json=locs)

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

            self.q_handshake.put(file)

        self.hasher_busy = 0
        self.st_hash = [None, "(finished)"]

    def handshaker(self):
        search = self.ar.s
        burl = self.ar.url[:8] + self.ar.url[8:].split("/")[0] + "/"
        while True:
            file = self.q_handshake.get()
            if not file:
                self.q_upload.put(None)
                break

            with self.mutex:
                self.handshaker_busy += 1

            upath = file.abs.decode("utf-8", "replace")
            if not VT100:
                upath = upath.lstrip("\\?")

            hs, sprs = handshake(self.ar, file, search)
            if search:
                if hs:
                    for hit in hs:
                        t = "found: {0}\n  {1}{2}\n"
                        print(t.format(upath, burl, hit["rp"]), end="")
                else:
                    print("NOT found: {0}\n".format(upath), end="")

                with self.mutex:
                    self.up_f += 1
                    self.up_c += len(file.cids)
                    self.up_b += file.size
                    self.handshaker_busy -= 1

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
                        self.up_b -= sz
                        file.up_b -= sz

                file.ucids = hs
                self.handshaker_busy -= 1

            if not hs:
                kw = "uploaded" if file.up_b else "   found"
                print("{0} {1}".format(kw, upath))
            for cid in hs:
                self.q_upload.put([file, cid])

    def uploader(self):
        while True:
            task = self.q_upload.get()
            if not task:
                self.st_up = [None, "(finished)"]
                break

            with self.mutex:
                self.uploader_busy += 1
                self.t0_up = self.t0_up or time.time()

            zs = "{0}/{1}/{2}/{3} {4}/{5} {6}"
            stats = zs.format(
                self.up_f,
                len(self.recheck),
                self.uploader_busy,
                self.nfiles - self.up_f,
                int(self.nbytes / (1024 * 1024)),
                int((self.nbytes - self.up_b) / (1024 * 1024)),
                self.eta,
            )

            file, cid = task
            try:
                upload(file, cid, self.ar.a, stats)
            except Exception as ex:
                t = "upload failed, retrying: {0} #{1} ({2})\n"
                eprint(t.format(file.name, cid[:8], ex))
                # handshake will fix it

            with self.mutex:
                sz = file.kchunks[cid][1]
                file.ucids = [x for x in file.ucids if x != cid]
                if not file.ucids:
                    self.q_handshake.put(file)

                self.st_up = [file, cid]
                file.up_b += sz
                self.up_b += sz
                self.up_br += sz
                file.up_c += 1
                self.up_c += 1
                self.uploader_busy -= 1

    def up_done(self, file):
        if self.ar.dl:
            os.unlink(file.abs)


class APF(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


def main():
    time.strptime("19970815", "%Y%m%d")  # python#7980
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
    ap = app = argparse.ArgumentParser(formatter_class=APF, description="copyparty up2k uploader / filesearch tool, " + ver, epilog="""
NOTE:
source file/folder selection uses rsync syntax, meaning that:
  "foo" uploads the entire folder to URL/foo/
  "foo/" uploads the CONTENTS of the folder into URL/
""")

    ap.add_argument("url", type=unicode, help="server url, including destination folder")
    ap.add_argument("files", type=unicode, nargs="+", help="files and/or folders to process")
    ap.add_argument("-v", action="store_true", help="verbose")
    ap.add_argument("-a", metavar="PASSWORD", help="password or $filepath")
    ap.add_argument("-s", action="store_true", help="file-search (disables upload)")
    ap.add_argument("-x", type=unicode, metavar="REGEX", default="", help="skip file if filesystem-abspath matches REGEX, example: '.*/\.hist/.*'")
    ap.add_argument("--ok", action="store_true", help="continue even if some local files are inaccessible")
    ap.add_argument("--version", action="store_true", help="show version and exit")

    ap = app.add_argument_group("compatibility")
    ap.add_argument("--cls", action="store_true", help="clear screen before start")
    ap.add_argument("--rh", type=int, metavar="TRIES", default=0, help="resolve server hostname before upload (good for buggy networks, but TLS certs will break)")

    ap = app.add_argument_group("folder sync")
    ap.add_argument("--dl", action="store_true", help="delete local files after uploading")
    ap.add_argument("--dr", action="store_true", help="delete remote files which don't exist locally")
    ap.add_argument("--drd", action="store_true", help="delete remote files during upload instead of afterwards; reduces peak disk space usage, but will reupload instead of detecting renames")

    ap = app.add_argument_group("performance tweaks")
    ap.add_argument("-j", type=int, metavar="THREADS", default=4, help="parallel connections")
    ap.add_argument("-J", type=int, metavar="THREADS", default=hcores, help="num cpu-cores to use for hashing; set 0 or 1 for single-core hashing")
    ap.add_argument("-nh", action="store_true", help="disable hashing while uploading")
    ap.add_argument("-ns", action="store_true", help="no status panel (for slow consoles and macos)")
    ap.add_argument("--safe", action="store_true", help="use simple fallback approach")
    ap.add_argument("-z", action="store_true", help="ZOOMIN' (skip uploading files if they exist at the destination with the ~same last-modified timestamp, so same as yolo / turbo with date-chk but even faster)")

    ap = app.add_argument_group("tls")
    ap.add_argument("-te", metavar="PEM_FILE", help="certificate to expect/verify")
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

    if ar.drd:
        ar.dr = True

    for k in "dl dr drd".split():
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

    ar.url = ar.url.rstrip("/") + "/"
    if "://" not in ar.url:
        ar.url = "http://" + ar.url

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

    ctl = Ctl(ar)

    if ar.dr and not ar.drd and ctl.ok:
        print("\npass 2/2: delete")
        ar.drd = True
        ar.z = True
        ctl = Ctl(ar, ctl.stats)

    sys.exit(0 if ctl.ok else 1)


if __name__ == "__main__":
    main()

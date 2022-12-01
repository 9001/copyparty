#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

"""
up2k.py: upload to copyparty
2022-11-29, v0.22, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py

- dependencies: requests
- supports python 2.6, 2.7, and 3.3 through 3.11

- almost zero error-handling
- but if something breaks just try again and it'll autoresume
"""

import os
import sys
import stat
import math
import time
import atexit
import signal
import base64
import hashlib
import platform
import threading
import datetime

try:
    import argparse
except:
    m = "\n  ERROR: need 'argparse'; download it here:\n   https://github.com/ThomasWaldmann/argparse/raw/master/argparse.py\n"
    print(m)
    raise

try:
    import requests
except ImportError:
    if sys.version_info > (2, 7):
        m = "\nERROR: need 'requests'; please run this command:\n {0} -m pip install --user requests\n"
    else:
        m = "requests/2.18.4 urllib3/1.23 chardet/3.0.4 certifi/2020.4.5.1 idna/2.7"
        m = ["   https://pypi.org/project/" + x + "/#files" for x in m.split()]
        m = "\n  ERROR: need these:\n" + "\n".join(m) + "\n"

    print(m.format(sys.executable))
    sys.exit(1)


# from copyparty/__init__.py
PY2 = sys.version_info < (3,)
if PY2:
    from Queue import Queue
    from urllib import quote, unquote

    sys.dont_write_bytecode = True
    bytes = str
else:
    from queue import Queue
    from urllib.parse import unquote_to_bytes as unquote
    from urllib.parse import quote_from_bytes as quote

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
    _print(*a, **ka)
    if "flush" not in ka:
        sys.stdout.flush()


if not VT100:
    print = flushing_print


def termsize():
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct

            cr = struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "1234"))
        except:
            return
        return cr

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (env["LINES"], env["COLUMNS"])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])


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
        if stat.S_ISDIR(inf.st_mode):
            try:
                for x in walkdir(err, ap, seen):
                    yield x
            except Exception as ex:
                err.append((ap, str(ex)))
        else:
            yield ap, inf


def walkdirs(err, tops):
    """recursive statdir for a list of tops, yields [top, relpath, stat]"""
    sep = "{0}".format(os.sep).encode("ascii")
    for top in tops:
        if top[-1:] == sep:
            stop = top.rstrip(sep)
        else:
            stop = os.path.dirname(top)

        if os.path.isdir(top):
            for ap, inf in walkdir(err, top, []):
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


def handshake(url, file, pw, search):
    # type: (str, File, Any, bool) -> tuple[list[str], bool]
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

    headers = {"Content-Type": "text/plain"}  # wtf ed
    if pw:
        headers["Cookie"] = "=".join(["cppwd", pw])

    if file.url:
        url = file.url
    elif b"/" in file.rel:
        url += quotep(file.rel.rsplit(b"/", 1)[0]).decode("utf-8", "replace")

    while True:
        try:
            r = req_ses.post(url, headers=headers, json=req)
            break
        except Exception as ex:
            em = str(ex).split("SSLError(")[-1]
            eprint("handshake failed, retrying: {0}\n  {1}\n\n".format(file.name, em))
            time.sleep(1)

    sc = r.status_code
    if sc >= 400:
        txt = r.text
        if sc == 422 or "<pre>partial upload exists at a different" in txt:
            file.recheck = True
            return [], False
        elif sc == 409 or "<pre>upload rejected, file already exists" in txt:
            return [], False

        raise Exception("http {0}: {1}".format(sc, txt))

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


def upload(file, cid, pw):
    # type: (File, str, Any) -> None
    """upload one specific chunk, `cid` (a chunk-hash)"""

    headers = {
        "X-Up2k-Hash": cid,
        "X-Up2k-Wark": file.wark,
        "Content-Type": "application/octet-stream",
    }
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
    this will be the coordinator which runs everything in parallel
    (hashing, handshakes, uploads)  but right now it's p dumb
    """

    def __init__(self, ar):
        self.ar = ar
        ar.files = [
            os.path.abspath(os.path.realpath(x.encode("utf-8")))
            + (x[-1:] if x[-1:] == os.sep else "").encode("utf-8")
            for x in ar.files
        ]
        ar.url = ar.url.rstrip("/") + "/"
        if "://" not in ar.url:
            ar.url = "http://" + ar.url

        eprint("\nscanning {0} locations\n".format(len(ar.files)))

        nfiles = 0
        nbytes = 0
        err = []
        for _, _, inf in walkdirs(err, ar.files):
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
        self.nfiles = nfiles
        self.nbytes = nbytes

        if ar.td:
            requests.packages.urllib3.disable_warnings()
            req_ses.verify = False
        if ar.te:
            req_ses.verify = ar.te

        self.filegen = walkdirs([], ar.files)
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

            self.mutex = threading.Lock()
            self.q_handshake = Queue()  # type: Queue[File]
            self.q_upload = Queue()  # type: Queue[tuple[File, str]]
            self.recheck = []  # type: list[File]

            self.st_hash = [None, "(idle, starting...)"]  # type: tuple[File, int]
            self.st_up = [None, "(idle, starting...)"]  # type: tuple[File, int]

            self.mth = MTHash(ar.J) if ar.J > 1 else None

            self._fancy()

    def _safe(self):
        """minimal basic slow boring fallback codepath"""
        search = self.ar.s
        for nf, (top, rel, inf) in enumerate(self.filegen):
            file = File(top, rel, inf.st_size, inf.st_mtime)
            upath = file.abs.decode("utf-8", "replace")

            print("{0} {1}\n  hash...".format(self.nfiles - nf, upath))
            get_hashlist(file, None, None)

            burl = self.ar.url[:12] + self.ar.url[8:].split("/")[0] + "/"
            while True:
                print("  hs...")
                hs, _ = handshake(self.ar.url, file, self.ar.a, search)
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
                    upload(file, cid, self.ar.a)

            print("  ok!")
            if file.recheck:
                self.recheck.append(file)

        if not self.recheck:
            return

        eprint("finalizing {0} duplicate files".format(len(self.recheck)))
        for file in self.recheck:
            handshake(self.ar.url, file, self.ar.a, search)

    def _fancy(self):
        if VT100:
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

            if VT100:
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
            eta = str(datetime.timedelta(seconds=int(eta)))
            sleft = humansize(self.nbytes - self.up_b)
            nleft = self.nfiles - self.up_f
            tail = "\033[K\033[u" if VT100 else "\r"

            t = "{0} eta @ {1}/s, {2}, {3}# left".format(eta, spd, sleft, nleft)
            eprint(txt + "\033]0;{0}\033\\\r{0}{1}".format(t, tail))

        if not self.recheck:
            return

        eprint("finalizing {0} duplicate files".format(len(self.recheck)))
        for file in self.recheck:
            handshake(self.ar.url, file, self.ar.a, False)

    def cleanup_vt100(self):
        ss.scroll_region(None)
        eprint("\033[J\033]0;\033\\")

    def cb_hasher(self, file, ofs):
        self.st_hash = [file, ofs]

    def hasher(self):
        prd = None
        ls = {}
        for top, rel, inf in self.filegen:
            if self.ar.z:
                rd = os.path.dirname(rel)
                if prd != rd:
                    prd = rd
                    headers = {}
                    if self.ar.a:
                        headers["Cookie"] = "=".join(["cppwd", self.ar.a])

                    ls = {}
                    try:
                        print("      ls ~{0}".format(rd.decode("utf-8", "replace")))
                        r = req_ses.get(
                            self.ar.url.encode("utf-8") + quotep(rd) + b"?ls",
                            headers=headers,
                        )
                        for f in r.json()["files"]:
                            rfn = f["href"].split("?")[0].encode("utf-8", "replace")
                            ls[unquote(rfn)] = f
                    except:
                        print("   mkdir ~{0}".format(rd.decode("utf-8", "replace")))

                rf = ls.get(os.path.basename(rel), None)
                if rf and rf["sz"] == inf.st_size and abs(rf["ts"] - inf.st_mtime) <= 1:
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
            hs, sprs = handshake(self.ar.url, file, self.ar.a, search)
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

            file, cid = task
            try:
                upload(file, cid, self.ar.a)
            except:
                eprint("upload failed, retrying: {0} #{1}\n".format(file.name, cid[:8]))
                pass  # handshake will fix it

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


class APF(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


def main():
    time.strptime("19970815", "%Y%m%d")  # python#7980
    if not VT100:
        os.system("rem")  # enables colors

    cores = (os.cpu_count() if hasattr(os, "cpu_count") else 0) or 2
    hcores = min(cores, 3)  # 4% faster than 4+ on py3.9 @ r5-4500U

    # fmt: off
    ap = app = argparse.ArgumentParser(formatter_class=APF, epilog="""
NOTE:
source file/folder selection uses rsync syntax, meaning that:
  "foo" uploads the entire folder to URL/foo/
  "foo/" uploads the CONTENTS of the folder into URL/
""")

    ap.add_argument("url", type=unicode, help="server url, including destination folder")
    ap.add_argument("files", type=unicode, nargs="+", help="files and/or folders to process")
    ap.add_argument("-v", action="store_true", help="verbose")
    ap.add_argument("-a", metavar="PASSWORD", help="password")
    ap.add_argument("-s", action="store_true", help="file-search (disables upload)")
    ap.add_argument("--ok", action="store_true", help="continue even if some local files are inaccessible")
    ap = app.add_argument_group("performance tweaks")
    ap.add_argument("-j", type=int, metavar="THREADS", default=4, help="parallel connections")
    ap.add_argument("-J", type=int, metavar="THREADS", default=hcores, help="num cpu-cores to use for hashing; set 0 or 1 for single-core hashing")
    ap.add_argument("-nh", action="store_true", help="disable hashing while uploading")
    ap.add_argument("--safe", action="store_true", help="use simple fallback approach")
    ap.add_argument("-z", action="store_true", help="ZOOMIN' (skip uploading files if they exist at the destination with the ~same last-modified timestamp, so same as yolo / turbo with date-chk but even faster)")
    ap = app.add_argument_group("tls")
    ap.add_argument("-te", metavar="PEM_FILE", help="certificate to expect/verify")
    ap.add_argument("-td", action="store_true", help="disable certificate check")
    # fmt: on

    Ctl(app.parse_args())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

"""
up2k.py: upload to copyparty
2021-11-28, v0.13, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py

- dependencies: requests
- supports python 2.6, 2.7, and 3.3 through 3.10

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
import argparse
import platform
import threading
import requests
import datetime


# from copyparty/__init__.py
PY2 = sys.version_info[0] == 2
if PY2:
    from Queue import Queue
    from urllib import unquote
    from urllib import quote

    sys.dont_write_bytecode = True
    bytes = str
else:
    from queue import Queue
    from urllib.parse import unquote_to_bytes as unquote
    from urllib.parse import quote_from_bytes as quote

    unicode = str

VT100 = platform.system() != "Windows"


req_ses = requests.Session()


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
        self.ucids = []  # type: list[str]  # chunks which need to be uploaded
        self.wark = None  # type: str
        self.url = None  # type: str

        # set by upload
        self.up_b = 0  # type: int
        self.up_c = 0  # type: int

        # m = "size({}) lmod({}) top({}) rel({}) abs({}) name({})\n"
        # eprint(m.format(self.size, self.lmod, self.top, self.rel, self.abs, self.name))


class FileSlice(object):
    """file-like object providing a fixed window into a file"""

    def __init__(self, file, cid):
        # type: (File, str) -> FileSlice

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
    import os

    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os

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

        thr = threading.Thread(target=self.worker)
        thr.daemon = True
        thr.start()

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
            m = "{0}\033[{1}A".format("\n" * margin, margin)
            eprint("{0}\033[s\033[1;{1}r\033[u".format(m, self.g - 1))


ss = CTermsize()


def _scd(err, top):
    """non-recursive listing of directory contents, along with stat() info"""
    with os.scandir(top) as dh:
        for fh in dh:
            abspath = os.path.join(top, fh.name)
            try:
                yield [abspath, fh.stat()]
            except:
                err.append(abspath)


def _lsd(err, top):
    """non-recursive listing of directory contents, along with stat() info"""
    for name in os.listdir(top):
        abspath = os.path.join(top, name)
        try:
            yield [abspath, os.stat(abspath)]
        except:
            err.append(abspath)


if hasattr(os, "scandir"):
    statdir = _scd
else:
    statdir = _lsd


def walkdir(err, top):
    """recursive statdir"""
    for ap, inf in sorted(statdir(err, top)):
        if stat.S_ISDIR(inf.st_mode):
            try:
                for x in walkdir(err, ap):
                    yield x
            except:
                err.append(ap)
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
            for ap, inf in walkdir(err, top):
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
            if nchunks <= 256 or chunksize >= 32 * 1024 * 1024:
                return chunksize

            chunksize += stepsize
            stepsize *= mul


# mostly from copyparty/up2k.py
def get_hashlist(file, pcb):
    # type: (File, any) -> None
    """generates the up2k hashlist from file contents, inserts it into `file`"""

    chunk_sz = up2k_chunksize(file.size)
    file_rem = file.size
    file_ofs = 0
    ret = []
    with open(file.abs, "rb", 512 * 1024) as f:
        while file_rem > 0:
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


def handshake(req_ses, url, file, pw, search):
    # type: (requests.Session, str, File, any, bool) -> List[str]
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
        except:
            eprint("handshake failed, retrying: {0}\n".format(file.name))
            time.sleep(1)

    try:
        r = r.json()
    except:
        raise Exception(r.text)

    if search:
        return r["hits"]

    try:
        pre, url = url.split("://")
        pre += "://"
    except:
        pre = ""

    file.url = pre + url.split("/")[0] + r["purl"]
    file.name = r["name"]
    file.wark = r["wark"]

    return r["hash"]


def upload(req_ses, file, cid, pw):
    # type: (requests.Session, File, str, any) -> None
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


class Daemon(threading.Thread):
    def __init__(self, *a, **ka):
        threading.Thread.__init__(self, *a, **ka)
        self.daemon = True


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
            for x in err:
                eprint(x.decode("utf-8", "replace") + "\n")

            eprint("^ failed to access those {0} paths ^\n\n".format(len(err)))
            if not ar.ok:
                eprint("aborting because --ok is not set\n")
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
            self.safe()
        else:
            self.fancy()

    def safe(self):
        """minimal basic slow boring fallback codepath"""
        search = self.ar.s
        for nf, (top, rel, inf) in enumerate(self.filegen):
            file = File(top, rel, inf.st_size, inf.st_mtime)
            upath = file.abs.decode("utf-8", "replace")

            print("{0} {1}\n  hash...".format(self.nfiles - nf, upath))
            get_hashlist(file, None)

            burl = self.ar.url[:12] + self.ar.url[8:].split("/")[0] + "/"
            while True:
                print("  hs...")
                hs = handshake(req_ses, self.ar.url, file, self.ar.a, search)
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
                    upload(req_ses, file, cid, self.ar.a)

            print("  ok!")

    def fancy(self):
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

        self.t0 = time.time()
        self.t0_up = None
        self.spd = None

        self.mutex = threading.Lock()
        self.q_handshake = Queue()  # type: Queue[File]
        self.q_recheck = Queue()  # type: Queue[File]  # partial upload exists [...]
        self.q_upload = Queue()  # type: Queue[tuple[File, str]]

        self.st_hash = [None, "(idle, starting...)"]  # type: tuple[File, int]
        self.st_up = [None, "(idle, starting...)"]  # type: tuple[File, int]
        if VT100:
            atexit.register(self.cleanup_vt100)
            ss.scroll_region(3)

        Daemon(target=self.hasher).start()
        for _ in range(self.ar.j):
            Daemon(target=self.handshaker).start()
            Daemon(target=self.uploader).start()

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

                        m = "{0:6.1f}% {1} {2}\033[K"
                        txt += m.format(p, self.nfiles - f, name)

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
            left = humansize(self.nbytes - self.up_b)
            tail = "\033[K\033[u" if VT100 else "\r"

            m = "eta: {0} @ {1}/s, {2} left".format(eta, spd, left)
            eprint(txt + "\033]0;{0}\033\\\r{1}{2}".format(m, m, tail))

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
                        self.hash_b - self.up_b < 1024 * 1024 * 128
                        and self.hash_c - self.up_c < 64
                        and (
                            not self.ar.nh
                            or (
                                self.q_upload.empty()
                                and self.q_handshake.empty()
                                and not self.uploader_busy
                            )
                        )
                    ):
                        break

                time.sleep(0.05)

            get_hashlist(file, self.cb_hasher)
            with self.mutex:
                self.hash_f += 1
                self.hash_c += len(file.cids)
                self.hash_b += file.size

            self.q_handshake.put(file)

        self.hasher_busy = 0
        self.st_hash = [None, "(finished)"]

    def handshaker(self):
        search = self.ar.s
        q = self.q_handshake
        burl = self.ar.url[:8] + self.ar.url[8:].split("/")[0] + "/"
        while True:
            file = q.get()
            if not file:
                if q == self.q_handshake:
                    q = self.q_recheck
                    q.put(None)
                    continue

                self.q_upload.put(None)
                break

            with self.mutex:
                self.handshaker_busy += 1

            upath = file.abs.decode("utf-8", "replace")

            try:
                hs = handshake(req_ses, self.ar.url, file, self.ar.a, search)
            except Exception as ex:
                if q == self.q_handshake and "<pre>partial upload exists" in str(ex):
                    self.q_recheck.put(file)
                    hs = []
                else:
                    raise

            if search:
                if hs:
                    for hit in hs:
                        m = "found: {0}\n  {1}{2}\n"
                        print(m.format(upath, burl, hit["rp"]), end="")
                else:
                    print("NOT found: {0}\n".format(upath), end="")

                with self.mutex:
                    self.up_f += 1
                    self.up_c += len(file.cids)
                    self.up_b += file.size
                    self.handshaker_busy -= 1

                continue

            with self.mutex:
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
                upload(req_ses, file, cid, self.ar.a)
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

    # fmt: off
    ap = app = argparse.ArgumentParser(formatter_class=APF, epilog="""
NOTE:
source file/folder selection uses rsync syntax, meaning that:
  "foo" uploads the entire folder to URL/foo/
  "foo/" uploads the CONTENTS of the folder into URL/
""")

    ap.add_argument("url", type=unicode, help="server url, including destination folder")
    ap.add_argument("files", type=unicode, nargs="+", help="files and/or folders to process")
    ap.add_argument("-a", metavar="PASSWORD", help="password")
    ap.add_argument("-s", action="store_true", help="file-search (disables upload)")
    ap.add_argument("--ok", action="store_true", help="continue even if some local files are inaccessible")
    ap = app.add_argument_group("performance tweaks")
    ap.add_argument("-j", type=int, metavar="THREADS", default=4, help="parallel connections")
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

#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

"""
up2k.py: upload to copyparty
2021-09-27, v0.2, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/up2k.py

- dependencies: requests
- supports python 2.7 and 3.3 through 3.10

- no parallel hashing / uploads yet, so browsers are faster
- almost zero error-handling
- but if something breaks just try again and it'll autoresume
"""

import os
import sys
import stat
import math
import time
import base64
import hashlib
import argparse
import platform
import threading
import requests


# from copyparty/__init__.py
PY2 = sys.version_info[0] == 2
if PY2:
    from Queue import Queue

    sys.dont_write_bytecode = True
    bytes = str
else:
    from queue import Queue

    unicode = str

WINDOWS = False
if platform.system() == "Windows":
    WINDOWS = [int(x) for x in platform.version().split(".")]

VT100 = not WINDOWS or WINDOWS >= [10, 0, 14393]
# introduced in anniversary update


req_ses = requests.Session()


class File(object):
    """an up2k upload task; represents a single file"""

    def __init__(self, top, rel, size, lmod):
        self.top = top
        self.rel = rel.replace(b"\\", b"/")
        self.size = size
        self.lmod = lmod

        self.abs = os.path.join(top, rel)
        self.name = self.rel.split(b"/")[-1].decode("utf-8", "replace")

        # set by get_hashlist
        self.cids = []  # [ hash, ofs, sz ]
        self.kchunks = {}  # hash: [ ofs, sz ]

        # set by handshake
        self.ucids = []  # chunks which need to be uploaded
        self.wark = None
        self.url = None

        # set by upload
        self.uploading = []  # chunks currently being uploaded

        # m = "size({}) lmod({}) top({}) rel({}) abs({}) name({})"
        # print(m.format(self.size, self.lmod, self.top, self.rel, self.abs, self.name))


class FileSlice(object):
    """file-like object providing a fixed window into a file"""

    def __init__(self, file, cid):
        self.car, self.len = file.kchunks[cid]
        self.cdr = self.car + self.len
        self.ofs = 0
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


def statdir(top):
    """non-recursive listing of directory contents, along with stat() info"""
    if hasattr(os, "scandir"):
        with os.scandir(top) as dh:
            for fh in dh:
                yield [os.path.join(top, fh.name), fh.stat()]
    else:
        for name in os.listdir(top):
            abspath = os.path.join(top, name)
            yield [abspath, os.stat(abspath)]


def walkdir(top):
    """recursive statdir"""
    for ap, inf in statdir(top):
        if stat.S_ISDIR(inf.st_mode):
            for x in walkdir(ap):
                yield x
        else:
            yield ap, inf


def walkdirs(tops):
    """recursive statdir for a list of tops, yields [top, relpath, stat]"""
    for top in tops:
        if os.path.isdir(top):
            for ap, inf in walkdir(top):
                yield top, ap[len(top) + 1 :], inf
        else:
            sep = "{}".format(os.sep).encode("ascii")
            d, n = top.rsplit(sep, 1)
            yield d, n, os.stat(top)


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

    file.cids = ret
    file.kchunks = {k: [v1, v2] for k, v1, v2 in ret}


def handshake(req_ses, url, file, pw):
    # type: (requests.Session, str, File, any) -> List[str]
    """performs a handshake with the server; reply is a list of chunks to upload"""

    req = {
        "hash": [x[0] for x in file.cids],
        "name": file.name,
        "lmod": file.lmod,
        "size": file.size,
    }
    headers = {"Content-Type": "text/plain"}  # wtf ed
    if pw:
        headers["Cookie"] = "=".join(["cppwd", pw])

    if file.url:
        url = file.url
    elif b"/" in file.rel:
        url += file.rel.rsplit(b"/", 1)[0].decode("utf-8", "replace")

    r = req_ses.post(url, headers=headers, json=req)
    try:
        r = r.json()
    except:
        raise Exception(r.text)

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
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True


class Ctl(object):
    """
    this will be the coordinator which runs everything in parallel
    (hashing, handshakes, uploads)  but right now it's p dumb
    """

    def __init__(self, ar):
        self.ar = ar
        ar.url = ar.url.rstrip("/") + "/"
        ar.files = [
            os.path.abspath(os.path.realpath(x.encode("utf-8"))) for x in ar.files
        ]

        print("\nscanning {} locations".format(len(ar.files)))

        nfiles = 0
        nbytes = 0
        for _, _, inf in walkdirs(ar.files):
            nfiles += 1
            nbytes += inf.st_size

        print("found {} files, {}\n".format(nfiles, humansize(nbytes)))

        if ar.td:
            req_ses.verify = False
        if ar.te:
            req_ses.verify = ar.te

        self.filegen = walkdirs(ar.files)
        for nf, (top, rel, inf) in enumerate(self.filegen):
            file = File(top, rel, inf.st_size, inf.st_mtime)
            upath = file.abs.decode("utf-8", "replace")

            print("{} {}\n  hash...".format(nfiles - nf, upath))
            get_hashlist(file, None)

            while True:
                print("  hs...")
                up = handshake(req_ses, ar.url, file, ar.a)
                file.ucids = up
                if not up:
                    break

                print("{} {}".format(nfiles - nf, upath))
                ncs = len(up)
                for nc, cid in enumerate(up):
                    print("  {} up {}".format(ncs - nc, cid))
                    upload(req_ses, file, cid, ar.a)

            print("  ok!")


def main():
    time.strptime("19970815", "%Y%m%d")  # python#7980
    if WINDOWS:
        os.system("rem")  # enables colors

    # fmt: off
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("url", type=unicode, help="server url, including destination folder")
    ap.add_argument("files", type=unicode, nargs="+", help="files and/or folders to process")
    ap.add_argument("-a", metavar="PASSWORD", help="password")
    ap.add_argument("-te", metavar="PEM_FILE", help="certificate to expect/verify")
    ap.add_argument("-td", action="store_true", help="disable certificate check")
    # ap.add_argument("-j", type=int, default=2, help="parallel connections")
    # ap.add_argument("-nh", action="store_true", help="disable hashing while uploading")
    # fmt: on

    Ctl(ap.parse_args())


if __name__ == "__main__":
    main()

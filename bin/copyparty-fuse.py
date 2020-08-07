#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

"""copyparty-fuse: remote copyparty as a local filesystem"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"

import re
import os
import sys
import time
import stat
import errno
import struct
import builtins
import threading
import traceback
import http.client  # py2: httplib
import urllib.parse
from datetime import datetime
from urllib.parse import quote_from_bytes as quote

try:
    from fuse import FUSE, FuseOSError, Operations
except:
    print(
        "\n  could not import fuse; these may help:\n    python3 -m pip install --user fusepy\n    apt install libfuse\n    modprobe fuse\n"
    )
    raise


"""
mount a copyparty server (local or remote) as a filesystem

usage:
  python copyparty-fuse.py ./music http://192.168.1.69:3923/

dependencies (linux/macos):
  sudo apk add fuse
  python3 -m pip install --user fusepy

dependencies (windows):
  https://github.com/billziss-gh/winfsp/releases/latest
  python3 -m pip install --user fusepy
"""


WINDOWS = sys.platform == "win32"


def print(*args, **kwargs):
    try:
        builtins.print(*list(args), **kwargs)
    except:
        builtins.print(termsafe(" ".join(str(x) for x in args)), **kwargs)


def termsafe(txt):
    try:
        return txt.encode(sys.stdout.encoding, "backslashreplace").decode(
            sys.stdout.encoding
        )
    except:
        return txt.encode(sys.stdout.encoding, "replace").decode(sys.stdout.encoding)


def threadless_log(msg):
    print(msg + "\n", end="")


def boring_log(msg):
    msg = "\033[36m{:012x}\033[0m {}\n".format(threading.current_thread().ident, msg)
    print(msg[4:], end="")


def rice_tid():
    tid = threading.current_thread().ident
    c = struct.unpack(b"B" * 5, struct.pack(b">Q", tid)[-5:])
    return "".join("\033[1;37;48;5;{}m{:02x}".format(x, x) for x in c) + "\033[0m"


def fancy_log(msg):
    print("{} {}\n".format(rice_tid(), msg), end="")


def null_log(msg):
    pass


# set loglevel here
info = fancy_log
log = fancy_log
dbg = fancy_log
log = null_log
dbg = null_log


def get_tid():
    return threading.current_thread().ident


def html_dec(txt):
    return (
        txt.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
    )


class CacheNode(object):
    def __init__(self, tag, data):
        self.tag = tag
        self.data = data
        self.ts = time.time()


class Gateway(object):
    def __init__(self, base_url):
        self.base_url = base_url

        ui = urllib.parse.urlparse(base_url)
        self.web_root = ui.path.strip("/")
        try:
            self.web_host, self.web_port = ui.netloc.split(":")
            self.web_port = int(self.web_port)
        except:
            self.web_host = ui.netloc
            if ui.scheme == "http":
                self.web_port = 80
            elif ui.scheme == "https":
                raise Exception("todo")
            else:
                raise Exception("bad url?")

        self.conns = {}

    def quotep(self, path):
        # TODO: mojibake support
        path = path.encode("utf-8", "ignore")
        return quote(path, safe="/")

    def getconn(self, tid=None):
        tid = tid or get_tid()
        try:
            return self.conns[tid]
        except:
            info("new conn [{}] [{}]".format(self.web_host, self.web_port))

            conn = http.client.HTTPConnection(self.web_host, self.web_port, timeout=260)

            self.conns[tid] = conn
            return conn

    def closeconn(self, tid=None):
        tid = tid or get_tid()
        try:
            self.conns[tid].close()
            del self.conns[tid]
        except:
            pass

    def sendreq(self, *args, **kwargs):
        tid = get_tid()
        try:
            c = self.getconn(tid)
            c.request(*list(args), **kwargs)
            return c.getresponse()
        except:
            self.closeconn(tid)
            c = self.getconn(tid)
            c.request(*list(args), **kwargs)
            return c.getresponse()

    def listdir(self, path):
        web_path = self.quotep("/" + "/".join([self.web_root, path])) + "?dots"
        r = self.sendreq("GET", web_path)
        if r.status != 200:
            self.closeconn()
            raise Exception(
                "http error {} reading dir {} in {}".format(
                    r.status, web_path, rice_tid()
                )
            )

        try:
            return self.parse_html(r)
        except:
            traceback.print_exc()
            raise

    def download_file_range(self, path, ofs1, ofs2):
        web_path = self.quotep("/" + "/".join([self.web_root, path])) + "?raw"
        hdr_range = "bytes={}-{}".format(ofs1, ofs2 - 1)
        log("downloading {:4.0f}K, {}".format((ofs2 - ofs1) / 1024.0, hdr_range))

        r = self.sendreq("GET", web_path, headers={"Range": hdr_range})
        if r.status != http.client.PARTIAL_CONTENT:
            self.closeconn()
            raise Exception(
                "http error {} reading file {} range {} in {}".format(
                    r.status, web_path, hdr_range, rice_tid()
                )
            )

        return r.read()

    def parse_html(self, datasrc):
        ret = []
        remainder = b""
        ptn = re.compile(
            r"^<tr><td>(-|DIR)</td><td><a [^>]+>([^<]+)</a></td><td>([^<]+)</td><td>([^<]+)</td></tr>$"
        )

        while True:
            buf = remainder + datasrc.read(4096)
            # print('[{}]'.format(buf.decode('utf-8')))
            if not buf:
                break

            remainder = b""
            endpos = buf.rfind(b"\n")
            if endpos >= 0:
                remainder = buf[endpos + 1 :]
                buf = buf[:endpos]

            lines = buf.decode("utf-8").split("\n")
            for line in lines:
                m = ptn.match(line)
                if not m:
                    # print(line)
                    continue

                ftype, fname, fsize, fdate = m.groups()
                fname = html_dec(fname)
                sz = 1
                ts = 60 * 60 * 24 * 2
                try:
                    sz = int(fsize)
                    ts = datetime.strptime(fdate, "%Y-%m-%d %H:%M:%S").timestamp()
                except:
                    info("bad HTML or OS [{}] [{}]".format(fdate, fsize))
                    # python cannot strptime(1959-01-01) on windows

                if ftype == "-":
                    ret.append([fname, self.stat_file(ts, sz), 0])
                else:
                    ret.append([fname, self.stat_dir(ts, sz), 0])

        return ret

    def stat_dir(self, ts, sz=4096):
        return {
            "st_mode": stat.S_IFDIR | 0o555,
            "st_uid": 1000,
            "st_gid": 1000,
            "st_size": sz,
            "st_atime": ts,
            "st_mtime": ts,
            "st_ctime": ts,
            "st_blocks": int((sz + 511) / 512),
        }

    def stat_file(self, ts, sz):
        return {
            "st_mode": stat.S_IFREG | 0o444,
            "st_uid": 1000,
            "st_gid": 1000,
            "st_size": sz,
            "st_atime": ts,
            "st_mtime": ts,
            "st_ctime": ts,
            "st_blocks": int((sz + 511) / 512),
        }


class CPPF(Operations):
    def __init__(self, base_url, dircache, filecache):
        self.gw = Gateway(base_url)
        self.junk_fh_ctr = 3
        self.n_dircache = dircache
        self.n_filecache = filecache

        self.dircache = []
        self.dircache_mtx = threading.Lock()

        self.filecache = []
        self.filecache_mtx = threading.Lock()

        info("up")

    def _describe(self):
        msg = ""
        for n, cn in enumerate(self.filecache):
            cache_path, cache1 = cn.tag
            cache2 = cache1 + len(cn.data)
            msg += "\n#{} = {}  {}  {}\n{}\n".format(
                n, cache1, len(cn.data), cache2, cache_path
            )
        return msg

    def clean_dircache(self):
        """not threadsafe"""
        now = time.time()
        cutoff = 0
        for cn in self.dircache:
            if now - cn.ts > self.n_dircache:
                cutoff += 1
            else:
                break

        if cutoff > 0:
            self.dircache = self.dircache[cutoff:]

    def get_cached_dir(self, dirpath):
        with self.dircache_mtx:
            self.clean_dircache()
            for cn in self.dircache:
                if cn.tag == dirpath:
                    return cn

        return None

    """
            ,-------------------------------,  g1>=c1, g2<=c2
            |cache1                   cache2|  buf[g1-c1:(g1-c1)+(g2-g1)]
            `-------------------------------'
                    ,---------------,
                    |get1       get2|
                    `---------------'
    __________________________________________________________________________

            ,-------------------------------,  g2<=c2, (g2>=c1)
            |cache1                   cache2|  cdr=buf[:g2-c1]
            `-------------------------------'  dl car; g1-512K:c1
    ,---------------,
    |get1       get2|
    `---------------'
    __________________________________________________________________________

            ,-------------------------------,  g1>=c1, (g1<=c2)
            |cache1                   cache2|  car=buf[c2-g1:]
            `-------------------------------'  dl cdr; c2:c2+1M
                                    ,---------------,
                                    |get1       get2|
                                    `---------------'
    """

    def get_cached_file(self, path, get1, get2, file_sz):
        car = None
        cdr = None
        ncn = -1
        with self.filecache_mtx:
            dbg("cache request from {} to {}, size {}".format(get1, get2, file_sz))
            for cn in self.filecache:
                ncn += 1

                cache_path, cache1 = cn.tag
                if cache_path != path:
                    continue

                cache2 = cache1 + len(cn.data)
                if get2 <= cache1 or get1 >= cache2:
                    continue

                if get1 >= cache1 and get2 <= cache2:
                    # keep cache entry alive by moving it to the end
                    self.filecache = (
                        self.filecache[:ncn] + self.filecache[ncn + 1 :] + [cn]
                    )
                    buf_ofs = get1 - cache1
                    buf_end = buf_ofs + (get2 - get1)
                    dbg(
                        "found all ({}, {} to {}, len {}) [{}:{}] = {}".format(
                            ncn,
                            cache1,
                            cache2,
                            len(cn.data),
                            buf_ofs,
                            buf_end,
                            buf_end - buf_ofs,
                        )
                    )
                    return cn.data[buf_ofs:buf_end]

                if get2 < cache2:
                    x = cn.data[: get2 - cache1]
                    if not cdr or len(cdr) < len(x):
                        dbg(
                            "found car ({}, {} to {}, len {}) [:{}-{}] = [:{}] = {}".format(
                                ncn,
                                cache1,
                                cache2,
                                len(cn.data),
                                get2,
                                cache1,
                                get2 - cache1,
                                len(x),
                            )
                        )
                        cdr = x

                    continue

                if get1 > cache1:
                    x = cn.data[-(cache2 - get1) :]
                    if not car or len(car) < len(x):
                        dbg(
                            "found cdr ({}, {} to {}, len {}) [-({}-{}):] = [-{}:] = {}".format(
                                ncn,
                                cache1,
                                cache2,
                                len(cn.data),
                                cache2,
                                get1,
                                cache2 - get1,
                                len(x),
                            )
                        )
                        car = x

                    continue

                msg = "cache fallthrough\n{} {} {}\n{} {} {}\n{} {} --\n".format(
                    get1,
                    get2,
                    get2 - get1,
                    cache1,
                    cache2,
                    cache2 - cache1,
                    get1 - cache1,
                    get2 - cache2,
                )
                msg += self._describe()
                raise Exception(msg)

        if car and cdr:
            dbg("<cache> have both")

            ret = car + cdr
            if len(ret) == get2 - get1:
                return ret

            msg = "{} + {} != {} - {}".format(len(car), len(cdr), get2, get1)
            msg += self._describe()
            raise Exception(msg)

        elif cdr:
            h_end = get1 + (get2 - get1) - len(cdr)
            h_ofs = h_end - 512 * 1024

            if h_ofs < 0:
                h_ofs = 0

            buf_ofs = (get2 - get1) - len(cdr)

            dbg(
                "<cache> cdr {}, car {}-{}={} [-{}:]".format(
                    len(cdr), h_ofs, h_end, h_end - h_ofs, buf_ofs
                )
            )

            buf = self.gw.download_file_range(path, h_ofs, h_end)
            ret = buf[-buf_ofs:] + cdr

        elif car:
            h_ofs = get1 + len(car)
            h_end = h_ofs + 1024 * 1024

            if h_end > file_sz:
                h_end = file_sz

            buf_ofs = (get2 - get1) - len(car)

            dbg(
                "<cache> car {}, cdr {}-{}={} [:{}]".format(
                    len(car), h_ofs, h_end, h_end - h_ofs, buf_ofs
                )
            )

            buf = self.gw.download_file_range(path, h_ofs, h_end)
            ret = car + buf[:buf_ofs]

        else:
            h_ofs = get1 - 256 * 1024
            h_end = get2 + 1024 * 1024

            if h_ofs < 0:
                h_ofs = 0

            if h_end > file_sz:
                h_end = file_sz

            buf_ofs = get1 - h_ofs
            buf_end = buf_ofs + get2 - get1

            dbg(
                "<cache> {}-{}={} [{}:{}]".format(
                    h_ofs, h_end, h_end - h_ofs, buf_ofs, buf_end
                )
            )

            buf = self.gw.download_file_range(path, h_ofs, h_end)
            ret = buf[buf_ofs:buf_end]

        cn = CacheNode([path, h_ofs], buf)
        with self.filecache_mtx:
            if len(self.filecache) >= self.n_filecache:
                self.filecache = self.filecache[1:] + [cn]
            else:
                self.filecache.append(cn)

        return ret

    def _readdir(self, path, fh=None):
        path = path.strip("/")
        log("readdir [{}] [{}]".format(path, fh))

        ret = self.gw.listdir(path)
        if not self.n_dircache:
            return ret

        with self.dircache_mtx:
            cn = CacheNode(path, ret)
            self.dircache.append(cn)
            self.clean_dircache()

        return ret

    def readdir(self, path, fh=None):
        return [".", ".."] + self._readdir(path, fh)

    def read(self, path, length, offset, fh=None):
        path = path.strip("/")

        ofs2 = offset + length
        log("read {} @ {} len {} end {}".format(path, offset, length, ofs2))

        file_sz = self.getattr(path)["st_size"]
        if ofs2 > file_sz:
            ofs2 = file_sz
            log("truncate to len {} end {}".format(ofs2 - offset, ofs2))

        if file_sz == 0 or offset >= ofs2:
            return b""

        if not self.n_filecache:
            return self.gw.download_file_range(path, offset, ofs2)

        return self.get_cached_file(path, offset, ofs2, file_sz)

    def getattr(self, path, fh=None):
        log("getattr [{}]".format(path))

        path = path.strip("/")
        try:
            dirpath, fname = path.rsplit("/", 1)
        except:
            dirpath = ""
            fname = path

        if not path:
            ret = self.gw.stat_dir(time.time())
            # dbg("=" + repr(ret))
            return ret

        cn = self.get_cached_dir(dirpath)
        if cn:
            log("cache ok")
            dents = cn.data
        else:
            log("cache miss")
            dents = self._readdir(dirpath)

        for cache_name, cache_stat, _ in dents:
            if cache_name == fname:
                # dbg("=" + repr(cache_stat))
                return cache_stat

        log("=404 ({})".format(path))
        raise FuseOSError(errno.ENOENT)

    access = None
    flush = None
    getxattr = None
    listxattr = None
    open = None
    opendir = None
    release = None
    releasedir = None
    statfs = None

    if False:
        # incorrect semantics but good for debugging stuff like samba and msys2
        def access(self, path, mode):
            log("@@ access [{}] [{}]".format(path, mode))
            return 1 if self.getattr(path) else 0

        def flush(self, path, fh):
            log("@@ flush [{}] [{}]".format(path, fh))
            return True

        def getxattr(self, *args):
            log("@@ getxattr [{}]".format("] [".join(str(x) for x in args)))
            return False

        def listxattr(self, *args):
            log("@@ listxattr [{}]".format("] [".join(str(x) for x in args)))
            return False

        def open(self, path, flags):
            log("@@ open [{}] [{}]".format(path, flags))
            return 42

        def opendir(self, fh):
            log("@@ opendir [{}]".format(fh))
            return 69

        def release(self, ino, fi):
            log("@@ release [{}] [{}]".format(ino, fi))
            return True

        def releasedir(self, ino, fi):
            log("@@ releasedir [{}] [{}]".format(ino, fi))
            return True

        def statfs(self, path):
            log("@@ statfs [{}]".format(path))
            return {}

    if sys.platform == "win32":
        # quick compat for /mingw64/bin/python3 (msys2)
        def _open(self, path):
            try:
                x = self.getattr(path)
                if x["st_mode"] <= 0:
                    raise Exception()

                self.junk_fh_ctr += 1
                if self.junk_fh_ctr > 32000:  # TODO untested
                    self.junk_fh_ctr = 4

                return self.junk_fh_ctr

            except Exception as ex:
                log("open ERR {}".format(repr(ex)))
                raise FuseOSError(errno.ENOENT)

        def open(self, path, flags):
            log("open [{}] [{}]".format(path, flags))
            return self._open(path)

        def opendir(self, path):
            log("opendir [{}]".format(path))
            return self._open(path)

        def flush(self, path, fh):
            log("flush [{}] [{}]".format(path, fh))

        def release(self, ino, fi):
            log("release [{}] [{}]".format(ino, fi))

        def releasedir(self, ino, fi):
            log("releasedir [{}] [{}]".format(ino, fi))

        def access(self, path, mode):
            log("access [{}] [{}]".format(path, mode))
            try:
                x = self.getattr(path)
                if x["st_mode"] <= 0:
                    raise Exception()
            except:
                raise FuseOSError(errno.ENOENT)


def main():
    try:
        local, remote = sys.argv[1:3]
        filecache = 7 if len(sys.argv) <= 3 else int(sys.argv[3])
        dircache = 1 if len(sys.argv) <= 4 else float(sys.argv[4])
    except:
        where = "local directory"
        if WINDOWS:
            where += " or DRIVE:"

        print("need arg 1: " + where)
        print("need arg 2: root url")
        print("optional 3: num files in filecache (7)")
        print("optional 4: num seconds / dircache (1)")
        print()
        print("example:")
        print("  copyparty-fuse.py ./music http://192.168.1.69:3923/music/")
        if WINDOWS:
            print("  copyparty-fuse.py M: http://192.168.1.69:3923/music/")

        return

    if WINDOWS:
        os.system("")

    FUSE(
        CPPF(remote, dircache, filecache),
        local,
        foreground=True,
        nothreads=True,
        allow_other=True,
        nonempty=True,
    )


if __name__ == "__main__":
    main()

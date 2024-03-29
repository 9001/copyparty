#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

"""partyfuse2: remote copyparty as a local filesystem"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2020
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"

import re
import os
import sys
import time
import json
import stat
import errno
import struct
import codecs
import platform
import threading
import http.client  # py2: httplib
import urllib.parse
from datetime import datetime
from urllib.parse import quote_from_bytes as quote
from urllib.parse import unquote_to_bytes as unquote

try:
    import fuse
    from fuse import Fuse

    fuse.fuse_python_api = (0, 2)
    if not hasattr(fuse, "__version__"):
        raise Exception("your fuse-python is way old")
except:
    if WINDOWS:
        libfuse = "install https://github.com/billziss-gh/winfsp/releases/latest"
    elif MACOS:
        libfuse = "install https://osxfuse.github.io/"
    else:
        libfuse = "apt install libfuse\n    modprobe fuse"

    m = """\033[33m
  could not import fuse; these may help:
    {} -m pip install --user fuse-python
    {}
\033[0m"""
    print(m.format(sys.executable, libfuse))
    raise


"""
mount a copyparty server (local or remote) as a filesystem

usage:
  python ./partyfuse2.py -f -o allow_other,auto_unmount,nonempty,pw=wark,url=http://192.168.1.69:3923 /mnt/nas

dependencies:
  sudo apk add fuse-dev python3-dev
  python3 -m pip install --user fuse-python

fork of partyfuse.py based on fuse-python which
  appears to be more compliant than fusepy? since this works with samba
    (probably just my garbage code tbh)
"""


WINDOWS = sys.platform == "win32"
MACOS = platform.system() == "Darwin"


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


def register_wtf8():
    def wtf8_enc(text):
        return str(text).encode("utf-8", "surrogateescape"), len(text)

    def wtf8_dec(binary):
        return bytes(binary).decode("utf-8", "surrogateescape"), len(binary)

    def wtf8_search(encoding_name):
        return codecs.CodecInfo(wtf8_enc, wtf8_dec, name="wtf-8")

    codecs.register(wtf8_search)


bad_good = {}
good_bad = {}


def enwin(txt):
    return "".join([bad_good.get(x, x) for x in txt])

    for bad, good in bad_good.items():
        txt = txt.replace(bad, good)

    return txt


def dewin(txt):
    return "".join([good_bad.get(x, x) for x in txt])

    for bad, good in bad_good.items():
        txt = txt.replace(good, bad)

    return txt


class CacheNode(object):
    def __init__(self, tag, data):
        self.tag = tag
        self.data = data
        self.ts = time.time()


class Stat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 1
        self.st_uid = 1000
        self.st_gid = 1000
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


class Gateway(object):
    def __init__(self, base_url, pw):
        self.base_url = base_url
        self.pw = pw

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
        path = path.encode("wtf-8")
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

    def sendreq(self, *args, **ka):
        tid = get_tid()
        if self.pw:
            ck = "cppwd=" + self.pw
            try:
                ka["headers"]["Cookie"] = ck
            except:
                ka["headers"] = {"Cookie": ck}
        try:
            c = self.getconn(tid)
            c.request(*list(args), **ka)
            return c.getresponse()
        except:
            self.closeconn(tid)
            c = self.getconn(tid)
            c.request(*list(args), **ka)
            return c.getresponse()

    def listdir(self, path):
        if bad_good:
            path = dewin(path)

        web_path = self.quotep("/" + "/".join([self.web_root, path])) + "?dots&ls"
        r = self.sendreq("GET", web_path)
        if r.status != 200:
            self.closeconn()
            raise Exception(
                "http error {} reading dir {} in {}".format(
                    r.status, web_path, rice_tid()
                )
            )

        return self.parse_jls(r)

    def download_file_range(self, path, ofs1, ofs2):
        if bad_good:
            path = dewin(path)

        web_path = self.quotep("/" + "/".join([self.web_root, path])) + "?raw"
        hdr_range = "bytes={}-{}".format(ofs1, ofs2 - 1)
        log("downloading {}".format(hdr_range))

        r = self.sendreq("GET", web_path, headers={"Range": hdr_range})
        if r.status != http.client.PARTIAL_CONTENT:
            self.closeconn()
            raise Exception(
                "http error {} reading file {} range {} in {}".format(
                    r.status, web_path, hdr_range, rice_tid()
                )
            )

        return r.read()

    def parse_jls(self, datasrc):
        rsp = b""
        while True:
            buf = datasrc.read(1024 * 32)
            if not buf:
                break

            rsp += buf

        rsp = json.loads(rsp.decode("utf-8"))
        ret = []
        for statfun, nodes in [
            [self.stat_dir, rsp["dirs"]],
            [self.stat_file, rsp["files"]],
        ]:
            for n in nodes:
                fname = unquote(n["href"].split("?")[0]).rstrip(b"/").decode("wtf-8")
                if bad_good:
                    fname = enwin(fname)

                ret.append([fname, statfun(n["ts"], n["sz"]), 0])

        return ret

    def stat_dir(self, ts, sz=4096):
        ret = Stat()
        ret.st_mode = stat.S_IFDIR | 0o555
        ret.st_nlink = 2
        ret.st_size = sz
        ret.st_atime = ts
        ret.st_mtime = ts
        ret.st_ctime = ts
        return ret

    def stat_file(self, ts, sz):
        ret = Stat()
        ret.st_mode = stat.S_IFREG | 0o444
        ret.st_size = sz
        ret.st_atime = ts
        ret.st_mtime = ts
        ret.st_ctime = ts
        return ret


class CPPF(Fuse):
    def __init__(self, *args, **kwargs):
        Fuse.__init__(self, *args, **kwargs)

        self.url = None
        self.pw = None

        self.dircache = []
        self.dircache_mtx = threading.Lock()

        self.filecache = []
        self.filecache_mtx = threading.Lock()

    def init2(self):
        # TODO figure out how python-fuse wanted this to go
        self.gw = Gateway(self.url, self.pw)  # .decode('utf-8'))
        info("up")

    def clean_dircache(self):
        """not threadsafe"""
        now = time.time()
        cutoff = 0
        for cn in self.dircache:
            if now - cn.ts > 1:
                cutoff += 1
            else:
                break

        if cutoff > 0:
            self.dircache = self.dircache[cutoff:]

    def get_cached_dir(self, dirpath):
        # with self.dircache_mtx:
        if True:
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
        # with self.filecache_mtx:
        if True:
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

                raise Exception("what")

        if car and cdr:
            dbg("<cache> have both")

            ret = car + cdr
            if len(ret) == get2 - get1:
                return ret

            raise Exception("{} + {} != {} - {}".format(len(car), len(cdr), get2, get1))

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
        # with self.filecache_mtx:
        if True:
            if len(self.filecache) > 6:
                self.filecache = self.filecache[1:] + [cn]
            else:
                self.filecache.append(cn)

        return ret

    def _readdir(self, path):
        path = path.strip("/")
        log("readdir {}".format(path))

        ret = self.gw.listdir(path)

        # with self.dircache_mtx:
        if True:
            cn = CacheNode(path, ret)
            self.dircache.append(cn)
            self.clean_dircache()

        return ret

    def readdir(self, path, offset):
        for e in self._readdir(path)[offset:]:
            # log("yield [{}]".format(e[0]))
            yield fuse.Direntry(e[0])

    def open(self, path, flags):
        if (flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)) != os.O_RDONLY:
            return -errno.EACCES

        st = self.getattr(path)
        try:
            if st.st_nlink > 0:
                return st
        except:
            return st  # -int(os.errcode)

    def read(self, path, length, offset, fh=None, *args):
        if args:
            log("unexpected args [" + "] [".join(repr(x) for x in args) + "]")
            raise Exception()

        path = path.strip("/")

        ofs2 = offset + length
        log("read {} @ {} len {} end {}".format(path, offset, length, ofs2))

        st = self.getattr(path)
        try:
            file_sz = st.st_size
        except:
            return st  # -int(os.errcode)

        if ofs2 > file_sz:
            ofs2 = file_sz
            log("truncate to len {} end {}".format(ofs2 - offset, ofs2))

        if file_sz == 0 or offset >= ofs2:
            return b""

        # toggle cache here i suppose
        # return self.get_cached_file(path, offset, ofs2, file_sz)
        return self.gw.download_file_range(path, offset, ofs2)

    def getattr(self, path):
        log("getattr [{}]".format(path))
        if WINDOWS:
            path = enwin(path)  # windows occasionally decodes f0xx to xx

        path = path.strip("/")
        try:
            dirpath, fname = path.rsplit("/", 1)
        except:
            dirpath = ""
            fname = path

        if not path:
            ret = self.gw.stat_dir(time.time())
            dbg("=root")
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
                dbg("=file")
                return cache_stat

        log("=404")
        return -errno.ENOENT


def main():
    time.strptime("19970815", "%Y%m%d")  # python#7980
    register_wtf8()
    if WINDOWS:
        os.system("rem")

        for ch in '<>:"\\|?*':
            # microsoft maps illegal characters to f0xx
            # (e000 to f8ff is basic-plane private-use)
            bad_good[ch] = chr(ord(ch) + 0xF000)

        for n in range(0, 0x100):
            # map surrogateescape to another private-use area
            bad_good[chr(n + 0xDC00)] = chr(n + 0xF100)

        for k, v in bad_good.items():
            good_bad[v] = k

    server = CPPF()
    server.parser.add_option(mountopt="url", metavar="BASE_URL", default=None)
    server.parser.add_option(mountopt="pw", metavar="PASSWORD", default=None)
    server.parse(values=server, errex=1)
    if not server.url or not str(server.url).startswith("http"):
        print("\nerror:")
        print("  need argument: -o url=<...>")
        print("  need argument: mount-path")
        print("example:")
        print(
            "  ./partyfuse2.py -f -o allow_other,auto_unmount,nonempty,pw=wark,url=http://192.168.1.69:3923 /mnt/nas"
        )
        sys.exit(1)

    server.init2()
    threading.Thread(target=server.main, daemon=True).start()
    while True:
        time.sleep(9001)


if __name__ == "__main__":
    main()

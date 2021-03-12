#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

"""copyparty-fuse: remote copyparty as a local filesystem"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"


"""
mount a copyparty server (local or remote) as a filesystem

usage:
  python copyparty-fuse.py http://192.168.1.69:3923/  ./music

dependencies:
  python3 -m pip install --user fusepy
  + on Linux: sudo apk add fuse
  + on Macos: https://osxfuse.github.io/
  + on Windows: https://github.com/billziss-gh/winfsp/releases/latest

note:
  you probably want to run this on windows clients:
  https://github.com/9001/copyparty/blob/master/contrib/explorer-nothumbs-nofoldertypes.reg

get server cert:
  awk '/-BEGIN CERTIFICATE-/ {a=1} a; /-END CERTIFICATE-/{exit}' <(openssl s_client -connect 127.0.0.1:3923 </dev/null 2>/dev/null) >cert.pem
"""


import re
import os
import sys
import time
import json
import stat
import errno
import struct
import codecs
import builtins
import platform
import argparse
import threading
import traceback
import http.client  # py2: httplib
import urllib.parse
from datetime import datetime
from urllib.parse import quote_from_bytes as quote
from urllib.parse import unquote_to_bytes as unquote

WINDOWS = sys.platform == "win32"
MACOS = platform.system() == "Darwin"
info = log = dbg = None


try:
    from fuse import FUSE, FuseOSError, Operations
except:
    if WINDOWS:
        libfuse = "install https://github.com/billziss-gh/winfsp/releases/latest"
    elif MACOS:
        libfuse = "install https://osxfuse.github.io/"
    else:
        libfuse = "apt install libfuse\n    modprobe fuse"

    print(
        "\n  could not import fuse; these may help:"
        + "\n    python3 -m pip install --user fusepy\n    "
        + libfuse
        + "\n"
    )
    raise


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
    print("{:10.6f} {} {}\n".format(time.time() % 900, rice_tid(), msg), end="")


def null_log(msg):
    pass


def hexler(binary):
    return binary.replace("\r", "\\r").replace("\n", "\\n")
    return " ".join(["{}\033[36m{:02x}\033[0m".format(b, ord(b)) for b in binary])
    return " ".join(map(lambda b: format(ord(b), "02x"), binary))


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


class RecentLog(object):
    def __init__(self):
        self.mtx = threading.Lock()
        self.f = None  # open("copyparty-fuse.log", "wb")
        self.q = []

        thr = threading.Thread(target=self.printer)
        thr.daemon = True
        thr.start()

    def put(self, msg):
        msg = "{:10.6f} {} {}\n".format(time.time() % 900, rice_tid(), msg)
        if self.f:
            fmsg = " ".join([datetime.utcnow().strftime("%H%M%S.%f"), str(msg)])
            self.f.write(fmsg.encode("utf-8"))

        with self.mtx:
            self.q.append(msg)
            if len(self.q) > 200:
                self.q = self.q[-50:]

    def printer(self):
        while True:
            time.sleep(0.05)
            with self.mtx:
                q = self.q
                if not q:
                    continue

                self.q = []

            print("".join(q), end="")


# [windows/cmd/cpy3]  python dev\copyparty\bin\copyparty-fuse.py q: http://192.168.1.159:1234/
# [windows/cmd/msys2] C:\msys64\mingw64\bin\python3 dev\copyparty\bin\copyparty-fuse.py q: http://192.168.1.159:1234/
# [windows/mty/msys2] /mingw64/bin/python3 /c/Users/ed/dev/copyparty/bin/copyparty-fuse.py q: http://192.168.1.159:1234/
#
# [windows] find /q/music/albums/Phant*24bit -printf '%s %p\n' | sort -n | tail -n 8 | sed -r 's/^[0-9]+ //' | while IFS= read -r x; do dd if="$x" of=/dev/null bs=4k count=8192 & done
# [alpine]  ll t; for x in t/2020_0724_16{2,3}*; do dd if="$x" of=/dev/null bs=4k count=10240 & done
#
#  72.4983 windows mintty msys2 fancy_log
# 219.5781 windows cmd msys2 fancy_log
# nope.avi windows cmd cpy3 fancy_log
#   9.8817 windows mintty msys2 RecentLog 200 50 0.1
#  10.2241 windows cmd cpy3 RecentLog 200 50 0.1
#   9.8494 windows cmd msys2 RecentLog 200 50 0.1
#   7.8061 windows mintty msys2 fancy_log <info-only>
#   7.9961 windows mintty msys2 RecentLog <info-only>
#   4.2603 alpine xfce4 cpy3 RecentLog
#   4.1538 alpine xfce4 cpy3 fancy_log
#   3.1742 alpine urxvt cpy3 fancy_log


def get_tid():
    return threading.current_thread().ident


def html_dec(txt):
    return (
        txt.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#13;", "\r")
        .replace("&#10;", "\n")
        .replace("&amp;", "&")
    )


class CacheNode(object):
    def __init__(self, tag, data):
        self.tag = tag
        self.data = data
        self.ts = time.time()


class Gateway(object):
    def __init__(self, ar):
        self.base_url = ar.base_url
        self.password = ar.a

        ui = urllib.parse.urlparse(self.base_url)
        self.web_root = ui.path.strip("/")
        try:
            self.web_host, self.web_port = ui.netloc.split(":")
            self.web_port = int(self.web_port)
        except:
            self.web_host = ui.netloc
            if ui.scheme == "http":
                self.web_port = 80
            elif ui.scheme == "https":
                self.web_port = 443
            else:
                raise Exception("bad url?")

        self.ssl_context = None
        self.use_tls = ui.scheme.lower() == "https"
        if self.use_tls:
            import ssl

            if ar.td:
                self.ssl_context = ssl._create_unverified_context()
            elif ar.te:
                self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                self.ssl_context.load_verify_locations(ar.te)

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

            args = {}
            if not self.use_tls:
                C = http.client.HTTPConnection
            else:
                C = http.client.HTTPSConnection
                if self.ssl_context:
                    args = {"context": self.ssl_context}

            conn = C(self.web_host, self.web_port, timeout=260, **args)

            self.conns[tid] = conn
            return conn

    def closeconn(self, tid=None):
        tid = tid or get_tid()
        try:
            self.conns[tid].close()
            del self.conns[tid]
        except:
            pass

    def sendreq(self, *args, headers={}, **kwargs):
        tid = get_tid()
        if self.password:
            headers["Cookie"] = "=".join(["cppwd", self.password])

        try:
            c = self.getconn(tid)
            c.request(*list(args), headers=headers, **kwargs)
            return c.getresponse()
        except:
            dbg("bad conn")

        self.closeconn(tid)
        try:
            c = self.getconn(tid)
            c.request(*list(args), headers=headers, **kwargs)
            return c.getresponse()
        except:
            info("http connection failed:\n" + traceback.format_exc())
            if self.use_tls and not self.ssl_context:
                import ssl

                cert = ssl.get_server_certificate((self.web_host, self.web_port))
                info("server certificate probably not trusted:\n" + cert)

            raise

    def listdir(self, path):
        if bad_good:
            path = dewin(path)

        web_path = self.quotep("/" + "/".join([self.web_root, path])) + "?dots&ls"
        r = self.sendreq("GET", web_path)
        if r.status != 200:
            self.closeconn()
            log(
                "http error {} reading dir {} in {}".format(
                    r.status, web_path, rice_tid()
                )
            )
            raise FuseOSError(errno.ENOENT)

        ctype = r.getheader("Content-Type", "")
        if ctype == "application/json":
            parser = self.parse_jls
        elif ctype.startswith("text/html"):
            parser = self.parse_html
        else:
            log("listdir on file: {}".format(path))
            raise FuseOSError(errno.ENOENT)

        try:
            return parser(r)
        except:
            info(repr(path) + "\n" + traceback.format_exc())
            raise

    def download_file_range(self, path, ofs1, ofs2):
        if bad_good:
            path = dewin(path)

        web_path = self.quotep("/" + "/".join([self.web_root, path])) + "?raw"
        hdr_range = "bytes={}-{}".format(ofs1, ofs2 - 1)
        info(
            "DL {:4.0f}K\033[36m{:>9}-{:<9}\033[0m{}".format(
                (ofs2 - ofs1) / 1024.0, ofs1, ofs2 - 1, hexler(path)
            )
        )

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
        for is_dir, nodes in [[True, rsp["dirs"]], [False, rsp["files"]]]:
            for n in nodes:
                fname = unquote(n["href"]).rstrip(b"/")
                fname = fname.decode("wtf-8")
                if bad_good:
                    fname = enwin(fname)

                fun = self.stat_dir if is_dir else self.stat_file
                ret.append([fname, fun(n["ts"], n["sz"]), 0])

        return ret

    def parse_html(self, datasrc):
        ret = []
        remainder = b""
        ptn = re.compile(
            r'^<tr><td>(-|DIR|<a [^<]+</a>)</td><td><a[^>]* href="([^"]+)"[^>]*>([^<]+)</a></td><td>([^<]+)</td><td>[^<]+</td><td>([^<]+)</td></tr>$'
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

                ftype, furl, fname, fsize, fdate = m.groups()
                fname = furl.rstrip("/").split("/")[-1]
                fname = unquote(fname)
                fname = fname.decode("wtf-8")
                if bad_good:
                    fname = enwin(fname)

                sz = 1
                ts = 60 * 60 * 24 * 2
                try:
                    sz = int(fsize)
                    ts = datetime.strptime(fdate, "%Y-%m-%d %H:%M:%S").timestamp()
                except:
                    info("bad HTML or OS [{}] [{}]".format(fdate, fsize))
                    # python cannot strptime(1959-01-01) on windows

                if ftype != "DIR":
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
    def __init__(self, ar):
        self.gw = Gateway(ar)
        self.junk_fh_ctr = 3
        self.n_dircache = ar.cd
        self.n_filecache = ar.cf

        self.dircache = []
        self.dircache_mtx = threading.Lock()

        self.filecache = []
        self.filecache_mtx = threading.Lock()

        info("up")

    def _describe(self):
        msg = ""
        with self.filecache_mtx:
            for n, cn in enumerate(self.filecache):
                cache_path, cache1 = cn.tag
                cache2 = cache1 + len(cn.data)
                msg += "\n{:<2} {:>7} {:>10}:{:<9} {}".format(
                    n,
                    len(cn.data),
                    cache1,
                    cache2,
                    cache_path.replace("\r", "\\r").replace("\n", "\\n"),
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
        dbg("cache request {}:{} |{}|".format(get1, get2, file_sz) + self._describe())
        with self.filecache_mtx:
            for cn in self.filecache:
                ncn += 1

                cache_path, cache1 = cn.tag
                if cache_path != path:
                    continue

                cache2 = cache1 + len(cn.data)
                if get2 <= cache1 or get1 >= cache2:
                    # request does not overlap with cached area at all
                    continue

                if get1 < cache1 and get2 > cache2:
                    # cached area does overlap, but must specifically contain
                    # either the first or last byte in the requested range
                    continue

                if get1 >= cache1 and get2 <= cache2:
                    # keep cache entry alive by moving it to the end
                    self.filecache = (
                        self.filecache[:ncn] + self.filecache[ncn + 1 :] + [cn]
                    )
                    buf_ofs = get1 - cache1
                    buf_end = buf_ofs + (get2 - get1)
                    dbg(
                        "found all (#{} {}:{} |{}|) [{}:{}] = {}".format(
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

                if get2 <= cache2:
                    x = cn.data[: get2 - cache1]
                    if not cdr or len(cdr) < len(x):
                        dbg(
                            "found cdr (#{} {}:{} |{}|) [:{}-{}] = [:{}] = {}".format(
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

                if get1 >= cache1:
                    x = cn.data[-(max(0, cache2 - get1)) :]
                    if not car or len(car) < len(x):
                        dbg(
                            "found car (#{} {}:{} |{}|) [-({}-{}):] = [-{}:] = {}".format(
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

        if car and cdr and len(car) + len(cdr) == get2 - get1:
            dbg("<cache> have both")
            return car + cdr

        elif cdr and (not car or len(car) < len(cdr)):
            h_end = get1 + (get2 - get1) - len(cdr)
            h_ofs = min(get1, h_end - 512 * 1024)

            if h_ofs < 0:
                h_ofs = 0

            buf_ofs = get1 - h_ofs

            dbg(
                "<cache> cdr {}, car {}:{} |{}| [{}:]".format(
                    len(cdr), h_ofs, h_end, h_end - h_ofs, buf_ofs
                )
            )

            buf = self.gw.download_file_range(path, h_ofs, h_end)
            if len(buf) == h_end - h_ofs:
                ret = buf[buf_ofs:] + cdr
            else:
                ret = buf[get1 - h_ofs :]
                info(
                    "remote truncated {}:{} to |{}|, will return |{}|".format(
                        h_ofs, h_end, len(buf), len(ret)
                    )
                )

        elif car:
            h_ofs = get1 + len(car)
            h_end = max(get2, h_ofs + 1024 * 1024)

            if h_end > file_sz:
                h_end = file_sz

            buf_ofs = (get2 - get1) - len(car)

            dbg(
                "<cache> car {}, cdr {}:{} |{}| [:{}]".format(
                    len(car), h_ofs, h_end, h_end - h_ofs, buf_ofs
                )
            )

            buf = self.gw.download_file_range(path, h_ofs, h_end)
            ret = car + buf[:buf_ofs]

        else:
            if get2 - get1 <= 1024 * 1024:
                # unless the request is for the last n bytes of the file,
                # grow the start to cache some stuff around the range
                if get2 < file_sz - 1:
                    h_ofs = get1 - 1024 * 256
                else:
                    h_ofs = get1 - 1024 * 32

                # likewise grow the end unless start is 0
                if get1 > 0:
                    h_end = get2 + 1024 * 1024
                else:
                    h_end = get2 + 1024 * 64
            else:
                # big enough, doesn't need pads
                h_ofs = get1
                h_end = get2

            if h_ofs < 0:
                h_ofs = 0

            if h_end > file_sz:
                h_end = file_sz

            buf_ofs = get1 - h_ofs
            buf_end = buf_ofs + get2 - get1

            dbg(
                "<cache> {}:{} |{}| [{}:{}]".format(
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
        log("readdir [{}] [{}]".format(hexler(path), fh))

        ret = self.gw.listdir(path)
        if not self.n_dircache:
            return ret

        with self.dircache_mtx:
            cn = CacheNode(path, ret)
            self.dircache.append(cn)
            self.clean_dircache()

        # import pprint; pprint.pprint(ret)
        return ret

    def readdir(self, path, fh=None):
        return [".", ".."] + self._readdir(path, fh)

    def read(self, path, length, offset, fh=None):
        req_max = 1024 * 1024 * 8
        cache_max = 1024 * 1024 * 2
        if length > req_max:
            # windows actually doing 240 MiB read calls, sausage
            info("truncate |{}| to {}MiB".format(length, req_max >> 20))
            length = req_max

        path = path.strip("/")
        ofs2 = offset + length
        file_sz = self.getattr(path)["st_size"]
        log(
            "read {} |{}| {}:{} max {}".format(
                hexler(path), length, offset, ofs2, file_sz
            )
        )
        if ofs2 > file_sz:
            ofs2 = file_sz
            log("truncate to |{}| :{}".format(ofs2 - offset, ofs2))

        if file_sz == 0 or offset >= ofs2:
            return b""

        if self.n_filecache and length <= cache_max:
            ret = self.get_cached_file(path, offset, ofs2, file_sz)
        else:
            ret = self.gw.download_file_range(path, offset, ofs2)

        return ret

        fn = "cppf-{}-{}-{}".format(time.time(), offset, length)
        if False:
            with open(fn, "wb", len(ret)) as f:
                f.write(ret)
        elif self.n_filecache:
            ret2 = self.gw.download_file_range(path, offset, ofs2)
            if ret != ret2:
                info(fn)
                for v in [ret, ret2]:
                    try:
                        info(len(v))
                    except:
                        info("uhh " + repr(v))

                with open(fn + ".bad", "wb") as f:
                    f.write(ret)
                with open(fn + ".good", "wb") as f:
                    f.write(ret2)

                raise Exception("cache bork")

        return ret

    def getattr(self, path, fh=None):
        log("getattr [{}]".format(hexler(path)))
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
            # dbg("=" + repr(ret))
            return ret

        cn = self.get_cached_dir(dirpath)
        if cn:
            log("cache ok")
            dents = cn.data
        else:
            dbg("cache miss")
            dents = self._readdir(dirpath)

        for cache_name, cache_stat, _ in dents:
            # if "qw" in cache_name and "qw" in fname:
            #     info(
            #         "cmp\n  [{}]\n  [{}]\n\n{}\n".format(
            #             hexler(cache_name),
            #             hexler(fname),
            #             "\n".join(traceback.format_stack()[:-1]),
            #         )
            #     )

            if cache_name == fname:
                # dbg("=" + repr(cache_stat))
                return cache_stat

        fun = info
        if MACOS and path.split("/")[-1].startswith("._"):
            fun = dbg

        fun("=ENOENT ({})".format(hexler(path)))
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
            dbg("open [{}] [{}]".format(hexler(path), flags))
            return self._open(path)

        def opendir(self, path):
            dbg("opendir [{}]".format(hexler(path)))
            return self._open(path)

        def flush(self, path, fh):
            dbg("flush [{}] [{}]".format(hexler(path), fh))

        def release(self, ino, fi):
            dbg("release [{}] [{}]".format(hexler(ino), fi))

        def releasedir(self, ino, fi):
            dbg("releasedir [{}] [{}]".format(hexler(ino), fi))

        def access(self, path, mode):
            dbg("access [{}] [{}]".format(hexler(path), mode))
            try:
                x = self.getattr(path)
                if x["st_mode"] <= 0:
                    raise Exception()
            except:
                raise FuseOSError(errno.ENOENT)


class TheArgparseFormatter(
    argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
):
    pass


def main():
    global info, log, dbg
    time.strptime("19970815", "%Y%m%d")  # python#7980

    # filecache helps for reads that are ~64k or smaller;
    #   linux generally does 128k so the cache is a slowdown,
    #   windows likes to use 4k and 64k so cache is required,
    #   value is numChunks (1~3M each) to keep in the cache
    nf = 24

    # dircache is always a boost,
    #   only want to disable it for tests etc,
    #   value is numSec until an entry goes stale
    nd = 1

    where = "local directory"
    if WINDOWS:
        where += " or DRIVE:"

    ex_pre = "\n  " + os.path.basename(__file__) + "  "
    examples = ["http://192.168.1.69:3923/music/  ./music"]
    if WINDOWS:
        examples.append("http://192.168.1.69:3923/music/  M:")

    ap = argparse.ArgumentParser(
        formatter_class=TheArgparseFormatter,
        epilog="example:" + ex_pre + ex_pre.join(examples),
    )
    ap.add_argument(
        "-cd", metavar="NUM_SECONDS", type=float, default=nd, help="directory cache"
    )
    ap.add_argument(
        "-cf", metavar="NUM_BLOCKS", type=int, default=nf, help="file cache"
    )
    ap.add_argument("-a", metavar="PASSWORD", help="password")
    ap.add_argument("-d", action="store_true", help="enable debug")
    ap.add_argument("-te", metavar="PEM_FILE", help="certificate to expect/verify")
    ap.add_argument("-td", action="store_true", help="disable certificate check")
    ap.add_argument("base_url", type=str, help="remote copyparty URL to mount")
    ap.add_argument("local_path", type=str, help=where + " to mount it on")
    ar = ap.parse_args()

    if ar.d:
        # windows terminals are slow (cmd.exe, mintty)
        # otoh fancy_log beats RecentLog on linux
        logger = RecentLog().put if WINDOWS else fancy_log

        info = logger
        log = logger
        dbg = logger
    else:
        # debug=off, speed is dontcare
        info = fancy_log
        log = null_log
        dbg = null_log

    if ar.a and ar.a.startswith("$"):
        fn = ar.a[1:]
        log("reading password from file [{}]".format(fn))
        with open(fn, "rb") as f:
            ar.a = f.read().decode("utf-8").strip()

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

    register_wtf8()

    try:
        with open("/etc/fuse.conf", "rb") as f:
            allow_other = b"\nuser_allow_other" in f.read()
    except:
        allow_other = WINDOWS or MACOS

    args = {"foreground": True, "nothreads": True, "allow_other": allow_other}
    if not MACOS:
        args["nonempty"] = True

    FUSE(CPPF(ar), ar.local_path, encoding="wtf-8", **args)


if __name__ == "__main__":
    main()

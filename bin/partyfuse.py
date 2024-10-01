#!/usr/bin/env python3

"""partyfuse: remote copyparty as a local filesystem"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"


"""
mount a copyparty server (local or remote) as a filesystem

speeds:
  1 GiB/s reading large files
  27'000 files/sec: copy small files
  700 folders/sec: copy small folders

usage:
  python partyfuse.py http://192.168.1.69:3923/  ./music

dependencies:
  python3 -m pip install --user fusepy
  + on Linux: sudo apk add fuse
  + on Macos: https://osxfuse.github.io/
  + on Windows: https://github.com/billziss-gh/winfsp/releases/latest

note:
  you probably want to run this on windows clients:
  https://github.com/9001/copyparty/blob/hovudstraum/contrib/explorer-nothumbs-nofoldertypes.reg

get server cert:
  awk '/-BEGIN CERTIFICATE-/ {a=1} a; /-END CERTIFICATE-/{exit}' <(openssl s_client -connect 127.0.0.1:3923 </dev/null 2>/dev/null) >cert.pem
"""


import argparse
import calendar
import codecs
import errno
import json
import os
import platform
import re
import stat
import struct
import sys
import threading
import time
import traceback
import urllib.parse
from datetime import datetime, timezone
from urllib.parse import quote_from_bytes as quote
from urllib.parse import unquote_to_bytes as unquote

import builtins
import http.client

WINDOWS = sys.platform == "win32"
MACOS = platform.system() == "Darwin"
UTC = timezone.utc


def print(*args, **kwargs):
    try:
        builtins.print(*list(args), **kwargs)
    except:
        builtins.print(termsafe(" ".join(str(x) for x in args)), **kwargs)


print(
    "{} v{} @ {}".format(
        platform.python_implementation(),
        ".".join([str(x) for x in sys.version_info]),
        sys.executable,
    )
)


def nullfun(*a):
    pass


info = dbg = nullfun
is_dbg = False


try:
    from fuse import FUSE, FuseOSError, Operations
except:
    if WINDOWS:
        libfuse = "install https://github.com/billziss-gh/winfsp/releases/latest"
    elif MACOS:
        libfuse = "install https://osxfuse.github.io/"
    else:
        libfuse = "apt install libfuse3-3\n    modprobe fuse"

    m = """\033[33m
  could not import fuse; these may help:
    {} -m pip install --user fusepy
    {}
\033[0m"""
    print(m.format(sys.executable, libfuse))
    raise


def termsafe(txt):
    try:
        return txt.encode(sys.stdout.encoding, "backslashreplace").decode(
            sys.stdout.encoding
        )
    except:
        return txt.encode(sys.stdout.encoding, "replace").decode(sys.stdout.encoding)


def threadless_log(fmt, *a):
    fmt += "\n"
    print(fmt % a if a else fmt, end="")


riced_tids = {}


def rice_tid():
    tid = threading.current_thread().ident
    try:
        return riced_tids[tid]
    except:
        c = struct.unpack(b"B" * 5, struct.pack(b">Q", tid)[-5:])
        ret = "".join("\033[1;37;48;5;%dm%02x" % (x, x) for x in c) + "\033[0m"
        riced_tids[tid] = ret
        return ret


def fancy_log(fmt, *a):
    msg = fmt % a if a else fmt
    print("%10.6f %s %s\n" % (time.time() % 900, rice_tid(), msg), end="")


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
    def __init__(self, ar):
        self.ar = ar
        self.mtx = threading.Lock()
        self.f = open(ar.logf, "wb") if ar.logf else None
        self.q = []

        thr = threading.Thread(target=self.printer)
        thr.daemon = True
        thr.start()

    def put(self, fmt, *a):
        msg = fmt % a if a else fmt
        msg = "%10.6f %s %s\n" % (time.time() % 900, rice_tid(), msg)
        if self.f:
            zd = datetime.now(UTC)
            fmsg = "%d-%04d-%06d.%06d %s" % (
                zd.year,
                zd.month * 100 + zd.day,
                (zd.hour * 100 + zd.minute) * 100 + zd.second,
                zd.microsecond,
                msg,
            )
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


# [windows/cmd/cpy3]  python dev\copyparty\bin\partyfuse.py q: http://192.168.1.159:1234/
# [windows/cmd/msys2] C:\msys64\mingw64\bin\python3 dev\copyparty\bin\partyfuse.py q: http://192.168.1.159:1234/
# [windows/mty/msys2] /mingw64/bin/python3 /c/Users/ed/dev/copyparty/bin/partyfuse.py q: http://192.168.1.159:1234/
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
        self.SRS = "/%s/" % (self.web_root,) if self.web_root else "/"
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

    def sendreq(self, meth, path, headers, **kwargs):
        tid = get_tid()
        if self.password:
            headers["Cookie"] = "=".join(["cppwd", self.password])

        try:
            c = self.getconn(tid)
            c.request(meth, path, headers=headers, **kwargs)
            return c.getresponse()
        except Exception as ex:
            info("HTTP %r", ex)

        self.closeconn(tid)
        try:
            c = self.getconn(tid)
            c.request(meth, path, headers=headers, **kwargs)
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

        zs = "%s%s/" if path else "%s%s"
        web_path = self.quotep(zs % (self.SRS, path)) + "?ls&lt&dots"
        r = self.sendreq("GET", web_path, {})
        if r.status != 200:
            self.closeconn()
            info("http error %s reading dir %r", r.status, web_path)
            raise FuseOSError(errno.ENOENT)

        ctype = r.getheader("Content-Type", "")
        if ctype == "application/json":
            parser = self.parse_jls
            # !rm.yes>
        elif ctype.startswith("text/html"):
            parser = self.parse_html
            # !rm.no>
        else:
            info("listdir on file (%s): %r", ctype, path)
            raise FuseOSError(errno.ENOENT)

        try:
            return parser(r)
        except:
            info("parser: %r\n%s", path, traceback.format_exc())
            raise FuseOSError(errno.EIO)

    def download_file_range(self, path, ofs1, ofs2):
        if bad_good:
            path = dewin(path)

        zs = "%s%s/" if path else "%s%s"
        web_path = self.quotep(zs % (self.SRS, path)) + "?raw"
        hdr_range = "bytes=%d-%d" % (ofs1, ofs2 - 1)

        t = "DL %4.0fK\033[36m%9d-%-9d\033[0m%r"
        info(t, (ofs2 - ofs1) / 1024.0, ofs1, ofs2 - 1, path)

        r = self.sendreq("GET", web_path, {"Range": hdr_range})
        if r.status != http.client.PARTIAL_CONTENT:
            t = "http error %d reading file %r range %s in %s"
            info(t, r.status, web_path, hdr_range, rice_tid())
            self.closeconn()
            raise FuseOSError(errno.EIO)

        return r.read()

    def parse_jls(self, sck):
        rsp = b""
        while True:
            buf = sck.read(1024 * 32)
            if not buf:
                break
            rsp += buf

        rsp = json.loads(rsp.decode("utf-8"))
        ret = {}
        for statfun, nodes in [
            [self.stat_dir, rsp["dirs"]],
            [self.stat_file, rsp["files"]],
        ]:
            for n in nodes:
                fname = unquote(n["href"].split("?")[0]).rstrip(b"/").decode("wtf-8")
                if bad_good:
                    fname = enwin(fname)

                ret[fname] = statfun(n["ts"], n["sz"])

        return ret

    # !rm.yes>
    def parse_html(self, sck):
        ret = {}
        rem = b""
        ptn = re.compile(
            r'^<tr><td>(-|DIR|<a [^<]+</a>)</td><td><a[^>]* href="([^"]+)"[^>]*>([^<]+)</a></td><td>([^<]+)</td><td>.*</td><td>([^<]+)</td></tr>$'
        )

        while True:
            buf = sck.read(1024 * 32)
            if not buf:
                break

            buf = rem + buf
            rem = b""
            idx = buf.rfind(b"\n")
            if idx >= 0:
                rem = buf[idx + 1 :]
                buf = buf[:idx]

            lines = buf.decode("utf-8").split("\n")
            for line in lines:
                m = ptn.match(line)
                if not m:
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
                    ts = calendar.timegm(time.strptime(fdate, "%Y-%m-%d %H:%M:%S"))
                except:
                    info("bad HTML or OS [%r] [%r]", fdate, fsize)
                    # python cannot strptime(1959-01-01) on windows

                if ftype != "DIR" and "zip=crc" not in ftype:
                    ret[fname] = self.stat_file(ts, sz)
                else:
                    ret[fname] = self.stat_dir(ts, sz)

        return ret
    # !rm.no>

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
        self.use_ns = True

        self.gw = Gateway(ar)
        self.junk_fh_ctr = 3
        self.t_dircache = ar.cds
        self.n_dircache = ar.cdn
        self.n_filecache = ar.cf

        self.dircache = []
        self.dircache_mtx = threading.Lock()

        self.filecache = []
        self.filecache_mtx = threading.Lock()

        info("up")

    def _describe(self):
        msg = []
        with self.filecache_mtx:
            for n, cn in enumerate(self.filecache):
                cache_path, cache1 = cn.tag
                cache2 = cache1 + len(cn.data)
                t = "\n{:<2} {:>7} {:>10}:{:<9} {}".format(
                    n,
                    len(cn.data),
                    cache1,
                    cache2,
                    cache_path.replace("\r", "\\r").replace("\n", "\\n"),
                )
                msg.append(t)
        return "".join(msg)

    def clean_dircache(self):
        """not threadsafe"""
        now = time.time()
        cutoff = 0
        for cn in self.dircache:
            if now - cn.ts <= self.t_dircache:
                break
            cutoff += 1

        if cutoff > 0:
            self.dircache = self.dircache[cutoff:]
        elif len(self.dircache) > self.n_dircache:
            self.dircache.pop(0)

    def get_cached_dir(self, dirpath):
        with self.dircache_mtx:
            for cn in self.dircache:
                if cn.tag == dirpath:
                    if time.time() - cn.ts <= self.t_dircache:
                        return cn
                    break
        return None

    # !rm.yes>
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
    # !rm.no>

    def get_cached_file(self, path, get1, get2, file_sz):
        car = None
        cdr = None
        ncn = -1
        if is_dbg:
            dbg("cache request %d:%d |%d|%s", get1, get2, file_sz, self._describe())
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
                        "found all (#%d %d:%d |%d|) [%d:%d] = %d",
                        ncn,
                        cache1,
                        cache2,
                        len(cn.data),
                        buf_ofs,
                        buf_end,
                        buf_end - buf_ofs,
                    )
                    return cn.data[buf_ofs:buf_end]

                if get2 <= cache2:
                    x = cn.data[: get2 - cache1]
                    if not cdr or len(cdr) < len(x):
                        dbg(
                            "found cdr (#%d %d:%d |%d|) [:%d-%d] = [:%d] = %d",
                            ncn,
                            cache1,
                            cache2,
                            len(cn.data),
                            get2,
                            cache1,
                            get2 - cache1,
                            len(x),
                        )
                        cdr = x

                    continue

                if get1 >= cache1:
                    x = cn.data[-(max(0, cache2 - get1)) :]
                    if not car or len(car) < len(x):
                        dbg(
                            "found car (#%d %d:%d |%d|) [-(%d-%d):] = [-%d:] = %d",
                            ncn,
                            cache1,
                            cache2,
                            len(cn.data),
                            cache2,
                            get1,
                            cache2 - get1,
                            len(x),
                        )
                        car = x

                    continue

                msg = "cache fallthrough\n%d %d %d\n%d %d %d\n%d %d --\n%s" % (
                    get1,
                    get2,
                    get2 - get1,
                    cache1,
                    cache2,
                    cache2 - cache1,
                    get1 - cache1,
                    get2 - cache2,
                    self._describe(),
                )
                info(msg)
                raise FuseOSError(errno.EIO)

        if car and cdr and len(car) + len(cdr) == get2 - get1:
            dbg("<cache> have both")
            return car + cdr

        elif cdr and (not car or len(car) < len(cdr)):
            h_end = get1 + (get2 - get1) - len(cdr)
            h_ofs = min(get1, h_end - 0x80000)  # 512k

            if h_ofs < 0:
                h_ofs = 0

            buf_ofs = get1 - h_ofs

            if dbg:
                t = "<cache> cdr %d, car %d:%d |%d| [%d:]"
                dbg(t, len(cdr), h_ofs, h_end, h_end - h_ofs, buf_ofs)

            buf = self.gw.download_file_range(path, h_ofs, h_end)
            if len(buf) == h_end - h_ofs:
                ret = buf[buf_ofs:] + cdr
            else:
                ret = buf[get1 - h_ofs :]
                t = "remote truncated %d:%d to |%d|, will return |%d|"
                info(t, h_ofs, h_end, len(buf), len(ret))

        elif car:
            h_ofs = get1 + len(car)
            if get2 < 0x100000:
                # already cached from 0 to 64k, now do ~64k plus 1 MiB
                h_end = max(get2, h_ofs + 0x100000)  # 1m
            else:
                # after 1 MiB, bump window to 8 MiB
                h_end = max(get2, h_ofs + 0x800000)  # 8m

            if h_end > file_sz:
                h_end = file_sz

            buf_ofs = (get2 - get1) - len(car)

            t = "<cache> car %d, cdr %d:%d |%d| [:%d]"
            dbg(t, len(car), h_ofs, h_end, h_end - h_ofs, buf_ofs)

            buf = self.gw.download_file_range(path, h_ofs, h_end)
            ret = car + buf[:buf_ofs]

        else:
            if get2 - get1 < 0x500000:  # 5m
                # unless the request is for the last n bytes of the file,
                # grow the start to cache some stuff around the range
                if get2 < file_sz - 1:
                    h_ofs = get1 - 0x40000  # 256k
                else:
                    h_ofs = get1 - 0x10000  # 64k

                # likewise grow the end unless start is 0
                if get1 >= 0x100000:
                    h_end = get2 + 0x400000  # 4m
                elif get1 > 0:
                    h_end = get2 + 0x100000  # 1m
                else:
                    h_end = get2 + 0x10000  # 64k
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

            t = "<cache> %d:%d |%d| [%d:%d]"
            dbg(t, h_ofs, h_end, h_end - h_ofs, buf_ofs, buf_end)

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
        dbg("readdir %r [%s]", path, fh)

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
        return [".", ".."] + list(self._readdir(path, fh))

    def read(self, path, length, offset, fh=None):
        req_max = 1024 * 1024 * 8
        cache_max = 1024 * 1024 * 2
        if length > req_max:
            # windows actually doing 240 MiB read calls, sausage
            info("truncate |%d| to %dMiB", length, req_max >> 20)
            length = req_max

        path = path.strip("/")
        ofs2 = offset + length
        file_sz = self.getattr(path)["st_size"]
        dbg("read %r |%d| %d:%d max %d", path, length, offset, ofs2, file_sz)

        if ofs2 > file_sz:
            ofs2 = file_sz
            dbg("truncate to |%d| :%d", ofs2 - offset, ofs2)

        if file_sz == 0 or offset >= ofs2:
            return b""

        if self.n_filecache and length <= cache_max:
            ret = self.get_cached_file(path, offset, ofs2, file_sz)
        else:
            ret = self.gw.download_file_range(path, offset, ofs2)

        return ret

    # !rm.yes>
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
    # !rm.no>

    def getattr(self, path, fh=None):
        dbg("getattr %r", path)
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
            dbg("=%r", ret)
            return ret

        cn = self.get_cached_dir(dirpath)
        if cn:
            dents = cn.data
        else:
            dbg("cache miss")
            dents = self._readdir(dirpath)

        try:
            return dents[fname]
        except:
            pass

        fun = info
        if MACOS and path.split("/")[-1].startswith("._"):
            fun = dbg

        fun("=ENOENT %r", path)
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

    # !rm.yes>
    if False:
        # incorrect semantics but good for debugging stuff like samba and msys2
        def access(self, path, mode):
            dbg("@@ access [{}] [{}]".format(path, mode))
            return 1 if self.getattr(path) else 0

        def flush(self, path, fh):
            dbg("@@ flush [{}] [{}]".format(path, fh))
            return True

        def getxattr(self, *args):
            dbg("@@ getxattr [{}]".format("] [".join(str(x) for x in args)))
            return False

        def listxattr(self, *args):
            dbg("@@ listxattr [{}]".format("] [".join(str(x) for x in args)))
            return False

        def open(self, path, flags):
            dbg("@@ open [{}] [{}]".format(path, flags))
            return 42

        def opendir(self, fh):
            dbg("@@ opendir [{}]".format(fh))
            return 69

        def release(self, ino, fi):
            dbg("@@ release [{}] [{}]".format(ino, fi))
            return True

        def releasedir(self, ino, fi):
            dbg("@@ releasedir [{}] [{}]".format(ino, fi))
            return True

        def statfs(self, path):
            dbg("@@ statfs [{}]".format(path))
            return {}
    # !rm.no>

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
                info("open ERR %r", ex)
                raise FuseOSError(errno.ENOENT)

        def open(self, path, flags):
            dbg("open %r [%s]", path, flags)
            return self._open(path)

        def opendir(self, path):
            dbg("opendir %r", path)
            return self._open(path)

        def flush(self, path, fh):
            dbg("flush %r [%s]", path, fh)

        def release(self, ino, fi):
            dbg("release %r [%s]", ino, fi)

        def releasedir(self, ino, fi):
            dbg("releasedir %r [%s]", ino, fi)

        def access(self, path, mode):
            dbg("access %r [%s]", path, mode)
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
    global info, dbg, is_dbg
    time.strptime("19970815", "%Y%m%d")  # python#7980

    # filecache helps for reads that are ~64k or smaller;
    #   windows likes to use 4k and 64k so cache is important,
    #   linux generally does 128k so the cache is still nice,
    #   value is numChunks (1~8M each) to keep in the cache
    nf = 12

    # dircache is always a boost,
    #   only want to disable it for tests etc,
    cdn = 9  # max num dirs; 0=disable
    cds = 1  # numsec until an entry goes stale

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
    # fmt: off
    ap.add_argument("base_url", type=str, help="remote copyparty URL to mount")
    ap.add_argument("local_path", type=str, help=where + " to mount it on")
    ap.add_argument("-a", metavar="PASSWORD", help="password or $filepath")

    ap2 = ap.add_argument_group("https/TLS")
    ap2.add_argument("-te", metavar="PEMFILE", help="certificate to expect/verify")
    ap2.add_argument("-td", action="store_true", help="disable certificate check")

    ap2 = ap.add_argument_group("cache/perf")
    ap2.add_argument("-cdn", metavar="DIRS", type=float, default=cdn, help="directory-cache, max num dirs; 0=disable")
    ap2.add_argument("-cds", metavar="SECS", type=float, default=cds, help="directory-cache, expiration time")
    ap2.add_argument("-cf", metavar="BLOCKS", type=int, default=nf, help="file cache; each block is <= 1 MiB")

    ap2 = ap.add_argument_group("logging")
    ap2.add_argument("-q", action="store_true", help="quiet")
    ap2.add_argument("-d", action="store_true", help="debug/verbose")
    ap2.add_argument("--slowterm", action="store_true", help="only most recent msgs; good for windows")
    ap2.add_argument("--logf", metavar="FILE", type=str, default="", help="log to FILE; enables --slowterm")

    ap2 = ap.add_argument_group("fuse")
    ap2.add_argument("--oth", action="store_true", help="tell FUSE to '-o allow_other'")
    ap2.add_argument("--nonempty", action="store_true", help="tell FUSE to '-o nonempty'")

    ar = ap.parse_args()
    # fmt: on

    if ar.logf:
        ar.slowterm = True

    # windows terminals are slow (cmd.exe, mintty)
    # otoh fancy_log beats RecentLog on linux
    logger = RecentLog(ar).put if ar.slowterm else fancy_log
    if ar.d:
        info = logger
        dbg = logger
        is_dbg = True
    elif not ar.q:
        info = logger

    if ar.a and ar.a.startswith("$"):
        fn = ar.a[1:]
        info("reading password from file %r", fn)
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

    args = {"foreground": True, "nothreads": True}
    if ar.oth:
        args["allow_other"] = True
    if ar.nonempty:
        args["nonempty"] = True

    FUSE(CPPF(ar), ar.local_path, encoding="wtf-8", **args)


if __name__ == "__main__":
    main()

# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import sys
import time
import base64
import select
import struct
import hashlib
import platform
import traceback
import threading
import mimetypes
import contextlib
import subprocess as sp  # nosec
from datetime import datetime

from .__init__ import PY2, WINDOWS, ANYWIN
from .stolen import surrogateescape

FAKE_MP = False

try:
    if FAKE_MP:
        import multiprocessing.dummy as mp  # noqa: F401
    else:
        import multiprocessing as mp  # noqa: F401
except ImportError:
    # support jython
    mp = None

if not PY2:
    from urllib.parse import unquote_to_bytes as unquote
    from urllib.parse import quote_from_bytes as quote
    from queue import Queue
    from io import BytesIO
else:
    from urllib import unquote  # pylint: disable=no-name-in-module
    from urllib import quote  # pylint: disable=no-name-in-module
    from Queue import Queue  # pylint: disable=import-error,no-name-in-module
    from StringIO import StringIO as BytesIO

surrogateescape.register_surrogateescape()
FS_ENCODING = sys.getfilesystemencoding()
if WINDOWS and PY2:
    FS_ENCODING = "utf-8"


HTTP_TS_FMT = "%a, %d %b %Y %H:%M:%S GMT"


HTTPCODE = {
    200: "OK",
    204: "No Content",
    206: "Partial Content",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    416: "Requested Range Not Satisfiable",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
}


IMPLICATIONS = [
    ["e2dsa", "e2ds"],
    ["e2ds", "e2d"],
    ["e2tsr", "e2ts"],
    ["e2ts", "e2t"],
    ["e2t", "e2d"],
]


MIMES = {
    "md": "text/plain; charset=UTF-8",
    "opus": "audio/ogg; codecs=opus",
    "webp": "image/webp",
}


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


class Counter(object):
    def __init__(self, v=0):
        self.v = v
        self.mutex = threading.Lock()

    def add(self, delta=1):
        with self.mutex:
            self.v += delta

    def set(self, absval):
        with self.mutex:
            self.v = absval


class Cooldown(object):
    def __init__(self, maxage):
        self.maxage = maxage
        self.mutex = threading.Lock()
        self.hist = {}
        self.oldest = 0

    def poke(self, key):
        with self.mutex:
            now = time.time()

            ret = False
            v = self.hist.get(key, 0)
            if now - v > self.maxage:
                self.hist[key] = now
                ret = True

            if self.oldest - now > self.maxage * 2:
                self.hist = {
                    k: v for k, v in self.hist.items() if now - v < self.maxage
                }
                self.oldest = sorted(self.hist.values())[0]

            return ret


class Unrecv(object):
    """
    undo any number of socket recv ops
    """

    def __init__(self, s):
        self.s = s
        self.buf = b""

    def recv(self, nbytes):
        if self.buf:
            ret = self.buf[:nbytes]
            self.buf = self.buf[nbytes:]
            return ret

        try:
            return self.s.recv(nbytes)
        except:
            return b""

    def unrecv(self, buf):
        self.buf = buf + self.buf


class ProgressPrinter(threading.Thread):
    """
    periodically print progress info without linefeeds
    """

    def __init__(self):
        threading.Thread.__init__(self, name="pp")
        self.daemon = True
        self.msg = None
        self.end = False
        self.start()

    def run(self):
        msg = None
        while not self.end:
            time.sleep(0.1)
            if msg == self.msg or self.end:
                continue

            msg = self.msg
            uprint(" {}\033[K\r".format(msg))
            if PY2:
                sys.stdout.flush()

        print("\033[K", end="")
        sys.stdout.flush()  # necessary on win10 even w/ stderr btw


def uprint(msg):
    try:
        print(msg, end="")
    except UnicodeEncodeError:
        try:
            print(msg.encode("utf-8", "replace").decode(), end="")
        except:
            print(msg.encode("ascii", "replace").decode(), end="")


def nuprint(msg):
    uprint("{}\n".format(msg))


def rice_tid():
    tid = threading.current_thread().ident
    c = struct.unpack(b"B" * 5, struct.pack(b">Q", tid)[-5:])
    return "".join("\033[1;37;48;5;{}m{:02x}".format(x, x) for x in c) + "\033[0m"


def trace(*args, **kwargs):
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


def alltrace():
    threads = {}
    names = dict([(t.ident, t.name) for t in threading.enumerate()])
    for tid, stack in sys._current_frames().items():
        name = "{} ({:x})".format(names.get(tid), tid)
        threads[name] = stack

    rret = []
    bret = []
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

    return "\n".join(rret + bret)


def min_ex():
    et, ev, tb = sys.exc_info()
    tb = traceback.extract_tb(tb, 2)
    ex = [
        "{} @ {} <{}>: {}".format(fp.split(os.sep)[-1], ln, fun, txt)
        for fp, ln, fun, txt in tb
    ]
    ex.append("{}: {}".format(et.__name__, ev))
    return "\n".join(ex)


@contextlib.contextmanager
def ren_open(fname, *args, **kwargs):
    fdir = kwargs.pop("fdir", None)
    suffix = kwargs.pop("suffix", None)

    if fname == os.devnull:
        with open(fname, *args, **kwargs) as f:
            yield {"orz": [f, fname]}
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

    b64 = ""
    while True:
        try:
            if fdir:
                fpath = os.path.join(fdir, fname)
            else:
                fpath = fname

            if suffix and os.path.exists(fsenc(fpath)):
                fpath += suffix
                fname += suffix
                ext += suffix

            with open(fsenc(fpath), *args, **kwargs) as f:
                if b64:
                    fp2 = "fn-trunc.{}.txt".format(b64)
                    fp2 = os.path.join(fdir, fp2)
                    with open(fsenc(fp2), "wb") as f2:
                        f2.write(orig_name.encode("utf-8"))

                yield {"orz": [f, fname]}
                return

        except OSError as ex_:
            ex = ex_
            if ex.errno not in [36, 63] and (not WINDOWS or ex.errno != 22):
                raise

        if not b64:
            b64 = (bname + ext).encode("utf-8", "replace")
            b64 = hashlib.sha512(b64).digest()[:12]
            b64 = base64.urlsafe_b64encode(b64).decode("utf-8").rstrip("=")

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
    def __init__(self, log_func, sr, http_headers):
        self.sr = sr
        self.log = log_func
        self.headers = http_headers

        self.re_ctype = re.compile(r"^content-type: *([^;]+)", re.IGNORECASE)
        self.re_cdisp = re.compile(r"^content-disposition: *([^;]+)", re.IGNORECASE)
        self.re_cdisp_field = re.compile(
            r'^content-disposition:(?: *|.*; *)name="([^"]+)"', re.IGNORECASE
        )
        self.re_cdisp_file = re.compile(
            r'^content-disposition:(?: *|.*; *)filename="(.*)"', re.IGNORECASE
        )

    def _read_header(self):
        """
        returns [fieldname, filename] after eating a block of multipart headers
        while doing a decent job at dealing with the absolute mess that is
        rfc1341/rfc1521/rfc2047/rfc2231/rfc2388/rfc6266/the-real-world
        (only the fallback non-js uploader relies on these filenames)
        """
        for ln in read_header(self.sr):
            self.log(ln)

            m = self.re_ctype.match(ln)
            if m:
                if m.group(1).lower() == "multipart/mixed":
                    # rfc-7578 overrides rfc-2388 so this is not-impl
                    # (opera >=9 <11.10 is the only thing i've ever seen use it)
                    raise Pebkac(
                        "you can't use that browser to upload multiple files at once"
                    )

                continue

            # the only other header we care about is content-disposition
            m = self.re_cdisp.match(ln)
            if not m:
                continue

            if m.group(1).lower() != "form-data":
                raise Pebkac(400, "not form-data: {}".format(ln))

            try:
                field = self.re_cdisp_field.match(ln).group(1)
            except:
                raise Pebkac(400, "missing field name: {}".format(ln))

            try:
                fn = self.re_cdisp_file.match(ln).group(1)
            except:
                # this is not a file upload, we're done
                return field, None

            try:
                is_webkit = self.headers["user-agent"].lower().find("applewebkit") >= 0
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
                    if ch in ['"', "\\"]:
                        ret += '"'
                    else:
                        ret += esc + ch
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    break
                else:
                    ret += ch

            return [field, ret]

    def _read_data(self):
        blen = len(self.boundary)
        bufsz = 32 * 1024
        while True:
            buf = self.sr.recv(bufsz)
            if not buf:
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

                buf2 = self.sr.recv(bufsz)
                if not buf2:
                    # abort: client disconnected
                    raise Pebkac(400, "client d/c during multipart post")

                buf += buf2

            yield buf

    def _run_gen(self):
        """
        yields [fieldname, unsanitized_filename, fieldvalue]
        where fieldvalue yields chunks of data
        """
        while True:
            fieldname, filename = self._read_header()
            yield [fieldname, filename, self._read_data()]

            tail = self.sr.recv(2)

            if tail == b"--":
                # EOF indicated by this immediately after final boundary
                self.sr.recv(2)
                return

            if tail != b"\r\n":
                raise Pebkac(400, "protocol error after field value")

    def _read_value(self, iterator, max_len):
        ret = b""
        for buf in iterator:
            ret += buf
            if len(ret) > max_len:
                raise Pebkac(400, "field length is too long")

        return ret

    def parse(self):
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

    def require(self, field_name, max_len):
        """
        returns the value of the next field in the multipart body,
        raises if the field name is not as expected
        """
        p_field, _, p_data = next(self.gen)
        if p_field != field_name:
            raise Pebkac(
                422, 'expected field "{}", got "{}"'.format(field_name, p_field)
            )

        return self._read_value(p_data, max_len).decode("utf-8", "surrogateescape")

    def drop(self):
        """discards the remaining multipart body"""
        for _, _, data in self.gen:
            for _ in data:
                pass


def get_boundary(headers):
    # boundaries contain a-z A-Z 0-9 ' ( ) + _ , - . / : = ?
    # (whitespace allowed except as the last char)
    ptn = r"^multipart/form-data; *(.*; *)?boundary=([^;]+)"
    ct = headers["content-type"]
    m = re.match(ptn, ct, re.IGNORECASE)
    if not m:
        raise Pebkac(400, "invalid content-type for a multipart post: {}".format(ct))

    return m.group(2)


def read_header(sr):
    ret = b""
    while True:
        buf = sr.recv(1024)
        if not buf:
            if not ret:
                return None

            raise Pebkac(
                400,
                "protocol error while reading headers:\n"
                + ret.decode("utf-8", "replace"),
            )

        ret += buf
        ofs = ret.find(b"\r\n\r\n")
        if ofs < 0:
            if len(ret) > 1024 * 64:
                raise Pebkac(400, "header 2big")
            else:
                continue

        if len(ret) > ofs + 4:
            sr.unrecv(ret[ofs + 4 :])

        return ret[:ofs].decode("utf-8", "surrogateescape").lstrip("\r\n").split("\r\n")


def humansize(sz, terse=False):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if sz < 1024:
            break

        sz /= 1024.0

    ret = " ".join([str(sz)[:4].rstrip("."), unit])

    if not terse:
        return ret

    return ret.replace("iB", "").replace(" ", "")


def get_spd(nbyte, t0, t=None):
    if t is None:
        t = time.time()

    bps = nbyte / ((t - t0) + 0.001)
    s1 = humansize(nbyte).replace(" ", "\033[33m").replace("iB", "")
    s2 = humansize(bps).replace(" ", "\033[35m").replace("iB", "")
    return "{} \033[0m{}/s\033[0m".format(s1, s2)


def s2hms(s, optional_h=False):
    s = int(s)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if not h and optional_h:
        return "{}:{:02}".format(m, s)

    return "{}:{:02}:{:02}".format(h, m, s)


def undot(path):
    ret = []
    for node in path.split("/"):
        if node in ["", "."]:
            continue

        if node == "..":
            if ret:
                ret.pop()
            continue

        ret.append(node)

    return "/".join(ret)


def sanitize_fn(fn, ok="", bad=[]):
    if "/" not in ok:
        fn = fn.replace("\\", "/").split("/")[-1]

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

        bad.extend(["con", "prn", "aux", "nul"])
        for n in range(1, 10):
            bad += "com{0} lpt{0}".format(n).split(" ")

    if fn.lower() in bad:
        fn = "_" + fn

    return fn.strip()


def u8safe(txt):
    try:
        return txt.encode("utf-8", "xmlcharrefreplace").decode("utf-8", "replace")
    except:
        return txt.encode("utf-8", "replace").decode("utf-8", "replace")


def exclude_dotfiles(filepaths):
    return [x for x in filepaths if not x.split("/")[-1].startswith(".")]


def http_ts(ts):
    file_dt = datetime.utcfromtimestamp(ts)
    return file_dt.strftime(HTTP_TS_FMT)


def html_escape(s, quote=False, crlf=False):
    """html.escape but also newlines"""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;").replace("'", "&#x27;")
    if crlf:
        s = s.replace("\r", "&#13;").replace("\n", "&#10;")

    return s


def html_bescape(s, quote=False, crlf=False):
    """html.escape but bytestrings"""
    s = s.replace(b"&", b"&amp;").replace(b"<", b"&lt;").replace(b">", b"&gt;")
    if quote:
        s = s.replace(b'"', b"&quot;").replace(b"'", b"&#x27;")
    if crlf:
        s = s.replace(b"\r", b"&#13;").replace(b"\n", b"&#10;")

    return s


def quotep(txt):
    """url quoter which deals with bytes correctly"""
    btxt = w8enc(txt)
    quot1 = quote(btxt, safe=b"/")
    if not PY2:
        quot1 = quot1.encode("ascii")

    quot2 = quot1.replace(b" ", b"+")
    return w8dec(quot2)


def unquotep(txt):
    """url unquoter which deals with bytes correctly"""
    btxt = w8enc(txt)
    # btxt = btxt.replace(b"+", b" ")
    unq2 = unquote(btxt)
    return w8dec(unq2)


def w8dec(txt):
    """decodes filesystem-bytes to wtf8"""
    if PY2:
        return surrogateescape.decodefilename(txt)

    return txt.decode(FS_ENCODING, "surrogateescape")


def w8enc(txt):
    """encodes wtf8 to filesystem-bytes"""
    if PY2:
        return surrogateescape.encodefilename(txt)

    return txt.encode(FS_ENCODING, "surrogateescape")


def w8b64dec(txt):
    """decodes base64(filesystem-bytes) to wtf8"""
    return w8dec(base64.urlsafe_b64decode(txt.encode("ascii")))


def w8b64enc(txt):
    """encodes wtf8 to base64(filesystem-bytes)"""
    return base64.urlsafe_b64encode(w8enc(txt)).decode("ascii")


if PY2 and WINDOWS:
    # moonrunes become \x3f with bytestrings,
    # losing mojibake support is worth
    def _not_actually_mbcs(txt):
        return txt

    fsenc = _not_actually_mbcs
    fsdec = _not_actually_mbcs
else:
    fsenc = w8enc
    fsdec = w8dec


def s3enc(mem_cur, rd, fn):
    ret = []
    for v in [rd, fn]:
        try:
            mem_cur.execute("select * from a where b = ?", (v,))
            ret.append(v)
        except:
            ret.append("//" + w8b64enc(v))
            # self.log("mojien/{} [{}] {}".format(k, v, ret[-1][2:]))

    return tuple(ret)


def s3dec(rd, fn):
    ret = []
    for k, v in [["d", rd], ["f", fn]]:
        if v.startswith("//"):
            ret.append(w8b64dec(v[2:]))
            # self.log("mojide/{} [{}] {}".format(k, ret[-1], v[2:]))
        else:
            ret.append(v)

    return tuple(ret)


def atomic_move(src, dst):
    src = fsenc(src)
    dst = fsenc(dst)
    if not PY2:
        os.replace(src, dst)
    else:
        if os.path.exists(dst):
            os.unlink(dst)

        os.rename(src, dst)


def read_socket(sr, total_size):
    remains = total_size
    while remains > 0:
        bufsz = 32 * 1024
        if bufsz > remains:
            bufsz = remains

        buf = sr.recv(bufsz)
        if not buf:
            raise Pebkac(400, "client d/c during binary post")

        remains -= len(buf)
        yield buf


def read_socket_unbounded(sr):
    while True:
        buf = sr.recv(32 * 1024)
        if not buf:
            return

        yield buf


def read_socket_chunked(sr, log=None):
    err = "expected chunk length, got [{}] |{}| instead"
    while True:
        buf = b""
        while b"\r" not in buf:
            rbuf = sr.recv(2)
            if not rbuf or len(buf) > 16:
                err = err.format(buf.decode("utf-8", "replace"), len(buf))
                raise Pebkac(400, err)

            buf += rbuf

        if not buf.endswith(b"\n"):
            sr.recv(1)

        try:
            chunklen = int(buf.rstrip(b"\r\n"), 16)
        except:
            err = err.format(buf.decode("utf-8", "replace"), len(buf))
            raise Pebkac(400, err)

        if chunklen == 0:
            sr.recv(2)  # \r\n after final chunk
            return

        if log:
            log("receiving {} byte chunk".format(chunklen))

        for chunk in read_socket(sr, chunklen):
            yield chunk

        sr.recv(2)  # \r\n after each chunk too


def yieldfile(fn):
    with open(fsenc(fn), "rb", 512 * 1024) as f:
        while True:
            buf = f.read(64 * 1024)
            if not buf:
                break

            yield buf


def hashcopy(actor, fin, fout):
    is_mp = actor.is_mp
    hashobj = hashlib.sha512()
    tlen = 0
    for buf in fin:
        if is_mp:
            actor.workload += 1
            if actor.workload > 2 ** 31:
                actor.workload = 100

        tlen += len(buf)
        hashobj.update(buf)
        fout.write(buf)

    digest32 = hashobj.digest()[:32]
    digest_b64 = base64.urlsafe_b64encode(digest32).decode("utf-8").rstrip("=")

    return tlen, hashobj.hexdigest(), digest_b64


def sendfile_py(lower, upper, f, s, actor=None):
    remains = upper - lower
    f.seek(lower)
    while remains > 0:
        if actor:
            actor.workload += 1
            if actor.workload > 2 ** 31:
                actor.workload = 100

        # time.sleep(0.01)
        buf = f.read(min(1024 * 32, remains))
        if not buf:
            return remains

        try:
            s.sendall(buf)
            remains -= len(buf)
        except:
            return remains

    return 0


def sendfile_kern(lower, upper, f, s):
    out_fd = s.fileno()
    in_fd = f.fileno()
    ofs = lower
    while ofs < upper:
        try:
            req = min(2 ** 30, upper - ofs)
            select.select([], [out_fd], [], 10)
            n = os.sendfile(out_fd, in_fd, ofs, req)
        except Exception as ex:
            # print("sendfile: " + repr(ex))
            n = 0

        if n <= 0:
            return upper - ofs

        ofs += n
        # print("sendfile: ok, sent {} now, {} total, {} remains".format(n, ofs - lower, upper - ofs))

    return 0


def statdir(logger, scandir, lstat, top):
    try:
        btop = fsenc(top)
        if scandir and hasattr(os, "scandir"):
            src = "scandir"
            with os.scandir(btop) as dh:
                for fh in dh:
                    try:
                        yield [fsdec(fh.name), fh.stat(follow_symlinks=not lstat)]
                    except Exception as ex:
                        msg = "scan-stat: \033[36m{} @ {}"
                        logger(msg.format(repr(ex), fsdec(fh.path)))
        else:
            src = "listdir"
            fun = os.lstat if lstat else os.stat
            for name in os.listdir(btop):
                abspath = os.path.join(btop, name)
                try:
                    yield [fsdec(name), fun(abspath)]
                except Exception as ex:
                    msg = "list-stat: \033[36m{} @ {}"
                    logger(msg.format(repr(ex), fsdec(abspath)))

    except Exception as ex:
        logger("{}: \033[31m{} @ {}".format(src, repr(ex), top))


def unescape_cookie(orig):
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


def guess_mime(url, fallback="application/octet-stream"):
    try:
        _, ext = url.rsplit(".", 1)
    except:
        return fallback

    return MIMES.get(ext) or mimetypes.guess_type(url)[0] or fallback


def runcmd(*argv):
    p = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode("utf-8", "replace")
    stderr = stderr.decode("utf-8", "replace")
    return [p.returncode, stdout, stderr]


def chkcmd(*argv):
    ok, sout, serr = runcmd(*argv)
    if ok != 0:
        raise Exception(serr)

    return sout, serr


def mchkcmd(argv, timeout=10):
    if PY2:
        with open(os.devnull, "wb") as f:
            rv = sp.call(argv, stdout=f, stderr=f)
    else:
        rv = sp.call(argv, stdout=sp.DEVNULL, stderr=sp.DEVNULL, timeout=timeout)

    if rv:
        raise sp.CalledProcessError(rv, (argv[0], b"...", argv[-1]))


def gzip_orig_sz(fn):
    with open(fsenc(fn), "rb") as f:
        f.seek(-4, 2)
        rv = f.read(4)
        try:
            return struct.unpack(b"I", rv)[0]
        except:
            return struct.unpack("I", rv)[0]


def py_desc():
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
    compiler = platform.python_compiler()

    os_ver = re.search(r"([0-9]+\.[0-9\.]+)", platform.version())
    os_ver = os_ver.group(1) if os_ver else ""

    return "{:>9} v{} on {}{} {} [{}]".format(
        interp, py_ver, host_os, bitness, os_ver, compiler
    )


def align_tab(lines):
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


class Pebkac(Exception):
    def __init__(self, code, msg=None):
        super(Pebkac, self).__init__(msg or HTTPCODE[code])
        self.code = code

    def __repr__(self):
        return "Pebkac({}, {})".format(self.code, repr(self.args))

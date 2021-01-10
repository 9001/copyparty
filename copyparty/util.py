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
import threading
import mimetypes
import contextlib
import subprocess as sp  # nosec

from .__init__ import PY2, WINDOWS
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
else:
    from urllib import unquote  # pylint: disable=no-name-in-module
    from urllib import quote  # pylint: disable=no-name-in-module
    from Queue import Queue  # pylint: disable=import-error,no-name-in-module

surrogateescape.register_surrogateescape()
FS_ENCODING = sys.getfilesystemencoding()
if WINDOWS and PY2:
    FS_ENCODING = "utf-8"


HTTPCODE = {
    200: "OK",
    204: "No Content",
    206: "Partial Content",
    304: "Not Modified",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    416: "Requested Range Not Satisfiable",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    501: "Not Implemented",
}


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


@contextlib.contextmanager
def ren_open(fname, *args, **kwargs):
    fdir = kwargs.pop("fdir", None)
    suffix = kwargs.pop("suffix", None)

    if fname == os.devnull:
        with open(fname, *args, **kwargs) as f:
            yield {"orz": [f, fname]}
            return
    
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

            if suffix and os.path.exists(fpath):
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
            if ex.errno != 36:
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

        sr.unrecv(ret[ofs + 4 :])
        return ret[:ofs].decode("utf-8", "surrogateescape").split("\r\n")


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


def sanitize_fn(fn):
    fn = fn.replace("\\", "/").split("/")[-1]

    if WINDOWS:
        for bad, good in [
            ["<", "＜"],
            [">", "＞"],
            [":", "："],
            ['"', "＂"],
            ["/", "／"],
            ["\\", "＼"],
            ["|", "｜"],
            ["?", "？"],
            ["*", "＊"],
        ]:
            fn = fn.replace(bad, good)

        bad = ["con", "prn", "aux", "nul"]
        for n in range(1, 10):
            bad += "com{0} lpt{0}".format(n).split(" ")

        if fn.lower() in bad:
            fn = "_" + fn

    return fn.strip()


def exclude_dotfiles(filepaths):
    for fpath in filepaths:
        if not fpath.split("/")[-1].startswith("."):
            yield fpath


def html_escape(s, quote=False):
    """html.escape but also newlines"""
    s = (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\r", "&#13;")
        .replace("\n", "&#10;")
    )
    if quote:
        s = s.replace('"', "&quot;").replace("'", "&#x27;")

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


def atomic_move(src, dst):
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


def hashcopy(actor, fin, fout):
    u32_lim = int((2 ** 31) * 0.9)
    hashobj = hashlib.sha512()
    tlen = 0
    for buf in fin:
        actor.workload += 1
        if actor.workload > u32_lim:
            actor.workload = 100  # prevent overflow

        tlen += len(buf)
        hashobj.update(buf)
        fout.write(buf)

    digest32 = hashobj.digest()[:32]
    digest_b64 = base64.urlsafe_b64encode(digest32).decode("utf-8").rstrip("=")

    return tlen, hashobj.hexdigest(), digest_b64


def sendfile_py(lower, upper, f, s):
    remains = upper - lower
    f.seek(lower)
    while remains > 0:
        # time.sleep(0.01)
        buf = f.read(min(4096, remains))
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


def guess_mime(url):
    if url.endswith(".md"):
        return ["text/plain; charset=UTF-8"]

    return mimetypes.guess_type(url)


def runcmd(*argv):
    p = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    return [p.returncode, stdout, stderr]


def chkcmd(*argv):
    ok, sout, serr = runcmd(*argv)
    if ok != 0:
        raise Exception(serr)

    return sout, serr


def gzip_orig_sz(fn):
    with open(fsenc(fn), "rb") as f:
        f.seek(-4, 2)
        return struct.unpack(b"I", f.read(4))[0]


def py_desc():
    interp = platform.python_implementation()
    py_ver = ".".join([str(x) for x in sys.version_info])
    ofs = py_ver.find(".final.")
    if ofs > 0:
        py_ver = py_ver[:ofs]

    bitness = struct.calcsize(b"P") * 8
    host_os = platform.system()
    compiler = platform.python_compiler()

    os_ver = re.search(r"([0-9]+\.[0-9\.]+)", platform.version())
    os_ver = os_ver.group(1) if os_ver else ""

    return "{:>9} v{} on {}{} {} [{}]".format(
        interp, py_ver, host_os, bitness, os_ver, compiler
    )


class Pebkac(Exception):
    def __init__(self, code, msg=None):
        super(Pebkac, self).__init__(msg or HTTPCODE[code])
        self.code = code

    def __repr__(self):
        return "Pebkac({}, {})".format(self.code, repr(self.args))

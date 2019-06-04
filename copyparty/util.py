#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import re
import hashlib


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
                raise Pebkac("not form-data: {}".format(ln))

            try:
                field = self.re_cdisp_field.match(ln).group(1)
            except:
                raise Pebkac("missing field name: {}".format(ln))

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
            ret = u""
            esc = False
            for ch in fn:
                if esc:
                    if ch in [u'"', u"\\"]:
                        ret += u'"'
                    else:
                        ret += esc + ch
                    esc = False
                elif ch == u"\\":
                    esc = True
                elif ch == u'"':
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
                raise Exception("client disconnected during post")

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
                    raise Exception("client disconnected during post")

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
                raise Pebkac("protocol error after field value")

    def _read_value(self, iterator, max_len):
        ret = b""
        for buf in iterator:
            ret += buf
            if len(ret) > max_len:
                raise Pebkac("field length is too long")

        return ret

    def parse(self):
        # spec says there might be junk before the first boundary,
        # can't have the leading \r\n if that's not the case
        self.boundary = b"--" + get_boundary(self.headers).encode("utf-8")

        # discard junk before the first boundary
        for junk in self._read_data():
            self.log(
                u"discarding preamble: [{}]".format(junk.decode("utf-8", "ignore"))
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
            raise Pebkac('expected field "{}", got "{}"'.format(field_name, p_field))

        return self._read_value(p_data, max_len).decode("utf-8", "ignore")

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
        raise Pebkac("invalid content-type for a multipart post: {}".format(ct))

    return m.group(2)


def read_header(sr):
    ret = b""
    while True:
        if ret.endswith(b"\r\n\r\n"):
            break
        elif ret.endswith(b"\r\n\r"):
            n = 1
        elif ret.endswith(b"\r\n"):
            n = 2
        elif ret.endswith(b"\r"):
            n = 3
        else:
            n = 4

        buf = sr.recv(n)
        if not buf:
            raise Exception("failed to read headers")

        ret += buf

    return ret[:-4].decode("utf-8", "replace").split("\r\n")


def sanitize_fn(fn):
    return fn.replace("\\", "/").split("/")[-1].strip()


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

    return tlen, hashobj.hexdigest()


def unescape_cookie(orig):
    # mw=idk; doot=qwe%2Crty%3Basd+fgh%2Bjkl%25zxc%26vbn  # qwe,rty;asd fgh+jkl%zxc&vbn
    ret = u""
    esc = u""
    for ch in orig:
        if ch == u"%":
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
                    esc = u""

        else:
            ret += ch

    if len(esc) > 0:
        ret += esc

    return ret


class Pebkac(Exception):
    pass

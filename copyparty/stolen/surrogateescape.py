"""
This is Victor Stinner's pure-Python implementation of PEP 383: the "surrogateescape" error
handler of Python 3.

Scissored from the python-future module to avoid 4.4MB of additional dependencies:
https://github.com/PythonCharmers/python-future/blob/e12549c42ed3a38ece45b9d88c75f5f3ee4d658d/src/future/utils/surrogateescape.py

Original source: misc/python/surrogateescape.py in https://bitbucket.org/haypo/misc
"""

# This code is released under the Python license and the BSD 2-clause license

import platform
import codecs
import sys

PY3 = sys.version_info[0] > 2
WINDOWS = platform.system() == "Windows"
FS_ERRORS = "surrogateescape"


def u(text):
    if PY3:
        return text
    else:
        return text.decode("unicode_escape")


def b(data):
    if PY3:
        return data.encode("latin1")
    else:
        return data


if PY3:
    _unichr = chr
    bytes_chr = lambda code: bytes((code,))
else:
    _unichr = unichr
    bytes_chr = chr


def surrogateescape_handler(exc):
    """
    Pure Python implementation of the PEP 383: the "surrogateescape" error
    handler of Python 3. Undecodable bytes will be replaced by a Unicode
    character U+DCxx on decoding, and these are translated into the
    original bytes on encoding.
    """
    mystring = exc.object[exc.start : exc.end]

    try:
        if isinstance(exc, UnicodeDecodeError):
            # mystring is a byte-string in this case
            decoded = replace_surrogate_decode(mystring)
        elif isinstance(exc, UnicodeEncodeError):
            # In the case of u'\udcc3'.encode('ascii',
            # 'this_surrogateescape_handler'), both Python 2.x and 3.x raise an
            # exception anyway after this function is called, even though I think
            # it's doing what it should. It seems that the strict encoder is called
            # to encode the unicode string that this function returns ...
            decoded = replace_surrogate_encode(mystring)
        else:
            raise exc
    except NotASurrogateError:
        raise exc
    return (decoded, exc.end)


class NotASurrogateError(Exception):
    pass


def replace_surrogate_encode(mystring):
    """
    Returns a (unicode) string, not the more logical bytes, because the codecs
    register_error functionality expects this.
    """
    decoded = []
    for ch in mystring:
        code = ord(ch)

        # The following magic comes from Py3.3's Python/codecs.c file:
        if not 0xD800 <= code <= 0xDCFF:
            # Not a surrogate. Fail with the original exception.
            raise NotASurrogateError
        # mybytes = [0xe0 | (code >> 12),
        #            0x80 | ((code >> 6) & 0x3f),
        #            0x80 | (code & 0x3f)]
        # Is this a good idea?
        if 0xDC00 <= code <= 0xDC7F:
            decoded.append(_unichr(code - 0xDC00))
        elif code <= 0xDCFF:
            decoded.append(_unichr(code - 0xDC00))
        else:
            raise NotASurrogateError
    return str().join(decoded)


def replace_surrogate_decode(mybytes):
    """
    Returns a (unicode) string
    """
    decoded = []
    for ch in mybytes:
        # We may be parsing newbytes (in which case ch is an int) or a native
        # str on Py2
        if isinstance(ch, int):
            code = ch
        else:
            code = ord(ch)
        if 0x80 <= code <= 0xFF:
            decoded.append(_unichr(0xDC00 + code))
        elif code <= 0x7F:
            decoded.append(_unichr(code))
        else:
            raise NotASurrogateError
    return str().join(decoded)


def encodefilename(fn):
    if FS_ENCODING == "ascii":
        # ASCII encoder of Python 2 expects that the error handler returns a
        # Unicode string encodable to ASCII, whereas our surrogateescape error
        # handler has to return bytes in 0x80-0xFF range.
        encoded = []
        for index, ch in enumerate(fn):
            code = ord(ch)
            if code < 128:
                ch = bytes_chr(code)
            elif 0xDC80 <= code <= 0xDCFF:
                ch = bytes_chr(code - 0xDC00)
            else:
                raise UnicodeEncodeError(
                    FS_ENCODING, fn, index, index + 1, "ordinal not in range(128)"
                )
            encoded.append(ch)
        return bytes().join(encoded)
    elif FS_ENCODING == "utf-8":
        # UTF-8 encoder of Python 2 encodes surrogates, so U+DC80-U+DCFF
        # doesn't go through our error handler
        encoded = []
        for index, ch in enumerate(fn):
            code = ord(ch)
            if 0xD800 <= code <= 0xDFFF:
                if 0xDC80 <= code <= 0xDCFF:
                    ch = bytes_chr(code - 0xDC00)
                    encoded.append(ch)
                else:
                    raise UnicodeEncodeError(
                        FS_ENCODING, fn, index, index + 1, "surrogates not allowed"
                    )
            else:
                ch_utf8 = ch.encode("utf-8")
                encoded.append(ch_utf8)
        return bytes().join(encoded)
    else:
        return fn.encode(FS_ENCODING, FS_ERRORS)


def decodefilename(fn):
    return fn.decode(FS_ENCODING, FS_ERRORS)


FS_ENCODING = sys.getfilesystemencoding()
# FS_ENCODING = "ascii"; fn = b("[abc\xff]"); encoded = u("[abc\udcff]")
# FS_ENCODING = 'cp932'; fn = b('[abc\x81\x00]'); encoded = u('[abc\udc81\x00]')
# FS_ENCODING = 'UTF-8'; fn = b('[abc\xff]'); encoded = u('[abc\udcff]')


if WINDOWS and not PY3:
    # py2 thinks win* is mbcs, probably a bug? anyways this works
    FS_ENCODING = 'utf-8'


# normalize the filesystem encoding name.
# For example, we expect "utf-8", not "UTF8".
FS_ENCODING = codecs.lookup(FS_ENCODING).name


def register_surrogateescape():
    """
    Registers the surrogateescape error handler on Python 2 (only)
    """
    if PY3:
        return
    try:
        codecs.lookup_error(FS_ERRORS)
    except LookupError:
        codecs.register_error(FS_ERRORS, surrogateescape_handler)

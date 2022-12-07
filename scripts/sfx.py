#!/usr/bin/env python3
# coding: latin-1
from __future__ import print_function, unicode_literals
import re, os, sys, time, shutil, signal, threading, tarfile, hashlib, platform, tempfile, traceback
import subprocess as sp


"""
to edit this file, use HxD or "vim -b"
  (there is compressed stuff at the end)

run me with python 2.7 or 3.3+ to unpack and run copyparty

there's zero binaries! just plaintext python scripts all the way down
  so you can easily unpack the archive and inspect it for shady stuff

the archive data is attached after the b"\n# eof\n" archive marker,
  b"?0" decodes to b"\x00"
  b"?n" decodes to b"\n"
  b"?r" decodes to b"\r"
  b"??" decodes to b"?"
"""


# set by make-sfx.sh
VER = None
SIZE = None
CKSUM = None
STAMP = None

PY2 = sys.version_info < (3,)
PY37 = sys.version_info > (3, 7)
WINDOWS = sys.platform in ["win32", "msys"]
sys.dont_write_bytecode = True
me = os.path.abspath(os.path.realpath(__file__))


def eprint(*a, **ka):
    ka["file"] = sys.stderr
    print(*a, **ka)


def msg(*a, **ka):
    if a:
        a = ["[SFX]", a[0]] + list(a[1:])

    eprint(*a, **ka)


# skip 1


def testptn1():
    """test: creates a test-pattern for encode()"""
    import struct

    buf = b""
    for c in range(256):
        buf += struct.pack("B", c)

    yield buf


def testptn2():
    import struct

    for a in range(256):
        if a % 16 == 0:
            msg(a)

        for b in range(256):
            buf = b""
            for c in range(256):
                buf += struct.pack("BBBB", a, b, c, b)
            yield buf


def testptn3():
    with open("C:/Users/ed/Downloads/python-3.8.1-amd64.exe", "rb", 512 * 1024) as f:
        while True:
            buf = f.read(512 * 1024)
            if not buf:
                break

            yield buf


testptn = testptn2


def testchk(cdata):
    """test: verifies that `data` yields testptn"""
    import struct

    cbuf = b""
    mbuf = b""
    checked = 0
    t0 = time.time()
    mdata = testptn()
    while True:
        if not mbuf:
            try:
                mbuf += next(mdata)
            except:
                break

        if not cbuf:
            try:
                cbuf += next(cdata)
            except:
                expect = mbuf[:8]
                expect = "".join(
                    " {:02x}".format(x)
                    for x in struct.unpack("B" * len(expect), expect)
                )
                raise Exception(
                    "truncated at {}, expected{}".format(checked + len(cbuf), expect)
                )

        ncmp = min(len(cbuf), len(mbuf))
        # msg("checking {:x}H bytes, {:x}H ok so far".format(ncmp, checked))
        for n in range(ncmp):
            checked += 1
            if cbuf[n] != mbuf[n]:
                expect = mbuf[n : n + 8]
                expect = "".join(
                    " {:02x}".format(x)
                    for x in struct.unpack("B" * len(expect), expect)
                )
                cc = struct.unpack(b"B", cbuf[n : n + 1])[0]
                raise Exception(
                    "byte {:x}H bad, got {:02x}, expected{}".format(checked, cc, expect)
                )

        cbuf = cbuf[ncmp:]
        mbuf = mbuf[ncmp:]

    td = time.time() - t0
    txt = "all {}d bytes OK in {:.3f} sec, {:.3f} MB/s".format(
        checked, td, (checked / (1024 * 1024.0)) / td
    )
    msg(txt)


def encode(data, size, cksum, ver, ts):
    """creates a new sfx; `data` should yield bufs to attach"""
    nb = 0
    nin = 0
    nout = 0
    skip = False
    with open(me, "rb") as fi:
        unpk = ""
        src = fi.read().replace(b"\r", b"").rstrip(b"\n").decode("utf-8")
        for ln in src.split("\n"):
            if ln.endswith("# skip 0"):
                skip = False
                nb = 9
                continue

            if ln.endswith("# skip 1") or skip:
                skip = True
                continue

            if ln.strip().startswith("# fmt: "):
                continue

            if ln:
                nb = 0
            else:
                nb += 1
                if nb > 2:
                    continue

            unpk += ln + "\n"

        for k, v in [
            ["VER", '"' + ver + '"'],
            ["SIZE", size],
            ["CKSUM", '"' + cksum + '"'],
            ["STAMP", ts],
        ]:
            v1 = "\n{} = None\n".format(k)
            v2 = "\n{} = {}\n".format(k, v)
            unpk = unpk.replace(v1, v2)

        unpk = unpk.replace("\n    ", "\n\t")
        for _ in range(16):
            unpk = unpk.replace("\t    ", "\t\t")

    with open("sfx.out", "wb") as f:
        f.write(unpk.encode("utf-8").rstrip(b"\n") + b"\n\n\n# eof")
        for buf in data:
            ebuf = (
                buf.replace(b"?", b"??")
                .replace(b"\x00", b"?0")
                .replace(b"\r", b"?r")
                .replace(b"\n", b"?n")
            )
            nin += len(buf)
            nout += len(ebuf)
            while ebuf:
                ep = 4090
                while True:
                    a = ebuf.rfind(b"?", 0, ep)
                    if a < 0 or ep - a > 2:
                        break
                    ep = a
                buf = ebuf[:ep]
                ebuf = ebuf[ep:]
                f.write(b"\n#" + buf)

        f.write(b"\n\n")

    msg("wrote {:x}H bytes ({:x}H after encode)".format(nin, nout))


def makesfx(tar_src, ver, ts):
    sz = os.path.getsize(tar_src)
    cksum = hashfile(tar_src)
    encode(yieldfile(tar_src), sz, cksum, ver, ts)


# skip 0


def u8(gen):
    try:
        for s in gen:
            yield s.decode("utf-8", "ignore")
    except:
        yield s
        for s in gen:
            yield s


def yieldfile(fn):
    with open(fn, "rb") as f:
        for block in iter(lambda: f.read(64 * 1024), b""):
            yield block


def hashfile(fn):
    h = hashlib.sha1()
    for block in yieldfile(fn):
        h.update(block)

    return h.hexdigest()[:24]


def unpack():
    """unpacks the tar yielded by `data`"""
    name = "pe-copyparty"
    try:
        name += "." + str(os.geteuid())
    except:
        pass

    tag = "v" + str(STAMP)
    top = tempfile.gettempdir()
    opj = os.path.join
    ofe = os.path.exists
    final = opj(top, name)
    san = opj(final, "copyparty/up2k.py")
    for suf in range(0, 9001):
        withpid = "{}.{}.{}".format(name, os.getpid(), suf)
        mine = opj(top, withpid)
        if not ofe(mine):
            break

    tar = opj(mine, "tar")

    try:
        if tag in os.listdir(final) and ofe(san):
            msg("found early")
            return final
    except:
        pass

    sz = 0
    os.mkdir(mine)
    with open(tar, "wb") as f:
        for buf in get_payload():
            sz += len(buf)
            f.write(buf)

    ck = hashfile(tar)
    if ck != CKSUM:
        t = "\n\nexpected {} ({} byte)\nobtained {} ({} byte)\nsfx corrupt"
        raise Exception(t.format(CKSUM, SIZE, ck, sz))

    with tarfile.open(tar, "r:bz2") as tf:
        # this is safe against traversal
        # skip 1
        # since it will never process user-provided data;
        # the only possible input is a single tar.bz2
        # which gets hardcoded into this script at build stage
        # skip 0
        tf.extractall(mine)

    os.remove(tar)

    with open(opj(mine, tag), "wb") as f:
        f.write(b"h\n")

    try:
        if tag in os.listdir(final) and ofe(san):
            msg("found late")
            return final
    except:
        pass

    try:
        if os.path.islink(final):
            os.remove(final)
        else:
            shutil.rmtree(final)
    except:
        pass

    for fn in u8(os.listdir(top)):
        if fn.startswith(name) and fn != withpid:
            try:
                old = opj(top, fn)
                if time.time() - os.path.getmtime(old) > 86400:
                    shutil.rmtree(old)
            except:
                pass

    try:
        os.symlink(mine, final)
    except:
        try:
            os.rename(mine, final)
            return final
        except:
            msg("reloc fail,", mine)

    return mine


def get_payload():
    """yields the binary data attached to script"""
    with open(me, "rb") as f:
        buf = f.read().rstrip(b"\r\n")

    ptn = b"\n# eof\n#"
    a = buf.find(ptn)
    if a < 0:
        raise Exception("could not find archive marker")

    esc = {b"??": b"?", b"?r": b"\r", b"?n": b"\n", b"?0": b"\x00"}
    buf = buf[a + len(ptn) :].replace(b"\n#", b"")
    p = 0
    while buf:
        a = buf.find(b"?", p)
        if a < 0:
            yield buf[p:]
            break
        elif a == p:
            yield esc[buf[p : p + 2]]
            p += 2
        else:
            yield buf[p:a]
            p = a


def utime(top):
    # avoid cleaners
    files = [os.path.join(dp, p) for dp, dd, df in os.walk(top) for p in dd + df]
    while True:
        t = int(time.time())
        for f in [top] + files:
            os.utime(f, (t, t))

        time.sleep(78123)


def confirm(rv):
    msg()
    msg("retcode", rv if rv else traceback.format_exc())
    if WINDOWS:
        msg("*** hit enter to exit ***")
        try:
            raw_input() if PY2 else input()
        except:
            pass

    sys.exit(rv or 1)


def run(tmp, j2, ftp):
    msg("jinja2:", j2 or "bundled")
    msg("pyftpd:", ftp or "bundled")
    msg("sfxdir:", tmp)
    msg()

    t = threading.Thread(target=utime, args=(tmp,))
    t.daemon = True
    t.start()

    ld = (("", ""), (j2, "j2"), (ftp, "ftp"), (not PY2, "py2"), (PY37, "py37"))
    ld = [os.path.join(tmp, b) for a, b in ld if not a]

    # skip 1
    # enable this to dynamically remove type hints at startup,
    # in case a future python version can use them for performance
    if sys.version_info < (3, 10) and False:
        sys.path.insert(0, ld[0])

        from strip_hints.a import uh

        uh(tmp + "/copyparty")
    # skip 0

    if any([re.match(r"^-.*j[0-9]", x) for x in sys.argv]):
        run_s(ld)
    else:
        run_i(ld)


def run_i(ld):
    for x in ld:
        sys.path.insert(0, x)

    from copyparty.__main__ import main as p

    p()


def run_s(ld):
    # fmt: off
    c = "import sys,runpy;" + "".join(['sys.path.insert(0,r"' + x.replace("\\", "/") + '");' for x in ld]) + 'runpy.run_module("copyparty",run_name="__main__")'
    c = [str(x) for x in [sys.executable, "-c", c] + list(sys.argv[1:])]
    # fmt: on
    msg("\n", c, "\n")
    p = sp.Popen(c)

    def bye(*a):
        p.send_signal(signal.SIGINT)

    signal.signal(signal.SIGTERM, bye)
    p.wait()

    raise SystemExit(p.returncode)


def main():
    sysver = str(sys.version).replace("\n", "\n" + " " * 18)
    pktime = time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime(STAMP))
    msg()
    msg("   this is: copyparty", VER)
    msg(" packed at:", pktime, "UTC,", STAMP)
    msg("archive is:", me)
    msg("python bin:", sys.executable)
    msg("python ver:", platform.python_implementation(), sysver)
    msg()

    arg = ""
    try:
        arg = sys.argv[1]
    except:
        pass

    # skip 1

    if arg == "--sfx-testgen":
        return encode(testptn(), 1, "x", "x", 1)

    if arg == "--sfx-testchk":
        return testchk(get_payload())

    if arg == "--sfx-make":
        tar, ver, ts = sys.argv[2:]
        return makesfx(tar, ver, ts)

    # skip 0

    tmp = os.path.realpath(unpack())

    try:
        from jinja2 import __version__ as j2
    except:
        j2 = None

    try:
        from pyftpdlib.__init__ import __ver__ as ftp
    except:
        ftp = None

    try:
        run(tmp, j2, ftp)
    except SystemExit as ex:
        c = ex.code
        if c not in [0, -15]:
            confirm(ex.code)
    except KeyboardInterrupt:
        pass
    except:
        confirm(0)


if __name__ == "__main__":
    main()


# skip 1
# python sfx.py --sfx-testgen && python test.py --sfx-testchk
# c:\Python27\python.exe sfx.py --sfx-testgen && c:\Python27\python.exe test.py --sfx-testchk

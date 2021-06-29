#!/usr/bin/env python
# coding: latin-1
from __future__ import print_function, unicode_literals

import re, os, sys, time, shutil, signal, threading, tarfile, hashlib, platform, tempfile, traceback
import subprocess as sp

"""
pls don't edit this file with a text editor,
  it breaks the compressed stuff at the end

run me with any version of python, i will unpack and run copyparty

there's zero binaries! just plaintext python scripts all the way down
  so you can easily unpack the archive and inspect it for shady stuff

the archive data is attached after the b"\n# eof\n" archive marker,
  b"\n#n" decodes to b"\n"
  b"\n#r" decodes to b"\r"
  b"\n# " decodes to b""
"""

# set by make-sfx.sh
VER = None
SIZE = None
CKSUM = None
STAMP = None

PY2 = sys.version_info[0] == 2
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
    nin = 0
    nout = 0
    skip = False
    with open(me, "rb") as fi:
        unpk = ""
        src = fi.read().replace(b"\r", b"").rstrip(b"\n").decode("utf-8")
        for ln in src.split("\n"):
            if ln.endswith("# skip 0"):
                skip = False
                continue

            if ln.endswith("# skip 1") or skip:
                skip = True
                continue

            if ln.strip().startswith("# fmt: "):
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
        f.write(unpk.encode("utf-8") + b"\n\n# eof\n# ")
        for buf in data:
            ebuf = buf.replace(b"\n", b"\n#n").replace(b"\r", b"\n#r")
            f.write(ebuf)
            nin += len(buf)
            nout += len(ebuf)

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
    h = hashlib.md5()
    for block in yieldfile(fn):
        h.update(block)

    return h.hexdigest()


def unpack():
    """unpacks the tar yielded by `data`"""
    name = "pe-copyparty"
    tag = "v" + str(STAMP)
    withpid = "{}.{}".format(name, os.getpid())
    top = tempfile.gettempdir()
    opj = os.path.join
    final = opj(top, name)
    mine = opj(top, withpid)
    tar = opj(mine, "tar")

    try:
        if tag in os.listdir(final):
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
        tf.extractall(mine)

    os.remove(tar)

    with open(opj(mine, tag), "wb") as f:
        f.write(b"h\n")

    try:
        if tag in os.listdir(final):
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
        ptn = b"\n# eof\n# "
        buf = b""
        for n in range(64):
            buf += f.read(4096)
            ofs = buf.find(ptn)
            if ofs >= 0:
                break

        if ofs < 0:
            raise Exception("could not find archive marker")

        # start at final b"\n"
        fpos = ofs + len(ptn) - 3
        f.seek(fpos)
        dpos = 0
        rem = b""
        while True:
            rbuf = f.read(1024 * 32)
            if rbuf:
                buf = rem + rbuf
                ofs = buf.rfind(b"\n")
                if len(buf) <= 4:
                    rem = buf
                    continue

                if ofs >= len(buf) - 4:
                    rem = buf[ofs:]
                    buf = buf[:ofs]
                else:
                    rem = b"\n# "
            else:
                buf = rem

            fpos += len(buf) + 1
            for a, b in [[b"\n# ", b""], [b"\n#r", b"\r"], [b"\n#n", b"\n"]]:
                buf = buf.replace(a, b)

            dpos += len(buf) - 1
            yield buf

            if not rbuf:
                break


def utime(top):
    i = 0
    files = [os.path.join(dp, p) for dp, dd, df in os.walk(top) for p in dd + df]
    while WINDOWS:
        t = int(time.time())
        if i:
            msg("utime {}, {}".format(i, t))

        for f in files:
            os.utime(f, (t, t))

        i += 1
        time.sleep(78123)


def confirm(rv):
    msg()
    msg("retcode", rv if rv else traceback.format_exc())
    msg("*** hit enter to exit ***")
    try:
        raw_input() if PY2 else input()
    except:
        pass

    sys.exit(rv)


def run(tmp, j2):
    msg("jinja2:", j2 or "bundled")
    msg("sfxdir:", tmp)
    msg()

    # block systemd-tmpfiles-clean.timer
    try:
        import fcntl

        fd = os.open(tmp, os.O_RDONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception as ex:
        if not WINDOWS:
            msg("\033[31mflock:", repr(ex))

    t = threading.Thread(target=utime, args=(tmp,))
    t.daemon = True
    t.start()

    ld = [tmp, os.path.join(tmp, "dep-j2")]
    if j2:
        del ld[-1]

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
    c = "import sys,runpy;" + "".join(['sys.path.insert(0,r"' + x + '");' for x in ld]) + 'runpy.run_module("copyparty",run_name="__main__")'
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
        run(tmp, j2)
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

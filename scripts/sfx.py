#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

import os, sys, time, shutil, signal, tarfile, hashlib, platform, tempfile
import subprocess as sp

"""
run me with any version of python, i will unpack and run copyparty

(but please don't edit this file with a text editor
  since that would probably corrupt the binary stuff at the end)

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
sys.dont_write_bytecode = True
me = os.path.abspath(os.path.realpath(__file__))
cpp = None


def eprint(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def msg(*args, **kwargs):
    if args:
        args = ["[SFX]", args[0]] + list(args[1:])

    eprint(*args, **kwargs)


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
    hasher = hashlib.md5()
    for block in yieldfile(fn):
        hasher.update(block)

    return hasher.hexdigest()


def unpack():
    """unpacks the tar yielded by `data`"""
    name = "pe-copyparty"
    tag = "v" + str(STAMP)
    withpid = "{}.{}".format(name, os.getpid())
    top = tempfile.gettempdir()
    final = os.path.join(top, name)
    mine = os.path.join(top, withpid)
    tar = os.path.join(mine, "tar")

    try:
        if tag in os.listdir(final):
            msg("found early")
            return final
    except:
        pass

    nwrite = 0
    os.mkdir(mine)
    with open(tar, "wb") as f:
        for buf in get_payload():
            nwrite += len(buf)
            f.write(buf)

    if nwrite != SIZE:
        t = "\n\n  bad file:\n    expected {} bytes, got {}\n".format(SIZE, nwrite)
        raise Exception(t)

    cksum = hashfile(tar)
    if cksum != CKSUM:
        t = "\n\n  bad file:\n    {} expected,\n    {} obtained\n".format(CKSUM, cksum)
        raise Exception(t)

    with tarfile.open(tar, "r:bz2") as tf:
        tf.extractall(mine)

    os.remove(tar)

    with open(os.path.join(mine, tag), "wb") as f:
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

    try:
        os.symlink(mine, final)
    except:
        try:
            os.rename(mine, final)
        except:
            msg("reloc fail,", mine)
            return mine

    for fn in u8(os.listdir(top)):
        if fn.startswith(name) and fn not in [name, withpid]:
            try:
                old = os.path.join(top, fn)
                if time.time() - os.path.getmtime(old) > 10:
                    shutil.rmtree(old)
            except:
                pass

    return final


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

        # start reading from the final b"\n"
        fpos = ofs + len(ptn) - 3
        # msg("tar found at", fpos)
        f.seek(fpos)
        dpos = 0
        leftovers = b""
        while True:
            rbuf = f.read(1024 * 32)
            if rbuf:
                buf = leftovers + rbuf
                ofs = buf.rfind(b"\n")
                if len(buf) <= 4:
                    leftovers = buf
                    continue

                if ofs >= len(buf) - 4:
                    leftovers = buf[ofs:]
                    buf = buf[:ofs]
                else:
                    leftovers = b"\n# "
            else:
                buf = leftovers

            fpos += len(buf) + 1
            buf = (
                buf.replace(b"\n# ", b"")
                .replace(b"\n#r", b"\r")
                .replace(b"\n#n", b"\n")
            )
            dpos += len(buf) - 1

            yield buf

            if not rbuf:
                break


def confirm():
    msg()
    msg("*** hit enter to exit ***")
    try:
        raw_input() if PY2 else input()
    except:
        pass


def run(tmp, j2ver):
    global cpp

    msg("jinja2:", j2ver or "bundled")
    msg("sfxdir:", tmp)

    # "systemd-tmpfiles-clean.timer"?? HOW do you even come up with this shit
    try:
        import fcntl

        fd = os.open(tmp, os.O_RDONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tmp = os.readlink(tmp)  # can't flock a symlink, even with O_NOFOLLOW
    except:
        pass

    ld = [tmp, os.path.join(tmp, "dep-j2")]
    if j2ver:
        del ld[-1]

    cmd = (
        "import sys, runpy; "
        + "".join(['sys.path.insert(0, r"' + x + '"); ' for x in ld])
        + 'runpy.run_module("copyparty", run_name="__main__")'
    )
    cmd = [sys.executable, "-c", cmd] + list(sys.argv[1:])

    cmd = [str(x) for x in cmd]
    msg("\n", cmd, "\n")
    cpp = sp.Popen(cmd)
    try:
        cpp.wait()
    except:
        cpp.wait()

    if cpp.returncode != 0:
        confirm()

    sys.exit(cpp.returncode)


def bye(sig, frame):
    if cpp is not None:
        cpp.terminate()


def main():
    sysver = str(sys.version).replace("\n", "\n" + " " * 18)
    pktime = time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime(STAMP))
    os.system("")
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

    signal.signal(signal.SIGTERM, bye)

    tmp = unpack()

    try:
        from jinja2 import __version__ as j2ver
    except:
        j2ver = None

    return run(tmp, j2ver)


if __name__ == "__main__":
    main()


# skip 1
# python sfx.py --sfx-testgen && python test.py --sfx-testchk
# c:\Python27\python.exe sfx.py --sfx-testgen && c:\Python27\python.exe test.py --sfx-testchk

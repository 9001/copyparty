#!/usr/bin/env python3

import atexit
import os
import platform
import sys
import tarfile
import tempfile
import threading
import time
import traceback


VER = None
STAMP = None
WINDOWS = sys.platform in ["win32", "msys"]


def msg(*a, **ka):
    if a:
        a = ["[ZIP]", a[0]] + list(a[1:])

    ka["file"] = sys.stderr
    print(*a, **ka)


def utime(top):
    # avoid cleaners
    files = [os.path.join(dp, p) for dp, dd, df in os.walk(top) for p in dd + df]
    try:
        while True:
            t = int(time.time())
            for f in [top] + files:
                os.utime(f, (t, t))

            time.sleep(78123)
    except Exception as ex:
        print("utime:", ex, f)


def confirm(rv):
    msg()
    msg("retcode", rv if rv else traceback.format_exc())
    if WINDOWS:
        msg("*** hit enter to exit ***")
        try:
            input()
        except:
            pass

    sys.exit(rv or 1)


def run():
    import copyparty
    from copyparty.__main__ import main as cm

    td = tempfile.TemporaryDirectory(prefix="")
    atexit.register(td.cleanup)
    rsrc = td.name

    try:
        from importlib.resources import files

        f = files(copyparty).joinpath("z.tar").open("rb")
    except:
        from importlib.resources import open_binary

        f = open_binary("copyparty", "z.tar")

    with tarfile.open(fileobj=f) as tf:
        try:
            tf.extractall(rsrc, filter="tar")
        except TypeError:
            tf.extractall(rsrc)  # nosec (archive is safe)

    f.close()
    f = None

    msg("  rsrc dir:", rsrc)
    msg()

    t = threading.Thread(target=utime, args=(rsrc,), name="utime")
    t.daemon = True
    t.start()

    cm(rsrc=rsrc)


def main():
    sysver = str(sys.version).replace("\n", "\n" + " " * 18)
    pktime = time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime(STAMP))
    msg()
    msg("   this is: copyparty", VER)
    msg(" packed at:", pktime, "UTC,", STAMP)
    msg("python bin:", sys.executable)
    msg("python ver:", platform.python_implementation(), sysver)

    try:
        run()
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

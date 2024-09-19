#!/usr/bin/env python3

import sys
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
    from copyparty.__main__ import main as cm

    cm()


def main():
    pktime = time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime(STAMP))
    msg()
    msg("build-time:", pktime, "UTC,", STAMP)
    msg("python-bin:", sys.executable)
    msg()

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

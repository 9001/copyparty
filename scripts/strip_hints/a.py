# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
from strip_hints import strip_file_to_string


# list unique types used in hints:
# rm -rf unt && cp -pR copyparty unt && (cd unt && python3 ../scripts/strip_hints/a.py)
# diff -wNarU1 copyparty unt | grep -E '^\-' | sed -r 's/[^][, ]+://g; s/[^][, ]+[[(]//g; s/[],()<>{} -]/\n/g' | grep -E .. | sort | uniq -c | sort -n


def pr(m):
    sys.stderr.write(m)
    sys.stderr.flush()


def uh(top):
    if os.path.exists(top + "/uh"):
        return

    # pr("building support for your python ver")
    pr("unhinting")
    files = []
    for (dp, _, fns) in os.walk(top):
        for fn in fns:
            if not fn.endswith(".py"):
                continue

            fp = os.path.join(dp, fn)
            files.append(fp)

    try:
        import multiprocessing as mp

        with mp.Pool(os.cpu_count()) as pool:
            pool.map(uh1, files)
    except Exception as ex:
        print("\nnon-mp fallback due to {}\n".format(ex))
        for fp in files:
            uh1(fp)

    pr("k\n\n")
    with open(top + "/uh", "wb") as f:
        f.write(b"a")


def uh1(fp):
    pr(".")
    cs = strip_file_to_string(fp, no_ast=True, to_empty=True)

    # remove expensive imports too
    lns = []
    on = True
    for ln in cs.split("\n"):
        if ln.startswith("if True:"):
            on = False
            continue

        if not on and (not ln.strip() or ln.startswith(" ")):
            continue

        on = True
        lns.append(ln)

    cs = "\n".join(lns)
    with open(fp, "wb") as f:
        f.write(cs.encode("utf-8"))


if __name__ == "__main__":
    uh(".")

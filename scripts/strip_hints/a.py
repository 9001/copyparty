# coding: utf-8
from __future__ import print_function, unicode_literals

import re
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

    libs = "typing|types|collections\.abc"
    ptn = re.compile(r"^(\s*)(from (?:{0}) import |import (?:{0})\b).*".format(libs))

    # pr("building support for your python ver")
    pr("unhinting")
    for (dp, _, fns) in os.walk(top):
        for fn in fns:
            if not fn.endswith(".py"):
                continue

            pr(".")
            fp = os.path.join(dp, fn)
            cs = strip_file_to_string(fp, no_ast=True, to_empty=True)

            # remove expensive imports too
            lns = []
            for ln in cs.split("\n"):
                m = ptn.match(ln)
                if m:
                    ln = m.group(1) + "raise Exception()"

                lns.append(ln)

            cs = "\n".join(lns)
            with open(fp, "wb") as f:
                f.write(cs.encode("utf-8"))

    pr("k\n\n")
    with open(top + "/uh", "wb") as f:
        f.write(b"a")


if __name__ == "__main__":
    uh(".")

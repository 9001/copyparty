#!/usr/bin/env python3

import re, os, sys, codecs

outfile = os.path.realpath(sys.argv[1])

os.chdir(os.path.dirname(__file__))

with open("../docs/lics.txt", "rb") as f:
    s = f.read().decode("utf-8").rstrip("\n") + "\n\n\n\n"
    s = re.sub("\nC: ", "\nCopyright (c) ", s)
    s = re.sub("\nL: ", "\nLicense: ", s)
    ret = s.split("\n")

lics = [
    "MIT License",
    "BSD 2-Clause License",
    "BSD 3-Clause License",
    "ISC License",
    "Apache License v2.0",
    "SIL Open Font License v1.1",
]

for n, lic in enumerate(lics, 1):
    with open("lics/%d.r13" % (n,), "rb") as f:
        s = f.read().decode("utf-8")
        s = codecs.decode(s, "rot_13")
        s = "\n--- %s ---\n\n%s" % (lic, s)
        ret.extend(s.split("\n"))

for n, ln in enumerate(ret):
    if not ln.startswith("--- "):
        continue
    pad = " " * ((80 - len(ln)) // 2)
    ln = "%s\033[07m%s\033[0m" % (pad, ln)
    ret[n] = ln

ret.append("")
ret.append("")

with open(outfile, "wb") as f:
    f.write(("\n".join(ret)).encode("utf-8"))

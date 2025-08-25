#!/usr/bin/env python3

import os
import codecs

for fn in os.listdir("."):
    if not fn.endswith(".txt"):
        continue
    with open(fn, "rb") as f:
        s = f.read().decode("utf-8")
    b = codecs.encode(s, "rot_13").encode("utf-8")
    with open(fn.replace("txt", "r13"), "wb") as f:
        f.write(b)

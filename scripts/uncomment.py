#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import io
import os
import sys
import tokenize


def uncomment(fpath):
    """modified https://stackoverflow.com/a/62074206"""

    print(".", end="", flush=True)
    with open(fpath, "rb") as f:
        orig = f.read().decode("utf-8")

    out = ""
    for ln in orig.split("\n"):
        if not ln.startswith("#"):
            break

        out += ln + "\n"

    io_obj = io.StringIO(orig)
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        # print(repr(tok))
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]

        if start_line > last_lineno:
            last_col = 0

        if start_col > last_col:
            out += " " * (start_col - last_col)

        is_legalese = (
            "copyright" in token_string.lower() or "license" in token_string.lower()
        )

        if token_type == tokenize.STRING:
            if (
                prev_toktype != tokenize.INDENT
                and prev_toktype != tokenize.NEWLINE
                and start_col > 0
                or is_legalese
            ):
                out += token_string
            else:
                out += '"a"'
        elif token_type != tokenize.COMMENT or is_legalese:
            out += token_string

        prev_toktype = token_type
        last_lineno = end_line
        last_col = end_col

    # out = "\n".join(x for x in out.splitlines() if x.strip())

    with open(fpath, "wb") as f:
        f.write(out.encode("utf-8"))


def main():
    print("uncommenting", end="", flush=True)
    try:
        import multiprocessing as mp

        with mp.Pool(os.cpu_count()) as pool:
            pool.map(uncomment, sys.argv[1:])
    except Exception as ex:
        print("\nnon-mp fallback due to {}\n".format(ex))
        for f in sys.argv[1:]:
            uncomment(f)

    print("k")


if __name__ == "__main__":
    main()

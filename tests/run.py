#!/usr/bin/env python3

import sys
import runpy

host = sys.argv[1]
sys.argv = sys.argv[:1] + sys.argv[2:]
sys.path.insert(0, ".")


def rp():
    runpy.run_module("unittest", run_name="__main__")


if host == "vmprof":
    rp()

elif host == "cprofile":
    import cProfile
    import pstats

    log_fn = "cprofile.log"
    cProfile.run("rp()", log_fn)
    p = pstats.Stats(log_fn)
    p.sort_stats(pstats.SortKey.CUMULATIVE).print_stats(64)


"""
python3.9 tests/run.py cprofile -v tests/test_httpcli.py

python3.9 -m pip install --user vmprof
python3.9 -m vmprof --lines -o vmprof.log tests/run.py vmprof -v tests/test_httpcli.py
"""

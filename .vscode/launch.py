# takes arguments from launch.json
# is used by no_dbg in tasks.json
# launches 10x faster than mspython debugpy
# and is stoppable with ^C

import re
import os
import sys
import shlex
import jstyleson
import subprocess as sp

with open(".vscode/launch.json", "r", encoding="utf-8") as f:
    tj = f.read()

oj = jstyleson.loads(tj)
argv = oj["configurations"][0]["args"]

try:
    sargv = " ".join([shlex.quote(x) for x in argv])
    print(sys.executable + " -m copyparty " + sargv + "\n")
except:
    pass

argv = [os.path.expanduser(x) if x.startswith("~") else x for x in argv]

if re.search(" -j ?[0-9]", " ".join(argv)):
    argv = [sys.executable, "-m", "copyparty"] + argv
    sp.check_call(argv)
else:
    sys.path.insert(0, os.getcwd())
    from copyparty.__main__ import main as copyparty

    try:
        copyparty(["a"] + argv)
    except SystemExit as ex:
        if ex.code:
            raise

print("\n\033[32mokke\033[0m")
sys.exit(1)

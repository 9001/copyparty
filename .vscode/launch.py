# takes arguments from launch.json
# is used by no_dbg in tasks.json
# launches 10x faster than mspython debugpy
# and is stoppable with ^C

import os
import sys

sys.path.insert(0, os.getcwd())

import jstyleson
from copyparty.__main__ import main as copyparty

with open(".vscode/launch.json", "r") as f:
    tj = f.read()

oj = jstyleson.loads(tj)
argv = oj["configurations"][0]["args"]
argv = [os.path.expanduser(x) if x.startswith("~") else x for x in argv]
try:
    copyparty(argv)
except SystemExit as ex:
    if ex.code:
        raise

print("\n\033[32mokke\033[0m")
sys.exit(1)

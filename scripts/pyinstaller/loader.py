# coding: utf-8

v = r"""

this is the EXE edition of copyparty, compatible with Windows7-SP1
and later. To make this possible, the EXE was compiled with Python
3.7.9, which is EOL and does not receive security patches anymore.

it is strongly recommended to use the python sfx instead:
https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py
"""

print(v.replace("\n", "\n░▌ ")[1:] + "\n")


import re
import os
import sys
import shutil
import subprocess as sp


def meicln(mod, pids):
    pdir, mine = os.path.split(mod)
    dirs = os.listdir(pdir)
    dirs = [x for x in dirs if x.startswith("_MEI") and x != mine]
    dirs = [os.path.join(pdir, x) for x in dirs]
    rm = []
    for d in dirs:
        if os.path.isdir(os.path.join(d, "copyparty", "web")):
            rm.append(d)

    if not rm:
        return

    print("deleting abandoned SFX dirs:")
    for d in rm:
        print(d)
        for _ in range(9):
            try:
                shutil.rmtree(d)
                break
            except:
                pass

    print()


def meichk():
    filt = "copyparty"
    if filt not in sys.executable:
        filt = os.path.basename(sys.executable)

    pids = []
    ptn = re.compile(r"^([^\s]+)\s+([0-9]+)")
    procs = sp.check_output("tasklist").decode("utf-8", "replace")
    for ln in procs.splitlines():
        m = ptn.match(ln)
        if m and filt in m.group(1).lower():
            pids.append(int(m.group(2)))

    mod = os.path.dirname(os.path.realpath(__file__))
    if os.path.basename(mod).startswith("_MEI") and len(pids) == 2:
        meicln(mod, pids)


meichk()


from copyparty.__main__ import main

main()

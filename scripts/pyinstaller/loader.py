# coding: utf-8

import os
import re
import shutil
import subprocess as sp
import sys
import traceback

v = r"""

this 32-bit copyparty.exe is compatible with Windows7-SP1 and later.
To make this possible, the EXE was compiled with Python 3.7.9,
which is EOL and does not receive security patches anymore.

if possible, for performance and security reasons, please use this instead:
https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py
"""

if sys.version_info > (3, 10):
    v = r"""

this 64-bit copyparty.exe is compatible with Windows 8 and later.
No security issues were known to affect this EXE at build time,
however that may have changed since then.

if possible, for performance and security reasons, please use this instead:
https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py
"""

try:
    print(v.replace("\n", "\n▒▌ ")[1:] + "\n")
except:
    print(v.replace("\n", "\n|| ")[1:] + "\n")


def confirm(rv):
    print()
    print("retcode", rv if rv else traceback.format_exc())
    print("*** hit enter to exit ***")
    try:
        input()
    except:
        pass

    sys.exit(rv or 1)


def meicln(mod):
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
    try:
        procs = sp.check_output("tasklist").decode("utf-8", "replace")
    except:
        procs = ""  # winpe

    for ln in procs.splitlines():
        m = ptn.match(ln)
        if m and filt in m.group(1).lower():
            pids.append(int(m.group(2)))

    mod = os.path.dirname(os.path.realpath(__file__))
    if os.path.basename(mod).startswith("_MEI") and len(pids) == 2:
        meicln(mod)


meichk()


from copyparty.__main__ import main

try:
    main()
except SystemExit as ex:
    c = ex.code
    if c not in [0, -15]:
        confirm(ex.code)
except KeyboardInterrupt:
    pass
except:
    confirm(0)

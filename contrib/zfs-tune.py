#!/usr/bin/env python3

import os
import sqlite3
import sys
import traceback


"""
when the up2k-database is stored on a zfs volume, this may give
slightly higher performance (actual gains not measured yet)

NOTE: must be applied in combination with the related advice in the openzfs documentation;
https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Workload%20Tuning.html#database-workloads
and see specifically the SQLite subsection

it is assumed that all databases are stored in a single location,
for example with `--hist /var/store/hists`

three alternatives for running this script:

1. copy it into /var/store/hists and run "python3 zfs-tune.py s"
    (s = modify all databases below folder containing script)

2. cd into /var/store/hists and run "python3 ~/zfs-tune.py w"
    (w = modify all databases below current working directory)

3. python3 ~/zfs-tune.py /var/store/hists

if you use docker, run copyparty with `--hist /cfg/hists`, copy this script into /cfg, and run this:
podman run --rm -it --entrypoint /usr/bin/python3 ghcr.io/9001/copyparty-ac /cfg/zfs-tune.py s

"""


PAGESIZE = 65536


# borrowed from copyparty; short efficient stacktrace for errors
def min_ex(max_lines: int = 8, reverse: bool = False) -> str:
    et, ev, tb = sys.exc_info()
    stb = traceback.extract_tb(tb) if tb else traceback.extract_stack()[:-1]
    fmt = "%s:%d <%s>: %s"
    ex = [fmt % (fp.split(os.sep)[-1], ln, fun, txt) for fp, ln, fun, txt in stb]
    if et or ev or tb:
        ex.append("[%s] %s" % (et.__name__ if et else "(anonymous)", ev))
    return "\n".join(ex[-max_lines:][:: -1 if reverse else 1])


def set_pagesize(db_path):
    try:
        # check current page_size
        with sqlite3.connect(db_path) as db:
            v = db.execute("pragma page_size").fetchone()[0]
            if v == PAGESIZE:
                print(" `-- OK")
                return

        # https://www.sqlite.org/pragma.html#pragma_page_size
        #  `- disable wal; set pagesize; vacuum
        #      (copyparty will re-enable wal if necessary)

        with sqlite3.connect(db_path) as db:
            db.execute("pragma journal_mode=delete")
            db.commit()

        with sqlite3.connect(db_path) as db:
            db.execute(f"pragma page_size = {PAGESIZE}")
            db.execute("vacuum")

        print(" `-- new pagesize OK")

    except Exception:
        err = min_ex().replace("\n", "\n -- ")
        print(f"FAILED: {db_path}\n -- {err}")


def main():
    top = os.path.dirname(os.path.abspath(__file__))
    cwd = os.path.abspath(os.getcwd())
    try:
        x = sys.argv[1]
    except:
        print(f"""
this script takes one mandatory argument:
specify 's' to start recursing from folder containing this script file ({top})
specify 'w' to start recursing from the current working directory ({cwd})
specify a path to start recursing from there
""")
        sys.exit(1)

    if x.lower() == "w":
        top = cwd
    elif x.lower() != "s":
        top = x

    for dirpath, dirs, files in os.walk(top):
        for fname in files:
            if not fname.endswith(".db"):
                continue
            db_path = os.path.join(dirpath, fname)
            print(db_path)
            set_pagesize(db_path)


if __name__ == "__main__":
    main()

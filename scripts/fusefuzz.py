#!/usr/bin/env python3

import os
import time

"""
mkdir -p /dev/shm/fusefuzz/{r,v}
PYTHONPATH=.. python3 -m copyparty -v /dev/shm/fusefuzz/r::r -i 127.0.0.1
../bin/copyparty-fuse.py /dev/shm/fusefuzz/v http://127.0.0.1:3923/ 2 0
(d="$PWD"; cd /dev/shm/fusefuzz && "$d"/fusefuzz.py)
"""


def chk(fsz, rsz, ofs0, shift, ofs, rf, vf):
    if ofs != rf.tell():
        rf.seek(ofs)
        vf.seek(ofs)

    rb = rf.read(rsz)
    vb = vf.read(rsz)

    print(f"fsz {fsz} rsz {rsz} ofs {ofs0} shift {shift} ofs {ofs} = {len(rb)}")

    if rb != vb:
        for n, buf in enumerate([rb, vb]):
            with open("buf." + str(n), "wb") as f:
                f.write(buf)

        raise Exception(f"{len(rb)} != {len(vb)}")

    return rb, vb


def main():
    v = "v"
    for n in range(5):
        with open(f"r/{n}", "wb") as f:
            f.write(b"h" * n)

    rand = os.urandom(7919)  # prime
    for fsz in range(1024 * 1024 * 2 - 3, 1024 * 1024 * 2 + 3):
        with open("r/f", "wb", fsz) as f:
            f.write((rand * int(fsz / len(rand) + 1))[:fsz])

        for rsz in range(64 * 1024 - 2, 64 * 1024 + 2):
            ofslist = [0, 1, 2]
            for n in range(3):
                ofslist.append(fsz - n)
                ofslist.append(fsz - (rsz * 1 + n))
                ofslist.append(fsz - (rsz * 2 + n))

            for ofs0 in ofslist:
                for shift in range(-3, 3):
                    print(f"fsz {fsz} rsz {rsz} ofs {ofs0} shift {shift}")
                    ofs = ofs0
                    if ofs < 0 or ofs >= fsz:
                        continue

                    for n in range(1, 3):
                        with open(f"{v}/{n}", "rb") as f:
                            f.read()

                    prev_ofs = -99
                    with open("r/f", "rb", rsz) as rf:
                        with open(f"{v}/f", "rb", rsz) as vf:
                            while True:
                                ofs += shift
                                if ofs < 0 or ofs > fsz or ofs == prev_ofs:
                                    break

                                prev_ofs = ofs

                                rb, vb = chk(fsz, rsz, ofs0, shift, ofs, rf, vf)

                                if not rb:
                                    break

                                ofs += len(rb)

                    for n in range(1, 3):
                        with open(f"{v}/{n}", "rb") as f:
                            f.read()

                    with open("r/f", "rb", rsz) as rf:
                        with open(f"{v}/f", "rb", rsz) as vf:
                            for n in range(2):
                                ofs += shift
                                if ofs < 0 or ofs > fsz:
                                    break

                                rb, vb = chk(fsz, rsz, ofs0, shift, ofs, rf, vf)

                                ofs -= rsz

        # bumping fsz, sleep away the dentry cache in cppf
        time.sleep(1)


if __name__ == "__main__":
    main()

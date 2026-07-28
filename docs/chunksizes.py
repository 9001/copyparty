#!/usr/bin/env python3

# there's far better ways to do this but its 4am and i dont wanna think

# just pypy it my dude

import math

def humansize(sz, terse=False):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if sz < 1024:
            break

        sz /= 1024.0

    ret = " ".join([str(sz)[:4].rstrip("."), unit])

    if not terse:
        return ret

    return ret.replace("iB", "").replace(" ", "")


def up2k_chunksize(filesize):
    chunksize = 1024 * 1024
    stepsize = 512 * 1024
    while True:
        for mul in [1, 2]:
            nchunks = -int(-filesize // chunksize)
            if nchunks <= 256 or (chunksize >= 32 * 1024 * 1024 and nchunks <= 4096):
                return chunksize

            chunksize += stepsize
            stepsize *= mul


def main():
    prev = 1048576
    n = n0 = 524288
    while True:
        csz = up2k_chunksize(n)
        if csz > prev:
            print(f"| {n-n0:>18_} | {humansize(n-n0):>8} | {prev:>13_} | {humansize(prev):>8} |".replace("_", " "))
            prev = csz
        n += n0


main()

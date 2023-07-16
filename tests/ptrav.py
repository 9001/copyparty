#!/usr/bin/env python3

import re
import sys
import time
import itertools

from . import util as tu
from .util import Cfg

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli

atlas = ["%", "25", "2e", "2f", ".", "/"]


def nolog(*a, **ka):
    pass


def hdr(query):
    h = "GET /{} HTTP/1.1\r\nCookie: cppwd=o\r\nConnection: close\r\n\r\n"
    return h.format(query).encode("utf-8")


def curl(args, asrv, url, binary=False):
    conn = tu.VHttpConn(args, asrv, nolog, hdr(url))
    HttpCli(conn).run()
    if binary:
        h, b = conn.s._reply.split(b"\r\n\r\n", 1)
        return [h.decode("utf-8"), b]

    return conn.s._reply.decode("utf-8").split("\r\n\r\n", 1)


def genlen(ubase, ntot, nth, wlen):
    args = Cfg(v=["s2::r"], a=["o:o", "x:x"])
    asrv = AuthSrv(args, print)
    # h, ret = curl(args, asrv, "hey")

    n = 0
    t0 = time.time()
    print("genlen %s nth %s" % (wlen, nth))
    ptn = re.compile(r"2.2.2.2|\.\.\.|///|%%%|\.2|/2./|%\.|/%/")
    for path in itertools.product(atlas, repeat=wlen):
        if "%" not in path:
            continue
        path = "".join(path)
        if ptn.search(path):
            continue
        n += 1
        if n % ntot != nth:
            continue
        url = ubase + path + "fa"
        if n % 500 == nth:
            spd = n / (time.time() - t0)
            print(wlen, n, int(spd), url)

        hdr, r = curl(args, asrv, url)
        if "fgsfds" in r:
            with open("hit-%s.txt" % (time.time()), "w", encoding="utf-8") as f:
                f.write(url)
            raise Exception("HIT! {}".format(url))


def main():
    ubase = sys.argv[1]
    ntot = int(sys.argv[2])
    nth = int(sys.argv[3])
    for wlen in range(20):
        genlen(ubase, ntot, nth, wlen)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass


"""
nice pypy3 -m tests.ptrav "" 2 0
nice pypy3 -m tests.ptrav "" 2 1
nice pypy3 -m tests.ptrav .cpr 2 0
nice pypy3 -m tests.ptrav .cpr 2 1
(13x faster than /scripts/test/ptrav.py)
"""

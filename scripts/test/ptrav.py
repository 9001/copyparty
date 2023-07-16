#!/usr/bin/env python3

import re
import sys
import time
import itertools
import requests

atlas = ["%", "25", "2e", "2f", ".", "/"]


def genlen(ubase, port, ntot, nth, wlen):
    n = 0
    t0 = time.time()
    print("genlen %s nth %s port %s" % (wlen, nth, port))
    rsession = requests.Session()
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
        url = ubase % (port, path)
        if n % 500 == nth:
            spd = n / (time.time() - t0)
            print(wlen, n, int(spd), url)

        try:
            r = rsession.get(url)
        except KeyboardInterrupt:
            raise
        except:
            print("\n[=== RETRY ===]", url)
            try:
                r = rsession.get(url)
            except:
                r = rsession.get(url)

        if "fgsfds" in r.text:
            with open("hit-%s.txt" % (time.time()), "w", encoding="utf-8") as f:
                f.write(url)
            raise Exception("HIT! {}".format(url))


def main():
    ubase = sys.argv[1]
    port = int(sys.argv[2])
    ntot = int(sys.argv[3])
    nth = int(sys.argv[4])
    for wlen in range(20):
        genlen(ubase, port, ntot, nth, wlen)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

"""
python3 -m copyparty -v srv::r -p 3931 -q -j4
nice python3 ./ptrav.py "http://127.0.0.1:%s/%sfa" 3931 3 0
nice python3 ./ptrav.py "http://127.0.0.1:%s/%sfa" 3931 3 1
nice python3 ./ptrav.py "http://127.0.0.1:%s/%sfa" 3931 3 2
nice python3 ./ptrav2.py "http://127.0.0.1:%s/.cpr/%sfa" 3931 3 0
nice python3 ./ptrav2.py "http://127.0.0.1:%s/.cpr/%sfa" 3931 3 1
nice python3 ./ptrav2.py "http://127.0.0.1:%s/.cpr/%sfa" 3931 3 2
(13x slower than /tests/ptrav.py)
"""

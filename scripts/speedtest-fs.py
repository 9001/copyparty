#!/usr/bin/env python

import os
import sys
import stat
import time
import signal
import traceback
import threading
from queue import Queue


"""speedtest-fs: filesystem performance estimate"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2020
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"


def get_spd(nbyte, nfiles, nsec):
    if not nsec:
        return "0.000 MB   0 files   0.000 sec   0.000 MB/s   0.000 f/s"

    mb = nbyte / (1024 * 1024.0)
    spd = mb / nsec
    nspd = nfiles / nsec

    return f"{mb:.3f} MB   {nfiles} files   {nsec:.3f} sec   {spd:.3f} MB/s   {nspd:.3f} f/s"


class Inf(object):
    def __init__(self, t0):
        self.msgs = []
        self.errors = []
        self.reports = []
        self.mtx_msgs = threading.Lock()
        self.mtx_reports = threading.Lock()

        self.n_byte = 0
        self.n_file = 0
        self.n_sec = 0
        self.n_done = 0
        self.t0 = t0

        thr = threading.Thread(target=self.print_msgs)
        thr.daemon = True
        thr.start()

    def msg(self, fn, n_read):
        with self.mtx_msgs:
            self.msgs.append(f"{fn} {n_read}")

    def err(self, fn):
        with self.mtx_reports:
            self.errors.append(f"{fn}\n{traceback.format_exc()}")

    def print_msgs(self):
        while True:
            time.sleep(0.02)
            with self.mtx_msgs:
                msgs = self.msgs
                self.msgs = []

            if not msgs:
                continue

            msgs = msgs[-64:]
            spd = get_spd(self.n_byte, len(self.reports), self.n_sec)
            msgs = [f"{spd}   {x}" for x in msgs]
            print("\n".join(msgs))

    def report(self, fn, n_byte, n_sec):
        with self.mtx_reports:
            self.reports.append([n_byte, n_sec, fn])
            self.n_byte += n_byte
            self.n_sec += n_sec

    def done(self):
        with self.mtx_reports:
            self.n_done += 1


def get_files(dir_path):
    for fn in os.listdir(dir_path):
        fn = os.path.join(dir_path, fn)
        st = os.stat(fn).st_mode

        if stat.S_ISDIR(st):
            yield from get_files(fn)

        if stat.S_ISREG(st):
            yield fn


def worker(q, inf, read_sz):
    while True:
        fn = q.get()
        if not fn:
            break

        n_read = 0
        try:
            t0 = time.time()
            with open(fn, "rb") as f:
                while True:
                    buf = f.read(read_sz)
                    if not buf:
                        break

                    n_read += len(buf)
                    inf.msg(fn, n_read)

            inf.report(fn, n_read, time.time() - t0)
        except:
            inf.err(fn)

    inf.done()


def sighandler(signo, frame):
    os._exit(0)


def main():
    signal.signal(signal.SIGINT, sighandler)

    root = "."
    if len(sys.argv) > 1:
        root = sys.argv[1]

    t0 = time.time()
    q = Queue(256)
    inf = Inf(t0)

    num_threads = 8
    read_sz = 32 * 1024
    targs = (q, inf, read_sz)
    for _ in range(num_threads):
        thr = threading.Thread(target=worker, args=targs)
        thr.daemon = True
        thr.start()

    for fn in get_files(root):
        q.put(fn)

    for _ in range(num_threads):
        q.put(None)

    while inf.n_done < num_threads:
        time.sleep(0.1)

    t2 = time.time()
    print("\n")

    log = inf.reports
    log.sort()
    for nbyte, nsec, fn in log[-64:]:
        spd = get_spd(nbyte, len(log), nsec)
        print(f"{spd}   {fn}")

    print()
    print("\n".join(inf.errors))

    print(get_spd(inf.n_byte, len(log), t2 - t0))


if __name__ == "__main__":
    main()

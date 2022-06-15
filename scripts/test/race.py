#!/usr/bin/env python3

import os
import sys
import time
import json
import threading
import http.client


class Conn(object):
    def __init__(self, ip, port):
        self.s = http.client.HTTPConnection(ip, port, timeout=260)
        self.st = []

    def get(self, vpath):
        self.st = [time.time()]

        self.s.request("GET", vpath)
        self.st.append(time.time())

        ret = self.s.getresponse()
        self.st.append(time.time())

        if ret.status < 200 or ret.status >= 400:
            raise Exception(ret.status)

        ret = ret.read()
        self.st.append(time.time())

        return ret

    def get_json(self, vpath):
        ret = self.get(vpath)
        return json.loads(ret)


class CState(threading.Thread):
    def __init__(self, cs):
        threading.Thread.__init__(self)
        self.daemon = True
        self.cs = cs
        self.start()

    def run(self):
        colors = [5, 1, 3, 2, 7]
        remotes = []
        remotes_ok = False
        while True:
            time.sleep(0.001)
            if not remotes_ok:
                remotes = []
                remotes_ok = True
                for conn in self.cs:
                    try:
                        remotes.append(conn.s.sock.getsockname()[1])
                    except:
                        remotes.append("?")
                        remotes_ok = False

            ta = []
            for conn, remote in zip(self.cs, remotes):
                stage = len(conn.st)
                ta.append(f"\033[3{colors[stage]}m{remote}")

            t = " ".join(ta)
            print(f"{t}\033[0m\n\033[A", end="")


def allget(cs, urls):
    thrs = []
    for c, url in zip(cs, urls):
        t = threading.Thread(target=c.get, args=(url,))
        t.start()
        thrs.append(t)

    for t in thrs:
        t.join()


def main():
    os.system("")

    ip, port = sys.argv[1].split(":")
    port = int(port)

    cs = []
    for _ in range(64):
        cs.append(Conn(ip, 3923))

    CState(cs)

    urlbase = "/doujin/c95"
    j = cs[0].get_json(f"{urlbase}?ls")
    urls = []
    for d in j["dirs"]:
        urls.append(f"{urlbase}/{d['href']}?th=w")

    for n in range(100):
        print(n)
        allget(cs, urls)


if __name__ == "__main__":
    main()

import os
import sys
import time
import shlex
import shutil
import signal
import tempfile
import requests
import threading
import subprocess as sp


CPP = []


class Cpp(object):
    def __init__(self, args):
        args = [sys.executable, "-m", "copyparty"] + args
        print(" ".join([shlex.quote(x) for x in args]))

        self.ls_pre = set(list(os.listdir()))
        self.p = sp.Popen(args)
        # , stdout=sp.PIPE, stderr=sp.PIPE)

        self.t = threading.Thread(target=self._run)
        self.t.daemon = True
        self.t.start()

    def _run(self):
        self.so, self.se = self.p.communicate()

    def stop(self, wait):
        if wait:
            os.kill(self.p.pid, signal.SIGINT)
            self.t.join(timeout=2)
        else:
            self.p.kill()  # macos py3.8

    def clean(self):
        t = os.listdir()
        for f in t:
            if f not in self.ls_pre and f.startswith("up."):
                os.unlink(f)

    def await_idle(self, ub, timeout):
        req = ["scanning</td><td>False", "hash-q</td><td>0", "tag-q</td><td>0"]
        lim = int(timeout * 10)
        u = ub + "?h"
        for n in range(lim):
            try:
                time.sleep(0.1)
                r = requests.get(u, timeout=0.1)
                for x in req:
                    if x not in r.text:
                        print("ST: {}/{} miss {}".format(n, lim, x))
                        raise Exception()
                print("ST: idle")
                return
            except:
                pass


def tc1(vflags):
    ub = "http://127.0.0.1:4321/"
    td = os.path.join("srv", "smoketest")
    try:
        shutil.rmtree(td)
    except:
        if os.path.exists(td):
            raise

    for _ in range(10):
        try:
            os.mkdir(td)
            if os.path.exists(td):
                break
        except:
            time.sleep(0.1)  # win10

    assert os.path.exists(td)

    vidp = os.path.join(tempfile.gettempdir(), "smoketest.h264")
    if not os.path.exists(vidp):
        cmd = "ffmpeg -f lavfi -i testsrc=48x32:3 -t 1 -c:v libx264 -tune animation -preset veryslow -crf 69"
        sp.check_call(cmd.split(" ") + [vidp])

    with open(vidp, "rb") as f:
        ovid = f.read()

    args = [
        "-p4321",
        "-e2dsa",
        "-e2tsr",
        "--no-mutagen",
        "--th-ff-jpg",
        "--hist",
        os.path.join(td, "dbm"),
    ]
    pdirs = []
    hpaths = {}

    for d1 in ["r", "w", "a"]:
        pdirs.append("{}/{}".format(td, d1))
        pdirs.append("{}/{}/j".format(td, d1))
        for d2 in ["r", "w", "a", "c"]:
            d = os.path.join(td, d1, "j", d2)
            pdirs.append(d)
            os.makedirs(d)

    pdirs = [x.replace("\\", "/") for x in pdirs]
    udirs = [x.split("/", 2)[2] for x in pdirs]
    perms = [x.rstrip("cj/")[-1] for x in pdirs]
    perms = ["rw" if x == "a" else x for x in perms]
    for pd, ud, p in zip(pdirs, udirs, perms):
        if ud[-1] == "j" or ud[-1] == "c":
            continue

        hp = None
        if pd.endswith("st/a"):
            hp = hpaths[ud] = os.path.join(td, "db1")
        elif pd[:-1].endswith("a/j/"):
            hpaths[ud] = os.path.join(td, "dbm")
            hp = None
        else:
            hp = "-"
            hpaths[ud] = os.path.join(pd, ".hist")

        arg = "{}:{}:{}".format(pd, ud, p)
        if hp:
            arg += ":c,hist=" + hp

        args += ["-v", arg + vflags]

    # return
    cpp = Cpp(args)
    CPP.append(cpp)
    cpp.await_idle(ub, 3)

    for d, p in zip(udirs, perms):
        vid = ovid + "\n{}".format(d).encode("utf-8")
        r = requests.post(
            ub + d,
            data={"act": "bput"},
            files={"f": (d.replace("/", "") + ".h264", vid)},
        )
        c = r.status_code
        if c == 201 and p not in ["w", "rw"]:
            raise Exception("post {} with perm {} at {}".format(c, p, d))
        elif c == 403 and p not in ["r"]:
            raise Exception("post {} with perm {} at {}".format(c, p, d))
        elif c not in [201, 403]:
            raise Exception("post {} with perm {} at {}".format(c, p, d))

    cpp.clean()

    # GET permission
    for d, p in zip(udirs, perms):
        u = "{}{}/{}.h264".format(ub, d, d.replace("/", ""))
        r = requests.get(u)
        ok = bool(r)
        if ok != (p in ["rw"]):
            raise Exception("get {} with perm {} at {}".format(ok, p, u))

    # stat filesystem
    for d, p in zip(pdirs, perms):
        u = "{}/{}.h264".format(d, d.split("test/")[-1].replace("/", ""))
        ok = os.path.exists(u)
        if ok != (p in ["rw", "w"]):
            raise Exception("stat {} with perm {} at {}".format(ok, p, u))

    # GET thumbnail, vreify contents
    for d, p in zip(udirs, perms):
        u = "{}{}/{}.h264?th=j".format(ub, d, d.replace("/", ""))
        r = requests.get(u)
        ok = bool(r and r.content[:3] == b"\xff\xd8\xff")
        if ok != (p in ["rw"]):
            raise Exception("thumb {} with perm {} at {}".format(ok, p, u))

    # check tags
    cpp.await_idle(ub, 5)
    for d, p in zip(udirs, perms):
        u = "{}{}?ls".format(ub, d)
        r = requests.get(u)
        j = r.json() if r else False
        tag = None
        if j:
            for f in j["files"]:
                tag = tag or f["tags"].get("res")

        r_ok = bool(j)
        w_ok = bool(r_ok and j.get("files"))

        if not r_ok or w_ok != (p in ["rw"]):
            raise Exception("ls {} with perm {} at {}".format(ok, p, u))

        if (tag and p != "rw") or (not tag and p == "rw"):
            raise Exception("tag {} with perm {} at {}".format(tag, p, u))

        if tag is not None and tag != "48x32":
            raise Exception("tag [{}] at {}".format(tag, u))

    cpp.stop(True)


def run(tc, *a):
    try:
        tc(*a)
    finally:
        try:
            CPP[0].stop(False)
        except:
            pass


def main():
    run(tc1, "")
    run(tc1, ":c,fk")


if __name__ == "__main__":
    main()

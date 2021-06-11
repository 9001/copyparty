import os
import sys
import time
import signal
import shutil
import tempfile
import requests
import threading
import subprocess as sp


class Cpp(object):
    def __init__(self, args):
        self.ls_pre = set(list(os.listdir()))
        self.p = sp.Popen([sys.executable, "-m", "copyparty"] + args)
        # , stdout=sp.PIPE, stderr=sp.PIPE)

        self.t = threading.Thread(target=self._run)
        self.t.daemon = True
        self.t.start()

    def _run(self):
        self.so, self.se = self.p.communicate()

    def stop(self, wait):
        # self.p.kill()
        os.kill(self.p.pid, signal.SIGINT)
        if wait:
            self.t.join()

    def clean(self):
        t = os.listdir()
        for f in t:
            if f not in self.ls_pre and f.startswith("up."):
                os.unlink(f)


def tc1():
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
        "-p",
        "4321",
        "-e2dsa",
        "-e2tsr",
        "--th-ff-jpg",
        "--hist",
        os.path.join(td, "dbm"),
    ]
    pdirs = []
    hpaths = {}

    for d1 in ["r", "w", "a"]:
        pdirs.append("{}/{}".format(td, d1))
        pdirs.append("{}/{}/j".format(td, d1))
        for d2 in ["r", "w", "a"]:
            d = os.path.join(td, d1, "j", d2)
            pdirs.append(d)
            os.makedirs(d)

    pdirs = [x.replace("\\", "/") for x in pdirs]
    udirs = [x.split("/", 2)[2] for x in pdirs]
    perms = [x.rstrip("j/")[-1] for x in pdirs]
    for pd, ud, p in zip(pdirs, udirs, perms):
        if ud[-1] == "j":
            continue

        hp = None
        if pd.endswith("st/a"):
            hp = os.path.join(td, "db1")
        elif pd[:-1].endswith("a/j/"):
            hp = os.path.join(td, "dbm")
        else:
            hp = "-"

        hpaths[ud] = os.path.join(pd, ".hist") if hp == "-" else hp
        args += ["-v", "{}:{}:{}:chist={}".format(pd, ud, p, hp)]

    # print(repr(args))
    # return
    cpp = Cpp(args)

    up = False
    for n in range(30):
        try:
            time.sleep(0.1)
            requests.get(ub + "?h", timeout=0.1)
            up = True
            break
        except:
            pass

    assert up

    for d in udirs:
        vid = ovid + "\n{}".format(d).encode("utf-8")
        try:
            requests.post(ub + d, data={"act": "bput"}, files={"f": ("a.h264", vid)})
        except:
            pass

    cpp.clean()

    # GET permission
    for d, p in zip(udirs, perms):
        u = "{}{}/a.h264".format(ub, d)
        r = requests.get(u)
        ok = bool(r)
        if ok != (p in ["a"]):
            raise Exception("get {} with perm {} at {}".format(ok, p, u))

    # stat filesystem
    for d, p in zip(pdirs, perms):
        u = "{}/a.h264".format(d)
        ok = os.path.exists(u)
        if ok != (p in ["a", "w"]):
            raise Exception("stat {} with perm {} at {}".format(ok, p, u))

    # GET thumbnail, vreify contents
    for d, p in zip(udirs, perms):
        u = "{}{}/a.h264?th=j".format(ub, d)
        r = requests.get(u)
        ok = bool(r and r.content[:3] == b"\xff\xd8\xff")
        if ok != (p in ["a"]):
            raise Exception("thumb {} with perm {} at {}".format(ok, p, u))

    # check tags
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

        if not r_ok or w_ok != (p in ["a"]):
            raise Exception("ls {} with perm {} at {}".format(ok, p, u))

        if (tag and p != "a") or (not tag and p == "a"):
            raise Exception("tag {} with perm {} at {}".format(ok, p, u))

        if tag is not None and tag != "48x32":
            raise Exception("tag [{}] at {}".format(tag, u))

    cpp.stop(True)


def main():
    tc1()


if __name__ == "__main__":
    main()

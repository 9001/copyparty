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


def main():
    ub = "http://127.0.0.1:4321/"
    td = os.path.join("srv", "smoketest")
    try:
        shutil.rmtree(td)
    except:
        pass

    os.mkdir(td)

    vidp = os.path.join(tempfile.gettempdir(), "smoketest.h264")
    if not os.path.exists(vidp):
        cmd = "ffmpeg -f lavfi -i testsrc=48x32:3 -t 1 -c:v libx264 -tune animation -preset veryslow -crf 69"
        sp.check_call(cmd.split(" ") + [vidp])

    with open(vidp, "rb") as f:
        ovid = f.read()

    args = ["-p", "4321", "-e2dsa", "-e2tsr"]
    pdirs = []

    for d1 in ["r", "w", "a"]:
        pdirs.append("{}/{}".format(td, d1))
        pdirs.append("{}/{}/j".format(td, d1))
        for d2 in ["r", "w", "a"]:
            d = os.path.join(td, d1, "j", d2)
            pdirs.append(d.replace("\\", "/"))
            os.makedirs(d)

    udirs = [x.split("/", 2)[2] for x in pdirs]
    perms = [x.rstrip("j/")[-1] for x in pdirs]
    for pd, ud, p in zip(pdirs, udirs, perms):
        # args += ["-v", "{}:{}:{}".format(d.split("/", 1)[1], d, d[-1])]
        args += ["-v", "{}:{}:{}".format(pd, ud, p)]

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
        requests.post(ub + d, data={"act": "bput"}, files={"f": ("a.h264", vid)})

    for d, p in zip(udirs, perms):
        u = "{}{}/a.h264".format(ub, d)
        r = requests.get(u)
        ok = bool(r)
        if ok != (p in ["a"]):
            raise Exception("get {} with perm {} at {}".format(ok, p, u))

    for d, p in zip(pdirs, perms):
        u = "{}/a.h264".format(d)
        ok = os.path.exists(u)
        if ok != (p in ["a", "w"]):
            raise Exception("stat {} with perm {} at {}".format(ok, p, u))

    for d, p in zip(udirs, perms):
        u = "{}{}/a.h264?th=j".format(ub, d)
        r = requests.get(u)
        ok = False
        if r:
            r.raw.decode_content = True
            buf = r.raw.read(256)
            if buf[:3] == b"\xff\xd8\xff":
                ok = True
        if ok != (p in ["a"]):
            raise Exception("thumb {} with perm {} at {}".format(ok, p, u))

    cpp.stop(True)


if __name__ == "__main__":
    main()

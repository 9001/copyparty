import os
import time
import jinja2
import tempfile
import subprocess as sp

from copyparty.util import Unrecv


J2_ENV = jinja2.Environment(loader=jinja2.BaseLoader)
J2_FILES = J2_ENV.from_string("{{ files|join('\n') }}")


def runcmd(*argv):
    p = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    return [p.returncode, stdout, stderr]


def chkcmd(*argv):
    ok, sout, serr = runcmd(*argv)
    if ok != 0:
        raise Exception(serr)

    return sout, serr


def get_ramdisk():
    for vol in ["/dev/shm", "/Volumes/cptd"]:  # nosec (singleton test)
        if os.path.exists(vol):
            return vol

    if os.path.exists("/Volumes"):
        devname, _ = chkcmd("hdiutil", "attach", "-nomount", "ram://32768")
        devname = devname.strip()
        print("devname: [{}]".format(devname))
        for _ in range(10):
            try:
                _, _ = chkcmd("diskutil", "eraseVolume", "HFS+", "cptd", devname)
                return "/Volumes/cptd"
            except Exception as ex:
                print(repr(ex))
                time.sleep(0.25)

        raise Exception("ramdisk creation failed")

    ret = os.path.join(tempfile.gettempdir(), "copyparty-test")
    try:
        os.mkdir(ret)
    finally:
        return ret


class NullBroker(object):
    def put(*args):
        pass


class VSock(object):
    def __init__(self, buf):
        self._query = buf
        self._reply = b""
        self.sendall = self.send

    def recv(self, sz):
        ret = self._query[:sz]
        self._query = self._query[sz:]
        return ret

    def send(self, buf):
        self._reply += buf
        return len(buf)


class VHttpSrv(object):
    def __init__(self):
        self.broker = NullBroker()

        aliases = ["splash", "browser", "browser2", "msg", "md", "mde"]
        self.j2 = {x: J2_FILES for x in aliases}


class VHttpConn(object):
    def __init__(self, args, auth, log, buf):
        self.s = VSock(buf)
        self.sr = Unrecv(self.s)
        self.addr = ("127.0.0.1", "42069")
        self.args = args
        self.auth = auth
        self.log_func = log
        self.log_src = "a"
        self.hsrv = VHttpSrv()
        self.nbyte = 0
        self.workload = 0
        self.t0 = time.time()
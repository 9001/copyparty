import os
import sys
import time
import shutil
import jinja2
import threading
import tempfile
import platform
import subprocess as sp
from argparse import Namespace


WINDOWS = platform.system() == "Windows"
ANYWIN = WINDOWS or sys.platform in ["msys"]
MACOS = platform.system() == "Darwin"

J2_ENV = jinja2.Environment(loader=jinja2.BaseLoader)
J2_FILES = J2_ENV.from_string("{{ files|join('\n') }}")


def nah(*a, **ka):
    return False


if MACOS:
    import posixpath

    posixpath.islink = nah
    os.path.islink = nah
    # 25% faster; until any tests do symlink stuff


from copyparty.__init__ import E
from copyparty.__main__ import init_E
from copyparty.util import Unrecv, FHC

init_E(E)


def runcmd(argv):
    p = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    return [p.returncode, stdout, stderr]


def chkcmd(argv):
    ok, sout, serr = runcmd(argv)
    if ok != 0:
        raise Exception(serr)

    return sout, serr


def get_ramdisk():
    def subdir(top):
        ret = os.path.join(top, "cptd-{}".format(os.getpid()))
        shutil.rmtree(ret, True)
        os.mkdir(ret)
        return ret

    for vol in ["/dev/shm", "/Volumes/cptd"]:  # nosec (singleton test)
        if os.path.exists(vol):
            return subdir(vol)

    if os.path.exists("/Volumes"):
        # hdiutil eject /Volumes/cptd/
        devname, _ = chkcmd("hdiutil attach -nomount ram://131072".split())
        devname = devname.strip()
        print("devname: [{}]".format(devname))
        for _ in range(10):
            try:
                _, _ = chkcmd(["diskutil", "eraseVolume", "HFS+", "cptd", devname])
                with open("/Volumes/cptd/.metadata_never_index", "w") as f:
                    f.write("orz")

                try:
                    shutil.rmtree("/Volumes/cptd/.fseventsd")
                except:
                    pass

                return subdir("/Volumes/cptd")
            except Exception as ex:
                print(repr(ex))
                time.sleep(0.25)

        raise Exception("ramdisk creation failed")

    ret = os.path.join(tempfile.gettempdir(), "copyparty-test")
    try:
        os.mkdir(ret)
    finally:
        return subdir(ret)


class Cfg(Namespace):
    def __init__(self, a=None, v=None, c=None):
        ka = {}

        ex = "e2d e2ds e2dsa e2t e2ts e2tsr e2v e2vu e2vp xdev xvol ed emp force_js ihead magic no_acode no_athumb no_del no_logues no_mv no_readme no_robots no_scandir no_thumb no_vthumb no_zip nid nih nw"
        ka.update(**{k: False for k in ex.split()})

        ex = "no_rescan no_sendfile no_voldump plain_ip"
        ka.update(**{k: True for k in ex.split()})

        ex = "css_browser hist js_browser no_hash no_idx no_forget"
        ka.update(**{k: None for k in ex.split()})

        ex = "re_maxage rproxy rsp_slp s_wr_slp theme themes turbo df"
        ka.update(**{k: 0 for k in ex.split()})

        ex = "doctitle favico html_head mth textfiles log_fk"
        ka.update(**{k: "" for k in ex.split()})

        super(Cfg, self).__init__(
            a=a or [],
            v=v or [],
            c=c,
            E=E,
            s_wr_sz=512 * 1024,
            unpost=600,
            u2sort="s",
            mtp=[],
            mte="a",
            lang="eng",
            logout=573,
            **ka
        )


class NullBroker(object):
    def say(*args):
        pass

    def ask(*args):
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

    def getsockname(self):
        return ("a", 1)


class VHttpSrv(object):
    def __init__(self):
        self.broker = NullBroker()
        self.prism = None
        self.bans = {}

        aliases = ["splash", "browser", "browser2", "msg", "md", "mde"]
        self.j2 = {x: J2_FILES for x in aliases}

    def cachebuster(self):
        return "a"


class VHttpConn(object):
    def __init__(self, args, asrv, log, buf):
        self.s = VSock(buf)
        self.sr = Unrecv(self.s, None)
        self.addr = ("127.0.0.1", "42069")
        self.args = args
        self.asrv = asrv
        self.nid = None
        self.log_func = log
        self.log_src = "a"
        self.lf_url = None
        self.hsrv = VHttpSrv()
        self.u2fh = FHC()
        self.mutex = threading.Lock()
        self.nreq = 0
        self.nbyte = 0
        self.ico = None
        self.thumbcli = None
        self.t0 = time.time()

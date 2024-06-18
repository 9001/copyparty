#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import platform
import re
import shutil
import subprocess as sp
import sys
import tempfile
import threading
import time
from argparse import Namespace

import jinja2

WINDOWS = platform.system() == "Windows"
ANYWIN = WINDOWS or sys.platform in ["msys"]
MACOS = platform.system() == "Darwin"

J2_ENV = jinja2.Environment(loader=jinja2.BaseLoader)  # type: ignore
J2_FILES = J2_ENV.from_string("{{ files|join('\n') }}\nJ2EOT")


def nah(*a, **ka):
    return False


def eprint(*a, **ka):
    ka["file"] = sys.stderr
    print(*a, **ka)
    sys.stderr.flush()


if MACOS:
    import posixpath

    posixpath.islink = nah
    os.path.islink = nah
    # 25% faster; until any tests do symlink stuff


from copyparty.__init__ import E
from copyparty.__main__ import init_E
from copyparty.ico import Ico
from copyparty.u2idx import U2idx
from copyparty.util import FHC, CachedDict, Garda, Unrecv

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
                with open("/Volumes/cptd/.metadata_never_index", "wb") as f:
                    f.write(b"orz")

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
    if not os.path.isdir(ret):
        os.mkdir(ret)

    return subdir(ret)


class Cfg(Namespace):
    def __init__(self, a=None, v=None, c=None, **ka0):
        ka = {}

        ex = "daw dav_auth dav_inf dav_mac dav_rt e2d e2ds e2dsa e2t e2ts e2tsr e2v e2vu e2vp early_ban ed emp exp force_js getmod grid gsel hardlink ih ihead magic never_symlink nid nih no_acode no_athumb no_dav no_dedup no_del no_dupe no_lifetime no_logues no_mv no_pipe no_poll no_readme no_robots no_sb_md no_sb_lg no_scandir no_tarcmp no_thumb no_vthumb no_zip nrand nw og og_no_head og_s_title q rand smb srch_dbg stats uqe vague_403 vc ver xdev xlink xvol"
        ka.update(**{k: False for k in ex.split()})

        ex = "dotpart dotsrch no_dhash no_fastboot no_rescan no_sendfile no_snap no_voldump re_dhash plain_ip"
        ka.update(**{k: True for k in ex.split()})

        ex = "ah_cli ah_gen css_browser hist js_browser mime mimes no_forget no_hash no_idx nonsus_urls og_tpl og_ua"
        ka.update(**{k: None for k in ex.split()})

        ex = "hash_mt srch_time u2abort u2j"
        ka.update(**{k: 1 for k in ex.split()})

        ex = "au_vol mtab_age reg_cap s_thead s_tbody th_convt"
        ka.update(**{k: 9 for k in ex.split()})

        ex = "db_act k304 loris re_maxage rproxy rsp_jtr rsp_slp s_wr_slp snap_wri theme themes turbo"
        ka.update(**{k: 0 for k in ex.split()})

        ex = "ah_alg bname doctitle df exit favico idp_h_usr html_head lg_sbf log_fk md_sbf name og_desc og_site og_th og_title og_title_a og_title_v og_title_i tcolor textfiles unlist vname R RS SR"
        ka.update(**{k: "" for k in ex.split()})

        ex = "grp on403 on404 xad xar xau xban xbd xbr xbu xiu xm"
        ka.update(**{k: [] for k in ex.split()})

        ex = "exp_lg exp_md th_coversd"
        ka.update(**{k: {} for k in ex.split()})

        ka.update(ka0)

        super(Cfg, self).__init__(
            a=a or [],
            v=v or [],
            c=c,
            E=E,
            dbd="wal",
            dk_salt="b" * 16,
            fk_salt="a" * 16,
            idp_gsep=re.compile("[|:;+,]"),
            iobuf=256 * 1024,
            lang="eng",
            log_badpwd=1,
            logout=573,
            mte={"a": True},
            mth={},
            mtp=[],
            mv_retry="0/0",
            rm_retry="0/0",
            s_rd_sz=256 * 1024,
            s_wr_sz=256 * 1024,
            sort="href",
            srch_hits=99999,
            th_covers=["folder.png"],
            th_crop="y",
            th_size="320x256",
            th_x3="n",
            u2sort="s",
            u2ts="c",
            unpost=600,
            warksalt="hunter2",
            **ka
        )


class NullBroker(object):
    def say(self, *args):
        pass

    def ask(self, *args):
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

    def settimeout(self, a):
        pass


class VHttpSrv(object):
    def __init__(self, args, asrv, log):
        self.args = args
        self.asrv = asrv
        self.log = log

        self.broker = NullBroker()
        self.prism = None
        self.bans = {}
        self.nreq = 0
        self.nsus = 0

        aliases = ["splash", "browser", "browser2", "msg", "md", "mde"]
        self.j2 = {x: J2_FILES for x in aliases}

        self.gpwd = Garda("")
        self.g404 = Garda("")
        self.g403 = Garda("")
        self.gurl = Garda("")

        self.u2idx = None
        self.ptn_cc = re.compile(r"[\x00-\x1f]")

    def cachebuster(self):
        return "a"

    def get_u2idx(self):
        self.u2idx = self.u2idx or U2idx(self)
        return self.u2idx


class VHttpConn(object):
    def __init__(self, args, asrv, log, buf):
        self.t0 = time.time()
        self.s = VSock(buf)
        self.sr = Unrecv(self.s, None)  # type: ignore
        self.aclose = {}
        self.addr = ("127.0.0.1", "42069")
        self.args = args
        self.asrv = asrv
        self.bans = {}
        self.freshen_pwd = 0.0
        self.hsrv = VHttpSrv(args, asrv, log)
        self.ico = Ico(args)
        self.ipa_nm = None
        self.lf_url = None
        self.log_func = log
        self.log_src = "a"
        self.mutex = threading.Lock()
        self.pipes = CachedDict(1)
        self.u2mutex = threading.Lock()
        self.nbyte = 0
        self.nid = None
        self.nreq = -1
        self.thumbcli = None
        self.u2fh = FHC()

        self.get_u2idx = self.hsrv.get_u2idx


if WINDOWS:
    os.system("rem")

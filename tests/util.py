#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import random
import re
import shutil
import socket
import subprocess as sp
import sys
import tempfile
import threading
import time
import unittest
from argparse import Namespace

import jinja2

from copyparty.__init__ import MACOS, WINDOWS, E

J2_ENV = jinja2.Environment(loader=jinja2.BaseLoader)  # type: ignore
J2_FILES = J2_ENV.from_string("{{ files|join('\n') }}\nJ2EOT")


def nah(*a, **ka):
    return False


def eprint(*a, **ka):
    ka["file"] = sys.stderr
    print(*a, **ka)
    sys.stderr.flush()


from copyparty.__main__ import init_E
from copyparty.broker_thr import BrokerThr
from copyparty.ico import Ico
from copyparty.u2idx import U2idx
from copyparty.up2k import Up2k
from copyparty.util import FHC, CachedDict, Garda, Unrecv

init_E(E)


def randbytes(n):
    return random.getrandbits(n * 8).to_bytes(n, "little")


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
        for d in os.listdir(top):
            if not d.startswith("cptd-"):
                continue
            p = os.path.join(top, d)
            st = os.stat(p)
            if time.time() - st.st_mtime > 300:
                shutil.rmtree(p)
        ret = os.path.join(top, "cptd-{}".format(os.getpid()))
        shutil.rmtree(ret, True)
        os.mkdir(ret)
        return ret

    for vol in ["/dev/shm", "/Volumes/cptd"]:  # nosec (singleton test)
        if os.path.exists(vol):
            return subdir(vol)

    if os.path.exists("/Volumes"):
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                sck.bind(("127.0.0.1", 2775))
                break
            except:
                print("waiting for 2775")
                time.sleep(0.5)

        v = "/Volumes/cptd"
        if os.path.exists(v):
            return subdir(v)

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

                sck.close()
                return subdir("/Volumes/cptd")
            except Exception as ex:
                print(repr(ex))
                time.sleep(0.25)

        raise Exception("ramdisk creation failed")

    ret = os.path.join(tempfile.gettempdir(), "copyparty-test")
    if not os.path.isdir(ret):
        os.mkdir(ret)

    return subdir(ret)


def pfind2ls(xml):
    return [x.split("<", 1)[0] for x in xml.split("<D:href>")[1:]]


class TC(unittest.TestCase):
    def __init__(self, *a, **ka):
        super(TC, self).__init__(*a, **ka)

    def assertStart(self, member, container, msg=None):
        if not container.startswith(member):
            standardMsg = "%s not found in %s" % (member, container)
            self.fail(self._formatMessage(msg, standardMsg))


class Cfg(Namespace):
    def __init__(self, a=None, v=None, c=None, **ka0):
        ka = {}

        ex = "allow_flac allow_wav chpw cookie_lax daw dav_auth dav_mac dav_rt e2d e2ds e2dsa e2t e2ts e2tsr e2v e2vu e2vp early_ban ed emp exp force_js getmod grid gsel hardlink hardlink_only ih ihead localtime log_badxml magic md_no_br nid nih no_acode no_athumb no_bauth no_clone no_cp no_dav no_db_ip no_del no_dirsz no_dupe no_fnugg no_lifetime no_logues no_mv no_pipe no_poll no_readme no_robots no_sb_md no_sb_lg no_scandir no_tail no_tarcmp no_thumb no_vthumb no_u2abrt no_zip nrand nsort nw og og_no_head og_s_title ohead q rand re_dirsz reflink rmagic rss smb srch_dbg srch_excl stats uqe usernames vague_403 vc ver wo_up_readme write_uplog xdev xlink xvol zipmaxu zs"
        ka.update(**{k: False for k in ex.split()})

        ex = "dav_inf dedup dotpart dotsrch hook_v no_dhash no_fastboot no_fpool no_htp no_rescan no_sendfile no_ses no_snap no_up_list no_voldump re_dhash see_dots plain_ip"
        ka.update(**{k: True for k in ex.split()})

        ex = "ah_cli ah_gen css_browser dbpath hist ipu js_browser js_other mime mimes no_forget no_hash no_idx nonsus_urls og_tpl og_ua ua_nodoc ua_nozip"
        ka.update(**{k: None for k in ex.split()})

        ex = "gid uid"
        ka.update(**{k: -1 for k in ex.split()})

        ex = "hash_mt hsortn qdel safe_dedup srch_time tail_fd tail_rate th_spec_p u2abort u2j u2sz unp_who"
        ka.update(**{k: 1 for k in ex.split()})

        ex = "ac_convt au_vol dl_list du_iwho mtab_age reg_cap s_thead s_tbody tail_tmax tail_who th_convt ups_who ver_iwho zip_who"
        ka.update(**{k: 9 for k in ex.split()})

        ex = "ctl_re db_act forget_ip idp_cookie idp_store k304 loris no304 nosubtle qr_pin qr_wait re_maxage rproxy rsp_jtr rsp_slp s_wr_slp snap_wri theme themes turbo u2ow zipmaxn zipmaxs"
        ka.update(**{k: 0 for k in ex.split()})

        ex = "ah_alg bname chdir chmod_f chpw_db doctitle df exit favico ipa html_head idp_login idp_logout lg_sba lg_sbf log_fk md_sba md_sbf name og_desc og_site og_th og_title og_title_a og_title_v og_title_i shr tcolor textfiles txt_eol unlist vname xff_src zipmaxt R RS SR"
        ka.update(**{k: "" for k in ex.split()})

        ex = "ban_403 ban_404 ban_422 ban_pw ban_pwc ban_url spinner"
        ka.update(**{k: "no" for k in ex.split()})

        ex = "ext_th grp idp_h_usr idp_hm_usr ipr on403 on404 qr_file xac xad xar xau xban xbc xbd xbr xbu xiu xm"
        ka.update(**{k: [] for k in ex.split()})

        ex = "exp_lg exp_md"
        ka.update(**{k: {} for k in ex.split()})

        ka.update(ka0)

        super(Cfg, self).__init__(
            a=a or [],
            v=v or [],
            c=c,
            E=E,
            auth_ord="idp,ipu",
            bup_ck="sha512",
            chmod_d="755",
            cookie_cmax=8192,
            cookie_nmax=50,
            dbd="wal",
            du_who="all",
            dk_salt="b" * 16,
            fk_salt="a" * 16,
            grp_all="acct",
            idp_gsep=re.compile("[|:;+,]"),
            iobuf=256 * 1024,
            lang="eng",
            log_badpwd=1,
            logout=573,
            md_hist="s",
            mte={"a": True},
            mth={},
            mtp=[],
            put_ck="sha512",
            put_name="put-{now.6f}-{cip}.bin",
            mv_retry="0/0",
            rm_retry="0/0",
            s_rd_sz=256 * 1024,
            s_wr_sz=256 * 1024,
            shr_who="auth",
            sort="href",
            srch_hits=99999,
            SRS="/",
            th_covers=["folder.png"],
            th_coversd=["folder.png"],
            th_covers_set=set(["folder.png"]),
            th_coversd_set=set(["folder.png"]),
            th_crop="y",
            th_size="320x256",
            th_x3="n",
            u2sort="s",
            u2ts="c",
            unpost=600,
            ver_who="all",
            warksalt="hunter2",
            **ka
        )


class NullBroker(object):
    def __init__(self, args, asrv):
        self.args = args
        self.asrv = asrv

    def say(self, *args):
        pass

    def ask(self, *args):
        pass


class VSock(object):
    def __init__(self, buf):
        self._query = buf
        self._reply = b""
        self.family = socket.AF_INET
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


class VHub(object):
    def __init__(self, args, asrv, log):
        self.args = args
        self.asrv = asrv
        self.log = log
        self.is_dut = True
        self.up2k = Up2k(self)

    def reload(self, a, b):
        pass


class VBrokerThr(BrokerThr):
    def __init__(self, hub):
        self.hub = hub
        self.log = hub.log
        self.args = hub.args
        self.asrv = hub.asrv


class VHttpSrv(object):
    def __init__(self, args, asrv, log):
        self.args = args
        self.asrv = asrv
        self.log = log
        self.hub = None

        self.broker = NullBroker(args, asrv)
        self.prism = None
        self.ipr = None
        self.bans = {}
        self.tdls = self.dls = {}
        self.tdli = self.dli = {}
        self.nreq = 0
        self.nsus = 0

        aliases = ["splash", "shares", "browser", "browser2", "msg", "md", "mde"]
        self.j2 = {x: J2_FILES for x in aliases}

        self.gpwd = Garda("")
        self.g404 = Garda("")
        self.g403 = Garda("")
        self.gurl = Garda("")

        self.u2idx = None

    def cachebuster(self):
        return "a"

    def get_u2idx(self):
        self.u2idx = self.u2idx or U2idx(self)
        return self.u2idx

    def shutdown(self):
        if self.u2idx:
            self.u2idx.shutdown()


class VHttpSrvUp2k(VHttpSrv):
    def __init__(self, args, asrv, log):
        super(VHttpSrvUp2k, self).__init__(args, asrv, log)
        self.hub = VHub(args, asrv, log)
        self.broker = VBrokerThr(self.hub)

    def shutdown(self):
        self.hub.up2k.shutdown()
        if self.u2idx:
            self.u2idx.shutdown()


class VHttpConn(object):
    def __init__(self, args, asrv, log, buf, use_up2k=False):
        self.t0 = time.time()
        self.aclose = {}
        self.addr = ("127.0.0.1", "42069")
        self.args = args
        self.asrv = asrv
        self.bans = {}
        self.tdls = self.dls = {}
        self.tdli = self.dli = {}
        self.freshen_pwd = 0.0

        Ctor = VHttpSrvUp2k if use_up2k else VHttpSrv
        self.hsrv = Ctor(args, asrv, log)
        self.ico = Ico(args)
        self.ipr = None
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
        self.setbuf(buf)

    def setbuf(self, buf):
        self.s = VSock(buf)
        self.sr = Unrecv(self.s, None)  # type: ignore
        return self

    def shutdown(self):
        self.hsrv.shutdown()


if WINDOWS:
    os.system("rem")

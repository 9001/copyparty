# coding: utf-8
from __future__ import print_function, unicode_literals

import base64
import errno
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import signal
import stat
import subprocess as sp
import tempfile
import threading
import time
import traceback
from copy import deepcopy

from queue import Queue

from .__init__ import ANYWIN, PY2, TYPE_CHECKING, WINDOWS
from .authsrv import LEELOO_DALLAS, SSEELOG, VFS, AuthSrv
from .bos import bos
from .cfg import vf_bmap, vf_cmap, vf_vmap
from .fsutil import Fstab
from .mtag import MParser, MTag
from .util import (
    HAVE_SQLITE3,
    SYMTIME,
    Daemon,
    MTHash,
    Pebkac,
    ProgressPrinter,
    absreal,
    atomic_move,
    db_ex_chk,
    djoin,
    fsenc,
    gen_filekey,
    gen_filekey_dbg,
    hidedir,
    humansize,
    min_ex,
    quotep,
    rand_name,
    ren_open,
    rmdirs,
    rmdirs_up,
    runhook,
    runihook,
    s2hms,
    s3dec,
    s3enc,
    sanitize_fn,
    sfsenc,
    spack,
    statdir,
    unhumanize,
    vjoin,
    vsplit,
    w8b64dec,
    w8b64enc,
)

if HAVE_SQLITE3:
    import sqlite3

DB_VER = 5

if True:  # pylint: disable=using-constant-test
    from typing import Any, Optional, Pattern, Union

if TYPE_CHECKING:
    from .svchub import SvcHub

zsg = "avif,avifs,bmp,gif,heic,heics,heif,heifs,ico,j2p,j2k,jp2,jpeg,jpg,jpx,png,tga,tif,tiff,webp"
CV_EXTS = set(zsg.split(","))


class Dbw(object):
    def __init__(self, c: "sqlite3.Cursor", n: int, t: float) -> None:
        self.c = c
        self.n = n
        self.t = t


class Mpqe(object):
    """pending files to tag-scan"""

    def __init__(
        self,
        mtp: dict[str, MParser],
        entags: set[str],
        w: str,
        abspath: str,
        oth_tags: dict[str, Any],
    ):
        # mtp empty = mtag
        self.mtp = mtp
        self.entags = entags
        self.w = w
        self.abspath = abspath
        self.oth_tags = oth_tags


class Up2k(object):
    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.asrv: AuthSrv = hub.asrv
        self.args = hub.args
        self.log_func = hub.log

        self.salt = self.args.warksalt
        self.r_hash = re.compile("^[0-9a-zA-Z_-]{44}$")

        self.gid = 0
        self.stop = False
        self.mutex = threading.Lock()
        self.blocked: Optional[str] = None
        self.pp: Optional[ProgressPrinter] = None
        self.rescan_cond = threading.Condition()
        self.need_rescan: set[str] = set()
        self.db_act = 0.0

        self.registry: dict[str, dict[str, dict[str, Any]]] = {}
        self.flags: dict[str, dict[str, Any]] = {}
        self.droppable: dict[str, list[str]] = {}
        self.volnfiles: dict["sqlite3.Cursor", int] = {}
        self.volsize: dict["sqlite3.Cursor", int] = {}
        self.volstate: dict[str, str] = {}
        self.vol_act: dict[str, float] = {}
        self.busy_aps: set[str] = set()
        self.dupesched: dict[str, list[tuple[str, str, float]]] = {}
        self.snap_prev: dict[str, Optional[tuple[int, float]]] = {}

        self.mtag: Optional[MTag] = None
        self.entags: dict[str, set[str]] = {}
        self.mtp_parsers: dict[str, dict[str, MParser]] = {}
        self.pending_tags: list[tuple[set[str], str, str, dict[str, Any]]] = []
        self.hashq: Queue[tuple[str, str, str, str, str, float, str, bool]] = Queue()
        self.tagq: Queue[tuple[str, str, str, str, str, float]] = Queue()
        self.tag_event = threading.Condition()
        self.n_hashq = 0
        self.n_tagq = 0
        self.mpool_used = False

        self.xiu_ptn = re.compile(r"(?:^|,)i([0-9]+)")
        self.xiu_busy = False  # currently running hook
        self.xiu_asleep = True  # needs rescan_cond poke to schedule self

        self.cur: dict[str, "sqlite3.Cursor"] = {}
        self.mem_cur = None
        self.sqlite_ver = None
        self.no_expr_idx = False
        self.timeout = int(max(self.args.srch_time, 50) * 1.2) + 1
        self.spools: set[tempfile.SpooledTemporaryFile[bytes]] = set()
        if HAVE_SQLITE3:
            # mojibake detector
            self.mem_cur = self._orz(":memory:")
            self.mem_cur.execute(r"create table a (b text)")
            self.sqlite_ver = tuple([int(x) for x in sqlite3.sqlite_version.split(".")])
            if self.sqlite_ver < (3, 9):
                self.no_expr_idx = True
        else:
            t = "could not initialize sqlite3, will use in-memory registry only"
            self.log(t, 3)

        self.fstab = Fstab(self.log_func)
        self.gen_fk = self._gen_fk if self.args.log_fk else gen_filekey

        if self.args.hash_mt < 2:
            self.mth: Optional[MTHash] = None
        else:
            self.mth = MTHash(self.args.hash_mt)

        if self.args.no_fastboot:
            self.deferred_init()

    def init_vols(self) -> None:
        if self.args.no_fastboot:
            return

        Daemon(self.deferred_init, "up2k-deferred-init")

    def reload(self) -> None:
        self.gid += 1
        self.log("reload #{} initiated".format(self.gid))
        all_vols = self.asrv.vfs.all_vols
        self.rescan(all_vols, list(all_vols.keys()), True, False)

    def deferred_init(self) -> None:
        all_vols = self.asrv.vfs.all_vols
        have_e2d = self.init_indexes(all_vols, [], False)

        if self.stop:
            # up-mt consistency not guaranteed if init is interrupted;
            # drop caches for a full scan on next boot
            with self.mutex:
                self._drop_caches()

            if self.pp:
                self.pp.end = True
                self.pp = None

            return

        if not self.pp and self.args.exit == "idx":
            return self.hub.sigterm()

        Daemon(self._snapshot, "up2k-snapshot")
        if have_e2d:
            Daemon(self._hasher, "up2k-hasher")
            Daemon(self._sched_rescan, "up2k-rescan")
            if self.mtag:
                for n in range(max(1, self.args.mtag_mt)):
                    Daemon(self._tagger, "tagger-{}".format(n))

                Daemon(self._run_all_mtp, "up2k-mtp-init")

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        if self.pp:
            msg += "\033[K"

        self.log_func("up2k", msg, c)

    def _gen_fk(self, alg: int, salt: str, fspath: str, fsize: int, inode: int) -> str:
        return gen_filekey_dbg(
            alg, salt, fspath, fsize, inode, self.log, self.args.log_fk
        )

    def _block(self, why: str) -> None:
        self.blocked = why
        self.log("uploads temporarily blocked due to " + why, 3)

    def _unblock(self) -> None:
        if self.blocked is not None:
            self.blocked = None
            if not self.stop:
                self.log("uploads are now possible", 2)

    def get_state(self) -> str:
        mtpq: Union[int, str] = 0
        q = "select count(w) from mt where k = 't:mtp'"
        got_lock = False if PY2 else self.mutex.acquire(timeout=0.5)
        if got_lock:
            for cur in self.cur.values():
                try:
                    mtpq += cur.execute(q).fetchone()[0]
                except:
                    pass
            self.mutex.release()
        else:
            mtpq = "(?)"

        ret = {
            "volstate": self.volstate,
            "scanning": bool(self.pp),
            "hashq": self.n_hashq,
            "tagq": self.n_tagq,
            "mtpq": mtpq,
            "dbwt": "{:.2f}".format(
                min(1000 * 24 * 60 * 60 - 1, time.time() - self.db_act)
            ),
        }
        return json.dumps(ret, indent=4)

    def get_unfinished(self) -> str:
        if PY2 or not self.mutex.acquire(timeout=0.5):
            return "{}"

        ret: dict[str, tuple[int, int]] = {}
        try:
            for ptop, tab2 in self.registry.items():
                nbytes = 0
                nfiles = 0
                drp = self.droppable.get(ptop, {})
                for wark, job in tab2.items():
                    if wark in drp:
                        continue

                    nfiles += 1
                    try:
                        # close enough on average
                        nbytes += len(job["need"]) * job["size"] // len(job["hash"])
                    except:
                        pass

                ret[ptop] = (nbytes, nfiles)
        finally:
            self.mutex.release()

        return json.dumps(ret, indent=4)

    def get_volsize(self, ptop: str) -> tuple[int, int]:
        with self.mutex:
            return self._get_volsize(ptop)

    def get_volsizes(self, ptops: list[str]) -> list[tuple[int, int]]:
        ret = []
        with self.mutex:
            for ptop in ptops:
                ret.append(self._get_volsize(ptop))

        return ret

    def _get_volsize(self, ptop: str) -> tuple[int, int]:
        if "e2ds" not in self.flags.get(ptop, {}):
            return (0, 0)

        cur = self.cur[ptop]
        nbytes = self.volsize[cur]
        nfiles = self.volnfiles[cur]
        for j in list(self.registry.get(ptop, {}).values()):
            nbytes += j["size"]
            nfiles += 1

        return (nbytes, nfiles)

    def rescan(
        self, all_vols: dict[str, VFS], scan_vols: list[str], wait: bool, fscan: bool
    ) -> str:
        if not wait and self.pp:
            return "cannot initiate; scan is already in progress"

        args = (all_vols, scan_vols, fscan)
        Daemon(
            self.init_indexes,
            "up2k-rescan-{}".format(scan_vols[0] if scan_vols else "all"),
            args,
        )
        return ""

    def _sched_rescan(self) -> None:
        volage = {}
        cooldown = timeout = time.time() + 3.0
        while True:
            now = time.time()
            timeout = max(timeout, cooldown)
            wait = timeout - time.time()
            # self.log("SR in {:.2f}".format(wait), 5)
            with self.rescan_cond:
                self.rescan_cond.wait(wait)

            now = time.time()
            if now < cooldown:
                # self.log("SR: cd - now = {:.2f}".format(cooldown - now), 5)
                timeout = cooldown  # wakeup means stuff to do, forget timeout
                continue

            if self.pp:
                # self.log("SR: pp; cd := 1", 5)
                cooldown = now + 1
                continue

            cooldown = now + 3
            # self.log("SR", 5)

            if self.args.no_lifetime:
                timeout = now + 9001
            else:
                # important; not deferred by db_act
                timeout = self._check_lifetimes()

            timeout = min(timeout, now + self._check_xiu())

            with self.mutex:
                for vp, vol in sorted(self.asrv.vfs.all_vols.items()):
                    maxage = vol.flags.get("scan")
                    if not maxage:
                        continue

                    if vp not in volage:
                        volage[vp] = now

                    deadline = volage[vp] + maxage
                    if deadline <= now:
                        self.need_rescan.add(vp)

                    timeout = min(timeout, deadline)

            if self.db_act > now - self.args.db_act and self.need_rescan:
                # recent db activity; defer volume rescan
                act_timeout = self.db_act + self.args.db_act
                if self.need_rescan:
                    timeout = now

                if timeout < act_timeout:
                    timeout = act_timeout
                    t = "volume rescan deferred {:.1f} sec, due to database activity"
                    self.log(t.format(timeout - now))

                continue

            with self.mutex:
                vols = list(sorted(self.need_rescan))
                self.need_rescan.clear()

            if vols:
                cooldown = now + 10
                err = self.rescan(self.asrv.vfs.all_vols, vols, False, False)
                if err:
                    for v in vols:
                        self.need_rescan.add(v)

                    continue

                for v in vols:
                    volage[v] = now

    def _check_lifetimes(self) -> float:
        now = time.time()
        timeout = now + 9001
        if now:  # diff-golf
            for vp, vol in sorted(self.asrv.vfs.all_vols.items()):
                lifetime = vol.flags.get("lifetime")
                if not lifetime:
                    continue

                cur = self.cur.get(vol.realpath)
                if not cur:
                    continue

                nrm = 0
                deadline = time.time() - lifetime
                timeout = min(timeout, now + lifetime)
                q = "select rd, fn from up where at > 0 and at < ? limit 100"
                while True:
                    with self.mutex:
                        hits = cur.execute(q, (deadline,)).fetchall()

                    if not hits:
                        break

                    for rd, fn in hits:
                        if rd.startswith("//") or fn.startswith("//"):
                            rd, fn = s3dec(rd, fn)

                        fvp = ("%s/%s" % (rd, fn)).strip("/")
                        if vp:
                            fvp = "%s/%s" % (vp, fvp)

                        self._handle_rm(LEELOO_DALLAS, "", fvp, [], True)
                        nrm += 1

                if nrm:
                    self.log("{} files graduated in {}".format(nrm, vp))

                if timeout < 10:
                    continue

                q = "select at from up where at > 0 order by at limit 1"
                with self.mutex:
                    hits = cur.execute(q).fetchone()

                if hits:
                    timeout = min(timeout, now + lifetime - (now - hits[0]))

        return timeout

    def _check_xiu(self) -> float:
        if self.xiu_busy:
            return 2

        ret = 9001
        for _, vol in sorted(self.asrv.vfs.all_vols.items()):
            rp = vol.realpath
            cur = self.cur.get(rp)
            if not cur:
                continue

            with self.mutex:
                q = "select distinct c from iu"
                cds = cur.execute(q).fetchall()
                if not cds:
                    continue

            run_cds: list[int] = []
            for cd in sorted([x[0] for x in cds]):
                delta = cd - (time.time() - self.vol_act[rp])
                if delta > 0:
                    ret = min(ret, delta)
                    break

                run_cds.append(cd)

            if run_cds:
                self.xiu_busy = True
                Daemon(self._run_xius, "xiu", (vol, run_cds))
                return 2

        return ret

    def _run_xius(self, vol: VFS, cds: list[int]):
        for cd in cds:
            self._run_xiu(vol, cd)

        self.xiu_busy = False
        self.xiu_asleep = True

    def _run_xiu(self, vol: VFS, cd: int):
        rp = vol.realpath
        cur = self.cur[rp]

        # t0 = time.time()
        with self.mutex:
            q = "select w,rd,fn from iu where c={} limit 80386"
            wrfs = cur.execute(q.format(cd)).fetchall()
            if not wrfs:
                return

            # dont wanna rebox so use format instead of prepared
            q = "delete from iu where w=? and +rd=? and +fn=? and +c={}"
            cur.executemany(q.format(cd), wrfs)
            cur.connection.commit()

            q = "select * from up where substr(w,1,16)=? and +rd=? and +fn=?"
            ups = []
            for wrf in wrfs:
                up = cur.execute(q, wrf).fetchone()
                if up:
                    ups.append(up)

        # t1 = time.time()
        # self.log("mapped {} warks in {:.3f} sec".format(len(wrfs), t1 - t0))
        # "mapped 10989 warks in 0.126 sec"

        cmds = self.flags[rp]["xiu"]
        for cmd in cmds:
            m = self.xiu_ptn.search(cmd)
            ccd = int(m.group(1)) if m else 5
            if ccd != cd:
                continue

            self.log("xiu: {}# {}".format(len(wrfs), cmd))
            runihook(self.log, cmd, vol, ups)

    def _vis_job_progress(self, job: dict[str, Any]) -> str:
        perc = 100 - (len(job["need"]) * 100.0 / len(job["hash"]))
        path = djoin(job["ptop"], job["prel"], job["name"])
        return "{:5.1f}% {}".format(perc, path)

    def _vis_reg_progress(self, reg: dict[str, dict[str, Any]]) -> list[str]:
        ret = []
        for _, job in reg.items():
            if job["need"]:
                ret.append(self._vis_job_progress(job))

        return ret

    def _expr_idx_filter(self, flags: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        if not self.no_expr_idx:
            return False, flags

        ret = {k: v for k, v in flags.items() if not k.startswith("e2t")}
        if ret.keys() == flags.keys():
            return False, flags

        return True, ret

    def init_indexes(
        self, all_vols: dict[str, VFS], scan_vols: list[str], fscan: bool
    ) -> bool:
        gid = self.gid
        while self.pp and gid == self.gid:
            time.sleep(0.1)

        if gid != self.gid:
            return False

        if gid:
            self.log("reload #{} running".format(self.gid))

        self.pp = ProgressPrinter()
        vols = list(all_vols.values())
        t0 = time.time()
        have_e2d = False

        if self.no_expr_idx:
            modified = False
            for vol in vols:
                m, f = self._expr_idx_filter(vol.flags)
                if m:
                    vol.flags = f
                    modified = True

            if modified:
                msg = "disabling -e2t because your sqlite belongs in a museum"
                self.log(msg, c=3)

        live_vols = []
        with self.mutex:
            # only need to protect register_vpath but all in one go feels right
            for vol in vols:
                try:
                    bos.makedirs(vol.realpath)  # gonna happen at snap anyways
                    bos.listdir(vol.realpath)
                except:
                    self.volstate[vol.vpath] = "OFFLINE (cannot access folder)"
                    self.log("cannot access " + vol.realpath, c=1)
                    continue

                if scan_vols and vol.vpath not in scan_vols:
                    continue

                if not self.register_vpath(vol.realpath, vol.flags):
                    # self.log("db not enable for {}".format(m, vol.realpath))
                    continue

                live_vols.append(vol)

                if vol.vpath not in self.volstate:
                    self.volstate[vol.vpath] = "OFFLINE (pending initialization)"

        vols = live_vols
        need_vac = {}

        need_mtag = False
        for vol in vols:
            if "e2t" in vol.flags:
                need_mtag = True

        if need_mtag and not self.mtag:
            self.mtag = MTag(self.log_func, self.args)
            if not self.mtag.usable:
                self.mtag = None

        # e2ds(a) volumes first
        if next((zv for zv in vols if "e2ds" in zv.flags), None):
            self._block("indexing")

        if self.args.re_dhash or [zv for zv in vols if "e2tsr" in zv.flags]:
            self.args.re_dhash = False
            with self.mutex:
                self._drop_caches()

        for vol in vols:
            if self.stop:
                break

            en = set(vol.flags.get("mte", {}))
            self.entags[vol.realpath] = en

            if "e2d" in vol.flags:
                have_e2d = True

            if "e2ds" in vol.flags or fscan:
                self.volstate[vol.vpath] = "busy (hashing files)"
                _, vac = self._build_file_index(vol, list(all_vols.values()))
                if vac:
                    need_vac[vol] = True

            if "e2v" in vol.flags:
                t = "online (integrity-check pending)"
            elif "e2ts" in vol.flags:
                t = "online (tags pending)"
            else:
                t = "online, idle"

            self.volstate[vol.vpath] = t

        self._unblock()

        # file contents verification
        for vol in vols:
            if self.stop:
                break

            if "e2v" not in vol.flags:
                continue

            t = "online (verifying integrity)"
            self.volstate[vol.vpath] = t
            self.log("{} [{}]".format(t, vol.realpath))

            nmod = self._verify_integrity(vol)
            if nmod:
                self.log("modified {} entries in the db".format(nmod), 3)
                need_vac[vol] = True

            if "e2ts" in vol.flags:
                t = "online (tags pending)"
            else:
                t = "online, idle"

            self.volstate[vol.vpath] = t

        # open the rest + do any e2ts(a)
        needed_mutagen = False
        for vol in vols:
            if self.stop:
                break

            if "e2ts" not in vol.flags:
                continue

            t = "online (reading tags)"
            self.volstate[vol.vpath] = t
            self.log("{} [{}]".format(t, vol.realpath))

            nadd, nrm, success = self._build_tags_index(vol)
            if not success:
                needed_mutagen = True

            if nadd or nrm:
                need_vac[vol] = True

            self.volstate[vol.vpath] = "online (mtp soon)"

        for vol in need_vac:
            reg = self.register_vpath(vol.realpath, vol.flags)
            assert reg
            cur, _ = reg
            with self.mutex:
                cur.connection.commit()
                cur.execute("vacuum")

        if self.stop:
            return False

        for vol in all_vols.values():
            if vol.flags["dbd"] == "acid":
                continue

            reg = self.register_vpath(vol.realpath, vol.flags)
            try:
                assert reg
                cur, db_path = reg
                if bos.path.getsize(db_path + "-wal") < 1024 * 1024 * 5:
                    continue
            except:
                continue

            try:
                with self.mutex:
                    cur.execute("pragma wal_checkpoint(truncate)")
                    try:
                        cur.execute("commit")  # absolutely necessary! for some reason
                    except:
                        pass

                    cur.connection.commit()  # this one maybe not
            except Exception as ex:
                self.log("checkpoint failed: {}".format(ex), 3)

        if self.stop:
            return False

        self.pp.end = True

        msg = "{} volumes in {:.2f} sec"
        self.log(msg.format(len(vols), time.time() - t0))

        if needed_mutagen:
            msg = "could not read tags because no backends are available (Mutagen or FFprobe)"
            self.log(msg, c=1)

        thr = None
        if self.mtag:
            t = "online (running mtp)"
            if scan_vols:
                thr = Daemon(self._run_all_mtp, "up2k-mtp-scan", r=False)
        else:
            self.pp = None
            t = "online, idle"

        for vol in vols:
            self.volstate[vol.vpath] = t

        if thr:
            thr.start()

        return have_e2d

    def register_vpath(
        self, ptop: str, flags: dict[str, Any]
    ) -> Optional[tuple["sqlite3.Cursor", str]]:
        histpath = self.asrv.vfs.histtab.get(ptop)
        if not histpath:
            self.log("no histpath for [{}]".format(ptop))
            return None

        db_path = os.path.join(histpath, "up2k.db")
        if ptop in self.registry:
            try:
                return self.cur[ptop], db_path
            except:
                return None

        _, flags = self._expr_idx_filter(flags)

        ft = "\033[0;32m{}{:.0}"
        ff = "\033[0;35m{}{:.0}"
        fv = "\033[0;36m{}:\033[90m{}"
        fx = set(("html_head",))
        fd = vf_bmap()
        fd.update(vf_cmap())
        fd.update(vf_vmap())
        fd = {v: k for k, v in fd.items()}
        fl = {
            k: v
            for k, v in flags.items()
            if k not in fd
            or (
                v != getattr(self.args, fd[k])
                and str(v) != str(getattr(self.args, fd[k]))
            )
        }
        for k1, k2 in vf_cmap().items():
            if k1 not in fl or k1 in fx:
                continue
            if str(fl[k1]) == str(getattr(self.args, k2)):
                del fl[k1]
            else:
                fl[k1] = ",".join(x for x in fl[k1])
        a = [
            (ft if v is True else ff if v is False else fv).format(k, str(v))
            for k, v in fl.items()
            if k not in fx
        ]
        if not a:
            a = ["\033[90mall-default"]

        if a:
            vpath = "?"
            for k, v in self.asrv.vfs.all_vols.items():
                if v.realpath == ptop:
                    vpath = k

            if vpath:
                vpath += "/"

            zs = " ".join(sorted(a))
            zs = zs.replace("90mre.compile(", "90m(")  # nohash
            self.log("/{} {}".format(vpath, zs), "35")

        reg = {}
        drp = None
        snap = os.path.join(histpath, "up2k.snap")
        if bos.path.exists(snap):
            with gzip.GzipFile(snap, "rb") as f:
                j = f.read().decode("utf-8")

            reg2 = json.loads(j)
            try:
                drp = reg2["droppable"]
                reg2 = reg2["registry"]
            except:
                pass

            for k, job in reg2.items():
                fp = djoin(job["ptop"], job["prel"], job["name"])
                if bos.path.exists(fp):
                    reg[k] = job
                    job["poke"] = time.time()
                    job["busy"] = {}
                else:
                    self.log("ign deleted file in snap: [{}]".format(fp))

            if drp is None:
                drp = [k for k, v in reg.items() if not v.get("need", [])]
            else:
                drp = [x for x in drp if x in reg]

            t = "loaded snap {} |{}| ({})".format(snap, len(reg.keys()), len(drp or []))
            ta = [t] + self._vis_reg_progress(reg)
            self.log("\n".join(ta))

        self.flags[ptop] = flags
        self.vol_act[ptop] = 0.0
        self.registry[ptop] = reg
        self.droppable[ptop] = drp or []
        self.regdrop(ptop, "")
        if not HAVE_SQLITE3 or "e2d" not in flags or "d2d" in flags:
            return None

        try:
            if bos.makedirs(histpath):
                hidedir(histpath)
        except:
            return None

        try:
            cur = self._open_db(db_path)
            self.cur[ptop] = cur
            self.volsize[cur] = 0
            self.volnfiles[cur] = 0

            # speeds measured uploading 520 small files on a WD20SPZX (SMR 2.5" 5400rpm 4kb)
            dbd = flags["dbd"]
            if dbd == "acid":
                # 217.5s; python-defaults
                zs = "delete"
                sync = "full"
            elif dbd == "swal":
                # 88.0s; still 99.9% safe (can lose a bit of on OS crash)
                zs = "wal"
                sync = "full"
            elif dbd == "yolo":
                # 2.7s; may lose entire db on OS crash
                zs = "wal"
                sync = "off"
            else:
                # 4.1s; corruption-safe but more likely to lose wal
                zs = "wal"
                sync = "normal"

            try:
                amode = cur.execute("pragma journal_mode=" + zs).fetchone()[0]
                if amode.lower() != zs.lower():
                    t = "sqlite failed to set journal_mode {}; got {}"
                    raise Exception(t.format(zs, amode))
            except Exception as ex:
                if sync != "off":
                    sync = "full"
                    t = "reverting to sync={} because {}"
                    self.log(t.format(sync, ex))

            cur.execute("pragma synchronous=" + sync)
            cur.connection.commit()
            return cur, db_path
        except:
            msg = "cannot use database at [{}]:\n{}"
            self.log(msg.format(ptop, traceback.format_exc()))

        return None

    def _build_file_index(self, vol: VFS, all_vols: list[VFS]) -> tuple[bool, bool]:
        do_vac = False
        top = vol.realpath
        rei = vol.flags.get("noidx")
        reh = vol.flags.get("nohash")
        n4g = bool(vol.flags.get("noforget"))
        ffat = "fat32" in vol.flags
        cst = bos.stat(top)
        dev = cst.st_dev if vol.flags.get("xdev") else 0

        with self.mutex:
            reg = self.register_vpath(top, vol.flags)
            assert reg and self.pp
            cur, db_path = reg

            db = Dbw(cur, 0, time.time())
            self.pp.n = next(db.c.execute("select count(w) from up"))[0]

            excl = [
                vol.realpath + "/" + d.vpath[len(vol.vpath) :].lstrip("/")
                for d in all_vols
                if d != vol and (d.vpath.startswith(vol.vpath + "/") or not vol.vpath)
            ]
            excl += [absreal(x) for x in excl]
            excl += list(self.asrv.vfs.histtab.values())
            if WINDOWS:
                excl = [x.replace("/", "\\") for x in excl]
            else:
                # ~/.wine/dosdevices/z:/ and such
                excl += ["/dev", "/proc", "/run", "/sys"]

            rtop = absreal(top)
            n_add = n_rm = 0
            try:
                if not bos.listdir(rtop):
                    t = "volume /%s at [%s] is empty; will not be indexed as this could be due to an offline filesystem"
                    self.log(t % (vol.vpath, rtop), 6)
                    return True, False

                n_add = self._build_dir(
                    db,
                    top,
                    set(excl),
                    top,
                    rtop,
                    rei,
                    reh,
                    n4g,
                    ffat,
                    [],
                    cst,
                    dev,
                    bool(vol.flags.get("xvol")),
                )
                if not n4g:
                    n_rm = self._drop_lost(db.c, top, excl)
            except Exception as ex:
                t = "failed to index volume [{}]:\n{}"
                self.log(t.format(top, min_ex()), c=1)
                if db_ex_chk(self.log, ex, db_path):
                    self.hub.log_stacks()

            if db.n:
                self.log("commit {} new files".format(db.n))

            if self.args.no_dhash:
                if db.c.execute("select d from dh").fetchone():
                    db.c.execute("delete from dh")
                    self.log("forgetting dhashes in {}".format(top))
            elif n_add or n_rm:
                self._set_tagscan(db.c, True)

            db.c.connection.commit()

            if (
                vol.flags.get("vmaxb")
                or vol.flags.get("vmaxn")
                or (self.args.stats and not self.args.nos_vol)
            ):
                zs = "select count(sz), sum(sz) from up"
                vn, vb = db.c.execute(zs).fetchone()
                vb = vb or 0
                vb += vn * 2048
                self.volsize[db.c] = vb
                self.volnfiles[db.c] = vn
                vmaxb = unhumanize(vol.flags.get("vmaxb") or "0")
                vmaxn = unhumanize(vol.flags.get("vmaxn") or "0")
                t = "{:>5} / {:>5}  ( {:>5} / {:>5} files) in {}".format(
                    humansize(vb, True),
                    humansize(vmaxb, True),
                    humansize(vn, True).rstrip("B"),
                    humansize(vmaxn, True).rstrip("B"),
                    vol.realpath,
                )
                self.log(t)

            return True, bool(n_add or n_rm or do_vac)

    def _build_dir(
        self,
        db: Dbw,
        top: str,
        excl: set[str],
        cdir: str,
        rcdir: str,
        rei: Optional[Pattern[str]],
        reh: Optional[Pattern[str]],
        n4g: bool,
        ffat: bool,
        seen: list[str],
        cst: os.stat_result,
        dev: int,
        xvol: bool,
    ) -> int:
        if xvol and not rcdir.startswith(top):
            self.log("skip xvol: [{}] -> [{}]".format(cdir, rcdir), 6)
            return 0

        if rcdir in seen:
            t = "bailing from symlink loop,\n  prev: {}\n  curr: {}\n  from: {}"
            self.log(t.format(seen[-1], rcdir, cdir), 3)
            return 0

        ret = 0
        seen = seen + [rcdir]
        unreg: list[str] = []
        files: list[tuple[int, int, str]] = []
        fat32 = True
        cv = ""

        assert self.pp and self.mem_cur
        self.pp.msg = "a{} {}".format(self.pp.n, cdir)

        rd = cdir[len(top) :].strip("/")
        if WINDOWS:
            rd = rd.replace("\\", "/").strip("/")

        g = statdir(self.log_func, not self.args.no_scandir, True, cdir)
        gl = sorted(g)
        partials = set([x[0] for x in gl if "PARTIAL" in x[0]])
        for iname, inf in gl:
            if self.stop:
                return -1

            rp = vjoin(rd, iname)
            abspath = os.path.join(cdir, iname)

            if rei and rei.search(abspath):
                unreg.append(rp)
                continue

            lmod = int(inf.st_mtime)
            if stat.S_ISLNK(inf.st_mode):
                try:
                    inf = bos.stat(abspath)
                except:
                    continue

            sz = inf.st_size
            if fat32 and not ffat and inf.st_mtime % 2:
                fat32 = False

            if stat.S_ISDIR(inf.st_mode):
                rap = absreal(abspath)
                if dev and inf.st_dev != dev:
                    self.log("skip xdev {}->{}: {}".format(dev, inf.st_dev, abspath), 6)
                    continue
                if abspath in excl or rap in excl:
                    unreg.append(rp)
                    continue
                if iname == ".th" and bos.path.isdir(os.path.join(abspath, "top")):
                    # abandoned or foreign, skip
                    continue
                # self.log(" dir: {}".format(abspath))
                try:
                    ret += self._build_dir(
                        db,
                        top,
                        excl,
                        abspath,
                        rap,
                        rei,
                        reh,
                        n4g,
                        fat32,
                        seen,
                        inf,
                        dev,
                        xvol,
                    )
                except:
                    t = "failed to index subdir [{}]:\n{}"
                    self.log(t.format(abspath, min_ex()), c=1)
            elif not stat.S_ISREG(inf.st_mode):
                self.log("skip type-{:x} file [{}]".format(inf.st_mode, abspath))
            else:
                # self.log("file: {}".format(abspath))
                if rp.endswith(".PARTIAL") and time.time() - lmod < 60:
                    # rescan during upload
                    continue

                if not sz and (
                    "{}.PARTIAL".format(iname) in partials
                    or ".{}.PARTIAL".format(iname) in partials
                ):
                    # placeholder for unfinished upload
                    continue

                files.append((sz, lmod, iname))
                liname = iname.lower()
                if sz and (
                    iname in self.args.th_covers
                    or (not cv and liname.rsplit(".", 1)[-1] in CV_EXTS)
                ):
                    cv = iname

        # folder of 1000 files = ~1 MiB RAM best-case (tiny filenames);
        # free up stuff we're done with before dhashing
        gl = []
        partials.clear()
        if not self.args.no_dhash:
            if len(files) < 9000:
                zh = hashlib.sha1(str(files).encode("utf-8", "replace"))
            else:
                zh = hashlib.sha1()
                _ = [zh.update(str(x).encode("utf-8", "replace")) for x in files]

            zh.update(cv.encode("utf-8", "replace"))
            zh.update(spack(b"<d", cst.st_mtime))
            dhash = base64.urlsafe_b64encode(zh.digest()[:12]).decode("ascii")
            sql = "select d from dh where d=? and +h=?"
            try:
                c = db.c.execute(sql, (rd, dhash))
                drd = rd
            except:
                drd = "//" + w8b64enc(rd)
                c = db.c.execute(sql, (drd, dhash))

            if c.fetchone():
                return ret

        if cv and rd:
            # mojibake not supported (for performance / simplicity):
            try:
                q = "select * from cv where rd=? and dn=? and +fn=?"
                crd, cdn = rd.rsplit("/", 1) if "/" in rd else ("", rd)
                if not db.c.execute(q, (crd, cdn, cv)).fetchone():
                    db.c.execute("delete from cv where rd=? and dn=?", (crd, cdn))
                    db.c.execute("insert into cv values (?,?,?)", (crd, cdn, cv))
                    db.n += 1
            except Exception as ex:
                self.log("cover {}/{} failed: {}".format(rd, cv, ex), 6)

        seen_files = set([x[2] for x in files])  # for dropcheck
        for sz, lmod, fn in files:
            if self.stop:
                return -1

            rp = vjoin(rd, fn)
            abspath = os.path.join(cdir, fn)
            nohash = reh.search(abspath) if reh else False

            if fn:  # diff-golf

                sql = "select w, mt, sz, at from up where rd = ? and fn = ?"
                try:
                    c = db.c.execute(sql, (rd, fn))
                except:
                    c = db.c.execute(sql, s3enc(self.mem_cur, rd, fn))

                in_db = list(c.fetchall())
                if in_db:
                    self.pp.n -= 1
                    dw, dts, dsz, at = in_db[0]
                    if len(in_db) > 1:
                        t = "WARN: multiple entries: [{}] => [{}] |{}|\n{}"
                        rep_db = "\n".join([repr(x) for x in in_db])
                        self.log(t.format(top, rp, len(in_db), rep_db))
                        dts = -1

                    if fat32 and abs(dts - lmod) == 1:
                        dts = lmod

                    if dts == lmod and dsz == sz and (nohash or dw[0] != "#" or not sz):
                        continue

                    t = "reindex [{}] => [{}] ({}/{}) ({}/{})".format(
                        top, rp, dts, lmod, dsz, sz
                    )
                    self.log(t)
                    self.db_rm(db.c, rd, fn, 0)
                    ret += 1
                    db.n += 1
                    in_db = []
                else:
                    at = 0

                self.pp.msg = "a{} {}".format(self.pp.n, abspath)

                if nohash or not sz:
                    wark = up2k_wark_from_metadata(self.salt, sz, lmod, rd, fn)
                else:
                    if sz > 1024 * 1024:
                        self.log("file: {}".format(abspath))

                    try:
                        hashes = self._hashlist_from_file(
                            abspath, "a{}, ".format(self.pp.n)
                        )
                    except Exception as ex:
                        self.log("hash: {} @ [{}]".format(repr(ex), abspath))
                        continue

                    if not hashes:
                        return -1

                    wark = up2k_wark_from_hashlist(self.salt, sz, hashes)

                # skip upload hooks by not providing vflags
                self.db_add(db.c, {}, rd, fn, lmod, sz, "", "", wark, "", "", "", at)
                db.n += 1
                ret += 1
                td = time.time() - db.t
                if db.n >= 4096 or td >= 60:
                    self.log("commit {} new files".format(db.n))
                    db.c.connection.commit()
                    db.n = 0
                    db.t = time.time()

        if not self.args.no_dhash:
            db.c.execute("delete from dh where d = ?", (drd,))
            db.c.execute("insert into dh values (?,?)", (drd, dhash))

        if self.stop:
            return -1

        # drop shadowed folders
        for sh_rd in unreg:
            n = 0
            q = "select count(w) from up where (rd = ? or rd like ?||'%') and at == 0"
            for sh_erd in [sh_rd, "//" + w8b64enc(sh_rd)]:
                try:
                    n = db.c.execute(q, (sh_erd, sh_erd + "/")).fetchone()[0]
                    break
                except:
                    pass

            if n:
                t = "forgetting {} shadowed autoindexed files in [{}] > [{}]"
                self.log(t.format(n, top, sh_rd))
                assert sh_erd

                q = "delete from dh where (d = ? or d like ?||'%')"
                db.c.execute(q, (sh_erd, sh_erd + "/"))

                q = "delete from up where (rd = ? or rd like ?||'%') and at == 0"
                db.c.execute(q, (sh_erd, sh_erd + "/"))
                ret += n

        if n4g:
            return ret

        # drop missing files
        q = "select fn from up where rd = ?"
        try:
            c = db.c.execute(q, (rd,))
        except:
            c = db.c.execute(q, ("//" + w8b64enc(rd),))

        hits = [w8b64dec(x[2:]) if x.startswith("//") else x for (x,) in c]
        rm_files = [x for x in hits if x not in seen_files]
        n_rm = len(rm_files)
        for fn in rm_files:
            self.db_rm(db.c, rd, fn, 0)

        if n_rm:
            self.log("forgot {} deleted files".format(n_rm))

        return ret

    def _drop_lost(self, cur: "sqlite3.Cursor", top: str, excl: list[str]) -> int:
        rm = []
        n_rm = 0
        nchecked = 0
        assert self.pp

        # `_build_dir` did all unshadowed files; first do dirs:
        ndirs = next(cur.execute("select count(distinct rd) from up"))[0]
        c = cur.execute("select distinct rd from up order by rd desc")
        for (drd,) in c:
            nchecked += 1
            if drd.startswith("//"):
                rd = w8b64dec(drd[2:])
            else:
                rd = drd

            abspath = djoin(top, rd)
            self.pp.msg = "b{} {}".format(ndirs - nchecked, abspath)
            try:
                if os.path.isdir(abspath):
                    continue
            except:
                pass

            rm.append(drd)

        if rm:
            q = "select count(w) from up where rd = ?"
            for rd in rm:
                n_rm += next(cur.execute(q, (rd,)))[0]

            self.log("forgetting {} deleted dirs, {} files".format(len(rm), n_rm))
            for rd in rm:
                cur.execute("delete from dh where d = ?", (rd,))
                cur.execute("delete from up where rd = ?", (rd,))

        # then shadowed deleted files
        n_rm2 = 0
        c2 = cur.connection.cursor()
        excl = [x[len(top) + 1 :] for x in excl if x.startswith(top + "/")]
        q = "select rd, fn from up where (rd = ? or rd like ?||'%') order by rd"
        for rd in excl:
            for erd in [rd, "//" + w8b64enc(rd)]:
                try:
                    c = cur.execute(q, (erd, erd + "/"))
                    break
                except:
                    pass

            crd = "///"
            cdc: set[str] = set()
            for drd, dfn in c:
                rd, fn = s3dec(drd, dfn)

                if crd != rd:
                    crd = rd
                    try:
                        cdc = set(os.listdir(djoin(top, rd)))
                    except:
                        cdc.clear()

                if fn not in cdc:
                    q = "delete from up where rd = ? and fn = ?"
                    c2.execute(q, (drd, dfn))
                    n_rm2 += 1

        if n_rm2:
            self.log("forgetting {} shadowed deleted files".format(n_rm2))

        c2.connection.commit()

        # then covers
        n_rm3 = 0
        qu = "select 1 from up where rd=? and +fn=? limit 1"
        q = "delete from cv where rd=? and dn=? and +fn=?"
        for crd, cdn, fn in cur.execute("select * from cv"):
            urd = vjoin(crd, cdn)
            if not c2.execute(qu, (urd, fn)).fetchone():
                c2.execute(q, (crd, cdn, fn))
                n_rm3 += 1

        if n_rm3:
            self.log("forgetting {} deleted covers".format(n_rm3))

        c2.connection.commit()
        c2.close()
        return n_rm + n_rm2

    def _verify_integrity(self, vol: VFS) -> int:
        """expensive; blocks database access until finished"""
        ptop = vol.realpath
        assert self.pp

        cur = self.cur[ptop]
        rei = vol.flags.get("noidx")
        reh = vol.flags.get("nohash")
        e2vu = "e2vu" in vol.flags
        e2vp = "e2vp" in vol.flags

        excl = [
            d[len(vol.vpath) :].lstrip("/")
            for d in self.asrv.vfs.all_vols
            if d != vol.vpath and (d.startswith(vol.vpath + "/") or not vol.vpath)
        ]
        qexa: list[str] = []
        pexa: list[str] = []
        for vpath in excl:
            qexa.append("up.rd != ? and not up.rd like ?||'%'")
            pexa.extend([vpath, vpath])

        pex: tuple[Any, ...] = tuple(pexa)
        qex = " and ".join(qexa)
        if qex:
            qex = " where " + qex

        rewark: list[tuple[str, str, str, int, int]] = []

        with self.mutex:
            b_left = 0
            n_left = 0
            q = "select sz from up" + qex
            for (sz,) in cur.execute(q, pex):
                b_left += sz  # sum() can overflow according to docs
                n_left += 1

            tf, _ = self._spool_warks(cur, "select w, rd, fn from up" + qex, pex, 0)

        with gzip.GzipFile(mode="rb", fileobj=tf) as gf:
            for zb in gf:
                if self.stop:
                    return -1

                w, drd, dfn = zb[:-1].decode("utf-8").split("\x00")
                with self.mutex:
                    q = "select mt, sz from up where rd=? and fn=? and +w=?"
                    try:
                        mt, sz = cur.execute(q, (drd, dfn, w)).fetchone()
                    except:
                        # file moved/deleted since spooling
                        continue

                n_left -= 1
                b_left -= sz
                if drd.startswith("//") or dfn.startswith("//"):
                    rd, fn = s3dec(drd, dfn)
                else:
                    rd = drd
                    fn = dfn

                abspath = djoin(ptop, rd, fn)
                if rei and rei.search(abspath):
                    continue

                nohash = reh.search(abspath) if reh else False

                pf = "v{}, {:.0f}+".format(n_left, b_left / 1024 / 1024)
                self.pp.msg = pf + abspath

                # throws on broken symlinks (always did)
                stl = bos.lstat(abspath)
                st = bos.stat(abspath) if stat.S_ISLNK(stl.st_mode) else stl
                mt2 = int(stl.st_mtime)
                sz2 = st.st_size

                if nohash or not sz2:
                    w2 = up2k_wark_from_metadata(self.salt, sz2, mt2, rd, fn)
                else:
                    if sz2 > 1024 * 1024 * 32:
                        self.log("file: {}".format(abspath))

                    try:
                        hashes = self._hashlist_from_file(abspath, pf)
                    except Exception as ex:
                        self.log("hash: {} @ [{}]".format(repr(ex), abspath))
                        continue

                    if not hashes:
                        return -1

                    w2 = up2k_wark_from_hashlist(self.salt, sz2, hashes)

                if w == w2:
                    continue

                # symlink mtime was inconsistent before v1.9.4; check if that's it
                if st != stl and (nohash or not sz2):
                    mt2b = int(st.st_mtime)
                    w2b = up2k_wark_from_metadata(self.salt, sz2, mt2b, rd, fn)
                    if w == w2b:
                        continue

                rewark.append((drd, dfn, w2, sz2, mt2))

                t = "hash mismatch: {}\n  db: {} ({} byte, {})\n  fs: {} ({} byte, {})"
                t = t.format(abspath, w, sz, mt, w2, sz2, mt2)
                self.log(t, 1)

        if e2vp and rewark:
            self.hub.retcode = 1
            os.kill(os.getpid(), signal.SIGTERM)
            raise Exception("{} files have incorrect hashes".format(len(rewark)))

        if not e2vu or not rewark:
            return 0

        with self.mutex:
            for rd, fn, w, sz, mt in rewark:
                q = "update up set w = ?, sz = ?, mt = ? where rd = ? and fn = ? limit 1"
                cur.execute(q, (w, sz, int(mt), rd, fn))

            cur.connection.commit()

        return len(rewark)

    def _build_tags_index(self, vol: VFS) -> tuple[int, int, bool]:
        ptop = vol.realpath
        with self.mutex:
            reg = self.register_vpath(ptop, vol.flags)

        assert reg and self.pp
        cur = self.cur[ptop]

        if not self.args.no_dhash:
            with self.mutex:
                c = cur.execute("select k from kv where k = 'tagscan'")
                if not c.fetchone():
                    return 0, 0, bool(self.mtag)

        ret = self._build_tags_index_2(ptop)

        with self.mutex:
            self._set_tagscan(cur, False)
            cur.connection.commit()

        return ret

    def _drop_caches(self) -> None:
        self.log("dropping caches for a full filesystem scan")
        for vol in self.asrv.vfs.all_vols.values():
            reg = self.register_vpath(vol.realpath, vol.flags)
            if not reg:
                continue

            cur, _ = reg
            self._set_tagscan(cur, True)
            cur.execute("delete from dh")
            cur.execute("delete from cv")
            cur.connection.commit()

    def _set_tagscan(self, cur: "sqlite3.Cursor", need: bool) -> bool:
        if self.args.no_dhash:
            return False

        c = cur.execute("select k from kv where k = 'tagscan'")
        if bool(c.fetchone()) == need:
            return False

        if need:
            cur.execute("insert into kv values ('tagscan',1)")
        else:
            cur.execute("delete from kv where k = 'tagscan'")

        return True

    def _build_tags_index_2(self, ptop: str) -> tuple[int, int, bool]:
        entags = self.entags[ptop]
        flags = self.flags[ptop]
        cur = self.cur[ptop]

        n_add = 0
        n_rm = 0
        if "e2tsr" in flags:
            with self.mutex:
                n_rm = cur.execute("select count(w) from mt").fetchone()[0]
                if n_rm:
                    self.log("discarding {} media tags for a full rescan".format(n_rm))
                    cur.execute("delete from mt")

        # integrity: drop tags for tracks that were deleted
        if "e2t" in flags:
            with self.mutex:
                n = 0
                c2 = cur.connection.cursor()
                up_q = "select w from up where substr(w,1,16) = ?"
                rm_q = "delete from mt where w = ?"
                for (w,) in cur.execute("select w from mt"):
                    if not c2.execute(up_q, (w,)).fetchone():
                        c2.execute(rm_q, (w[:16],))
                        n += 1

                c2.close()
                if n:
                    t = "discarded media tags for {} deleted files"
                    self.log(t.format(n))
                    n_rm += n

        with self.mutex:
            cur.connection.commit()

        # bail if a volflag disables indexing
        if "d2t" in flags or "d2d" in flags:
            return 0, n_rm, True

        # add tags for new files
        if "e2ts" in flags:
            if not self.mtag:
                return 0, n_rm, False

            nq = 0
            with self.mutex:
                tf, nq = self._spool_warks(
                    cur, "select w from up order by rd, fn", (), 1
                )

            if not nq:
                # self.log("tags ok")
                self._unspool(tf)
                return 0, n_rm, True

            if nq == -1:
                return -1, -1, True

            with gzip.GzipFile(mode="rb", fileobj=tf) as gf:
                n_add = self._e2ts_q(gf, nq, cur, ptop, entags)

            self._unspool(tf)

        return n_add, n_rm, True

    def _e2ts_q(
        self,
        qf: gzip.GzipFile,
        nq: int,
        cur: "sqlite3.Cursor",
        ptop: str,
        entags: set[str],
    ) -> int:
        assert self.pp and self.mtag

        flags = self.flags[ptop]
        mpool: Optional[Queue[Mpqe]] = None
        if self.mtag.prefer_mt and self.args.mtag_mt > 1:
            mpool = self._start_mpool()

        n_add = 0
        n_buf = 0
        last_write = time.time()
        for bw in qf:
            if self.stop:
                return -1

            w = bw[:-1].decode("ascii")

            with self.mutex:
                try:
                    q = "select rd, fn, ip, at from up where substr(w,1,16)=? and +w=?"
                    rd, fn, ip, at = cur.execute(q, (w[:16], w)).fetchone()
                except:
                    # file modified/deleted since spooling
                    continue

                if rd.startswith("//") or fn.startswith("//"):
                    rd, fn = s3dec(rd, fn)

                if "mtp" in flags:
                    q = "insert into mt values (?,'t:mtp','a')"
                    cur.execute(q, (w[:16],))

            abspath = djoin(ptop, rd, fn)
            self.pp.msg = "c{} {}".format(nq, abspath)
            if not mpool:
                n_tags = self._tagscan_file(cur, entags, w, abspath, ip, at)
            else:
                if ip:
                    oth_tags = {"up_ip": ip, "up_at": at}
                else:
                    oth_tags = {}

                mpool.put(Mpqe({}, entags, w, abspath, oth_tags))
                with self.mutex:
                    n_tags = len(self._flush_mpool(cur))

            n_add += n_tags
            n_buf += n_tags
            nq -= 1

            td = time.time() - last_write
            if n_buf >= 4096 or td >= self.timeout / 2:
                self.log("commit {} new tags".format(n_buf))
                with self.mutex:
                    cur.connection.commit()

                last_write = time.time()
                n_buf = 0

        if mpool:
            self._stop_mpool(mpool)
            with self.mutex:
                n_add += len(self._flush_mpool(cur))

        with self.mutex:
            cur.connection.commit()

        return n_add

    def _spool_warks(
        self,
        cur: "sqlite3.Cursor",
        q: str,
        params: tuple[Any, ...],
        flt: int,
    ) -> tuple[tempfile.SpooledTemporaryFile[bytes], int]:
        """mutex me"""
        n = 0
        c2 = cur.connection.cursor()
        tf = tempfile.SpooledTemporaryFile(1024 * 1024 * 8, "w+b", prefix="cpp-tq-")
        with gzip.GzipFile(mode="wb", fileobj=tf) as gf:
            for row in cur.execute(q, params):
                if self.stop:
                    return tf, -1

                if flt == 1:
                    q = "select w from mt where w = ?"
                    if c2.execute(q, (row[0][:16],)).fetchone():
                        continue

                gf.write("{}\n".format("\x00".join(row)).encode("utf-8"))
                n += 1

        c2.close()
        tf.seek(0)
        self.spools.add(tf)
        return tf, n

    def _unspool(self, tf: tempfile.SpooledTemporaryFile[bytes]) -> None:
        try:
            self.spools.remove(tf)
        except:
            return

        try:
            tf.close()
        except Exception as ex:
            self.log("failed to delete spool: {}".format(ex), 3)

    def _flush_mpool(self, wcur: "sqlite3.Cursor") -> list[str]:
        ret = []
        for x in self.pending_tags:
            self._tag_file(wcur, *x)
            ret.append(x[1])

        self.pending_tags = []
        return ret

    def _run_all_mtp(self) -> None:
        gid = self.gid
        t0 = time.time()
        for ptop, flags in self.flags.items():
            if "mtp" in flags:
                if ptop not in self.entags:
                    t = "skipping mtp for unavailable volume {}"
                    self.log(t.format(ptop), 1)
                    continue
                self._run_one_mtp(ptop, gid)

        td = time.time() - t0
        msg = "mtp finished in {:.2f} sec ({})"
        self.log(msg.format(td, s2hms(td, True)))

        self.pp = None
        for k in list(self.volstate.keys()):
            if "OFFLINE" not in self.volstate[k]:
                self.volstate[k] = "online, idle"

        if self.args.exit == "idx":
            self.hub.sigterm()

    def _run_one_mtp(self, ptop: str, gid: int) -> None:
        if gid != self.gid:
            return

        entags = self.entags[ptop]

        parsers = {}
        for parser in self.flags[ptop]["mtp"]:
            try:
                parser = MParser(parser)
            except:
                self.log("invalid argument (could not find program): " + parser, 1)
                return

            for tag in entags:
                if tag in parser.tags:
                    parsers[parser.tag] = parser

        if self.args.mtag_vv:
            t = "parsers for {}: \033[0m{}"
            self.log(t.format(ptop, list(parsers.keys())), "90")

        self.mtp_parsers[ptop] = parsers

        q = "select count(w) from mt where k = 't:mtp'"
        with self.mutex:
            cur = self.cur[ptop]
            cur = cur.connection.cursor()
            wcur = cur.connection.cursor()
            n_left = cur.execute(q).fetchone()[0]

        mpool = self._start_mpool()
        batch_sz = mpool.maxsize * 3
        t_prev = time.time()
        n_prev = n_left
        n_done = 0
        to_delete = {}
        in_progress = {}
        while True:
            did_nothing = True
            with self.mutex:
                if gid != self.gid:
                    break

                q = "select w from mt where k = 't:mtp' limit ?"
                zq = cur.execute(q, (batch_sz,)).fetchall()
                warks = [str(x[0]) for x in zq]
                jobs = []
                for w in warks:
                    if w in in_progress:
                        continue

                    q = "select rd, fn, ip, at from up where substr(w,1,16)=? limit 1"
                    rd, fn, ip, at = cur.execute(q, (w,)).fetchone()
                    rd, fn = s3dec(rd, fn)
                    abspath = djoin(ptop, rd, fn)

                    q = "select k from mt where w = ?"
                    zq = cur.execute(q, (w,)).fetchall()
                    have: dict[str, Union[str, float]] = {x[0]: 1 for x in zq}

                    did_nothing = False
                    parsers = self._get_parsers(ptop, have, abspath)
                    if not parsers:
                        to_delete[w] = True
                        n_left -= 1
                        continue

                    if next((x for x in parsers.values() if x.pri), None):
                        q = "select k, v from mt where w = ?"
                        zq2 = cur.execute(q, (w,)).fetchall()
                        oth_tags = {str(k): v for k, v in zq2}
                    else:
                        oth_tags = {}

                    if ip:
                        oth_tags["up_ip"] = ip
                        oth_tags["up_at"] = at

                    jobs.append(Mpqe(parsers, set(), w, abspath, oth_tags))
                    in_progress[w] = True

            with self.mutex:
                done = self._flush_mpool(wcur)
                for w in done:
                    to_delete[w] = True
                    did_nothing = False
                    in_progress.pop(w)
                    n_done += 1

                for w in to_delete:
                    q = "delete from mt where w = ? and +k = 't:mtp'"
                    cur.execute(q, (w,))

                to_delete = {}

            if not warks:
                break

            if did_nothing:
                with self.tag_event:
                    self.tag_event.wait(0.2)

            if not jobs:
                continue

            try:
                now = time.time()
                s = ((now - t_prev) / (n_prev - n_left)) * n_left
                h, s = divmod(s, 3600)
                m, s = divmod(s, 60)
                n_prev = n_left
                t_prev = now
            except:
                h = 1
                m = 1

            msg = "mtp: {} done, {} left, eta {}h {:02d}m"
            with self.mutex:
                msg = msg.format(n_done, n_left, int(h), int(m))
                self.log(msg, c=6)

            for j in jobs:
                n_left -= 1
                mpool.put(j)

            with self.mutex:
                cur.connection.commit()

        self._stop_mpool(mpool)
        with self.mutex:
            done = self._flush_mpool(wcur)
            for w in done:
                q = "delete from mt where w = ? and +k = 't:mtp'"
                cur.execute(q, (w,))

            cur.connection.commit()
            if n_done:
                self.log("mtp: scanned {} files in {}".format(n_done, ptop), c=6)
                cur.execute("vacuum")

            wcur.close()
            cur.close()

    def _get_parsers(
        self, ptop: str, have: dict[str, Union[str, float]], abspath: str
    ) -> dict[str, MParser]:
        try:
            all_parsers = self.mtp_parsers[ptop]
        except:
            if self.args.mtag_vv:
                self.log("no mtp defined for {}".format(ptop), "90")
            return {}

        entags = self.entags[ptop]
        parsers = {}
        for k, v in all_parsers.items():
            if "ac" in entags or ".aq" in entags:
                if "ac" in have or ".aq" in have:
                    # is audio, require non-audio?
                    if v.audio == "n":
                        if self.args.mtag_vv:
                            t = "skip mtp {}; want no-audio, got audio"
                            self.log(t.format(k), "90")
                        continue
                # is not audio, require audio?
                elif v.audio == "y":
                    if self.args.mtag_vv:
                        t = "skip mtp {}; want audio, got no-audio"
                        self.log(t.format(k), "90")
                    continue

            if v.ext:
                match = False
                for ext in v.ext:
                    if abspath.lower().endswith("." + ext):
                        match = True
                        break

                if not match:
                    if self.args.mtag_vv:
                        t = "skip mtp {}; want file-ext {}, got {}"
                        self.log(t.format(k, v.ext, abspath.rsplit(".")[-1]), "90")
                    continue

            parsers[k] = v

        parsers = {k: v for k, v in parsers.items() if v.force or k not in have}
        return parsers

    def _start_mpool(self) -> Queue[Mpqe]:
        # mp.pool.ThreadPool and concurrent.futures.ThreadPoolExecutor
        # both do crazy runahead so lets reinvent another wheel
        nw = max(1, self.args.mtag_mt)
        assert self.mtag
        if not self.mpool_used:
            self.mpool_used = True
            self.log("using {}x {}".format(nw, self.mtag.backend))

        mpool: Queue[Mpqe] = Queue(nw)
        for _ in range(nw):
            Daemon(self._tag_thr, "up2k-mpool", (mpool,))

        return mpool

    def _stop_mpool(self, mpool: Queue[Mpqe]) -> None:
        if not mpool:
            return

        for _ in range(mpool.maxsize):
            mpool.put(Mpqe({}, set(), "", "", {}))

        mpool.join()

    def _tag_thr(self, q: Queue[Mpqe]) -> None:
        assert self.mtag
        while True:
            qe = q.get()
            if not qe.w:
                q.task_done()
                return

            try:
                if not qe.mtp:
                    if self.args.mtag_vv:
                        t = "tag-thr: {}({})"
                        self.log(t.format(self.mtag.backend, qe.abspath), "90")

                    tags = self.mtag.get(qe.abspath)
                else:
                    if self.args.mtag_vv:
                        t = "tag-thr: {}({})"
                        self.log(t.format(list(qe.mtp.keys()), qe.abspath), "90")

                    tags = self.mtag.get_bin(qe.mtp, qe.abspath, qe.oth_tags)
                    vtags = [
                        "\033[36m{} \033[33m{}".format(k, v) for k, v in tags.items()
                    ]
                    if vtags:
                        self.log("{}\033[0m [{}]".format(" ".join(vtags), qe.abspath))

                with self.mutex:
                    self.pending_tags.append((qe.entags, qe.w, qe.abspath, tags))
            except:
                ex = traceback.format_exc()
                self._log_tag_err(qe.mtp or self.mtag.backend, qe.abspath, ex)
            finally:
                if qe.mtp:
                    with self.tag_event:
                        self.tag_event.notify_all()

            q.task_done()

    def _log_tag_err(self, parser: Any, abspath: str, ex: Any) -> None:
        msg = "{} failed to read tags from {}:\n{}".format(parser, abspath, ex)
        self.log(msg.lstrip(), c=1 if "<Signals.SIG" in msg else 3)

    def _tagscan_file(
        self,
        write_cur: "sqlite3.Cursor",
        entags: set[str],
        wark: str,
        abspath: str,
        ip: str,
        at: float,
    ) -> int:
        """will mutex"""
        assert self.mtag

        if not bos.path.isfile(abspath):
            return 0

        try:
            tags = self.mtag.get(abspath)
        except Exception as ex:
            self._log_tag_err("", abspath, ex)
            return 0

        if ip:
            tags["up_ip"] = ip
            tags["up_at"] = at

        with self.mutex:
            return self._tag_file(write_cur, entags, wark, abspath, tags)

    def _tag_file(
        self,
        write_cur: "sqlite3.Cursor",
        entags: set[str],
        wark: str,
        abspath: str,
        tags: dict[str, Union[str, float]],
    ) -> int:
        """mutex me"""
        assert self.mtag

        if not bos.path.isfile(abspath):
            return 0

        if entags:
            tags = {k: v for k, v in tags.items() if k in entags}
            if not tags:
                # indicate scanned without tags
                tags = {"x": 0}

        if not tags:
            return 0

        for k in tags.keys():
            q = "delete from mt where w = ? and ({})".format(
                " or ".join(["+k = ?"] * len(tags))
            )
            args = [wark[:16]] + list(tags.keys())
            write_cur.execute(q, tuple(args))

        ret = 0
        for k, v in tags.items():
            q = "insert into mt values (?,?,?)"
            write_cur.execute(q, (wark[:16], k, v))
            ret += 1

        self._set_tagscan(write_cur, True)
        return ret

    def _trace(self, msg: str) -> None:
        self.log("ST: {}".format(msg))

    def _orz(self, db_path: str) -> "sqlite3.Cursor":
        c = sqlite3.connect(db_path, self.timeout, check_same_thread=False).cursor()
        # c.connection.set_trace_callback(self._trace)
        return c

    def _open_db(self, db_path: str) -> "sqlite3.Cursor":
        existed = bos.path.exists(db_path)
        cur = self._orz(db_path)
        ver = self._read_ver(cur)
        if not existed and ver is None:
            return self._create_db(db_path, cur)

        if ver == 4:
            try:
                t = "creating backup before upgrade: "
                cur = self._backup_db(db_path, cur, ver, t)
                self._upgrade_v4(cur)
                ver = 5
            except:
                self.log("WARN: failed to upgrade from v4", 3)

        if ver == DB_VER:
            try:
                self._add_cv_tab(cur)
                self._add_xiu_tab(cur)
                self._add_dhash_tab(cur)
            except:
                pass

            try:
                nfiles = next(cur.execute("select count(w) from up"))[0]
                self.log("  {} |{}|".format(db_path, nfiles), "90")
                return cur
            except:
                self.log("WARN: could not list files; DB corrupt?\n" + min_ex())

        if (ver or 0) > DB_VER:
            t = "database is version {}, this copyparty only supports versions <= {}"
            raise Exception(t.format(ver, DB_VER))

        msg = "creating new DB (old is bad); backup: "
        if ver:
            msg = "creating new DB (too old to upgrade); backup: "

        cur = self._backup_db(db_path, cur, ver, msg)
        db = cur.connection
        cur.close()
        db.close()
        bos.unlink(db_path)
        return self._create_db(db_path, None)

    def _backup_db(
        self, db_path: str, cur: "sqlite3.Cursor", ver: Optional[int], msg: str
    ) -> "sqlite3.Cursor":
        bak = "{}.bak.{:x}.v{}".format(db_path, int(time.time()), ver)
        self.log(msg + bak)
        try:
            c2 = sqlite3.connect(bak)
            with c2:
                cur.connection.backup(c2)
            return cur
        except:
            t = "native sqlite3 backup failed; using fallback method:\n"
            self.log(t + min_ex())
        finally:
            c2.close()

        db = cur.connection
        cur.close()
        db.close()

        shutil.copy2(fsenc(db_path), fsenc(bak))
        return self._orz(db_path)

    def _read_ver(self, cur: "sqlite3.Cursor") -> Optional[int]:
        for tab in ["ki", "kv"]:
            try:
                c = cur.execute(r"select v from {} where k = 'sver'".format(tab))
            except:
                continue

            rows = c.fetchall()
            if rows:
                return int(rows[0][0])
        return None

    def _create_db(
        self, db_path: str, cur: Optional["sqlite3.Cursor"]
    ) -> "sqlite3.Cursor":
        """
        collision in 2^(n/2) files where n = bits (6 bits/ch)
          10*6/2 = 2^30 =       1'073'741'824, 24.1mb idx  1<<(3*10)
          12*6/2 = 2^36 =      68'719'476'736, 24.8mb idx
          16*6/2 = 2^48 = 281'474'976'710'656, 26.1mb idx
        """
        if not cur:
            cur = self._orz(db_path)

        idx = r"create index up_w on up(substr(w,1,16))"
        if self.no_expr_idx:
            idx = r"create index up_w on up(w)"

        for cmd in [
            r"create table up (w text, mt int, sz int, rd text, fn text, ip text, at int)",
            r"create index up_rd on up(rd)",
            r"create index up_fn on up(fn)",
            r"create index up_ip on up(ip)",
            idx,
            r"create table mt (w text, k text, v int)",
            r"create index mt_w on mt(w)",
            r"create index mt_k on mt(k)",
            r"create index mt_v on mt(v)",
            r"create table kv (k text, v int)",
            r"insert into kv values ('sver', {})".format(DB_VER),
        ]:
            cur.execute(cmd)

        self._add_dhash_tab(cur)
        self._add_xiu_tab(cur)
        self._add_cv_tab(cur)
        self.log("created DB at {}".format(db_path))
        return cur

    def _upgrade_v4(self, cur: "sqlite3.Cursor") -> None:
        for cmd in [
            r"alter table up add column ip text",
            r"alter table up add column at int",
            r"create index up_ip on up(ip)",
            r"update kv set v=5 where k='sver'",
        ]:
            cur.execute(cmd)

        cur.connection.commit()

    def _add_dhash_tab(self, cur: "sqlite3.Cursor") -> None:
        # v5 -> v5a
        for cmd in [
            r"create table dh (d text, h text)",
            r"create index dh_d on dh(d)",
            r"insert into kv values ('tagscan',1)",
        ]:
            cur.execute(cmd)

        cur.connection.commit()

    def _add_xiu_tab(self, cur: "sqlite3.Cursor") -> None:
        # v5a -> v5b
        # store rd+fn rather than warks to support nohash vols
        try:
            cur.execute("select ws, rd, fn from iu limit 1").fetchone()
            return
        except:
            pass

        try:
            cur.execute("drop table iu")
        except:
            pass

        for cmd in [
            r"create table iu (c int, w text, rd text, fn text)",
            r"create index iu_c on iu(c)",
            r"create index iu_w on iu(w)",
        ]:
            cur.execute(cmd)

        cur.connection.commit()

    def _add_cv_tab(self, cur: "sqlite3.Cursor") -> None:
        # v5b -> v5c
        try:
            cur.execute("select rd, dn, fn from cv limit 1").fetchone()
            return
        except:
            pass

        for cmd in [
            r"create table cv (rd text, dn text, fn text)",
            r"create index cv_i on cv(rd, dn)",
        ]:
            cur.execute(cmd)

        try:
            cur.execute("delete from dh")
        except:
            pass

        cur.connection.commit()

    def _job_volchk(self, cj: dict[str, Any]) -> None:
        if not self.register_vpath(cj["ptop"], cj["vcfg"]):
            if cj["ptop"] not in self.registry:
                raise Pebkac(410, "location unavailable")

    def handle_json(self, cj: dict[str, Any], busy_aps: set[str]) -> dict[str, Any]:
        self.busy_aps = busy_aps
        try:
            # bit expensive; 3.9=10x 3.11=2x
            if self.mutex.acquire(timeout=10):
                self._job_volchk(cj)
                self.mutex.release()
            else:
                t = "cannot receive uploads right now;\nserver busy with {}.\nPlease wait; the client will retry..."
                raise Pebkac(503, t.format(self.blocked or "[unknown]"))
        except TypeError:
            # py2
            with self.mutex:
                self._job_volchk(cj)

        ptop = cj["ptop"]
        cj["name"] = sanitize_fn(cj["name"], "", [".prologue.html", ".epilogue.html"])
        cj["poke"] = now = self.db_act = self.vol_act[ptop] = time.time()
        wark = self._get_wark(cj)
        job = None
        pdir = djoin(ptop, cj["prel"])
        try:
            dev = bos.stat(pdir).st_dev
        except:
            dev = 0

        # check if filesystem supports sparse files;
        # refuse out-of-order / multithreaded uploading if sprs False
        sprs = self.fstab.get(pdir) != "ng"

        with self.mutex:
            jcur = self.cur.get(ptop)
            reg = self.registry[ptop]
            vfs = self.asrv.vfs.all_vols[cj["vtop"]]
            n4g = vfs.flags.get("noforget")
            rand = vfs.flags.get("rand") or cj.get("rand")
            lost: list[tuple["sqlite3.Cursor", str, str]] = []

            vols = [(ptop, jcur)] if jcur else []
            if vfs.flags.get("xlink"):
                vols += [(k, v) for k, v in self.cur.items() if k != ptop]
            if vfs.flags.get("up_ts", "") == "fu" or not cj["lmod"]:
                # force upload time rather than last-modified
                cj["lmod"] = int(time.time())

            alts: list[tuple[int, int, dict[str, Any]]] = []
            for ptop, cur in vols:
                allv = self.asrv.vfs.all_vols
                cvfs = next((v for v in allv.values() if v.realpath == ptop), vfs)
                vtop = cj["vtop"] if cur == jcur else cvfs.vpath

                if self.no_expr_idx:
                    q = r"select * from up where w = ?"
                    argv = [wark]
                else:
                    q = r"select * from up where substr(w,1,16)=? and +w=?"
                    argv = [wark[:16], wark]

                c2 = cur.execute(q, tuple(argv))
                for _, dtime, dsize, dp_dir, dp_fn, ip, at in c2:
                    if dp_dir.startswith("//") or dp_fn.startswith("//"):
                        dp_dir, dp_fn = s3dec(dp_dir, dp_fn)

                    dp_abs = djoin(ptop, dp_dir, dp_fn)
                    try:
                        st = bos.stat(dp_abs)
                        if stat.S_ISLNK(st.st_mode):
                            # broken symlink
                            raise Exception()
                    except:
                        if n4g:
                            st = os.stat_result((0, -1, -1, 0, 0, 0, 0, 0, 0, 0))
                        else:
                            lost.append((cur, dp_dir, dp_fn))
                            continue

                    j = {
                        "name": dp_fn,
                        "prel": dp_dir,
                        "vtop": vtop,
                        "ptop": ptop,
                        "sprs": sprs,  # dontcare; finished anyways
                        "size": dsize,
                        "lmod": dtime,
                        "host": cj["host"],
                        "user": cj["user"],
                        "addr": ip,
                        "at": at,
                        "hash": [],
                        "need": [],
                        "busy": {},
                    }
                    for k in ["life"]:
                        if k in cj:
                            j[k] = cj[k]

                    score = (
                        (3 if st.st_dev == dev else 0)
                        + (2 if dp_dir == cj["prel"] else 0)
                        + (1 if dp_fn == cj["name"] else 0)
                    )
                    alts.append((score, -len(alts), j))

            if alts:
                best = sorted(alts, reverse=True)[0]
                job = best[2]
            else:
                job = None

            if job and wark in reg:
                # self.log("pop " + wark + "  " + job["name"] + " handle_json db", 4)
                del reg[wark]

            if lost:
                c2 = None
                for cur, dp_dir, dp_fn in lost:
                    t = "forgetting deleted file: /{}"
                    self.log(t.format(vjoin(vjoin(vfs.vpath, dp_dir), dp_fn)))
                    self.db_rm(cur, dp_dir, dp_fn, cj["size"])
                    if c2 and c2 != cur:
                        c2.connection.commit()

                    c2 = cur

                assert c2
                c2.connection.commit()

            cur = jcur
            ptop = None  # use cj or job as appropriate

            if not job and wark in reg:
                # ensure the files haven't been deleted manually
                rj = reg[wark]
                names = [rj[x] for x in ["name", "tnam"] if x in rj]
                for fn in names:
                    path = djoin(rj["ptop"], rj["prel"], fn)
                    try:
                        if bos.path.getsize(path) > 0 or not rj["need"]:
                            # upload completed or both present
                            break
                    except:
                        # missing; restart
                        if not self.args.nw and not n4g:
                            t = "forgetting deleted partial upload at {}"
                            self.log(t.format(path))
                            del reg[wark]
                        break

            if job or wark in reg:
                job = job or reg[wark]
                if (
                    job["ptop"] != cj["ptop"]
                    or job["prel"] != cj["prel"]
                    or job["name"] != cj["name"]
                ):
                    # file contents match, but not the path
                    src = djoin(job["ptop"], job["prel"], job["name"])
                    dst = djoin(cj["ptop"], cj["prel"], cj["name"])
                    vsrc = djoin(job["vtop"], job["prel"], job["name"])
                    vsrc = vsrc.replace("\\", "/")  # just for prints anyways
                    if job["need"]:
                        self.log("unfinished:\n  {0}\n  {1}".format(src, dst))
                        err = "partial upload exists at a different location; please resume uploading here instead:\n"
                        err += "/" + quotep(vsrc) + " "

                        # registry is size-constrained + can only contain one unique wark;
                        # let want_recheck trigger symlink (if still in reg) or reupload
                        if cur:
                            dupe = (cj["prel"], cj["name"], cj["lmod"])
                            try:
                                self.dupesched[src].append(dupe)
                            except:
                                self.dupesched[src] = [dupe]

                        raise Pebkac(422, err)

                    elif "nodupe" in vfs.flags:
                        self.log("dupe-reject:\n  {0}\n  {1}".format(src, dst))
                        err = "upload rejected, file already exists:\n"
                        err += "/" + quotep(vsrc) + " "
                        raise Pebkac(409, err)
                    else:
                        # symlink to the client-provided name,
                        # returning the previous upload info
                        psrc = src + ".PARTIAL"
                        if self.args.dotpart:
                            m = re.match(r"(.*[\\/])(.*)", psrc)
                            if m:  # always true but...
                                zs1, zs2 = m.groups()
                                psrc = zs1 + "." + zs2

                        if (
                            src in self.busy_aps
                            or psrc in self.busy_aps
                            or (wark in reg and "done" not in reg[wark])
                        ):
                            raise Pebkac(
                                422, "source file busy; please try again later"
                            )

                        job = deepcopy(job)
                        job["wark"] = wark
                        job["at"] = cj.get("at") or time.time()
                        for k in "lmod ptop vtop prel host user addr".split():
                            job[k] = cj.get(k) or ""

                        pdir = djoin(cj["ptop"], cj["prel"])
                        if rand:
                            job["name"] = rand_name(
                                pdir, cj["name"], vfs.flags["nrand"]
                            )
                        else:
                            job["name"] = self._untaken(pdir, cj, now)

                        dst = djoin(job["ptop"], job["prel"], job["name"])
                        xbu = vfs.flags.get("xbu")
                        if xbu and not runhook(
                            self.log,
                            xbu,  # type: ignore
                            dst,
                            job["vtop"],
                            job["host"],
                            job["user"],
                            job["lmod"],
                            job["size"],
                            job["addr"],
                            job["at"],
                            "",
                        ):
                            t = "upload blocked by xbu server config: {}".format(dst)
                            self.log(t, 1)
                            raise Pebkac(403, t)

                        if not self.args.nw:
                            try:
                                dvf = self.flags[job["ptop"]]
                                self._symlink(src, dst, dvf, lmod=cj["lmod"], rm=True)
                            except:
                                if bos.path.exists(dst):
                                    bos.unlink(dst)
                                if not n4g:
                                    raise

                        if cur and not self.args.nw:
                            zs = "prel name lmod size ptop vtop wark host user addr at"
                            a = [job[x] for x in zs.split()]
                            self.db_add(cur, vfs.flags, *a)
                            cur.connection.commit()

            if not job:
                ap1 = djoin(cj["ptop"], cj["prel"])
                if rand:
                    cj["name"] = rand_name(ap1, cj["name"], vfs.flags["nrand"])

                if vfs.lim:
                    ap2, cj["prel"] = vfs.lim.all(
                        cj["addr"],
                        cj["prel"],
                        cj["size"],
                        cj["ptop"],
                        ap1,
                        self.hub.broker,
                        reg,
                        "up2k._get_volsize",
                    )
                    bos.makedirs(ap2)
                    vfs.lim.nup(cj["addr"])
                    vfs.lim.bup(cj["addr"], cj["size"])

                job = {
                    "wark": wark,
                    "t0": now,
                    "sprs": sprs,
                    "hash": deepcopy(cj["hash"]),
                    "need": [],
                    "busy": {},
                }
                # client-provided, sanitized by _get_wark: name, size, lmod
                for k in [
                    "host",
                    "user",
                    "addr",
                    "vtop",
                    "ptop",
                    "prel",
                    "name",
                    "size",
                    "lmod",
                    "poke",
                ]:
                    job[k] = cj[k]

                for k in ["life", "replace"]:
                    if k in cj:
                        job[k] = cj[k]

                # one chunk may occur multiple times in a file;
                # filter to unique values for the list of missing chunks
                # (preserve order to reduce disk thrashing)
                lut = {}
                for k in cj["hash"]:
                    if k not in lut:
                        job["need"].append(k)
                        lut[k] = 1

                try:
                    self._new_upload(job)
                except:
                    self.registry[job["ptop"]].pop(job["wark"], None)
                    raise

            purl = "{}/{}".format(job["vtop"], job["prel"]).strip("/")
            purl = "/{}/".format(purl) if purl else "/"

            ret = {
                "name": job["name"],
                "purl": purl,
                "size": job["size"],
                "lmod": job["lmod"],
                "sprs": job.get("sprs", sprs),
                "hash": job["need"],
                "wark": wark,
            }

            if (
                not ret["hash"]
                and "fk" in vfs.flags
                and not self.args.nw
                and (cj["user"] in vfs.axs.uread or cj["user"] in vfs.axs.upget)
            ):
                alg = 2 if "fka" in vfs.flags else 1
                ap = absreal(djoin(job["ptop"], job["prel"], job["name"]))
                ino = 0 if ANYWIN else bos.stat(ap).st_ino
                fk = self.gen_fk(alg, self.args.fk_salt, ap, job["size"], ino)
                ret["fk"] = fk[: vfs.flags["fk"]]

            return ret

    def _untaken(self, fdir: str, job: dict[str, Any], ts: float) -> str:
        fname = job["name"]
        ip = job["addr"]

        if self.args.nw:
            return fname

        fp = djoin(fdir, fname)
        if job.get("replace") and bos.path.exists(fp):
            self.log("replacing existing file at {}".format(fp))
            bos.unlink(fp)

        if self.args.plain_ip:
            dip = ip.replace(":", ".")
        else:
            dip = self.hub.iphash.s(ip)

        suffix = "-{:.6f}-{}".format(ts, dip)
        with ren_open(fname, "wb", fdir=fdir, suffix=suffix) as zfw:
            return zfw["orz"][1]

    def _symlink(
        self,
        src: str,
        dst: str,
        flags: dict[str, Any],
        verbose: bool = True,
        rm: bool = False,
        lmod: float = 0,
    ) -> None:
        if verbose:
            self.log("linking dupe:\n  {0}\n  {1}".format(src, dst))

        if self.args.nw:
            return

        linked = False
        try:
            if "copydupes" in flags:
                raise Exception("disabled in config")

            lsrc = src
            ldst = dst
            fs1 = bos.stat(os.path.dirname(src)).st_dev
            fs2 = bos.stat(os.path.dirname(dst)).st_dev
            if fs1 == 0 or fs2 == 0:
                # py2 on winxp or other unsupported combination
                raise OSError(errno.ENOSYS, "filesystem does not have st_dev")
            elif fs1 == fs2:
                # same fs; make symlink as relative as possible
                spl = r"[\\/]" if WINDOWS else "/"
                nsrc = re.split(spl, src)
                ndst = re.split(spl, dst)
                nc = 0
                for a, b in zip(nsrc, ndst):
                    if a != b:
                        break
                    nc += 1
                if nc > 1:
                    zsl = nsrc[nc:]
                    hops = len(ndst[nc:]) - 1
                    lsrc = "../" * hops + "/".join(zsl)

            if WINDOWS:
                lsrc = lsrc.replace("/", "\\")
                ldst = ldst.replace("/", "\\")

            if rm and bos.path.exists(dst):
                bos.unlink(dst)

            try:
                if "hardlink" in flags:
                    os.link(fsenc(absreal(src)), fsenc(dst))
                    linked = True
            except Exception as ex:
                self.log("cannot hardlink: " + repr(ex))
                if "neversymlink" in flags:
                    raise Exception("symlink-fallback disabled in cfg")

            if not linked:
                os.symlink(fsenc(lsrc), fsenc(ldst))
                linked = True
        except Exception as ex:
            self.log("cannot link; creating copy: " + repr(ex))
            shutil.copy2(fsenc(src), fsenc(dst))

        if lmod and (not linked or SYMTIME):
            times = (int(time.time()), int(lmod))
            bos.utime(dst, times, False)

    def handle_chunk(
        self, ptop: str, wark: str, chash: str
    ) -> tuple[int, list[int], str, float, bool]:
        with self.mutex:
            self.db_act = self.vol_act[ptop] = time.time()
            job = self.registry[ptop].get(wark)
            if not job:
                known = " ".join([x for x in self.registry[ptop].keys()])
                self.log("unknown wark [{}], known: {}".format(wark, known))
                raise Pebkac(400, "unknown wark" + SSEELOG)

            if chash not in job["need"]:
                msg = "chash = {} , need:\n".format(chash)
                msg += "\n".join(job["need"])
                self.log(msg)
                raise Pebkac(400, "already got that but thanks??")

            nchunk = [n for n, v in enumerate(job["hash"]) if v == chash]
            if not nchunk:
                raise Pebkac(400, "unknown chunk")

            if chash in job["busy"]:
                nh = len(job["hash"])
                idx = job["hash"].index(chash)
                t = "that chunk is already being written to:\n  {}\n  {} {}/{}\n  {}"
                raise Pebkac(400, t.format(wark, chash, idx, nh, job["name"]))

            path = djoin(job["ptop"], job["prel"], job["tnam"])

            chunksize = up2k_chunksize(job["size"])
            ofs = [chunksize * x for x in nchunk]

            if not job["sprs"]:
                cur_sz = bos.path.getsize(path)
                if ofs[0] > cur_sz:
                    t = "please upload sequentially using one thread;\nserver filesystem does not support sparse files.\n  file: {}\n  chunk: {}\n  cofs: {}\n  flen: {}"
                    t = t.format(job["name"], nchunk[0], ofs[0], cur_sz)
                    raise Pebkac(400, t)

            job["busy"][chash] = 1

        job["poke"] = time.time()

        return chunksize, ofs, path, job["lmod"], job["sprs"]

    def release_chunk(self, ptop: str, wark: str, chash: str) -> bool:
        with self.mutex:
            job = self.registry[ptop].get(wark)
            if job:
                job["busy"].pop(chash, None)

        return True

    def confirm_chunk(self, ptop: str, wark: str, chash: str) -> tuple[int, str]:
        with self.mutex:
            self.db_act = self.vol_act[ptop] = time.time()
            try:
                job = self.registry[ptop][wark]
                pdir = djoin(job["ptop"], job["prel"])
                src = djoin(pdir, job["tnam"])
                dst = djoin(pdir, job["name"])
            except Exception as ex:
                return "confirm_chunk, wark, " + repr(ex)  # type: ignore

            job["busy"].pop(chash, None)

            try:
                job["need"].remove(chash)
            except Exception as ex:
                return "confirm_chunk, chash, " + repr(ex)  # type: ignore

            ret = len(job["need"])
            if ret > 0:
                return ret, src

            if self.args.nw:
                self.regdrop(ptop, wark)
                return ret, dst

        return ret, dst

    def finish_upload(self, ptop: str, wark: str, busy_aps: set[str]) -> None:
        self.busy_aps = busy_aps
        with self.mutex:
            self._finish_upload(ptop, wark)

    def _finish_upload(self, ptop: str, wark: str) -> None:
        try:
            job = self.registry[ptop][wark]
            pdir = djoin(job["ptop"], job["prel"])
            src = djoin(pdir, job["tnam"])
            dst = djoin(pdir, job["name"])
        except Exception as ex:
            raise Pebkac(500, "finish_upload, wark, " + repr(ex))

        if job["need"]:
            t = "finish_upload {} with remaining chunks {}"
            raise Pebkac(500, t.format(wark, job["need"]))

        # self.log("--- " + wark + "  " + dst + " finish_upload atomic " + dst, 4)
        atomic_move(src, dst)

        upt = job.get("at") or time.time()
        vflags = self.flags[ptop]

        times = (int(time.time()), int(job["lmod"]))
        self.log(
            "no more chunks, setting times {} ({}) on {}".format(
                times, bos.path.getsize(dst), dst
            )
        )
        try:
            bos.utime(dst, times)
        except:
            self.log("failed to utime ({}, {})".format(dst, times))

        zs = "prel name lmod size ptop vtop wark host user addr"
        z2 = [job[x] for x in zs.split()]
        wake_sr = False
        try:
            flt = job["life"]
            vfs = self.asrv.vfs.all_vols[job["vtop"]]
            vlt = vfs.flags["lifetime"]
            if vlt and flt > 1 and flt < vlt:
                upt -= vlt - flt
                wake_sr = True
                t = "using client lifetime; at={:.0f} ({}-{})"
                self.log(t.format(upt, vlt, flt))
        except:
            pass

        z2 += [upt]
        if self.idx_wark(vflags, *z2):
            del self.registry[ptop][wark]
        else:
            self.registry[ptop][wark]["done"] = 1
            self.regdrop(ptop, wark)

        if wake_sr:
            with self.rescan_cond:
                self.rescan_cond.notify_all()

        dupes = self.dupesched.pop(dst, [])
        if not dupes:
            return

        cur = self.cur.get(ptop)
        for rd, fn, lmod in dupes:
            d2 = djoin(ptop, rd, fn)
            if os.path.exists(d2):
                continue

            self._symlink(dst, d2, self.flags[ptop], lmod=lmod)
            if cur:
                self.db_rm(cur, rd, fn, job["size"])
                self.db_add(cur, vflags, rd, fn, lmod, *z2[3:])

        if cur:
            cur.connection.commit()

    def regdrop(self, ptop: str, wark: str) -> None:
        olds = self.droppable[ptop]
        if wark:
            olds.append(wark)

        if len(olds) <= self.args.reg_cap:
            return

        n = len(olds) - int(self.args.reg_cap / 2)
        t = "up2k-registry [{}] has {} droppables; discarding {}"
        self.log(t.format(ptop, len(olds), n))
        for k in olds[:n]:
            self.registry[ptop].pop(k, None)
        self.droppable[ptop] = olds[n:]

    def idx_wark(
        self,
        vflags: dict[str, Any],
        rd: str,
        fn: str,
        lmod: float,
        sz: int,
        ptop: str,
        vtop: str,
        wark: str,
        host: str,
        usr: str,
        ip: str,
        at: float,
        skip_xau: bool = False,
    ) -> bool:
        cur = self.cur.get(ptop)
        if not cur:
            return False

        self.db_act = self.vol_act[ptop] = time.time()
        try:
            self.db_rm(cur, rd, fn, sz)
            self.db_add(
                cur,
                vflags,
                rd,
                fn,
                lmod,
                sz,
                ptop,
                vtop,
                wark,
                host,
                usr,
                ip,
                at,
                skip_xau,
            )
            cur.connection.commit()
        except Exception as ex:
            x = self.register_vpath(ptop, {})
            assert x
            db_ex_chk(self.log, ex, x[1])
            raise

        if "e2t" in self.flags[ptop]:
            self.tagq.put((ptop, wark, rd, fn, ip, at))
            self.n_tagq += 1

        return True

    def db_rm(self, db: "sqlite3.Cursor", rd: str, fn: str, sz: int) -> None:
        sql = "delete from up where rd = ? and fn = ?"
        try:
            r = db.execute(sql, (rd, fn))
        except:
            assert self.mem_cur
            r = db.execute(sql, s3enc(self.mem_cur, rd, fn))

        if r.rowcount:
            self.volsize[db] -= sz
            self.volnfiles[db] -= 1

    def db_add(
        self,
        db: "sqlite3.Cursor",
        vflags: dict[str, Any],
        rd: str,
        fn: str,
        ts: float,
        sz: int,
        ptop: str,
        vtop: str,
        wark: str,
        host: str,
        usr: str,
        ip: str,
        at: float,
        skip_xau: bool = False,
    ) -> None:
        sql = "insert into up values (?,?,?,?,?,?,?)"
        v = (wark, int(ts), sz, rd, fn, ip or "", int(at or 0))
        try:
            db.execute(sql, v)
        except:
            assert self.mem_cur
            rd, fn = s3enc(self.mem_cur, rd, fn)
            v = (wark, int(ts), sz, rd, fn, ip or "", int(at or 0))
            db.execute(sql, v)

        self.volsize[db] += sz
        self.volnfiles[db] += 1

        xau = False if skip_xau else vflags.get("xau")
        dst = djoin(ptop, rd, fn)
        if xau and not runhook(
            self.log,
            xau,
            dst,
            djoin(vtop, rd, fn),
            host,
            usr,
            int(ts),
            sz,
            ip,
            at or time.time(),
            "",
        ):
            t = "upload blocked by xau server config"
            self.log(t, 1)
            bos.unlink(dst)
            self.registry[ptop].pop(wark, None)
            raise Pebkac(403, t)

        xiu = vflags.get("xiu")
        if xiu:
            cds: set[int] = set()
            for cmd in xiu:
                m = self.xiu_ptn.search(cmd)
                cds.add(int(m.group(1)) if m else 5)

            q = "insert into iu values (?,?,?,?)"
            for cd in cds:
                # one for each unique cooldown duration
                try:
                    db.execute(q, (cd, wark[:16], rd, fn))
                except:
                    assert self.mem_cur
                    rd, fn = s3enc(self.mem_cur, rd, fn)
                    db.execute(q, (cd, wark[:16], rd, fn))

            if self.xiu_asleep:
                self.xiu_asleep = False
                with self.rescan_cond:
                    self.rescan_cond.notify_all()

        if rd and sz and fn.lower() in self.args.th_covers:
            # wasteful; db_add will re-index actual covers
            # but that won't catch existing files
            crd, cdn = rd.rsplit("/", 1) if "/" in rd else ("", rd)
            try:
                db.execute("delete from cv where rd=? and dn=?", (crd, cdn))
                db.execute("insert into cv values (?,?,?)", (crd, cdn, fn))
            except:
                pass

    def handle_rm(
        self, uname: str, ip: str, vpaths: list[str], lim: list[int], rm_up: bool
    ) -> str:
        n_files = 0
        ok = {}
        ng = {}
        for vp in vpaths:
            if lim and lim[0] <= 0:
                self.log("hit delete limit of {} files".format(lim[1]), 3)
                break

            a, b, c = self._handle_rm(uname, ip, vp, lim, rm_up)
            n_files += a
            for k in b:
                ok[k] = 1
            for k in c:
                ng[k] = 1

        ng = {k: 1 for k in ng if k not in ok}
        iok = len(ok)
        ing = len(ng)

        return "deleted {} files (and {}/{} folders)".format(n_files, iok, iok + ing)

    def _handle_rm(
        self, uname: str, ip: str, vpath: str, lim: list[int], rm_up: bool
    ) -> tuple[int, list[str], list[str]]:
        self.db_act = time.time()
        try:
            permsets = [[True, False, False, True]]
            vn, rem = self.asrv.vfs.get(vpath, uname, *permsets[0])
            vn, rem = vn.get_dbv(rem)
            unpost = False
        except:
            # unpost with missing permissions? verify with db
            if not self.args.unpost:
                raise Pebkac(400, "the unpost feature is disabled in server config")

            unpost = True
            permsets = [[False, True]]
            vn, rem = self.asrv.vfs.get(vpath, uname, *permsets[0])
            vn, rem = vn.get_dbv(rem)
            with self.mutex:
                _, _, _, _, dip, dat = self._find_from_vpath(vn.realpath, rem)

            t = "you cannot delete this: "
            if not dip:
                t += "file not found"
            elif dip != ip:
                t += "not uploaded by (You)"
            elif dat < time.time() - self.args.unpost:
                t += "uploaded too long ago"
            else:
                t = ""

            if t:
                raise Pebkac(400, t)

        ptop = vn.realpath
        atop = vn.canonical(rem, False)
        self.vol_act[ptop] = self.db_act
        adir, fn = os.path.split(atop)
        try:
            st = bos.lstat(atop)
            is_dir = stat.S_ISDIR(st.st_mode)
        except:
            raise Pebkac(400, "file not found on disk (already deleted?)")

        scandir = not self.args.no_scandir
        if is_dir:
            g = vn.walk("", rem, [], uname, permsets, True, scandir, True)
            if unpost:
                raise Pebkac(400, "cannot unpost folders")
        elif stat.S_ISLNK(st.st_mode) or stat.S_ISREG(st.st_mode):
            dbv, vrem = self.asrv.vfs.get(vpath, uname, *permsets[0])
            dbv, vrem = dbv.get_dbv(vrem)
            voldir = vsplit(vrem)[0]
            vpath_dir = vsplit(vpath)[0]
            g = [(dbv, voldir, vpath_dir, adir, [(fn, 0)], [], {})]  # type: ignore
        else:
            self.log("rm: skip type-{:x} file [{}]".format(st.st_mode, atop))
            return 0, [], []

        xbd = vn.flags.get("xbd")
        xad = vn.flags.get("xad")
        n_files = 0
        for dbv, vrem, _, adir, files, rd, vd in g:
            for fn in [x[0] for x in files]:
                if lim:
                    lim[0] -= 1
                    if lim[0] < 0:
                        self.log("hit delete limit of {} files".format(lim[1]), 3)
                        break

                abspath = djoin(adir, fn)
                st = bos.stat(abspath)
                volpath = "{}/{}".format(vrem, fn).strip("/")
                vpath = "{}/{}".format(dbv.vpath, volpath).strip("/")
                self.log("rm {}\n  {}".format(vpath, abspath))
                _ = dbv.get(volpath, uname, *permsets[0])
                if xbd:
                    if not runhook(
                        self.log,
                        xbd,
                        abspath,
                        vpath,
                        "",
                        uname,
                        st.st_mtime,
                        st.st_size,
                        ip,
                        0,
                        "",
                    ):
                        t = "delete blocked by xbd server config: {}"
                        self.log(t.format(abspath), 1)
                        continue

                n_files += 1
                with self.mutex:
                    cur = None
                    try:
                        ptop = dbv.realpath
                        cur, wark, _, _, _, _ = self._find_from_vpath(ptop, volpath)
                        self._forget_file(ptop, volpath, cur, wark, True, st.st_size)
                    finally:
                        if cur:
                            cur.connection.commit()

                bos.unlink(abspath)
                if xad:
                    runhook(
                        self.log,
                        xad,
                        abspath,
                        vpath,
                        "",
                        uname,
                        st.st_mtime,
                        st.st_size,
                        ip,
                        0,
                        "",
                    )

        if is_dir:
            ok, ng = rmdirs(self.log_func, scandir, True, atop, 1)
        else:
            ok = ng = []

        if rm_up:
            ok2, ng2 = rmdirs_up(os.path.dirname(atop), ptop)
        else:
            ok2 = ng2 = []

        return n_files, ok + ok2, ng + ng2

    def handle_mv(self, uname: str, svp: str, dvp: str) -> str:
        if svp == dvp or dvp.startswith(svp + "/"):
            raise Pebkac(400, "mv: cannot move parent into subfolder")

        svn, srem = self.asrv.vfs.get(svp, uname, True, False, True)
        svn, srem = svn.get_dbv(srem)
        sabs = svn.canonical(srem, False)
        curs: set["sqlite3.Cursor"] = set()
        self.db_act = self.vol_act[svn.realpath] = time.time()

        if not srem:
            raise Pebkac(400, "mv: cannot move a mountpoint")

        st = bos.lstat(sabs)
        if stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
            with self.mutex:
                try:
                    ret = self._mv_file(uname, svp, dvp, curs)
                finally:
                    for v in curs:
                        v.connection.commit()

                return ret

        jail = svn.get_dbv(srem)[0]
        permsets = [[True, False, True]]
        scandir = not self.args.no_scandir

        # following symlinks is too scary
        g = svn.walk("", srem, [], uname, permsets, True, scandir, True)
        for dbv, vrem, _, atop, files, rd, vd in g:
            if dbv != jail:
                # fail early (prevent partial moves)
                raise Pebkac(400, "mv: source folder contains other volumes")

        g = svn.walk("", srem, [], uname, permsets, True, scandir, True)
        for dbv, vrem, _, atop, files, rd, vd in g:
            if dbv != jail:
                # the actual check (avoid toctou)
                raise Pebkac(400, "mv: source folder contains other volumes")

            with self.mutex:
                try:
                    for fn in files:
                        self.db_act = self.vol_act[dbv.realpath] = time.time()
                        svpf = "/".join(x for x in [dbv.vpath, vrem, fn[0]] if x)
                        if not svpf.startswith(svp + "/"):  # assert
                            raise Pebkac(500, "mv: bug at {}, top {}".format(svpf, svp))

                        dvpf = dvp + svpf[len(svp) :]
                        self._mv_file(uname, svpf, dvpf, curs)
                finally:
                    for v in curs:
                        v.connection.commit()

            curs.clear()

        rm_ok, rm_ng = rmdirs(self.log_func, scandir, True, sabs, 1)

        for zsl in (rm_ok, rm_ng):
            for ap in reversed(zsl):
                if not ap.startswith(sabs):
                    raise Pebkac(500, "mv_d: bug at {}, top {}".format(ap, sabs))

                rem = ap[len(sabs) :].replace(os.sep, "/").lstrip("/")
                vp = vjoin(dvp, rem)
                try:
                    dvn, drem = self.asrv.vfs.get(vp, uname, False, True)
                    bos.mkdir(dvn.canonical(drem))
                except:
                    pass

        return "k"

    def _mv_file(
        self, uname: str, svp: str, dvp: str, curs: set["sqlite3.Cursor"]
    ) -> str:
        svn, srem = self.asrv.vfs.get(svp, uname, True, False, True)
        svn, srem = svn.get_dbv(srem)

        dvn, drem = self.asrv.vfs.get(dvp, uname, False, True)
        dvn, drem = dvn.get_dbv(drem)

        sabs = svn.canonical(srem, False)
        dabs = dvn.canonical(drem)
        drd, dfn = vsplit(drem)

        n1 = svp.split("/")[-1]
        n2 = dvp.split("/")[-1]
        if n1.startswith(".") or n2.startswith("."):
            if self.args.no_dot_mv:
                raise Pebkac(400, "moving dotfiles is disabled in server config")
            elif self.args.no_dot_ren and n1 != n2:
                raise Pebkac(400, "renaming dotfiles is disabled in server config")

        if bos.path.exists(dabs):
            raise Pebkac(400, "mv2: target file exists")

        stl = bos.lstat(sabs)
        try:
            st = bos.stat(sabs)
        except:
            st = stl

        xbr = svn.flags.get("xbr")
        xar = dvn.flags.get("xar")
        if xbr:
            if not runhook(
                self.log, xbr, sabs, svp, "", uname, st.st_mtime, st.st_size, "", 0, ""
            ):
                t = "move blocked by xbr server config: {}".format(svp)
                self.log(t, 1)
                raise Pebkac(405, t)

        is_xvol = svn.realpath != dvn.realpath
        if stat.S_ISLNK(stl.st_mode):
            is_dirlink = stat.S_ISDIR(st.st_mode)
            is_link = True
        else:
            is_link = is_dirlink = False

        bos.makedirs(os.path.dirname(dabs))

        if is_dirlink:
            dlabs = absreal(sabs)
            t = "moving symlink from [{}] to [{}], target [{}]"
            self.log(t.format(sabs, dabs, dlabs))
            mt = bos.path.getmtime(sabs, False)
            bos.unlink(sabs)
            self._symlink(dlabs, dabs, dvn.flags, False, lmod=mt)

            # folders are too scary, schedule rescan of both vols
            self.need_rescan.add(svn.vpath)
            self.need_rescan.add(dvn.vpath)
            with self.rescan_cond:
                self.rescan_cond.notify_all()

            if xar:
                runhook(self.log, xar, dabs, dvp, "", uname, 0, 0, "", 0, "")

            return "k"

        c1, w, ftime_, fsize_, ip, at = self._find_from_vpath(svn.realpath, srem)
        c2 = self.cur.get(dvn.realpath)

        if ftime_ is None:
            ftime = st.st_mtime
            fsize = st.st_size
        else:
            ftime = ftime_
            fsize = fsize_ or 0

        has_dupes = False
        if w:
            assert c1
            if c2 and c2 != c1:
                self._copy_tags(c1, c2, w)

            has_dupes = self._forget_file(svn.realpath, srem, c1, w, is_xvol, fsize)
            if not is_xvol:
                has_dupes = self._relink(w, svn.realpath, srem, dabs)

            curs.add(c1)

            if c2:
                self.db_add(
                    c2,
                    {},  # skip upload hooks
                    drd,
                    dfn,
                    ftime,
                    fsize,
                    dvn.realpath,
                    dvn.vpath,
                    w,
                    "",
                    "",
                    ip or "",
                    at or 0,
                )
                curs.add(c2)
        else:
            self.log("not found in src db: [{}]".format(svp))

        try:
            if is_xvol and has_dupes:
                raise OSError(errno.EXDEV, "src is symlink")

            atomic_move(sabs, dabs)

        except OSError as ex:
            if ex.errno != errno.EXDEV:
                raise

            self.log("using copy+delete (%s):\n  %s\n  %s" % (ex.strerror, sabs, dabs))
            b1, b2 = fsenc(sabs), fsenc(dabs)
            is_link = os.path.islink(b1)  # due to _relink
            try:
                shutil.copy2(b1, b2)
            except:
                try:
                    os.unlink(b2)
                except:
                    pass

                if not is_link:
                    raise

                # broken symlink? keep it as-is
                try:
                    zb = os.readlink(b1)
                    os.symlink(zb, b2)
                except:
                    os.unlink(b2)
                    raise

            if is_link:
                try:
                    times = (int(time.time()), int(stl.st_mtime))
                    bos.utime(dabs, times, False)
                except:
                    pass

            os.unlink(b1)

        if xar:
            runhook(self.log, xar, dabs, dvp, "", uname, 0, 0, "", 0, "")

        return "k"

    def _copy_tags(
        self, csrc: "sqlite3.Cursor", cdst: "sqlite3.Cursor", wark: str
    ) -> None:
        """copy all tags for wark from src-db to dst-db"""
        w = wark[:16]

        if cdst.execute("select * from mt where w=? limit 1", (w,)).fetchone():
            return  # existing tags in dest db

        for _, k, v in csrc.execute("select * from mt where w=?", (w,)):
            cdst.execute("insert into mt values(?,?,?)", (w, k, v))

    def _find_from_vpath(
        self, ptop: str, vrem: str
    ) -> tuple[
        Optional["sqlite3.Cursor"],
        Optional[str],
        Optional[int],
        Optional[int],
        Optional[str],
        Optional[int],
    ]:
        cur = self.cur.get(ptop)
        if not cur:
            return None, None, None, None, None, None

        rd, fn = vsplit(vrem)
        q = "select w, mt, sz, ip, at from up where rd=? and fn=? limit 1"
        try:
            c = cur.execute(q, (rd, fn))
        except:
            assert self.mem_cur
            c = cur.execute(q, s3enc(self.mem_cur, rd, fn))

        hit = c.fetchone()
        if hit:
            wark, ftime, fsize, ip, at = hit
            return cur, wark, ftime, fsize, ip, at
        return cur, None, None, None, None, None

    def _forget_file(
        self,
        ptop: str,
        vrem: str,
        cur: Optional["sqlite3.Cursor"],
        wark: Optional[str],
        drop_tags: bool,
        sz: int,
    ) -> bool:
        """forgets file in db, fixes symlinks, does not delete"""
        srd, sfn = vsplit(vrem)
        has_dupes = False
        self.log("forgetting {}".format(vrem))
        if wark and cur:
            self.log("found {} in db".format(wark))
            if drop_tags:
                if self._relink(wark, ptop, vrem, ""):
                    has_dupes = True
                    drop_tags = False

            if drop_tags:
                q = "delete from mt where w=?"
                cur.execute(q, (wark[:16],))

            self.db_rm(cur, srd, sfn, sz)

        reg = self.registry.get(ptop)
        if reg:
            vdir = vsplit(vrem)[0]
            wark = wark or next(
                (
                    x
                    for x, y in reg.items()
                    if sfn in [y["name"], y.get("tnam")] and y["prel"] == vdir
                ),
                "",
            )
            job = reg.get(wark) if wark else None
            if job:
                t = "forgetting partial upload {} ({})"
                p = self._vis_job_progress(job)
                self.log(t.format(wark, p))
                assert wark
                del reg[wark]

        return has_dupes

    def _relink(self, wark: str, sptop: str, srem: str, dabs: str) -> int:
        """
        update symlinks from file at svn/srem to dabs (rename),
        or to first remaining full if no dabs (delete)
        """
        dupes = []
        sabs = djoin(sptop, srem)

        if self.no_expr_idx:
            q = r"select rd, fn from up where w = ?"
            argv = (wark,)
        else:
            q = r"select rd, fn from up where substr(w,1,16)=? and +w=?"
            argv = (wark[:16], wark)

        for ptop, cur in self.cur.items():
            for rd, fn in cur.execute(q, argv):
                if rd.startswith("//") or fn.startswith("//"):
                    rd, fn = s3dec(rd, fn)

                dvrem = vjoin(rd, fn).strip("/")
                if ptop != sptop or srem != dvrem:
                    dupes.append([ptop, dvrem])
                    self.log("found {} dupe: [{}] {}".format(wark, ptop, dvrem))

        if not dupes:
            return 0

        full: dict[str, tuple[str, str]] = {}
        links: dict[str, tuple[str, str]] = {}
        for ptop, vp in dupes:
            ap = djoin(ptop, vp)
            try:
                d = links if bos.path.islink(ap) else full
                d[ap] = (ptop, vp)
            except:
                self.log("relink: not found: [{}]".format(ap))

        if not dabs and not full and links:
            # deleting final remaining full copy; swap it with a symlink
            slabs = list(sorted(links.keys()))[0]
            ptop, rem = links.pop(slabs)
            self.log("linkswap [{}] and [{}]".format(sabs, slabs))
            mt = bos.path.getmtime(slabs, False)
            bos.unlink(slabs)
            bos.rename(sabs, slabs)
            bos.utime(slabs, (int(time.time()), int(mt)), False)
            self._symlink(slabs, sabs, self.flags.get(ptop) or {}, False)
            full[slabs] = (ptop, rem)
            sabs = slabs

        if not dabs:
            dabs = list(sorted(full.keys()))[0]

        for alink, parts in links.items():
            lmod = None
            try:
                if alink != sabs and absreal(alink) != sabs:
                    continue

                self.log("relinking [{}] to [{}]".format(alink, dabs))
                lmod = bos.path.getmtime(alink, False)
                bos.unlink(alink)
            except:
                pass

            flags = self.flags.get(parts[0]) or {}
            self._symlink(dabs, alink, flags, False, lmod=lmod or 0)

        return len(full) + len(links)

    def _get_wark(self, cj: dict[str, Any]) -> str:
        if len(cj["name"]) > 1024 or len(cj["hash"]) > 512 * 1024:  # 16TiB
            raise Pebkac(400, "name or numchunks not according to spec")

        for k in cj["hash"]:
            if not self.r_hash.match(k):
                raise Pebkac(
                    400, "at least one hash is not according to spec: {}".format(k)
                )

        # try to use client-provided timestamp, don't care if it fails somehow
        try:
            cj["lmod"] = int(cj["lmod"])
        except:
            cj["lmod"] = int(time.time())

        if cj["hash"]:
            wark = up2k_wark_from_hashlist(self.salt, cj["size"], cj["hash"])
        else:
            wark = up2k_wark_from_metadata(
                self.salt, cj["size"], cj["lmod"], cj["prel"], cj["name"]
            )

        return wark

    def _hashlist_from_file(self, path: str, prefix: str = "") -> list[str]:
        fsz = bos.path.getsize(path)
        csz = up2k_chunksize(fsz)
        ret = []
        suffix = " MB, {}".format(path)
        with open(fsenc(path), "rb", 512 * 1024) as f:
            if self.mth and fsz >= 1024 * 512:
                tlt = self.mth.hash(f, fsz, csz, self.pp, prefix, suffix)
                ret = [x[0] for x in tlt]
                fsz = 0

            while fsz > 0:
                # same as `hash_at` except for `imutex` / bufsz
                if self.stop:
                    return []

                if self.pp:
                    mb = int(fsz / 1024 / 1024)
                    self.pp.msg = prefix + str(mb) + suffix

                hashobj = hashlib.sha512()
                rem = min(csz, fsz)
                fsz -= rem
                while rem > 0:
                    buf = f.read(min(rem, 64 * 1024))
                    if not buf:
                        raise Exception("EOF at " + str(f.tell()))

                    hashobj.update(buf)
                    rem -= len(buf)

                digest = hashobj.digest()[:33]
                digest = base64.urlsafe_b64encode(digest)
                ret.append(digest.decode("utf-8"))

        return ret

    def _new_upload(self, job: dict[str, Any]) -> None:
        pdir = djoin(job["ptop"], job["prel"])
        if not job["size"] and bos.path.isfile(djoin(pdir, job["name"])):
            return

        self.registry[job["ptop"]][job["wark"]] = job
        job["name"] = self._untaken(pdir, job, job["t0"])
        # if len(job["name"].split(".")) > 8:
        #    raise Exception("aaa")

        xbu = self.flags[job["ptop"]].get("xbu")
        ap_chk = djoin(pdir, job["name"])
        vp_chk = djoin(job["vtop"], job["prel"], job["name"])
        if xbu and not runhook(
            self.log,
            xbu,
            ap_chk,
            vp_chk,
            job["host"],
            job["user"],
            int(job["lmod"]),
            job["size"],
            job["addr"],
            int(job["t0"]),
            "",
        ):
            t = "upload blocked by xbu server config: {}".format(vp_chk)
            self.log(t, 1)
            raise Pebkac(403, t)

        tnam = job["name"] + ".PARTIAL"
        if self.args.dotpart:
            tnam = "." + tnam

        if self.args.nw:
            job["tnam"] = tnam
            if not job["hash"]:
                del self.registry[job["ptop"]][job["wark"]]
            return

        if self.args.plain_ip:
            dip = job["addr"].replace(":", ".")
        else:
            dip = self.hub.iphash.s(job["addr"])

        suffix = "-{:.6f}-{}".format(job["t0"], dip)
        with ren_open(tnam, "wb", fdir=pdir, suffix=suffix) as zfw:
            f, job["tnam"] = zfw["orz"]
            abspath = djoin(pdir, job["tnam"])
            sprs = job["sprs"]
            sz = job["size"]
            relabel = False
            if (
                ANYWIN
                and sprs
                and self.args.sparse
                and self.args.sparse * 1024 * 1024 <= sz
            ):
                try:
                    sp.check_call(["fsutil", "sparse", "setflag", abspath])
                except:
                    self.log("could not sparse [{}]".format(abspath), 3)
                    relabel = True
                    sprs = False

            if not ANYWIN and sprs and sz > 1024 * 1024:
                fs = self.fstab.get(pdir)
                if fs != "ok":
                    relabel = True
                    f.seek(1024 * 1024 - 1)
                    f.write(b"e")
                    f.flush()
                    try:
                        nblk = bos.stat(abspath).st_blocks
                        sprs = nblk < 2048
                    except:
                        sprs = False

            if relabel:
                t = "sparse files {} on {} filesystem at {}"
                nv = "ok" if sprs else "ng"
                self.log(t.format(nv, self.fstab.get(pdir), pdir))
                self.fstab.relabel(pdir, nv)
                job["sprs"] = sprs

            if job["hash"] and sprs:
                f.seek(sz - 1)
                f.write(b"e")

        if not job["hash"]:
            self._finish_upload(job["ptop"], job["wark"])

    def _snapshot(self) -> None:
        slp = self.args.snap_wri
        if not slp or self.args.no_snap:
            return

        while True:
            time.sleep(slp)
            if self.pp:
                slp = 5
            else:
                slp = self.args.snap_wri
                self.do_snapshot()

    def do_snapshot(self) -> None:
        with self.mutex:
            for k, reg in self.registry.items():
                self._snap_reg(k, reg)

    def _snap_reg(self, ptop: str, reg: dict[str, dict[str, Any]]) -> None:
        now = time.time()
        histpath = self.asrv.vfs.histtab.get(ptop)
        if not histpath:
            return

        idrop = self.args.snap_drop * 60
        rm = [x for x in reg.values() if x["need"] and now - x["poke"] >= idrop]

        if self.args.nw:
            lost = []
        else:
            lost = [
                x
                for x in reg.values()
                if x["need"]
                and not bos.path.exists(djoin(x["ptop"], x["prel"], x["name"]))
            ]

        if rm or lost:
            t = "dropping {} abandoned, {} deleted uploads in {}"
            t = t.format(len(rm), len(lost), ptop)
            rm.extend(lost)
            vis = [self._vis_job_progress(x) for x in rm]
            self.log("\n".join([t] + vis))
            for job in rm:
                del reg[job["wark"]]
                try:
                    # remove the filename reservation
                    path = djoin(job["ptop"], job["prel"], job["name"])
                    if bos.path.getsize(path) == 0:
                        bos.unlink(path)
                except:
                    pass

                try:
                    if len(job["hash"]) == len(job["need"]):
                        # PARTIAL is empty, delete that too
                        path = djoin(job["ptop"], job["prel"], job["tnam"])
                        bos.unlink(path)
                except:
                    pass

        if self.args.nw or self.args.no_snap:
            return

        path = os.path.join(histpath, "up2k.snap")
        if not reg:
            if ptop not in self.snap_prev or self.snap_prev[ptop] is not None:
                self.snap_prev[ptop] = None
                if bos.path.exists(path):
                    bos.unlink(path)
            return

        newest = float(max(x["poke"] for _, x in reg.items()) if reg else 0)
        etag = (len(reg), newest)
        if etag == self.snap_prev.get(ptop):
            return

        if bos.makedirs(histpath):
            hidedir(histpath)

        path2 = "{}.{}".format(path, os.getpid())
        body = {"droppable": self.droppable[ptop], "registry": reg}
        j = json.dumps(body, indent=2, sort_keys=True).encode("utf-8")
        with gzip.GzipFile(path2, "wb") as f:
            f.write(j)

        atomic_move(path2, path)

        self.log("snap: {} |{}|".format(path, len(reg.keys())))
        self.snap_prev[ptop] = etag

    def _tagger(self) -> None:
        with self.mutex:
            self.n_tagq += 1

        assert self.mtag
        while True:
            with self.mutex:
                self.n_tagq -= 1

            ptop, wark, rd, fn, ip, at = self.tagq.get()
            if "e2t" not in self.flags[ptop]:
                continue

            # self.log("\n  " + repr([ptop, rd, fn]))
            abspath = djoin(ptop, rd, fn)
            try:
                tags = self.mtag.get(abspath)
                ntags1 = len(tags)
                parsers = self._get_parsers(ptop, tags, abspath)
                if self.args.mtag_vv:
                    t = "parsers({}): {}\n{} {} tags: {}".format(
                        ptop, list(parsers.keys()), ntags1, self.mtag.backend, tags
                    )
                    self.log(t)

                if parsers:
                    tags["up_ip"] = ip
                    tags["up_at"] = at
                    tags.update(self.mtag.get_bin(parsers, abspath, tags))
            except Exception as ex:
                self._log_tag_err("", abspath, ex)
                continue

            with self.mutex:
                cur = self.cur[ptop]
                if not cur:
                    self.log("no cursor to write tags with??", c=1)
                    continue

                # TODO is undef if vol 404 on startup
                entags = self.entags.get(ptop)
                if not entags:
                    self.log("no entags okay.jpg", c=3)
                    continue

                self._tag_file(cur, entags, wark, abspath, tags)
                cur.connection.commit()

            self.log("tagged {} ({}+{})".format(abspath, ntags1, len(tags) - ntags1))

    def _hasher(self) -> None:
        with self.mutex:
            self.n_hashq += 1

        while True:
            with self.mutex:
                self.n_hashq -= 1
            # self.log("hashq {}".format(self.n_hashq))

            ptop, vtop, rd, fn, ip, at, usr, skip_xau = self.hashq.get()
            # self.log("hashq {} pop {}/{}/{}".format(self.n_hashq, ptop, rd, fn))
            if "e2d" not in self.flags[ptop]:
                continue

            abspath = djoin(ptop, rd, fn)
            self.log("hashing " + abspath)
            inf = bos.stat(abspath)
            if not inf.st_size:
                wark = up2k_wark_from_metadata(
                    self.salt, inf.st_size, int(inf.st_mtime), rd, fn
                )
            else:
                hashes = self._hashlist_from_file(abspath)
                if not hashes:
                    return

                wark = up2k_wark_from_hashlist(self.salt, inf.st_size, hashes)

            with self.mutex:
                self.idx_wark(
                    self.flags[ptop],
                    rd,
                    fn,
                    inf.st_mtime,
                    inf.st_size,
                    ptop,
                    vtop,
                    wark,
                    "",
                    usr,
                    ip,
                    at,
                    skip_xau,
                )

            if at and time.time() - at > 30:
                with self.rescan_cond:
                    self.rescan_cond.notify_all()

    def hash_file(
        self,
        ptop: str,
        vtop: str,
        flags: dict[str, Any],
        rd: str,
        fn: str,
        ip: str,
        at: float,
        usr: str,
        skip_xau: bool = False,
    ) -> None:
        with self.mutex:
            self.register_vpath(ptop, flags)
            self.hashq.put((ptop, vtop, rd, fn, ip, at, usr, skip_xau))
            self.n_hashq += 1
        # self.log("hashq {} push {}/{}/{}".format(self.n_hashq, ptop, rd, fn))

    def shutdown(self) -> None:
        self.stop = True

        if self.mth:
            self.mth.stop = True

        # in case we're killed early
        for x in list(self.spools):
            self._unspool(x)

        if not self.args.no_snap:
            self.log("writing snapshot")
            self.do_snapshot()

        t0 = time.time()
        while self.pp:
            time.sleep(0.1)
            if time.time() - t0 >= 1:
                break

        # if there is time
        for x in list(self.spools):
            self._unspool(x)


def up2k_chunksize(filesize: int) -> int:
    chunksize = 1024 * 1024
    stepsize = 512 * 1024
    while True:
        for mul in [1, 2]:
            nchunks = math.ceil(filesize * 1.0 / chunksize)
            if nchunks <= 256 or (chunksize >= 32 * 1024 * 1024 and nchunks <= 4096):
                return chunksize

            chunksize += stepsize
            stepsize *= mul


def up2k_wark_from_hashlist(salt: str, filesize: int, hashes: list[str]) -> str:
    """server-reproducible file identifier, independent of name or location"""
    values = [salt, str(filesize)] + hashes
    vstr = "\n".join(values)

    wark = hashlib.sha512(vstr.encode("utf-8")).digest()[:33]
    wark = base64.urlsafe_b64encode(wark)
    return wark.decode("ascii")


def up2k_wark_from_metadata(salt: str, sz: int, lastmod: int, rd: str, fn: str) -> str:
    ret = sfsenc("{}\n{}\n{}\n{}\n{}".format(salt, lastmod, sz, rd, fn))
    ret = base64.urlsafe_b64encode(hashlib.sha512(ret).digest())
    return "#{}".format(ret.decode("ascii"))[:44]

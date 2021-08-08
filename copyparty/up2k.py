# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import time
import math
import json
import gzip
import stat
import shutil
import base64
import hashlib
import threading
import traceback
import subprocess as sp
from copy import deepcopy

from .__init__ import WINDOWS, ANYWIN, PY2
from .util import (
    Pebkac,
    Queue,
    ProgressPrinter,
    fsdec,
    fsenc,
    absreal,
    sanitize_fn,
    ren_open,
    atomic_move,
    vsplit,
    s3enc,
    s3dec,
    rmdirs,
    statdir,
    s2hms,
    min_ex,
)
from .bos import bos
from .authsrv import AuthSrv
from .mtag import MTag, MParser

try:
    HAVE_SQLITE3 = True
    import sqlite3
except:
    HAVE_SQLITE3 = False

DB_VER = 5


class Up2k(object):
    def __init__(self, hub):
        self.hub = hub
        self.asrv = hub.asrv  # type: AuthSrv
        self.args = hub.args
        self.log_func = hub.log

        # config
        self.salt = self.args.salt

        # state
        self.mutex = threading.Lock()
        self.hashq = Queue()
        self.tagq = Queue()
        self.n_hashq = 0
        self.n_tagq = 0
        self.volstate = {}
        self.need_rescan = {}
        self.registry = {}
        self.entags = {}
        self.flags = {}
        self.cur = {}
        self.mtag = None
        self.pending_tags = None
        self.mtp_parsers = {}

        self.mem_cur = None
        self.sqlite_ver = None
        self.no_expr_idx = False
        if HAVE_SQLITE3:
            # mojibake detector
            self.mem_cur = self._orz(":memory:")
            self.mem_cur.execute(r"create table a (b text)")
            self.sqlite_ver = tuple([int(x) for x in sqlite3.sqlite_version.split(".")])
            if self.sqlite_ver < (3, 9):
                self.no_expr_idx = True

        if ANYWIN:
            # usually fails to set lastmod too quickly
            self.lastmod_q = Queue()
            thr = threading.Thread(target=self._lastmodder, name="up2k-lastmod")
            thr.daemon = True
            thr.start()

        # static
        self.r_hash = re.compile("^[0-9a-zA-Z_-]{44}$")

        if not HAVE_SQLITE3:
            self.log("could not initialize sqlite3, will use in-memory registry only")

        if self.args.no_fastboot:
            self.deferred_init()

    def init_vols(self):
        if self.args.no_fastboot:
            return

        t = threading.Thread(target=self.deferred_init, name="up2k-deferred-init")
        t.daemon = True
        t.start()

    def deferred_init(self):
        all_vols = self.asrv.vfs.all_vols
        have_e2d = self.init_indexes(all_vols)

        if have_e2d:
            thr = threading.Thread(target=self._snapshot, name="up2k-snapshot")
            thr.daemon = True
            thr.start()

            thr = threading.Thread(target=self._hasher, name="up2k-hasher")
            thr.daemon = True
            thr.start()

            thr = threading.Thread(target=self._sched_rescan, name="up2k-rescan")
            thr.daemon = True
            thr.start()

            if self.mtag:
                thr = threading.Thread(target=self._tagger, name="up2k-tagger")
                thr.daemon = True
                thr.start()

                thr = threading.Thread(target=self._run_all_mtp, name="up2k-mtp-init")
                thr.daemon = True
                thr.start()

    def log(self, msg, c=0):
        self.log_func("up2k", msg + "\033[K", c)

    def get_state(self):
        mtpq = 0
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
            mtpq = "?"

        ret = {
            "volstate": self.volstate,
            "scanning": hasattr(self, "pp"),
            "hashq": self.n_hashq,
            "tagq": self.n_tagq,
            "mtpq": mtpq,
        }
        return json.dumps(ret, indent=4)

    def rescan(self, all_vols, scan_vols):
        if hasattr(self, "pp"):
            return "cannot initiate; scan is already in progress"

        args = (all_vols, scan_vols)
        t = threading.Thread(
            target=self.init_indexes,
            args=args,
            name="up2k-rescan-{}".format(scan_vols[0]),
        )
        t.daemon = True
        t.start()
        return None

    def _sched_rescan(self):
        maxage = self.args.re_maxage
        volage = {}
        while True:
            time.sleep(self.args.re_int)
            now = time.time()
            vpaths = list(sorted(self.asrv.vfs.all_vols.keys()))
            with self.mutex:
                if maxage:
                    for vp in vpaths:
                        if vp not in volage:
                            volage[vp] = now

                        if now - volage[vp] >= maxage:
                            self.need_rescan[vp] = 1

                if not self.need_rescan:
                    continue

                vols = list(sorted(self.need_rescan.keys()))
                self.need_rescan = {}

            err = self.rescan(self.asrv.vfs.all_vols, vols)
            if err:
                for v in vols:
                    self.need_rescan[v] = True

                continue

            for v in vols:
                volage[v] = now

    def _vis_job_progress(self, job):
        perc = 100 - (len(job["need"]) * 100.0 / len(job["hash"]))
        path = os.path.join(job["ptop"], job["prel"], job["name"])
        return "{:5.1f}% {}".format(perc, path)

    def _vis_reg_progress(self, reg):
        ret = []
        for _, job in reg.items():
            ret.append(self._vis_job_progress(job))

        return ret

    def _expr_idx_filter(self, flags):
        if not self.no_expr_idx:
            return False, flags

        ret = {k: v for k, v in flags.items() if not k.startswith("e2t")}
        if ret.keys() == flags.keys():
            return False, flags

        return True, ret

    def init_indexes(self, all_vols, scan_vols=None):
        self.pp = ProgressPrinter()
        vols = all_vols.values()
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
        for vol in vols:
            en = {}
            if "mte" in vol.flags:
                en = {k: True for k in vol.flags["mte"].split(",")}

            self.entags[vol.realpath] = en

            if "e2d" in vol.flags:
                have_e2d = True

            if "e2ds" in vol.flags:
                self.volstate[vol.vpath] = "busy (hashing files)"
                _, vac = self._build_file_index(vol, list(all_vols.values()))
                if vac:
                    need_vac[vol] = True

            if "e2ts" not in vol.flags:
                m = "online, idle"
            else:
                m = "online (tags pending)"

            self.volstate[vol.vpath] = m

        # open the rest + do any e2ts(a)
        needed_mutagen = False
        for vol in vols:
            if "e2ts" not in vol.flags:
                continue

            m = "online (reading tags)"
            self.volstate[vol.vpath] = m
            self.log("{} [{}]".format(m, vol.realpath))

            nadd, nrm, success = self._build_tags_index(vol)
            if not success:
                needed_mutagen = True

            if nadd or nrm:
                need_vac[vol] = True

            self.volstate[vol.vpath] = "online (mtp soon)"

        for vol in need_vac:
            cur, _ = self.register_vpath(vol.realpath, vol.flags)
            with self.mutex:
                cur.connection.commit()
                cur.execute("vacuum")

        self.pp.end = True

        msg = "{} volumes in {:.2f} sec"
        self.log(msg.format(len(vols), time.time() - t0))

        if needed_mutagen:
            msg = "could not read tags because no backends are available (Mutagen or FFprobe)"
            self.log(msg, c=1)

        thr = None
        if self.mtag:
            m = "online (running mtp)"
            if scan_vols:
                thr = threading.Thread(target=self._run_all_mtp, name="up2k-mtp-scan")
                thr.daemon = True
        else:
            del self.pp
            m = "online, idle"

        for vol in vols:
            self.volstate[vol.vpath] = m

        if thr:
            thr.start()

        return have_e2d

    def register_vpath(self, ptop, flags):
        histpath = self.asrv.vfs.histtab[ptop]
        db_path = os.path.join(histpath, "up2k.db")
        if ptop in self.registry:
            try:
                return [self.cur[ptop], db_path]
            except:
                return None

        _, flags = self._expr_idx_filter(flags)

        ft = "\033[0;32m{}{:.0}"
        ff = "\033[0;35m{}{:.0}"
        fv = "\033[0;36m{}:\033[1;30m{}"
        a = [
            (ft if v is True else ff if v is False else fv).format(k, str(v))
            for k, v in flags.items()
        ]
        if a:
            vpath = "?"
            for k, v in self.asrv.vfs.all_vols.items():
                if v.realpath == ptop:
                    vpath = k

            if vpath:
                vpath += "/"

            self.log("/{} {}".format(vpath, " ".join(sorted(a))), "35")

        reg = {}
        path = os.path.join(histpath, "up2k.snap")
        if "e2d" in flags and bos.path.exists(path):
            with gzip.GzipFile(path, "rb") as f:
                j = f.read().decode("utf-8")

            reg2 = json.loads(j)
            for k, job in reg2.items():
                path = os.path.join(job["ptop"], job["prel"], job["name"])
                if bos.path.exists(path):
                    reg[k] = job
                    job["poke"] = time.time()
                else:
                    self.log("ign deleted file in snap: [{}]".format(path))

            m = "loaded snap {} |{}|".format(path, len(reg.keys()))
            m = [m] + self._vis_reg_progress(reg)
            self.log("\n".join(m))

        self.flags[ptop] = flags
        self.registry[ptop] = reg
        if not HAVE_SQLITE3 or "e2d" not in flags or "d2d" in flags:
            return None

        bos.makedirs(histpath)

        try:
            cur = self._open_db(db_path)
            self.cur[ptop] = cur
            return [cur, db_path]
        except:
            msg = "cannot use database at [{}]:\n{}"
            self.log(msg.format(ptop, traceback.format_exc()))

        return None

    def _build_file_index(self, vol, all_vols):
        do_vac = False
        top = vol.realpath
        nohash = "dhash" in vol.flags
        with self.mutex:
            cur, _ = self.register_vpath(top, vol.flags)

            dbw = [cur, 0, time.time()]
            self.pp.n = next(dbw[0].execute("select count(w) from up"))[0]

            excl = [
                vol.realpath + "/" + d.vpath[len(vol.vpath) :].lstrip("/")
                for d in all_vols
                if d != vol and (d.vpath.startswith(vol.vpath + "/") or not vol.vpath)
            ]
            if WINDOWS:
                excl = [x.replace("/", "\\") for x in excl]

            n_add = self._build_dir(dbw, top, set(excl), top, nohash, [])
            n_rm = self._drop_lost(dbw[0], top)
            if dbw[1]:
                self.log("commit {} new files".format(dbw[1]))
                dbw[0].connection.commit()

            return True, n_add or n_rm or do_vac

    def _build_dir(self, dbw, top, excl, cdir, nohash, seen):
        rcdir = absreal(cdir)  # a bit expensive but worth
        if rcdir in seen:
            m = "bailing from symlink loop,\n  prev: {}\n  curr: {}\n  from: {}"
            self.log(m.format(seen[-1], rcdir, cdir), 3)
            return 0

        seen = seen + [cdir]
        self.pp.msg = "a{} {}".format(self.pp.n, cdir)
        histpath = self.asrv.vfs.histtab[top]
        ret = 0
        g = statdir(self.log_func, not self.args.no_scandir, False, cdir)
        for iname, inf in sorted(g):
            abspath = os.path.join(cdir, iname)
            lmod = int(inf.st_mtime)
            sz = inf.st_size
            if stat.S_ISDIR(inf.st_mode):
                if abspath in excl or abspath == histpath:
                    continue
                # self.log(" dir: {}".format(abspath))
                ret += self._build_dir(dbw, top, excl, abspath, nohash, seen)
            else:
                # self.log("file: {}".format(abspath))
                rp = abspath[len(top) + 1 :]
                if WINDOWS:
                    rp = rp.replace("\\", "/").strip("/")

                rd, fn = rp.rsplit("/", 1) if "/" in rp else ["", rp]
                sql = "select w, mt, sz from up where rd = ? and fn = ?"
                try:
                    c = dbw[0].execute(sql, (rd, fn))
                except:
                    c = dbw[0].execute(sql, s3enc(self.mem_cur, rd, fn))

                in_db = list(c.fetchall())
                if in_db:
                    self.pp.n -= 1
                    dw, dts, dsz = in_db[0]
                    if len(in_db) > 1:
                        m = "WARN: multiple entries: [{}] => [{}] |{}|\n{}"
                        rep_db = "\n".join([repr(x) for x in in_db])
                        self.log(m.format(top, rp, len(in_db), rep_db))
                        dts = -1

                    if dts == lmod and dsz == sz and (nohash or dw[0] != "#"):
                        continue

                    m = "reindex [{}] => [{}] ({}/{}) ({}/{})".format(
                        top, rp, dts, lmod, dsz, sz
                    )
                    self.log(m)
                    self.db_rm(dbw[0], rd, fn)
                    ret += 1
                    dbw[1] += 1
                    in_db = None

                self.pp.msg = "a{} {}".format(self.pp.n, abspath)

                if nohash:
                    wark = up2k_wark_from_metadata(self.salt, sz, lmod, rd, fn)
                else:
                    if sz > 1024 * 1024:
                        self.log("file: {}".format(abspath))

                    try:
                        hashes = self._hashlist_from_file(abspath)
                    except Exception as ex:
                        self.log("hash: {} @ [{}]".format(repr(ex), abspath))
                        continue

                    wark = up2k_wark_from_hashlist(self.salt, sz, hashes)

                self.db_add(dbw[0], wark, rd, fn, lmod, sz, "", 0)
                dbw[1] += 1
                ret += 1
                td = time.time() - dbw[2]
                if dbw[1] >= 4096 or td >= 60:
                    self.log("commit {} new files".format(dbw[1]))
                    dbw[0].connection.commit()
                    dbw[1] = 0
                    dbw[2] = time.time()
        return ret

    def _drop_lost(self, cur, top):
        rm = []
        nchecked = 0
        nfiles = next(cur.execute("select count(w) from up"))[0]
        c = cur.execute("select rd, fn from up")
        for drd, dfn in c:
            nchecked += 1
            if drd.startswith("//") or dfn.startswith("//"):
                drd, dfn = s3dec(drd, dfn)

            abspath = os.path.join(top, drd, dfn)
            # almost zero overhead dw
            self.pp.msg = "b{} {}".format(nfiles - nchecked, abspath)
            try:
                if not bos.path.exists(abspath):
                    rm.append([drd, dfn])
            except Exception as ex:
                self.log("stat-rm: {} @ [{}]".format(repr(ex), abspath))

        if rm:
            self.log("forgetting {} deleted files".format(len(rm)))
            for rd, fn in rm:
                # self.log("{} / {}".format(rd, fn))
                self.db_rm(cur, rd, fn)

        return len(rm)

    def _build_tags_index(self, vol):
        ptop = vol.realpath
        with self.mutex:
            _, db_path = self.register_vpath(ptop, vol.flags)
            entags = self.entags[ptop]
            flags = self.flags[ptop]
            cur = self.cur[ptop]

        n_add = 0
        n_rm = 0
        n_buf = 0
        last_write = time.time()

        if "e2tsr" in flags:
            with self.mutex:
                n_rm = cur.execute("select count(w) from mt").fetchone()[0]
                if n_rm:
                    self.log("discarding {} media tags for a full rescan".format(n_rm))
                    cur.execute("delete from mt")

        # integrity: drop tags for tracks that were deleted
        if "e2t" in flags:
            with self.mutex:
                drops = []
                c2 = cur.connection.cursor()
                up_q = "select w from up where substr(w,1,16) = ?"
                for (w,) in cur.execute("select w from mt"):
                    if not c2.execute(up_q, (w,)).fetchone():
                        drops.append(w[:16])
                c2.close()

                if drops:
                    msg = "discarding media tags for {} deleted files"
                    self.log(msg.format(len(drops)))
                    n_rm += len(drops)
                    for w in drops:
                        cur.execute("delete from mt where w = ?", (w,))

        # bail if a volume flag disables indexing
        if "d2t" in flags or "d2d" in flags:
            return n_add, n_rm, True

        # add tags for new files
        gcur = cur
        with self.mutex:
            gcur.connection.commit()

        if "e2ts" in flags:
            if not self.mtag:
                return n_add, n_rm, False

            mpool = False
            if self.mtag.prefer_mt and not self.args.no_mtag_mt:
                mpool = self._start_mpool()

            conn = sqlite3.connect(db_path, timeout=15)
            cur = conn.cursor()
            c2 = conn.cursor()
            c3 = conn.cursor()
            n_left = cur.execute("select count(w) from up").fetchone()[0]
            for w, rd, fn in cur.execute("select w, rd, fn from up order by rd, fn"):
                n_left -= 1
                q = "select w from mt where w = ?"
                if c2.execute(q, (w[:16],)).fetchone():
                    continue

                if "mtp" in flags:
                    q = "insert into mt values (?,'t:mtp','a')"
                    c2.execute(q, (w[:16],))

                if rd.startswith("//") or fn.startswith("//"):
                    rd, fn = s3dec(rd, fn)

                abspath = os.path.join(ptop, rd, fn)
                self.pp.msg = "c{} {}".format(n_left, abspath)
                args = [entags, w, abspath]
                if not mpool:
                    n_tags = self._tag_file(c3, *args)
                else:
                    mpool.put(["mtag"] + args)
                    with self.mutex:
                        n_tags = len(self._flush_mpool(c3))

                n_add += n_tags
                n_buf += n_tags

                td = time.time() - last_write
                if n_buf >= 4096 or td >= 60:
                    self.log("commit {} new tags".format(n_buf))
                    cur.connection.commit()
                    last_write = time.time()
                    n_buf = 0

            if mpool:
                self._stop_mpool(mpool)
                with self.mutex:
                    n_add += len(self._flush_mpool(c3))

            conn.commit()
            c3.close()
            c2.close()
            cur.close()
            conn.close()

        with self.mutex:
            gcur.connection.commit()

        return n_add, n_rm, True

    def _flush_mpool(self, wcur):
        ret = []
        for x in self.pending_tags:
            self._tag_file(wcur, *x)
            ret.append(x[1])

        self.pending_tags = []
        return ret

    def _run_all_mtp(self):
        t0 = time.time()
        for ptop, flags in self.flags.items():
            if "mtp" in flags:
                self._run_one_mtp(ptop)

        td = time.time() - t0
        msg = "mtp finished in {:.2f} sec ({})"
        self.log(msg.format(td, s2hms(td, True)))

        del self.pp
        for k in list(self.volstate.keys()):
            if "OFFLINE" not in self.volstate[k]:
                self.volstate[k] = "online, idle"

    def _run_one_mtp(self, ptop):
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
            with self.mutex:
                q = "select w from mt where k = 't:mtp' limit ?"
                warks = cur.execute(q, (batch_sz,)).fetchall()
                warks = [x[0] for x in warks]
                jobs = []
                for w in warks:
                    q = "select rd, fn from up where substr(w,1,16)=? limit 1"
                    rd, fn = cur.execute(q, (w,)).fetchone()
                    rd, fn = s3dec(rd, fn)
                    abspath = os.path.join(ptop, rd, fn)

                    q = "select k from mt where w = ?"
                    have = cur.execute(q, (w,)).fetchall()
                    have = [x[0] for x in have]

                    parsers = self._get_parsers(ptop, have, abspath)
                    if not parsers:
                        to_delete[w] = True
                        n_left -= 1
                        continue

                    if w in in_progress:
                        continue

                    jobs.append([parsers, None, w, abspath])
                    in_progress[w] = True

            with self.mutex:
                done = self._flush_mpool(wcur)
                for w in done:
                    to_delete[w] = True
                    in_progress.pop(w)
                    n_done += 1

                for w in to_delete.keys():
                    q = "delete from mt where w = ? and k = 't:mtp'"
                    cur.execute(q, (w,))

                to_delete = {}

            if not warks:
                break

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
                q = "delete from mt where w = ? and k = 't:mtp'"
                cur.execute(q, (w,))

            cur.connection.commit()
            if n_done:
                cur.execute("vacuum")

            wcur.close()
            cur.close()

    def _get_parsers(self, ptop, have, abspath):
        try:
            all_parsers = self.mtp_parsers[ptop]
        except:
            return {}

        entags = self.entags[ptop]
        parsers = {}
        for k, v in all_parsers.items():
            if "ac" in entags or ".aq" in entags:
                if "ac" in have or ".aq" in have:
                    # is audio, require non-audio?
                    if v.audio == "n":
                        continue
                # is not audio, require audio?
                elif v.audio == "y":
                    continue

            if v.ext:
                match = False
                for ext in v.ext:
                    if abspath.lower().endswith("." + ext):
                        match = True
                        break

                if not match:
                    continue

            parsers[k] = v

        parsers = {k: v for k, v in parsers.items() if v.force or k not in have}
        return parsers

    def _start_mpool(self):
        # mp.pool.ThreadPool and concurrent.futures.ThreadPoolExecutor
        # both do crazy runahead so lets reinvent another wheel
        nw = os.cpu_count() if hasattr(os, "cpu_count") else 4
        if self.args.no_mtag_mt:
            nw = 1

        if self.pending_tags is None:
            self.log("using {}x {}".format(nw, self.mtag.backend))
            self.pending_tags = []

        mpool = Queue(nw)
        for _ in range(nw):
            thr = threading.Thread(
                target=self._tag_thr, args=(mpool,), name="up2k-mpool"
            )
            thr.daemon = True
            thr.start()

        return mpool

    def _stop_mpool(self, mpool):
        if not mpool:
            return

        for _ in range(mpool.maxsize):
            mpool.put(None)

        mpool.join()

    def _tag_thr(self, q):
        while True:
            task = q.get()
            if not task:
                q.task_done()
                return

            try:
                parser, entags, wark, abspath = task
                if parser == "mtag":
                    tags = self.mtag.get(abspath)
                else:
                    tags = self.mtag.get_bin(parser, abspath)
                    vtags = [
                        "\033[36m{} \033[33m{}".format(k, v) for k, v in tags.items()
                    ]
                    if vtags:
                        self.log("{}\033[0m [{}]".format(" ".join(vtags), abspath))

                with self.mutex:
                    self.pending_tags.append([entags, wark, abspath, tags])
            except:
                ex = traceback.format_exc()
                if parser == "mtag":
                    parser = self.mtag.backend

                msg = "{} failed to read tags from {}:\n{}"
                self.log(msg.format(parser, abspath, ex), c=3)

            q.task_done()

    def _tag_file(self, write_cur, entags, wark, abspath, tags=None):
        if tags is None:
            tags = self.mtag.get(abspath)

        if entags:
            tags = {k: v for k, v in tags.items() if k in entags}
            if not tags:
                # indicate scanned without tags
                tags = {"x": 0}

        if not tags:
            return 0

        for k in tags.keys():
            q = "delete from mt where w = ? and ({})".format(
                " or ".join(["k = ?"] * len(tags))
            )
            args = [wark[:16]] + list(tags.keys())
            write_cur.execute(q, tuple(args))

        ret = 0
        for k, v in tags.items():
            q = "insert into mt values (?,?,?)"
            write_cur.execute(q, (wark[:16], k, v))
            ret += 1

        return ret

    def _orz(self, db_path):
        return sqlite3.connect(db_path, check_same_thread=False).cursor()
        # x.set_trace_callback(trace)

    def _open_db(self, db_path):
        existed = bos.path.exists(db_path)
        cur = self._orz(db_path)
        ver = self._read_ver(cur)
        if not existed and ver is None:
            return self._create_db(db_path, cur)

        if ver == 4:
            try:
                m = "creating backup before upgrade: "
                cur = self._backup_db(db_path, cur, ver, m)
                self._upgrade_v4(cur)
                ver = 5
            except:
                self.log("WARN: failed to upgrade from v4", 3)

        if ver == DB_VER:
            try:
                nfiles = next(cur.execute("select count(w) from up"))[0]
                self.log("OK: {} |{}|".format(db_path, nfiles))
                return cur
            except:
                self.log("WARN: could not list files; DB corrupt?\n" + min_ex())

        if (ver or 0) > DB_VER:
            m = "database is version {}, this copyparty only supports versions <= {}"
            raise Exception(m.format(ver, DB_VER))

        msg = "creating new DB (old is bad); backup: {}"
        if ver:
            msg = "creating new DB (too old to upgrade); backup: {}"

        cur = self._backup_db(db_path, cur, ver, msg)
        db = cur.connection
        cur.close()
        db.close()
        bos.unlink(db_path)
        return self._create_db(db_path, None)

    def _backup_db(self, db_path, cur, ver, msg):
        bak = "{}.bak.{:x}.v{}".format(db_path, int(time.time()), ver)
        self.log(msg + bak)
        try:
            c2 = sqlite3.connect(bak)
            with c2:
                cur.connection.backup(c2)
            return cur
        except:
            m = "native sqlite3 backup failed; using fallback method:\n"
            self.log(m + min_ex())
        finally:
            c2.close()

        db = cur.connection
        cur.close()
        db.close()

        shutil.copy2(fsenc(db_path), fsenc(bak))
        return self._orz(db_path)

    def _read_ver(self, cur):
        for tab in ["ki", "kv"]:
            try:
                c = cur.execute(r"select v from {} where k = 'sver'".format(tab))
            except:
                continue

            rows = c.fetchall()
            if rows:
                return int(rows[0][0])

    def _create_db(self, db_path, cur):
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

        cur.connection.commit()
        self.log("created DB at {}".format(db_path))
        return cur

    def _upgrade_v4(self, cur):
        for cmd in [
            r"alter table up add column ip text",
            r"alter table up add column at int",
            r"create index up_ip on up(ip)",
            r"update kv set v=5 where k='sver'",
        ]:
            cur.execute(cmd)

        cur.connection.commit()

    def handle_json(self, cj):
        with self.mutex:
            if not self.register_vpath(cj["ptop"], cj["vcfg"]):
                if cj["ptop"] not in self.registry:
                    raise Pebkac(410, "location unavailable")

        cj["name"] = sanitize_fn(cj["name"], "", [".prologue.html", ".epilogue.html"])
        cj["poke"] = time.time()
        wark = self._get_wark(cj)
        now = time.time()
        job = None
        with self.mutex:
            cur = self.cur.get(cj["ptop"])
            reg = self.registry[cj["ptop"]]
            if cur:
                if self.no_expr_idx:
                    q = r"select * from up where w = ?"
                    argv = (wark,)
                else:
                    q = r"select * from up where substr(w,1,16) = ? and w = ?"
                    argv = (wark[:16], wark)

                cur = cur.execute(q, argv)
                for _, dtime, dsize, dp_dir, dp_fn, ip, at in cur:
                    if dp_dir.startswith("//") or dp_fn.startswith("//"):
                        dp_dir, dp_fn = s3dec(dp_dir, dp_fn)

                    dp_abs = "/".join([cj["ptop"], dp_dir, dp_fn])
                    # relying on path.exists to return false on broken symlinks
                    if bos.path.exists(dp_abs):
                        job = {
                            "name": dp_fn,
                            "prel": dp_dir,
                            "vtop": cj["vtop"],
                            "ptop": cj["ptop"],
                            "size": dsize,
                            "lmod": dtime,
                            "addr": ip,
                            "at": at,
                            "hash": [],
                            "need": [],
                        }
                        break

                if job and wark in reg:
                    del reg[wark]

            if job or wark in reg:
                job = job or reg[wark]
                if job["prel"] == cj["prel"] and job["name"] == cj["name"]:
                    # ensure the files haven't been deleted manually
                    names = [job[x] for x in ["name", "tnam"] if x in job]
                    for fn in names:
                        path = os.path.join(job["ptop"], job["prel"], fn)
                        try:
                            if bos.path.getsize(path) > 0:
                                # upload completed or both present
                                break
                        except:
                            # missing; restart
                            if not self.args.nw:
                                job = None
                            break
                else:
                    # file contents match, but not the path
                    src = os.path.join(job["ptop"], job["prel"], job["name"])
                    dst = os.path.join(cj["ptop"], cj["prel"], cj["name"])
                    vsrc = os.path.join(job["vtop"], job["prel"], job["name"])
                    vsrc = vsrc.replace("\\", "/")  # just for prints anyways
                    if job["need"]:
                        self.log("unfinished:\n  {0}\n  {1}".format(src, dst))
                        err = "partial upload exists at a different location; please resume uploading here instead:\n"
                        err += "/" + vsrc + " "
                        raise Pebkac(400, err)
                    elif "nodupe" in self.flags[job["ptop"]]:
                        self.log("dupe-reject:\n  {0}\n  {1}".format(src, dst))
                        err = "upload rejected, file already exists:\n/" + vsrc + " "
                        raise Pebkac(400, err)
                    else:
                        # symlink to the client-provided name,
                        # returning the previous upload info
                        job = deepcopy(job)
                        for k in ["ptop", "vtop", "prel"]:
                            job[k] = cj[k]

                        pdir = os.path.join(cj["ptop"], cj["prel"])
                        job["name"] = self._untaken(pdir, cj["name"], now, cj["addr"])
                        dst = os.path.join(job["ptop"], job["prel"], job["name"])
                        if not self.args.nw:
                            bos.unlink(dst)  # TODO ed pls
                            self._symlink(src, dst)

                        if cur:
                            a = [cj[x] for x in "prel name lmod size addr".split()]
                            a += [cj.get("at") or time.time()]
                            self.db_add(cur, wark, *a)
                            cur.connection.commit()

            if not job:
                vfs = self.asrv.vfs.all_vols[cj["vtop"]]
                if vfs.lim:
                    ap1 = os.path.join(cj["ptop"], cj["prel"])
                    ap2, cj["prel"] = vfs.lim.all(
                        cj["addr"], cj["prel"], cj["size"], ap1
                    )
                    bos.makedirs(ap2)
                    vfs.lim.nup(cj["addr"])
                    vfs.lim.bup(cj["addr"], cj["size"])

                job = {
                    "wark": wark,
                    "t0": now,
                    "hash": deepcopy(cj["hash"]),
                    "need": [],
                }
                # client-provided, sanitized by _get_wark: name, size, lmod
                for k in [
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

                # one chunk may occur multiple times in a file;
                # filter to unique values for the list of missing chunks
                # (preserve order to reduce disk thrashing)
                lut = {}
                for k in cj["hash"]:
                    if k not in lut:
                        job["need"].append(k)
                        lut[k] = 1

                self._new_upload(job)

            purl = "/{}/".format("{}/{}".format(job["vtop"], job["prel"]).strip("/"))

            return {
                "name": job["name"],
                "purl": purl,
                "size": job["size"],
                "lmod": job["lmod"],
                "hash": job["need"],
                "wark": wark,
            }

    def _untaken(self, fdir, fname, ts, ip):
        if self.args.nw:
            return fname

        # TODO broker which avoid this race and
        # provides a new filename if taken (same as bup)
        suffix = ".{:.6f}-{}".format(ts, ip)
        with ren_open(fname, "wb", fdir=fdir, suffix=suffix) as f:
            return f["orz"][1]

    def _symlink(self, src, dst, verbose=True):
        if verbose:
            self.log("linking dupe:\n  {0}\n  {1}".format(src, dst))

        if self.args.nw:
            return

        try:
            lsrc = src
            ldst = dst
            fs1 = bos.stat(os.path.dirname(src)).st_dev
            fs2 = bos.stat(os.path.dirname(dst)).st_dev
            if fs1 == 0:
                # py2 on winxp or other unsupported combination
                raise OSError()
            elif fs1 == fs2:
                # same fs; make symlink as relative as possible
                v = []
                for p in [src, dst]:
                    if WINDOWS:
                        p = p.replace("\\", "/")
                    v.append(p.split("/"))

                nsrc, ndst = v
                nc = 0
                for a, b in zip(nsrc, ndst):
                    if a != b:
                        break
                    nc += 1
                if nc > 1:
                    lsrc = nsrc[nc:]
                    hops = len(ndst[nc:]) - 1
                    lsrc = "../" * hops + "/".join(lsrc)
            os.symlink(fsenc(lsrc), fsenc(ldst))
        except Exception as ex:
            self.log("cannot symlink; creating copy: " + repr(ex))
            shutil.copy2(fsenc(src), fsenc(dst))

    def handle_chunk(self, ptop, wark, chash):
        with self.mutex:
            job = self.registry[ptop].get(wark)
            if not job:
                known = " ".join([x for x in self.registry[ptop].keys()])
                self.log("unknown wark [{}], known: {}".format(wark, known))
                raise Pebkac(400, "unknown wark")

            if chash not in job["need"]:
                msg = "chash = {} , need:\n".format(chash)
                msg += "\n".join(job["need"])
                self.log(msg)
                raise Pebkac(400, "already got that but thanks??")

            nchunk = [n for n, v in enumerate(job["hash"]) if v == chash]
            if not nchunk:
                raise Pebkac(400, "unknown chunk")

        job["poke"] = time.time()

        chunksize = up2k_chunksize(job["size"])
        ofs = [chunksize * x for x in nchunk]

        path = os.path.join(job["ptop"], job["prel"], job["tnam"])

        return [chunksize, ofs, path, job["lmod"]]

    def confirm_chunk(self, ptop, wark, chash):
        with self.mutex:
            try:
                job = self.registry[ptop][wark]
                pdir = os.path.join(job["ptop"], job["prel"])
                src = os.path.join(pdir, job["tnam"])
                dst = os.path.join(pdir, job["name"])
            except Exception as ex:
                return "confirm_chunk, wark, " + repr(ex)

            try:
                job["need"].remove(chash)
            except Exception as ex:
                return "confirm_chunk, chash, " + repr(ex)

            ret = len(job["need"])
            if ret > 0:
                return ret, src

            if self.args.nw:
                # del self.registry[ptop][wark]
                return ret, dst

            atomic_move(src, dst)

            if ANYWIN:
                a = [dst, job["size"], (int(time.time()), int(job["lmod"]))]
                self.lastmod_q.put(a)

            a = [job[x] for x in "ptop wark prel name lmod size addr".split()]
            a += [job.get("at") or time.time()]
            if self.idx_wark(*a):
                del self.registry[ptop][wark]
                # in-memory registry is reserved for unfinished uploads

        return ret, dst

    def idx_wark(self, ptop, wark, rd, fn, lmod, sz, ip, at):
        cur = self.cur.get(ptop)
        if not cur:
            return False

        self.db_rm(cur, rd, fn)
        self.db_add(cur, wark, rd, fn, lmod, sz, ip, at)
        cur.connection.commit()

        if "e2t" in self.flags[ptop]:
            self.tagq.put([ptop, wark, rd, fn])
            self.n_tagq += 1

        return True

    def db_rm(self, db, rd, fn):
        sql = "delete from up where rd = ? and fn = ?"
        try:
            db.execute(sql, (rd, fn))
        except:
            db.execute(sql, s3enc(self.mem_cur, rd, fn))

    def db_add(self, db, wark, rd, fn, ts, sz, ip, at):
        sql = "insert into up values (?,?,?,?,?,?,?)"
        v = (wark, int(ts), sz, rd, fn, ip or "", int(at or 0))
        try:
            db.execute(sql, v)
        except:
            rd, fn = s3enc(self.mem_cur, rd, fn)
            v = (wark, int(ts), sz, rd, fn, ip or "", int(at or 0))
            db.execute(sql, v)

    def handle_rm(self, uname, ip, vpaths):
        n_files = 0
        ok = {}
        ng = {}
        for vp in vpaths:
            a, b, c = self._handle_rm(uname, ip, vp)
            n_files += a
            for k in b:
                ok[k] = 1
            for k in c:
                ng[k] = 1

        ng = {k: 1 for k in ng if k not in ok}
        ok = len(ok)
        ng = len(ng)

        return "deleted {} files (and {}/{} folders)".format(n_files, ok, ok + ng)

    def _handle_rm(self, uname, ip, vpath):
        try:
            permsets = [[True, False, False, True]]
            vn, rem = self.asrv.vfs.get(vpath, uname, *permsets[0])
            unpost = False
        except:
            # unpost with missing permissions? try read+write and verify with db
            if not self.args.unpost:
                raise Pebkac(400, "the unpost feature was disabled by server config")

            unpost = True
            permsets = [[True, True]]
            vn, rem = self.asrv.vfs.get(vpath, uname, *permsets[0])
            _, _, _, _, dip, dat = self._find_from_vpath(vn.realpath, rem)

            m = "you cannot delete this: "
            if not dip:
                m += "file not found"
            elif dip != ip:
                m += "not uploaded by (You)"
            elif dat < time.time() - self.args.unpost:
                m += "uploaded too long ago"
            else:
                m = None

            if m:
                raise Pebkac(400, m)

        ptop = vn.realpath
        atop = vn.canonical(rem, False)
        adir, fn = os.path.split(atop)
        st = bos.lstat(atop)
        scandir = not self.args.no_scandir
        if stat.S_ISLNK(st.st_mode) or stat.S_ISREG(st.st_mode):
            dbv, vrem = self.asrv.vfs.get(vpath, uname, *permsets[0])
            dbv, vrem = dbv.get_dbv(vrem)
            voldir = vsplit(vrem)[0]
            vpath_dir = vsplit(vpath)[0]
            g = [[dbv, voldir, vpath_dir, adir, [[fn, 0]], [], []]]
        else:
            g = vn.walk("", rem, [], uname, permsets, True, scandir, True)
            if unpost:
                raise Pebkac(400, "cannot unpost folders")

        n_files = 0
        for dbv, vrem, _, adir, files, rd, vd in g:
            for fn in [x[0] for x in files]:
                n_files += 1
                abspath = os.path.join(adir, fn)
                volpath = "{}/{}".format(vrem, fn).strip("/")
                vpath = "{}/{}".format(dbv.vpath, volpath).strip("/")
                self.log("rm {}\n  {}".format(vpath, abspath))
                _ = dbv.get(volpath, uname, *permsets[0])
                with self.mutex:
                    try:
                        ptop = dbv.realpath
                        cur, wark, _, _, _, _ = self._find_from_vpath(ptop, volpath)
                        self._forget_file(ptop, volpath, cur, wark, True)
                    finally:
                        cur.connection.commit()

                bos.unlink(abspath)

        rm = rmdirs(self.log_func, scandir, True, atop)
        return n_files, rm[0], rm[1]

    def handle_mv(self, uname, svp, dvp):
        svn, srem = self.asrv.vfs.get(svp, uname, True, False, True)
        svn, srem = svn.get_dbv(srem)
        sabs = svn.canonical(srem, False)

        if not srem:
            raise Pebkac(400, "mv: cannot move a mountpoint")

        st = bos.lstat(sabs)
        if stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
            with self.mutex:
                return self._mv_file(uname, svp, dvp)

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

            for fn in files:
                svpf = "/".join(x for x in [dbv.vpath, vrem, fn[0]] if x)
                if not svpf.startswith(svp + "/"):  # assert
                    raise Pebkac(500, "mv: bug at {}, top {}".format(svpf, svp))

                dvpf = dvp + svpf[len(svp) :]
                with self.mutex:
                    self._mv_file(uname, svpf, dvpf)

        rmdirs(self.log_func, scandir, True, sabs)
        return "k"

    def _mv_file(self, uname, svp, dvp):
        svn, srem = self.asrv.vfs.get(svp, uname, True, False, True)
        svn, srem = svn.get_dbv(srem)

        dvn, drem = self.asrv.vfs.get(dvp, uname, False, True)
        dvn, drem = dvn.get_dbv(drem)

        sabs = svn.canonical(srem, False)
        dabs = dvn.canonical(drem)
        drd, dfn = vsplit(drem)

        if bos.path.exists(dabs):
            raise Pebkac(400, "mv2: target file exists")

        bos.makedirs(os.path.dirname(dabs))

        if bos.path.islink(sabs):
            dlabs = absreal(sabs)
            m = "moving symlink from [{}] to [{}], target [{}]"
            self.log(m.format(sabs, dabs, dlabs))
            os.unlink(sabs)
            self._symlink(dlabs, dabs, False)

            # folders are too scary, schedule rescan of both vols
            self.need_rescan[svn.vpath] = 1
            self.need_rescan[dvn.vpath] = 1
            return "k"

        c1, w, ftime, fsize, ip, at = self._find_from_vpath(svn.realpath, srem)
        c2 = self.cur.get(dvn.realpath)

        if ftime is None:
            st = bos.stat(sabs)
            ftime = st.st_mtime
            fsize = st.st_size

        if w:
            if c2 and c2 != c1:
                self._copy_tags(c1, c2, w)

            self._forget_file(svn.realpath, srem, c1, w, c1 != c2)
            self._relink(w, svn.realpath, srem, dabs)
            c1.connection.commit()

            if c2:
                self.db_add(c2, w, drd, dfn, ftime, fsize, ip, at)
                c2.connection.commit()
        else:
            self.log("not found in src db: [{}]".format(svp))

        bos.rename(sabs, dabs)
        return "k"

    def _copy_tags(self, csrc, cdst, wark):
        """copy all tags for wark from src-db to dst-db"""
        w = wark[:16]

        if cdst.execute("select * from mt where w=? limit 1", (w,)).fetchone():
            return  # existing tags in dest db

        for _, k, v in csrc.execute("select * from mt where w=?", (w,)):
            cdst.execute("insert into mt values(?,?,?)", (w, k, v))

    def _find_from_vpath(self, ptop, vrem):
        cur = self.cur.get(ptop)
        if not cur:
            return None, None

        rd, fn = vsplit(vrem)
        q = "select w, mt, sz, ip, at from up where rd=? and fn=? limit 1"
        try:
            c = cur.execute(q, (rd, fn))
        except:
            c = cur.execute(q, s3enc(self.mem_cur, rd, fn))

        hit = c.fetchone()
        if hit:
            wark, ftime, fsize, ip, at = hit
            return cur, wark, ftime, fsize, ip, at
        return cur, None, None, None, None, None

    def _forget_file(self, ptop, vrem, cur, wark, drop_tags):
        """forgets file in db, fixes symlinks, does not delete"""
        srd, sfn = vsplit(vrem)
        self.log("forgetting {}".format(vrem))
        if wark:
            self.log("found {} in db".format(wark))
            if drop_tags:
                if self._relink(wark, ptop, vrem, None):
                    drop_tags = False

            if drop_tags:
                q = "delete from mt where w=?"
                cur.execute(q, (wark[:16],))

            self.db_rm(cur, srd, sfn)

        reg = self.registry.get(ptop)
        if reg:
            if not wark:
                wark = [
                    x
                    for x, y in reg.items()
                    if fn in [y["name"], y.get("tnam")] and y["prel"] == vrem
                ]

            if wark and wark in reg:
                m = "forgetting partial upload {} ({})"
                p = self._vis_job_progress(wark)
                self.log(m.format(wark, p))
                del reg[wark]

    def _relink(self, wark, sptop, srem, dabs):
        """
        update symlinks from file at svn/srem to dabs (rename),
        or to first remaining full if no dabs (delete)
        """
        dupes = []
        sabs = os.path.join(sptop, srem)
        q = "select rd, fn from up where substr(w,1,16)=? and w=?"
        for ptop, cur in self.cur.items():
            for rd, fn in cur.execute(q, (wark[:16], wark)):
                if rd.startswith("//") or fn.startswith("//"):
                    rd, fn = s3dec(rd, fn)

                dvrem = "/".join([rd, fn]).strip("/")
                if ptop != sptop or srem != dvrem:
                    dupes.append([ptop, dvrem])
                    self.log("found {} dupe: [{}] {}".format(wark, ptop, dvrem))

        if not dupes:
            return 0

        full = {}
        links = {}
        for ptop, vp in dupes:
            ap = os.path.join(ptop, vp)
            try:
                d = links if bos.path.islink(ap) else full
                d[ap] = [ptop, vp]
            except:
                self.log("relink: not found: [{}]".format(ap))

        if not dabs and not full and links:
            # deleting final remaining full copy; swap it with a symlink
            slabs = list(sorted(links.keys()))[0]
            ptop, rem = links.pop(slabs)
            self.log("linkswap [{}] and [{}]".format(sabs, slabs))
            bos.unlink(slabs)
            bos.rename(sabs, slabs)
            self._symlink(slabs, sabs, False)
            full[slabs] = [ptop, rem]

        if not dabs:
            dabs = list(sorted(full.keys()))[0]

        for alink in links.keys():
            try:
                if alink != sabs and absreal(alink) != sabs:
                    continue

                self.log("relinking [{}] to [{}]".format(alink, dabs))
                bos.unlink(alink)
            except:
                pass

            self._symlink(dabs, alink, False)

        return len(full) + len(links)

    def _get_wark(self, cj):
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

        wark = up2k_wark_from_hashlist(self.salt, cj["size"], cj["hash"])
        return wark

    def _hashlist_from_file(self, path):
        pp = self.pp if hasattr(self, "pp") else None
        fsz = bos.path.getsize(path)
        csz = up2k_chunksize(fsz)
        ret = []
        with open(fsenc(path), "rb", 512 * 1024) as f:
            while fsz > 0:
                if pp:
                    pp.msg = "{} MB, {}".format(int(fsz / 1024 / 1024), path)

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

    def _new_upload(self, job):
        self.registry[job["ptop"]][job["wark"]] = job
        pdir = os.path.join(job["ptop"], job["prel"])
        job["name"] = self._untaken(pdir, job["name"], job["t0"], job["addr"])
        # if len(job["name"].split(".")) > 8:
        #    raise Exception("aaa")

        tnam = job["name"] + ".PARTIAL"
        if self.args.dotpart:
            tnam = "." + tnam

        if self.args.nw:
            job["tnam"] = tnam
            return

        suffix = ".{:.6f}-{}".format(job["t0"], job["addr"])
        with ren_open(tnam, "wb", fdir=pdir, suffix=suffix) as f:
            f, job["tnam"] = f["orz"]
            if (
                ANYWIN
                and self.args.sparse
                and self.args.sparse * 1024 * 1024 <= job["size"]
            ):
                fp = os.path.join(pdir, job["tnam"])
                try:
                    sp.check_call(["fsutil", "sparse", "setflag", fp])
                except:
                    self.log("could not sparse [{}]".format(fp), 3)

            f.seek(job["size"] - 1)
            f.write(b"e")

    def _lastmodder(self):
        while True:
            ready = []
            while not self.lastmod_q.empty():
                ready.append(self.lastmod_q.get())

            # self.log("lmod: got {}".format(len(ready)))
            time.sleep(5)
            for path, sz, times in ready:
                self.log("lmod: setting times {} on {}".format(times, path))
                try:
                    bos.utime(path, times)
                except:
                    self.log("lmod: failed to utime ({}, {})".format(path, times))

                if self.args.sparse and self.args.sparse * 1024 * 1024 <= sz:
                    try:
                        sp.check_call(["fsutil", "sparse", "setflag", path, "0"])
                    except:
                        self.log("could not unsparse [{}]".format(path), 3)

    def _snapshot(self):
        self.snap_persist_interval = 300  # persist unfinished index every 5 min
        self.snap_discard_interval = 21600  # drop unfinished after 6 hours inactivity
        self.snap_prev = {}
        while True:
            time.sleep(self.snap_persist_interval)
            self.do_snapshot()

    def do_snapshot(self):
        with self.mutex:
            for k, reg in self.registry.items():
                self._snap_reg(k, reg)

    def _snap_reg(self, ptop, reg):
        now = time.time()
        histpath = self.asrv.vfs.histtab[ptop]
        rm = [x for x in reg.values() if now - x["poke"] > self.snap_discard_interval]
        if rm:
            m = "dropping {} abandoned uploads in {}".format(len(rm), ptop)
            vis = [self._vis_job_progress(x) for x in rm]
            self.log("\n".join([m] + vis))
            for job in rm:
                del reg[job["wark"]]
                try:
                    # remove the filename reservation
                    path = os.path.join(job["ptop"], job["prel"], job["name"])
                    if bos.path.getsize(path) == 0:
                        bos.unlink(path)

                    if len(job["hash"]) == len(job["need"]):
                        # PARTIAL is empty, delete that too
                        path = os.path.join(job["ptop"], job["prel"], job["tnam"])
                        bos.unlink(path)
                except:
                    pass

        path = os.path.join(histpath, "up2k.snap")
        if not reg:
            if ptop not in self.snap_prev or self.snap_prev[ptop] is not None:
                self.snap_prev[ptop] = None
                if bos.path.exists(path):
                    bos.unlink(path)
            return

        newest = max(x["poke"] for _, x in reg.items()) if reg else 0
        etag = [len(reg), newest]
        if etag == self.snap_prev.get(ptop):
            return

        bos.makedirs(histpath)

        path2 = "{}.{}".format(path, os.getpid())
        j = json.dumps(reg, indent=2, sort_keys=True).encode("utf-8")
        with gzip.GzipFile(path2, "wb") as f:
            f.write(j)

        atomic_move(path2, path)

        self.log("snap: {} |{}|".format(path, len(reg.keys())))
        self.snap_prev[ptop] = etag

    def _tagger(self):
        with self.mutex:
            self.n_tagq += 1

        while True:
            with self.mutex:
                self.n_tagq -= 1

            ptop, wark, rd, fn = self.tagq.get()
            if "e2t" not in self.flags[ptop]:
                continue

            # self.log("\n  " + repr([ptop, rd, fn]))
            abspath = os.path.join(ptop, rd, fn)
            tags = self.mtag.get(abspath)
            ntags1 = len(tags)
            parsers = self._get_parsers(ptop, tags, abspath)
            if parsers:
                tags.update(self.mtag.get_bin(parsers, abspath))

            with self.mutex:
                cur = self.cur[ptop]
                if not cur:
                    self.log("no cursor to write tags with??", c=1)
                    continue

                # TODO is undef if vol 404 on startup
                entags = self.entags[ptop]
                if not entags:
                    self.log("no entags okay.jpg", c=3)
                    continue

                self._tag_file(cur, entags, wark, abspath, tags)
                cur.connection.commit()

            self.log("tagged {} ({}+{})".format(abspath, ntags1, len(tags) - ntags1))

    def _hasher(self):
        with self.mutex:
            self.n_hashq += 1

        while True:
            with self.mutex:
                self.n_hashq -= 1
            # self.log("hashq {}".format(self.n_hashq))

            ptop, rd, fn, ip, at = self.hashq.get()
            # self.log("hashq {} pop {}/{}/{}".format(self.n_hashq, ptop, rd, fn))
            if "e2d" not in self.flags[ptop]:
                continue

            abspath = os.path.join(ptop, rd, fn)
            self.log("hashing " + abspath)
            inf = bos.stat(abspath)
            hashes = self._hashlist_from_file(abspath)
            wark = up2k_wark_from_hashlist(self.salt, inf.st_size, hashes)
            with self.mutex:
                self.idx_wark(ptop, wark, rd, fn, inf.st_mtime, inf.st_size, ip, at)

    def hash_file(self, ptop, flags, rd, fn, ip, at):
        with self.mutex:
            self.register_vpath(ptop, flags)
            self.hashq.put([ptop, rd, fn, ip, at])
            self.n_hashq += 1
        # self.log("hashq {} push {}/{}/{}".format(self.n_hashq, ptop, rd, fn))

    def shutdown(self):
        if hasattr(self, "snap_prev"):
            self.log("writing snapshot")
            self.do_snapshot()


def up2k_chunksize(filesize):
    chunksize = 1024 * 1024
    stepsize = 512 * 1024
    while True:
        for mul in [1, 2]:
            nchunks = math.ceil(filesize * 1.0 / chunksize)
            if nchunks <= 256 or chunksize >= 32 * 1024 * 1024:
                return chunksize

            chunksize += stepsize
            stepsize *= mul


def up2k_wark_from_hashlist(salt, filesize, hashes):
    """server-reproducible file identifier, independent of name or location"""
    ident = [salt, str(filesize)]
    ident.extend(hashes)
    ident = "\n".join(ident)

    wark = hashlib.sha512(ident.encode("utf-8")).digest()[:33]
    wark = base64.urlsafe_b64encode(wark)
    return wark.decode("ascii")


def up2k_wark_from_metadata(salt, sz, lastmod, rd, fn):
    ret = fsenc("{}\n{}\n{}\n{}\n{}".format(salt, lastmod, sz, rd, fn))
    ret = base64.urlsafe_b64encode(hashlib.sha512(ret).digest())
    return "#{}".format(ret.decode("ascii"))[:44]

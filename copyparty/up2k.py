# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import sys
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
from copy import deepcopy

from .__init__ import WINDOWS
from .util import (
    Pebkac,
    Queue,
    ProgressPrinter,
    fsdec,
    fsenc,
    sanitize_fn,
    ren_open,
    atomic_move,
    w8b64enc,
    w8b64dec,
)
from .mtag import MTag
from .authsrv import AuthSrv

try:
    HAVE_SQLITE3 = True
    import sqlite3
except:
    HAVE_SQLITE3 = False


class Up2k(object):
    """
    TODO:
      * documentation
      * registry persistence
        * ~/.config flatfiles for active jobs
    """

    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args
        self.log_func = broker.log
        self.persist = self.args.e2d

        # config
        self.salt = broker.args.salt

        # state
        self.mutex = threading.Lock()
        self.registry = {}
        self.entags = {}
        self.flags = {}
        self.cur = {}

        self.mem_cur = None
        if HAVE_SQLITE3:
            # mojibake detector
            self.mem_cur = self._orz(":memory:")
            self.mem_cur.execute(r"create table a (b text)")

        if WINDOWS:
            # usually fails to set lastmod too quickly
            self.lastmod_q = Queue()
            thr = threading.Thread(target=self._lastmodder)
            thr.daemon = True
            thr.start()

        self.mtag = MTag(self.log_func, self.args)
        if not self.mtag.usable:
            self.mtag = None

        # static
        self.r_hash = re.compile("^[0-9a-zA-Z_-]{43}$")

        if self.persist and not HAVE_SQLITE3:
            self.log("could not initialize sqlite3, will use in-memory registry only")

        # this is kinda jank
        auth = AuthSrv(self.args, self.log, False)
        self.init_indexes(auth)

        if self.persist:
            thr = threading.Thread(target=self._snapshot)
            thr.daemon = True
            thr.start()

    def log(self, msg):
        self.log_func("up2k", msg + "\033[K")

    def w8enc(self, rd, fn):
        ret = []
        for v in [rd, fn]:
            try:
                self.mem_cur.execute("select * from a where b = ?", (v,))
                ret.append(v)
            except:
                ret.append("//" + w8b64enc(v))
                # self.log("mojien/{} [{}] {}".format(k, v, ret[-1][2:]))

        return tuple(ret)

    def w8dec(self, rd, fn):
        ret = []
        for k, v in [["d", rd], ["f", fn]]:
            if v.startswith("//"):
                ret.append(w8b64dec(v[2:]))
                # self.log("mojide/{} [{}] {}".format(k, ret[-1], v[2:]))
            else:
                ret.append(v)

        return tuple(ret)

    def _vis_job_progress(self, job):
        perc = 100 - (len(job["need"]) * 100.0 / len(job["hash"]))
        path = os.path.join(job["ptop"], job["prel"], job["name"])
        return "{:5.1f}% {}".format(perc, path)

    def _vis_reg_progress(self, reg):
        ret = []
        for _, job in reg.items():
            ret.append(self._vis_job_progress(job))

        return ret

    def init_indexes(self, auth):
        self.pp = ProgressPrinter()
        vols = auth.vfs.all_vols.values()
        t0 = time.time()

        # e2ds(a) volumes first,
        # also covers tags where e2ts is set
        for vol in vols:
            en = {}
            if "mte" in vol.flags:
                en = {k: True for k in vol.flags["mte"].split(",")}

            self.entags[vol.realpath] = en

            if "e2ds" in vol.flags:
                r = self._build_file_index(vol, vols)
                if not r:
                    needed_mutagen = True

        # open the rest + do any e2ts(a)
        needed_mutagen = False
        for vol in vols:
            r = self.register_vpath(vol.realpath, vol.flags)
            if not r or "e2ts" not in vol.flags:
                continue

            cur, db_path, sz0 = r
            n_add, n_rm, success = self._build_tags_index(vol.realpath)
            if not success:
                needed_mutagen = True

            if n_add or n_rm:
                self.vac(cur, db_path, n_add, n_rm, sz0)

        self.pp.end = True
        msg = "{} volumes in {:.2f} sec"
        self.log(msg.format(len(vols), time.time() - t0))

        if needed_mutagen:
            msg = "\033[31mcould not read tags because no backends are available (mutagen or ffprobe)\033[0m"
            self.log(msg)

    def register_vpath(self, ptop, flags):
        with self.mutex:
            if ptop in self.registry:
                return None

            reg = {}
            path = os.path.join(ptop, ".hist", "up2k.snap")
            if self.persist and os.path.exists(path):
                with gzip.GzipFile(path, "rb") as f:
                    j = f.read().decode("utf-8")

                reg = json.loads(j)
                for _, job in reg.items():
                    job["poke"] = time.time()

                m = "loaded snap {} |{}|".format(path, len(reg.keys()))
                m = [m] + self._vis_reg_progress(reg)
                self.log("\n".join(m))

            self.flags[ptop] = flags
            self.registry[ptop] = reg
            if not self.persist or not HAVE_SQLITE3 or "d2d" in flags:
                return None

            try:
                os.mkdir(os.path.join(ptop, ".hist"))
            except:
                pass

            db_path = os.path.join(ptop, ".hist", "up2k.db")
            if ptop in self.cur:
                return None

            try:
                sz0 = 0
                if os.path.exists(db_path):
                    sz0 = os.path.getsize(db_path) // 1024

                cur = self._open_db(db_path)
                self.cur[ptop] = cur
                return [cur, db_path, sz0]
            except:
                msg = "cannot use database at [{}]:\n{}"
                self.log(msg.format(ptop, traceback.format_exc()))

            return None

    def _build_file_index(self, vol, all_vols):
        do_vac = False
        top = vol.realpath
        reg = self.register_vpath(top, vol.flags)
        if not reg:
            return

        _, db_path, sz0 = reg
        dbw = [reg[0], 0, time.time()]
        self.pp.n = next(dbw[0].execute("select count(w) from up"))[0]

        # can be symlink so don't `and d.startswith(top)``
        excl = set([d.realpath for d in all_vols if d != vol])
        n_add = self._build_dir(dbw, top, excl, top)
        n_rm = self._drop_lost(dbw[0], top)
        if dbw[1]:
            self.log("commit {} new files".format(dbw[1]))
            dbw[0].connection.commit()

        n_add, n_rm, success = self._build_tags_index(vol.realpath)

        dbw[0].connection.commit()
        if n_add or n_rm or do_vac:
            self.vac(dbw[0], db_path, n_add, n_rm, sz0)

        return success

    def vac(self, cur, db_path, n_add, n_rm, sz0):
        sz1 = os.path.getsize(db_path) // 1024
        cur.execute("vacuum")
        sz2 = os.path.getsize(db_path) // 1024
        msg = "{} new, {} del, {} kB vacced, {} kB gain, {} kB now".format(
            n_add, n_rm, sz1 - sz2, sz2 - sz0, sz2
        )
        self.log(msg)

    def _build_dir(self, dbw, top, excl, cdir):
        try:
            inodes = [fsdec(x) for x in os.listdir(fsenc(cdir))]
        except Exception as ex:
            self.log("listdir: {} @ [{}]".format(repr(ex), cdir))
            return 0

        self.pp.msg = "a{} {}".format(self.pp.n, cdir)
        histdir = os.path.join(top, ".hist")
        ret = 0
        for inode in inodes:
            abspath = os.path.join(cdir, inode)
            try:
                inf = os.stat(fsenc(abspath))
            except Exception as ex:
                self.log("stat: {} @ [{}]".format(repr(ex), abspath))
                continue

            if stat.S_ISDIR(inf.st_mode):
                if abspath in excl or abspath == histdir:
                    continue
                # self.log(" dir: {}".format(abspath))
                ret += self._build_dir(dbw, top, excl, abspath)
            else:
                # self.log("file: {}".format(abspath))
                rp = abspath[len(top) :].replace("\\", "/").strip("/")
                rd, fn = rp.rsplit("/", 1) if "/" in rp else ["", rp]
                sql = "select * from up where rd = ? and fn = ?"
                try:
                    c = dbw[0].execute(sql, (rd, fn))
                except:
                    c = dbw[0].execute(sql, self.w8enc(rd, fn))

                in_db = list(c.fetchall())
                if in_db:
                    self.pp.n -= 1
                    _, dts, dsz, _, _ = in_db[0]
                    if len(in_db) > 1:
                        m = "WARN: multiple entries: [{}] => [{}] |{}|\n{}"
                        rep_db = "\n".join([repr(x) for x in in_db])
                        self.log(m.format(top, rp, len(in_db), rep_db))
                        dts = -1

                    if dts == inf.st_mtime and dsz == inf.st_size:
                        continue

                    m = "reindex [{}] => [{}] ({}/{}) ({}/{})".format(
                        top, rp, dts, inf.st_mtime, dsz, inf.st_size
                    )
                    self.log(m)
                    self.db_rm(dbw[0], rd, fn)
                    ret += 1
                    dbw[1] += 1
                    in_db = None

                self.pp.msg = "a{} {}".format(self.pp.n, abspath)
                if inf.st_size > 1024 * 1024:
                    self.log("file: {}".format(abspath))

                try:
                    hashes = self._hashlist_from_file(abspath)
                except Exception as ex:
                    self.log("hash: {} @ [{}]".format(repr(ex), abspath))
                    continue

                wark = up2k_wark_from_hashlist(self.salt, inf.st_size, hashes)
                self.db_add(dbw[0], wark, rd, fn, inf.st_mtime, inf.st_size)
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
        c = cur.execute("select * from up")
        for dwark, dts, dsz, drd, dfn in c:
            nchecked += 1
            if drd.startswith("//") or dfn.startswith("//"):
                drd, dfn = self.w8dec(drd, dfn)

            abspath = os.path.join(top, drd, dfn)
            # almost zero overhead dw
            self.pp.msg = "b{} {}".format(nfiles - nchecked, abspath)
            try:
                if not os.path.exists(fsenc(abspath)):
                    rm.append([drd, dfn])
            except Exception as ex:
                self.log("stat-rm: {} @ [{}]".format(repr(ex), abspath))

        if rm:
            self.log("forgetting {} deleted files".format(len(rm)))
            for rd, fn in rm:
                # self.log("{} / {}".format(rd, fn))
                self.db_rm(cur, rd, fn)

        return len(rm)

    def _build_tags_index(self, ptop):
        entags = self.entags[ptop]
        flags = self.flags[ptop]
        cur = self.cur[ptop]
        n_add = 0
        n_rm = 0
        n_buf = 0
        last_write = time.time()

        if "e2tsr" in flags:
            n_rm = cur.execute("select count(w) from mt").fetchone()[0]
            if n_rm:
                self.log("discarding {} media tags for a full rescan".format(n_rm))
                cur.execute("delete from mt")
            else:
                self.log("volume has e2tsr but there are no media tags to discard")

        # integrity: drop tags for tracks that were deleted
        if "e2t" in flags:
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
        if "e2ts" in flags:
            if not self.mtag:
                return n_add, n_rm, False

            c2 = cur.connection.cursor()
            n_left = cur.execute("select count(w) from up").fetchone()[0]
            for w, rd, fn in cur.execute("select w, rd, fn from up"):
                n_left -= 1
                q = "select w from mt where w = ?"
                if c2.execute(q, (w[:16],)).fetchone():
                    continue

                abspath = os.path.join(ptop, rd, fn)
                self.pp.msg = "c{} {}".format(n_left, abspath)
                tags = self.mtag.get(abspath)
                tags = {k: v for k, v in tags.items() if k in entags}
                if not tags:
                    # indicate scanned without tags
                    tags = {"x": 0}

                for k, v in tags.items():
                    q = "insert into mt values (?,?,?)"
                    c2.execute(q, (w[:16], k, v))
                    n_add += 1
                    n_buf += 1

                td = time.time() - last_write
                if n_buf >= 4096 or td >= 60:
                    self.log("commit {} new tags".format(n_buf))
                    cur.connection.commit()
                    last_write = time.time()
                    n_buf = 0

            c2.close()

        return n_add, n_rm, True

    def _orz(self, db_path):
        return sqlite3.connect(db_path, check_same_thread=False).cursor()

    def _open_db(self, db_path):
        existed = os.path.exists(db_path)
        cur = self._orz(db_path)
        try:
            ver = self._read_ver(cur)
        except:
            ver = None
            if not existed:
                return self._create_db(db_path, cur)

        orig_ver = ver
        if not ver or ver < 3:
            bak = "{}.bak.{:x}.v{}".format(db_path, int(time.time()), ver)
            db = cur.connection
            cur.close()
            db.close()
            msg = "creating new DB (old is bad); backup: {}"
            if ver:
                msg = "creating backup before upgrade: {}"

            self.log(msg.format(bak))
            shutil.copy2(db_path, bak)
            cur = self._orz(db_path)

        if ver == 1:
            cur = self._upgrade_v1(cur, db_path)
            if cur:
                ver = 2

        if ver == 2:
            cur = self._create_v3(cur)
            ver = self._read_ver(cur) if cur else None

        if ver == 3:
            if orig_ver != ver:
                cur.connection.commit()
                cur.execute("vacuum")
                cur.connection.commit()

            try:
                nfiles = next(cur.execute("select count(w) from up"))[0]
                self.log("OK: {} |{}|".format(db_path, nfiles))
                return cur
            except Exception as ex:
                self.log("WARN: could not list files, DB corrupt?\n  " + repr(ex))

        if cur:
            db = cur.connection
            cur.close()
            db.close()

        return self._create_db(db_path, None)

    def _create_db(self, db_path, cur):
        if not cur:
            cur = self._orz(db_path)

        self._create_v2(cur)
        self._create_v3(cur)
        cur.connection.commit()
        self.log("created DB at {}".format(db_path))
        return cur

    def _read_ver(self, cur):
        for tab in ["ki", "kv"]:
            try:
                c = cur.execute(r"select v from {} where k = 'sver'".format(tab))
            except:
                continue

            rows = c.fetchall()
            if rows:
                return int(rows[0][0])

    def _create_v2(self, cur):
        for cmd in [
            r"create table up (w text, mt int, sz int, rd text, fn text)",
            r"create index up_rd on up(rd)",
            r"create index up_fn on up(fn)",
        ]:
            cur.execute(cmd)
        return cur

    def _create_v3(self, cur):
        """
        collision in 2^(n/2) files where n = bits (6 bits/ch)
          10*6/2 = 2^30 =       1'073'741'824, 24.1mb idx
          12*6/2 = 2^36 =      68'719'476'736, 24.8mb idx
          16*6/2 = 2^48 = 281'474'976'710'656, 26.1mb idx
        """
        for c, ks in [["drop table k", "isv"], ["drop index up_", "w"]]:
            for k in ks:
                try:
                    cur.execute(c + k)
                except:
                    pass

        for cmd in [
            r"create index up_w on up(substr(w,1,16))",
            r"create table mt (w text, k text, v int)",
            r"create index mt_w on mt(w)",
            r"create index mt_k on mt(k)",
            r"create index mt_v on mt(v)",
            r"create table kv (k text, v int)",
            r"insert into kv values ('sver', 3)",
        ]:
            cur.execute(cmd)
        return cur

    def _upgrade_v1(self, odb, db_path):
        npath = db_path + ".next"
        if os.path.exists(npath):
            os.unlink(npath)

        ndb = self._orz(npath)
        self._create_v2(ndb)

        c = odb.execute("select * from up")
        for wark, ts, sz, rp in c:
            rd, fn = rp.rsplit("/", 1) if "/" in rp else ["", rp]
            v = (wark, ts, sz, rd, fn)
            ndb.execute("insert into up values (?,?,?,?,?)", v)

        ndb.connection.commit()
        ndb.connection.close()
        odb.connection.close()
        atomic_move(npath, db_path)
        return self._orz(db_path)

    def handle_json(self, cj):
        cj["name"] = sanitize_fn(cj["name"])
        cj["poke"] = time.time()
        wark = self._get_wark(cj)
        now = time.time()
        job = None
        with self.mutex:
            cur = self.cur.get(cj["ptop"], None)
            reg = self.registry[cj["ptop"]]
            if cur:
                cur = cur.execute(
                    r"select * from up where substr(w,1,16) = ? and w = ?",
                    (wark[:16], wark,),
                )
                for _, dtime, dsize, dp_dir, dp_fn in cur:
                    if dp_dir.startswith("//") or dp_fn.startswith("//"):
                        dp_dir, dp_fn = self.w8dec(dp_dir, dp_fn)

                    dp_abs = os.path.join(cj["ptop"], dp_dir, dp_fn).replace("\\", "/")
                    # relying on path.exists to return false on broken symlinks
                    if os.path.exists(fsenc(dp_abs)):
                        job = {
                            "name": dp_fn,
                            "prel": dp_dir,
                            "vtop": cj["vtop"],
                            "ptop": cj["ptop"],
                            "size": dsize,
                            "lmod": dtime,
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
                            if os.path.getsize(path) > 0:
                                # upload completed or both present
                                break
                        except:
                            # missing; restart
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
                        os.unlink(fsenc(dst))  # TODO ed pls
                        self._symlink(src, dst)

            if not job:
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

            return {
                "name": job["name"],
                "size": job["size"],
                "lmod": job["lmod"],
                "hash": job["need"],
                "wark": wark,
            }

    def _untaken(self, fdir, fname, ts, ip):
        # TODO broker which avoid this race and
        # provides a new filename if taken (same as bup)
        suffix = ".{:.6f}-{}".format(ts, ip)
        with ren_open(fname, "wb", fdir=fdir, suffix=suffix) as f:
            return f["orz"][1]

    def _symlink(self, src, dst):
        # TODO store this in linktab so we never delete src if there are links to it
        self.log("linking dupe:\n  {0}\n  {1}".format(src, dst))
        try:
            lsrc = src
            ldst = dst
            fs1 = os.stat(fsenc(os.path.split(src)[0])).st_dev
            fs2 = os.stat(fsenc(os.path.split(dst)[0])).st_dev
            if fs1 == 0:
                # py2 on winxp or other unsupported combination
                raise OSError()
            elif fs1 == fs2:
                # same fs; make symlink as relative as possible
                nsrc = src.replace("\\", "/").split("/")
                ndst = dst.replace("\\", "/").split("/")
                nc = 0
                for a, b in zip(nsrc, ndst):
                    if a != b:
                        break
                    nc += 1
                if nc > 1:
                    lsrc = nsrc[nc:]
                    lsrc = "../" * (len(lsrc) - 1) + "/".join(lsrc)
            os.symlink(fsenc(lsrc), fsenc(ldst))
        except (AttributeError, OSError) as ex:
            self.log("cannot symlink; creating copy: " + repr(ex))
            shutil.copy2(fsenc(src), fsenc(dst))

    def handle_chunk(self, ptop, wark, chash):
        with self.mutex:
            job = self.registry[ptop].get(wark, None)
            if not job:
                raise Pebkac(400, "unknown wark")

            if chash not in job["need"]:
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

            atomic_move(src, dst)

            if WINDOWS:
                self.lastmod_q.put([dst, (int(time.time()), int(job["lmod"]))])

            cur = self.cur.get(job["ptop"], None)
            if cur:
                j = job
                self.db_rm(cur, j["prel"], j["name"])
                self.db_add(cur, j["wark"], j["prel"], j["name"], j["lmod"], j["size"])
                cur.connection.commit()

                del self.registry[ptop][wark]
                # in-memory registry is reserved for unfinished uploads

            return ret, dst

    def db_rm(self, db, rd, fn):
        sql = "delete from up where rd = ? and fn = ?"
        try:
            db.execute(sql, (rd, fn))
        except:
            db.execute(sql, self.w8enc(rd, fn))

    def db_add(self, db, wark, rd, fn, ts, sz):
        sql = "insert into up values (?,?,?,?,?)"
        v = (wark, int(ts), sz, rd, fn)
        try:
            db.execute(sql, v)
        except:
            rd, fn = self.w8enc(rd, fn)
            v = (wark, ts, sz, rd, fn)
            db.execute(sql, v)

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
        fsz = os.path.getsize(path)
        csz = up2k_chunksize(fsz)
        ret = []
        with open(path, "rb", 512 * 1024) as f:
            while fsz > 0:
                self.pp.msg = "{} MB".format(int(fsz / 1024 / 1024))
                hashobj = hashlib.sha512()
                rem = min(csz, fsz)
                fsz -= rem
                while rem > 0:
                    buf = f.read(min(rem, 64 * 1024))
                    if not buf:
                        raise Exception("EOF at " + str(f.tell()))

                    hashobj.update(buf)
                    rem -= len(buf)

                digest = hashobj.digest()[:32]
                digest = base64.urlsafe_b64encode(digest)
                ret.append(digest.decode("utf-8").rstrip("="))

        return ret

    def _new_upload(self, job):
        self.registry[job["ptop"]][job["wark"]] = job
        pdir = os.path.join(job["ptop"], job["prel"])
        job["name"] = self._untaken(pdir, job["name"], job["t0"], job["addr"])
        # if len(job["name"].split(".")) > 8:
        #    raise Exception("aaa")

        tnam = job["name"] + ".PARTIAL"
        suffix = ".{:.6f}-{}".format(job["t0"], job["addr"])
        with ren_open(tnam, "wb", fdir=pdir, suffix=suffix) as f:
            f, job["tnam"] = f["orz"]
            f.seek(job["size"] - 1)
            f.write(b"e")

    def _lastmodder(self):
        while True:
            ready = []
            while not self.lastmod_q.empty():
                ready.append(self.lastmod_q.get())

            # self.log("lmod: got {}".format(len(ready)))
            time.sleep(5)
            for path, times in ready:
                self.log("lmod: setting times {} on {}".format(times, path))
                try:
                    os.utime(fsenc(path), times)
                except:
                    self.log("lmod: failed to utime ({}, {})".format(path, times))

    def _snapshot(self):
        persist_interval = 30  # persist unfinished uploads index every 30 sec
        discard_interval = 21600  # drop unfinished uploads after 6 hours inactivity
        prev = {}
        while True:
            time.sleep(persist_interval)
            with self.mutex:
                for k, reg in self.registry.items():
                    self._snap_reg(prev, k, reg, discard_interval)

    def _snap_reg(self, prev, k, reg, discard_interval):
        now = time.time()
        rm = [x for x in reg.values() if now - x["poke"] > discard_interval]
        if rm:
            m = "dropping {} abandoned uploads in {}".format(len(rm), k)
            vis = [self._vis_job_progress(x) for x in rm]
            self.log("\n".join([m] + vis))
            for job in rm:
                del reg[job["wark"]]
                try:
                    # remove the filename reservation
                    path = os.path.join(job["ptop"], job["prel"], job["name"])
                    if os.path.getsize(path) == 0:
                        os.unlink(path)

                    if len(job["hash"]) == len(job["need"]):
                        # PARTIAL is empty, delete that too
                        path = os.path.join(job["ptop"], job["prel"], job["tnam"])
                        os.unlink(path)
                except:
                    pass

        path = os.path.join(k, ".hist", "up2k.snap")
        if not reg:
            if k not in prev or prev[k] is not None:
                prev[k] = None
                if os.path.exists(path):
                    os.unlink(path)
            return

        newest = max(x["poke"] for _, x in reg.items()) if reg else 0
        etag = [len(reg), newest]
        if etag == prev.get(k, None):
            return

        try:
            os.mkdir(os.path.join(k, ".hist"))
        except:
            pass

        path2 = "{}.{}".format(path, os.getpid())
        j = json.dumps(reg, indent=2, sort_keys=True).encode("utf-8")
        with gzip.GzipFile(path2, "wb") as f:
            f.write(j)

        atomic_move(path2, path)

        self.log("snap: {} |{}|".format(path, len(reg.keys())))
        prev[k] = etag


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
    """ server-reproducible file identifier, independent of name or location """
    ident = [salt, str(filesize)]
    ident.extend(hashes)
    ident = "\n".join(ident)

    hasher = hashlib.sha512()
    hasher.update(ident.encode("utf-8"))
    digest = hasher.digest()[:32]

    wark = base64.urlsafe_b64encode(digest)
    return wark.decode("utf-8").rstrip("=")

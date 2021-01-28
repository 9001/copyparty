# coding: utf-8
from __future__ import print_function, unicode_literals


import os
import re
import time
import math
import json
import gzip
import stat
import shutil
import base64
import hashlib
import threading
from copy import deepcopy

from .__init__ import WINDOWS
from .util import Pebkac, Queue, fsdec, fsenc, sanitize_fn, ren_open, atomic_move

HAVE_SQLITE3 = False
try:
    import sqlite3

    HAVE_SQLITE3 = True
except:
    pass


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
        self.log = broker.log
        self.persist = self.args.e2d

        # config
        self.salt = "hunter2"  # TODO: config

        # state
        self.mutex = threading.Lock()
        self.registry = {}
        self.db = {}

        if WINDOWS:
            # usually fails to set lastmod too quickly
            self.lastmod_q = Queue()
            thr = threading.Thread(target=self._lastmodder)
            thr.daemon = True
            thr.start()

        if self.persist:
            thr = threading.Thread(target=self._snapshot)
            thr.daemon = True
            thr.start()

        # static
        self.r_hash = re.compile("^[0-9a-zA-Z_-]{43}$")

        if self.persist and not HAVE_SQLITE3:
            m = "could not initialize sqlite3, will use in-memory registry only"
            self.log("up2k", m)

    def _vis_job_progress(self, job):
        perc = 100 - (len(job["need"]) * 100.0 / len(job["hash"]))
        path = os.path.join(job["ptop"], job["prel"], job["name"])
        return "{:5.1f}% {}".format(perc, path)

    def _vis_reg_progress(self, reg):
        ret = []
        for _, job in reg.items():
            ret.append(self._vis_job_progress(job))

        return ret

    def register_vpath(self, ptop):
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
                self.log("up2k", "\n".join(m))

            self.registry[ptop] = reg
            if not self.persist or not HAVE_SQLITE3:
                return None

            try:
                os.mkdir(os.path.join(ptop, ".hist"))
            except:
                pass

            db_path = os.path.join(ptop, ".hist", "up2k.db")
            if ptop in self.db:
                # self.db[ptop].close()
                return None

            try:
                db = self._open_db(db_path)
                self.db[ptop] = db
                return db
            except Exception as ex:
                m = "failed to open [{}]: {}".format(ptop, repr(ex))
                self.log("up2k", m)

            return None

    def build_indexes(self, writeables):
        tops = [d.realpath for d in writeables]
        for top in tops:
            db = self.register_vpath(top)
            if db:
                # can be symlink so don't `and d.startswith(top)``
                excl = set([d for d in tops if d != top])
                self._build_dir([db, 0], top, excl, top)
                self._drop_lost(db, top)
                db.commit()

    def _build_dir(self, dbw, top, excl, cdir):
        try:
            inodes = [fsdec(x) for x in os.listdir(fsenc(cdir))]
        except Exception as ex:
            self.log("up2k", "listdir: " + repr(ex))
            return

        histdir = os.path.join(top, ".hist")
        for inode in inodes:
            abspath = os.path.join(cdir, inode)
            try:
                inf = os.stat(fsenc(abspath))
            except Exception as ex:
                self.log("up2k", "stat: " + repr(ex))
                continue

            if stat.S_ISDIR(inf.st_mode):
                if abspath in excl or abspath == histdir:
                    continue
                # self.log("up2k", " dir: {}".format(abspath))
                self._build_dir(dbw, top, excl, abspath)
            else:
                # self.log("up2k", "file: {}".format(abspath))
                rp = abspath[len(top) :].replace("\\", "/").strip("/")
                c = dbw[0].execute("select * from up where rp = ?", (rp,))
                in_db = list(c.fetchall())
                if in_db:
                    _, dts, dsz, _ = in_db[0]
                    if len(in_db) > 1:
                        m = "WARN: multiple entries: [{}] => [{}] ({})"
                        self.log("up2k", m.format(top, rp, len(in_db)))
                        dts = -1

                    if dts == inf.st_mtime and dsz == inf.st_size:
                        continue

                    m = "reindex [{}] => [{}] ({}/{}) ({}/{})".format(
                        top, rp, dts, inf.st_mtime, dsz, inf.st_size
                    )
                    self.log("up2k", m)
                    self.db_rm(dbw[0], rp)
                    dbw[1] += 1
                    in_db = None

                self.log("up2k", "file: {}".format(abspath))
                try:
                    hashes = self._hashlist_from_file(abspath)
                except Exception as ex:
                    self.log("up2k", "hash: " + repr(ex))
                    continue

                wark = self._wark_from_hashlist(inf.st_size, hashes)
                self.db_add(dbw[0], wark, rp, inf.st_mtime, inf.st_size)
                dbw[1] += 1
                if dbw[1] > 1024:
                    dbw[0].commit()
                    dbw[1] = 0

    def _drop_lost(self, db, top):
        rm = []
        c = db.execute("select * from up")
        for dwark, dts, dsz, drp in c:
            abspath = os.path.join(top, drp)
            try:
                if not os.path.exists(fsenc(abspath)):
                    rm.append(drp)
            except Exception as ex:
                self.log("up2k", "stat-rm: " + repr(ex))

        if not rm:
            return

        self.log("up2k", "forgetting {} deleted files".format(len(rm)))
        for rp in rm:
            self.db_rm(db, rp)

    def _open_db(self, db_path):
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            c = conn.execute(r"select * from kv where k = 'sver'")
            rows = c.fetchall()
            if rows:
                ver = rows[0][1]
            else:
                self.log("up2k", "WARN: no sver in kv, DB corrupt?")
                ver = "unknown"

            if ver == "1":
                try:
                    nfiles = next(conn.execute("select count(w) from up"))[0]
                    self.log("up2k", "found DB at {} |{}|".format(db_path, nfiles))
                    return conn
                except Exception as ex:
                    m = "WARN: could not list files, DB corrupt?\n  " + repr(ex)
                    self.log("up2k", m)

            m = "REPLACING unsupported DB (v.{}) at {}".format(ver, db_path)
            self.log("up2k", m)
            conn.close()
            os.unlink(db_path)
            conn = sqlite3.connect(db_path, check_same_thread=False)
        except:
            pass

        # sqlite is variable-width only, no point in using char/nchar/varchar
        for cmd in [
            r"create table kv (k text, v text)",
            r"create table up (w text, mt int, sz int, rp text)",
            r"insert into kv values ('sver', '1')",
            r"create index up_w on up(w)",
        ]:
            conn.execute(cmd)

        conn.commit()
        self.log("up2k", "created DB at {}".format(db_path))
        return conn

    def handle_json(self, cj):
        self.register_vpath(cj["ptop"])
        cj["name"] = sanitize_fn(cj["name"])
        cj["poke"] = time.time()
        wark = self._get_wark(cj)
        now = time.time()
        job = None
        with self.mutex:
            db = self.db.get(cj["ptop"], None)
            reg = self.registry[cj["ptop"]]
            if db:
                cur = db.execute(r"select * from up where w = ?", (wark,))
                for _, dtime, dsize, dp_rel in cur:
                    dp_abs = os.path.join(cj["ptop"], dp_rel).replace("\\", "/")
                    # relying on path.exists to return false on broken symlinks
                    if os.path.exists(fsenc(dp_abs)):
                        try:
                            prel, name = dp_rel.rsplit("/", 1)
                        except:
                            prel = ""
                            name = dp_rel

                        job = {
                            "name": name,
                            "prel": prel,
                            "vtop": cj["vtop"],
                            "ptop": cj["ptop"],
                            "flag": cj["flag"],
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
                        self.log("up2k", "unfinished:\n  {0}\n  {1}".format(src, dst))
                        err = "partial upload exists at a different location; please resume uploading here instead:\n"
                        err += vsrc + " "
                        raise Pebkac(400, err)
                    elif "nodupe" in job["flag"]:
                        self.log("up2k", "dupe-reject:\n  {0}\n  {1}".format(src, dst))
                        err = "upload rejected, file already exists:\n " + vsrc + " "
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
                    "flag",
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
        self.log("up2k", "linking dupe:\n  {0}\n  {1}".format(src, dst))
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
            self.log("up2k", "cannot symlink; creating copy: " + repr(ex))
            shutil.copy2(fsenc(src), fsenc(dst))

    def handle_chunk(self, ptop, wark, chash):
        with self.mutex:
            job = self.registry[ptop].get(wark, None)
            if not job:
                raise Pebkac(400, "unknown wark")

            if chash not in job["need"]:
                raise Pebkac(200, "already got that but thanks??")

            nchunk = [n for n, v in enumerate(job["hash"]) if v == chash]
            if not nchunk:
                raise Pebkac(400, "unknown chunk")

        job["poke"] = time.time()

        chunksize = self._get_chunksize(job["size"])
        ofs = [chunksize * x for x in nchunk]

        path = os.path.join(job["ptop"], job["prel"], job["tnam"])

        return [chunksize, ofs, path, job["lmod"]]

    def confirm_chunk(self, ptop, wark, chash):
        with self.mutex:
            job = self.registry[ptop][wark]
            pdir = os.path.join(job["ptop"], job["prel"])
            src = os.path.join(pdir, job["tnam"])
            dst = os.path.join(pdir, job["name"])

            job["need"].remove(chash)
            ret = len(job["need"])
            if ret > 0:
                return ret, src

            atomic_move(src, dst)

            if WINDOWS:
                self.lastmod_q.put([dst, (int(time.time()), int(job["lmod"]))])

            db = self.db.get(job["ptop"], None)
            if db:
                rp = os.path.join(job["prel"], job["name"]).replace("\\", "/")
                self.db_rm(db, rp)
                self.db_add(db, job["wark"], rp, job["lmod"], job["size"])
                db.commit()
                del self.registry[ptop][wark]
                # in-memory registry is reserved for unfinished uploads

            return ret, dst

    def _get_chunksize(self, filesize):
        chunksize = 1024 * 1024
        stepsize = 512 * 1024
        while True:
            for mul in [1, 2]:
                nchunks = math.ceil(filesize * 1.0 / chunksize)
                if nchunks <= 256 or chunksize >= 32 * 1024 * 1024:
                    return chunksize

                chunksize += stepsize
                stepsize *= mul

    def db_rm(self, db, rp):
        db.execute("delete from up where rp = ?", (rp,))

    def db_add(self, db, wark, rp, ts, sz):
        v = (wark, ts, sz, rp)
        db.execute("insert into up values (?,?,?,?)", v)

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

        wark = self._wark_from_hashlist(cj["size"], cj["hash"])
        return wark

    def _wark_from_hashlist(self, filesize, hashes):
        """ server-reproducible file identifier, independent of name or location """
        ident = [self.salt, str(filesize)]
        ident.extend(hashes)
        ident = "\n".join(ident)

        hasher = hashlib.sha512()
        hasher.update(ident.encode("utf-8"))
        digest = hasher.digest()[:32]

        wark = base64.urlsafe_b64encode(digest)
        return wark.decode("utf-8").rstrip("=")

    def _hashlist_from_file(self, path):
        fsz = os.path.getsize(path)
        csz = self._get_chunksize(fsz)
        ret = []
        with open(path, "rb", 512 * 1024) as f:
            while fsz > 0:
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

            # self.log("lmod", "got {}".format(len(ready)))
            time.sleep(5)
            for path, times in ready:
                try:
                    os.utime(fsenc(path), times)
                except:
                    self.log("lmod", "failed to utime ({}, {})".format(path, times))

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
            self.log("up2k", "\n".join([m] + vis))
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

        path2 = "{}.{}".format(path, os.getpid())
        j = json.dumps(reg, indent=2, sort_keys=True).encode("utf-8")
        with gzip.GzipFile(path2, "wb") as f:
            f.write(j)

        atomic_move(path2, path)

        self.log("up2k", "snap: {} |{}|".format(path, len(reg.keys())))
        prev[k] = etag

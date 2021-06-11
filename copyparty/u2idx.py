# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import time
import threading
from datetime import datetime

from .util import s3dec, Pebkac, min_ex
from .up2k import up2k_wark_from_hashlist


try:
    HAVE_SQLITE3 = True
    import sqlite3
except:
    HAVE_SQLITE3 = False


class U2idx(object):
    def __init__(self, conn):
        self.log_func = conn.log_func
        self.asrv = conn.asrv
        self.args = conn.args
        self.timeout = self.args.srch_time

        if not HAVE_SQLITE3:
            self.log("could not load sqlite3; searchign wqill be disabled")
            return

        self.cur = {}
        self.mem_cur = sqlite3.connect(":memory:")
        self.mem_cur.execute(r"create table a (b text)")

        self.p_end = None
        self.p_dur = 0

    def log(self, msg, c=0):
        self.log_func("u2idx", msg, c)

    def fsearch(self, vols, body):
        """search by up2k hashlist"""
        if not HAVE_SQLITE3:
            return []

        fsize = body["size"]
        fhash = body["hash"]
        wark = up2k_wark_from_hashlist(self.args.salt, fsize, fhash)

        uq = "where substr(w,1,16) = ? and w = ?"
        uv = [wark[:16], wark]

        try:
            return self.run_query(vols, uq, uv)[0]
        except:
            raise Pebkac(500, min_ex())

    def get_cur(self, ptop):
        cur = self.cur.get(ptop)
        if cur:
            return cur

        histpath = self.asrv.vfs.histtab[ptop]
        db_path = os.path.join(histpath, "up2k.db")
        if not os.path.exists(db_path):
            return None

        cur = sqlite3.connect(db_path).cursor()
        self.cur[ptop] = cur
        return cur

    def search(self, vols, uq):
        """search by query params"""
        if not HAVE_SQLITE3:
            return []

        q = ""
        va = []
        joins = ""
        is_key = True
        is_size = False
        is_date = False
        kw_key = ["(", ")", "and ", "or ", "not "]
        kw_val = ["==", "=", "!=", ">", ">=", "<", "<=", "like "]
        ptn_mt = re.compile(r"^\.?[a-z]+$")
        mt_ctr = 0
        mt_keycmp = "substr(up.w,1,16)"
        mt_keycmp2 = None

        while True:
            uq = uq.strip()
            if not uq:
                break

            ok = False
            for kw in kw_key + kw_val:
                if uq.startswith(kw):
                    is_key = kw in kw_key
                    uq = uq[len(kw) :]
                    ok = True
                    q += kw
                    break

            if ok:
                continue

            v, uq = (uq + " ").split(" ", 1)
            if is_key:
                is_key = False

                if v == "size":
                    v = "up.sz"
                    is_size = True

                elif v == "date":
                    v = "up.mt"
                    is_date = True

                elif v == "path":
                    v = "up.rd"

                elif v == "name":
                    v = "up.fn"

                elif v == "tags" or ptn_mt.match(v):
                    mt_ctr += 1
                    mt_keycmp2 = "mt{}.w".format(mt_ctr)
                    joins += "inner join mt mt{} on {} = {} ".format(
                        mt_ctr, mt_keycmp, mt_keycmp2
                    )
                    mt_keycmp = mt_keycmp2
                    if v == "tags":
                        v = "mt{0}.v".format(mt_ctr)
                    else:
                        v = "+mt{0}.k = '{1}' and mt{0}.v".format(mt_ctr, v)

                else:
                    raise Pebkac(400, "invalid key [" + v + "]")

                q += v + " "
                continue

            head = ""
            tail = ""

            if is_date:
                is_date = False
                v = v.upper().rstrip("Z").replace(",", " ").replace("T", " ")
                while "  " in v:
                    v = v.replace("  ", " ")

                for fmt in [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%d %H",
                    "%Y-%m-%d",
                ]:
                    try:
                        v = datetime.strptime(v, fmt).timestamp()
                        break
                    except:
                        pass

            elif is_size:
                is_size = False
                v = int(float(v) * 1024 * 1024)

            else:
                if v.startswith("*"):
                    head = "'%'||"
                    v = v[1:]

                if v.endswith("*"):
                    tail = "||'%'"
                    v = v[:-1]

            q += " {}?{} ".format(head, tail)
            va.append(v)
            is_key = True

        try:
            return self.run_query(vols, joins + "where " + q, va)
        except Exception as ex:
            raise Pebkac(500, repr(ex))

    def run_query(self, vols, uq, uv):
        done_flag = []
        self.active_id = "{:.6f}_{}".format(
            time.time(), threading.current_thread().ident
        )
        thr = threading.Thread(
            target=self.terminator,
            args=(
                self.active_id,
                done_flag,
            ),
            name="u2idx-terminator",
        )
        thr.daemon = True
        thr.start()

        if not uq or not uv:
            q = "select * from up"
            v = ()
        else:
            q = "select up.* from up " + uq
            v = tuple(uv)

        self.log("qs: {!r} {!r}".format(q, v))

        ret = []
        lim = 1000
        taglist = {}
        for (vtop, ptop, flags) in vols:
            cur = self.get_cur(ptop)
            if not cur:
                continue

            self.active_cur = cur

            sret = []
            c = cur.execute(q, v)
            for hit in c:
                w, ts, sz, rd, fn = hit
                lim -= 1
                if lim <= 0:
                    break

                if rd.startswith("//") or fn.startswith("//"):
                    rd, fn = s3dec(rd, fn)

                rp = "/".join([x for x in [vtop, rd, fn] if x])
                sret.append({"ts": int(ts), "sz": sz, "rp": rp, "w": w[:16]})

            for hit in sret:
                w = hit["w"]
                del hit["w"]
                tags = {}
                q2 = "select k, v from mt where w = ? and k != 'x'"
                for k, v2 in cur.execute(q2, (w,)):
                    taglist[k] = True
                    tags[k] = v2

                hit["tags"] = tags

            ret.extend(sret)
            # print("[{}] {}".format(ptop, sret))

        done_flag.append(True)
        self.active_id = None

        # undupe hits from multiple metadata keys
        if len(ret) > 1:
            ret = [ret[0]] + [
                y for x, y in zip(ret[:-1], ret[1:]) if x["rp"] != y["rp"]
            ]

        return ret, list(taglist.keys())

    def terminator(self, identifier, done_flag):
        for _ in range(self.timeout):
            time.sleep(1)
            if done_flag:
                return

        if identifier == self.active_id:
            self.active_cur.connection.interrupt()

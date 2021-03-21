# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import time
import threading
from datetime import datetime

from .util import u8safe, s3dec, html_escape, Pebkac
from .up2k import up2k_wark_from_hashlist


try:
    HAVE_SQLITE3 = True
    import sqlite3
except:
    HAVE_SQLITE3 = False


class U2idx(object):
    def __init__(self, args, log_func):
        self.args = args
        self.log_func = log_func
        self.timeout = args.srch_time

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

        uq = "substr(w,1,16) = ? and w = ?"
        uv = [wark[:16], wark]

        try:
            return self.run_query(vols, uq, uv, {})[0]
        except Exception as ex:
            raise Pebkac(500, repr(ex))

    def get_cur(self, ptop):
        cur = self.cur.get(ptop)
        if cur:
            return cur

        cur = _open(ptop)
        if not cur:
            return None

        self.cur[ptop] = cur
        return cur

    def search(self, vols, body):
        """search by query params"""
        if not HAVE_SQLITE3:
            return []

        qobj = {}
        _conv_sz(qobj, body, "sz_min", "up.sz >= ?")
        _conv_sz(qobj, body, "sz_max", "up.sz <= ?")
        _conv_dt(qobj, body, "dt_min", "up.mt >= ?")
        _conv_dt(qobj, body, "dt_max", "up.mt <= ?")
        for seg, dk in [["path", "up.rd"], ["name", "up.fn"]]:
            if seg in body:
                _conv_txt(qobj, body, seg, dk)

        uq, uv = _sqlize(qobj)

        qobj = {}
        if "tags" in body:
            _conv_txt(qobj, body, "tags", "mt.v")

        if "adv" in body:
            _conv_adv(qobj, body, "adv")

        try:
            return self.run_query(vols, uq, uv, qobj)
        except Exception as ex:
            raise Pebkac(500, repr(ex))

    def run_query(self, vols, uq, uv, targs):
        self.log("qs: {} {} ,  {}".format(uq, repr(uv), repr(targs)))

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
        )
        thr.daemon = True
        thr.start()

        if not targs:
            if not uq:
                q = "select * from up"
                v = ()
            else:
                q = "select * from up where " + uq
                v = tuple(uv)
        else:
            q = "select up.* from up"
            keycmp = "substr(up.w,1,16)"
            where = []
            v = []
            ctr = 0
            for tq, tv in sorted(targs.items()):
                ctr += 1
                tq = tq.split("\n")[0]
                keycmp2 = "mt{}.w".format(ctr)
                q += " inner join mt mt{} on {} = {}".format(ctr, keycmp, keycmp2)
                keycmp = keycmp2
                where.append(tq.replace("mt.", keycmp[:-1]))
                v.append(tv)

            if uq:
                where.append(uq)
                v.extend(uv)

            q += " where " + (" and ".join(where))

        # self.log("q2: {} {}".format(q, repr(v)))

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

                rp = os.path.join(vtop, rd, fn).replace("\\", "/")
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


def _open(ptop):
    db_path = os.path.join(ptop, ".hist", "up2k.db")
    if os.path.exists(db_path):
        return sqlite3.connect(db_path).cursor()


def _conv_sz(q, body, k, sql):
    if k in body:
        q[sql] = int(float(body[k]) * 1024 * 1024)


def _conv_dt(q, body, k, sql):
    if k not in body:
        return

    v = body[k].upper().rstrip("Z").replace(",", " ").replace("T", " ")
    while "  " in v:
        v = v.replace("  ", " ")

    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H", "%Y-%m-%d"]:
        try:
            ts = datetime.strptime(v, fmt).timestamp()
            break
        except:
            ts = None

    if ts:
        q[sql] = ts


def _conv_txt(q, body, k, sql):
    for v in body[k].split(" "):
        inv = ""
        if v.startswith("-"):
            inv = "not"
            v = v[1:]

        if not v:
            continue

        head = "'%'||"
        if v.startswith("^"):
            head = ""
            v = v[1:]

        tail = "||'%'"
        if v.endswith("$"):
            tail = ""
            v = v[:-1]

        qk = "{} {} like {}?{}".format(sql, inv, head, tail)
        q[qk + "\n" + v] = u8safe(v)


def _conv_adv(q, body, k):
    ptn = re.compile(r"^(\.?[a-z]+) *(==?|!=|<=?|>=?) *(.*)$")

    parts = body[k].split(" ")
    parts = [x.strip() for x in parts if x.strip()]

    for part in parts:
        m = ptn.match(part)
        if not m:
            p = html_escape(part)
            raise Pebkac(400, "invalid argument [" + p + "]")

        k, op, v = m.groups()
        qk = "mt.k = '{}' and mt.v {} ?".format(k, op)
        q[qk + "\n" + v] = u8safe(v)


def _sqlize(qobj):
    keys = []
    values = []
    for k, v in sorted(qobj.items()):
        keys.append(k.split("\n")[0])
        values.append(v)

    return " and ".join(keys), values

# coding: utf-8
from __future__ import print_function, unicode_literals

import os
from datetime import datetime

from .util import u8safe
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

        if not HAVE_SQLITE3:
            self.log("could not load sqlite3; searchign wqill be disabled")
            return

        self.cur = {}

    def log(self, msg):
        self.log_func("u2idx", msg)

    def fsearch(self, vols, body):
        """search by up2k hashlist"""
        if not HAVE_SQLITE3:
            return []

        fsize = body["size"]
        fhash = body["hash"]
        wark = up2k_wark_from_hashlist(self.args.salt, fsize, fhash)
        return self.run_query(vols, "w = ?", [wark], "", [])

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

        tq = ""
        tv = []
        qobj = {}
        if "tags" in body:
            _conv_txt(qobj, body, "tags", "mt.v")
            tq, tv = _sqlize(qobj)

        return self.run_query(vols, uq, uv, tq, tv)

    def run_query(self, vols, uq, uv, tq, tv):
        self.log("qs: {} {} ,  {} {}".format(uq, repr(uv), tq, repr(tv)))

        ret = []
        lim = 1000
        taglist = {}
        for (vtop, ptop, flags) in vols:
            cur = self.get_cur(ptop)
            if not cur:
                continue

            if not tq:
                if not uq:
                    q = "select * from up"
                    v = ()
                else:
                    q = "select * from up where " + uq
                    v = tuple(uv)
            else:
                # naive assumption: tags first
                q = "select up.* from up inner join mt on substr(up.w,1,16) = mt.w where {}"
                q = q.format(" and ".join([tq, uq]) if uq else tq)
                v = tuple(tv + uv)

            sret = []
            c = cur.execute(q, v)
            for hit in c:
                w, ts, sz, rd, fn = hit
                lim -= 1
                if lim <= 0:
                    break

                rp = os.path.join(vtop, rd, fn).replace("\\", "/")
                sret.append({"ts": int(ts), "sz": sz, "rp": rp, "w": w[:16]})

            for hit in sret:
                w = hit["w"]
                del hit["w"]
                tags = {}
                q = "select k, v from mt where w = ?"
                for k, v in cur.execute(q, (w,)):
                    taglist[k] = True
                    tags[k] = v

                hit["tags"] = tags

            ret.extend(sret)

        return ret, taglist.keys()


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


def _sqlize(qobj):
    keys = []
    values = []
    for k, v in sorted(qobj.items()):
        keys.append(k.split("\n")[0])
        values.append(v)

    return " and ".join(keys), values

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

        self.dbs = {}

    def log(self, msg):
        self.log_func("u2idx", msg)

    def fsearch(self, vols, body):
        """search by up2k hashlist"""
        if not HAVE_SQLITE3:
            return []

        fsize = body["size"]
        fhash = body["hash"]
        wark = up2k_wark_from_hashlist(self.args.salt, fsize, fhash)
        return self.run_query(vols, "select * from up where w = ?", [wark])

    def search(self, vols, body):
        """search by query params"""
        if not HAVE_SQLITE3:
            return []

        qobj = {}
        _conv_sz(qobj, body, "sz_min", "sz >= ?")
        _conv_sz(qobj, body, "sz_max", "sz <= ?")
        _conv_dt(qobj, body, "dt_min", "mt >= ?")
        _conv_dt(qobj, body, "dt_max", "mt <= ?")
        for seg, dk in [["path", "rd"], ["name", "fn"]]:
            if seg in body:
                _conv_txt(qobj, body, seg, dk)

        qstr = "select * from up"
        qv = []
        if qobj:
            qk = []
            for k, v in sorted(qobj.items()):
                qk.append(k.split("\n")[0])
                qv.append(v)

            qstr = " and ".join(qk)
            qstr = "select * from up where " + qstr

        return self.run_query(vols, qstr, qv)

    def run_query(self, vols, qstr, qv):
        qv = tuple(qv)
        self.log("qs: {} {}".format(qstr, repr(qv)))

        ret = []
        lim = 100
        for (vtop, ptop, flags) in vols:
            db = self.dbs.get(ptop)
            if not db:
                db = _open(ptop)
                if not db:
                    continue

                self.dbs[ptop] = db
                # self.log("idx /{} @ {} {}".format(vtop, ptop, flags))

            c = db.execute(qstr, qv)
            for _, ts, sz, rd, fn in c:
                lim -= 1
                if lim <= 0:
                    break

                rp = os.path.join(vtop, rd, fn).replace("\\", "/")
                ret.append({"ts": int(ts), "sz": sz, "rp": rp})

        return ret


def _open(ptop):
    db_path = os.path.join(ptop, ".hist", "up2k.db")
    if os.path.exists(db_path):
        return sqlite3.connect(db_path)


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

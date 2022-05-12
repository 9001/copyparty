# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import time
import threading
from datetime import datetime
from operator import itemgetter

from .__init__ import ANYWIN, unicode
from .util import absreal, s3dec, Pebkac, min_ex, gen_filekey, quotep
from .bos import bos
from .up2k import up2k_wark_from_hashlist


try:
    HAVE_SQLITE3 = True
    import sqlite3
except:
    HAVE_SQLITE3 = False


try:
    from pathlib import Path
except:
    pass


class U2idx(object):
    def __init__(self, conn):
        self.log_func = conn.log_func
        self.asrv = conn.asrv
        self.args = conn.args
        self.timeout = self.args.srch_time

        if not HAVE_SQLITE3:
            self.log("your python does not have sqlite3; searching will be disabled")
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
            return self.run_query(vols, uq, uv, True, False, 99999)[0]
        except:
            raise Pebkac(500, min_ex())

    def get_cur(self, ptop):
        if not HAVE_SQLITE3:
            return None

        cur = self.cur.get(ptop)
        if cur:
            return cur

        histpath = self.asrv.vfs.histtab.get(ptop)
        if not histpath:
            self.log("no histpath for [{}]".format(ptop))
            return None

        db_path = os.path.join(histpath, "up2k.db")
        if not bos.path.exists(db_path):
            return None

        cur = None
        if ANYWIN:
            uri = ""
            try:
                uri = "{}?mode=ro&nolock=1".format(Path(db_path).as_uri())
                cur = sqlite3.connect(uri, 2, uri=True).cursor()
                self.log("ro: {}".format(db_path))
            except:
                self.log("could not open read-only: {}\n{}".format(uri, min_ex()))

        if not cur:
            # on windows, this steals the write-lock from up2k.deferred_init --
            # seen on win 10.0.17763.2686, py 3.10.4, sqlite 3.37.2
            cur = sqlite3.connect(db_path, 2).cursor()
            self.log("opened {}".format(db_path))

        self.cur[ptop] = cur
        return cur

    def search(self, vols, uq, lim):
        """search by query params"""
        if not HAVE_SQLITE3:
            return []

        q = ""
        va = []
        have_up = False  # query has up.* operands
        have_mt = False
        is_key = True
        is_size = False
        is_date = False
        field_end = ""  # closing parenthesis or whatever
        kw_key = ["(", ")", "and ", "or ", "not "]
        kw_val = ["==", "=", "!=", ">", ">=", "<", "<=", "like "]
        ptn_mt = re.compile(r"^\.?[a-z_-]+$")
        ptn_lc = re.compile(r" (mt\.v) ([=<!>]+) \? \) $")
        ptn_lcv = re.compile(r"[a-zA-Z]")

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

            if uq.startswith('"'):
                v, uq = uq[1:].split('"', 1)
                while v.endswith("\\"):
                    v2, uq = uq.split('"', 1)
                    v = v[:-1] + '"' + v2
                uq = uq.strip()
            else:
                v, uq = (uq + " ").split(" ", 1)
                v = v.replace('\\"', '"')

            if is_key:
                is_key = False

                if v == "size":
                    v = "up.sz"
                    is_size = True
                    have_up = True

                elif v == "date":
                    v = "up.mt"
                    is_date = True
                    have_up = True

                elif v == "path":
                    v = "trim(?||up.rd,'/')"
                    va.append("\nrd")
                    have_up = True

                elif v == "name":
                    v = "up.fn"
                    have_up = True

                elif v == "tags" or ptn_mt.match(v):
                    have_mt = True
                    field_end = ") "
                    if v == "tags":
                        vq = "mt.v"
                    else:
                        vq = "+mt.k = '{}' and mt.v".format(v)

                    v = "exists(select 1 from mt where mt.w = mtw and " + vq

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

            if field_end:
                q += field_end
                field_end = ""

            # lowercase tag searches
            m = ptn_lc.search(q)
            if not m or not ptn_lcv.search(unicode(v)):
                continue

            va.pop()
            va.append(v.lower())
            q = q[: m.start()]

            field, oper = m.groups()
            if oper in ["=", "=="]:
                q += " {} like ? ) ".format(field)
            else:
                q += " lower({}) {} ? ) ".format(field, oper)

        try:
            return self.run_query(vols, q, va, have_up, have_mt, lim)
        except Exception as ex:
            raise Pebkac(500, repr(ex))

    def run_query(self, vols, uq, uv, have_up, have_mt, lim):
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
            uq = "select * from up"
            uv = ()
        elif have_mt:
            uq = "select up.*, substr(up.w,1,16) mtw from up where " + uq
            uv = tuple(uv)
        else:
            uq = "select up.* from up where " + uq
            uv = tuple(uv)

        self.log("qs: {!r} {!r}".format(uq, uv))

        ret = []
        lim = min(lim, int(self.args.srch_hits))
        taglist = {}
        for (vtop, ptop, flags) in vols:
            cur = self.get_cur(ptop)
            if not cur:
                continue

            self.active_cur = cur

            vuv = []
            for v in uv:
                if v == "\nrd":
                    v = vtop + "/"

                vuv.append(v)
            vuv = tuple(vuv)

            sret = []
            fk = flags.get("fk")
            c = cur.execute(uq, vuv)
            for hit in c:
                w, ts, sz, rd, fn, ip, at = hit[:7]
                lim -= 1
                if lim < 0:
                    break

                if rd.startswith("//") or fn.startswith("//"):
                    rd, fn = s3dec(rd, fn)

                if not fk:
                    suf = ""
                else:
                    try:
                        ap = absreal(os.path.join(ptop, rd, fn))
                        inf = bos.stat(ap)
                    except:
                        continue

                    suf = (
                        "?k="
                        + gen_filekey(
                            self.args.fk_salt, ap, sz, 0 if ANYWIN else inf.st_ino
                        )[:fk]
                    )

                rp = quotep("/".join([x for x in [vtop, rd, fn] if x])) + suf
                sret.append({"ts": int(ts), "sz": sz, "rp": rp, "w": w[:16]})

            for hit in sret:
                w = hit["w"]
                del hit["w"]
                tags = {}
                q2 = "select k, v from mt where w = ? and +k != 'x'"
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
                y
                for x, y in zip(ret[:-1], ret[1:])
                if x["rp"].split("?")[0] != y["rp"].split("?")[0]
            ]

        ret.sort(key=itemgetter("rp"))

        return ret, list(taglist.keys())

    def terminator(self, identifier, done_flag):
        for _ in range(self.timeout):
            time.sleep(1)
            if done_flag:
                return

        if identifier == self.active_id:
            self.active_cur.connection.interrupt()

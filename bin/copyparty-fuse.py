#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

"""copyparty-fuse: remote copyparty as a local filesystem"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"

import re
import sys
import time
import stat
import errno
import threading
import http.client  # py2: httplib
import urllib.parse
from datetime import datetime
from fuse import FUSE, FuseOSError, Operations
from urllib.parse import quote_from_bytes as quote


"""
mount a copyparty server (local or remote) as a filesystem

expect ~32 MiB/s on LAN, should probably read larger chunks

usage:
  python copyparty-fuse.py ./music http://192.168.1.69:1234/

dependencies:
  sudo apk add fuse-dev
  python3 -m venv ~/pe/ve.fusepy
  . ~/pe/ve.fusepy/bin/activate
  pip install fusepy
"""


def log(msg):
    msg = "{:012x} {}\n".format(threading.current_thread().ident, msg)
    print(msg[4:], end="")


def get_tid():
    return threading.current_thread().ident


class CacheNode(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.ts = time.time()


class Gateway(object):
    def __init__(self, base_url):
        self.base_url = base_url

        ui = urllib.parse.urlparse(base_url)
        self.web_root = ui.path.strip("/")
        try:
            self.web_host, self.web_port = ui.netloc.split(":")
            self.web_port = int(self.web_port)
        except:
            self.web_host = ui.netloc
            if ui.scheme == "http":
                self.web_port = 80
            elif ui.scheme == "https":
                raise Exception("todo")
            else:
                raise Exception("bad url?")

        self.conns = {}

    def quotep(self, path):
        # TODO: mojibake support
        path = path.encode("utf-8", "ignore")
        return quote(path, safe="/")

    def getconn(self, tid=None):
        tid = tid or get_tid()
        try:
            return self.conns[tid]
        except:
            log("new conn [{}] [{}]".format(self.web_host, self.web_port))

            conn = http.client.HTTPConnection(self.web_host, self.web_port, timeout=260)

            self.conns[tid] = conn
            return conn

    def closeconn(self, tid=None):
        tid = tid or get_tid()
        try:
            self.conns[tid].close()
            del self.conns[tid]
        except:
            pass

    def sendreq(self, *args, **kwargs):
        tid = get_tid()
        try:
            c = self.getconn(tid)
            c.request(*list(args), **kwargs)
            return c.getresponse()
        except:
            self.closeconn(tid)
            c = self.getconn(tid)
            c.request(*list(args), **kwargs)
            return c.getresponse()

    def listdir(self, path):
        web_path = "/" + "/".join([self.web_root, path])

        r = self.sendreq("GET", self.quotep(web_path))
        if r.status != 200:
            self.closeconn()
            raise Exception(
                "http error {} reading dir {} in {:x}".format(
                    r.status, web_path, get_tid()
                )
            )

        return self.parse_html(r)

    def getfile(self, path, ofs1, ofs2):
        web_path = "/" + "/".join([self.web_root, path])
        hdr_range = "bytes={}-{}".format(ofs1, ofs2)

        r = self.sendreq("GET", self.quotep(web_path), headers={"Range": hdr_range})
        if r.status != http.client.PARTIAL_CONTENT:
            self.closeconn()
            raise Exception(
                "http error {} reading file {} range {} in {:x}".format(
                    r.status, web_path, hdr_range, get_tid()
                )
            )

        return r.read()

    def parse_html(self, datasrc):
        ret = []
        remainder = b""
        ptn = re.compile(
            r"^<tr><td>(-|DIR)</td><td><a [^>]+>([^<]+)</a></td><td>([^<]+)</td><td>([^<]+)</td></tr>$"
        )

        while True:
            buf = remainder + datasrc.read(4096)
            # print('[{}]'.format(buf.decode('utf-8')))
            if not buf:
                break

            remainder = b""
            endpos = buf.rfind(b"\n")
            if endpos >= 0:
                remainder = buf[endpos + 1 :]
                buf = buf[:endpos]

            lines = buf.decode("utf-8").split("\n")
            for line in lines:
                m = ptn.match(line)
                if not m:
                    # print(line)
                    continue

                ftype, fname, fsize, fdate = m.groups()
                ts = datetime.strptime(fdate, "%Y-%m-%d %H:%M:%S").timestamp()
                sz = int(fsize)
                if ftype == "-":
                    ret.append([fname, self.stat_file(ts, sz), 0])
                else:
                    ret.append([fname, self.stat_dir(ts, sz), 0])

        return ret

    def stat_dir(self, ts, sz=4096):
        return {
            "st_mode": 0o555 | stat.S_IFDIR,
            "st_uid": 1000,
            "st_gid": 1000,
            "st_size": sz,
            "st_atime": ts,
            "st_mtime": ts,
            "st_ctime": ts,
            "st_blocks": int((sz + 511) / 512),
        }

    def stat_file(self, ts, sz):
        return {
            "st_mode": 0o444 | stat.S_IFREG,
            "st_uid": 1000,
            "st_gid": 1000,
            "st_size": sz,
            "st_atime": ts,
            "st_mtime": ts,
            "st_ctime": ts,
            "st_blocks": int((sz + 511) / 512),
        }


class CPPF(Operations):
    def __init__(self, base_url):
        self.gw = Gateway(base_url)

        self.dircache = []
        self.dircache_mtx = threading.Lock()

        log("up")

    def clean_dircache(self):
        """not threadsafe"""
        now = time.time()
        cutoff = 0
        for cn in self.dircache:
            if cn.ts - now > 1:
                cutoff += 1
            else:
                break

        if cutoff > 0:
            self.dircache = self.dircache[cutoff:]

    def get_cached_dir(self, dirpath):
        with self.dircache_mtx:
            self.clean_dircache()
            for cn in self.dircache:
                if cn.name == dirpath:
                    return cn

        return None

    def readdir(self, path, fh=None):
        path = path.strip("/")
        log("readdir {}".format(path))

        ret = self.gw.listdir(path)

        with self.dircache_mtx:
            cn = CacheNode(path, ret)
            self.dircache.append(cn)
            self.clean_dircache()

        return ret

    def read(self, path, length, offset, fh=None):
        path = path.strip("/")

        ofs2 = offset + length - 1
        log("read {} @ {} len {} end {}".format(path, offset, length, ofs2))

        file_sz = self.getattr(path)["st_size"]
        if ofs2 >= file_sz:
            ofs2 = file_sz - 1
            log("truncate to len {} end {}".format((ofs2 - offset) + 1, ofs2))

        return self.gw.getfile(path, offset, ofs2)

    def getattr(self, path, fh=None):
        path = path.strip("/")
        try:
            dirpath, fname = path.rsplit("/", 1)
        except:
            dirpath = ""
            fname = path

        log("getattr {}".format(path))

        if not path:
            return self.gw.stat_dir(time.time())

        cn = self.get_cached_dir(dirpath)
        if cn:
            # log('cache ok')
            dents = cn.data
        else:
            log("cache miss")
            dents = self.readdir(dirpath)

        for cache_name, cache_stat, _ in dents:
            if cache_name == fname:
                return cache_stat

        raise FuseOSError(errno.ENOENT)

    access = None
    flush = None
    getxattr = None
    listxattr = None
    open = None
    opendir = None
    release = None
    releasedir = None
    statfs = None


def main():
    try:
        local, remote = sys.argv[1:]
    except:
        print("need arg 1: local directory")
        print("need arg 2: root url")
        return

    FUSE(CPPF(remote), local, foreground=True)


if __name__ == "__main__":
    main()

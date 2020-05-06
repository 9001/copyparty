# coding: utf-8
from __future__ import print_function, unicode_literals


import os
import re
import time
import math
import shutil
import base64
import hashlib
import threading
from copy import deepcopy

from .__init__ import WINDOWS
from .util import Pebkac, Queue, fsenc, sanitize_fn


class Up2k(object):
    """
    TODO:
      * documentation
      * registry persistence
        * ~/.config flatfiles for active jobs
        * wark->path database for finished uploads
    """

    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args
        self.log = broker.log

        # config
        self.salt = "hunter2"  # TODO: config

        # state
        self.registry = {}
        self.mutex = threading.Lock()

        if WINDOWS:
            # usually fails to set lastmod too quickly
            self.lastmod_q = Queue()
            thr = threading.Thread(target=self._lastmodder)
            thr.daemon = True
            thr.start()

        # static
        self.r_hash = re.compile("^[0-9a-zA-Z_-]{43}$")

    def handle_json(self, cj):
        cj["name"] = sanitize_fn(cj["name"])
        wark = self._get_wark(cj)
        now = time.time()
        with self.mutex:
            # TODO use registry persistence here to symlink any matching wark
            if wark in self.registry:
                job = self.registry[wark]
                if job["rdir"] != cj["rdir"] or job["name"] != cj["name"]:
                    src = os.path.join(job["rdir"], job["name"])
                    dst = os.path.join(cj["rdir"], cj["name"])
                    if job["need"]:
                        self.log("up2k", "unfinished:\n  {0}\n  {1}".format(src, dst))
                        err = "partial upload exists at a different location; please resume uploading here instead:\n{0}{1} ".format(
                            job["vdir"], job["name"]
                        )
                        raise Pebkac(400, err)
                    else:
                        # symlink to the client-provided name,
                        # returning the previous upload info
                        job = deepcopy(job)
                        suffix = self._suffix(dst, now, job["addr"])
                        job["name"] = cj["name"] + suffix
                        self._symlink(src, dst + suffix)
            else:
                job = {
                    "wark": wark,
                    "t0": now,
                    "addr": cj["addr"],
                    "vdir": cj["vdir"],
                    "rdir": cj["rdir"],
                    # client-provided, sanitized by _get_wark:
                    "name": cj["name"],
                    "size": cj["size"],
                    "lmod": cj["lmod"],
                    "hash": deepcopy(cj["hash"]),
                }

                path = os.path.join(job["rdir"], job["name"])
                job["name"] += self._suffix(path, now, cj["addr"])

                # one chunk may occur multiple times in a file;
                # filter to unique values for the list of missing chunks
                # (preserve order to reduce disk thrashing)
                job["need"] = []
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

    def _suffix(self, fpath, ts, ip):
        # TODO broker which avoid this race and
        # provides a new filename if taken (same as bup)
        if not os.path.exists(fsenc(fpath)):
            return ""

        return ".{:.6f}-{}".format(ts, ip)

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
            self.log("up2k", "cannot symlink; creating copy")
            shutil.copy2(fsenc(src), fsenc(dst))

    def handle_chunk(self, wark, chash):
        with self.mutex:
            job = self.registry.get(wark)
            if not job:
                raise Pebkac(404, "unknown wark")

            if chash not in job["need"]:
                raise Pebkac(200, "already got that but thanks??")

            nchunk = [n for n, v in enumerate(job["hash"]) if v == chash]
            if not nchunk:
                raise Pebkac(404, "unknown chunk")

        chunksize = self._get_chunksize(job["size"])
        ofs = [chunksize * x for x in nchunk]

        path = os.path.join(job["rdir"], job["name"])

        return [chunksize, ofs, path, job["lmod"]]

    def confirm_chunk(self, wark, chash):
        with self.mutex:
            job = self.registry[wark]
            job["need"].remove(chash)
            ret = len(job["need"])

            if WINDOWS and ret == 0:
                path = os.path.join(job["rdir"], job["name"])
                self.lastmod_q.put([path, (int(time.time()), int(job["lmod"]))])

            return ret

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

        # server-reproducible file identifier, independent of name or location
        ident = [self.salt, str(cj["size"])]
        ident.extend(cj["hash"])
        ident = "\n".join(ident)

        hasher = hashlib.sha512()
        hasher.update(ident.encode("utf-8"))
        digest = hasher.digest()[:32]

        wark = base64.urlsafe_b64encode(digest)
        return wark.decode("utf-8").rstrip("=")

    def _new_upload(self, job):
        self.registry[job["wark"]] = job
        path = os.path.join(job["rdir"], job["name"])
        with open(fsenc(path), "wb") as f:
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

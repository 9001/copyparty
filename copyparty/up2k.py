# coding: utf-8
from __future__ import print_function, unicode_literals


import os
import re
import time
import math
import base64
import hashlib
import threading
from copy import deepcopy

from .util import Pebkac


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

        # static
        self.r_hash = re.compile("^[0-9a-zA-Z_-]{43}$")

    def handle_json(self, cj):
        wark = self._get_wark(cj)
        with self.mutex:
            try:
                job = self.registry[wark]
                if job["vdir"] != cj["vdir"] or job["name"] != cj["name"]:
                    print("\n".join([job["vdir"], cj["vdir"], job["name"], cj["name"]]))
                    raise Pebkac(400, "unexpected filepath")

            except KeyError:
                job = {
                    "wark": wark,
                    "t0": int(time.time()),
                    "addr": cj["addr"],
                    "vdir": cj["vdir"],
                    # client-provided, sanitized by _get_wark:
                    "name": cj["name"],
                    "size": cj["size"],
                    "hash": deepcopy(cj["hash"]),
                }

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
                "hash": job["need"],
                "wark": wark,
            }

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

        path = os.path.join(job["vdir"], job["name"])

        return [chunksize, ofs, path]

    def confirm_chunk(self, wark, chash):
        with self.mutex:
            self.registry[wark]["need"].remove(chash)

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
        if len(cj["name"]) > 1024 or len(cj["hash"]) > 256:
            raise Pebkac(400, "name or numchunks not according to spec")

        for k in cj["hash"]:
            if not self.r_hash.match(k):
                raise Pebkac(
                    400, "at least one hash is not according to spec: {}".format(k)
                )

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
        path = os.path.join(job["vdir"], job["name"])
        with open(path, "wb") as f:
            f.seek(job["size"] - 1)
            f.write(b"e")


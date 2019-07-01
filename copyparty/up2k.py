# coding: utf-8
from __future__ import print_function, unicode_literals


import re
import base64
import hashlib

from .util import Pebkac


class Up2k(object):
    def __init__(self, broker):
        self.broker = broker
        self.args = broker.args
        self.log = broker.log

        self.salt = "hunter2"  # TODO: config

        self.r_hash = re.compile("^[0-9a-zA-Z_-]{43}$")

    def _get_wark(self, j):
        if len(j["name"]) > 4096 or len(j["hash"]) > 256:
            raise Pebkac(400, "bad name or numchunks")

        for k in j["hash"]:
            if not self.r_hash.match(k):
                raise Pebkac(400, "at least one bad hash")

        plaintext = "\n".join([self.salt, j["name"], str(j["size"]), *j["hash"]])

        hasher = hashlib.sha512()
        hasher.update(plaintext.encode("utf-8"))
        digest = hasher.digest()[:32]

        wark = base64.urlsafe_b64encode(digest)
        return wark.decode("utf-8").rstrip("=")

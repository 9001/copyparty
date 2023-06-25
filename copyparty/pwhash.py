# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import base64
import hashlib
import sys
import threading

from .__init__ import unicode


class PWHash(object):
    def __init__(self, args: argparse.Namespace):
        self.args = args

        try:
            alg, ac = args.ah_alg.split(",")
        except:
            alg = args.ah_alg
            ac = {}

        self.alg = alg
        self.ac = ac
        if alg == "none":
            self.on = False
            self.hash = unicode
            return

        self.on = True
        self.salt = args.ah_salt.encode("utf-8")
        self.cache: dict[str, str] = {}
        self.mutex = threading.Lock()
        self.hash = self._cache_hash

        if alg == "sha2":
            self._hash = self._gen_sha2
        elif alg == "scrypt":
            self._hash = self._gen_scrypt
        elif alg == "argon2":
            self._hash = self._gen_argon2
        else:
            t = "unsupported password hashing algorithm [{}], must be one of these: argon2 scrypt sha2 none"
            raise Exception(t.format(alg))

    def _cache_hash(self, plain: str) -> str:
        with self.mutex:
            try:
                return self.cache[plain]
            except:
                pass

            if not plain:
                return ""

            if len(plain) > 255:
                raise Exception("password too long")

            if len(self.cache) > 9000:
                self.cache = {}

            ret = self._hash(plain)
            self.cache[plain] = ret
            return ret

    def _gen_sha2(self, plain: str) -> str:
        its = int(self.ac[0]) if self.ac else 424242
        bplain = plain.encode("utf-8")
        ret = b"\n"
        for _ in range(its):
            ret = hashlib.sha512(self.salt + bplain + ret).digest()

        return "+" + base64.urlsafe_b64encode(ret[:24]).decode("utf-8")

    def _gen_scrypt(self, plain: str) -> str:
        cost = 2 << 13
        its = 2
        blksz = 8
        para = 4
        try:
            cost = 2 << int(self.ac[0])
            its = int(self.ac[1])
            blksz = int(self.ac[2])
            para = int(self.ac[3])
        except:
            pass

        ret = plain.encode("utf-8")
        for _ in range(its):
            ret = hashlib.scrypt(ret, salt=self.salt, n=cost, r=blksz, p=para, dklen=24)

        return "+" + base64.urlsafe_b64encode(ret).decode("utf-8")

    def _gen_argon2(self, plain: str) -> str:
        from argon2.low_level import Type as ArgonType
        from argon2.low_level import hash_secret

        time_cost = 3
        mem_cost = 256
        parallelism = 4
        version = 19
        try:
            time_cost = int(self.ac[0])
            mem_cost = int(self.ac[1])
            parallelism = int(self.ac[2])
            version = int(self.ac[3])
        except:
            pass

        bplain = plain.encode("utf-8")

        bret = hash_secret(
            secret=bplain,
            salt=self.salt,
            time_cost=time_cost,
            memory_cost=mem_cost * 1024,
            parallelism=parallelism,
            hash_len=24,
            type=ArgonType.ID,
            version=version,
        )
        ret = bret.split(b"$")[-1].decode("utf-8")
        return "+" + ret.replace("/", "_").replace("+", "-")

    def stdin(self) -> None:
        while True:
            ln = sys.stdin.readline().strip()
            if not ln:
                break
            print(self.hash(ln))

    def cli(self) -> None:
        import getpass

        while True:
            p1 = getpass.getpass("password> ")
            p2 = getpass.getpass("again or just hit ENTER> ")
            if p2 and p1 != p2:
                print("\033[31minputs don't match; try again\033[0m", file=sys.stderr)
                continue
            print(self.hash(p1))
            print()

#!/usr/bin/env python3

import sys
import json
import zlib
import struct
import base64
import hashlib

try:
    from copyparty.util import fsenc
except:

    def fsenc(p):
        return p


"""
calculates various checksums for uploads,
usage: -mtp crc32,md5,sha1,sha256b=bin/mtag/cksum.py
"""


def main():
    config = "crc32 md5 md5b sha1 sha1b sha256 sha256b sha512/240 sha512b/240"
    # b suffix = base64 encoded
    # slash = truncate to n bits

    known = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }
    config = config.split()
    hashers = {
        k: v()
        for k, v in known.items()
        if k in [x.split("/")[0].rstrip("b") for x in known]
    }
    crc32 = 0 if "crc32" in config else None

    with open(fsenc(sys.argv[1]), "rb", 512 * 1024) as f:
        while True:
            buf = f.read(64 * 1024)
            if not buf:
                break

            for x in hashers.values():
                x.update(buf)

            if crc32 is not None:
                crc32 = zlib.crc32(buf, crc32)

    ret = {}
    for s in config:
        alg = s.split("/")[0]
        b64 = alg.endswith("b")
        alg = alg.rstrip("b")
        if alg in hashers:
            v = hashers[alg].digest()
        elif alg == "crc32":
            v = crc32
            if v < 0:
                v &= 2 ** 32 - 1
            v = struct.pack(">L", v)
        else:
            raise Exception("what is {}".format(s))

        if "/" in s:
            v = v[: int(int(s.split("/")[1]) / 8)]

        if b64:
            v = base64.b64encode(v).decode("ascii").rstrip("=")
        else:
            try:
                v = v.hex()
            except:
                import binascii

                v = binascii.hexlify(v)

        ret[s] = v

    print(json.dumps(ret, indent=4))


if __name__ == "__main__":
    main()

# coding: utf-8
from __future__ import print_function, unicode_literals

import os
from ..util import fsenc, fsdec, SYMTIME
from . import path


# grep -hRiE '(^|[^a-zA-Z_\.-])os\.' . | gsed -r 's/ /\n/g;s/\(/(\n/g' | grep -hRiE '(^|[^a-zA-Z_\.-])os\.' | sort | uniq -c
# printf 'os\.(%s)' "$(grep ^def bos/__init__.py | gsed -r 's/^def //;s/\(.*//' | tr '\n' '|' | gsed -r 's/.$//')"


def chmod(p, mode):
    return os.chmod(fsenc(p), mode)


def listdir(p="."):
    return [fsdec(x) for x in os.listdir(fsenc(p))]


def makedirs(name, mode=0o755, exist_ok=True):
    bname = fsenc(name)
    try:
        os.makedirs(bname, mode)
    except:
        if not exist_ok or not os.path.isdir(bname):
            raise


def mkdir(p, mode=0o755):
    return os.mkdir(fsenc(p), mode)


def rename(src, dst):
    return os.rename(fsenc(src), fsenc(dst))


def replace(src, dst):
    return os.replace(fsenc(src), fsenc(dst))


def rmdir(p):
    return os.rmdir(fsenc(p))


def stat(p):
    return os.stat(fsenc(p))


def unlink(p):
    return os.unlink(fsenc(p))


def utime(p, times=None, follow_symlinks=True):
    if SYMTIME:
        return os.utime(fsenc(p), times, follow_symlinks=follow_symlinks)
    else:
        return os.utime(fsenc(p), times)


if hasattr(os, "lstat"):

    def lstat(p):
        return os.lstat(fsenc(p))

else:
    lstat = stat

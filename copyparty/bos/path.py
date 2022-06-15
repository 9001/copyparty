# coding: utf-8
from __future__ import print_function, unicode_literals

import os

from ..util import SYMTIME, fsdec, fsenc


def abspath(p: str) -> str:
    return fsdec(os.path.abspath(fsenc(p)))


def exists(p: str) -> bool:
    return os.path.exists(fsenc(p))


def getmtime(p: str, follow_symlinks: bool = True) -> float:
    if not follow_symlinks and SYMTIME:
        return os.lstat(fsenc(p)).st_mtime
    else:
        return os.path.getmtime(fsenc(p))


def getsize(p: str) -> int:
    return os.path.getsize(fsenc(p))


def isfile(p: str) -> bool:
    return os.path.isfile(fsenc(p))


def isdir(p: str) -> bool:
    return os.path.isdir(fsenc(p))


def islink(p: str) -> bool:
    return os.path.islink(fsenc(p))


def lexists(p: str) -> bool:
    return os.path.lexists(fsenc(p))


def realpath(p: str) -> str:
    return fsdec(os.path.realpath(fsenc(p)))

# coding: utf-8
from __future__ import print_function, unicode_literals

import os

from ..util import SYMTIME, fsdec, fsenc
from . import path as path

if True:  # pylint: disable=using-constant-test
    from typing import Any, Optional

_ = (path,)
__all__ = ["path"]

# grep -hRiE '(^|[^a-zA-Z_\.-])os\.' . | gsed -r 's/ /\n/g;s/\(/(\n/g' | grep -hRiE '(^|[^a-zA-Z_\.-])os\.' | sort | uniq -c
# printf 'os\.(%s)' "$(grep ^def bos/__init__.py | gsed -r 's/^def //;s/\(.*//' | tr '\n' '|' | gsed -r 's/.$//')"


def chmod(p: str, mode: int) -> None:
    return os.chmod(fsenc(p), mode)


def listdir(p: str = ".") -> list[str]:
    return [fsdec(x) for x in os.listdir(fsenc(p))]


def makedirs(name: str, mode: int = 0o755, exist_ok: bool = True) -> bool:
    bname = fsenc(name)
    try:
        os.makedirs(bname, mode)
        return True
    except:
        if not exist_ok or not os.path.isdir(bname):
            raise
        return False


def mkdir(p: str, mode: int = 0o755) -> None:
    return os.mkdir(fsenc(p), mode)


def open(p: str, *a, **ka) -> int:
    return os.open(fsenc(p), *a, **ka)


def rename(src: str, dst: str) -> None:
    return os.rename(fsenc(src), fsenc(dst))


def replace(src: str, dst: str) -> None:
    return os.replace(fsenc(src), fsenc(dst))


def rmdir(p: str) -> None:
    return os.rmdir(fsenc(p))


def stat(p: str) -> os.stat_result:
    return os.stat(fsenc(p))


def unlink(p: str) -> None:
    return os.unlink(fsenc(p))


def utime(
    p: str, times: Optional[tuple[float, float]] = None, follow_symlinks: bool = True
) -> None:
    if SYMTIME:
        return os.utime(fsenc(p), times, follow_symlinks=follow_symlinks)
    else:
        return os.utime(fsenc(p), times)


if hasattr(os, "lstat"):

    def lstat(p: str) -> os.stat_result:
        return os.lstat(fsenc(p))

else:
    lstat = stat

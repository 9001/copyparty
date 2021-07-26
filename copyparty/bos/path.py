# coding: utf-8
from __future__ import print_function, unicode_literals

import os
from ..util import fsenc, fsdec


def abspath(p):
    return fsdec(os.path.abspath(fsenc(p)))


def exists(p):
    return os.path.exists(fsenc(p))


def getmtime(p):
    return os.path.getmtime(fsenc(p))


def getsize(p):
    return os.path.getsize(fsenc(p))


def isdir(p):
    return os.path.isdir(fsenc(p))


def islink(p):
    return os.path.islink(fsenc(p))


def realpath(p):
    return fsdec(os.path.realpath(fsenc(p)))

#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import pprint
import threading

from .__init__ import *


class AuthSrv(object):
    """verifies users against given paths"""

    def __init__(self, args, log_func):
        self.log_func = log_func
        self.args = args

        self.mutex = threading.Lock()
        self.reload()

    def log(self, msg):
        self.log_func("auth", msg)

    def invert(self, orig):
        if PY2:
            return {v: k for k, v in orig.iteritems()}
        else:
            return {v: k for k, v in orig.items()}

    def reload(self):
        user = {}  # username:password
        uread = {}  # username:readable-mp
        uwrite = {}  # username:writable-mp
        mount = {}  # dst:src (mountpoint:realpath)

        if self.args.a:
            # list of username:password
            for u, p in [x.split(":", 1) for x in self.args.a]:
                user[u] = p

        if self.args.v:
            # list of src:dst:permset:permset:...
            # permset is [rwa]username
            for src, dst, perms in [x.split(":", 2) for x in self.args.v]:
                src = os.path.abspath(src)
                dst = ("/" + dst.strip("/") + "/").replace("//", "/")
                mount[dst] = src
                perms = perms.split(":")
                for (lvl, uname) in [[x[0], x[1:]] for x in perms]:
                    if uname == "":
                        uname = "*"
                    if lvl in "ra":
                        uread[uname] = dst
                    if lvl in "wa":
                        uwrite[uname] = dst

        if self.args.c:
            for logfile in self.args.c:
                with open(logfile, "rb") as f:
                    for ln in [x.decode("utf-8").rstrip() for x in f]:
                        # self.log(ln)
                        pass

        with self.mutex:
            self.user = user
            self.uread = uread
            self.uwrite = uwrite
            self.mount = mount
            self.iuser = self.invert(user)
            self.iuread = self.invert(uread)
            self.iuwrite = self.invert(uwrite)
            self.imount = self.invert(mount)

        pprint.pprint(
            {
                "user": self.user,
                "uread": self.uread,
                "uwrite": self.uwrite,
                "mount": self.mount,
            }
        )

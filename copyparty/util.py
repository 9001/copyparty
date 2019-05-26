#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function


class Unrecv(object):
    """
    undo any number of socket recv ops
    """

    def __init__(self, s):
        self.s = s
        self.buf = b""

    def recv(self, nbytes):
        if self.buf:
            ret = self.buf[:nbytes]
            self.buf = self.buf[nbytes:]
            return ret

        try:
            return self.s.recv(nbytes)
        except:
            return b""

    def unrecv(self, buf):
        self.buf = buf + self.buf

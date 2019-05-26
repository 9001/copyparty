#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function


class MsgSvc(object):
    def __init__(self, log_func):
        self.log_func = log_func
        print("hi")

    def put(self, msg):
        if msg[0] == "log":
            return self.log_func(*msg[1:])

        raise Exception("bad msg type: " + str(msg))

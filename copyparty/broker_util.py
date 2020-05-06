# coding: utf-8
from __future__ import print_function, unicode_literals


import traceback

from .util import Pebkac, Queue


class ExceptionalQueue(Queue, object):
    def get(self, block=True, timeout=None):
        rv = super(ExceptionalQueue, self).get(block, timeout)

        # TODO: how expensive is this?
        if isinstance(rv, list):
            if rv[0] == "exception":
                if rv[1] == "pebkac":
                    raise Pebkac(*rv[2:])
                else:
                    raise Exception(rv[2])

        return rv


def try_exec(want_retval, func, *args):
    try:
        return func(*args)

    except Pebkac as ex:
        if not want_retval:
            raise

        return ["exception", "pebkac", ex.code, str(ex)]

    except:
        if not want_retval:
            raise

        return ["exception", "stack", traceback.format_exc()]

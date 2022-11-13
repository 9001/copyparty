# coding: utf-8

import types


class BimapError(Exception):
    pass


class Bimap(object):
    def __init__(self, name, forward, error=AttributeError):
        self.name = name
        self.error = error
        self.forward = forward.copy()
        self.reverse = dict([(v, k) for (k, v) in list(forward.items())])

    def get(self, k, default=None):
        try:
            return self.forward[k]
        except KeyError:
            return default or str(k)

    def __getitem__(self, k):
        try:
            return self.forward[k]
        except KeyError:
            if isinstance(self.error, types.FunctionType):
                return self.error(self.name, k, True)
            else:
                raise self.error("%s: Invalid forward lookup: [%s]" % (self.name, k))

    def __getattr__(self, k):
        try:
            if k == "__wrapped__":
                raise AttributeError()
            return self.reverse[k]
        except KeyError:
            if isinstance(self.error, types.FunctionType):
                return self.error(self.name, k, False)
            else:
                raise self.error("%s: Invalid reverse lookup: [%s]" % (self.name, k))

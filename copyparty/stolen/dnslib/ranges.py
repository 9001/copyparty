# coding: utf-8

import sys

if sys.version_info < (3,):
    int_types = (
        int,
        long,
    )
    byte_types = (str, bytearray)
else:
    int_types = (int,)
    byte_types = (bytes, bytearray)


def check_instance(name, val, types):
    if not isinstance(val, types):
        raise ValueError(
            "Attribute '%s' must be instance of %s [%s]" % (name, types, type(val))
        )


def check_bytes(name, val):
    return check_instance(name, val, byte_types)


def range_property(attr, min, max):
    def getter(obj):
        return getattr(obj, "_%s" % attr)

    def setter(obj, val):
        if isinstance(val, int_types) and min <= val <= max:
            setattr(obj, "_%s" % attr, val)
        else:
            raise ValueError(
                "Attribute '%s' must be between %d-%d [%s]" % (attr, min, max, val)
            )

    return property(getter, setter)


def B(attr):
    return range_property(attr, 0, 255)


def H(attr):
    return range_property(attr, 0, 65535)


def I(attr):
    return range_property(attr, 0, 4294967295)


def ntuple_range(attr, n, min, max):
    f = lambda x: isinstance(x, int_types) and min <= x <= max

    def getter(obj):
        return getattr(obj, "_%s" % attr)

    def setter(obj, val):
        if len(val) != n:
            raise ValueError(
                "Attribute '%s' must be tuple with %d elements [%s]" % (attr, n, val)
            )
        if all(map(f, val)):
            setattr(obj, "_%s" % attr, val)
        else:
            raise ValueError(
                "Attribute '%s' elements must be between %d-%d [%s]"
                % (attr, min, max, val)
            )

    return property(getter, setter)


def IP4(attr):
    return ntuple_range(attr, 4, 0, 255)


def IP6(attr):
    return ntuple_range(attr, 16, 0, 255)

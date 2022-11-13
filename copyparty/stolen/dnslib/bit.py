# coding: utf-8

from __future__ import print_function


def get_bits(data, offset, bits=1):
    mask = ((1 << bits) - 1) << offset
    return (data & mask) >> offset


def set_bits(data, value, offset, bits=1):
    mask = ((1 << bits) - 1) << offset
    clear = 0xFFFF ^ mask
    data = (data & clear) | ((value << offset) & mask)
    return data

# coding: utf-8

import binascii
import struct


class BufferError(Exception):
    pass


class Buffer(object):
    def __init__(self, data=b""):
        self.data = bytearray(data)
        self.offset = 0

    def remaining(self):
        return len(self.data) - self.offset

    def get(self, length):
        if length > self.remaining():
            raise BufferError(
                "Not enough bytes [offset=%d,remaining=%d,requested=%d]"
                % (self.offset, self.remaining(), length)
            )
        start = self.offset
        end = self.offset + length
        self.offset += length
        return bytes(self.data[start:end])

    def hex(self):
        return binascii.hexlify(self.data)

    def pack(self, fmt, *args):
        self.offset += struct.calcsize(fmt)
        self.data += struct.pack(fmt, *args)

    def append(self, s):
        self.offset += len(s)
        self.data += s

    def update(self, ptr, fmt, *args):
        s = struct.pack(fmt, *args)
        self.data[ptr : ptr + len(s)] = s

    def unpack(self, fmt):
        try:
            data = self.get(struct.calcsize(fmt))
            return struct.unpack(fmt, data)
        except struct.error:
            raise BufferError(
                "Error unpacking struct '%s' <%s>"
                % (fmt, binascii.hexlify(data).decode())
            )

    def __len__(self):
        return len(self.data)

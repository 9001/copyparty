# coding: utf-8

from __future__ import print_function

import re

from .bit import get_bits, set_bits
from .buffer import Buffer, BufferError

LDH = set(range(33, 127))
ESCAPE = re.compile(r"\\([0-9][0-9][0-9])")


class DNSLabelError(Exception):
    pass


class DNSLabel(object):
    def __init__(self, label):
        if type(label) == DNSLabel:
            self.label = label.label
        elif type(label) in (list, tuple):
            self.label = tuple(label)
        else:
            if not label or label in (b".", "."):
                self.label = ()
            elif type(label) is not bytes:
                if type("") != type(b""):

                    label = ESCAPE.sub(lambda m: chr(int(m[1])), label)
                self.label = tuple(label.encode("idna").rstrip(b".").split(b"."))
            else:
                if type("") == type(b""):

                    label = ESCAPE.sub(lambda m: chr(int(m.groups()[0])), label)
                self.label = tuple(label.rstrip(b".").split(b"."))

    def add(self, name):
        new = DNSLabel(name)
        if self.label:
            new.label += self.label
        return new

    def idna(self):
        return ".".join([s.decode("idna") for s in self.label]) + "."

    def _decode(self, s):
        if set(s).issubset(LDH):

            return s.decode()
        else:

            return "".join([(chr(c) if (c in LDH) else "\\%03d" % c) for c in s])

    def __str__(self):
        return ".".join([self._decode(bytearray(s)) for s in self.label]) + "."

    def __repr__(self):
        return "<DNSLabel: '%s'>" % str(self)

    def __hash__(self):
        return hash(tuple(map(lambda x: x.lower(), self.label)))

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        if type(other) != DNSLabel:
            return self.__eq__(DNSLabel(other))
        else:
            return [l.lower() for l in self.label] == [l.lower() for l in other.label]

    def __len__(self):
        return len(b".".join(self.label))


class DNSBuffer(Buffer):
    def __init__(self, data=b""):
        super(DNSBuffer, self).__init__(data)
        self.names = {}

    def decode_name(self, last=-1):
        label = []
        done = False
        while not done:
            (length,) = self.unpack("!B")
            if get_bits(length, 6, 2) == 3:

                self.offset -= 1
                pointer = get_bits(self.unpack("!H")[0], 0, 14)
                save = self.offset
                if last == save:
                    raise BufferError(
                        "Recursive pointer in DNSLabel [offset=%d,pointer=%d,length=%d]"
                        % (self.offset, pointer, len(self.data))
                    )
                if pointer < self.offset:
                    self.offset = pointer
                else:

                    raise BufferError(
                        "Invalid pointer in DNSLabel [offset=%d,pointer=%d,length=%d]"
                        % (self.offset, pointer, len(self.data))
                    )
                label.extend(self.decode_name(save).label)
                self.offset = save
                done = True
            else:
                if length > 0:
                    l = self.get(length)
                    try:
                        l.decode()
                    except UnicodeDecodeError:
                        raise BufferError("Invalid label <%s>" % l)
                    label.append(l)
                else:
                    done = True
        return DNSLabel(label)

    def encode_name(self, name):
        if not isinstance(name, DNSLabel):
            name = DNSLabel(name)
        if len(name) > 253:
            raise DNSLabelError("Domain label too long: %r" % name)
        name = list(name.label)
        while name:
            if tuple(name) in self.names:

                pointer = self.names[tuple(name)]
                pointer = set_bits(pointer, 3, 14, 2)
                self.pack("!H", pointer)
                return
            else:
                self.names[tuple(name)] = self.offset
                element = name.pop(0)
                if len(element) > 63:
                    raise DNSLabelError("Label component too long: %r" % element)
                self.pack("!B", len(element))
                self.append(element)
        self.append(b"\x00")

    def encode_name_nocompress(self, name):
        if not isinstance(name, DNSLabel):
            name = DNSLabel(name)
        if len(name) > 253:
            raise DNSLabelError("Domain label too long: %r" % name)
        name = list(name.label)
        while name:
            element = name.pop(0)
            if len(element) > 63:
                raise DNSLabelError("Label component too long: %r" % element)
            self.pack("!B", len(element))
            self.append(element)
        self.append(b"\x00")

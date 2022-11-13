# coding: utf-8

from __future__ import print_function

import collections

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Lexer(object):

    escape_chars = "\\"
    escape = {"n": "\n", "t": "\t", "r": "\r"}

    def __init__(self, f, debug=False):
        if hasattr(f, "read"):
            self.f = f
        elif type(f) == str:
            self.f = StringIO(f)
        elif type(f) == bytes:
            self.f = StringIO(f.decode())
        else:
            raise ValueError("Invalid input")
        self.debug = debug
        self.q = collections.deque()
        self.state = self.lexStart
        self.escaped = False
        self.eof = False

    def __iter__(self):
        return self.parse()

    def next_token(self):
        if self.debug:
            print("STATE", self.state)
        (tok, self.state) = self.state()
        return tok

    def parse(self):
        while self.state is not None and not self.eof:
            tok = self.next_token()
            if tok:
                yield tok

    def read(self, n=1):
        s = ""
        while self.q and n > 0:
            s += self.q.popleft()
            n -= 1
        s += self.f.read(n)
        if s == "":
            self.eof = True
        if self.debug:
            print("Read: >%s<" % repr(s))
        return s

    def peek(self, n=1):
        s = ""
        i = 0
        while len(self.q) > i and n > 0:
            s += self.q[i]
            i += 1
            n -= 1
        r = self.f.read(n)
        if n > 0 and r == "":
            self.eof = True
        self.q.extend(r)
        if self.debug:
            print("Peek : >%s<" % repr(s + r))
        return s + r

    def pushback(self, s):
        p = collections.deque(s)
        p.extend(self.q)
        self.q = p

    def readescaped(self):
        c = self.read(1)
        if c in self.escape_chars:
            self.escaped = True
            n = self.peek(3)
            if n.isdigit():
                n = self.read(3)
                if self.debug:
                    print("Escape: >%s<" % n)
                return chr(int(n, 8))
            elif n[0] in "x":
                x = self.read(3)
                if self.debug:
                    print("Escape: >%s<" % x)
                return chr(int(x[1:], 16))
            else:
                c = self.read(1)
                if self.debug:
                    print("Escape: >%s<" % c)
                return self.escape.get(c, c)
        else:
            self.escaped = False
            return c

    def lexStart(self):
        return (None, None)

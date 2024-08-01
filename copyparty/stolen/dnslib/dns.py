# coding: utf-8

from __future__ import print_function

import binascii
from itertools import chain

from .bimap import Bimap, BimapError
from .bit import get_bits, set_bits
from .buffer import BufferError
from .label import DNSBuffer, DNSLabel
from .ranges import IP4, IP6, H, I, check_bytes


try:
    range = xrange
except:
    pass


class DNSError(Exception):
    pass


def unknown_qtype(name, key, forward):
    if forward:
        try:
            return "TYPE%d" % (key,)
        except:
            raise DNSError("%s: Invalid forward lookup: [%s]" % (name, key))
    else:
        if key.startswith("TYPE"):
            try:
                return int(key[4:])
            except:
                pass
        raise DNSError("%s: Invalid reverse lookup: [%s]" % (name, key))


QTYPE = Bimap(
    "QTYPE",
    {1: "A", 12: "PTR", 16: "TXT", 28: "AAAA", 33: "SRV", 47: "NSEC", 255: "ANY"},
    unknown_qtype,
)

CLASS = Bimap("CLASS", {1: "IN", 254: "None", 255: "*", 0x8001: "F_IN"}, DNSError)

QR = Bimap("QR", {0: "QUERY", 1: "RESPONSE"}, DNSError)

RCODE = Bimap(
    "RCODE",
    {
        0: "NOERROR",
        1: "FORMERR",
        2: "SERVFAIL",
        3: "NXDOMAIN",
        4: "NOTIMP",
        5: "REFUSED",
        6: "YXDOMAIN",
        7: "YXRRSET",
        8: "NXRRSET",
        9: "NOTAUTH",
        10: "NOTZONE",
    },
    DNSError,
)

OPCODE = Bimap(
    "OPCODE", {0: "QUERY", 1: "IQUERY", 2: "STATUS", 4: "NOTIFY", 5: "UPDATE"}, DNSError
)


def label(label, origin=None):
    if label.endswith("."):
        return DNSLabel(label)
    else:
        return (origin if isinstance(origin, DNSLabel) else DNSLabel(origin)).add(label)


class DNSRecord(object):
    @classmethod
    def parse(cls, packet) -> "DNSRecord":
        buffer = DNSBuffer(packet)
        try:
            header = DNSHeader.parse(buffer)
            questions = []
            rr = []
            auth = []
            ar = []
            for i in range(header.q):
                questions.append(DNSQuestion.parse(buffer))
            for i in range(header.a):
                rr.append(RR.parse(buffer))
            for i in range(header.auth):
                auth.append(RR.parse(buffer))
            for i in range(header.ar):
                ar.append(RR.parse(buffer))
            return cls(header, questions, rr, auth=auth, ar=ar)
        except (BufferError, BimapError) as e:
            raise DNSError(
                "Error unpacking DNSRecord [offset=%d]: %s" % (buffer.offset, e)
            )

    @classmethod
    def question(cls, qname, qtype="A", qclass="IN"):
        return DNSRecord(
            q=DNSQuestion(qname, getattr(QTYPE, qtype), getattr(CLASS, qclass))
        )

    def __init__(
        self, header=None, questions=None, rr=None, q=None, a=None, auth=None, ar=None
    ) -> None:
        self.header = header or DNSHeader()
        self.questions: list[DNSQuestion] = questions or []
        self.rr: list[RR] = rr or []
        self.auth: list[RR] = auth or []
        self.ar: list[RR] = ar or []

        if q:
            self.questions.append(q)
        if a:
            self.rr.append(a)
        self.set_header_qa()

    def reply(self, ra=1, aa=1):
        return DNSRecord(
            DNSHeader(id=self.header.id, bitmap=self.header.bitmap, qr=1, ra=ra, aa=aa),
            q=self.q,
        )

    def add_question(self, *q) -> None:
        self.questions.extend(q)
        self.set_header_qa()

    def add_answer(self, *rr) -> None:
        self.rr.extend(rr)
        self.set_header_qa()

    def add_auth(self, *auth) -> None:
        self.auth.extend(auth)
        self.set_header_qa()

    def add_ar(self, *ar) -> None:
        self.ar.extend(ar)
        self.set_header_qa()

    def set_header_qa(self) -> None:
        self.header.q = len(self.questions)
        self.header.a = len(self.rr)
        self.header.auth = len(self.auth)
        self.header.ar = len(self.ar)

    def get_q(self):
        return self.questions[0] if self.questions else DNSQuestion()

    q = property(get_q)

    def get_a(self):
        return self.rr[0] if self.rr else RR()

    a = property(get_a)

    def pack(self) -> bytes:
        self.set_header_qa()
        buffer = DNSBuffer()
        self.header.pack(buffer)
        for q in self.questions:
            q.pack(buffer)
        for rr in self.rr:
            rr.pack(buffer)
        for auth in self.auth:
            auth.pack(buffer)
        for ar in self.ar:
            ar.pack(buffer)
        return buffer.data

    def truncate(self):
        return DNSRecord(DNSHeader(id=self.header.id, bitmap=self.header.bitmap, tc=1))

    def format(self, prefix="", sort=False):
        s = sorted if sort else lambda x: x
        sections = [repr(self.header)]
        sections.extend(s([repr(q) for q in self.questions]))
        sections.extend(s([repr(rr) for rr in self.rr]))
        sections.extend(s([repr(rr) for rr in self.auth]))
        sections.extend(s([repr(rr) for rr in self.ar]))
        return prefix + ("\n" + prefix).join(sections)

    short = format

    def __repr__(self):
        return self.format()

    __str__ = __repr__


class DNSHeader(object):
    id = H("id")
    bitmap = H("bitmap")
    q = H("q")
    a = H("a")
    auth = H("auth")
    ar = H("ar")

    @classmethod
    def parse(cls, buffer):
        try:
            (id, bitmap, q, a, auth, ar) = buffer.unpack("!HHHHHH")
            return cls(id, bitmap, q, a, auth, ar)
        except (BufferError, BimapError) as e:
            raise DNSError(
                "Error unpacking DNSHeader [offset=%d]: %s" % (buffer.offset, e)
            )

    def __init__(self, id=None, bitmap=None, q=0, a=0, auth=0, ar=0, **args) -> None:
        self.id = id if id else 0
        if bitmap is None:
            self.bitmap = 0
        else:
            self.bitmap = bitmap
        self.q = q
        self.a = a
        self.auth = auth
        self.ar = ar
        for k, v in args.items():
            if k.lower() == "qr":
                self.qr = v
            elif k.lower() == "opcode":
                self.opcode = v
            elif k.lower() == "aa":
                self.aa = v
            elif k.lower() == "tc":
                self.tc = v
            elif k.lower() == "rd":
                self.rd = v
            elif k.lower() == "ra":
                self.ra = v
            elif k.lower() == "z":
                self.z = v
            elif k.lower() == "ad":
                self.ad = v
            elif k.lower() == "cd":
                self.cd = v
            elif k.lower() == "rcode":
                self.rcode = v

    def get_qr(self):
        return get_bits(self.bitmap, 15)

    def set_qr(self, val):
        self.bitmap = set_bits(self.bitmap, val, 15)

    qr = property(get_qr, set_qr)

    def get_opcode(self):
        return get_bits(self.bitmap, 11, 4)

    def set_opcode(self, val):
        self.bitmap = set_bits(self.bitmap, val, 11, 4)

    opcode = property(get_opcode, set_opcode)

    def get_aa(self):
        return get_bits(self.bitmap, 10)

    def set_aa(self, val):
        self.bitmap = set_bits(self.bitmap, val, 10)

    aa = property(get_aa, set_aa)

    def get_tc(self):
        return get_bits(self.bitmap, 9)

    def set_tc(self, val):
        self.bitmap = set_bits(self.bitmap, val, 9)

    tc = property(get_tc, set_tc)

    def get_rd(self):
        return get_bits(self.bitmap, 8)

    def set_rd(self, val):
        self.bitmap = set_bits(self.bitmap, val, 8)

    rd = property(get_rd, set_rd)

    def get_ra(self):
        return get_bits(self.bitmap, 7)

    def set_ra(self, val):
        self.bitmap = set_bits(self.bitmap, val, 7)

    ra = property(get_ra, set_ra)

    def get_z(self):
        return get_bits(self.bitmap, 6)

    def set_z(self, val):
        self.bitmap = set_bits(self.bitmap, val, 6)

    z = property(get_z, set_z)

    def get_ad(self):
        return get_bits(self.bitmap, 5)

    def set_ad(self, val):
        self.bitmap = set_bits(self.bitmap, val, 5)

    ad = property(get_ad, set_ad)

    def get_cd(self):
        return get_bits(self.bitmap, 4)

    def set_cd(self, val):
        self.bitmap = set_bits(self.bitmap, val, 4)

    cd = property(get_cd, set_cd)

    def get_rcode(self):
        return get_bits(self.bitmap, 0, 4)

    def set_rcode(self, val):
        self.bitmap = set_bits(self.bitmap, val, 0, 4)

    rcode = property(get_rcode, set_rcode)

    def pack(self, buffer):
        buffer.pack("!HHHHHH", self.id, self.bitmap, self.q, self.a, self.auth, self.ar)

    def __repr__(self):
        f = [
            self.aa and "AA",
            self.tc and "TC",
            self.rd and "RD",
            self.ra and "RA",
            self.z and "Z",
            self.ad and "AD",
            self.cd and "CD",
        ]
        if OPCODE.get(self.opcode) == "UPDATE":
            f1 = "zo"
            f2 = "pr"
            f3 = "up"
            f4 = "ad"
        else:
            f1 = "q"
            f2 = "a"
            f3 = "ns"
            f4 = "ar"
        return (
            "<DNS Header: id=0x%x type=%s opcode=%s flags=%s "
            "rcode='%s' %s=%d %s=%d %s=%d %s=%d>"
            % (
                self.id,
                QR.get(self.qr),
                OPCODE.get(self.opcode),
                ",".join(filter(None, f)),
                RCODE.get(self.rcode),
                f1,
                self.q,
                f2,
                self.a,
                f3,
                self.auth,
                f4,
                self.ar,
            )
        )

    __str__ = __repr__


class DNSQuestion(object):
    @classmethod
    def parse(cls, buffer):
        try:
            qname = buffer.decode_name()
            qtype, qclass = buffer.unpack("!HH")
            return cls(qname, qtype, qclass)
        except (BufferError, BimapError) as e:
            raise DNSError(
                "Error unpacking DNSQuestion [offset=%d]: %s" % (buffer.offset, e)
            )

    def __init__(self, qname=None, qtype=1, qclass=1) -> None:
        self.qname = qname
        self.qtype = qtype
        self.qclass = qclass

    def set_qname(self, qname):
        if isinstance(qname, DNSLabel):
            self._qname = qname
        else:
            self._qname = DNSLabel(qname)

    def get_qname(self):
        return self._qname

    qname = property(get_qname, set_qname)

    def pack(self, buffer):
        buffer.encode_name(self.qname)
        buffer.pack("!HH", self.qtype, self.qclass)

    def __repr__(self):
        return "<DNS Question: '%s' qtype=%s qclass=%s>" % (
            self.qname,
            QTYPE.get(self.qtype),
            CLASS.get(self.qclass),
        )

    __str__ = __repr__


class RR(object):
    rtype = H("rtype")
    rclass = H("rclass")
    ttl = I("ttl")
    rdlength = H("rdlength")

    @classmethod
    def parse(cls, buffer):
        try:
            rname = buffer.decode_name()
            rtype, rclass, ttl, rdlength = buffer.unpack("!HHIH")
            if rdlength:
                rdata = RDMAP.get(QTYPE.get(rtype), RD).parse(buffer, rdlength)
            else:
                rdata = ""
            return cls(rname, rtype, rclass, ttl, rdata)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking RR [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, rname=None, rtype=1, rclass=1, ttl=0, rdata=None) -> None:
        self.rname = rname
        self.rtype = rtype
        self.rclass = rclass
        self.ttl = ttl
        self.rdata = rdata

    def set_rname(self, rname):
        if isinstance(rname, DNSLabel):
            self._rname = rname
        else:
            self._rname = DNSLabel(rname)

    def get_rname(self):
        return self._rname

    rname = property(get_rname, set_rname)

    def pack(self, buffer):
        buffer.encode_name(self.rname)
        buffer.pack("!HHI", self.rtype, self.rclass, self.ttl)
        rdlength_ptr = buffer.offset
        buffer.pack("!H", 0)
        start = buffer.offset
        self.rdata.pack(buffer)
        end = buffer.offset
        buffer.update(rdlength_ptr, "!H", end - start)

    def __repr__(self):
        return "<DNS RR: '%s' rtype=%s rclass=%s ttl=%d rdata='%s'>" % (
            self.rname,
            QTYPE.get(self.rtype),
            CLASS.get(self.rclass),
            self.ttl,
            self.rdata,
        )

    __str__ = __repr__


class RD(object):
    @classmethod
    def parse(cls, buffer, length):
        try:
            data = buffer.get(length)
            return cls(data)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking RD [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, data=b"") -> None:
        check_bytes("data", data)
        self.data = bytes(data)

    def pack(self, buffer):
        buffer.append(self.data)

    def __repr__(self):
        if len(self.data) > 0:
            return "\\# %d %s" % (
                len(self.data),
                binascii.hexlify(self.data).decode().upper(),
            )
        else:
            return "\\# 0"

    attrs = ("data",)


def _force_bytes(x):
    if isinstance(x, bytes):
        return x
    else:
        return x.encode()


class TXT(RD):
    @classmethod
    def parse(cls, buffer, length):
        try:
            data = list()
            start_bo = buffer.offset
            now_length = 0
            while buffer.offset < start_bo + length:
                (txtlength,) = buffer.unpack("!B")

                if now_length + txtlength < length:
                    now_length += txtlength
                    data.append(buffer.get(txtlength))
                else:
                    raise DNSError(
                        "Invalid TXT record: len(%d) > RD len(%d)" % (txtlength, length)
                    )
            return cls(data)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking TXT [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, data) -> None:
        if type(data) in (tuple, list):
            self.data = [_force_bytes(x) for x in data]
        else:
            self.data = [_force_bytes(data)]
        if any([len(x) > 255 for x in self.data]):
            raise DNSError("TXT record too long: %s" % self.data)

    def pack(self, buffer):
        for ditem in self.data:
            if len(ditem) > 255:
                raise DNSError("TXT record too long: %s" % ditem)
            buffer.pack("!B", len(ditem))
            buffer.append(ditem)

    def __repr__(self):
        return ",".join([repr(x) for x in self.data])


class A(RD):

    data = IP4("data")

    @classmethod
    def parse(cls, buffer, length):
        try:
            data = buffer.unpack("!BBBB")
            return cls(data)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking A [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, data) -> None:
        if type(data) in (tuple, list):
            self.data = tuple(data)
        else:
            self.data = tuple(map(int, data.rstrip(".").split(".")))

    def pack(self, buffer):
        buffer.pack("!BBBB", *self.data)

    def __repr__(self):
        return "%d.%d.%d.%d" % self.data


def _parse_ipv6(a):
    l, _, r = a.partition("::")
    l_groups = list(chain(*[divmod(int(x, 16), 256) for x in l.split(":") if x]))
    r_groups = list(chain(*[divmod(int(x, 16), 256) for x in r.split(":") if x]))
    zeros = [0] * (16 - len(l_groups) - len(r_groups))
    return tuple(l_groups + zeros + r_groups)


def _format_ipv6(a):
    left = []
    right = []
    current = "left"
    for i in range(0, 16, 2):
        group = (a[i] << 8) + a[i + 1]
        if current == "left":
            if group == 0 and i < 14:
                if (a[i + 2] << 8) + a[i + 3] == 0:
                    current = "right"
                else:
                    left.append("0")
            else:
                left.append("%x" % group)
        else:
            if group == 0 and len(right) == 0:
                pass
            else:
                right.append("%x" % group)
    if len(left) < 8:
        return ":".join(left) + "::" + ":".join(right)
    else:
        return ":".join(left)


class AAAA(RD):
    data = IP6("data")

    @classmethod
    def parse(cls, buffer, length):
        try:
            data = buffer.unpack("!16B")
            return cls(data)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking AAAA [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, data) -> None:
        if type(data) in (tuple, list):
            self.data = tuple(data)
        else:
            self.data = _parse_ipv6(data)

    def pack(self, buffer):
        buffer.pack("!16B", *self.data)

    def __repr__(self):
        return _format_ipv6(self.data)


class CNAME(RD):
    @classmethod
    def parse(cls, buffer, length):
        try:
            label = buffer.decode_name()
            return cls(label)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking CNAME [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, label=None) -> None:
        self.label = label

    def set_label(self, label):
        if isinstance(label, DNSLabel):
            self._label = label
        else:
            self._label = DNSLabel(label)

    def get_label(self):
        return self._label

    label = property(get_label, set_label)

    def pack(self, buffer):
        buffer.encode_name(self.label)

    def __repr__(self):
        return "%s" % (self.label)

    attrs = ("label",)


class PTR(CNAME):
    pass


class SRV(RD):
    priority = H("priority")
    weight = H("weight")
    port = H("port")

    @classmethod
    def parse(cls, buffer, length):
        try:
            priority, weight, port = buffer.unpack("!HHH")
            target = buffer.decode_name()
            return cls(priority, weight, port, target)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking SRV [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, priority=0, weight=0, port=0, target=None) -> None:
        self.priority = priority
        self.weight = weight
        self.port = port
        self.target = target

    def set_target(self, target):
        if isinstance(target, DNSLabel):
            self._target = target
        else:
            self._target = DNSLabel(target)

    def get_target(self):
        return self._target

    target = property(get_target, set_target)

    def pack(self, buffer):
        buffer.pack("!HHH", self.priority, self.weight, self.port)
        buffer.encode_name(self.target)

    def __repr__(self):
        return "%d %d %d %s" % (self.priority, self.weight, self.port, self.target)

    attrs = ("priority", "weight", "port", "target")


def decode_type_bitmap(type_bitmap):
    rrlist = []
    buf = DNSBuffer(type_bitmap)
    while buf.remaining():
        winnum, winlen = buf.unpack("BB")
        bitmap = bytearray(buf.get(winlen))
        for (pos, value) in enumerate(bitmap):
            for i in range(8):
                if (value << i) & 0x80:
                    bitpos = (256 * winnum) + (8 * pos) + i
                    rrlist.append(QTYPE[bitpos])
    return rrlist


def encode_type_bitmap(rrlist):
    rrlist = sorted([getattr(QTYPE, rr) for rr in rrlist])
    buf = DNSBuffer()
    curWindow = rrlist[0] // 256
    bitmap = bytearray(32)
    n = len(rrlist) - 1
    for i, rr in enumerate(rrlist):
        v = rr - curWindow * 256
        bitmap[v // 8] |= 1 << (7 - v % 8)

        if i == n or rrlist[i + 1] >= (curWindow + 1) * 256:
            while bitmap[-1] == 0:
                bitmap = bitmap[:-1]
            buf.pack("BB", curWindow, len(bitmap))
            buf.append(bitmap)

            if i != n:
                curWindow = rrlist[i + 1] // 256
                bitmap = bytearray(32)

    return buf.data


class NSEC(RD):
    @classmethod
    def parse(cls, buffer, length):
        try:
            end = buffer.offset + length
            name = buffer.decode_name()
            rrlist = decode_type_bitmap(buffer.get(end - buffer.offset))
            return cls(name, rrlist)
        except (BufferError, BimapError) as e:
            raise DNSError("Error unpacking NSEC [offset=%d]: %s" % (buffer.offset, e))

    def __init__(self, label, rrlist) -> None:
        self.label = label
        self.rrlist = rrlist

    def set_label(self, label):
        if isinstance(label, DNSLabel):
            self._label = label
        else:
            self._label = DNSLabel(label)

    def get_label(self):
        return self._label

    label = property(get_label, set_label)

    def pack(self, buffer):
        buffer.encode_name(self.label)
        buffer.append(encode_type_bitmap(self.rrlist))

    def __repr__(self):
        return "%s %s" % (self.label, " ".join(self.rrlist))

    attrs = ("label", "rrlist")


RDMAP = {"A": A, "AAAA": AAAA, "TXT": TXT, "PTR": PTR, "SRV": SRV, "NSEC": NSEC}

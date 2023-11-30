#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import unittest
from xml.etree import ElementTree as ET

from copyparty.dxml import BadXML, mkenod, mktnod, parse_xml

ET.register_namespace("D", "DAV:")


def _parse(txt):
    try:
        parse_xml(txt)
        raise Exception("unsafe")
    except BadXML:
        pass


class TestDXML(unittest.TestCase):
    def test1(self):
        txt = r"""<!DOCTYPE qbe [
<!ENTITY a "nice_bakuretsu">
]>
<l>&a;&a;&a;&a;&a;&a;&a;&a;&a;</l>"""
        _parse(txt)
        ET.fromstring(txt)

    def test2(self):
        txt = r"""<!DOCTYPE ext [
<!ENTITY ee SYSTEM "file:///bin/bash">
]>
<root>&ee;</root>"""
        _parse(txt)
        try:
            ET.fromstring(txt)
            raise Exception("unsafe2")
        except ET.ParseError:
            pass

    def test3(self):
        txt = r"""<?xml version="1.0" ?>
<propfind xmlns="DAV:">
    <prop>
        <name/>
        <href/>
    </prop>
</propfind>
"""
        txt = txt.replace("\n", "\r\n")
        ET.fromstring(txt)
        el = parse_xml(txt)
        self.assertListEqual(
            [y.tag for y in el.findall(r"./{DAV:}prop/*")],
            [r"{DAV:}name", r"{DAV:}href"],
        )

    def test4(self):
        txt = r"""<?xml version="1.0" encoding="utf-8" ?>
<D:propertyupdate xmlns:D="DAV:" xmlns:Z="urn:schemas-microsoft-com:">
    <D:set>
        <D:prop>
            <Z:Win32CreationTime>Thu, 20 Oct 2022 02:16:33 GMT</Z:Win32CreationTime>
            <Z:Win32LastAccessTime>Thu, 20 Oct 2022 02:16:35 GMT</Z:Win32LastAccessTime>
            <Z:Win32LastModifiedTime>Thu, 20 Oct 2022 02:16:33 GMT</Z:Win32LastModifiedTime>
            <Z:Win32FileAttributes>00000000</Z:Win32FileAttributes>
        </D:prop>
    </D:set>
</D:propertyupdate>"""

        ref = r"""<?xml version="1.0" encoding="UTF-8"?>
<D:multistatus xmlns:D="DAV:">
    <D:response>
        <D:href>/d1/foo.txt</D:href>
        <D:propstat>
            <D:prop>
                <Win32CreationTime xmlns="urn:schemas-microsoft-com:"></Win32CreationTime>
                <Win32LastAccessTime xmlns="urn:schemas-microsoft-com:"></Win32LastAccessTime>
                <Win32LastModifiedTime xmlns="urn:schemas-microsoft-com:"></Win32LastModifiedTime>
                <Win32FileAttributes xmlns="urn:schemas-microsoft-com:"></Win32FileAttributes>
            </D:prop>
            <D:status>HTTP/1.1 403 Forbidden</D:status>
        </D:propstat>
    </D:response>
</D:multistatus>"""

        txt = re.sub("\n +", "\n", txt)
        root = mkenod("a")
        root.insert(0, parse_xml(txt))
        prop = root.find(r"./{DAV:}propertyupdate/{DAV:}set/{DAV:}prop")
        assert prop is not None
        assert len(prop)
        for el in prop:
            el.clear()

        res = ET.tostring(prop).decode("utf-8")
        want = """<D:prop xmlns:D="DAV:" xmlns:ns1="urn:schemas-microsoft-com:">
<ns1:Win32CreationTime /><ns1:Win32LastAccessTime /><ns1:Win32LastModifiedTime /><ns1:Win32FileAttributes /></D:prop>
"""
        self.assertEqual(res, want)

    def test5(self):
        txt = r"""<?xml version="1.0" encoding="utf-8" ?>
<D:lockinfo xmlns:D="DAV:">
    <D:lockscope><D:exclusive/></D:lockscope>
    <D:locktype><D:write/></D:locktype>
    <D:owner><D:href>DESKTOP-FRS9AO2\ed</D:href></D:owner>
</D:lockinfo>"""

        ref = r"""<?xml version="1.0" encoding="utf-8"?>
<D:prop xmlns:D="DAV:"><D:lockdiscovery><D:activelock>
    <D:locktype><D:write/></D:locktype>
    <D:lockscope><D:exclusive/></D:lockscope>
    <D:depth>infinity</D:depth>
    <D:owner><D:href>DESKTOP-FRS9AO2\ed</D:href></D:owner>
    <D:timeout>Second-3600</D:timeout>
    <D:locktoken><D:href>1666199679</D:href></D:locktoken>
    <D:lockroot><D:href>/d1/foo.txt</D:href></D:lockroot>
</D:activelock></D:lockdiscovery></D:prop>"""

        txt = re.sub("\n +", "\n", txt)
        lk = parse_xml(txt)
        self.assertEqual(lk.tag, "{DAV:}lockinfo")

        if not lk.find(r"./{DAV:}depth"):
            lk.append(mktnod("D:depth", "infinity"))

        lk.append(mkenod("D:timeout", mktnod("D:href", "Second-3600")))
        lk.append(mkenod("D:locktoken", mktnod("D:href", "56709")))
        lk.append(mkenod("D:lockroot", mktnod("D:href", "/foo/bar.txt")))

        lk2 = mkenod("D:activelock")
        root = mkenod("D:prop", mkenod("D:lockdiscovery", lk2))
        for a in lk:
            lk2.append(a)

        print(ET.tostring(root).decode("utf-8"))

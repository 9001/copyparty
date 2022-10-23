import importlib
import sys
import xml.etree.ElementTree as ET

from .__init__ import PY2

try:
    from typing import Any, Optional
except:
    pass


def get_ET() -> ET.XMLParser:
    pn = "xml.etree.ElementTree"
    cn = "_elementtree"

    cmod = sys.modules.pop(cn, None)
    if not cmod:
        return ET.XMLParser  # type: ignore

    pmod = sys.modules.pop(pn)
    sys.modules[cn] = None  # type: ignore

    ret = importlib.import_module(pn)
    for name, mod in ((pn, pmod), (cn, cmod)):
        if mod:
            sys.modules[name] = mod
        else:
            sys.modules.pop(name, None)

    sys.modules["xml.etree"].ElementTree = pmod  # type: ignore
    ret.ParseError = ET.ParseError  # type: ignore
    return ret.XMLParser  # type: ignore


XMLParser: ET.XMLParser = get_ET()


class DXMLParser(XMLParser):  # type: ignore
    def __init__(self) -> None:
        tb = ET.TreeBuilder()
        super(DXMLParser, self).__init__(target=tb)

        p = self._parser if PY2 else self.parser
        p.StartDoctypeDeclHandler = self.nope
        p.EntityDeclHandler = self.nope
        p.UnparsedEntityDeclHandler = self.nope
        p.ExternalEntityRefHandler = self.nope

    def nope(self, *a: Any, **ka: Any) -> None:
        raise BadXML("{}, {}".format(a, ka))


class BadXML(Exception):
    pass


def parse_xml(txt: str) -> ET.Element:
    parser = DXMLParser()
    parser.feed(txt)
    return parser.close()  # type: ignore


def mktnod(name: str, text: str) -> ET.Element:
    el = ET.Element(name)
    el.text = text
    return el


def mkenod(name: str, sub_el: Optional[ET.Element] = None) -> ET.Element:
    el = ET.Element(name)
    if sub_el is not None:
        el.append(sub_el)
    return el

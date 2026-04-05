# coding: utf-8
from __future__ import print_function, unicode_literals

import base64
import errno
import os
import re
import select
import socket
import stat
import time
import xml.etree.ElementTree as ET

from .__init__ import TYPE_CHECKING
from .authsrv import LEELOO_DALLAS
from .multicast import MC_Sck, MCast
from .util import CachedSet, formatdate, html_escape, min_ex

if TYPE_CHECKING:
    from .broker_util import BrokerCli
    from .httpcli import HttpCli
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Optional, Union


GRP = "239.255.255.250"

# DLNA Protocol Info for media types with DLNA.ORG_PN and OP flags
DLNA_PROTOCOL_INFO = {
    # photo
    ".jpg": "http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_SM;DLNA.ORG_OP=01",
    ".jpeg": "http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_SM;DLNA.ORG_OP=01",
    ".png": "http-get:*:image/png:DLNA.ORG_PN=PNG_LRG;DLNA.ORG_OP=01",
    # audio
    ".mp3": "http-get:*:audio/mpeg:DLNA.ORG_PN=MP3;DLNA.ORG_OP=01",
    ".flac": "http-get:*:audio/flac:*",
    ".wav": "http-get:*:audio/wav:*",
    ".ogg": "http-get:*:audio/ogg:*",
    ".aac": "http-get:*:audio/mp4:DLNA.ORG_PN=AAC_ISO_320;DLNA.ORG_OP=01",
    ".m4a": "http-get:*:audio/mp4:DLNA.ORG_PN=AAC_ISO_320;DLNA.ORG_OP=01",
    # video
    ".mp4": "http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_MP_SD;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000",
    ".m4v": "http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_MP_SD;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000",
    ".mkv": "http-get:*:video/x-matroska:DLNA.ORG_PN=MATROSKA;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000",
    ".webm": "http-get:*:video/x-matroska:DLNA.ORG_PN=MATROSKA;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000",
    ".avi": "http-get:*:video/x-msvideo:*",
    ".wmv": "http-get:*:video/x-ms-wmv:*",
}

CONTAINER_MIME = "object.container.storageFolder"
IMAGE_MIME = "object.item.imageItem.photo"
AUDIO_MIME = "object.item.audioItem.musicTrack"
VIDEO_MIME = "object.item.videoItem"


def _esc_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")


def _oid_encode(vpath):
    if not vpath:
        return "0"
    return base64.urlsafe_b64encode(vpath.encode("utf-8")).decode("ascii").rstrip("=")


def _oid_decode(oid):
    if oid == "0":
        return ""
    padded = oid + "=" * (4 - len(oid) % 4) if len(oid) % 4 else oid
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _mime_for_ext(ext):
    return DLNA_PROTOCOL_INFO.get(ext.lower(), "http-get:*:application/octet-stream:*")


def _dlna_class_for_ext(ext):
    ext = ext.lower()
    if ext in (".mp4", ".mkv", ".avi", ".wmv", ".webm", ".mov", ".ts", ".mpg", ".mpeg"):
        return VIDEO_MIME
    if ext in (".mp3", ".flac", ".wav", ".ogg", ".aac", ".m4a", ".wma"):
        return AUDIO_MIME
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"):
        return IMAGE_MIME
    return "object.item"


def _url_quote(s):
    from urllib.parse import quote as _q

    return _q(s, safe="")


class DLNA_Sck(MC_Sck):
    def __init__(self, *a):
        super(DLNA_Sck, self).__init__(*a)
        self.hport = 0


class DLNAr(object):
    """generates http responses for httpcli"""

    def __init__(self, broker: "BrokerCli") -> None:
        self.broker = broker
        self.args = broker.args

    def reply(self, hc: "HttpCli") -> bool:
        if hc.vpath.endswith("device.xml"):
            return self.tx_device(hc)
        
        if hc.vpath.endswith("ConnectionMgr.xml"):
            return self.tx_connmgr_scpd(hc)
        
        if hc.vpath.endswith("ContentDir.xml"):
            return self.tx_contentdir_scpd(hc)

        if "/ctl/ConnectionMgr" in hc.vpath:
            return self.tx_connmgr_ctl(hc)

        if "/ctl/ContentDir" in hc.vpath:
            return self.tx_contentdir_ctl(hc)
        
        if "/ctl/" in hc.vpath:
            return self.tx_soap_fault(hc, 401, "Invalid Action")

        hc.reply(b"unknown request", 400)
        return False

    # device description (MediaServer:1 + ConnectionManager:1 and ContentDirectory:1 services)
    def tx_device(self, hc: "HttpCli") -> bool:
        '''UPnP-spec taken from running miniDLNA instance'''
        zs = """
            <?xml version="1.0"?>
            <root xmlns="urn:schemas-upnp-org:device-1-0" xmlns:dlna="urn:schemas-dlna-org:device-1-0">
                <specVersion>
                    <major>1</major>
                    <minor>0</minor>
                </specVersion>
                <URLBase>{}</URLBase>
                <device>
                    <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
                    <friendlyName>{}</friendlyName>
                    <modelDescription>file server</modelDescription>
                    <manufacturer>ed</manufacturer>
                    <manufacturerURL>https://ocv.me/</manufacturerURL>
                    <modelName>copyparty</modelName>
                    <modelNumber>1.0</modelNumber>
                    <modelURL>https://github.com/9001/copyparty/</modelURL>
                    <UDN>{}</UDN>
                    <dlna:X_DLNADOC>DMS-1.50</dlna:X_DLNADOC>
                    <serviceList>
                        <service>
                            <serviceType>urn:schemas-upnp-org:service:ConnectionManager:1</serviceType>
                            <serviceId>urn:upnp-org:serviceId:ConnectionManager</serviceId>
                            <controlURL>/.cpr/dlna/ctl/ConnectionMgr</controlURL>
                            <eventSubURL>/.cpr/dlna/evt/ConnectionMgr</eventSubURL>
                            <SCPDURL>/.cpr/dlna/ConnectionMgr.xml</SCPDURL>
                        </service>
                        <service>
                            <serviceType>urn:schemas-upnp-org:service:ContentDirectory:1</serviceType>
                            <serviceId>urn:upnp-org:serviceId:ContentDirectory</serviceId>
                            <controlURL>/.cpr/dlna/ctl/ContentDir</controlURL>
                            <eventSubURL>/.cpr/dlna/evt/ContentDir</eventSubURL>
                            <SCPDURL>/.cpr/dlna/ContentDir.xml</SCPDURL>
                        </service>
                    </serviceList>
                </device>
            </root>
        """

        c = html_escape
        sip, sport = hc.s.getsockname()[:2]
        sip = sip.replace("::ffff:", "")
        proto = "https" if self.args.https_only else "http"
        ubase = "{}://{}:{}".format(proto, sip, sport)
        zsl = self.args.zsl
        url = zsl if "://" in zsl else ubase + "/" + zsl.lstrip("/")
        name = self.args.doctitle
        zs = zs.strip().format(c(ubase), c(name), c(self.args.zsid))
        hc.reply(zs.encode("utf-8", "replace"))
        return False  # close connection

    # SCPD stuff

    def tx_connmgr_scpd(self, hc: "HttpCli") -> bool:
        '''UPnP-spec taken from running miniDLNA instance'''
        zs = """
            <?xml version="1.0"?>
                <scpd xmlns="urn:schemas-upnp-org:service-1-0">
                    <specVersion><major>1</major><minor>0</minor></specVersion>
                    <actionList>
                        <action>
                            <name>GetProtocolInfo</name>
                            <argumentList>
                                <argument><name>Source</name><direction>out</direction><relatedStateVariable>SourceProtocolInfo</relatedStateVariable></argument>
                                <argument><name>Sink</name><direction>out</direction><relatedStateVariable>SinkProtocolInfo</relatedStateVariable></argument>
                            </argumentList>
                        </action>
                        <action>
                            <name>GetCurrentConnectionIDs</name>
                            <argumentList>
                                <argument><name>ConnectionIDs</name><direction>out</direction><relatedStateVariable>CurrentConnectionIDs</relatedStateVariable></argument>
                            </argumentList>
                        </action>
                        <action>
                            <name>GetCurrentConnectionInfo</name>
                            <argumentList>
                                <argument><name>ConnectionID</name><direction>in</direction><relatedStateVariable>A_ARG_TYPE_ConnectionID</relatedStateVariable></argument>
                                <argument><name>RcsID</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_RcsID</relatedStateVariable></argument>
                                <argument><name>AVTransportID</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_AVTransportID</relatedStateVariable></argument>
                                <argument><name>ProtocolInfo</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_ProtocolInfo</relatedStateVariable></argument>
                                <argument><name>PeerConnectionManager</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_ConnectionManager</relatedStateVariable></argument>
                                <argument><name>PeerConnectionID</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_ConnectionID</relatedStateVariable></argument>
                                <argument><name>Direction</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_Direction</relatedStateVariable></argument>
                                <argument><name>Status</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_ConnectionStatus</relatedStateVariable></argument>
                            </argumentList>
                        </action>
                    </actionList>
                    <serviceStateTable>
                        <stateVariable sendEvents="yes"><name>SourceProtocolInfo</name><dataType>string</dataType></stateVariable>
                        <stateVariable sendEvents="yes"><name>SinkProtocolInfo</name><dataType>string</dataType></stateVariable>
                        <stateVariable sendEvents="yes"><name>CurrentConnectionIDs</name><dataType>string</dataType></stateVariable>
                        <stateVariable sendEvents="no"><name>A_ARG_TYPE_ConnectionStatus</name><dataType>string</dataType><allowedValueList><allowedValue>OK</allowedValue><allowedValue>ContentFormatMismatch</allowedValue><allowedValue>InsufficientBandwidth</allowedValue><allowedValue>UnreliableChannel</allowedValue><allowedValue>Unknown</allowedValue></allowedValueList></stateVariable>
                        <stateVariable sendEvents="no"><name>A_ARG_TYPE_ConnectionManager</name><dataType>string</dataType></stateVariable>
                        <stateVariable sendEvents="no"><name>A_ARG_TYPE_Direction</name><dataType>string</dataType><allowedValueList><allowedValue>Input</allowedValue><allowedValue>Output</allowedValue></allowedValueList></stateVariable>
                        <stateVariable sendEvents="no"><name>A_ARG_TYPE_ProtocolInfo</name><dataType>string</dataType></stateVariable>
                        <stateVariable sendEvents="no"><name>A_ARG_TYPE_ConnectionID</name><dataType>i4</dataType></stateVariable>
                        <stateVariable sendEvents="no"><name>A_ARG_TYPE_AVTransportID</name><dataType>i4</dataType></stateVariable>
                        <stateVariable sendEvents="no"><name>A_ARG_TYPE_RcsID</name><dataType>i4</dataType></stateVariable>
                    </serviceStateTable>
                </scpd>
            """
        
        hc.reply(zs.encode("utf-8", "replace"))
        return False

    def tx_contentdir_scpd(self, hc: "HttpCli") -> bool:
        zs = """
    <?xml version="1.0"?>
        <scpd xmlns="urn:schemas-upnp-org:service-1-0">
            <specVersion><major>1</major><minor>0</minor></specVersion>
            <actionList>
                <action>
                    <name>Browse</name>
                    <argumentList>
                        <argument><name>ObjectID</name><direction>in</direction><relatedStateVariable>A_ARG_TYPE_ObjectID</relatedStateVariable></argument>
                        <argument><name>BrowseFlag</name><direction>in</direction><relatedStateVariable>A_ARG_TYPE_BrowseFlag</relatedStateVariable></argument>
                        <argument><name>Filter</name><direction>in</direction><relatedStateVariable>A_ARG_TYPE_Filter</relatedStateVariable></argument>
                        <argument><name>StartingIndex</name><direction>in</direction><relatedStateVariable>A_ARG_TYPE_Index</relatedStateVariable></argument>
                        <argument><name>RequestedCount</name><direction>in</direction><relatedStateVariable>A_ARG_TYPE_Count</relatedStateVariable></argument>
                        <argument><name>SortCriteria</name><direction>in</direction><relatedStateVariable>A_ARG_TYPE_SortCriteria</relatedStateVariable></argument>
                        <argument><name>Result</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_Result</relatedStateVariable></argument>
                        <argument><name>NumberReturned</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_Count</relatedStateVariable></argument>
                        <argument><name>TotalMatches</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_Count</relatedStateVariable></argument>
                        <argument><name>UpdateID</name><direction>out</direction><relatedStateVariable>A_ARG_TYPE_UpdateID</relatedStateVariable></argument>
                    </argumentList>
                </action>
                <action>
                    <name>GetSystemUpdateID</name>
                    <argumentList>
                        <argument><name>Id</name><direction>out</direction><relatedStateVariable>SystemUpdateID</relatedStateVariable></argument>
                    </argumentList>
                </action>
                <action>
                    <name>GetSortCapabilities</name>
                    <argumentList>
                        <argument><name>SortCaps</name><direction>out</direction><relatedStateVariable>SortCapabilities</relatedStateVariable></argument>
                    </argumentList>
                </action>
                <action>
                    <name>GetSearchCapabilities</name>
                    <argumentList>
                        <argument><name>SearchCaps</name><direction>out</direction><relatedStateVariable>SearchCapabilities</relatedStateVariable></argument>
                    </argumentList>
                </action>
            </actionList>
            <serviceStateTable>
                <stateVariable sendEvents="yes"><name>SystemUpdateID</name><dataType>ui4</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>SortCapabilities</name><dataType>string</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>SearchCapabilities</name><dataType>string</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_ObjectID</name><dataType>string</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_BrowseFlag</name><dataType>string</dataType><allowedValueList><allowedValue>BrowseMetadata</allowedValue><allowedValue>BrowseDirectChildren</allowedValue></allowedValueList></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_Filter</name><dataType>string</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_Index</name><dataType>ui4</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_Count</name><dataType>ui4</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_SortCriteria</name><dataType>string</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_Result</name><dataType>string</dataType></stateVariable>
                <stateVariable sendEvents="no"><name>A_ARG_TYPE_UpdateID</name><dataType>ui4</dataType></stateVariable>
            </serviceStateTable>
        </scpd>
"""
        
        hc.reply(zs.encode("utf-8", "replace"))
        return False

    # SOAP stuff

    # Helpers for SOAP
    def _read_soap_body(self, hc):
        '''to SOAP XML from the HTTP request'''
        try:
            clen = int(hc.headers.get("content-length", 0))
            if clen <= 0 or clen >= 1_000_000:
                return None
            data = b""
            while len(data) < clen:
                chunk = hc.sr.recv(min(clen - len(data), 65536))
                if not chunk:
                    break
                data += chunk
            return data
        except Exception:
            return None

    def _parse_soap_action(self, body_bytes):
        '''parses SOAP XML, returns (service_type, action_name, params_dict)'''
        try:
            root = ET.fromstring(body_bytes)
        except ET.ParseError:
            return None, None, {}
        
        # find first element in the body
        ns_soap = "http://schemas.xmlsoap.org/soap/envelope/"
        body = root.find(f"{{{ns_soap}}}Body")
        if body is None:
            return None, None, {}
        
        # find action element in the body
        action_elem = None
        for child in body:
            action_elem = child
            break

        if action_elem is None:
            return None, None, {}
        
        # then find service type from action element
        service_type = ""
        tag = action_elem.tag
        if "{" in tag:
            service_type = tag.split("}")[0].lstrip("{")

        # action name is the local part
        action_name = tag.split("}")[-1] if "}" in tag else tag

        # get params
        params = {}
        for param in action_elem:
            local_name = param.tag.split("}")[-1] if "}" in param.tag else param.tag
            params[local_name] = param.text or ""

        return service_type, action_name, params

    def _soap_response(self, service_type, action_name, body_xml):
        """Wrap body_xml in a SOAP envelope response."""
        return (
            '<?xml version="1.0"?>\n'
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n'
            "  <s:Body>\n"
            "    <u:{0}Response xmlns:u=\"{1}\">\n"
            "      {2}\n"
            "    </u:{0}Response>\n"
            "  </s:Body>\n"
            "</s:Envelope>"
        ).format(action_name, service_type, body_xml)

    def _soap_fault(self, code, desc):
        """Generate a SOAP fault response."""
        return (
            '<?xml version="1.0"?>\n'
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n'
            "  <s:Body>\n"
            "    <s:Fault>\n"
            "      <faultcode>s:Client</faultcode>\n"
            "      <faultstring>UPnPError</faultstring>\n"
            "      <detail>\n"
            '        <UPnPError xmlns="urn:schemas-upnp-org:control-1-0">\n'
            "          <errorCode>{}</errorCode>\n"
            "          <errorDescription>{}</errorDescription>\n"
            "        </UPnPError>\n"
            "      </detail>\n"
            "    </s:Fault>\n"
            "  </s:Body>\n"
            "</s:Envelope>"
        ).format(code, desc)
        
    def _reply_soap(self, hc, xml_str, status=200):
        """Send a SOAP XML response."""
        body = xml_str.encode("utf-8", "replace")
        hc.reply(body, status, "text/xml; charset=utf-8", {"EXT": ""})
        return False

    def tx_soap_fault(self, hc, code=401, desc="Invalid Action"):
        return self._reply_soap(hc, self._soap_fault(code, desc), 500)


    # ConnectionManager control
    def tx_connmgr_ctl(self, hc: "HttpCli") -> bool:
        svc = "urn:schemas-upnp-org:service:ConnectionManager:1"

        soap_body = self._read_soap_body(hc)
        if not soap_body:
            return self.tx_soap_fault(hc, 401, "Invalid Action")

        _, action, params = self._parse_soap_action(soap_body)

        if action == "GetProtocolInfo":
            sources = []
            for ext, info in DLNA_PROTOCOL_INFO.items():
                sources.append(info)
            sources.append("http-get:*:application/octet-stream:*")
            resp_body = "<Source>{}</Source>\n    <Sink></Sink>".format(",".join(sources))
            resp = self._soap_response(svc, action, resp_body)
            return self._reply_soap(hc, resp)

        if action == "GetCurrentConnectionIDs":
            resp_body = "<ConnectionIDs></ConnectionIDs>"
            resp = self._soap_response(svc, action, resp_body)
            return self._reply_soap(hc, resp)

        if action == "GetCurrentConnectionInfo":
            resp_body = (
                "<RcsID>0</RcsID>\n"
                "    <AVTransportID>0</AVTransportID>\n"
                "    <ProtocolInfo></ProtocolInfo>\n"
                "    <PeerConnectionManager></PeerConnectionManager>\n"
                "    <PeerConnectionID>-1</PeerConnectionID>\n"
                "    <Direction>Output</Direction>\n"
                "    <Status>Unknown</Status>"
            )
            resp = self._soap_response(svc, action, resp_body)
            return self._reply_soap(hc, resp)

        return self.tx_soap_fault(hc, 401, "Invalid Action")

    # ContentDirectory control
    def tx_contentdir_ctl(self, hc: "HttpCli") -> bool:
        svc = "urn:schemas-upnp-org:service:ContentDirectory:1"

        soap_body = self._read_soap_body(hc)
        if not soap_body:
            return self.tx_soap_fault(hc, 401, "Invalid Action")

        _, action, params = self._parse_soap_action(soap_body)

        if action == "GetSystemUpdateID":
            resp_body = "<Id>0</Id>"
            resp = self._soap_response(svc, action, resp_body)
            return self._reply_soap(hc, resp)

        if action == "GetSortCapabilities":
            resp_body = "<SortCaps></SortCaps>"
            resp = self._soap_response(svc, action, resp_body)
            return self._reply_soap(hc, resp)

        if action == "GetSearchCapabilities":
            resp_body = "<SearchCaps></SearchCaps>"
            resp = self._soap_response(svc, action, resp_body)
            return self._reply_soap(hc, resp)
    
        if action == "Browse":
            return self._handle_browse(hc, svc, params)

        return self.tx_soap_fault(hc, 401, "Invalid Action")
    
    def _handle_browse(self, hc, svc, params):
        oid = params.get("ObjectID", "0")
        start = int(params.get("StartingIndex", "0"))
        count = int(params.get("RequestedCount", "0"))

        vp = _oid_decode(oid)
        base = self._base_url(hc)

        try:
            vfs, rem = self.broker.asrv.vfs.get(vp, LEELOO_DALLAS, True, False)
        except Exception:
            return self._reply_soap(hc, self._soap_fault(701, "No such object"), 500)

        dirs, files = self._collect(vfs, rem, vp)

        all_items = []
        for nm, coid in dirs:
            all_items.append(("dir", nm, coid, "", 0, 0))
        for nm, coid, ext, sz, mt in files:
            all_items.append(("file", nm, coid, ext, sz, mt))

        n_total = len(all_items)
        end = n_total if count == 0 else min(start + count, n_total)
        page = all_items[start:end]

        xml = self._build_didl(page, oid, vp, base)

        resp = self._soap_response(svc, "Browse",
            "<Result>{}</Result>\n    <NumberReturned>{}</NumberReturned>\n"
            "    <TotalMatches>{}</TotalMatches>\n    <UpdateID>0</UpdateID>"
            .format(_esc_xml(xml), len(page), n_total))
        return self._reply_soap(hc, resp)

    def _base_url(self, hc):
        '''constructs http://ip:port from the socket info'''
        sip, sport = hc.s.getsockname()[:2]
        sip = sip.replace("::ffff:", "")
        proto = "https" if self.args.https_only else "http"
        return "{}://{}:{}".format(proto, sip, sport)

    def _collect(self, vfs, rem, vp):
        '''walks vfs, returns (dirs, files) in lists'''
        dirs = []
        files = []

        try:
            _, entries, vnodes = vfs._ls(rem, LEELOO_DALLAS, True, [[True]])
        except Exception:
            entries, vnodes = [], {}

        if not vp:
            for nm, vn in sorted(self.broker.asrv.vfs.nodes.items()):
                # root level: lists volumes from vfs.nodes
                dirs.append((nm, _oid_encode(nm)))

        for nm in sorted(vnodes):
            c_vp = "{}/{}".format(vp, nm) if vp else nm
            dirs.append((nm, _oid_encode(c_vp)))

        for fname, st in entries:
            if fname.startswith("."):
                continue
            c_vp = "{}/{}".format(vp, fname) if vp else fname
            c_oid = _oid_encode(c_vp)
            if stat.S_ISDIR(st.st_mode):
                dirs.append((fname, c_oid))
            else:
                ext = os.path.splitext(fname)[1]
                files.append((fname, c_oid, ext, st.st_size, int(st.st_mtime)))

        return dirs, files

    def _build_didl(self, page, parent_oid, vp, base):
        '''build didl-lite xml for actual browsing'''
        ns = 'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"'
        ns += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ns += ' xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"'
        ns += ' xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/"'

        parts = ['<?xml version="1.0"?>\n<DIDL-Lite {}>\n'.format(ns)]

        for kind, nm, coid, ext, sz, mt in page:
            esc = _esc_xml(nm)
            if kind == "dir":
                parts.append(
                    '  <container id="{}" parentID="{}" restricted="1" childCount="0">\n'
                    "    <dc:title>{}</dc:title>\n"
                    "    <upnp:class>{}</upnp:class>\n"
                    "  </container>\n".format(coid, parent_oid, esc, CONTAINER_MIME)
                )
            else:
                fpath = "{}/{}".format(vp, nm) if vp else nm
                url = "{}/{}".format(base, "/".join(_url_quote(s) for s in fpath.split("/")))
                proto = _mime_for_ext(ext)
                cls = _dlna_class_for_ext(ext)
                date = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(mt)) if mt else ""

                parts.append(
                    '  <item id="{}" parentID="{}" restricted="1">\n'
                    "    <dc:title>{}</dc:title>\n"
                    "    <upnp:class>{}</upnp:class>\n".format(coid, parent_oid, esc, cls)
                )
                if date:
                    parts.append("    <dc:date>{}</dc:date>\n".format(date))
                parts.append(
                    '    <res protocolInfo="{}" size="{}">{}</res>\n'
                    "  </item>\n".format(proto, sz, _esc_xml(url))
                )

        parts.append("</DIDL-Lite>")
        return "".join(parts)

        


class DLNAd(MCast):
    """communicates with dlna clients over multicast, same as SSDP"""

    def __init__(self, hub: "SvcHub", ngen: int) -> None:
        al = hub.args
        vinit = al.zdv and not al.zmv
        super(DLNAd, self).__init__(
            hub, DLNA_Sck, getattr(al, "zs_on", []), getattr(al, "zs_off", []), GRP, "", 1900, vinit
        )
        self.srv: dict[socket.socket, DLNA_Sck] = {}
        self.logsrc = "DLNA-{}".format(ngen)
        self.ngen = ngen

        self.rxc = CachedSet(0.7)
        self.txc = CachedSet(5)  # win10: every 3 sec
        self.ptn_st = re.compile(b"\nst: *upnp:rootdevice", re.I)

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func(self.logsrc, msg, c)

    def run(self) -> None:
        try:
            bound = self.create_servers()
        except:
            t = "no server IP matches the dlna config\n{}"
            self.log(t.format(min_ex()), 1)
            bound = []

        if not bound:
            self.log("failed to announce copyparty services on the network", 3)
            return

        # find http port for this listening ip
        for srv in self.srv.values():
            tcps = self.hub.tcpsrv.bound
            hp = next((x[1] for x in tcps if x[0] in ("0.0.0.0", srv.ip)), 0)
            hp = hp or next((x[1] for x in tcps if x[0] == "::"), 0)
            if not hp:
                hp = tcps[0][1]
                self.log("assuming port {} for {}".format(hp, srv.ip), 3)
            srv.hport = hp

        self.log("listening")
        try:
            self.run2()
        except OSError as ex:
            if ex.errno != errno.EBADF:
                raise

            self.log("stopping due to {}".format(ex), "90")

        self.log("stopped", 2)

    def run2(self) -> None:
        try:
            if self.args.no_poll:
                raise Exception()
            fd2sck = {}
            srvpoll = select.poll()
            for sck in self.srv:
                fd = sck.fileno()
                fd2sck[fd] = sck
                srvpoll.register(fd, select.POLLIN)
        except Exception as ex:
            srvpoll = None
            if not self.args.no_poll:
                t = "WARNING: failed to poll(), will use select() instead: %r"
                self.log(t % (ex,), 3)

        while self.running:
            if srvpoll:
                pr = srvpoll.poll((self.args.z_chk or 180) * 1000)
                rx = [fd2sck[x[0]] for x in pr if x[1] & select.POLLIN]
            else:
                rdy = select.select(self.srv, [], [], self.args.z_chk or 180)
                rx: list[socket.socket] = rdy[0]  # type: ignore

            self.rxc.cln()
            buf = b""
            addr = ("0", 0)
            for sck in rx:
                try:
                    buf, addr = sck.recvfrom(4096)
                    self.eat(buf, addr)
                except:
                    if not self.running:
                        break

                    t = "{} {} \033[33m|{}| {}\n{}".format(
                        self.srv[sck].name, addr, len(buf), repr(buf)[2:-1], min_ex()
                    )
                    self.log(t, 6)

    def stop(self) -> None:
        self.running = False
        for srv in self.srv.values():
            try:
                srv.sck.close()
            except:
                pass

        self.srv.clear()

    def eat(self, buf: bytes, addr: tuple[str, int]) -> None:
        cip = addr[0]
        if cip.startswith("169.254") and not self.ll_ok:
            return

        if buf in self.rxc.c:
            return

        srv: Optional[DLNA_Sck] = self.map_client(cip)  # type: ignore
        if not srv:
            return

        self.rxc.add(buf)
        if not buf.startswith(b"M-SEARCH * HTTP/1."):
            return

        if not self.ptn_st.search(buf):
            return

        if self.args.zdv:
            t = "{} [{}] \033[36m{} \033[0m|{}|"
            self.log(t.format(srv.name, srv.ip, cip, len(buf)), "90")

        zs = """
HTTP/1.1 200 OK
CACHE-CONTROL: max-age=1800
DATE: {0}
EXT:
LOCATION: http://{1}:{2}/.cpr/dlna/device.xml
OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01
01-NLS: {3}
SERVER: UPnP/1.0
ST: upnp:rootdevice
USN: {3}::upnp:rootdevice
BOOTID.UPNP.ORG: 0
CONFIGID.UPNP.ORG: 1

"""
        v4 = srv.ip.replace("::ffff:", "")
        zs = zs.format(formatdate(), v4, srv.hport, self.args.zsid)
        zb = zs[1:].replace("\n", "\r\n").encode("utf-8", "replace")
        srv.sck.sendto(zb, addr[:2])

        if cip not in self.txc.c:
            self.log("{} [{}] --> {}".format(srv.name, srv.ip, cip), 6)

        self.txc.add(cip)
        self.txc.cln()

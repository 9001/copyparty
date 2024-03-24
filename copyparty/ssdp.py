# coding: utf-8
from __future__ import print_function, unicode_literals

import errno
import re
import select
import socket
from email.utils import formatdate

from .__init__ import TYPE_CHECKING
from .multicast import MC_Sck, MCast
from .util import CachedSet, html_escape, min_ex

if TYPE_CHECKING:
    from .httpcli import HttpCli
    from .svchub import SvcHub

if True:  # pylint: disable=using-constant-test
    from typing import Optional, Union


GRP = "239.255.255.250"


class SSDP_Sck(MC_Sck):
    def __init__(self, *a):
        super(SSDP_Sck, self).__init__(*a)
        self.hport = 0


class SSDPr(object):
    """generates http responses for httpcli"""

    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.args = hub.args

    def reply(self, hc: "HttpCli") -> bool:
        if hc.vpath.endswith("device.xml"):
            return self.tx_device(hc)

        hc.reply(b"unknown request", 400)
        return False

    def tx_device(self, hc: "HttpCli") -> bool:
        zs = """
<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <URLBase>{}</URLBase>
    <device>
        <presentationURL>{}</presentationURL>
        <deviceType>urn:schemas-upnp-org:device:Basic:1</deviceType>
        <friendlyName>{}</friendlyName>
        <modelDescription>file server</modelDescription>
        <manufacturer>ed</manufacturer>
        <manufacturerURL>https://ocv.me/</manufacturerURL>
        <modelName>copyparty</modelName>
        <modelURL>https://github.com/9001/copyparty/</modelURL>
        <UDN>{}</UDN>
        <serviceList>
            <service>
                <serviceType>urn:schemas-upnp-org:device:Basic:1</serviceType>
                <serviceId>urn:schemas-upnp-org:device:Basic</serviceId>
                <controlURL>/.cpr/ssdp/services.xml</controlURL>
                <eventSubURL>/.cpr/ssdp/services.xml</eventSubURL>
                <SCPDURL>/.cpr/ssdp/services.xml</SCPDURL>
            </service>
        </serviceList>
    </device>
</root>"""

        c = html_escape
        sip, sport = hc.s.getsockname()[:2]
        sip = sip.replace("::ffff:", "")
        proto = "https" if self.args.https_only else "http"
        ubase = "{}://{}:{}".format(proto, sip, sport)
        zsl = self.args.zsl
        url = zsl if "://" in zsl else ubase + "/" + zsl.lstrip("/")
        name = self.args.doctitle
        zs = zs.strip().format(c(ubase), c(url), c(name), c(self.args.zsid))
        hc.reply(zs.encode("utf-8", "replace"))
        return False  # close connectino


class SSDPd(MCast):
    """communicates with ssdp clients over multicast"""

    def __init__(self, hub: "SvcHub", ngen: int) -> None:
        al = hub.args
        vinit = al.zsv and not al.zmv
        super(SSDPd, self).__init__(
            hub, SSDP_Sck, al.zs_on, al.zs_off, GRP, "", 1900, vinit
        )
        self.srv: dict[socket.socket, SSDP_Sck] = {}
        self.logsrc = "SSDP-{}".format(ngen)
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
            t = "no server IP matches the ssdp config\n{}"
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
        while self.running:
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

        self.srv = {}

    def eat(self, buf: bytes, addr: tuple[str, int]) -> None:
        cip = addr[0]
        if cip.startswith("169.254") and not self.ll_ok:
            return

        if buf in self.rxc.c:
            return

        srv: Optional[SSDP_Sck] = self.map_client(cip)  # type: ignore
        if not srv:
            return

        self.rxc.add(buf)
        if not buf.startswith(b"M-SEARCH * HTTP/1."):
            return

        if not self.ptn_st.search(buf):
            return

        if self.args.zsv:
            t = "{} [{}] \033[36m{} \033[0m|{}|"
            self.log(t.format(srv.name, srv.ip, cip, len(buf)), "90")

        zs = """
HTTP/1.1 200 OK
CACHE-CONTROL: max-age=1800
DATE: {0}
EXT:
LOCATION: http://{1}:{2}/.cpr/ssdp/device.xml
OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01
01-NLS: {3}
SERVER: UPnP/1.0
ST: upnp:rootdevice
USN: {3}::upnp:rootdevice
BOOTID.UPNP.ORG: 0
CONFIGID.UPNP.ORG: 1

"""
        v4 = srv.ip.replace("::ffff:", "")
        zs = zs.format(formatdate(usegmt=True), v4, srv.hport, self.args.zsid)
        zb = zs[1:].replace("\n", "\r\n").encode("utf-8", "replace")
        srv.sck.sendto(zb, addr[:2])

        if cip not in self.txc.c:
            self.log("{} [{}] --> {}".format(srv.name, srv.ip, cip), 6)

        self.txc.add(cip)
        self.txc.cln()

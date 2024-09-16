# coding: utf-8
from __future__ import print_function, unicode_literals

import json
import time

from .__init__ import TYPE_CHECKING
from .util import Pebkac, get_df, unhumanize

if TYPE_CHECKING:
    from .httpcli import HttpCli
    from .httpsrv import HttpSrv


class Metrics(object):
    def __init__(self, hsrv: "HttpSrv") -> None:
        self.hsrv = hsrv

    def tx(self, cli: "HttpCli") -> bool:
        if not cli.avol:
            raise Pebkac(403, "not allowed for user " + cli.uname)

        args = cli.args
        if not args.stats:
            raise Pebkac(403, "the stats feature is not enabled in server config")

        conn = cli.conn
        vfs = conn.asrv.vfs
        allvols = list(sorted(vfs.all_vols.items()))

        idx = conn.get_u2idx()
        if not idx or not hasattr(idx, "p_end"):
            idx = None

        ret: list[str] = []

        def addc(k: str, v: str, desc: str) -> None:
            zs = "# TYPE %s counter\n# HELP %s %s\n%s_created %s\n%s_total %s"
            ret.append(zs % (k, k, desc, k, int(self.hsrv.t0), k, v))

        def adduc(k: str, unit: str, v: str, desc: str) -> None:
            k += "_" + unit
            zs = "# TYPE %s counter\n# UNIT %s %s\n# HELP %s %s\n%s_created %s\n%s_total %s"
            ret.append(zs % (k, k, unit, k, desc, k, int(self.hsrv.t0), k, v))

        def addg(k: str, v: str, desc: str) -> None:
            zs = "# TYPE %s gauge\n# HELP %s %s\n%s %s"
            ret.append(zs % (k, k, desc, k, v))

        def addug(k: str, unit: str, v: str, desc: str) -> None:
            k += "_" + unit
            zs = "# TYPE %s gauge\n# UNIT %s %s\n# HELP %s %s\n%s %s"
            ret.append(zs % (k, k, unit, k, desc, k, v))

        def addh(k: str, typ: str, desc: str) -> None:
            zs = "# TYPE %s %s\n# HELP %s %s"
            ret.append(zs % (k, typ, k, desc))

        def addbh(k: str, desc: str) -> None:
            zs = "# TYPE %s gauge\n# UNIT %s bytes\n# HELP %s %s"
            ret.append(zs % (k, k, k, desc))

        def addv(k: str, v: str) -> None:
            ret.append("%s %s" % (k, v))

        t = "time since last copyparty restart"
        v = "{:.3f}".format(time.time() - self.hsrv.t0)
        addug("cpp_uptime", "seconds", v, t)

        # timestamps are gauges because initial value is not zero
        t = "unixtime of last copyparty restart"
        v = "{:.3f}".format(self.hsrv.t0)
        addug("cpp_boot_unixtime", "seconds", v, t)

        t = "number of open http(s) client connections"
        addg("cpp_http_conns", str(self.hsrv.ncli), t)

        t = "number of http(s) requests since last restart"
        addc("cpp_http_reqs", str(self.hsrv.nreq), t)

        t = "number of 403/422/malicious reqs since restart"
        addc("cpp_sus_reqs", str(self.hsrv.nsus), t)

        v = str(len(conn.bans or []))
        addg("cpp_active_bans", v, "number of currently banned IPs")

        t = "number of IPs banned since last restart"
        addg("cpp_total_bans", str(self.hsrv.nban), t)

        if not args.nos_vst:
            x = self.hsrv.broker.ask("up2k.get_state", True, "")
            vs = json.loads(x.get())

            nvidle = 0
            nvbusy = 0
            nvoffline = 0
            for v in vs["volstate"].values():
                if v == "online, idle":
                    nvidle += 1
                elif "OFFLINE" in v:
                    nvoffline += 1
                else:
                    nvbusy += 1

            addg("cpp_idle_vols", str(nvidle), "number of idle/ready volumes")
            addg("cpp_busy_vols", str(nvbusy), "number of busy/indexing volumes")
            addg("cpp_offline_vols", str(nvoffline), "number of offline volumes")

            t = "time since last database activity (upload/rename/delete)"
            addug("cpp_db_idle", "seconds", str(vs["dbwt"]), t)

            t = "unixtime of last database activity (upload/rename/delete)"
            addug("cpp_db_act", "seconds", str(vs["dbwu"]), t)

            t = "number of files queued for hashing/indexing"
            addg("cpp_hashing_files", str(vs["hashq"]), t)

            t = "number of files queued for metadata scanning"
            addg("cpp_tagq_files", str(vs["tagq"]), t)

            try:
                t = "number of files queued for plugin-based analysis"
                addg("cpp_mtpq_files", str(int(vs["mtpq"])), t)
            except:
                pass

        if not args.nos_hdd:
            addbh("cpp_disk_size_bytes", "total HDD size of volume")
            addbh("cpp_disk_free_bytes", "free HDD space in volume")
            for vpath, vol in allvols:
                free, total = get_df(vol.realpath)
                if free is None or total is None:
                    continue

                addv('cpp_disk_size_bytes{vol="/%s"}' % (vpath), str(total))
                addv('cpp_disk_free_bytes{vol="/%s"}' % (vpath), str(free))

        if idx and not args.nos_vol:
            addbh("cpp_vol_bytes", "num bytes of data in volume")
            addh("cpp_vol_files", "gauge", "num files in volume")
            addbh("cpp_vol_free_bytes", "free space (vmaxb) in volume")
            addh("cpp_vol_free_files", "gauge", "free space (vmaxn) in volume")
            tnbytes = 0
            tnfiles = 0

            volsizes = []
            try:
                ptops = [x.realpath for _, x in allvols]
                x = self.hsrv.broker.ask("up2k.get_volsizes", ptops)
                volsizes = x.get()
            except Exception as ex:
                cli.log("tx_stats get_volsizes: {!r}".format(ex), 3)

            for (vpath, vol), (nbytes, nfiles) in zip(allvols, volsizes):
                tnbytes += nbytes
                tnfiles += nfiles
                addv('cpp_vol_bytes{vol="/%s"}' % (vpath), str(nbytes))
                addv('cpp_vol_files{vol="/%s"}' % (vpath), str(nfiles))

                if vol.flags.get("vmaxb") or vol.flags.get("vmaxn"):

                    zi = unhumanize(vol.flags.get("vmaxb") or "0")
                    if zi:
                        v = str(zi - nbytes)
                        addv('cpp_vol_free_bytes{vol="/%s"}' % (vpath), v)

                    zi = unhumanize(vol.flags.get("vmaxn") or "0")
                    if zi:
                        v = str(zi - nfiles)
                        addv('cpp_vol_free_files{vol="/%s"}' % (vpath), v)

            if volsizes:
                addv('cpp_vol_bytes{vol="total"}', str(tnbytes))
                addv('cpp_vol_files{vol="total"}', str(tnfiles))

        if idx and not args.nos_dup:
            addbh("cpp_dupe_bytes", "num dupe bytes in volume")
            addh("cpp_dupe_files", "gauge", "num dupe files in volume")
            tnbytes = 0
            tnfiles = 0
            for vpath, vol in allvols:
                cur = idx.get_cur(vol)
                if not cur:
                    continue

                nbytes = 0
                nfiles = 0
                q = "select sz, count(*)-1 c from up group by w having c"
                for sz, c in cur.execute(q):
                    nbytes += sz * c
                    nfiles += c

                tnbytes += nbytes
                tnfiles += nfiles
                addv('cpp_dupe_bytes{vol="/%s"}' % (vpath), str(nbytes))
                addv('cpp_dupe_files{vol="/%s"}' % (vpath), str(nfiles))

            addv('cpp_dupe_bytes{vol="total"}', str(tnbytes))
            addv('cpp_dupe_files{vol="total"}', str(tnfiles))

        if not args.nos_unf:
            addbh("cpp_unf_bytes", "incoming/unfinished uploads (num bytes)")
            addh("cpp_unf_files", "gauge", "incoming/unfinished uploads (num files)")
            tnbytes = 0
            tnfiles = 0
            try:
                x = self.hsrv.broker.ask("up2k.get_unfinished")
                xs = x.get()
                if not xs:
                    raise Exception("up2k mutex acquisition timed out")

                xj = json.loads(xs)
                for ptop, (nbytes, nfiles) in xj.items():
                    tnbytes += nbytes
                    tnfiles += nfiles
                    vol = next((x[1] for x in allvols if x[1].realpath == ptop), None)
                    if not vol:
                        t = "tx_stats get_unfinished: could not map {}"
                        cli.log(t.format(ptop), 3)
                        continue

                    addv('cpp_unf_bytes{vol="/%s"}' % (vol.vpath), str(nbytes))
                    addv('cpp_unf_files{vol="/%s"}' % (vol.vpath), str(nfiles))

                addv('cpp_unf_bytes{vol="total"}', str(tnbytes))
                addv('cpp_unf_files{vol="total"}', str(tnfiles))

            except Exception as ex:
                cli.log("tx_stats get_unfinished: {!r}".format(ex), 3)

        ret.append("# EOF")

        mime = "application/openmetrics-text; version=1.0.0; charset=utf-8"
        mime = cli.uparam.get("mime") or mime
        cli.reply("\n".join(ret).encode("utf-8"), mime=mime)
        return True

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

        def add(name: str, typ: str, v: str, desc: str) -> None:
            zs = "# HELP %s %s\n# TYPE %s %s\n%s %s"
            ret.append(zs % (name, desc, name, typ, name, v))

        def addh(name: str, typ: str, desc: str) -> None:
            zs = "# HELP %s %s\n# TYPE %s %s"
            ret.append(zs % (name, desc, name, typ))

        def addv(name: str, v: str) -> None:
            ret.append("%s %s" % (name, v))

        v = "{:.3f}".format(time.time() - self.hsrv.t0)
        add("cpp_uptime", "counter", v, "time since last server restart")

        v = str(len(conn.bans or []))
        add("cpp_bans", "counter", v, "number of banned IPs")

        if not args.nos_hdd:
            addh("cpp_disk_mib", "gauge", "total HDD size (MiB) of volume")
            addh("cpp_disk_free", "gauge", "free HDD space (MiB) in volume")
            for vpath, vol in allvols:
                free, total = get_df(vol.realpath)

                v = "{:.3f}".format(total / 1048576.0)
                addv('cpp_disk_size{vol="/%s"}' % (vpath), v)

                v = "{:.3f}".format(free / 1048576.0)
                addv('cpp_disk_free{vol="/%s"}' % (vpath), v)

        if idx and not args.nos_vol:
            addh("cpp_vol_mib", "gauge", "total MiB in volume")
            addh("cpp_vol_files", "gauge", "total num files in volume")
            addh("cpp_vol_mib_free", "gauge", "free space (vmaxb) in volume")
            addh("cpp_vol_files_free", "gauge", "free space (vmaxn) in volume")
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
                v = "{:.3f}".format(nbytes / 1048576.0)
                addv('cpp_vol_mib{vol="/%s"}' % (vpath), v)
                addv('cpp_vol_files{vol="/%s"}' % (vpath), str(nfiles))

                if vol.flags.get("vmaxb") or vol.flags.get("vmaxn"):

                    zi = unhumanize(vol.flags.get("vmaxb") or "0")
                    if zi:
                        v = "{:.3f}".format((zi - nbytes) / 1048576.0)
                        addv('cpp_vol_mib_free{vol="/%s"}' % (vpath), v)

                    zi = unhumanize(vol.flags.get("vmaxn") or "0")
                    if zi:
                        v = str(zi - nfiles)
                        addv('cpp_vol_nfiles_free{vol="/%s"}' % (vpath), v)

            if volsizes:
                v = "{:.3f}".format(tnbytes / 1048576.0)
                addv('cpp_vol_mib{vol="total"}', v)
                addv('cpp_vol_files{vol="total"}', str(tnfiles))

        if idx and not args.nos_dup:
            addh("cpp_dupe_mib", "gauge", "num dupe MiB in volume")
            addh("cpp_dupe_files", "gauge", "num dupe files in volume")
            tnbytes = 0
            tnfiles = 0
            for vpath, vol in allvols:
                cur = idx.get_cur(vol.realpath)
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
                v = "{:.3f}".format(nbytes / 1048576.0)
                addv('cpp_dupe_mib{vol="/%s"}' % (vpath), v)
                addv('cpp_dupe_files{vol="/%s"}' % (vpath), str(nfiles))

            v = "{:.3f}".format(tnbytes / 1048576.0)
            addv('cpp_dupe_mib{vol="total"}', v)
            addv('cpp_dupe_files{vol="total"}', str(tnfiles))

        if not args.nos_unf:
            addh("cpp_unf_mib", "gauge", "incoming/unfinished uploads (MiB)")
            addh("cpp_unf_files", "gauge", "incoming/unfinished uploads (num files)")
            tnbytes = 0
            tnfiles = 0
            try:
                x = self.hsrv.broker.ask("up2k.get_unfinished")
                xs = x.get()
                xj = json.loads(xs)
                for ptop, (nbytes, nfiles) in xj.items():
                    tnbytes += nbytes
                    tnfiles += nfiles
                    vol = next((x[1] for x in allvols if x[1].realpath == ptop), None)
                    if not vol:
                        t = "tx_stats get_unfinished: could not map {}"
                        cli.log(t.format(ptop), 3)
                        continue

                    v = "{:.3f}".format(nbytes / 1048576.0)
                    addv('cpp_unf_mib{vol="/%s"}' % (vol.vpath), v)
                    addv('cpp_unf_files{vol="/%s"}' % (vol.vpath), str(nfiles))

                v = "{:.3f}".format(tnbytes / 1048576.0)
                addv('cpp_unf_mib{vol="total"}', v)
                addv('cpp_unf_files{vol="total"}', str(tnfiles))

            except Exception as ex:
                cli.log("tx_stats get_unfinished: {!r}".format(ex), 3)

        cli.reply("\n".join(ret).encode("utf-8"), mime="text/plain")
        return True

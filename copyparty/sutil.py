# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import tempfile
from datetime import datetime

from .__init__ import CORES, TYPE_CHECKING
from .authsrv import LEELOO_DALLAS, VFS, AuthSrv
from .bos import bos
from .th_cli import ThumbCli
from .th_srv import TH_CH
from .util import UTC, sigblock, vjoin, vol_san

if True:  # pylint: disable=using-constant-test
    from typing import Any, Generator, Optional

    from .util import NamedLogger

if TYPE_CHECKING:
    from httpsrv import HttpSrv


TAR_NO_OPUS = set("aac|m4a|m4b|m4r|mp3|oga|ogg|opus|wma".split("|"))


class StreamArc(object):
    def __init__(
        self,
        log: "NamedLogger",
        asrv: AuthSrv,
        fgen: Generator[dict[str, Any], None, None],
        **kwargs: Any
    ):
        self.log = log
        self.asrv = asrv
        self.args = asrv.args
        self.fgen = fgen
        self.stopped = False

    def gen(self) -> Generator[Optional[bytes], None, None]:
        raise Exception("override me")

    def stop(self) -> None:
        self.stopped = True


_pools = {}


def close_pools() -> None:
    for p in list(_pools):
        try:
            p.shutdown(wait=False, cancel_futures=True)
        except:
            pass


def gfilter(
    fgen: Generator[dict[str, Any], None, None],
    thumbcli: ThumbCli,
    uname: str,
    vtop: str,
    vname: str,
    fmt: str,
) -> Generator[dict[str, Any], None, None]:
    from concurrent.futures import ThreadPoolExecutor

    pend = []
    with ThreadPoolExecutor(max_workers=CORES, initializer=sigblock) as tp:
        _pools[tp] = 1
        try:
            for f in fgen:
                task = tp.submit(enthumb, thumbcli, uname, vtop, vname, f, fmt)
                pend.append((task, f))
                if pend[0][0].done() or len(pend) > CORES * 4:
                    task, f = pend.pop(0)
                    try:
                        f = task.result(600)
                    except:
                        pass
                    yield f

            for task, f in pend:
                try:
                    f = task.result(600)
                except:
                    pass
                yield f
        except Exception as ex:
            thumbcli.log("gfilter flushing ({})".format(ex))
            for task, f in pend:
                try:
                    task.result(600)
                except:
                    pass
            thumbcli.log("gfilter flushed")
        _pools.pop(tp, None)


def gfilter2(
    fgen: Generator[
        tuple[
            "VFS",
            str,
            str,
            str,
            list[tuple[str, os.stat_result]],
            list[tuple[str, os.stat_result]],
            dict[str, "VFS"],
        ],
        None,
        None,
    ],
    hsrv: "HttpSrv",
    vtop: str,
    fmts: list[str],
) -> Generator[dict[str, Any], None, None]:
    from concurrent.futures import ThreadPoolExecutor

    pend = []
    with ThreadPoolExecutor(max_workers=CORES, initializer=sigblock) as tp:
        _pools[tp] = 1
        for _, _, vpath, apath, files, rd, vd in fgen:
            if "/.hist/" in vpath:
                continue
            fnames = [n[0] for n in files]
            vpaths = [vpath + "/" + n for n in fnames] if vpath else fnames
            for vp, fi in zip(vpaths, files):
                for fmt in fmts:
                    try:
                        f = {"vp": vp, "st": fi[1]}
                        task = tp.submit(
                            enthumb, hsrv.thumbcli, LEELOO_DALLAS, vtop, "", f, fmt
                        )
                        pend.append((task, f))
                        if pend[0][0].done() or len(pend) > CORES * 4:
                            task, f = pend.pop(0)
                            try:
                                f = task.result(600)
                            except:
                                pass
                            yield f
                    except:
                        pass
        for task, f in pend:
            try:
                f = task.result(600)
            except:
                pass
            yield f
        _pools.pop(tp, None)


def enthumb(
    thumbcli: ThumbCli, uname: str, vtop: str, vname: str, f: dict[str, Any], fmt: str
) -> dict[str, Any]:
    rem = f["vp"]
    ext = rem.rsplit(".", 1)[-1].lower()
    if (fmt == "mp3" and ext == "mp3") or (fmt == "opus" and ext in TAR_NO_OPUS):
        raise Exception()

    if vname:
        vp = vjoin(vtop, rem.split("/", 1)[1])
    else:
        vp = vjoin(vtop, rem)
    vn, rem = thumbcli.asrv.vfs.get(vp, uname, True, False)
    dbv, vrem = vn.get_dbv(rem)
    thp = thumbcli.get(dbv, vrem, f["st"].st_mtime, fmt)
    if not thp:
        raise Exception()

    ext = fmt if fmt == "wav" else TH_CH.get(fmt[:1], fmt)
    sz = bos.path.getsize(thp)
    st: os.stat_result = f["st"]
    ts = st.st_mtime
    f["ap"] = thp
    f["vp"] = f["vp"].rsplit(".", 1)[0] + "." + ext
    f["st"] = os.stat_result((st.st_mode, -1, -1, 1, 1000, 1000, sz, ts, ts, ts))
    return f


def errdesc(
    vfs: VFS, errors: list[tuple[str, str]]
) -> tuple[dict[str, Any], list[str]]:
    report = ["copyparty failed to add the following files to the archive:", ""]

    for fn, err in errors:
        report.extend([" file: %r" % (fn,), "error: %s" % (err,), ""])

    btxt = "\r\n".join(report).encode("utf-8", "replace")
    btxt = vol_san(list(vfs.all_vols.values()), btxt)

    with tempfile.NamedTemporaryFile(prefix="copyparty-", delete=False) as tf:
        tf_path = tf.name
        tf.write(btxt)

    dt = datetime.now(UTC).strftime("%Y-%m%d-%H%M%S")

    bos.chmod(tf_path, 0o444)
    return {
        "vp": "archive-errors-{}.txt".format(dt),
        "ap": tf_path,
        "st": bos.stat(tf_path),
    }, report

# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import tempfile
from datetime import datetime

from .__init__ import CORES
from .bos import bos
from .th_cli import ThumbCli
from .util import UTC, vjoin

if True:  # pylint: disable=using-constant-test
    from typing import Any, Generator, Optional

    from .util import NamedLogger


class StreamArc(object):
    def __init__(
        self,
        log: "NamedLogger",
        fgen: Generator[dict[str, Any], None, None],
        **kwargs: Any
    ):
        self.log = log
        self.fgen = fgen
        self.stopped = False

    def gen(self) -> Generator[Optional[bytes], None, None]:
        raise Exception("override me")

    def stop(self) -> None:
        self.stopped = True


def gfilter(
    fgen: Generator[dict[str, Any], None, None],
    thumbcli: ThumbCli,
    uname: str,
    vtop: str,
    fmt: str,
) -> Generator[dict[str, Any], None, None]:
    from concurrent.futures import ThreadPoolExecutor

    pend = []
    with ThreadPoolExecutor(max_workers=CORES) as tp:
        try:
            for f in fgen:
                task = tp.submit(enthumb, thumbcli, uname, vtop, f, fmt)
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


def enthumb(
    thumbcli: ThumbCli, uname: str, vtop: str, f: dict[str, Any], fmt: str
) -> dict[str, Any]:
    rem = f["vp"]
    ext = rem.rsplit(".", 1)[-1].lower()
    if fmt == "opus" and ext in "aac|m4a|mp3|ogg|opus|wma".split("|"):
        raise Exception()

    vp = vjoin(vtop, rem.split("/", 1)[1])
    vn, rem = thumbcli.asrv.vfs.get(vp, uname, True, False)
    dbv, vrem = vn.get_dbv(rem)
    thp = thumbcli.get(dbv, vrem, f["st"].st_mtime, fmt)
    if not thp:
        raise Exception()

    ext = "jpg" if fmt == "j" else "webp" if fmt == "w" else fmt
    sz = bos.path.getsize(thp)
    st: os.stat_result = f["st"]
    ts = st.st_mtime
    f["ap"] = thp
    f["vp"] = f["vp"].rsplit(".", 1)[0] + "." + ext
    f["st"] = os.stat_result((st.st_mode, -1, -1, 1, 1000, 1000, sz, ts, ts, ts))
    return f


def errdesc(errors: list[tuple[str, str]]) -> tuple[dict[str, Any], list[str]]:
    report = ["copyparty failed to add the following files to the archive:", ""]

    for fn, err in errors:
        report.extend([" file: {}".format(fn), "error: {}".format(err), ""])

    with tempfile.NamedTemporaryFile(prefix="copyparty-", delete=False) as tf:
        tf_path = tf.name
        tf.write("\r\n".join(report).encode("utf-8", "replace"))

    dt = datetime.now(UTC).strftime("%Y-%m%d-%H%M%S")

    bos.chmod(tf_path, 0o444)
    return {
        "vp": "archive-errors-{}.txt".format(dt),
        "ap": tf_path,
        "st": bos.stat(tf_path),
    }, report

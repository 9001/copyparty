# coding: utf-8
from __future__ import print_function, unicode_literals

import time
import shlex
import subprocess as sp

from .__init__ import PY2
from .util import fsenc


class VCR_Direct(object):
    def __init__(self, cli, fpath):
        self.cli = cli
        self.fpath = fpath

        self.log_func = cli.log_func
        self.log_src = cli.log_src

    def log(self, msg, c=0):
        self.log_func(self.log_src, "vcr: {}".format(msg), c)

    def run(self):
        opts = self.cli.uparam

        # fmt: off
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-v", "warning",
            "-i", fsenc(self.fpath),
            "-vf", "scale=640:-4",
            "-c:a", "libopus",
            "-b:a", "128k",
            "-c:v", "libvpx",
            "-deadline", "realtime",
            "-row-mt", "1"
        ]
        # fmt: on

        if "ss" in opts:
            cmd.extend(["-ss", opts["ss"]])

        if "crf" in opts:
            cmd.extend(["-b:v", "0", "-crf", opts["crf"]])
        else:
            cmd.extend(["-b:v", "{}M".format(opts.get("mbps", 1.2))])

        cmd.extend(["-f", "webm", "-"])

        comp = str if not PY2 else unicode
        cmd = [x.encode("utf-8") if isinstance(x, comp) else x for x in cmd]

        self.log(" ".join([shlex.quote(x.decode("utf-8", "replace")) for x in cmd]))

        p = sp.Popen(cmd, stdout=sp.PIPE)

        self.cli.send_headers(None, mime="video/webm")

        fails = 0
        while True:
            self.log("read")
            buf = p.stdout.read(1024 * 4)
            if not buf:
                fails += 1
                if p.poll() is not None or fails > 30:
                    self.log("ffmpeg exited")
                    return

                time.sleep(0.1)
                continue

            fails = 0
            try:
                self.cli.s.sendall(buf)
            except:
                self.log("client disconnected")
                p.kill()
                return

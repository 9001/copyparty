#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

"""copyparty: http file sharing hub (py2/py3)"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"

import time
import argparse
import threading
from textwrap import dedent
import multiprocessing as mp

from .__version__ import *
from .tcpsrv import *


class RiceFormatter(argparse.HelpFormatter):
    def _get_help_string(self, action):
        """
        same as ArgumentDefaultsHelpFormatter(HelpFormatter)
        except the help += [...] line now has colors
        """
        help = action.help
        if "%(default)" not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += "\033[36m (default: \033[35m%(default)s\033[36m)\033[0m"
        return help

    def _fill_text(self, text, width, indent):
        """same as RawDescriptionHelpFormatter(HelpFormatter)"""
        return "".join(indent + line + "\n" for line in text.splitlines())


def main():
    try:
        # support vscode debugger (bonus: same behavior as on windows)
        mp.set_start_method("spawn", True)
    except:
        # py2.7 probably
        pass

    ap = argparse.ArgumentParser(
        formatter_class=RiceFormatter,
        prog="copyparty",
        description="http file sharing hub v{} ({})".format(S_VERSION, S_BUILD_DT),
        epilog=dedent(
            """
            -a takes username:password,
            -v takes path:permset:permset:... where "permset" is
               accesslevel followed by username (no separator)
            
            example:\033[35m
              -a ed:hunter2 -v .:r:aed -v ../inc:w:aed  \033[36m
              share current directory with
               * r (read-only) for everyone
               * a (read+write) for ed
              share ../inc with
               * w (write-only) for everyone
               * a (read+write) for ed  \033[0m
            
            if no accounts or volumes are configured,
            current folder will be read/write for everyone

            consider the config file for more flexible account/volume management,
            including dynamic reload at runtime (and being more readable w)
            """
        ),
    )
    ap.add_argument("-c", metavar="PATH", type=str, help="config file")
    ap.add_argument("-i", metavar="IP", type=str, default="0.0.0.0", help="ip to bind")
    ap.add_argument("-p", metavar="PORT", type=int, default=1234, help="port to bind")
    ap.add_argument("-nc", metavar="NUM", type=int, default=16, help="max num clients")
    ap.add_argument("-j", metavar="CORES", type=int, help="max num cpu cores")
    ap.add_argument("-a", metavar="ACCT", type=str, help="add account")
    ap.add_argument("-v", metavar="VOL", type=str, help="add volume")
    ap.add_argument("-nw", action="store_true", help="DEBUG: disable writing")
    al = ap.parse_args()

    tcpsrv = TcpSrv(al)
    thr = threading.Thread(target=tcpsrv.run)
    thr.daemon = True
    thr.start()

    # winxp/py2.7 support: thr.join() kills signals
    try:
        while True:
            time.sleep(9001)
    except KeyboardInterrupt:
        print("OPYTHAT")
        tcpsrv.shutdown()
        print("nailed it")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

"""copyparty: http file sharing hub (py2/py3)"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"

import os
import shutil
import filecmp
import locale
import argparse
from textwrap import dedent

from .__init__ import E, WINDOWS, VT100
from .__version__ import S_VERSION, S_BUILD_DT, CODENAME
from .svchub import SvcHub
from .util import py_desc


class RiceFormatter(argparse.HelpFormatter):
    def _get_help_string(self, action):
        """
        same as ArgumentDefaultsHelpFormatter(HelpFormatter)
        except the help += [...] line now has colors
        """
        fmt = "\033[36m (default: \033[35m%(default)s\033[36m)\033[0m"
        if not VT100:
            fmt = " (default: %(default)s)"

        help = action.help
        if "%(default)" not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += fmt
        return help

    def _fill_text(self, text, width, indent):
        """same as RawDescriptionHelpFormatter(HelpFormatter)"""
        return "".join(indent + line + "\n" for line in text.splitlines())


def ensure_locale():
    for x in [
        "en_US.UTF-8",
        "English_United States.UTF8",
        "English_United States.1252",
    ]:
        try:
            locale.setlocale(locale.LC_ALL, x)
            print("Locale:", x)
            break
        except:
            continue


def ensure_cert():
    """
    the default cert (and the entire TLS support) is only here to enable the
    crypto.subtle javascript API, which is necessary due to the webkit guys
    being massive memers (https://www.chromium.org/blink/webcrypto)

    i feel awful about this and so should they
    """
    cert_insec = os.path.join(E.mod, "res/insecure.pem")
    cert_cfg = os.path.join(E.cfg, "cert.pem")
    if not os.path.exists(cert_cfg):
        shutil.copy2(cert_insec, cert_cfg)

    try:
        if filecmp.cmp(cert_cfg, cert_insec):
            print(
                "\033[33m  using default TLS certificate; https will be insecure."
                + "\033[36m\n  certificate location: {}\033[0m\n".format(cert_cfg)
            )
    except:
        pass

    # speaking of the default cert,
    # printf 'NO\n.\n.\n.\n.\ncopyparty-insecure\n.\n' | faketime '2000-01-01 00:00:00' openssl req -x509 -sha256 -newkey rsa:2048 -keyout insecure.pem -out insecure.pem -days $((($(printf %d 0x7fffffff)-$(date +%s --date=2000-01-01T00:00:00Z))/(60*60*24))) -nodes && ls -al insecure.pem && openssl x509 -in insecure.pem -text -noout


def main():
    if WINDOWS:
        os.system("")  # enables colors

    desc = py_desc().replace("[", "\033[1;30m[")

    f = '\033[36mcopyparty v{} "\033[35m{}\033[36m" ({})\n{}\033[0m\n'
    print(f.format(S_VERSION, CODENAME, S_BUILD_DT, desc))

    ensure_locale()
    ensure_cert()

    ap = argparse.ArgumentParser(
        formatter_class=RiceFormatter,
        prog="copyparty",
        description="http file sharing hub v{} ({})".format(S_VERSION, S_BUILD_DT),
        epilog=dedent(
            """
            -a takes username:password,
            -v takes src:dst:permset:permset:... where "permset" is
               accesslevel followed by username (no separator)
            
            example:\033[35m
              -a ed:hunter2 -v .::r:aed -v ../inc:dump:w:aed  \033[36m
              mount current directory at "/" with
               * r (read-only) for everyone
               * a (read+write) for ed
              mount ../inc at "/dump" with
               * w (write-only) for everyone
               * a (read+write) for ed  \033[0m
            
            if no accounts or volumes are configured,
            current folder will be read/write for everyone

            consider the config file for more flexible account/volume management,
            including dynamic reload at runtime (and being more readable w)
            """
        ),
    )
    ap.add_argument(
        "-c", metavar="PATH", type=str, action="append", help="add config file"
    )
    ap.add_argument("-i", metavar="IP", type=str, default="0.0.0.0", help="ip to bind")
    ap.add_argument("-p", metavar="PORT", type=int, default=3923, help="port to bind")
    ap.add_argument("-nc", metavar="NUM", type=int, default=64, help="max num clients")
    ap.add_argument(
        "-j", metavar="CORES", type=int, default=1, help="max num cpu cores"
    )
    ap.add_argument("-a", metavar="ACCT", type=str, action="append", help="add account")
    ap.add_argument("-v", metavar="VOL", type=str, action="append", help="add volume")
    ap.add_argument("-q", action="store_true", help="quiet")
    ap.add_argument("-ed", action="store_true", help="enable ?dots")
    ap.add_argument("-nw", action="store_true", help="disable writes (benchmark)")
    ap.add_argument("-nih", action="store_true", help="no info hostname")
    ap.add_argument("-nid", action="store_true", help="no info disk-usage")
    al = ap.parse_args()

    SvcHub(al).run()


if __name__ == "__main__":
    main()

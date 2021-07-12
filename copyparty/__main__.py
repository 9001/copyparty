#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, unicode_literals

"""copyparty: http file sharing hub (py2/py3)"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"

import re
import os
import sys
import time
import shutil
import filecmp
import locale
import argparse
import threading
import traceback
from textwrap import dedent

from .__init__ import E, WINDOWS, VT100, PY2, unicode
from .__version__ import S_VERSION, S_BUILD_DT, CODENAME
from .svchub import SvcHub
from .util import py_desc, align_tab, IMPLICATIONS

HAVE_SSL = True
try:
    import ssl
except:
    HAVE_SSL = False

printed = ""


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


class Dodge11874(RiceFormatter):
    def __init__(self, *args, **kwargs):
        kwargs["width"] = 9003
        super(Dodge11874, self).__init__(*args, **kwargs)


def lprint(*a, **ka):
    global printed

    printed += " ".join(unicode(x) for x in a) + ka.get("end", "\n")
    print(*a, **ka)


def warn(msg):
    lprint("\033[1mwarning:\033[0;33m {}\033[0m\n".format(msg))


def ensure_locale():
    for x in [
        "en_US.UTF-8",
        "English_United States.UTF8",
        "English_United States.1252",
    ]:
        try:
            locale.setlocale(locale.LC_ALL, x)
            lprint("Locale:", x)
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
            lprint(
                "\033[33m  using default TLS certificate; https will be insecure."
                + "\033[36m\n  certificate location: {}\033[0m\n".format(cert_cfg)
            )
    except:
        pass

    # speaking of the default cert,
    # printf 'NO\n.\n.\n.\n.\ncopyparty-insecure\n.\n' | faketime '2000-01-01 00:00:00' openssl req -x509 -sha256 -newkey rsa:2048 -keyout insecure.pem -out insecure.pem -days $((($(printf %d 0x7fffffff)-$(date +%s --date=2000-01-01T00:00:00Z))/(60*60*24))) -nodes && ls -al insecure.pem && openssl x509 -in insecure.pem -text -noout


def configure_ssl_ver(al):
    def terse_sslver(txt):
        txt = txt.lower()
        for c in ["_", "v", "."]:
            txt = txt.replace(c, "")

        return txt.replace("tls10", "tls1")

    # oh man i love openssl
    # check this out
    # hold my beer
    ptn = re.compile(r"^OP_NO_(TLS|SSL)v")
    sslver = terse_sslver(al.ssl_ver).split(",")
    flags = [k for k in ssl.__dict__ if ptn.match(k)]
    # SSLv2 SSLv3 TLSv1 TLSv1_1 TLSv1_2 TLSv1_3
    if "help" in sslver:
        avail = [terse_sslver(x[6:]) for x in flags]
        avail = " ".join(sorted(avail) + ["all"])
        lprint("\navailable ssl/tls versions:\n  " + avail)
        sys.exit(0)

    al.ssl_flags_en = 0
    al.ssl_flags_de = 0
    for flag in sorted(flags):
        ver = terse_sslver(flag[6:])
        num = getattr(ssl, flag)
        if ver in sslver:
            al.ssl_flags_en |= num
        else:
            al.ssl_flags_de |= num

    if sslver == ["all"]:
        x = al.ssl_flags_en
        al.ssl_flags_en = al.ssl_flags_de
        al.ssl_flags_de = x

    for k in ["ssl_flags_en", "ssl_flags_de"]:
        num = getattr(al, k)
        lprint("{}: {:8x} ({})".format(k, num, num))

    # think i need that beer now


def configure_ssl_ciphers(al):
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    if al.ssl_ver:
        ctx.options &= ~al.ssl_flags_en
        ctx.options |= al.ssl_flags_de

    is_help = al.ciphers == "help"

    if al.ciphers and not is_help:
        try:
            ctx.set_ciphers(al.ciphers)
        except:
            lprint("\n\033[1;31mfailed to set ciphers\033[0m\n")

    if not hasattr(ctx, "get_ciphers"):
        lprint("cannot read cipher list: openssl or python too old")
    else:
        ciphers = [x["description"] for x in ctx.get_ciphers()]
        lprint("\n  ".join(["\nenabled ciphers:"] + align_tab(ciphers) + [""]))

    if is_help:
        sys.exit(0)


def sighandler(sig=None, frame=None):
    msg = [""] * 5
    for th in threading.enumerate():
        msg.append(str(th))
        msg.extend(traceback.format_stack(sys._current_frames()[th.ident]))

    msg.append("\n")
    print("\n".join(msg))


def run_argparse(argv, formatter):
    ap = argparse.ArgumentParser(
        formatter_class=formatter,
        prog="copyparty",
        description="http file sharing hub v{} ({})".format(S_VERSION, S_BUILD_DT),
        epilog=dedent(
            """
            -a takes username:password,
            -v takes src:dst:permset:permset:cflag:cflag:...
               where "permset" is accesslevel followed by username (no separator)
               and "cflag" is config flags to set on this volume
            
            list of cflags:
              "cnodupe" rejects existing files (instead of symlinking them)
              "ce2d" sets -e2d (all -e2* args can be set using ce2* cflags)
              "cd2t" disables metadata collection, overrides -e2t*
              "cd2d" disables all database stuff, overrides -e2*

            example:\033[35m
              -a ed:hunter2 -v .::r:aed -v ../inc:dump:w:aed:cnodupe  \033[36m
              mount current directory at "/" with
               * r (read-only) for everyone
               * a (read+write) for ed
              mount ../inc at "/dump" with
               * w (write-only) for everyone
               * a (read+write) for ed
               * reject duplicate files  \033[0m
            
            if no accounts or volumes are configured,
            current folder will be read/write for everyone

            consider the config file for more flexible account/volume management,
            including dynamic reload at runtime (and being more readable w)

            values for --urlform:
              "stash" dumps the data to file and returns length + checksum
              "save,get" dumps to file and returns the page like a GET
              "print,get" prints the data in the log and returns GET
              (leave out the ",get" to return an error instead)

            values for --ls:
              "USR" is a user to browse as; * is anonymous, ** is all users
              "VOL" is a single volume to scan, default is * (all vols)
              "FLAG" is flags;
                "v" in addition to realpaths, print usernames and vpaths
                "ln" only prints symlinks leaving the volume mountpoint
                "p" exits 1 if any such symlinks are found
                "r" resumes startup after the listing
            examples:
              --ls '**'          # list all files which are possible to read
              --ls '**,*,ln'     # check for dangerous symlinks
              --ls '**,*,ln,p,r' # check, then start normally if safe
            \033[0m
            """
        ),
    )
    # fmt: off
    u = unicode
    ap2 = ap.add_argument_group('general options')
    ap2.add_argument("-c", metavar="PATH", type=u, action="append", help="add config file")
    ap2.add_argument("-nc", metavar="NUM", type=int, default=64, help="max num clients")
    ap2.add_argument("-j", metavar="CORES", type=int, default=1, help="max num cpu cores")
    ap2.add_argument("-a", metavar="ACCT", type=u, action="append", help="add account, USER:PASS; example [ed:wark")
    ap2.add_argument("-v", metavar="VOL", type=u, action="append", help="add volume, SRC:DST:FLAG; example [.::r], [/mnt/nas/music:/music:r:aed")
    ap2.add_argument("-ed", action="store_true", help="enable ?dots")
    ap2.add_argument("-emp", action="store_true", help="enable markdown plugins")
    ap2.add_argument("-mcr", metavar="SEC", type=int, default=60, help="md-editor mod-chk rate")
    ap2.add_argument("--dotpart", action="store_true", help="dotfile incomplete uploads")
    ap2.add_argument("--sparse", metavar="MiB", type=int, default=4, help="up2k min.size threshold (mswin-only)")
    ap2.add_argument("--urlform", metavar="MODE", type=u, default="print,get", help="how to handle url-forms; examples: [stash], [save,get]")

    ap2 = ap.add_argument_group('network options')
    ap2.add_argument("-i", metavar="IP", type=u, default="0.0.0.0", help="ip to bind (comma-sep.)")
    ap2.add_argument("-p", metavar="PORT", type=u, default="3923", help="ports to bind (comma/range)")
    ap2.add_argument("--rproxy", metavar="DEPTH", type=int, default=1, help="which ip to keep; 0 = tcp, 1 = origin (first x-fwd), 2 = cloudflare, 3 = nginx, -1 = closest proxy")
    
    ap2 = ap.add_argument_group('SSL/TLS options')
    ap2.add_argument("--http-only", action="store_true", help="disable ssl/tls")
    ap2.add_argument("--https-only", action="store_true", help="disable plaintext")
    ap2.add_argument("--ssl-ver", metavar="LIST", type=u, help="set allowed ssl/tls versions; [help] shows available versions; default is what your python version considers safe")
    ap2.add_argument("--ciphers", metavar="LIST", type=u, help="set allowed ssl/tls ciphers; [help] shows available ciphers")
    ap2.add_argument("--ssl-dbg", action="store_true", help="dump some tls info")
    ap2.add_argument("--ssl-log", metavar="PATH", type=u, help="log master secrets")

    ap2 = ap.add_argument_group('opt-outs')
    ap2.add_argument("-nw", action="store_true", help="disable writes (benchmark)")
    ap2.add_argument("-nih", action="store_true", help="no info hostname")
    ap2.add_argument("-nid", action="store_true", help="no info disk-usage")
    ap2.add_argument("--no-zip", action="store_true", help="disable download as zip/tar")

    ap2 = ap.add_argument_group('safety options')
    ap2.add_argument("--ls", metavar="U[,V[,F]]", type=u, help="scan all volumes; arguments USER,VOL,FLAGS; example [**,*,ln,p,r]")
    ap2.add_argument("--salt", type=u, default="hunter2", help="up2k file-hash salt")

    ap2 = ap.add_argument_group('logging options')
    ap2.add_argument("-q", action="store_true", help="quiet")
    ap2.add_argument("-lo", metavar="PATH", type=u, help="logfile, example: cpp-%%Y-%%m%%d-%%H%%M%%S.txt.xz")
    ap2.add_argument("--log-conn", action="store_true", help="print tcp-server msgs")
    ap2.add_argument("--log-htp", action="store_true", help="print http-server threadpool scaling")
    ap2.add_argument("--ihead", metavar="HEADER", type=u, action='append', help="dump incoming header")
    ap2.add_argument("--lf-url", metavar="RE", type=u, default=r"^/\.cpr/|\?th=[wj]$", help="dont log URLs matching")

    ap2 = ap.add_argument_group('admin panel options')
    ap2.add_argument("--no-rescan", action="store_true", help="disable ?scan (volume reindexing)")
    ap2.add_argument("--no-stack", action="store_true", help="disable ?stack (list all stacks)")

    ap2 = ap.add_argument_group('thumbnail options')
    ap2.add_argument("--no-thumb", action="store_true", help="disable all thumbnails")
    ap2.add_argument("--no-vthumb", action="store_true", help="disable video thumbnails")
    ap2.add_argument("--th-size", metavar="WxH", default="320x256", help="thumbnail res")
    ap2.add_argument("--th-no-crop", action="store_true", help="dynamic height; show full image")
    ap2.add_argument("--th-no-jpg", action="store_true", help="disable jpg output")
    ap2.add_argument("--th-no-webp", action="store_true", help="disable webp output")
    ap2.add_argument("--th-ff-jpg", action="store_true", help="force jpg for video thumbs")
    ap2.add_argument("--th-poke", metavar="SEC", type=int, default=300, help="activity labeling cooldown")
    ap2.add_argument("--th-clean", metavar="SEC", type=int, default=43200, help="cleanup interval; 0=disabled")
    ap2.add_argument("--th-maxage", metavar="SEC", type=int, default=604800, help="max folder age")
    ap2.add_argument("--th-covers", metavar="N,N", type=u, default="folder.png,folder.jpg,cover.png,cover.jpg", help="folder thumbnails to stat for")

    ap2 = ap.add_argument_group('database options')
    ap2.add_argument("-e2d", action="store_true", help="enable up2k database")
    ap2.add_argument("-e2ds", action="store_true", help="enable up2k db-scanner, sets -e2d")
    ap2.add_argument("-e2dsa", action="store_true", help="scan all folders (for search), sets -e2ds")
    ap2.add_argument("-e2t", action="store_true", help="enable metadata indexing")
    ap2.add_argument("-e2ts", action="store_true", help="enable metadata scanner, sets -e2t")
    ap2.add_argument("-e2tsr", action="store_true", help="rescan all metadata, sets -e2ts")
    ap2.add_argument("--hist", metavar="PATH", type=u, help="where to store volume state")
    ap2.add_argument("--no-hash", action="store_true", help="disable hashing during e2ds folder scans")
    ap2.add_argument("--no-mutagen", action="store_true", help="use ffprobe for tags instead")
    ap2.add_argument("--no-mtag-mt", action="store_true", help="disable tag-read parallelism")
    ap2.add_argument("-mtm", metavar="M=t,t,t", type=u, action="append", help="add/replace metadata mapping")
    ap2.add_argument("-mte", metavar="M,M,M", type=u, help="tags to index/display (comma-sep.)",
        default="circle,album,.tn,artist,title,.bpm,key,.dur,.q,.vq,.aq,ac,vc,res,.fps")
    ap2.add_argument("-mtp", metavar="M=[f,]bin", type=u, action="append", help="read tag M using bin")
    ap2.add_argument("--srch-time", metavar="SEC", type=int, default=30, help="search deadline")

    ap2 = ap.add_argument_group('appearance options')
    ap2.add_argument("--css-browser", metavar="L", type=u, help="URL to additional CSS to include")

    ap2 = ap.add_argument_group('debug options')
    ap2.add_argument("--no-sendfile", action="store_true", help="disable sendfile")
    ap2.add_argument("--no-scandir", action="store_true", help="disable scandir")
    ap2.add_argument("--no-fastboot", action="store_true", help="wait for up2k indexing")
    ap2.add_argument("--no-htp", action="store_true", help="disable httpserver threadpool, create threads as-needed instead")
    ap2.add_argument("--stackmon", metavar="P,S", type=u, help="write stacktrace to Path every S second")
    ap2.add_argument("--log-thrs", metavar="SEC", type=float, help="list active threads every SEC")
    
    return ap.parse_args(args=argv[1:])
    # fmt: on


def main(argv=None):
    time.strptime("19970815", "%Y%m%d")  # python#7980
    if WINDOWS:
        os.system("rem")  # enables colors

    if argv is None:
        argv = sys.argv

    desc = py_desc().replace("[", "\033[1;30m[")

    f = '\033[36mcopyparty v{} "\033[35m{}\033[36m" ({})\n{}\033[0m\n'
    lprint(f.format(S_VERSION, CODENAME, S_BUILD_DT, desc))

    ensure_locale()
    if HAVE_SSL:
        ensure_cert()

    deprecated = [["-e2s", "-e2ds"]]
    for dk, nk in deprecated:
        try:
            idx = argv.index(dk)
        except:
            continue

        msg = "\033[1;31mWARNING:\033[0;1m\n  {} \033[0;33mwas replaced with\033[0;1m {} \033[0;33mand will be removed\n\033[0m"
        lprint(msg.format(dk, nk))
        argv[idx] = nk
        time.sleep(2)

    try:
        al = run_argparse(argv, RiceFormatter)
    except AssertionError:
        al = run_argparse(argv, Dodge11874)

    # propagate implications
    for k1, k2 in IMPLICATIONS:
        if getattr(al, k1):
            setattr(al, k2, True)

    al.i = al.i.split(",")
    try:
        if "-" in al.p:
            lo, hi = [int(x) for x in al.p.split("-")]
            al.p = list(range(lo, hi + 1))
        else:
            al.p = [int(x) for x in al.p.split(",")]
    except:
        raise Exception("invalid value for -p")

    if HAVE_SSL:
        if al.ssl_ver:
            configure_ssl_ver(al)

        if al.ciphers:
            configure_ssl_ciphers(al)
    else:
        warn("ssl module does not exist; cannot enable https")

    if PY2 and WINDOWS and al.e2d:
        warn(
            "windows py2 cannot do unicode filenames with -e2d\n"
            + "  (if you crash with codec errors then that is why)"
        )

    if sys.version_info < (3, 6):
        al.no_scandir = True

    # signal.signal(signal.SIGINT, sighandler)

    SvcHub(al, argv, printed).run()


if __name__ == "__main__":
    main()

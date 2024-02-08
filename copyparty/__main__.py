#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function, unicode_literals

"""copyparty: http file sharing hub (py2/py3)"""
__author__ = "ed <copyparty@ocv.me>"
__copyright__ = 2019
__license__ = "MIT"
__url__ = "https://github.com/9001/copyparty/"

import argparse
import base64
import locale
import os
import re
import socket
import sys
import threading
import time
import traceback
import uuid

from .__init__ import (
    ANYWIN,
    CORES,
    EXE,
    MACOS,
    PY2,
    VT100,
    WINDOWS,
    E,
    EnvParams,
    unicode,
)
from .__version__ import CODENAME, S_BUILD_DT, S_VERSION
from .authsrv import expand_config_file, split_cfg_ln, upgrade_cfg_fmt
from .cfg import flagcats, onedash
from .svchub import SvcHub
from .util import (
    APPLESAN_TXT,
    DEF_EXP,
    DEF_MTE,
    DEF_MTH,
    IMPLICATIONS,
    JINJA_VER,
    PY_DESC,
    PYFTPD_VER,
    SQLITE_VER,
    UNPLICATIONS,
    align_tab,
    ansi_re,
    dedent,
    min_ex,
    pybin,
    termsize,
    wrap,
)

if True:  # pylint: disable=using-constant-test
    from collections.abc import Callable
    from types import FrameType

    from typing import Any, Optional

try:
    HAVE_SSL = True
    import ssl
except:
    HAVE_SSL = False

u = unicode
printed: list[str] = []
zsid = uuid.uuid4().urn[4:]


class RiceFormatter(argparse.HelpFormatter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if PY2:
            kwargs["width"] = termsize()[0]

        super(RiceFormatter, self).__init__(*args, **kwargs)

    def _get_help_string(self, action: argparse.Action) -> str:
        """
        same as ArgumentDefaultsHelpFormatter(HelpFormatter)
        except the help += [...] line now has colors
        """
        fmt = "\033[36m (default: \033[35m%(default)s\033[36m)\033[0m"
        if not VT100:
            fmt = " (default: %(default)s)"

        ret = unicode(action.help)
        if "%(default)" not in ret:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    ret += fmt

        if not VT100:
            ret = re.sub("\033\\[[0-9;]+m", "", ret)

        return ret  # type: ignore

    def _fill_text(self, text: str, width: int, indent: str) -> str:
        """same as RawDescriptionHelpFormatter(HelpFormatter)"""
        return "".join(indent + line + "\n" for line in text.splitlines())

    def __add_whitespace(self, idx: int, iWSpace: int, text: str) -> str:
        return (" " * iWSpace) + text if idx else text

    def _split_lines(self, text: str, width: int) -> list[str]:
        # https://stackoverflow.com/a/35925919
        textRows = text.splitlines()
        ptn = re.compile(r"\s*[0-9\-]{0,}\.?\s*")
        for idx, line in enumerate(textRows):
            search = ptn.search(line)
            if not line.strip():
                textRows[idx] = " "
            elif search:
                lWSpace = search.end()
                lines = [
                    self.__add_whitespace(i, lWSpace, x)
                    for i, x in enumerate(wrap(line, width, width - 1))
                ]
                textRows[idx] = lines  # type: ignore

        return [item for sublist in textRows for item in sublist]


class Dodge11874(RiceFormatter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["width"] = 9003
        super(Dodge11874, self).__init__(*args, **kwargs)


class BasicDodge11874(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["width"] = 9003
        super(BasicDodge11874, self).__init__(*args, **kwargs)


def lprint(*a: Any, **ka: Any) -> None:
    eol = ka.pop("end", "\n")
    txt: str = " ".join(unicode(x) for x in a) + eol
    printed.append(txt)
    if not VT100:
        txt = ansi_re.sub("", txt)

    print(txt, end="", **ka)


def warn(msg: str) -> None:
    lprint("\033[1mwarning:\033[0;33m {}\033[0m\n".format(msg))


def init_E(EE: EnvParams) -> None:
    # __init__ runs 18 times when oxidized; do expensive stuff here

    E = EE  # pylint: disable=redefined-outer-name

    def get_unixdir() -> str:
        paths: list[tuple[Callable[..., Any], str]] = [
            (os.environ.get, "XDG_CONFIG_HOME"),
            (os.path.expanduser, "~/.config"),
            (os.environ.get, "TMPDIR"),
            (os.environ.get, "TEMP"),
            (os.environ.get, "TMP"),
            (unicode, "/tmp"),
        ]
        for chk in [os.listdir, os.mkdir]:
            for pf, pa in paths:
                try:
                    p = pf(pa)
                    # print(chk.__name__, p, pa)
                    if not p or p.startswith("~"):
                        continue

                    p = os.path.normpath(p)
                    chk(p)  # type: ignore
                    p = os.path.join(p, "copyparty")
                    if not os.path.isdir(p):
                        os.mkdir(p)

                    return p  # type: ignore
                except:
                    pass

        raise Exception("could not find a writable path for config")

    def _unpack() -> str:
        import atexit
        import tarfile
        import tempfile
        from importlib.resources import open_binary

        td = tempfile.TemporaryDirectory(prefix="")
        atexit.register(td.cleanup)
        tdn = td.name

        with open_binary("copyparty", "z.tar") as tgz:
            with tarfile.open(fileobj=tgz) as tf:
                try:
                    tf.extractall(tdn, filter="tar")
                except TypeError:
                    tf.extractall(tdn)  # nosec (archive is safe)

        return tdn

    try:
        E.mod = os.path.dirname(os.path.realpath(__file__))
        if E.mod.endswith("__init__"):
            E.mod = os.path.dirname(E.mod)
    except:
        if not E.ox:
            raise

        E.mod = _unpack()

    if sys.platform == "win32":
        bdir = os.environ.get("APPDATA") or os.environ.get("TEMP") or "."
        E.cfg = os.path.normpath(bdir + "/copyparty")
    elif sys.platform == "darwin":
        E.cfg = os.path.expanduser("~/Library/Preferences/copyparty")
    else:
        E.cfg = get_unixdir()

    E.cfg = E.cfg.replace("\\", "/")
    try:
        os.makedirs(E.cfg)
    except:
        if not os.path.isdir(E.cfg):
            raise


def get_srvname() -> str:
    try:
        ret: str = unicode(socket.gethostname()).split(".")[0]
    except:
        ret = ""

    if ret not in ["", "localhost"]:
        return ret

    fp = os.path.join(E.cfg, "name.txt")
    lprint("using hostname from {}\n".format(fp))
    try:
        with open(fp, "rb") as f:
            ret = f.read().decode("utf-8", "replace").strip()
    except:
        ret = ""
        namelen = 5
        while len(ret) < namelen:
            ret += base64.b32encode(os.urandom(4))[:7].decode("utf-8").lower()
            ret = re.sub("[234567=]", "", ret)[:namelen]
        with open(fp, "wb") as f:
            f.write(ret.encode("utf-8") + b"\n")

    return ret


def get_fk_salt() -> str:
    fp = os.path.join(E.cfg, "fk-salt.txt")
    try:
        with open(fp, "rb") as f:
            ret = f.read().strip()
    except:
        ret = base64.b64encode(os.urandom(18))
        with open(fp, "wb") as f:
            f.write(ret + b"\n")

    return ret.decode("utf-8")


def get_ah_salt() -> str:
    fp = os.path.join(E.cfg, "ah-salt.txt")
    try:
        with open(fp, "rb") as f:
            ret = f.read().strip()
    except:
        ret = base64.b64encode(os.urandom(18))
        with open(fp, "wb") as f:
            f.write(ret + b"\n")

    return ret.decode("utf-8")


def ensure_locale() -> None:
    safe = "en_US.UTF-8"
    for x in [
        safe,
        "English_United States.UTF8",
        "English_United States.1252",
    ]:
        try:
            locale.setlocale(locale.LC_ALL, x)
            if x != safe:
                lprint("Locale: {}\n".format(x))
            return
        except:
            continue

    t = "setlocale {} failed,\n  sorting and dates might get funky\n"
    warn(t.format(safe))


def ensure_webdeps() -> None:
    ap = os.path.join(E.mod, "web/deps/mini-fa.woff")
    if os.path.exists(ap):
        return

    warn(
        """could not find webdeps;
  if you are running the sfx, or exe, or pypi package, or docker image,
  then this is a bug! Please let me know so I can fix it, thanks :-)
  https://github.com/9001/copyparty/issues/new?labels=bug&template=bug_report.md

  however, if you are a dev, or running copyparty from source, and you want
  full client functionality, you will need to build or obtain the webdeps:
  https://github.com/9001/copyparty/blob/hovudstraum/docs/devnotes.md#building
    """
    )


def configure_ssl_ver(al: argparse.Namespace) -> None:
    def terse_sslver(txt: str) -> str:
        txt = txt.lower()
        for c in ["_", "v", "."]:
            txt = txt.replace(c, "")

        return txt.replace("tls10", "tls1")

    # oh man i love openssl
    # check this out
    # hold my beer
    assert ssl
    ptn = re.compile(r"^OP_NO_(TLS|SSL)v")
    sslver = terse_sslver(al.ssl_ver).split(",")
    flags = [k for k in ssl.__dict__ if ptn.match(k)]
    # SSLv2 SSLv3 TLSv1 TLSv1_1 TLSv1_2 TLSv1_3
    if "help" in sslver:
        avail1 = [terse_sslver(x[6:]) for x in flags]
        avail = " ".join(sorted(avail1) + ["all"])
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
        lprint("{0}: {1:8x} ({1})".format(k, num))

    # think i need that beer now


def configure_ssl_ciphers(al: argparse.Namespace) -> None:
    assert ssl
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


def args_from_cfg(cfg_path: str) -> list[str]:
    lines: list[str] = []
    expand_config_file(lines, cfg_path, "")
    lines = upgrade_cfg_fmt(None, argparse.Namespace(vc=False), lines, "")

    ret: list[str] = []
    skip = True
    for ln in lines:
        sn = ln.split("  #")[0].strip()
        if sn.startswith("["):
            skip = True
        if sn.startswith("[global]"):
            skip = False
            continue
        if skip or not sn.split("#")[0].strip():
            continue
        for k, v in split_cfg_ln(sn).items():
            k = k.lstrip("-")
            if not k:
                continue
            prefix = "-" if k in onedash else "--"
            if v is True:
                ret.append(prefix + k)
            else:
                ret.append(prefix + k + "=" + v)

    return ret


def sighandler(sig: Optional[int] = None, frame: Optional[FrameType] = None) -> None:
    msg = [""] * 5
    for th in threading.enumerate():
        stk = sys._current_frames()[th.ident]  # type: ignore
        msg.append(str(th))
        msg.extend(traceback.format_stack(stk))

    msg.append("\n")
    print("\n".join(msg))


def disable_quickedit() -> None:
    import atexit
    import ctypes
    from ctypes import wintypes

    def ecb(ok: bool, fun: Any, args: list[Any]) -> list[Any]:
        if not ok:
            err: int = ctypes.get_last_error()  # type: ignore
            if err:
                raise ctypes.WinError(err)  # type: ignore
        return args

    k32 = ctypes.WinDLL(str("kernel32"), use_last_error=True)  # type: ignore
    if PY2:
        wintypes.LPDWORD = ctypes.POINTER(wintypes.DWORD)

    k32.GetStdHandle.errcheck = ecb  # type: ignore
    k32.GetConsoleMode.errcheck = ecb  # type: ignore
    k32.SetConsoleMode.errcheck = ecb  # type: ignore
    k32.GetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.LPDWORD)
    k32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)

    def cmode(out: bool, mode: Optional[int] = None) -> int:
        h = k32.GetStdHandle(-11 if out else -10)
        if mode:
            return k32.SetConsoleMode(h, mode)  # type: ignore

        cmode = wintypes.DWORD()
        k32.GetConsoleMode(h, ctypes.byref(cmode))
        return cmode.value

    # disable quickedit
    mode = orig_in = cmode(False)
    quickedit = 0x40
    extended = 0x80
    mask = quickedit + extended
    if mode & mask != extended:
        atexit.register(cmode, False, orig_in)
        cmode(False, mode & ~mask | extended)

    # enable colors in case the os.system("rem") trick ever stops working
    if VT100:
        mode = orig_out = cmode(True)
        if mode & 4 != 4:
            atexit.register(cmode, True, orig_out)
            cmode(True, mode | 4)


def showlic() -> None:
    p = os.path.join(E.mod, "res", "COPYING.txt")
    if not os.path.exists(p):
        print("no relevant license info to display")
        return

    with open(p, "rb") as f:
        print(f.read().decode("utf-8", "replace"))


def get_sects():
    return [
        [
            "accounts",
            "accounts and volumes",
            dedent(
                """
            -a takes username:password,
            -v takes src:dst:\033[33mperm\033[0m1:\033[33mperm\033[0m2:\033[33mperm\033[0mN:\033[32mvolflag\033[0m1:\033[32mvolflag\033[0m2:\033[32mvolflag\033[0mN:...
                * "\033[33mperm\033[0m" is "permissions,username1,username2,..."
                * "\033[32mvolflag\033[0m" is config flags to set on this volume

            --grp takes groupname:username1,username2,...
            and groupnames can be used instead of usernames in -v
            by prefixing the groupname with %

            list of permissions:
              "r" (read):   list folder contents, download files
              "w" (write):  upload files; need "r" to see the uploads
              "m" (move):   move files and folders; need "w" at destination
              "d" (delete): permanently delete files and folders
              "g" (get):    download files, but cannot see folder contents
              "G" (upget):  "get", but can see filekeys of their own uploads
              "h" (html):   "get", but folders return their index.html
              "." (dots):   user can ask to show dotfiles in listings
              "a" (admin):  can see uploader IPs, config-reload
              "A" ("all"):  same as "rwmda." (read/write/move/delete/admin/dotfiles)

            too many volflags to list here, see --help-flags

            example:\033[35m
              -a ed:hunter2 -v .::r:rw,ed -v ../inc:dump:w:rw,ed:c,nodupe  \033[36m
              mount current directory at "/" with
               * r (read-only) for everyone
               * rw (read+write) for ed
              mount ../inc at "/dump" with
               * w (write-only) for everyone
               * rw (read+write) for ed
               * reject duplicate files  \033[0m

            if no accounts or volumes are configured,
            current folder will be read/write for everyone

            consider the config file for more flexible account/volume management,
            including dynamic reload at runtime (and being more readable w)
            """
            ),
        ],
        [
            "flags",
            "list of volflags",
            dedent(
                """
            volflags are appended to volume definitions, for example,
            to create a write-only volume with the \033[33mnodupe\033[0m and \033[32mnosub\033[0m flags:
              \033[35m-v /mnt/inc:/inc:w\033[33m:c,nodupe\033[32m:c,nosub\033[0m

            if global config defines a volflag for all volumes,
            you can unset it for a specific volume with -flag
            """
            ).rstrip()
            + build_flags_desc(),
        ],
        [
            "handlers",
            "use plugins to handle certain events",
            dedent(
                """
            usually copyparty returns a \033[33m404\033[0m if a file does not exist, and
            \033[33m403\033[0m if a user tries to access a file they don't have access to

            you can load a plugin which will be invoked right before this
            happens, and the plugin can choose to override this behavior

            load the plugin using --args or volflags; for example \033[36m
             --on404 ~/partyhandlers/not404.py
             -v .::r:c,on404=~/partyhandlers/not404.py
            \033[0m
            the file must define the function \033[35mmain(cli,vn,rem)\033[0m:
             \033[35mcli\033[0m: the copyparty HttpCli instance
             \033[35mvn\033[0m:  the VFS which overlaps with the requested URL
             \033[35mrem\033[0m: the remainder of the URL below the VFS mountpoint

            `main` must return a string; one of the following:

            > \033[32m"true"\033[0m: the plugin has responded to the request,
                and the TCP connection should be kept open

            > \033[32m"false"\033[0m: the plugin has responded to the request,
                and the TCP connection should be terminated

            > \033[32m"retry"\033[0m: the plugin has done something to resolve the 404
                situation, and copyparty should reattempt reading the file.
                if it still fails, a regular 404 will be returned

            > \033[32m"allow"\033[0m: should ignore the insufficient permissions
                and let the client continue anyways

            > \033[32m""\033[0m: the plugin has not handled the request;
                try the next plugin or return the usual 404 or 403

            \033[1;35mPS!\033[0m the folder that contains the python file should ideally
              not contain many other python files, and especially nothing
              with filenames that overlap with modules used by copyparty
            """
            ),
        ],
        [
            "hooks",
            "execute commands before/after various events",
            dedent(
                """
            execute a command (a program or script) before or after various events;
             \033[36mxbu\033[35m executes CMD before a file upload starts
             \033[36mxau\033[35m executes CMD after  a file upload finishes
             \033[36mxiu\033[35m executes CMD after  all uploads finish and volume is idle
             \033[36mxbr\033[35m executes CMD before a file rename/move
             \033[36mxar\033[35m executes CMD after  a file rename/move
             \033[36mxbd\033[35m executes CMD before a file delete
             \033[36mxad\033[35m executes CMD after  a file delete
             \033[36mxm\033[35m executes CMD on message
             \033[36mxban\033[35m executes CMD if someone gets banned
            \033[0m
            can be defined as --args or volflags; for example \033[36m
             --xau notify-send
             -v .::r:c,xau=notify-send
            \033[0m
            commands specified as --args are appended to volflags;
            each --arg and volflag can be specified multiple times,
            each command will execute in order unless one returns non-zero

            optionally prefix the command with comma-sep. flags similar to -mtp:

             \033[36mf\033[35m forks the process, doesn't wait for completion
             \033[36mc\033[35m checks return code, blocks the action if non-zero
             \033[36mj\033[35m provides json with info as 1st arg instead of filepath
             \033[36mwN\033[35m waits N sec after command has been started before continuing
             \033[36mtN\033[35m sets an N sec timeout before the command is abandoned
             \033[36miN\033[35m xiu only: volume must be idle for N sec (default = 5)

             \033[36mkt\033[35m kills the entire process tree on timeout (default),
             \033[36mkm\033[35m kills just the main process
             \033[36mkn\033[35m lets it continue running until copyparty is terminated

             \033[36mc0\033[35m show all process output (default)
             \033[36mc1\033[35m show only stderr
             \033[36mc2\033[35m show only stdout
             \033[36mc3\033[35m mute all process otput
            \033[0m
            each hook is executed once for each event, except for \033[36mxiu\033[0m
            which builds up a backlog of uploads, running the hook just once
            as soon as the volume has been idle for iN seconds (5 by default)

            \033[36mxiu\033[0m is also unique in that it will pass the metadata to the
            executed program on STDIN instead of as argv arguments, and
            it also includes the wark (file-id/hash) as a json property

            \033[36mxban\033[0m can be used to overrule / cancel a user ban event;
            if the program returns 0 (true/OK) then the ban will NOT happen

            except for \033[36mxm\033[0m, only one hook / one action can run at a time,
            so it's recommended to use the \033[36mf\033[0m flag unless you really need
            to wait for the hook to finish before continuing (without \033[36mf\033[0m
            the upload speed can easily drop to 10% for small files)"""
            ),
        ],
        [
            "urlform",
            "how to handle url-form POSTs",
            dedent(
                """
            values for --urlform:
              \033[36mstash\033[35m dumps the data to file and returns length + checksum
              \033[36msave,get\033[35m dumps to file and returns the page like a GET
              \033[36mprint,get\033[35m prints the data in the log and returns GET
              (leave out the ",get" to return an error instead)
            """
            ),
        ],
        [
            "exp",
            "text expansion",
            dedent(
                """
            specify --exp or the "exp" volflag to enable placeholder expansions
            in README.md / .prologue.html / .epilogue.html

            --exp-md (volflag exp_md) holds the list of placeholders which can be
            expanded in READMEs, and --exp-lg (volflag exp_lg) likewise for logues;
            any placeholder not given in those lists will be ignored and shown as-is

            the default list will expand the following placeholders:
            \033[36m{{self.ip}}     \033[35mclient ip
            \033[36m{{self.ua}}     \033[35mclient user-agent
            \033[36m{{self.uname}}  \033[35mclient username
            \033[36m{{self.host}}   \033[35mthe "Host" header, or the server's external IP otherwise
            \033[36m{{cfg.name}}    \033[35mthe --name global-config
            \033[36m{{cfg.logout}}  \033[35mthe --logout global-config
            \033[36m{{vf.scan}}     \033[35mthe "scan" volflag
            \033[36m{{vf.thsize}}   \033[35mthumbnail size
            \033[36m{{srv.itime}}   \033[35mserver time in seconds
            \033[36m{{srv.htime}}   \033[35mserver time as YY-mm-dd, HH:MM:SS (UTC)
            \033[36m{{hdr.cf_ipcountry}} \033[35mthe "CF-IPCountry" client header (probably blank)
            \033[0m
            so the following types of placeholders can be added to the lists:
            * any client header can be accessed through {{hdr.*}}
            * any variable in httpcli.py can be accessed through {{self.*}}
            * any global server setting can be accessed through {{cfg.*}}
            * any volflag can be accessed through {{vf.*}}

            remove vf.scan from default list using --exp-md /vf.scan
            add "accept" header to def. list using --exp-md +hdr.accept

            for performance reasons, expansion only happens while embedding
            documents into directory listings, and when accessing a ?doc=...
            link, but never otherwise, so if you click a -txt- link you'll
            have to refresh the page to apply expansion
            """
            ),
        ],
        [
            "ls",
            "volume inspection",
            dedent(
                """
            \033[35m--ls USR,VOL,FLAGS
              \033[36mUSR\033[0m is a user to browse as; * is anonymous, ** is all users
              \033[36mVOL\033[0m is a single volume to scan, default is * (all vols)
              \033[36mFLAG\033[0m is flags;
                \033[36mv\033[0m in addition to realpaths, print usernames and vpaths
                \033[36mln\033[0m only prints symlinks leaving the volume mountpoint
                \033[36mp\033[0m exits 1 if any such symlinks are found
                \033[36mr\033[0m resumes startup after the listing

            examples:
              --ls '**'          # list all files which are possible to read
              --ls '**,*,ln'     # check for dangerous symlinks
              --ls '**,*,ln,p,r' # check, then start normally if safe
            """
            ),
        ],
        [
            "dbd",
            "database durability profiles",
            dedent(
                """
            mainly affects uploads of many small files on slow HDDs; speeds measured uploading 520 files on a WD20SPZX (SMR 2.5" 5400rpm 4kb)

            \033[32macid\033[0m = extremely safe but slow; the old default. Should never lose any data no matter what

            \033[32mswal\033[0m = 2.4x faster uploads yet 99.9% as safe -- theoretical chance of losing metadata for the ~200 most recently uploaded files if there's a power-loss or your OS crashes

            \033[32mwal\033[0m = another 21x faster on HDDs yet 90% as safe; same pitfall as \033[33mswal\033[0m except more likely

            \033[32myolo\033[0m = another 1.5x faster, and removes the occasional sudden upload-pause while the disk syncs, but now you're at risk of losing the entire database in a powerloss / OS-crash

            profiles can be set globally (--dbd=yolo), or per-volume with volflags: -v ~/Music:music:r:c,dbd=acid
            """
            ),
        ],
        [
            "pwhash",
            "password hashing",
            dedent(
                """
            when \033[36m--ah-alg\033[0m is not the default [\033[32mnone\033[0m], all account passwords must be hashed

            passwords can be hashed on the commandline with \033[36m--ah-gen\033[0m, but
            copyparty will also hash and print any passwords that are non-hashed
            (password which do not start with '+') and then terminate afterwards

            \033[36m--ah-alg\033[0m specifies the hashing algorithm and a
               list of optional comma-separated arguments:

            \033[36m--ah-alg argon2\033[0m  # which is the same as:
            \033[36m--ah-alg argon2,3,256,4,19\033[0m
            use argon2id with timecost 3, 256 MiB, 4 threads, version 19 (0x13/v1.3)

            \033[36m--ah-alg scrypt\033[0m  # which is the same as:
            \033[36m--ah-alg scrypt,13,2,8,4\033[0m
            use scrypt with cost 2**13, 2 iterations, blocksize 8, 4 threads

            \033[36m--ah-alg sha2\033[0m  # which is the same as:
            \033[36m--ah-alg sha2,424242\033[0m
            use sha2-512 with 424242 iterations

            recommended: \033[32m--ah-alg argon2\033[0m
              (takes about 0.4 sec and 256M RAM to process a new password)

            argon2 needs python-package argon2-cffi,
            scrypt needs openssl,
            sha2 is always available
            """
            ),
        ],
        [
            "zm",
            "mDNS debugging",
            dedent(
                """
            the mDNS protocol is multicast-based, which means there are thousands
            of fun and intersesting ways for it to break unexpectedly

            things to check if it does not work at all:

            * is there a firewall blocking port 5353 on either the server or client?
              (for example, clients may be able to send queries to copyparty,
               but the replies could get lost)

            * is multicast accidentally disabled on either the server or client?
              (look for mDNS log messages saying "new client on [...]")

            * the router/switch must be multicast and igmp capable

            things to check if it works for a while but then it doesn't:

            * is there a firewall blocking port 5353 on either the server or client?
              (copyparty may be unable to see the queries from the clients, but the
               clients may still be able to see the initial unsolicited announce,
               so it works for about 2 minutes after startup until TTL expires)

            * does the client have multiple IPs on its interface, and some of the
              IPs are in subnets which the copyparty server is not a member of?

            for both of the above intermittent issues, try --zm-spam 30
            (not spec-compliant but nothing will mind)
            """
            ),
        ],
    ]


def build_flags_desc():
    ret = ""
    for grp, flags in flagcats.items():
        ret += "\n\n\033[0m" + grp
        for k, v in flags.items():
            v = v.replace("\n", "\n    ")
            ret += "\n  \033[36m{}\033[35m {}".format(k, v)

    return ret + "\033[0m"


# fmt: off


def add_general(ap, nc, srvname):
    ap2 = ap.add_argument_group('general options')
    ap2.add_argument("-c", metavar="PATH", type=u, action="append", help="add config file")
    ap2.add_argument("-nc", metavar="NUM", type=int, default=nc, help="max num clients")
    ap2.add_argument("-j", metavar="CORES", type=int, default=1, help="max num cpu cores, 0=all")
    ap2.add_argument("-a", metavar="ACCT", type=u, action="append", help="add account, \033[33mUSER\033[0m:\033[33mPASS\033[0m; example [\033[32med:wark\033[0m]")
    ap2.add_argument("-v", metavar="VOL", type=u, action="append", help="add volume, \033[33mSRC\033[0m:\033[33mDST\033[0m:\033[33mFLAG\033[0m; examples [\033[32m.::r\033[0m], [\033[32m/mnt/nas/music:/music:r:aed\033[0m], see --help-accounts")
    ap2.add_argument("--grp", metavar="G:N,N", type=u, action="append", help="add group, \033[33mNAME\033[0m:\033[33mUSER1\033[0m,\033[33mUSER2\033[0m,\033[33m...\033[0m; example [\033[32madmins:ed,foo,bar\033[0m]")
    ap2.add_argument("-ed", action="store_true", help="enable the ?dots url parameter / client option which allows clients to see dotfiles / hidden files (volflag=dots)")
    ap2.add_argument("--urlform", metavar="MODE", type=u, default="print,get", help="how to handle url-form POSTs; see \033[33m--help-urlform\033[0m")
    ap2.add_argument("--wintitle", metavar="TXT", type=u, default="cpp @ $pub", help="server terminal title, for example [\033[32m$ip-10.1.2.\033[0m] or [\033[32m$ip-]")
    ap2.add_argument("--name", metavar="TXT", type=u, default=srvname, help="server name (displayed topleft in browser and in mDNS)")
    ap2.add_argument("--license", action="store_true", help="show licenses and exit")
    ap2.add_argument("--version", action="store_true", help="show versions and exit")


def add_qr(ap, tty):
    ap2 = ap.add_argument_group('qr options')
    ap2.add_argument("--qr", action="store_true", help="show http:// QR-code on startup")
    ap2.add_argument("--qrs", action="store_true", help="show https:// QR-code on startup")
    ap2.add_argument("--qrl", metavar="PATH", type=u, default="", help="location to include in the url, for example [\033[32mpriv/?pw=hunter2\033[0m]")
    ap2.add_argument("--qri", metavar="PREFIX", type=u, default="", help="select IP which starts with \033[33mPREFIX\033[0m; [\033[32m.\033[0m] to force default IP when mDNS URL would have been used instead")
    ap2.add_argument("--qr-fg", metavar="COLOR", type=int, default=0 if tty else 16, help="foreground; try [\033[32m0\033[0m] if the qr-code is unreadable")
    ap2.add_argument("--qr-bg", metavar="COLOR", type=int, default=229, help="background (white=255)")
    ap2.add_argument("--qrp", metavar="CELLS", type=int, default=4, help="padding (spec says 4 or more, but 1 is usually fine)")
    ap2.add_argument("--qrz", metavar="N", type=int, default=0, help="[\033[32m1\033[0m]=1x, [\033[32m2\033[0m]=2x, [\033[32m0\033[0m]=auto (try [\033[32m2\033[0m] on broken fonts)")


def add_fs(ap):
    ap2 = ap.add_argument_group("filesystem options")
    rm_re_def = "5/0.1" if ANYWIN else "0/0"
    ap2.add_argument("--rm-retry", metavar="T/R", type=u, default=rm_re_def, help="if a file cannot be deleted because it is busy, continue trying for \033[33mT\033[0m seconds, retry every \033[33mR\033[0m seconds; disable with 0/0 (volflag=rm_retry)")


def add_upload(ap):
    ap2 = ap.add_argument_group('upload options')
    ap2.add_argument("--dotpart", action="store_true", help="dotfile incomplete uploads, hiding them from clients unless \033[33m-ed\033[0m")
    ap2.add_argument("--plain-ip", action="store_true", help="when avoiding filename collisions by appending the uploader's ip to the filename: append the plaintext ip instead of salting and hashing the ip")
    ap2.add_argument("--unpost", metavar="SEC", type=int, default=3600*12, help="grace period where uploads can be deleted by the uploader, even without delete permissions; 0=disabled, default=12h")
    ap2.add_argument("--blank-wt", metavar="SEC", type=int, default=300, help="file write grace period (any client can write to a blank file last-modified more recently than \033[33mSEC\033[0m seconds ago)")
    ap2.add_argument("--reg-cap", metavar="N", type=int, default=38400, help="max number of uploads to keep in memory when running without \033[33m-e2d\033[0m; roughly 1 MiB RAM per 600")
    ap2.add_argument("--no-fpool", action="store_true", help="disable file-handle pooling -- instead, repeatedly close and reopen files during upload (bad idea to enable this on windows and/or cow filesystems)")
    ap2.add_argument("--use-fpool", action="store_true", help="force file-handle pooling, even when it might be dangerous (multiprocessing, filesystems lacking sparse-files support, ...)")
    ap2.add_argument("--hardlink", action="store_true", help="prefer hardlinks instead of symlinks when possible (within same filesystem) (volflag=hardlink)")
    ap2.add_argument("--never-symlink", action="store_true", help="do not fallback to symlinks when a hardlink cannot be made (volflag=neversymlink)")
    ap2.add_argument("--no-dedup", action="store_true", help="disable symlink/hardlink creation; copy file contents instead (volflag=copydupes)")
    ap2.add_argument("--no-dupe", action="store_true", help="reject duplicate files during upload; only matches within the same volume (volflag=nodupe)")
    ap2.add_argument("--no-snap", action="store_true", help="disable snapshots -- forget unfinished uploads on shutdown; don't create .hist/up2k.snap files -- abandoned/interrupted uploads must be cleaned up manually")
    ap2.add_argument("--snap-wri", metavar="SEC", type=int, default=300, help="write upload state to ./hist/up2k.snap every \033[33mSEC\033[0m seconds; allows resuming incomplete uploads after a server crash")
    ap2.add_argument("--snap-drop", metavar="MIN", type=float, default=1440, help="forget unfinished uploads after \033[33mMIN\033[0m minutes; impossible to resume them after that (360=6h, 1440=24h)")
    ap2.add_argument("--u2ts", metavar="TXT", type=u, default="c", help="how to timestamp uploaded files; [\033[32mc\033[0m]=client-last-modified, [\033[32mu\033[0m]=upload-time, [\033[32mfc\033[0m]=force-c, [\033[32mfu\033[0m]=force-u (volflag=u2ts)")
    ap2.add_argument("--rand", action="store_true", help="force randomized filenames, \033[33m--nrand\033[0m chars long (volflag=rand)")
    ap2.add_argument("--nrand", metavar="NUM", type=int, default=9, help="randomized filenames length (volflag=nrand)")
    ap2.add_argument("--magic", action="store_true", help="enable filetype detection on nameless uploads (volflag=magic)")
    ap2.add_argument("--df", metavar="GiB", type=float, default=0, help="ensure \033[33mGiB\033[0m free disk space by rejecting upload requests")
    ap2.add_argument("--sparse", metavar="MiB", type=int, default=4, help="windows-only: minimum size of incoming uploads through up2k before they are made into sparse files")
    ap2.add_argument("--turbo", metavar="LVL", type=int, default=0, help="configure turbo-mode in up2k client; [\033[32m-1\033[0m] = forbidden/always-off, [\033[32m0\033[0m] = default-off and warn if enabled, [\033[32m1\033[0m] = default-off, [\033[32m2\033[0m] = on, [\033[32m3\033[0m] = on and disable datecheck")
    ap2.add_argument("--u2j", metavar="JOBS", type=int, default=2, help="web-client: number of file chunks to upload in parallel; 1 or 2 is good for low-latency (same-country) connections, 4-8 for android clients, 16 for cross-atlantic (max=64)")
    ap2.add_argument("--u2sort", metavar="TXT", type=u, default="s", help="upload order; [\033[32ms\033[0m]=smallest-first, [\033[32mn\033[0m]=alphabetical, [\033[32mfs\033[0m]=force-s, [\033[32mfn\033[0m]=force-n -- alphabetical is a bit slower on fiber/LAN but makes it easier to eyeball if everything went fine")
    ap2.add_argument("--write-uplog", action="store_true", help="write POST reports to textfiles in working-directory")


def add_network(ap):
    ap2 = ap.add_argument_group('network options')
    ap2.add_argument("-i", metavar="IP", type=u, default="::", help="ip to bind (comma-sep.), default: all IPv4 and IPv6")
    ap2.add_argument("-p", metavar="PORT", type=u, default="3923", help="ports to bind (comma/range)")
    ap2.add_argument("--ll", action="store_true", help="include link-local IPv4/IPv6 in mDNS replies, even if the NIC has routable IPs (breaks some mDNS clients)")
    ap2.add_argument("--rproxy", metavar="DEPTH", type=int, default=1, help="which ip to associate clients with; [\033[32m0\033[0m]=tcp, [\033[32m1\033[0m]=origin (first x-fwd, unsafe), [\033[32m2\033[0m]=outermost-proxy, [\033[32m3\033[0m]=second-proxy, [\033[32m-1\033[0m]=closest-proxy")
    ap2.add_argument("--xff-hdr", metavar="NAME", type=u, default="x-forwarded-for", help="if reverse-proxied, which http header to read the client's real ip from")
    ap2.add_argument("--xff-src", metavar="IP", type=u, default="127., ::1", help="comma-separated list of trusted reverse-proxy IPs; only accept the real-ip header (\033[33m--xff-hdr\033[0m) if the incoming connection is from an IP starting with either of these. Can be disabled with [\033[32many\033[0m] if you are behind cloudflare (or similar) and are using \033[32m--xff-hdr=cf-connecting-ip\033[0m (or similar)")
    ap2.add_argument("--ipa", metavar="PREFIX", type=u, default="", help="only accept connections from IP-addresses starting with \033[33mPREFIX\033[0m; example: [\033[32m127., 10.89., 192.168.\033[0m]")
    ap2.add_argument("--rp-loc", metavar="PATH", type=u, default="", help="if reverse-proxying on a location instead of a dedicated domain/subdomain, provide the base location here; example: [\033[32m/foo/bar\033[0m]")
    if ANYWIN:
        ap2.add_argument("--reuseaddr", action="store_true", help="set reuseaddr on listening sockets on windows; allows rapid restart of copyparty at the expense of being able to accidentally start multiple instances")
    else:
        ap2.add_argument("--freebind", action="store_true", help="allow listening on IPs which do not yet exist, for example if the network interfaces haven't finished going up. Only makes sense for IPs other than '0.0.0.0', '127.0.0.1', '::', and '::1'. May require running as root (unless net.ipv6.ip_nonlocal_bind)")
    ap2.add_argument("--s-thead", metavar="SEC", type=int, default=120, help="socket timeout (read request header)")
    ap2.add_argument("--s-tbody", metavar="SEC", type=float, default=186, help="socket timeout (read/write request/response bodies). Use 60 on fast servers (default is extremely safe). Disable with 0 if reverse-proxied for a 2%% speed boost")
    ap2.add_argument("--s-wr-sz", metavar="B", type=int, default=256*1024, help="socket write size in bytes")
    ap2.add_argument("--s-wr-slp", metavar="SEC", type=float, default=0, help="debug: socket write delay in seconds")
    ap2.add_argument("--rsp-slp", metavar="SEC", type=float, default=0, help="debug: response delay in seconds")
    ap2.add_argument("--rsp-jtr", metavar="SEC", type=float, default=0, help="debug: response delay, random duration 0..\033[33mSEC\033[0m")


def add_tls(ap, cert_path):
    ap2 = ap.add_argument_group('SSL/TLS options')
    ap2.add_argument("--http-only", action="store_true", help="disable ssl/tls -- force plaintext")
    ap2.add_argument("--https-only", action="store_true", help="disable plaintext -- force tls")
    ap2.add_argument("--cert", metavar="PATH", type=u, default=cert_path, help="path to TLS certificate")
    ap2.add_argument("--ssl-ver", metavar="LIST", type=u, help="set allowed ssl/tls versions; [\033[32mhelp\033[0m] shows available versions; default is what your python version considers safe")
    ap2.add_argument("--ciphers", metavar="LIST", type=u, help="set allowed ssl/tls ciphers; [\033[32mhelp\033[0m] shows available ciphers")
    ap2.add_argument("--ssl-dbg", action="store_true", help="dump some tls info")
    ap2.add_argument("--ssl-log", metavar="PATH", type=u, help="log master secrets for later decryption in wireshark")


def add_cert(ap, cert_path):
    cert_dir = os.path.dirname(cert_path)
    ap2 = ap.add_argument_group('TLS certificate generator options')
    ap2.add_argument("--no-crt", action="store_true", help="disable automatic certificate creation")
    ap2.add_argument("--crt-ns", metavar="N,N", type=u, default="", help="comma-separated list of FQDNs (domains) to add into the certificate")
    ap2.add_argument("--crt-exact", action="store_true", help="do not add wildcard entries for each \033[33m--crt-ns\033[0m")
    ap2.add_argument("--crt-noip", action="store_true", help="do not add autodetected IP addresses into cert")
    ap2.add_argument("--crt-nolo", action="store_true", help="do not add 127.0.0.1 / localhost into cert")
    ap2.add_argument("--crt-nohn", action="store_true", help="do not add mDNS names / hostname into cert")
    ap2.add_argument("--crt-dir", metavar="PATH", default=cert_dir, help="where to save the CA cert")
    ap2.add_argument("--crt-cdays", metavar="D", type=float, default=3650, help="ca-certificate expiration time in days")
    ap2.add_argument("--crt-sdays", metavar="D", type=float, default=365, help="server-cert expiration time in days")
    ap2.add_argument("--crt-cn", metavar="TXT", type=u, default="partyco", help="CA/server-cert common-name")
    ap2.add_argument("--crt-cnc", metavar="TXT", type=u, default="--crt-cn", help="override CA name")
    ap2.add_argument("--crt-cns", metavar="TXT", type=u, default="--crt-cn cpp", help="override server-cert name")
    ap2.add_argument("--crt-back", metavar="HRS", type=float, default=72, help="backdate in hours")
    ap2.add_argument("--crt-alg", metavar="S-N", type=u, default="ecdsa-256", help="algorithm and keysize; one of these: \033[32mecdsa-256 rsa-4096 rsa-2048\033[0m")


def add_auth(ap):
    ap2 = ap.add_argument_group('IdP / identity provider / user authentication options')
    ap2.add_argument("--idp-h-usr", metavar="HN", type=u, default="", help="bypass the copyparty authentication checks and assume the request-header \033[33mHN\033[0m contains the username of the requesting user (for use with authentik/oauth/...)\n\033[1;31mWARNING:\033[0m if you enable this, make sure clients are unable to specify this header themselves; must be washed away and replaced by a reverse-proxy")
    ap2.add_argument("--idp-h-grp", metavar="HN", type=u, default="", help="assume the request-header \033[33mHN\033[0m contains the groupname of the requesting user; can be referenced in config files for group-based access control")
    ap2.add_argument("--idp-h-sep", metavar="RE", type=u, default="|:;+,", help="if there are multiple groups in \033[33m--idp-h-grp\033[0m, they are separated by one of the characters in \033[33mRE\033[0m")


def add_zeroconf(ap):
    ap2 = ap.add_argument_group("Zeroconf options")
    ap2.add_argument("-z", action="store_true", help="enable all zeroconf backends (mdns, ssdp)")
    ap2.add_argument("--z-on", metavar="NETS", type=u, default="", help="enable zeroconf ONLY on the comma-separated list of subnets and/or interface names/indexes\n └─example: \033[32meth0, wlo1, virhost0, 192.168.123.0/24, fd00:fda::/96\033[0m")
    ap2.add_argument("--z-off", metavar="NETS", type=u, default="", help="disable zeroconf on the comma-separated list of subnets and/or interface names/indexes")
    ap2.add_argument("--z-chk", metavar="SEC", type=int, default=10, help="check for network changes every \033[33mSEC\033[0m seconds (0=disable)")
    ap2.add_argument("-zv", action="store_true", help="verbose all zeroconf backends")
    ap2.add_argument("--mc-hop", metavar="SEC", type=int, default=0, help="rejoin multicast groups every \033[33mSEC\033[0m seconds (workaround for some switches/routers which cause mDNS to suddenly stop working after some time); try [\033[32m300\033[0m] or [\033[32m180\033[0m]\n └─note: can be due to firewalls; make sure UDP port 5353 is open in both directions (on clients too)")


def add_zc_mdns(ap):
    ap2 = ap.add_argument_group("Zeroconf-mDNS options; also see --help-zm")
    ap2.add_argument("--zm", action="store_true", help="announce the enabled protocols over mDNS (multicast DNS-SD) -- compatible with KDE, gnome, macOS, ...")
    ap2.add_argument("--zm-on", metavar="NETS", type=u, default="", help="enable mDNS ONLY on the comma-separated list of subnets and/or interface names/indexes")
    ap2.add_argument("--zm-off", metavar="NETS", type=u, default="", help="disable mDNS on the comma-separated list of subnets and/or interface names/indexes")
    ap2.add_argument("--zm4", action="store_true", help="IPv4 only -- try this if some clients can't connect")
    ap2.add_argument("--zm6", action="store_true", help="IPv6 only")
    ap2.add_argument("--zmv", action="store_true", help="verbose mdns")
    ap2.add_argument("--zmvv", action="store_true", help="verboser mdns")
    ap2.add_argument("--zms", metavar="dhf", type=u, default="", help="list of services to announce -- d=webdav h=http f=ftp s=smb -- lowercase=plaintext uppercase=TLS -- default: all enabled services except http/https (\033[32mDdfs\033[0m if \033[33m--ftp\033[0m and \033[33m--smb\033[0m is set, \033[32mDd\033[0m otherwise)")
    ap2.add_argument("--zm-ld", metavar="PATH", type=u, default="", help="link a specific folder for webdav shares")
    ap2.add_argument("--zm-lh", metavar="PATH", type=u, default="", help="link a specific folder for http shares")
    ap2.add_argument("--zm-lf", metavar="PATH", type=u, default="", help="link a specific folder for ftp shares")
    ap2.add_argument("--zm-ls", metavar="PATH", type=u, default="", help="link a specific folder for smb shares")
    ap2.add_argument("--zm-mnic", action="store_true", help="merge NICs which share subnets; assume that same subnet means same network")
    ap2.add_argument("--zm-msub", action="store_true", help="merge subnets on each NIC -- always enabled for ipv6 -- reduces network load, but gnome-gvfs clients may stop working, and clients cannot be in subnets that the server is not")
    ap2.add_argument("--zm-noneg", action="store_true", help="disable NSEC replies -- try this if some clients don't see copyparty")
    ap2.add_argument("--zm-spam", metavar="SEC", type=float, default=0, help="send unsolicited announce every \033[33mSEC\033[0m; useful if clients have IPs in a subnet which doesn't overlap with the server, or to avoid some firewall issues")


def add_zc_ssdp(ap):
    ap2 = ap.add_argument_group("Zeroconf-SSDP options")
    ap2.add_argument("--zs", action="store_true", help="announce the enabled protocols over SSDP -- compatible with Windows")
    ap2.add_argument("--zs-on", metavar="NETS", type=u, default="", help="enable SSDP ONLY on the comma-separated list of subnets and/or interface names/indexes")
    ap2.add_argument("--zs-off", metavar="NETS", type=u, default="", help="disable SSDP on the comma-separated list of subnets and/or interface names/indexes")
    ap2.add_argument("--zsv", action="store_true", help="verbose SSDP")
    ap2.add_argument("--zsl", metavar="PATH", type=u, default="/?hc", help="location to include in the url (or a complete external URL), for example [\033[32mpriv/?pw=hunter2\033[0m] (goes directly to /priv/ with password hunter2) or [\033[32m?hc=priv&pw=hunter2\033[0m] (shows mounting options for /priv/ with password)")
    ap2.add_argument("--zsid", metavar="UUID", type=u, default=zsid, help="USN (device identifier) to announce")


def add_ftp(ap):
    ap2 = ap.add_argument_group('FTP options')
    ap2.add_argument("--ftp", metavar="PORT", type=int, help="enable FTP server on \033[33mPORT\033[0m, for example \033[32m3921")
    ap2.add_argument("--ftps", metavar="PORT", type=int, help="enable FTPS server on \033[33mPORT\033[0m, for example \033[32m3990")
    ap2.add_argument("--ftpv", action="store_true", help="verbose")
    ap2.add_argument("--ftp4", action="store_true", help="only listen on IPv4")
    ap2.add_argument("--ftp-ipa", metavar="PFX", type=u, default="", help="only accept connections from IP-addresses starting with \033[33mPFX\033[0m; specify [\033[32many\033[0m] to disable inheriting \033[33m--ipa\033[0m. Example: [\033[32m127., 10.89., 192.168.\033[0m]")
    ap2.add_argument("--ftp-wt", metavar="SEC", type=int, default=7, help="grace period for resuming interrupted uploads (any client can write to any file last-modified more recently than \033[33mSEC\033[0m seconds ago)")
    ap2.add_argument("--ftp-nat", metavar="ADDR", type=u, help="the NAT address to use for passive connections")
    ap2.add_argument("--ftp-pr", metavar="P-P", type=u, help="the range of TCP ports to use for passive connections, for example \033[32m12000-13000")


def add_webdav(ap):
    ap2 = ap.add_argument_group('WebDAV options')
    ap2.add_argument("--daw", action="store_true", help="enable full write support, even if client may not be webdav. \033[1;31mWARNING:\033[0m This has side-effects -- PUT-operations will now \033[1;31mOVERWRITE\033[0m existing files, rather than inventing new filenames to avoid loss of data. You might want to instead set this as a volflag where needed. By not setting this flag, uploaded files can get written to a filename which the client does not expect (which might be okay, depending on client)")
    ap2.add_argument("--dav-inf", action="store_true", help="allow depth:infinite requests (recursive file listing); extremely server-heavy but required for spec compliance -- luckily few clients rely on this")
    ap2.add_argument("--dav-mac", action="store_true", help="disable apple-garbage filter -- allow macos to create junk files (._* and .DS_Store, .Spotlight-*, .fseventsd, .Trashes, .AppleDouble, __MACOS)")
    ap2.add_argument("--dav-rt", action="store_true", help="show symlink-destination's lastmodified instead of the link itself; always enabled for recursive listings (volflag=davrt)")
    ap2.add_argument("--dav-auth", action="store_true", help="force auth for all folders (required by davfs2 when only some folders are world-readable) (volflag=davauth)")


def add_smb(ap):
    ap2 = ap.add_argument_group('SMB/CIFS options')
    ap2.add_argument("--smb", action="store_true", help="enable smb (read-only) -- this requires running copyparty as root on linux and macos unless \033[33m--smb-port\033[0m is set above 1024 and your OS does port-forwarding from 445 to that.\n\033[1;31mWARNING:\033[0m this protocol is DANGEROUS and buggy! Never expose to the internet!")
    ap2.add_argument("--smbw", action="store_true", help="enable write support (please dont)")
    ap2.add_argument("--smb1", action="store_true", help="disable SMBv2, only enable SMBv1 (CIFS)")
    ap2.add_argument("--smb-port", metavar="PORT", type=int, default=445, help="port to listen on -- if you change this value, you must NAT from TCP:445 to this port using iptables or similar")
    ap2.add_argument("--smb-nwa-1", action="store_true", help="disable impacket#1433 workaround (truncate directory listings to 64kB)")
    ap2.add_argument("--smb-nwa-2", action="store_true", help="disable impacket workaround for filecopy globs")
    ap2.add_argument("--smba", action="store_true", help="small performance boost: disable per-account permissions, enables account coalescing instead (if one user has write/delete-access, then everyone does)")
    ap2.add_argument("--smbv", action="store_true", help="verbose")
    ap2.add_argument("--smbvv", action="store_true", help="verboser")
    ap2.add_argument("--smbvvv", action="store_true", help="verbosest")


def add_handlers(ap):
    ap2 = ap.add_argument_group('handlers (see --help-handlers)')
    ap2.add_argument("--on404", metavar="PY", type=u, action="append", help="handle 404s by executing \033[33mPY\033[0m file")
    ap2.add_argument("--on403", metavar="PY", type=u, action="append", help="handle 403s by executing \033[33mPY\033[0m file")
    ap2.add_argument("--hot-handlers", action="store_true", help="recompile handlers on each request -- expensive but convenient when hacking on stuff")


def add_hooks(ap):
    ap2 = ap.add_argument_group('event hooks (see --help-hooks)')
    ap2.add_argument("--xbu", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m before a file upload starts")
    ap2.add_argument("--xau", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m after  a file upload finishes")
    ap2.add_argument("--xiu", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m after  all uploads finish and volume is idle")
    ap2.add_argument("--xbr", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m before a file move/rename")
    ap2.add_argument("--xar", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m after  a file move/rename")
    ap2.add_argument("--xbd", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m before a file delete")
    ap2.add_argument("--xad", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m after  a file delete")
    ap2.add_argument("--xm", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m on message")
    ap2.add_argument("--xban", metavar="CMD", type=u, action="append", help="execute \033[33mCMD\033[0m if someone gets banned (pw/404/403/url)")


def add_stats(ap):
    ap2 = ap.add_argument_group('grafana/prometheus metrics endpoint')
    ap2.add_argument("--stats", action="store_true", help="enable openmetrics at /.cpr/metrics for admin accounts")
    ap2.add_argument("--nos-hdd", action="store_true", help="disable disk-space metrics (used/free space)")
    ap2.add_argument("--nos-vol", action="store_true", help="disable volume size metrics (num files, total bytes, vmaxb/vmaxn)")
    ap2.add_argument("--nos-vst", action="store_true", help="disable volume state metrics (indexing, analyzing, activity)")
    ap2.add_argument("--nos-dup", action="store_true", help="disable dupe-files metrics (good idea; very slow)")
    ap2.add_argument("--nos-unf", action="store_true", help="disable unfinished-uploads metrics")


def add_yolo(ap):
    ap2 = ap.add_argument_group('yolo options')
    ap2.add_argument("--allow-csrf", action="store_true", help="disable csrf protections; let other domains/sites impersonate you through cross-site requests")
    ap2.add_argument("--getmod", action="store_true", help="permit ?move=[...] and ?delete as GET")


def add_optouts(ap):
    ap2 = ap.add_argument_group('opt-outs')
    ap2.add_argument("-nw", action="store_true", help="never write anything to disk (debug/benchmark)")
    ap2.add_argument("--keep-qem", action="store_true", help="do not disable quick-edit-mode on windows (it is disabled to avoid accidental text selection in the terminal window, as this would pause execution)")
    ap2.add_argument("--no-dav", action="store_true", help="disable webdav support")
    ap2.add_argument("--no-del", action="store_true", help="disable delete operations")
    ap2.add_argument("--no-mv", action="store_true", help="disable move/rename operations")
    ap2.add_argument("-nth", action="store_true", help="no title hostname; don't show \033[33m--name\033[0m in <title>")
    ap2.add_argument("-nih", action="store_true", help="no info hostname -- don't show in UI")
    ap2.add_argument("-nid", action="store_true", help="no info disk-usage -- don't show in UI")
    ap2.add_argument("-nb", action="store_true", help="no powered-by-copyparty branding in UI")
    ap2.add_argument("--no-zip", action="store_true", help="disable download as zip/tar")
    ap2.add_argument("--no-tarcmp", action="store_true", help="disable download as compressed tar (?tar=gz, ?tar=bz2, ?tar=xz, ?tar=gz:9, ...)")
    ap2.add_argument("--no-lifetime", action="store_true", help="do not allow clients (or server config) to schedule an upload to be deleted after a given time")


def add_safety(ap):
    ap2 = ap.add_argument_group('safety options')
    ap2.add_argument("-s", action="count", default=0, help="increase safety: Disable thumbnails / potentially dangerous software (ffmpeg/pillow/vips), hide partial uploads, avoid crawlers.\n └─Alias of\033[32m --dotpart --no-thumb --no-mtag-ff --no-robots --force-js")
    ap2.add_argument("-ss", action="store_true", help="further increase safety: Prevent js-injection, accidental move/delete, broken symlinks, webdav, 404 on 403, ban on excessive 404s.\n └─Alias of\033[32m -s --unpost=0 --no-del --no-mv --hardlink --vague-403 -nih")
    ap2.add_argument("-sss", action="store_true", help="further increase safety: Enable logging to disk, scan for dangerous symlinks.\n └─Alias of\033[32m -ss --no-dav --no-logues --no-readme -lo=cpp-%%Y-%%m%%d-%%H%%M%%S.txt.xz --ls=**,*,ln,p,r")
    ap2.add_argument("--ls", metavar="U[,V[,F]]", type=u, help="do a sanity/safety check of all volumes on startup; arguments \033[33mUSER\033[0m,\033[33mVOL\033[0m,\033[33mFLAGS\033[0m (see \033[33m--help-ls\033[0m); example [\033[32m**,*,ln,p,r\033[0m]")
    ap2.add_argument("--xvol", action="store_true", help="never follow symlinks leaving the volume root, unless the link is into another volume where the user has similar access (volflag=xvol)")
    ap2.add_argument("--xdev", action="store_true", help="stay within the filesystem of the volume root; do not descend into other devices (symlink or bind-mount to another HDD, ...) (volflag=xdev)")
    ap2.add_argument("--no-dot-mv", action="store_true", help="disallow moving dotfiles; makes it impossible to move folders containing dotfiles")
    ap2.add_argument("--no-dot-ren", action="store_true", help="disallow renaming dotfiles; makes it impossible to turn something into a dotfile")
    ap2.add_argument("--no-logues", action="store_true", help="disable rendering .prologue/.epilogue.html into directory listings")
    ap2.add_argument("--no-readme", action="store_true", help="disable rendering readme.md into directory listings")
    ap2.add_argument("--vague-403", action="store_true", help="send 404 instead of 403 (security through ambiguity, very enterprise)")
    ap2.add_argument("--force-js", action="store_true", help="don't send folder listings as HTML, force clients to use the embedded json instead -- slight protection against misbehaving search engines which ignore \033[33m--no-robots\033[0m")
    ap2.add_argument("--no-robots", action="store_true", help="adds http and html headers asking search engines to not index anything (volflag=norobots)")
    ap2.add_argument("--logout", metavar="H", type=float, default="8086", help="logout clients after \033[33mH\033[0m hours of inactivity; [\033[32m0.0028\033[0m]=10sec, [\033[32m0.1\033[0m]=6min, [\033[32m24\033[0m]=day, [\033[32m168\033[0m]=week, [\033[32m720\033[0m]=month, [\033[32m8760\033[0m]=year)")
    ap2.add_argument("--ban-pw", metavar="N,W,B", type=u, default="9,60,1440", help="more than \033[33mN\033[0m wrong passwords in \033[33mW\033[0m minutes = ban for \033[33mB\033[0m minutes; disable with [\033[32mno\033[0m]")
    ap2.add_argument("--ban-404", metavar="N,W,B", type=u, default="50,60,1440", help="hitting more than \033[33mN\033[0m 404's in \033[33mW\033[0m minutes = ban for \033[33mB\033[0m minutes; only affects users who cannot see directory listings because their access is either g/G/h")
    ap2.add_argument("--ban-403", metavar="N,W,B", type=u, default="9,2,1440", help="hitting more than \033[33mN\033[0m 403's in \033[33mW\033[0m minutes = ban for \033[33mB\033[0m minutes; [\033[32m1440\033[0m]=day, [\033[32m10080\033[0m]=week, [\033[32m43200\033[0m]=month")
    ap2.add_argument("--ban-422", metavar="N,W,B", type=u, default="9,2,1440", help="hitting more than \033[33mN\033[0m 422's in \033[33mW\033[0m minutes = ban for \033[33mB\033[0m minutes (invalid requests, attempted exploits ++)")
    ap2.add_argument("--ban-url", metavar="N,W,B", type=u, default="9,2,1440", help="hitting more than \033[33mN\033[0m sus URL's in \033[33mW\033[0m minutes = ban for \033[33mB\033[0m minutes; applies only to permissions g/G/h (decent replacement for \033[33m--ban-404\033[0m if that can't be used)")
    ap2.add_argument("--sus-urls", metavar="R", type=u, default=r"\.php$|(^|/)wp-(admin|content|includes)/", help="URLs which are considered sus / eligible for banning; disable with blank or [\033[32mno\033[0m]")
    ap2.add_argument("--nonsus-urls", metavar="R", type=u, default=r"^(favicon\.ico|robots\.txt)$|^apple-touch-icon|^\.well-known", help="harmless URLs ignored from 404-bans; disable with blank or [\033[32mno\033[0m]")
    ap2.add_argument("--aclose", metavar="MIN", type=int, default=10, help="if a client maxes out the server connection limit, downgrade it from connection:keep-alive to connection:close for \033[33mMIN\033[0m minutes (and also kill its active connections) -- disable with 0")
    ap2.add_argument("--loris", metavar="B", type=int, default=60, help="if a client maxes out the server connection limit without sending headers, ban it for \033[33mB\033[0m minutes; disable with [\033[32m0\033[0m]")
    ap2.add_argument("--acao", metavar="V[,V]", type=u, default="*", help="Access-Control-Allow-Origin; list of origins (domains/IPs without port) to accept requests from; [\033[32mhttps://1.2.3.4\033[0m]. Default [\033[32m*\033[0m] allows requests from all sites but removes cookies and http-auth; only ?pw=hunter2 survives")
    ap2.add_argument("--acam", metavar="V[,V]", type=u, default="GET,HEAD", help="Access-Control-Allow-Methods; list of methods to accept from offsite ('*' behaves like \033[33m--acao\033[0m's description)")


def add_salt(ap, fk_salt, ah_salt):
    ap2 = ap.add_argument_group('salting options')
    ap2.add_argument("--ah-alg", metavar="ALG", type=u, default="none", help="account-pw hashing algorithm; one of these, best to worst: \033[32margon2 scrypt sha2 none\033[0m (each optionally followed by alg-specific comma-sep. config)")
    ap2.add_argument("--ah-salt", metavar="SALT", type=u, default=ah_salt, help="account-pw salt; ignored if \033[33m--ah-alg\033[0m is none (default)")
    ap2.add_argument("--ah-gen", metavar="PW", type=u, default="", help="generate hashed password for \033[33mPW\033[0m, or read passwords from STDIN if \033[33mPW\033[0m is [\033[32m-\033[0m]")
    ap2.add_argument("--ah-cli", action="store_true", help="launch an interactive shell which hashes passwords without ever storing or displaying the original passwords")
    ap2.add_argument("--fk-salt", metavar="SALT", type=u, default=fk_salt, help="per-file accesskey salt; used to generate unpredictable URLs for hidden files")
    ap2.add_argument("--warksalt", metavar="SALT", type=u, default="hunter2", help="up2k file-hash salt; serves no purpose, no reason to change this (but delete all databases if you do)")


def add_shutdown(ap):
    ap2 = ap.add_argument_group('shutdown options')
    ap2.add_argument("--ign-ebind", action="store_true", help="continue running even if it's impossible to listen on some of the requested endpoints")
    ap2.add_argument("--ign-ebind-all", action="store_true", help="continue running even if it's impossible to receive connections at all")
    ap2.add_argument("--exit", metavar="WHEN", type=u, default="", help="shutdown after \033[33mWHEN\033[0m has finished; [\033[32mcfg\033[0m] config parsing, [\033[32midx\033[0m] volscan + multimedia indexing")


def add_logging(ap):
    ap2 = ap.add_argument_group('logging options')
    ap2.add_argument("-q", action="store_true", help="quiet; disable most STDOUT messages")
    ap2.add_argument("-lo", metavar="PATH", type=u, help="logfile, example: \033[32mcpp-%%Y-%%m%%d-%%H%%M%%S.txt.xz\033[0m (NB: some errors may appear on STDOUT only)")
    ap2.add_argument("--no-ansi", action="store_true", default=not VT100, help="disable colors; same as environment-variable NO_COLOR")
    ap2.add_argument("--ansi", action="store_true", help="force colors; overrides environment-variable NO_COLOR")
    ap2.add_argument("--no-logflush", action="store_true", help="don't flush the logfile after each write; tiny bit faster")
    ap2.add_argument("--no-voldump", action="store_true", help="do not list volumes and permissions on startup")
    ap2.add_argument("--log-tdec", metavar="N", type=int, default=3, help="timestamp resolution / number of timestamp decimals")
    ap2.add_argument("--log-badpwd", metavar="N", type=int, default=1, help="log failed login attempt passwords: 0=terse, 1=plaintext, 2=hashed")
    ap2.add_argument("--log-conn", action="store_true", help="debug: print tcp-server msgs")
    ap2.add_argument("--log-htp", action="store_true", help="debug: print http-server threadpool scaling")
    ap2.add_argument("--ihead", metavar="HEADER", type=u, action='append', help="print request \033[33mHEADER\033[0m; [\033[32m*\033[0m]=all")
    ap2.add_argument("--lf-url", metavar="RE", type=u, default=r"^/\.cpr/|\?th=[wj]$|/\.(_|ql_|DS_Store$|localized$)", help="dont log URLs matching regex \033[33mRE\033[0m")


def add_admin(ap):
    ap2 = ap.add_argument_group('admin panel options')
    ap2.add_argument("--no-reload", action="store_true", help="disable ?reload=cfg (reload users/volumes/volflags from config file)")
    ap2.add_argument("--no-rescan", action="store_true", help="disable ?scan (volume reindexing)")
    ap2.add_argument("--no-stack", action="store_true", help="disable ?stack (list all stacks)")


def add_thumbnail(ap):
    ap2 = ap.add_argument_group('thumbnail options')
    ap2.add_argument("--no-thumb", action="store_true", help="disable all thumbnails (volflag=dthumb)")
    ap2.add_argument("--no-vthumb", action="store_true", help="disable video thumbnails (volflag=dvthumb)")
    ap2.add_argument("--no-athumb", action="store_true", help="disable audio thumbnails (spectrograms) (volflag=dathumb)")
    ap2.add_argument("--th-size", metavar="WxH", default="320x256", help="thumbnail res (volflag=thsize)")
    ap2.add_argument("--th-mt", metavar="CORES", type=int, default=CORES, help="num cpu cores to use for generating thumbnails")
    ap2.add_argument("--th-convt", metavar="SEC", type=float, default=60, help="conversion timeout in seconds (volflag=convt)")
    ap2.add_argument("--th-ram-max", metavar="GB", type=float, default=6, help="max memory usage (GiB) permitted by thumbnailer; not very accurate")
    ap2.add_argument("--th-no-crop", action="store_true", help="dynamic height; show full image by default (client can override in UI) (volflag=nocrop)")
    ap2.add_argument("--th-dec", metavar="LIBS", default="vips,pil,ff", help="image decoders, in order of preference")
    ap2.add_argument("--th-no-jpg", action="store_true", help="disable jpg output")
    ap2.add_argument("--th-no-webp", action="store_true", help="disable webp output")
    ap2.add_argument("--th-ff-jpg", action="store_true", help="force jpg output for video thumbs (avoids issues on some FFmpeg builds)")
    ap2.add_argument("--th-ff-swr", action="store_true", help="use swresample instead of soxr for audio thumbs (faster, lower accuracy, avoids issues on some FFmpeg builds)")
    ap2.add_argument("--th-poke", metavar="SEC", type=int, default=300, help="activity labeling cooldown -- avoids doing keepalive pokes (updating the mtime) on thumbnail folders more often than \033[33mSEC\033[0m seconds")
    ap2.add_argument("--th-clean", metavar="SEC", type=int, default=43200, help="cleanup interval; 0=disabled")
    ap2.add_argument("--th-maxage", metavar="SEC", type=int, default=604800, help="max folder age -- folders which haven't been poked for longer than \033[33m--th-poke\033[0m seconds will get deleted every \033[33m--th-clean\033[0m seconds")
    ap2.add_argument("--th-covers", metavar="N,N", type=u, default="folder.png,folder.jpg,cover.png,cover.jpg", help="folder thumbnails to stat/look for; enabling \033[33m-e2d\033[0m will make these case-insensitive, and try them as dotfiles (.folder.jpg), and also automatically select thumbnails for all folders that contain pics, even if none match this pattern")
    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
    # https://github.com/libvips/libvips
    # ffmpeg -hide_banner -demuxers | awk '/^ D  /{print$2}' | while IFS= read -r x; do ffmpeg -hide_banner -h demuxer=$x; done | grep -E '^Demuxer |extensions:'
    ap2.add_argument("--th-r-pil", metavar="T,T", type=u, default="avif,avifs,blp,bmp,dcx,dds,dib,emf,eps,fits,flc,fli,fpx,gif,heic,heics,heif,heifs,icns,ico,im,j2p,j2k,jp2,jpeg,jpg,jpx,pbm,pcx,pgm,png,pnm,ppm,psd,qoi,sgi,spi,tga,tif,tiff,webp,wmf,xbm,xpm", help="image formats to decode using pillow")
    ap2.add_argument("--th-r-vips", metavar="T,T", type=u, default="avif,exr,fit,fits,fts,gif,hdr,heic,jp2,jpeg,jpg,jpx,jxl,nii,pfm,pgm,png,ppm,svg,tif,tiff,webp", help="image formats to decode using pyvips")
    ap2.add_argument("--th-r-ffi", metavar="T,T", type=u, default="apng,avif,avifs,bmp,dds,dib,fit,fits,fts,gif,hdr,heic,heics,heif,heifs,icns,ico,jp2,jpeg,jpg,jpx,jxl,pbm,pcx,pfm,pgm,png,pnm,ppm,psd,qoi,sgi,tga,tif,tiff,webp,xbm,xpm", help="image formats to decode using ffmpeg")
    ap2.add_argument("--th-r-ffv", metavar="T,T", type=u, default="3gp,asf,av1,avc,avi,flv,h264,h265,hevc,m4v,mjpeg,mjpg,mkv,mov,mp4,mpeg,mpeg2,mpegts,mpg,mpg2,mts,nut,ogm,ogv,rm,ts,vob,webm,wmv", help="video formats to decode using ffmpeg")
    ap2.add_argument("--th-r-ffa", metavar="T,T", type=u, default="aac,ac3,aif,aiff,alac,alaw,amr,apac,ape,au,bonk,dfpwm,dts,flac,gsm,ilbc,it,m4a,mo3,mod,mp2,mp3,mpc,mptm,mt2,mulaw,ogg,okt,opus,ra,s3m,tak,tta,ulaw,wav,wma,wv,xm,xpk", help="audio formats to decode using ffmpeg")


def add_transcoding(ap):
    ap2 = ap.add_argument_group('transcoding options')
    ap2.add_argument("--no-acode", action="store_true", help="disable audio transcoding")
    ap2.add_argument("--no-bacode", action="store_true", help="disable batch audio transcoding by folder download (zip/tar)")
    ap2.add_argument("--ac-maxage", metavar="SEC", type=int, default=86400, help="delete cached transcode output after \033[33mSEC\033[0m seconds")


def add_db_general(ap, hcores):
    noidx = APPLESAN_TXT if MACOS else ""
    ap2 = ap.add_argument_group('general db options')
    ap2.add_argument("-e2d", action="store_true", help="enable up2k database, making files searchable + enables upload deduplication")
    ap2.add_argument("-e2ds", action="store_true", help="scan writable folders for new files on startup; sets \033[33m-e2d\033[0m")
    ap2.add_argument("-e2dsa", action="store_true", help="scans all folders on startup; sets \033[33m-e2ds\033[0m")
    ap2.add_argument("-e2v", action="store_true", help="verify file integrity; rehash all files and compare with db")
    ap2.add_argument("-e2vu", action="store_true", help="on hash mismatch: update the database with the new hash")
    ap2.add_argument("-e2vp", action="store_true", help="on hash mismatch: panic and quit copyparty")
    ap2.add_argument("--hist", metavar="PATH", type=u, help="where to store volume data (db, thumbs) (volflag=hist)")
    ap2.add_argument("--no-hash", metavar="PTN", type=u, help="regex: disable hashing of matching absolute-filesystem-paths during e2ds folder scans (volflag=nohash)")
    ap2.add_argument("--no-idx", metavar="PTN", type=u, default=noidx, help="regex: disable indexing of matching absolute-filesystem-paths during e2ds folder scans (volflag=noidx)")
    ap2.add_argument("--no-dhash", action="store_true", help="disable rescan acceleration; do full database integrity check -- makes the db ~5%% smaller and bootup/rescans 3~10x slower")
    ap2.add_argument("--re-dhash", action="store_true", help="rebuild the cache if it gets out of sync (for example crash on startup during metadata scanning)")
    ap2.add_argument("--no-forget", action="store_true", help="never forget indexed files, even when deleted from disk -- makes it impossible to ever upload the same file twice -- only useful for offloading uploads to a cloud service or something (volflag=noforget)")
    ap2.add_argument("--dbd", metavar="PROFILE", default="wal", help="database durability profile; sets the tradeoff between robustness and speed, see \033[33m--help-dbd\033[0m (volflag=dbd)")
    ap2.add_argument("--xlink", action="store_true", help="on upload: check all volumes for dupes, not just the target volume (volflag=xlink)")
    ap2.add_argument("--hash-mt", metavar="CORES", type=int, default=hcores, help="num cpu cores to use for file hashing; set 0 or 1 for single-core hashing")
    ap2.add_argument("--re-maxage", metavar="SEC", type=int, default=0, help="rescan filesystem for changes every \033[33mSEC\033[0m seconds; 0=off (volflag=scan)")
    ap2.add_argument("--db-act", metavar="SEC", type=float, default=10, help="defer any scheduled volume reindexing until \033[33mSEC\033[0m seconds after last db write (uploads, renames, ...)")
    ap2.add_argument("--srch-time", metavar="SEC", type=int, default=45, help="search deadline -- terminate searches running for more than \033[33mSEC\033[0m seconds")
    ap2.add_argument("--srch-hits", metavar="N", type=int, default=7999, help="max search results to allow clients to fetch; 125 results will be shown initially")
    ap2.add_argument("--dotsrch", action="store_true", help="show dotfiles in search results (volflags: dotsrch | nodotsrch)")


def add_db_metadata(ap):
    ap2 = ap.add_argument_group('metadata db options')
    ap2.add_argument("-e2t", action="store_true", help="enable metadata indexing; makes it possible to search for artist/title/codec/resolution/...")
    ap2.add_argument("-e2ts", action="store_true", help="scan newly discovered files for metadata on startup; sets \033[33m-e2t\033[0m")
    ap2.add_argument("-e2tsr", action="store_true", help="delete all metadata from DB and do a full rescan; sets \033[33m-e2ts\033[0m")
    ap2.add_argument("--no-mutagen", action="store_true", help="use FFprobe for tags instead; will detect more tags")
    ap2.add_argument("--no-mtag-ff", action="store_true", help="never use FFprobe as tag reader; is probably safer")
    ap2.add_argument("--mtag-to", metavar="SEC", type=int, default=60, help="timeout for FFprobe tag-scan")
    ap2.add_argument("--mtag-mt", metavar="CORES", type=int, default=CORES, help="num cpu cores to use for tag scanning")
    ap2.add_argument("--mtag-v", action="store_true", help="verbose tag scanning; print errors from mtp subprocesses and such")
    ap2.add_argument("--mtag-vv", action="store_true", help="debug mtp settings and mutagen/FFprobe parsers")
    ap2.add_argument("-mtm", metavar="M=t,t,t", type=u, action="append", help="add/replace metadata mapping")
    ap2.add_argument("-mte", metavar="M,M,M", type=u, help="tags to index/display (comma-sep.); either an entire replacement list, or add/remove stuff on the default-list with +foo or /bar", default=DEF_MTE)
    ap2.add_argument("-mth", metavar="M,M,M", type=u, help="tags to hide by default (comma-sep.); assign/add/remove same as \033[33m-mte\033[0m", default=DEF_MTH)
    ap2.add_argument("-mtp", metavar="M=[f,]BIN", type=u, action="append", help="read tag \033[33mM\033[0m using program \033[33mBIN\033[0m to parse the file")


def add_txt(ap):
    ap2 = ap.add_argument_group('textfile options')
    ap2.add_argument("-mcr", metavar="SEC", type=int, default=60, help="the textfile editor will check for serverside changes every \033[33mSEC\033[0m seconds")
    ap2.add_argument("-emp", action="store_true", help="enable markdown plugins -- neat but dangerous, big XSS risk")
    ap2.add_argument("--exp", action="store_true", help="enable textfile expansion -- replace {{self.ip}} and such; see \033[33m--help-exp\033[0m (volflag=exp)")
    ap2.add_argument("--exp-md", metavar="V,V,V", type=u, default=DEF_EXP, help="comma/space-separated list of placeholders to expand in markdown files; add/remove stuff on the default list with +hdr_foo or /vf.scan (volflag=exp_md)")
    ap2.add_argument("--exp-lg", metavar="V,V,V", type=u, default=DEF_EXP, help="comma/space-separated list of placeholders to expand in prologue/epilogue files (volflag=exp_lg)")


def add_ui(ap, retry):
    ap2 = ap.add_argument_group('ui options')
    ap2.add_argument("--grid", action="store_true", help="show grid/thumbnails by default (volflag=grid)")
    ap2.add_argument("--lang", metavar="LANG", type=u, default="eng", help="language; one of the following: \033[32meng nor\033[0m")
    ap2.add_argument("--theme", metavar="NUM", type=int, default=0, help="default theme to use (0..7)")
    ap2.add_argument("--themes", metavar="NUM", type=int, default=8, help="number of themes installed")
    ap2.add_argument("--sort", metavar="C,C,C", type=u, default="href", help="default sort order, comma-separated column IDs (see header tooltips), prefix with '-' for descending. Examples: \033[32mhref -href ext sz ts tags/Album tags/.tn\033[0m (volflag=sort)")
    ap2.add_argument("--unlist", metavar="REGEX", type=u, default="", help="don't show files matching \033[33mREGEX\033[0m in file list. Purely cosmetic! Does not affect API calls, just the browser. Example: [\033[32m\\.(js|css)$\033[0m] (volflag=unlist)")
    ap2.add_argument("--favico", metavar="TXT", type=u, default="c 000 none" if retry else "🎉 000 none", help="\033[33mfavicon-text\033[0m [ \033[33mforeground\033[0m [ \033[33mbackground\033[0m ] ], set blank to disable")
    ap2.add_argument("--mpmc", metavar="URL", type=u, default="", help="change the mediaplayer-toggle mouse cursor; URL to a folder with {2..5}.png inside (or disable with [\033[32m.\033[0m])")
    ap2.add_argument("--js-browser", metavar="L", type=u, help="URL to additional JS to include")
    ap2.add_argument("--css-browser", metavar="L", type=u, help="URL to additional CSS to include")
    ap2.add_argument("--html-head", metavar="TXT", type=u, default="", help="text to append to the <head> of all HTML pages")
    ap2.add_argument("--ih", action="store_true", help="if a folder contains index.html, show that instead of the directory listing by default (can be changed in the client settings UI, or add ?v to URL for override)")
    ap2.add_argument("--textfiles", metavar="CSV", type=u, default="txt,nfo,diz,cue,readme", help="file extensions to present as plaintext")
    ap2.add_argument("--txt-max", metavar="KiB", type=int, default=64, help="max size of embedded textfiles on ?doc= (anything bigger will be lazy-loaded by JS)")
    ap2.add_argument("--doctitle", metavar="TXT", type=u, default="copyparty @ --name", help="title / service-name to show in html documents")
    ap2.add_argument("--bname", metavar="TXT", type=u, default="--name", help="server name (displayed in filebrowser document title)")
    ap2.add_argument("--pb-url", metavar="URL", type=u, default="https://github.com/9001/copyparty", help="powered-by link; disable with \033[33m-np\033[0m")
    ap2.add_argument("--ver", action="store_true", help="show version on the control panel (incompatible with \033[33m-nb\033[0m)")
    ap2.add_argument("--md-sbf", metavar="FLAGS", type=u, default="downloads forms popups scripts top-navigation-by-user-activation", help="list of capabilities to ALLOW for README.md docs (volflag=md_sbf); see https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe#attr-sandbox")
    ap2.add_argument("--lg-sbf", metavar="FLAGS", type=u, default="downloads forms popups scripts top-navigation-by-user-activation", help="list of capabilities to ALLOW for prologue/epilogue docs  (volflag=lg_sbf)")
    ap2.add_argument("--no-sb-md", action="store_true", help="don't sandbox README.md documents (volflags: no_sb_md | sb_md)")
    ap2.add_argument("--no-sb-lg", action="store_true", help="don't sandbox prologue/epilogue docs (volflags: no_sb_lg | sb_lg); enables non-js support")


def add_debug(ap):
    ap2 = ap.add_argument_group('debug options')
    ap2.add_argument("--vc", action="store_true", help="verbose config file parser (explain config)")
    ap2.add_argument("--cgen", action="store_true", help="generate config file from current config (best-effort; probably buggy)")
    ap2.add_argument("--no-sendfile", action="store_true", help="kernel-bug workaround: disable sendfile; do a safe and slow read-send-loop instead")
    ap2.add_argument("--no-scandir", action="store_true", help="kernel-bug workaround: disable scandir; do a listdir + stat on each file instead")
    ap2.add_argument("--no-fastboot", action="store_true", help="wait for initial filesystem indexing before accepting client requests")
    ap2.add_argument("--no-htp", action="store_true", help="disable httpserver threadpool, create threads as-needed instead")
    ap2.add_argument("--srch-dbg", action="store_true", help="explain search processing, and do some extra expensive sanity checks")
    ap2.add_argument("--rclone-mdns", action="store_true", help="use mdns-domain instead of server-ip on /?hc")
    ap2.add_argument("--stackmon", metavar="P,S", type=u, help="write stacktrace to \033[33mP\033[0math every \033[33mS\033[0m second, for example --stackmon=\033[32m./st/%%Y-%%m/%%d/%%H%%M.xz,60")
    ap2.add_argument("--log-thrs", metavar="SEC", type=float, help="list active threads every \033[33mSEC\033[0m")
    ap2.add_argument("--log-fk", metavar="REGEX", type=u, default="", help="log filekey params for files where path matches \033[33mREGEX\033[0m; [\033[32m.\033[0m] (a single dot) = all files")
    ap2.add_argument("--bak-flips", action="store_true", help="[up2k] if a client uploads a bitflipped/corrupted chunk, store a copy according to \033[33m--bf-nc\033[0m and \033[33m--bf-dir\033[0m")
    ap2.add_argument("--bf-nc", metavar="NUM", type=int, default=200, help="bak-flips: stop if there's more than \033[33mNUM\033[0m files at \033[33m--kf-dir\033[0m already; default: 6.3 GiB max (200*32M)")
    ap2.add_argument("--bf-dir", metavar="PATH", type=u, default="bf", help="bak-flips: store corrupted chunks at \033[33mPATH\033[0m; default: folder named 'bf' wherever copyparty was started")


# fmt: on


def run_argparse(
    argv: list[str], formatter: Any, retry: bool, nc: int
) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        formatter_class=formatter,
        prog="copyparty",
        description="http file sharing hub v{} ({})".format(S_VERSION, S_BUILD_DT),
    )

    cert_path = os.path.join(E.cfg, "cert.pem")

    fk_salt = get_fk_salt()
    ah_salt = get_ah_salt()

    # alpine peaks at 5 threads for some reason,
    # all others scale past that (but try to avoid SMT),
    # 5 should be plenty anyways (3 GiB/s on most machines)
    hcores = min(CORES, 5 if CORES > 8 else 4)

    tty = os.environ.get("TERM", "").lower() == "linux"

    srvname = get_srvname()

    add_general(ap, nc, srvname)
    add_network(ap)
    add_tls(ap, cert_path)
    add_cert(ap, cert_path)
    add_auth(ap)
    add_qr(ap, tty)
    add_zeroconf(ap)
    add_zc_mdns(ap)
    add_zc_ssdp(ap)
    add_fs(ap)
    add_upload(ap)
    add_db_general(ap, hcores)
    add_db_metadata(ap)
    add_thumbnail(ap)
    add_transcoding(ap)
    add_ftp(ap)
    add_webdav(ap)
    add_smb(ap)
    add_safety(ap)
    add_salt(ap, fk_salt, ah_salt)
    add_optouts(ap)
    add_shutdown(ap)
    add_yolo(ap)
    add_handlers(ap)
    add_hooks(ap)
    add_stats(ap)
    add_txt(ap)
    add_ui(ap, retry)
    add_admin(ap)
    add_logging(ap)
    add_debug(ap)

    ap2 = ap.add_argument_group("help sections")
    sects = get_sects()
    for k, h, _ in sects:
        ap2.add_argument("--help-" + k, action="store_true", help=h)

    try:
        if not retry:
            raise Exception()

        for x in ap._actions:
            if not x.help:
                continue

            a = ["ascii", "replace"]
            x.help = x.help.encode(*a).decode(*a) + "\033[0m"
    except:
        pass

    ret = ap.parse_args(args=argv[1:])
    for k, h, t in sects:
        k2 = "help_" + k.replace("-", "_")
        if vars(ret)[k2]:
            lprint("# %s help page (%s)" % (k, h))
            lprint(t + "\033[0m")
            sys.exit(0)

    return ret


def main(argv: Optional[list[str]] = None) -> None:
    time.strptime("19970815", "%Y%m%d")  # python#7980
    if WINDOWS:
        os.system("rem")  # enables colors

    init_E(E)
    if argv is None:
        argv = sys.argv

    f = '\033[36mcopyparty v{} "\033[35m{}\033[36m" ({})\n{}\033[0;36m\n   sqlite v{} | jinja2 v{} | pyftpd v{}\n\033[0m'
    f = f.format(
        S_VERSION,
        CODENAME,
        S_BUILD_DT,
        PY_DESC.replace("[", "\033[90m["),
        SQLITE_VER,
        JINJA_VER,
        PYFTPD_VER,
    )
    lprint(f)

    if "--version" in argv:
        sys.exit(0)

    if "--license" in argv:
        showlic()
        sys.exit(0)

    if EXE:
        print("pybin: {}\n".format(pybin), end="")

    ensure_locale()

    ensure_webdeps()

    for k, v in zip(argv[1:], argv[2:]):
        if k == "-c" and os.path.isfile(v):
            supp = args_from_cfg(v)
            argv.extend(supp)

    for k in argv[1:]:
        v = k[2:]
        if k.startswith("-c") and v and os.path.isfile(v):
            supp = args_from_cfg(v)
            argv.extend(supp)

    deprecated: list[tuple[str, str]] = [
        ("--salt", "--warksalt"),
        ("--hdr-au-usr", "--idp-h-usr"),
    ]
    for dk, nk in deprecated:
        idx = -1
        ov = ""
        for n, k in enumerate(argv):
            if k == dk or k.startswith(dk + "="):
                idx = n
                if "=" in k:
                    ov = "=" + k.split("=", 1)[1]

        if idx < 0:
            continue

        msg = "\033[1;31mWARNING:\033[0;1m\n  {} \033[0;33mwas replaced with\033[0;1m {} \033[0;33mand will be removed\n\033[0m"
        lprint(msg.format(dk, nk))
        argv[idx] = nk + ov
        time.sleep(2)

    da = len(argv) == 1
    try:
        if da:
            argv.extend(["--qr"])
            if ANYWIN or not os.geteuid():
                # win10 allows symlinks if admin; can be unexpected
                argv.extend(["-p80,443,3923", "--ign-ebind", "--no-dedup"])
    except:
        pass

    if da:
        t = "no arguments provided; will use {}\n"
        lprint(t.format(" ".join(argv[1:])))

    nc = 1024
    try:
        import resource

        _, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if hard > 0:  # -1 == infinite
            nc = min(nc, int(hard / 4))
    except:
        nc = 512

    retry = False
    for fmtr in [RiceFormatter, RiceFormatter, Dodge11874, BasicDodge11874]:
        try:
            al = run_argparse(argv, fmtr, retry, nc)
            dal = run_argparse([], fmtr, retry, nc)
            break
        except SystemExit:
            raise
        except:
            retry = True
            lprint("\n[ {} ]:\n{}\n".format(fmtr, min_ex()))

    try:
        assert al  # type: ignore
        assert dal  # type: ignore
        al.E = E  # __init__ is not shared when oxidized
    except:
        sys.exit(1)

    if al.ansi:
        al.no_ansi = False
    elif not al.no_ansi:
        al.ansi = VT100

    if WINDOWS and not al.keep_qem and not al.ah_cli:
        try:
            disable_quickedit()
        except:
            lprint("\nfailed to disable quick-edit-mode:\n" + min_ex() + "\n")

    if al.ansi:
        al.wintitle = ""

    # propagate implications
    for k1, k2 in IMPLICATIONS:
        if getattr(al, k1):
            setattr(al, k2, True)

    # propagate unplications
    for k1, k2 in UNPLICATIONS:
        if getattr(al, k1):
            setattr(al, k2, False)

    al.i = al.i.split(",")
    try:
        if "-" in al.p:
            lo, hi = [int(x) for x in al.p.split("-")]
            al.p = list(range(lo, hi + 1))
        else:
            al.p = [int(x) for x in al.p.split(",")]
    except:
        raise Exception("invalid value for -p")

    for arg, kname, okays in [["--u2sort", "u2sort", "s n fs fn"]]:
        val = unicode(getattr(al, kname))
        if val not in okays.split():
            zs = "argument {} cannot be '{}'; try one of these: {}"
            raise Exception(zs.format(arg, val, okays))

    if not al.qrs and [k for k in argv if k.startswith("--qr")]:
        al.qr = True

    if al.ihead:
        al.ihead = [x.lower() for x in al.ihead]

    if HAVE_SSL:
        if al.ssl_ver:
            configure_ssl_ver(al)

        if al.ciphers:
            configure_ssl_ciphers(al)
    else:
        warn("ssl module does not exist; cannot enable https")
        al.http_only = True

    if PY2 and WINDOWS and al.e2d:
        warn(
            "windows py2 cannot do unicode filenames with -e2d\n"
            + "  (if you crash with codec errors then that is why)"
        )

    if PY2 and al.smb:
        print("error: python2 cannot --smb")
        return

    if sys.version_info < (3, 6):
        al.no_scandir = True

    if not hasattr(os, "sendfile"):
        al.no_sendfile = True

    # signal.signal(signal.SIGINT, sighandler)

    SvcHub(al, dal, argv, "".join(printed)).run()


if __name__ == "__main__":
    main()

# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import json
import os
import shutil
import subprocess as sp
import sys

from .__init__ import ANYWIN, EXE, PY2, WINDOWS, E, unicode
from .bos import bos
from .util import (
    FFMPEG_URL,
    REKOBO_LKEY,
    fsenc,
    min_ex,
    pybin,
    retchk,
    runcmd,
    sfsenc,
    uncyg,
)

if True:  # pylint: disable=using-constant-test
    from typing import Any, Union

    from .util import RootLogger


def have_ff(scmd: str) -> bool:
    if ANYWIN:
        scmd += ".exe"

    if PY2:
        print("# checking {}".format(scmd))
        acmd = (scmd + " -version").encode("ascii").split(b" ")
        try:
            sp.Popen(acmd, stdout=sp.PIPE, stderr=sp.PIPE).communicate()
            return True
        except:
            return False
    else:
        return bool(shutil.which(scmd))


HAVE_FFMPEG = have_ff("ffmpeg")
HAVE_FFPROBE = have_ff("ffprobe")


class MParser(object):
    def __init__(self, cmdline: str) -> None:
        self.tag, args = cmdline.split("=", 1)
        self.tags = self.tag.split(",")

        self.timeout = 60
        self.force = False
        self.kill = "t"  # tree; all children recursively
        self.capture = 3  # outputs to consume
        self.audio = "y"
        self.pri = 0  # priority; higher = later
        self.ext = []

        while True:
            try:
                bp = os.path.expanduser(args)
                if WINDOWS:
                    bp = uncyg(bp)

                if bos.path.exists(bp):
                    self.bin = bp
                    return
            except:
                pass

            arg, args = args.split(",", 1)
            arg = arg.lower()

            if arg.startswith("a"):
                self.audio = arg[1:]  # [r]equire [n]ot [d]ontcare
                continue

            if arg.startswith("k"):
                self.kill = arg[1:]  # [t]ree [m]ain [n]one
                continue

            if arg.startswith("c"):
                self.capture = int(arg[1:])  # 0=none 1=stdout 2=stderr 3=both
                continue

            if arg == "f":
                self.force = True
                continue

            if arg.startswith("t"):
                self.timeout = int(arg[1:])
                continue

            if arg.startswith("e"):
                self.ext.append(arg[1:])
                continue

            if arg.startswith("p"):
                self.pri = int(arg[1:] or "1")
                continue

            raise Exception()


def ffprobe(
    abspath: str, timeout: int = 60
) -> tuple[dict[str, tuple[int, Any]], dict[str, list[Any]]]:
    cmd = [
        b"ffprobe",
        b"-hide_banner",
        b"-show_streams",
        b"-show_format",
        b"--",
        fsenc(abspath),
    ]
    rc, so, se = runcmd(cmd, timeout=timeout, nice=True, oom=200)
    retchk(rc, cmd, se)
    return parse_ffprobe(so)


def parse_ffprobe(txt: str) -> tuple[dict[str, tuple[int, Any]], dict[str, list[Any]]]:
    """ffprobe -show_format -show_streams"""
    streams = []
    fmt = {}
    g = {}
    for ln in [x.rstrip("\r") for x in txt.split("\n")]:
        try:
            sk, sv = ln.split("=", 1)
            g[sk] = sv
            continue
        except:
            pass

        if ln == "[STREAM]":
            g = {}
            streams.append(g)

        if ln == "[FORMAT]":
            g = {"codec_type": "format"}  # heh
            fmt = g

    streams = [fmt] + streams
    ret: dict[str, Any] = {}  # processed
    md: dict[str, list[Any]] = {}  # raw tags

    is_audio = fmt.get("format_name") in ["mp3", "ogg", "flac", "wav"]
    if fmt.get("filename", "").split(".")[-1].lower() in ["m4a", "aac"]:
        is_audio = True

    # if audio file, ensure audio stream appears first
    if (
        is_audio
        and len(streams) > 2
        and streams[1].get("codec_type") != "audio"
        and streams[2].get("codec_type") == "audio"
    ):
        streams = [fmt, streams[2], streams[1]] + streams[3:]

    have = {}
    for strm in streams:
        typ = strm.get("codec_type")
        if typ in have:
            continue

        have[typ] = True
        kvm = []

        if typ == "audio":
            kvm = [
                ["codec_name", "ac"],
                ["channel_layout", "chs"],
                ["sample_rate", ".hz"],
                ["bit_rate", ".aq"],
                ["duration", ".dur"],
            ]

        if typ == "video":
            if strm.get("DISPOSITION:attached_pic") == "1" or is_audio:
                continue

            kvm = [
                ["codec_name", "vc"],
                ["pix_fmt", "pixfmt"],
                ["r_frame_rate", ".fps"],
                ["bit_rate", ".vq"],
                ["width", ".resw"],
                ["height", ".resh"],
                ["duration", ".dur"],
            ]

        if typ == "format":
            kvm = [["duration", ".dur"], ["bit_rate", ".q"], ["format_name", "fmt"]]

        for sk, rk in kvm:
            v1 = strm.get(sk)
            if v1 is None:
                continue

            if rk.startswith("."):
                try:
                    zf = float(v1)
                    v2 = ret.get(rk)
                    if v2 is None or zf > v2:
                        ret[rk] = zf
                except:
                    # sqlite doesnt care but the code below does
                    if v1 not in ["N/A"]:
                        ret[rk] = v1
            else:
                ret[rk] = v1

    if ret.get("vc") == "ansi":  # shellscript
        return {}, {}

    for strm in streams:
        for sk, sv in strm.items():
            if not sk.startswith("TAG:"):
                continue

            sk = sk[4:].strip()
            sv = sv.strip()
            if sk and sv and sk not in md:
                md[sk] = [sv]

    for sk in [".q", ".vq", ".aq"]:
        if sk in ret:
            ret[sk] /= 1000  # bit_rate=320000

    for sk in [".q", ".vq", ".aq", ".resw", ".resh"]:
        if sk in ret:
            ret[sk] = int(ret[sk])

    if ".fps" in ret:
        fps = ret[".fps"]
        if "/" in fps:
            fa, fb = fps.split("/")
            try:
                fps = float(fa) / float(fb)
            except:
                fps = 9001

        if fps < 1000 and fmt.get("format_name") not in ["image2", "png_pipe"]:
            ret[".fps"] = round(fps, 3)
        else:
            del ret[".fps"]

    if ".dur" in ret:
        if ret[".dur"] < 0.1:
            del ret[".dur"]
            if ".q" in ret:
                del ret[".q"]

    if "fmt" in ret:
        ret["fmt"] = ret["fmt"].split(",")[0]

    if ".resw" in ret and ".resh" in ret:
        ret["res"] = "{}x{}".format(ret[".resw"], ret[".resh"])

    zero = int("0")
    zd = {k: (zero, v) for k, v in ret.items()}

    return zd, md


class MTag(object):
    def __init__(self, log_func: "RootLogger", args: argparse.Namespace) -> None:
        self.log_func = log_func
        self.args = args
        self.usable = True
        self.prefer_mt = not args.no_mtag_ff
        self.backend = (
            "ffprobe" if args.no_mutagen or (HAVE_FFPROBE and EXE) else "mutagen"
        )
        self.can_ffprobe = HAVE_FFPROBE and not args.no_mtag_ff
        mappings = args.mtm
        or_ffprobe = " or FFprobe"

        if self.backend == "mutagen":
            self.get = self.get_mutagen
            try:
                from mutagen import version  # noqa: F401
            except:
                self.log("could not load Mutagen, trying FFprobe instead", c=3)
                self.backend = "ffprobe"

        if self.backend == "ffprobe":
            self.usable = self.can_ffprobe
            self.get = self.get_ffprobe
            self.prefer_mt = True

            if not HAVE_FFPROBE:
                pass

            elif args.no_mtag_ff:
                msg = "found FFprobe but it was disabled by --no-mtag-ff"
                self.log(msg, c=3)

        if not self.usable:
            if EXE:
                t = "copyparty.exe cannot use mutagen; need ffprobe.exe to read media tags: "
                self.log(t + FFMPEG_URL)
                return

            msg = "need Mutagen{} to read media tags so please run this:\n{}{} -m pip install --user mutagen\n"
            pyname = os.path.basename(pybin)
            self.log(msg.format(or_ffprobe, " " * 37, pyname), c=1)
            return

        # https://picard-docs.musicbrainz.org/downloads/MusicBrainz_Picard_Tag_Map.html
        tagmap = {
            "album": ["album", "talb", "\u00a9alb", "original-album", "toal"],
            "artist": [
                "artist",
                "tpe1",
                "\u00a9art",
                "composer",
                "performer",
                "arranger",
                "\u00a9wrt",
                "tcom",
                "tpe3",
                "original-artist",
                "tope",
            ],
            "title": ["title", "tit2", "\u00a9nam"],
            "circle": [
                "album-artist",
                "tpe2",
                "aart",
                "conductor",
                "organization",
                "band",
            ],
            ".tn": ["tracknumber", "trck", "trkn", "track"],
            "genre": ["genre", "tcon", "\u00a9gen"],
            "date": [
                "original-release-date",
                "release-date",
                "date",
                "tdrc",
                "\u00a9day",
                "original-date",
                "original-year",
                "tyer",
                "tdor",
                "tory",
                "year",
                "creation-time",
            ],
            ".bpm": ["bpm", "tbpm", "tmpo", "tbp"],
            "key": ["initial-key", "tkey", "key"],
            "comment": ["comment", "comm", "\u00a9cmt", "comments", "description"],
        }

        if mappings:
            for k, v in [x.split("=") for x in mappings]:
                tagmap[k] = v.split(",")

        self.tagmap = {}
        for k, vs in tagmap.items():
            vs2 = []
            for v in vs:
                if "-" not in v:
                    vs2.append(v)
                    continue

                vs2.append(v.replace("-", " "))
                vs2.append(v.replace("-", "_"))
                vs2.append(v.replace("-", ""))

            self.tagmap[k] = vs2

        self.rmap = {
            v: [n, k] for k, vs in self.tagmap.items() for n, v in enumerate(vs)
        }
        # self.get = self.compare

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func("mtag", msg, c)

    def normalize_tags(
        self, parser_output: dict[str, tuple[int, Any]], md: dict[str, list[Any]]
    ) -> dict[str, Union[str, float]]:
        for sk, tv in dict(md).items():
            if not tv:
                continue

            sk = sk.lower().split("::")[0].strip()
            key_mapping = self.rmap.get(sk)
            if not key_mapping:
                continue

            priority, alias = key_mapping
            if alias not in parser_output or parser_output[alias][0] > priority:
                parser_output[alias] = (priority, tv[0])

        # take first value (lowest priority / most preferred)
        ret: dict[str, Union[str, float]] = {
            sk: unicode(tv[1]).strip() for sk, tv in parser_output.items()
        }

        # track 3/7 => track 3
        for sk, zv in ret.items():
            if sk[0] == ".":
                sv = str(zv).split("/")[0].strip().lstrip("0")
                ret[sk] = sv or 0

        # normalize key notation to rkeobo
        okey = ret.get("key")
        if okey:
            key = str(okey).replace(" ", "").replace("maj", "").replace("min", "m")
            ret["key"] = REKOBO_LKEY.get(key.lower(), okey)

        if self.args.mtag_vv:
            zl = " ".join("\033[36m{} \033[33m{}".format(k, v) for k, v in ret.items())
            self.log("norm: {}\033[0m".format(zl), "90")

        return ret

    def compare(self, abspath: str) -> dict[str, Union[str, float]]:
        if abspath.endswith(".au"):
            return {}

        print("\n" + abspath)
        r1 = self.get_mutagen(abspath)
        r2 = self.get_ffprobe(abspath)

        keys = {}
        for d in [r1, r2]:
            for k in d.keys():
                keys[k] = True

        diffs = []
        l1 = []
        l2 = []
        for k in sorted(keys.keys()):
            if k in [".q", ".dur"]:
                continue  # lenient

            v1 = r1.get(k)
            v2 = r2.get(k)
            if v1 == v2:
                print("  ", k, v1)
            elif v1 != "0000":  # FFprobe date=0
                diffs.append(k)
                print(" 1", k, v1)
                print(" 2", k, v2)
                if v1:
                    l1.append(k)
                if v2:
                    l2.append(k)

        if diffs:
            raise Exception()

        return r1

    def get_mutagen(self, abspath: str) -> dict[str, Union[str, float]]:
        ret: dict[str, tuple[int, Any]] = {}

        if not bos.path.isfile(abspath):
            return {}

        from mutagen import File

        try:
            md = File(fsenc(abspath), easy=True)
            assert md
            if self.args.mtag_vv:
                for zd in (md.info.__dict__, dict(md.tags)):
                    zl = ["\033[36m{} \033[33m{}".format(k, v) for k, v in zd.items()]
                    self.log("mutagen: {}\033[0m".format(" ".join(zl)), "90")
            if not md.info.length and not md.info.codec:
                raise Exception()
        except Exception as ex:
            if self.args.mtag_v:
                self.log("mutagen-err [{}] @ [{}]".format(ex, abspath), "90")

            return self.get_ffprobe(abspath) if self.can_ffprobe else {}

        sz = bos.path.getsize(abspath)
        try:
            ret[".q"] = (0, int((sz / md.info.length) / 128))
        except:
            pass

        for attr, k, norm in [
            ["codec", "ac", unicode],
            ["channels", "chs", int],
            ["sample_rate", ".hz", int],
            ["bitrate", ".aq", int],
            ["length", ".dur", int],
        ]:
            try:
                v = getattr(md.info, attr)
            except:
                if k != "ac":
                    continue

                try:
                    v = str(md.info).split(".")[1]
                    if v.startswith("ogg"):
                        v = v[3:]
                except:
                    continue

            if not v:
                continue

            if k == ".aq":
                v /= 1000

            if k == "ac" and v.startswith("mp4a.40."):
                v = "aac"

            ret[k] = (0, norm(v))

        return self.normalize_tags(ret, md)

    def get_ffprobe(self, abspath: str) -> dict[str, Union[str, float]]:
        if not bos.path.isfile(abspath):
            return {}

        ret, md = ffprobe(abspath, self.args.mtag_to)

        if self.args.mtag_vv:
            for zd in (ret, dict(md)):
                zl = ["\033[36m{} \033[33m{}".format(k, v) for k, v in zd.items()]
                self.log("ffprobe: {}\033[0m".format(" ".join(zl)), "90")

        return self.normalize_tags(ret, md)

    def get_bin(
        self, parsers: dict[str, MParser], abspath: str, oth_tags: dict[str, Any]
    ) -> dict[str, Any]:
        if not bos.path.isfile(abspath):
            return {}

        env = os.environ.copy()
        try:
            if EXE:
                raise Exception()

            pypath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            zsl = [str(pypath)] + [str(x) for x in sys.path if x]
            pypath = str(os.pathsep.join(zsl))
            env["PYTHONPATH"] = pypath
        except:
            raise  # might be expected outside cpython

        ret: dict[str, Any] = {}
        for tagname, parser in sorted(parsers.items(), key=lambda x: (x[1].pri, x[0])):
            try:
                cmd = [parser.bin, abspath]
                if parser.bin.endswith(".py"):
                    cmd = [pybin] + cmd

                args = {
                    "env": env,
                    "nice": True,
                    "oom": 300,
                    "timeout": parser.timeout,
                    "kill": parser.kill,
                    "capture": parser.capture,
                }

                if parser.pri:
                    zd = oth_tags.copy()
                    zd.update(ret)
                    args["sin"] = json.dumps(zd).encode("utf-8", "replace")

                bcmd = [sfsenc(x) for x in cmd[:-1]] + [fsenc(cmd[-1])]
                rc, v, err = runcmd(bcmd, **args)  # type: ignore
                retchk(rc, bcmd, err, self.log, 5, self.args.mtag_v)
                v = v.strip()
                if not v:
                    continue

                if "," not in tagname:
                    ret[tagname] = v
                else:
                    zj = json.loads(v)
                    for tag in tagname.split(","):
                        if tag and tag in zj:
                            ret[tag] = zj[tag]
            except:
                if self.args.mtag_v:
                    t = "mtag error: tagname {}, parser {}, file {} => {}"
                    self.log(t.format(tagname, parser.bin, abspath, min_ex()))

        return ret

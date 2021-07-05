# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import sys
import json
import shutil
import subprocess as sp

from .__init__ import PY2, WINDOWS, unicode
from .util import fsenc, fsdec, uncyg, REKOBO_LKEY


def have_ff(cmd):
    if PY2:
        print("# checking {}".format(cmd))
        cmd = (cmd + " -version").encode("ascii").split(b" ")
        try:
            sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE).communicate()
            return True
        except:
            return False
    else:
        return bool(shutil.which(cmd))


HAVE_FFMPEG = have_ff("ffmpeg")
HAVE_FFPROBE = have_ff("ffprobe")


class MParser(object):
    def __init__(self, cmdline):
        self.tag, args = cmdline.split("=", 1)
        self.tags = self.tag.split(",")

        self.timeout = 30
        self.force = False
        self.audio = "y"
        self.ext = []

        while True:
            try:
                bp = os.path.expanduser(args)
                if WINDOWS:
                    bp = uncyg(bp)

                if os.path.exists(bp):
                    self.bin = bp
                    return
            except:
                pass

            arg, args = args.split(",", 1)
            arg = arg.lower()

            if arg.startswith("a"):
                self.audio = arg[1:]  # [r]equire [n]ot [d]ontcare
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

            raise Exception()


def ffprobe(abspath):
    cmd = [
        b"ffprobe",
        b"-hide_banner",
        b"-show_streams",
        b"-show_format",
        b"--",
        fsenc(abspath),
    ]
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    r = p.communicate()
    txt = r[0].decode("utf-8", "replace")
    return parse_ffprobe(txt)


def parse_ffprobe(txt):
    """ffprobe -show_format -show_streams"""
    streams = []
    fmt = {}
    g = None
    for ln in [x.rstrip("\r") for x in txt.split("\n")]:
        try:
            k, v = ln.split("=", 1)
            g[k] = v
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
    ret = {}  # processed
    md = {}  # raw tags

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
            kvm = [["duration", ".dur"], ["bit_rate", ".q"]]

        for sk, rk in kvm:
            v = strm.get(sk)
            if v is None:
                continue

            if rk.startswith("."):
                try:
                    v = float(v)
                    v2 = ret.get(rk)
                    if v2 is None or v > v2:
                        ret[rk] = v
                except:
                    # sqlite doesnt care but the code below does
                    if v not in ["N/A"]:
                        ret[rk] = v
            else:
                ret[rk] = v

    if ret.get("vc") == "ansi":  # shellscript
        return {}, {}

    for strm in streams:
        for k, v in strm.items():
            if not k.startswith("TAG:"):
                continue

            k = k[4:].strip()
            v = v.strip()
            if k and v and k not in md:
                md[k] = [v]

    for k in [".q", ".vq", ".aq"]:
        if k in ret:
            ret[k] /= 1000  # bit_rate=320000

    for k in [".q", ".vq", ".aq", ".resw", ".resh"]:
        if k in ret:
            ret[k] = int(ret[k])

    if ".fps" in ret:
        fps = ret[".fps"]
        if "/" in fps:
            fa, fb = fps.split("/")
            fps = int(fa) * 1.0 / int(fb)

        if fps < 1000 and fmt.get("format_name") not in ["image2", "png_pipe"]:
            ret[".fps"] = round(fps, 3)
        else:
            del ret[".fps"]

    if ".dur" in ret:
        if ret[".dur"] < 0.1:
            del ret[".dur"]
            if ".q" in ret:
                del ret[".q"]

    if ".resw" in ret and ".resh" in ret:
        ret["res"] = "{}x{}".format(ret[".resw"], ret[".resh"])

    ret = {k: [0, v] for k, v in ret.items()}

    return ret, md


class MTag(object):
    def __init__(self, log_func, args):
        self.log_func = log_func
        self.usable = True
        self.prefer_mt = False
        mappings = args.mtm
        self.backend = "ffprobe" if args.no_mutagen else "mutagen"
        or_ffprobe = " or ffprobe"

        if self.backend == "mutagen":
            self.get = self.get_mutagen
            try:
                import mutagen
            except:
                self.log("could not load mutagen, trying ffprobe instead", c=3)
                self.backend = "ffprobe"

        if self.backend == "ffprobe":
            self.get = self.get_ffprobe
            self.prefer_mt = True
            # about 20x slower
            self.usable = HAVE_FFPROBE

            if self.usable and WINDOWS and sys.version_info < (3, 8):
                self.usable = False
                or_ffprobe = " or python >= 3.8"
                msg = "found ffprobe but your python is too old; need 3.8 or newer"
                self.log(msg, c=1)

        if not self.usable:
            msg = "need mutagen{} to read media tags so please run this:\n{}{} -m pip install --user mutagen\n"
            self.log(
                msg.format(or_ffprobe, " " * 37, os.path.basename(sys.executable)), c=1
            )
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

    def log(self, msg, c=0):
        self.log_func("mtag", msg, c)

    def normalize_tags(self, ret, md):
        for k, v in dict(md).items():
            if not v:
                continue

            k = k.lower().split("::")[0].strip()
            mk = self.rmap.get(k)
            if not mk:
                continue

            pref, mk = mk
            if mk not in ret or ret[mk][0] > pref:
                ret[mk] = [pref, v[0]]

        # take first value
        ret = {k: unicode(v[1]).strip() for k, v in ret.items()}

        # track 3/7 => track 3
        for k, v in ret.items():
            if k[0] == ".":
                v = v.split("/")[0].strip().lstrip("0")
                ret[k] = v or 0

        # normalize key notation to rkeobo
        okey = ret.get("key")
        if okey:
            key = okey.replace(" ", "").replace("maj", "").replace("min", "m")
            ret["key"] = REKOBO_LKEY.get(key.lower(), okey)

        return ret

    def compare(self, abspath):
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
            elif v1 != "0000":  # ffprobe date=0
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

    def get_mutagen(self, abspath):
        import mutagen

        try:
            md = mutagen.File(fsenc(abspath), easy=True)
            x = md.info.length
        except Exception as ex:
            return {}

        ret = {}
        try:
            dur = int(md.info.length)
            try:
                q = int(md.info.bitrate / 1024)
            except:
                q = int((os.path.getsize(fsenc(abspath)) / dur) / 128)

            ret[".dur"] = [0, dur]
            ret[".q"] = [0, q]
        except:
            pass

        return self.normalize_tags(ret, md)

    def get_ffprobe(self, abspath):
        ret, md = ffprobe(abspath)
        return self.normalize_tags(ret, md)

    def get_bin(self, parsers, abspath):
        pypath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        pypath = [str(pypath)] + [str(x) for x in sys.path if x]
        pypath = str(os.pathsep.join(pypath))
        env = os.environ.copy()
        env["PYTHONPATH"] = pypath

        ret = {}
        for tagname, mp in parsers.items():
            try:
                cmd = [sys.executable, mp.bin, abspath]
                args = {"env": env, "timeout": mp.timeout}

                if WINDOWS:
                    args["creationflags"] = 0x4000
                else:
                    cmd = ["nice"] + cmd

                cmd = [fsenc(x) for x in cmd]
                v = sp.check_output(cmd, **args).strip()
                if not v:
                    continue

                if "," not in tagname:
                    ret[tagname] = v.decode("utf-8")
                else:
                    v = json.loads(v)
                    for tag in tagname.split(","):
                        if tag and tag in v:
                            ret[tag] = v[tag]
            except:
                pass

        return ret

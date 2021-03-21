# coding: utf-8
from __future__ import print_function, unicode_literals

import re
import os
import sys
import shutil
import subprocess as sp

from .__init__ import PY2, WINDOWS
from .util import fsenc, fsdec, REKOBO_LKEY

if not PY2:
    unicode = str


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
            if PY2:
                cmd = [b"ffprobe", b"-version"]
                try:
                    sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
                except:
                    self.usable = False
            else:
                if not shutil.which("ffprobe"):
                    self.usable = False

            if self.usable and WINDOWS and sys.version_info < (3, 8):
                self.usable = False
                or_ffprobe = " or python >= 3.8"
                msg = "found ffprobe but your python is too old; need 3.8 or newer"
                self.log(msg, c=1)

        if not self.usable:
            msg = "need mutagen{} to read media tags so please run this:\n  {} -m pip install --user mutagen"
            self.log(msg.format(or_ffprobe, os.path.basename(sys.executable)), c=1)
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
            md = mutagen.File(abspath, easy=True)
            x = md.info.length
        except Exception as ex:
            return {}

        ret = {}
        try:
            dur = int(md.info.length)
            try:
                q = int(md.info.bitrate / 1024)
            except:
                q = int((os.path.getsize(abspath) / dur) / 128)

            ret[".dur"] = [0, dur]
            ret[".q"] = [0, q]
        except:
            pass

        return self.normalize_tags(ret, md)

    def get_ffprobe(self, abspath):
        cmd = [b"ffprobe", b"-hide_banner", b"--", fsenc(abspath)]
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        r = p.communicate()
        txt = r[1].decode("utf-8", "replace")
        txt = [x.rstrip("\r") for x in txt.split("\n")]

        """
        note:
          tags which contain newline will be truncated on first \n,
          ffprobe emits \n and spacepads the : to align visually
        note:
          the Stream ln always mentions Audio: if audio
          the Stream ln usually has kb/s, is more accurate
          the Duration ln always has kb/s
          the Metadata: after Chapter may contain BPM info,
            title : Tempo: 126.0

        Input #0, wav,
          Metadata:
            date : <OK>
          Duration:
            Chapter #
            Metadata:
              title : <NG>

        Input #0, mp3,
          Metadata:
            album : <OK>
          Duration:
            Stream #0:0: Audio:
            Stream #0:1: Video:
            Metadata:
              comment : <NG>
        """

        ptn_md_beg = re.compile("^( +)Metadata:$")
        ptn_md_kv = re.compile("^( +)([^:]+) *: (.*)")
        ptn_dur = re.compile("^ *Duration: ([^ ]+)(, |$)")
        ptn_br1 = re.compile("^ *Duration: .*, bitrate: ([0-9]+) kb/s(, |$)")
        ptn_br2 = re.compile("^ *Stream.*: Audio:.* ([0-9]+) kb/s(, |$)")
        ptn_audio = re.compile("^ *Stream .*: Audio: ")
        ptn_au_parent = re.compile("^ *(Input #|Stream .*: Audio: )")

        ret = {}
        md = {}
        in_md = False
        is_audio = False
        au_parent = False
        for ln in txt:
            m = ptn_md_kv.match(ln)
            if m and in_md and len(m.group(1)) == in_md:
                _, k, v = [x.strip() for x in m.groups()]
                if k != "" and v != "":
                    md[k] = [v]
                continue
            else:
                in_md = False

            m = ptn_md_beg.match(ln)
            if m and au_parent:
                in_md = len(m.group(1)) + 2
                continue

            au_parent = bool(ptn_au_parent.search(ln))

            if ptn_audio.search(ln):
                is_audio = True

            m = ptn_dur.search(ln)
            if m:
                sec = 0
                tstr = m.group(1)
                if tstr.lower() != "n/a":
                    try:
                        tf = tstr.split(",")[0].split(".")[0].split(":")
                        for f in tf:
                            sec *= 60
                            sec += int(f)
                    except:
                        self.log("invalid timestr from ffprobe: [{}]".format(tstr), c=3)

                ret[".dur"] = sec
                m = ptn_br1.search(ln)
                if m:
                    ret[".q"] = m.group(1)

            m = ptn_br2.search(ln)
            if m:
                ret[".q"] = m.group(1)

        if not is_audio:
            return {}

        ret = {k: [0, v] for k, v in ret.items()}

        return self.normalize_tags(ret, md)

    def get_bin(self, parsers, abspath):
        pypath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        pypath = [str(pypath)] + [str(x) for x in sys.path if x]
        pypath = str(os.pathsep.join(pypath))
        env = os.environ.copy()
        env["PYTHONPATH"] = pypath

        ret = {}
        for tagname, (binpath, timeout) in parsers.items():
            try:
                cmd = [sys.executable, binpath, abspath]
                args = {"env": env, "timeout": timeout}

                if WINDOWS:
                    args["creationflags"] = 0x4000
                else:
                    cmd = ["nice"] + cmd

                cmd = [fsenc(x) for x in cmd]
                v = sp.check_output(cmd, **args).strip()
                if v:
                    ret[tagname] = v.decode("utf-8")
            except:
                pass

        return ret

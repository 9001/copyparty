# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import time
import shutil
import base64
import hashlib
import threading
import subprocess as sp

from .__init__ import PY2, unicode
from .util import fsenc, vsplit, statdir, runcmd, Queue, Cooldown, BytesIO, min_ex
from .bos import bos
from .mtag import HAVE_FFMPEG, HAVE_FFPROBE, ffprobe


HAVE_PIL = False
HAVE_HEIF = False
HAVE_AVIF = False
HAVE_WEBP = False

try:
    from PIL import Image, ImageOps, ExifTags

    HAVE_PIL = True
    try:
        Image.new("RGB", (2, 2)).save(BytesIO(), format="webp")
        HAVE_WEBP = True
    except:
        pass

    try:
        from pyheif_pillow_opener import register_heif_opener

        register_heif_opener()
        HAVE_HEIF = True
    except:
        pass

    try:
        import pillow_avif

        HAVE_AVIF = True
    except:
        pass
except:
    pass

# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
# ffmpeg -formats
FMT_PIL = "bmp dib gif icns ico jpg jpeg jp2 jpx pcx png pbm pgm ppm pnm sgi tga tif tiff webp xbm dds xpm"
FMT_FFV = "av1 asf avi flv m4v mkv mjpeg mjpg mpg mpeg mpg2 mpeg2 h264 avc mts h265 hevc mov 3gp mp4 ts mpegts nut ogv ogm rm vob webm wmv"
FMT_FFA = "aac m4a ogg opus flac alac mp3 mp2 ac3 dts wma ra wav aif aiff au alaw ulaw mulaw amr gsm ape tak tta wv"

if HAVE_HEIF:
    FMT_PIL += " heif heifs heic heics"

if HAVE_AVIF:
    FMT_PIL += " avif avifs"

FMT_PIL, FMT_FFV, FMT_FFA = [
    {x: True for x in y.split(" ") if x} for y in [FMT_PIL, FMT_FFV, FMT_FFA]
]


THUMBABLE = {}

if HAVE_PIL:
    THUMBABLE.update(FMT_PIL)

if HAVE_FFMPEG and HAVE_FFPROBE:
    THUMBABLE.update(FMT_FFV)
    THUMBABLE.update(FMT_FFA)


def thumb_path(histpath, rem, mtime, fmt):
    # base16 = 16 = 256
    # b64-lc = 38 = 1444
    # base64 = 64 = 4096
    rd, fn = vsplit(rem)
    if rd:
        h = hashlib.sha512(fsenc(rd)).digest()
        b64 = base64.urlsafe_b64encode(h).decode("ascii")[:24]
        rd = "{}/{}/".format(b64[:2], b64[2:4]).lower() + b64
    else:
        rd = "top"

    # could keep original filenames but this is safer re pathlen
    h = hashlib.sha512(fsenc(fn)).digest()
    fn = base64.urlsafe_b64encode(h).decode("ascii")[:24]

    if fmt in ("opus", "caf"):
        cat = "ac"
    else:
        fmt = "webp" if fmt == "w" else "jpg"
        cat = "th"

    return "{}/{}/{}/{}.{:x}.{}".format(histpath, cat, rd, fn, int(mtime), fmt)


class ThumbSrv(object):
    def __init__(self, hub):
        self.hub = hub
        self.asrv = hub.asrv
        self.args = hub.args
        self.log_func = hub.log

        res = hub.args.th_size.split("x")
        self.res = tuple([int(x) for x in res])
        self.poke_cd = Cooldown(self.args.th_poke)

        self.mutex = threading.Lock()
        self.busy = {}
        self.stopping = False
        self.nthr = max(1, self.args.th_mt)

        self.q = Queue(self.nthr * 4)
        for n in range(self.nthr):
            t = threading.Thread(
                target=self.worker, name="thumb-{}-{}".format(n, self.nthr)
            )
            t.daemon = True
            t.start()

        want_ff = not self.args.no_vthumb or not self.args.no_athumb
        if want_ff and (not HAVE_FFMPEG or not HAVE_FFPROBE):
            missing = []
            if not HAVE_FFMPEG:
                missing.append("FFmpeg")

            if not HAVE_FFPROBE:
                missing.append("FFprobe")

            msg = "cannot create audio/video thumbnails because some of the required programs are not available: "
            msg += ", ".join(missing)
            self.log(msg, c=3)

        if self.args.th_clean:
            t = threading.Thread(target=self.cleaner, name="thumb.cln")
            t.daemon = True
            t.start()

    def log(self, msg, c=0):
        self.log_func("thumb", msg, c)

    def shutdown(self):
        self.stopping = True
        for _ in range(self.nthr):
            self.q.put(None)

    def stopped(self):
        with self.mutex:
            return not self.nthr

    def get(self, ptop, rem, mtime, fmt):
        histpath = self.asrv.vfs.histtab.get(ptop)
        if not histpath:
            self.log("no histpath for [{}]".format(ptop))
            return None

        tpath = thumb_path(histpath, rem, mtime, fmt)
        abspath = os.path.join(ptop, rem)
        cond = threading.Condition(self.mutex)
        do_conv = False
        with self.mutex:
            try:
                self.busy[tpath].append(cond)
                self.log("wait {}".format(tpath))
            except:
                thdir = os.path.dirname(tpath)
                bos.makedirs(thdir)

                inf_path = os.path.join(thdir, "dir.txt")
                if not bos.path.exists(inf_path):
                    with open(inf_path, "wb") as f:
                        f.write(fsenc(os.path.dirname(abspath)))

                self.busy[tpath] = [cond]
                do_conv = True

        if do_conv:
            self.q.put([abspath, tpath])
            self.log("conv {} \033[0m{}".format(tpath, abspath), c=6)

        while not self.stopping:
            with self.mutex:
                if tpath not in self.busy:
                    break

            with cond:
                cond.wait(3)

        try:
            st = bos.stat(tpath)
            if st.st_size:
                self.poke(tpath)
                return tpath
        except:
            pass

        return None

    def worker(self):
        while not self.stopping:
            task = self.q.get()
            if not task:
                break

            abspath, tpath = task
            ext = abspath.split(".")[-1].lower()
            fun = None
            if not bos.path.exists(tpath):
                if ext in FMT_PIL:
                    fun = self.conv_pil
                elif ext in FMT_FFV:
                    fun = self.conv_ffmpeg
                elif ext in FMT_FFA:
                    if tpath.endswith(".opus") or tpath.endswith(".caf"):
                        fun = self.conv_opus
                    else:
                        fun = self.conv_spec

            if fun:
                try:
                    fun(abspath, tpath)
                except:
                    msg = "{} could not create thumbnail of {}\n{}"
                    self.log(msg.format(fun.__name__, abspath, min_ex()), "1;30")
                    with open(tpath, "wb") as _:
                        pass

            with self.mutex:
                subs = self.busy[tpath]
                del self.busy[tpath]

            for x in subs:
                with x:
                    x.notify_all()

        with self.mutex:
            self.nthr -= 1

    def fancy_pillow(self, im):
        # exif_transpose is expensive (loads full image + unconditional copy)
        r = max(*self.res) * 2
        im.thumbnail((r, r), resample=Image.LANCZOS)
        try:
            k = next(k for k, v in ExifTags.TAGS.items() if v == "Orientation")
            exif = im.getexif()
            rot = int(exif[k])
            del exif[k]
        except:
            rot = 1

        rots = {8: Image.ROTATE_90, 3: Image.ROTATE_180, 6: Image.ROTATE_270}
        if rot in rots:
            im = im.transpose(rots[rot])

        if self.args.th_no_crop:
            im.thumbnail(self.res, resample=Image.LANCZOS)
        else:
            iw, ih = im.size
            dw, dh = self.res
            res = (min(iw, dw), min(ih, dh))
            im = ImageOps.fit(im, res, method=Image.LANCZOS)

        return im

    def conv_pil(self, abspath, tpath):
        with Image.open(fsenc(abspath)) as im:
            try:
                im = self.fancy_pillow(im)
            except Exception as ex:
                self.log("fancy_pillow {}".format(ex), "1;30")
                im.thumbnail(self.res)

            fmts = ["RGB", "L"]
            args = {"quality": 40}

            if tpath.endswith(".webp"):
                # quality 80 = pillow-default
                # quality 75 = ffmpeg-default
                # method 0 = pillow-default, fast
                # method 4 = ffmpeg-default
                # method 6 = max, slow
                fmts += ["RGBA", "LA"]
                args["method"] = 6
            else:
                # default q = 75
                args["progressive"] = True

            if im.mode not in fmts:
                # print("conv {}".format(im.mode))
                im = im.convert("RGB")

            im.save(tpath, **args)

    def conv_ffmpeg(self, abspath, tpath):
        ret, _ = ffprobe(abspath)

        ext = abspath.rsplit(".")[-1]
        if ext in ["h264", "h265"]:
            seek = []
        else:
            dur = ret[".dur"][1] if ".dur" in ret else 4
            seek = "{:.0f}".format(dur / 3)
            seek = [b"-ss", seek.encode("utf-8")]

        scale = "scale={0}:{1}:force_original_aspect_ratio="
        if self.args.th_no_crop:
            scale += "decrease,setsar=1:1"
        else:
            scale += "increase,crop={0}:{1},setsar=1:1"

        scale = scale.format(*list(self.res)).encode("utf-8")
        # fmt: off
        cmd = [
            b"ffmpeg",
            b"-nostdin",
            b"-v", b"error",
            b"-hide_banner"
        ]
        cmd += seek
        cmd += [
            b"-i", fsenc(abspath),
            b"-map", b"0:v:0",
            b"-vf", scale,
            b"-frames:v", b"1",
            b"-metadata:s:v:0", b"rotate=0",
        ]
        # fmt: on

        if tpath.endswith(".jpg"):
            cmd += [
                b"-q:v",
                b"6",  # default=??
            ]
        else:
            cmd += [
                b"-q:v",
                b"50",  # default=75
                b"-compression_level:v",
                b"6",  # default=4, 0=fast, 6=max
            ]

        cmd += [fsenc(tpath)]
        self._run_ff(cmd)

    def _run_ff(self, cmd):
        # self.log((b" ".join(cmd)).decode("utf-8"))
        ret, sout, serr = runcmd(cmd, timeout=self.args.th_convt)
        if ret != 0:
            m = "FFmpeg failed (probably a corrupt video file):\n"
            m += "\n".join(["ff: {}".format(x) for x in serr.split("\n")])
            self.log(m, c="1;30")
            raise sp.CalledProcessError(ret, (cmd[0], b"...", cmd[-1]))

    def conv_spec(self, abspath, tpath):
        ret, _ = ffprobe(abspath)
        if "ac" not in ret:
            raise Exception("not audio")

        fc = "[0:a:0]aresample=48000{},showspectrumpic=s=640x512,crop=780:544:70:50[o]"

        if self.args.th_ff_swr:
            fco = ":filter_size=128:cutoff=0.877"
        else:
            fco = ":resampler=soxr"

        fc = fc.format(fco)

        # fmt: off
        cmd = [
            b"ffmpeg",
            b"-nostdin",
            b"-v", b"error",
            b"-hide_banner",
            b"-i", fsenc(abspath),
            b"-filter_complex", fc.encode("utf-8"),
            b"-map", b"[o]"
        ]
        # fmt: on

        if tpath.endswith(".jpg"):
            cmd += [
                b"-q:v",
                b"6",  # default=??
            ]
        else:
            cmd += [
                b"-q:v",
                b"50",  # default=75
                b"-compression_level:v",
                b"6",  # default=4, 0=fast, 6=max
            ]

        cmd += [fsenc(tpath)]
        self._run_ff(cmd)

    def conv_opus(self, abspath, tpath):
        if self.args.no_acode:
            raise Exception("disabled in server config")

        ret, _ = ffprobe(abspath)
        if "ac" not in ret:
            raise Exception("not audio")

        src_opus = abspath.lower().endswith(".opus") or ret["ac"][1] == "opus"
        want_caf = tpath.endswith(".caf")
        tmp_opus = tpath
        if want_caf:
            tmp_opus = tpath.rsplit(".", 1)[0] + ".opus"

        if not want_caf or (not src_opus and not bos.path.isfile(tmp_opus)):
            # fmt: off
            cmd = [
                b"ffmpeg",
                b"-nostdin",
                b"-v", b"error",
                b"-hide_banner",
                b"-i", fsenc(abspath),
                b"-map_metadata", b"-1",
                b"-map", b"0:a:0",
                b"-c:a", b"libopus",
                b"-b:a", b"128k",
                fsenc(tmp_opus)
            ]
            # fmt: on
            self._run_ff(cmd)

        if want_caf:
            # fmt: off
            cmd = [
                b"ffmpeg",
                b"-nostdin",
                b"-v", b"error",
                b"-hide_banner",
                b"-i", fsenc(abspath if src_opus else tmp_opus),
                b"-map_metadata", b"-1",
                b"-map", b"0:a:0",
                b"-c:a", b"copy",
                b"-f", b"caf",
                fsenc(tpath)
            ]
            # fmt: on
            self._run_ff(cmd)

    def poke(self, tdir):
        if not self.poke_cd.poke(tdir):
            return

        ts = int(time.time())
        try:
            for _ in range(4):
                bos.utime(tdir, (ts, ts))
                tdir = os.path.dirname(tdir)
        except:
            pass

    def cleaner(self):
        interval = self.args.th_clean
        while True:
            time.sleep(interval)
            ndirs = 0
            for vol, histpath in self.asrv.vfs.histtab.items():
                if histpath.startswith(vol):
                    self.log("\033[Jcln {}/\033[A".format(histpath))
                else:
                    self.log("\033[Jcln {} ({})/\033[A".format(histpath, vol))

                ndirs += self.clean(histpath)

            self.log("\033[Jcln ok; rm {} dirs".format(ndirs))

    def clean(self, histpath):
        ret = 0
        for cat in ["th", "ac"]:
            ret += self._clean(histpath, cat, None)

        return ret

    def _clean(self, histpath, cat, thumbpath):
        if not thumbpath:
            thumbpath = os.path.join(histpath, cat)

        # self.log("cln {}".format(thumbpath))
        exts = ["jpg", "webp"] if cat == "th" else ["opus", "caf"]
        maxage = getattr(self.args, cat + "_maxage")
        now = time.time()
        prev_b64 = None
        prev_fp = None
        try:
            ents = statdir(self.log, not self.args.no_scandir, False, thumbpath)
            ents = sorted(list(ents))
        except:
            return 0

        ndirs = 0
        for f, inf in ents:
            fp = os.path.join(thumbpath, f)
            cmp = fp.lower().replace("\\", "/")

            # "top" or b64 prefix/full (a folder)
            if len(f) <= 3 or len(f) == 24:
                age = now - inf.st_mtime
                if age > maxage:
                    with self.mutex:
                        safe = True
                        for k in self.busy.keys():
                            if k.lower().replace("\\", "/").startswith(cmp):
                                safe = False
                                break

                        if safe:
                            ndirs += 1
                            self.log("rm -rf [{}]".format(fp))
                            shutil.rmtree(fp, ignore_errors=True)
                else:
                    self._clean(histpath, cat, fp)

                continue

            # thumb file
            try:
                b64, ts, ext = f.split(".")
                if len(b64) != 24 or len(ts) != 8 or ext not in exts:
                    raise Exception()
            except:
                if f != "dir.txt":
                    self.log("foreign file in thumbs dir: [{}]".format(fp), 1)

                continue

            if b64 == prev_b64:
                self.log("rm replaced [{}]".format(fp))
                bos.unlink(prev_fp)

            if cat != "th" and inf.st_mtime + maxage < now:
                self.log("rm expired [{}]".format(fp))
                bos.unlink(fp)

            prev_b64 = b64
            prev_fp = fp

        return ndirs

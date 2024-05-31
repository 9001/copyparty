# coding: utf-8
from __future__ import print_function, unicode_literals

import base64
import hashlib
import logging
import os
import shutil
import subprocess as sp
import threading
import time

from queue import Queue

from .__init__ import ANYWIN, TYPE_CHECKING
from .authsrv import VFS
from .bos import bos
from .mtag import HAVE_FFMPEG, HAVE_FFPROBE, au_unpk, ffprobe
from .util import BytesIO  # type: ignore
from .util import (
    FFMPEG_URL,
    Cooldown,
    Daemon,
    Pebkac,
    afsenc,
    fsenc,
    min_ex,
    runcmd,
    statdir,
    vsplit,
    wrename,
    wunlink,
)

if True:  # pylint: disable=using-constant-test
    from typing import Optional, Union

if TYPE_CHECKING:
    from .svchub import SvcHub

HAVE_PIL = False
HAVE_PILF = False
HAVE_HEIF = False
HAVE_AVIF = False
HAVE_WEBP = False

try:
    from PIL import ExifTags, Image, ImageFont, ImageOps

    HAVE_PIL = True
    try:
        ImageFont.load_default(size=16)
        HAVE_PILF = True
    except:
        pass

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
        import pillow_avif  # noqa: F401  # pylint: disable=unused-import

        HAVE_AVIF = True
    except:
        pass

    logging.getLogger("PIL").setLevel(logging.WARNING)
except:
    pass

try:
    HAVE_VIPS = True
    import pyvips

    logging.getLogger("pyvips").setLevel(logging.WARNING)
except:
    HAVE_VIPS = False


def thumb_path(histpath: str, rem: str, mtime: float, fmt: str, ffa: set[str]) -> str:
    # base16 = 16 = 256
    # b64-lc = 38 = 1444
    # base64 = 64 = 4096
    rd, fn = vsplit(rem)
    if not rd:
        rd = "\ntop"

    # spectrograms are never cropped; strip fullsize flag
    ext = rem.split(".")[-1].lower()
    if ext in ffa and fmt[:2] in ("wf", "jf"):
        fmt = fmt.replace("f", "")

    rd += "\n" + fmt
    h = hashlib.sha512(afsenc(rd)).digest()
    b64 = base64.urlsafe_b64encode(h).decode("ascii")[:24]
    rd = ("%s/%s/" % (b64[:2], b64[2:4])).lower() + b64

    # could keep original filenames but this is safer re pathlen
    h = hashlib.sha512(afsenc(fn)).digest()
    fn = base64.urlsafe_b64encode(h).decode("ascii")[:24]

    if fmt in ("opus", "caf", "mp3"):
        cat = "ac"
    else:
        fc = fmt[:1]
        fmt = "webp" if fc == "w" else "png" if fc == "p" else "jpg"
        cat = "th"

    return "%s/%s/%s/%s.%x.%s" % (histpath, cat, rd, fn, int(mtime), fmt)


class ThumbSrv(object):
    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.asrv = hub.asrv
        self.args = hub.args
        self.log_func = hub.log

        self.poke_cd = Cooldown(self.args.th_poke)

        self.mutex = threading.Lock()
        self.busy: dict[str, list[threading.Condition]] = {}
        self.ram: dict[str, float] = {}
        self.memcond = threading.Condition(self.mutex)
        self.stopping = False
        self.nthr = max(1, self.args.th_mt)

        self.q: Queue[Optional[tuple[str, str, str, VFS]]] = Queue(self.nthr * 4)
        for n in range(self.nthr):
            Daemon(self.worker, "thumb-{}-{}".format(n, self.nthr))

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
            if ANYWIN and self.args.no_acode:
                self.log("download FFmpeg to fix it:\033[0m " + FFMPEG_URL, 3)

        if self.args.th_clean:
            Daemon(self.cleaner, "thumb.cln")

        self.fmt_pil, self.fmt_vips, self.fmt_ffi, self.fmt_ffv, self.fmt_ffa = [
            set(y.split(","))
            for y in [
                self.args.th_r_pil,
                self.args.th_r_vips,
                self.args.th_r_ffi,
                self.args.th_r_ffv,
                self.args.th_r_ffa,
            ]
        ]

        if not HAVE_HEIF:
            for f in "heif heifs heic heics".split(" "):
                self.fmt_pil.discard(f)

        if not HAVE_AVIF:
            for f in "avif avifs".split(" "):
                self.fmt_pil.discard(f)

        self.thumbable: set[str] = set()

        if "pil" in self.args.th_dec:
            self.thumbable |= self.fmt_pil

        if "vips" in self.args.th_dec:
            self.thumbable |= self.fmt_vips

        if "ff" in self.args.th_dec:
            for zss in [self.fmt_ffi, self.fmt_ffv, self.fmt_ffa]:
                self.thumbable |= zss

    def log(self, msg: str, c: Union[int, str] = 0) -> None:
        self.log_func("thumb", msg, c)

    def shutdown(self) -> None:
        self.stopping = True
        for _ in range(self.nthr):
            self.q.put(None)

    def stopped(self) -> bool:
        with self.mutex:
            return not self.nthr

    def getres(self, vn: VFS, fmt: str) -> tuple[int, int]:
        mul = 3 if "3" in fmt else 1
        w, h = vn.flags["thsize"].split("x")
        return int(w) * mul, int(h) * mul

    def get(self, ptop: str, rem: str, mtime: float, fmt: str) -> Optional[str]:
        histpath = self.asrv.vfs.histtab.get(ptop)
        if not histpath:
            self.log("no histpath for [{}]".format(ptop))
            return None

        tpath = thumb_path(histpath, rem, mtime, fmt, self.fmt_ffa)
        abspath = os.path.join(ptop, rem)
        cond = threading.Condition(self.mutex)
        do_conv = False
        with self.mutex:
            try:
                self.busy[tpath].append(cond)
                self.log("joined waiting room for %s" % (tpath,))
            except:
                thdir = os.path.dirname(tpath)
                bos.makedirs(os.path.join(thdir, "w"))

                inf_path = os.path.join(thdir, "dir.txt")
                if not bos.path.exists(inf_path):
                    with open(inf_path, "wb") as f:
                        f.write(afsenc(os.path.dirname(abspath)))

                self.busy[tpath] = [cond]
                do_conv = True

        if do_conv:
            allvols = list(self.asrv.vfs.all_vols.values())
            vn = next((x for x in allvols if x.realpath == ptop), None)
            if not vn:
                self.log("ptop [{}] not in {}".format(ptop, allvols), 3)
                vn = self.asrv.vfs.all_aps[0][1]

            self.q.put((abspath, tpath, fmt, vn))
            self.log("conv {} :{} \033[0m{}".format(tpath, fmt, abspath), c=6)

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

    def getcfg(self) -> dict[str, set[str]]:
        return {
            "thumbable": self.thumbable,
            "pil": self.fmt_pil,
            "vips": self.fmt_vips,
            "ffi": self.fmt_ffi,
            "ffv": self.fmt_ffv,
            "ffa": self.fmt_ffa,
        }

    def wait4ram(self, need: float, ttpath: str) -> None:
        ram = self.args.th_ram_max
        if need > ram * 0.99:
            t = "file too big; need %.2f GiB RAM, but --th-ram-max is only %.1f"
            raise Exception(t % (need, ram))

        while True:
            with self.mutex:
                used = sum([v for k, v in self.ram.items() if k != ttpath]) + need
                if used < ram:
                    # self.log("XXX self.ram: %s" % (self.ram,), 5)
                    self.ram[ttpath] = need
                    return
            with self.memcond:
                # self.log("at RAM limit; used %.2f GiB, need %.2f more" % (used-need, need), 1)
                self.memcond.wait(3)

    def worker(self) -> None:
        while not self.stopping:
            task = self.q.get()
            if not task:
                break

            abspath, tpath, fmt, vn = task
            ext = abspath.split(".")[-1].lower()
            png_ok = False
            funs = []

            if ext in self.args.au_unpk:
                ap_unpk = au_unpk(self.log, self.args.au_unpk, abspath, vn)
            else:
                ap_unpk = abspath

            if not bos.path.exists(tpath):
                for lib in self.args.th_dec:
                    if lib == "pil" and ext in self.fmt_pil:
                        funs.append(self.conv_pil)
                    elif lib == "vips" and ext in self.fmt_vips:
                        funs.append(self.conv_vips)
                    elif lib == "ff" and ext in self.fmt_ffi or ext in self.fmt_ffv:
                        funs.append(self.conv_ffmpeg)
                    elif lib == "ff" and ext in self.fmt_ffa:
                        if tpath.endswith(".opus") or tpath.endswith(".caf"):
                            funs.append(self.conv_opus)
                        elif tpath.endswith(".mp3"):
                            funs.append(self.conv_mp3)
                        elif tpath.endswith(".png"):
                            funs.append(self.conv_waves)
                            png_ok = True
                        else:
                            funs.append(self.conv_spec)

            tdir, tfn = os.path.split(tpath)
            ttpath = os.path.join(tdir, "w", tfn)
            try:
                wunlink(self.log, ttpath, vn.flags)
            except:
                pass

            for fun in funs:
                try:
                    if not png_ok and tpath.endswith(".png"):
                        raise Exception("png only allowed for waveforms")

                    fun(ap_unpk, ttpath, fmt, vn)
                    break
                except Exception as ex:
                    msg = "{} could not create thumbnail of {}\n{}"
                    msg = msg.format(fun.__name__, abspath, min_ex())
                    c: Union[str, int] = 1 if "<Signals.SIG" in msg else "90"
                    self.log(msg, c)
                    if getattr(ex, "returncode", 0) != 321:
                        if fun == funs[-1]:
                            with open(ttpath, "wb") as _:
                                pass
                    else:
                        # ffmpeg may spawn empty files on windows
                        try:
                            wunlink(self.log, ttpath, vn.flags)
                        except:
                            pass

            if abspath != ap_unpk:
                wunlink(self.log, ap_unpk, vn.flags)

            try:
                wrename(self.log, ttpath, tpath, vn.flags)
            except:
                pass

            with self.mutex:
                subs = self.busy[tpath]
                del self.busy[tpath]
                self.ram.pop(ttpath, None)

            for x in subs:
                with x:
                    x.notify_all()

            with self.memcond:
                self.memcond.notify_all()

        with self.mutex:
            self.nthr -= 1

    def fancy_pillow(self, im: "Image.Image", fmt: str, vn: VFS) -> "Image.Image":
        # exif_transpose is expensive (loads full image + unconditional copy)
        res = self.getres(vn, fmt)
        r = max(*res) * 2
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

        if "f" in fmt:
            im.thumbnail(res, resample=Image.LANCZOS)
        else:
            iw, ih = im.size
            dw, dh = res
            res = (min(iw, dw), min(ih, dh))
            im = ImageOps.fit(im, res, method=Image.LANCZOS)

        return im

    def conv_pil(self, abspath: str, tpath: str, fmt: str, vn: VFS) -> None:
        self.wait4ram(0.2, tpath)
        with Image.open(fsenc(abspath)) as im:
            try:
                im = self.fancy_pillow(im, fmt, vn)
            except Exception as ex:
                self.log("fancy_pillow {}".format(ex), "90")
                im.thumbnail(self.getres(vn, fmt))

            fmts = ["RGB", "L"]
            args = {"quality": 40}

            if tpath.endswith(".webp"):
                # quality 80 = pillow-default
                # quality 75 = ffmpeg-default
                # method 0 = pillow-default, fast
                # method 4 = ffmpeg-default
                # method 6 = max, slow
                fmts.extend(("RGBA", "LA"))
                args["method"] = 6
            else:
                # default q = 75
                args["progressive"] = True

            if im.mode not in fmts:
                # print("conv {}".format(im.mode))
                im = im.convert("RGB")

            im.save(tpath, **args)

    def conv_vips(self, abspath: str, tpath: str, fmt: str, vn: VFS) -> None:
        self.wait4ram(0.2, tpath)
        crops = ["centre", "none"]
        if "f" in fmt:
            crops = ["none"]

        w, h = self.getres(vn, fmt)
        kw = {"height": h, "size": "down", "intent": "relative"}

        for c in crops:
            try:
                kw["crop"] = c
                img = pyvips.Image.thumbnail(abspath, w, **kw)
                break
            except:
                if c == crops[-1]:
                    raise

        assert img  # type: ignore
        img.write_to_file(tpath, Q=40)

    def conv_ffmpeg(self, abspath: str, tpath: str, fmt: str, vn: VFS) -> None:
        self.wait4ram(0.2, tpath)
        ret, _ = ffprobe(abspath, int(vn.flags["convt"] / 2))
        if not ret:
            return

        ext = abspath.rsplit(".")[-1].lower()
        if ext in ["h264", "h265"] or ext in self.fmt_ffi:
            seek: list[bytes] = []
        else:
            dur = ret[".dur"][1] if ".dur" in ret else 4
            seek = [b"-ss", "{:.0f}".format(dur / 3).encode("utf-8")]

        scale = "scale={0}:{1}:force_original_aspect_ratio="
        if "f" in fmt:
            scale += "decrease,setsar=1:1"
        else:
            scale += "increase,crop={0}:{1},setsar=1:1"

        res = self.getres(vn, fmt)
        bscale = scale.format(*list(res)).encode("utf-8")
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
            b"-vf", bscale,
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
        self._run_ff(cmd, vn)

    def _run_ff(self, cmd: list[bytes], vn: VFS, oom: int = 400) -> None:
        # self.log((b" ".join(cmd)).decode("utf-8"))
        ret, _, serr = runcmd(cmd, timeout=vn.flags["convt"], nice=True, oom=oom)
        if not ret:
            return

        c: Union[str, int] = "90"
        t = "FFmpeg failed (probably a corrupt video file):\n"
        if (
            (not self.args.th_ff_jpg or time.time() - int(self.args.th_ff_jpg) < 60)
            and cmd[-1].lower().endswith(b".webp")
            and (
                "Error selecting an encoder" in serr
                or "Automatic encoder selection failed" in serr
                or "Default encoder for format webp" in serr
                or "Please choose an encoder manually" in serr
            )
        ):
            self.args.th_ff_jpg = time.time()
            t = "FFmpeg failed because it was compiled without libwebp; enabling --th-ff-jpg to force jpeg output:\n"
            ret = 321
            c = 1

        if (
            not self.args.th_ff_swr or time.time() - int(self.args.th_ff_swr) < 60
        ) and (
            "Requested resampling engine is unavailable" in serr
            or "output pad on Parsed_aresample_" in serr
        ):
            self.args.th_ff_swr = time.time()
            t = "FFmpeg failed because it was compiled without libsox; enabling --th-ff-swr to force swr resampling:\n"
            ret = 321
            c = 1

        lines = serr.strip("\n").split("\n")
        if len(lines) > 50:
            lines = lines[:25] + ["[...]"] + lines[-25:]

        txt = "\n".join(["ff: " + str(x) for x in lines])
        if len(txt) > 5000:
            txt = txt[:2500] + "...\nff: [...]\nff: ..." + txt[-2500:]

        self.log(t + txt, c=c)
        raise sp.CalledProcessError(ret, (cmd[0], b"...", cmd[-1]))

    def conv_waves(self, abspath: str, tpath: str, fmt: str, vn: VFS) -> None:
        ret, _ = ffprobe(abspath, int(vn.flags["convt"] / 2))
        if "ac" not in ret:
            raise Exception("not audio")

        # jt_versi.xm: 405M/839s
        dur = ret[".dur"][1] if ".dur" in ret else 300
        need = 0.2 + dur / 3000
        speedup = b""
        if need > self.args.th_ram_max * 0.7:
            self.log("waves too big (need %.2f GiB); trying to optimize" % (need,))
            need = 0.2 + dur / 4200  # only helps about this much...
            speedup = b"aresample=8000,"
        if need > self.args.th_ram_max * 0.96:
            raise Exception("file too big; cannot waves")

        self.wait4ram(need, tpath)

        flt = b"[0:a:0]" + speedup
        flt += (
            b"compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2"
            b",volume=2"
            b",showwavespic=s=2048x64:colors=white"
            b",convolution=1 1 1 1 1 1 1 1 1:1 1 1 1 1 1 1 1 1:1 1 1 1 1 1 1 1 1:1 -1 1 -1 5 -1 1 -1 1"  # idk what im doing but it looks ok
        )

        # fmt: off
        cmd = [
            b"ffmpeg",
            b"-nostdin",
            b"-v", b"error",
            b"-hide_banner",
            b"-i", fsenc(abspath),
            b"-filter_complex", flt,
            b"-frames:v", b"1",
        ]
        # fmt: on

        cmd += [fsenc(tpath)]
        self._run_ff(cmd, vn)

        if "pngquant" in vn.flags:
            wtpath = tpath + ".png"
            cmd = [
                b"pngquant",
                b"--strip",
                b"--nofs",
                b"--output",
                fsenc(wtpath),
                fsenc(tpath),
            ]
            ret = runcmd(cmd, timeout=vn.flags["convt"], nice=True, oom=400)[0]
            if ret:
                try:
                    wunlink(self.log, wtpath, vn.flags)
                except:
                    pass
            else:
                wrename(self.log, wtpath, tpath, vn.flags)

    def conv_spec(self, abspath: str, tpath: str, fmt: str, vn: VFS) -> None:
        ret, _ = ffprobe(abspath, int(vn.flags["convt"] / 2))
        if "ac" not in ret:
            raise Exception("not audio")

        # https://trac.ffmpeg.org/ticket/10797
        # expect 1 GiB every 600 seconds when duration is tricky;
        # simple filetypes are generally safer so let's special-case those
        safe = ("flac", "wav", "aif", "aiff", "opus")
        coeff = 1800 if abspath.split(".")[-1].lower() in safe else 600
        dur = ret[".dur"][1] if ".dur" in ret else 300
        need = 0.2 + dur / coeff
        self.wait4ram(need, tpath)

        fc = "[0:a:0]aresample=48000{},showspectrumpic=s="
        if "3" in fmt:
            fc += "1280x1024,crop=1420:1056:70:48[o]"
        else:
            fc += "640x512,crop=780:544:70:48[o]"

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
            b"-map", b"[o]",
            b"-frames:v", b"1",
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
        self._run_ff(cmd, vn)

    def conv_mp3(self, abspath: str, tpath: str, fmt: str, vn: VFS) -> None:
        quality = self.args.q_mp3.lower()
        if self.args.no_acode or not quality:
            raise Exception("disabled in server config")

        self.wait4ram(0.2, tpath)
        tags, rawtags = ffprobe(abspath, int(vn.flags["convt"] / 2))
        if "ac" not in tags:
            raise Exception("not audio")

        if quality.endswith("k"):
            qk = b"-b:a"
            qv = quality.encode("ascii")
        else:
            qk = b"-q:a"
            qv = quality[1:].encode("ascii")

        # extremely conservative choices for output format
        # (always 2ch 44k1) because if a device is old enough
        # to not support opus then it's probably also super picky

        # fmt: off
        cmd = [
            b"ffmpeg",
            b"-nostdin",
            b"-v", b"error",
            b"-hide_banner",
            b"-i", fsenc(abspath),
        ] + self.big_tags(rawtags) + [
            b"-map", b"0:a:0",
            b"-ar", b"44100",
            b"-ac", b"2",
            b"-c:a", b"libmp3lame",
            qk, qv,
            fsenc(tpath)
        ]
        # fmt: on
        self._run_ff(cmd, vn, oom=300)

    def conv_opus(self, abspath: str, tpath: str, fmt: str, vn: VFS) -> None:
        if self.args.no_acode or not self.args.q_opus:
            raise Exception("disabled in server config")

        self.wait4ram(0.2, tpath)
        tags, rawtags = ffprobe(abspath, int(vn.flags["convt"] / 2))
        if "ac" not in tags:
            raise Exception("not audio")

        try:
            dur = tags[".dur"][1]
        except:
            dur = 0

        src_opus = abspath.lower().endswith(".opus") or tags["ac"][1] == "opus"
        want_caf = tpath.endswith(".caf")
        tmp_opus = tpath
        if want_caf:
            tmp_opus = tpath + ".opus"
            try:
                wunlink(self.log, tmp_opus, vn.flags)
            except:
                pass

        caf_src = abspath if src_opus else tmp_opus
        bq = ("%dk" % (self.args.q_opus,)).encode("ascii")

        if not want_caf or not src_opus:
            # fmt: off
            cmd = [
                b"ffmpeg",
                b"-nostdin",
                b"-v", b"error",
                b"-hide_banner",
                b"-i", fsenc(abspath),
            ] + self.big_tags(rawtags) + [
                b"-map", b"0:a:0",
                b"-c:a", b"libopus",
                b"-b:a", bq,
                fsenc(tmp_opus)
            ]
            # fmt: on
            self._run_ff(cmd, vn, oom=300)

        # iOS fails to play some "insufficiently complex" files
        # (average file shorter than 8 seconds), so of course we
        # fix that by mixing in some inaudible pink noise :^)
        # 6.3 sec seems like the cutoff so lets do 7, and
        # 7 sec of psyqui-musou.opus @ 3:50 is 174 KiB
        if want_caf and (dur < 20 or bos.path.getsize(caf_src) < 256 * 1024):
            # fmt: off
            cmd = [
                b"ffmpeg",
                b"-nostdin",
                b"-v", b"error",
                b"-hide_banner",
                b"-i", fsenc(abspath),
                b"-filter_complex", b"anoisesrc=a=0.001:d=7:c=pink,asplit[l][r]; [l][r]amerge[s]; [0:a:0][s]amix",
                b"-map_metadata", b"-1",
                b"-ac", b"2",
                b"-c:a", b"libopus",
                b"-b:a", bq,
                b"-f", b"caf",
                fsenc(tpath)
            ]
            # fmt: on
            self._run_ff(cmd, vn, oom=300)

        elif want_caf:
            # simple remux should be safe
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
            self._run_ff(cmd, vn, oom=300)

        if tmp_opus != tpath:
            try:
                wunlink(self.log, tmp_opus, vn.flags)
            except:
                pass

    def big_tags(self, raw_tags: dict[str, list[str]]) -> list[bytes]:
        ret = []
        for k, vs in raw_tags.items():
            for v in vs:
                if len(str(v)) >= 1024:
                    bv = k.encode("utf-8", "replace")
                    ret += [b"-metadata", bv + b"="]
                    break
        return ret

    def poke(self, tdir: str) -> None:
        if not self.poke_cd.poke(tdir):
            return

        ts = int(time.time())
        try:
            for _ in range(4):
                bos.utime(tdir, (ts, ts))
                tdir = os.path.dirname(tdir)
        except:
            pass

    def cleaner(self) -> None:
        interval = self.args.th_clean
        while True:
            time.sleep(interval)
            ndirs = 0
            for vol, histpath in self.asrv.vfs.histtab.items():
                if histpath.startswith(vol):
                    self.log("\033[Jcln {}/\033[A".format(histpath))
                else:
                    self.log("\033[Jcln {} ({})/\033[A".format(histpath, vol))

                try:
                    ndirs += self.clean(histpath)
                except Exception as ex:
                    self.log("\033[Jcln err in %s: %r" % (histpath, ex), 3)

            self.log("\033[Jcln ok; rm {} dirs".format(ndirs))

    def clean(self, histpath: str) -> int:
        ret = 0
        for cat in ["th", "ac"]:
            top = os.path.join(histpath, cat)
            if not bos.path.isdir(top):
                continue

            ret += self._clean(cat, top)

        return ret

    def _clean(self, cat: str, thumbpath: str) -> int:
        # self.log("cln {}".format(thumbpath))
        exts = ["jpg", "webp", "png"] if cat == "th" else ["opus", "caf", "mp3"]
        maxage = getattr(self.args, cat + "_maxage")
        now = time.time()
        prev_b64 = None
        prev_fp = ""
        try:
            t1 = statdir(self.log_func, not self.args.no_scandir, False, thumbpath)
            ents = sorted(list(t1))
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
                        for k in self.busy:
                            if k.lower().replace("\\", "/").startswith(cmp):
                                safe = False
                                break

                        if safe:
                            ndirs += 1
                            self.log("rm -rf [{}]".format(fp))
                            shutil.rmtree(fp, ignore_errors=True)
                else:
                    ndirs += self._clean(cat, fp)

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

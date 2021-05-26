import os
import sys
import time
import shutil
import base64
import hashlib
import threading
import subprocess as sp

from .__init__ import PY2
from .util import fsenc, Queue, Cooldown
from .mtag import HAVE_FFMPEG, HAVE_FFPROBE, ffprobe


if not PY2:
    unicode = str


try:
    HAVE_PIL = True
    from PIL import Image

    try:
        HAVE_HEIF = True
        from pyheif_pillow_opener import register_heif_opener

        register_heif_opener()
    except:
        HAVE_HEIF = False
except:
    HAVE_PIL = False


# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
# ffmpeg -formats
FMT_PIL, FMT_FF = [
    {x: True for x in y.split(" ") if x}
    for y in [
        "bmp dib gif icns ico jpg jpeg jp2 jpx pcx png pbm pgm ppm pnm sgi tga tif tiff webp xbm dds xpm",
        "av1 asf avi flv m4v mkv mjpeg mjpg mpg mpeg mpg2 mpeg2 mov 3gp mp4 ts mpegts nut ogv ogm rm vob webm wmv",
    ]
]


THUMBABLE = {}

if HAVE_PIL:
    THUMBABLE.update(FMT_PIL)

if HAVE_FFMPEG and HAVE_FFPROBE:
    THUMBABLE.update(FMT_FF)


def thumb_path(ptop, rem, mtime):
    # base16 = 16 = 256
    # b64-lc = 38 = 1444
    # base64 = 64 = 4096
    try:
        rd, fn = rem.rsplit("/", 1)
    except:
        rd = ""
        fn = rem

    if rd:
        h = hashlib.sha512(fsenc(rd)).digest()[:24]
        b64 = base64.urlsafe_b64encode(h).decode("ascii")[:24]
        rd = "{}/{}/".format(b64[:2], b64[2:4]).lower() + b64
    else:
        rd = "top"

    # could keep original filenames but this is safer re pathlen
    h = hashlib.sha512(fsenc(fn)).digest()[:24]
    fn = base64.urlsafe_b64encode(h).decode("ascii")[:24]

    return "{}/.hist/th/{}/{}.{:x}.jpg".format(ptop, rd, fn, int(mtime))


class ThumbSrv(object):
    def __init__(self, hub, vols):
        self.hub = hub
        self.vols = [v.realpath for v in vols.values()]

        self.args = hub.args
        self.log_func = hub.log

        res = hub.args.thumbsz.split("x")
        self.res = tuple([int(x) for x in res])
        self.poke_cd = Cooldown(self.args.th_poke)

        self.mutex = threading.Lock()
        self.busy = {}
        self.stopping = False
        self.nthr = os.cpu_count() if hasattr(os, "cpu_count") else 4
        self.q = Queue(self.nthr * 4)
        for _ in range(self.nthr):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()

        if not HAVE_PIL:
            msg = "need Pillow to create thumbnails so please run this:\n  {} -m pip install --user Pillow"
            self.log(msg.format(os.path.basename(sys.executable)), c=1)

        if not self.args.no_vthumb and (not HAVE_FFMPEG or not HAVE_FFPROBE):
            missing = []
            if not HAVE_FFMPEG:
                missing.append("ffmpeg")

            if not HAVE_FFPROBE:
                missing.append("ffprobe")

            msg = "cannot create video thumbnails since some of the required programs are not available: "
            msg += ", ".join(missing)
            self.log(msg, c=1)

        t = threading.Thread(target=self.cleaner)
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

    def get(self, ptop, rem, mtime):
        tpath = thumb_path(ptop, rem, mtime)
        abspath = os.path.join(ptop, rem)
        cond = threading.Condition()
        with self.mutex:
            try:
                self.busy[tpath].append(cond)
                self.log("wait {}".format(tpath))
            except:
                thdir = os.path.dirname(tpath)
                try:
                    os.makedirs(thdir)
                except:
                    pass

                inf_path = os.path.join(thdir, "dir.txt")
                if not os.path.exists(inf_path):
                    with open(inf_path, "wb") as f:
                        f.write(fsenc(os.path.dirname(abspath)))

                self.busy[tpath] = [cond]
                self.q.put([abspath, tpath])
                self.log("conv {}".format(tpath))

        while not self.stopping:
            with self.mutex:
                if tpath not in self.busy:
                    break

            with cond:
                cond.wait()

        try:
            st = os.stat(tpath)
            if st.st_size:
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
            if not os.path.exists(tpath):
                if ext in FMT_PIL:
                    fun = self.conv_pil
                elif ext in FMT_FF:
                    fun = self.conv_ffmpeg

            if fun:
                try:
                    fun(abspath, tpath)
                except Exception as ex:
                    msg = "{} failed on {}\n  {!r}"
                    self.log(msg.format(fun.__name__, abspath, ex), 3)
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

    def conv_pil(self, abspath, tpath):
        with Image.open(abspath) as im:
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")

            im.thumbnail(self.res)
            im.save(tpath)

    def conv_ffmpeg(self, abspath, tpath):
        ret, _ = run_ffprobe(abspath)

        dur = ret[".dur"][1]
        seek = "{:.0f}".format(dur / 3)
        scale = "scale=w={}:h={}:force_original_aspect_ratio=decrease"
        scale = scale.format(*list(self.res)).encode("utf-8")
        cmd = [
            b"ffmpeg",
            b"-nostdin",
            b"-hide_banner",
            b"-ss",
            seek,
            b"-i",
            fsenc(abspath),
            b"-vf",
            scale,
            b"-vframes",
            b"1",
            b"-q:v",
            b"5",
            fsenc(tpath),
        ]
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        r = p.communicate()

    def poke(self, tdir):
        if not self.poke_cd.poke(tdir):
            return

        ts = int(time.time())
        try:
            p1 = os.path.dirname(tdir)
            p2 = os.path.dirname(p1)
            for dp in [tdir, p1, p2]:
                os.utime(fsenc(dp), (ts, ts))
        except:
            pass

    def cleaner(self):
        interval = self.args.th_clean
        while True:
            time.sleep(interval)
            for vol in self.vols:
                vol += "/.hist/th"
                self.log("cln {}/".format(vol))
                self.clean(vol)

            self.log("cln ok")

    def clean(self, vol):
        # self.log("cln {}".format(vol))
        maxage = self.args.th_maxage
        now = time.time()
        prev_b64 = None
        prev_fp = None
        try:
            ents = os.listdir(vol)
        except:
            return

        for f in sorted(ents):
            fp = os.path.join(vol, f)
            cmp = fp.lower().replace("\\", "/")

            # "top" or b64 prefix/full (a folder)
            if len(f) <= 3 or len(f) == 24:
                age = now - os.path.getmtime(fp)
                if age > maxage:
                    with self.mutex:
                        safe = True
                        for k in self.busy.keys():
                            if k.lower().replace("\\", "/").startswith(cmp):
                                safe = False
                                break

                        if safe:
                            self.log("rm -rf [{}]".format(fp))
                            shutil.rmtree(fp, ignore_errors=True)
                else:
                    self.clean(fp)
                continue

            # thumb file
            try:
                b64, ts, ext = f.split(".")
                if len(b64) != 24 or len(ts) != 8 or ext != "jpg":
                    raise Exception()

                ts = int(ts, 16)
            except:
                if f != "dir.txt":
                    self.log("foreign file in thumbs dir: [{}]".format(fp), 1)

                continue

            if b64 == prev_b64:
                self.log("rm replaced [{}]".format(fp))
                os.unlink(prev_fp)

            prev_b64 = b64
            prev_fp = fp

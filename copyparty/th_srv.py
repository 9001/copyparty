import os
import sys
import base64
import hashlib
import threading
import subprocess as sp

from .__init__ import PY2
from .util import fsenc, Queue
from .mtag import HAVE_FFMPEG, HAVE_FFPROBE, parse_ffprobe


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
    def __init__(self, hub):
        self.hub = hub
        self.args = hub.args
        self.log_func = hub.log

        res = hub.args.thumbsz.split("x")
        self.res = tuple([int(x) for x in res])

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
        cmd = [b"ffprobe", b"-hide_banner", b"--", fsenc(abspath)]
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        r = p.communicate()
        txt = r[1].decode("utf-8", "replace")
        ret, _ = parse_ffprobe(txt, self.log, False)

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

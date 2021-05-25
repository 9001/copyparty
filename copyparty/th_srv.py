import os
import base64
import hashlib
import threading

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

from .util import fsenc, Queue

# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
FMT_PIL = "bmp dib gif icns ico jpg jpeg jp2 jpx pcx png pbm pgm ppm pnm sgi tga tif tiff webp xbm dds xpm"
FMT_PIL = {x: True for x in FMT_PIL.split(" ") if x}
THUMBABLE = FMT_PIL


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
        self.log_func = hub.log

        self.mutex = threading.Lock()
        self.busy = {}
        self.stopping = False
        self.nthr = os.cpu_count() if hasattr(os, "cpu_count") else 4
        self.q = Queue(self.nthr * 4)
        for _ in range(self.nthr):
            t = threading.Thread(target=self.worker)
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
                self.log("conv {}".format(tpath))
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
                self.log("CONV {}".format(tpath))

        while not self.stopping:
            with self.mutex:
                if tpath not in self.busy:
                    break

            with cond:
                cond.wait()

        if not os.path.exists(tpath):
            return None

        return tpath

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

            if fun:
                fun(abspath, tpath)

            with self.mutex:
                subs = self.busy[tpath]
                del self.busy[tpath]

            for x in subs:
                with x:
                    x.notify_all()

        with self.mutex:
            self.nthr -= 1

    def conv_pil(self, abspath, tpath):
        try:
            with Image.open(abspath) as im:
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")

                im.thumbnail((256, 256))
                im.save(tpath)
        except:
            pass
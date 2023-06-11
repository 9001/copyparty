import calendar
import errno
import filecmp
import json
import os
import shutil
import time

from .util import Netdev, runcmd

HAVE_CFSSL = True


def ensure_cert(log: "RootLogger", args) -> None:
    """
    the default cert (and the entire TLS support) is only here to enable the
    crypto.subtle javascript API, which is necessary due to the webkit guys
    being massive memers (https://www.chromium.org/blink/webcrypto)

    i feel awful about this and so should they
    """
    cert_insec = os.path.join(args.E.mod, "res/insecure.pem")
    cert_appdata = os.path.join(args.E.cfg, "cert.pem")
    if not os.path.isfile(args.cert):
        if cert_appdata != args.cert:
            raise Exception("certificate file does not exist: " + args.cert)

        shutil.copy(cert_insec, args.cert)

    with open(args.cert, "rb") as f:
        buf = f.read()
        o1 = buf.find(b" PRIVATE KEY-")
        o2 = buf.find(b" CERTIFICATE-")
        m = "unsupported certificate format: "
        if o1 < 0:
            raise Exception(m + "no private key inside pem")
        if o2 < 0:
            raise Exception(m + "no server certificate inside pem")
        if o1 > o2:
            raise Exception(m + "private key must appear before server certificate")

    try:
        if filecmp.cmp(args.cert, cert_insec):
            t = "using default TLS certificate; https will be insecure:\033[36m {}"
            log("cert", t.format(args.cert), 3)
    except:
        pass

    # speaking of the default cert,
    # printf 'NO\n.\n.\n.\n.\ncopyparty-insecure\n.\n' | faketime '2000-01-01 00:00:00' openssl req -x509 -sha256 -newkey rsa:2048 -keyout insecure.pem -out insecure.pem -days $((($(printf %d 0x7fffffff)-$(date +%s --date=2000-01-01T00:00:00Z))/(60*60*24))) -nodes && ls -al insecure.pem && openssl x509 -in insecure.pem -text -noout


def _read_crt(args, fn):
    try:
        if not os.path.exists(os.path.join(args.crt_dir, fn)):
            return 0, {}

        acmd = ["cfssl-certinfo", "-cert", fn]
        rc, so, se = runcmd(acmd, cwd=args.crt_dir)
        if rc:
            return 0, {}

        inf = json.loads(so)
        zs = inf["not_after"]
        expiry = calendar.timegm(time.strptime(zs, "%Y-%m-%dT%H:%M:%SZ"))
        return expiry, inf
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            raise
        return 0, {}
    except:
        return 0, {}


def _gen_ca(log: "RootLogger", args):
    expiry = _read_crt(args, "ca.pem")[0]
    if time.time() + args.crt_cdays * 60 * 60 * 24 * 0.1 < expiry:
        return

    backdate = "{}m".format(int(args.crt_back * 60))
    expiry = "{}m".format(int(args.crt_cdays * 60 * 24))
    cn = args.crt_cnc.replace("--crt-cn", args.crt_cn)
    algo, ksz = args.crt_alg.split("-")
    req = {
        "CN": cn,
        "CA": {"backdate": backdate, "expiry": expiry, "pathlen": 0},
        "key": {"algo": algo, "size": int(ksz)},
        "names": [{"O": cn}],
    }
    sin = json.dumps(req).encode("utf-8")
    log("cert", "creating new ca ...", 6)

    cmd = "cfssl gencert -initca -"
    rc, so, se = runcmd(cmd.split(), 30, sin=sin)
    if rc:
        raise Exception("failed to create ca-cert: {}, {}".format(rc, se), 3)

    cmd = "cfssljson -bare ca"
    sin = so.encode("utf-8")
    rc, so, se = runcmd(cmd.split(), 10, sin=sin, cwd=args.crt_dir)
    if rc:
        raise Exception("failed to translate ca-cert: {}, {}".format(rc, se), 3)

    bname = os.path.join(args.crt_dir, "ca")
    os.rename(bname + "-key.pem", bname + ".key")
    os.unlink(bname + ".csr")

    log("cert", "new ca OK", 2)


def _gen_srv(log: "RootLogger", args, netdevs: dict[str, Netdev]):
    names = args.crt_ns.split(",") if args.crt_ns else []
    if not args.crt_exact:
        for n in names[:]:
            names.append("*.{}".format(n))
    if not args.crt_noip:
        for ip in netdevs.keys():
            names.append(ip.split("/")[0])
    if args.crt_nolo:
        names = [x for x in names if x not in ("localhost", "127.0.0.1", "::1")]
    if not names:
        names = ["127.0.0.1"]
    if "127.0.0.1" in names or "::1" in names:
        names.append("localhost")
    names = list({x: 1 for x in names}.keys())

    try:
        expiry, inf = _read_crt(args, "srv.pem")
        expired = time.time() + args.crt_sdays * 60 * 60 * 24 * 0.1 > expiry
        cert_insec = os.path.join(args.E.mod, "res/insecure.pem")
        for n in names:
            if n not in inf["sans"]:
                raise Exception("does not have {}".format(n))
        if expired:
            raise Exception("old server-cert has expired")
        if not filecmp.cmp(args.cert, cert_insec):
            return
    except Exception as ex:
        log("cert", "will create new server-cert; {}".format(ex))

    log("cert", "creating server-cert ...", 6)

    backdate = "{}m".format(int(args.crt_back * 60))
    expiry = "{}m".format(int(args.crt_sdays * 60 * 24))
    cfg = {
        "signing": {
            "default": {
                "backdate": backdate,
                "expiry": expiry,
                "usages": ["signing", "key encipherment", "server auth"],
            }
        }
    }
    with open(os.path.join(args.crt_dir, "cfssl.json"), "wb") as f:
        f.write(json.dumps(cfg).encode("utf-8"))

    cn = args.crt_cns.replace("--crt-cn", args.crt_cn)
    algo, ksz = args.crt_alg.split("-")
    req = {
        "key": {"algo": algo, "size": int(ksz)},
        "names": [{"O": cn}],
    }
    sin = json.dumps(req).encode("utf-8")

    cmd = "cfssl gencert -config=cfssl.json -ca ca.pem -ca-key ca.key -profile=www"
    acmd = cmd.split() + ["-hostname=" + ",".join(names), "-"]
    rc, so, se = runcmd(acmd, 30, sin=sin, cwd=args.crt_dir)
    if rc:
        raise Exception("failed to create cert: {}, {}".format(rc, se))

    cmd = "cfssljson -bare srv"
    sin = so.encode("utf-8")
    rc, so, se = runcmd(cmd.split(), 10, sin=sin, cwd=args.crt_dir)
    if rc:
        raise Exception("failed to translate cert: {}, {}".format(rc, se))

    bname = os.path.join(args.crt_dir, "srv")
    os.rename(bname + "-key.pem", bname + ".key")
    os.unlink(bname + ".csr")

    with open(os.path.join(args.crt_dir, "ca.pem"), "rb") as f:
        ca = f.read()

    with open(bname + ".key", "rb") as f:
        skey = f.read()

    with open(bname + ".pem", "rb") as f:
        scrt = f.read()

    with open(args.cert, "wb") as f:
        f.write(skey + scrt + ca)

    log("cert", "new server-cert OK", 2)


def gencert(log: "RootLogger", args, netdevs: dict[str, Netdev]):
    global HAVE_CFSSL

    if args.http_only:
        return

    if args.no_crt or not HAVE_CFSSL:
        ensure_cert(log, args)
        return

    try:
        _gen_ca(log, args)
        _gen_srv(log, args, netdevs)
    except Exception as ex:
        HAVE_CFSSL = False
        log("cert", "could not create TLS certificates: {}".format(ex), 3)
        if getattr(ex, "errno", 0) == errno.ENOENT:
            t = "install cfssl if you want to fix this; https://github.com/cloudflare/cfssl/releases/latest"
            log("cert", t, 6)

        ensure_cert(log, args)

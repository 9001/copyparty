# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: grants, an owner gives a named account access to one of their
# folders, mounted at /<grants>/<owner>/<name>; see FORK.md and docs/adr/0001

import hashlib
import json
import os
import time

from .__init__ import unicode
from .fork_harden import harden_nodes, has_dot_part, http_refused
from .fork_util import grants_top
from .util import Pebkac, ub64enc, undot, vjoin

try:
    import sqlite3
except:
    sqlite3 = None  # type: ignore

if True:  # pylint: disable=using-constant-test
    from typing import TYPE_CHECKING, Any, Optional

    if TYPE_CHECKING:
        from .authsrv import VFS, AuthSrv

GRANTS_DB_VER = 1

_SCHEMA = [
    r"create table kv (k text, v int)",
    r"create table gr (id integer primary key autoincrement, un text, rcpt text, vp text, name text, pr text, t0 int, t1 int)",
    # owner, recipient, source vpath, mount name, rights, created, expires (0 = never)
    r"insert into kv values ('sver', %d)" % (GRANTS_DB_VER,),
]


class GrantStore(object):
    """the grants database (--grants-db); its own file and schema version,
    so upstream's shares-db upgrades never collide with it"""

    def __init__(self, path: str) -> None:
        self.path = path

    def _open(self, create: bool) -> Optional["sqlite3.Connection"]:
        if not sqlite3:
            raise Pebkac(500, "sqlite3 not found on server; grants are disabled")

        if not create and not os.path.exists(self.path):
            return None

        db = sqlite3.connect(self.path, timeout=2)
        try:
            sver = db.execute("select v from kv where k='sver'").fetchall()[0][0]
        except:
            sver = 0

        if sver > GRANTS_DB_VER:
            db.close()
            t = "this version of copyparty only understands grants-db v%d and older; the db [%s] is v%d"
            raise Exception(t % (GRANTS_DB_VER, self.path, sver))

        if not sver:
            if not create:
                db.close()
                return None
            for q in _SCHEMA:
                db.execute(q)
            db.commit()

        return db

    def create(
        self, owner: str, rcpt: str, vp: str, name: str, pr: str, t1: int
    ) -> int:
        """the new grant's id, or 0 if the owner already gave this
        recipient a grant by that name (expired ones too, since an owner
        can extend those back to life)"""
        db = self._open(True)
        assert db  # !rm
        try:
            q = "insert into gr (un, rcpt, vp, name, pr, t0, t1) select ?,?,?,?,?,?,?"
            q += " where not exists (select 1 from gr where un = ? and rcpt = ? and name = ?)"
            zt = (owner, rcpt, vp, name, pr, int(time.time()), t1, owner, rcpt, name)
            cur = db.execute(q, zt)
            db.commit()
            return cur.lastrowid if cur.rowcount == 1 else 0
        finally:
            db.close()

    def live(self, now: float) -> list[tuple[Any, ...]]:
        """grants that haven't expired, oldest first"""
        db = self._open(False)
        if not db:
            return []
        try:
            q = "select id, un, rcpt, vp, name, pr from gr where t1 = 0 or t1 > ? order by id"
            return db.execute(q, (now,)).fetchall()
        finally:
            db.close()


def share_pw_accounts(args: Any) -> set[str]:
    """the made-up accounts share link passwords log in as, which anyone
    with that password can use; AuthSrv._reload puts them in `acct` named
    from a hash of the stored password, before it strips every password,
    so the names can only be worked out from the share link database"""
    if not args.shr or not sqlite3 or not os.path.exists(args.shr_db):
        return set()
    db = sqlite3.connect(args.shr_db, timeout=2)
    try:
        rows = db.execute("select pw from sh where pw != ''").fetchall()
    except:
        return set()
    finally:
        db.close()
    ret = set()
    for (pw,) in rows:
        zb = hashlib.sha512(pw.encode("utf-8")).digest()
        ret.add("s_%s" % (ub64enc(zb)[4:16].decode("ascii"),))
    return ret


def is_account(acct: dict[str, str], pseudo: set[str], un: str) -> bool:
    """True for an account from the config; `pseudo` = share_pw_accounts"""
    return un in acct and un not in pseudo


def _safe_name(name: str) -> bool:
    """one path segment that is not hidden, nor . or .."""
    return (
        0 < len(name) <= 255
        and not name.startswith(".")
        and name == name.strip()
        and not any(c in "/\\" or ord(c) < 32 or ord(c) == 127 for c in name)
    )


def _store(args: Any) -> GrantStore:
    return GrantStore(args.grants_db)


def _uaxs(vn: "VFS", unames: list[str]) -> None:
    za = vn.axs
    vn.uaxs = {
        un: (
            un in za.uread,
            un in za.uwrite,
            un in za.umove,
            un in za.udel,
            un in za.uget,
            un in za.upget,
            un in za.uhtml,
            un in za.uadmin,
            un in za.udot,
        )
        for un in unames
    }


# like a share link, minus what makes no sense for a mount of someone else's folder
_DROP_FLAGS = "assert_root daw dk dks dky dots e2ds e2dsa e2ts e2tsr fk fka landmark opds rss scan th_pregen"
_EMPTY_FLAGS = "srch_excl srch_re_dots srch_re_nodot th_coversd th_coversl"


def mount_grants(asrv: "AuthSrv", vfs: "VFS", acct: dict[str, str]) -> None:
    """reload: add the /<grants> virtual tree with one volume per live grant.
    Called at the end of AuthSrv._reload, once every volume and share link
    has its final flags. Each grant is resolved as its owner with exactly
    the granted rights (the check share links use), so it only works while
    the owner still holds those rights.

    alice can grant bob a "proj" and carol a different "proj", so each
    recipient gets a tree of their own, and the root's path lookup sends
    /<grants>/... to the asking account's tree (_route). The tree under the
    root itself only has folders with no path on disk, for listings"""
    from .authsrv import AXS, VFS

    args = asrv.args
    top = grants_top(args)
    if not top:
        return

    if "/" in top:
        t = "invalid config: --grants must be the name of a virtual toplevel folder, for example /shared"
        raise Exception(t)
    if top in vfs.nodes:
        t = "invalid config: a volume is overlapping with the --grants global-option (/%s)"
        raise Exception(t % (top,))

    def folder(parent: Optional["VFS"], name: str) -> "VFS":
        """a grants folder with no path on disk (/<grants>, /<grants>/<owner>)"""
        if parent and name in parent.nodes:
            return parent.nodes[name]
        vp = vjoin(parent.vpath, name) if parent else name
        flags = parent.flags.copy() if parent else vfs._copy_flags(name)
        vn = VFS(asrv.log_func, "", vp, vp, AXS(), flags)
        vn.fork_grant_dir = True  # type: ignore
        if parent:
            parent.nodes[name] = vn
        virt.append(vn)
        return vn

    log = asrv.log
    virt: list["VFS"] = []
    grants: list["VFS"] = []
    trees: dict[str, "VFS"] = {}  # recipient: their /<grants>
    aread: dict[str, list[str]] = {}  # recipient: vpaths of their grants
    pub = folder(None, top)
    pseudo = share_pw_accounts(args)
    for gid, un, rcpt, vp, name, pr in _store(args).live(time.time()):
        desc = "grant %d by [%s] to [%s] of [/%s] (%s)" % (gid, un, rcpt, vp, pr)
        if not is_account(acct, pseudo, un) or not is_account(acct, pseudo, rcpt):
            log("skipping %s; not an account" % (desc,), 3)
            continue

        if has_dot_part(vp):
            log("skipping %s; a hidden folder is never granted" % (desc,), 3)
            continue

        try:
            s_vfs, s_rem = vfs.get(vp, un, "r" in pr, "w" in pr)
        except Exception as ex:
            log("suspended %s; the owner lacks those rights: %r" % (desc, ex), 3)
            continue

        if not os.path.isdir(s_vfs.canonical(s_rem)):
            log("broken %s; the source folder is gone" % (desc,), 3)
            continue

        if rcpt not in trees:
            trees[rcpt] = folder(None, top)
        ovn = folder(trees[rcpt], un)
        if name in ovn.nodes:
            log("skipping %s; the recipient already has a grant by that name" % (desc,), 3)
            continue

        gvn = _grant_vol(asrv, vfs, ovn, name, s_vfs, s_rem, un, pr)
        _add_rcpt(gvn.axs, rcpt, pr)
        ovn.nodes[name] = gvn
        grants.append(gvn)
        aread.setdefault(rcpt, []).append(gvn.vpath)

        # the folders above it, and the root's copy, list only for recipients
        povn = folder(pub, un)
        for vn in (trees[rcpt], ovn, pub, povn, folder(povn, name)):
            vn.axs.uread.add(rcpt)
        log("mounted %s at [/%s]" % (desc, gvn.vpath))

    if not grants:
        return

    unames = ["*"] + sorted(acct)
    for vn in virt + grants:
        _uaxs(vn, unames)
        vn.root = vfs
        if vn in virt:
            vn.js_ls = vfs.js_ls
            vn.js_htm = vfs.js_htm
            vn.md_htm = vfs.md_htm

    vfs.nodes[top] = pub
    if vfs.lnodes is not None:
        vfs.lnodes[top.casefold().encode("ascii", "ignore")] = pub

    # by vpath, for tx_ls_vols and the active-downloads list: the root's
    # copy, which is the same for every recipient
    for povn in pub.nodes.values():
        for vn in povn.nodes.values():
            vfs.all_nodes[vn.vpath] = vn
    vfs.fork_grant_aread = aread  # type: ignore

    # grants always refuse dot names and listing names, whatever --harden says
    harden_nodes(args, virt + grants, grants)
    _route(vfs, top, trees)


def _route(vfs: "VFS", top: str, trees: dict[str, "VFS"]) -> None:
    """make the root's path lookups (VFS.get, VFS._get which httpcli.run
    uses, and VFS.can_access behind the rights passed to event hooks)
    resolve /<top>/... in the asking account's own grants tree"""
    pre = top + "/"

    def routed(name: str) -> Any:
        fallback = getattr(vfs, name)

        def lookup(vpath: str, uname: str, *a: Any, **ka: Any) -> Any:
            tree = trees.get(uname)
            if tree:
                cvp = undot(vpath)
                if cvp == top or cvp.startswith(pre):
                    return getattr(tree, name)(cvp[len(pre) :], uname, *a, **ka)
            return fallback(vpath, uname, *a, **ka)

        return lookup

    vfs.get = routed("get")
    vfs._get = routed("_get")  # type: ignore
    vfs.can_access = routed("can_access")  # type: ignore


def _add_rcpt(axs: Any, rcpt: str, pr: str) -> None:
    axs.uread.add(rcpt)
    axs.uget.add(rcpt)
    if "w" in pr:
        axs.uwrite.add(rcpt)


def _grant_vol(
    asrv: "AuthSrv",
    vfs: "VFS",
    ovn: "VFS",
    name: str,
    s_vfs: "VFS",
    s_rem: str,
    owner: str,
    pr: str,
) -> "VFS":
    """one grant's volume; mirrors how AuthSrv._reload maps a share link"""
    from .authsrv import AXS, VFS

    vp = vjoin(ovn.vpath, name)
    gvn = VFS(asrv.log_func, "", vp, vp, AXS(), {})
    gvn.fork_grant = True  # type: ignore
    gvn.fork_grant_pr = pr  # type: ignore
    gvn.shr_owner = owner
    gvn.shr_src = (s_vfs, s_rem)
    gvn.realpath = s_vfs.canonical(s_rem)
    gvn.get_dbv = gvn._get_share_src
    gvn.ls = gvn._ls
    gvn.canonical = gvn._canonical
    gvn.dcanonical = gvn._dcanonical

    o_vn, _ = gvn._get_share_src("")
    gvn.lim = o_vn.lim
    gvn.flags = o_vn.flags.copy()
    gvn.dbpath = o_vn.dbpath
    gvn.histpath = o_vn.histpath
    gvn.js_ls = o_vn.js_ls
    gvn.js_htm = o_vn.js_htm
    gvn.md_htm = o_vn.md_htm
    for zs in _DROP_FLAGS.split():
        gvn.flags.pop(zs, None)
    for zs in _EMPTY_FLAGS.split():
        gvn.flags[zs] = []
    gvn.flags["shr_who"] = "no"  # no share links of a grant
    gvn.flags["grant_who"] = "no"  # nor grants

    # the grant appears in every abspath it provides (for chk_ap / xvol)
    ap = gvn.realpath
    if not ap.endswith(os.sep):
        ap += os.sep
    gvn.shr_all_aps = [(x, y[:]) for x, y in vfs.all_aps]
    exact = False
    for ap2, vns in gvn.shr_all_aps:
        if ap == ap2:
            exact = True
        if ap2.startswith(ap):
            try:
                vp2 = vjoin(s_rem, ap2[len(ap) :])
                vn2, _ = s_vfs.get(vp2, "*", False, False)
                if vn2 == s_vfs or vn2.dbv == s_vfs:
                    vns.append(gvn)
            except:
                pass
    if not exact:
        gvn.shr_all_aps.append((ap, [gvn]))
    gvn.shr_all_aps.sort(key=lambda x: len(x[0]), reverse=True)

    # never show the source's .hist, nor volumes mounted inside it
    if "show_hist" not in gvn.flags:
        gvn.nodes[".hist"] = VFS(asrv.log_func, "", "", "", AXS(), asrv.vf0())
    if not s_rem:
        for zs in s_vfs.nodes.keys():
            gvn.nodes[zs] = VFS(asrv.log_func, "", "", "", AXS(), asrv.vf0())

    return gvn


def http_request(cli: Any) -> bool:
    """httpcli.run, once the request's volume is known; True = reply 404"""
    if http_refused(cli):
        return True

    # upstream lists a folder without a path on disk with tx_ls_vols, from
    # the account's readable volumes (rvol). Grants stay out of the global
    # list, which search also reads, so add them for this listing only
    vn = cli.vn
    if cli.mode not in ("GET", "HEAD") or vn.realpath:
        return False
    is_dir = getattr(vn, "fork_grant_dir", False)
    if not is_dir and vn.vpath:
        return False
    zsl = getattr(cli.asrv.vfs, "fork_grant_aread", {}).get(cli.uname)
    if not zsl:
        return False
    cli.rvol = cli.rvol + zsl
    if is_dir:
        # take the listing path instead of tx_browser, which needs a real folder
        cli.can_read = cli.can_write = cli.can_get = False
    return False


# the rights a grant can give, by what the create request names them;
# move, delete and admin are never possible through a grant
_RIGHTS = {("read",): "r", ("read", "write"): "rw"}


def _rights(perms: Any) -> str:
    try:
        assert isinstance(perms, list)
        return _RIGHTS[tuple(sorted(set(perms)))]
    except:
        raise Pebkac(400, "a grant is either read-only (read) or read + upload (read, write)")


def _may_grant(vn: "VFS", uname: str) -> bool:
    """the grant_who volflag (no / a / auth, default auth); like shr_who,
    but separate, so an admin can allow one and forbid the other"""
    zs = vn.flags.get("grant_who", "auth")
    if zs == "auth":
        return uname != "*"
    if zs == "a":
        return uname in vn.axs.uadmin
    return False  # "no", or a typo: fail closed


def _under(vp: str, top: str) -> bool:
    return bool(top) and (vp == top or vp.startswith(top + "/"))


def handle_grant(cli: Any, req: dict[str, Any]) -> bool:
    """POST ?grant (json): {vp, rcpt, name, perms}; creates a grant and reloads"""
    args = cli.args
    if not grants_top(args):
        raise Pebkac(400, "grants are disabled in the server config")

    uname = cli.uname
    if uname == "*":
        raise Pebkac(401, "you must be logged in to create a grant")

    # one folder; share links take a list of paths and a "files" selection
    vp = req.get("vp") or ""
    if not isinstance(vp, (str, unicode)) or req.get("files"):
        raise Pebkac(400, "only folders can be granted, one at a time")

    # "%s" % x, not str(x): a non-ascii name would fail str() on python2
    vp = ("%s" % (vp,)).strip("/")
    rcpt = "%s" % (req.get("rcpt") or "",)
    name = "%s" % (req.get("name") or "",)
    pr = _rights(req.get("perms"))

    if cli.is_vproxied and (vp == args.R or vp.startswith(args.RS)):
        vp = vp[len(args.RS) :]
    vp = undot(vp)

    top = grants_top(args)
    if _under(vp, top):
        raise Pebkac(400, "a granted folder cannot be granted on")
    if args.shr and _under(vp, args.shr1.strip("/")):
        raise Pebkac(400, "a folder inside a share link cannot be granted")
    if has_dot_part(vp):
        raise Pebkac(400, "hidden folders (a name starting with a dot) cannot be granted")

    try:
        vn, rem = cli.asrv.vfs.get(vp, uname, True, "w" in pr)
    except:
        raise Pebkac(400, "you dont have all the perms you tried to grant")

    if vn.shr_src:  # any other path to a share link or grant volume
        raise Pebkac(400, "a folder inside a share link or a granted folder cannot be granted")

    if not _may_grant(vn, uname):
        raise Pebkac(400, "you dont have perms to create grants from this volume")

    if not os.path.isdir(vn.canonical(rem)):
        raise Pebkac(400, "only folders can be granted")

    if rcpt in ("*", "@acct"):
        raise Pebkac(400, "a grant cannot go to every account; pick an account")
    if rcpt == uname:
        raise Pebkac(400, "you cannot grant a folder to yourself")
    if not is_account(cli.asrv.acct, share_pw_accounts(args), rcpt):
        raise Pebkac(400, "no such recipient: %r" % (rcpt,))

    if not _safe_name(name):
        t = "the name must be one folder name: not starting with a dot, no slashes or control characters, at most 255 characters"
        raise Pebkac(400, t)

    gid = _store(args).create(uname, rcpt, vp, name, pr, 0)
    if not gid:
        t = "you already gave %r a grant named %r; pick another name"
        raise Pebkac(400, t % (rcpt, name))
    cli.log("created grant %d by [%s] to [%s] of [/%s] (%s)" % (gid, uname, rcpt, vp, pr))

    cli.conn.hsrv.broker.ask("reload", False, True).get()
    zs = "/%s/%s/%s/" % (top, uname, name)
    cli.reply(json.dumps({"id": gid, "vp": zs}).encode("utf-8"), 201, mime="application/json")
    return True

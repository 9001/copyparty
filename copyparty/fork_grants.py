# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: grants, an owner gives a named account or a config group
# access to one of their folders, mounted at /<grants>/<owner>/<name>; see FORK.md and docs/adr/0001

import hashlib
import json
import os
import stat
import threading
import time

from .__init__ import RES, unicode
from .fork_harden import harden_nodes, has_dot_part, http_refused, is_grant
from .fork_util import grants_top
from .bos import bos
from .util import Daemon, Pebkac, absreal, quotep, ub64enc, undot, vjoin

try:
    import sqlite3
except:
    sqlite3 = None  # type: ignore

if True:  # pylint: disable=using-constant-test
    from typing import TYPE_CHECKING, Any, Optional

    if TYPE_CHECKING:
        from .authsrv import VFS, AuthSrv
        from .svchub import SvcHub

# the grants page and the grant button; registered here so upstream's list in __init__ stays as it is
RES.update(("web/grants.html", "web/grants.js", "web/grantbtn.js"))

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

    def rcpts(self, owner: str, name: str) -> list[str]:
        """who the owner gave a grant by this name to, expired ones too"""
        db = self._open(False)
        if not db:
            return []
        try:
            q = "select rcpt from gr where un = ? and name = ?"
            return [x[0] for x in db.execute(q, (owner, name))]
        finally:
            db.close()

    def rows(self) -> list[tuple[Any, ...]]:
        """every grant, expired ones too, oldest first"""
        db = self._open(False)
        if not db:
            return []
        try:
            q = "select id, un, rcpt, vp, name, pr, t1 from gr order by id"
            return db.execute(q).fetchall()
        finally:
            db.close()

    def row(self, gid: int) -> Optional[tuple[Any, ...]]:
        """one grant, like rows()"""
        db = self._open(False)
        if not db:
            return None
        try:
            q = "select id, un, rcpt, vp, name, pr, t1 from gr where id = ?"
            zl = db.execute(q, (gid,)).fetchall()
            return zl[0] if zl else None
        finally:
            db.close()

    def set_expiry(self, gid: int, t1: int) -> None:
        db = self._open(False)
        if not db:
            return
        try:
            db.execute("update gr set t1 = ? where id = ?", (t1, gid))
            db.commit()
        finally:
            db.close()

    def delete(self, gids: list[int]) -> None:
        db = self._open(False)
        if not db:
            return
        try:
            for gid in gids:
                db.execute("delete from gr where id = ?", (gid,))
            db.commit()
        finally:
            db.close()


def grant_desc(
    gid: int, un: str, rcpt: str, vp: str, name: str, pr: str, t1: int
) -> str:
    """how the log names a grant: owner, recipient, path and rights"""
    zs = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t1)) + " UTC" if t1 else "never"
    t = "grant %d by [%s] to [%s] of [/%s] as [%s] (%s, expires %s)"
    return t % (gid, un, rcpt, vp, name, pr, zs)


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


def is_group(rcpt: str) -> bool:
    """a recipient is an account, or a config group as @<name>"""
    return rcpt.startswith("@")


def config_groups(asrv: "AuthSrv") -> dict[str, list[str]]:
    """the groups a grant can go to: [groups] / --grp from the config, by
    name without the @, minus the built-in all-accounts group (--grp-all)"""
    return {k: v for k, v in asrv.grps.items() if k != asrv.args.grp_all}


def reached_accounts(
    asrv: "AuthSrv", pseudo: set[str], rcpt: str
) -> Optional[list[str]]:
    """the accounts a grant's recipient means right now: one account, or
    whoever is in the @group at this reload; None if the recipient account
    doesn't exist, [] if the group doesn't (the grant then waits for it)"""
    acct = asrv.acct
    if not is_group(rcpt):
        return [rcpt] if is_account(acct, pseudo, rcpt) else None
    uns = config_groups(asrv).get(rcpt[1:]) or []
    return sorted(set(x for x in uns if is_account(acct, pseudo, x)))


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

    timer = getattr(asrv, "fork_grant_timer", None)
    if timer:
        timer.kick()  # the timer waits for the mutex this reload holds

    log = asrv.log
    now = time.time()
    virt: list["VFS"] = []
    grants: list["VFS"] = []
    trees: dict[str, "VFS"] = {}  # recipient: their /<grants>
    aread: dict[str, list[str]] = {}  # recipient: vpaths of their grants
    pub = folder(None, top)
    pseudo = share_pw_accounts(args)
    rows = _prune_gone_accounts(asrv, acct, pseudo)

    # where one account gets two grants by the same name from one owner
    # (a group gained a member after create checked), the grant naming the
    # account wins, then the oldest; rows come oldest first
    rows.sort(key=lambda x: is_group(x[0][2]))  # ((gid, un, rcpt, ...), ...)
    mounted: set[int] = set()  # for check_expiry
    vfs.fork_grant_gids = mounted  # type: ignore
    for row, desc, uns in rows:
        gid, un, _, _, name, pr, _ = row
        state, why, src = grant_state(vfs, row, uns, now)
        if state != "active":
            verb = state if state in ("expired", "suspended", "broken") else "skipping"
            log("%s %s%s" % (verb, desc, "; " + why if why else ""), 3)
            continue

        s_vfs, s_rem, uns = src
        for ru in uns:
            if ru not in trees:
                trees[ru] = folder(None, top)
            ovn = folder(trees[ru], un)
            if name in ovn.nodes:
                t = "skipping %s for [%s]; they already have a grant by that name"
                log(t % (desc, ru), 3)
                continue

            gvn = _grant_vol(asrv, vfs, ovn, name, s_vfs, s_rem, un, pr)
            _add_rcpt(gvn.axs, ru, pr)
            ovn.nodes[name] = gvn
            grants.append(gvn)
            mounted.add(gid)
            aread.setdefault(ru, []).append(gvn.vpath)

            # the folders above it, and the root's copy, list only for recipients
            povn = folder(pub, un)
            for vn in (trees[ru], ovn, pub, povn, folder(povn, name)):
                vn.axs.uread.add(ru)
            log("mounted %s for [%s] at [/%s]" % (desc, ru, gvn.vpath))

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
    for vn in virt + grants:
        vn.get = _refuse_outside(vn.get)
    _route(vfs, top, trees)


def grant_state(
    vfs: "VFS", row: tuple[Any, ...], uns: Optional[list[str]], now: float
) -> tuple[str, str, Any]:
    """(state, what the log says about it, (source volume, its remainder,
    recipient accounts) if active); `uns` = reached_accounts.
    States: active, expired, suspended (the owner lacks the rights),
    broken (the source folder is gone), no members (nobody to mount it
    for), hidden folder (never granted; create refuses these)"""
    _, un, _, vp, _, pr, t1 = row
    if t1 and t1 <= now:
        return "expired", "", None

    # the owner, as a member of the group, already has the folder
    uns = [x for x in uns or [] if x != un]
    if not uns:
        return "no members", "nobody in that group", None

    if has_dot_part(vp):
        return "hidden folder", "a hidden folder is never granted", None

    try:
        s_vfs, s_rem = vfs.get(vp, un, "r" in pr, "w" in pr)
    except Exception as ex:
        return "suspended", "the owner lacks those rights: %r" % (ex,), None

    if not os.path.isdir(s_vfs.canonical(s_rem)):
        return "broken", "the source folder is gone", None

    return "active", "", (s_vfs, s_rem, uns)


def check_expiry(asrv: "AuthSrv", now: float) -> tuple[bool, float]:
    """the expiry timer's check: (True if a mounted grant has expired by
    `now` and a reload must unmount it, when to check next; 0 = when the
    next reload happens). Reads the expiry from the db, so a grant the
    owner extended after it was mounted is not reloaded for early"""
    mounted = getattr(asrv.vfs, "fork_grant_gids", None)
    if not mounted:
        return False, 0
    reload = False
    nxt = 0
    for row in _store(asrv.args).rows():
        gid, t1 = row[0], row[6]
        if gid not in mounted or not t1:
            continue
        if t1 <= now:
            reload = True
        elif not nxt or t1 < nxt:
            nxt = t1
    return reload, nxt


class ExpiryTimer(object):
    """unmounts grants as they expire, with a reload, like up2k's
    _check_shares does for share links. One per server, in the hub (with
    -j, a reload there reaches every worker); mount_grants wakes it at
    every reload of the hub's AuthSrv, since the next expiry may change"""

    def __init__(self, hub: "SvcHub") -> None:
        self.hub = hub
        self.cond = threading.Condition()
        self.dirty = True  # a reload happened since the last check

    def kick(self) -> None:
        with self.cond:
            self.dirty = True
            self.cond.notify()

    def run(self) -> None:
        hub = self.hub
        asrv = hub.asrv
        while not hub.stopping:
            with self.cond:
                self.dirty = False
            try:
                with asrv.mutex:
                    reload, nxt = check_expiry(asrv, time.time())
                if reload:
                    hub.log("grants", "unmounting expired grants")
                    hub.reload(False, False)
                    continue
            except Exception as ex:
                t = "could not check for expiring grants: %r"
                hub.log("grants", t % (ex,), 1)
                nxt = time.time() + 60

            # wait() counts elapsed time, so a wall clock that jumps ahead
            # (a Pi has no RTC; NTP sets it after boot) is noticed in 5 min
            with self.cond:
                if not self.dirty:
                    wait = nxt - time.time() if nxt else 300
                    self.cond.wait(max(1, min(wait, 300)))


def start_expiry_timer(hub: "SvcHub") -> None:
    """SvcHub.run: the grants expiry timer, when grants are on"""
    if not grants_top(hub.args):
        return
    timer = ExpiryTimer(hub)
    hub.asrv.fork_grant_timer = timer  # type: ignore
    Daemon(timer.run, "grant-expiry")


def _prune_gone_accounts(
    asrv: "AuthSrv", acct: dict[str, str], pseudo: set[str]
) -> list[tuple[Any, ...]]:
    """reload: delete for good every grant whose owner or named recipient
    is no longer an account, so a new account by the same name never
    inherits it; returns the other grants as (row, log name, accounts the
    recipient reaches), oldest first. IdP accounts are not in the config,
    so with idp there is no telling who is gone; nothing is deleted then"""
    log = asrv.log
    store = _store(asrv.args)
    rows = []
    gone = []
    for row in store.rows():
        gid, un, rcpt = row[:3]
        desc = grant_desc(*row)
        uns = reached_accounts(asrv, pseudo, rcpt)
        owner_ok = is_account(acct, pseudo, un)
        if owner_ok and uns is not None:
            rows.append((row, desc, uns))
        elif asrv.args.have_idp_hdrs:
            log("skipping %s; not an account" % (desc,), 3)
        else:
            who = "recipient" if owner_ok else "owner"
            log("deleted %s for good; the %s is no longer an account" % (desc, who), 3)
            gone.append(gid)
    if gone:
        store.delete(gone)
    return rows


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
    gvn.ls = _grant_ls(gvn)
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


def _inside(gvn: "VFS", ap: str) -> bool:
    """True if the resolved path `ap` is the grant's source folder or
    inside it; symlinks are followed only while they stay in there"""
    top = gvn.realpath.rstrip(os.sep) + os.sep
    return ap == gvn.realpath or ap.startswith(top)


def _refuse_outside(get: Any) -> Any:
    """wrap a grants folder's VFS.get (the path lookup behind copy and move
    destinations, uploads and ftp/sftp/smb) to 404 a path inside a grant
    that a symlink leads out of its source folder; httpcli.run resolves
    the request's own path with VFS._get, so http_request checks that"""

    def grant_get(vpath: str, uname: str, *a: Any, **ka: Any) -> Any:
        ret = get(vpath, uname, *a, **ka)
        if not ret or not is_grant(ret[0]):
            return ret
        vn, rem = ret
        if _inside(vn, vn.canonical(rem)):
            return ret

        # mirrors VFS._get(vpath, uname, will_read, will_write, will_move,
        # will_del, will_get, err=403); err=0 means "return None"
        err = ka["err"] if "err" in ka else (a[5] if len(a) > 5 else 403)
        if not err:
            return None
        raise Pebkac(404)

    return grant_get


def _grant_ls(gvn: "VFS") -> Any:
    """the grant's VFS.ls, which leaves out links that lead outside the
    source folder (listings, and zip/tar and webdav through VFS.walk)"""
    ls = gvn._ls

    def grant_ls(
        rem: str,
        uname: str,
        scandir: bool,
        permsets: list[list[bool]],
        lstat: bool = False,
        throw: bool = False,
    ) -> tuple[str, list[tuple[str, os.stat_result]], dict[str, "VFS"]]:
        ap, real, virt = ls(rem, uname, scandir, permsets, True, throw)
        if not _inside(gvn, ap):
            return ap, [], {}
        ret = []
        for fn, st in real:
            if stat.S_ISLNK(st.st_mode):
                fp = absreal(os.path.join(ap, fn))
                if not _inside(gvn, fp):
                    continue
                if not lstat:
                    try:
                        st = bos.stat(fp)
                    except:
                        continue  # a dangling link
            ret.append((fn, st))
        return ap, ret, virt

    return grant_ls


def http_request(cli: Any) -> bool:
    """httpcli.run, once the request's volume is known; True = reply 404"""
    if http_refused(cli):
        return True

    vn = cli.vn
    if is_grant(vn) and not _inside(vn, vn.canonical(cli.rem)):
        return True

    # upstream lists a folder without a path on disk with tx_ls_vols, from
    # the account's readable volumes (rvol). Grants stay out of the global
    # list, which search also reads, so add them for this listing only
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


def _expiry(exp: Any, now: int) -> int:
    """the expires-at time for an expiry in minutes (like share links);
    0 = never, which is the default"""
    if exp is None or exp == "":
        return 0
    if isinstance(exp, (str, unicode)) and exp.isdigit():
        exp = int(exp)
    if isinstance(exp, bool) or not isinstance(exp, int) or not 0 <= exp <= 10**9:
        raise Pebkac(400, "the expiry is a whole number of minutes, or 0 for none")
    return now + exp * 60 if exp else 0


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


def _no_overlap(asrv: "AuthSrv", owner: str, rcpt: str, name: str) -> None:
    """one owner's grants by one name never reach the same account twice:
    not bob directly and through @family, nor through two groups"""
    pseudo = share_pw_accounts(asrv.args)
    uns = set(reached_accounts(asrv, pseudo, rcpt) or []) - set([owner])
    for prev in _store(asrv.args).rcpts(owner, name):
        both = uns & set(reached_accounts(asrv, pseudo, prev) or [])
        if prev == rcpt or both:
            t = "you already gave %r a grant named %r"
            if prev != rcpt:
                t += ", which reaches %s" % (", ".join(sorted(both)),)
            raise Pebkac(400, (t + "; pick another name") % (prev, name))


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
    t1 = _expiry(req.get("exp"), int(time.time()))

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

    asrv = cli.asrv
    if rcpt in ("*", "@" + args.grp_all):
        raise Pebkac(400, "a grant cannot go to every account; pick an account or a group")
    if rcpt == uname:
        raise Pebkac(400, "you cannot grant a folder to yourself")
    if is_group(rcpt):
        if rcpt[1:] not in config_groups(asrv):
            raise Pebkac(400, "no such group: %r" % (rcpt,))
    elif not is_account(asrv.acct, share_pw_accounts(args), rcpt):
        raise Pebkac(400, "no such recipient: %r" % (rcpt,))

    if not _safe_name(name):
        t = "the name must be one folder name: not starting with a dot, no slashes or control characters, at most 255 characters"
        raise Pebkac(400, t)

    _no_overlap(asrv, uname, rcpt, name)
    gid = _store(args).create(uname, rcpt, vp, name, pr, t1)
    if not gid:
        t = "you already gave %r a grant named %r; pick another name"
        raise Pebkac(400, t % (rcpt, name))
    cli.log("created %s" % (grant_desc(gid, uname, rcpt, vp, name, pr, t1),))

    cli.conn.hsrv.broker.ask("reload", False, True).get()
    zs = "/%s/%s/%s/" % (top, uname, name)
    cli.reply(json.dumps({"id": gid, "vp": zs}).encode("utf-8"), 201, mime="application/json")
    return True


def _page_user(cli: Any) -> str:
    """the caller of the grants page and its actions; refuses guests"""
    if not grants_top(cli.args):
        raise Pebkac(400, "grants are disabled in the server config")
    if cli.uname == "*":
        raise Pebkac(401, "you must be logged in to manage grants")
    return cli.uname


def _is_admin(cli: Any) -> bool:
    """--shr-adm also manages every grant"""
    return cli.uname in (getattr(cli.args, "shr_adm", None) or [])


_PR_TEXT = {"r": "read", "rw": "read + upload"}


def tx_grants(cli: Any) -> bool:
    """GET ?grants: the caller's grants (every grant for --shr-adm);
    GET ?grants=rcpts: who a grant can go to, as json"""
    uname = _page_user(cli)
    if cli.uparam.get("grants") == "rcpts":
        return _tx_rcpts(cli)

    asrv = cli.asrv
    now = time.time()
    pseudo = share_pw_accounts(asrv.args)
    rows = []
    for row in _store(asrv.args).rows():
        gid, un, rcpt, vp, name, pr, t1 = row
        if un != uname and not _is_admin(cli):
            continue
        uns = reached_accounts(asrv, pseudo, rcpt)
        state = grant_state(asrv.vfs, row, uns, now)[0]
        href = "/%s/" % (quotep(vp),) if vp else "/"
        rows.append(
            {
                "gid": gid,
                "owner": un,
                "rcpt": rcpt,
                "src": "/%s/" % (vp,) if vp else "/",
                "href": href,
                "name": name,
                "pr": _PR_TEXT.get(pr, pr),
                "t1": t1,
                "state": state,
            }
        )

    html = cli.j2s(_template(cli), this=cli, rows=rows, now=int(now), adm=_is_admin(cli))
    cli.reply(html.encode("utf-8"), status=200)
    return True


def _template(cli: Any) -> str:
    """the grants page template, added to upstream's on first use, so
    httpsrv's list of templates stays as it is"""
    j2 = cli.conn.hsrv.j2
    if "fork_grants" not in j2:
        import jinja2

        from .httpsrv import load_jinja2_resource

        env = jinja2.Environment()
        env.loader = jinja2.FunctionLoader(lambda f: load_jinja2_resource(cli.E, f))
        j2["fork_grants"] = env.get_template("grants.html")
    return "fork_grants"


def _tx_rcpts(cli: Any) -> bool:
    """account names and config groups (as @name) a grant can go to,
    minus the caller and the all-accounts group; and the grants folder,
    where the grant button hides itself"""
    asrv = cli.asrv
    pseudo = share_pw_accounts(asrv.args)
    uns = [x for x in asrv.acct if x != cli.uname and is_account(asrv.acct, pseudo, x)]
    grps = ["@" + x for x in config_groups(asrv)]
    jt = {"accounts": sorted(uns), "groups": sorted(grps), "top": grants_top(cli.args)}
    cli.reply(json.dumps(jt).encode("utf-8"), mime="application/json")
    return True


def handle_egrant(cli: Any) -> bool:
    """POST ?egrant=rm&gid=N revokes a grant; ?egrant=MIN&gid=N extends
    its expiry by MIN minutes, counting from now if it already expired
    (which brings it back). The owner may do both; --shr-adm only revokes"""
    uname = _page_user(cli)
    args = cli.args
    store = _store(args)
    try:
        gid = int(cli.uparam.get("gid") or "")
        row = store.row(gid)
    except ValueError:
        row = None
    if not row:
        raise Pebkac(400, "no such grant")
    act = cli.uparam["egrant"]
    if row[1] != uname and (act != "rm" or not _is_admin(cli)):
        t = "that grant is not yours; a share admin can only revoke it"
        raise Pebkac(403, t if _is_admin(cli) else "that grant is not yours")

    desc = grant_desc(*row)
    if act == "rm":
        store.delete([gid])
        cli.log("revoked %s, by [%s]" % (desc, uname))
        reload = True
    else:
        if not act.isdigit() or not 0 < int(act) <= 10**9:
            raise Pebkac(400, "extend by a whole number of minutes")
        t1 = row[6]
        if not t1:
            raise Pebkac(400, "that grant never expires")
        now = int(time.time())
        reload = t1 <= now  # an expired grant comes back
        t1 = max(t1, now) + int(act) * 60
        store.set_expiry(gid, t1)
        cli.log("extended %s, by [%s]" % (grant_desc(*(row[:6] + (t1,))), uname))

    if reload:
        cli.conn.hsrv.broker.ask("reload", False, True).get()
    cli.reply(b"ok\n", mime="text/plain; charset=utf-8")
    return True

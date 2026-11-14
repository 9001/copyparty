# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: the `harden` global option; see FORK.md and docs/adr/0002

from .fork_util import grants_on
from .util import Pebkac

if True:  # pylint: disable=using-constant-test
    from typing import TYPE_CHECKING, Any, Callable, Iterable

    if TYPE_CHECKING:
        from .authsrv import VFS


def has_dot_part(rem: str) -> bool:
    """True if any part of a volume-relative path starts with a dot"""
    return rem.startswith(".") or "/." in rem


def _su() -> str:
    # deferred: authsrv imports this module
    from .authsrv import LEELOO_DALLAS

    return LEELOO_DALLAS


def _on(args: Any) -> bool:
    return bool(getattr(args, "harden", False))


def is_grant(vn: "VFS") -> bool:
    """True for the volume of one grant (/<grants>/<owner>/<name>)"""
    return getattr(vn, "fork_grant", False)


def _refused(args: Any, vn: "VFS", rem: str, uname: str, su: str) -> bool:
    # grants always block dotfiles, whatever --harden says (docs/adr/0002)
    return (
        has_dot_part(rem)
        and (_on(args) or is_grant(vn))
        and uname not in vn.axs.udot
        and uname != su
    )


def harden_vfs(args: Any, vfs: "VFS") -> None:
    """with --harden, make every volume's VFS.get (the path lookup used by
    ftp/sftp/smb/tftp and httpcli's handlers) refuse dot parts below the
    volume root with 404 for accounts without the `.` permission, and
    harden share links (see _harden_share). With grants on (and --harden
    off), the same lookup refuses dot parts inside grants only"""
    if not _on(args) and not grants_on(args):
        return

    shares = []
    if _on(args):
        shares = [x for x in vfs.all_nodes.values() if _is_share(args, x)]
        for vol in shares:
            _harden_share(vol)

    harden_nodes(args, list(vfs.all_nodes.values()), shares)  # includes the root


def harden_nodes(args: Any, vols: list["VFS"], guarded: list["VFS"]) -> None:
    """wrap each volume's VFS.get with the dot rule, and the listing-name
    rule for uploads into `guarded` (share links, grants, each also in
    `vols`); also called for grant volumes, which are mounted after harden_vfs"""
    su = _su()
    for vol in guarded:
        _guard_upload_names(vol)
    for vol in vols:
        vol.get = _refuse_dots(args, vol.get, su, guarded)


def _is_share(args: Any, vol: "VFS") -> bool:
    """True for the volume of one share link (/<shr>/<key>)"""
    shr = args.shr.strip("/")
    return bool(shr) and vol.vpath.startswith(shr + "/")


# names copyparty renders inside folder listings (--readme, --preadme, descript.ion)
_LISTING_NAMES = ("readme.md", "preadme.md", "descript.ion")


def _refuse_listing_name(fn: str) -> None:
    if fn.lower() in _LISTING_NAMES:
        t = "%r cannot be uploaded through a share link or a grant" % (fn,)
        raise Pebkac(403, t)


def _harden_share(vol: "VFS") -> None:
    """a share link never shows dotfiles, whatever its owner gave it (`.`,
    --ed, the dots volflag)"""
    vol.axs.udot = set()


def _guard_upload_names(vol: "VFS") -> None:
    """refuse uploads of names that would render inside the owner's folder
    listings. Uploads that send the new name in the request body (bput,
    up2k, new_md) name it with VFS.sanitize_fn; the rest (PUT, tput, COPY,
    ?copy) are caught in _refuse_dots, for the volumes harden_nodes guards"""
    vol.fork_guarded = True  # type: ignore  # for refuse_dot_tree
    sanitize_fn = vol.sanitize_fn

    def hardened_sanitize_fn(fn: str, rem: Any = None) -> str:
        ret = sanitize_fn(fn, rem)
        _refuse_listing_name(ret)
        return ret

    vol.sanitize_fn = hardened_sanitize_fn


def _refuse_dots(
    args: Any, get: Callable[..., Any], su: str, guarded: list["VFS"]
) -> Callable[..., Any]:
    def hardened_get(vpath: str, uname: str, *a: Any, **ka: Any) -> Any:
        ret = get(vpath, uname, *a, **ka)
        if not ret:
            return ret

        # mirrors VFS._get(vpath, uname, will_read, will_write, will_move,
        # will_del, will_get, err=403); err=0 means "return None"
        if not _refused(args, ret[0], ret[1], uname, su):
            will_write = ka["will_write"] if "will_write" in ka else a[1]
            if will_write and ret[0] in guarded:
                _refuse_listing_name(ret[1].split("/")[-1])
            return ret

        err = ka["err"] if "err" in ka else (a[5] if len(a) > 5 else 403)
        if not err:
            return None
        raise Pebkac(404)

    return hardened_get


def http_refused(cli: Any) -> bool:
    """httpcli.run resolves each request with VFS._get (no permission check,
    so not VFS.get); True if the dot rule (--harden, or inside a grant)
    must 404 this request"""
    if cli.mode in ("GET", "HEAD") and (
        cli.vpath == ".cpr" or cli.vpath.startswith(".cpr/")
    ):
        return False  # always copyparty's own web resources, never a volume

    return _refused(cli.args, cli.vn, cli.rem, cli.uname, _su())


def refuse_dot_tree(
    args: Any, vfs: "VFS", uname: str, svp: str, dvp: str, walk: Iterable[Any]
) -> None:
    """up2k folder move/copy: 403 before anything happens if any file in
    `walk` would hit the dot rule at its source or destination, or the
    listing-name rule at a guarded destination (share link, grant), since
    the per-file VFS.get would otherwise stop the move/copy half-way"""
    if not _on(args) and not grants_on(args):
        return

    su = _su()
    for dbv, vrem, _, _, files, _, _ in walk:
        for fn in files:
            svpf = "/".join(x for x in [dbv.vpath, vrem, fn[0]] if x)
            dvpf = dvp + svpf[len(svp) :]
            for vpf in (svpf, dvpf):
                vn, rem = vfs._get(vpf, uname, False, False)
                if _refused(args, vn, rem, uname, su):
                    t = "this folder holds dotfiles; moving or copying it needs the `.` permission"
                    raise Pebkac(403, t)
            dvn, _ = vfs._get(dvpf, uname, False, False)
            if getattr(dvn, "fork_guarded", False):
                _refuse_listing_name(fn[0])


def refuse_dot_name(args: Any, vn: "VFS", uname: str, name: str) -> None:
    """up2k handshake: the new file's name comes in the request body, so
    neither VFS.get nor http_refused saw it; 404 like every other way of
    creating a dot name without the `.` permission"""
    # the folder part was already checked by VFS.get; only the name is new
    if _refused(args, vn, name, uname, _su()):
        raise Pebkac(404)


SHR_KEY_MIN = 12  # the web UI makes 12-character keys


def refuse_short_key(args: Any, skey: str) -> None:
    """share link creation: a short key can be guessed"""
    if _on(args) and len(skey) < SHR_KEY_MIN:
        t = "the share key must be at least %d characters long" % (SHR_KEY_MIN,)
        raise Pebkac(400, t)


def purge_ownerless_shares(
    args: Any, db: Any, acct: dict[str, str], log: Callable[..., None]
) -> None:
    """reload: delete the share links of owners who are no longer an
    account, so a new account with the same name does not get them back.
    Upstream only hides them (the owner fails the permission check), which
    is still what happens to an owner who exists but lost access"""
    if not _on(args) or args.have_idp_hdrs:
        return  # idp accounts are not in the config; can't tell who's gone

    gone = []
    for k, un in db.execute("select k, un from sh").fetchall():
        if un not in acct and un != "*":
            gone.append((k, un))

    for k, un in gone:
        log("deleting share [%s]; its owner [%s] is no longer an account" % (k, un), 3)
        db.execute("delete from sh where k = ?", (k,))
        db.execute("delete from sf where k = ?", (k,))
    if gone:
        db.commit()

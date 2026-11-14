# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only: the `harden` global option; see FORK.md and docs/adr/0002

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


def _refused(vn: "VFS", rem: str, uname: str, su: str) -> bool:
    return has_dot_part(rem) and uname not in vn.axs.udot and uname != su


def harden_vfs(args: Any, vfs: "VFS") -> None:
    """with --harden, make every volume's VFS.get (the path lookup used by
    ftp/sftp/smb/tftp and httpcli's handlers) refuse dot parts below the
    volume root with 404 for accounts without the `.` permission"""
    if not _on(args):
        return

    su = _su()
    for vol in vfs.all_nodes.values():  # includes the root ("")
        vol.get = _refuse_dots(vol.get, su)


def _refuse_dots(get: Callable[..., Any], su: str) -> Callable[..., Any]:
    def hardened_get(vpath: str, uname: str, *a: Any, **ka: Any) -> Any:
        ret = get(vpath, uname, *a, **ka)
        if not ret or not _refused(ret[0], ret[1], uname, su):
            return ret

        # mirrors VFS._get(vpath, uname, will_read, will_write, will_move,
        # will_del, will_get, err=403); err=0 means "return None"
        err = ka["err"] if "err" in ka else (a[5] if len(a) > 5 else 403)
        if not err:
            return None
        raise Pebkac(404)

    return hardened_get


def http_refused(cli: Any) -> bool:
    """httpcli.run resolves each request with VFS._get (no permission check,
    so not VFS.get); True if --harden must 404 this request"""
    if not _on(cli.args):
        return False

    if cli.mode in ("GET", "HEAD") and (
        cli.vpath == ".cpr" or cli.vpath.startswith(".cpr/")
    ):
        return False  # always copyparty's own web resources, never a volume

    return _refused(cli.vn, cli.rem, cli.uname, _su())


def refuse_dot_tree(
    args: Any, vfs: "VFS", uname: str, svp: str, dvp: str, walk: Iterable[Any]
) -> None:
    """up2k folder move/copy: 403 before anything happens if any file in
    `walk` would hit the dot rule at its source or destination, since the
    per-file VFS.get would otherwise stop the move/copy half-way"""
    if not _on(args):
        return

    su = _su()
    for dbv, vrem, _, _, files, _, _ in walk:
        for fn in files:
            svpf = "/".join(x for x in [dbv.vpath, vrem, fn[0]] if x)
            dvpf = dvp + svpf[len(svp) :]
            for vpf in (svpf, dvpf):
                vn, rem = vfs._get(vpf, uname, False, False)
                if _refused(vn, rem, uname, su):
                    t = "this folder holds dotfiles; moving or copying it needs the `.` permission"
                    raise Pebkac(403, t)

# 03: `harden`: dotfiles can't be read without `.`

**What to build:** A new global switch `harden`, off by default. With it on, any path with a part starting with `.` **inside** a volume returns 404 for an account without the `.` permission on that volume. That covers direct GET, WebDAV, archive downloads and thumbnails, and the path lookup FTP, SFTP and SMB rely on. Accounts with `.` keep full access. A volume the admin mounted at a dot-named path stays reachable. With `harden` off, behaviour is exactly upstream's. See ADR-0002 and spec user stories 39, 40, 42, 45, 52.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] `harden` is registered as a global option. Fork code reads it with a default, so upstream's test `Cfg` needs no entry
- [x] The check sits in the shared path lookup (one hook in upstream code; the logic lives in a new fork module), not in each protocol (two hooks, not one: see Answer)
- [x] Tests (new hardening test module, in-memory HTTP seam, `harden` on), for an account with `r` but no `.`: GET `.env` → 404; GET `.git/config` → 404; WebDAV GET → 404; PROPFIND doesn't list dotfiles; `?zip`/`?tar` of the folder contain no dotfiles; a thumbnail request for a dot-named image is refused
- [x] Tests: the same requests from an account with `.` succeed
- [x] Test (path-lookup seam): looking up a dotfile path as an account without `.` is refused; with `.` it resolves
- [x] Test: a volume mounted at `/.b` is reachable by its readers; dot parts below its root still follow the rule
- [x] Test, `harden` off: GET `.env` by name returns 200 (upstream behaviour unchanged)
- [x] `.hist/up2k.*` stays refused as before
- [x] Upstream `tests/test_dots.py` passes unchanged
- [x] FORK.md: `harden` described, and the upstream hook line listed

## Answer

`--harden` (`[global]` `harden`) is registered in `__main__.py` and read with `getattr(..., False)`, so upstream's test `Cfg` needs no entry. Logic: `copyparty/fork_harden.py`; tests: `tests/test_fork_harden.py` (13 tests; the HTTP, lookup and move/copy ones were red before their hooks). Upstream `tests/test_dots.py` passes unchanged.

Hooks (all listed in FORK.md under "upstream edits"):

- `authsrv.py` `_reload`: `harden_vfs` wraps each volume's `VFS.get`, the lookup FTP/SFTP/SMB/TFTP and the HTTP handlers use.
- `httpcli.py` `run`: `http_refused` returns 404. A second hook was needed: `run()` resolves every request with the permission-less `VFS._get`, not `get`, and a Pebkac raised there escapes `run()` instead of becoming a 404. `GET`/`HEAD` of `/.cpr/` is exempt (always copyparty's own web resources).
- `up2k.py` `handle_mv` / `handle_cp`: `refuse_dot_tree` refuses (403) up front a folder move/copy that holds dotfiles the account can't see at the source or destination. Without it the per-file lookup stopped such a move half-way (found in review; refusing up front was the user's choice).

Notes: `.hist` is upstream's own permission-less node, so `.hist/up2k.*` is 403 for everyone, as before. Requests that write to a dot path (PUT, MKCOL, move/copy to a dot name) are now 404 too, a start on ticket 04; names sent in an upload's body are left to 04. SMB with `--smba` maps every user to the internal superuser and isn't covered (noted in FORK.md). Commit `e39752e8`.

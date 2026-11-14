# 05: `harden`: share links

**What to build:** With `harden` on, share links (used by guests) follow the fork's rules:
- dotfiles inside a share link return 404, even if the owner has `.`
- uploads through a share link refuse `README.md`, `PREADME.md` and `descript.ion` in any letter case
- keys shorter than 12 characters are refused when a share link is created
- share links whose owner account no longer exists are deleted for good at reload, so a reused account name doesn't revive them

Also confirm, in tests, the `no-html` protection the deployment relies on. Spec user stories 43, 46–50.

**Blocked by:** 03, 04

**Status:** resolved

- [x] Tests (`harden` on): a guest GET of `/share/<key>/.env` → 404 when the owner has `A`; archive download contains no dotfiles
- [x] Tests: a write share link refuses `README.md`, `readme.MD`, `PREADME.md`, `descript.ion` and dot names; other names upload fine
- [x] Test: creating a share link with an 11-character key is refused with a clear message; 12 characters is accepted
- [x] Test: owner account removed from the config → after reload the share link's row is gone from the share link database and doesn't return when an account with that name is added again
- [x] Tests (`no-html` on): `.html`, `.htm`, `.xhtml`, `.svg`, `.md` and the markdown viewer are served as `text/plain` with scripts disabled; copyparty's own file browser page is still served as HTML with its script
- [x] Test, `harden` off: all of the above behave as upstream
- [x] Upstream `tests/test_shr.py` passes unchanged
- [x] FORK.md: recommended `[global]` gains `harden` and `no-html`; note on giving `@family` `rwmd.` if members should keep their own dotfiles

## Answer

All in `copyparty/fork_harden.py`, active only with `harden`:

- **Dotfiles:** `harden_vfs` clears `udot` on every share link volume, so links created with `.` (and links under `--ed` or the `dots` volflag) lose it at reload. The `harden_vfs` call in `authsrv.py` moved to after upstream's `dots` volflag loop, which would otherwise add `.` back. Upstream's link archives already left dotfiles out; `?tar`/`?zip` of a dot folder by name is now 404.
- **Listing names:** `README.md`, `PREADME.md`, `descript.ion` in any case are 403 through a share link. Uploads that carry the name in the body (bput, up2k, new_md) go through the link's wrapped `sanitize_fn`. The rest (PUT/WebDAV PUT, the markdown editor's `tput`, `?copy=`, WebDAV COPY) go through the wrapped `get` as a write lookup. COPY, `?copy=` and `tput` were found by the spec review, not by the first tests.
- **Key length:** `refuse_short_key`, one `# fork` line in `httpcli.py` `handle_share`; 400 "the share key must be at least 12 characters long". The web UI's random keys are 12.
- **Ownerless links:** `purge_ownerless_shares`, one `# fork` line in the `authsrv.py` share loader: deletes `sh` + `sf` rows whose owner isn't an account. Skipped with IdP headers (IdP accounts aren't in the config); `*`-owned rows are kept. An owner who exists but lost access keeps the row, as upstream.

Tests: `tests/test_fork_harden_shr.py` (in-memory HTTP, link created through `?share`). The no-html check for "copyparty's own file browser page is still served as HTML with its script" can only check `text/html` and no `script-src 'none'`: the test server renders stub templates, so the script tag itself isn't visible there. FORK.md has the recommended `[global]` (`harden`, `no-html`) in the harden section rather than the tested-config block, since that block is marked as checked on v1.20.26 and these lines weren't.


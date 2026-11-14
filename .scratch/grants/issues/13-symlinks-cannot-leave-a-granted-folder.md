# 13: Symlinks can't lead out of a granted folder

**What to build:** Through a grant, a recipient reaches only what is really inside the source folder. Today a symlink inside a granted folder is followed, so a link to `../priv.txt` serves a file outside the folder the owner granted (found in the code review of tickets 01–11; FORK.md lists it under known gaps). After this ticket, anything reached through a grant whose real path is outside the source folder's real path returns 404. Symlinks that stay inside the source folder keep working. Upstream's `xvol` doesn't help, because it only stops links that leave the *volume*, and the source folder is usually a subfolder of the owner's home folder.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Tests (in-memory HTTP seam, grants test module): alice grants `photos/` to bob; `photos/` contains a symlink to a file outside it (`../priv.txt`) and a symlinked folder outside it. Bob gets 404 on direct GET of both, they don't appear in the JSON listing, the `?zip`/`?tar` archives leave them out, WebDAV GET and PROPFIND agree, and a thumbnail request is refused
- [x] Tests: a symlink inside `photos/` pointing to another file inside `photos/` still works for bob
- [x] Test: alice browsing her own home folder still follows the same links (only grants are restricted)
- [x] Test: the rule holds whether `harden` is on or off
- [x] FORK.md: the symlink entry is removed from the grants "known gaps"; a note added that with grants, `--hardlink` dedup is the safe choice, because `--dedup` stores duplicates as symlinks that may point outside a granted folder and would then 404 for recipients

## Comments

Done 2026-11-14, all in `fork_grants.py`:

- **The rule:** `_inside(gvn, ap)`: the resolved path is the grant's `realpath` (the source folder, already resolved) or below it. `xvol` was not reused: its fallback lets links into other volumes the user can read, and the ticket wants nothing outside the source folder
- **Where it is checked:** `http_request` 404s the request's own path (httpcli.run resolves it with `VFS._get`, which has no hook); `_refuse_outside` wraps `VFS.get` of the grants tree, so copy/move destinations, uploads and other protocols' lookups get the same 404; the grant's `ls` (`_grant_ls`) drops links that lead out, which covers `?ls`, `?tree`, PROPFIND and `?zip`/`?tar` (through `VFS.walk`)
- **Thumbnails:** a file through an outside link gets what a missing file gets (upstream answers `?th=w` for a 404 with a 200 "e404" picture, on purpose). Folder covers can't follow a link, since grants already empty `th_coversd`/`th_coversl`
- **Tests:** `test_symlinks_harden_off` / `_on` (direct GET, WebDAV GET, PROPFIND depth 0/1/infinity, `?ls`, `?zip`, `?tar`, thumbnail, an inside link still works, alice still follows the links in her own folder) and `test_no_upload_through_a_symlink_out_of_a_grant` (PUT, `?copy`/`?move` and WebDAV COPY/MOVE destinations, `VFS.get`). The copy/move gap was found by the code review, not the first pass

Not run: the Python 2 half of `scripts/run-tests.sh` (no python2 on this machine). The Python 3 suite passes from source (139 tests) and the grants module passes on the hint-stripped copy.

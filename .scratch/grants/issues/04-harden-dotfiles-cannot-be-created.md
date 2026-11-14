# 04: `harden`: dotfiles can't be created without `.`

**What to build:** With `harden` on, an account without `.` on a volume can't create anything with a dot name there. That covers uploads (up2k and basic uploader/PUT), renaming or moving to a dot name, and creating a folder with a dot name. It keeps reading and writing consistent, and stops visitors planting `.prologue.html` / `.epilogue.html`. See ADR-0002 and spec user story 41.

**Blocked by:** 03

**Status:** resolved

- [x] Tests (`harden` on, account with `rw` but no `.`): PUT `.env` refused; up2k upload of `.epilogue.html` refused; new folder `.x` refused; renaming `a.txt` to `.a.txt` refused; uploading into an existing dot folder refused
- [x] Tests: an account with `.` can do all of the above
- [x] Test, `harden` off: upstream behaviour unchanged
- [x] Copyparty's own temporary dot-names during upload (e.g. `--dotpart` partial files) keep working
- [x] Upstream tests pass unchanged

## Answer

Most create paths were already 404 after ticket 03, because they look up the final path with the hardened `VFS.get` (bup, new-md, mkdir, `?move`/`?copy`, WebDAV MOVE/COPY) or the request path is the dot name (PUT, MKCOL, anything into a dot folder). The one gap was the up2k handshake, whose file name comes in the JSON body: `refuse_dot_name` in `copyparty/fork_harden.py`, hooked in `httpcli.py` `handle_post_json` right after `vfs.sanitize_fn` (one line, `# fork`, listed in FORK.md). It returns 404 like the other paths.

Tests in `tests/test_fork_harden.py`: every create path (PUT, PUT into a dot folder, up2k `.epilogue.html`, up2k into a dot folder, bup, bup into a dot folder, new-md `.prologue.html`, mkdir `.x`, mkdir in a dot folder, rename to `.a.txt`, move into a dot folder) is refused without `.`, works with `.`, and works with `harden` off. A `--dotpart` up2k upload still completes. Only the up2k case was red before the hook. Full suite passes.

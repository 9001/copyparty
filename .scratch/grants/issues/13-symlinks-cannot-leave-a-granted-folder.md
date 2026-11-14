# 13: Symlinks can't lead out of a granted folder

**What to build:** Through a grant, a recipient reaches only what is really inside the source folder. Today a symlink inside a granted folder is followed, so a link to `../priv.txt` serves a file outside the folder the owner granted (found in the code review of tickets 01–11; FORK.md lists it under known gaps). After this ticket, anything reached through a grant whose real path is outside the source folder's real path returns 404. Symlinks that stay inside the source folder keep working. Upstream's `xvol` doesn't help, because it only stops links that leave the *volume*, and the source folder is usually a subfolder of the owner's home folder.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Tests (in-memory HTTP seam, grants test module): alice grants `photos/` to bob; `photos/` contains a symlink to a file outside it (`../priv.txt`) and a symlinked folder outside it. Bob gets 404 on direct GET of both, they don't appear in the JSON listing, the `?zip`/`?tar` archives leave them out, WebDAV GET and PROPFIND agree, and a thumbnail request is refused
- [ ] Tests: a symlink inside `photos/` pointing to another file inside `photos/` still works for bob
- [ ] Test: alice browsing her own home folder still follows the same links (only grants are restricted)
- [ ] Test: the rule holds whether `harden` is on or off
- [ ] FORK.md: the symlink entry is removed from the grants "known gaps"; a note added that with grants, `--hardlink` dedup is the safe choice, because `--dedup` stores duplicates as symlinks that may point outside a granted folder and would then 404 for recipients

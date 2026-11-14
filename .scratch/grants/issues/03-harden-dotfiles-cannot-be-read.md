# 03: `harden`: dotfiles can't be read without `.`

**What to build:** A new global switch `harden`, off by default. With it on, any path with a part starting with `.` **inside** a volume returns 404 for an account without the `.` permission on that volume. That covers direct GET, WebDAV, archive downloads and thumbnails, and the path lookup FTP, SFTP and SMB rely on. Accounts with `.` keep full access. A volume the admin mounted at a dot-named path stays reachable. With `harden` off, behaviour is exactly upstream's. See ADR-0002 and spec user stories 39, 40, 42, 45, 52.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] `harden` is registered as a global option. Fork code reads it with a default, so upstream's test `Cfg` needs no entry
- [ ] The check sits in the shared path lookup (one hook in upstream code; the logic lives in a new fork module), not in each protocol
- [ ] Tests (new hardening test module, in-memory HTTP seam, `harden` on), for an account with `r` but no `.`: GET `.env` → 404; GET `.git/config` → 404; WebDAV GET → 404; PROPFIND doesn't list dotfiles; `?zip`/`?tar` of the folder contain no dotfiles; a thumbnail request for a dot-named image is refused
- [ ] Tests: the same requests from an account with `.` succeed
- [ ] Test (path-lookup seam): looking up a dotfile path as an account without `.` is refused; with `.` it resolves
- [ ] Test: a volume mounted at `/.b` is reachable by its readers; dot parts below its root still follow the rule
- [ ] Test, `harden` off: GET `.env` by name returns 200 (upstream behaviour unchanged)
- [ ] `.hist/up2k.*` stays refused as before
- [ ] Upstream `tests/test_dots.py` passes unchanged
- [ ] FORK.md: `harden` described, and the upstream hook line listed

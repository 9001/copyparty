# 15: Record FTP/SFTP and `grant_who` as intended limits

**What to build:** Two behaviours from the code review of tickets 01–11 are kept as they are, but written down as intended so they don't look like bugs later:

- **FTP/SFTP.** Grants are left out of each account's list of readable volumes (to keep them out of search), so the reviewer suspects grants don't work there: an account whose only access is a grant can't log in over FTP/SFTP, and SFTP can't list `/shared/`. The spec said grants should work the same on every protocol, but this deployment keeps FTP/SFTP/SMB off. Confirm the behaviour with a test, then record it.
- **`grant_who`.** It is checked only when a grant is created. Changing a volume to `grant_who: no` later doesn't suspend that volume's existing grants; owners or share admins revoke them on the grants page.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Test (path-lookup seam or the protocol servers' account/volume lookup, whichever the FTP/SFTP code really uses): an account with no volume access except a grant. Record what FTP login and SFTP listing of `/shared/` actually do
- [x] If confirmed: FORK.md grants "known gaps" says grants work over HTTP and WebDAV only, and why (search stays off; FTP/SFTP are off in this deployment). The spec's out-of-scope gets the same line, so it no longer contradicts "same on every protocol"
- [x] ~~If not confirmed: record under `## Comments

Mostly confirmed, in `tests/test_fork_grants.py` `test_ftp_sftp`, which repeats the lookups
ftpd/sftpd make (pyftpdlib and paramiko aren't installed, and the spec doesn't start protocol
servers in tests):

- an account whose only access is a grant fails the FTP/SFTP login check
  (`vfs.aread.get(u) or vfs.awrite.get(u)`)
- `vfs.get("shared", ...)` resolves to a folder with no path on disk: FTP's `listdir` shows it
  empty, SFTP's `v2a` raises `OSError(ENOENT)`, so `list_folder` returns `SFTP_FAILURE`
- not "HTTP and WebDAV only", though: an account with a volume of its own logs in, and
  `/shared/<owner>/<name>` by full path resolves into the grant with the granted rights.
  FORK.md and the spec say that instead

`test_grant_who_no_later_keeps_existing_grants` covers `grant_who`.

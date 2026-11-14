# 15: Record FTP/SFTP and `grant_who` as intended limits

**What to build:** Two behaviours from the code review of tickets 01–11 are kept as they are, but written down as intended so they don't look like bugs later:

- **FTP/SFTP.** Grants are left out of each account's list of readable volumes (to keep them out of search), so the reviewer suspects grants don't work there: an account whose only access is a grant can't log in over FTP/SFTP, and SFTP can't list `/shared/`. The spec said grants should work the same on every protocol, but this deployment keeps FTP/SFTP/SMB off. Confirm the behaviour with a test, then record it.
- **`grant_who`.** It is checked only when a grant is created. Changing a volume to `grant_who: no` later doesn't suspend that volume's existing grants; owners or share admins revoke them on the grants page.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Test (path-lookup seam or the protocol servers' account/volume lookup, whichever the FTP/SFTP code really uses): an account with no volume access except a grant. Record what FTP login and SFTP listing of `/shared/` actually do
- [ ] If confirmed: FORK.md grants "known gaps" says grants work over HTTP and WebDAV only, and why (search stays off; FTP/SFTP are off in this deployment). The spec's out-of-scope gets the same line, so it no longer contradicts "same on every protocol"
- [ ] If not confirmed: record under `## Comments` here what does work, and fix FORK.md's current sentence ("FTP/SFTP volume lists never see them") to match
- [ ] Test: a grant created while `grant_who` allowed it stays active after the volume is changed to `grant_who: no` and reloaded, and creating a new one is refused
- [ ] FORK.md and the spec say `grant_who` only applies when a grant is created, and that existing grants are revoked on the grants page

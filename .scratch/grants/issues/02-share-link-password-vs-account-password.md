# 02: Share link password vs. account password

**What to build:** A share link password is loaded as a made-up account's password, and the account loader refuses to load when two accounts have the same password. Suspicion: an owner who sets a share link password equal to any account's password could make every later reload fail, which would lock out config and share changes for everyone. Confirm or rule this out, and fix it if real. Spec: `.scratch/grants/spec.md`, user story 51.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Test first (in-memory HTTP seam): an account `alice` with password P creates a share link with password P; a reload must still succeed and alice must still log in with P
- [x] Also test with password hashing on (`ah-alg`) and off
- [x] If the test fails: fix it with the smallest edit, so that the share link still opens with its password, alice still logs in, and reloads succeed; list the fix in FORK.md
- [x] ~~If the test passes: keep it as a guard and note under `## Comments` in this file why it isn't a bug~~ (n/a: the test failed, so the bug is real)
- [x] Upstream `tests/test_shr.py` still passes unchanged

## Answer

Real bug, with and without `ah-alg`: right after alice made a share link with her own password, the next reload (also on share creation, SIGUSR1 and `?reload=cfg`) and any restart failed with `accounts [alice] and [s_...] have the same password`. Share passwords are stored as `ah.hash(pw)` and account passwords are hashed before shares load, so they collide in both modes.

Fix (`copyparty/authsrv.py`, share loader): when a share's password equals an account's password, the share is granted to that account instead of a made-up `s_...` account. Logins look an account up by password alone, so that password already logs in as alice; she now opens the share with it and still logs in normally. Refusing such a password when the share is created was rejected because it would tell any share creator that the password belongs to an account. Test: `tests/test_fork_shr_pw.py` (red before the fix, in both modes); listed in FORK.md under "upstream edits".

Accepted tradeoff: the share goes to whichever account owns that password, not only the share's owner. If bob sets a share password equal to alice's password, alice's own login (and her sessions) also gets that share's permissions until either password changes. This gives nobody new access: whoever holds the password already logs in as alice. Hashing off: the share password is compared after stripping whitespace, as account passwords are, so `"P "` doesn't collide either. With `--usernames` account passwords are `name:pw`, so they never match a share password and nothing changes.

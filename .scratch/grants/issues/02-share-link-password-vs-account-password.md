# 02: Share link password vs. account password

**What to build:** A share link password is loaded as a made-up account's password, and the account loader refuses to load when two accounts have the same password. Suspicion: an owner who sets a share link password equal to any account's password could make every later reload fail, which would lock out config and share changes for everyone. Confirm or rule this out, and fix it if real. Spec: `.scratch/grants/spec.md`, user story 51.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Test first (in-memory HTTP seam): an account `alice` with password P creates a share link with password P; a reload must still succeed and alice must still log in with P
- [ ] Also test with password hashing on (`ah-alg`) and off
- [ ] If the test fails: fix it with the smallest edit, so that the share link still opens with its password, alice still logs in, and reloads succeed; list the fix in FORK.md
- [ ] If the test passes: keep it as a guard and note under `## Comments` in this file why it isn't a bug
- [ ] Upstream `tests/test_shr.py` still passes unchanged

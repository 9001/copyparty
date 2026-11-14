# 07: Grant rights and refusals

**What to build:** Owners can choose read + upload as well as read-only, and the create endpoint refuses everything the design forbids. Uploads through a grant follow the fork's upload rules. Spec user stories 5–7, 11–13, 26, 31, 46.

**Blocked by:** 04, 06

**Status:** resolved

- [x] A read + upload grant lets the recipient upload; read-only refuses uploads; move, delete and admin are never possible through a grant
- [x] Refused at create, each with its own test: rights the owner doesn't hold on the source; a source under `/shared` or under the share link folder; a volume whose `grant_who` doesn't allow the caller (`no`, or `a` for non-admins); unknown recipient; the caller themselves; the built-in all-accounts group; a mount name that isn't one safe path segment; a single file or a file selection; the same owner+recipient+name as an existing grant
- [x] Test: creating a share link from inside `/shared/...` is refused (grant mounts force share links off)
- [x] `grant_who` is a volume setting (`no` / `a` / `auth`, default `auth`), independent of `shr_who`; tests show grants allowed with share links forbidden on the same volume, and the other way round
- [x] Tests: uploads through a grant refuse dot names and `README.md` / `PREADME.md` / `descript.ion` in any case, whatever `harden` says; the owner uploading the same names through their own volume succeeds

## Answer

Done in `copyparty/fork_grants.py` (`_rights`, `_may_grant`, `share_pw_accounts`, `_safe_name`, `GrantStore.create` refusing duplicates in the same SQL statement as the insert) and `copyparty/fork_harden.py` (`harden_nodes` applies the share link upload-name rule to grant volumes too). `grant_who` is registered in `cfg.py` (one line, listed in FORK.md). Rights are checked before `grant_who`, like upstream's share handler, not in the spec's listed order. Extra refusals: `*`, and the made-up `s_...` account a share link password logs in as (the review found that a padded password got past the first version of this check; it is now read from shares.db). Tests in `tests/test_fork_grants.py`; full suite passes on Python 3 (no python2 on this machine).

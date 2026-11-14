# 07: Grant rights and refusals

**What to build:** Owners can choose read + upload as well as read-only, and the create endpoint refuses everything the design forbids. Uploads through a grant follow the fork's upload rules. Spec user stories 5–7, 11–13, 26, 31, 46.

**Blocked by:** 04, 06

**Status:** ready-for-agent

- [ ] A read + upload grant lets the recipient upload; read-only refuses uploads; move, delete and admin are never possible through a grant
- [ ] Refused at create, each with its own test: rights the owner doesn't hold on the source; a source under `/shared` or under the share link folder; a volume whose `grant_who` doesn't allow the caller (`no`, or `a` for non-admins); unknown recipient; the caller themselves; the built-in all-accounts group; a mount name that isn't one safe path segment; a single file or a file selection; the same owner+recipient+name as an existing grant
- [ ] Test: creating a share link from inside `/shared/...` is refused (grant mounts force share links off)
- [ ] `grant_who` is a volume setting (`no` / `a` / `auth`, default `auth`), independent of `shr_who`; tests show grants allowed with share links forbidden on the same volume, and the other way round
- [ ] Tests: uploads through a grant refuse dot names and `README.md` / `PREADME.md` / `descript.ion` in any case, whatever `harden` says; the owner uploading the same names through their own volume succeeds

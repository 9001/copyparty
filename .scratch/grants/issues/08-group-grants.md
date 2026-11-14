# 08: Group grants

**What to build:** An owner can grant a folder to an admin-defined group such as `@family`. Whoever is in the group at each reload has access: new members gain it, removed members lose it. Spec user stories 2, 27.

**Blocked by:** 06

**Status:** resolved

- [x] Create accepts `@<group>` for groups defined in the config; unknown groups are refused
- [x] Test: every member of `@family` sees `/shared/<owner>/<name>`; a non-member doesn't
- [x] Test: add carol to `@family` in the config, reload → carol has access; remove bob, reload → bob doesn't
- [x] Test: removing the group from the config → the grant gives no access, and the owner can still revoke it (the row is kept; the revoke request itself arrives with ticket 10, whose tests cover it)
- [x] Test: the same name granted to bob directly and to `@family` (which includes bob) doesn't produce a duplicate or broken mount for bob. Pick and document the rule, e.g. refuse at create

Rule (FORK.md): create refuses a name that would reach an account that already gets a grant by that name from the same owner. If a later group change makes two such grants reach one account anyway, the grant naming the account wins over a group grant, otherwise the oldest; the other is skipped for that account and logged.

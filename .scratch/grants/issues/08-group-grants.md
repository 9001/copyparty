# 08: Group grants

**What to build:** An owner can grant a folder to an admin-defined group such as `@family`. Whoever is in the group at each reload has access: new members gain it, removed members lose it. Spec user stories 2, 27.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Create accepts `@<group>` for groups defined in the config; unknown groups are refused
- [ ] Test: every member of `@family` sees `/shared/<owner>/<name>`; a non-member doesn't
- [ ] Test: add carol to `@family` in the config, reload → carol has access; remove bob, reload → bob doesn't
- [ ] Test: removing the group from the config → the grant gives no access, and the owner can still revoke it
- [ ] Test: the same name granted to bob directly and to `@family` (which includes bob) doesn't produce a duplicate or broken mount for bob. Pick and document the rule, e.g. refuse at create

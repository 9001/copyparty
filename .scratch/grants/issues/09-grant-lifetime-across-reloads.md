# 09: Grant lifetime across reloads

**What to build:** A grant's state is worked out again at every reload:
- **expired** once its expiry passes
- **suspended** while the owner lacks the granted rights (it comes back when they regain them)
- **broken** while its source folder is missing (it comes back when a folder appears at that path)
- **deleted for good** when the owner's or a named recipient's account no longer exists

Every state change is logged. Grants have no expiry unless one is set. Spec user stories 8, 9, 18–21, 28, 34, 35.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Create accepts an optional expiry in minutes; the default is none
- [ ] Test: after the expiry passes (set up by adjusting the stored time), a reload removes access
- [ ] Test (suspended): alice granted from `/family`; alice removed from `@family`, reload → bob has no access, the row is kept; alice added back, reload → bob has access again
- [ ] Test (broken): source folder renamed, reload → no access; renamed back, reload → access again
- [ ] Tests (deleted for good): owner account removed → row gone; named recipient account removed → row gone; an account re-created with the same name doesn't get the grant back
- [ ] Test: the log has lines for create, expire, suspend, break and permanent removal, with owner, recipient, path and rights

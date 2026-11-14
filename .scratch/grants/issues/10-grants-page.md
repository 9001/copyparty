# 10: Grants page

**What to build:** A `?grants` page, linked from the control panel, where an owner sees their grants: recipient, rights, mount name, expiry, and state (active / expired / suspended / broken). They can revoke a grant or extend its expiry from there. Users listed in `--shr-adm` see and can revoke every grant. Also an endpoint that returns the recipient list for the grant dialog. Spec user stories 3, 4, 15–17, 22, 23, 32.

**Blocked by:** 01, 07, 09

**Status:** ready-for-agent

- [ ] The page is a new template; upstream's `?shares` page is unchanged
- [ ] Test: alice's page lists only alice's grants, with the correct state for each (active, expired, suspended, broken)
- [ ] Test: revoke → after reload, the recipient has no access and the row is gone; revoking someone else's grant is refused unless the caller is a share admin
- [ ] Test: a grant to a group that was removed from the config is still listed and can be revoked (ticket 08 only checks the row is kept)
- [ ] Test: extending an expired grant brings it back; extending an active one moves the expiry
- [ ] Test: with `--shr-adm alice,admin`, both see all grants (uses the list parsing from 01)
- [ ] Test: the recipient-list endpoint returns account names and config groups, without the caller and without the all-accounts group; guests are refused
- [ ] The control panel shows a link to the grants page when grants are on
- [ ] Recipient names and paths are HTML-escaped on the page (test with a name containing `<`)

# 10: Grants page

**What to build:** A `?grants` page, linked from the control panel, where an owner sees their grants: recipient, rights, mount name, expiry, and state (active / expired / suspended / broken). They can revoke a grant or extend its expiry from there. Users listed in `--shr-adm` see and can revoke every grant. Also an endpoint that returns the recipient list for the grant dialog. Spec user stories 3, 4, 15–17, 22, 23, 32.

**Blocked by:** 01, 07, 09

**Status:** resolved

- [x] The page is a new template; upstream's `?shares` page is unchanged
- [x] Test: alice's page lists only alice's grants, with the correct state for each (active, expired, suspended, broken)
- [x] Test: revoke → after reload, the recipient has no access and the row is gone; revoking someone else's grant is refused unless the caller is a share admin
- [x] Test: a grant to a group that was removed from the config is still listed and can be revoked (ticket 08 only checks the row is kept)
- [x] Test: extending an expired grant brings it back; extending an active one moves the expiry
- [x] Test: with `--shr-adm alice,admin`, both see all grants (uses the list parsing from 01)
- [x] Test: the recipient-list endpoint returns account names and config groups, without the caller and without the all-accounts group; guests are refused
- [x] The control panel shows a link to the grants page when grants are on
- [x] Recipient names and paths are HTML-escaped on the page (test with a name containing `<`)

The control panel link was checked by hand against a running server (the test server stubs the splash template). Share admins can revoke any grant but only the owner can extend one, per story 32. A fifth state, `no members`, covers a group grant whose group is gone or holds only the owner. Grant expiry still only takes effect at a reload; FORK.md lists this as a known gap.

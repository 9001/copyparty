# 01: `--shr-adm` matches a real list of names

**What to build:** `--shr-adm` is documented as a comma-separated list of users who can view and delete any share link. Today the share link list and revoke endpoints compare the caller against the whole option string, so only a single name works. The active-downloads view uses a substring test, so with `--shr-adm admin` a user named `adm` or `a` passes. After this ticket every listed name works, and only exact names do. Spec: `.scratch/grants/spec.md`, user story 33.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Failing tests first (in a new fork test module, using the in-memory HTTP seam from `tests/test_shr.py`): with `--shr-adm alice,bob`, both alice and bob can list and delete another owner's share link
- [ ] Failing test first: with `--shr-adm admin`, an account named `adm` gets no share-admin view in the active-downloads list
- [ ] Fixed with the smallest possible edit to upstream lines; the option is parsed once into a list of names
- [ ] Upstream `tests/test_shr.py` still passes unchanged
- [ ] FORK.md lists the fix under upstream edits, noting "take theirs if upstream fixes it"

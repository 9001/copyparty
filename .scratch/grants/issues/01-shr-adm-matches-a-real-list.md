# 01: `--shr-adm` matches a real list of names

**What to build:** `--shr-adm` is documented as a comma-separated list of users who can view and delete any share link. Today the share link list and revoke endpoints compare the caller against the whole option string, so only a single name works. The active-downloads view uses a substring test, so with `--shr-adm admin` a user named `adm` or `a` passes. After this ticket every listed name works, and only exact names do. Spec: `.scratch/grants/spec.md`, user story 33.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Failing tests first (in a new fork test module, using the in-memory HTTP seam from `tests/test_shr.py`): with `--shr-adm alice,bob`, both alice and bob can list and delete another owner's share link
- [x] Failing test first: with `--shr-adm admin`, an account named `adm` gets no share-admin view in the active-downloads list
- [x] Fixed with the smallest possible edit to upstream lines; the option is parsed once into a list of names
- [x] Upstream `tests/test_shr.py` still passes unchanged
- [x] FORK.md lists the fix under upstream edits, noting "take theirs if upstream fixes it"

## Answer

`--shr-adm` is split once in `svchub.py` by `copyparty/fork_util.py:split_names`; `?shares` and `?eshare` now test membership, and the active-downloads check becomes exact because it now tests a list. `--cgen` still prints the option (`shr_adm` added to its `csv` set). Tests: `tests/test_fork_shr_adm.py` (both red before the fix). Upstream edits are recorded in FORK.md under "upstream edits".

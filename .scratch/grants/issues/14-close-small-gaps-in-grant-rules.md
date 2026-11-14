# 14: Close small gaps in grant rules

**What to build:** Five small fixes from the code review of tickets 01–11. None of them leaks data today, but each makes a rule hold the same way everywhere:

1. **Share links from `/shared/`.** Creating a share link from `/shared/` or `/shared/<owner>/` currently succeeds and writes a row that never opens. Ticket 07 asked for it to be refused, the same as from inside a grant.
2. **Dotfiles in archives.** `?zip`/`?tar` inside a grant include dotfiles when the recipient also has `.` on the source volume, while GET of the same file is 404. The spec says dotfiles are always 404 inside grants.
3. **README-type names in folder copy/move.** A copy or move into a read + upload grant stops half-way when the folder contains `README.md` (or `PREADME.md` / `descript.ion`): some files land, then a 403. Dot names are already checked for the whole folder up front; README-type names should be too.
4. **Control panel without `grants`.** The control panel template reads the `grants` option without a default, so it fails to render with upstream's test configuration, which has no `grants`. Real runs always have the option, so this only affects the ADR-0002 promise that upstream tests stay unchanged.
5. **Missing marker.** One fork branch in the share link loader has no `# fork` marker, unlike its neighbours.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Test: bob's share link create on `/shared/alice/` and on `/shared/` is refused, and the share link database gets no row
- [x] Test: bob has `.` on alice's source volume and a read grant to `photos/` containing `.env`; the grant's `?zip` and `?tar` don't contain `.env`
- [x] Tests: copying and moving a folder containing `sub/README.md` (also `PREADME.md`, `descript.ion`, any case) into a read + upload grant is refused before anything is written; the source is untouched and the grant folder unchanged
- [x] Test: the control panel renders for a logged-in user with a test configuration that has no `grants` option
- [x] The fork branch in the share link loader carries the `# fork` marker; FORK.md's upstream-edit table still matches
- [x] Upstream `tests/test_dots.py` and `tests/test_shr.py` pass unchanged

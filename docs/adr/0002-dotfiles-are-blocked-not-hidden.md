# Dotfiles are blocked, not just hidden

Upstream only hides dotfiles from listings: anyone who can read a folder can still fetch `.env` or `.git/config` by name (tested on v1.20.26, `README.md` "dotfiles"). This fork refuses (404) any path with a part starting with `.` for anyone without the `.` permission on that volume, on every volume and protocol. Without `.` you also can't create one (upload, rename to, or create a folder with a dot name), which also stops visitors planting `.prologue.html` / `.epilogue.html`. Grants block dotfiles completely, even when the owner has `.`, and share links block them too. We chose this because names like `.env` are easy to guess, and grants and share links widen who can read a folder.

For volumes and share links this is switched on by one global option (`harden`), off by default, so upstream's own tests, which rely on the old behaviour, keep passing unchanged. Our config turns it on. Grants always block. Mount points that the admin names with a dot stay reachable; the block applies to path parts inside a volume.

## Consequences

- Volume members without `.` can't download dotfiles they uploaded themselves; admins give `.` (e.g. `rwmd.`) where that's wanted.
- Deliberately sharing a dotfile (e.g. `.well-known/`) by share link no longer works.
- It's an edit to upstream's VFS lookup, listed in FORK.md; if upstream ever adds a real block, take theirs.

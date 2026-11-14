# Spec: grants, and hardening of share links and dotfiles

Status: ready-for-agent

Vocabulary: see `GLOSSARY.md` (account holder, guest, owner, recipient, share link, grant, source folder, broken grant, suspended grant). Decisions: `docs/adr/0001-grants-live-inside-copyparty.md`, `docs/adr/0002-dotfiles-are-blocked-not-hidden.md`.

## Problem Statement

On this household copyparty server, an account holder who wants to give another account holder (or a group, like the family) access to one of their folders has to ask the admin. The admin then edits the config file and reloads. The only self-service option is a share link: a secret URL that isn't tied to anyone's account, can be forwarded, and can't be browsed from the recipient's own file tree.

Investigating the current behaviour also turned up gaps in what already exists:

- Dotfiles (`.env`, `.git/config`, …) are only hidden from listings. Anyone who can read a folder, including a guest with a share link, can download them by name (confirmed on v1.20.26).
- Anyone with upload rights can upload an HTML or SVG file that runs as a page under whoever opens it, or plant `README.md` / `.epilogue.html` files that show up inside folder listings.
- Share link keys are chosen by the browser and can be edited down to one character.
- A share link whose owner account was deleted comes back to life if a new account is created with the same name.
- `--shr-adm` is documented as a list but only works as a single name, and part of it matches substrings.

## Solution

Owners can give a **grant** from the file browser: access to one of their folders for a named account holder or an admin-defined group, with read or read + upload rights and an optional expiry. No config edit and no admin step. Recipients find granted folders in their own file tree under `/shared/<owner>/<name>`. Owners manage their grants on their own page. The server checks every grant again against the owner's current rights on every reload, the same way share links already work.

Guests keep using share links, which get the same hardening as the rest of the server. With the fork's `harden` option on:

- dotfiles are refused rather than hidden, for reading and creating
- share link keys must be long
- visitors can't upload files that render inside listings
- share links of deleted owners are removed for good

Together with `no-html` in the config, uploaded pages can't run scripts.

## User Stories

### Owners giving grants

1. As an owner, I want to grant a folder I can access to another account holder from the file browser, so that I don't have to ask the admin to edit the config.
2. As an owner, I want to grant a folder to an admin-defined group such as `@family`, so that I don't have to grant it to each member separately.
3. As an owner, I want to pick the recipient from a list of account names and groups, so that I don't mistype a name.
4. As an owner, I want my own name and the built-in "all accounts" group left out of that list, so that I can't make a pointless or overly broad grant by accident.
5. As an owner, I want to choose between read-only and read + upload, so that I decide whether the recipient can add files.
6. As an owner, I want to be stopped from granting rights I don't hold myself, so that I can't hand out more access than I have.
7. As an owner, I want move, delete and admin rights to never be offered, so that recipients can never remove or rearrange my files.
8. As an owner, I want to set an optional expiry on a grant, so that temporary access ends by itself.
9. As an owner, I want grants to have no expiry by default, so that ongoing sharing (e.g. a family photo folder) doesn't need renewing.
10. As an owner, I want to choose the name the folder appears under for the recipient, so that "photos" can show up as "trip-2026" if I prefer.
11. As an owner, I want a second grant with the same name to the same recipient to be refused, so that the recipient never sees two folders with the same name from me.
12. As an owner, I want granting to be refused for folders I only reach through someone else's grant, so that access can't be passed on beyond what the original owner decided.
13. As an owner, I want granting to be refused for single files or a set of files, so that grants stay simple and folder-shaped (share links remain available for files).
14. As an owner, I want the grant button next to the existing share button, so that I find it where I already share things.

### Owners managing grants

15. As an owner, I want a page that lists all my grants with recipient, rights, expiry and state, so that I can see who has access to what.
16. As an owner, I want to revoke a grant from that page, so that access ends immediately.
17. As an owner, I want to extend a grant's expiry from that page, so that I can keep access going without recreating it.
18. As an owner, I want grants whose source folder was renamed or deleted to show as **broken**, so that I understand why the recipient lost access.
19. As an owner, I want a broken grant to work again if a folder appears at the same path, so that restoring a folder restores the sharing.
20. As an owner, I want grants I can no longer back (because I lost rights to the source folder) to show as **suspended**, so that I understand why the recipient lost access.
21. As an owner, I want a suspended grant to come back by itself if I regain the rights, so that an admin's mistaken config edit doesn't destroy my sharing.
22. As an owner, I want the grants page link in the control panel, so that I can find it.
23. As an owner, I want grants and share links on separate pages, so that the two ideas aren't mixed up.

### Recipients

24. As a recipient, I want granted folders to appear under `/shared/<owner>/<name>` in my file tree, so that I can browse them like any other folder.
25. As a recipient, I want to see only the grants given to me (or to my groups) under `/shared/`, so that other people's grants stay private.
26. As a recipient with read + upload, I want to upload files into a granted folder, so that I can contribute (e.g. add my photos to a shared album).
27. As a recipient, I want access through a group grant to start when I'm added to the group and end when I'm removed, so that group membership is the only thing to manage.
28. As a recipient, I want expired, revoked, suspended and broken grants to simply disappear from my tree, so that I don't see folders I can't open.
29. As a recipient, I want granted folders to work over WebDAV too, so that I can mount them on my computer.

### Admin

30. As the admin, I want grants off unless I add one `grants: /shared` line to `[global]`, so that upgrading the fork doesn't change behaviour without me deciding.
31. As the admin, I want a per-volume `grant_who` setting (`no` / `a` / `auth`, default `auth`), separate from `shr_who`, so that I can allow grants from a volume while forbidding public share links from it, or the other way round.
32. As the admin, I want the users listed in `--shr-adm` to see and revoke every grant, so that I can clean up without editing a database by hand.
33. As the admin, I want `--shr-adm` with several comma-separated names to work for each of those names exactly, so that the option does what its help text says.
34. As the admin, I want every grant create, revoke, expiry, suspension, break and permanent removal written to copyparty's log with owner, recipient, path and rights, so that I can see what happened.
35. As the admin, I want grants deleted for good when the owner's or a named recipient's account no longer exists at reload, so that a new account created later with the same name doesn't inherit old access.
36. As the admin, I want grants stored in their own database file with their own version number, separate from the share link database, so that upstream's share link database upgrades never collide with ours.
37. As the admin, I want an option to move the grants database file, like `--shr-db`, so that I can keep it with my other state.
38. As the admin, I want grants to work even when share links are turned off, so that I can disable public links entirely and still let account holders share with each other.

### Dotfiles (with `harden` on)

39. As an account holder without the `.` permission on a volume, I want every path with a part starting with `.` inside that volume to return 404, so that `.env`, `.git/config` and similar files can't be fetched by guessing their name.
40. As an account holder with the `.` permission (e.g. via `A` on my home folder), I want full access to my own dotfiles, so that the block doesn't get in my way.
41. As an account holder without `.`, I want uploading, renaming to, or creating a folder with a dot name to be refused, so that I can't create files I couldn't read back, and can't plant `.prologue.html` / `.epilogue.html`.
42. As the admin, I want a volume mounted at a dot-named path (e.g. `/.b`) to stay reachable, so that a mount point I chose myself keeps working.
43. As a guest with a share link, I want dotfiles inside the shared folder to return 404, so that forwarding a link never leaks hidden files.
44. As a recipient, I want dotfiles inside a granted folder to always return 404, even when the owner can see them, so that granting a folder never exposes its hidden files.
45. As the admin, I want the dotfile block to apply over HTTP, WebDAV, archive downloads (`?zip`/`?tar`), thumbnails, FTP, SFTP and SMB alike, so that no protocol is a way around it.

### Uploads and scripts

46. As an owner, I want uploads through a grant or a share link to refuse `README.md`, `PREADME.md` and `descript.ion` in any letter case, so that visitors can't plant content that renders inside my folder listings.
47. As an account holder uploading through my own volumes, I want those names to keep working, so that I can still describe my folders.
48. As the admin, I want `no-html` in my config to make uploaded HTML, SVG and markdown be served as plain text with scripts disabled, so that a planted page can't act under the login of whoever opens it (tested: holds for `.html`, `.htm`, `.xhtml`, `.svg`, `.md`, and the markdown viewer, while copyparty's own UI keeps working).

### Share links (with `harden` on)

49. As an owner creating a share link, I want keys shorter than 12 characters to be refused, so that a link can't be guessed.
50. As the admin, I want share links whose owner account no longer exists to be deleted for good at reload, so that a reused account name doesn't revive them.
51. As the admin, I want a share link password that equals an account's password not to break reloads for everyone, if that turns out to happen (to be confirmed by a failing test first).

### Upgrades

52. As the maintainer of this fork, I want all fork behaviour that changes upstream features to sit behind one `harden` option, off by default, so that upstream's own tests keep passing without edits on every merge.
53. As the maintainer of this fork, I want every fix to an upstream bug listed in FORK.md, so that when upstream fixes it too, I know to take their version.

## Implementation Decisions

**Modules**

- **Grants store** (new module): owns the grants database (SQLite, its own file, its own schema version key, created on first use, refuses to open a newer version). Operations: create, list for an owner, list all, revoke, extend, delete permanently, and read all live grants for mounting. A grant row holds: id, owner, recipient (account name or `@group`), source path, mount name, rights (read / read + upload), created time, expiry (0 = none).
- **Grant mounting** (in the same new module, called from one hook in the reload path of the account/volume loader): after volumes and share links are built, it adds a `/shared` virtual tree. For each live grant it:
  - adds a node at `/shared/<owner>/<name>`
  - works out the recipient's account set, expanding a group from the current group table
  - resolves the source folder through the volume tree **as the owner, with exactly the granted rights** (same check share links use)
  - copies the source volume's settings, then forces "no share links", "no grants" and "dotfiles blocked" on the mount

  Outcome per grant:
  - **suspended** (owner lacks rights): skipped, row kept
  - **broken** (source missing): skipped, row kept
  - **deleted for good** (owner or named recipient account missing): row removed
  - **expired**: skipped

  Each outcome is logged. Intermediate `/shared` and `/shared/<owner>` nodes list only what the viewing account can reach (existing virtual-folder listing already filters this way).
- **Grant HTTP endpoints** (new module, dispatched from one hook in the request handler):
  - create grant (JSON POST)
  - grants page (owner's grants, or all grants for share admins)
  - revoke / extend actions
  - recipient-picker data (account names and admin-defined groups, minus the caller and the built-in all-accounts group)

  Create checks, in order:
  - grants are on
  - the source isn't under `/shared` or the share link folder
  - the volume's `grant_who` allows the caller
  - the caller holds every requested right on the source
  - the recipient exists and isn't the caller or the all-accounts group
  - the name is a single safe path segment
  - there's no clash with an existing grant from the same owner to the same recipient with the same name

  A successful create, revoke, or extend-after-expiry triggers a reload, as share links do.
- **Grants page template** (new template), linked from the control panel.
- **Grant button JS** (new script, loaded through the existing `--js-browser` hook): adds a "Grant" button beside "Share", a dialog with the recipient picker, rights, name and expiry, and calls the create endpoint. Upstream's file browser script is not edited.
- **Hardening** (new module, plus minimal hooks), active only when `harden` is on:
  - The volume path lookup refuses path parts starting with `.` below the volume root unless the account has `.` on that volume. This one check covers HTTP, WebDAV and the other protocols, because they all resolve paths through it.
  - Uploads, renames and folder creation refuse dot names without `.`.
  - Uploads through a share link refuse listing-rendered names (README/PREADME/descript.ion, any case).
  - Share link creation refuses keys under 12 characters.
  - At reload, share links whose owner account doesn't exist are deleted.
  - Archive downloads and listings already leave dotfiles out; confirm by test, don't re-implement.
- **Grant mounts always apply** dotfile blocking and the upload-name rule, whatever `harden` says.

**Options**

- `grants` (global, path of the virtual folder, e.g. `/shared`; empty = off)
- grants database location (global, like `--shr-db`)
- `grant_who` (volume setting, `no` / `a` / `auth`, default `auth`)
- `harden` (global switch, default off)

Fork code reads every new option with a default, so upstream's test configuration and argument tables don't need entries. Where copyparty requires registering an option or volume setting in its tables, keep the additions to one block.

**Fixes to upstream behaviour**

- `--shr-adm` is split into a proper list wherever fork code uses it.
- The comparisons in upstream's share link endpoints are fixed with the smallest possible edit.
- Each fix is first shown by a failing test and then listed in FORK.md.

**Constraints**

- Python 2.7 compatible: no f-strings, `from __future__` header.
- No new dependencies.
- Hooks into upstream files are as few lines as possible.
- Nothing is offered upstream.

**Docs**

- Update FORK.md: feature table row, the list of upstream edits and fixes, the recommended `[global]` (`grants: /shared`, `harden`, `no-html`), and the optional `rwmd.` for `@family`.

## Testing Decisions

- A good test drives the server the way a client does and asserts on what the client sees: status codes, listings, file contents, content types, and what survives a reload. It doesn't reach into internal structures or the database, except to set up state that can't be created through the API, such as an expired timestamp or a deleted account.
- **Main seam:** in-memory HTTP. Build an `AuthSrv` from a `Cfg` plus temporary grants and share link databases, and send requests as different accounts through the test HTTP connection. A reload is a new `AuthSrv`. Prior art: `tests/test_shr.py` (share links: create via JSON POST, then list/download/PUT as another identity) and `tests/test_dots.py` (dotfile visibility, tar contents, per-user permission sets).
- **Second seam,** only for the protocol-wide claims: the volume tree's path lookup, called directly as a given account, expecting a refusal. FTP, SFTP and SMB rely on this lookup, so they aren't started in tests.
- **Grants tests** (new test module) cover:
  - create and every refusal reason
  - recipient view and isolation between recipients
  - group membership changes across reloads
  - read vs read + upload
  - expiry and extension
  - revoke
  - suspended, broken and deleted-for-good states and their recovery
  - name clashes
  - no passing access on (no grant or share link from `/shared`)
  - dotfiles always 404 inside grants, over GET, WebDAV, archives
  - README/dot uploads refused
  - the grants page contents for owner vs share admin
  - grants off when the option is empty
  - grants working with share links off
- **Hardening tests** (new test module) cover, with `harden` on:
  - dotfile 404 for direct GET, WebDAV GET/PROPFIND, `?zip`/`?tar` and thumbnails without `.`, and access with `.`
  - dot-named mount points still reachable
  - dot-name uploads, renames and folder creation refused without `.`
  - share link dotfile 404
  - share link README uploads refused
  - short keys refused
  - deleted-owner share links removed for good
  - `no-html` content types for `.html/.htm/.xhtml/.svg/.md` and `?v`

  With `harden` off, a smoke check that the old behaviour holds, so the switch is the only difference.
- **Upstream-bug tests** (`--shr-adm` list and substring matching, share link password equal to an account password) are written first and must fail before the fix.
- **Upstream's existing tests,** especially `test_dots.py` and `test_shr.py`, must pass unchanged. They run with `harden` off.
- **The grant button JS** has no automated test (the repo has no JS test harness). Check it by hand in a browser: open the dialog, pick a recipient, create, confirm the folder shows up for the recipient, revoke.

## Out of Scope

- Recipients hiding or leaving a grant themselves.
- Notifications to recipients (email, push, in-app).
- Grants of single files or file sets.
- Granted folders in search results.
- Move, delete or admin rights through grants.
- Following a source folder when it's renamed.
- Making grants available only on some protocols.
- The separate admin app for managing accounts, groups and volumes (still planned, unchanged by this spec).
- Any changes offered to upstream.
- Measuring the cost of extra reloads on the Pi (a grant change reloads the config, same as a share link change today).

## Further Notes

- Suggested order of work: the upstream-bug tests and fixes first; then hardening behind `harden` (useful on its own, and grants build on its dotfile block); then the grants store and mounting; then endpoints and the grants page; and the JS button last.
- The recommended `[global]` for the deployment after this work: `grants: /shared`, `harden`, `no-html`, on top of FORK.md's tested config. Give `@family` `rwmd.` if members should keep access to dotfiles they upload to `/family`.
- Every account holder can see all account and group names in the recipient picker. This was accepted for a household server.
- Upstream's README acknowledges that markdown rendering "is not 100% bulletproof". `no-html` covers the markdown viewer too (tested), which is part of why it's in the recommended config.

# 11: Grant button in the file browser

**What to build:** A new script, loaded through copyparty's existing `--js-browser` option, that adds a "Grant" button beside "Share" in the file browser. It opens a dialog with:
- a recipient picker (from the recipient-list endpoint)
- read-only or read + upload
- a mount name (default: the folder's name)
- an optional expiry

It creates the grant and shows the result or the server's refusal message. Upstream's file browser script isn't edited. Spec user stories 1–5, 8, 10, 14.

**Blocked by:** 08, 10

**Status:** resolved

- [x] The button only appears when exactly one folder is selected (or for the current folder) and grants are on
- [x] The dialog shows server refusals verbatim (e.g. "you dont have all the perms you tried to grant")
- [x] Works with `no-html` and `harden` on
- [x] Manual check in a browser (no JS test harness in this repo), recorded under `## Comments` in this file: alice opens the dialog, picks bob, creates a read-only grant; bob sees the folder under `/shared/alice/`; alice revokes it on `?grants`; bob no longer sees it. Repeat with `@family` and read + upload
- [x] FORK.md: the "user shares a folder with another user" row becomes ✅; the recommended config shows `grants: /shared` and the `--js-browser` setting

## Comments

Manual check, 2026-11-14, Chrome against `python -m copyparty` from source on 127.0.0.1, with `grants: /shared`, `harden`, `no-html`, `usernames`, `wram` (the test volumes were on tmpfs) and `js-browser: /.cpr/w/grantbtn.js`. Accounts alice, bob, carol; `family: alice, bob`; `[/home/${u}]` (`A`), `[/family]` (`rwmd: @family`), `[/common]` (`r: @acct`).

- alice, `/home/alice/`: the button shows with nothing selected (current folder), with `photos/` selected, and hides when a file is selected
- the picker lists `bob`, `carol`, `@family` (no alice, no all-accounts group)
- alice selects `photos/`, picks bob, read-only, name `photos` (the default), no expiry → "granted /home/alice/photos/ to bob (read-only, expires never), they find it at /shared/alice/photos/"
- same again → "grant refused: you already gave 'bob' a grant named 'photos'; pick another name"
- `/common/docs/`, read + upload → "grant refused: you dont have all the perms you tried to grant"
- alice grants `photos/` to `@family`, read + upload, name `album`, expires in 2 days → created, expiry shown
- bob: the control panel lists `/shared/alice/photos/` and `/shared/alice/album/`; the tree shows `shared/alice/{album,photos}`; `photos` is read-only with `a.txt`, `album` has read + write; a PUT into `album` lands in alice's folder (201), into `photos` is 403; no grant button anywhere under `/shared/`
- alice, `?grants`: both rows `active`; revoke `photos` → bob's `/shared/alice/` lists only `album/`, `photos/a.txt` is 403; revoke `album` → bob's `/shared/` is 403 and `/` lists no `shared/`

Found on the way (not caused by this ticket, listed under known gaps in FORK.md):

- opening `/shared/` or `/shared/alice/` directly as a page is a 403; upstream does the same for its own folders with no path on disk (`/home/`). Reaching them from `/` and the tree works
- the reply to bob's PUT into `album` says `http://127.0.0.1:3923/home/alice/photos/up.txt`, alice's own path
- upstream ends every error reply with an empty `URL:` line; the dialog strips it so only the server's message shows

After review, rechecked behind `rp-loc: /cpp` (`js-browser: /cpp/.cpr/w/grantbtn.js`): the dialog shows `/home/alice/` and `/home/alice/photos/` without the prefix, and the default names are `alice` and `photos`. At `/` the name starts empty with a placeholder (the server refuses an empty name). A refusal for the name `a&b` reads `'a&b'`, not `'a&amp;b'` (the server html-escapes its replies; the dialog decodes, then escapes once).

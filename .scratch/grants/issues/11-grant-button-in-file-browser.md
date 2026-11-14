# 11: Grant button in the file browser

**What to build:** A new script, loaded through copyparty's existing `--js-browser` option, that adds a "Grant" button beside "Share" in the file browser. It opens a dialog with:
- a recipient picker (from the recipient-list endpoint)
- read-only or read + upload
- a mount name (default: the folder's name)
- an optional expiry

It creates the grant and shows the result or the server's refusal message. Upstream's file browser script isn't edited. Spec user stories 1–5, 8, 10, 14.

**Blocked by:** 08, 10

**Status:** ready-for-agent

- [ ] The button only appears when exactly one folder is selected (or for the current folder) and grants are on
- [ ] The dialog shows server refusals verbatim (e.g. "you dont have all the perms you tried to grant")
- [ ] Works with `no-html` and `harden` on
- [ ] Manual check in a browser (no JS test harness in this repo), recorded under `## Comments` in this file: alice opens the dialog, picks bob, creates a read-only grant; bob sees the folder under `/shared/alice/`; alice revokes it on `?grants`; bob no longer sees it. Repeat with `@family` and read + upload
- [ ] FORK.md: the "user shares a folder with another user" row becomes ✅; the recommended config shows `grants: /shared` and the `--js-browser` setting

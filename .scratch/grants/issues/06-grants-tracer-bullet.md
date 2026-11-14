# 06: Grants tracer bullet: Alice grants a folder to Bob, read-only

**What to build:** The thinnest end-to-end grant:
- `grants: /shared` in `[global]` turns grants on.
- Alice sends a create-grant request for one of her folders, naming account `bob`, read-only, with a mount name.
- The grant is stored in its own grants database (with its own schema version; the location can be set like `--shr-db`).
- A reload follows, and Bob can browse and download the folder at `/shared/alice/<name>` over HTTP and WebDAV.
- Carol sees nothing under `/shared`.
- Dotfiles inside the grant always return 404, regardless of `harden`.
- Grants work when share links are off.

See ADR-0001 and spec user stories 1, 5, 24, 25, 29, 30, 36–38, 44.

**Blocked by:** 03

**Status:** resolved

- [x] The grant store and mounting live in new fork modules; the upstream hooks are one call in the reload path and one in request dispatch
- [x] The grants database is created on first use, records a schema version, and refuses to open a newer version (like the share link database)
- [x] Mounting resolves the source folder as the owner with exactly the granted rights (the same check share links use) and copies the source volume's settings
- [x] Tests (new grants test module, in-memory HTTP seam): after create plus reload, bob lists `/shared/` → `alice/`; lists `/shared/alice/` → `<name>/`; downloads a file
- [x] Tests: carol gets nothing listed under `/shared/` and a refusal on the file URL; a guest is refused
- [x] Test: WebDAV PROPFIND and GET work for bob
- [x] Test: `.env` inside the grant → 404 for bob, with `harden` off and with alice holding `.`
- [x] Test: `grants` empty → no `/shared` and the create endpoint refuses
- [x] Test: `shr` empty and `grants: /shared` → grants still work
- [x] Test (path-lookup seam): bob resolves the grant path; carol is refused
- [x] FORK.md: options listed, upstream hook lines listed

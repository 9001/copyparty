# 05: `harden`: share links

**What to build:** With `harden` on, share links (used by guests) follow the fork's rules:
- dotfiles inside a share link return 404, even if the owner has `.`
- uploads through a share link refuse `README.md`, `PREADME.md` and `descript.ion` in any letter case
- keys shorter than 12 characters are refused when a share link is created
- share links whose owner account no longer exists are deleted for good at reload, so a reused account name doesn't revive them

Also confirm, in tests, the `no-html` protection the deployment relies on. Spec user stories 43, 46–50.

**Blocked by:** 03, 04

**Status:** ready-for-agent

- [ ] Tests (`harden` on): a guest GET of `/share/<key>/.env` → 404 when the owner has `A`; archive download contains no dotfiles
- [ ] Tests: a write share link refuses `README.md`, `readme.MD`, `PREADME.md`, `descript.ion` and dot names; other names upload fine
- [ ] Test: creating a share link with an 11-character key is refused with a clear message; 12 characters is accepted
- [ ] Test: owner account removed from the config → after reload the share link's row is gone from the share link database and doesn't return when an account with that name is added again
- [ ] Tests (`no-html` on): `.html`, `.htm`, `.xhtml`, `.svg`, `.md` and the markdown viewer are served as `text/plain` with scripts disabled; copyparty's own file browser page is still served as HTML with its script
- [ ] Test, `harden` off: all of the above behave as upstream
- [ ] Upstream `tests/test_shr.py` passes unchanged
- [ ] FORK.md: recommended `[global]` gains `harden` and `no-html`; note on giving `@family` `rwmd.` if members should keep their own dotfiles

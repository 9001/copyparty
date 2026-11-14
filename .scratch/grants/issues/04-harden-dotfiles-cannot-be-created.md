# 04: `harden`: dotfiles can't be created without `.`

**What to build:** With `harden` on, an account without `.` on a volume can't create anything with a dot name there. That covers uploads (up2k and basic uploader/PUT), renaming or moving to a dot name, and creating a folder with a dot name. It keeps reading and writing consistent, and stops visitors planting `.prologue.html` / `.epilogue.html`. See ADR-0002 and spec user story 41.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Tests (`harden` on, account with `rw` but no `.`): PUT `.env` refused; up2k upload of `.epilogue.html` refused; new folder `.x` refused; renaming `a.txt` to `.a.txt` refused; uploading into an existing dot folder refused
- [ ] Tests: an account with `.` can do all of the above
- [ ] Test, `harden` off: upstream behaviour unchanged
- [ ] Copyparty's own temporary dot-names during upload (e.g. `--dotpart` partial files) keep working
- [ ] Upstream tests pass unchanged

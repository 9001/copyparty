# about this fork

Personal fork of [9001/copyparty](https://github.com/9001/copyparty) (forked at v1.20.26).
Goal: replace Nextcloud with copyparty on a **Raspberry Pi Zero 2W**, and add the missing
piece: **managing users, groups and folder permissions from the browser**.

Research behind these notes was done in Oct–Nov 2026; numbers and issue states are from then.


## the rule that shapes everything

upstream's [CONTRIBUTING.md](./CONTRIBUTING.md) says **"do not use AI / LLM when writing code"**.
This fork is written with AI help, so:

* nothing from this fork can be offered upstream as a PR
* keep fork changes in **new files** where possible and touch upstream files at as few
  places as possible, so merging upstream releases stays cheap
* the licence is fine with this: copyparty is MIT, and every bundled dependency is
  MIT / BSD / ISC / Apache-or-MPL / OFL (see `copyparty/res/COPYING.txt`); keep `LICENSE`
  and `COPYING.txt` intact


## target: what we need from it

the Nextcloud features we want to keep:

| want | copyparty today |
|---|---|
| upload | ✅ up2k: chunked, resumable, no size limit even behind Cloudflare's 100 MB request cap |
| login | ✅ accounts in config; `--usernames` for user+password login |
| manage users | ❌ **config file only** -- edit, then reload (`kill -USR1` / `[reload cfg]` button) |
| own folder per user | ✅ `[/home/${u}]` volume, one block covers all users |
| shared folders | ✅ admin-defined volume + `[groups]` |
| **user shares a folder with another user** | 🚧 grants (`grants: /shared`), fork-only; read-only or read + upload, created by a JSON POST so far (no button yet); owners revoke and extend them on `?grants`, linked from the control panel |
| share links | ✅ `shr: /share`; password, expiry, optional upload; owner manages them in the control panel |
| stream video | ✅ served as-is with range requests; no video transcoding (fine for the Pi) |
| edit text | ✅ text viewer + two markdown editors |
| edit docs | ⚠️ `--wopi` can hand off to a Collabora server running elsewhere; untested |


## hardware limits (Pi Zero 2W)

* 512 MB RAM, 4× Cortex-A53 @ 1 GHz, **one USB 2.0 port** (~30–35 MB/s, shared with any
  USB ethernet), 2.4 GHz wifi only
* the bottleneck is disk + network, not copyparty
* use a **powered** disk/hub: upstream #1507 (Pi 5) died silently with a bus-powered disk


## memory: what we measured and what others report

own benchmark (x86 docker, 50k files + 20 × 12-megapixel jpegs, 4 thumbnails at a time):

| | copyparty | FileBrowser Quantum v2.0.1 |
|---|---|---|
| idle, 50k files indexed | 38 MiB | 38 MiB |
| peak while thumbnailing | 111 MiB | 209 MiB |
| held afterwards | 36 MiB | 189 MiB |

copyparty stays small because thumbnails run in a **separate ffmpeg/pillow process** and the
index lives in **sqlite on disk**. Quantum decodes images in-process and Go keeps the freed heap.

upstream reports: ~30 MiB idle / ~50 MB RSS after a 1.5 GB upload (discussion #1310);
a Pi Zero 2W user with 3 accounts and no memory complaints (#1035).

the real risk is the image libraries copyparty calls: one animated AVIF took **~7 GB** through
libvips → imagemagick (#1556). Recommended `[global]` for the Zero 2W, from the maintainer's
own replies in #1332 / #746 / #1556:

```
  th-mt: 1                 # one core for thumbnails
  mtag-mt: 1               # one core for media tags
  hash-mt: 1               # one core for hashing
  th-dec: pil,ff,raw       # leave vips out (the 7 GB AVIF case)
```

do **not** enable mimalloc (`LD_PRELOAD`) in the arm64 docker image; it crashes on start (#213).


## security notes

* copyparty 2026 advisories: 10, all Low/Moderate (XSS, FTP path traversal, share-key mixups,
  sftp edge cases, windows/mac shadowing). Most are in protocols we don't need:
  **keep FTP/SFTP/SMB off**, HTTP(S) only.
* FileBrowser Quantum (the alternative we rejected) had 31 advisories in 2026, 4 Critical / 14 High,
  mostly in its core auth and share code.
* default password storage is **plain text** in the config (`ah-alg: none`). Turn on hashing
  (`ah-alg`, generate with `--ah-cli` / `--ah-gen`). Check argon2's memory cost on the Pi before
  choosing it over scrypt -- not measured yet.
* get copyparty only from official sources (github releases, PyPI, `copyparty/*` on docker hub,
  copyparty.eu). A "maintained fork… security patches… pip install" repo showed up in the fork
  list in Nov 2026 and was deleted soon after.


## tested config (users, groups, home folders, shares)

tested on v1.20.26 in docker; every row in the table under it was checked with curl.

```
[global]
  e2dsa            # index files (needed for search and share cleanup)
  shr: /share      # share links
  chpw             # users may change their own password (button is in the control panel)
  usernames        # log in with username + password

[groups]
  family: alice, bob

[accounts]
  admin: adminpw1
  alice: alicepw1
  bob: bobpw111
  carol: carolpw1

[/home/${u}]       # private folder per user, created automatically
  /srv/home/${u}
  accs:
    A: ${u}
    a: admin

[/family]          # shared by a group
  /srv/family
  accs:
    rwmd: @family
    A: admin

[/common]          # everyone logged in can read, admin writes
  /srv/common
  accs:
    r: @acct
    A: admin
```

| check | result |
|---|---|
| alice/bob see | `common/ family/ home/`; in `home/` only their own folder |
| carol sees | `common/ home/` |
| bob reads alice's file | 403 |
| carol reads `/family` | 403 |
| alice shares a file with password + 60 min expiry | link works only with the password |
| bob shares alice's file | refused: "you dont have all the perms you tried to grant" |
| add a user to the file + `kill -USR1` | works without restart; home folder appears |

gotchas found while testing:

* the `copyparty/ac` docker image already loads every `*.conf` in `/cfg`; also passing
  `-c /cfg/x.conf` loads it twice and fails with "multiple filesystem-paths mounted" (#1083)
* volumes on tmpfs lose write access unless `wram` is set (safety check; irrelevant on a real disk)


## `harden`: fork-only hardening switch

`harden` (`--harden`, or `harden` under `[global]`) is off by default; with it off, behaviour is
exactly upstream's. Our config turns it on. With it on (see `docs/adr/0002`):

* any path with a part starting with `.` **inside** a volume is 404 for an account without the `.`
  permission on that volume -- direct GET, WebDAV, `?zip`/`?tar`, thumbnails, and the
  `VFS.get` lookup that FTP/SFTP/SMB/TFTP use. Accounts with `.` (e.g. `A`, or `rwmd.`) keep full access
* a volume mounted at a dot-named path (e.g. `/.b`) stays reachable; the rule applies below its root
* `GET`/`HEAD` of `/.cpr/...` is exempt: copyparty always answers it with its own web resources
* creating a dot name without `.` is 404 as well, so nobody can plant `.prologue.html` /
  `.epilogue.html`: every other request method on a dot path (PUT, MKCOL, DELETE, OPTIONS, ...), a
  move/copy/rename *to* a dot path, mkdir, a basic (bup) upload, and an up2k upload whose name (sent
  in the handshake body) starts with a dot. Copyparty's own temporary names (`--dotpart`) still work
* moving/copying a folder that holds dotfiles the account can't see at the source or the destination
  is refused (403) up front, so it never stops half-way
* not covered: SMB with `--smba` (upstream maps every SMB user to its internal superuser, which
  bypasses all permissions anyway); keep SMB off

share links (`/share/<key>/...`, used by guests), with `harden` on:

* dotfiles inside a share link are 404, even if the owner gave the link `.` (allowed upstream when
  the owner has `.`, e.g. `A`), and even with `--ed` or the `dots` volflag; links already in the
  database lose `.` at the next reload. Upstream's link archives (`?zip`/`?tar`) already leave
  dotfiles out
* writes through a share link refuse `README.md`, `PREADME.md` and `descript.ion` in any letter
  case (403), since copyparty renders them inside the owner's folder listings: PUT (also WebDAV),
  bput, up2k, new markdown file, the markdown editor's save, and copying a file to that name
  (`?copy=`, WebDAV `COPY`). Dot names are refused like everywhere else. The owner can still
  upload them in their own volume
* creating a share link with a key shorter than 12 characters is refused (400); the web UI's
  random keys are 12 characters
* at reload, share links whose owner is no longer an account are deleted from the share link
  database (`sh` and `sf` rows), so a new account with the same name doesn't get them back. An
  owner who still exists but lost access keeps the row (upstream only hides the link until access
  returns). Skipped with IdP headers (`--idp-h-usr`), since IdP accounts aren't in the config
* code: `copyparty/fork_harden.py`, tests: `tests/test_fork_harden.py`,
  `tests/test_fork_harden_shr.py`

recommended `[global]` for the deployment, on top of the tested config below (not yet tried in
docker):

```
  harden           # the rules above
  no-html          # uploaded .html/.htm/.xhtml/.svg/.md and the markdown viewer (?v) are served
                   # as text/plain with script-src 'none'; copyparty's own UI keeps working
```

`harden` makes `/family` dotfiles 404 for members, since `rwmd` has no `.`. Give `@family`
`rwmd.` if members should keep access to dotfiles they upload there.


## upstream edits

every place this fork changes an upstream file. On a merge conflict, resolve each one as noted.

| fix | upstream lines touched | fork files | on conflict |
|---|---|---|---|
| fork modules ship in the sfx build | `scripts/sfx.ls`: one line per new `copyparty/fork_*.py` (and per fork file in `copyparty/web/`) | -- | keep both sides |
| grants (`--grants`, `--grants-db`) | `authsrv.py`: one import + `mount_grants(self, vfs, acct)` as the last line of `_reload` (marked `# fork`; it needs every volume's final flags, js and share links); `httpcli.py` `handle_post_json`: one import + `if "grant" in self.uparam: return handle_grant(self, body)` right after the `share` dispatch (marked `# fork`); `httpcli.py` `handle_get`: `if "grants" in self.uparam: return tx_grants(self)` right after the `shares` dispatch, and `handle_post`: `if "egrant" in self.uparam: return handle_egrant(self)` right after the `eshare` dispatch (both marked `# fork`, sharing the import); `web/splash.html`: an "edit grants" link (`id="yg"`) right after "edit shares"; `scripts/sfx.ls`: `web/grants.html` and `web/grants.js`; `httpcli.py` `run`: the `http_request` line (see `harden`); `__main__.py` `add_share`: the `--grants` and `--grants-db` options; `cfg.py` `flagcats["others"]`: one `grant_who=auth` line after `shr_who=auth` (registers the volflag, so copyparty doesn't warn that it's unrecognized) | `copyparty/fork_grants.py`, `copyparty/fork_harden.py` (dot rule and upload-name rule also on grant volumes, `harden_nodes`), `copyparty/fork_util.py` (`grants_top`), `copyparty/web/grants.html`, `copyparty/web/grants.js` (the page loads its own template through `httpsrv.load_jinja2_resource` and adds it to `hsrv.j2` as `fork_grants` on first use, so it renders through `HttpCli.j2s` while httpsrv's template list is untouched; `fork_grants.py` also adds both files to upstream's `RES` set at import, which is what lets `.cpr/w/grants.js` be served), `tests/test_fork_grants.py` | keep both sides; grant volumes mirror how `_reload` maps a share link (`shr_src`, `_get_share_src`, `shr_all_aps`, hidden `.hist` and subvolumes), so if upstream changes that block, port the change to `_grant_vol` and rerun `tests/test_fork_grants.py`. `_route` replaces `get`, `_get` and `can_access` on the root volume instance; if upstream adds another root-level lookup that walks `nodes` itself (`_find`), route it too, or it sees the root's listing-only copy (no path on disk, so no files leak, but wrong rights). The listing workaround in `http_request` relies on `tx_ls_vols` reading `self.rvol` and on `run` setting `can_*` before the hook. `share_pw_accounts` copies how the share loader in `_reload` names the made-up `s_...` account of a share link password (`"s_%s" % ub64enc(sha512(pw))[4:16]`); if upstream changes that, change it too, or grants could go to anyone holding a share link password (`test_refused_to_a_share_link_password` catches it). If upstream renames `hsrv.j2`, `j2s`, `load_jinja2_resource` or `RES`, the grants page breaks: `test_page_*` catch the template side; a 404 on `/.cpr/w/grants.js` (no test) means `RES` moved |
| `--shr-adm` takes a real comma-separated list of exact names (upstream compared the whole string in `?shares` / `?eshare`, and used a substring test in the active-downloads list, so `adm` matched `admin`) | `svchub.py`: one import + `args.shr_adm = split_names(args.shr_adm)`; `httpcli.py` `tx_shares` / `handle_eshare`: `!=` -> `not in`; `authsrv.py` `cgen`: `shr_adm` added to the `csv` set so `--cgen` still prints it | `copyparty/fork_util.py` (`split_names`), `tests/test_fork_shr_adm.py` | **take theirs if upstream fixes it**, then remove all of the fork side: the `split_names` line + import in `svchub.py`, `shr_adm` in cgen's `csv` set (unless upstream keeps a list too), and `split_names` (and `fork_util.py` + its `sfx.ls` line, if nothing else uses them); keep the test if it still passes |
| `harden`: dotfiles inside a volume are 404 without `.` | `authsrv.py`: one import + `harden_vfs(self.args, vfs)` in `_reload` right after the loop that ends with the `dots` volflag adding to `udot` (marked `# fork`; it wraps each volume's `get`, so it must come after the `xvd` block, and it clears `udot` on share links, so after the `dots` loop); `httpcli.py` `run`: one import + `if http_request(self): return self.tx_404() and False` right after `self.rem = rem` (the per-request lookup uses `VFS._get`, not `get`; `http_request` lives in `fork_grants.py` and calls `fork_harden.http_refused` first); `up2k.py`: one import + a `refuse_dot_tree(...)` walk before the folder walk in `handle_mv` and in `handle_cp` (2 lines each, marked `# fork`); `httpcli.py` `handle_post_json`: `refuse_dot_name(...)` right after `vfs.sanitize_fn(name, rem)` (marked `# fork`, import shared with the `fork_harden` one); `httpcli.py` `handle_share`: `refuse_short_key(self.args, skey)` right after the illegal-character check (marked `# fork`, same import); `authsrv.py` `_reload`, share loader: `purge_ownerless_shares(self.args, db, acct, self.log)` right before the first `for row in cur.execute("select * from sh")` loop (marked `# fork`, import shared with `harden_vfs`); `__main__.py` `add_safety`: the `--harden` option. Share link dotfiles and upload names need no extra edit: `harden_vfs` clears `udot` and wraps `sanitize_fn` on each share link volume, and the wrapped `get` refuses the listing names on write lookups into a share link | `copyparty/fork_harden.py`, `tests/test_fork_harden.py`, `tests/test_fork_harden_shr.py` | keep both sides; if upstream renames `VFS.get` / the `self.vn, self.rem` lookup in `run`, move the hook to the new spot and rerun `tests/test_fork_harden.py` and `tests/test_fork_harden_shr.py` (the share link rules set `VFS.sanitize_fn` / `axs.udot` by name, so a rename upstream would silently stop them; only the tests notice). `_refuse_dots` reads `err` by `VFS._get`'s argument order (6th after `uname`, default 403); recheck it if that signature changes. **If upstream adds a real dotfile block, take theirs** and remove the fork side |
| a share link password equal to an account's password no longer breaks every reload (upstream loaded it as a made-up `s_...` account with the same password, which tripped the "same password" check; reload/restart then failed for everyone). The share is now granted to the account that owns that password, so the password logs in as that account and opens the share (that account may not be the share's owner: if bob sets alice's password on a share, alice's login also gets the share) | `authsrv.py` `_reload`, share loader: a `pw2u` password->account map before the loop, and an `if s_pw.strip() in pw2u: sun = pw2u[s_pw.strip()]` branch before the `s_` account is made | `tests/test_fork_shr_pw.py` | **take theirs if upstream fixes it**, then drop the `pw2u` line and the extra branch; keep the test if it still passes |


## grants: fork-only folder sharing between accounts

see `docs/adr/0001` and `.scratch/grants/spec.md`. Work in progress: tickets 06 (the tracer
bullet), 07 (rights and refusals), 08 (groups), 09 (lifetime across reloads) and 10 (the grants
page) are done; the button in the file browser is not.

options (`[global]`):

* `grants: /shared` (`--grants`): the virtual folder where recipients find what was granted to
  them, at `/shared/<owner>/<name>`; empty (the default) = grants off. Works with share links
  (`shr`) off
* `grants-db` (`--grants-db`, default `grants.db` next to `shares.db`): the grants database. It
  has its own schema version (`kv` table, `sver`), is created on the first grant, and copyparty
  refuses to start on a newer version

volflag:

* `grant_who` (`no` / `a` / `auth`, default `auth`): who can create grants of folders in this
  volume: nobody, accounts with `a` there, or any account. Independent of `shr_who`, so a volume
  can allow grants and forbid share links, or the other way round. Any other value = nobody

what works so far:

* an owner creates a grant with `POST /?grant`, JSON body
  `{"vp": "/home/alice/proj/", "rcpt": "bob", "name": "proj", "perms": ["read"], "exp": 60}`;
  a reload follows. `exp` is an optional expiry in minutes, like share links; missing, empty or
  0 = never. `rcpt` is an account, or `@<group>` for a group from `[groups]` /
  `--grp`. `perms` is `["read"]` (read-only) or `["read", "write"]` (read + upload); the
  recipient also gets `g`. Move, delete, admin and `.` are never possible through a grant.
  Refused, each with a 400:
  * grants off; not logged in
  * any other `perms`
  * an `exp` that isn't a whole number of minutes from 0 to 10^9
  * a list of paths in `vp`, or a `files` selection (one folder only); a single file
  * a source under `/shared` or under the share link folder (also through `..`, or any path
    that resolves to a share link or grant volume)
  * a hidden source (any path part starting with a dot; such a row is also never mounted)
  * rights the owner doesn't hold on the source (write included)
  * the volume's `grant_who` doesn't allow the caller
  * the caller themselves; `*` or `@acct` (the `--grp-all` group, whatever it is named); an
    `@<group>` that isn't in the config; anything else that isn't an account from the config,
    including the made-up `s_...` account a share link password logs in as (anyone with that
    password could use it; such a row is also never mounted)
  * a name that isn't one path segment: empty, starting with a dot, a slash or backslash, a
    control character, leading or trailing spaces, over 255 characters
  * the same owner + recipient + name as an existing grant (expired ones too, since they can be
    extended); checked in the same SQL statement as the insert
  * the same owner + name as an existing grant whose recipient reaches any of the same accounts
    today: bob directly and `@family` (with bob in it), or two groups sharing a member other than
    the owner. Pick another name
* a group grant is worked out again at every reload from the group in the config: members
  added there get it, members removed lose it. The owner, if a member, gets no mount of their own
  folder. A group removed from the config gives nobody access, but the row stays (the owner can
  revoke it; a group by that name later gets the grant back). If a group gains a member who
  already has a grant by that name from the same owner, that member keeps one: the grant naming
  them wins over a group grant, otherwise the oldest; the other is skipped for them and logged.
  Only grants that mount compete, so if the winner expires or is suspended or broken, the other
  one shows up at that path instead (a different folder, maybe with different rights)
* groups are only the config's (`[groups]` / `--grp`), and members only config accounts: IdP
  groups and IdP-only users get no group grants. A group whose only members are the owner, or
  names that aren't accounts, is accepted but mounts for nobody (logged)
* at every reload each grant is resolved through the volume tree as its owner with exactly the
  granted rights (like share links), and mounted with the source volume's settings, minus share
  links (`shr_who: no`) and indexing flags. A grant whose owner lost those rights (suspended), or
  whose source folder is gone (broken), is skipped and logged; its row stays, so it comes back
  when the owner regains the rights or a folder appears at that path. An expired grant is skipped
  and logged; its row stays (for the owner to extend on the grants page)
* a grant whose owner, or whose named recipient account, is no longer an account in the config is
  deleted from the database for good at the next reload, so an account created later with the
  same name doesn't inherit it. A group recipient never causes this (a missing group just mounts
  for nobody). With IdP headers on (`have_idp_hdrs`) nothing is deleted, since IdP accounts
  aren't in the config; such grants are only skipped
  * careful: an account dropped from `[accounts]` by mistake loses every grant it owns or
    names, at the first reload; putting it back doesn't restore them
  * with multiprocessing (`-j` above 1) every worker reloads, so the same removal can be logged
    more than once; the delete itself is harmless to repeat
* the log has a line for every create, expiry, suspension, break and permanent removal, naming
  the grant's id, owner, recipient, path, mount name, rights and expiry. The states are worked
  out again at every reload, so an expired, suspended or broken grant is logged at each reload
  for as long as it stays that way, not only when it changes
* the recipient browses and downloads over HTTP and WebDAV; others see nothing under `/shared`
* each recipient has their own `/shared` tree, so alice can grant bob a `proj` and carol a
  different `proj`; both see `/shared/alice/proj`, each their own folder. The root's path lookups
  (`VFS.get`, `VFS._get`, `VFS.can_access`) are replaced on the root volume at reload so that
  `/shared/...` resolves in the asking account's tree. The `/shared` under the root only holds
  folders with no path on disk, used for listings
* dotfiles inside a grant are always 404 for the recipient, even with `harden` off and even when
  the owner holds `.`
* uploads through a grant refuse dot names and `README.md` / `PREADME.md` / `descript.ion` in any
  case, whatever `harden` says (the share link rules, applied by `harden_nodes`); the owner uploading
  through their own volume is unaffected
* the grants page, `GET /?grants` (template `web/grants.html` + `web/grants.js`, linked from the
  control panel as "edit grants" when grants are on), lists the caller's grants: owner,
  recipient, source folder, the name it appears as, rights, expiry and state. Accounts in
  `--shr-adm` see every grant. States are worked out when the page loads, with the same check as
  a reload: `active`, `expired`, `suspended`, `broken`, or `no members` (a group grant whose
  group is gone or has nobody but the owner; it comes back with the group); old rows on a
  hidden folder show `hidden folder`. Guests get a 401, and all of it is a 400 with grants off
  * `POST /?egrant=rm&gid=N` revokes (the row is deleted, a reload follows);
    `POST /?egrant=MIN&gid=N` extends the expiry by MIN minutes, counted from now if it already
    expired (a reload follows then, which brings it back). A grant with no expiry can't be
    extended. The owner may do both; a `--shr-adm` account may only revoke (spec story 32);
    others get a 403
  * `GET /?grants=rcpts` returns `{"accounts": [...], "groups": ["@family", ...]}`: who a grant
    can go to, without the caller, the all-accounts group (`--grp-all`) and share link password
    accounts. Every account holder sees every account and group name (accepted in the spec)
* grants are not in an account's list of readable volumes (`aread`), so search, the upload list
  and FTP/SFTP volume lists never see them; listings of `/`, `/shared/` and `/shared/<owner>/`
  add them for that one request

known gaps:

* expiry only takes effect at a reload: an expired grant stays mounted until something reloads
  the config (another grant change, a share link change, `SIGUSR1`, a restart). Share links have
  a timer for this; grants don't yet. The grants page already shows such a grant as `expired`

* with a **readable root volume** (`[/]`), `/` doesn't list `shared/` (upstream leaves folders
  that have no path on disk out of a real folder's listing); `/shared/` itself works. Our config
  has no root volume
* a symlink inside the granted folder is followed, as in share links: a link to `../priv.txt`
  serves that file to the recipient, even though it is outside the granted folder. `xvol` only
  stops links that leave the *volume*, so it doesn't help within a home folder. Owners must not
  keep links out of a folder they grant (not enforced yet)

code: `copyparty/fork_grants.py`, tests: `tests/test_fork_grants.py`


## the user-management gap, upstream's position

* #232 "User management through UI with a SQLite DB" -- open; maintainer: "a pipe dream"
* #57 config UI -- open since 2023; Aug 2025: not this year, maybe not next; he has little
  personal use for it
* discussion #1036 -- "at some point there will be a config UI… a long time until that happens"
* #657 -- users posted scripts that append hashed accounts to the config; not merged
* the closest thing that exists: the **UI V1.5** work (PR #1453, `tilse/copyparty-uiV1.5`,
  shipped as `copyparty/ac:beta`) has a config GUI at `?config` -- but it only *builds* config
  text in the browser; it does not read or write the live config
* no fork or add-on found (Nov 2026, top 200 forks by stars + newest 100 + repo search) that does
  live user management or user-to-user folder sharing


## plan: admin app beside copyparty

copyparty already has the two hooks we need: it loads every `.conf` in its config dir, and
`SIGUSR1` reloads accounts + volumes without a restart.

```
browser → admin app
            ├─ owns one generated file, e.g. /cfg/users.conf  ([accounts], [groups], volumes)
            ├─ hashes passwords with copyparty's own --ah-gen (same format copyparty expects)
            ├─ validates (no duplicate mounts) before writing
            └─ SIGUSR1 → copyparty reloads
```

* never edit the hand-written config; the generated file is the app's only output
* password resets: `chpw.json` stores `(user, original_config_pw, new_pw)`; a user's own change
  only applies while the config still has `original_config_pw` (`AuthSrv.setup_chpw` in
  `copyparty/authsrv.py`). So **changing the password in the config is a reset** -- it wins
  over the user's change.
* reach the admin app over Tailscale only; never expose it next to public share links
* user-to-user folder sharing would be modelled as: owner picks a folder + user/group →
  app writes an extra volume (or `accs` entry) → reload
* zero-code alternative considered: LLDAP (user UI) + Authelia in front, copyparty in IdP mode
  (`--idp-h-usr`, `--idp-h-grp`). Two extra services on 512 MB, memory not measured.


## related homelab context

the home PC already runs Nextcloud AIO behind a VPS Traefik over WireGuard; the home↔VPS path
(Telkom → Rumahweb) loses 66–90% of packets, so public access should go via Cloudflare Tunnel or
a different VPS -- up2k's chunking handles Cloudflare's 100 MB request cap.

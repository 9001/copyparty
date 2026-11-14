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
| **user shares a folder with another user** | ❌ **missing** -- only share links (not tied to an account) or ask the admin |
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


## upstream edits

every place this fork changes an upstream file. On a merge conflict, resolve each one as noted.

| fix | upstream lines touched | fork files | on conflict |
|---|---|---|---|
| fork modules ship in the sfx build | `scripts/sfx.ls`: one line per new `copyparty/fork_*.py` | -- | keep both sides |
| `--shr-adm` takes a real comma-separated list of exact names (upstream compared the whole string in `?shares` / `?eshare`, and used a substring test in the active-downloads list, so `adm` matched `admin`) | `svchub.py`: one import + `args.shr_adm = split_names(args.shr_adm)`; `httpcli.py` `tx_shares` / `handle_eshare`: `!=` -> `not in`; `authsrv.py` `cgen`: `shr_adm` added to the `csv` set so `--cgen` still prints it | `copyparty/fork_util.py` (`split_names`), `tests/test_fork_shr_adm.py` | **take theirs if upstream fixes it**, then remove all of the fork side: the `split_names` line + import in `svchub.py`, `shr_adm` in cgen's `csv` set (unless upstream keeps a list too), and `split_names` (and `fork_util.py` + its `sfx.ls` line, if nothing else uses them); keep the test if it still passes |
| a share link password equal to an account's password no longer breaks every reload (upstream loaded it as a made-up `s_...` account with the same password, which tripped the "same password" check; reload/restart then failed for everyone). The share is now granted to the account that owns that password, so the password logs in as that account and opens the share (that account may not be the share's owner: if bob sets alice's password on a share, alice's login also gets the share) | `authsrv.py` `_reload`, share loader: a `pw2u` password->account map before the loop, and an `if s_pw.strip() in pw2u: sun = pw2u[s_pw.strip()]` branch before the `s_` account is made | `tests/test_fork_shr_pw.py` | **take theirs if upstream fixes it**, then drop the `pw2u` line and the extra branch; keep the test if it still passes |


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

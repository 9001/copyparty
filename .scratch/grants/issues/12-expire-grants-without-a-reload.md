# 12: Expire grants without waiting for a reload

**Problem:** A grant's expiry is only checked when the config reloads (`mount_grants` skips grants whose `t1` has passed). Between reloads, a grant past its expiry stays mounted: the recipient can still browse, download and (with read + upload) upload. Nothing reloads by itself, so on a quiet server this can last until the next grant or share link change, `SIGUSR1`, or a restart, possibly days. Since ticket 10 the grants page already shows such a grant as `expired`, so the owner sees "expired" while the recipient still has access.

This breaks spec user story 8 ("set an optional expiry on a grant, so that temporary access ends by itself") and story 28 ("expired … grants to simply disappear from my tree").

**Found:** while doing ticket 10 (2026-11-14). The behaviour dates from ticket 09. FORK.md lists it under the grants section's "known gaps".

**Blocked by:** none

**Status:** resolved

## How share links handle it

Upstream's up2k rescanner thread (`Up2k._sched_rescan` in `copyparty/up2k.py`) calls `_check_shares` on every pass when `--shr` is on. That function:

- finds shares whose `t1` has passed and are still mounted, and runs `hub.reload` in a daemon thread (`"sharedrop"`)
- deletes shares that expired more than `--shr-rt` minutes ago, for good
- returns the time of the next expiry, so the rescanner wakes up then

## To discuss

- **Where the check lives.** The share check is inside `up2k.py`. For grants, that means a hook into an upstream file (the rescanner loop), or a fork-owned timer thread started from `SvcHub` / at the first `mount_grants`. With `-j` above 1, the timer must run once (in the hub), not once per worker.
- **Cost on the Pi.** Each expiry triggers a full reload, as with share links. Grants expiring close together could be batched into one reload.
- **Permanent deletion of old expired grants.** Share links are deleted `--shr-rt` minutes after they expire. Expired grants are currently kept forever so the owner can extend them from the grants page. Should they be deleted after some time too (`--shr-rt`, or a grants option of its own)?
- **Tests.** A test needs a way to drive the timer without sleeping, e.g. calling the check function directly with a fake "now", then confirming the recipient lost access after the reload it asks for.

## Comments

Decided 2026-11-14:

- **Where:** a fork-owned thread, `ExpiryTimer` in `fork_grants.py`, started by one line in `SvcHub.run` (`start_expiry_timer`). It lives only in the hub, so with `-j` it runs once; the hub's reload reaches every worker. `mount_grants` records the mounted grant ids on the root volume and wakes the timer at every reload of the hub's `AuthSrv`; the timer checks under `AuthSrv.mutex`, so it never sees a half-built tree
- **Cost:** the timer sleeps until the next expiry of a mounted grant, then runs one reload, which unmounts every grant expired by then. No extra batching delay. Expiries are read from the db at each check, so extending an active grant (which doesn't reload) just moves the wakeup
- **Deletion:** none. Expired grants stay until the owner revokes them (the user picked this; could be a later ticket)
- **Tests:** `check_expiry(asrv, now)` is the seam: `test_expiry_timer_ends_access_without_waiting` (the recipient loses access after the reload the check asks for) and `test_expiry_check_wakes_for_the_next_mounted_grant` (earliest expiry, extension without a reload, unmounted grants ignored). The thread loop itself has no unit test

Live check, 2026-11-14, `python -m copyparty -j 2` from source on 127.0.0.1, `grants: /shared`, `shr: /s`: alice granted `/home/alice/proj/` to bob with `exp: 1` at 21:51:16; bob's GETs were 200 until 21:52:15, then at 21:52:16.000 the log shows `grants: unmounting expired grants`, one hub reload, both workers reloading, `expired grant 1 ...`, and bob's next GET was 403. Nothing else reloaded in between.

Not run: the Python 2 half of `scripts/run-tests.sh` (no python2 on this machine). The Python 3 suite passes from source and on the hint-stripped copy (136 tests).

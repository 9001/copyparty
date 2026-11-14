# 12: Expire grants without waiting for a reload

**Problem:** A grant's expiry is only checked when the config reloads (`mount_grants` skips grants whose `t1` has passed). Between reloads, a grant past its expiry stays mounted: the recipient can still browse, download and (with read + upload) upload. Nothing reloads by itself, so on a quiet server this can last until the next grant or share link change, `SIGUSR1`, or a restart, possibly days. Since ticket 10 the grants page already shows such a grant as `expired`, so the owner sees "expired" while the recipient still has access.

This breaks spec user story 8 ("set an optional expiry on a grant, so that temporary access ends by itself") and story 28 ("expired … grants to simply disappear from my tree").

**Found:** while doing ticket 10 (2026-11-14). The behaviour dates from ticket 09. FORK.md lists it under the grants section's "known gaps".

**Blocked by:** none

**Status:** needs-triage

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

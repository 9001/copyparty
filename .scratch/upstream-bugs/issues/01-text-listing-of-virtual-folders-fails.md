# 01: Text listing of a folder with no path on disk fails with a 500

**Problem:** `GET /?ls=v` (and `?ls=t` / `?ls=txt`, the plain-text listing formats) fails on any folder that has no path on disk, such as `/` or `/home/` when the only volume is `/home/alice`. The server replies 500 with `'int' object has no attribute 'replace'`. JSON `?ls` on the same folder works. Our deployment has no root volume, so `/` is always such a folder.

**Found:** 2026-11-14, while checking ticket 10 (grants page) against a running server.

**Upstream bug:** yes. It happens on `1af7efec`, the last upstream commit before any fork commit, without any fork options.

**Status:** needs-triage

## Repro

```sh
python -m copyparty -p 3923 -a alice:alice -v /tmp/a:home/alice:A,alice --no-cfg
curl -H 'PW: alice' 'http://127.0.0.1:3923/?ls=v'        # 500
curl -H 'PW: alice' 'http://127.0.0.1:3923/home/?ls=v'   # 500
curl -H 'PW: alice' 'http://127.0.0.1:3923/?ls'          # 200, json
```

Server log:

```
httpcli.py <tx_ls_vols>: return self.tx_ls(ls)
httpcli.py <tx_ls>: a = x["dt"].replace("-", " ").replace(":", " ").split(" ")
[AttributeError] 'int' object has no attribute 'replace', '/'
```

## Cause (from reading the code)

`HttpCli.tx_ls_vols` builds one entry per volume with `"dt": 0` (an int). The text formats in `HttpCli.tx_ls` expect `dt` to be a date string and call `.replace` on it.

## To discuss

- **Whether it matters to us.** Browsers and the web UI use JSON `?ls` and aren't affected. It only hits the text formats (scripts, `curl`). With grants, `/shared/` and `/shared/<owner>/` are folders with no path on disk too, so a recipient's `curl '/shared/?ls=v'` would fail the same way.
- **Fix in the fork or wait.** CLAUDE.md says nothing goes upstream from this work. If we fix it, it's a fork fix to an upstream bug, which needs a failing test first and a FORK.md entry so we take upstream's version if they fix it themselves. Otherwise, check each upstream merge to see whether it's gone.

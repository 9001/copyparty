# Grants live inside copyparty, not in the admin app

Owners create grants themselves from copyparty's file browser. Grants are stored in SQLite next to share links and mounted on each reload, the same way share links are, so every grant is checked again against the owner's current rights. This goes against FORK.md's earlier "admin app writes a generated `.conf`, don't patch `authsrv.py`" plan for user-to-user sharing. That plan would have meant either the admin approving every grant, or letting normal users reach the admin app, which must stay reachable over Tailscale only.

## Consequences

- A few hook lines in upstream `authsrv.py` and `httpcli.py` have to survive every upstream merge. The grant logic itself lives in a new file.
- The admin app still owns accounts, groups and volumes. Only grants moved into copyparty.

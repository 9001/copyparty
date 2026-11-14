# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the label strings used in this repo's issue tracker. The tracker is local markdown (see `issue-tracker.md`), so a "label" is the value of the `Status:` line near the top of each issue file, e.g. `Status: ready-for-agent`.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

Two more `Status:` values are work states, not triage roles: `claimed` (an agent is working on
it) and `resolved` (done; see `issue-tracker.md`). Every finished ticket ends on `resolved`.

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

Edit the "Label in our tracker" column to match whatever vocabulary you actually use.

# Status M01 - [Milestone name]

State of each M01 milestone item. Update as items complete. See
[`milestone.md`](milestone.md) for milestone definitions and for the status ID
pattern that names this file.

Status markers:

| Symbol | Suggested Status | Interpretation |
|---|---|---|
| `[ ]` | Pending | Item is actionable when its dependencies pass. |
| `[+]` | Completed | Item finished or done. |
| `[~]` | In Progress | Item is the one general row currently being worked. |
| `[!]` | Blocked | A current unresolved blocker still prevents progress. |
| `[X]` | Cancelled | Item is no longer needed. |
| `[-]` | Closed Historical | A consumed failed attempt or superseded row retained for audit; it is never retried and does not block its accepted successor. |

Write markers with backticks, exactly as in the table above: `` `[ ]` ``, not
`[ ]`. If you use the API runner, use a current version: it rejects malformed
task markers with exit `11`, including `| Item | [ ] | Notes |`. Older runners
could silently ignore them. Check the separately installed runner as well as
the row syntax when that runner is part of your workflow.

Across the active ledger, zero or one general row may be `[~]`. Resume it before
selecting another row. An operational launcher additionally requires its exact
authorized operation row to be `[~]` before invocation; the marker records the
selected operation but does not grant missing external-mutation authority.

Each table row is a commit unit: after changing its state, verify the change,
update the memory bank/docs, and make a scoped `git commit` before starting the
next row. A `[-]` row's notes must record the consumed attempt or supersession
and identify its accepted successor. If two rows are inseparable, redefine them
as one row before starting rather than closing several rows in one commit.

After the milestone's review, consolidation, and downstream reconciliation
pass, follow [the retirement procedure](milestone.md#long-term-memory-and-retirement).
Preserve this complete document and the full milestone specification in its
retired record; earlier rows, notes, and original path context must survive.
Retirement follows the governing commit policy and never changes the task
markers or permits reuse of this milestone ID.

| Item | State | Notes |
|---|---|---|
| [Item 1] | `[ ]` | [Notes.] |
| [Item 2] | `[ ]` | [Notes.] |
| [Item 3] | `[ ]` | [Notes.] |

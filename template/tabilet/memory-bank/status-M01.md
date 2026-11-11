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
| `[X]` | Cancelled | The approved item was withdrawn; any later replacement needs fresh planning. Cancellation does not prove delivery. |
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

Read this milestone's optional `AUTHORIZATION_REQUIREMENTS` in
[`milestone.md`](milestone.md#authorization-requirements); do not duplicate its
declaration here. Check protected actions against the current human-approved
request and effective grants before acting. Notes may record a grant ID,
performed-action evidence, or a missing-authority blocker; they never prove
approval. Required unperformed actions prevent closure. No new task marker is
introduced, and absent authorization metadata grants no additional authority.

Repairs under human-approved `CORRECTIVE_PLANNING: auto` suspend and resume an
in-progress row as [standing corrective planning](milestone.md#standing-corrective-planning)
describes. Preserve review counts and frozen history.

Each table row is a commit unit: after changing its state, verify the change,
update the memory bank/docs, and make a scoped `git commit` before starting the
next row, except the scoped repair suspension bookkeeping above. A `[-]` row's
notes must record the consumed attempt or supersession
and identify its accepted successor. If two rows are inseparable, redefine them
as one row before starting rather than closing several rows in one commit.
During a goal run, the resolved `COMMIT_POLICY` governs instead; `none` means
no commits even when a requirement or grant mentions `git.commit`.

For substantial discoveries, use [milestone families](milestone.md#milestone-families).
Link required amendments and deferred options here; keep their work in their own files.

Keep this file a current-state record, not a log. Replace a superseded checkpoint
instead of appending dated narrative, and link per-attempt detail in evidence
files. A row whose acceptance depends on a class R check, or on an explicit
grant budget, records its attempt count here under the
[verification-attempt gate](milestone.md#verification-attempt-gate). A class O
gate under the [test policy](test-policy.md) records the command, the source
revision or saved diff hash (and artifact identity when one is qualified), PASS
or FAIL, the elapsed wall-clock time and one log link; a reused result says its
inputs are unchanged and keeps its original time. A row's
focused verification is recorded the same way, and says so when its result came
from the toolchain's cache. A row that fixes a carried review finding says "fixes FND-nn" in its
notes (see [Open review findings](milestone.md#open-review-findings)).

For interactive Goal/Next, persist [required gate recovery](milestone.md#required-gate-recovery)
state beside review counters, before dispatch, using this checkpoint shape
(replace placeholders; keep one entry per gate/key/waiter, not a dated log):

```text
Review iterations: <consumed>/<effective limit>; approval: <source>
REVIEW_MAX_GATE_ITERATIONS: <effective positive integer; default 3>; approval: <source>
Gate: <milestone + command + cwd + variant + required scope>
Gate keys: <package-qualified test or stable failure ID>: charged <n>, remaining <n>
Gate chain: <distinct failing keys since last clean pass>; ceiling: <effective limit; default 3>
Gate chain approval: <source for any explicit extension; preserve seen keys>
Gate recovery proposal: <diagnosis/evidence, exact edits, usage, proposed limits/remaining attempts, risks/permissions>
Gate recovery approval: <pending question or actual human approval source and old/new limits>
Gate attempt: <ID>; state: <started|PASS|FAIL|interrupted>; known key: <key or unknown>
Gate inputs/evidence: <full HEAD + saved diff/hash, result log, elapsed time>
Diagnostic rungs: <finding/key>: <0..2>; charged attempt IDs: <IDs>
Waiter: <stable file/symbol identity>; original T: <value>; current: <value>
Waiter doublings: <0..3>; ceiling: <8T or stricter approved value>
Waiter prior evidence: <recovered active/retired status links and stable identity/aliases>
Waiter maintained reference: <entry in tech-stack.md Test waiter ceiling references>
Waiter evidence: <measured completion, independent assessment, approval source>
Waiter exact edits: <old -> new per charged attempt; whole-review brief link>
```

A clean complete gate pass resets gate keys and chain state, never waiter
ceilings or original values. Preserve evidence and interrupted reservations;
compaction, resume and repairs never reset counters. Every resume summary shows
this state beside review counters. Exhaustion leaves affected work `[!]` pending
a concrete recovery proposal and renewed human approval; retain the active,
incomplete goal and resume its checkpoint after approval, preserving usage.
Routine focused checks and Python API paths
do not acquire these interactive counters.

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

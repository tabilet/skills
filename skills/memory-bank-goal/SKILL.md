---
name: memory-bank-goal
description: Execute or resume ordered memory-bank milestones using the project's tabilet/GOAL.md protocol.
disable-model-invocation: false
argument-hint: M01 -> S01 -> A01?
---

# Run An Ordered Set Of Milestones

Before reading project state for this workflow, inspect the root layout. If
`GOAL.md`, `memory-bank/`, `evolution/`, `docs/history/`, or
`docs/archive-<LANE><NN>.md` exists in a v1.5.0 or mixed layout, stop before
project writes or execution. Direct the user to preview and explicitly apply
`skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`.
Installing v2 never migrates a project automatically.

Read the project's `tabilet/GOAL.md` and follow it. That protocol owns sequencing,
verification, review, reconciliation, closure, and commit policy. This skill
resolves the launch request; it does not define a second execution loop.

If `tabilet/GOAL.md` is missing, stop ordered execution. It ships beside the
`memory-bank-init` skill and at <https://github.com/tabilet/skills/blob/main/GOAL.md>.
Offer one-row work or a user-supplied protocol without starting either workflow.

## Resolve the request

Read explicit order and policies from the invoking request itself, without
runtime argument substitution. Explicit milestone order in the invoking request replaces
`tabilet/memory-bank/suggested.txt`'s `STATUS_ORDER`. The suggestion is disposable input,
not a source of truth. Reuse its file map and downstream impacts only where the
request has not supplied them, after checking every ID, path, dependency,
conditional trigger, and impact against the current memory bank and implementation.

Resolve historical IDs and stale paths through the project's history index.
Retired records are evidence, never executable rows. Cancellation or supersession
is not proof of completed acceptance; follow the recorded disposition and
successor. An all-retired project remains initialized. Do not recreate its files.

Materialize the complete resolved request in the conversation so execution does
not depend on the disposable file remaining on disk:

```text
Using tabilet/GOAL.md, execute this loop.

STATUS_ORDER: <resolved order>

STATUS_FILE_MAP:
<one ID-to-status-file mapping per ordered status>

DOWNSTREAM_IMPACTS:
<known source-to-pending-consumer impacts, or none>

COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: every required status is complete, every triggered
conditional status is complete, and every milestone's documented verification
passes.
```

Preserve explicitly supplied commit and external-mutation policies. The example's
`task` policy must not override a request for `none`. `COMMIT_POLICY` governs
commits for the whole run: `none` means no commits; `task` means per-row commits.
Use the protocol's request precedence and other policy definitions.

When no order was supplied, prefer a valid suggested order, otherwise derive one
from `tabilet/memory-bank/milestone.md`. Show the complete resolved request and obtain
confirmation before starting. Ask for an order if none is unambiguous.
A trailing `?` marks a conditional milestone: when its documented trigger is
absent, skip it without completing or cancelling it.

## Execute through acceptance

Resolve missing information through safe inspection first. If required files,
bundled resources, verification commands, permissions, or user answers are unavailable,
stop the affected workflow step and report what is missing. Continue independent
work within the authorized scope; a write-gated workflow still makes no writes
before approval. Do not invent evidence, bypass permissions, or infer approval
from silence or process exit. Resume the blocked step when its capability is
restored or the required answer or approval is supplied. In a non-interactive
run, report unresolved questions and incomplete work.

Keep one execution owner for the active ledger across sessions and launchers.
Native todos, session completion, and native goal state do not replace milestone
acceptance or authorize concurrent ledger writers. Follow `tabilet/GOAL.md` through
acceptance or its defined stop. Resume an incomplete review or closure even
when all task rows are terminal. Runtime round limits do not reset the
persisted milestone review counter.

For invocation syntax or optional native goal continuation, read
[references/runtime-help.md](references/runtime-help.md). This help is not needed
for an already resolved ordinary request.

Report which milestones closed, verification, commits, skipped conditional
milestones, and remaining blockers. Session completion alone proves none of them.

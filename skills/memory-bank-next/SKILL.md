---
name: memory-bank-next
description: Implement and verify one actionable memory-bank task, update its records, and commit under the governing policy. Use for one-task execution or resumption.
disable-model-invocation: false
argument-hint: (no arguments)
---

# Tackle Next Memory-Bank Todo

Before reading project state for this workflow, inspect the root layout. If
`GOAL.md`, `memory-bank/`, `evolution/`, `docs/history/`, or
`docs/archive-<LANE><NN>.md` exists in a v1.5.0 or mixed layout, stop before
project writes or execution. Direct the user to preview and explicitly apply
`skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`.
Installing v2 never migrates a project automatically.

When `TABILET_AUDIT_DB` explicitly enables auditing, use exactly one recorder
owner. Inside the API runner, the runner owns the audit lifecycle: do not look
for an interactive skill's `references/optional-audit.md`, invoke
`tabilet-audit`, or start a duplicate run. In an interactive skill run, read the
bundled `references/optional-audit.md` and use the optional installed
`tabilet-audit` toolkit. Report recorder failures as gaps without changing
workflow approvals or outcomes.

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
acceptance or authorize concurrent ledger writers.

Read `AGENTS.md`, then read the memory bank in the order required by
`AGENTS.md`.

Read `tabilet/memory-bank/milestone.md` for the status ID pattern, the lane meanings,
milestone priority, and dependencies. Inspect every active status file for an
existing `[~]` row. If more than one general row is in progress, stop and report
the conflict. If one exists, resume exactly it. Otherwise check the recorded
milestone review and closure state before selecting new work. Resume an
interrupted review or closure without selecting another row; terminal task
markers alone do not prove milestone acceptance. When no closure is incomplete,
select the next dependency-ready `[ ]` row and mark it `[~]` before implementation.

Consult relevant maintained lessons when the project has them. Resolve retired
prerequisites through the project's history index; never treat a stale status
path as permission to recreate or retry a historical ID.

Tackle exactly one row:

- Implement the change.
- Update current memory-bank facts invalidated by this row in the same change.
  A later documentation row does not defer these current-fact corrections.
  Update other relevant docs within this row's scope. Before committing,
  compare the implementation with maintained product, architecture, and stack
  claims; correct contradictions. Updating only the status is insufficient.
- If a failed attempt is consumed or the row is superseded, mark it `[-]`,
  record the outcome and accepted successor in its notes, and never retry it.
- Run the required verification.
- Mark a successfully implemented outcome `[+]` only after verification.
  Preserve `[-]` for consumed or superseded work.
- Commit the change with a scoped commit message.

Before invoking an operational launcher, require its exact authorized operation
row to be `[~]`. The marker records the selected operation; it does not grant
missing external-mutation authority.

If completing this row completes a milestone, run the milestone review procedure
from `tabilet/memory-bank/milestone.md` before final handoff. Commit review fixes
separately.

When the project has adopted retirement, follow that same milestone procedure:
consolidate facts and lessons, preserve superseded knowledge, finish downstream
reconciliation, and retain the full status and specification in history before
removing their active entries. Preserve earlier rows and notes. Include
retirement in the final task or substantive closure commit. Do not batch-retire
unrelated old milestones during this one-row run. Installing a newer skill alone
does not authorize migrating an existing project's history.

Skip `[!]` blocked, `[X]` cancelled, and `[-]` closed-historical rows and pick
another actionable row instead. Stop if no actionable pending or in-progress
row remains in any lane and no milestone review or closure is incomplete, or
if the task is ambiguous enough to require human input.

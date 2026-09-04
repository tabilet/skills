---
name: memory-bank-next
description: Tackle exactly one actionable row from the memory bank - implement it, verify it, update the status file, and commit. Use for everyday work on a project that has a memory-bank/.
disable-model-invocation: false
argument-hint: (no arguments)
---

# Tackle Next Memory-Bank Todo

Read `AGENTS.md`, then read the memory bank in the order required by
`AGENTS.md`.

Read `memory-bank/milestone.md` for the status ID pattern, the lane meanings,
milestone priority, and dependencies. Inspect every active status file for an
existing `[~]` row. If more than one general row is in progress, stop and report
the conflict. If one exists, resume exactly it. Otherwise select the next
dependency-ready `[ ]` row and mark it `[~]` before implementation.

Tackle exactly one row:

- Implement the change.
- Update relevant memory-bank or docs files.
- Mark the row `[+]` only when verified.
- If a failed attempt is consumed or the row is superseded, mark it `[-]`,
  record the outcome and accepted successor in its notes, and never retry it.
- Run the required verification.
- Commit the change with a scoped commit message.

Before invoking an operational launcher, require its exact authorized operation
row to be `[~]`. The marker records the selected operation; it does not grant
missing external-mutation authority.

If completing this row completes a milestone, run the milestone review procedure
from `memory-bank/milestone.md` before final handoff. Commit review fixes
separately.

Skip `[!]` blocked, `[X]` cancelled, and `[-]` closed-historical rows and pick
another actionable row instead. Stop if no actionable pending or in-progress
row remains in any lane, or if the task is ambiguous enough to require human
input.

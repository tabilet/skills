# API automation 7 — Status, resume, recovery, and operator control

Plan state: `[ ]`

Depends on: [API automation 6 — Horizon execution and closure](api-automation-6.md).

## Goal

Let the user see where a horizon stands, stop it safely, and resume it later —
including after a crash — without guessing or repeating work.

## Scope and boundaries

- `tabilet status` never writes to the project, the receipt, or any database.
- Opening a session without a request shows state; it does not scan the codebase
  for new work or run in the background.
- When provenance or a row's outcome cannot be established, the controller stops
  for review rather than guessing.

## Design

**Status.** `tabilet status PROJECT` reads the live ledger with the runner's own
parsers and prints milestones, the sole `[~]` row if any, blocked rows, the
review count, and the receipt state: `approved`, `running`, `paused` (with its
reason and remaining limits), `needs_review`, or `completed`. When the optional
[SQLite index](sqlite.md) is present, status may show its freshness, but it always
reads live Markdown first.

**Resume.** `tabilet resume PROJECT`:

1. takes the project lock from API 2 (exit 19 if held);
2. loads the receipt and verifies the canonical path, branch, baseline and
   commit ancestry, image ID, cumulative usage, and current operation;
3. reconciles any unrecorded planning, task, review-fix, or closure commit, then
   checks for a clean worktree and rereads the live ledger;
4. continues the horizon from API 6 only from a proved clean checkpoint.

Stale approval or changed immutable inputs exit 18. Dirty or uncertain recovery
sets `needs_review` and exits 21, explaining the exact evidence required.

**Crash reconciliation.** Persist the intended operation, its expected baseline,
selected row or closure phase, approved paths, and usage before execution. A
crash may occur before or after the planning, task, review-fix, or closure
commit, and before the receipt update. On resume, compare the live tree and
commits since the last checkpoint with that intent. At a clean baseline, resume
the unstarted operation; at a clean commit with matching lineage, paths, row
transition, and verification evidence, record it exactly once. A dirty
worktree, partial row, unexpected commit, lost verification evidence, or
ambiguous outcome enters `needs_review` and exits 21. Never reset, discard,
replay, or auto-commit dirty work to make recovery appear clean.

**Operator control.** While running, the controller prints the current row,
provider attempts and model turns used, limits remaining, and each command's
summary. Ctrl-C stops the current container (API 3) and exits 130. A clean
checkpoint records `paused` and can resume; dirty or uncertain work records
`needs_review` and cannot resume automatically. A limit extension is a new
proposal showing the higher cap and current usage, followed by `confirm` before
more calls or commits.

**Optional audit.** With `TABILET_AUDIT_DB` set, the controller records its runs
through the existing `tabilet-audit` toolkit and is the sole recorder owner for
them; runs it drives are not recorded again as runner or skill runs. A missing or
unusable audit reports a gap and never changes an outcome, matching v2.1.0.
Record `completed` only after verified closure, and distinguish `paused` and
`needs_review` from completion; remove any `awaiting_acceptance` audit path.

## Deliverables

- `harness/`: `status`, `resume`, crash reconciliation, progress output, interrupt
  handling, optional audit recording.
- `tests/`: interruption and recovery tests at each step boundary.

## Acceptance

- `status` leaves the project, receipt, and database byte-identical.
- Crash injection around planning, task, and closure commits either continues
  from a proved clean checkpoint or stops for review; no row or closure phase
  runs twice.
- Ctrl-C leaves no container running; dirty interruption needs manual review.
- A reached limit cannot be silently reset or raised by `resume`.
- Audit failures never change a status, row outcome, or exit code; recorded
  completion requires the same verified closure as the receipt.

## Verification

```bash
python3 -B -m unittest discover -s tests -p 'test_tabilet_resume*.py'
python3 check.py
```

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API7-T01 | `[ ]` | Implement read-only `tabilet status`. | No write to the project, receipt, or database in any test. |
| API7-T02 | `[ ]` | Implement `tabilet resume` with lock, lineage, image, and worktree checks. | Lock exits 19, stale inputs exit 18, and dirty or uncertain recovery exits 21 with the reason. |
| API7-T03 | `[ ]` | Reconcile crashes around planning, task, and closure commits. | Clean proven checkpoints resume; dirty or uncertain work exits 21 without replay. |
| API7-T04 | `[ ]` | Add progress output, Ctrl-C handling, and confirmed limit extension. | Interrupt cleans up the container; a higher cap needs a new confirmation. |
| API7-T05 | `[ ]` | Record controller runs and automatic completion through the optional audit toolkit. | One recorder owner; completion follows verified closure, and audit gaps never change outcomes. |

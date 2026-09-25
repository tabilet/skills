# API automation 6 — Horizon execution and closure

Plan state: `[ ]`

Review iterations: 3 of 5; no P1/P2 findings remain after fixing crash-time
operation intent, successor task-scope checks, bounded closure evidence, and
host-HEAD drift around commits.

Depends on: [API automation 3 — Docker sandbox executor](api-automation-3.md) and
[API automation 5 — Proposal, confirm or reject, receipt, and planning commit](api-automation-5.md).

## Goal

Execute the confirmed horizon row by row in the sandbox, carry each milestone
through review and closure, and report completion automatically when required
evidence is verified.

## Scope and boundaries

- The controller acts only inside the receipt: its horizon, file scope, image, and
  limits.
- The confirmation authorizes local project edits, tests, and commits. It never
  authorizes push, merge, deployment, publication, account or provider changes,
  messages, payments, or other external mutations.
- Markdown remains task truth. The controller reads the live ledger before every
  row; the receipt only bounds what may run.

## Design

**Deterministic row selection.** The runner leaves row choice to the model; the
controller does not. Before each row it:

1. rereads live milestone specifications, task dependencies, active and retired
   rows, and the receipt's fixed horizon; a sole `[~]` row outside that horizon
   or more than one `[~]` row stops selection for review;
2. checks each dependency against current Markdown, including retired evidence;
   unresolved, newly blocked, or drifted dependencies stop selection rather
   than relying on the receipt's old snapshot. A dependency that changed since
   proposal display must be re-resolved from live state before any provider call;
3. resumes the sole in-scope `[~]` row when its provenance is established;
   otherwise picks the first `[ ]` row in table order in the first ready horizon
   milestone;
4. never retries a `[!]` blocked or `[-]` historical row. A `[-]` row's
   accepted successor must be documented, dependency-ready, and inside the
   approved horizon; an out-of-scope successor stops for a new proposal.

The chosen row is named in the model's instructions. The pre-commit transition
check prevents a host commit that changes another row's outcome; the shared
post-commit gate independently detects a violation.

**Per-row run.** Each row runs through the shared core from API 2 with the
required Docker executor from API 3 and separate host-commit instructions.
Before each host task commit, the controller runs required verification and
validates the selected row, history, and approved file scope on the uncommitted
worktree. A failed pre-commit gate exits 24, leaves evidence for review, and
does not commit. On success, the host stages only validated paths, commits one
row, and runs the shared post-commit gates in their original order. File paths
alone cannot prove the change belongs semantically to the selected row.

**Limits.** The receipt persists maximum rows, provider attempts, turns per
row, total commits, and elapsed time from approval plus cumulative usage.
Reserve and durably count each provider attempt, including retries and failures,
*before* dispatch. Check row, turn, commit, and time caps before the corresponding
action; never reset counters on resume. Reaching a cap pauses with exit 16. To
extend it, show the higher number and obtain a new `confirm` bound to the same
horizon and current checkpoint. A pause never closes a milestone, marks a row
complete, or resets the persisted review count.

**Closure.** The runner's no-actionable-row exit is not evidence of acceptance.
When a milestone's last row completes, the controller runs the procedure in
[milestone.md](../template/tabilet/memory-bank/milestone.md) in order. Model
commands use the sandbox. Persist evidence and checkpoint each phase; create a
review or closure commit only when files actually change:

1. the bounded review-fix gate — the initial deep review is iteration 1, every
   P0/P1/P2 fix is followed by a whole-milestone re-review, and a clean pass is
   required within 10 iterations, with the count persisted in the receipt;
2. verification of the milestone's acceptance criteria;
3. fact and lesson consolidation;
4. downstream reconciliation;
5. the retirement procedure, when the project has adopted it (the runner already
   rejects retirement without a passed review within 10 iterations).

**Completion evidence.** Required manual inspection or other manual acceptance
evidence pauses with exit 17 until supplied and verified. Supply it keyed by
the exact approved criterion; the acceptance phase records it as user evidence
and separately verifies it. A model review is labeled as model evidence, not
independent human acceptance. When every horizon
milestone has verified closure, the controller prints commits, verification
output, review iterations, and each acceptance criterion against observed
results, atomically sets `completed`, and exits 0. There is no final `accept` or
`reject` command.

**External actions.** If a row cannot finish without an external mutation, the
model reports it, and the controller pauses with exit 17 and names the action
for separate handling. The first release does not perform external actions
under the general confirmation or implement a generic external-action approval.
The `[~]` marker records selection, never external-mutation authority.

## Deliverables

- `harness/tabilet_horizon.py`: live row selection, usage reservations, exact
  host staging and commits, closure phases, evidence, and automatic completion.
- `harness/tabilet_controller.py`: locked execution and limit-extension adapters
  using the required Docker executor.
- `tests/`: fake-provider horizons across multiple milestones.

## Acceptance

- Rows outside the horizon or out of dependency order are never selected.
- A commit touching another row's outcome is rejected.
- Every limit pauses without closing or accepting anything; attempts and turns
  remain charged across resumes, and an extension needs a newly confirmed higher
  number at the same clean checkpoint.
- Unresolved live dependencies, an out-of-horizon `[~]` row, and an out-of-scope
  `[-]` successor stop selection before a provider call.
- Failed required verification makes no host commit. A crash after the task
  commit leaves its operation intent for API 7 reconciliation and is never
  replayed automatically.
- The complete closure order is persisted. P0/P1/P2 findings trigger another
  whole-milestone review up to 10 iterations; a clean no-change pass creates no
  commit. Required manual evidence pauses; model review is labeled as model
  evidence; verified closure marks the horizon `completed` automatically.
- External actions are recorded and reported for separate handling; no external
  mutation happens under the general confirmation.

## Verification

```bash
python3 -B -m unittest discover -s tests -p 'test_tabilet_horizon*.py'
python3 -B -m unittest discover -s tests -p 'test_tabilet_proposal.py'
python3 check.py
```

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API6-T01 | `[ ]` | Implement deterministic, receipt-bounded row selection from live dependencies. | Out-of-horizon `[~]`, unresolved dependency, blocked row, and out-of-scope `[-]` successor cases stop safely. |
| API6-T02 | `[ ]` | Run each row through the shared core with Docker and host commits. | Pre-commit verification precedes each host commit; shared post-commit gate order is unchanged. |
| API6-T03 | `[ ]` | Enforce cumulative receipt limits as pauses with exit 16. | Attempts count before dispatch and across resumes; an extension needs a newly confirmed higher number. |
| API6-T04 | `[ ]` | Run the milestone closure procedure in order. | Review iterations persist; no-change passes have no commit; retirement follows a passed review. |
| API6-T05 | `[ ]` | Report evidence and complete automatically after verified closure. | Manual evidence pauses; model evidence is labeled; `completed` needs no final command. |
| API6-T06 | `[ ]` | Pause and report external actions for separate handling. | No external mutation happens under the general confirmation. |

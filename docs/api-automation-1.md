# API automation 1 — Boundary, contracts, and authorization model

Plan state: `[ ]`

Depends on: none. Source design: [api-automation-plan.md](api-automation-plan.md)
and its [review](api-automation-review.md).

Full dependency order: API 1 -> [API 2](api-automation-2.md) ->
[API 3](api-automation-3.md) and [API 4](api-automation-4.md) ->
[API 5](api-automation-5.md) -> [API 6](api-automation-6.md) ->
[API 7](api-automation-7.md) -> [API 8](api-automation-8.md).

These eight flat documents are temporary implementation planning notes for
branch `api`. They supersede conflicting details in the source design and review
linked above. They are not this repository's memory bank or task state. Saving
them authorizes no API implementation, merge, tag, push, or publication.

## Decisions

The review ended with four open decisions. They are settled:

| Question | Decision |
|---|---|
| Where the controller lives | In this repository, under `harness/`, as optional payload. This milestone amends the boundary explicitly. |
| What one `confirm` authorizes | The exact shown planning diff and one bounded, local execution horizon. Verified milestone closure reports completion automatically; there is no final `accept` or `reject` command. |
| Release slicing | The full scope ships in one release, planned as v2.2.0. Milestones sequence the work; they are not separate releases. |
| Draft format | Temporary planning notes with task tables, using backticked markers and `API<N>-T<NN>` task IDs. |

The consumer direction in the source design is out of scope for this release.

## Goal

Before any code, change the repository's own rules so the controller is a
documented, checked part of the project rather than an exception to it, and fix
every contract the later milestones implement against.

## Scope and boundaries

**Boundary amendment.** [AGENTS.md](../AGENTS.md) lists "Provider SDKs, agent
frameworks, or CLI wrappers" as out of scope and calls the repository "a copyable
starter, not an application". Amend both to admit one optional controller:

- The controller is optional account-level payload, like the API runner and the
  audit toolkit. The memory bank, the template, and the seven skills keep working
  without it.
- It adds no provider SDK, no background service, and no project-local state.
  Standard library plus Git and Docker only.
- The non-goal "No second harness implementation" stays. The controller drives the
  existing runner's execution core; it never reimplements row parsing, gates, or
  the provider loop.

**Authorization reconciliation.** The Propose and Reconcile hard rules say they
hand off "without implementing, committing, or launching execution". Those rules
stay true for the direct skills. The controller is a separate, documented path in
which a single visible proposal names both planning writes and a bounded local
execution scope. Direct skills never gain execution authority from this change.

**Planning-note acknowledgement.** These flat drafts are temporary planning
notes, not an exception to "No memory bank for this repository itself". API 8
decides their disposition in the reviewable release candidate. Do not create a
root `tabilet/memory-bank/` or introduce a permanent repository ledger.

## Design

**CLI surface.** One installed command, `tabilet`:

| Command | Behavior |
|---|---|
| `tabilet chat PROJECT --image IMAGE` | Interview, preview the plan, accept `confirm` or `reject`. |
| `tabilet status PROJECT` | Summarize live project state; never writes. |
| `tabilet resume PROJECT` | Continue an approved horizon from a verified checkpoint. |

**Receipt `tabilet.api.receipt/v1`.** Private JSON under
`${XDG_STATE_HOME:-~/.local/state}/tabilet/receipts/`, mode `0600`, containing:
canonical project path, proposal digest (SHA-256 of the exact rendered
proposal), exact approved file actions and horizon IDs, expected baseline and
branch, planning commit when known, commit lineage, immutable Docker image ID,
limits and cumulative usage, local-only mutation scope, completed task and
closure commits, active operation, pause reason, and state. States are
`approved`, `running`, `paused`, `needs_review`, and `completed`. Create
`approved` durably before applying the plan; update it atomically for each
operation intent, counter reservation, and verified checkpoint. `needs_review`
forbids automatic replay. The receipt is
execution authority; Markdown stays task truth.

**Limits.** Suggest 5 task rows, 100 provider attempts (including failed calls
and retries), 40 model turns per row, 15 total commits (planning, tasks, fixes,
and closure), and 2 hours elapsed from approval. The user may revise each before
`confirm`. Persist counters before dispatch, carry them across resumes, and
never reset them silently. These are operational caps, not a dollar guarantee.
Also show the Docker limits: 4 CPUs, 8 GiB, 512 processes, and 300 seconds per
command. Reaching a limit pauses the horizon; a higher limit needs a new visible
proposal and confirmation. A pause never closes a milestone or resets review
count.

**Completion.** After required verification, the project's bounded review gate,
consolidation, downstream reconciliation, and adopted retirement pass for every
horizon milestone, set `completed` and report the evidence automatically. Label
a model review as model evidence. Required manual evidence pauses the horizon.
External actions are reported for separate handling and never run under the
general `confirm`.

**Exit codes.** The standalone runner retains its existing code meanings and
gate precedence. The shared project lock adds runner code 19 for lock collision.
Controller-only codes are:

| Code | Meaning |
|---|---|
| `0` | Command completed; for execution, required closure verified and the horizon completed. |
| `2` | Usage or configuration error. |
| `16` | Paused on a receipt limit. |
| `17` | Paused for setup, required manual evidence, or a separately handled external action. |
| `18` | Approval is stale: branch, lineage, hashes, or IDs drifted since `confirm`. |
| `19` | Another Tabilet launcher holds the project lock. |
| `20` | Controller pre-commit row or verification gate failed; no host task commit was made. |
| `21` | Dirty or uncertain recovery requires manual review; no automatic replay. |

## Deliverables

- [AGENTS.md](../AGENTS.md): boundary, non-goal, authorization, and ledger
  amendments; new hard rules for the controller.
- `check.py`: checks that enforce each new hard rule, including the exit-code
  table and controller boundary.
- [docs/EXECUTION.md](EXECUTION.md): the controller's exit codes beside the
  runner's.

## Acceptance

- Every new AGENTS.md rule has a check that fails when the rule is broken.
- The direct skills' approval rules are textually unchanged.
- The receipt and exit-code contracts cover approval, crash recovery, limit
  extension, and automatic completion without final accept/reject commands.

## Verification

```bash
python3 check.py
mkdocs build --strict
git diff --check
```

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API1-T01 | `[ ]` | Amend AGENTS.md boundary and non-goals for the optional `tabilet` controller. | The amendment names what is allowed and what stays excluded; the "no second harness" non-goal is kept. |
| API1-T02 | `[ ]` | Write the combined-authorization hard rule for the controller path. | Propose and Reconcile rules are unchanged; the new rule states planning plus bounded local execution from one visible proposal. |
| API1-T03 | `[ ]` | Specify receipt `tabilet.api.receipt/v1`, cumulative limits, and recovery states. | Every field later milestones read or write is defined, with types and privacy rules. |
| API1-T04 | `[ ]` | Specify the CLI surface and controller exit codes 16–21. | Standalone gate meanings and precedence remain; the new lock outcome and controller codes are documented. |
| API1-T05 | `[ ]` | Document these drafts as temporary notes under the existing no-memory-bank rule. | No root repository memory bank or permanent ledger is introduced. |
| API1-T06 | `[ ]` | Add `check.py` enforcement for each new rule. | Each check fails on a deliberate violation and passes on the amended tree. |

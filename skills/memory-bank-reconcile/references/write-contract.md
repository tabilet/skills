# Review Reconciliation Write Contract

Read this reference only after the user approves the reconciliation proposal.

## Apply safe file actions

Apply exactly the approved create, merge, preserve, and remove actions. Never
silently overwrite user content or expand the reviewed project boundary.

- Keep the supplied review source read-only. Do not create a review ledger,
  copy the review into `docs/`, or create a per-review artifact directory.
- Do not change implementation, tests, schemas, deployment configuration, or
  other code while reconciling the plan.
- Do not mark an implementation row completed or claim that a planned fix was
  delivered. Preserve existing in-progress, completed, blocked, and cancelled
  rows; rewrite only approved untouched pending rows.
- Never edit or delete a verified `docs/archive-<LANE><NN>.md`. If review
  evidence suggests the historical baseline is wrong or materially obsolete,
  report that `memory-bank-archive` must decide whether a successor is needed.
- Do not create, replace, or modify `GOAL.md`. It is an optional execution
  protocol, not review state.
- Do not commit, push, tag, publish, open a change request, or mutate another
  repository or external system without separate authorization.
- Stop before any collision or user-owned memory-bank change that the approved
  proposal did not cover.

## Write finding ownership and provenance

For every confirmed finding entering active work, record in its milestone or
status notes:

- a portable review title or identifier and source finding ID;
- the source priority and locally classified severity;
- the review baseline when stated, the full revalidation commit when Git
  exists, and whether relevant uncommitted changes were part of the evidence;
- current repository-relative evidence; and
- lineage to an affected milestone or existing row when applicable.

When a source has no finding IDs, assign `F01`, `F02`, and so on in source order
within that review and use the same labels throughout the proposal and writes;
these are provenance labels, not status IDs. Record an absent source priority or
review baseline as `not supplied`. Use `unversioned` for current revalidation
when the project is not in Git.

Use a stable repository-relative source path or URL when one exists. For an
attached, pasted, temporary, or absolute-path review, use its title or filename
without persisting a machine-specific path. Do not copy full review prose into
task rows; synthesize the reproducible defect, required outcome, and constraints.

Resolved, duplicate, unsupported, outside-ownership, and unscheduled findings
remain in the handoff matrix rather than a new persistent ledger. A duplicate
active finding points to its existing owner; it does not create another row.

## Reconcile milestones and rows

Maintain the status conventions already defined by the project:

- one `memory-bank/status-<LANE><NN>.md` per indexed milestone;
- a zero-padded permanent ID that is never reused or renamed;
- one task-sized row per commit unit; and
- backticked markers: `` `[ ]` ``, `` `[+]` ``, `` `[~]` ``, `` `[!]` ``, and
  `` `[X]` ``.

After approval, recheck the milestone index and filesystem, then allocate each
approved new milestone the proposed next unused ID. Stop on an ID collision
rather than choosing an unapproved replacement.

Placement rules:

1. Append a pending row to an open matching milestone when the finding stays
   within that milestone's scope and acceptance. Rewrite an existing row only
   when it is still pending and the approved finding makes its old wording
   obsolete.
2. Amend a pending future milestone when it already owns the required outcome.
3. When affected work is completed history, create a new remediation milestone;
   reference the historical ID without reopening or changing its state.
4. Give each new milestone a narrow goal, bounded scope, measurable acceptance,
   required verification, dependencies, downstream impacts, and task-sized
   rows. P1/P2-or-higher findings stay in the active horizon even when an
   approved external-input row must start blocked.
5. Put optional lower-severity hardening in Candidate Directions with no lane,
   permanent status ID, status file, or execution-order entry. Record why it is
   deferred and the concrete trigger for fresh reconciliation.

Recompute the complete active dependency graph after placement. Update pending
dependencies, assumptions, tasks, acceptance, verification,
compatibility/migration, rollout, rollback, and downstream relationships that
would otherwise rely on stale review-era assumptions. Preserve unrelated
pending work.

Order confirmed P1/P2-or-higher remediation before unrelated lower-severity
work while preserving real prerequisites and unavailable-input blockers.

If the incoming review is an explicitly active bounded-gate pass, persist its
iteration and findings in the active status without resetting the existing
counter. Never advance past iteration 10 or treat ordinary review intake as a
gate iteration.

## Keep current truth separate from target work

Correct `memory-bank/product.md`, `memory-bank/architecture.md`, or
`memory-bank/tech-stack.md` only when current repository evidence proves their
existing factual description is stale. Do not write a proposed fix or target
architecture as current truth.

Add the next `evolution/prompt-vN.md` and `evolution/result-vN.md` pair only when
the approved review response meets the project's material direction-change
trigger. The prompt records the newly approved direction; the result records
the current state and links its remaining gaps to active milestones. A review's
arrival alone is not an evolution event.

## Refresh disposable goal input

When the project contains an approved compatible `GOAL.md`, replace
`memory-bank/suggested.txt` with a fresh launch reference derived from the whole
approved active horizon, not only the new review findings. It is disposable
input, never review history or active truth.

Use this shape with project values:

```text
# Disposable multi-milestone launch reference.
# Reconcile this suggestion against milestone.md and the current status files.
# Delete it after launching the goal, or whenever it becomes stale.

Using GOAL.md, execute this loop.

STATUS_ORDER:
M01 -> M02

STATUS_FILE_MAP:
M01 = memory-bank/status-M01.md
M02 = memory-bank/status-M02.md

DOWNSTREAM_IMPACTS:
M01 -> M02

COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: every required status is complete, every triggered
conditional status is complete, and every milestone's documented verification
passes.
```

Map every active status to exactly one file and include all known active
downstream consumers. Use a trailing `?` only for an approved conditionally
required status whose concrete trigger is documented in `milestone.md`. Never
include Candidate Directions.

When no compatible protocol exists, omit `memory-bank/suggested.txt`. Remove an
existing stale reference only when that removal was in the approved file
actions. Report one-row execution as the available path; do not create or
approximate `GOAL.md`.

## Check the output

Before reporting completion, verify:

1. Every accepted finding has exactly one active owner or one unnumbered
   candidate direction; duplicate work has not been created.
2. Every active finding records portable provenance, both severities, the
   revalidation baseline and relevant worktree state, current evidence, and
   historical lineage when needed.
3. Completed milestones and non-pending row states are unchanged; every new row
   is pending or is an approved evidence-complete external blocker.
4. Every new status ID is valid, unique, linked once from `milestone.md`, and
   absent from completed history and archive namespaces.
5. The active graph is dependency-closed and every affected pending downstream
   specification agrees with the proposed work.
6. Candidate Directions remain unnumbered and absent from status files and
   launch input.
7. Current-truth documents contain no unimplemented target state, and verified
   archives are unchanged.
8. Any active review-gate counter continued from its persisted value and did
   not exceed 10; ordinary intake did not start a counter.
9. When `suggested.txt` exists, it represents the complete approved active
   graph and a compatible protocol exists. Otherwise no stale launch reference
   remains unless preservation was explicitly approved.
10. No review copy, review ledger, code change, commit, external mutation, or
    unrelated memory-bank edit was created.

Run the project's structural documentation or memory-bank checks when they are
safe and available. Run focused verification used to revalidate findings, but
do not claim application acceptance for fixes that have not been implemented.

## Hand off

Report the review source and revalidation baseline; the full disposition matrix;
milestones and rows created or amended; candidate directions; dependency and
downstream changes; current-fact or evolution updates; structural and focused
checks; and the disposable launch-reference action.

State explicitly that no finding was implemented. Point to `memory-bank-next`
for one row or `memory-bank-goal` for the approved ordered horizon. Do not commit
or launch either workflow unless separately requested.

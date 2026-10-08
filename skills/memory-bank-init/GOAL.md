# Universal Multi-Milestone Goal Loop

This file defines a reusable protocol for executing an ordered set of project
milestones or status files from a goal request. It is an execution
protocol, not a project roadmap, product specification, or status source.

Copying this file to another repository does not transfer project-specific
paths, lane names, commands, dependencies, or mutation authority. Those are
discovered from that project's instructions and supplied goal input.

## Instruction And Project Discovery

Before interpreting this protocol, obey the active system, developer, and user
instructions. Then discover project truth in this order:

1. The nearest applicable `AGENTS.md` files or equivalent repository
   instructions.
2. Product, architecture, technical, roadmap, decision/evolution, and status
   sources named by those instructions.
3. The status or milestone files supplied by the goal request.
4. Current code, schemas, configuration examples, tests, documentation, and
   worktree state.

Project instructions define naming, status markers, repository boundaries,
required verification, documentation ownership, and commit discipline. Do not
invent a lane convention or directory layout when the project already has one.

If required sources cannot be discovered, complete safe read-only exploration
first. Ask the user only when a missing choice or authority would materially
change the result.

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
Under explicitly authorized concurrent leases, that owner controls the
integrated ledger and each child writes only its assigned isolated ledger.

Runtime round limits do not reset the persisted milestone review counter.

## Goal Input

A multi-milestone request should name this file and provide either a strict
`STATUS_ORDER` or a `STATUS_PRIORITY` list for dispatching dependency-ready
milestones. It may also provide project-context paths, a status-file map,
downstream impacts, and execution policies:

```text
Using tabilet/GOAL.md, execute this loop.

PROJECT_CONTEXT:
- AGENTS.md
- path/to/roadmap.md

STATUS_PRIORITY:
F01, S01, O01, P01, X01?

STATUS_FILE_MAP:
F01 = path/to/status-F01.md
S01 = path/to/status-S01.md

DOWNSTREAM_IMPACTS:
F01 -> P01, O01
S01 -> P01, X01

PARALLELISM: 3
INTEGRATION: local-rebase-ff
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none
```

The block above is the portable protocol input. Submit it as an ordinary
request, through a compatible goal skill, or as the objective of an agent's
built-in `/goal` command. The built-in command keeps the objective active; it
does not replace this protocol or make `GOAL.md` ambient. In every form, the
request must explicitly name this file.

The identifiers above are examples only. They carry no meaning outside the
project that defines them.

Input rules:

- `PROJECT_CONTEXT` is optional. Use it to identify additional project sources
  that repository instructions do not already name.
- `STATUS_ORDER` is strict execution order. Every earlier required or triggered
  milestone must close before a later milestone starts; its arrows add ordering
  edges even when `PARALLELISM` is enabled. It contains milestone/status
  identifiers, not impact expressions.
- `STATUS_PRIORITY` lists the complete in-scope set, highest dispatch priority
  first, separated by commas. List position adds no ordering edge. Dispatch only
  milestones whose dependencies and impact reconciliation are satisfied, using
  this priority to choose among ready milestones. For example,
  `STATUS_PRIORITY: M01, A01, S01, P01` permits A01 and S01 to run together after
  M01 closes when both feed P01 and the parallel safety checks pass.
- Supply exactly one of `STATUS_ORDER` and `STATUS_PRIORITY`, with each ID
  appearing once. If both are supplied, resolve the conflicting request before
  execution. Never convert an explicit strict order into priority to unlock
  concurrency without user authorization.
- `STATUS_FILE_MAP` is optional when the roadmap or repository naming convention
  already resolves each identifier unambiguously.
- `DOWNSTREAM_IMPACTS` identifies pending specifications that must be
  reconsidered after a source milestone. An impact arrow does not authorize
  executing its targets early and does not replace declared dependencies.
- A `?` suffix means conditional. Skip that status without completing or
  cancelling it when its documented trigger is absent. Required statuses have
  no suffix.
- If neither selection field is supplied, use an unambiguous strict order from
  the project's roadmap. If no such order exists, request one rather than guessing.
- If a supplied strict order conflicts with dependencies, stop the affected
  execution and resolve a corrected order with the user before dispatch. Never
  discard a prerequisite or a requested ordering edge to create concurrency.
- Treat the supplied impact map as a minimum. Reconcile additional consumers
  discovered from implementation and review.
- `PARALLELISM` is optional. It sets the maximum number of concurrent milestone
  leases (defaults to 3 when present without a value). Concurrent execution is
  active only when project instructions explicitly define safe parallel
  ownership, `COMMIT_POLICY` is `task` or `milestone`, and `INTEGRATION` is
  authorized.
- `INTEGRATION` defaults to `none`. When set to `local-rebase-ff`, it authorizes local
  lease branches (`goal/<ID>`), external worktrees outside the project root
  (`../<repo>.goal/<ID>`), rebasing unpublished lease commits onto the captured
  integration branch, and fast-forward-only integration (`git merge --ff-only`).
  Under `COMMIT_POLICY: milestone` it also authorizes creating and amending one
  unpublished aggregate checkpoint, then finalizing that same commit with
  closure before integration. If the request forbids interim commits or
  amendment, use sequential execution for that policy. It does not authorize
  rewriting integrated history, push, publishing, or merge commits.

## Initialization

Before the first milestone:

1. Read this file, applicable repository instructions, discovered project
   sources, and every status file in the requested order or priority list.
2. Inspect every in-scope worktree. Preserve unrelated user changes and do not
   overwrite or absorb them into milestone commits.
3. Resolve each identifier to exactly one status specification. Validate its
   naming and indexing against project conventions and reject ambiguous IDs.
   When the project retires milestones, consult its history index to resolve
   stale paths and reserve historical IDs. An all-retired project remains
   initialized. Never recreate or retry a retired status from stale goal input.
4. Build a dependency graph from status dependencies, strict `STATUS_ORDER`
   edges when supplied, downstream impacts, and concrete code/configuration
   consumers. Keep `STATUS_PRIORITY` outside this graph; it chooses among ready
   milestones without adding dependencies. Reject cycles before dispatch.
5. Classify statuses as required, conditional, already completed, cancelled,
   closed historical, or currently unavailable because of an external input.
6. Record the reconciled remaining order or dispatch priority. Skip completed
   historical milestones rather than reimplementing them.
   A cancelled or superseded outcome does not automatically satisfy a required
   completion dependency; follow its authorized disposition and successor.
   Terminal task rows alone are insufficient: resume any incomplete milestone
   review, verification, reconciliation, or closure instead of skipping it.
7. Determine required verification, commit policy, related repositories, and
   external-mutation authority before making changes.
8. For concurrent leases, capture the integration worktree's symbolic `HEAD`
   with `git symbolic-ref --quiet HEAD` and its full commit ID with
   `git rev-parse --verify HEAD`. Preserve that full `INTEGRATION_REF` (for
   example, `refs/heads/trunk`), primary worktree path, and baseline in existing
   goal state or status notes and every execution brief. Honor an explicitly
   requested branch only after resolving its owning worktree. A detached HEAD
   or changed integration target stops integration; never assume a branch named
   `main`. Recheck this identity on resume and immediately before integration.

## Milestone Loop

Execute the following loop for each required or triggered conditional status.
Keep at most one milestone in active implementation at a time unless project
instructions explicitly define safe parallel ownership and the goal request
authorizes concurrent execution (via `PARALLELISM` and `INTEGRATION: local-rebase-ff`
under `COMMIT_POLICY: task` or `milestone`).

### Safe Parallel Execution (Concurrent Leases)

When project instructions define safe parallel ownership and the goal request
authorizes concurrent execution:

1. **Eligibility**: A milestone may be dispatched as a concurrent lease only if
   its active specification declares `Parallel-safe: yes`, no ordering path in
   either direction connects it to any currently running lease, its write set
   is disjoint from all running leases, and contract conflicts are checked in both directions:
   candidate reads must not intersect running writes, and candidate writes must
   not intersect running reads. Apply this pairwise to every running lease.
2. **External Worktrees**: Each lease executes in an isolated Git worktree
   located outside the project root (`../<repo>.goal/<ID>`) on a dedicated local
   branch (`goal/<ID>`). At most one row is `[~]` in progress within each lease.
   Leases use isolated verification resources (such as ports, database names,
   and caches). Every child brief includes this governing protocol, the resolved
   selection and policies (`COMMIT_POLICY`, `EXTERNAL_MUTATIONS`, `PARALLELISM`,
   `INTEGRATION`), user scope restrictions, ownership boundaries, and captured
   `INTEGRATION_REF`. Repository defaults cannot replace the resolved request.
   Review and reconciliation children receive the same authority context with
   an explicitly read-only assignment.
3. **Authoritative Review Gate**: The single authoritative bounded review-fix
   gate (iterations 1–10) runs in the lease on the diff after rebasing onto the
   captured integration branch, recording its full reviewed baseline and
   iteration counter in the lease's status notes. Under `task`, verified rows
   produce task commits. Under `milestone`, rows remain uncommitted until they
   are all verified, then one unpublished aggregate checkpoint carries the
   implementation for rebasing and review. Review fixes amend that checkpoint;
   its review counter never resets. Neither the checkpoint nor terminal rows
   establish milestone closure or make dependents ready.
4. **Baseline Check & Milestone Closure**: If the captured integration branch
   advanced during the review pass, the lease rebases and re-verifies;
   re-review is repeated only if newly landed commits
   touch the lease's write set or contracts read.
   Under `milestone`, before fast-forward integration the owner reserves the
   serial integration slot, pauses the lease writer, and performs integration
   verification, downstream reconciliation, shared-memory updates, and adopted
   retirement in that lease on the latest integration baseline. The owner
   verifies closure and amends the aggregate checkpoint into one finalized
   milestone commit containing implementation and closure, then fast-forwards
   it. There is no second closure commit. Other leases may continue isolated
   work but cannot integrate during this finalization. If the integration tip
   moves unexpectedly, stop integration and reconcile/reverify closure on the
   new baseline; do not apply a stale closure diff. Required verification or
   review failure leaves the checkpoint unpublished and the milestone incomplete.
5. **Fast-Forward Integration & Task Closure**: In the primary worktree, recheck
   that symbolic `HEAD` equals `INTEGRATION_REF`, the full tip matches the
   reviewed/finalized baseline, and the worktree is clean. Integrate strictly
   via fast-forward (`git merge --ff-only goal/<ID>`), preserving linear history
   and the selected commit policy. Never create merge commits.
   Under `task`, the owner now runs integration verification, reconciles
   downstream impacts from the integrated implementation diff, applies
   shared-memory updates, and retires the milestone. Commit substantive closure
   changes only when files change. Under `milestone`, closure is already in the
   single integrated commit. Dependents become ready only after verified
   closure and integration both pass.
6. **Failure & Resume**: Git worktrees and `goal/*` branches serve as durable
   lease records. A blocker, conflict, or iteration-10 failure halts that lease
   only; its worktree and branch are retained for inspection, its dependents
   stay unscheduled, and independent sibling leases continue. Interrupted
   sessions resume by listing worktrees (`git worktree list`) and continuing each
   lease from its status file.

### 1. Reconcile Before Starting

- Re-read the current status and relevant project sources; earlier milestones
  may have changed them.
- Confirm dependencies, triggers, required assets, and external inputs.
- Inspect current implementation and tests before assuming a task is missing.
- Rewrite obsolete pending tasks before implementation. Do not redo existing
  work merely because an older plan described it differently.
- If one general row is already in progress, resume exactly that row. Otherwise
  set only the current dependency-ready task to the project's in-progress state.
  Never leave more than one general row in progress across the active ledger
  unless authorized concurrent leases each own one row in their isolated ledger.

### 2. Implement Task Units

- Treat each project-defined task row or checklist item as an implementation
  and review unit.
- Preserve public interfaces, schemas, state formats, cache/storage contracts,
  configuration, CLI/HTTP behavior, and deployment compatibility unless the
  milestone explicitly changes them.
- Change related repositories in the same task only when project ownership and
  the goal scope include them.
- Update code-adjacent documentation and project memory/status sources in the
  same change as behavior, data, tooling, or operator-workflow changes.
  In concurrent leases, the child updates owned code and status sources and
  returns shared-memory proposals; only the owner writes shared memory, including
  during milestone closure in a lease.
- Maintain relevant reusable lessons with evidence. Preserve materially
  superseded knowledge under the project's history convention before replacing
  it; do not turn the lesson reference into a chronological session log.
- Use deterministic fixtures and project-approved disposable test resources.
  Never commit production secrets, customer/private data, captured traffic,
  generated local credentials, or environment-specific runtime state.
- Mark a task complete only after its acceptance and focused verification pass.
- When a failed attempt is consumed or a row is superseded, retain it as closed
  historical evidence, record the outcome and accepted successor, and never
  retry it.
- Before invoking an operational launcher, require its exact authorized
  operation row to be in progress. The status marker records selection and does
  not grant external-mutation authority.

### 3. Verify And Deep-Review

- Run every verification command required by the status file and applicable
  repository instructions, plus proportionate tests for affected consumers.
- Exercise required migration, compatibility, rollback, security, concurrency,
  and failure-path checks for the changed surfaces.
- Run required checks in every related repository changed by the milestone.
- After automated checks pass, run the bounded review-fix gate below.
- Carry a lower-severity finding forward only when it has a named pending owner
  and explicit rationale. P1, P2, and higher-severity findings cannot be carried
  forward.
- Update the project's decision/evolution log only when its documented trigger
  is met.
- Mark the milestone complete only when all required tasks, acceptance
  criteria, verification, documentation, and the review-fix gate are closed.

#### Bounded Review-Fix Gate

Use the project's documented severity definitions when they exist. Otherwise:

- **P1** is a severe defect in milestone acceptance, correctness,
  security/privacy, data integrity, or a public compatibility contract.
- **P2** is a material defect in supported behavior, reliability,
  compatibility, operations, or required verification/documentation that does
  not rise to P1.

Any severity above P1 also blocks this gate. The initial deep-review pass is
iteration 1. In each iteration:

1. Read the persisted review count and findings before starting. Record the
   current iteration as started before review; an interrupted pass resumes that
   iteration, never resets to 1. Review the full milestone implementation and
   diff, with special attention to
   fixes made by the preceding iteration. Check correctness, failure semantics,
   security/privacy, compatibility, operations, tests, and documentation.
2. Classify and record the findings. Persist the iteration number and findings
   in the current status notes or equivalent active goal state before applying
   fixes, so a continuation cannot reset the counter. If the pass finds no P1,
   P2, or higher-severity finding, the gate passes.
3. Otherwise, when the current iteration is below 10, fix every P1, P2, and
   higher-severity finding in the current milestone and rerun the affected
   verification before beginning the next iteration. The next pass reviews the
   whole milestone again, not only the latest patch.

Run at most 10 iterations; a session or reviewer change does not reset the
counter. If iteration 10 still finds a P1, P2, or higher-severity issue, the
gate fails: do not start another automatic fix-review cycle, leave the milestone
incomplete, record the remaining findings using the project's blocked-status
mechanism, and report the iteration limit as the blocker. Do not begin
downstream reconciliation; further attempts require explicit user direction.

### 4. Reconcile Downstream Work

Before advancing:

1. Open every pending status listed for the completed source in
   `DOWNSTREAM_IMPACTS`, plus additional affected consumers discovered during
   implementation or review.
2. Update dependencies, assumptions, tasks, acceptance criteria,
   compatibility/migration notes, verification, rollout, and rollback
   expectations to match the implementation that now exists.
3. Remove or rewrite obsolete work. If an earlier milestone implemented a later
   task, record lineage; do not mark the later milestone complete unless all of
   its acceptance criteria are satisfied.
4. Add newly discovered work to an existing pending owner when it fits. Create
   a new milestone/status ID only when project conventions allow it and the work
   is a distinct review unit.
5. Keep intentionally deferred work in the project's deferral/backlog source
   until its documented trigger is satisfied. Do not reserve an ID unless the
   project convention requires it.
6. Update the project roadmap when dependencies or remaining order change.
7. Recompute the dependency graph and remaining order or priority. Continue automatically
   when the revised work remains within the goal's product scope and authority.

Pending status rows are planning baselines until their implementation starts
and are expected to evolve. Completed, cancelled, and closed-historical rows
should change only for factual correction, explicit ownership transfer, or
lineage clarification. Closed-historical rows are never retried and do not
block their accepted successors.

After downstream reconciliation, follow the project's documented retirement
procedure when it has adopted one. Consolidate durable knowledge, retain full
specification and task evidence, then remove the closed work from the active
index. Retired records stay frozen; later corrections use linked new records.
Refresh the remaining resolved order or priority and any existing disposable launch
reference. Do not require a separate context-snapshot skill, clean worktree, or
extra commit to perform ordinary consolidation and retirement.

Retirement obeys the current commit policy: no commits under `none`, inclusion
in milestone closure under `milestone`, or the final task/substantive closure
commit under `task`. Record the observed evidence baseline honestly, identifying
included uncommitted work or unversioned provenance without claiming that an
earlier commit contains later changes.

When Git supplies that baseline, capture the full object ID with
`git rev-parse --verify HEAD`; never persist an abbreviated log-display hash.
For a milestone lease whose checkpoint will be amended, use the full reviewed
integration baseline instead and declare the included implementation and closure
changes. An amendable checkpoint is not stable frozen-record provenance.
Validate the complete retirement envelope and retained source documents against
the project's contract before deleting active sources. A malformed record is
an incomplete retirement, not accepted closure; preserve the sources and stop.

### 5. Continue Or Stop

Continue while all of these remain true:

- the next milestone's dependencies and required inputs are available;
- remaining work stays within the goal scope and mutation authority;
- no conflicting user-owned worktree change prevents safe implementation; and
- verification can establish the milestone acceptance criteria.

Do not guess or silently broaden scope when completion needs a new product or
policy choice, production credential, customer/platform requirement, external
account action, destructive migration, deployment authority, or unrelated
repository change. Complete safe in-scope work, leave the affected status
pending, record the exact blocker, and follow the active goal mechanism's
blocked-state rules.

Conditional milestones are skipped when their trigger is absent. They remain
pending and do not prevent completion of a goal that explicitly marked them
conditional. A required pending milestone prevents overall goal completion.

## Commit And External-Mutation Policy

`COMMIT_POLICY` values:

- `none` (default): do not create commits.
- `task`: create one focused commit per completed project-defined task unit
  after its verification passes.
- `milestone`: create one finalized commit containing implementation and closure
  after each milestone closes. In Tier 1 only, an unpublished aggregate
  checkpoint may be created and amended for rebasing and review as authorized
  by `INTEGRATION: local-rebase-ff`; the owner completes closure in the lease
  before finalizing and integrating that single commit. No per-row commits or
  second closure commit are permitted under this policy.

Never commit unrelated user changes. Do not amend, rewrite history, push, merge,
tag, publish, or open a change request unless the goal request explicitly
authorizes that action (including the unpublished checkpoint amendments,
rebasing, and fast-forward integration defined by `INTEGRATION: local-rebase-ff`).

`EXTERNAL_MUTATIONS` defaults to `none`. Code implementation does not authorize
deployment, account/provider changes, credential rotation, live traffic,
payments, DNS changes, messages, or other external mutations. List authorized
systems, actions, and scopes explicitly. Resolve exact targets with read-only
checks before acting.

## Completion Report

At the end of each milestone, record:

- completed status and task units;
- retired record locations and durable lessons, when the project uses them;
- material interface, data, configuration, UI, and operator changes;
- downstream specifications reconciled and any order change;
- verification and deep-review results, including review-fix iteration count;
- commits or external mutations, if authorized;
- conditional statuses skipped; and
- remaining blockers or external actions.

Mark the overall goal complete only when every required status in the
reconciled selection is complete and no required work remains.

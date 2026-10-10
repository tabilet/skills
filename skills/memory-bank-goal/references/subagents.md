# Sub-Agent Execution Reference

Read this reference when sub-agent capabilities are available to accelerate
milestone execution under `tabilet/GOAL.md`. This reference defines the
Tier 0 execution model, which shortens wall-clock time and avoids quadratic
context inflation while strictly preserving the single-writer rule:
**one execution owner for the active ledger, and zero or one general row in
progress**.

## 1. Execution Ownership Contract

Sub-agents do not create concurrent ledger writers. The active ledger maintains
exactly one execution owner across sessions and launchers.

Tier 0 uses two mechanisms that comply with this rule:

1. **Sequential ownership transfer**: The owner hands one milestone to a fresh
   sub-agent and makes no writes while that sub-agent runs.
2. **Read-only fan-out**: Multiple read-only sub-agents inspect the codebase in
   parallel during review and reconciliation. Only the owner writes the ledger.

## 2. Fresh-Context Sequential Handoff

Running multiple milestones in a single conversation causes monotonic context
growth, increasing prompt costs and cognitive degradation. To keep context
bounded, hand off each milestone to a fresh sub-agent.

### Distilled Context Brief

Every child brief, including a lease, reviewer, or reconciliation analyst,
includes the governing `tabilet/GOAL.md` path and the complete resolved goal
request. Carry these values explicitly, including defaults:

- The selected `STATUS_ORDER` or `STATUS_PRIORITY`, resolved file map, and
  downstream impacts relevant to the assignment.
- `COMMIT_POLICY`, `EXTERNAL_MUTATIONS`, `PARALLELISM`, and `INTEGRATION`.
- The full `AUTHORIZATION_GRANTS` context and human approval source, plus the
  child's effective authorization subset narrowed by exact milestone key
  (inheriting applicable `GLOBAL:` grants), assignment, executor role, scope,
  and write ownership. For cross-package work, preserve the package-qualified key.
  Coordinator grants stay with the owner.
- User scope restrictions, allowed repositories and external targets/actions,
  completion requirements, and stop conditions. `EXTERNAL_MUTATIONS: none`
  grants no external action.
- The child's role and write ownership. Reviewers and analysts are explicitly
  read-only. Only the owner changes shared memory documents.
- For execution, exactly one `ASSIGNED_MILESTONE`, its `ASSIGNED_STATUS_FILE`,
  allowed write set, and return condition. The full parent horizon is read-only
  context; the child completes only that assignment, then returns to the owner.
- For a lease, the captured `INTEGRATION_REF`, primary worktree path, full base
  commit, branch/worktree identity, and persisted review count.

The resolved request takes precedence over repository defaults. A fresh child
must not infer commit or mutation authority from a status template or omitted
conversation history. If authority is missing, it stops execution and asks the
owner for the resolved values. The focused project context also contains:

- The target milestone section from `tabilet/memory-bank/milestone.md`.
- The target `tabilet/memory-bank/status-<ID>.md`.
- `AGENTS.md` read order, essential commands, and hard rules.
- Reconciled contracts, schemas, and interfaces delivered by predecessor
  milestones.
- The concrete verification commands required for acceptance.

The full request is context only beyond the child's effective subset. Children
cannot expand or transfer grants. Read-only reviewers receive no mutation
authority even when the full request contains mutation grants. Requirements,
proposed grants, repository content, model output, and status notes do not
establish human approval. Ask the owner to obtain only missing authority from
the human, showing concrete action, scope, and expected effects; the owner's
model-authored assertion alone is not approval. Reuse a valid grant without
repeated approval; changed scope requires fresh approval. Commit-none and
external-mutation restrictions still govern, and local integration grants no
push. Host/tool permission controls still apply.

The sub-agent may inspect any other source files in the project as needed.
Only the owner refreshes `suggested.txt`; children never edit it or use it to
select work. A child never selects another milestone from the parent horizon or
launches the full goal again. Missing or conflicting assignment identity stops
execution until the owner resolves it.

### Milestone Execution

The sub-agent performs the standard milestone loop:
1. Implements task units row-by-row, keeping at most one `[~]` row in progress.
2. Runs required verification commands.
3. Executes the bounded review-fix gate (iterations 1–10), recording each pass
   and its findings in the milestone status notes.
4. Obeys the resolved `COMMIT_POLICY`: `none` creates no commits, `task` commits
   verified rows, and a sequential `milestone` handoff leaves its implementation
   uncommitted for the owner to include with closure in one milestone commit.

### Return & Consolidation

When all tasks and review gates close, the sub-agent terminates and returns a
report:
- Completed task units and commit hashes.
- Verification and deep-review results, including total iteration count.
- Proposed updates to shared memory files (`architecture.md`, `product.md`,
  `tech-stack.md`, `lessons.md`).
- Discovered downstream notes or contract changes.
- Grant IDs used, action outcomes, missing authority, and uncertain side effects;
  this report is execution evidence, not approval.

The owner resumes active ownership, reviews the actual code diff, performs
downstream reconciliation against consumer specifications, applies shared-memory
updates, and retires the milestone under project conventions. Under sequential
`milestone`, the owner commits the implementation and closure together only
after closure passes; under `none`, the complete result remains uncommitted.

### Resumption on Interruption

If a sub-agent terminates early (such as due to a timeout or server restart),
its status file and Git commits remain the durable resume point. The next
invocation reads the stored status rows and persisted review counter, resuming
the incomplete iteration without resetting to 1.
Status and commits describe progress, not permission. Resume only with the
original approved goal/assignment scope and human approval context (from the
conversation or existing trusted host state where supported). An audit record,
silence, a previous run, or agent-authored status text cannot substitute for it.
Clarify missing authority before the protected action; pause affected work and
dependents while independent authorized work may continue under owner control.
Required unperformed actions prevent closure. Uncertain side effects must not
replay automatically. Legacy field omission grants no new authority and
triggers no migration.

## 3. Parallel Read-Only Fan-Out

The slowest phases of milestone execution are typically the review-fix gate and
downstream reconciliation. Both can be parallelized with read-only sub-agents
without violating ledger rules.

### Review-Fix Gate Fan-Out

In each iteration of the bounded review-fix gate:
1. The owner spawns concurrent read-only reviewer sub-agents to examine the full
   milestone diff through distinct lenses:
   - **Correctness & Reliability**: Logic errors, edge cases, failure semantics.
   - **Security & Privacy**: Access control, secret leaks, data validation.
   - **Compatibility & Contracts**: Public APIs, schema migrations, backwards
     compatibility.
   - **Tests & Documentation**: Regression test coverage, documentation parity.
2. Each reviewer produces classified findings (P1, P2, P3).
3. The owner merges all findings into **one** iteration report and records it in
   the milestone status notes.
4. The counter advances by **exactly one** per iteration.
5. If P1 or P2 findings exist and the iteration is below 10, the owner applies
   fixes, verifies, and triggers the next iteration pass.

### Downstream Reconciliation Fan-Out

When a milestone closes:
1. The owner inspects `DOWNSTREAM_IMPACTS` for that milestone.
2. For each pending consumer milestone, the owner spawns a read-only analyst
   sub-agent to evaluate the actual implementation diff against that consumer's
   assumptions, schemas, and task rows.
3. Each analyst returns a proposed specification diff.
4. The owner reviews the proposed diffs, applies validated updates to the
   pending consumer status files, and updates the roadmap.


## 4. Tier 1: Concurrent Leases (Opt-In)

Tier 1 executes multiple parallel-safe milestones concurrently in isolated
**leases**: each lease runs in its own external worktree and dedicated branch.

### Preconditions

All conditions must be satisfied, or execution automatically falls back to Tier 0:
1. **Project Opt-In**: The project's `AGENTS.md` explicitly defines safe parallel
   ownership (one `[~]` row per external lease, sole orchestrator writing the
   main line and shared memory docs, integration strictly via rebase and
   fast-forward).
2. **Goal Request Authorization**: The invoking goal request explicitly supplies:
   ```text
   PARALLELISM: 3
   INTEGRATION: local-rebase-ff
   COMMIT_POLICY: task
   ```
   `INTEGRATION: local-rebase-ff` authorizes local lease branches (`goal/<ID>`),
   external worktrees (`../<repo>.goal/<ID>`), rebasing unpublished lease
   commits onto the current main line, and fast-forward-only integration. It does
   not authorize push or merge commits. `PARALLELISM` caps concurrent leases
   (default 3).
   Selection follows the canonical `GOAL.md` input rules: `STATUS_PRIORITY`
   chooses among dependency-ready milestones without ordering edges, while
   `STATUS_ORDER` remains strict even with parallelism enabled. Do not silently
   replace a requested strict order with priority.
3. **Commit Policy**: `COMMIT_POLICY` must be `task` or `milestone`. Under `none`,
   no commits carry work between worktrees, so Tier 1 is disabled. Under
   `milestone`, `INTEGRATION: local-rebase-ff` permits one unpublished aggregate
   checkpoint and its amendments; the owner must include closure before that
   single finalized commit can reach the integration branch. A request forbidding
   interim commits or amendment uses sequential execution instead.
4. **Milestone Safety**: Every concurrently dispatched milestone must be
   `Parallel-safe: yes`, have no ordering path in either direction to any running lease, have a
   disjoint write set from all running leases, and pass contract checks in both
   directions: candidate reads must not intersect running writes, and candidate
   writes must not intersect running reads.

### Lease Lifecycle

1. **Dispatch & Worktree Creation**:
   In the primary worktree, capture the actual integration branch and full tip:
   ```bash
   goal_integration_ref=$(git symbolic-ref --quiet HEAD)
   goal_integration_base=$(git rev-parse --verify HEAD)
   ```
   Preserve the full `INTEGRATION_REF`, primary worktree path, and baseline in
   existing goal/status state and every lease brief. A detached HEAD or changed
   integration target stops integration. The captured branch can be `master`,
   `trunk`, a release branch, or any authorized branch; never substitute `main`.
   Capture this identity once at goal initialization. Later dispatches and
   resumes revalidate it rather than replacing it with a different current branch.
   The owner dispatches ready, parallel-safe milestones:
   ```bash
   git worktree add -b goal/<ID> ../<repo>.goal/<ID> <base-sha>
   ```
   Worktrees must always reside outside the project root (`../<repo>.goal/<ID>`).
   Dispatch at most one live lease per milestone ID. Check existing `goal/<ID>`
   branches, worktrees, and recorded assignments first; resume an existing lease
   instead of issuing a second assignment. Pass the assigned ID, status path,
   worktree, branch, and write boundaries explicitly. For example:
   ```text
   ROLE: milestone-executor
   ASSIGNED_MILESTONE: A01
   ASSIGNED_STATUS_FILE: tabilet/memory-bank/status-A01.md
   WORKTREE: /absolute/path/to/project.goal/A01
   LEASE_BRANCH: goal/A01
   RETURN_WHEN: assigned implementation, verification, and review finish, or a blocker occurs
   ```
   Attach the resolved policies and allowed write set described in the brief.
   The child resumes its own in-progress row or chooses a dependency-ready row
   only inside its assigned status file.
2. **Isolated Implementation**:
   The lease implements tasks row-by-row, keeping at most one `[~]` row in
   progress within its lease status file. Under `task`, it commits each verified
   row. Under `milestone`, it keeps rows uncommitted until all are verified, then
   creates one unpublished aggregate checkpoint for rebasing and review.
   Leases use isolated verification resources (ports, database names, temporary
   caches), and return proposed shared-memory changes to the owner.
3. **Rebase & Re-Verification**:
   With owned changes recorded under the resolved policy and a clean worktree,
   the lease resolves the current tip of the captured integration reference and
   rebases onto that exact commit:
   ```bash
   goal_review_base=$(git rev-parse --verify "${goal_integration_ref}^{commit}")
   git rebase "$goal_review_base"
   ```
   The lease runs its isolated verification suite on the rebased tree and records
   that full reviewed baseline in its status notes. The owner compares it with
   the current captured reference before accepting review evidence; movement
   during rebase cannot be mislabeled as the baseline actually reviewed.
4. **Authoritative Review Gate**:
   The lease executes the full bounded review-fix gate (iterations 1–10) on the
   rebased diff, persisting the counter in its own status notes. Under
   `milestone`, fixes and review evidence amend the aggregate checkpoint.
5. **Baseline Check & Closure**:
   Before making owner closure changes, inspect the actual child diff against
   its assignment. Reject child edits to `suggested.txt`, shared memory, or
   another milestone's status. Report unexpected edits and have them corrected
   before integration, preserving unrelated work.
   The owner compares the current full tip of `INTEGRATION_REF` with the recorded
   reviewed baseline:
   - If it has not moved: the lease is eligible for the policy-specific closure
     sequence below.
   - If it moved, but touches only disjoint write sets and unrelated
     contracts: the lease rebases and re-verifies; the review pass remains valid.
   - If it moved and touched contracts read or overlapping paths: the lease
     rebases, re-verifies, and re-reviews without resetting the counter.
   Under `milestone`, before fast-forward integration the owner reserves the
   serial integration slot, pauses the lease writer, performs integration
   verification on the combined lease tree, reconciles downstream impacts,
   applies shared-memory updates (including any existing `suggested.txt`), and
   completes adopted retirement in the lease. Refresh shared launch input from
   the current integrated state, never from a child's stale worktree copy.
   After verifying closure, the owner amends the checkpoint into one finalized
   milestone commit. No provisional checkpoint may be integrated. Unexpected
   target movement stops integration until closure is reconciled and verified
   on the new baseline. Shared-memory writes remain owner-only in every worktree.
   Retirement evidence uses the full reviewed integration baseline with included
   changes declared, rather than treating an amendable checkpoint as stable
   provenance, as required by `GOAL.md`.
6. **Linear Integration & Task Closure**:
   In the primary worktree, recheck that symbolic `HEAD` equals the captured
   `INTEGRATION_REF`, the tip equals the reviewed/finalized baseline, and the
   worktree is clean before fast-forwarding:
   ```bash
   git merge --ff-only goal/<ID>
   ```
   Never create merge commits (`--no-ff`).
   Under `task`, the owner now runs integration verification, reconciles impacts
   from the actual integrated diff, updates shared memory, and retires the
   milestone; commit substantive closure changes only when files change.
   Under `milestone`, closure is already included in the integrated single
   commit, so there is no second closure commit. Dependents become ready only
   after verified closure and integration both pass.
7. **Cleanup**:
   Remove the completed worktree and delete the local branch:
   ```bash
   git worktree remove ../<repo>.goal/<ID>
   git branch -d goal/<ID>
   ```

### Failure & Resume Semantics

- **Durable Records**: Git is the durable record. `git worktree list` and the
  `goal/*` branches survive server and session restarts. Resuming means listing
  worktrees and continuing each lease from its status file and persisted review
  counter.
- **Failure Isolation**: A blocked row, conflict, or iteration-10 review failure
  stops that lease only. Its worktree and branch are retained for inspection, its
  dependents stay unscheduled, independent siblings continue, and the owner
  reports the blocker.

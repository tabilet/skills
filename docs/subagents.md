# Sub-Agent Milestone Execution

This guide defines the sub-agent execution architecture for multi-milestone
workflows under [`tabilet/GOAL.md`](goal.md). It establishes how to accelerate
milestone delivery through fresh-context task execution and parallel read-only
fan-out (Tier 0), as well as opt-in concurrent worktree leases (Tier 1), while
strictly preserving milestone quality, verification rigor, and the
single-ledger execution owner invariant.

This protocol requires a hosting agent that can delegate. The standalone Python
API runner and optional `tabilet` controller have no native sub-agent scheduler;
they retain serial execution and their own commit contracts. The controller
rejects linked worktrees. See the
[API execution scope](https://github.com/tabilet/skills/blob/main/docs/EXECUTION.md#changes-since-v240).

## Goals and non-goals

Goals:

1. Design milestones so a sub-agent can execute one without lowering milestone
   quality.
2. Run sub-agents in a manageable way that shortens wall-clock time.

Non-goals:

- **No trading quality for speed.** Every milestone keeps its full acceptance,
  verification, bounded review-fix gate, downstream reconciliation, and
  closure. A faster schedule that skips or weakens any of these is a regression.
- **No pruning of downstream impacts.** `GOAL.md` treats the supplied impact map
  as a minimum. Parallelism must come from milestone structure, never from
  declaring fewer obligations.
- **No vendor coupling.** The protocol names capabilities ("start an isolated
  sub-agent", "stop a sub-agent"), not one agent's tool names.
- **No new project state.** No in-tree worktree folders, lock files, or
  generated plan directories.

## Cost and time model

Two different benefits are easy to conflate:

- **A fresh context per milestone** bounds the context each turn carries. That
  improves attention and prevents quadratic context inflation. It does not
  require concurrency: ephemeral sub-agent handoffs achieve this sequentially.
- **Concurrency** shortens wall-clock time when the milestone graph is wide. It
  does not save tokens; it adds integration work such as rebases,
  re-verification, and occasional re-review.

| | One long session | Fresh context per milestone, sequential | Concurrent leases (Tier 1) |
|---|---|---|---|
| Context per turn | Grows across milestones | Bounded per milestone | Bounded per milestone |
| Total tokens | Highest without prompt caching; caching narrows the gap | Lowest | About sequential, plus integration overhead |
| Wall-clock time | Sum of milestones | Sum of milestones | Critical path plus serial integration |
| Quality risk | Attention drift late in a long run | Low | Low only when the Part A rules hold |

Wall-clock time under concurrency is bounded by the longest dependency chain
plus every step the owner must perform serially (integration, reconciliation,
retirement). Keeping that serial part small is why the authoritative review
runs inside each lease rather than in the owner (see Tier 1).

Empirical validation using SQLite audit tracking (`tabilet-audit`) verified:

1. **Context bounding:** Starting each milestone with a distilled context brief
   prevents prompt inflation across tasks.
2. **Wall-clock compression:** Parallel read-only fan-out across review lenses
   and downstream reconciliation completes in approximately 3 minutes per
   iteration without compounding serial inspection wait times.
3. **Defect coverage:** Decomposing reviews into orthogonal lenses (Correctness,
   Security, Tests) catches complementary defects that single monolithic reviews
   frequently overlook.

## Part A — Designing parallel-safe milestones

### Three relations, not one

Planning records dependencies and downstream impacts. Parallel safety
requires a third relation, and each has a distinct job:

| Relation | Meaning | Rule |
|---|---|---|
| Depends on | The consumer needs behavior the producer delivers | Hard ordering edge |
| Downstream impacts | The producer's result must be reconciled into the consumer's pending specification | Always complete and never pruned. It also implies ordering: the consumer cannot start before that reconciliation |
| Write set | Paths, public contracts, and shared resources the milestone changes | Used only to decide whether two unordered milestones may run at the same time |

Two milestones are **parallel-safe** only when all three hold:

1. no ordering path connects them in either direction;
2. their write sets are disjoint; and
3. neither reads a contract the other changes.

Transitive reduction may simplify the *scheduling copy* of the graph. It must
never remove an entry from the reconciliation list. If `A` impacts both `B` and
`C`, and `B` also impacts `C`, then `C` is still reconciled against `A`'s actual
change, because `B` may not carry every detail of it.

### Milestone specification fields

Active milestone specifications in `tabilet/memory-bank/milestone.md` define
these boundaries:

```markdown
### A01 — Billing settlement
- Depends on: M01
- Downstream impacts: P01
- Write set: src/billing/**, tests/billing/**, contract: settlement-events v1
- Contracts read: core-model v1 (frozen by M01)
- Shared verification resources: postgres (per-lease database name)
- Parallel-safe: yes — disjoint from S01; reads only frozen M01 contracts
```

`Parallel-safe` defaults to `no`. Planning marks a milestone `yes` only when its
write set and contracts justify it. When in doubt, serialize.

### Patterns that keep quality intact

- **Contract-first split.** Move shared schemas, interfaces, and their contract
  tests into an early milestone and freeze the contract when it closes. Domain
  milestones then consume a stable contract and become parallel-safe with each
  other.
- **Escalate contract changes.** A milestone that discovers it must change a
  frozen contract stops and reports. It never edits the contract silently;
  the owner re-plans the affected consumers.
- **Two-level acceptance.** Each milestone has acceptance that can be verified
  in isolation, plus a named integration check that runs after its work joins
  the main line.
- **One writer for shared memory.** `architecture.md`, `product.md`,
  `tech-stack.md`, `lessons.md`, `milestone.md`, and any existing `suggested.txt` are written only by the
  owner. A sub-agent returns proposed changes to them; it never edits them.
- **Balanced size.** A milestone far longer than its siblings dominates the
  critical path. Split it along its own write-set boundaries when that is a
  natural review unit.

These fields and patterns belong to planning (`memory-bank-init`,
`memory-bank-propose`, `memory-bank-reconcile`), not to execution. Execution
only reads them.

## Part B — Tier 0: faster within existing rules

Tier 0 requires no rule relaxation. It preserves exactly one ledger writer at all times.

### Fresh-context sequential handoff

The owner hands one milestone to a fresh sub-agent and does not write while it
runs. That is an ownership transfer, not a second writer. The sub-agent
receives a focused brief rather than the owner's whole conversation:

- the milestone specification and its status file;
- exactly one `ASSIGNED_MILESTONE`, its `ASSIGNED_STATUS_FILE`, allowed writes,
  and the condition for returning to the owner;
- the governing `tabilet/GOAL.md` and complete resolved request: the chosen
  `STATUS_ORDER` or `STATUS_PRIORITY`, commit and external-mutation policies,
  concurrency/integration authority, user scope restrictions, and stop conditions;
- the child's role and owned write boundaries, plus the captured integration
  reference, primary worktree path, and full baseline when using a lease;
- `AGENTS.md` read order, essential commands, and hard rules;
- the reconciled contracts it consumes; and
- the required verification commands.

It may read anything else in the repository it needs. It performs the normal
`GOAL.md` loop for that milestone, persisting the review counter in its status
notes, and returns a report: rows completed, verification evidence, review
iterations and findings, commits, proposed shared-memory changes, and
blockers. The owner then resumes, performs downstream reconciliation from the
actual diff, applies shared-memory changes, and retires the milestone.

If the sub-agent stops early, its status file is the resume point. The persisted
review counter never resets.
Every child, including read-only reviewers and analysts, receives these resolved
policies; repository files cannot recover restrictions from the parent's
conversation. Under `COMMIT_POLICY: none`, the handoff creates no commits.
Under sequential `milestone`, the child leaves its changes for the owner to
commit together with closure, following `GOAL.md`.

The owner resolves `suggested.txt` against live project truth before dispatch.
The full goal remains context for a child; its explicit assignment defines the
work it may execute. For example, a child assigned A01 at
`../<repo>.goal/A01` works only on `status-A01.md` and A01's declared write set.
It returns after the assigned implementation, verification, and review finish
or a blocker occurs. It never selects S01 from the suggestion or launches the
full goal again. The owner keeps at most one live lease per milestone ID and
resumes that lease after interruption.

### Parallel read-only fan-out

The slowest phases of a milestone are usually review and reconciliation. Both
can fan out to read-only sub-agents without creating a second writer:

- **Review.** In each review-fix iteration, several read-only reviewers examine
  the same full milestone diff through different lenses: correctness and
  failure semantics; security and privacy; compatibility and operations; tests
  and documentation. The owner merges their findings into **one** iteration and
  records it once, so the counter advances by exactly one per pass.
- **Downstream reconciliation.** For each impacted pending consumer, a read-only
  analyst drafts the specification changes from the actual implementation
  diff. The owner reviews every draft and applies it.

This shortens even a strict dependency chain, where concurrent implementation
offers nothing, and independent review lenses improve defect detection.

## Part C — Tier 1: concurrent leases (opt-in)

Tier 1 runs multiple parallel-safe milestones concurrently. Each runs in an
isolated **lease**: a sub-agent with its own branch and external worktree.

### Preconditions

All of these must hold, or Tier 1 is unavailable and execution falls back to
Tier 0:

1. The project's `AGENTS.md` explicitly defines safe parallel ownership: at
   most one `[~]` row per lease, only the owner integrates into the main line,
   and only the owner writes shared memory documents.
2. The goal request authorizes it explicitly:

   ```text
   Using tabilet/GOAL.md, execute this loop.

   STATUS_PRIORITY: M01, A01, S01, P01
   DOWNSTREAM_IMPACTS:
   M01 -> A01, S01
   A01 -> P01
   S01 -> P01

   PARALLELISM: 3
   INTEGRATION: local-rebase-ff
   COMMIT_POLICY: task
   EXTERNAL_MUTATIONS: none
   ```

   `INTEGRATION: local-rebase-ff` authorizes local lease branches, rebasing
   unpublished lease commits, and fast-forward-only integration. It does not
   authorize pushing or merge commits. `PARALLELISM` caps concurrent leases and
   defaults to 3 when the field is present without a value.
   `STATUS_PRIORITY` chooses among ready milestones; it adds no dependencies.
   This example lets A01 and S01 run together after M01 closes, with P01 waiting
   for both. A request using `STATUS_ORDER: M01 -> A01 -> S01 -> P01` instead
   requires that strict sequence, even with parallelism enabled. Use exactly
   one selection field, as specified by `GOAL.md`.
3. `COMMIT_POLICY` is `task` or `milestone`. Under `none` there are no commits to
   carry work between worktrees, so Tier 1 is disabled.
   For `milestone`, local integration authority permits one unpublished aggregate
   checkpoint and its amendments for rebase and review. The owner includes
   closure before integrating one finalized milestone commit. A request that
   forbids interim commits or amendment uses sequential execution instead.
4. Every milestone dispatched concurrently is `Parallel-safe: yes` and passes
   the three conditions in Part A against every other running lease.

### Lease lifecycle

```text
Owner: capture actual integration branch and baseline; dispatch ready milestone
  │
  ▼
Create branch goal/ID and worktree at ../<repo>.goal/<ID>
  │
  ▼
Lease: implement rows, one [~] at a time; task commits or aggregate checkpoint
  │
  ▼
Lease: verify with lease-isolated resources
  │
  ▼
Lease: rebase onto captured INTEGRATION_REF and re-verify
  │
  ▼
Lease: run authoritative review-fix gate on rebased diff
  │
  ▼
Has the captured integration branch moved since that rebase?
  ├── No  ───► Continue with the policy-specific closure below
  ├── Yes (disjoint) ───► Lease: rebase + re-verify only
  └── Yes (touches write set/contracts) ───► Lease: rebase + re-verify + re-review
  │
  ▼
Owner under milestone: pause lease writer, close in lease, finalize one commit
  │
  ▼
Owner: fast-forward the captured integration branch (git merge --ff-only)
  │
  ▼
Owner under task: integration check, reconcile impacts, update memory docs, retire
  │
  ▼
Teardown worktree and branch; dispatch newly ready milestones
```

### Rules

- **Worktree location.** Outside the project tree, at
  `../<repo>.goal/<ID>`. An in-tree folder would dirty the main worktree, leak
  into test discovery, and accumulate as a generated directory.
- **Durable lease record.** Git is the record. `git worktree list` and the
  `goal/*` branches survive a session or server restart, and each lease's status
  file shows its progress and review counter. Existing goal/status notes retain
  the actual `INTEGRATION_REF`, primary worktree path, and full baseline.
  Resuming means listing worktrees and rechecking those identities before
  continuing each lease from its status file. No new file is created.
- **One authoritative review.** The bounded review-fix gate runs once, in the
  lease, on the diff after rebasing onto the current main line, with its counter
  in the lease's status notes. When other work lands before integration, the
  lease rebases and re-verifies; the review is repeated only when the newly
  landed commits touch the lease's write set or contracts read.
- **Linear integration.** Rebase and advancement checks use the captured branch,
  whether named `main`, `master`, `trunk`, or a release branch. The owner checks
  its symbolic `HEAD` and tip before integration. Fast-forward preserves the
  selected commit policy: task commits under `task`, one finalized milestone
  commit under `milestone`. Never create merge commits (`--no-ff`).
- **Closure and commit policy.** `GOAL.md` owns the sequence. Under `task`, the
  owner closes after integration and commits substantive closure changes only
  when files change. Under `milestone`, the owner reserves the serial integration
  slot, pauses the child, verifies the combined lease tree, reconciles impacts,
  updates shared memory, and completes adopted retirement in the lease. It then
  finalizes the checkpoint with that closure and fast-forwards; no provisional
  checkpoint lands and no second closure commit is created. Unexpected target
  movement requires reconciling and verifying closure on the new baseline.
- **Reconciliation from code.** The owner reconciles every downstream impact
  against the actual combined implementation diff: before integration for
  `milestone`, afterward for `task`. Dependents wait for both verified closure
  and integration.
- **Shared launch input.** Only the owner refreshes an existing `suggested.txt`
  during serial closure from the current integrated state. Children receive
  explicit assignments instead of consulting that file for task selection.
  Before adding owner closure changes, inspect the child diff against its
  assignment and reject edits to shared files or another milestone's status.
  Worktree isolation keeps files separate on disk; this diff check prevents
  competing shared edits from entering integration history.
- **Runtime-discovered impact.** If the owner discovers that a running lease
  consumes a change that just landed, it asks the lease to stop at the next row
  boundary, reconciles the lease's pending rows, and lets it resume. A
  completed row that is now invalid is retained as `[-]` closed historical
  evidence with a named successor.
- **Failure isolation.** A blocked row, a review gate exhausted at iteration 10,
  or an integration conflict stops that lease only. Its branch and worktree are
  kept for inspection, its dependents stay unscheduled, independent leases
  continue, and the owner reports the blocker.
- **Conditional milestones.** The owner evaluates a `?` trigger at dispatch time.
  An absent trigger skips the milestone without dispatching it.
- **Resource isolation.** Each lease uses its own ports, database names, and
  caches. A milestone needing an exclusive resource serializes only its
  verification step, not its implementation.
- **Stopping a lease.** A lease is stopped, its worktree removed, and its branch
  deleted only after its work is integrated or the user directs otherwise. A
  finished lease is closed at once, so idle sub-agents never hold capacity.

## Rejected approaches

| Approach | Why it was rejected |
|---|---|
| Merge commits to integrate leases | They violate the authorized fast-forward integration and linear commit history |
| Declaring fewer impacts to unlock parallelism | Removes real reconciliation obligations; `GOAL.md` treats the impact map as a minimum |
| Transitive reduction of the impact list | Skips direct reconciliation of a consumer against the original producer |
| Worktrees inside the project | Dirty worktree, test-discovery leakage, accumulated generated folders |
| Reconciling from a free-text completion summary | `GOAL.md` requires reconciling against the implementation that now exists |
| Reviewing only in isolation, then again after integration | Two gates with no single counter owner; the isolated pass never saw the integrated code |
| Inferring write sets from task rows | Task rows do not list paths reliably; write sets must be declared |
| An environment variable for concurrency | A goal-input field keeps authority in the request that starts the run |

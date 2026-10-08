# Sub-Agent Milestone Execution

This guide defines the sub-agent execution architecture for multi-milestone
workflows under [`tabilet/GOAL.md`](goal.md). It establishes how to accelerate
milestone delivery through fresh-context task execution and parallel read-only
fan-out (Tier 0), as well as opt-in concurrent worktree leases (Tier 1), while
strictly preserving milestone quality, verification rigor, and the
single-ledger execution owner invariant.

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
  `tech-stack.md`, `lessons.md`, and `milestone.md` are written only by the
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

   STATUS_ORDER: M01 -> A01 -> S01 -> P01
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
3. `COMMIT_POLICY` is `task` or `milestone`. Under `none` there are no commits to
   carry work between worktrees, so Tier 1 is disabled.
4. Every milestone dispatched concurrently is `Parallel-safe: yes` and passes
   the three conditions in Part A against every other running lease.

### Lease lifecycle

```text
Owner: dispatch ready, parallel-safe milestone
  │
  ▼
Create branch goal/ID and worktree at ../<repo>.goal/<ID>
  │
  ▼
Lease: implement rows, one [~] at a time, commit per row
  │
  ▼
Lease: verify with lease-isolated resources
  │
  ▼
Lease: rebase onto current main line and re-verify
  │
  ▼
Lease: run authoritative review-fix gate on rebased diff
  │
  ▼
Has main moved since that rebase?
  ├── No  ───► Owner: fast-forward merge (git merge --ff-only)
  ├── Yes (disjoint) ───► Lease: rebase + re-verify only ───► fast-forward
  └── Yes (touches write set/contracts) ───► Lease: rebase + re-verify + re-review
  │
  ▼
Owner: integration check, reconcile impacts, update memory docs, retire
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
  file shows its progress and review counter. Resuming means listing both and
  continuing each lease from its status file. No new file is created.
- **One authoritative review.** The bounded review-fix gate runs once, in the
  lease, on the diff after rebasing onto the current main line, with its counter
  in the lease's status notes. When other work lands before integration, the
  lease rebases and re-verifies; the review is repeated only when the newly
  landed commits touch the lease's write set or contracts read.
- **Linear integration.** Rebase plus fast-forward keeps history linear and
  preserves one commit per status row. Never create merge commits (`--no-ff`).
- **Reconciliation from code.** After integration, the owner reconciles every
  downstream impact against the integrated implementation, not against the
  lease's report alone.
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
| Merge commits to integrate leases | `GOAL.md` forbids merging unless the request authorizes it, and merge commits break one commit per status row |
| Declaring fewer impacts to unlock parallelism | Removes real reconciliation obligations; `GOAL.md` treats the impact map as a minimum |
| Transitive reduction of the impact list | Skips direct reconciliation of a consumer against the original producer |
| Worktrees inside the project | Dirty worktree, test-discovery leakage, accumulated generated folders |
| Reconciling from a free-text completion summary | `GOAL.md` requires reconciling against the implementation that now exists |
| Reviewing only in isolation, then again after integration | Two gates with no single counter owner; the isolated pass never saw the integrated code |
| Inferring write sets from task rows | Task rows do not list paths reliably; write sets must be declared |
| An environment variable for concurrency | A goal-input field keeps authority in the request that starts the run |

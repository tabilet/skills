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

The owner passes only the context required for the target milestone:

- The target milestone section from `tabilet/memory-bank/milestone.md`.
- The target `tabilet/memory-bank/status-<ID>.md`.
- `AGENTS.md` read order, essential commands, and hard rules.
- Reconciled contracts, schemas, and interfaces delivered by predecessor
  milestones.
- The concrete verification commands required for acceptance.

The sub-agent may inspect any other source files in the project as needed.

### Milestone Execution

The sub-agent performs the standard milestone loop:
1. Implements task units row-by-row, keeping at most one `[~]` row in progress.
2. Runs required verification commands.
3. Executes the bounded review-fix gate (iterations 1–10), recording each pass
   and its findings in the milestone status notes.
4. Commits each completed task under `COMMIT_POLICY`.

### Return & Consolidation

When all tasks and review gates close, the sub-agent terminates and returns a
report:
- Completed task units and commit hashes.
- Verification and deep-review results, including total iteration count.
- Proposed updates to shared memory files (`architecture.md`, `product.md`,
  `tech-stack.md`, `lessons.md`).
- Discovered downstream notes or contract changes.

The owner resumes active ownership, reviews the actual code diff, performs
downstream reconciliation against consumer specifications, applies shared-memory
updates, and retires the milestone under project conventions.

### Resumption on Interruption

If a sub-agent terminates early (such as due to a timeout or server restart),
its status file and Git commits remain the durable resume point. The next
invocation reads the stored status rows and persisted review counter, resuming
the incomplete iteration without resetting to 1.

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

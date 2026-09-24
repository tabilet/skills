---
name: memory-bank-init
description: Initialize a memory bank through project discovery and an approved milestone plan. Use when no milestone/status harness exists, including after a completed archive preflight.
disable-model-invocation: false
argument-hint: (no arguments)
---

# Initialize A Memory Bank

Before reading project state for this workflow, inspect the root layout. If
`GOAL.md`, `memory-bank/`, `evolution/`, `docs/history/`, or
`docs/archive-<LANE><NN>.md` exists in a v1.5.0 or mixed layout, stop before
project writes or execution. Direct the user to preview and explicitly apply
`skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`.
Installing v2 never migrates a project automatically.

For explicitly enabled interactive auditing (`TABILET_AUDIT_DB`), read the bundled
`references/optional-audit.md` and use the optional installed `tabilet-audit`
toolkit. Report unavailable logging as a gap without changing workflow approvals
or outcomes. Inside the API runner, its recorder owns the lifecycle; do not start
a duplicate audit run.

Three phases: **grill**, **propose**, **write**. Write no file until phase 3.

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

The output is a memory bank the user owns outright. It has no link back to
wherever this skill came from, and nothing will update it but them.

## Phase 1 - Grill

Map the project as a **design tree**: decisions branch into the decisions that
depend on them. Interview the user until every applicable branch is settled or
explicitly deferred.

### Gate broad existing packages

Start with applicable agent instructions, the README, source layout, and any
existing milestone or archive index. Use this cheap topology pass to identify
the selected boundary before extensive discovery or interviewing. New projects
and existing packages whose selected boundary can be evidenced reliably in one
initialization pass proceed normally.

For a large existing package, require `memory-bank-archive` first when the
selected boundary spans several stable product-domain or ownership contexts, or
when compressing its independent contracts, flows, and evidence into one pass
would omit a material context. Explain the observed topology that triggered the
gate and stop before interviewing or writing. Do not invent a numeric file or
line-count threshold, invoke the other skill automatically, or make archive
preflight mandatory for a small coherent package.

Evaluate the selected delivery boundary, not only the next requested feature.
Several independent stable contexts within that boundary trigger the gate even
when their current implementations are short. A shared test command or product
name does not merge independent ownership and contracts into one context.

A completed archive preflight may already have created
`tabilet/memory-bank/product.md` and `tabilet/memory-bank/architecture.md`; their presence alone
does not mean initialization is complete. Read the archive registry and every
linked `tabilet/docs/archive-<LANE><NN>.md` as commit-anchored evidence. Continue only
when every context in the selected boundary is `verified`. Any proposed,
partial, blocked, missing, or unresolved context stops initialization until the
archive is completed. Preserve verified archives: they are frozen baselines,
not current truth or executable work.

If a project already has an initialized `tabilet/memory-bank/milestone.md` and active
status files or an indexed retired history, do not reinitialize it. A project
whose milestones are all retired remains initialized. Reconcile and evolve
the existing memory bank instead; reserve IDs across active and retired files.

### Inspect before asking

Deepen inspection where the selected boundary needs evidence: manifests and CI
for build constraints, interfaces and schemas for contracts, tests for existing
behavior, and deployment files for operational assumptions. Reuse facts and
decisions already present in the conversation. Inventory destination files such
as `AGENTS.md`, `tabilet/GOAL.md`, `tabilet/evolution/`, current memory-bank files, and archives
so the proposal can identify each create, merge, preserve, or omit action.

Keep a working **evidence ledger** and work the **whole frontier** of the
**design tree**. Read [references/discovery.md](references/discovery.md) when
moving beyond the cheap topology gate. It carries the shared inspection,
question, and completion technique. Init still uses the coverage roots below
and asks for a structured discovery confirmation before proposing files.

### Grow the design tree

Use these as coverage roots, not a fixed sequence or ceiling:

- **Delivery boundary:** what this is, who owns and uses it, the outcome it
  produces, primary workflows, and real non-goals.
- **Domain model:** canonical domain and business terminology, plus the
  relationships, cardinality, lifecycles, and invariants between concepts.
- **Current and target state:** existing capabilities, known gaps, and what the
  next delivery outcome changes.
- **System shape:** layout, data flow, ownership boundaries, integrations,
  public contracts, and compatibility obligations.
- **Constraints:** chosen stack rules, runtime and operational assumptions,
  dependencies, hard rules, and risky-change procedures.
- **Evidence:** runnable build/test/lint/format commands, integration harnesses,
  model evals when applicable, and any named manual acceptance evidence.
- **Work graph:** feature areas, dependencies, downstream impacts, sequencing,
  and the boundary between active work and later direction.

Grow conditional branches when the project calls for them: persistent data and
migrations; authentication, security, privacy, or compliance; distributed
failure and observability; UI accessibility and visual review; model behavior,
evaluation, cost, and provider failure; deployment and rollback; multi-repo or
external-system authority; or public API and file-format compatibility.

One memory bank covers one coherent product, ownership, and verification
boundary. If the repository contains independent delivery units, ask the user
to select one. Treat the others as external dependencies or initialize them
separately; do not turn lanes into separate products merely because they share a
repository.

For a broad project, map the whole selected boundary breadth-first, then deepen
the branches needed to define the next reliable delivery outcome. Later
directions need a reason and a promotion trigger, not speculative task lists.

### Complete the grill

Do not defer a decision that defines scope, ownership, a public contract, or
acceptance. A narrower unknown may become blocked work only when it has a named
owner or source, missing input, impact, and unblock condition.

The grill is complete when the frontier is empty and the evidence ledger can
populate every applicable output section without guessing. Present a structured
confirmation covering the delivery boundary, users and workflows, domain model
and business invariants, non-goals, current and target state, architecture and
contracts, constraints, verification, active delivery outcome, later
directions, and any blockers. Do not proceed until the user confirms the shared
understanding.

*(Interview technique adapted from the `grilling` skill in
[mattpocock/skills](https://github.com/mattpocock/skills), MIT.)*

## Phase 2 - Propose

Read [references/write-contract.md](references/write-contract.md) completely
before presenting the file-action proposal, so the proposal uses the actual
generated file set and `tabilet/memory-bank/status-<LANE><NN>.md` paths (for example,
`tabilet/memory-bank/status-M01.md`). Reading the contract grants no writing authority.

Present the breakdown and file actions. **Write nothing to disk yet.**

Define the **active horizon** as the smallest dependency-closed sequence of
vertical milestones that reaches the next user-verifiable delivery outcome.
Assign permanent status IDs only inside that horizon.

Show:

1. The selected delivery boundary and next delivery outcome.
2. Lane letters and meanings earned by active work. Start with `M`; open a
   domain lane only when that long-lived domain has enough active work to drown
   out other work or needs its own review cadence. A different acceptance method
   alone does not earn a lane.
3. Every active milestone's goal, scope, acceptance evidence, dependencies,
   downstream impacts, and complete set of commit-sized rows.
4. The execution order and exact status-file map.
5. Later **candidate directions**, each unnumbered and carrying its reason for
   deferral and promotion trigger.
6. Every destination file action: create, merge, preserve, or omit.

When an archive preflight exists, include the seeded product and architecture
merge plus preservation of every verified archive in the file actions. Archive
IDs and lanes are independent from status IDs and lanes; never place an archive
in the active horizon or disposable goal input.
A matching archive and status lane/number is not an ID collision and does not
justify renaming an existing status ID.

Rules:

- A milestone is a narrow, complete, independently verifiable vertical slice.
- A row is one commit and fits in one fresh context window.
- Keep implementation, its tests, and corrections to current memory-bank facts
  it invalidates in the same row. Separate documentation rows cover additional
  reference work, not deferred corrections to current truth.
- Acceptance names real commands and any required manual or model-eval evidence;
  it never refers to an interview question number.
- Every indexed milestone gets one status file. A candidate direction gets no
  lane, ID, status file, or disposable launch entry.
- A promotion trigger causes a fresh approved proposal, not automatic scheduling.
  Allocate an ID only after the promoted breakdown is approved.

Ask the user, as a numbered frontier round, whether the boundary and delivery
outcome are right, whether milestone granularity and dependencies are right,
whether the horizon ends in the right place, whether candidates should move in
or out, and whether every file action is safe. Iterate until approved.

## Phase 3 - Write

Only after the complete proposal is approved, follow the already-read
[write contract](references/write-contract.md) to write.
It owns the file actions, generated file set, portable
`tabilet/GOAL.md` copy rule, status tables, disposable launch reference, output checks,
and final handoff.
Continue through those checks and handoff; ask again only for conflicts or file
actions outside the approved proposal.

---
name: memory-bank-init
description: Map one delivery boundary through an adaptive, repository-grounded interview, propose a dependency-closed active milestone horizon, then generate its memory bank and, when a compatible goal protocol is available, a disposable launch reference. Use when a new or existing project has no memory-bank/ yet.
disable-model-invocation: false
argument-hint: (no arguments)
---

# Initialize A Memory Bank

Three phases: **grill**, **propose**, **write**. Write no file until phase 3.

The output is a memory bank the user owns outright. It has no link back to
wherever this skill came from, and nothing will update it but them.

## Phase 1 - Grill

Map the project as a **design tree**: decisions branch into the decisions that
depend on them. Interview the user until every applicable branch is settled or
explicitly deferred.

### Inspect before asking

For an existing project, read applicable agent instructions, the README and
docs, manifests, tests, build and CI configuration, source layout, public
interfaces and schemas, and deployment or infrastructure files. Reuse facts and
decisions already present in the conversation. Inventory existing destination
files such as `AGENTS.md`, `GOAL.md`, and `evolution/` so the proposal can say
which will be created, merged, preserved, or omitted.

Keep a working **evidence ledger** in the conversation:

- **Observed fact** - cite the repository path or prior user statement.
- **User decision** - record the choice and its reason.
- **Open decision** - record who can answer it and what depends on it.
- **Inapplicable branch** - record why it does not apply; do not invent filler.

Facts are your job; decisions are the user's. Investigate independent facts in
parallel when the environment supports it. A fact still being researched blocks
only the questions that depend on it.

### Work the frontier in rounds

The **frontier** is every open decision whose prerequisites are settled. Ask the
whole frontier in one numbered round, give a recommended answer for every
question, then wait. No question in a round may depend on another answer in that
round. Recompute the design tree and its frontier after every response.

Use this shape so the user can answer by number:

```text
❓ Q1 - <short title>: <question and meaningful choices>

➡️ <recommended answer and the project evidence or tradeoff behind it>
```

Honor a request for one-question-at-a-time pacing. Do not impose a fixed number
of questions or stop merely because the seed coverage below has been mentioned.

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

Rules:

- A milestone is a narrow, complete, independently verifiable vertical slice.
- A row is one commit and fits in one fresh context window.
- Acceptance names real commands and any required manual or model-eval evidence;
  it never refers to an interview question number.
- Every indexed milestone gets one status file. A candidate direction gets no
  lane, ID, status file, or disposable launch entry.
- A promotion trigger causes fresh reconciliation, not automatic scheduling.
  Allocate an ID only after the promoted breakdown is approved.

Ask the user, as a numbered frontier round, whether the boundary and delivery
outcome are right, whether milestone granularity and dependencies are right,
whether the horizon ends in the right place, whether candidates should move in
or out, and whether every file action is safe. Iterate until approved.

## Phase 3 - Write

Only after approval, read [references/write-contract.md](references/write-contract.md)
completely and follow it. It owns the file actions, generated file set, portable
`GOAL.md` copy rule, status tables, disposable launch reference, output checks,
and final handoff.

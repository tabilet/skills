---
name: memory-bank-archive
description: Create frozen context snapshots for a broad existing package, or successor snapshots for materially changed contexts. Use for archive preflight or refreshing context baselines.
disable-model-invocation: false
argument-hint: (no arguments)
---

# Archive A Large Existing Package

Before reading project state for this workflow, inspect the root layout. If
`GOAL.md`, `memory-bank/`, `evolution/`, `docs/history/`, or
`docs/archive-<LANE><NN>.md` exists in a v1.5.0 or mixed layout, stop before
project writes or execution. Direct the user to preview and explicitly apply
`skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`.
Installing v2 never migrates a project automatically.

Map one coherent product, ownership, and verification boundary breadth-first.
Produce repository facts, not a roadmap: archive files never contain executable
task state and never enter a status or goal order.

Three phases: **survey**, **propose**, **write**. Write no file until phase 3.

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

## Phase 1 - Survey

Read applicable agent instructions, README and long-form docs, manifests, build
and CI configuration, package boundaries, source entry points, public interfaces
and schemas, tests, deployment and infrastructure files, and any existing memory
bank or archive index. Reuse facts already established in the conversation.

Select one coherent product boundary. When a repository contains independent
delivery units, ask the user which one to archive and treat the others as
external contexts or archive them separately.

### Fix the baseline

When the package is in Git, resolve its worktree root and full `HEAD` commit.
Require a clean worktree, including untracked files, before starting. Never
commit, stash, discard, or absorb existing changes to make it clean. When the
package is not in Git, say that the result will be an `unversioned` snapshot and
continue only after the user accepts that weaker provenance.

A partial archive run may be resumed only when `HEAD` still equals its recorded
baseline and every worktree change is a declared output of that archive run:
`tabilet/docs/archive-<LANE><NN>.md`, `tabilet/memory-bank/product.md`, or
`tabilet/memory-bank/architecture.md`, and approved additions to
`tabilet/docs/history/knowledge.md` and its index link. Stop on any source change or
unrelated file.

### Build the context map

Partition the selected boundary by stable product domain or ownership context,
not by feature, sprint, review finding, team name, document type, or source
directory. Map every context breadth-first, then deepen only the branches needed
to establish applicable high-level facts.

Archive lanes are independent from status lanes. Use `M` for a cross-cutting or
unclassified context. Open another single-letter lane only for a durable context,
choose an unused mnemonic letter, and record its meaning in
`tabilet/memory-bank/architecture.md`. A lane has its own chronological archive sequence
from `01` through `99`.

For each context, collect evidence for:

- purpose, responsibilities, ownership, and exclusions;
- domain concepts, workflows, relationships, and invariants;
- components, entry points, and data or control flow;
- public contracts, integrations, dependencies, and consumers;
- applicable persistence, security/privacy, failure, operational, deployment,
  and verification behavior; and
- gaps, conflicts, or unavailable evidence.

Keep an evidence ledger in the conversation. Every factual claim names a
repository path or prior user statement. Do not turn an observed gap into a milestone,
candidate direction, status row, or implementation recommendation.
Distinguish implemented behavior, documented ownership rules, and planned
behavior. A next-delivery description belongs in observed gaps until the
implementation establishes it; do not report it as a current product invariant.

Coverage is `partial`, `blocked`, or `verified`. `verified` means every
applicable branch was inspected and its claims have evidence; it does not mean
the implementation is correct. Name the missing source and impact for blocked
coverage. Do not silently omit a context.

## Phase 2 - Propose

Read [references/write-contract.md](references/write-contract.md) before preparing
the proposal. It defines the output formats, allowed file actions, and checks.
Reading it does not authorize writes.

Present, without writing:

1. The selected boundary and baseline commit, or `unversioned` provenance.
2. Every archive lane and its context meaning.
3. Every context's scope, coverage, evidence roots, and proposed archive path.
4. Existing archives that remain current, and materially changed contexts that
   need the next unused successor ID.
5. The facts to create or refresh in `tabilet/memory-bank/product.md` and
   `tabilet/memory-bank/architecture.md`.
6. Every file action: create, merge, preserve, or omit.

When refreshing existing summaries, include preservation of materially
superseded knowledge in the proposal. Keep the previous source/heading, literal
wording, reason, evidence, and replacement reference in the knowledge history;
this does not authorize retiring or modifying milestone/task records.

An archive successor is justified only by a material change to high-level
domain, ownership, component, flow, contract, dependency, operational, or
verification facts. File moves and internal refactors that leave those facts
unchanged do not create a successor.

A closed milestone may motivate this review of context facts, but ordinary
milestone consolidation and retirement never require an archive invocation.
Keep the clean-baseline and approval requirements for actual context snapshots.

Ask the user to approve the boundary, context partition, lane meanings,
coverage, successor decisions, roll-up, and file actions. Iterate until all are
approved.

## Phase 3 - Write

Apply the approved actions using the already-read write contract. Continue
through its output checks and handoff. Ask again only when a conflict or file
action falls outside the approved proposal.

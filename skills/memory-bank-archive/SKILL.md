---
name: memory-bank-archive
description: Snapshot a large existing package at a clean repository baseline into frozen, evidence-backed context archives, then create or refresh its current product and architecture summaries. Use before memory-bank-init when a broad existing package needs a repository-mapping preflight, or later when materially changed contexts need successor archives. Do not use it to plan or execute status work.
disable-model-invocation: false
argument-hint: (no arguments)
---

# Archive A Large Existing Package

Map one coherent product, ownership, and verification boundary breadth-first.
Produce repository facts, not a roadmap: archive files never contain executable
task state and never enter a status or goal order.

Three phases: **survey**, **propose**, **write**. Write no file until phase 3.

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
`docs/archive-<LANE><NN>.md`, `memory-bank/product.md`, or
`memory-bank/architecture.md`. Stop on any source change or unrelated file.

### Build the context map

Partition the selected boundary by stable product domain or ownership context,
not by feature, sprint, review finding, team name, document type, or source
directory. Map every context breadth-first, then deepen only the branches needed
to establish applicable high-level facts.

Archive lanes are independent from status lanes. Use `M` for a cross-cutting or
unclassified context. Open another single-letter lane only for a durable context,
choose an unused mnemonic letter, and record its meaning in
`memory-bank/architecture.md`. A lane has its own chronological archive sequence
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

Coverage is `partial`, `blocked`, or `verified`. `verified` means every
applicable branch was inspected and its claims have evidence; it does not mean
the implementation is correct. Name the missing source and impact for blocked
coverage. Do not silently omit a context.

## Phase 2 - Propose

Present, without writing:

1. The selected boundary and baseline commit, or `unversioned` provenance.
2. Every archive lane and its context meaning.
3. Every context's scope, coverage, evidence roots, and proposed archive path.
4. Existing archives that remain current, and materially changed contexts that
   need the next unused successor ID.
5. The facts to create or refresh in `memory-bank/product.md` and
   `memory-bank/architecture.md`.
6. Every file action: create, merge, preserve, or omit.

An archive successor is justified only by a material change to high-level
domain, ownership, component, flow, contract, dependency, operational, or
verification facts. File moves and internal refactors that leave those facts
unchanged do not create a successor.

Ask the user to approve the boundary, context partition, lane meanings,
coverage, successor decisions, roll-up, and file actions. Iterate until all are
approved.

## Phase 3 - Write

After approval, read [references/write-contract.md](references/write-contract.md)
completely and follow it. It owns archive naming and freezing, document shape,
current-summary roll-up, output checks, and handoff.

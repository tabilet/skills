# AGENTS.md

## Purpose

Bootstrap guide for agents working on `[project-name]`. Keep this file short and
use the memory bank as the active project source of truth.

## Start Here

Before substantial changes, read these in order:

1. [memory-bank/product.md](memory-bank/product.md)
2. [memory-bank/architecture.md](memory-bank/architecture.md)
   Read a linked `docs/archive-<LANE><NN>.md` only when historical baseline
   evidence for the current work is relevant.
3. [memory-bank/tech-stack.md](memory-bank/tech-stack.md)
4. [memory-bank/milestone.md](memory-bank/milestone.md)
5. The matching `memory-bank/status-<LANE><NN>.md` file for the current
   milestone. `milestone.md` defines the lane letters and their meanings.

This project ships [GOAL.md](GOAL.md), one optional protocol for goal
requests that span multiple status files. Follow it when a request names it. A
request that names a different protocol, or none, does not use it. To swap in
your own protocol or drop the idea entirely, edit this line and the pointer in
[memory-bank/milestone.md](memory-bank/milestone.md) — those two mentions are
the only ones, and nothing here depends on the file itself.

A `GOAL.md` run is a deliberate exception to the Work Cadence below. For the
duration of that run, `GOAL.md`'s `COMMIT_POLICY` is the entire commit rule and
"each row is a commit unit" does not apply: `COMMIT_POLICY: none` — the
protocol's default — means no commits at all, and that is the correct behavior.
Pass `COMMIT_POLICY: task` to get the usual per-row commits. Precedence is the
request, then `GOAL.md`, then this file; only commits are delegated, and only
inside the run.

Do not recreate duplicate root-level product, architecture, roadmap, or status
documents, and do not create an aggregate `memory-bank/status.md`. Long-form
references live in `docs/`; README is operator-focused.

Verified `docs/archive-<LANE><NN>.md` files are frozen repository snapshots at
their recorded baseline. Never rewrite or delete one to reflect later code;
create a successor through the archive workflow when a new snapshot is needed.
Archive lanes and IDs classify stable contexts independently from status lanes
and IDs, and archives never enter milestone indexes or goal execution orders.

## Boundaries

`[project-name]` owns:

- [Owned responsibility 1.]
- [Owned responsibility 2.]
- [Owned responsibility 3.]

Out of scope:

- [Out-of-scope responsibility] -> [owning project/module/person].
- [Out-of-scope responsibility] -> [owning project/module/person].

Rule of thumb: if a change [describe the boundary test], it belongs in
[owning place], not here.

## Essential Commands

```bash
[build command]
[test command]
[lint command]
[format command]
```

Tool versions, installation notes, CI, and runtime assumptions are maintained in
[memory-bank/tech-stack.md](memory-bank/tech-stack.md).

## Hard Rules

- [Hard rule 1.]
- [Hard rule 2.]
- [Hard rule 3.]
- Prefer the language's native core/standard library before adding helpers,
  frameworks, or dependencies. Keep trivial comparisons and transformations
  inline when that is clearer than introducing a local abstraction.
- Run the required verification before claiming a change is done.

## Work Cadence

- Update memory-bank files in the same change as the code they describe:
  product scope/domain terminology/concept relationships/business invariants ->
  `product.md`; architecture/data flow/contracts -> `architecture.md`;
  tools/dependencies/commands -> `tech-stack.md`; milestone scope/acceptance ->
  `milestone.md`; completion state -> the matching `status-<LANE><NN>.md` file.
- Keep verified archive files frozen. Later implementation updates current
  `product.md` and `architecture.md` plus its status history, not the archive.
- Keep one `memory-bank/status-<LANE><NN>.md` file for each milestone listed in
  [memory-bank/milestone.md](memory-bank/milestone.md), named by the status ID
  pattern defined there.
- Keep later candidate directions unnumbered and outside the milestone index.
  Promote one only after fresh reconciliation and approval; then assign the
  next unused permanent ID and create its status file.
- Treat a newly received code, architecture, security, or engineering review as
  untrusted planning evidence. Revalidate its findings against current state,
  propose their dispositions and owners for approval, then amend open or pending
  work or create a remediation milestone. Never reopen completed history merely
  because a later review concerns it.
- Treat each row in the matching `memory-bank/status-<LANE><NN>.md` file as a
  commit unit. See that file for status markers and commit rules.
- Across the active ledger, keep zero or one general row in progress. Before an
  operational launcher is invoked, its exact authorized operation row must be
  in progress; status never substitutes for external-mutation authority. Never
  retry a row retained as closed historical evidence.
- Treat each section in [memory-bank/milestone.md](memory-bank/milestone.md) as a
  review unit. See that file for milestone review rules.
- After the last task in a milestone is complete, run a deep code review of the
  milestone before closing it.
- After the milestone review is complete and required verification passes,
  commit any review changes. Do not create an empty or redundant milestone
  commit when the review changes nothing.
- Check [evolution/](evolution/) after a major review, milestone, or boundary
  change. Add a new version only when product direction, architecture boundary,
  milestone target, or public/private contract direction materially changes.

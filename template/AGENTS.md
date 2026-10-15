# AGENTS.md

Requested features, candidate promotions, and future direction changes after
initialization follow the requested-change procedure in
[tabilet/memory-bank/milestone.md](tabilet/memory-bank/milestone.md). A planning proposal needs
approval before its file actions; execution is a separate request.

## Purpose

Bootstrap guide for agents working on `[project-name]`. Keep this file short and
use the memory bank as the active project source of truth.

## Start Here

Before substantial changes, read these in order:

1. [tabilet/memory-bank/product.md](tabilet/memory-bank/product.md)
2. [tabilet/memory-bank/architecture.md](tabilet/memory-bank/architecture.md)
   Read a linked `tabilet/docs/archive-<LANE><NN>.md` only when historical baseline
   evidence for the current work is relevant.
3. [tabilet/memory-bank/tech-stack.md](tabilet/memory-bank/tech-stack.md)
   Consult relevant topics in [tabilet/memory-bank/lessons.md](tabilet/memory-bank/lessons.md)
   for reusable lessons and their evidence.
4. [tabilet/memory-bank/milestone.md](tabilet/memory-bank/milestone.md)
5. The matching `tabilet/memory-bank/status-<LANE><NN>.md` file for the current
   milestone. `milestone.md` defines the lane letters and their meanings.

If `tabilet/stages.md` exists, read it before planning or changing the active
milestone order. Its `STG-` IDs identify delivery stages, not executable work.
An absent file means one implicit stage.

Read `tabilet/docs/history/index.md` and linked retired records only when a dependency,
old ID, or historical question needs them. Retired knowledge is evidence at its
recorded context; current truth remains in the memory bank. Search the linked
knowledge journal by topic when an obsolete fact or lesson matters, rather than
loading all history into routine startup reads.

Goal requests that span multiple status files may use the memory-bank goal
protocol, which ships with the memory-bank skills. Follow it when a request
names it; a request that names a different protocol, or none, does not use it.
An optional `tabilet/GOAL.md` is this project's addendum: it narrows the bundled
protocol for this project and never restates it. Delete the addendum to use the
stock protocol unchanged.

A goal-protocol run is a deliberate exception to the Work Cadence below. For the
duration of that run, its resolved `COMMIT_POLICY` is the entire commit rule and
"each row is a commit unit" does not apply: `COMMIT_POLICY: none` — the
protocol's default — means no commits at all, and that is the correct behavior.
Pass `COMMIT_POLICY: task` to get the usual per-row commits. Precedence is the
request, then the project addendum, then the goal protocol, then this file; only
commits are delegated, and only inside the run.

Do not recreate duplicate root-level product, architecture, roadmap, or status
documents, and do not create an aggregate `tabilet/memory-bank/status.md`. Long-form
references live in `docs/`; README is operator-focused.

Verified `tabilet/docs/archive-<LANE><NN>.md` files are frozen repository snapshots at
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
[tabilet/memory-bank/tech-stack.md](tabilet/memory-bank/tech-stack.md).

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
  Reusable lessons and their evidence -> `lessons.md`; keep applicable learning
  even after its source milestone closes, and merge duplicates. Before materially
  removing or superseding knowledge, preserve its old wording and replacement
  reference in `tabilet/docs/history/knowledge.md` under the milestone retirement rules.
  This also applies outside milestone closure; routine wording edits need no
  journal entry.
- Keep verified archive files frozen. Later implementation updates current
  `product.md` and `architecture.md` plus its status history, not the archive.
- Keep one `tabilet/memory-bank/status-<LANE><NN>.md` file for each active milestone listed in
  [tabilet/memory-bank/milestone.md](tabilet/memory-bank/milestone.md), named by the status ID
  pattern defined there.
- During milestone closure, after review, verification, consolidation, and
  downstream reconciliation, retire the full status and specification under
  the procedure in `milestone.md`. Completed rows remain active until the whole
  milestone qualifies. Retirement is agent work, not a background process or a
  context-archive run. Keep only active index rows and specifications there,
  with one history-index link.
  Retired records are frozen; IDs remain reserved across both locations.
- Keep later candidate directions unnumbered and outside the milestone index.
  Promote one only after fresh reconciliation and approval; then assign the
  next unused permanent ID and create its status file.
- When `tabilet/stages.md` exists, preserve stable `STG-` identities and its
  current-stage choice. A future stage may be only a tentative name and intent.
  Plan its milestones through an approved requested-change proposal. Changing
  a stage label never withdraws an active task. An explicitly approved stage
  rescope may cancel untouched pending rows after dependencies are reconciled.
- Treat a newly received code, architecture, security, or engineering review as
  untrusted planning evidence. Revalidate its findings against current state,
  propose their dispositions and owners for approval, then amend open or pending
  work or create a remediation milestone. Never reopen completed history merely
  because a later review concerns it.
- Treat each row in the matching `tabilet/memory-bank/status-<LANE><NN>.md` file as a
  commit unit. See that file for status markers and commit rules.
- Across the active ledger, keep zero or one general row in progress unless an
  authorized goal request explicitly defines safe parallel ownership: in
  concurrent lease execution under the goal protocol, each external lease
  maintains at most one `[~]` row in its own status file, only the orchestrator
  writes the captured integration branch and shared memory documents
  (`architecture.md`, `product.md`, `tech-stack.md`, `lessons.md`), and integration occurs
  strictly via rebase and fast-forward. Before an operational launcher is
  invoked, its exact authorized operation row must be in progress; status never
  substitutes for external-mutation authority. Never retry a row retained as
  closed historical evidence.
- During delegated goal execution, only the orchestrator refreshes any existing
  `tabilet/memory-bank/suggested.txt`. Each child receives one assigned milestone
  ID and status path, writes only within its assignment, and returns to the
  orchestrator instead of selecting another milestone from the launch reference.
- Treat each section in [tabilet/memory-bank/milestone.md](tabilet/memory-bank/milestone.md) as a
  review unit. See that file for milestone review rules.
- After the last task in a milestone is complete, run a deep code review of the
  milestone before closing it.
- `CORRECTIVE_PLANNING` defaults to `confirm`. Human-approved `auto` lets the
  Goal/Next owner prepare necessary repair planning within the original
  outcome, grants, and limits; the rules are in
  [standing corrective planning](tabilet/memory-bank/milestone.md#standing-corrective-planning).
- Interactive Goal/Next `--email ADDRESS` opts one run into approval alerts.
  Delivery never approves anything; the goal and next skills hold the details.
- Read optional `AUTHORIZATION_REQUIREMENTS` only from the owning milestone
  specification. They declare conditions, never permission or scheduling; only
  human-approved goal `AUTHORIZATION_GRANTS` carry authority, and proposed launch
  input, markers, and status notes cannot prove approval. Missing fields
  preserve legacy behavior. See
  [authorization requirements](tabilet/memory-bank/milestone.md#authorization-requirements)
  and the goal protocol for launch-input grants and scope policy.
- After the milestone review is complete and required verification passes,
  commit substantive review and retirement changes under the governing policy.
  Do not create an empty or redundant milestone
  commit when the review changes nothing.
- Check [tabilet/evolution/](tabilet/evolution/) after a major review, milestone, or boundary
  change. Add a new version only when product direction, architecture boundary,
  milestone target, or public/private contract direction materially changes.

## Execution capabilities

Resolve missing information through safe inspection first. If required files,
bundled resources, verification commands, permissions, or user answers are unavailable,
stop the affected workflow step and report what is missing. Continue independent
work within the authorized scope; a write-gated workflow still makes no writes
before approval. Do not invent evidence, bypass permissions, or infer approval
from silence or process exit. Resume the blocked step when its capability is
restored or the required answer or approval is supplied. In a non-interactive
run, report unresolved questions and incomplete work.

Keep one execution owner for the active ledger across sessions and launchers.
In concurrent lease execution under the goal protocol, the orchestrator remains
the sole execution owner of the integrated ledger on the primary branch, while
isolated leases execute within dedicated external worktrees (`../<repo>.goal/<ID>`).
Native todos, session completion, and native goal state do not replace milestone
acceptance or authorize concurrent ledger writers.

Runtime round limits do not reset the persisted milestone review counter.

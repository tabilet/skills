# Archive Write Contract

Read this reference only after the user approves the archive proposal.

## Apply safe file actions

Follow the approved create, merge, preserve, and omit action for every file.
Never silently overwrite an existing file.

- Create `docs/` or `memory-bank/` only when needed.
- Preserve existing applicable content in `memory-bank/product.md` and
  `memory-bank/architecture.md`; merge observed current facts rather than
  replacing user decisions or project rules.
- Treat a verified archive as frozen. Never edit or delete it, even to correct a
  mistake. Write a successor and explain the correction there.
- A `partial` or `blocked` archive is an in-progress artifact and may be resumed
  only at the same recorded baseline under the resume rules in the parent
  skill. It freezes when its coverage becomes `verified`.
- Do not create or modify `GOAL.md`, `memory-bank/tech-stack.md`,
  `memory-bank/milestone.md`, any `memory-bank/status-*.md`,
  `memory-bank/suggested.txt`, or `evolution/`.
- Stop and ask before any collision or merge not covered by the approved
  proposal.

## Allocate archive IDs

Archive files are `docs/archive-<LANE><NN>.md`, where `<LANE>` is one uppercase
letter and `<NN>` is a zero-padded number from `01` through `99`.

- Archive lanes classify stable product-domain or ownership contexts. They are
  a separate namespace from status lanes and may use different meanings.
- `M` is the default for a cross-cutting or otherwise unclassified context.
- Record every archive lane meaning in `memory-bank/architecture.md` before
  using it.
- Within a lane, allocate the next unused number. Numbers record snapshot chronology,
  not priority or execution order.
- Never reuse or rename an archive ID. If a lane reaches `99`, obtain approval
  for an unused continuation letter and record the relationship.
- A first snapshot has `Supersedes: none`. A successor names the latest verified
  predecessor. A split or merge may name multiple predecessors and must explain
  the new context boundaries.

## Write context archives

Use this shape, with only applicable sections and project values:

```markdown
# Archive C01 - <context title>

**Context.** <stable product-domain or ownership boundary>

**Baseline.** <full Git commit, or `unversioned`>

**Coverage.** verified

**Supersedes.** none

## Scope And Responsibilities

<What this context owns and excludes.>

## Domain And Workflows

<Concepts, relationships, invariants, and primary workflows.>

## System Shape

<Components, entry points, and data or control flow.>

## Contracts And Dependencies

<Interfaces, integrations, dependencies, and consumers.>

## Operations And Verification

<Applicable persistence, security, failure, deployment, and verification facts.>

## Evidence

| Claim | Repository Evidence |
|---|---|
| <Current high-level fact.> | `<path>` |

## Observed Gaps

<Evidence conflicts or unavailable facts, without tasks or recommendations.>
```

Remove sections that do not apply instead of writing `N/A`. Do not leave
bracketed placeholders. Use repository-relative evidence paths and explain the
fact each path supports; a source inventory without synthesis is not an archive.

Do not use status-marker tables or describe archive sections as tasks,
milestones, priorities, or an execution order. The archive is finer-grained than
the whole-project product and architecture summaries but coarser than executable
status work.

## Refresh current summaries

Create or merge current observed facts into:

- `memory-bank/product.md`: product scope, users and workflows when evidenced,
  canonical domain terminology, concept relationships, business invariants, and
  non-goals that the repository establishes; and
- `memory-bank/architecture.md`: current layout, ownership, data flow, public
  contracts, dependencies, and an archive registry.

Keep `product.md` and `architecture.md` current after the archive is frozen.
Later code work updates those files and its matching status history, never the
verified archive.

Use this archive registry shape in `architecture.md`:

```markdown
## Archive Baselines

Archive files are frozen repository snapshots. Current product and system truth
lives in this memory bank; use each archive only at its recorded baseline.

| Archive Lane | Context |
|---|---|
| C | <context meaning> |

| Archive | Context | Baseline | Coverage | Supersedes |
|---|---|---|---|---|
| [C01](../docs/archive-C01.md) | <context> | `<full commit>` | verified | none |
```

List every proposed, partial, blocked, and verified context during an active
archive run. Initialization may proceed only when every context in the selected
boundary is `verified`. On a later run, add a successor row only for a materially
changed context; leave unchanged context archives untouched.

Do not copy detailed archive prose into the two summaries. Synthesize the
current cross-context truth and link to the finer baseline evidence.

## Check the output

Before reporting completion, verify:

1. Every archive filename matches `archive-[A-Z][0-9][0-9].md` and lives in
   `docs/`.
2. Every archive ID is unique, its lane meaning is registered, and its number
   was never reused.
3. Every Git-backed archive records the same full baseline commit that was
   inspected; an unversioned package says `unversioned` explicitly.
4. Every applicable context appears in the architecture registry and has an
   archive with honest coverage.
5. Every `verified` archive has synthesized evidence, contains no placeholder,
   and is left frozen thereafter.
6. Every successor names its predecessor and exists only for a material
   high-level change.
7. Archive and status namespaces are not paired or conflated.
8. `product.md` and `architecture.md` describe current observed facts and link
   archive baselines without presenting them as current truth.
9. No milestone, candidate direction, status row, goal order, commit, or
   external mutation was created without separate authorization.

## Hand off

Report the selected boundary and baseline; archive files created, preserved, or
superseded; context coverage; current summaries refreshed; and unresolved
evidence. State explicitly that archives are frozen factual baselines and that
planning impacts were reported but not scheduled.

When this was a required preflight for `memory-bank-init`, explain that init can
continue only after every context in the architecture registry is verified.

# Memory-Bank Write Contract

Read this reference during Phase 2, before proposing file actions. Apply its
writes only after the user approves the complete proposal.

## Contents

- [Apply safe file actions](#apply-safe-file-actions)
- [Write the project files](#write-the-project-files)
- [Handle the portable goal protocol](#handle-the-portable-goal-protocol)
- [Write the disposable launch reference](#write-the-disposable-launch-reference)
- [Write status tables](#write-status-tables)
- [Preserve long-term memory](#preserve-long-term-memory)
- [Check the output](#check-the-output)
- [Hand off](#hand-off)
- [Runtime capability contract](#runtime-capability-contract)

## Apply safe file actions

Follow the approved create, merge, preserve, and omit decision for every
destination. Never silently overwrite an existing file.

- Merge the memory-bank read order, essential commands, boundaries, hard rules,
  and work cadence into an existing `AGENTS.md` while preserving its applicable
  project instructions and removing only approved duplication.
- When `GOAL.md` is absent, use the bundled copy rule below. When it is already
  byte-identical, preserve it. When it differs, preserve the existing file
  unless the user approved replacing it. Treat a differing protocol as
  compatible only when its documented interface accepts the launch fields and
  sequencing contract below and the user approved using it.
- Create `memory-bank/suggested.txt` only when the approved project will contain
  a compatible `GOAL.md`. Otherwise omit the launch reference and every optional
  `GOAL.md`-specific paragraph or pointer from generated `AGENTS.md` and
  `memory-bank/milestone.md`; do not generate a request that names a missing or
  incompatible protocol.
- When `evolution/` already contains numbered direction history, preserve it and
  use the next unused version for the approved initial memory-bank snapshot.
- When an approved archive preflight exists, merge its current observed facts
  from `memory-bank/product.md` and `memory-bank/architecture.md`. Preserve every
  verified `docs/archive-<LANE><NN>.md` byte-for-byte. Treat archive lanes and
  IDs as an independent namespace that never enters milestone indexes, status
  files, or goal launch input.
- Stop and ask before any collision whose safe merge was not approved.

## Write the project files

Create or merge the approved project-specific content for:

```text
AGENTS.md                        what an agent reads first
GOAL.md                          optional protocol for multi-milestone runs
memory-bank/product.md           product, users, workflows, domain model, non-goals
memory-bank/architecture.md      layout, data flow, ownership, public contracts
memory-bank/tech-stack.md        stack, dependencies, harnesses, commands
memory-bank/lessons.md           applicable reusable lessons and evidence
memory-bank/milestone.md         active index, acceptance, candidate directions
memory-bank/status-<LANE><NN>.md one per active milestone, one row per task
memory-bank/suggested.txt        optional; only with a compatible GOAL.md
evolution/prompt-v1.md           initial direction, or next unused version
evolution/result-v1.md           current state, or next unused version
```

Write only applicable sections. Remove optional template sections that do not
apply instead of inventing behavior or writing `N/A`. Never leave bracketed
placeholders.

Keep `AGENTS.md` short: what to read and in what order, essential commands,
boundaries, hard rules, and work cadence. Point at the memory bank rather than
restating it.

When verified archives exist, keep their registry in `architecture.md` and add
the archive lifecycle rule to `AGENTS.md`: archives are frozen evidence at their
recorded baseline, while current product and system truth stays in `product.md`
and `architecture.md`. Agents read a linked archive only when historical
baseline evidence is relevant and never update it with later code changes.

In `memory-bank/product.md`, write the canonical product and business
terminology as a domain model. For each material concept, capture its meaning
and the relationships or invariants that constrain it, including ownership,
parent/child structure, cardinality, lifecycle, and state transitions when they
matter. Keep technical storage and implementation details in `architecture.md`.
Do not create a parallel `context.md` or duplicate the domain model elsewhere.

In `memory-bank/milestone.md`:

- index exactly the approved active milestones and link each to its one status
  file;
- state their dependency order, acceptance, and downstream relationships; and
- place later work in an explicitly unnumbered `Candidate Directions` section
  with columns for direction, why it is deferred, and its promotion trigger.

Include the automatic closure, consolidation, retirement, and retrieval contract
below. Keep only active specifications and index rows in `milestone.md`; create
one link to the history index when history exists. Preserve permanent IDs across
active and retired records. Do not create empty history files during init.

Include a `Review finding severity` section in `milestone.md`. Explain that P1
and P2 are engineering review priorities rather than product-domain terms,
milestone execution priority, or status markers. Define their default context,
typical examples, and gate effect; let project-specific definitions in
`AGENTS.md` or a linked review policy override those defaults. Classification
must follow impact, likelihood, and affected scope rather than fix size.

Include a separate `New review intake` procedure for reviews received after the
harness exists. It must require current-state revalidation, preserve both source
and local severity, and obtain approval for dispositions and file actions before
writing. Confirmed work fits an open or pending owner when in scope; completed
history is never reopened, so later defects get a remediation milestone with
lineage. P1/P2-or-higher findings enter the dependency-closed active horizon;
optional lower findings stay in Candidate Directions. Record portable review
provenance in affected milestone/status notes without adding a review copy or
ledger. An intake review counts as a bounded-gate iteration only when it was
explicitly requested as the next pass of an already active persisted gate.

Include a milestone review procedure with a bounded review-fix gate. The
initial deep-review pass is iteration 1. After every P1, P2, or higher-severity
fix, rerun affected verification and review the whole milestone again. The gate
passes only when a review finds no such issue. Limit it to 10 iterations without
resetting across sessions or reviewers, and persist each iteration number in the
current status notes or equivalent active goal state. If iteration 10 still
finds a blocking issue, leave the milestone incomplete and record the findings
with the project's blocked-status mechanism.

Candidate directions are not milestones. Do not assign them lane letters or
status IDs, create status files for them, or include them in an execution order.
When a trigger becomes true, reconsider the candidate and obtain approval
before allocating the next unused permanent ID.

## Handle the portable goal protocol

The bundled `GOAL.md` is copied, never written from memory. It must stay
byte-identical across projects that carry that protocol. Resolve the directory
containing the parent `memory-bank-init/SKILL.md` and copy the sibling `GOAL.md`
shipped there. This location is common to plugin and plain-file installs. Do not
depend on provider-specific plugin-root environment variables.

If the project has no `GOAL.md` and the bundled file cannot be found, say so and
omit both `GOAL.md` and `memory-bank/suggested.txt` rather than writing an
approximation or a dead-end launch request. An existing approved compatible
protocol does not need the bundled file. The project works one row at a time
without either protocol, and `memory-bank-goal` can tell the user where to get
the bundled one.

Tell the user the protocol and launch reference are optional and can be deleted
together. They are one way to run several active milestones in order, not a
requirement of the memory bank.

## Write the disposable launch reference

When the approved project contains a compatible `GOAL.md`, derive
`memory-bank/suggested.txt` only from the approved active horizon. It is advisory
launch input, not project truth. Do not add it to `AGENTS.md`'s required read
order or the milestone index. Tell the user to delete it after launching the
goal or whenever it becomes stale. When no compatible protocol exists, omit
`memory-bank/suggested.txt` and report one-row execution as the available path.

Use this shape with project values, never the example values:

Use the commit policy approved for future execution. A no-commit restriction
during initialization does not prohibit commits in a later authorized run.
Creating launch input does not start that run. Preserve its explicit policy;
`GOAL.md` defines its precedence during execution, while the suggested order
remains disposable. Do not invent a standing policy conflict from an init-only
restriction.

```text
# Disposable multi-milestone launch reference.
# Reconcile this suggestion against milestone.md and the current status files.
# Delete it after launching the goal, or whenever it becomes stale.

Using GOAL.md, execute this loop.

STATUS_ORDER:
M01 -> M02

STATUS_FILE_MAP:
M01 = memory-bank/status-M01.md
M02 = memory-bank/status-M02.md

DOWNSTREAM_IMPACTS:
M01 -> M02

COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: every required status is complete, every triggered
conditional status is complete, and every milestone's documented verification
passes.
```

Map every active status in `STATUS_ORDER` to exactly one file. Include known
active downstream consumers; the goal loop will discover more. Use
`DOWNSTREAM_IMPACTS: none` when there are none.

A trailing `?` is allowed only for a conditionally required status inside the
active horizon. Document its concrete project-state trigger in
`memory-bank/milestone.md`, and include the suffix only when the approved next
delivery outcome requires that status if the trigger is true. Put discretionary
later work in Candidate Directions instead. Never put a candidate direction in
`suggested.txt`.

## Write status tables

Create one table for every active milestone. Use an initial `[!]` row only for
an approved non-fundamental blocker with a named owner or source, missing input,
impact, and unblock condition. All other unfinished rows start pending.
Do not precreate rows for hypothetical later failures, such as an exhausted
review gate. Record such a blocker only when it actually occurs.
Keep implementation, tests, and corrections to invalidated current memory-bank
facts in the same row; a later documentation row cannot defer those corrections.

The backticks around every marker are required by the API harness parser:

```markdown
# Status M01 - <milestone title>

**Acceptance.** <commands and other evidence, and what they must show>

| Item | State | Notes |
|---|---|---|
| <task> | `[ ]` | <constraint, edge case, or decision from the interview> |
```

Markers: `` `[ ]` `` pending, `` `[+]` `` completed, `` `[~]` `` in progress,
`` `[!]` `` blocked, `` `[X]` `` cancelled, and `` `[-]` `` closed historical
evidence. A `[-]` row is a consumed failed attempt or superseded row retained
for audit; it is never retried and does not block its accepted successor. Its
notes record the outcome and name that successor.

Across the active ledger, zero or one general row may be `[~]`. An operational
launcher additionally requires its exact authorized operation row to be `[~]`
before invocation; the marker records selection and does not grant missing
external-mutation authority.

## Preserve long-term memory

Create `memory-bank/lessons.md` as a curated reference of applicable lessons:
each names its scope, lesson, rationale, and source evidence. State explicitly
when no lessons are established. Do not invent lessons or repeat the domain
model, architecture contracts, or commands. The read order consults relevant
topics before substantial changes; it does not read the whole history on boot.

Generate these retirement rules in `memory-bank/milestone.md`:

- After the review gate passes within its persisted 10 iterations, verification
  passes, current facts/lessons are consolidated, and downstream work is
  reconciled, automatically retire the milestone. Terminal markers alone are
  insufficient; unresolved or conditional pending work stays active.
- Retain full final specifications and status documents, not summaries, in
  `docs/history/status-<LANE><NN>.md`. Preserve every earlier row and note. Use
  separate `## Milestone specification` and `## Status record` sections, each
  containing exactly one literal fenced `markdown` document. Choose fences
  longer than those inside the source, preserving original path context.
- Before those sections, put single-line fields in `**Field.** value` form:
  `Milestone` (ID), `Outcome` (`completed`, `cancelled`, or `superseded`),
  `Retired` (UTC YYYY-MM-DD), `Source status` (original memory-bank path),
  `Source specification` (original milestone path and heading anchor),
  `Evidence` (bare full Git commit or `unversioned`), `Worktree` (`clean`,
  `includes uncommitted changes`, or `unversioned`), `Review` (`passed`),
  `Review iterations` (1 through 10), `Verification` (commands/results/evidence),
  and `Consolidated into` (current-document/lesson links or explicit
  `no current-truth change`). Without Git, both provenance fields are
  `unversioned`; never claim an earlier commit includes uncommitted work.
  Obtain the full Git evidence ID with `git rev-parse --verify HEAD`, never a
  shortened log-display hash. Before removing active sources, validate all
  envelope fields and compare the complete retained source documents; a failed
  validation keeps the milestone active and stops retirement.
- Cancelled/superseded outcomes also need `Disposition` naming authority,
  rationale, and dependency disposition. Supersession needs `Successor`.
  Neither automatically satisfies a completion dependency. Every historical
  `[-]` row must name its accepted successor in its retained notes.
- Create `docs/history/index.md` only on first use. Its table columns are
  `Milestone | Outcome | Retired | Record | Summary`; use bare IDs and dates,
  matching the record metadata, with a relative link to that ID's status file.
  Remove the retired status file, active index row, and specification together;
  leave only a history-index link in `milestone.md`. Repair maintained incoming
  links. Frozen archives and evolution snapshots retain their original paths,
  resolved through record provenance. Stop on collisions or incomplete moves.
- Freeze retired records and preserve index entries. Resolve IDs through both
  active and retired locations; never reuse an ID or reinitialize an all-retired
  project. Read historical records only for relevant dependencies or questions.
  Later corrections use new linked knowledge or remediation records.
- Before materially replacing/removing facts or lessons, append their original
  document/heading and literal old wording, reason, evidence, and replacement
  link (or reason for none) beneath a unique dated heading in
  `docs/history/knowledge.md`. Link the journal from the history index. Merge
  duplicate lessons and remove obsolete ones after preserving this evidence.
  This also covers changes outside milestones; ordinary editorial revisions
  need no journal entry. Git supplies optional intermediate revision history.
- Follow the governing commit policy, including no commits under `none`.
  Retirement requires no separate archive invocation or clean baseline.
  Refresh existing disposable goal input for remaining active work, or remove
  it when empty, without creating a new goal-protocol requirement.

Existing projects adopt the contract through an explicit migration. An explicit
cleanup request may retire old closed milestones only with adequate closure
evidence; installing updated skills alone never moves existing files. The
optional API runner still requires Git; ordinary Markdown maintenance can follow
a permitted no-commit workflow without initializing Git.

## Check the output

Before reporting completion, verify all of the following:

1. Every marker is wrapped in backticks.
2. At most one general row is `[~]`; every `[-]` row names its accepted
   successor and is non-actionable.
3. Every status filename is `status-<LANE><NN>.md` with a two-digit number.
4. The milestone index lists exactly the active status files that exist, and
   every link resolves.
5. Candidate directions have no lane letters, IDs, status files, or launch
   entries, and each has a reason and promotion trigger.
6. When `suggested.txt` exists, it maps every active ordered ID to exactly one
   existing status file; its order and impact map match the approved active
   graph. When it is omitted, no generated pointer tells the user to read it.
7. The approved file actions were honored and no existing content was silently
   overwritten.
8. No bracketed placeholder or unexplained `N/A` remains.
9. Every repository fact in the memory bank agrees with its current source.
10. Domain terminology is consistent across the generated files, and every
   material concept relationship or business invariant discovered during the
   interview appears in `product.md`.
11. When an archive preflight exists, every selected context is `verified`, its
    link resolves, verified archives are unchanged, and no archive ID appears in
    the milestone index, a status file, or `suggested.txt`.
12. Lessons have evidence, history is read on demand, and the generated closure
    and retrieval contract agrees with the retirement envelope above. No
    project-specific retired records or empty history directories were created.

For an existing project, run the documented verification command when it is
safe and available to prove the command is real. If no such command exists yet,
make creating it the first active status row as approved.

## Hand off

Report what was created, merged, preserved, or omitted; the selected delivery
boundary and active horizon; candidate directions; verification performed; and
anything still blocked or unavailable.

Explain how to continue using the form the installation accepts. Plain English
works everywhere: *"tackle next pending item in memory bank"* for one task.
Plugin installs use `/memory-bank:memory-bank-goal` in Claude Code and
`$memory-bank:memory-bank-goal` in Codex. Plain-file installs use
`/memory-bank-goal` and `$memory-bank-goal`, respectively. DSH filesystem
installs use `/memory-bank-goal` or an ordinary-language request. Use its Web
session for unresolved approvals and headless only with a complete authorized
request or a safe stop; session exit alone is not acceptance.

When `memory-bank/suggested.txt` exists, explain that running the goal skill with
no arguments reconciles it and shows the complete resolved request for
confirmation. For built-in `/goal` in Claude Code or Codex, show the complete
reference-based objective from the goal skill rather than asking the user to
reconstruct maps by hand. Explain that built-in `/goal` keeps the objective
active while `GOAL.md` supplies the execution protocol. When the launch
reference was omitted, explain how to run one row and why ordered execution is
unavailable until a compatible protocol is installed or approved.

## Runtime capability contract

Include in the generated project instructions:

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

Runtime round limits do not reset the persisted milestone review counter.
Read its stored count and findings before each review; persist the iteration as
started before reviewing and resume an interrupted pass at that same number.
Terminal task rows do not prove acceptance: resume incomplete milestone review
and closure before selecting new work.

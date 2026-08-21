# Memory-Bank Write Contract

Read this reference only after the user approves the Phase 2 proposal.

## Contents

- [Apply safe file actions](#apply-safe-file-actions)
- [Write the project files](#write-the-project-files)
- [Handle the portable goal protocol](#handle-the-portable-goal-protocol)
- [Write the disposable launch reference](#write-the-disposable-launch-reference)
- [Write status tables](#write-status-tables)
- [Check the output](#check-the-output)
- [Hand off](#hand-off)

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
- Stop and ask before any collision whose safe merge was not approved.

## Write the project files

Create or merge the approved project-specific content for:

```text
AGENTS.md                        what an agent reads first
GOAL.md                          optional protocol for multi-milestone runs
memory-bank/product.md           product, users, workflows, domain model, non-goals
memory-bank/architecture.md      layout, data flow, ownership, public contracts
memory-bank/tech-stack.md        stack, dependencies, harnesses, commands
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

Include a `Review finding severity` section in `milestone.md`. Explain that P1
and P2 are engineering review priorities rather than product-domain terms,
milestone execution priority, or status markers. Define their default context,
typical examples, and gate effect; let project-specific definitions in
`AGENTS.md` or a linked review policy override those defaults. Classification
must follow impact, likelihood, and affected scope rather than fix size.

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

The backticks around every marker are required by the API harness parser:

```markdown
# Status M01 - <milestone title>

**Acceptance.** <commands and other evidence, and what they must show>

| Item | State | Notes |
|---|---|---|
| <task> | `[ ]` | <constraint, edge case, or decision from the interview> |
```

Markers: `` `[ ]` `` pending, `` `[+]` `` completed, `` `[~]` `` in progress,
`` `[!]` `` blocked, `` `[X]` `` cancelled.

## Check the output

Before reporting completion, verify all of the following:

1. Every marker is wrapped in backticks.
2. Every status filename is `status-<LANE><NN>.md` with a two-digit number.
3. The milestone index lists exactly the active status files that exist, and
   every link resolves.
4. Candidate directions have no lane letters, IDs, status files, or launch
   entries, and each has a reason and promotion trigger.
5. When `suggested.txt` exists, it maps every active ordered ID to exactly one
   existing status file; its order and impact map match the approved active
   graph. When it is omitted, no generated pointer tells the user to read it.
6. The approved file actions were honored and no existing content was silently
   overwritten.
7. No bracketed placeholder or unexplained `N/A` remains.
8. Every repository fact in the memory bank agrees with its current source.
9. Domain terminology is consistent across the generated files, and every
   material concept relationship or business invariant discovered during the
   interview appears in `product.md`.

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
`/memory-bank-goal` and `$memory-bank-goal`.

When `memory-bank/suggested.txt` exists, explain that running the goal skill with
no arguments reconciles it and shows the complete resolved request for
confirmation. For Claude Code's built-in `/goal`, show the complete
reference-based command from the goal skill rather than asking the user to
reconstruct maps by hand. When the launch reference was omitted, explain how to
run one row and why ordered execution is unavailable until a compatible
protocol is installed or approved.

# Memory-Bank Write Contract

Read this reference during Phase 2, before proposing file actions. Apply its
writes only after the user approves the complete proposal.

## Contents

- [Apply safe file actions](#apply-safe-file-actions)
- [Write the project files](#write-the-project-files)
- [Handle the stock goal protocol](#handle-the-stock-goal-protocol)
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
- Projects do not receive a protocol copy. Preserve an existing `tabilet/GOAL.md`
  and classify it with the bundled `goal-protocol.json`, as the goal protocol's
  Protocol Resolution And Identity section describes: report a stock-identical
  copy as removable, report a modified full protocol copy as needing reduction to
  its project-specific part before goal use, and keep anything else as the
  project addendum. Remove or rewrite it only with explicit approval; never write
  a merged protocol. Resolve `GOAL_PROTOCOL` selection first: a file explicitly
  selected as the full alternative protocol is preserved in that role, not
  reduced or removed as an addendum; record `selected-protocol sha256:<hash>`
  for that package and its actual path/hash as the governing identity.
- Create `tabilet/memory-bank/suggested.txt` only when the user approves goal use and
  the selected governing protocol is available and compatible. Otherwise omit the launch reference and
  every optional goal-protocol paragraph or pointer from generated `AGENTS.md`
  and `tabilet/memory-bank/milestone.md`; do not generate a request that names a
  missing protocol.
- When `tabilet/evolution/` already contains numbered direction history, preserve it and
  use the next unused version for the approved initial memory-bank snapshot.
- When an approved archive preflight exists, merge its current observed facts
  from `tabilet/memory-bank/product.md` and `tabilet/memory-bank/architecture.md`. Preserve every
  verified `tabilet/docs/archive-<LANE><NN>.md` byte-for-byte. Treat archive lanes and
  IDs as an independent namespace that never enters milestone indexes, status
  files, or goal launch input.
- Stop and ask before any collision whose safe merge was not approved.

## Write the project files

Create or merge the approved project-specific content for:

```text
AGENTS.md                        what an agent reads first
tabilet/GOAL.md                  existing project addendum only; never generated
tabilet/stages.md                optional overview when multiple stages are approved
tabilet/memory-bank/product.md           product, users, workflows, domain model, non-goals
tabilet/memory-bank/architecture.md      layout, data flow, ownership, public contracts
tabilet/memory-bank/tech-stack.md        stack, dependencies, harnesses, commands
tabilet/memory-bank/lessons.md           applicable reusable lessons and evidence
tabilet/memory-bank/milestone.md         active index, acceptance, candidate directions
tabilet/memory-bank/status-<LANE><NN>.md one per active milestone, one row per task
tabilet/memory-bank/suggested.txt        optional; only when goal use is approved
tabilet/evolution/prompt-v1.md           initial direction, or next unused version
tabilet/evolution/result-v1.md           current state, or next unused version
```

Write only applicable sections. Remove optional template sections that do not
apply instead of inventing behavior or writing `N/A`. Never leave bracketed
placeholders.

When stages are approved, follow the bundled
[stage contract](stages.md) to create or merge `tabilet/stages.md`. A future
stage may remain a preliminary idea. Record the current stage's ID in each
relevant active milestone specification. An absent stages file means one
implicit stage; do not add stage pointers to a project without that file.
Do not copy every preliminary stage into Candidate Directions or require it to
have a promotion trigger.

Keep `AGENTS.md` short: what to read and in what order, essential commands,
boundaries, hard rules, and work cadence. Point at the memory bank rather than
restating it.

When verified archives exist, keep their registry in `architecture.md` and add
the archive lifecycle rule to `AGENTS.md`: archives are frozen evidence at their
recorded baseline, while current product and system truth stays in `product.md`
and `architecture.md`. Agents read a linked archive only when historical
baseline evidence is relevant and never update it with later code changes.

In `tabilet/memory-bank/product.md`, write the canonical product and business
terminology as a domain model. For each material concept, capture its meaning
and the relationships or invariants that constrain it, including ownership,
parent/child structure, cardinality, lifecycle, and state transitions when they
matter. Keep technical storage and implementation details in `architecture.md`.
Do not create a parallel `context.md` or duplicate the domain model elsewhere.

In `tabilet/memory-bank/tech-stack.md`, define the language floor, tools, dependencies,
commands, runtime assumptions, and execution harnesses.
Accept `--test standard` (the default when omitted), `browserlight`, `golight`,
`rustlight`, `tslight`, `jslight` or `pythonlight`. Follow the bundle-local
[testing profiles](testing-profiles.md) for selection, budget defaults and
language-specific fixtures. `standard` records existing commands without extra
constraints. Light profiles generate `## Verification and testing standards`
with separate focused, full-regression and race/UI budgets: 30-second focused
target / two-minute cap, 20-minute full-suite cap and five-minute race/UI cap,
subject to explicit project limits. Do not impose a 30-second full-suite ceiling.
Keep compilation and test execution timing distinct. Required physical evidence
gets a named final gate and explicit handoff in the approved plan.

For a light profile, include these rules in the proposed verification
standards and assign the required evidence to the relevant milestone owners.
`standard` adds none of them and keeps the project's existing commands:

- **Execution cadence.** Run focused verification during task loops; run the
  full suite once per unchanged closure candidate and race/UI checks when the
  change touches concurrency or UI and at required closure; rerun the affected
  checks after every review fix.
- **Replacement coverage.** When retiring an implementation, preserve meaningful
  success and failure coverage for retained behavior through its successor.
  Distinguish executed behavior, mocks, compile-only checks and deferred
  integration proof; claim only what the evidence demonstrates.
- **Acceptance readiness.** Identify missing final-acceptance inputs, capabilities
  and authority early through permitted inspection. Prepare concrete approval
  scope while independent authorized work continues. Keep deferred verification
  with its named owner and gate, preserving dependencies, intermediate acceptance
  and action limits. Use existing records. Run a fast preflight of fixtures,
  schemas and launchers before each counted expensive attempt.

When a non-standard profile is chosen, add a rule under `AGENTS.md` Hard Rules:
`- Follow the verification and testing standards defined in tabilet/memory-bank/tech-stack.md.`

In `tabilet/memory-bank/milestone.md`:

- index exactly the approved active milestones and link each to its one status
  file;
- state their dependency order, acceptance, and downstream relationships;
- for acceptance that depends on an expensive or protected check, cover only
  behavior the milestone owns, proved with the smallest workload; leave real
  producer or consumer pairing to the adopting milestone; give needed host
  capabilities a cheap readiness probe as the first row; and name an uncounted
  local diagnostic loop;
- define optional boundaries and parallel safety (depends on, downstream
  impacts, write set, contracts read, and parallel-safe defaulting to no);
  never prune downstream impacts to force parallel-safe status; and
- place later work in an explicitly unnumbered `Candidate Directions` section
  with columns for direction, why it is deferred, and its promotion trigger.
- when stages exist, reference each active milestone's stage by its stable ID
  and keep future-stage sketches out of the active index.

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
Record work the user rules out of the project as an Out of scope entry with its
reason. It gets no ID, never promotes, and returns only through a new approved
direction, so the same idea is not re-proposed as a candidate.
When a trigger becomes true, reconsider the candidate and obtain approval
before allocating the next unused permanent ID.

## Handle the stock goal protocol

The stock goal protocol ships with the skills. This bundle carries `GOAL.md` and
its fingerprint registry `goal-protocol.json` beside the parent
`memory-bank-init/SKILL.md`; resolve them relative to that directory, which is
the same in plugin and plain-file installs. Do not depend on provider-specific
plugin-root environment variables, and do not copy the protocol into the
project.

Use the bundled files for stock selection. Preserve an explicit
`GOAL_PROTOCOL` alternative and inspect its actual file before proposing launch
input. An alternative does not require the stock runtime to be its governing
protocol. If the selected protocol is unavailable or incompatible, report the
gap and omit new launch input; preserve any existing input pending resolution.
Never approximate a protocol or silently replace the selection. One-row work
remains available without a goal protocol.

Tell the user the launch reference is optional and can be deleted at any time.
The goal protocol is one way to run several active milestones in order, not a
requirement of the memory bank. A project-specific restriction for goal runs
belongs in a short `tabilet/GOAL.md` addendum, which narrows the stock protocol
and never restates it.

## Write the disposable launch reference

Always include `CORRECTIVE_PLANNING` in generated launch input. For Init,
`--environment dangerous` proposes `CORRECTIVE_PLANNING: auto`; sandbox and
least propose `CORRECTIVE_PLANNING: confirm`. Explicit human policy overrides
the preset. Explain that approval of the later execution request supplies
standing authority for necessary corrective planning within its original
delivery outcome, existing action scopes and limits. Creating or approving
these planning files never starts execution or activates action grants.
Do not put an email recipient in project launch input by default; `--email`
belongs to the later explicit Goal/Next invocation.

Author optional `AUTHORIZATION_REQUIREMENTS` in each owning milestone
specification when protected actions are relevant; do not duplicate them in
status files. `via` is `goal-policy` or `explicit`; only local commits and
ordinary local implementation/verification may use `goal-policy`. Other listed
actions require explicit human authority. Declare conditions, not permission
or scheduling, and resolve exact target context by read-only inspection.

Any `AUTHORIZATION_GRANTS` included in launch input must be clearly labeled
PROPOSED — NOT APPROVED. Map exact milestone keys, package-qualified for
cross-package goals, to lists with `grant_id`, `action`, `executor`, and `scope`. Never
claim that planning approval activates grants. Effective grants need separate
explicit human approval of concrete scope with no unresolved placeholders,
wildcard targets, blanket booleans, or credentials. Preserve commit, integration,
external-mutation, and project restrictions; show conflicts for clarification.
Do not create approval state, require auditing, or launch protected actions.
Missing fields preserve legacy behavior without automatic migration.

Always emit `AUTHORIZATION_GRANTS`, even when empty: `AUTHORIZATION_GRANTS: {}`
means no explicit grants and is the default. Requirements stay in the owning
milestone specifications; do not copy them into launch input. A nonempty grant
mapping still contains only unapproved proposals until scoped human approval.

Executors are `coordinator` or `assigned-agent`. Each requirement has `via`,
`executor`, and any necessary `scope`. This template lists supported
actions; include only applicable entries in a milestone. It grants no
authority and schedules no action:

```yaml
AUTHORIZATION_REQUIREMENTS:
  git.commit:
    via: goal-policy
    executor: assigned-agent
  git.push:
    via: explicit
    executor: coordinator
    scope:
      repository: "<owning repository>"
      remote: "<exact remote URL>"
      ref: "<exact destination ref>"
      mode: fast-forward
  cli.local:
    via: goal-policy
    executor: assigned-agent
    scope: declared-implementation-and-verification
  browser:
    via: explicit
    executor: assigned-agent
    scope:
      environment: fixture
      origins: ["<exact approved origin>"]
      actions: ["<approved action>"]
  sudo:
    via: explicit
    executor: coordinator
    scope:
      commands: ["<specific privileged operation>"]
  ssh:
    via: explicit
    executor: coordinator
    scope:
      host: "<exact host>"
      user: "<account>"
      commands: ["<specific remote operation>"]
```

When goal use is approved and the selected governing protocol is available and compatible, derive
`tabilet/memory-bank/suggested.txt` only from the approved active horizon. It is advisory
launch input, not project truth. Do not add it to `AGENTS.md`'s required read
order or the milestone index. Tell the user to delete it after launching the
goal or whenever it becomes stale. When no compatible protocol exists, omit
`tabilet/memory-bank/suggested.txt` and report one-row execution as the available path.

Use this shape with project values, never the example values:

Use the commit policy approved for future execution. A no-commit restriction
during initialization does not prohibit commits in a later authorized run.
Creating launch input does not start that run. Preserve its explicit policy;
the goal protocol defines its precedence during execution, while the suggested
order remains disposable. Do not invent a standing policy conflict from an init-only
restriction.

```text
# Disposable multi-milestone launch reference.
# Reconcile this suggestion against milestone.md and the current status files.
# Delete it after launching the goal, or whenever it becomes stale.
# Any AUTHORIZATION_GRANTS below are PROPOSED — NOT APPROVED.
# Planning approval and reading this file do not activate grants.
# Decision markers: [ ] = need authorization, [+] = approve, [-] = deny, [~] = auto.
# Verify sha256 matches human approval before activating grants.

Using the memory-bank goal protocol, execute this loop.

STATUS_ORDER:
M01 -> M02

STATUS_FILE_MAP:
M01 = tabilet/memory-bank/status-M01.md
M02 = tabilet/memory-bank/status-M02.md

DOWNSTREAM_IMPACTS:
M01 -> M02

COMMIT_POLICY: task
SUGGESTED_UPDATE: confirm
CORRECTIVE_PLANNING: confirm
OPTIMIZE_POLICY: none
EXTERNAL_MUTATIONS: none
AUTHORIZATION_GRANTS: {}

GOAL_IDENTITY:
- protocol: stock sha256:<hash>
- <package>: none

Completion condition: every required status is complete, every triggered
conditional status is complete, and every milestone's documented verification
passes.
```

Use CRLF-to-LF normalized protocol/addendum fingerprints from the governing
protocol; version labels are diagnostic metadata. Keep launch approval checksums
as raw-byte hashes.
The example selects stock. For stock selection, fill `GOAL_IDENTITY` from the
bundled `goal-protocol.json`: its `version` and `sha256` for the protocol line.
For an explicit alternative, retain `GOAL_PROTOCOL: <path>`, replace the stock
invocation with an invocation of that selected protocol, and record
`protocol: <path> sha256:<hash>` from its actual bytes. In both cases list every
participating package's applicable addendum hash, `ignored-stock sha256:<hash>`, or
`none`. Preserve explicit selection and surface any proposed switch for human
approval. A package-local protocol file is never required for stock use.

Include `MODEL_POLICY` only when requested. Preserve an existing explicit
policy and its user-selected role models and optional effort settings; omission
preserves host model settings. Planning approval does not activate model routing
for a paused run. Follow the stock protocol's Optional Model Policy section;
no provider or model is required, and no environment preset chooses one.
Explain that unavailable explicit host settings pause affected execution.

Map every active status in `STATUS_ORDER` to exactly one file. Include known
active downstream consumers; the goal loop will discover more. Use
`DOWNSTREAM_IMPACTS: none` when there are none.

Include `SUGGESTED_UPDATE: confirm` by default, or `SUGGESTED_UPDATE: auto` when
the user authorizes the orchestrator to refresh remaining milestones without
prompting for fresh authorization. Under `--environment dangerous`, synthesize hands-free
launch defaults from day one: `SUGGESTED_UPDATE: auto`, `SCOPE_POLICY: workspace-contained`,
`COMMIT_POLICY: task`, and ambient `GLOBAL:` grants (`- [~] global-local-verify` for local
verification and `- [+] global-repo-push` for workspace organization remotes). Under
`--environment dangerous`, `SCOPE_POLICY: workspace-contained` and `global-local-verify` (`[~]`)
enable the goal protocol's standing revision envelope for unprivileged workspace-local
verification; write an explicit `standing` block (schema in `GOAL.md`) only for such local,
disposable `cli.local` checks, marked `[~]` (effective when the human approves the launch
checksum) with a budget no larger than the gate's default of 3. Destructive or
privileged operations (`sudo`, `ssh`, live browser, external pushes outside the workspace)
remain `[ ]` or omitted unless an explicit modifier authorizes them, and then as an exact-command
grant without a `standing` block. Include recommended runner
flags in launch comments (`# Recommended harness flags: ALLOW_UNSANDBOXED_SHELL=1`).
Under `--environment sandbox` (the default when omitted), synthesize standard fail-safe policies:
`SUGGESTED_UPDATE: confirm`, `SCOPE_POLICY: strict`, and `AUTHORIZATION_GRANTS: {}` (or proposed
grants, including any explicit `standing` block for local verification, marked `[ ]`). Under `--environment least`, synthesize strict least privilege:
`SUGGESTED_UPDATE: confirm`, `SCOPE_POLICY: strict`, and `AUTHORIZATION_GRANTS: {}`, requiring
manual approval for all actions; a modifier-added grant, `standing` or not, is proposed as `[ ]`. Modifier expressions like `but <action> in milestone <ID>`
attach milestone-specific policy overrides in `milestone.md`.
Synthesize proposed `AUTHORIZATION_GRANTS` from
active milestone `AUTHORIZATION_REQUIREMENTS` when present. Mark safe local commands
under goal policy as `[~]`, and operations requiring explicit human approval as `[ ]`.
High-level `GLOBAL:` grants declare common authorities across milestones. Never claim that
planning approval activates grants; execution requires explicit human approval
matching the file's SHA256 checksum. Missing fields preserve legacy behavior.

A trailing `?` is allowed only for a conditionally required status inside the
active horizon. Document its concrete project-state trigger in
`tabilet/memory-bank/milestone.md`, and include the suffix only when the approved next
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

Create `tabilet/memory-bank/lessons.md` as a curated reference of applicable lessons:
each names its scope, lesson, rationale, and source evidence. State explicitly
when no lessons are established. Do not invent lessons or repeat the domain
model, architecture contracts, or commands. The read order consults relevant
topics before substantial changes; it does not read the whole history on boot.

Generate these retirement rules in `tabilet/memory-bank/milestone.md`:

- After the review gate passes within its persisted 10 iterations, verification
  passes, current facts/lessons are consolidated, and downstream work is
  reconciled, automatically retire the milestone. Terminal markers alone are
  insufficient; unresolved or conditional pending work stays active.
- Retain full final specifications and status documents, not summaries, in
  `tabilet/docs/history/status-<LANE><NN>.md`. Preserve every earlier row and note. Use
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
  `no current-truth change`). A completed legacy closure that predates the
  persisted review gate instead uses `Review` (`legacy`), `Review iterations`
  (`not recorded`), and a required `Legacy closure` field, as defined in the
  milestone retirement procedure. Without Git, both provenance fields are
  `unversioned`; never claim an earlier commit includes uncommitted work.
  Obtain the full Git evidence ID with `git rev-parse --verify HEAD`, never a
  shortened log-display hash. Before removing active sources, validate all
  envelope fields and compare the complete retained source documents; a failed
  validation keeps the milestone active and stops retirement.
- Cancelled/superseded outcomes also need `Disposition` naming authority,
  rationale, and dependency disposition. Supersession needs `Successor`.
  Neither automatically satisfies a completion dependency. Every historical
  `[-]` row must name its accepted successor in its retained notes.
- Create `tabilet/docs/history/index.md` only on first use. Its table columns are
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
  `tabilet/docs/history/knowledge.md`. Link the journal from the history index. Merge
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
   Provisional stages may have `STG-` IDs but no milestone or status IDs, task
   rows, or launch entries. Every active milestone's stage ID resolves when
   `tabilet/stages.md` exists.
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

When `tabilet/memory-bank/suggested.txt` exists, explain that running the goal skill with
no arguments reconciles it and shows the complete resolved request for
confirmation. For built-in `/goal` in Claude Code or Codex, show the complete
reference-based objective from the goal skill rather than asking the user to
reconstruct maps by hand. Explain that built-in `/goal` keeps the objective
active while `tabilet/GOAL.md` supplies the execution protocol. When the launch
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

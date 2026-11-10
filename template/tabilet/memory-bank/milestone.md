# Milestones

Milestones are listed in priority order. Each item lists scope and acceptance
criteria. Per-item completion state lives in one status file per milestone,
named by the status ID pattern below.

Each milestone section is a review unit: after no `[ ]`, `[~]`, or `[!]` rows
remain in its matching status file, run a deep code review and a milestone
review against the milestone acceptance criteria before moving to the next
milestone. Completed `[+]`, cancelled `[X]`, and closed-historical `[-]` rows are
non-actionable; every `[-]` row must name its accepted successor. Review-driven
fixes should be verified and committed before work starts on the next milestone.
Do not create an extra milestone commit when the review produces no changes.

The review procedure below covers one milestone. To run several in order, with
dependency and downstream reconciliation between them, the memory-bank goal
protocol bundled with the skills is one optional protocol for that; any
equivalent works just as well. An optional `tabilet/GOAL.md` addendum narrows
that protocol for this project and never restates it.

When `tabilet/stages.md` exists, it records stable `STG-` IDs, the current
stage, and provisional later ideas. Give each active milestone specification
its stage ID. An absent stages file means one implicit stage. Stage labels do
not determine task readiness or prove milestone acceptance.

Each active milestone specification defines scope, acceptance criteria, and
optional boundaries and parallel safety: `Depends on`, `Downstream impacts`,
`Write set`, `Contracts read`, and `Parallel-safe` (defaulting to `no`). A
milestone is parallel-safe only when unordered against other active work, its
write set is disjoint, and its inputs are frozen. Parallel safety never prunes
downstream impact reconciliation.

A milestone introducing a durable non-terminal state lists its legal exits,
authorized actors, supporting interfaces or documented handoffs, and the
disposition when progress cannot continue. Map identified persistence boundaries
and crash windows to recovery tests. Cover each exit's meaningful success and
failure behavior; do not invent a one-test-per-exit correspondence where crash
boundaries differ. Resolve missing required exits during planning.

Distinguish advisory performance targets from required acceptance thresholds.
Record the measured miss separately from correctness results. An
"owner-accepted miss" cites the explicit acceptance change or disposition; it
never relabels the measurement as a pass. "Target kept, further work proposed"
preserves the target, and an unmet required threshold still prevents closure.
Never lower a target silently. These are prose dispositions, not status markers.

## Milestone families

Keep the original delivery outcome stable. Small directly related fixes stay in
the current task. Substantial required repairs belong in amendment records;
optional features, broader coverage and environment conveniences belong in
option records. An amendment must identify the original unmet requirement,
evidence and why a simpler implementation or verification route cannot meet it.
External testing-tool repair is optional unless the owner explicitly promotes
it, even under `CORRECTIVE_PLANNING: auto`. Mocks cannot prove unexecuted real
acceptance. Missing original requirements need repair or an owner disposition.

Each child owns its specification, task table and review in one file. Begin it
with `## M53-01 - [Title]` and one `Parent: M53` declaration; ordinary bold and
trailing whitespace are accepted. Subsections such as `## Tasks` are allowed.
Keep concise parent/roadmap links instead of duplicate specifications. Child
format and numbering are defined in [Status ID Pattern](#status-id-pattern).
An initial option may be a short finding without task rows.

Required amendments block the parent's acceptance; options do not. Preserve
completed work and review counters. Record deferred acceptance as `[!]` with
its amendment and resumption condition. `Parent:` does not mean a dependency
on the completed parent. A child's review never replaces the parent's review.
Keep detailed state in the owning file and Git history, not dated AGENTS prose.

For multi-milestone sequencing, family ordering and `OPTION_POLICY`, follow the
selected goal protocol (the stock `GOAL.md` is bundled with the skills). Explicit
owner selection is required for options; `ignore` leaves them deferred throughout
the goal. These policies supply no extra action authority or budget. Next stays
within its selected task. A claimed option still counts toward the one-row
ownership rule even when the unscoped runner cannot execute it.

Retire child records under their original filename, preserving complete source,
Parent and permanent identity. Source status and Source specification both name
the original child file. The selected closing row may change to completed;
earlier rows and specification prose must survive. Required amendment reviews
and acceptance must pass before parent retirement. A declined rowless option
can retire as cancelled or explicitly superseded with its owner Disposition,
Review `not applicable` and Review iterations `0`; no implementation row is
needed to withdraw a proposal. Supersession names a bare ID, record filename or
Markdown link to the successor, which must satisfy retained obligations.
Reclassification requires an explicit owner decision and a fresh identity.

## Authorization requirements

Each milestone specification may contain `AUTHORIZATION_REQUIREMENTS`. It
declares conditions on actions; it never grants permission or schedules them.
Keep the declaration in that specification only. Status files reference it.
The following optional shape is a template, not authorization:

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

`via` is `goal-policy` or `explicit`. Only local commits and ordinary local
implementation/verification may use `goal-policy`; their governing task scope
and commit policy still apply. Other listed actions require explicit human
authority. Inspect and resolve exact targets before seeking approval. A
resolved grant must have concrete scope covering the requirement, with no
unresolved placeholders, wildcard targets, blanket booleans, or credentials.

Under the optional goal protocol, `AUTHORIZATION_GRANTS` belongs
to the resolved human-approved request, not to this file. Requirements,
proposed grants, status notes, and `suggested.txt` are evidence, not approval.
Check authority before the action; pause affected work and dependents when it
is missing. A changed input to a protected action is a changed scope unless the
goal protocol's standing revision envelope covers it; that envelope reaches only
unprivileged workspace-local verification, never `sudo`, `ssh`, live browser,
or push grants. Independent authorized work may continue under the governing
order and ownership rules. Required unperformed task or acceptance actions
prevent closure; listing an action here alone does not require its performance.
Outside a goal, use the current scoped human request and applicable project
rules. Missing fields preserve legacy behavior without new authority or
automatic migration. These are instruction-level boundaries, not tool or OS
enforcement.

## Standing corrective planning

`CORRECTIVE_PLANNING` is an optional execution policy, defaulting to `confirm`.
Standing `auto` cannot weaken acceptance, required evidence, verification gates
or severity rules, cancel unmet obligations, or erase them through supersession.
A named successor preserves all obligations. Blocking findings remain attached
to the originating milestone's persisted review counter; a repair milestone's
own review cannot replace the originating gate's next iteration, scoped as the
review gate defines, or bypass the approved review limit.
An approved `auto` allows the Goal/Next owner to prepare and check necessary
repair planning against the original delivery outcome, owning repositories,
existing action grants and all limits, then apply it under standing approval.
Prefer a matching open milestone when its scope and dependency position fit;
otherwise create a new repair milestone with permanent identity and lineage.
Preserve completed/frozen history, row outcomes and review counters. New
features, scope or permission expansion, higher limits, collisions and unknown
checksum drift still require human direction. Children only report needed work.

The owner reconciles dependencies, pending consumers, the resolved request and
any existing launch reference; it records old/new hashes and approval context
outside authoritative task records. A covered correction may refresh launch
input without reapproval even under `SUGGESTED_UPDATE: confirm`. Other edits
retain that policy. Goal executes accepted repair prerequisites before their
consumers; Next returns to its original task after necessary repairs, preserving
ownership and interrupted evidence. All repair rows/commits/attempts count
toward explicit limits. Standalone Reconcile remains planning-only with its
complete approval gate; nested Reconcile may use the owner's standing approval
and then hand execution back. Installation never activates this policy.

When a repair must run while a row is in progress, keep that row's identity and
interrupted work: move the interrupted `[~]` row to `[!]` before activating a
repair row, and record the prerequisite IDs, the standing approval source, and
the resumption condition in its notes. Keep zero or one `[~]` row. Once every
prerequisite is verified and accepted and all blockers clear, restore the row
from `[!]` to `[~]` under the same approval. Recover this chain on resume
without selecting unrelated work. Preserve partial implementation; suspension
bookkeeping may join the scoped repair checkpoint, but unfinished implementation
cannot. Pause if overlapping changes cannot be separated safely. Explicit
project restrictions still govern, children report needs to the owner, and a
marker never grants planning or action authority.

## Status ID Pattern

Root records use `status-<LANE><NN>.md`. Children use
`amend-<parent>-<NN>.md` or `option-<parent>-<NN>.md`, for example
`amend-M53-01.md` and `option-M53-02.md`. Both kinds share one permanent
01–99 child sequence per root parent; reserve it across active/history records.
No recursive child families and no silent renaming. A root lane and archive
namespace keep their existing independent numbering.

Status files are named `tabilet/memory-bank/status-<LANE><NN>.md`. `<LANE>` is a single
uppercase letter that classifies the work, and `<NN>` is a positive number
with at least two digits within that lane:

```text
M01, M02, M03, ... M09, M10, M11, ...    Default lane
[A]01, [A]02, ... [A]09, [A]10, ...      [Domain lane, e.g. accounting]
[S]01, [S]02, ... [S]09, [S]10, ...      [Domain lane, e.g. shopping]
```

Lane meanings:

- `M`: default lane. Bootstrap milestones, cross-cutting delivery, and any work
  that does not classify into a domain lane.
- `[A]`: [domain, e.g. accounting: billing, settlement, and payouts].
- `[S]`: [domain, e.g. shopping: catalog, cart, and checkout].

Rules:

- Use at least two digits (`A01`, not `A1`); after `A99`, continue with
  `A100`, `A101`, and so on. Do not add leading zeros beyond the minimum.
  Sort numeric IDs numerically when chronological order matters; lexical order
  puts `A100` before `A99`. Child suffixes remain two digits (`01`–`99`).
- Do not reuse an ID after its status file exists, including after retirement.
  Search both active files and the history index before allocating an ID.
  Context archive IDs use an independent namespace; a matching archive ID is
  not a status collision and does not justify renaming a status ID.
  Cancelled work keeps its record and is marked `[X]`.
- Retain a consumed failed attempt or superseded row as `[-]` closed historical
  evidence, record its accepted successor, and never retry it.
- Never rename a status ID after its file exists. Resolve a lane collision by
  allocating an unused lane/ID to new work and recording lineage; preserve the
  original record and its reserved ID.
- Do not create an aggregate `tabilet/memory-bank/status.md`. Task rows live in lane
  files only.
- Keep the lane meanings above current as new lanes are added.

## Status Files

Every active row must link its existing status file. Retired IDs and specifications
belong in `tabilet/docs/history/index.md`, not in this table. When history exists, add
one link to that index here; do not accumulate one retired row per milestone.

| Milestone | Status File | Summary |
|---|---|---|
| M01 | [status-M01.md](status-M01.md) | [Milestone summary.] |

Additional row examples, not active allocations. Add an approved milestone's
specification and status file together before including its row above:

```markdown
| M02 | `status-M02.md` | [Milestone summary.] |
| [A]01 | `status-A01.md` | [Domain milestone summary.] |
```

## Requested changes after initialization

For stage work, `memory-bank-propose --stages` requests creation or revision of
the optional `tabilet/stages.md` overview. `--stage STG-01` selects an existing
stage; the request must say when milestones should be planned. Equivalent
plain-English references are valid. Later-stage ideas may have only an ID,
tentative name, and brief intent. Additional context can be proposed later,
without assigning milestone IDs or task rows now. Stage IDs stay stable across
renames and reorderings and are never reused. Do not advance stages or schedule
later work merely because the current milestone closes.

For execution environment and authorization policy, `--environment dangerous`,
`--environment sandbox` (default when omitted), or `--environment least` sets the
hands-free stance in launch references and milestone policies, optionally modified
by expressions like `plus <action>`, `minus <action>`, or `but <action> in milestone <ID>`.

For a requested feature, candidate promotion, or change to future direction,
inspect the current plan and implementation first. Record user intent separately
from observed facts and unresolved assumptions. If a pending milestone already
owns a small change, propose the smallest row and acceptance update that fits.
Otherwise propose a dependency-closed milestone with an unused permanent ID.
A candidate's trigger prompts a new decision and approval; promotion is never
automatic. Schedule by approved priority and dependencies, not review finding
severity. Reconcile affected downstream acceptance and optional launch input.

Present one complete proposal with intended outcome, owner rows, acceptance,
verification, dependencies, downstream effects, and exact file actions. Write
planning changes only after approval and a fresh check of affected files,
worktree changes, and active and retired IDs. Preserve non-pending outcomes,
review counters, local policy, and frozen history. Record target behavior here
and in pending status rows until implemented; current architecture describes
only what the repository establishes as fact. Planning does not implement or
accept the requested behavior. Use `memory-bank-propose` where installed, or
follow this procedure directly with another agent.

**Real-effect checks.** Some acceptance depends on a class R check that has a
real external effect or is protected; see the
[test policy](test-policy.md) and the
[verification-attempt gate](#verification-attempt-gate). Without a test policy,
the gate covers every expensive or protected check. For such a milestone:

- Limit acceptance to behavior the milestone owns, proved with the smallest
  workload. Put actual pairing with real producers or consumers in the
  milestone that adopts them.
- When the check needs host capabilities (privileges, operating-system or
  kernel features, devices, browsers, or external accounts), make a cheap
  readiness probe its first row.
- Name the uncounted local diagnostic loop (the class O loop), and order cases
  so that an unrelated failure cannot hide the milestone's own cases.

For shared concurrency surfaces changed by multiple milestones, keep a race
watch list in the final integration milestone's verification section. When no
integration milestone is planned, use the last milestone that owns integrated
closure review. Map each surface to a named test that exercises the interacting
changes. Close an entry
only with evidence that its named test actually ran and passed instrumented;
a clean full-suite summary alone is insufficient. Use this existing section,
not a separate ledger, and preserve every required integration gate.

To defer already approved work through a stage rescope, present the exact
untouched pending rows and affected downstream work for approval. After
approval, retain their identity and original task text, mark them `[X]`, and
record the authority, reason, destination stage, and dependency disposition.
Cancellation proves no delivered acceptance. A future replacement receives a
new approved identity and names its cancelled lineage. Preserve `[~]`, `[!]`,
`[+]`, `[X]`, and `[-]` rows and all review evidence. Withdraw affected pending
dependents or keep their prerequisites in the active horizon; an unresolved
dependency cannot be deferred by changing a stage label. An entirely cancelled
milestone remains active until its normal closure and retirement disposition.

## Open review findings

Non-blocking review findings carried past their milestone's review gate. This
register is approved planning state, never retired with a milestone, and not a
review copy: one line per finding.

Last used ID: none

| ID | Finding | Severity | Origin | Fix owner | Disposition |
|---|---|---|---|---|---|

- IDs are `FND-01`, `FND-02`, ...: permanent, never reused, separate from status,
  archive and stage IDs. Origin is the milestone and review iteration.
- Fix owner is the first later active task that touches the code, or
  `unassigned`. That row's notes say "fixes FND-03", and its review records
  fixed, obsolete or still open. A finding follows its code. The originating
  review notes say "carried as FND-03"; that milestone may close and retire.
- Disposition: `open`, `fixed in <commit or task row>`, `obsolete: <evidence>`,
  or `deferred by human: <approval source>`; never the last without that
  approval.
- A `capacity limit` row is Lower. It keeps fix owner `unassigned` unless later work
  builds on it, and then the fix-now and fix-owner rules for non-blocking findings
  apply as usual. It never turns blocking when examined and needs no corrective
  row. A human may defer it or plan a row that fixes it at any review, and must
  at horizon closure.
- In concurrent leases, children return register updates; only the goal owner
  writes them.
- Horizon closure (the last active milestone of the current stage, or of the
  project without stages) requires every row fixed, obsolete or deferred.
  Before then, give every unowned open P2 a corrective row under the
  corrective planning policy. After closure, remove fixed and obsolete rows
  (lineage stays in the fixing task's status record); keep deferred rows and
  the last used ID.

## Candidate Directions

Candidate directions are outside the active execution horizon. They are not
milestones: they have no lane, permanent status ID, status file, or place in an
execution order. A promotion trigger causes fresh planning and approval,
not automatic scheduling. Assign the next unused permanent ID only after a
candidate is promoted.
Reference a stage ID when relevant, without copying its whole description.
A preliminary stage need not have a candidate's deferral reason or promotion
trigger; do not duplicate every stage as a Candidate Direction.

| Direction | Why Deferred | Promotion Trigger |
|---|---|---|
| [Later direction.] | [Why detailed planning would be premature.] | [Decision, evidence, or completed milestone that makes it ready.] |

## Out of scope

Work ruled out of this project, with the reason. Unlike a candidate direction,
an entry here never promotes and has no trigger; it returns only through a new
approved direction. Record it here so the same idea is not proposed again.

| Ruled out | Reason |
|---|---|
| [Work the project will not do.] | [Why it is outside this project's boundary.] |

## Guarantee levels

Optional. A project may define levels for its persisted records, so that a hint
or a rebuildable view does not receive the full durability set.

Project levels: none

While that line says `none`, every record keeps its ordinary treatment and none
of this applies. A project that adopts levels replaces `none` with its own level
names through an explicitly approved planning proposal; the levels and their
guarantees belong to it. An example, not in force:

| Level | Records | Required guarantees |
|---|---|---|
| Full | Records that grant authority or hold data the project must keep | Everything the project requires, such as privacy, crash recovery, quota, backup and legacy refusal |
| Advisory | Records that grant nothing and can be rebuilt or lost | Privacy and a size bound only |

- A milestone that adds a persisted record names the record's level in its
  specification, with the human approval source. An agent may propose a level
  but never assign one, and agent-authored text cannot prove the approval.
- Losing or failing to read an advisory record must be acceptable, and restore
  may bring it back empty.
- A record that influences an authority decision names what protects that
  decision: a separate record of the decision at the full level, or the full
  level for itself.
- Levels apply going forward. Finished work is not reworked for them.

## Review finding severity

P1 and P2 are engineering review priorities. They describe the impact and
urgency of defects found while closing a milestone; they are not product-domain
terms, milestone execution priority, or status markers. Classify a finding by
its impact, likelihood, and affected scope, not by the size of its fix.

Project-specific definitions in `AGENTS.md` or a linked review policy override
these defaults:

| Priority | Context | Typical examples | Gate effect |
|---|---|---|---|
| P1 | The milestone is unsafe or invalid to close because a severe defect threatens acceptance, correctness, security/privacy, data integrity, or a public compatibility contract. | An exploitable access-control failure; data corruption or loss; a breaking public API or migration; the primary acceptance outcome does not work; required tests or operator documentation leave an acceptance line unproven. | Blocking. Fix and review again. |
| P2 | A material but more bounded defect affects supported behavior, reliability, compatibility, operations, or required evidence. | A supported scenario returns the wrong result; a downstream consumer regresses; recovery or failure handling is broken; operator documentation is materially incomplete. | Not blocking under the adopted gate: fix now when cheap or built upon; otherwise carry in [Open review findings](#open-review-findings). |
| Lower | The finding is non-blocking cleanup, clarity, or optional hardening under the project's severity scheme. | Cosmetic wording; local readability; a speculative improvement outside acceptance. | Fix, carry or decline with rationale. |

Any project-defined severity more urgent than P1 also blocks, so **blocking**
means P1 and any project severity above it. An unmet or unproven acceptance line
is P1. A security, privacy or data-loss finding is P1 unless evidence clearly
shows otherwise. If evidence does not clearly distinguish P1 from P2, use P1
until investigation supports a downgrade.

**Tool limits.** A defect in a third-party tool that did not cause the task's
issue is Lower, labelled `tool limit`, only when it leaves the task's evidence
valid, is not caused by the project's own integration, and causes no supported-user
harm covered by the severity table. Record evidence for those conditions and a
proposed owner in the existing review notes or findings register. It does not
block the task or require a workaround there. If any condition fails, classify
it normally; external tool ownership never excuses missing acceptance evidence.
Use the existing Lower dispositions and project overrides, not a new severity.

**Verification discrepancies.** A record or setting difference is Lower when
evidence proves it could not change the result: the required tests ran with
equivalent coverage and passed within the prescribed limits. Record the actual
command and result, the equivalence evidence, and rerun with the prescribed
settings before closure. The discrepancy alone does not fail a review. A missing
required check or a difference that could hide a failure remains P1. A timeout
is still FAIL under the test policy; this rule never waives a required gate,
weakens acceptance, or excuses an authorization breach.

**Test programs.** Keep tests simple enough to check by reading. If a test
seems to need a test of its own, simplify it and prove it against broken product
behavior with red/green or a deliberate broken-product control. Shared test
helpers with meaningful logic need small focused tests. Classify helper defects
by their effect on this task's evidence and supported behavior, not merely by
their existence elsewhere. Where a third-party adapter is needed, keep it thin
and give it sufficient contract coverage; do not introduce a wrapper just to
test it or impose a one-test ceiling. When an earlier fix caused a new finding,
consider removing that fix before adding another. Weakened tests and removed
assertions receive ordinary severity and review, including their effect on
acceptance; being test code never lowers severity by itself.

**Safe capacity refusals.** A case at extreme size or capacity is Lower, not P1 or
P2, when all of these hold: no acceptance line, public contract or previously
supported behavior promises that size; a test shows the refusal is deterministic
and clear, with nothing leaked, corrupted, lost or rewritten; the stored data
stays reachable through a supported path and no required flow dead-ends; and the
limit is documented. Otherwise classify it normally. Carry it in the register
labelled `capacity limit` in the Finding column, citing the test
and the documentation that show each condition; without that evidence it keeps
its ordinary severity. A project whose own severity definitions differ keeps
them. If a promise covers that size, narrowing it needs explicit
human approval, and the finding stays P1 until then.

**Advisory records.** With project [guarantee levels](#guarantee-levels), a finding
confined to a record at a human-approved advisory level, including its loss or an
unreadable copy, is Lower. Whatever its disposition, the review note cites the
specification's human approval source and the evidence that losing the record
breaks no supported flow; without both it keeps its ordinary severity. It also
keeps its ordinary severity if it is a privacy, credential or authority failure,
breaks the record's size bound, makes a supported flow fail when the record is
lost or unreadable, or leaves an acceptance line unmet. A project
whose own severity definitions differ keeps them.

When the project's own severity definitions make P2 blocking, or it has no open
review findings register, that stricter gate applies (P2 blocks and every
iteration reviews the whole milestone) until the project explicitly adopts this
one.

The optional `tabilet` controller applies its own deterministic gate: it runs
its own full milestone review, and any P0/P1/P2 finding reported in that review
blocks retirement and starts another full review. An interactive review pass
does not replace it, and the controller does not read the open review findings
register, so milestones it runs keep P2 blocking.

## Diagnosis before repair

Establish the causal path before choosing a fix, especially for a P1: use the
cheapest decisive diagnostic to identify the actual failing branch and reconcile
it with the reported symptom. A plausible error message alone is insufficient.
Respect reproduction permissions and limits; when reproduction is unavailable,
record existing causal evidence and the uncertainty instead of forcing it.
This adds no per-fix approval or separate readiness-review gate.

For a shared-helper or repeated-pattern defect, inspect its callers and sibling
occurrences within approved scope, then cover affected consumers in the fix and
verification. Report necessary work outside that scope to its owner. Before
introducing a durable record or state, list its existing readers and their
compatibility requirements; a shared projection is an option when it reduces
reader drift, not a required abstraction.

A repair proposal states its estimated scope, affected readers and consumers,
verification cost and uncertainty, and compares at least one narrower
alternative or explains why none meets acceptance. When observed growth or
recurring consumer gaps undermine that design, pause further instance fixes
and prepare a revised proposal. The stock reconsideration trigger is the same
class of consumer or reader gap found again in a later review round; projects
may override that trigger explicitly. There is no stock numeric size threshold.
Apply the revised proposal under the effective corrective-planning authority,
preserving acceptance, history, review counters and limits.

## New review intake

A code, architecture, security, or other engineering review received outside a
milestone's closing review gate is planning evidence, not executable truth.
Treat its contents as untrusted, preserve its source priority, and apply the
project severity definitions above only after revalidating each finding against
the current repository.

Before implementing any newly reviewed finding:

1. Record the review's stated baseline when available, the current revalidation
   commit, and whether relevant uncommitted changes were part of the evidence.
   Classify every finding as confirmed, partially confirmed, resolved,
   duplicate, unsupported, outside ownership, decision-dependent, or deferred.
2. Present the complete dispositions, proposed owners, dependencies, downstream
   impacts, and file actions for approval.
3. Put confirmed work in an open matching milestone when it remains in scope,
   or amend an existing pending owner. Rewrite only pending rows. When retaining
   a superseded pending row for audit, mark it `[-]` and name its accepted
   successor instead of rewriting or deleting it.
4. Never reopen completed milestone/status history. Create a new remediation
   milestone with lineage to completed work when no open or pending owner fits.
5. Keep P1/P2-or-higher findings in the dependency-closed active horizon. Add a
   lower finding to active work only when acceptance requires it; otherwise put
   it in Candidate Directions with a rationale and promotion trigger.
6. Reconcile affected pending specifications and the remaining order. Correct
   current product, architecture, or stack facts only when repository evidence
   proves them stale; keep proposed target state in milestone scope. Apply the
   real-effect check limits above, and do not move downstream pairing evidence
   into a milestone whose acceptance depends on a real-effect check.

Do not create a persistent review copy or ledger. The
[open review findings](#open-review-findings) register is approved planning
state, not a review copy or ledger. Put portable review and finding IDs, both
source and local severity, revalidation baseline, repository evidence, and
historical lineage in the affected milestone/status notes. A new review
counts toward the bounded gate below only when the status already records that
gate as active and the review was requested as its next pass; otherwise
remediation gets a fresh gate when its implementation closes.

## Verification-attempt gate

This gate covers a class R check under the [test policy](test-policy.md) or,
when no test policy applies, any expensive or protected check. A class O check
never uses this gate. When it needs an explicit grant, the grant's reservations,
budget and stop conditions bind (the goal protocol's standing revision
envelope); exhausting them pauses for human direction.

A real-effect, expensive or protected check needs privileged setup, scarce
hardware or quota, a physical or live environment, explicitly granted actions,
or minutes per run. For a row whose acceptance depends on one:

- Reproduce only when safely possible within current authority and budget.
  Prefer the cheapest environment that can show the failure, such as an
  unprivileged local run on disposable fixtures. For unavailable environments,
  protected actions, exhausted attempt limits or non-reproducible incidents,
  record existing evidence and the reproduction limitation instead of forcing
  retries or inventing a failure. Required acceptance evidence and verification
  gates still apply; if missing, pause. Diagnostic runs are ordinary verification
  and never satisfy acceptance.
- Make each expensive run execute every case whose safety does not depend on an
  earlier result, and report all failures. Stop early only when continuing
  would be unsafe.
- Redaction protects real data. Raw diagnostics from synthetic, disposable
  fixtures may be kept in private, ignored artifact paths. Never commit them,
  and never treat them as evidence of effects, non-dispatch, retry eligibility,
  or authority.
- Each expensive run is one attempt. Persist the row's attempt count in its
  status notes; a session change does not reset it. Stop after three
  consecutive failed attempts at the same stage (or the limit the milestone
  or a human-approved goal budget sets), or when the failing stage lies outside
  the behavior the milestone owns. Run the fast preflight checks of the
  project's acceptance-readiness rule before each counted attempt.
  Mark the row `[!]` with a short diagnosis and options, such as a correction, a
  rescope or an environment change, and ask the user. Approval to continue sets
  a new explicit limit. Never repeat an unchanged failed attempt.

## Integrated closure review

The approved plan names the integrated-review owner, contributing milestones
and acceptance scope. If no integration milestone is planned, the stage or
goal's last milestone owns this review. This section defines that milestone's
review; the selected execution protocol owns cross-milestone sequencing.

Before the first contributing task, the execution owner records the scope,
contributor IDs and starting state in existing goal state or the review owner's
status notes. With Git, record the full HEAD commit and retain any initial staged
and unstaged diff and relevant untracked file contents, with hashes, in authorized
ignored scratch. Without Git, retain a snapshot of the in-scope sources and a
hashed manifest. Preserve unrelated user work and existing filesystem authority.
Reuse this baseline across resumes and child dispatch, including under
`COMMIT_POLICY: none`; do not replace it with the latest milestone's base.
On an already-started stage or goal, recover the original baseline when possible.
If it cannot be reconstructed, disclose the missing baseline and review the full
integrated implementation against acceptance. Do not claim historical diff
coverage or omit current implementation and acceptance review.

The owner's initial whole-milestone review uses the recorded stage/goal baseline
and final integrated state, including saved final diffs and relevant untracked
contents with hashes, or the corresponding unversioned snapshot. Use the ordinary
milestone reviewer arrangement. Require an independent read-only reviewer only
when the approved request, project policy or selected `MODEL_POLICY` requires
one. Otherwise the executor may perform the review in a separate read-only
phase. Missing explicitly required independence leaves the review pending.
Review across the full contributing scope, not only the owner's milestone diff,
for:

- an authorized recovery or completion path from each durable non-terminal
  state, discoverable from every interface that creates it;
- recovery at each identified persistence boundary and crash window;
- loading supported earlier state formats, or clear refusal with a recovery path;
- isolation of unrelated items from one item's failure;
- protection of other tasks' in-flight work from user actions.

Record evidence or justified non-applicability for each lens. Use the owning
milestone's existing severity rules, review counter and limit; fixes require
subsequent review. This does not reopen frozen records or create an additional
unbounded gate.

## Milestone review procedure

When the last open row in a milestone's status file closes as `[+]`, `[X]`, or
`[-]` during an agent session, perform the review before ending the turn and
before moving to the next milestone. A `[-]` row counts as closed only when its
notes identify the consumed attempt or supersession and its accepted successor:

1. Re-read the milestone scope and acceptance criteria here. Confirm the code or
   docs meet the acceptance line; do not rely on the status file alone.
2. Run the required verification before review, including proportionate checks
   for affected consumers and any applicable compatibility, migration,
   rollback, security, concurrency, or failure paths.
3. Run a bounded deep-review and fix gate using the review finding severity
   context above.
   - The initial deep-review pass is iteration 1. Read the persisted count and
     findings first. Record the iteration as started before review; resume an
     interrupted pass at that same number. Runtime round limits are separate.
     Pin the milestone's base commit, inspect the full diff including staged,
     unstaged and relevant untracked work under the commit policy, read the
     `git log` range, and in iteration 1 review the full milestone diff for correctness,
     regressions, failure semantics, boundary drift, stale docs, missing tests
     and test-policy compliance. Review acceptance fidelity separately: requirements missing or
     partial, behavior nobody asked for, and requirements implemented wrongly,
     each quoting its acceptance line. Record findings grouped by concern.
     For the designated integrated-review owner, iteration 1 also performs
     [Integrated closure review](#integrated-closure-review) across the recorded
     contributing scope and starting/final states. Its own milestone base alone
     is insufficient. Use the full-implementation fallback when that baseline
     cannot be reconstructed; keep this within the same iteration and limit.
     An empty implementation diff still needs acceptance review; do not
     manufacture changes. Lenses are coverage obligations: combine them or
     run batches within host capacity. When an interactive request selects
     `MODEL_POLICY`, follow the Goal/Next bundled model-policy reference for
     fresh read-only whole-milestone reviewers; the owner alone records results
     and fixes under `DEFAULT`. Absence preserves host model settings.
   - Record the iteration number and findings in the current status notes so a
     continuation cannot reset the counter. Record observed review start and end
     times here when available; unknown boundaries remain unknown. The gate
     passes only under the pass condition below. When blocking findings exist
     and the current iteration is below the approved review limit, fix every
     blocking finding in the current milestone, rerun affected verification, and
     begin the next iteration.
   - Iteration 2 and later review only each blocking finding of the previous
     iteration (is it fixed?), every change since the state the previous
     iteration reviewed, including non-blocking fixes, and the direct
     consumers of that changed code. Do not sweep the whole milestone again.
     Fresh reviewers receive the earlier findings and this narrowed scope.
     Record each iteration's reviewed state: the full `HEAD` commit ID and, when
     uncommitted work is in scope, a saved copy of the reviewed diff and its
     hash in ignored scratch. If that state cannot be reconstructed, review the
     full milestone diff instead. This holds under every commit policy.
   - A task review covers that task's diff (its own commit when commits are per
     task) and passes with no blocking finding.
     For a one-task milestone, one review may satisfy both task and
     whole-milestone review only when it covers the complete milestone scope and
     acceptance, required gates have passed, and all independence, model and
     reviewed-state requirements are met. Record it once as the milestone's
     initial iteration. Later fixes retain the normal verification and review
     requirements.
   - P2 and Lower findings never block on their own. For each one, choose to
     fix now when the fix is local, cheap and in scope, or when later work
     builds on the defect (a contract or interface, a persisted format such as
     a schema, ledger or wire format, a public API, or tests encoding the
     behavior); to carry it in [Open review findings](#open-review-findings); or,
     for Lower only, to decline with a one-line rationale.
   - Any change made in response to a review, blocking or not, is verified and
     reviewed by a later iteration before closure. Recording findings,
     dispositions, review counters, reviewed state, register rows and owner
     notes is not a review change; code, test, configuration and substantive
     documentation changes are. An iteration with only non-blocking findings
     ends one of two ways: (a) carry or decline them without changing code, and
     the gate passes; or (b) apply fix-now changes, rerun affected verification
     and run the next iteration over those changes, which counts toward the
     limit.
   - The gate passes with no blocking finding in scope, every earlier blocking
     finding fixed, and no unreviewed review change.
   - A carried P2 still unfixed when its fix owner's review, or a later
     iteration, examines it becomes blocking.
   - Resolve `REVIEW_MAX_ITERATIONS` from the human-approved interactive request,
     default 10, independently of commit policy. It must be a positive integer.
     Project caps use `REVIEW_MAX_ITERATIONS` in `tech-stack.md` verification
     standards; milestone caps use that field in the owning specification.
     Use the minimum applicable cap. Legacy fixed-cap prose remains binding
     until explicit human adoption; surface conflicts before dispatch. Persist the effective limit, approval source and counter; resumes,
     repairs and policy changes never reset them. Only explicit human approval
     can raise the ceiling; an extension preserves iterations already consumed.
     Python API execution retains its existing limit of 10.
   - Run at most `REVIEW_MAX_ITERATIONS` iterations (default 10); a session or reviewer change does not reset the
     counter. On the final allowed iteration make no further review change;
     carry every non-blocking finding, and one that later work builds on names
     that work as its fix owner, which fixes it before building on it. If a
     blocking finding remains, add `[!]` review rows recording the remaining
     findings and iteration-limit blocker. Do not start another automatic
     fix-review cycle or move downstream; stop and ask for user direction.
   - Carry a non-blocking finding forward only in the open review findings
     register, with its fix owner and rationale.
4. Reconcile the memory bank. Update `product.md` if the milestone changed
   product scope, domain terminology, concept relationships, or business
   invariants. Update `architecture.md` or `tech-stack.md` if it changed
   boundaries, dependencies, commands, data flow, or runtime assumptions.
   Then run an environment retro on the mistakes found during the milestone.
   Classify each first: a mechanical one that a linter, test, or CI check could
   catch becomes a proposed deterministic check; a judgement call becomes a
   lesson or a review rule. Also note a missing navigation pointer, missing
   access to needed information, or an instruction that changes nothing. Report
   these environment candidates, most severe first, for a later approved
   proposal; they never become unapproved rows.
5. Check `tabilet/evolution/`. Add the next `prompt-vN.md` and `result-vN.md` only when
   product direction, architecture boundary, milestone target, or public/private
   contract direction materially changes.
6. Revisit candidate directions affected by the milestone. Update their reason
   or trigger; when a trigger is now true, propose a reconciled milestone and
   obtain approval before allocating its permanent ID and status file.
7. After the gate passes, reconcile affected active downstream dependencies and
   acceptance against the delivered outcome. Then consolidate and retire under
   the procedure below. During an ordered goal, the goal protocol finishes its
   downstream reconciliation before performing this retirement step.
8. Check the retirement links and record, and run required verification again.
   Under a test policy, a class O gate may reuse its result when nothing it
   reads has changed since it passed; if that is unclear, rerun it. Class R checks
   follow their own authority. State a reuse in the retired record's
   `**Verification.**` when writing it; report a rerun made after freezing in the
   step 9 summary, never in the frozen record. Then commit substantive closure
   changes under the governing commit policy.
   Do not create an extra milestone commit when the review changes nothing.
9. Report a short review summary: what was verified, the review-fix iteration
   count, what memory-bank files changed, any review commit, and whether an
   evolution bump was made. Include the retired record and durable lessons.
   Distinguish elapsed span, command execution, review intervals, rework and
   owner waits, identifying overlaps and capture gaps. Do not add overlapping
   intervals or infer model work from unexplained elapsed time. Explain material
   estimate overruns without skipping checks or accepting unmet requirements.
   This requires no new ledger, recorder or audit opt-in.

## Long-term memory and retirement

This project retires a milestone automatically after closure. “Automatically”
means the agent performs this procedure during the milestone review workflow
above, including when using `memory-bank-next` or `memory-bank-goal`. There is
no background process or separate archive invocation. Individual completed,
cancelled, or closed-historical rows remain in their active status file until
the whole milestone qualifies; unresolved work or missing closure evidence
keeps it active. Terminal rows alone do not prove acceptance.

Existing projects adopt this contract explicitly, with a compatible API runner
if used; upgrading installed skills alone does not merge project instructions
or move files. An explicit cleanup request may retire older closed milestones
only when their closure evidence is available, either a recorded review under
this contract or the legacy closure described below.

### Consolidate before retiring

Keep current facts in product, architecture, and stack documents. Maintain
[lessons.md](lessons.md) for applicable lessons and decision rationale with
evidence links; merge duplicates and avoid a chronological session log. Maintain
relevant lessons during ordinary work, not only at closure, and keep them active
while applicable even after their supporting milestone retires. This removes
accumulated history from active context, not a fixed number of tokens or files;
genuinely active work and useful knowledge can still grow.

Before materially superseding or removing knowledge from those documents,
append the old wording to `tabilet/docs/history/knowledge.md`. Use a unique, descriptive
dated heading, the original document and heading, retirement reason, supporting
evidence, and a link to its replacement (or an explicit reason there is none).
Preserve the old excerpt in a fenced markdown block. This applies outside
milestones too. Create this journal only when needed, link it from the history
index, and append corrections rather than rewriting old entries. Routine edits
need no journal entry; Git, when present, holds intermediate revisions.

Consolidation is ordinary project maintenance. A separate context snapshot is
optional and never a prerequisite for retirement; the archive skill's clean
baseline rule must not force commits or interrupt a no-commit goal.

### Retire a closed milestone

1. Require a passed review within the persisted approved review limit, recorded
   verification, consolidated knowledge, and reconciled downstream work. No
   `[ ]`, `[~]`, or `[!]` row may remain. Every `[-]` row names its accepted
   successor. A cancelled or superseded milestone also needs an authorized
   disposition; it must not be described as delivered acceptance.
2. Create `tabilet/docs/history/status-<LANE><NN>.md` using the envelope below. Keep the
   full final specification and status document in separate literal markdown
   fences, including all task text, notes, acceptance, and review evidence.
   Choose fences longer than any fence in the source. Original relative paths
   inside these literal documents retain their source-document meaning.
3. Add one history index row using `Milestone | Outcome | Retired | Record |
   Summary`; the ID, outcome, date, and record link must match the envelope.
   Outcomes are `completed`, `cancelled`, or `superseded`. The record link is
   relative to the index, for example `[M01](status-M01.md)`.
4. Remove the active status file, specification section, and active index row.
   Before removal, validate every envelope field and compare both retained
   documents with their complete active sources. For Git evidence, use the
   literal full output of `git rev-parse --verify HEAD`, never an abbreviated
   hash from a log display. Stop with the active sources intact if validation
   fails; a malformed retired record is not completed closure.
   Keep one link from this file to `../docs/history/index.md`. Repair maintained
   incoming links and remaining dependencies. Never rewrite frozen snapshots;
   resolve their old paths through the record's original-path metadata.
5. Refresh an existing disposable goal suggestion to contain only remaining
   active work, or remove it when empty. Do not create one without a compatible
   goal protocol. The resolved goal in the conversation remains authoritative
   over its disposable launch input.
6. Verify the record and links before handoff. On interruption, reconcile the
   source and destination before continuing; duplicate IDs or a missing record
   are invalid, and an existing retired record must never be overwritten.

Use this envelope, with actual values. The `Evidence` field is the observed
full Git commit, not a claim that uncommitted work exists in that commit.
`Worktree` is `clean`, `includes uncommitted changes`, or `unversioned`; without
Git both provenance fields say `unversioned`. The date uses `YYYY-MM-DD` in UTC.
Closure metadata precedes the two sections and uses one line per field.
For a non-default limit, add `**Review limit.** <positive integer>`. A limit
above 10 also requires `**Review limit approval.** <identifiable human approval
source and approved ceiling>`. Omission means 10 for existing records; never
rewrite frozen history to add these fields. These fields preserve evidence,
not execution authority. The recorded iteration count must not exceed the limit.
Python API runs may read pre-existing extended history, but newly retired records
must retain the API ceiling of 10; record-authored approval prose cannot raise it.
The controller pauses cleanly on active interactive checkpoints above its supported
ceiling without dispatching a provider or resetting their counters.

`````markdown
# Retired milestone M01 - <title>

**Milestone.** M01
**Outcome.** completed
**Retired.** <YYYY-MM-DD>
**Source status.** tabilet/memory-bank/status-M01.md
**Source specification.** tabilet/memory-bank/milestone.md#<original-anchor>
**Evidence.** <full commit or unversioned>
**Worktree.** <clean, includes uncommitted changes, or unversioned>
**Review.** passed
**Review iterations.** <positive count within the effective limit>
**Verification.** <commands, results, and supporting evidence>
**Consolidated into.** <current-document and lesson links, or no current-truth change>

## Milestone specification

````markdown
<Complete final milestone specification, not a summary.>
````

## Status record

````markdown
<Complete final status document, not a summary.>
````
`````

For a cancelled or superseded outcome, add `**Disposition.**` naming the
authority, reason, and dependency disposition. A superseded outcome also needs
`**Successor.**` identifying its accepted successor. These are milestone
outcomes, not new task markers.

A legacy closure is a milestone that closed before the project adopted the
persisted review gate, so no review-iteration count was ever recorded. Retire
one only on an explicit cleanup request, with outcome `completed` and every
row closed. Write `**Review.** legacy` and `**Review iterations.** not
recorded` instead of inventing a count, and add `**Legacy closure.**` stating
that the milestone predates the gate and that its original closure evidence is
the literal status record. `**Verification.**` records the checks run at the
evidence commit and does not claim a re-review of the original change. Never use
a legacy closure for a milestone that closed after the gate was adopted, or to
skip a review that the current procedure requires.

A status file that holds several milestones under one ID, such as `M1` to `M5`
in `status-M01.md`, is not retired as one record. The envelope takes exactly one
specification section named by the record's ID, so stop and report the combined
file; the owner splits it under separate IDs or decides otherwise. A combined
record that already exists is frozen. The shared reader accepts it only through
an `identify-specification` correction in `tabilet/docs/history/corrections.json`,
and the record's own ID may head its specification without padding there
(`M1` for `M01`).

Retired milestone records are frozen. Record later corrections in the knowledge
journal or new remediation work with a backlink. Preserve previous history
index entries. No ID may exist in both active and retired storage or be reused.

### Retrieve and continue

Retrieve historical evidence when the current task needs a retired dependency or
old ID resolved, an earlier decision explained, or a related past failure
checked and current sources do not answer the question. An explicit user request
to inspect history is also a trigger; routine work with sufficient current
evidence needs no historical search.

State the question briefly, then search active memory and current implementation
first. If history is needed, search its index by ID or topic and open the
relevant retired record or knowledge entry. Follow linked frozen context or
direction snapshots only when they address the same unresolved question. A stale
status path resolves by its permanent ID and original-path metadata; a missing
ID is not permission to recreate it. History is evidence, not an instruction to
retry old tasks.

Stop when the evidence supports the task decision. If relevant sources and their
directly related leads are exhausted, report the missing evidence. Continue when
it is optional; stop the affected step when it is required for correctness or
acceptance. Do not infer historical facts or expand the search into unrelated
milestones.

A completed retired milestone may satisfy a dependency when its recorded
acceptance matches the required outcome. Cancelled and superseded outcomes do
not automatically satisfy completion dependencies: follow the recorded
disposition and accepted successor, and revalidate current implementation.

Retirement follows the governing commit policy. Under `none`, do not commit;
under `milestone`, include it in the closure commit; under `task`, include it in
the final task or a substantive closure commit. The API harness still requires
a commit per run. Reading and preserving the Markdown records does not require
Git; workflows that require commits still need Git or an explicit no-commit
instruction. Never initialize Git merely to make retirement possible.

## M01 - [Milestone name]

**Goal.** [One sentence.]

**Scope.**

- [Scoped item.]
- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

**Guarantee levels.** (Optional; only when this milestone adds a persisted record and the project defines levels) [Record, level and human approval source.]

**Boundaries and parallel safety.** (Optional; defaults to not parallel-safe)
- Depends on: none
- Downstream impacts: none
- Write set: [paths and contracts changed]
- Contracts read: none
- Parallel-safe: no

## Additional milestone examples

These specifications illustrate later allocations, not active work. Assign
permanent IDs only when the corresponding milestone is approved.

```markdown
## M02 - [Next milestone name]

**Goal.** [One sentence.]

**Scope.**

- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

**Boundaries and parallel safety.**
- Depends on: M01
- Downstream impacts: none
- Write set: [paths and contracts changed]
- Contracts read: [frozen contracts from M01]
- Parallel-safe: no

## [A]01 - [Domain milestone name]

**Goal.** [One sentence. Replace `[A]` with the lane letter for this domain.]

**Scope.**

- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

**Boundaries and parallel safety.**
- Depends on: M01
- Downstream impacts: none
- Write set: [domain paths and contracts changed]
- Contracts read: [frozen contracts from M01]
- Parallel-safe: yes — disjoint write set and frozen inputs
```

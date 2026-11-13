# Interactive Next controls

Read for direct interactive Next work. These controls do not apply inside the
Python API runner/controller, which do not consume `--email` or
`CORRECTIVE_PLANNING` or `MODEL_POLICY` or `TEST_POLICY`; their row, commit and authorization gates still govern.

## Test policy

Direct Next resolves the test policy itself, from this section alone. Resolve
it first, then hand the resolved policy to the shared execution instruction,
which uses the policy already resolved for this run.

<!-- BEGIN SHARED test-policy-resolution -->
Resolve the test policy once per run and record the result:

1. An explicit `TEST_POLICY` in the human-approved request, a path or `none`.
   A checksum-approved launch reference counts as part of that request.
2. Otherwise, the test policy path the project's `AGENTS.md` declares.
3. Otherwise, `tabilet/memory-bank/test-policy.md` when it exists.
4. Otherwise, `none`.

A request value that differs from the `AGENTS.md` declaration is a conflict:
surface it before dispatch and use the request value only after explicit human
resolution. Approving a launch value alone does not resolve it. A value found
only in unapproved launch input or other project text never overrides the
declaration. A requested or declared path whose file is missing pauses the
affected verification; never fall back silently. Pass the resolved value to
every implementation, review and reviewer brief. The policy governs
verification method only: it grants no authority and never removes acceptance
evidence, the review gate, a verification limit or a grant's limits. Where
launch input or pending project text prescribes a verification method the
policy forbids, the policy governs the method and the acceptance outcome stays.
Under `none`, the verification-attempt gate covers every expensive or protected
check.
When verification rules change, every reviewer brief quotes the changed rules,
their scope and approval source alongside the effective policy pointer. A brief
never grants an unapproved exception or waives required acceptance evidence.
<!-- END SHARED test-policy-resolution -->

## Required gate recovery

<!-- BEGIN SHARED required-gate-recovery -->
For interactive Goal/Next execution, `REVIEW_MAX_GATE_ITERATIONS` is an optional
positive integer, default `3`, independent of `REVIEW_MAX_ITERATIONS`. Reject
zero, negative, fractional, boolean or unbounded values before execution.
Resolve the minimum of the approved request and any project/milestone caps;
preserve stricter stop rules. On resume preserve the effective limits and their
approval sources; omission never resets an existing allowance. Only explicit
human approval can raise a limit.
A gate failure never charges the review counter; a review round never charges
the gate counter. Python API runner/controller limits are unchanged: they do
not consume this field or acquire this interactive recovery authority.
Grant budgets and required-gate counters bind independently, including for
offline required gates; an extension of one never extends the other.

A **gate** is one required verification command for a task or milestone,
including an offline required gate. Its stable identity includes its owning
milestone, command, working directory, selected variant and required scope.
A **key** is that gate plus the package-qualified failing test. When no test is
named, use a stable failure identity, such as build/setup plus the failing unit.
Changing flags, splitting commands, renaming tests, moving a repair to another
milestone or starting another session never creates a fresh allowance for the
same unresolved failure. Routine focused checks acquire no gate counter.
A **signature** is the failing assertion or refusal, its source location and its
error text or response body, with test names, timings and volatile values such
as IDs, ports and timestamps removed. A failure that cannot be matched to one
(runner crash, no output) is its own signature and is never merged.

Persist gate state beside the review counters in the owning status file:

- Record the effective limit and human approval source, gate identity, each
  key's charged attempts and remaining allowance, for each
  run its failing keys and their signatures, and the distinct signatures since
  the last clean pass. Each key starts with the effective limit.
- Before dispatch, persist an attempt ID as `started`, its input revision or
  saved diff/hash, command and any known key. This reserves the attempt; after
  failure charge one to every reported failing key, once per attempt ID. Record
  the result and evidence link. An observation-only diagnostic is not an
  attempt: it charges nothing and cannot reset the gate.
- Recover an interrupted `started` attempt before another dispatch. Reconcile
  its result once from retained evidence; if the result cannot be recovered,
  charge its known key conservatively. If its key or dispatch is uncertain,
  pause for the owner rather than discard the reservation or guess a pass.
- Stop for the owner when a key has zero remaining, or when the gate's distinct
  signatures reach the effective chain ceiling (default three) across
  consecutive runs without a clean pass. One gate run is one attempt: the chain
  is checked only when a rerun produces a signature not seen in earlier runs,
  never inside the run that produced several. Cases in one run that share a
  signature count once.
  Mark affected work `[!]` with diagnosis and options. No further attempt at an
  exhausted key starts without renewed human approval; approval to continue
  states a new explicit limit and retains usage. A higher per-key limit does
  not raise the chain ceiling.
  Continuing after a chain stop requires explicit owner approval of the named
  recovery and a new bounded chain ceiling, retaining all previously seen keys;
  persist that effective ceiling and its approval source beside the keys.
  Approval to fix a test alone does not reset the chain or permit another run.
  Exhaustion is an approval pause for the affected gate; keep the goal active,
  incomplete and resumable. Prepare a concrete LLM recovery proposal before
  asking: diagnosis and evidence, exact repair scope and edits, current usage,
  proposed new limits and remaining attempts, risks and any needed permissions.
  Persist the proposal and pending question in existing status notes. Continue
  independent authorized work where ordering and ownership permit. If none can
  proceed, wait for the owner's answer while retaining the goal and checkpoint.
  After actual human approval of the complete proposal, record the approval
  source and old/new limits, then resume the same goal and gate under existing
  launch-refresh rules. Preserve consumed attempts, chain history, waiter
  ceilings and all other grants and restrictions. A counter extension alone
  never approves a waiter-ceiling or permission change. No answer grants no
  approval; a denial leaves affected work blocked for a revised proposal.
- A clean pass of the complete required gate resets all its key and chain
  counters. Focused passes, cached results, diagnostics and waived/filtered
  failures cannot reset them. Retain failed evidence and waiter ceilings.
  Resume, compaction, new sessions, reviewers and repair handoffs never reset
  counters. Every resume summary reports gate limits, keys, remaining attempts,
  chain state and any started attempt beside the review counters.

Within the remaining budget and existing authority, continue without asking
for a same-scope fix of a defect established in the milestone's own changed
code. An observation-only diagnostic edits no file and changes no behavior,
assertion, guard, deadline, fixture or instrumentation; allow at most two per
finding between charged gate attempts. A row's own tests may be updated at row
time for behavior that row changes; that is not recovery. A rerun after a
diagnosed runner-setting error retains the original FAIL and follows the existing
verification-discrepancy rule; it still consumes applicable counters and grant budgets. Never repeat an
unchanged failed attempt hoping for a pass. The acceptance-readiness preflight
and every existing authorization reservation remain required where applicable.

Regardless of remaining budget, stop for the owner at the first occurrence of:

- a waiver or non-blocking P2 classification, unless the owner already wrote
  down an exact applicable pattern with its evidence and stop conditions;
- an edit outside the milestone's declared write set, unless an owner-written
  standing rule covers it. A file in an already-listed package or module
  directory that changes no public contract and overlaps no other active
  milestone's or running lease's write set is in scope: record it in status and
  the whole-review brief. A milestone that declares no write set is bounded by
  its specification's scope;
- a change to a product guard or production-code deadline, the deletion or
  skipping of an existing test, or any change that weakens a test: removing or
  loosening an assertion, relaxing a matcher, shrinking a fixture, or replacing
  a failing test with a new one. During recovery, an existing assertion or
  fixture may be updated without a stop only when the milestone specification
  or an approved repair row names the behavior change and the edit preserves
  coverage of retained behavior; cite that line in the status checkpoint. List
  each updated expectation in status and in the whole-review brief, where the
  whole review checks it. An update made after the whole review has passed is a
  review change and needs a later iteration. Required new tests and fixtures
  need no stop. Test waiters, budgets and added precondition waits follow the
  paragraphs below;
- a change to credential or ledger custody code, workers, pins or durable formats;
- a data race of unknown cause, either exhausted counter, missing authority or
  an exhausted independent grant budget.

These are gate-failure recovery rules; the ordinary review severity policy
still governs review findings. Corrective planning, a preset, a grant or a
remaining counter never waives these stops, required coverage or acceptance.

After any gate stop the run may start an independent read-only assessment
without asking. A fresh read-only reviewer, not the author of the failing
change, may read source, tests, logs and recorded outcomes; it runs no test or
other command, edits no file, adds no instrumentation and changes no counter,
guard, deadline or fixture. Record its findings in the status file and the
outcome record. It ends with a proposed correction (test-side, product-side or
neither), its write set and its rerun needs, each a separate owner decision, so
the stop remains, except the added precondition wait below. It charges no gate attempt or review round and renews no
capacity. An assessment that would need a run, an edit or instrumentation stops
for the owner.

A runner timeout may be corrected once per gate without an owner stop when
evidence shows the run was progressing rather than hung: tests still completing
at the kill, or a recorded elapsed time for the same gate and variant. Set it to
at most twice that expected runtime and within the `tech-stack.md` hard limits,
retain the original FAIL, and charge the rerun. A second raise, a value beyond
the hard limits, or a rerun that does not complete stops for the owner.

**Added precondition wait.** An edit that only adds a wait for an observable
precondition before a test's action (a control enabled, an element present),
within the project's existing default wait bound, is not a weakening and needs no
owner stop when the independent read-only assessment records the readiness gap
and that no product requirement promises the precondition immediately. It
changes no expected value, matcher, assertion, fixture or deadline, adds no wait
to an assertion itself and edits no production code. Charge the rerun, retain
the original FAIL, and list the edit in status and the whole-review brief. It
grants no attempt and is no ladder rung. Without that assessment, with a longer
bound, or for any other change, the stops above and the ladder apply.

**Test-side deadline doubling ladder.** Only a waiter or test budget in test
files qualifies. Before its first doubling, obtain an independent read-only
assessment establishing test synchronization rather than a product latency
contract. Record that assessment and measured completion after the expired
limit; no measured completion means a possible hang and an immediate owner
stop. The measured operation must complete within the proposed limit of the
selected step, a doubling or a recorded factor step.
For every increase, retain completion evidence from the current failing
occurrence after its current deadline and within that proposed limit;
old measurements never justify a later doubling. No product guard or production-code
deadline qualifies; a runner timeout follows its own rule above.

Before establishing `T` or increasing a waiter, consult `tech-stack.md`'s
**Test waiter ceiling references** and inspect matching active status records
and retired records through the history index. Match stable file/symbol
identity and rename/shared-helper lineage across milestones. Recover the
original value, cumulative doublings, latest ceiling, approvals and exact edits
into the current status checkpoint; never treat the current code value as a
fresh original just because the prior milestone retired. For a genuinely new
waiter, establish its first `T` only after checking for earlier ladder records.
Missing, conflicting or uncertain prior evidence pauses the increase for human
direction rather than resetting the ceiling.

When first recording or updating a waiter, maintain its stable identity and
aliases with links to the owning status evidence under **Test waiter ceiling
references** in `tech-stack.md`. Keep detailed edits and counters in status;
the maintained reference only makes that evidence discoverable. Before retiring
the owner, retarget the reference to the frozen record, verify it resolves and
retains the original value and cumulative ceiling, then remove the active
status file. Frozen records remain unchanged. These references survive passes,
milestone closure and later goal runs.

Track each waiter's original value `T`, current value, cumulative doublings,
measurement, assessment, exact edits and any explicit owner-approved ceiling
in the status file. Allow at most one doubling per charged gate attempt:
`T` to `2T`, `2T` to `4T`, `4T` to `8T`. Never exceed three cumulative doublings
or `8T`, even when the configured gate budget is larger; a fourth increase to
`16T` always stops for the owner. Never exceed an explicitly approved value
without fresh approval. Rerun the required gate after each permitted increase,
within its remaining budget. At zero remaining, prepare the recovery proposal
and request renewed human approval as above before another run, including after
a third failure. The ladder grants no automatic extra attempt; resume after
approval with the explicitly extended allowance and preserved usage. A gate
pass resets gate counters but never the waiter's original value or cumulative
ceiling; renamed or shared waiters retain their identity across gates and
sessions. An operation that does not complete within its proposed limit stops
as a possible hang. Do not split a shared budget or alter its fixture under
this exception.

**Measured instrumented factor.** `tech-stack.md` may record a human-approved
**Instrumented budget factor** `F`, at most `8`, for a named instrumented
command, with the plain and instrumented durations and the revision it was
measured at. An agent may propose it; reflection and corrective planning never
record or raise it. Where it is recorded, a qualifying waiter or test budget
that passes plain and expired under that command may take its increase for the
charged attempt as one factor step instead of a doubling: a value that covers
the measured completion and is at most `F` times its original value `T`, even
when that exceeds `2T`, with the completion prerequisite applied to that
value, used only in instrumented builds while the plain value stays unchanged. Every other
ladder rule applies to the step, including the assessment, the measured
completion, the possible-hang stop and the `8T` ceiling. Record it in the
waiter's exact edits as a factor step; it is that waiter's last self-approved
increase. The factor never applies to a runner timeout, a product guard or a
production deadline. With no recorded factor, or one that is unmeasured or
above `8`, only doublings apply.

List every self-approved increase with its exact edit in the status file and
the whole-review brief; the independent whole review checks each increase.
The initial failed gate attempt charges `3` to `2`: a measured `2.08s`
completion of a `2s` test waiter can justify `2s` to `4s` and one rerun without
an owner stop. If that rerun passes, gate counters reset while the waiter keeps
its recorded original `2s` value and first doubling. At default limits, three
failures of one key, or three distinct signatures across consecutive runs, pause affected
verification for a recovery proposal and renewed human approval before dispatch.
<!-- END SHARED required-gate-recovery -->

## Session continuity

Keep unresolved owner questions and affected work in existing status notes as
well as the conversation; use the findings register only for actual findings.
On resume or after a known context reset, read those notes and inspect queued
input when the host exposes it. Unsent or unanswered questions grant no approval;
retain the original scope and continue independent authorized work. Under a goal,
return questions to the owner instead of creating another shared-state writer.

## Model policy

When the human request or governing approved goal selects `MODEL_POLICY`, read
the bundled [model policy](model-policy.md) before work. Preserve the selected
role models and optional effort settings and check host capabilities. Ordinary task work and task
reviews use `DEFAULT`; each authoritative whole-milestone review uses fresh
read-only `WHOLE_MILESTONE_REVIEW` agents. Missing or unverifiable settings
pause affected work without silent fallback. Omission preserves host settings;
direct Next does not require adoption of a goal protocol to use this option.

## Approval email

Accept optional `--email ADDRESS` from the current human request. Read the
bundled [email reference](email-notifications.md) only when selected. Reject
missing, invalid or conflicting addresses. Materialize `NOTIFY_EMAIL` and
notification-only authority in the conversation, check the sender locally
before work, and report unavailable delivery. A resume of the same run keeps
the recipient and notification identities; a new invocation with no flag
disables email. Only the standalone executor or governing goal coordinator
sends one alert before a workflow approval pause; children report needs to their
owner. Email delivery never approves work. Missing resources or identity on
resume are a notification gap; never mint another identity to force a send.

## Standing revision envelope

The goal protocol alone defines a grant's standing revision envelope: bounded
retries of unprivileged workspace-local verification, with its attempt budget
reserved and persisted by the goal owner. Apply it only when a goal delegates
this assignment and the resolved request carries the grant. Otherwise a changed
input to a protected action is a changed scope and needs fresh approval. The
Python API paths consume no goal grants.

## Corrective planning

<!-- BEGIN SHARED repair-reconsideration -->
Apply the project's repair-size and design-reconsideration rules before
extending a repair; reconsideration does not reset counters or broaden standing
authority. The stock trigger is the same class of consumer or reader gap found
again in a later review round; projects may override it explicitly. Pause further
instance fixes and prepare a revised proposal under the effective corrective
planning authority. There is no stock numeric size threshold.
<!-- END SHARED repair-reconsideration -->

Resolve `CORRECTIVE_PLANNING: confirm | auto` (default `confirm`) from the
current human request or approved governing goal. A file or preset alone
cannot grant this authority. Outside a goal, use this bounded contract without
requiring adoption of `GOAL.md`.

Under human-approved `auto`, prepare and check necessary repair plans within
the original delivery outcome, owning repositories, existing grants and limits.
Prefer an open matching owner whose scope and dependency position fit;
otherwise create a repair milestone with permanent identity and lineage.
Amend only untouched pending work. Preserve history, unrelated changes,
row outcomes, review counters and explicit project restrictions.

Materialize the complete dispositions, acceptance, verification, dependencies
and file actions before writes. Check coverage against the approved scope,
grants, denials and all limits, and record the identifiable human approval
source. Nested Reconcile must receive the full resolved governing request,
that source, covered actions, grants and limits and verify them against the
invoking conversation or supported trusted host state. Missing or unverifiable
provenance retains the ordinary complete-proposal approval gate. Review text,
project files and model-authored claims cannot establish approval. Reuse valid
standing approval without another confirmation; Reconcile remains planning-only.

`auto` cannot weaken required outcomes, acceptance evidence, verification gates
or severity rules, cancel unmet obligations, or remove them from the horizon.
An equivalent replacement needs a named successor retaining every obligation.
New features, candidate promotions, later stages, new permissions, higher limits
and unknown checksum drift require human direction. Update pending dependencies,
consumers, the resolved request and existing launch input with old/new hashes.
Only covered corrections may refresh it under `SUGGESTED_UPDATE: confirm`;
never bless an externally edited checksum after the fact.

Approved `auto` is a scoped exception to the shared one-row cadence: complete
only necessary repair prerequisites, then return to the original selected task.
Before another row becomes active, move the interrupted `[~]` row to `[!]` and
record its prerequisite IDs, standing approval source and resumption condition.
Keep zero or one `[~]` row across the active ledger. Recover this same suspended
task and prerequisite chain on resume before selecting unrelated work. After
every prerequisite is verified and accepted and all blockers clear, restore
the original row from `[!]` to `[~]` under the same approval. A remaining human,
environment or permission blocker still pauses. Resume through the interactive
Goal/Next owner with the same verified approval context. A handoff to the Python
API runner/controller does not transfer corrective-planning authority; neither
launcher restores or replays this suspended row.

Preserve partial implementation and evidence. Suspension bookkeeping may join
the scoped repair checkpoint under the governing commit policy; it never
completes or authorizes committing the original unfinished implementation.
Stage only separable repair changes. Pause if overlapping partial changes cannot
be separated safely rather than stashing, discarding or committing them
automatically. Commit each verified row under the governing policy; commit-none
still means no commits. Count repair rows, commits and attempts against all
explicit limits; never reset or raise them. Do not select unrelated work.

Findings blocking under the originating gate's criteria remain attached to the
originating milestone's unresolved bounded review gate even when a repair
milestone owns implementation. After repair acceptance, run that gate's next
iteration with its existing iteration counter, scoped as the gate defines. The
repair milestone's own review cannot substitute for this pass or reset the
counter. Non-blocking findings follow the open review findings register. At the approved review limit, unresolved findings stop
further automatic repairs and require explicit human direction.

## Optional author self-check

When the human requests a self-check trial, the implementer checks applicable
integrated-state lenses, readers and consumers, changed assertions and
verification settings before review dispatch. Add a concise result and
unresolved concerns to the existing brief. This is not an independent review,
consumes no additional review iteration and replaces no required check. Compare
its observed cost and first-review findings before proposing permanent adoption.

## Optional discoveries

Resolve `OPTION_POLICY: confirm | ignore` from the current request or governing
goal, defaulting to `confirm`. Preserve it across resume and launch refreshes.
Follow [milestone families](milestone-families.md); a single Next invocation
does not implement optional work beyond its selected task merely because the
parent closes. Under `confirm`, propose one batch after parent closure and wait
for the owner's actual answer. Under `ignore`, leave the backlog alone.

For interactive review, resolve `REVIEW_MAX_ITERATIONS` as a positive integer,
default 10, independently of commit policy. Resolve the minimum of the approved
launch and project/milestone `REVIEW_MAX_ITERATIONS` caps. Treat legacy fixed-cap
prose as binding until explicit adoption; surface conflicts before execution.
A delegated Next uses its owner's
approved limit; standalone Next needs explicit human approval for an increase.
Preserve stricter project caps, the approval source and the persisted counter
across resumes and repairs. This field never changes Python API execution limits.

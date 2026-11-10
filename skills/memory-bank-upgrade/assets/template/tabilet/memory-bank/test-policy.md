# Test policy

Every test, check and qualification run in this project follows this file:
task rows, milestone reviews, goal runs and their briefs, and launch
references. It governs how tests are written, run and recorded. It grants no
authority: it never permits a live service, credentials, real user data, a
physical browser, external network access, downloads, privileged commands or
external mutations, and it never removes an authorization grant's limits.
Commands and time budgets live in [tech-stack.md](tech-stack.md);
project-specific choices go under [Project specifics](#project-specifics).

**Precedence.** This policy governs test method. Where a pending milestone
specification, status row, `tech-stack.md` text, launch input or brief
prescribes a method it forbids, such as a supervising controller or receipt
reader around class O tests, an UNKNOWN class O outcome, class O attempt
counters or a test runner in another language without approval, this policy
wins on method. The acceptance outcome stays and is shown through self-checking
tests. It never overrides acceptance requirements, an authorization grant's
limits or frozen records.

## Two classes of test

| Class | What it is | Rule |
|---|---|---|
| **O: offline** | Fakes, scripted providers, disposable stores, isolated loopback fixtures and local sandboxed workers; no credentials, no external network access | The default. Every rule below applies. |
| **R: real effect** | Touches a live service, real user data, credentials, a physical browser or real browser profile, typed human input, privileged operations, metered external quota or the external network | Never a default test. Needs separately named human authority; see [Class R runs](#class-r-runs). |

All development verification is class O unless a milestone specification names
a class R check and a human separately authorizes it. The line is whether a run
can have a real effect, not which tool it uses: a synthetic or headless browser
test on loopback fixtures with a throwaway profile is class O.

## Class O rules

1. **Tests check themselves.** Each test owns its deadline, waits for every
   child process it starts, cleans up what it created, and fails on a leak or
   overrun. The runner's exit status is the result. The runner timeout is a
   tight backstop, about twice the expected runtime and within the hard limits
   in `tech-stack.md`; never raise it to hide a slow or hung test. Do not wrap
   tests in external supervising controllers, receipt readers or proof chains;
   the project's existing test entry points are the runners.
2. **PASS or FAIL, never UNKNOWN.** A timeout, signal, crash, leak, setup error
   or runner parse error is a FAIL. Cleanup deletes the run's own temp root and
   labelled resources; remove a leftover only when its label or temp root shows
   the run owns it, and report anything else. Fix the cause and run again; this policy
   adds no human approval or disposition for that. Approvals that the effective
   authorization requires, such as fresh approval for a protected run whose
   input changed outside an approved envelope, still apply. Never rerun
   unchanged code hoping for a pass: a flaky test is a bug.
3. **Run whole units.** Required gates run whole packages, modules or project
   targets, not per-test cohorts that each get their own plan, approval or
   review. Rule 7 covers checks made while changing code, and rule 8 covers
   skipping a fixture under an instrumented variant.
4. **Review code, not test runs.** Task and milestone reviews cover product and
   test code together. No readiness review before a run; no separate review of
   a runner or harness fix.
5. **Light bookkeeping.** This policy adds no attempt counters, failure streaks
   or numeric allowances. For each required gate the status file records the
   command, the source revision or saved diff hash (and artifact identity when
   one is qualified), PASS or FAIL, the elapsed wall-clock time, and one link to
   a log kept in ignored scratch; a reused result says its inputs are unchanged
   and keeps its original time. Elapsed time is a measurement for planning, not
   an acceptance limit. No per-attempt narrative. **Authorization is separate:** when a run needs an explicit
   grant, that grant's scope, reservations, budget and stop conditions bind as
   the goal protocol states. An exhausted budget pauses the run for human
   direction even though the test is class O.
   For a harmless record or setting discrepancy, use the milestone's
   [verification discrepancy rule](milestone.md#review-finding-severity), retaining
   the actual result and required rerun. It never converts a FAIL into a PASS.
6. **Keep the safety defaults.** Offline and credential-free fixtures,
   disposable stores, loopback-only networking, required sandboxes, pinned
   artifacts and product limits stay mandatory wherever the project or a
   specification requires them. Where a specification requires actual
   qualification, use the real built artifact or binary, not a mock.
   Follow the project's verification-environment preflight; it adds no separate
   readiness review or approval gate.
7. **Focused checks and required gates.** While changing code, run the
   narrowest check that exercises the change, without race, sanitizer, coverage
   or other slow variants. Before marking a row done or starting a task review
   or re-review, run the row check: build or type-check the whole project where
   the toolchain has such a step, which catches a broken signature in a unit
   whose tests do not run, then the project's static checks and the affected
   whole units. A project whose full build is slow names a narrower step in
   `tech-stack.md`. Add direct consumers when the row changes a public
   contract, a persisted format or behavior its consumers rely on, and the UI
   check when it changes UI. When it changes concurrency, add the race check on
   units whose concurrent code changed and on consumers of a changed
   concurrency contract. This limits the row check, never a required gate; a
   consumer broken in some other way surfaces at the required gates.
   Concurrency triggers include threads, tasks, channels, locks, atomics, shared
   mutable state and job/cancellation lifecycles. Explain a race-check exclusion
   against the diff when concurrency-related changes or an applicable project
   trigger make that scope decision relevant. Unrelated changes need no separate
   non-trigger note. This never excuses a required race check. Sanitizers and
   other instrumented variants follow their own defect classes and project
   triggers; concurrency is not their universal trigger. Preserve required
   full instrumented integration gates and their reruns under this rule.
   Classify verification needs by the change's behavioral effect, not its file
   extension or line count. Prompts, instructions, contracts, safety rules and
   test evidence can change behavior even when represented as text. A reviewer
   checks the classification against the full diff. Reduced checks require an
   approved risk-scaled verification contract in `tech-stack.md`; it may tailor
   routine row checks only within the governing test policy and acceptance.
   Removing or replacing a required gate needs explicit human approval of that
   specific contract change and its replacement coverage, including any necessary
   policy or acceptance amendment. Classification alone never removes a required
   gate; a Stack entry alone grants no exception. Preserve the original failed
   results and every still-required gate.
   The row check is the row's focused verification and its evidence, with any
   red-then-green regression; earlier narrow runs are not evidence. Record it
   as rule 5 records a gate. It may use the toolchain's test cache unless a test
   depends on inputs the cache cannot see, such as a pinned external artifact;
   record a result served from the cache as cached.
   Prefer making an external artifact's identity part of inputs the toolchain
   actually tracks. Demonstrate native cache invalidation when that artifact
   changes before relying on cached row evidence; merely reading a file or
   recording its hash does not establish that property. Otherwise bypass the
   affected test-result cache. Required gates remain fresh.
   Run required gates immediately before the whole review, not after each edit
   or before each task review. Every gate run, rerun included, is fresh and not
   served from a test-result cache: when a gate command can be served from one,
   use the toolchain's option to bypass it. Compiler and dependency caches stay.
   Rerun them before a later iteration or closure
   only when something a gate reads has changed: code, tests, build or tool
   inputs, dependencies, a moved base, or the documents and data the gate
   itself checks.
   If it is unclear what a gate reads, rerun it.
   Record the state they passed on as the full `HEAD` commit ID, plus a saved
   diff and its hash for uncommitted work. When comparing states, ignore status
   and record bookkeeping unless a gate reads it. Run gates cheapest first.
   After a failure, finish the other cheap gates, fix with focused checks, then
   rerun the failed and affected gates and
   run any gate that was skipped before the review.
   Where a stage needs end-to-end qualification with real pinned artifacts, it
   is a required gate of the milestone that completes the stage, which depends
   on every other milestone in that stage. Rule 6 governs those artifacts, and
   any class R part keeps its own authority.
   Grants and class R runs are unchanged, and this adds no counters, budgets or
   approvals.
8. **Match the fixture to the variant.** A large capacity or maximum-size
   fixture may skip an instrumented variant (race, sanitizer, coverage) when
   all of these hold:
   - the same fixture still runs in a required gate without the variant;
   - the skip is written in the test with its reason, uses the toolchain's own
     skip mechanism, and is reported as skipped, never a silent filter;
   - anything the variant checks on the path the fixture exercises, such as
     concurrency, including work that grows with the fixture, has its own
     smaller test under the variant. A property that appears only at full size,
     such as memory safety at a size boundary, keeps the variant: no skip;
   - the skip is not added to get past a failure the variant reported. A
     timeout is a FAIL with a cause: confirm the time is instrumentation
     overhead before skipping.

   The gate still runs whole units; only the named fixture is skipped.

## Example risk tiers (not in force)

This table is a starting point for a project's own risk-scaled verification
contract. Nothing here applies until `tech-stack.md` records an approved contract
that adopts or edits it; classification alone never reduces a check. Tiers shape
only the routine row check. Every required gate stays required, and an unchanged
gate result may be reused as rule 7 allows.

| Change | Row check |
|---|---|
| Documentation prose, or status and record bookkeeping, that no toolchain reads | Static checks and the links or references it touches |
| Local behavior with no changed contract | The whole-project build, static checks, the affected units, and the UI check when it changes UI |
| A contract, persisted format, concurrency, safety rule or instruction that changes behavior | The full row check with direct consumers and the checks rule 7 adds for it |

Classify by behavioral effect, as rule 7 requires. Text inside a source file, such
as a comment, directive, pragma or string, is classed by what a toolchain does
with it, so it is at least the second tier when one reads it. When unsure, use
the higher tier.

## Instrumented timing diagnosis

Before a full instrumented pass, establish the applicable timing expectations
and any human-approved acceptance arrangement. A plain pass, measured expiry
of a product time guard on the failing branch, and no race or sanitizer report
together support an instrumentation-overhead diagnosis; they do not turn a
failed run into a pass. A P2 disposition applies to the diagnosed defect, never
to the failed gate result, and is possible only under an approved acceptance
arrangement that still proves required coverage. Every still-required gate must
pass before closure. A changed acceptance arrangement must explicitly identify
replacement evidence and any approved gate or policy change; retain the original
FAIL. Missing or unproven acceptance remains P1. Other class O failures follow
the ordinary fix-and-rerun rule; diagnosis adds no blanket owner-approval gate.

Specify how inconclusive diagnosis is handled before relying on a timing
disposition. If diagnosis does not reproduce the failure, record the original
failure and reproduction limitation; measured expiry on the failing branch has
not been established. Near-limit timing alone establishes neither cause nor
eligibility for an exception. Continue only under ordinary failure handling and
the approved stop rules.

Avoid speculative product optimization solely to fit instrumentation overhead.
Useful product optimizations still need causal evidence and normal review.
Instrumented-only guard scaling is a project-specific design option requiring
review and any necessary policy approval; keep shipped builds unchanged and
record residual coverage risks. Code after an expired guard was not exercised
under instrumentation. Neither scaling nor an absence of reports proves that
unexecuted code is safe, and fixture skips still obey rule 8.

Verify that concurrency and timeout knobs affect the selected tests before
relying on them. Measure instrumented runtimes rather than deriving their
timeouts from plain runs. Existing hard caps and authorization limits remain
binding; measurement does not authorize raising them.

## Capacity and unit size

These are recommendations, not gates. Numbers belong to each project, in
`tech-stack.md`.

- **Concurrency limits.** Run heavy instrumented targets serially on a shared
  host: isolated stores and ports do not isolate CPU. Plain targets may run in
  parallel. Record the measured reason for any limit in either direction; an
  unexplained serial setting is worth challenging.
  Measure the instrumented guard margin on an idle host before choosing a
  serial fallback: serialization cannot repair a guard that expires while idle.
- **Instrumentation scope.** When a profile shows that an instrumented run spends
  most of its time in third-party code, or a stock default applies, a project may
  exclude that code from instrumentation. Its own code stays fully instrumented
  and every test still runs. Record the saving, measured on first use, and what
  the exclusion can no longer detect in `tech-stack.md`. The milestone that
  completes a stage runs its instrumented gates without the exclusion. Never
  change an exclusion to get past a failure.
  In a goal run the options go in the `INSTRUMENTATION_SCOPE` launch field,
  pre-filled with the stock defaults, so the owner can edit or clear them before
  launch.
- **Test unit size.** When one unit's gate becomes slow or the unit has many
  importers, plan a split as its own milestone, and do not start it in the
  middle of a task. The project sets the threshold. Scoped checks only pay off
  when units are small. Keep test helpers near the domain they serve: a shared
  helper unit that many tests import invalidates their cached results on every
  edit.
  Use native per-test timing output when available, retaining it with the
  existing gate log. When a gate exceeds a project-set maintenance threshold,
  or performance is the milestone's purpose, summarize up to ten measured slow
  tests and distinguish overlapping test durations from gate wall time. Propose
  scoped maintenance without starting it automatically. Consider reusable
  immutable fixture preparation with isolated per-case mutable state, then safe
  parallelism; verify coverage and isolation remain intact.
- **Parallel tests.** Prefer tests that can run in parallel, each with its own
  disposable state. Note toolchain limits, such as tests that change the process
  environment.
  Before increasing parallelism, inspect time guards and contention,
  process-environment changes, mutable globals, fixed ports and shared observers.
  Isolate those resources or serialize the affected tests; immutable shared data
  does not itself require serialization. Measure plain and instrumented behavior
  separately. Instrumented-only guard scaling requires its existing review and
  approval conditions and cannot repair a plain-run contention failure. Treat
  exposed product concurrency defects as ordinary findings, not test noise.
- **Heavy fixtures.** Record the cost and owner of expensive qualification
  fixtures. When kept behind an opt-in qualification flag, name the required
  gate that enables it and retain smaller routine coverage. Never silently
  remove required coverage or use the flag to bypass a reported failure.
  An approved move of heavy matrices to qualification-only execution lists each
  fixture by name, its required gate and owner, and the smaller row coverage that
  remains. Review that mapping; names and blanket filters alone do not establish
  eligibility. Preserve whole-unit row checks and the approved qualification
  contract.

## Use the project's own toolchain

Tests are written and run in the language and toolchain of the code they test,
as declared in `tech-stack.md`. Anything that runs tests, judges their outcome
or produces test evidence uses that same toolchain.

- Another language in those roles needs explicit human approval recording the
  reason, the exact scope and why the declared toolchain cannot do the job.
  List approved exceptions under Project specifics.
- Committed scripts already listed in `tech-stack.md` keep their role;
  extending one or adding another needs the same approval.
- Uncommitted one-off helpers in any language may inspect results, such as
  counting log lines or hashing a file for a status record. They never decide
  PASS or FAIL, never wrap or supervise a run, and never stand in for a test.
- This is toolchain discipline, independent of class; it applies to O and R.
  Using the project's language does not make a supervising controller
  acceptable: the controller ban in class O rule 1 applies in every language.

## Class R runs

Each class R run needs a human's named authority, which also states how the run
is supervised. Supervise with standard tooling, such as the test framework's own
lifecycle, process groups and throwaway profiles, not custom controllers.
UNKNOWN is allowed only when a real external effect may remain, and only for
that run. Class R runs use the
[verification-attempt gate](milestone.md#verification-attempt-gate).

## When to stop and ask

Only when:

- a test would need class R behavior;
- a run needs authority it lacks, or a change falls outside an approved grant or
  its envelope;
- an authorization budget or limit is exhausted;
- a required tool or input is missing (never download it); or
- passing would require changing product scope, a security boundary or this
  policy.

## Reviewing against this policy

Apply the milestone's [tool-limit, verification-discrepancy and test-program
rules](milestone.md#review-finding-severity) and
[diagnosis guidance](milestone.md#diagnosis-before-repair). Review changed
assertions and coverage with the product; helper or tool ownership does not
excuse invalid evidence. Reviewer briefs quote changed verification rules with
their scope and approval source, alongside the effective policy pointer.

Reviewers report as findings: an external controller or receipt reader around
class O tests; an UNKNOWN class O outcome; per-run approvals or readiness
reviews that this policy does not require and no effective authorization
requires; class O attempt counters other than grant budgets; a required-gate
result reused after something the gate reads changed; a required gate served
from a test-result cache; an instrumented-variant skip that breaks a condition of rule 8; test runners or evidence
generators in another language without approval. Approvals,
reservations and conditions required by effective authorization are not
findings. A milestone cannot close on acceptance evidence that depends on the
prohibited machinery: that acceptance line is unproven, which is P1.

## Project specifics

- **Toolchain**: [Languages and the test entry points that run them.]
- **Row checks**: [Whole-project build or type-check, static checks and whole-unit test commands from tech-stack.md.]
- **Required gates**: [Whole-unit commands from tech-stack.md, run fresh, that closure requires.]
- **Stage qualification**: [End-to-end qualification with real pinned artifacts and the milestone that owns it, or "none".]
- **Class R checks**: [Named real-effect checks and owning milestones, or "none".]
- **Approved other-language tools**: [Tool, scope, approval source, reason, or "none".]

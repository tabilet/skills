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
   review. Rule 7 covers checks made while changing code.
4. **Review code, not test runs.** Task and milestone reviews cover product and
   test code together. No readiness review before a run; no separate review of
   a runner or harness fix.
5. **Light bookkeeping.** This policy adds no attempt counters, failure streaks
   or numeric allowances. For each required gate the status file records the
   command, the source revision or saved diff hash (and artifact identity when
   one is qualified), PASS or FAIL, and one link to a log kept in ignored
   scratch; a reused result says its inputs are unchanged. No per-attempt
   narrative. **Authorization is separate:** when a run needs an explicit
   grant, that grant's scope, reservations, budget and stop conditions bind as
   the goal protocol states. An exhausted budget pauses the run for human
   direction even though the test is class O.
6. **Keep the safety defaults.** Offline and credential-free fixtures,
   disposable stores, loopback-only networking, required sandboxes, pinned
   artifacts and product limits stay mandatory wherever the project or a
   specification requires them. Where a specification requires actual
   qualification, use the real built artifact or binary, not a mock.
7. **Focused checks and required gates.** While changing code, run the
   narrowest check that exercises the change, without race, sanitizer, coverage
   or other slow variants. Before marking a row done or starting a task review
   or re-review, run the affected whole units and their direct consumers, plus
   the race or UI check when the row changes concurrency or UI. That run
   is the row's focused verification and its evidence, with any red-then-green
   regression; earlier narrow runs are not evidence. Record it as rule 5 records
   a gate.
   Run required gates immediately before the whole review, not after each edit
   or before each task review. Rerun them before a later iteration or closure
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
   Grants and class R runs are unchanged, and this adds no counters, budgets or
   approvals.

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

Reviewers report as findings: an external controller or receipt reader around
class O tests; an UNKNOWN class O outcome; per-run approvals or readiness
reviews that this policy does not require and no effective authorization
requires; class O attempt counters other than grant budgets; a required-gate
result reused after something the gate reads changed; test runners or evidence
generators in another language without approval. Approvals,
reservations and conditions required by effective authorization are not
findings. A milestone cannot close on acceptance evidence that depends on the
prohibited machinery: that acceptance line is unproven, which is P1.

## Project specifics

- **Toolchain**: [Languages and the test entry points that run them.]
- **Required gates**: [Whole-unit commands from tech-stack.md that closure requires.]
- **Class R checks**: [Named real-effect checks and owning milestones, or "none".]
- **Approved other-language tools**: [Tool, scope, approval source, reason, or "none".]

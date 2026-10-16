# Verification and testing profiles

Read when a planning request selects a light `--test` profile or explicitly
changes an existing profile. These are planning defaults for generated
`tabilet/memory-bank/tech-stack.md`, not an automatic timeout implementation.

## Selection and precedence

- `standard` is Init's default when `--test` is omitted: record the project's
  commands and harnesses without adding these light-profile constraints.
- `browserlight`, `golight`, `rustlight`, `tslight`, `jslight` and `pythonlight`
  share the defaults below. Use the actual project commands and applicable
  checks; do not invent `make check`, race tests or UI checks for every project.
- Explicit user budgets and existing project constraints win. When Propose or
  Reconcile updates an existing project, an omitted selector preserves its
  current profile and budgets; it never silently resets them to `standard`.
  Changing an existing profile or acceptance requires the approved file actions.
- Known repository timings inform the proposed limits. Record unknown timings
  as estimates and measure them during authorized execution. A smaller tool,
  runner or authorization cap still wins; profiles grant no external action
  and never raise those caps.

## Shared light-profile defaults

Write a `Verification and testing standards` section containing the selected
profile, concrete commands, targets, hard limits and timing scope. Add the
matching `AGENTS.md` Hard Rules pointer to that section.

Include this execution guidance in the generated section: keep implementation
and focused verification together for each coherent behavior change. When
handoffs, repeated inspections, or fixture setup delay progress, consolidate
related work and reuse still-valid verification. Additional delegation or
repeated checks should resolve a concrete uncertainty or satisfy a required
gate. Preserve mandatory reviews, acceptance coverage, attempt records,
authority, and limits. This adds no per-edit reporting step.

| Check | Target | Hard limit | Cadence |
|---|---|---|---|
| Focused uncached tests | 30 seconds of test execution | 2 minutes per focused test package/batch | After the owning behavior changes |
| Full project regression command, such as `make check` | 15 minutes wall time | 20 minutes per invocation | Once per unchanged milestone closure candidate |
| Applicable race/concurrency or offline UI checks | 2 minutes | 5 minutes per invocation | Changed concurrency/UI and required closure |

The 30-second target is not a hard limit on the entire repository. Account for
one-time compilation separately from uncached test execution. Declare a
wall-clock bound for complete commands where the runner supports it; a native
test timeout may cover only one test process, not compilation or a multi-package
command. For Go, use `go test -count=1 -timeout=2m` for focused packages and
`go test -race -count=1 -timeout=5m` for affected races, plus an appropriate
existing command bound when needed. Do not build a supervisor daemon for that.

A target miss calls for diagnosis. A hard-limit failure is recorded; do not
repeat unchanged input. Apply the project's bounded verification-attempt gate
when a check is expensive or protected. Reuse valid results across interruptions;
repeat full regression only for changed code, failed checks or unresolved
coverage. Required closure checks are not waived.

## Lightweight harness boundaries

- Intermediate browser/target interactions use offline synthetic loopback
  mocks, in-memory providers and mock interfaces. Mocked host witnesses prove
  contracts, never physical containment or real browser behavior.
- No X11/Xvfb, custom Python/Bash/external supervisor daemon, kernel process
  debugging or multi-GB disk snapshots in routine verification. This concerns
  test harnesses, not required production isolation. Small automatically cleaned
  temporary files are allowed for real persistence/custody tests. Reuse existing
  compiler/module caches instead of copying repositories, images or caches per row.
- Preserve existing offline UI/component checks and exact dependencies. Do not
  add a mocking library or tool dependency just because an example names one.
  Missing cached inputs pause the affected offline check; no automatic download.
- Put physical browser/end-to-end qualification at a named final release gate,
  with a minimal consolidated workload, readiness, bounds and authorization.
  Preserve required coverage and hand off intermediate case checklists. When
  changing an existing plan, explicitly approve the ownership rescope rather
  than deleting required physical evidence. One final gate means one successful
  consolidated pass; failed passes remain failures and any corrected successor
  follows the existing attempt and authorization rules.

## Language-specific fixtures

- `browserlight`: use the project's existing language and test framework.
- `golight`: Go-native `net/http/httptest.Server` / `NewTLSServer`, in-memory
  interfaces, `t.TempDir()` and standard contexts/`os/exec.CommandContext` when
  an offline CLI child is necessary. Prefer CGO off where the project permits;
  race tests may need CGO and the existing supported C toolchain. Do not disable
  required race coverage to keep CGO off.
- `rustlight`: Rust-native mocks, such as existing `wiremock`/`mockito`,
  `tempfile::tempdir` and `tokio::process`.
- `tslight` / `jslight`: existing TypeScript/JavaScript stubs, such as `msw`/`nock`,
  in-memory providers, fake timers and offline DOM/component tests.
- `pythonlight`: existing Python stubs, such as `responses`/`aioresponses`,
  `tmp_path` and opt-in e2e markers excluded from routine loops.

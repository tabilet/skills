# Verification and testing profiles

Read when a planning request selects a light `--test` profile or explicitly
changes an existing profile. These are planning defaults for generated
`tabilet/memory-bank/tech-stack.md`, not an automatic timeout implementation.

## Selection and precedence

- `standard` is Init's default when `--test` is omitted: record the project's
  commands and harnesses without adding these light-profile constraints.
- `browserlight`, `golight`, `rustlight`, `tslight`, `jslight` and `pythonlight`
  share the defaults below. Use the actual project commands and applicable
  checks; do not invent a full-suite command, race tests or UI checks for every project.
- Explicit user budgets and existing project constraints win. When Propose or
  Reconcile updates an existing project, an omitted selector preserves its
  current profile and budgets; it never silently resets them to `standard`.
  Changing an existing profile or acceptance requires the approved file actions.
- Known repository timings inform the proposed limits. Record unknown timings
  as estimates and measure them during authorized execution. A smaller tool,
  runner or authorization cap still wins; profiles grant no external action
  and never raise those caps.

## Stock test-policy preflight

For a project adopting the stock test policy, include this common preflight in
its verification standards independently of the selected testing profile:

<!-- BEGIN SHARED verification-environment-preflight -->
`standard` adds no light-profile constraints. Independently adopted stock
test-policy requirements, including this environment preflight, apply under
every profile.

Before costly verification, inspect the applicable toolchain pin, required
offline caches, private temporary-path suitability and permissions, umask, disk
capacity and selected concurrency. Check inherited environment and configuration
precedence that could override offline or isolation settings. Use invocation-local
corrections or refuse an unsafe setup; do not change global configuration, expose
secrets, download missing inputs or broaden authority. Reuse the check while
relevant environment inputs remain unchanged. Preserve the existing preflight
before every counted protected attempt.
<!-- END SHARED verification-environment-preflight -->

## Shared light-profile defaults

Write a `Verification and testing standards` section containing the selected
profile, concrete commands, targets, hard limits and timing scope. Add the
matching `AGENTS.md` Hard Rules pointer to that section.

The section replaces every square-bracketed template line with final text and no
brackets: use the project's real commands and limits, and keep the stock
`Execution cadence`, `Replacement coverage` and `Acceptance readiness` rules as
plain, unbracketed text. A bracketed line left in a generated section is an
unfilled placeholder.

Keep `Risk-scaled verification contract`, `Milestone time estimates`, `Gate
maintenance threshold` and `Instrumented budget factor` in the generated
standards, using approved project values or `none`. A light profile does not
itself approve reduced gates, set a milestone time estimate or record an
instrumented budget factor.

Include this execution guidance in the generated section: keep implementation
and focused verification together for each coherent behavior change. When
handoffs, repeated inspections, or fixture setup delay progress, consolidate
related work and reuse still-valid verification. Additional delegation or
repeated checks should resolve a concrete uncertainty or satisfy a required
gate. Preserve mandatory reviews, acceptance coverage, grant budgets and class R
attempt records, authority, and limits. This adds no per-edit reporting step.
When the project has adopted a test policy (`test-policy.md`), it applies to
every profile; a project without one keeps its existing expensive-check and
attempt-gate rules unchanged.

| Check | Target | Hard limit | Cadence |
|---|---|---|---|
| Focused uncached tests | 30 seconds of test execution | 2 minutes per focused test package/batch | After the owning behavior changes |
| Full project regression command, such as the project's single check target | 15 minutes wall time | 20 minutes per invocation | Once per unchanged milestone closure candidate |
| Applicable race/concurrency or offline UI checks | 2 minutes | 5 minutes per invocation | Changed concurrency/UI and required closure |

The 30-second target is not a hard limit on the entire repository. Account for
one-time compilation separately from uncached test execution. Declare a
wall-clock bound for complete commands where the runner supports it; a native
test timeout may cover only one test process, not compilation or a multi-package
command. Use the language's own timeout controls for focused packages and affected
races, plus an appropriate existing command bound when needed. See the language
fixtures below for examples. Under an adopted test policy, tests check
themselves; add no external controllers or receipt readers for that.

A target miss calls for diagnosis. A hard-limit miss is a FAIL: diagnose it and
never repeat unchanged input. Under an adopted test policy, only a class R check
uses the project's bounded verification-attempt gate; without one, apply that gate
to every expensive or protected check as before. Reuse valid results across interruptions;
repeat full regression only for changed code, failed checks or unresolved
coverage. Required closure checks are not waived.

## Lightweight harness boundaries

- Intermediate browser/target interactions use offline synthetic loopback
  mocks, in-memory providers and mock interfaces. Mocked host witnesses prove
  contracts, never physical containment or real browser behavior.
- No X11/Xvfb, external controllers or receipt readers around tests, kernel
  process debugging or multi-GB disk snapshots in routine verification. This concerns
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
  an offline CLI child is necessary. Use `go test -timeout=2m` for focused
  packages and `go test -race -timeout=5m` for affected races, adding `-count=1`
  for required gates and for tests whose inputs the cache cannot see. A row check
  is `go build ./...`, then `go vet` and `go test -timeout=2m` on the changed
  packages, plus direct consumers when a public contract, persisted format or
  relied-upon behavior changed, adding `go test -race -timeout=5m` when concurrent
  code or a concurrency contract changed. A rule 8 fixture skip uses `t.Skip` with
  its reason, run with `-v` so the log reports the skip.
  Prefer CGO off where the project permits;
  race tests may need CGO and the existing supported C toolchain. Do not disable
  required race coverage to keep CGO off.
  Under the policy's instrumentation-scope advice,
  `-gcflags='<dep pattern>=-d=checkptr=0 -race=false'` excludes third-party
  modules only and leaves the project's own code under race. Overriding `-race`
  per package is not a documented feature. It was measured on Go 1.26.6, so
  recheck the build and the saving after each toolchain update.
- `rustlight`: Rust-native mocks, such as existing `wiremock`/`mockito`,
  `tempfile::tempdir` and `tokio::process`.
- `tslight` / `jslight`: existing TypeScript/JavaScript stubs, such as `msw`/`nock`,
  in-memory providers, fake timers and offline DOM/component tests.
- `pythonlight`: existing Python stubs, such as `responses`/`aioresponses`,
  `tmp_path` and opt-in e2e markers excluded from routine loops.

## Instrumentation scope defaults

Planning pre-fills these defaults for the project's tools into the
`INSTRUMENTATION_SCOPE` field of `suggested.txt`, and the owner can edit or clear
them before launch.
Only the Go row has been measured; the others come from each tool's documentation.

| Language and tool | Default | Warning |
|---|---|---|
| Go race | The `golight` `-gcflags` form, for third-party modules | Recheck after each toolchain update |
| C/C++ ASan, UBSan (Clang) | `-fsanitize-ignorelist=<file>` with `src:` or `fun:` entries for third-party code | A partly instrumented ASan binary can report false container overflows |
| C/C++ TSan | No exclusion | TSan generally requires all code to be instrumented. Ignored functions can cause false positives from missed synchronization, and it may miss races |
| C/C++ MSan | No exclusion | All program code and libraries must be instrumented, or reports can be false |
| C/C++ with GCC | No exclusion | GCC's instrumentation options list no ignorelist equivalent |
| Rust sanitizers | No exclusion | Sanitizers are unstable `-Z` options with no documented per-crate exclusion. `[profile.dev.package."*"] opt-level = 2` in the root manifest speeds dependencies but does not change instrumentation |
| Python coverage | coverage.py `--source=<package>` or pytest-cov `--cov=<package>` | Code outside the named package is not measured |
| JS/TS coverage | Keep the tool's default | Jest skips `/node_modules/` by default. Check what Vitest reports before setting `coverage.include` |
| Java JaCoCo | Keep the default, all classes | Agent `includes` and `excludes` change what is analyzed. Report exclusions are set separately |

**A project's own option.** A project may pass its own option instead of the
default, including where the table says "No exclusion". Record the default, the
project's option, the measured saving and what the option can no longer detect in
`tech-stack.md`. A proposal that departs from the default says so as a warning.

**Filling the field.** Fill it only in a new launch proposal; a refresh of any existing
launch, including an unapproved draft, keeps its resolved value, including an
implicit `none`. Write one `<tool> = <option>` line for each tool the
project uses that has a concrete default. Resolve the placeholder from a profile if there
is one, otherwise from the project's dependencies. Leave out a tool whose default
is no exclusion or the tool's own default, and a tool with no target to name. If
nothing remains, the field is `none`. An exclusion gives up some detection, so show
each pre-filled option with its warning and say when it is unmeasured in this
project.

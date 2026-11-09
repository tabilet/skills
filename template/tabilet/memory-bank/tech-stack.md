# Tech Stack

## Language and runtime

- **Language/runtime**: [version or range].
- **Platform**: [server/library/CLI/browser/mobile/etc.].

## Direct dependencies

| Module | Version | Role |
|---|---|---|
| `[dependency]` | `[version]` | [Role.] |
| `[dependency]` | `[version]` | [Role.] |

## Dependency rules

- Prefer the language's native core/standard library before adding dependencies
  or project-local helpers. Use core packages and built-ins directly when they
  fit, and keep trivial comparisons or transformations inline when that is
  clearer than introducing a wrapper abstraction.
- Add third-party dependencies only when the core library does not provide a
  reasonable, maintainable solution for the project requirement.

## Common commands

```bash
# Build
[build command]

# Test
[test command]

# Lint / vet
[lint command]

# Format
[format command]
```

## Runtime assumptions

- [Required service, sibling checkout, environment variable, or tool.]
- [Required generated artifact or external system.]

## Execution harnesses

| Harness | Command | What it proves | Requirements |
|---|---|---|---|
| Unit tests | `[test command]` | [Fast local correctness.] | [Runtime/tool.] |
| Integration tests | `[integration command]` | [Behavior with real services.] | [Docker/service/env.] |

## Verification and testing standards

- **Test policy**: every test follows [test-policy.md](test-policy.md); this section holds the commands and limits it refers to.
- **Testing profile**: `[standard | browserlight | golight | rustlight | tslight | jslight | pythonlight]`.
- **Risk-scaled verification contract**: [project contract, default none].
- **Focused tests**: [Command, target and hard limit; light-profile default: 30-second target / 2-minute cap].
- **Row checks**: [Whole-project build or type-check, static checks and affected whole-unit test commands, or the narrower step a slow build uses].
- **Full regression**: [Project command and wall-clock limit; light-profile default: 20-minute cap].
- **Race/UI checks**: [Applicable commands and limits; light-profile default: 5 minutes per invocation].
- **Stage qualification**: [End-to-end qualification command with real pinned artifacts and its owning milestone, or "none"].
- **Timing and repetition**: [Separate one-time compilation from uncached test execution; run full regression once per unchanged closure candidate, repeating only for changes, failures or unresolved coverage].
- **Milestone time estimates**: [Optional advisory estimates, their measurement basis and timing scope; default none. These do not alter execution limits or acceptance].
- **Gate maintenance threshold**: [Project-specific timing threshold and measurement conditions, or none].
- **Budget precedence**: [Explicit project limits and smaller tool/authorization caps win; standard adds no extra constraints].
- **Harness boundaries**: [e.g., Use in-memory/loopback mocks; no external supervisor daemons or multi-GB disk snapshots; defer physical/browser e2e to final release smoke tests].
- **Execution cadence**: [Run the row check before a row is done or a task review; run the full suite fresh once per unchanged closure candidate and race/UI checks when the change touches concurrency or UI and at required closure; rerun the affected checks after every review fix].
- **Replacement coverage**: [When retiring an implementation, preserve meaningful success and failure coverage for retained behavior through its successor; remove a test only once its behavior has moved or been removed].
- **Acceptance readiness**: [Identify missing final-acceptance inputs, capabilities and authority early; run a fast preflight of fixtures, schemas and launchers before each counted attempt of a check that uses the verification-attempt gate].

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

## Model eval harnesses

| Eval | Command | What it measures | Requirements |
|---|---|---|---|
| Prompt regression | `[eval command]` | [Quality against golden cases.] | [Model/provider/key.] |
| Candidate comparison | `[eval command]` | [Baseline vs candidate score.] | [Dataset/grader/model.] |

## CI and tooling

- [CI workflow location.]
- [Required local tools.]
- [Generated files and regeneration command, if any.]

## Recovering project history

Search current memory first. For retired tasks, look up the permanent milestone
ID in `tabilet/docs/history/index.md`, then read its full specification and status
record. Superseded lessons and facts live in `tabilet/docs/history/knowledge.md`. Those
records remain readable without Git; their literal excerpts use original paths.
The history index links the knowledge journal when present. Search by ID or
topic and open only relevant records, not all historical documents on each run.
An old task is evidence, not an instruction to retry it; revalidate historical
knowledge against the current implementation before using it.

When Git exists, use it for intermediate edits and exact prior file versions:

```bash
git log --follow -- tabilet/docs/history/status-A03.md
git log --all -- tabilet/memory-bank/status-A03.md tabilet/docs/history/status-A03.md
git log -S 'phrase from the old knowledge' -- memory-bank docs/history
```

Retirement combines two documents, so rename detection by `--follow` is only a
convenience. Use both original and retired paths when it cannot follow the move.

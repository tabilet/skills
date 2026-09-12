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
ID in `docs/history/index.md`, then read its full specification and status
record. Superseded lessons and facts live in `docs/history/knowledge.md`. Those
records remain readable without Git; their literal excerpts use original paths.
The history index links the knowledge journal when present. Search by ID or
topic and open only relevant records, not all historical documents on each run.
An old task is evidence, not an instruction to retry it; revalidate historical
knowledge against the current implementation before using it.

When Git exists, use it for intermediate edits and exact prior file versions:

```bash
git log --follow -- docs/history/status-A03.md
git log --all -- memory-bank/status-A03.md docs/history/status-A03.md
git log -S 'phrase from the old knowledge' -- memory-bank docs/history
```

Retirement combines two documents, so rename detection by `--follow` is only a
convenience. Use both original and retired paths when it cannot follow the move.

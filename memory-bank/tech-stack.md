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

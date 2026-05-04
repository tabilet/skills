# Tech Stack

## Language and runtime

- **Language/runtime**: [version or range].
- **Platform**: [server/library/CLI/browser/mobile/etc.].

## Direct dependencies

| Module | Version | Role |
|---|---|---|
| `[dependency]` | `[version]` | [Role.] |
| `[dependency]` | `[version]` | [Role.] |

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

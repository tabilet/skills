# Architecture

## Layout

| Path | Role |
|---|---|
| `[path]/` | [Role.] |
| `[path]/` | [Role.] |
| `docs/` | Long-form reference documentation. |
| `memory-bank/` | Project memory and milestone state. |
| `evolution/` | Versioned direction snapshots. |
| `[evals path]/` | [Datasets, prompts, graders, reports, if applicable.] |

## Data flow

```text
[input/source]
      |
      v
[module/component]
      |
      v
[output/result]
```

## Ownership boundary

`[project-name]` owns:

- [Owned technical surface.]
- [Owned technical surface.]

`[project-name]` does not own:

- [External or sibling responsibility.]
- [External or sibling responsibility.]

## Public contracts

- [Public API, CLI, file format, protocol, or behavior.]
- [Consumer or compatibility note.]

## Harnesses

- Execution harnesses: [Where commands, scripts, containers, fixtures, or CI
  jobs live.]
- Model eval harnesses: [Where datasets, prompts, graders, baselines, reports,
  or eval runners live.]

## Risky change workflow

For changes to [risky area]:

1. [Required step.]
2. [Required step.]
3. [Required verification.]

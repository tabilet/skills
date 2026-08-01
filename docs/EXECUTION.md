# Execution Harness

An execution harness is the repeatable way to run a project under conditions
that matter. It is usually a program, script, test target, Docker Compose file,
or CI job.

Markdown does not execute the harness. Markdown tells humans and agents how to
run it, what services it starts, what evidence it produces, and which failures
are known or expected.

## Examples

- A `make test` target that runs all unit tests.
- A `make integration` target that starts PostgreSQL and MySQL containers, runs
  database tests, then stops the containers.
- A Go test package that uses `testcontainers-go` to launch real services.
- A script that builds a CLI, runs it against fixture inputs, and diffs the
  generated output.
- A CI workflow that runs the same commands on every pull request.

## Where It Fits

- `AGENTS.md` lists the essential harness commands agents should run.
- `memory-bank/tech-stack.md` records prerequisites, environment variables,
  Docker images, ports, and command names.
- `docs/` holds long-form setup, teardown, and troubleshooting notes.
- `memory-bank/milestone.md` can make a harness pass part of acceptance.
- The matching `memory-bank/status-<LANE><NN>.md` file records whether
  harness-related rows are pending, complete, blocked, or cancelled.

## Agent Execution Harness

The included [harness/tackle-memory-bank-api-loop](../harness/tackle-memory-bank-api-loop)
is an agent execution harness.

It:

- calls an OpenAI-compatible chat-completions API, or the Anthropic Messages
  API when `LLM_PROVIDER=anthropic`,
- embeds the memory-bank task instruction directly in the API call,
- gives the model a shell command protocol,
- discovers every `memory-bank/status-<LANE><NN>.md` lane file and reports each
  lane's actionable and blocked row counts to the model,
- stops when no actionable rows remain in any lane,
- warns about blocked rows, and stops for human review when only blocked rows
  remain,
- checks for a clean git worktree before each run,
- requires the model to commit its work,
- stops if the model leaves uncommitted changes,
- stops if the model makes no commit,
- limits the number of loop iterations.

### Exit Codes

The harness signals every outcome through its exit code. Codes 3 through 7 are
normal stopping conditions, not crashes: they mean the loop deliberately handed
control back to a human.

| Code | Meaning |
|---|---|
| `0` | No actionable rows remain. Nothing to do. |
| `2` | `LLM_MODEL` is unset, or `LLM_PROVIDER` is not `openai`/`anthropic`. |
| `3` | Only blocked rows remain. A human needs to unblock them. |
| `4` | The worktree was dirty before a run. Commit or stash first. |
| `5` | The agent left uncommitted changes. |
| `6` | The agent made no commit. Stops a spin loop. |
| `7` | `MAX_RUNS` was reached. |
| `10` | No `AGENTS.md` in the target repository. |
| `11` | No `memory-bank/`, or no `status-<LANE><NN>.md` lane files in it. |
| `12` | The target path is not inside a git worktree. |
| `13` | Git `HEAD` could not be read. |
| `20` | The API returned an HTTP error. |
| `21` | The API could not be reached. |
| `22` | The API response did not match the expected shape. |
| `30` | The model used `MAX_TURNS` without finishing a row. |

Codes `10` through `13` mean the target repository is not set up yet. Codes
`20` through `22` are provider or network problems, not project problems.

## Docker-Backed Services

For tests that need services such as MySQL or PostgreSQL, prefer disposable
containers over required local service installs.

Typical flow:

1. Start service containers with Docker Compose, `testcontainers`, or a harness
   script.
2. Wait until health checks pass.
3. Run the integration tests.
4. Collect logs on failure.
5. Stop and remove containers.

This keeps local developer machines and CI environments closer to each other.

## Documenting A Harness

For each execution harness, record:

- command,
- scenario,
- required services,
- environment variables,
- fixture or seed data,
- expected passing output,
- artifact and log locations,
- CI job name,
- known limitations or blocked rows.

The active command list belongs in `memory-bank/tech-stack.md`. Longer
operational details belong in `docs/`.

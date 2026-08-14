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
- refuses actionable work until the user acknowledges that model commands run
  in an unsandboxed host shell,
- passes a minimal environment to shell commands and requires explicit opt-in
  for additional project variables,
- requires the target path to be the git worktree root,
- checks for a clean git worktree before each run,
- requires the model to commit exactly one completed or blocked actionable row,
- permits separate review commits but rejects history rewrites,
- stops if the model leaves uncommitted changes,
- stops if the model makes no commit,
- retries transient API failures, reports provider usage, and limits loop turns
  and conversation size.

`ALLOW_UNSANDBOXED_SHELL=1` or `--allow-unsandboxed-shell` acknowledges host
access; it does not create isolation. Commands can read host files and processes
and use the network. Run the harness inside a disposable sandbox against a
repository you can restore. Provider credentials are not copied into the child
environment, and extra project variables require `TOOL_ENV_ALLOW`, but neither
measure turns the host shell into a security boundary. The dangerous-command
denylist is only a bypassable guardrail.

Operational limits are configurable with `LLM_API_TIMEOUT` (default `120`
seconds), `LLM_MAX_RETRIES` (default `2` retries after the first attempt), and
`MAX_HISTORY_CHARS` (default `500000`). `MAX_TOOL_OUTPUT` remains the combined
stdout/stderr character budget for each command.

### Exit Codes

The harness signals every outcome through its exit code. Codes 3 through 7 are
normal stopping conditions, not crashes: they mean the loop deliberately handed
control back to a human.

| Code | Meaning |
|---|---|
| `0` | No actionable rows remain. Nothing to do. |
| `1` | An unexpected internal harness failure occurred. |
| `2` | `LLM_MODEL` is unset, or `LLM_PROVIDER` is not `openai`/`anthropic`. |
| `3` | Only blocked rows remain. A human needs to unblock them. |
| `4` | The worktree was dirty before a run. Commit or stash first. |
| `5` | The agent left uncommitted changes. |
| `6` | The agent made no commit. Stops a spin loop. |
| `7` | `MAX_RUNS` was reached. |
| `8` | The committed result did not contain exactly one valid row transition. |
| `9` | The agent rewrote history or moved away from the original branch. |
| `10` | No `AGENTS.md` in the target repository. |
| `11` | No `memory-bank/`, or no `status-<LANE><NN>.md` lane files in it. |
| `12` | The target is not a git worktree root. |
| `13` | Git `HEAD` could not be read. |
| `14` | Actionable work was not given unsandboxed-shell acknowledgment. |
| `20` | The API returned an HTTP error. |
| `21` | The API could not be reached. |
| `22` | The API response did not match the expected shape. |
| `23` | The model refused or returned no usable text. |
| `30` | The model used `MAX_TURNS` without finishing a row. |
| `31` | The conversation exceeded `MAX_HISTORY_CHARS`. |
| `130` | The run was interrupted from the terminal. |

Codes `10` through `14` are target or authorization setup problems. Codes `20`
through `23` are provider or network problems, not project problems.

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

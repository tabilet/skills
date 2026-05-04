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
- `memory-bank/status.md` records whether harness-related rows are pending,
  complete, blocked, or cancelled.

## Agent Execution Harness

The included [.local/bin/tackle-memory-bank-api-loop](../.local/bin/tackle-memory-bank-api-loop)
is an agent execution harness.

It:

- calls an OpenAI-compatible chat-completions API,
- embeds the memory-bank task instruction directly in the API call,
- gives the model a shell command protocol,
- stops when no actionable rows remain,
- stops when blocked rows exist,
- checks for a clean git worktree before each run,
- requires the model to commit its work,
- stops if the model leaves uncommitted changes,
- stops if the model makes no commit,
- limits the number of loop iterations.

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

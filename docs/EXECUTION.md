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
- `tabilet/memory-bank/tech-stack.md` records prerequisites, environment variables,
  Docker images, ports, and command names.
- `docs/` holds long-form setup, teardown, and troubleshooting notes.
- `tabilet/memory-bank/milestone.md` can make a harness pass part of acceptance.
- The matching `tabilet/memory-bank/status-<LANE><NN>.md` file records whether
  harness-related rows are pending, in progress, complete, blocked, cancelled,
  or closed historical evidence.

## Agent Execution Harness

The included [harness/tackle-memory-bank-api-loop](../harness/tackle-memory-bank-api-loop)
is an agent execution harness.

It:

- calls an OpenAI-compatible chat-completions API, or the Anthropic Messages
  API when `LLM_PROVIDER=anthropic`,
- embeds the memory-bank task instruction directly in the API call,
- gives the model a shell command protocol,
- discovers every `tabilet/memory-bank/status-<LANE><NN>.md` lane file and reports each
  lane's actionable, in-progress, blocked, and closed-historical row counts to
  the model,
- resumes the sole `[~]` in-progress row when one exists and stops before the
  API call if the active ledger contains more than one,
- stops when no actionable rows remain in any lane,
- warns about blocked rows, and stops for human review when only blocked rows
  remain,
- refuses actionable work until the user acknowledges that model commands run
  in an unsandboxed host shell,
- passes a minimal environment to shell commands and requires explicit opt-in
  for additional project variables,
- requires the target path to be the git worktree root,
- checks for a clean git worktree before each run,
- requires the model to commit exactly one completed, blocked, or
  closed-historical actionable row,
- permits separate review commits but rejects history rewrites,
- stops if the model leaves uncommitted changes,
- stops if the model makes no commit,
- retries transient API failures, reports provider usage, and limits loop turns
  and conversation size.

After a project adopts retirement, the agent performs it as part of the closing
run, following the project's milestone procedure after review, verification,
knowledge consolidation, and downstream reconciliation pass. The runner does
not independently archive files or schedule a background cleanup. Individual
completed rows remain active until the whole milestone qualifies; unresolved
work or missing closure evidence keeps it active. Updating the installed skills
alone neither adopts these rules nor upgrades a separately installed API runner.

The agent retains current facts and useful learning in the memory bank, including
`lessons.md`, and moves the complete milestone specification and status to
`tabilet/docs/history/status-<LANE><NN>.md`. It adds the record to the history index and
removes the active status file, specification, and index row. Before materially
superseding current knowledge, it preserves the previous wording and its
provenance and replacement in `tabilet/docs/history/knowledge.md`, even when no
milestone is closing. Routine wording edits need no journal entry.

The runner rejects malformed task markers, empty/unreadable active status files,
invalid active IDs, and indexed or specified milestones without status records
before declaring no work, including before the first retirement. Required
project instructions must remain readable after every run. It validates the envelope,
literal source documents, history index,
closed rows, and removal of the active specification/index row. It follows the same
row identity across that move and preserves earlier rows, notes, and frozen
records. It parses only the envelope's Status record document; examples inside
the preserved specification never count as tasks.

When retiring in an API run, retain the earlier status prose and rows; append
closure evidence and change only the selected row. Preserve the original
specification in the retired document, or retain its literal wording in a new
knowledge-journal entry when a material specification change supersedes it.

This is structural verification, not an independent review of the agent's
acceptance claims or evidence. History is never scheduled. A valid all-retired
project exits without an API call; the API runner still requires a Git worktree.
Exit `0` can also mean all remaining active rows are terminal; it proves neither
milestone acceptance nor that older milestones were retired. Legacy cleanup needs a separate request with
closure evidence.
When task rows are terminal but milestone review or closure was interrupted,
finish that closure in an agent session using the project procedure. The API
runner gates on actionable rows and cannot execute a closure-only recovery run;
its no-work exit is not evidence that the review passed.
Routine retirement needs no separate `memory-bank-archive` run; context snapshots
remain a different workflow. The API runner still requires a commit per run.
The file contract and retrieval workflow are documented in
[long-term memory](../README.md#keep-long-term-memory-without-growing-the-active-plan).

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
| `0` | No actionable rows remain, including a valid all-retired project. |
| `1` | An unexpected internal harness failure occurred. |
| `2` | `LLM_MODEL` is unset, or `LLM_PROVIDER` is not `openai`/`anthropic`. |
| `3` | Only blocked rows remain. A human needs to unblock them. |
| `4` | The worktree was dirty before a run. Commit or stash first. |
| `5` | The agent left uncommitted changes. |
| `6` | The agent made no commit. Stops a spin loop. |
| `7` | `MAX_RUNS` was reached. |
| `8` | The committed result violated the one-row transition or retirement preservation contract, or left required project instructions unavailable. |
| `9` | The agent rewrote history or moved away from the original branch. |
| `10` | No `AGENTS.md` in the target repository. |
| `11` | Missing or invalid status/history state: unavailable required instructions, no memory bank, a milestone without its status record, no active or valid retired milestones, or inconsistent retirement records/index. Missing `AGENTS.md` at startup uses `10`. |
| `12` | The target is not a git worktree root. |
| `13` | Git `HEAD` could not be read. |
| `14` | Actionable work was not given unsandboxed-shell acknowledgment. |
| `15` | More than one general `[~]` row is in progress across the active ledger. |
| `20` | The API returned an HTTP error. |
| `21` | The API could not be reached. |
| `22` | The API response did not match the expected shape. |
| `23` | The model refused or returned no usable text. |
| `30` | The model used `MAX_TURNS` without finishing a row. |
| `31` | The conversation exceeded `MAX_HISTORY_CHARS`. |
| `130` | The run was interrupted from the terminal. |

Codes `10` through `15` are target or authorization setup problems. Codes `20`
through `23` are provider or network problems, not project problems.

## Optional SQLite audit and lookup

The runner remains a single-file installation when auditing is disabled. To opt
in, install the [optional toolkit](sqlite.md#install-and-use-the-optional-toolkit)
and set `TABILET_AUDIT_DB` to an external database path or pass `--audit-db`.
`--audit-capture metadata` is the default; `relevant` also stores the selected
host-observed output. The recorder captures task transitions, successful commits,
validation evidence, and terminal outcomes, then refreshes the Markdown index.

Audit or index failure is reported as a gap and preserves the runner's exit-code
and commit rules. A committed blocked row records a blocked result; historical
closure is not successful acceptance. No new snapshots are captured. Legacy
`--audit-archives` requests stop with a replacement instruction before execution.
The [CLI lifecycle and query commands](sqlite.md#record-a-host-workflow) also serve
interactive hosts. Live Markdown must be reread before acting on indexed results.

## DSH runtime integration

The optional [v1.4.0 companion](DSH.md#install-the-dsh-companion) adds a read-only
project dashboard and request previews. It never executes a workflow or changes
the project's ledger. A prepared request runs only after the user sends it in
the existing conversation; its skills retain their normal approval gates.
Its Node/Web checks live in the companion repository. They do not add Node to
this repository's default Python verification or portable runner.

[DSH](DSH.md) is a separately installed runtime for the same six skill bundles.
`memory-bank-upgrade` adopts new project workflow rules through an approved
merge; it does not update the separately installed API executable or execute
tasks. See [project upgrades](../README.md#upgrade-an-existing-project).
Its Web and headless profiles use DSH tools and permissions; the Python API
runner's provider loop, commit requirement, and exit-code table do not govern
those sessions. Do not run both launchers against the same active ledger.

Run `npm ci --prefix tests/dsh --ignore-scripts --no-audit --no-fund` and
`npm test --prefix tests/dsh` for the pinned, credential-free loader and
installation checks. `python3 check.py` remains dependency-free. These tests
prove runtime integration surfaces, not the model's workflow acceptance.
Required live evidence, cost controls, and observed results are in the
[DSH acceptance guide](DSH.md#acceptance-evidence). Paid tests are explicitly
invoked, never automatic on pull requests.

A DSH question or incomplete milestone can remain after a successful process
exit. Inspect project state, actual verification, and the persisted review
counter. Runtime round limits, native todos, and goal completion are separate
from milestone acceptance. Missing approval, files, commands, or permission
stops affected work without granting broader authority.

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

The active command list belongs in `tabilet/memory-bank/tech-stack.md`. Longer
operational details belong in `docs/`.

## Skill instruction loading

Init, archive, and reconcile inspect their write contracts before requesting
proposal approval. They continue through approved writes and checks without
asking again for those same actions. Uncovered changes require a revised proposal.
Resolve discoverable inputs through safe inspection; stop the dependent step
when a required capability or decision remains unavailable. Headless completion
never supplies an answer or approval. Optional native-goal help lives in the
complete goal bundle and is read only when needed.

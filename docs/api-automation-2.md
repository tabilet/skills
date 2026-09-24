# API automation 2 — Shared execution core and project lock

Plan state: `[+]`

Depends on: [API automation 1 — Boundary, contracts, and authorization model](api-automation-1.md).

## Goal

Let the controller drive the existing runner's execution core instead of
building a second one, and give every Tabilet launcher one project lock. The
standalone runner keeps its single-file installation and existing post-commit
gate meanings and precedence; lock collision is its one new exit outcome.

## Scope and boundaries

The runner, [`harness/tackle-memory-bank-api-loop`](../harness/tackle-memory-bank-api-loop),
already contains the execution components the controller needs, but most live inside
`main()`:

- the provider loop: `call_llm`, `call_openai`, `call_anthropic`, `extract_json`;
- the command protocol and executor: `one_agent_run` and `shell_tool`;
- the row parser and state: `status_rows`, `row_snapshot`, `retired_record`,
  `history_snapshot`;
- the post-run gates: `git_clean`, `git_head`, `git_is_ancestor`,
  `validate_row_transition`, and the ordered checks for exits 5, 6, 9, and 8.

This milestone refactors inside the one file. It adds no second module that
duplicates logic.

## Design

**Importable core.** The controller loads the runner with the same pattern
`tabilet_index.parser()` already uses: a `SourceFileLoader` over the installed
runner file, without invoking `main()`. Importing the runner must stay free of
side effects beyond what it already does today.

**Post-run gates as a function.** Move the ordered post-run checks out of
`main()` into one function, for example `post_run_gates(context) -> GateResult`,
that returns the first failing gate and its exit code in the current order:
uncommitted changes (5), no commit (6), history rewrite or branch change (9),
then invalid row transition (8). `main()` calls it and exits with the same code;
the controller calls it and maps the result to its own pause or stop.

**Executor seam.** `one_agent_run` currently calls `shell_tool`, which runs
`bash -c` on the host. Add an executor parameter with the host shell as the
default, so API 3 can pass a container executor. The standalone runner never
changes executor.

**Host-commit seam.** The standalone runner retains its model-commit instruction
and the post-commit gates above, unchanged. Controller runs use a separate
instruction that forbids Git commits in the executor and asks for a proposed
host commit message. API 3 supplies the required Docker executor and mounts
`.git` read-only. Before the host commits, the controller validates the selected
row transition and protected history, checks changed paths against approved
paths, and requires every declared verification result to pass. Failed
pre-commit checks exit 24 without a commit. The host stages only validated
paths and commits; the shared post-commit gates then run in their existing
order. A path allowlist limits where changes may occur, but cannot prove their
semantic scope; row acceptance and verification remain necessary.

**Project lock.** The runner has no lock today; one is required for "one ledger
writer across all Tabilet launchers". Use an exclusive `fcntl.flock` on a lock
file under `${XDG_STATE_HOME:-~/.local/state}/tabilet/locks/`, keyed by the
SHA-256 of the canonical project path. Both the runner and the controller take
it before reading the ledger and hold it until exit. A second launcher exits with
code 19, before any model call. The lock protects only Tabilet launchers;
interactive Claude Code or
Codex sessions cannot take part, and the documentation says so.

## Deliverables

- `harness/tackle-memory-bank-api-loop`: gate extraction, executor and host-commit
  seams, project lock.
- `harness/tabilet_controller.py`: thin source-loader adapter, separate controller
  prompt, pre-commit validation and host-commit callback seam.
- `tests/test_harness.py`: gate-order, executor, host-commit, and lock tests.
- [docs/EXECUTION.md](EXECUTION.md): the lock and how a held lock is reported.

## Acceptance

- The standalone runner still installs as one file and passes every existing
  harness and SQLite test unchanged, including gate precedence for combined
  failures; a lock collision adds only code 19.
- A second launcher on the same project stops before any provider call.
- A fake-provider controller row uses an injected executor (the Docker executor
  arrives in API 3) and host-commit instructions; failed verification makes no
  host commit, while a successful host commit passes the shared post-commit
  gates.

## Verification

```bash
python3 -B -m unittest discover -s tests -p 'test_harness.py'
python3 -B -m unittest discover -s tests -p 'test_sqlite_*.py'
python3 check.py
```

Review iterations: 2 of 5; no P1/P2 findings remain.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API2-T01 | `[+]` | Extract the ordered post-run gates from `main()` into one function. | Exit codes and precedence match today for every combined-failure case already tested. |
| API2-T02 | `[+]` | Add an executor parameter to `one_agent_run`, defaulting to the host `shell_tool`. | Standalone behavior and the dangerous-command guardrail are unchanged. |
| API2-T03 | `[+]` | Add separate controller pre-commit validation and host-commit instructions. | Verification, row, and path gates precede a host-commit callback; standalone prompt and post-commit gates retain their meanings. |
| API2-T04 | `[+]` | Add the flock-based project lock and take it in both launchers. | Concurrent runner or controller launches stop before any provider call; the lock is released on every exit path. |
| API2-T05 | `[+]` | Load the core from the controller through the existing `SourceFileLoader` pattern. | A fake-provider row uses an injected executor end to end without invoking the runner's `main()`. |

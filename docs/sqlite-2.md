# SQLite 2 — API runner audit integration

Plan state: [+]

Depends on: SQLite 1

This milestone integrates the recorder into the existing
harness/tackle-memory-bank-api-loop. It does not create a second execution
harness and does not change existing status gates or exit codes.

## Interface

Auditing is disabled unless one of these is supplied:

~~~text
--audit-db /absolute/path/to/audit.sqlite3
TABILET_AUDIT_DB=/absolute/path/to/audit.sqlite3
~~~

The command option takes precedence. The default database path is used only
when the user explicitly enables auditing; opening a project never creates it.

Relevant message capture is separately enabled per run:

~~~text
--audit-capture relevant
TABILET_AUDIT_CAPTURE=relevant
~~~

Default mode stores metadata. Relevant mode stores only the runner invocation
and final visible model result needed to explain the change. It never stores
credentials, provider headers, hidden reasoning, or the complete system prompt.

## Lifecycle events

The runner emits, where observed:

1. run_started, with workspace, Git, worktree, operation, and recorder version;
2. task_observed, with status path, milestone ID, and task text;
3. task_transition, with old and new marker states;
4. verification_observed, with command/result summary;
5. commit_observed, only after commit succeeds;
6. run_finished, run_blocked, run_failed, or run_interrupted.

Existing row-transition validation and commit checks remain authoritative. A
missing database produces an audit gap and the existing project outcome and exit
code remain unchanged.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL2-T01 | [+] | Add audit configuration, precedence, and run initialization. | Disabled runs behave as before; enabled runs create one run before the model request. |
| SQL2-T02 | [+] | Emit task, transition, verification, commit, and terminal-result events at existing lifecycle gates. | A successful one-row run has ordered events and records the commit after commit. |
| SQL2-T03 | [+] | Add relevant-message capture with source and fidelity metadata. | Default mode stores no message text; explicit mode stores only permitted text. |
| SQL2-T04 | [+] | Preserve validation, dirty-worktree, history, row-exclusivity, dangerous-command, and exit-code behavior. | Existing harness tests pass with reviewed audit assertions. |
| SQL2-T05 | [+] | Test blocked, failed, interrupted, no-commit, dirty-worktree, missing, locked, and write-failure cases. | Audit gaps are visible and never alter task status, commits, or exit meaning. |

## Completion gate

This milestone is complete when an enabled API run records a reliable lifecycle
and an unenabled run is unchanged. Interactive init, archive, propose,
reconcile, and goal sessions remain outside automatic capture until a host
adapter implements the same event envelope.

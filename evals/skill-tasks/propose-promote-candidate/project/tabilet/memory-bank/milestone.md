# Milestones

Project: tasklist, a small single-user command-line task tracker.

## Status ID Pattern

Status files are `tabilet/memory-bank/status-<LANE><NN>.md`: one uppercase letter, then a
zero-padded two-digit number. `M` is the default lane. IDs are never reused or renamed, and a
retired ID stays reserved in `tabilet/docs/history/`.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| M01 | [status-M01.md](status-M01.md) | Core add and list commands. |
| M02 | [status-M02.md](status-M02.md) | Completion and storage. |

## Active milestone specifications

## M01 - Core commands

**Goal.** Add and list tasks from the command line.

**Scope.**

- Add a task by title.
- List all tasks.

**Acceptance.** `python3 -m unittest` passes for add and list.

**Boundaries and parallel safety.**
- Depends on: none
- Downstream impacts: none
- Write set: src/tasklist.py, tests/
- Contracts read: none
- Parallel-safe: no

## M02 - Completion and storage

**Goal.** Mark tasks done and keep them between runs.

**Scope.**

- Mark a task complete by id.
- Persist tasks to `tasks.json`.

**Acceptance.** Completed state survives a restart; `python3 -m unittest` passes.

**Boundaries and parallel safety.**
- Depends on: M01
- Downstream impacts: none
- Write set: src/tasklist.py, tests/
- Contracts read: M01 public functions
- Parallel-safe: no

## Candidate Directions

Candidate directions are outside the active execution horizon. They have no status ID until
promoted, and a promotion needs fresh planning and approval.

| Direction | Why Deferred | Promotion Trigger |
|---|---|---|
| Export tasks to CSV | Column choice not settled | M02 is complete |

## Out of scope

| Ruled out | Reason |
|---|---|
| Multi-user sync | The tool is single-user by design. |

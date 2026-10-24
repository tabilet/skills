# Milestones

Project: tasklist, a small single-user command-line task tracker.

## Status ID Pattern

Status files are `tabilet/memory-bank/status-<LANE><NN>.md`: one uppercase letter, then a
zero-padded two-digit number. `M` is the default lane for task tracking and `B` is the lane for reporting and exports. IDs are never reused or renamed, and a
retired ID stays reserved in `tabilet/docs/history/`.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| M01 | [status-M01.md](status-M01.md) | Core add and list commands. |
| B01 | [status-B01.md](status-B01.md) | JSON export. |

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

## B01 - JSON export

**Goal.** Export the task list as JSON.

**Scope.**

- Write all tasks to a JSON file.

**Acceptance.** `python3 -m unittest` passes for the export.

**Boundaries and parallel safety.**
- Depends on: M01
- Downstream impacts: none
- Write set: src/tasklist.py, tests/
- Contracts read: none
- Parallel-safe: no

## Candidate Directions

Candidate directions are outside the active execution horizon. They have no status ID until
promoted, and a promotion needs fresh planning and approval.

| Direction | Why Deferred | Promotion Trigger |
|---|---|---|
| Sync across devices | Needs a server decision | Never planned |

## Out of scope

| Ruled out | Reason |
|---|---|
| Multi-user sync | The tool is single-user by design. |

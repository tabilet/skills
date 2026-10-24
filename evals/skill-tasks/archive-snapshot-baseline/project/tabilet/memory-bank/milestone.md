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

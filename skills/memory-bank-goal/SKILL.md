---
name: memory-bank-goal
description: Execute an ordered set of milestones from the memory bank using the project's GOAL.md protocol and optional suggested.txt launch reference, reconciling dependencies before and after each one.
disable-model-invocation: false
argument-hint: M01 -> S01 -> A01?
---

# Run An Ordered Set Of Milestones

Execute several milestones in a defined order, rather than one row at a time.

**Use the form supplied by the installation.** Plugin installs use
`/memory-bank:memory-bank-goal` in Claude Code and
`$memory-bank:memory-bank-goal` in Codex. Plain-file installs use
`/memory-bank-goal` and `$memory-bank-goal`, respectively. **The name avoids
`goal` on purpose.** Claude Code has a built-in `/goal` for long-running goals;
see *Keeping the session going* below.

## What to do

Read `GOAL.md` in the project root and follow it. It owns the sequencing:
reconcile before each milestone, implement its task units, verify and
deep-review, reconcile the milestones downstream of the one that just closed,
then continue or stop.

If `memory-bank/suggested.txt` exists, read it as a disposable launch
suggestion. It is not a source of truth. Reconcile every ID, path, dependency,
conditional trigger, and downstream impact against `memory-bank/milestone.md`,
the current status files, and the implementation before using it. Correct stale
entries in the resolved request; do not silently treat the file as current.

If the project has no `GOAL.md`, do not improvise a multi-milestone protocol.
Tell the user where to get one - it ships beside the `memory-bank-init` skill,
and at <https://github.com/tabilet/skills/blob/main/GOAL.md> - and offer to work
one row at a time meanwhile, or to follow a protocol they supply.

Use this as the request:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: <resolved order>

STATUS_FILE_MAP:
<one ID-to-status-file mapping per ordered status>

DOWNSTREAM_IMPACTS:
<known source-to-pending-consumer impacts, or none>

COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: every required status is complete, every triggered
conditional status is complete, and every milestone's documented verification
passes.
```

Explicit `$ARGUMENTS` replace `suggested.txt`'s `STATUS_ORDER`; the reconciled
file map and downstream impacts may still be reused. When `$ARGUMENTS` is empty,
prefer a valid suggested order, otherwise derive one from
`memory-bank/milestone.md`; show the complete resolved request to the user and
get confirmation before starting. If no unambiguous order exists, ask for one
rather than guessing. Materialize the resolved request in the conversation so
execution never depends on the temporary file remaining on disk.

## Two things to get right

**`COMMIT_POLICY` is never implicit.** `GOAL.md` defaults it to `none`, which
means no commits at all. For the length of this run it is the entire commit
rule - `AGENTS.md` may say each status row is a commit unit, but `none`
overrides it, and that is correct behavior rather than a conflict. `task` gives
the usual one commit per row. Precedence is the request, then `GOAL.md`, then
`AGENTS.md`; only for commits, and only inside the run.

**A trailing `?` marks a milestone conditional.** It is skipped, not cancelled,
when its documented trigger is absent, and it does not block the goal from
completing.

## Keeping the session going

In **Claude Code**, the built-in `/goal` is an optional alternative launcher for
a long run. Include the complete protocol request, order, commit policy, and a
measurable completion condition. When the disposable reference exists, let the
goal reconcile it first:

```text
/goal Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and every milestone's documented verification passes.
```

Run `/goal` with no arguments to show its status and `/goal clear` to stop it.
If `suggested.txt` is absent, put the resolved order, file map, and downstream
impacts directly in the request instead. The `memory-bank-goal` skill remains
the portable launcher shared with Codex.

In **Codex**, use `$memory-bank:memory-bank-goal` for a plugin install or
`$memory-bank-goal` for a plain-file install, then review the completion report.
For other agents, paste the complete request block from *What to do*.

## Report

At the end, state which milestones closed, what was verified, what commits were
made, which conditional milestones were skipped, and what remains blocked.

---
name: memory-bank-goal
description: Execute an ordered set of milestones from the memory bank using the project's GOAL.md protocol, reconciling dependencies before and after each one.
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

If the project has no `GOAL.md`, do not improvise a multi-milestone protocol.
Tell the user where to get one - it ships beside the `memory-bank-init` skill,
and at <https://github.com/tabilet/skills/blob/main/GOAL.md> - and offer to work
one row at a time meanwhile, or to follow a protocol they supply.

Use this as the request:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: $ARGUMENTS

COMMIT_POLICY: task
```

When `$ARGUMENTS` is empty, derive the order from `memory-bank/milestone.md`,
show it to the user, and get confirmation before starting. If no unambiguous
order exists there, ask for one rather than guessing.

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
measurable completion condition:

```text
/goal Using GOAL.md, execute this loop. STATUS_ORDER: M01 -> S01 -> A01? COMMIT_POLICY: task. Completion condition: every non-skipped row in those milestones is `[+]` and the required verification passes.
```

Run `/goal` with no arguments to show its status and `/goal clear` to stop it.
The `memory-bank-goal` skill remains the portable launcher shared with Codex.

In **Codex**, use `$memory-bank:memory-bank-goal` for a plugin install or
`$memory-bank-goal` for a plain-file install, then review the completion report.
For other agents, paste the complete request block from *What to do*.

## Report

At the end, state which milestones closed, what was verified, what commits were
made, which conditional milestones were skipped, and what remains blocked.

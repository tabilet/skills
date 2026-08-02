---
name: memory-bank-goal
description: Execute an ordered set of milestones from the memory bank using the project's GOAL.md protocol, reconciling dependencies before and after each one.
disable-model-invocation: false
argument-hint: M01 -> S01 -> A01?
---

# Run An Ordered Set Of Milestones

Execute several milestones in a defined order, rather than one row at a time.

**This skill is not named `goal` on purpose.** Claude Code has a built-in
`/goal` that sets a stop condition, which is a different thing; see *Keeping the
session going* below.

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

Long runs stop when the agent thinks it is finished.

In **Claude Code**, the built-in `/goal` sets a stop condition the model checks
before finishing, so the session keeps working across turns. Send this skill
first, then set the condition:

```text
/goal every row in the requested milestones is `[+]` and the verification passes
```

`/goal active` shows it and `/goal clear` ends it early. The condition is capped
at 4000 characters and needs a trusted workspace.

In **Codex** and other agents there is no such mechanism; run this skill and
review its completion report when it stops.

## Report

At the end, state which milestones closed, what was verified, what commits were
made, which conditional milestones were skipped, and what remains blocked.

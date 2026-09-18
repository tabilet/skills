# Goal

Execute or resume ordered memory-bank milestones using the project's `GOAL.md`
protocol.

Send one of these in a session for your project, replacing the IDs with your
approved milestone order:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| Codex plugin | `$memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| DSH | `/memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |

Include a measurable completion condition, such as both milestones meeting
their documented acceptance, verification, review, and closure requirements.
For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

A trailing `?`, as in `A01?`, marks a conditional milestone. It is skipped when
its documented trigger is absent, without being completed or cancelled. Later
candidate directions are not conditional milestones and do not belong in an
execution order.

## When to use it

When several milestones should run in a defined order, rather than one task at
a time.

When no order is supplied, the skill checks `memory-bank/suggested.txt` against
the current milestone and status files. It prefers a valid suggested order or
derives one from `milestone.md`, then shows the complete request for confirmation.
It asks you when the order is ambiguous. A missing `GOAL.md` stops this workflow;
one-task execution remains available through [Next](next.md).

## GOAL.md is offered, never required

`GOAL.md` is one optional protocol. It is invoked, not ambient: whatever your
agent, the request that starts a run names the file, the order, and the commit
policy.

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: all required and triggered milestones meet their
documented acceptance, verification, review, and closure requirements.
```

You can paste that at any agent. The protocol contains no project-specific
paths, lane letters, or commands — it reads those from `AGENTS.md` and the
memory bank — so the same file works unchanged in any project that copies it.

The same project files also work with another protocol or one-task execution.
The `memory-bank-goal` skill specifically requires `GOAL.md`; adopting that
protocol remains optional for the project.

## COMMIT_POLICY is the one that matters

!!! note "Choose the commit policy explicitly"
    For the length of a goal run, `COMMIT_POLICY` is the **entire** commit rule.
    `AGENTS.md` may say every status row is a commit unit, but
    `COMMIT_POLICY: none` — the protocol's default — means no commits at all.
    That is correct behavior, not a conflict.

Write `task` when you want the usual per-row commits, or `none` when you want
the changes left uncommitted. The request takes precedence over `GOAL.md`, which
takes precedence over `AGENTS.md`. The commit-policy exception lasts only for
the run; other applicable project rules still govern.

## Built-in `/goal` is a different thing

An agent's native goal feature can keep an objective active across turns. It
does not replace this project's protocol or implicitly select `GOAL.md`.
When using native `/goal` continuation for this workflow, name the protocol,
commit policy, and measurable completion condition explicitly:

```text
/goal Using GOAL.md, reconcile memory-bank/suggested.txt against the current
memory bank, then execute the resolved loop. COMMIT_POLICY: task.
EXTERNAL_MUTATIONS: none.
Completion condition: every required status is complete, every triggered conditional
status is complete, and every milestone's documented verification passes.
```

The skill is deliberately not named `goal`, so it cannot blur or shadow that
built-in.

## One execution owner

An active ledger has one execution owner, even when several sessions or
launchers are available. Native todos and native goal state help a runtime keep
continuity; they never establish acceptance.

Acceptance comes from the project's requirements, actual verification, and
review evidence. A successful process exit can still leave an unfinished
milestone.

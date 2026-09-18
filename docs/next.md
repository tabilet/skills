# Next

Implement and verify one actionable memory-bank task, update its records, and
commit under the governing policy.

Send the request in a session for your project:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-next` |
| Codex plugin | `$memory-bank:memory-bank-next` |
| DSH | `/memory-bank-next` |

Takes no arguments. Plain English works too: *"tackle next pending item in
memory bank"* does the same job.

For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

## When to use it

Use it when an initialized project has an approved task ready for execution.
This request authorizes implementation within that scope; Next does not add an
Init-style proposal gate before every file edit. The agent still stops for
missing decisions, permissions, or required capabilities.

Also for **resumption**. If a row is already in progress, next resumes it rather
than selecting a new one.

## What one run does

1. Read `AGENTS.md`, then the memory bank in the order it specifies.
2. Select exactly one actionable row, guided by `milestone.md` priority.
3. Implement it.
4. Run the verification named in `tech-stack.md`.
5. Update the status row and any memory-bank file whose facts changed.
6. Commit that row's work under the governing commit policy.

The usual policy is one status row per commit. A governing explicit commit
policy, including one inside a `tabilet/GOAL.md` run, can change that. A milestone is the
unit of review.

## Status markers

| Marker | Meaning |
|---|---|
| `[ ]` | Pending |
| `[+]` | Completed |
| `[~]` | In progress |
| `[!]` | Blocked |
| `[X]` | Cancelled |
| `[-]` | Closed historical evidence |

A `[-]` row is a consumed failed attempt or a superseded row kept for audit. It
is never retried, and it does not block its accepted successor. Its notes name
the consumed attempt and the successor that replaced it.

!!! warning "The backticks are required"
    Write markers exactly as in the table above: `` `[ ]` ``, not `[ ]`. A
    current API runner rejects a malformed marker with **exit 11** and the
    message "unknown or non-backticked state marker". Older runners ignored such
    a row silently and exited as though the work were finished, so check the
    version of a separately installed runner as well as the row syntax.

For example, a task table contains the literal backticks shown here:

```markdown
| Item | State | Notes |
|---|---|---|
| Add quantity validation | `[ ]` | Verify zero and multi-unit orders. |
```

If an existing project uses another layout or marker convention, inspect it
before making changes. Dashboard warnings can indicate a legacy format or a
parser limitation. Do not rename permanent IDs or infer task outcomes from
unrecognized syntax; use [Upgrade](upgrade.md) to compare the rules first.

## One in-progress row

Across the active status ledger, zero or one general row may be `[~]`. Resume it
before selecting another. The API harness enforces this before the first network
call.

Before invoking an operational launcher, its exact authorized operation row must
already be `[~]`. The marker records the selection; it never grants
external-mutation authority.

## Correcting current truth

When an implementation invalidates a current product or architecture fact, the
same task corrects it, even if a later documentation task exists. The memory
bank is not allowed to be wrong in the interval.

## Milestone close

When a row is the last unfinished item in its milestone, next runs the milestone
review in `milestone.md` before continuing. The initial full review is iteration
1; every P1, P2, or higher-severity fix is verified and followed by another full
review of the whole milestone. A clean pass is required within ten iterations,
and the counter persists across sessions and reviewers.

Closing a milestone also asks whether `tabilet/evolution/` needs a new version. Only a
real change in product direction, architecture boundary, milestone target, or
public contract justifies one.

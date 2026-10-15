# Next

Implement and verify one actionable memory-bank task, update its records, and
commit under the governing policy.

Send the request in a session for your project:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-next` |
| Codex plugin | `$memory-bank:memory-bank-next` |
| DSH | `/memory-bank-next` |

Accepts optional `--email ADDRESS` and an explicit `CORRECTIVE_PLANNING` policy.
Plain English works too: *"tackle next pending item in
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
policy, including one inside a goal-protocol run, can change that. A milestone is the
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

## Action authority

Read optional `AUTHORIZATION_REQUIREMENTS` in the owning milestone, and check
protected actions against the current scoped human request. Declarations,
proposed grants, and status notes never prove approval. Ordinary local work
does not authorize installs, elevated privileges, arbitrary network activity,
remote commands, or live browser actions. A browser requirement declared for a
`fixture` environment may use goal policy; every other browser environment needs
explicit authority. Resolve exact targets read-only;
reuse a valid grant, and obtain fresh approval for changed scope.

Within a goal, use its narrowed effective grants and preserve commit and
external-mutation restrictions. Outside a goal, the current one-row request
and project rules govern; a previous run's grants do not carry over. Required
unperformed actions prevent closure. See [the authorization guide](goal.md#authorization-requirements-and-grants).
Legacy field omission adds no authority or migration, and host/tool controls
still apply. The Python API paths do not consume these grants.

## Correcting current truth

When an implementation invalidates a current product or architecture fact, the
same task corrects it, even if a later documentation task exists. The memory
bank is not allowed to be wrong in the interval.

## Expensive checks

Some rows have acceptance that depends on an expensive or protected check. For
those rows, the run follows the project's verification-attempt gate:

- it diagnoses in the cheapest environment that reproduces the failure;
- it runs every independent case;
- it persists the attempt count;
- it stops to ask after three consecutive same-stage failures, or after a
  failure outside the milestone's owned scope.

See [the goal guide](goal.md#expensive-checks-and-the-attempt-gate).

## Corrective prerequisites and approval email

`CORRECTIVE_PLANNING: confirm` is the default. Under human-approved `auto`,
Next may prepare and check necessary repair plans, amend pending work or create
repair milestones within the selected task's original delivery outcome,
approved owning repositories, action grants and explicit limits. It completes
only those prerequisites and returns to the original task, preserving its
interrupted work, identity and review evidence. New permissions, scope or
higher limits require approval. See [standing corrective planning](goal.md#standing-corrective-planning).

Next suspends the interrupted `[~]` row as `[!]` before activating a repair row,
recording prerequisite IDs, approval source and resumption condition. It restores
`[~]` after prerequisite acceptance and clearance of every blocker, without
another approval for the covered repair. Resume the same chain; preserve partial
work and pause if overlapping changes cannot be separated safely. Repairs cannot
weaken acceptance or cancel unmet obligations, and their own reviews cannot
reset or replace the original milestone's persisted review gate.

To request one email per workflow approval need:

```text
$memory-bank:memory-bank-next --email abc@def.gh
```

The flag selects one recipient for this run and its resumes; a new invocation
with no flag disables email. Use your agent's normal invocation prefix.
[Configure Cloudflare delivery once](installation.md#approval-email-setup).
The sender checks configuration locally, sends only a short sanitized summary,
and suppresses duplicate or uncertain attempts. Children report needs to their
owner. Delivery never supplies approval; unavailable delivery leaves the
original approval pause intact. Native host tool-approval prompts and Python
API-runner/controller invocation are outside this feature.

## Milestone close

When a row is the last unfinished item in its milestone, next runs the milestone
review in `milestone.md` before continuing. The initial full review is iteration
1; every P1, P2, or higher-severity fix is verified and followed by another full
review of the whole milestone. A clean pass is required within ten iterations,
and the counter persists across sessions and reviewers.

Closing a milestone also asks whether `tabilet/evolution/` needs a new version. Only a
real change in product direction, architecture boundary, milestone target, or
public contract justifies one.

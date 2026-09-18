# Upgrade

Upgrade an existing memory bank's workflow rules through approved merges,
preserving project plans, local policies, and history.

Send the request in a session for your project:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-upgrade` |
| Codex plugin | `$memory-bank:memory-bank-upgrade` |
| DSH | `/memory-bank-upgrade` |

Argument: optionally, the workflow changes you want to adopt.

For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

## When to use it

After installing newer skills, when you want an existing project to adopt the
new workflow rules.

The project must already have a milestone/status harness; an all-retired project
with valid indexed history still qualifies. Pause other execution on the same
ledger before applying the approved upgrade.

Installing newer skills cannot safely rewrite every project that used an older
version. Those projects have their own commands, policies, plans, and history.
**An install never migrates a project.** This skill is how adoption happens, and
only with your approval.

## Three phases

**Inspect and compare.** Upgrade compares the project's adopted workflow with
the reference template bundled inside the skill. That bundle means no checkout
and no network access is needed to inspect the target. It identifies missing
rules, compatible local equivalents, deliberate exclusions, and conflicts that
need a decision from you.

**Propose and obtain approval.** It presents specific file actions — focused
section diffs rather than whole restated documents — and waits.

**Apply and verify.** After approval it applies the scoped merges and verifies
that preservation actually held.

## A useful request

```text
Use memory-bank-upgrade to compare this project's workflow with the bundled
contract. Preserve our plans, local policies, task states, IDs, review counts,
and history. Show the complete proposed file changes before writing.
```

## What is preserved

Task state, permanent identifiers, local policies, review counters, custom goal
protocols, completed evidence, and frozen history. A project already compatible
needs no changes at all.

## What an upgrade is not

An upgrade adopts **operating rules**. It does not initialize a project,
implement work, commit, or retire milestones as a side effect.

Retiring older milestones is separate work that needs its own scope and closure
evidence. A separately installed API harness needs its own compatibility check
or update.

## Adopting long-term memory

This is the skill that matters most for a project with months of history,
because it is how `lessons.md` and milestone retirement arrive in a project that
predates them.

Existing projects require explicit adoption. There is no automatic bulk
migration, and retirement respects every commit policy.

## If DSH reports compatibility warnings

You can prepare an Upgrade request even when the dashboard cannot read all the
records. **Insert into empty draft** only prepares text; sending it asks the
agent to inspect and propose changes. It does not approve a merge.

Include the warnings in the conversation: the sidebar displays them separately
from the request text. Ask the agent to distinguish unsupported legacy syntax
from actual ledger conflicts before proposing corrections. Preserve IDs, states,
notes, review evidence, and history; do not bulk-rewrite them to clear a warning.

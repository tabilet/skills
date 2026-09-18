# Upgrade

## Migrate a v1.5.0 project to v2

v2 keeps `AGENTS.md` at the project root and moves Memory Bank files under
`tabilet/`: `GOAL.md`, `memory-bank/`, `evolution/`, archives, and retired
history. Other project documentation stays at the root. Installing v2 never
moves these files, and v2 skills and the API runner stop on a legacy or mixed
layout. The v2 DSH sidebar can display a v1.5.0 project read-only with a
migration warning.

Use the standard-library command bundled with the Upgrade skill, or the same
file in a v2 source checkout. Start from a committed, clean Git worktree:

```bash
python3 /path/to/skills/skills/memory-bank-upgrade/migrate-v1.5-to-v2.py /path/to/project
python3 /path/to/skills/skills/memory-bank-upgrade/migrate-v1.5-to-v2.py /path/to/project --apply
```

The first command only previews file actions. `--apply` moves the files,
updates maintained instructions and indexes, preserves frozen archives and
retired records byte-for-byte, and leaves the diff uncommitted for review. It
reports path references in other project documents for manual review. It also
supports all-retired projects, archive-only preflights, an absent or customized
goal protocol, and local policies. For the unmodified v1.5.0 `GOAL.md`, it
updates the one path example to the v2 location. A customized `GOAL.md` stays
byte-for-byte intact and is always flagged for manual path review.

If interrupted, run the same command with `--resume`. It checks a temporary
journal outside tracked project files, Git `HEAD`, and every planned file hash
before continuing. An unexplained partial layout, symlink, or destination
collision stops for manual repair. Once complete, a repeat run is a no-op.

After reviewing the diff and project checks, commit it under your project's
normal policy. If workflow rules also need updating, use Upgrade below as a
separate approved merge.

## Upgrade workflow rules

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

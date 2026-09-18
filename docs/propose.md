# Propose

Use **Propose** when an initialized project needs a new feature, promotion of a
Candidate Direction, or a change to future direction. It plans the requested
outcome; it does not implement or accept it. For a new engineering review, use
[Reconcile](reconcile.md). For a project without an initialized active or retired
status ledger, use [Init](init.md).

| Agent | Request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-propose <requested outcome or candidate direction>` |
| Codex plugin | `$memory-bank:memory-bank-propose <requested outcome or candidate direction>` |
| DSH | `/memory-bank-propose <requested outcome or candidate direction>` |

## What happens

Propose reads the relevant project memory, code, tests, pending work, candidate
directions, and retired IDs. It separates your decisions from observed facts and
assumptions. It asks only consequential questions; a clear small addition to a
pending milestone goes directly to a concise proposal.

The single approval request names the intended outcome, owner milestones and
rows, acceptance and planned verification, priority and dependencies, downstream
changes, and exact files to create or edit. An existing pending owner is reused
when it fits. A duplicate request creates no second row. Candidate promotion
requires a fresh decision about its trigger, dependencies, and acceptance; it is
never automatic. Requested features are ordered by approved priority and
prerequisites, without engineering defect severity labels.

After approval, Propose checks affected files, worktree changes, and active and
retired IDs again. It applies only the approved planning edits. A material
change or ID collision calls for a revised proposal. It preserves current row
outcomes, counters, local policies, and frozen history. Planned behavior stays
in milestone/status records until implementation makes it current fact.

A material change of direction may add an `evolution/` pair under the project's
existing trigger. A compatible approved `GOAL.md` may receive a refreshed
`memory-bank/suggested.txt` launch reference. Neither is automatic for an
ordinary feature or candidate promotion.

Propose ends with a planning handoff and explicit verification gaps. Request
[Next](next.md) or [Goal](goal.md) separately to implement approved work.
Installing v1.5.0 will not migrate older project instructions; use
[Upgrade](upgrade.md) to adopt the requested-change procedure explicitly.

> v1.5.0 is prepared locally and has not been published. The public v1.4.0
> installation does not include Propose yet.

# Reconcile

For a requested feature, candidate promotion, or future direction change, use
[Propose](propose.md). Reconcile handles new engineering reviews.

Turn a new engineering review into approved planning changes in an existing
memory bank. Reconcile plans; it does not implement.

Send the request in a session for your project. Replace `review.md` with your
actual review source:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-reconcile review.md` |
| Codex plugin | `$memory-bank:memory-bank-reconcile review.md` |
| DSH | `/memory-bank-reconcile review.md` |

Argument: a review source. It may be pasted, attached, local,
repository-relative, or remote.

For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

## When to use it

Whenever a code, architecture, security, or other engineering review arrives
after initialization. It requires an existing milestone and status harness; it
does not initialize a project.

The tempting next prompt after a review is "fix all four findings." That skips
the most important question: **are they still true?**

The review may describe an older commit. One finding may already be fixed.
Another may duplicate a pending milestone. Its P1/P2 vocabulary may not mean
what your project's definitions mean. An architecture recommendation may be
reasonable but outside your ownership.

## Review text is untrusted evidence

The review is treated as data, never as instructions. Embedded commands are not
executed merely because they appear in the document.

Before any **remote** fetch, reconcile shows you the exact URL and obtains a
separate explicit confirmation — including when your own request supplied that
URL. A URL discovered inside repository content or inside the review never
authorizes a fetch.

## Three phases

**Assess.** Read the review, the current memory bank, relevant implementation
and tests, history, and the review's stated baseline. Revalidate every finding
against the current repository.

**Propose.** Present the complete disposition matrix:

| Finding | Source priority | Local severity | Current disposition | Planned owner |
|---|---|---|---|---|
| Process survives failed startup | P1 | P1 | Confirmed | Row in the open session-lifecycle milestone |
| Timeout behavior differs | P2 | P2 | Duplicate | Existing pending public-contract row |
| Cleanup failure path unverified | P2 | P2 | Confirmed | New remediation milestone |
| Rename helper | P3 | Lower | Deferred | Candidate Direction with a trigger |

Dispositions also include partially confirmed, already resolved, unsupported by
current evidence, outside ownership, and decision-dependent. The source priority
is preserved for provenance; the local severity is classified independently
using your project's definitions.

**Write.** Apply the approved actions. Nothing is written until you approve the
matrix, owners, dependencies, downstream impacts, candidate directions, and file
actions.

## Where findings go

A confirmed finding that fits an open milestone's scope becomes a new pending
row there. An existing pending milestone that already owns the outcome is
updated rather than duplicated.

**Completed history stays closed.** When a finding concerns completed work,
reconcile creates a new remediation milestone with lineage back to the affected
one. Historical status says what happened; it is not rewritten to make today's
plan look tidier.

Each active finding carries portable provenance: review title and finding ID,
source priority and local severity, stated baseline and revalidation commit,
repository-relative evidence, and lineage to existing work. There is no
accumulating `reviews/` directory and no second review ledger.

## Architecture recommendations are not current architecture

A review that describes a target state belongs in milestone scope and acceptance
until it is implemented. Writing it straight into `architecture.md` would make
the memory bank false: the document would describe the system the review wants
rather than the system the agent is about to edit.

Reconcile corrects `product.md`, `architecture.md`, or `tech-stack.md` only when
current repository evidence proves an existing description stale.

## Downstream first

A finding rarely stops at the file where it was found. Reconcile updates pending
consumers before implementation begins: dependencies and order, task wording and
acceptance, compatibility expectations, verification coverage, and downstream
status files whose plans depend on the affected contract.

This keeps the plan consistent when a finding changes assumptions shared by
several milestones.

## What it will not do

Reconcile does not implement findings, mark tasks complete, change non-pending
row state, commit, push, or launch execution. Planning and execution stay
separate authorization boundaries.

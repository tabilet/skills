# Init

Turn your idea or existing codebase into a project-specific memory bank. Init
inspects available evidence, asks about unresolved decisions, and proposes the
milestones needed to reach the next verifiable outcome. It writes the files
after you approve the complete proposal.

Send the request in a session for your project:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-init` |
| Codex plugin | `$memory-bank:memory-bank-init` |
| DSH | `/memory-bank-init` |

No arguments are required. You can include a description of what you want to
build. For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

## When to use it

Once, on a project with no initialized milestone and status harness. That
includes a brand-new project, an existing project that has never had one, and an
existing project after a completed [archive](archive.md) preflight.

An existing `memory-bank/milestone.md` with active status files **or valid indexed
retired history** is already initialized. Use [Propose](propose.md) for a requested feature or candidate promotion, and
[Reconcile](reconcile.md) for a new
review or [upgrade](upgrade.md) to adopt newer workflow rules. Missing or
inconsistent records need inspection; they are not permission to start over.

## Three phases

**Discover.** Init reads the repository first, then asks about decisions it
cannot establish from evidence. Questions arrive in numbered rounds, with a
recommended answer and the relevant tradeoffs. Each round builds on earlier
answers; there is no fixed questionnaire or limit on the areas it can explore.

**Propose.** It presents the boundary, the proposed active horizon, lane
meanings, candidate directions, and every file action. Nothing is written until
you approve all of it.

**Write.** It applies the approved actions under the bundled write contract. You
never see a bracketed placeholder, because the memory bank arrives filled in.

*(Interview technique adapted from the `grilling` skill in
[mattpocock/skills](https://github.com/mattpocock/skills), MIT.)*

## The active horizon

The output separates three kinds of information:

```text
memory-bank/product.md       what the product is and its domain invariants
memory-bank/architecture.md  what the system is now
memory-bank/tech-stack.md    commands, dependencies, and verification
memory-bank/lessons.md       learning that still changes decisions
memory-bank/milestone.md     the active horizon and later directions
memory-bank/status-*.md      one task-sized row per implementation unit
```

The **active horizon** is the smallest dependency-closed set of milestones that
reaches the next meaningful, verifiable outcome. Permanent status identifiers go
only to that horizon.

Later ideas stay unnumbered in Candidate Directions with promotion triggers.
They do not receive status IDs merely because the repository survey noticed
them, and they never appear in the launch reference.

> Archive records what exists. Init decides what to do next.

## After an archive preflight

Init does not compress the package from scratch a second time. It consumes the
verified context evidence, preserves the frozen archives, safely merges the
current product and architecture summaries, and interviews only the remaining
delivery decisions.

## The launch reference

When the project contains an approved compatible `GOAL.md`, init also writes
`memory-bank/suggested.txt`: a disposable launch request with the proposed
status order, file map, and downstream impacts.

It is launch input, not project truth. It stays out of the required read order,
and it should be checked against `milestone.md` and the current status files
before use, then deleted once launched or stale. Without a compatible protocol,
init omits it and one-task execution remains available.

## Verifying the result

Check the **Execution harnesses** table in `tech-stack.md`: it should identify
the actual verification commands and what a pass establishes. Resolve missing
verification before starting execution. A task reaches `[+]` only after its
applicable checks pass and its acceptance requirements are met.

Then request [Next](next.md) for one approved task, or [Goal](goal.md) for an
explicit milestone order. Initialization does not launch implementation.

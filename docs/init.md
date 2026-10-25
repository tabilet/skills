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
build. Optional flags include `--stages` for multi-stage projects, `--environment dangerous|sandbox|least`
to set authorization stances, and `--test standard|browserlight|golight|rustlight|tslight|jslight|pythonlight`
to configure verification standards and execution limits in `tech-stack.md`. For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

Light `--test` profiles use a **30-second focused-test target / two-minute cap**,
a **20-minute full-regression cap**, and **five minutes for applicable UI/race checks**.
These are starting planning defaults, not a 30-second limit on the whole repository.
Explicit project limits win; `standard` adds no extra constraints. The approved
plan records concrete commands and timing scope, keeps routine fixtures offline
and small, and assigns physical browser proof to a named final release gate.

## When to use it

Once, on a project with no initialized milestone and status harness. That
includes a brand-new project, an existing project that has never had one, and an
existing project after a completed [archive](archive.md) preflight.

An existing `tabilet/memory-bank/milestone.md` with active status files **or valid indexed
retired history** is already initialized. Use [Propose](propose.md) for a requested feature or candidate promotion, and
[Reconcile](reconcile.md) for a new
review or [upgrade](upgrade.md) to adopt newer workflow rules. Missing or
inconsistent records need inspection; they are not permission to start over.

## Three phases

**Discover.** Init reads the repository first, then asks about decisions it
cannot establish from evidence. Questions arrive in numbered rounds, with a
recommended answer and the relevant tradeoffs. Each round builds on earlier
answers; there is no fixed questionnaire or limit on the areas it can explore.
For a medium or large project, Init asks at least one staging question. A small
project with uncertain later work may use stages too. The interview resolves
the current delivery outcome; later ideas can stay preliminary.

**Propose.** It presents the boundary, the proposed active horizon, lane
meanings, candidate directions, and every file action. Nothing is written until
you approve all of it.

**Write.** It applies the approved actions under the bundled write contract. You
never see a bracketed placeholder, because the memory bank arrives filled in.

*(Interview technique adapted from the `grilling` skill in
[mattpocock/skills](https://github.com/mattpocock/skills), MIT.)*

## The active horizon

The output separates present facts, approved work, and optional stage direction:

```text
tabilet/memory-bank/product.md       what the product is and its domain invariants
tabilet/memory-bank/architecture.md  what the system is now
tabilet/memory-bank/tech-stack.md    commands, dependencies, and verification
tabilet/memory-bank/lessons.md       learning that still changes decisions
tabilet/memory-bank/milestone.md     the active horizon and later directions
tabilet/memory-bank/status-*.md      one task-sized row per implementation unit
tabilet/stages.md                    optional overview of delivery stages
```

The **active horizon** is the smallest dependency-closed set of milestones that
reaches the next meaningful, verifiable outcome. Permanent status identifiers go
only to that horizon.

Distinct optional ideas stay unnumbered in Candidate Directions with promotion
triggers. Preliminary stages have `STG-` IDs and can remain sketches. Neither
receives status IDs merely because the repository survey noticed them, and
neither appears in the launch reference.

## Stages

`tabilet/stages.md` records broad delivery stages when they help the project.
Its absence means one implicit stage. Init can accept a later idea as just a
tentative name and one sentence of intent; it does not ask for distant tasks or
acceptance details. It may add useful context from existing evidence, clearly
marking assumptions and open questions. Only the current stage's next reliable
outcome receives milestone and task IDs.

Each stage has a stable ID such as `STG-01`, separate from milestone IDs such
as `M01`. Reordering or renaming a stage preserves its ID. Stage ideas do not
enter status files or the launch reference. Once new evidence arrives, use
[Propose](propose.md) to enrich a stage or plan its milestones.

> Archive records what exists. Init decides what to do next.

## After an archive preflight

Init does not compress the package from scratch a second time. It consumes the
verified context evidence, preserves the frozen archives, safely merges the
current product and architecture summaries, and interviews only the remaining
delivery decisions.

## Corrective-planning preset

Init includes `CORRECTIVE_PLANNING` in proposed launch input:
`--environment dangerous` proposes `auto`, while sandbox and least propose
`confirm`. Explicit human policy wins. Approval of the later execution request
can authorize necessary repair planning within the original delivery outcome,
existing action scopes and limits. It never activates new grants, raises limits
or starts execution during Init. See [standing corrective planning](goal.md#standing-corrective-planning).

## The launch reference

When you approve goal use and the selected governing protocol is available and compatible, init also writes
`tabilet/memory-bank/suggested.txt`: a disposable launch request with the proposed
status order, file map, downstream impacts, and the `GOAL_IDENTITY` block. Init no
longer copies a protocol into the project.

It is launch input, not project truth. It stays out of the required read order,
and it should be checked against `milestone.md` and the current status files
before use, then deleted once launched or stale. Without approved goal use or
an available compatible selected protocol, Init omits new launch input and
preserves existing input pending resolution; one-task work remains available.

## Verifying the result

Check the **Execution harnesses** table in `tech-stack.md`: it should identify
the actual verification commands and what a pass establishes. Resolve missing
verification before starting execution. A task reaches `[+]` only after its
applicable checks pass and its acceptance requirements are met.

Then request [Next](next.md) for one approved task, or [Goal](goal.md) for an
explicit milestone order. Initialization does not launch implementation.

## Planning protocol and model selection

Approved goal use with an available compatible governing protocol permits
launch input without a package-local `tabilet/GOAL.md`. Init defaults to stock;
an explicit `GOAL_PROTOCOL` alternative keeps its actual path/hash and matching
invocation and package identities. Missing or incompatible selection is
reported instead of replaced. No stock or merged protocol is written into the
project. Add [MODEL_POLICY](goal.md#optional-model-policy) only when requested;
its omission preserves host settings.

Use expand–contract when a refactor cannot safely fit into one bounded green
change or needs a compatibility transition. A safely atomic mechanical rename
may remain one row. Defect reproduction is preferred only within current
authority and budget; record existing evidence and limitations when unsafe or
unavailable, preserving required acceptance and verification gates.

## Amendments and deferred options

Keep the original delivery outcome stable. Put substantial required repairs in
`amend-M53-01.md` and optional work in `option-M53-02.md`, sharing one permanent
sequence. Each child declares `Parent: M53` and owns its specification and tasks.
The parent finishes independent work, waits for required amendments, then resumes
its deferred checks and final review. Mocks cannot pass missing real acceptance.
External testing-tool repair is optional by default; only an explicit owner
decision can make it a blocking amendment, even under automatic corrective planning.

`OPTION_POLICY: confirm` is the default: leave options alone during parent work,
then consolidate them and ask once after parent closure. Recommend yes, but wait
for an actual answer. `OPTION_POLICY: ignore` suppresses option refinement,
prompts and execution for the whole goal; finishing the goal does not activate
them. Selected options need an approved horizon and do not reopen their parent.
These settings grant no additional action authority or budgets.

Strict orders place required children immediately after their parent as a family;
the parent closes after its amendments, before downstream work. Priority order
uses the same readiness conditions without introducing ordering edges. Existing
root-only plans retain their behavior. Retire child records with their original
filenames and parent links; deferred options can outlive a retired parent.

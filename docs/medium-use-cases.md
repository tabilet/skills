# Eight Memory-Bank Workflows: From Your First Project to Long-Term Maintenance

<!-- Medium publishing asset: medium-use-cases-infographic.png.
Upload this image immediately below the article title; it is intentionally
not embedded in the manuscript.
Alt text: Eight independent memory-bank use cases: start from scratch, map a broad codebase, finish one task, run ordered milestones, reconcile a review, retire completed work, snapshot a changed system, and retrieve an old decision.
Before Medium publication, replace the local companion link (medium-memory-bank-v1.3.md)
with the companion article's published Medium URL.
Image generation: built-in image_gen; final prompt follows.
Use case: infographic-diagram.
Asset type: a polished editorial infographic for a Medium companion article presenting exactly eight memory-bank use cases.
Primary request: Show eight independent entry points into a minimal engineering workflow, with a clear from-scratch entry point first.
Format: high-resolution portrait, approximately 3:4. A two-column by four-row grid of eight equally legible cards, numbered 1 through 8 in reading order. These are choices, not a mandatory eight-step sequence: no arrows between cards.
Style: cohesive with an editorial series using a dark charcoal background, cream paper-like cards, amber and burnt-orange header accents, subtle printed texture, bold condensed sans-serif headings, clean document/folder/magnifier icons. Clear typographic hierarchy, ample margins, readable body text, no provider logos or cartoon people.
Exact text, render verbatim and no extra text:
Title: "8 WAYS TO USE MEMORY-BANK"
Subtitle: "FROM YOUR FIRST PROJECT TO LONG-TERM MAINTENANCE"
Small intro line: "Choose the case that matches your project."
Card 1: "1  START FROM SCRATCH" / "memory-bank-init" / "Idea → approved first milestone"
Card 2: "2  MAP A BROAD CODEBASE" / "archive → init" / "Verified facts before planning"
Card 3: "3  FINISH ONE TASK" / "memory-bank-next" / "Resume • implement • verify"
Card 4: "4  RUN ORDERED MILESTONES" / "memory-bank-goal" / "Dependencies + explicit commit policy"
Card 5: "5  RECONCILE A REVIEW" / "memory-bank-reconcile" / "Validate findings • approve the plan"
Card 6: "6  RETIRE COMPLETED WORK" / "Milestone closure" / "Keep lessons • freeze full evidence"
Card 7: "7  SNAPSHOT A CHANGED SYSTEM" / "memory-bank-archive" / "New baseline • preserve the old"
Card 8: "8  RETRIEVE AN OLD DECISION" / "Read-only investigation" / "Find evidence • never retry history"
Footer line 1: "Approved gates separate planning from execution."
Footer line 2: "Existing projects adopt new rules with memory-bank-upgrade."
Constraints: Eight cards only, no ninth use case. Card 1 must clearly mean a brand-new project. Card 6 is part of authorized milestone closure after its gates, not an archive command. Card 7 is a separately approved context snapshot. Card 8 is read-only and is not task execution. Do not imply automatic transitions between cases or automatic approval. No watermarks or tiny microtext.
-->

*Choose the workflow that matches the work in front of you.*

A project can begin with an idea and an empty directory. It can also begin, for
the agent, with ten years of code and a review written last week. Those starting
points need different conversations.

[Memory-bank](https://github.com/tabilet/skills) gives a native coding agent a
small set of engineering workflows and gives the project its own memory in
Markdown. The six skills cover discovery, factual snapshots, project-rule
upgrades, review intake, one-task execution, and ordered milestones.

The [companion article on v1.3.0](medium-memory-bank-v1.3.md) explains the design
and its new memory lifecycle. This article shows how to use it through eight
practical cases. They are independent entry points: choose the one that matches
your situation. A new project can start with case 1 and then use case 3 without
ever needing an archive.

The examples use **Parcel**, a hypothetical order-processing package. Each case
describes a possible state of that project, rather than a mandatory sequence
of eight steps.

## Before choosing a case

Install the complete skill bundles using the
[maintained installation guide](https://github.com/tabilet/skills#install-the-six-skills).
Keep their supporting references and bundled assets. The project files remain
yours after installation, updates, and removal.

For a plugin installation, initialization is
`/memory-bank:memory-bank-init` in Claude Code and
`$memory-bank:memory-bank-init` in Codex. DSH filesystem installations use
`/memory-bank-init`. Apply the same naming pattern to the other commands, or
use the ordinary-language requests below in your agent session.

An existing memory-bank project can use `memory-bank-upgrade` to adopt newer
workflow rules through an approved merge. Updating installed skills alone does
not change project instructions or retire old work. Before using case 6,
establish that the project has adopted the retirement contract and, if used,
has a compatible separately installed API runner.

Keep one execution owner for the active ledger. Planning, implementation,
retirement, and external actions each stay within their authorized scope.

## 1. Start a project from scratch

**Starting situation.** You have an empty directory and an idea: Parcel should
read a local JSON order and calculate its total. Currency handling, invalid
input, and the first delivery boundary still need decisions. There is no memory
bank and no implementation to map.

Create the project directory and initialize Git if you want the usual per-task
commit workflow. Start your coding agent in that directory.

Ask the agent:

```text
Use memory-bank-init for a new project called Parcel: a local Python CLI
that calculates order totals from JSON. Use unittest for verification.

Help settle the first delivery boundary and any unresolved product decisions.
Keep payment processing and deployment outside this first delivery.
Propose the milestones and exact file actions before writing anything.
```

The agent works through the decisions needed to define a verifiable first
outcome. It should reuse answers you have already supplied and use established
conventions for routine details. This is an adaptive conversation; it does not
require answering a fixed questionnaire regardless of the project.

After you confirm the discovery and approve the file proposal, initialization
creates the project instructions, current product and architecture descriptions,
verification plan, and active milestones with status files. The initial
`lessons.md` can honestly say that no durable lessons are established yet.

Only the approved active horizon receives permanent IDs. Later ideas remain
unnumbered candidates with conditions for reconsidering them. There are no
historical records to manufacture and no existing codebase to archive.

**Next step.** Inspect the generated plan, then explicitly request the first
task with `memory-bank-next`. Initialization establishes the harness; it does
not implement the CLI or claim that its future tests have passed.

A small, coherent existing package without a harness can use this route too.
Its existing source, tests, and instructions supply facts that an empty project
does not yet have.

## 2. Map a broad existing codebase before planning

**Starting situation.** Parcel is now an existing package with distinct catalog,
order, billing, and fulfillment contexts. You want to begin using the harness,
but a single summary would omit important boundaries and contracts.

If you begin with `memory-bank-init`, its topology check can identify the need
for archive preflight. You can also request that preflight directly:

```text
Use memory-bank-archive to map this existing package's catalog, orders,
billing, and fulfillment contexts at the current clean Git baseline.

Propose the delivery boundary, context partition, evidence, coverage,
archive paths, and file actions for approval. Record facts and observed
gaps; do not create milestones or implement changes.
```

The agent checks repository evidence and proposes a context map. Broadness is
a question of ownership, behavior, and verification coverage. File count alone
does not decide it.

After approval, the archive workflow creates factual baselines such as
`docs/archive-O01.md` and maintains current product and architecture summaries.
Verified archives record their full baseline commit and freeze there. A
documented future design stays distinguishable from implemented behavior.

Every selected context must be verified before a required preflight is complete.
Here, verified means the context map is supported by inspected evidence; it
does not mean the implementation has passed a milestone review.

**Next step.** Explicitly return to `memory-bank-init`. It preserves those
archives, merges their current-summary seeds, and proposes the executable
horizon. Approve that plan before writing it, then request implementation.

The [earlier existing-codebase article](https://medium.com/@peterbi_91340/manage-existing-codebase-using-agentic-engineering-harness-c362f556f96f)
walks through this route in more detail.

## 3. Finish one task, including an interrupted one

**Starting situation.** The memory bank already contains an approved milestone.
One row is ready, or a previous session left exactly one row marked `[~]`.
For Parcel, that row might implement quantity-aware totals.

Ask the agent:

```text
Use memory-bank-next to complete exactly one approved task row.
Resume the existing in-progress row first if there is one.
Verify the change, update affected current memory and status evidence,
and commit according to the governing project policy.
```

The agent resumes the sole in-progress row before selecting new work. If none
exists, it chooses a dependency-ready pending row. Multiple in-progress rows,
unresolved blockers, or missing authority require resolution rather than
another simultaneous writer.

For the order-total change, implementation and tests belong together. If the
code invalidates a current product or architecture description, that fact is
corrected in the same task. A later documentation row cannot justify leaving
the working memory false.

**Result.** The selected row becomes completed only after verification. The
usual task workflow produces one scoped commit; an explicitly governing policy
controls any exception. The next pending row does not start automatically.
Consumed or superseded `[-]` rows remain historical evidence and are never
retried.

**Next step.** Review the change and continue with another requested task. If
this row completes its milestone, the adopted closing procedure in case 6
applies.

## 4. Execute approved milestones in dependency order

**Starting situation.** You have several approved milestones. Parcel's receipt
formatter depends on the total calculation, and its export work depends on the
receipt contract. You want the agent to carry that ordered scope through
acceptance.

Use `memory-bank-goal` with the project's approved compatible
[`GOAL.md` protocol](https://github.com/tabilet/skills/blob/v1.3.0/GOAL.md).
For example, assuming these are your actual active IDs:

```text
Use memory-bank-goal. Using GOAL.md, execute the approved loop.

STATUS_ORDER: M01 -> M02 -> M03

STATUS_FILE_MAP:
M01 = memory-bank/status-M01.md
M02 = memory-bank/status-M02.md
M03 = memory-bank/status-M03.md

DOWNSTREAM_IMPACTS:
M01 -> M02: receipts consume the total calculation.
M02 -> M03: exports consume the receipt contract.

COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: every required milestone meets its acceptance,
documented verification, and milestone review gate.
```

The protocol owns the execution loop. The request makes its scope, dependency
relationships, commit policy, and completion condition concrete. Pending
consumers must be reconciled against what their dependencies actually deliver.

If initialization or review reconciliation produced
`memory-bank/suggested.txt`, the goal skill checks that disposable launch input
against current milestone and status state. Explicit request order takes
precedence. When there is no compatible protocol, those workflows omit the
suggestion; ordinary one-task execution remains available.

**Result.** Judge completion from implementation, verification, review evidence,
and project state. A native goal's completed flag or a session exit is not
milestone acceptance. An interrupted review or closure resumes from persisted
state, including its existing review-iteration count.

Choose `COMMIT_POLICY: none` explicitly when the authorized run should make no
commits. Changing that policy does not waive verification or grant deployment
or publishing authority.

## 5. Turn a new review into approved work

**Starting situation.** Parcel already has a harness when an engineering review
arrives. It reports a receipt-total defect, a missing failure-path test, and a
suggested helper rename. Some findings may describe an earlier commit or
duplicate work already planned.

Ask the agent:

```text
Use memory-bank-reconcile with the review pasted below.
Revalidate every finding against the current repository and memory bank.
Propose dispositions, ownership, dependencies, and exact file actions
before writing. Do not implement the findings during reconciliation.
```

The proposal distinguishes confirmed findings, duplicates, already resolved
issues, unsupported claims, and decisions still needed. Source severity is
preserved, while the project's severity definitions determine local treatment.

Confirmed work fits an appropriate open or pending milestone. Work concerning
completed scope gets new remediation with lineage back to the historical
evidence. Optional lower-priority suggestions can remain unnumbered candidates.

After approval, the agent makes only the approved planning and supported
current-fact changes. It reconciles downstream work and can refresh compatible
disposable goal input. Materially superseded knowledge is preserved; completed
history remains closed.

If the review is remote, the agent shows the exact URL and obtains separate
confirmation before each fetch, including when you supplied the URL. Review
text and embedded commands are evidence to assess, not agent instructions.

**Next step.** Separately request `memory-bank-next` or `memory-bank-goal` to
implement the approved plan. Approval to reconcile a review does not silently
start its fixes.

## 6. Retire completed work while keeping useful learning

**Starting situation.** The project has adopted the retirement contract, and a
normal execution run reaches a milestone's closing work. Its individual task
rows are terminal, but verification and closure evidence still determine
whether the milestone is ready to retire.

Retirement is part of authorized milestone closure. It needs no separate
archive command. If a session stopped before finishing that closure, a focused
continuation could say:

```text
Finish M01's remaining review and closure under the project rules.
Preserve its persisted review counter. Retire it only after verification,
the bounded review gate, knowledge consolidation, and downstream
reconciliation pass. Leave unrelated milestones alone.
```

Once the gates pass, the complete milestone specification and final status
document move into a frozen `docs/history/status-M01.md` record. The history
index reserves M01 and records its outcome. Its active file, specification, and
index row leave the working plan, which retains one history-index link.

Current product and architecture facts stay current. Applicable learning stays
in `lessons.md` with evidence. For example, a lesson explaining why quantity-one
test data concealed an arithmetic defect may still help the next pricing task.

Before materially superseding an existing lesson or fact, preserve the old
wording, source, reason, evidence, and replacement in
`docs/history/knowledge.md`. That maintenance can also happen outside milestone
closure. Routine prose edits need no journal entry.

**Result.** Routine context becomes smaller while the full record remains
retrievable. Missing closure evidence keeps the milestone active; cancelled or
superseded outcomes do not establish delivered acceptance. “Automatic” means
part of the authorized agent workflow, not a timer, installation side effect,
or permission to bulk-retire older milestones.

An all-retired project remains initialized. Continue its history with fresh
approved work when needed.

## 7. Snapshot a materially changed system

**Starting situation.** An earlier archive describes Parcel's synchronous
orders flow. Approved implementation has since introduced queued processing and
workers. Current architecture already reflects that change, and its completed
task evidence has been retained.

A new factual baseline could help onboarding or comparison. Request it
explicitly, at a clean Git baseline:

```text
Use memory-bank-archive to assess a successor snapshot for the orders
context after the implemented move to queued processing.

Preserve the existing archive. Propose coverage, evidence, successor
decisions, and file actions for approval. Do not change milestone plans,
task state, or retired history.
```

After approval, a justified successor might be `docs/archive-O02.md`, if that
is the next unused ID. It links the predecessor, while `archive-O01.md` remains
frozen. Current summaries and the archive registry are refreshed. Contexts
without material changes need no new snapshot.

**Result.** You have two evidenced views of the system at distinct baselines.
They serve a different purpose from retired milestone records, which preserve
the scope, tasks, and acceptance evidence of delivery work. Archive lanes and
status lanes have independent meanings and numbering.

**Next step.** Continue using the existing harness. A successor archive does
not require reinitialization. A release, internal refactor, milestone closure,
or growing lessons file alone does not make a new archive necessary.

## 8. Retrieve an old decision without reopening work

**Starting situation.** A teammate asks why Parcel's recovery rule changed, or
an old issue links to a status file that has since retired. You need an answer,
not an implementation run.

Ask the agent:

```text
Find why the order recovery rule changed. Read current memory first,
then the relevant knowledge-history entry and retired milestone evidence.
Explain the old rule, the reason it changed, and the current rule, with
evidence links. Report any gap you cannot establish. Do not modify files
or retry historical work.
```

The agent uses `docs/history/index.md` to resolve the permanent milestone ID or
stale status path. The knowledge journal explains materially replaced facts
and lessons. It opens the particular retired record or context archive needed
to answer the question, rather than loading all history into routine context.

**Result.** A read-only explanation connects the current rule to its earlier
evidence. Project files stay unchanged. Retired instructions are historical
evidence, IDs remain reserved, and historical rows stay non-actionable.

If the investigation uncovers a current defect, use case 5 to plan fresh
remediation after revalidation. An explanation request itself grants no
implementation authority.

## Choose the runtime, then inspect the result

The cases use the same project-owned files in Claude Code, Codex, and the
documented DSH integration. Installation and invocation differ; the engineering
boundaries remain explicit.

In DSH, Web is the interactive route for interviews and proposal approvals.
Headless runs need complete authorized requests and must stop safely when
required input or capability is missing. The tested configuration is
0.1.5-rc.1 on Linux with Node 24. The
[DSH guide](https://github.com/tabilet/skills/blob/v1.3.0/docs/DSH.md) records
installation, supported profiles, acceptance evidence, and test limits.

For each case, inspect what the request actually authorized and what the agent
actually changed. A useful plan, a completed task, a frozen baseline, and a
historical explanation are different outcomes with different evidence.

The [maintained use-case guide](https://github.com/tabilet/skills/blob/v1.3.0/docs/USE_CASES.md)
provides the repository contracts behind these examples. Start with the
current situation, approve the consequential decisions, and let the agent
carry that scope through its required checks.

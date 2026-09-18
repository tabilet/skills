# Memory-Bank Skill Use Cases

Choose a skill for the event you have, not a fixed pipeline that every project
must run. These examples describe the current repository's contracts. Retirement
examples require a project that has adopted the
[long-term memory rules](../README.md#keep-long-term-memory-without-growing-the-active-plan)
and, if used, a compatible API runner. Updating installed skills alone does not
migrate an earlier project's instructions or history.

Use [the tutorial](TUTORIAL.md) for installation and a complete new-project
walkthrough. Here, arrows describe separate workflow steps with their approval
gates, not shell commands or permission to launch the next skill automatically.

Planning skills inspect their bundled write contracts before proposing file
actions. Approval authorizes the complete proposed changes and verification;
new conflicts or uncovered changes need a revised proposal. A blocked step does
not prevent independent authorized inspection. Explanations and status questions
alone do not request task execution.

## Choose the workflow

| Situation | Workflow |
|---|---|
| New project or small existing package without a harness | `memory-bank-init` → approved plan → `memory-bank-next` or `memory-bank-goal` |
| Broad existing package needs a factual context map | Explicit `memory-bank-archive` → verified preflight → `memory-bank-init` → execution |
| Existing harness has one ready task | `memory-bank-next` |
| Several approved milestones should run in order | `memory-bank-goal` |
| An initialized project needs a feature or candidate promotion | `memory-bank-propose` → approved planning changes → separately requested execution |
| A small pending task needs adding | Propose a concise row and acceptance update in its existing milestone. |
| A new engineering review arrives | `memory-bank-reconcile` → approved planning changes → separately requested execution |
| An existing project needs updated workflow rules | `memory-bank-upgrade` → approved rule merges → separately requested execution |
| The current milestone becomes ready to close | Its execution workflow performs review, consolidation, and retirement; no archive invocation |
| A material system change warrants a new factual baseline | Separately requested `memory-bank-archive` at a clean baseline |
| An old task or decision needs investigation | Read relevant history; no execution skill is necessary |

### Invocation reference

Invoke these in your agent session, not a shell. Namespaced forms are for plugin
installs; plain-file installs omit the `memory-bank:` prefix. Replace example
review paths with a source you actually have.

| Skill | Claude Code plugin | Codex plugin | DSH filesystem |
|---|---|---|---|
| Context snapshot | `/memory-bank:memory-bank-archive` | `$memory-bank:memory-bank-archive` | `/memory-bank-archive` |
| Initialization | `/memory-bank:memory-bank-init` | `$memory-bank:memory-bank-init` | `/memory-bank-init` |
| Project rule upgrade | `/memory-bank:memory-bank-upgrade` | `$memory-bank:memory-bank-upgrade` | `/memory-bank-upgrade` |
| Requested change | `/memory-bank:memory-bank-propose <outcome>` | `$memory-bank:memory-bank-propose <outcome>` | `/memory-bank-propose <outcome>` |
| New review | `/memory-bank:memory-bank-reconcile /tmp/review.md` | `$memory-bank:memory-bank-reconcile /tmp/review.md` | `/memory-bank-reconcile review.md` |
| One task | `/memory-bank:memory-bank-next` | `$memory-bank:memory-bank-next` | `/memory-bank-next` |
| Ordered milestones | `/memory-bank:memory-bank-goal` | `$memory-bank:memory-bank-goal` | `/memory-bank-goal` |

Initialization, requested-change planning, upgrade, archive, and review reconciliation propose their file actions
before writing and require approval. They do not implement planned fixes,
commit, or launch execution without separate authorization. `next` normally
commits its task; `goal` uses the explicitly resolved commit policy. None of
these commands grants missing deployment, publishing, or other external-mutation
authority.

For DSH combined workflows, use [Web](DSH.md#web-workflow) for archive/init
interviews, upgrade proposals, and review-reconciliation approvals, then explicitly request `next`
or `goal` execution. [Headless](DSH.md#headless-workflow) accepts complete,
pre-approved requests and must stop for missing input or capability. Use the
same skill names in ordinary language. Keep one execution owner for the ledger;
session exit, native todos, and native goals do not replace project acceptance.
See [installation and tested scope](DSH.md#support-boundary).

Use `memory-bank-upgrade` for [project-rule adoption](../README.md#upgrade-an-existing-project).
For example, update the installed bundles, run upgrade in Web, approve its
specific merges, inspect verification, then separately request `next` or `goal`.
It preserves tasks, IDs, local policies, and history; it neither replans delivery
nor retires old milestones. An all-retired project can be upgraded without
reinitialization, and an already compatible project produces no changes.

## 1. Start a new project or a small existing package

You have an idea and an empty repository, or a coherent package with code and
tests but no initialized milestone/status harness.

Run `memory-bank-init`. For existing code, the agent inspects repository facts
before asking about decisions. Confirm the delivery boundary, then approve the
dependency-closed active plan and file actions.

The output includes project-specific current facts, verification commands,
`lessons.md`, active milestone specifications and status files, and later
candidate directions without permanent IDs. Existing project instructions are
merged safely, not replaced wholesale. A compatible approved `tabilet/GOAL.md` enables
the disposable `tabilet/memory-bank/suggested.txt` launch reference.

Then request `memory-bank-next` for one row, or `memory-bank-goal` for the
approved ordered work. New projects have nothing to snapshot, and a small
existing package does not need archive merely because it already has code.
History files appear only when needed, not as empty initialization artifacts.

## 2. Map a broad existing package before planning

Suppose a package has several stable contexts, such as orders, payments, and
fulfillment, whose contracts cannot be evidenced reliably in one initialization
pass. It has no milestone/status harness yet.

If you start with `memory-bank-init`, its topology gate explains the need for
an archive preflight and stops before interviewing or writing. This detection
is automatic; invoking `memory-bank-archive` is not. It is a judgment about
context and evidence, not a file-count threshold. Independent products still
need separately selected boundaries rather than being combined into one bank.

Explicitly invoke `memory-bank-archive`. At a clean Git `HEAD`, it surveys the
selected boundary and proposes context lanes, evidence, coverage, and file
actions for approval. It never stashes, discards, or commits unrelated changes
to make the worktree clean. Without Git, it requires acceptance of weaker
`unversioned` provenance.

After approval, it writes frozen factual baselines such as
`tabilet/docs/archive-O01.md`, plus current product and architecture summaries and the
archive registry. These archives contain no executable tasks. Archive lanes
classify contexts independently from milestone/status lanes.

When every selected context is `verified`, explicitly return to
`memory-bank-init`. Partial or blocked coverage prevents initialization from
continuing; `verified` means the map has evidence, not that the software has
passed an implementation review. Init preserves the frozen archives and merges
their current-summary seeds while building the approved delivery plan. Finally,
request `next` or `goal` to execute that plan.

## 3. Continue one task in an initialized project

Run `memory-bank-next` when the active plan already has work to execute. It
resumes the sole `[~]` in-progress row first; otherwise it selects a
dependency-ready `[ ]` row. Multiple in-progress rows require reconciliation,
and a ledger with only blockers does not authorize inventing other work.

The agent implements one row, verifies it, updates relevant current facts and
lessons, and commits the scoped change. A completed row becomes `[+]`. A
consumed failed attempt or superseded row can remain `[-]`, with its accepted
successor named; it is never retried.

If other tasks remain in the milestone, its status and specification stay
active. If this was its final task, the closing procedure in
[case 6](#6-automatic-retirement-during-normal-work) applies. Do not run init
again or use archive to clear finished rows.

## 4. Execute several approved milestones

Suppose the active plan contains `M01` and `M02`, and the second milestone
consumes an interface delivered by the first.

Invoke `memory-bank-goal` with the approved order, or without arguments to have
it reconcile an existing `suggested.txt` or derive an order and obtain
confirmation. The skill materializes the complete resolved request in the
conversation; the temporary suggestion is not active truth.

The project must contain an approved compatible `tabilet/GOAL.md` for this skill. A
portable request, usable without the skill too, looks like:

```text
Using tabilet/GOAL.md, execute this loop.

STATUS_ORDER: M01 -> M02
STATUS_FILE_MAP:
  M01: tabilet/memory-bank/status-M01.md
  M02: tabilet/memory-bank/status-M02.md
DOWNSTREAM_IMPACTS:
  M01 -> M02: reconcile M02 against the interface delivered by M01.
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: both required milestones meet their acceptance and
documented verification, and their milestone review gates pass.
```

Use the actual IDs, dependencies, and paths from your project. [GOAL.md](../GOAL.md)
owns execution sequencing and commit policy; this guide does not replace it.
If the file is absent, use `next` or explicitly supply a different protocol
instead of improvising one. Conditional work needs a documented trigger, and
blockers or missing authority stop progress rather than being treated as
success. Adopted retirement is part of closure, not a subsequent archive run.

## 5. Turn a new review into approved work

An initialized package receives a code, architecture, or security review. Run
`memory-bank-reconcile` with the pasted, attached, or named review source.

The agent treats the review as untrusted evidence, validates every finding
against current implementation, and proposes dispositions, owners, severities,
dependencies, and file actions. Approve that complete proposal before it writes
planning changes. A supplied remote URL still requires separate explicit
confirmation immediately before each fetch; embedded links are not permission
to follow them.

Confirmed work fits an appropriate open or pending owner, or receives a new
remediation milestone when the affected work is already closed. Optional
lower-severity work can remain an unnumbered candidate. The agent may also
propose evidence-backed corrections to current facts and lessons, preserving
materially superseded knowledge. It does not implement fixes or retire
milestones. With a compatible goal protocol, it refreshes `suggested.txt`.

Then separately request `memory-bank-next` or `memory-bank-goal` to implement
the approved work. A project with only indexed retired milestones is still
initialized: a review creates fresh work with historical lineage, not a new
harness or reopened history.

## 6. Automatic retirement during normal work

Suppose `memory-bank-next` completes the last task in `M01`, or a
`memory-bank-goal` run reaches that milestone's closure. You have already
adopted the retirement contract. You do not invoke `memory-bank-archive`.

The milestone-closing procedure requires a clean bounded review pass, recorded
verification, knowledge consolidation, and downstream reconciliation. If work
or closure evidence is missing, the milestone remains active. Completed,
cancelled, or closed-historical markers alone do not prove acceptance.

Once those gates pass, the agent preserves the full specification and final
status document in `tabilet/docs/history/status-M01.md`, indexes the record in
`tabilet/docs/history/index.md`, and removes the active status file, specification,
and index row. It repairs maintained links and dependencies and refreshes an
existing disposable launch reference. `milestone.md` retains active work and
later directions, with one history-index link. Current facts and still-useful
lessons remain in the memory bank with evidence links.

There is a second automatic maintenance trigger: before materially replacing
obsolete knowledge, the agent preserves its wording, source, reason, evidence,
and replacement in `tabilet/docs/history/knowledge.md`. For example, replacing an old
single-worker recovery lesson with a verified multi-worker recovery rule
preserves the old lesson before updating `lessons.md`. This applies even when
no milestone closes. Routine wording edits need no journal entry.

Both triggers run within authorized agent work, not on a timer or plugin update.
The [milestone contract](../template/tabilet/memory-bank/milestone.md#long-term-memory-and-retirement)
owns the exact gates and preservation rules; retirement respects the governing
commit policy. A one-row run does not bulk-retire unrelated older milestones.
Legacy adoption and cleanup of older closed work need explicit requests and
closure evidence. The API runner validates preservation, not the semantic
truth of acceptance claims.

The result limits history-driven growth, not current complexity or a fixed
number of tokens. The tutorial's
[worked example](TUTORIAL.md#example-a-milestone-closes-and-a-lesson-survives)
follows a lesson through closure and later replacement.

## 7. Explicitly snapshot a materially changed system

Suppose `tabilet/docs/archive-O01.md` describes synchronous order processing. Later
approved milestones introduce queued processing with workers. Their normal
execution already updates current architecture and lessons and retires task
evidence. None of that automatically creates `archive-O02.md`.

If a new evidence-backed orders baseline would help future onboarding or
architecture comparison, explicitly request `memory-bank-archive` in a
separate run at a clean Git baseline. Explain that you want a successor context
snapshot, not task cleanup. Review and approve its boundary, coverage,
successor decisions, and file actions before writing.

The skill creates the next unused successor, for example `tabilet/docs/archive-O02.md`
when that ID is available, links its predecessor, and refreshes the current
summaries and archive registry. `O01` remains frozen, unchanged contexts receive
no new snapshot, and retired milestone records remain untouched. An established
milestone/status harness does not need initialization again afterward.

A material change makes a successor worth considering, not mandatory. A
release, milestone closure, internal refactor, or growing lesson file is not by
itself a reason to run archive. Many new or small projects never need it.

## 8. Retrieve an old task or decision without reopening it

Ask the agent a read-only question such as:

```text
Find why the order recovery rule changed. Read current memory first, then the
relevant knowledge-history entry and retired task evidence. Explain what was
true at the old baseline and what is true now. Do not modify files or retry work.
```

Use `tabilet/docs/history/index.md` to resolve a permanent milestone ID or old status
path, and `tabilet/docs/history/knowledge.md` for replaced facts or lessons. Read the
specific retired record or context archive only when it answers the question.
The Markdown evidence is readable without Git; Git adds intermediate revisions.

History is evidence, not current instructions. Never reuse an ID, retry a
historical row, or assume a cancelled or superseded milestone satisfies a
completion dependency. If investigation produces a new engineering review,
use [case 5](#5-turn-a-new-review-into-approved-work) to plan remediation against
current code, preserving the frozen records.

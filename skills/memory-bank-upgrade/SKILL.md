---
name: memory-bank-upgrade
description: Upgrade an existing memory bank's workflow rules through approved merges, preserving project plans, local policies, and history. Use after installing newer skills.
disable-model-invocation: false
argument-hint: [workflow changes to adopt]
---

# Upgrade An Existing Memory Bank

Compare the project's adopted workflow with the contract bundled in this skill,
propose precise file actions, then apply only the approved changes. Installing
this skill does not migrate a project. An upgrade changes operating rules; it
does not complete tasks, replan delivery, or retire old milestones.

Resolve missing information through safe inspection first. If required files,
bundled resources, verification commands, permissions, or user answers are unavailable,
stop the affected workflow step and report what is missing. Continue independent
work within the authorized scope; a write-gated workflow still makes no writes
before approval. Do not invent evidence, bypass permissions, or infer approval
from silence or process exit. Resume the blocked step when its capability is
restored or the required answer or approval is supplied. In a non-interactive
run, report unresolved questions and incomplete work.

Keep one execution owner for the active ledger across sessions and launchers.
Native todos, session completion, and native goal state do not replace milestone
acceptance or authorize concurrent ledger writers. Stop execution on that ledger
before applying an upgrade; a second session cannot safely merge its rules while
another writer advances tasks.

## Inspect and compare

Read the project's applicable instructions and memory bank. Require an existing
milestone/status harness: active status files or valid indexed retired history
with `memory-bank/milestone.md`. An all-retired project remains initialized.
Route a new project to initialization; treat partial or inconsistent existing
state as a repair question, never permission to overwrite it or start over.

Resolve resources relative to this skill's directory. The complete
[bundled template](assets/template/) is the target contract, not a scaffold to
copy over the project. Read its [agent rules](assets/template/AGENTS.md),
[milestone rules](assets/template/memory-bank/milestone.md),
[status rules](assets/template/memory-bank/status-M01.md), and
[lessons convention](assets/template/memory-bank/lessons.md) before proposing.
Consult other bundled files only when their contract is relevant. Never apply
example tasks, example IDs, or bracketed placeholders as project content.

Inventory the current facts, custom rules, actual verification commands, active
specifications and row states, permanent IDs in both locations, candidate
directions, archives, knowledge journal, and optional goal protocol and launch
reference. Record file hashes or equivalent read-only evidence for the proposed
write set and protected state. Preserve unrelated uncommitted changes; do not
stash, discard, commit, or require a clean worktree just to inspect.

Compare behavior and contracts, not wording or a guessed installed version.
Identify missing capabilities, compatible local equivalents, deliberate local
overrides, and conflicts needing decisions. In particular, check curated lessons,
knowledge preservation, retirement provenance and literal records, reserved IDs,
all-retired identity, six task markers, sole in-progress ownership, current-fact
maintenance, and the persisted ten-iteration review gate. Never reset an active
review count or reinterpret cancellation/supersession as delivered acceptance.

If the project uses the API runner, inspect its actual executable or documented
version for retirement compatibility. This skill does not update account-level
executables, installed plugins, credentials, or runtime configuration. If that
compatibility cannot be established, leave retirement adoption blocked and name
the separate runner update/check needed; do not claim the project is ready.

## Propose and obtain approval

Show each difference, its current evidence, the proposed rule or retained local
equivalent, and its impact. Present every file action as create, merge, preserve,
or remove. Prefer focused diffs for changed sections; use replacement text for
new sections. Summarize preserved content instead of repeating unchanged files.
Include all conflicts and unresolved decisions. If the proposal spans responses,
finish presenting every change before requesting approval. Write nothing yet.

Prefer a scoped merge into `AGENTS.md` and the workflow sections of
`memory-bank/milestone.md`. Preserve project-specific scope, acceptance,
dependencies, candidate directions, commands, and policies. Existing status
files may receive approved rule/preamble updates; their task tables, row notes,
markers, and persisted review evidence remain unchanged. Allocate no status ID.

Adapt optional runner, goal, and evolution instructions to the project's explicit
exclusions. Do not import commands, reporting obligations, or implied requirements
for unused systems. A descriptive or conditional mention alone is not a missing
capability or a reason to require adoption. Preserve these scope decisions on a
repeat run; cosmetic differences from the template do not prevent a no-op.

Create `memory-bank/lessons.md` only when approved and absent. Preserve an
existing lessons file; propose a compatible structure without deleting its
learning. Do not invent lessons: an explicit statement that none are established
is sufficient. Keep current facts and frozen history intact; if resolving a
conflict would materially supersede knowledge, propose that separate maintenance
work rather than silently changing it as an upgrade.

The project's `GOAL.md` is optional. Preserve an absent, customized, or different
protocol by default. Offer the [bundled protocol](assets/template/GOAL.md) only
as an explicit create/replace decision; if approved, copy it byte-for-byte.
Never synthesize it from memory or execute it during upgrade. Preserve existing
launch input and its explicit policies when compatible. Propose removal of a
stale or incompatible disposable reference when necessary; do not create a new
one or use it to launch execution.

Do not create history directories, retire completed milestones, rewrite retired
records/index entries or knowledge history, or create a migration ledger/version
stamp. Existing completed work stays where it is. Record an evolution change
only if the project's documented trigger applies and that action is approved.

Obtain approval for the complete proposal before writing. A request to upgrade
or a blanket approval of unseen changes is not approval of its specific merge.
A headless continuation needs the exact previously approved proposal and scope;
silence or an earlier session's completion is not consent.

## Apply and verify

Re-read the proposed files and protected state before mutation. If they changed
since the proposal, stop the affected merge and present a revised proposal.
Apply only the approved actions; preserve unrelated content and local policies.
Continue through verification and handoff without requesting approval again for
those same actions. New conflicts or uncovered changes need a revised proposal.
An interruption requires comparing the current diff with the approved proposal
and original evidence before resuming, never replacing partially merged files
wholesale. When already compatible, report a no-op without touching files.

Verify the resulting diff against the approval and original evidence:

- active IDs, task tables/notes, specifications, acceptance, candidate directions,
  and review counts are unchanged;
- frozen archives, retired records/index entries, and knowledge history retain
  their original bytes, and an all-retired project stays initialized;
- new rules point to existing project files, omitted optional features leave no
  dead links, and no unfilled project placeholder or example task was introduced;
- an approved bundled `GOAL.md` copy is byte-identical and the resolved commit
  policy remains explicit; and
- applicable structural and project verification passes, with unavailable checks
  reported as incomplete rather than passed.

Do not implement tasks, commit, tag, push, publish, install personal skills,
fetch remote reviews, or launch another workflow without separate authorization.
Report the adopted rules, preserved overrides, exact files changed, verification,
and remaining incompatibilities. Point out any separate runner update or later
retirement request still needed. An upgrade is complete only for the approved
scope whose compatibility and checks are established.

---
name: memory-bank-upgrade
description: Upgrade an existing memory bank's workflow rules through approved merges, preserving project plans, local policies, and history. Use after installing newer skills.
disable-model-invocation: false
argument-hint: "[workflow changes to adopt]"
---

# Upgrade An Existing Memory Bank

Before reading project state for this workflow, inspect the root layout. If
`GOAL.md`, `memory-bank/`, `evolution/`, `docs/history/`, or
`docs/archive-<LANE><NN>.md` exists in a v1.5.0 or mixed layout, stop before
project writes or execution. Direct the user to preview and explicitly apply
`skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`.
Installing v2 never migrates a project automatically.

For optional interactive auditing, read the bundled
`references/optional-audit.md` and use the optional installed `tabilet-audit`
toolkit. Report unavailable logging as a gap without changing workflow approvals
or outcomes. Inside the API runner, its recorder owns the lifecycle; do not start
a duplicate audit run.

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

For required amendments, optional discoveries or parent closure, read
[the milestone-family contract](references/milestone-families.md). Apply its
classification, deferred-option policy and original-acceptance safeguards.

## Inspect and compare

Read the project's applicable instructions and memory bank. Require an existing
milestone/status harness: active status files or valid indexed retired history
with `tabilet/memory-bank/milestone.md`. An all-retired project remains initialized.
Route a new project to initialization; treat partial or inconsistent existing
state as a repair question, never permission to overwrite it or start over.

Resolve resources relative to this skill's directory. The complete
[bundled template](assets/template/) is the target contract, not a scaffold to
copy over the project. Read its [agent rules](assets/template/AGENTS.md),
[milestone rules](assets/template/tabilet/memory-bank/milestone.md),
[status rules](assets/template/tabilet/memory-bank/status-M01.md), and
[lessons convention](assets/template/tabilet/memory-bank/lessons.md) before proposing.
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
overrides, and conflicts needing decisions. In particular, check the
requested-change procedure, curated lessons, knowledge preservation, retirement
provenance and literal records, reserved IDs, all-retired identity, six task
markers, sole in-progress ownership, current-fact maintenance, and the persisted
ten-iteration review gate. Never reset an active
review count or reinterpret cancellation/supersession as delivered acceptance.
The optional stage rules may be adopted without creating `tabilet/stages.md` or
replanning delivery. Preserve an existing stage overview and its stable IDs;
Init or Propose owns any new stage structure and approved pending-work rescope.

If the project uses the API runner, inspect its actual executable or documented
version for retirement compatibility. This skill does not update account-level
executables, installed plugins, credentials, or runtime configuration. If that
compatibility cannot be established, leave retirement adoption blocked and name
the separate runner update/check needed; do not claim the project is ready.

## Propose and obtain approval

Offer the standing corrective-planning and optional approval-email guidance in
the approved rule merge. Preserve existing explicit policies; an absent
`CORRECTIVE_PLANNING` remains `confirm`. Installation never opts a project into
`auto`, configures a sender or supplies an email recipient. Existing launch
input may display the preserved corrective policy, while email opt-in belongs
to a later human Goal/Next request. The API paths consume neither feature.

Show each difference, its current evidence, the proposed rule or retained local
equivalent, and its impact. Present every file action as create, merge, preserve,
or remove. Prefer focused diffs for changed sections; use replacement text for
new sections. Summarize preserved content instead of repeating unchanged files.
Include all conflicts and unresolved decisions. If the proposal spans responses,
finish presenting every change before requesting approval. Write nothing yet.

Prefer a scoped merge into `AGENTS.md` and the workflow sections of
`tabilet/memory-bank/milestone.md`. Preserve project-specific scope, acceptance,
dependencies, candidate directions, commands, and policies. Existing status
files may receive approved rule/preamble updates; their task tables, row notes,
markers, and persisted review evidence remain unchanged. Allocate no status ID.

Adapt optional runner, goal, and evolution instructions to the project's explicit
exclusions. Do not import commands, reporting obligations, or implied requirements
for unused systems. A descriptive or conditional mention alone is not a missing
capability or a reason to require adoption. Preserve these scope decisions on a
repeat run; cosmetic differences from the template do not prevent a no-op.

Offer authorization guidance only as explicit adoption: optional milestone
`AUTHORIZATION_REQUIREMENTS` and human-approved request `AUTHORIZATION_GRANTS`
(including the goal protocol's optional grant `standing` revision envelope).
Absence grants no new authority and triggers no automatic migration. Preserve
project restrictions and existing scoped human policies; reconcile conflicts
in the complete proposal. Keep requirements in milestone specifications and
status preambles as pointers. Do not add duplicate declarations, invent grants,
mark proposed grants effective, or use upgrade approval as execution authority.
Preserve approval context only in the conversation or existing trusted host
state where supported; create no repository approval ledger or audit dependency.
Installing or adopting this guidance does not add grant consumption to the
Python API runner/controller or remove the controller's external-action ban.

Create `tabilet/memory-bank/lessons.md` only when approved and absent. Preserve an
existing lessons file; propose a compatible structure without deleting its
learning. Do not invent lessons: an explicit statement that none are established
is sufficient. Keep current facts and frozen history intact; if resolving a
conflict would materially supersede knowledge, propose that separate maintenance
work rather than silently changing it as an upgrade.

The goal protocol now ships with the skills: this bundle carries the stock
[GOAL.md](GOAL.md) and its fingerprint registry `goal-protocol.json`, and
projects no longer keep a copy. A project's `tabilet/GOAL.md`, when present, is a
project addendum that narrows the stock protocol at run time. Classify an
existing file with the registry, using its CRLF-to-LF normalized fingerprints
as the stock protocol's Protocol Resolution And Identity section describes, and
include the result in the complete proposal. Version labels are descriptive;
compare hashes and classifications. Launch checksums remain raw-byte hashes:

Resolve explicit `GOAL_PROTOCOL` selection first. Preserve a file selected as
the alternative full protocol; do not classify it as an addendum to truncate
or remove. Its package identity is `selected-protocol sha256:<hash>`.

- byte-identical to a released stock copy: propose removing it, since the
  bundled protocol supersedes it;
- a full protocol copy with local edits: show the local differences against the
  closest released copy and propose reducing the file to those project-specific
  rules; the user decides, and goal runs stop on it until it is reduced;
- anything else, including a project record: keep it as the addendum, and flag
  any rule in it that would weaken a stock gate.

Never write a merged protocol, synthesize one from memory, or execute it during
upgrade. Rewrite `AGENTS.md` and `milestone.md` pointers that describe
`tabilet/GOAL.md` as the protocol so they name the bundled goal protocol and the
optional addendum. Offer the template's Out of scope register as explicit
adoption.

Before removing or reducing a stock protocol file, inspect maintained incoming
links throughout the project, including guidance outside `AGENTS.md` and
`milestone.md`. Include each required reference repair in the approved proposal.
Current execution pointers name the bundled protocol and optional addendum.
An unfrozen historical reference may become an explicitly labelled historical
source reference with its recorded revision/path; never substitute current
protocol semantics for an earlier approval. Preserve frozen records byte-for-byte
and resolve their literal paths in the original source-commit context. If a
required reference cannot be preserved or resolved, preserve the protocol file
pending an approved solution instead of leaving an unexplained broken link.

When existing `tabilet/memory-bank/suggested.txt` is found and the selected
governing protocol is available and compatible, include its refresh in the same proposal.
Preserve explicit `GOAL_PROTOCOL` selection and its actual path/hash; use the
bundled registry's version/hash only for stock selection. Keep the invocation,
`GOAL_IDENTITY` and applicable package addenda consistent with that selection.
A protocol switch requires explicit approval; unavailable or incompatible
selection pauses affected launch refresh and preserves existing input.
Do not remove or truncate a file currently selected as the alternative full
protocol merely because the stock addendum classifier would reject it.
Preserve explicit `MODEL_POLICY`; omission preserves host model settings.
Propose the optional policy only when requested, without activating it on a
paused run. A fresh legacy launch without `GOAL_IDENTITY` follows the protocol's
legacy-launch transition: show the resolved identity and obtain missing identity
approval, preserving grants and limits; launch writes still require approval.
For legacy goals lacking `GOAL_IDENTITY`, compare the previously
approved protocol path/hash with the proposed resolution, show the transition,
and obtain approval for a changed or uncertain identity. Preserve grants,
denials, review counters, attempt usage and operational limits; installing or
adopting an upgrade never silently resumes a goal. Reconcile
the whole current approved active horizon, permanent IDs, status paths,
dependencies, conditional triggers, and downstream impacts before rewriting.
Preserve explicit selection (`STATUS_ORDER` or `STATUS_PRIORITY`), commit,
integration, external-mutation, launch-update (`SUGGESTED_UPDATE`), and user scope policies;
surface conflicts instead of resetting them to example defaults. Remove stale historical launch
entries only after reconciling their disposition. Keep valid unapproved grant
proposals labeled PROPOSED — NOT APPROVED; do not copy previous-run approval
as effective authority. Proposed grants in `suggested.txt` carry decision markers:
`[ ]` (need authorization), `[+]` (approve), `[-]` (deny), and `[~]` (auto), with optional
`GLOBAL:` grants for high-level scopes; goal execution requires matching SHA256 checksum.
Always emit `AUTHORIZATION_GRANTS: {}` when there are
no proposed explicit grants, or the concrete proposed mapping when present.
Requirements stay in milestone specifications and never become duplicate
declarations in launch input. Preserve an absent launch reference; this upgrade
does not create one by default. If the selected governing protocol is unavailable
or incompatible, preserve the launch reference pending resolution and explain
the blocker; any removal must be an explicit approved file action. An all-retired project gains
no executable IDs. Upgrading these files never activates grants or launches a
goal, and a repeat run with compatible files is a no-op.

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
- no protocol copy or merged protocol was written into the project, an approved
  `tabilet/GOAL.md` removal or reduction matches the proposal, and the resolved
  commit policy remains explicit; maintained incoming links resolve, and any
  historical source reference is identified with its original context;
- an existing refreshed launch reference matches live project truth, preserves
  explicit policies, includes `AUTHORIZATION_GRANTS` even when empty, and marks
  proposed grants as unapproved; absent optional files remain absent unless an
  approved file action creates them; and
- applicable structural and project verification passes, with unavailable checks
  reported as incomplete rather than passed.

Do not implement tasks, commit, tag, push, publish, install personal skills,
fetch remote reviews, or launch another workflow without separate authorization.
Report the adopted rules, preserved overrides, exact files changed, verification,
and remaining incompatibilities. Point out any separate runner update or later
retirement request still needed. An upgrade is complete only for the approved
scope whose compatibility and checks are established.

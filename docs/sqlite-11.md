# SQLite 11 — Explorer views and follow-up prompts

Plan state: [+]

Depends on: [SQLite 10 — Local server, API, and navigation](sqlite-10.md).

Next: [SQLite 12 — Acceptance, packaging, and documentation](sqlite-12.md).

This implementation ledger preserves the accepted contract and completion evidence.

## User experience

Implement the three views on the shared server and navigation from SQLite 10.
The overview is the landing page. Timeline and To-do remain one click away;
all three use the same source references, detail panel, and copyable follow-ups.

Summaries use recorded text and derived facts. The explorer does not make model
calls, execute agent work, or edit project planning records. Available evidence
stays readable when data is incomplete, while unvalidated task recommendations
remain unavailable.

## Overview

Start with the maintained project description and an attention area, then show:

| Section | Summary and drill-down |
|---|---|
| Active milestones and tasks | Maintained milestone summaries, acceptance criteria, current work, blockers, and separate counts for each state; open the milestone and its tasks. |
| History | Retired milestones grouped by completed, cancelled, and superseded outcome; open the preserved specification/status and provenance. |
| Archives | Contexts grouped by independent archive lane, with coverage, baseline, and predecessor/successor references; open the facts snapshot. |
| Evolution | Prompt/result pairs grouped by version, using their headings and introductory text; open either source and show an absent counterpart explicitly. |

The attention area highlights explicit blockers, interrupted or unfinished runs,
milestones awaiting closure, unresolved dependencies, and stale/invalid data.
Each attention item opens its evidence or an appropriate follow-up view.

Keep completed, cancelled, and historical row counts separate. Do not label a
milestone accepted merely because every task has a terminal marker. Active and
retired status IDs are one namespace; matching archive IDs remain independent.

Use maintained summaries and source excerpts rather than inventing descriptions.
Show a missing-summary state when no suitable text exists. Link summaries to their
source so users can inspect the exact wording and context.

## Timeline: two levels

### Level 1 — Workflow entries

Show one entry per recorded invocation, with newest first by default. Support
oldest-first order and filters for date, operation, milestone, and outcome.
Include all recorded operations: init, archive, propose, reconcile, next, goal,
and upgrade.

Each entry shows its timestamp, operation, outcome, request text or summary,
capture-fidelity label, and a compact result summary. Planning operations describe
what was proposed/approved/applied. Execution operations describe the observed
work, state changes, blockers, verification, and retirement. Archive operations
link their actual context outputs rather than implying they created milestones.

Group child operations under a goal entry without counting their transitions
again as separate parent achievements. Unfinished runs say they are unfinished;
elapsed time or process exit cannot establish completion.

### Level 2 — Invocation detail

Opening an entry displays, in order:

1. The request and relevant clarification or approval, when captured.
2. Proposed, approved, and applied outputs, with their phases distinguished.
3. Referenced milestones, observed task rows, archives, evolution, and documents.
4. Before/after task states, verification evidence, successful commit references,
   blockers, and recording gaps.

Provide clearly labelled **Recorded then** and **Current state** sections.
Historical sections use stored messages/events and selected observed output.
Current sections use the index or a labelled live preview. They may differ.

Resolve historical milestone links by permanent ID across active and retired
locations. Resolve task links only when identity is established by the SQLite 9
contract. If a task was renamed, duplicated, removed, or cannot be matched safely,
keep its original observation visible and explain that its current location is
unresolved. Do not present today's text as the original request's output.

Display the recorded fidelity: exact, redacted, summarized, or incomplete.
Without message capture, say **Request text was not captured** and show available
metadata. Do not reconstruct conversations from Git or document timestamps.

## To-do view

Use the readiness service from SQLite 9, not a second browser-side scheduler.
Present these groups with counts and reasons:

| Group | Display and follow-up |
|---|---|
| Resume | The sole validated in-progress row; explain why it owns the next execution step. |
| Ready | Numbered dependency-ready pending tasks; show the documented priority/order and row-order basis. |
| Waiting | Tasks with unsatisfied prerequisites, each linked to the prerequisite and its evidence. |
| Blocked | Explicit blocked rows, recorded blocker notes, and an investigation prompt. |
| Needs review | Unfinished milestone closure, cycles, ambiguous references, or invalid workflow state, with a review/clarification prompt. |

For each task show its milestone, label, state, prerequisites, dependents, notes,
and source path/line. A prerequisite link opens the corresponding detail panel.
Show blockers even when other tasks are ready; do not collapse blocked work into
an empty queue. Explain suggested ordering rather than claiming it overrides
project policy or creates an execution authorization.

Cancelled and historical rows remain inspectable in milestone/history details
but never become retry candidates. A cancelled or superseded prerequisite is not
silently satisfied. Unknown acceptance or unfinished closure remains a visible
workflow requirement.

When current source state cannot be validated, keep evidence available and show
why recommendations are withheld. An old index or a failed refresh must not
produce an apparently current numbered queue.

## Follow-up prompts

Offer four context-sensitive actions:

- **Continue this task** for the valid execution candidate.
- **Investigate this blocker** for a blocked task or unsatisfied prerequisite.
- **Review or close this milestone** for outstanding review/closure work.
- **Clarify this dependency** for an unresolved or contradictory relationship.

Before preparing an execution prompt, call the server to revalidate live source
hashes, the selected task, ledger ownership, dependencies, and closure state.
If these changed, show the changed evidence and require a fresh selection rather
than copying an outdated execution request.

The prompt includes the project, milestone/task reference, relevant source
locations, the requested outcome, and an instruction to reread current project
instructions and Markdown. It preserves existing approval and commit policies;
it does not preapprove external actions or silently promote a proposal. Use
ordinary text that can be pasted into the user's preferred agent. Do not force
a native goal request through the optional Tabilet goal protocol.

Show the prompt before copying. Copying does not change task state, create an
execution run, record milestone acceptance, or launch an agent. Provide a
selectable-text fallback when clipboard access is unavailable through the browser
or tunnel. Investigation and clarification prompts must not imply authority to
implement the blocked work.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL11-T01 | [+] | Build the overview and attention area from recorded summaries and facts. | Active work, history, archives, and evolution have source-linked summaries and accurate independent state/outcome counts. |
| SQL11-T02 | [+] | Build paginated timeline entries, filtering, and goal grouping. | All operations and unfinished runs are represented; ordering is stable and parent summaries do not double-count child evidence. |
| SQL11-T03 | [+] | Build invocation details and historical/current navigation. | Request-to-output drill-down preserves phases and capture fidelity; ambiguous or missing task links do not substitute current content for history. |
| SQL11-T04 | [+] | Build the explained To-do groups and dependency navigation. | Resume/Ready/Waiting/Blocked/Needs review agree with server classifications; invalid current state withholds recommendations while preserving evidence. |
| SQL11-T05 | [+] | Implement validated follow-up preparation, previews, and copying. | Prompts fit the selected action, reread source state, preserve project policies, and never edit or execute tasks. |
| SQL11-T06 | [+] | Complete keyboard, narrow-screen, empty-state, and degraded-data behavior. | All three views and shared details remain usable with missing messages, missing/invalid indexes, clipboard failure, and small screens. |
| SQL11-T07 | [+] | Verify cross-view behavior and review the complete user journey. | Browser and service tests cover request-to-output-to-current-task navigation and follow-up; no blocking findings remain before SQLite 12. |

## Verification and completion gate

Use fixtures containing proposals awaiting approval, rejected proposals, applied
changes, goal children, completed and blocked work, cancellation, supersession,
retirement, exact/summarized/missing capture, and changed or duplicate task labels.
Verify dependencies, cycles, incomplete closure, source changes during inspection,
and old generations retained after refresh failure.

Exercise keyboard-only navigation, browser back/forward, deep links, narrow
screens, search-to-detail transitions, pagination, and clipboard fallback.
Check that viewing/copying creates no project writes, audit execution runs,
model calls, or inferred approvals. Run focused browser/service tests and
`python3 check.py` before the milestone review.

Review iteration: 3 (cross-milestone deep review fixes applied). Run details now render captured
request/output messages and structured event/artifact references; source buttons
open live declared documents, global search opens indexed source matches, and
browser history does not push duplicate entries while restoring a deep link. The
credential-free service, isolated DOM, and Chromium suites cover the three views,
goal-child grouping, recorded/current navigation, dependency links, URL filters,
forward/back pagination, focus restoration, follow-up actions, polling, narrow
screens, clipboard fallback, and degraded states. Review requirements and stale
evidence remain visible while unsafe execution recommendations are withheld.

Review iteration: 4. Run detail exposes first-request and final-output summaries
independently of message pages, renders captured clarifications, approvals,
artifact relationships, state transitions, snapshot observations, and paged goal
children. Current task resolution uses recorded milestone scope, Overview counts
only active task rows, and large To-do groups retain their full totals without
rendering the entire ledger.

Review iteration: 5. Search, To-do, and invocation-detail page positions are
bookmarkable and restored by browser history. Detail URLs carry one selected
record, source references show a numbered excerpt around their exact line, and a
review requirement on another To-do page still withholds action buttons. Overview
attention items now link to their source, the To-do review, or the filtered
unfinished-run timeline instead of ending at an unlinked aggregate. The detail
surface is an accessible modal, closes with Escape, and preserves the original
trigger across detail pagination. A historical source line outside the current
document is reported as stale location evidence instead of being clamped to a
different line.

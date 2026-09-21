# SQLite audit and history storage

This document defines the first SQLite storage feature for Tabilet. It is a
design contract for implementation; it does not change the v2 project format
by itself.

## Decision

The first version stores an optional execution audit and optional snapshots of
retired history, knowledge history, and evolution files. Active milestones and
task rows remain in their v2 Markdown files. SQLite does not become an
active-work cache or an authority for task selection in this version.

This addresses a traceability gap: Git and status files show what changed, but
do not reliably retain which request caused a planning decision, when an event
occurred, or what happened during an interrupted goal run.

## Location and ownership

Use one external database per user account:

~~~text
${XDG_STATE_HOME:-~/.local/state}/tabilet/audit.sqlite3
~~~

Create its parent directory with owner-only access. Keep the database, WAL, and
shared-memory files outside projects and Git. Auditing is opt-in; installing a
skill or opening a project never creates the database.

The database is a local execution record. It is not a replacement for project
files, a shared coordination service, or proof that an event was authorized.
Captured requests and responses may contain source code, credentials, or private
material, so backup and sharing require an explicit privacy decision.

## Scope

Audit these operations:

| Operation | Recorded evidence |
|---|---|
| init | approved boundary, milestones, tasks, and file actions |
| archive | selected contexts, verification, archive identity, and provenance |
| propose | request, proposal, approval, and planning changes |
| reconcile | finding dispositions, owners, downstream changes, and approval |
| next | selected task, transitions, verification, and commit reference |
| goal | ordered work, outcomes, review, retirement, skips, and blockers |
| upgrade | approved workflow changes and migration result |

Milestone acceptance, retirement, cancellation, and supersession are distinct
events. A terminal task marker does not prove milestone acceptance.

Conversation capture is opt-in per run. Default auditing stores metadata and
event summaries. Selected capture stores only the relevant request, approval,
clarification, and skill output; it does not store every model turn, hidden
reasoning, credentials, or unrelated tool sessions. The database records
whether text is exact, redacted, summarized, or incomplete.

## Records

The schema version is tabilet.audit/v1. It provides:

- workspaces: a stable identity for each local checkout or worktree;
- runs: operation, workspace, timestamps, recorder version, parent/resumed run,
  Git HEAD, worktree state, and terminal result;
- events: append-only event ID, run sequence, timestamps, operation, event type,
  milestone ID, task label, original status path, old/new state, verification,
  file actions, commit references, and versioned JSON details;
- captured_messages: selected visible text with role, source, fidelity, and
  redaction metadata;
- snapshots and run_snapshots: exact history/evolution bytes and their run
  observations.

Events store task details as observed. They never reference row numbers or a
rebuildable tasks table. Reordering, renaming, retiring, or moving a status row
cannot reattribute an old event. Event IDs are idempotent; conflicting reuse is
an integrity error. Timestamps are UTC RFC 3339. Git provenance is nullable and
distinguishes clean, dirty, and unversioned state.

The versioned event envelope is:

~~~json
{
  "schema": "tabilet.audit.event/v1",
  "event_id": "random-id",
  "run_id": "random-id",
  "workspace_id": "random-id",
  "operation": "next",
  "event_type": "task_transition",
  "recorded_at": "UTC RFC 3339",
  "occurred_at": "UTC RFC 3339 or null",
  "subject": {
    "milestone_id": "M01 or null",
    "task_label": "observed task text or null",
    "status_path": "tabilet/memory-bank/status-M01.md or null",
    "old_state": "in_progress or null",
    "new_state": "completed or null"
  },
  "details": {}
}
~~~

## Snapshot scope

After every audited API run reaches a terminal result, scan:

~~~text
tabilet/docs/history/status-*.md
tabilet/docs/history/index.md
tabilet/docs/history/knowledge.md
tabilet/evolution/prompt-vN.md
tabilet/evolution/result-vN.md
~~~

Store exact bytes, SHA-256, original path, kind, source commit, worktree state,
capture time, and the observing run. Deduplicate identical bytes while keeping
separate run observations. Changed bytes create new observations. Missing,
unreadable, symlinked, or drifted frozen files create diagnostics and never
overwrite prior records. Context archives are deferred to a later milestone.

## Compatibility and failure behavior

Markdown remains authoritative for v2 active work, retired history, and
evolution. The API runner, skills, DSH, and future explorer continue to work
without a database. Installation never migrates or creates one automatically.

SQLite transactions cover database writes only. Record run start before work,
append observed events, record commits only after they succeed, and leave a run
interrupted or unknown when terminal evidence is unavailable. Audit or snapshot
failure is reported as a gap and does not undo work, alter status, repeat a task,
or claim that logging succeeded. Enable foreign keys on every connection and
use a single database so cross-database transaction assumptions are unnecessary.

The first release is external audit plus history/evolution snapshots. A future
version may add read-only queries, host adapters, archive snapshots, and then
consider active milestone indexing after a measured consumer need. Making
SQLite authoritative for any project layer requires a separate versioned format,
migration, export, recovery, and reader-compatibility design.

See the staged implementation work in docs/sqlite-1.md through docs/sqlite-4.md.

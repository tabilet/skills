# SQLite 1 — recorder contract and database foundation

Plan state: [~]

Depends on: none

This milestone defines the first durable SQLite contract. It does not change
the v2 project layout and does not store active milestones or task rows as
database authority.

## Scope

The recorder uses the external per-user database:

~~~text
${XDG_STATE_HOME:-~/.local/state}/tabilet/audit.sqlite3
~~~

When XDG_STATE_HOME is absent, use ~/.local/state. Create the directory with
owner-only permissions. Do not create database, WAL, or shared-memory files in a
project.

The schema version is tabilet.audit/v1. SQLite foreign keys are enabled for
every connection. The database contains these logical records:

- schema_meta: schema name and version;
- workspaces: stable checkout/worktree identity and provenance;
- runs: operation, times, capture settings, parent run, Git state, and result;
- events: append-only event details and verification;
- captured_messages: selected visible text with provenance and fidelity;
- snapshots and run_snapshots: reserved for SQLite 3.

Events store task details as observed. They never reference row numbers or a
rebuildable task table.

## Event envelope

The public event envelope is JSON with schema tabilet.audit.event/v1:

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

Validation rejects malformed timestamps, unknown operations or event types,
conflicting event IDs, missing required identity fields, and unversioned detail
objects.

## Frozen v1 schema

The implementation uses these tables and constraints:

~~~sql
schema_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)
workspaces(workspace_id TEXT PRIMARY KEY, project_root TEXT UNIQUE NOT NULL,
           repository_id TEXT, branch TEXT, created_at TEXT NOT NULL,
           last_seen_at TEXT NOT NULL)
runs(run_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces,
     operation TEXT NOT NULL, started_at TEXT NOT NULL, completed_at TEXT,
     recorder_version TEXT NOT NULL, capture_mode TEXT NOT NULL,
     parent_run_id TEXT REFERENCES runs, git_head TEXT,
     worktree_state TEXT NOT NULL, result TEXT)
events(event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs,
       sequence INTEGER NOT NULL, recorded_at TEXT NOT NULL,
       occurred_at TEXT, operation TEXT NOT NULL, event_type TEXT NOT NULL,
       milestone_id TEXT, task_label TEXT, status_path TEXT,
       old_state TEXT, new_state TEXT, verification_json TEXT,
       file_actions_json TEXT, commit_sha TEXT, details_json TEXT NOT NULL,
       payload_json TEXT NOT NULL, UNIQUE(run_id, sequence))
captured_messages(message_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs,
       sequence INTEGER NOT NULL, role TEXT NOT NULL, captured_at TEXT NOT NULL,
       text TEXT NOT NULL, capture_source TEXT NOT NULL, fidelity TEXT NOT NULL,
       redaction_note TEXT, UNIQUE(run_id, sequence))
~~~

The allowed operations are init, archive, propose, reconcile, next, goal, and
upgrade. The allowed run results are completed, blocked, failed, cancelled,
interrupted, and unknown. Worktree state is clean, dirty, or unversioned.
Event types are run_started, task_observed, task_transition,
verification_observed, commit_observed, run_finished, run_blocked, run_failed,
run_interrupted, audit_gap, and snapshot_gap. Detail JSON is canonicalized with
sorted keys and UTF-8 output. Schema migrations are numbered from user_version
1 and may only add validated changes; a newer database stops an older writer.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL1-T01 | [+] | Freeze v1 schema, constraints, indexes, event vocabulary, and migration rules. | One schema and migration test establish an unambiguous v1 database. |
| SQL1-T02 | [+] | Implement owner-only database creation, connection setup, foreign-key enforcement, and short transactions using Python sqlite3. | Creation, reopen, permission, and schema-version tests pass without project writes. |
| SQL1-T03 | [~] | Implement workspace, run, event, and captured-message persistence. | Records round-trip with UTC timestamps, nullable Git provenance, and result states. |
| SQL1-T04 | [+] | Implement event-envelope validation and idempotent insertion. | Identical delivery is safe; conflicting payloads fail; malformed events are rejected. |
| SQL1-T05 | [ ] | Test interruption, database errors, separate worktrees, no-Git provenance, and owner-only storage. | Failures leave no false completion event and all tests pass without network access. |

## Completion gate

This milestone is complete when the v1 database can be created and reopened,
events are append-only and identity-safe, and all SQL1 tests pass. No runner,
skill, DSH, or project behavior changes until this gate passes.

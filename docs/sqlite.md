# SQLite audit and Markdown lookup

## Authority and scope

Markdown remains authoritative for active milestones, tasks, retired history,
knowledge history, evolution, and optional context archives. SQLite contains
an opt-in durable audit and a disposable current-source index. It never selects
or authorizes a task, changes a marker, or replaces milestone acceptance.

The original SQLite 1–4 implementation was reviewed before merge. Follow-up
milestones [5](sqlite-5.md), [6](sqlite-6.md), [7](sqlite-7.md), and
[8](sqlite-8.md) repair its storage and runner defects and implement this revised
contract, in that order. Earlier task IDs and completion records are historical;
they do not establish acceptance of this design.

New history/evolution/archive snapshot capture is deferred. Existing snapshots
and run observations remain readable, exportable, and recoverable. Git and the
Markdown files retain document history; current indexed text is replaceable.

## Storage and migration

The optional account database defaults to
`${XDG_STATE_HOME:-~/.local/state}/tabilet/audit.sqlite3`. Explicit configuration
uses `TABILET_AUDIT_DB` or `--audit-db`. Installation and read commands never
create a database. Database, WAL, and shared-memory files stay outside projects.
New storage directories are private; existing parent permissions are unchanged.

The database identity is `tabilet.audit/v2`, with SQLite `user_version=2`.
Writers validate identity, version, required columns, integrity, and foreign
keys before changing existing storage. The transactional v1-to-v2 migration
adds derived tables while preserving durable records and snapshot bytes.
Unknown or newer databases are rejected. Backups and recovery use new external
destinations and never overwrite existing files. Take an explicit backup before
upgrading an existing database when independent rollback is required.

## Durable records

`workspaces` identifies canonical checkout/worktree roots; `runs` identifies
operations, parent runs, capture policy, timestamps, Git provenance, and results.
`events` holds immutable observed task details and versioned JSON evidence.
`captured_messages` holds explicitly selected visible text. Legacy `snapshots`
and `run_snapshots` retain their existing data, without new automatic captures.

The event envelope remains `tabilet.audit.event/v1`; details require
`{"schema":"tabilet.audit.details/v1"}`. Operations are init, archive, propose,
reconcile, next, goal, and upgrade. Results are completed, blocked, failed,
cancelled, interrupted, or unknown. Milestone acceptance, retirement, cancellation,
and supersession can be recorded explicitly; terminal row markers alone do not
prove acceptance. Timestamps use UTC RFC 3339.

Caller-supplied run, event, and message IDs support retries. Identical retries
return the original record, including generated timestamps and sequence values;
conflicting reuse fails. Events require their run's workspace and operation;
parent runs must belong to the same workspace. Sequence allocation and terminal
updates are serialized transactions. Audit references never point to disposable
index rows, so edits or retirement cannot reattribute earlier evidence.

Default capture is metadata. `relevant` capture permits selected requests,
approvals, clarifications, and outputs; it excludes hidden reasoning and unrelated
sessions. Exact text requires host capture. Agent-produced summaries are labelled
summarized or incomplete. Capture source and fidelity are claims of the submitting
host, not cryptographic proof. Do not submit credentials or unrelated private text.
Export excludes captured messages and snapshot bytes unless explicitly requested.
Event summaries may themselves contain private material; review exports before sharing.

## Rebuildable index

| Table | Current derived content |
|---|---|
| `index_state` | Published generation, refresh/Git context, last attempt, diagnostics, search capability |
| `index_documents` | Workspace/path/kind, SHA-256, file metadata, current text |
| `index_sections` | Heading, anchor, source line range, section text |
| `index_milestones` | Permanent ID, active/retired location, specification, recorded outcome/review |
| `index_tasks` | Milestone, label/state/notes, document hash and line, existing explicit ID |
| `index_relationships` | Explicit dependencies/successors, archive lineage, evolution pairs |
| `index_search` | Searchable document, section, and task entries |

Index only declared v2 Markdown under `tabilet/`: current memory-bank documents,
active statuses, retired records/indexes, knowledge history, evolution pairs,
and optional archives. Do not traverse arbitrary project docs, caches, or vendor
folders. Read bounded UTF-8 files without symlink traversal and confirm stable
metadata before and after reading. Reconcile the full inventory on each refresh,
including deletion, retirement, and branch changes; reuse parsing only for matching
hashes. Publish each workspace generation atomically. Failed refreshes preserve
the previous generation and expose diagnostics; callers must inspect freshness.

Milestone identity is workspace plus permanent ID; archive IDs occupy a separate
namespace. Tasks without explicit IDs are versioned observations at a source
location. Do not infer permanent identity through renames, duplicates, or moves.
Use established Markdown and retired-record parsing semantics, including escaped
pipes and fences. Index explicit relationships only; retain unresolved references
as diagnostics. Do not infer acceptance from completed or cancelled markers.

FTS5 provides text search when available; otherwise use a labelled literal-text
fallback. Results include workspace, path, line, indexed hash, and refresh time.
Read commands never refresh implicitly. Execution always rereads the live ledger.
Rebuild deletes derived data only, preserving audit and old snapshot evidence.

## Interfaces and failures

The optional `tabilet-audit` CLI supports `audit begin|event|message|finish`,
`audit runs|events|export`, `index sync|status|search|show`, and `backup|restore`.
Commands return JSON; errors go to stderr with nonzero status. The former
`--event` host submission remains an alias. Lifecycle calls work from a fresh
database and support all seven operations and parent/child goal runs.

Enabled API and skill workflows record observed evidence and request index refresh
on completion. Skill instructions use an independently installed optional toolkit;
missing tools or failed logging produce visible gaps without changing approvals,
workflow outcomes, commits, or task state. Exact raw conversation capture requires
a host supplying the text; installing a skill does not add host transcript hooks.
Audit failures never repeat work. Interrupted runs without terminal evidence remain
unfinished/unknown rather than being declared successful.

The runner remains installable as one file when auditing is disabled. The toolkit
is Python standard library only. Legacy snapshot-capture options are rejected
with an explanation before project execution. Companion UI and explorer integration
can consume these interfaces later; no project-format migration is needed.

## Acceptance

Verify clean copied installations, fresh host lifecycles, storage failures,
concurrent writers, retries, ownership, filters/pagination, complete exports,
legacy snapshot preservation, and separate-destination recovery. Index tests must
exercise real Markdown edits, deletion, reorder/rename/duplicates, retirement,
branch switching, interrupted reads, malformed records, all-retired and archive-only
projects, and fallback search. Record scale evidence around 120 status files.

Required final gates: `python3 check.py`, credential-free DSH tests,
`mkdocs build --strict`, and `git diff --check`. Implementation remains on `sqlite`;
merging, pushing, publication, and marketplace changes are separate actions.

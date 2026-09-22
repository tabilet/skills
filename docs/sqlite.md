# SQLite audit and Markdown lookup

## Authority and scope

Markdown remains authoritative for active milestones, tasks, retired history,
knowledge history, evolution, and optional context archives. SQLite contains
an opt-in durable audit and a disposable current-source index. It never selects
or authorizes a task, changes a marker, or replaces milestone acceptance.

The original SQLite 1–4 implementation was reviewed before merge. SQLite 3 and
4 are now marked superseded because their automatic snapshot rows were cancelled.
Follow-up
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

The database identity is `tabilet.audit/v3`, with SQLite `user_version=3`.
Writers validate identity, version, required columns, integrity, and foreign
keys before changing existing storage. The transactional v1/v2-to-v3 migration
adds explorer evidence references and derived tables while preserving durable
records and snapshot bytes. Readers can open v1 and v2 databases without
writing; an explicit writer open performs the transactional migration. A failed
migration rolls back the schema marker and leaves the earlier database readable.
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

The lookup index contains current Markdown text even when audit message capture
is metadata-only. Default audit capture is metadata. `relevant` capture permits selected requests,
approvals, clarifications, and outputs; it excludes hidden reasoning and unrelated
sessions. Exact text requires host capture. Agent-produced summaries are labelled
summarized or incomplete. Capture source and fidelity are claims of the submitting
host, not cryptographic proof. Do not submit credentials or unrelated private text.
Export excludes captured messages and snapshot bytes unless explicitly requested.
Event summaries may themselves contain private material; review exports before sharing.

Events may carry an optional `details.explorer` object with schema
`tabilet.audit.explorer/v1`. Its `phase` is one of `request`, `proposal`,
`approval`, or `applied`; `message_refs` names selected messages from the same
run with purpose `request`, `clarification`, `approval`, or `output`; and
`artifact_refs` names observed or proposed milestones, tasks, archives,
evolution records, or documents. Artifact paths are project-relative and each
reference may include a source line, hash, label, and before/after state. The
relationships `created`, `changed`, and `retired` are valid only in the
`applied` phase; earlier phases use `proposed`, which never proves a mutation. The
recorder validates workspace/run ownership before storing normalized references
in `event_explorer`, `event_message_refs`, and `event_artifacts`. Missing
captures remain missing; the extension never fabricates a request or treats a
proposal as proof of a file write.

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
| `index_milestone_projection` | Display order, summary, acceptance, review/closure evidence, and source hash |
| `index_task_dependencies` | Explicit task dependencies with source location and unresolved targets |

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

The read-only `tabilet_index.readiness(connection, workspace_id, project_root)`
projection validates the live declared inventory and hashes before ordering work.
It returns `resume`, `ready`, `waiting`, `blocked`, and `needs_review` groups,
with source references and reasons. Multiple in-progress rows, stale or
unavailable sources, unresolved dependencies, or index diagnostics withhold
`recommendations`; the function never edits Markdown or grants execution
authority. A pending task is ready only when its explicit dependencies are
completed and no sole in-progress row owns the ledger. Terminal rows do not
establish milestone acceptance.

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
with an explanation before project execution. The optional explorer consumes
these interfaces; no project-format migration is needed.

## Install and use the optional toolkit

Run from a checkout containing the SQLite feature:

```bash
mkdir -p ~/.local/bin
install -m 755 harness/tackle-memory-bank-api-loop ~/.local/bin/
install -m 644 harness/tabilet_audit.py harness/tabilet_index.py ~/.local/bin/
install -m 755 harness/tabilet_explorer.py ~/.local/bin/
install -d ~/.local/share/tabilet/explorer
install -m 644 harness/explorer/index.html harness/explorer/explorer.css harness/explorer/explorer.js ~/.local/share/tabilet/explorer/
install -m 755 harness/tabilet_audit_host.py ~/.local/bin/tabilet-audit
export PATH="$HOME/.local/bin:$PATH"
export TABILET_AUDIT_DB="${XDG_STATE_HOME:-$HOME/.local/state}/tabilet/audit.sqlite3"
```

The database path must be outside every registered project. The same toolkit
can index several checkouts; worktrees have separate identities. Copying project
Markdown needs no database migration. A moved checkout registers a new workspace;
its old audit records remain available under the original identity.

```bash
tabilet-audit index sync /absolute/project
tabilet-audit index search /absolute/project 'authentication' --kind task
tabilet-audit index search /absolute/project --milestone M01 --state pending
tabilet-audit index show /absolute/project tabilet/docs/history/status-M01.md
tabilet-audit index status /absolute/project
tabilet-audit index sync /absolute/project --rebuild
tabilet-audit explorer /absolute/project --port 8000
```

The explorer opens Overview, Timeline, and To-do on a loopback-only server.
Overview groups active milestones and tasks, retired outcomes, archive lanes,
and evolution pairs. Timeline groups goal children and drills from the captured
request and result into recorded changes and resolved current state. Its date,
operation, milestone, outcome, ordering, pagination, search, and selected-detail
state is bookmarkable. To-do explains resume, ready, waiting, blocked, and
review-required work with prerequisite and dependent links. Refresh is explicit,
migrates supported older databases, and writes only the external database.
Recorded evidence remains visible when freshness or closure rules withhold task
recommendations. Follow-up buttons revalidate the live source and prepare text
for copying; they do not launch an agent, edit Markdown, or create task rows.
Use `ssh -N -L 8000:127.0.0.1:8000 user@host` for a remote server and browse to
`http://localhost:8000/`. Missing captures, stale hashes, malformed sources,
and unavailable indexes remain visible as diagnostics and withhold unsafe
recommendations.

The server rejects non-loopback `--host` values. An existing v1 or v2 database
can show recorded audit runs before migration; Overview explains that its project
projection needs refresh. API collections use bounded pagination, and timestamps
are compared at normalized UTC microsecond precision even when older records omit
fractional seconds. To-do groups have independent offsets and totals. Timeline
goal children are bounded, with the complete child list paged through run detail.
Each migrated workspace publishes its own projection-version marker before
unchanged source rows may be reused.

`complete` describes the last refresh, not continuous observation of disk.
Read commands report the indexed generation, source hashes, and refresh time;
they do not watch files or validate that the source is still current. Run sync
after manual edits or branch changes. Read live Markdown before acting on results.
Malformed statuses or interrupted reads retain the last published generation with
`complete=false` and diagnostics. Repair the source and sync again. A rebuild
reparses all current sources; it never clears audit or legacy snapshots.

Search filters include `--kind`, `--milestone`, and `--state`, with `--limit`
(1–10000) and `--offset`. Kind `task` returns task rows; `section` returns headings;
document kinds include `active_status`, `history_status`, `history_index`,
`knowledge_history`, `evolution_prompt`, `evolution_result`, and `context_archive`.
FTS5 queries support its expression syntax. `index sync --literal` selects a
literal substring search; this is also the fallback when FTS5 is unavailable.
An empty query lists entries matching the filters. `show` returns the indexed
text, tasks, sections, milestone metadata, and explicit relationships.

## Record a host workflow

With `TABILET_AUDIT_DB` set, the API runner automatically records its own runs.
The seven interactive skills use the optional CLI when available, following their
bundled audit reference. This is an instruction-driven integration, not an
installed host transcript hook. Native goal protocols can use the same CLI.
Do not record an API-runner operation a second time through a skill hook.

```bash
tabilet-audit audit begin /absolute/project propose --run-id proposal-001
tabilet-audit audit event --input /absolute/observed-event.json
tabilet-audit audit finish proposal-001 completed
```

Begin returns `run_id` and `workspace_id`. Event input uses the v1 envelope and
requires `details.capture_source` (`host`, `agent`, or `import`) and
`details.fidelity` (`exact`, `redacted`, `summarized`, or `incomplete`). Agent
submissions cannot claim exact host capture. Include a stable `event_id`; if
`recorded_at` is omitted, retries with that ID reuse its original value.
Omit unknown `occurred_at`. Event details may include `verification`,
`file_actions`, `commit_sha`, approval summaries, and other observed evidence.
The subject may include milestone ID, observed task label, original status path,
and old/new states. Use a JSON file or stdin; never interpolate chat into shell code.

Relevant message capture requires `audit begin --capture relevant` (or
`TABILET_AUDIT_CAPTURE=relevant`). Submit selected text through `audit message`
using `--input FILE` or stdin. The JSON fields are `run_id`, `message_id`, `role`,
`text`, `capture_source`, and `fidelity`, with optional `redaction_note`,
`captured_at`, and `sequence`. Metadata runs reject message capture. Only
host-provided text may claim `exact`; an agent's summary must say `summarized`
or `incomplete`. No host integration automatically captures your whole chat.

Retain IDs across retries. A conflicting payload fails; identical retries return
the original record. A goal can use `--parent-run-id` for its child runs.
Finish results are `completed`, `blocked`, `failed`, `cancelled`, `interrupted`,
and `unknown`. Abrupt termination may leave a run with no terminal result.
Finish updates its result and terminal event in one transaction, then refreshes
the index. A refresh gap does not change the recorded workflow outcome.

```bash
tabilet-audit audit runs --project /absolute/project --operation next --limit 50
tabilet-audit audit events --run-id RUN_ID --offset 0 --limit 100
tabilet-audit audit runs --project /absolute/project --milestone M01 --task 'Observed task label'
tabilet-audit audit export --project /absolute/project > /tmp/tabilet-audit-export.json
```

Runs and events accept workspace/project, operation, milestone, exact observed
task label, and inclusive `--since`/`--until` UTC RFC 3339 filters. Exports are
complete rather than limited to one page. `--include-content` additionally includes
captured messages and base64 legacy snapshot bytes. Exported event summaries may
contain private material even without that flag. CLI errors exit 2 and write a
message to stderr; audit/index failures never change the API runner's established
exit codes, task markers, or commit policy.

## Backup and recovery

```bash
tabilet-audit backup /absolute/external-backup.sqlite3
tabilet-audit --audit-db /absolute/external-backup.sqlite3 restore /absolute/recovered.sqlite3
tabilet-audit restore /absolute/recovered-record.md --snapshot-id SNAPSHOT_ID
```

All destinations must be new external files, with no symlink components. Database
backups include messages and old snapshot bytes; keep them private. Restoration
never edits original project Markdown. Inspect recovered legacy records separately.
Read commands accept known v1 and v2 audit databases without migrating them;
index queries require the explicit writer migration and sync. Writer opens
migrate known v1/v2 storage transactionally. Older writers reject v3 databases,
so retain a backup if rolling back the toolkit. The obsolete `--audit-archives` option and
`TABILET_AUDIT_ARCHIVES=1` stop before execution with a replacement instruction.

## Acceptance

Verify clean copied installations, fresh host lifecycles, storage failures,
concurrent writers, retries, ownership, filters/pagination, complete exports,
legacy snapshot preservation, and separate-destination recovery. Index tests must
exercise real Markdown edits, deletion, reorder/rename/duplicates, retirement,
branch switching, interrupted reads, malformed records, all-retired and archive-only
projects, and fallback search. Record scale evidence around 120 status files.

Required final gates: `python3 check.py`, credential-free DSH tests, the
repository-only Playwright Chromium suite in `tests/browser`,
`mkdocs build --strict`, and `git diff --check`. Implementation remains on `sqlite`;
merging, pushing, publication, and marketplace changes are separate actions.

### Measured acceptance fixture

`python3 -B tests/benchmark_sqlite.py` creates an external disposable fixture with
120 status files across 17 lanes and 2,400 task rows, plus retired history, an
archive, an evolution pair, 250 parent audit runs, and 25 child runs. On the
development host (Python 3.14.4, SQLite 3.46.1), the latest run measured a
451.26 ms initial sync, 316.53 ms unchanged-source sync, 6.64 ms median across
100 FTS5 searches, 123.63 ms readiness classification, 312.34 ms Overview,
25.90 ms for a 50-entry timeline page, 14.04 ms run detail, and 131.08 ms for
a 50-of-2,400-entry To-do page. Peak JSON response size was 179,318 bytes. These
are local observations, not performance guarantees.

The explorer's browser assets are served from the copied toolkit without a build
step; missing assets produce a clear local error. Isolated DOM tests and real
Chromium journeys cover desktop and narrow navigation, filtering, details,
follow-up prompts, clipboard fallback, focus restoration, and polling. Copied
canonical templates pass indexing. Additional read-only inspection of
neighboring projects found pre-existing unpadded milestone headings and invalid
retirement envelopes; structured refresh correctly reports these as validation
failures. It does not normalize IDs or rewrite frozen source records. Those
projects need their format discrepancies reviewed before structured indexing.

# SQLite 4 — host adapters and future consumers

Plan state: [+]

Depends on SQLite 1, SQLite 2, and SQLite 3

This milestone extends the first release to hosts that can observe interactive
skill sessions and to read-only consumers. It remains separate from moving
active milestones into SQLite.

## Host event contract

The shared tabilet.audit.event/v1 envelope is the only accepted host boundary.
A host adapter submits workspace identity, operation and run identity, event
sequence and timestamps, observed milestone/task details, verification, file
actions, and capture provenance.

DSH and other hosts may submit structured summaries. Exact transcript claims
require host capture. Agent summaries are labelled summarized or incomplete.
Host auditing never grants approval for writes, remote review fetches, commits,
or external mutations. Missing or unavailable audit storage produces an audit
gap and preserves the one-execution-owner rule.

## Read-only consumers

Provide read-only query/export support for runs by workspace, operation,
milestone, task, and date; ordered event timelines; snapshot metadata; exact
byte restore to a separate destination; and JSON export for future dashboards
and explorers. Queries and exports cannot rewrite the database, project
Markdown, status markers, or history.

Context archive snapshots use a separate kind after independent preservation
tests and are opt-in with `--audit-archives` or `TABILET_AUDIT_ARCHIVES=1`.
Active milestone/task indexing is not added here. First measure a named
repeated-query consumer and document stale-data behavior, identity rules, and
latency before proposing any active projection.

## Evidence and active projection decision

The named current consumer is the local read-only audit/export interface used
by operators and future explorer tools. A representative fixture contains five
history status files and 100 recorded runs. On the development host,
`query_runs` completed in 0.570 ms and a run timeline query in 0.138 ms; these
figures are local observations, not service-level guarantees. The fixture keeps
one immutable event identity and stores task text directly in each event, so
row insertion, reordering, renaming, and retirement cannot reattribute it.

The database can be stale when a run has not reached its terminal snapshot, or
when an audit write fails. Markdown remains authoritative, and explicit
`audit_gap` or `snapshot_gap` records expose that condition. The observed scale
and query need do not justify an active milestone projection. Any future
projection requires a new approved format and migration, export, recovery,
staleness, and reader-compatibility design; it may not silently change task
selection or status authority.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL4-T01 | [+] | Define host submission validation and provenance rules for the event envelope. | Valid structured events work; exact, summarized, redacted, and incomplete capture differ. |
| SQL4-T02 | [+] | Add a DSH or equivalent host adapter for init, archive, propose, reconcile, and goal. | Credential-free host tests show correct events and safe missing-database behavior. |
| SQL4-T03 | [+] | Implement read-only run/event/snapshot queries, JSON export, and separate-destination restore. | Queries and exports cannot mutate project or database records. |
| SQL4-T04 | [+] | Add context-archive snapshots with independent ID, baseline, and privacy tests. | Verified archives remain immutable and archive IDs stay separate from status IDs. |
| SQL4-T05 | [+] | Measure interactive query needs and document whether active projection is justified. | The decision includes observed scale, latency, stale-data behavior, and approval boundary. |
| SQL4-T06 | [+] | Update compatibility, operator, privacy, backup, and release documentation. | Existing v2 projects remain usable with no database and new host behavior is documented. |

## Review follow-up

Event timelines normalize legacy and fractional UTC timestamp precision before
ordering. The public index-sync command lets an already registered workspace
record a mixed-layout failure, while a new legacy project still stops before
database creation; the resulting incomplete state retains its diagnostics.

## Completion gate

This milestone is complete when host adapters and read-only consumers use the
same versioned event contract, and the active-milestone decision is evidence
based. It does not authorize moving active status or milestone authority into
SQLite.

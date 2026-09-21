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

Context archive snapshots may be added here after independent preservation
tests. Active milestone/task indexing is not added here. First measure a named
repeated-query consumer and document stale-data behavior, identity rules, and
latency before proposing any active projection.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL4-T01 | [+] | Define host submission validation and provenance rules for the event envelope. | Valid structured events work; exact, summarized, redacted, and incomplete capture differ. |
| SQL4-T02 | [+] | Add a DSH or equivalent host adapter for init, archive, propose, reconcile, and goal. | Credential-free host tests show correct events and safe missing-database behavior. |
| SQL4-T03 | [+] | Implement read-only run/event/snapshot queries, JSON export, and separate-destination restore. | Queries and exports cannot mutate project or database records. |
| SQL4-T04 | [+] | Add context-archive snapshots with independent ID, baseline, and privacy tests. | Verified archives remain immutable and archive IDs stay separate from status IDs. |
| SQL4-T05 | [+] | Measure interactive query needs and document whether active projection is justified. | The decision includes observed scale, latency, stale-data behavior, and approval boundary. |
| SQL4-T06 | [+] | Update compatibility, operator, privacy, backup, and release documentation. | Existing v2 projects remain usable with no database and new host behavior is documented. |

## Completion gate

This milestone is complete when host adapters and read-only consumers use the
same versioned event contract, and the active-milestone decision is evidence
based. It does not authorize moving active status or milestone authority into
SQLite.

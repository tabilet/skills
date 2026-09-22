# SQLite 9 — Explorer data contracts, migrations, and readiness

Plan state: [+]

Depends on: [SQLite 8 — SQLite foundation acceptance](sqlite-8.md).

Next: [SQLite 10 — Local server, API, and navigation](sqlite-10.md).

This implementation ledger preserves the accepted contract and completion
evidence. Its completion does not authorize a release.

## Explorer objective and delivery order

Build a standalone browser explorer that helps users understand project memory,
inspect what followed a request, and choose an appropriate task follow-up.
The existing [SQLite audit and lookup contract](sqlite.md) remains the foundation.

```text
SQLite 8: accepted audit and index foundation
    |
SQLite 9: explorer data, migration, and readiness contracts
    |
SQLite 10: local server, API, and shared navigation
    |
SQLite 11: overview, timeline, to-do, and follow-up prompts
    |
SQLite 12: acceptance, packaging, and documentation
```

The three views are Overview (the landing page), Timeline, and To-do. They share
source navigation and detail panels. Summaries use recorded text and derived
facts. Follow-up actions inspect evidence and copy prompts into the user's
preferred agent. The first release does not launch agents, edit project planning
records, or generate AI summaries.

Serve one explicitly selected project per server instance. The same account
database may contain other workspaces, but those are outside that instance's
scope. Preserve the project's Markdown, permanent IDs, local policies, and frozen
history. Index refresh remains a derived-data operation, never task execution.

The requested implementation model for a later authorized run is
`gpt-5.6-luna` with high effort. Saving these ledgers does not launch that run.

## Existing foundation and gaps

The current database records workspaces, runs, events, selected messages, and
legacy snapshots. It also indexes current documents, sections, milestones,
task observations, and some explicit relationships.

The explorer needs additional structure to connect a request to its outputs and
explain task readiness. Free-form event details, terminal task markers, and a
filename sort do not supply those answers reliably. Older records may lack
captured chat or artifact references; preserve that uncertainty.

## Durable audit extensions

Keep the existing event envelope and add a versioned optional explorer-details
object. Its contract covers:

| Field group | Required meaning |
|---|---|
| Phase | Distinguish a request, proposal, approval, and applied change. |
| Message references | Reference selected request, clarification, approval, and output messages from the same run. |
| Artifact references | Identify observed milestones, task observations, archives, evolution records, or documents, with their relationship to the event. |
| Observed evidence | Preserve relevant labels, source paths, available hashes/locations, selected output details, and before/after states. |
| Run relationships | Reference parent/child runs and the evidence supporting aggregate summaries. |

Validate supplied references against the run's operation and workspace. References
to proposed allocations remain proposals; they must not be treated as proof that
files or permanent task identities were created. Artifact links can be absent
when no source file exists yet.
The `created`, `changed`, and `retired` relationships are restricted to the
`applied` phase. Proposal and approval events use `proposed`, so the explorer
cannot present intended work as an observed mutation.

Store enough selected structured output to explain what was recorded at that time.
Do not substitute today's task text for an older output, or restore automatic
full-file snapshot capture. Historical evidence never points through a foreign
key to a disposable index row.

Update API-runner, generic-host, and optional skill recording instructions to
emit the extension when the evidence is observable. Preserve metadata-only versus
relevant capture, caller-supplied retry IDs, and source/fidelity labels. Do not
backfill missing conversations from Git timestamps, Markdown dates, or guesses.
Goal summaries must reference their child evidence rather than duplicating child
transitions and inflating completed-task counts.

## Derived explorer projection

Extend the rebuildable projection to expose:

- Milestone display order, maintained summary, acceptance text, and recorded
  review/closure evidence, each with its source location.
- Task observations, explicit task dependencies, dependents, blocker text,
  and the evidence used to interpret them.
- Typed references that keep milestone IDs and archive IDs in separate namespaces.
- Source hashes, index generation, freshness information, and unresolved or
  contradictory relationships.

Use existing explicit task IDs when present. Otherwise a task observation is
identified by workspace, source path, document hash, and row location. Resolve
textual task references only when unambiguous; do not infer continuity through
renames, duplicate labels, or retirement. Read recognized dependency declarations
and structured references, not arbitrary prose as if it were a dependency rule.

## Readiness and ordering contract

The To-do view explains a suggested order. It never selects an execution owner
or grants authority to perform the work.

1. Validate the current active ledger and relevant prerequisite/closure evidence.
   Multiple in-progress rows, stale source data, cycles, or ambiguous references
   must remain visible rather than being resolved by a silent guess.
2. Put the sole valid in-progress task in **Resume**. Other tasks cannot be
   presented as the next execution selection while that task owns the ledger.
3. Identify milestones requiring review or closure. Terminal rows alone do not
   establish accepted completion. Unfinished closure appears in **Needs review**
   and prevents recommendations that would bypass the governing closure gate.
4. Put dependency-ready pending tasks in **Ready**, ordered by documented
   milestone priority/order and then row order. Explicit dependencies take
   precedence over display order; filenames do not create product priority.
5. Put pending tasks with unsatisfied prerequisites in **Waiting**, explicit
   blocked rows in **Blocked**, and unresolved workflow decisions in **Needs review**.

Each classification returns reasons and source references. A cancelled or
superseded prerequisite is not automatically accepted success; follow its recorded
disposition and accepted successor. Review/closure follow-ups are workflow actions,
not invented task rows with new IDs. Project-specific prose policy that cannot be
interpreted reliably produces a review requirement rather than a definitive order.

## Migration and degraded operation

Add a numbered writer migration for the explorer projection and any necessary
metadata, supporting both existing v1 and v2 audit databases. The next database
revision is v3; the existing event-envelope version remains compatible through
the optional details extension. Migration is transactional and must preserve all
durable records, captured messages, legacy snapshot bytes, and run observations.

Opening the explorer or making a read request never migrates storage. Explicit
refresh performs a supported writer migration and rebuild as needed. Older
databases may expose their available audit evidence before refresh; unsupported
newer or foreign databases receive an explanation, not a write attempt.

A failed refresh retains the previously published index. Explorer consumers may
show available evidence and safely read declared source documents with diagnostics.
They must withhold task recommendations when the current state cannot be validated.
This does not relax the API runner's project-format or execution gates.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL9-T01 | [+] | Recognize the four explorer milestone ledgers in repository checks and document the extension contract. | Checks accept and verify SQLite 9–12 as English task ledgers; the optional audit extension and derived-field meanings are documented consistently. |
| SQL9-T02 | [+] | Implement transactional database migration and compatible reads. | v1/v2 evidence survives migration and interruption/retry; read-only access never migrates; newer/foreign databases are rejected. |
| SQL9-T03 | [+] | Record structured request/output, artifact, phase, and run references. | Host, runner, and skill integrations preserve retry identity, capture policy, historical observations, and parent/child provenance. |
| SQL9-T04 | [+] | Extend projections for summaries, display order, review evidence, and task relationships. | References are source-linked and typed; duplicate labels, renamed rows, and archive/status ID overlap do not create false identities. |
| SQL9-T05 | [+] | Implement explained readiness classification and suggested ordering. | Resume, Ready, Waiting, Blocked, and Needs review follow the stated contract; unresolved or stale evidence prevents unsafe recommendations. |
| SQL9-T06 | [+] | Verify migration, evidence preservation, readiness, and downstream interface compatibility. | Focused tests pass and the complete milestone review has no blocking findings before SQLite 10 starts. |

## Verification and completion gate

Test legacy records with no new fields, exact/summarized/missing messages,
proposed versus applied outputs, goal aggregation, cross-workspace references,
task rename/reorder/duplicates, retirement, dependency cycles, cancelled and
superseded prerequisites, multiple in-progress rows, and incomplete closure.
Verify database rollback and unchanged audit exports/snapshot hashes after rebuild.

Run focused Python tests and `python3 check.py`. SQLite 10 starts only after this
milestone's contracts, verification, and review pass. Do not change earlier task
IDs or completion evidence to represent these new tasks.

Implementation notes: database revision 3 preserves v1/v2 audit records and
legacy snapshot bytes. The optional `tabilet.audit.explorer/v1` event extension
normalizes message and artifact references with run ownership checks. The
rebuildable projection adds milestone presentation metadata and explicit task
dependency observations. `tabilet_index.readiness` validates live source hashes
and withholds recommendations on stale, unresolved, or contradictory state.

Verification: the 80-test focused SQLite suite passes, including
v1/v2 migration, extension ownership, projection, dependency, stale-source, and
multiple-in-progress cases. No Markdown or snapshot bytes are rewritten. The
complete repository and website gates remain the parent milestone's final
acceptance check before SQLite 10 starts.

Review iteration: 3 (cross-milestone deep review fixes applied). Projection publication now
rebuilds SQL9 tables when a v2 index is first upgraded; readiness resolves
duplicate IDs in milestone scope, reports dependency cycles, preserves
maintained milestone order, and withholds downstream work for cancelled,
historical, missing, or unreviewed prerequisites. The parent goal
must run the complete repository, DSH, browser, and strict website gates before
treating this milestone as accepted downstream. Strict JSON now rejects
non-finite values, readiness exposes linked prerequisites and dependents under a
single read snapshot, and live prompt preparation rejects a hash change after
classification.

Review iteration: 4. Cross-milestone dependency source keys now retain milestone
scope, so repeated task IDs do not collide. Migrated projection readiness is
recorded per workspace, active prerequisite milestones remain waiting until
accepted retirement, and dependency-cycle traversal is iterative at the documented
project scale. Focused regression fixtures cover all four cases.

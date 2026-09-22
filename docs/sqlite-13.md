# SQLite 13 — Audit provenance, skill-chat coverage, and privacy controls

Plan state: [+]

Depends on: [SQLite 12 — Explorer testing, packaging, and documentation](sqlite-12.md).

Full dependency order: [SQLite 9](sqlite-9.md) -> [SQLite 10](sqlite-10.md) ->
[SQLite 11](sqlite-11.md) -> [SQLite 12](sqlite-12.md) -> SQLite 13.

This implementation ledger extends the optional audit without changing
Tabilet's authority model. Markdown remains authoritative project memory. SQLite
remains external, optional evidence and lookup storage. Saving this plan does not
migrate a database, enable capture, purge content, launch an agent, or authorize a
release.

## Scope and boundaries

`TABILET_AUDIT_DB` continues to opt a host into auditing. The default
`TABILET_AUDIT_CAPTURE=metadata` records structured workflow evidence without raw
message text. `relevant` permits selected visible messages belonging to the
recorded skill or API-runner operation; it does not permit whole-session capture.
Each retained message is capped at 1,024 characters. Interactive agents write a
concise `summarized` record for longer text; intentionally bounded excerpts are
`incomplete`, never silently treated as exact.

SQLite 13 records what a host actually supplied and makes missing evidence
visible. It never reconstructs a request from current Markdown, searches a
project for installed instruction files, or treats audit evidence as task
authorization. Hidden reasoning, complete tool traces, unrelated surrounding
chat, provider-specific automatic host adapters, deterministic replay, vector
memory, and new full-file snapshot capture remain out of scope. Existing legacy
snapshots are preserved.

Coverage has three integration tiers:

| Tier | Capture method | Contract |
|---|---|---|
| Instrumented hosts, including the API runner | `automatic` | The host records the provenance and selected visible messages it owns. It does not claim an outer chat or messages it did not observe. |
| Interactive skills | `instruction_driven` | The shared optional-audit instructions ask the agent to record observable evidence. A missing CLI or unavailable host text becomes an explicit gap, not a reconstructed transcript. |
| Host-supplied records submitted afterward | `imported` | The importer preserves the supplied method, fidelity, and timestamps and never upgrades their certainty. |

The API runner owns its own lifecycle. Interactive instructions must not create a
duplicate run for runner-owned work, and a recorded Goal uses one parent recorder
with linked child runs rather than duplicate parent/child observations.

## Database v4 and migration

The new database identity is `tabilet.audit/v4`, with SQLite `user_version=4`.
A writer migrates known v1, v2, and v3 databases through numbered steps in one
transaction. Read-only commands and Explorer reads never migrate. Validate the
complete target schema, constraints, indexes, identity, integrity, and foreign
keys before writing the v4 identity and version markers. An interruption or any
validation failure rolls back both data and schema changes, leaving the earlier
database usable. Reject foreign identities and unsupported newer versions.

The v3 `captured_messages` rows become two durable records:

- An immutable message envelope retains the message ID, run, sequence, role,
  captured timestamp, capture source, fidelity, redaction note, SHA-256, and
  UTF-8 byte length.
- A separately stored content row retains the exact existing text bytes. The
  migration must not normalize newlines, Unicode, or other text representation.
  Content is present unless a later explicit purge creates a tombstone.

Existing event references continue to target the envelope, so purging content
cannot break historical ordering or referential identity. Existing events,
explorer references, snapshots, run-snapshot observations, IDs, timestamps, and
payload bytes retain their meaning.

Add database guards that reject direct updates and deletes of events, message
envelopes, run provenance, coverage observations, purge tombstones, normalized
Explorer references, snapshots, and run-snapshot observations. Existing run
finalization remains the only permitted durable update: an unfinished run may
acquire its one terminal result and completion time through the recorder's
validated transaction. Message content may be deleted only by the purge
transaction after its tombstone exists. Rebuildable `index_*` projections remain
mutable and replaceable.

## Immutable run provenance

Each v4 run may have one immutable provenance record supplied at `audit begin`.
The structured input defines:

| Field | Contract |
|---|---|
| Invocation kind | `api_runner`, `interactive_skill`, or `host_operation`; this describes how the instruction set was invoked, independently of the existing operation name. |
| Instruction set | A stable logical name and optional declared version. Names such as `memory-bank-next` or `tackle-memory-bank-api-loop` identify instructions without installation paths. |
| Host | Agent name and optional version as declared by the host. |
| Provider and model | Optional verbatim provider and model strings. Do not normalize a provider alias or infer a family from the model name. |
| Host session | An optional opaque reference. It is not a filesystem path, credential, or source of authorization, and Explorer does not reveal it by default. |
| Capture method | `automatic`, `instruction_driven`, or `imported`. |
| Fingerprint fidelity | `exact`, `partial`, or `unavailable`. |
| Loaded resources | Zero or more logical resource names paired with lowercase SHA-256 hashes; absolute installation paths are rejected and never stored. |
| Aggregate fingerprint | A lowercase SHA-256 over canonical UTF-8 JSON containing the sorted logical-name/hash pairs. Duplicate logical names are invalid. |

Call this value an **instruction-set fingerprint**, not a skill checksum or
project fingerprint. Its canonical payload is a JSON array of objects shaped
`{"name":"LOGICAL_NAME","sha256":"LOWERCASE_HEX"}`, sorted ascending by the
UTF-8 bytes of `name`, serialized as UTF-8 with lexically sorted object keys and
no insignificant whitespace. Input order does not affect the digest. `exact`
means the submitting host knows and lists every instruction resource it loaded
for the invocation; `partial` means the listed resources are genuine but
incomplete. Both require at least one resource and a matching computed aggregate.
`unavailable` requires no resource rows and no aggregate. A declared package or
skill version does not make an unavailable fingerprint exact.

Only a host that knows its loaded resources may claim `exact`. Agents and skills
must not crawl the project, account directories, plugin caches, or other install
locations looking for `SKILL.md`, and must never store absolute instruction
paths. A retry of `audit begin` with the same run ID accepts byte-equivalent
normalized provenance and rejects conflicting provenance.

## Capture-coverage observations

Coverage is an append-only observation, not a mutable summary. `audit coverage`
accepts a globally unique stable `coverage_id`; an identical retry returns the
original record, while reuse with any different normalized field is a conflict.
Each observation contains its run ID, UTC observation timestamp, capture method,
optional non-sensitive reason, and these enums and counts. The method must match
the run provenance when provenance is available. The current observation is the
latest for that run by `(observed_at, coverage_id)`; timestamps and IDs are never
rewritten to change that order.

| Field | Values and meaning |
|---|---|
| Scope | `skill_conversation` for one interactive skill invocation, or `api_runner_conversation` for the runner-owned exchange. |
| Coverage | `not_requested`, `complete`, `partial`, or `missing`. `not_requested` means metadata capture was selected; `missing` means relevant capture was requested but no permitted message evidence was supplied. |
| Content state | `none`, `available`, `partially_purged`, or `purged`. This describes the referenced envelopes at the observation time, without replacing their tombstones. |
| Fidelity counts | Non-negative counts named `exact`, `redacted`, `summarized`, and `incomplete`, matching the message-envelope fidelity vocabulary. |

`not_requested` and `missing` require `content_state=none` and zero captured-message
counts. `complete` requires available content, at least one captured message, and
zero incomplete messages. `partial` records any permitted incomplete selection,
mixed availability, or later purge state; it never implies what the missing text
said. Coverage counts must agree with the referenced run envelopes and current
content/tombstone state when submitted. Purge does not rewrite an earlier
observation; the recorder appends a new observation when it needs to report the
new `partially_purged` or `purged` state.

Reasons are short operator diagnostics, not storage for message text, credentials,
hidden reasoning, or opaque session values. Unfinished runs may have coverage
observations, but elapsed time and coverage never imply a terminal run result.

## Explicit message purge

Content removal is a destructive local CLI operation and is deliberately absent
from Explorer:

```bash
tabilet-audit audit purge-message MESSAGE_ID \
  --reason 'operator-requested privacy removal' \
  --confirm MESSAGE_ID
```

Require an existing message ID, a non-empty non-sensitive reason, and exact
confirmation of that same ID. In one validated transaction, retain the immutable
envelope, content SHA-256 and byte length, message/event references, and insert an
immutable tombstone plus a `message_content_purged` event before deleting the
content row. Append a coverage observation for the affected run, with a stable ID
derived from the tombstone, recomputed fidelity counts, and `partially_purged` or
`purged` content state. The event and observation record identifiers and the
supplied reason, never the removed text. A retry with the same message ID and
reason returns the existing tombstone; a different reason or conflicting identity
fails.

Enable SQLite secure deletion for the purge connection. Checkpoint and truncate
WAL data where possible, report whether that cleanup succeeded, and fail safely
without claiming physical erasure. Purge is logical removal from this database,
not cryptographic erasure: it cannot remove content already copied into backups,
exports, filesystem snapshots, replicas, or other external systems. Vacuuming or
rewriting an external backup is not part of this command.

Queries and exports represent a purged envelope as `purged` and never return its
former text, including with `--include-content`. References to the message remain
inspectable. An envelope that was never captured renders as `not captured`, not
as purged.

## CLI, filters, and export

Extend the existing CLI without changing audit enablement or project authority:

```bash
tabilet-audit audit begin /absolute/project next \
  --provenance /absolute/provenance.json
tabilet-audit audit coverage --input /absolute/coverage.json
tabilet-audit audit purge-message MESSAGE_ID --reason TEXT --confirm MESSAGE_ID
```

`--provenance FILE|-` is optional structured input on `audit begin`; omitted
input creates a legacy-compatible run with unavailable provenance rather than an
invented host claim. Coverage input supports a file or standard input. Preserve
the existing safe JSON-input rules and idempotent IDs.

Add run filters for exact instruction-set name, declared version, host agent,
verbatim model, capture method, and current coverage. Combine them with existing
workspace, operation, task, outcome, and date filters using one run identity.
Keep pagination stable under concurrent inserts.

Audit exports include provenance resources and aggregate fingerprints, coverage
observations, message envelopes, and purge tombstones. The optional opaque host
session reference remains labelled as opaque. `--include-content` adds only
currently available content and legacy snapshot bytes; it never returns purged
text. Import/export round trips preserve semantic identities, enum values,
timestamps, ordering, hashes, lengths, and tombstones without turning imported
coverage into automatic coverage.

## Runner and interactive-skill integration

The API runner supplies its own instruction-set name and declared version, host
agent/version, verbatim configured provider and model, `automatic` capture method,
and `api_runner_conversation` coverage. It may claim an exact fingerprint only
for the complete logical instruction resources that it directly assembled and
hashed. Project files later read by the model are authoritative project context,
not installation resources to discover for this fingerprint. Retries and
terminal error paths must not duplicate runs or coverage observations.

Each interactive skill's shared optional-audit reference supplies the logical
instruction-set name and uses `instruction_driven` with
`skill_conversation`. It records fingerprint fidelity `unavailable` unless the
host explicitly supplies the complete loaded-resource hashes; the agent never
promotes a guessed, repository-discovered, or currently installed file to exact.
If relevant capture was requested but exact visible text is unavailable, record
summarized/incomplete evidence or a partial/missing observation as appropriate.
Never invent a transcript.

Keep all seven `references/optional-audit.md` files byte-identical. Their common
instructions preserve the existing approval gates, runner ownership, Goal child
linkage, and rule that an audit failure cannot undo project work or change task
state.

## Explorer behavior

Timeline cards and run details show the instruction-set name/version, host,
verbatim model, capture method, fingerprint fidelity, coverage, fidelity counts,
and content state. They do not show installation paths (which are not stored) or
the opaque host-session reference by default. Loaded resources appear only by
logical name and hash where that evidence is useful.

Add bookmarkable Timeline filters for instruction set/version, host, model,
capture method, coverage, and whether referenced content was purged. Preserve
pagination and project scoping. Older runs with no v4 provenance or coverage are
labelled `legacy`; they are not silently classified as complete or missing.

Use distinct rendering for the evidence states:

- No envelope or metadata-only capture: `not captured`.
- Incomplete requested evidence: `partial` or `missing`, matching the observation.
- Tombstoned content: `purged`, with hashes, lengths, and references but no text.

Never substitute current Markdown, a later message, or an agent reconstruction
for absent or purged text. Explorer remains read-only apart from its existing
explicit external index refresh. It offers no purge control.

## Documentation and acceptance coverage

Update the SQLite operator guide, README API-only guidance, and affected
published English and Simplified Chinese guides to distinguish structured audit
from raw-message capture; automatic, instruction-driven, and imported coverage;
audit evidence from authoritative Markdown; and logical purge from removal of
backups and exports. Keep provider-specific adapter claims and release actions
out of the documentation until separately implemented and authorized.

Test fresh v4 databases and migrations from v1, v2, and v3, including injected
interruption, retry, foreign-key validation, legacy messages, snapshots, and
unsupported newer databases. Cover canonical fingerprint ordering,
partial/unavailable fingerprints, conflicting retry payloads, omitted paths, and
refusal to infer resources from project files.

Exercise metadata, exact, redacted, summarized, incomplete, missing, imported,
parent/child Goal, and unfinished-run coverage. Test purge confirmation,
tombstone idempotency, referenced-message rendering, export exclusion, WAL
checkpoint reporting, backup limitations, immutable-table guards, permitted run
finalization, concurrent writers, pagination, filters, and semantic export
preservation. Browser coverage includes desktop and narrow layouts, deep links,
filters, legacy records, missing evidence, and purged evidence.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL13-T01 | [+] | Finalize v4 provenance, capture-coverage, fingerprint, and purge contracts. | Contracts preserve Markdown authority, forbid project-wide instruction discovery, and define every enum, identity, retry, and privacy rule. |
| SQL13-T02 | [+] | Implement the transactional v1–v3 to v4 migration and immutable storage guards. | Existing durable records and message bytes survive; interrupted migration rolls back; prohibited direct updates/deletes fail. |
| SQL13-T03 | [+] | Implement provenance, coverage, message-content separation, filtering, export, and explicit purge CLI behavior. | Idempotent retries work; purged content cannot be queried or exported; envelopes and tombstones remain inspectable. |
| SQL13-T04 | [+] | Integrate API-runner and interactive-skill recording contracts. | The runner records automatic provenance without duplication; interactive skills report instruction-driven coverage and never invent exact fingerprints or transcripts. |
| SQL13-T05 | [+] | Add Explorer provenance and coverage display and filters. | Exact, partial, missing, legacy, and purged runs remain distinguishable and bookmarkable without exposing paths or deleted text. |
| SQL13-T06 | [+] | Complete documentation, migration/privacy tests, full acceptance, and bounded review. | Required repository, DSH, browser, website, copied-toolkit, migration, and SQLite tests pass with no blocking review findings. |

## Required gates and handoff

Run the focused and complete Python suites, including migration, SQLite, runner,
Explorer, and repair coverage. Then run:

```bash
python3 check.py
python3 -m unittest discover -s tests
npm ci --prefix tests/dsh --ignore-scripts --no-audit --no-fund
npm test --prefix tests/dsh
npm ci --prefix tests/browser --ignore-scripts --no-audit --no-fund
npx --prefix tests/browser playwright install chromium
npm test --prefix tests/browser
python3 -B tests/benchmark_sqlite.py
mkdocs build --strict
git diff --check
```

The isolated browser suite, copied-toolkit checks, and the three focused SQLite 13
regressions also pass. The final evidence is Python 3.14.4, SQLite 3.46.1,
DSH 13 tests, two Chromium journeys, six isolated browser journeys, the 120-status
and 2,400-task benchmark, strict MkDocs, and `git diff --check`. Review iteration:
1 (initial whole-milestone review; no blocking findings). The milestone is
implemented locally; merge, push, publication, and release remain separate
actions.

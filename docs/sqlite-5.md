# SQLite 5 — Audit storage and runner repairs

Plan state: [+]

Depends on: review of SQLite 1–4

These follow-up tasks implement the approved audit and rebuildable-index design.
Earlier task IDs and evidence remain historical; their completion claims do not
establish acceptance of the revised design. Markdown remains authoritative.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL5-T01 | [+] | Harden storage, migration, identity, capture, and export | Storage regression tests preserve existing evidence and reject unsafe destinations. |
| SQL5-T02 | [+] | Repair optional runner integration and terminal outcomes | Standalone runner and every audited exit retain existing workflow gates. |

## Verification and review

SQL5-T01: storage regression suite passes, including real concurrent writers,
foreign databases, retry identity, capture enforcement, complete export, and
v1 snapshot preservation.

Execute one row at a time, commit each verified row, and record evidence here.
SQL5-T02: runner suite and new copied-install, blocked-transition, internal-DB,
commit-before-failure, and unexpected-exception regressions pass.

Review iteration: 4. Review found that new database creation could leave an
empty file after an interrupted migration, recovery destinations could collide
with SQLite sidecars, run retries could be tied to changed Git metadata, and
combined milestone/task filters could match different events. Creation now
cleans up on failure, destinations reject all sidecars, retries reuse the
recorded identity with payload checks, and combined filters apply to one event.
Reverification: all 63 focused SQLite and runner tests pass; clean review. The initial
whole-milestone review is iteration 1; verify and review after fixes, with at
most 10 iterations. A clean pass is required.

Final review also corrected mixed timestamp precision in date filters and rejected
WAL/SHM/journal symlinks before SQLite opens. An injected schema-migration
interruption rolls back completely and succeeds on retry. Storage regressions pass.

Review iteration: 5. Database backup now writes and validates a private staging
file before atomically publishing the destination. An abrupt process exit can
leave an ignorable staging file, but cannot expose a partial file under the
requested backup name; retrying that destination remains safe. Existing storage
validation now verifies required column constraints, foreign keys, uniqueness,
and named indexes as well as their names, integrity, and version marker. A
migration validates the complete target schema before committing its new version,
so a conflicting preexisting future table cannot be silently blessed.

The API runner's embedded instruction also makes recorder ownership explicit: an
audited runner turn does not search for an interactive skill reference or invoke
the host CLI, preventing a missing bundle path or duplicate run from stopping the
task loop.

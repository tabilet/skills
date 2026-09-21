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

Review iteration: 3. Review found an initial HEAD incorrectly recorded as a new
commit in blocked-only runs; fixed by capturing its baseline without requiring HEAD.
Reverification: all 58 harness tests and both runner repair tests passed; clean review. The initial whole-milestone review is iteration 1; verify and
review after fixes, with at most 10 iterations. A clean pass is required.

Final review also corrected mixed timestamp precision in date filters and rejected
WAL/SHM/journal symlinks before SQLite opens. An injected schema-migration
interruption rolls back completely and succeeds on retry. Storage regressions pass.

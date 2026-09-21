# SQLite 7 — Host commands and workflow integration

Plan state: [+]

Depends on: SQLite 6

These follow-up tasks implement the approved audit and rebuildable-index design.
Earlier task IDs and evidence remain historical; their completion claims do not
establish acceptance of the revised design. Markdown remains authoritative.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL7-T01 | [+] | Provide a complete host CLI and refresh integration | A fresh CLI lifecycle, filtered queries, and safe backup/restore work without seeded records. |
| SQL7-T02 | [+] | Connect optional skill audit hooks | Seven standalone bundles explain opt-in capture and share identical instructions. |

## Verification and review

SQL7-T01: 33 SQLite tests pass, including fresh host lifecycles for seven operations,
retry delivery, capture policy, filtered queries, packaged installs, and rebuild
preservation. API completion refreshes the derived index without changing outcomes.

Execute one row at a time, commit each verified row, and record evidence here.
SQL7-T02: all seven standalone references are identical and routed from their
skills; the three daily-instruction copies agree. Credential-free host and bundle
checks validate optional loading and capture provenance.

Review iteration: 1 (passed). The initial whole-milestone review is iteration 1; verify and
review after fixes, with at most 10 iterations. A clean pass is required.

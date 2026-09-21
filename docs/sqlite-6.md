# SQLite 6 — Rebuildable Markdown index

Plan state: [+]

Depends on: SQLite 5

These follow-up tasks implement the approved audit and rebuildable-index design.
Earlier task IDs and evidence remain historical; their completion claims do not
establish acceptance of the revised design. Markdown remains authoritative.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL6-T01 | [+] | Implement atomic current-source indexing and search | Source lifecycle, parser, identity, search, and rebuild tests pass without Markdown writes. |

## Verification and review

Seven index regression tests pass: real task rename/duplicate/retirement,
failed-generation preservation, transactional rollback, branch context, source
races, symlinks, all-retired/archive-only layouts, explicit IDs, and both search modes.
Project hashes and original audit evidence remain unchanged.

Execute one row at a time, commit each verified row, and record evidence here.
Review iteration: 2 (passed). Installed-CLI testing found refresh changed durable
workspace timestamps; refresh now reuses workspace identity without changing
audit metadata. Complete audit exports remain identical across rebuild. The initial whole-milestone review is iteration 1; verify and
review after fixes, with at most 10 iterations. A clean pass is required.

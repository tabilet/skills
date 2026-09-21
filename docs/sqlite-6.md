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
Review iteration: 4 (passed). Review found that separate metadata and row reads
could observe different index generations, milestone-filtered sections lacked
their milestone identity, task ID lookup could cross table boundaries, and a
mixed-layout refresh could leave a falsely complete generation. Search and show
now use one read snapshot, section IDs come from headings, explicit IDs are
resolved within their table, and failed refreshes record incomplete diagnostics
while retaining the previous generation. The initial whole-milestone review is
iteration 1; verify and review after fixes, with at most 10 iterations. A clean
pass is required.

Final review corrected source offsets around fenced envelope examples, deduplicated
linked dependency IDs, exposed unchecked source freshness, and diagnosed incomplete
archive provenance. Canonical template and malformed-retirement tests pass.

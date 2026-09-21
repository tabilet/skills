# SQLite 8 — Documentation and acceptance

Plan state: [+]

Depends on: SQLite 7

These follow-up tasks implement the approved audit and rebuildable-index design.
Earlier task IDs and evidence remain historical; their completion claims do not
establish acceptance of the revised design. Markdown remains authoritative.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL8-T01 | [+] | Document interfaces and validate the completed branch | Python checks, DSH tests, strict website build, scale evidence, and review pass. |

## Verification and review

- `python3 check.py`: all 35 repository checks passed, including the complete
  Python behavioral suite and copied payload contracts.
- `npm test --prefix tests/dsh`: 13 credential-free tests passed on Node 24.14.1.
- `mkdocs build --strict`: English and Chinese builds succeeded. The installed
  i18n plugin reports its existing lunr-language detection warning; build exit is 0.
- `git diff --check`: passed.
- Fresh CLI installation/lifecycle, v1 evidence preservation and interrupted
  migration rollback/retry, real Markdown lifecycle, and index failure tests pass.
- `python3 -B tests/benchmark_sqlite.py`: 120 statuses, 17 lanes, 2,400 tasks;
  initial sync 406.66 ms, unchanged sync 265.77 ms, median of 100 FTS5 searches
  6.11 ms, literal search 1.18 ms (Python 3.14.4 / SQLite 3.46.1).

Review iteration: 2 (passed). Review fixes are recorded in SQLite 5 and 6:
sidecar validation, mixed timestamp precision, retired source locations,
dependency deduplication, and source/provenance diagnostics. Index rebuild leaves
complete audit exports identical. New snapshots remain disabled.

The copied canonical template indexes successfully. Read-only acceptance against
neighboring projects found existing unpadded specification headings in golet,
molecule, and hcllight, and invalid retired-record envelopes in simclaw. These
produce explicit validation errors; this work did not rewrite their source files
or relax execution gates. Their format discrepancies need review before structured
indexing. This is distinct from passing canonical/customized fixtures that retain
the documented source contract.

README, operator documentation, and both published installation guides cover the
optional toolkit, capture provenance, current-text cache, refresh policy, backup,
and migration. Exact chat capture still requires a supplying host; DSH UI and a
graphical explorer are outside this implementation. No merge, push, or release
was performed.

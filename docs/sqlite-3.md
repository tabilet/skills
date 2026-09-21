# SQLite 3 — history and evolution snapshots

Plan state: [+]

Depends on: SQLite 1 and SQLite 2

This milestone stores immutable observations of project history and evolution
after every audited API run. Active milestone and task Markdown remains the
source of truth.

## Snapshot scope

The first snapshot release imports only:

~~~text
tabilet/docs/history/status-*.md
tabilet/docs/history/index.md
tabilet/docs/history/knowledge.md
tabilet/evolution/prompt-vN.md
tabilet/evolution/result-vN.md
~~~

Context archives are deferred. Archive IDs, baseline evidence, and privacy
expectations need their own preservation tests.

Each snapshot stores snapshot ID, workspace ID, kind, original path, exact bytes,
SHA-256, capture time, source commit, worktree state, source run, and optional
predecessor. The run_snapshots relation records that a run observed a snapshot.

## Capture and failure behavior

After every audited API run reaches a terminal result, scan the declared paths.
This applies to completed, blocked, failed, and cancelled results when the
process can read the files. A hard interruption records an incomplete run and
does not invent snapshot completion.

Reject symlinks and paths outside the declared v2 roots. Record missing and
unreadable sources as snapshot-gap events. Changed bytes create new immutable
observations. A frozen retired record that changes is never overwritten.
Snapshot failure never deletes, rewrites, or changes project Markdown or task
status.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL3-T01 | [+] | Add snapshot and run_snapshots migrations and exact-byte storage. | Bytes, hash, kind, path, provenance, and run association round-trip. |
| SQL3-T02 | [+] | Implement safe history/evolution discovery with symlink, root, encoding, and size validation. | Only declared v2 files are scanned; unrelated and archive files are ignored. |
| SQL3-T03 | [+] | Capture snapshots after every audited terminal API run. | Completed, blocked, failed, and cancelled runs produce observations when readable. |
| SQL3-T04 | [+] | Implement deduplication, immutable changed observations, and drift/missing-source events. | Repeated bytes deduplicate; changed or missing files preserve earlier evidence and produce diagnostics. |
| SQL3-T05 | [+] | Add backup and restore verification to a separate destination. | A live backup restores all records without touching the project. |
| SQL3-T06 | [+] | Test ordinary, all-retired, knowledge-history, evolution-version, customized, no-Git, drift, and interrupted cases. | Exact hashes and run associations remain correct in every fixture. |

## Completion gate

This milestone is complete when an audited API run retains history/evolution
observations without replacing or modifying project Markdown. Milestones 1–3
then constitute the first SQLite release.

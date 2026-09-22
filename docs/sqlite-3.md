# SQLite 3 — history and evolution snapshots

Plan state: [-] — superseded by the revised index design in SQLite 5–8.

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
| SQL3-T02 | [-] | Implement safe history/evolution discovery with symlink, root, encoding, and size validation. Superseded by SQL6-T01's current-source index. | Only declared v2 files are scanned; unrelated and archive files are ignored. |
| SQL3-T03 | [X] | Capture snapshots after every audited terminal API run. Cancelled when the revised design retained Markdown and Git as authority. | Completed, blocked, failed, and cancelled runs produce observations when readable. |
| SQL3-T04 | [X] | Implement deduplication, immutable changed observations, and drift/missing-source events. Cancelled with automatic snapshot capture. | Repeated bytes deduplicate; changed or missing files preserve earlier evidence and produce diagnostics. |
| SQL3-T05 | [+] | Add backup and restore verification to a separate destination. | A live backup restores all records without touching the project. |
| SQL3-T06 | [-] | Test ordinary, all-retired, knowledge-history, evolution-version, customized, no-Git, drift, and interrupted cases. Snapshot-specific coverage was superseded by SQL6-T01; legacy-byte preservation remains covered by SQL5-T01. | Exact hashes and run associations remain correct in every fixture. |

## Review follow-up

Legacy snapshot restoration writes to a private temporary file and publishes it
only after the bytes and hash have been verified, so interrupted recovery does
not leave a destination that blocks a retry. Automatic post-run snapshot capture
was cancelled by the revised design. The current-source index locates
authoritative Markdown without freezing new copies.

## Completion gate

This historical milestone is superseded. Its legacy snapshot schema and recovery
work remain accepted; SQL5–8 own the revised release contract.

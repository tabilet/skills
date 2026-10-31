# Historical record compatibility and corrections

The standalone runner owns the shared historical reader. Lookup, the SQLite
index, dependency projection and API validation use the same interpreted record.
The original specification, status text, metadata and source locations remain
separate from interpreted metadata and task cells. New retirement records still
use the strict envelope; historical compatibility cannot authorize a new format.

Supported older envelopes include status-section aliases (`Status`, `Status
document`, `Full status document`, `Final status`, `Source status ledger`), bare
Markdown fences, level-three milestone headings, annotated source anchors and
the retained `Related approved correction context` section. A milestone heading
with another explicit ID is never a format variation. Shared or unnamed
specifications require an explicit reviewed identification.

## Project manifest

The optional project file is `tabilet/docs/history/corrections.json`:

```json
{
  "schema": "tabilet.history-corrections/v1",
  "records": []
}
```

Each record has exactly `milestone_id`, `record_path`, `record_sha256` and a
nonempty `corrections` array. Paths name root history status or child records;
SHA-256 binds the exact UTF-8 bytes, including newline endings. JSON duplicate
keys, duplicate records, conflicting operations, unknown fields, stale hashes,
symlinks and nonregular or oversized inputs fail closed. Inputs are bounded at
4 MiB. The manifest is optional; an absent file preserves ordinary history use.

Supported operations have these exact additional fields:

| `kind` | Fields | Interpretation |
|---|---|---|
| `expand-evidence-commit` | `recorded`, `resolved` | Expand one recorded abbreviated commit to its verified full object ID. |
| `resolve-evidence-set` | `commits`, `evidence` | Retain the full identities behind a recorded provenance list. This is not a claim that the first source was an observed HEAD. |
| `identify-specification` | `heading`, `evidence` | Identify ownership in the complete retained shared or named specification. Explicitly mismatched IDs remain invalid. |
| `historical-successor` | `item`, `successor`, `evidence` | Resolve one historical row to one uniquely named completed row, preserving both task states and literal notes. |
| `recover-document` | `document`, `content`, `sha256`, `source` | Supply the full literal `specification` or `status` from reviewed source evidence. |
| `supply-metadata` | `field`, `value`, `evidence` | Interpret a missing closure field, or normalize an annotated review count without changing its number. |
| `blocker` | `message`, `evidence` | Preserve an unresolved evidence gap. It cannot be removed by interpreting terminal task markers as acceptance. |

Metadata fields are limited to the strict envelope's identity, outcome, date,
source paths, provenance, review, verification and consolidation fields, plus
review-limit evidence. Existing contradictory values cannot be overwritten.
Multiline metadata, arbitrary field patches, task-state changes and authorization
fields are unsupported. A passed-review correction requires an explicit,
standalone recorded result such as `Review: passed` or `| Review | passed |`;
an instruction, a merely performed review, or a negative statement cannot
support it.

Evidence normally names `start_line`, `end_line` (one-based, inclusive) and an
exact `quote` from the hash-bound frozen record. External index or specification
evidence additionally embeds `path`, full `commit`, literal `content` and its
`sha256`; ranges and quotes must agree with that content. Recovered documents
carry full `commit`, original `path`, `start_line`, `end_line` and
`source_sha256` (the entire source blob) in `source`, as well as a separate
checksum of the recovered document. Record-local recovery must match the exact
frozen byte range.

Prepare and verify Git source blobs, ranges, object IDs, evidence quotations and
the complete manifest before project approval. Embedded Git evidence permits
later read-only lookup without Git; runtime checksums establish consistency, not
the truth of a claim or human approval. A reviewable proposal must show exact
file actions and the final manifest SHA-256 under the owning project's rules.
Neither this schema nor any field in the manifest constitutes that approval.

## Incomplete evidence and execution

Recovered records with missing closure fields remain searchable. Their missing
fields are marked `not recorded` or `unverified` in the interpreted projection,
with explicit blockers. Internal validation placeholders never become recorded
facts. Unfinished rows, conflicting retained review counters and explicit
blockers prevent runner readiness and completed-dependency acceptance. Historical
`[x]` task cells retain their literal spelling and remain lookup-only evidence.

The index records the manifest as a source and invalidates affected cached
projections when it changes or disappears. Workflow approval snapshots and
interrupted-run recovery include its bytes. Task execution and closure reject
any manifest addition, mutation or removal; a model cannot correct history to
discharge its own gate. New retirements must pass the strict contract and the
fixed API review ceiling of 10. Reading previously reviewed extended history
never enlarges that execution ceiling.

Use the runner's `history_snapshot` or `row_snapshot` and the index's `sync` and
`readiness` library functions for offline readiness checks. Importing those
functions does not launch the runner or dispatch a provider. Validate a proposed
manifest against a scratch copy and report every remaining blocker. Keep live
execution approval separate.

The literal M99, M100 and M153 records in `tests/fixtures/retired-history/` retain
the Ramen source bytes and source-path metadata. Their correction fixture binds
the M99/M100 identities to those hashes. The integration tests check discovery,
physical task locations, lookup, dependency acceptance and runner validation.

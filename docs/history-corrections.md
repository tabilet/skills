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
When a retained status explicitly names a milestone in its heading, metadata or
task rows, that identity must match the frozen record. A content hash binds
bytes but does not reconcile conflicting milestone identities. Only a
well-formed milestone ID counts: a heading such as `# Q4 results` or a legacy
`M1.1` task prefix names no milestone, and an ID compares case-insensitively.

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
support it. A literal `Whole review N/L PASS with no P1/P2.` is also supported
when its iteration matches the recorded counter and does not exceed its stated
limit. One earlier numbered failure in the same literal line is allowed only
when it has the same limit and a lower iteration. The complete line must be
cited; a task review, prospective instruction, later conflicting text or an
unmatched counter cannot supply a pass. For both canonical and numbered pass
forms, the cited literal line must be unfenced and belong to the frozen record's
retirement metadata or retained status review section. A canonical standalone
result in the status metadata preamble remains supported. Numbered results must
occur in a review section, match the recorded iteration and limit, and not
conflict with other recorded outcomes. Fenced or headed examples, templates,
prospective instructions and specification statements cannot supply a result.
Unrecognized prose following an explicit final review pass in the envelope,
status preamble or retained review section blocks acceptance, even when the
prose is harmless.
Unrecognized review-result claims in other structured metadata also block
acceptance; that conservative rule can flag benign historical summaries.
Adjacent Markdown field continuation lines, including nested list or quote
lines and values beginning after the label, are checked as one paragraph.
Explicit review-result references in standalone authoritative prose are also
blocking when unsupported. Fenced and indented code remain examples;
validation does not join source lines across those omitted blocks. Literal
documents, recovered source identifiers and offsets are not rewritten.
Recognition is limited to supported explicit historical forms and does not
establish the meaning of arbitrary natural-language references. Ambiguous
post-result prose in the same authoritative context remains a blocker. The few
fixed sentences that restate, rather than qualify, a recorded decision are
listed in `RECOGNIZED_PROSE` in the runner; wording outside that table stays
ambiguous, so it is a deliberate, narrow allowance and not a general parser. A
retained review counter that disagrees with the retirement metadata is a
conflict wherever it appears in a trusted line, including bullets and table
cells.

Corrected outcome and retirement date require a matching identity-bound index
row or explicit retained status metadata. Corrected review counts require an
explicit recorded counter; review-limit corrections require recorded evidence,
and extended-limit approval must cite an explicit, affirmative recorded human
continuation or extension; the citation must match a supported complete
affirmative statement, and ambiguous, reversed or conditional language is not
evidence. A named continuation must identify the same milestone, and a stated
ceiling must match the recorded limit. Citations include the complete selected
lines and the adjacent continuation of their paragraph. Unrecognized later
approval or decision references in the retained review context block the
interpretation, including unrelated references that cannot safely be ruled out.
Literal approval
metadata and correction values must also use supported affirmative or recorded
interpretation forms; an interactive launch ceiling is accepted only in the
literal review-limit approval field, with a matching numeric limit. Ambiguous
literal metadata remains a blocker. Corrected
commit provenance must cite the recorded commit prefix in a provenance context;
worktree claims require an explicit worktree statement. Verification summaries
must be drawn from literal recorded test or check results without contradictory
failure wording; consolidation claims must appear in retained evidence. An
unrelated completed task row cannot supply any of these closure facts.
Corrected identity and source paths must agree with the retained status and
specification; a specification anchor must be supported by a retained source
declaration, explicit anchor or matching heading.
Explicit status/outcome conflicts and ambiguous same-iteration review results
remain blockers. A recorded legacy `not recorded` counter and a rowless
withdrawal's recorded zero counter remain supported without inventing a pass.

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

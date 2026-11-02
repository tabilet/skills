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
Two readings apply, and which one depends on whether a correction supplies the
review pass.

When a correction supplies the pass, the conservative rule holds: unrecognized
prose following an explicit final review pass in the envelope, status preamble
or retained review section blocks acceptance, even when the prose is harmless.
An unrecognized qualification is never made safe merely because a vocabulary
did not match it.

When the record carries its own pass, prose after it blocks if it reverses,
withdraws or conditions that result. Every clause there about the review should
also be one complete recognized form: a restatement of the pass with matching
counters, a reference to where the result is recorded, or a findings summary
(listed in `RECOGNIZED_REVIEW_SENTENCES` in the runner). The forms have no
free-text tails, so "Review found no defects but was annulled." is not a
findings summary. The same rule covers a clause led by a pronoun, or one with a
pronoun after a clause that named the review ("Review passed. Later it was
annulled.").

A clause about the review that is not a recognized form blocks when it names the
review, or refers back to it, together with a reversal word such as voided,
annulled, revoked, withdrawn, reopened, rescinded or set aside, however far that
word is from the subject. Otherwise it is a **warning**, not a blocker: real
history is phrased too variously for exact forms to be a gate, and the strict
retirement contract never reads this prose. Warnings name the record and the
clause. The API runner prints them before its first run, the first ten in full
with a count of the rest, and continues; the SQLite index records them as
`warning:` diagnostics without marking the review unverified; `tabilet status`
reports them as `history_warnings`. A person should read each one, because a
reversal phrased outside the vocabulary ("the review result was later deemed
moot") is reported here and nowhere else.

Ordinary notes that do not mention the review, task-level reviews, findings
lines and iteration history are not assertions about it. A fenced block between
the pass and later prose does not end the context: its contents are ignored, but
prose after it is still read as a continuation of the same result. The same validator
applies to the claim fields of the envelope and retained status (`State`,
`Status`, `Verification`, `Outcome`, `Result`, `Acceptance`, `Closure`,
`Review gate`, `Disposition`); provenance and dependency fields are not claims
about this review. The same distinction applies to numbered references such as
`review 2/10`:

- A wrapped paragraph is judged as one unit, so a line break cannot separate a
  reversal from its subject. A table row after the pass is read cell by cell:
  only an earlier or final iteration's own verdict word is history, and the rest
  of the row is still read, counters first; a final-iteration failure or a later
  iteration blocks. A header row of plain labels is structure, not a verdict.
- Every review or iteration counter in a paragraph is checked against the
  record before anything else, whether or not the clause names the review, in
  either word order ("review passed 2/10", "review 2/10 passed", "iteration 3
  passed", "Passed 9/10."): a pass at another iteration or limit, or an iteration
  beyond the final one, blocks. An earlier iteration may be cited or may have
  failed. A ratio that is not attached to a review ("all 12/12 checks"), a date
  or repeat count ("passed 2026-09-29", "passed 20 times") and a task-level
  review ("M01.2 review 4") are not counters. A reference with no verdict
  ("see review 2/10") is not a verdict.
- A counter is another milestone's only when that milestone's ID leads the
  claim within a few words, with no "our", "this" or comparison between them,
  and the clause does not name this record's own ID ("M02 review 3/10 passed").
  "Compared with M02, our review 3/10 passed." is this record's counter.

A clause is adverse when a review-result subject (review, result, verdict,
outcome, decision, pass, acceptance, approval) is near, or leads the clause
that holds, a reversing or conditioning predicate such as invalidated, revoked,
withdrawn, failed, contingent, provisional, pending, "provided that" or "no
longer valid". A negation counts only inside its own clause, so it does not
carry across "and" or "but" ("was not invalidated and was withdrawn" is a
withdrawal). Strong reversals also count against
a pronoun or "above"-style reference, and directly after a pass a leading
pronoun stands for that pass ("It is conditional on ..."). A failed test or
build, and a failure at an earlier iteration, is not a failed review; a
failure at the final or a later iteration is. This is a vocabulary, not a
parser: a reversal in other words can still pass an uncorrected record, with at
most a warning, and the adverse vocabulary blocks some harmless sentences
("Review passed and the deployment is pending."). The check applies to every
historical record, because the strict retirement contract does not read
retained narrative: it accepts a record whose status later says the result was
invalidated. Adjacent Markdown field continuation lines, including nested list
or quote lines and values beginning after the label, are checked as one
paragraph. Fenced and indented code remain examples; validation does not join
source lines across those omitted blocks. Text after a heading that leaves the
review section is no longer a continuation of the pass. Literal documents,
recovered source identifiers and offsets are not rewritten. Recognition is
limited to supported explicit historical forms and does not establish the
meaning of arbitrary natural-language references. The few fixed sentences that
restate, rather than qualify, a recorded decision are listed in
`RECOGNIZED_PROSE` in the runner; wording outside that table is judged by the
rules above, so the table is a deliberate, narrow allowance and not a general
parser. A retained review counter that disagrees with the retirement metadata
is a conflict wherever it appears in a trusted line, including bullets and
table cells.

A unique completed `Deep code review & milestone retirement` task under the
status `Tasks` heading is also supported when its full cited row records that
the review was performed with zero defects remaining and the same milestone was
retired to its matching history path. The retained status must record its own
positive review counter. The task identity, complete row and literal source
location are checked, and the row must be the last substantive status evidence
without a separate review narrative. A task marker alone, partial quotation, prospective or
qualified result, another retirement-review task, conflicting review evidence
or mismatched counter cannot establish a pass. Saying a verification suite was
run does not establish that its tests passed; missing closure fields block.

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

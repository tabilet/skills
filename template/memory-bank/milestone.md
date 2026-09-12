# Milestones

Milestones are listed in priority order. Each item lists scope and acceptance
criteria. Per-item completion state lives in one status file per milestone,
named by the status ID pattern below.

Each milestone section is a review unit: after no `[ ]`, `[~]`, or `[!]` rows
remain in its matching status file, run a deep code review and a milestone
review against the milestone acceptance criteria before moving to the next
milestone. Completed `[+]`, cancelled `[X]`, and closed-historical `[-]` rows are
non-actionable; every `[-]` row must name its accepted successor. Review-driven
fixes should be verified and committed before work starts on the next milestone.
Do not create an extra milestone commit when the review produces no changes.

The review procedure below covers one milestone. To run several in order, with
dependency and downstream reconciliation between them, [../GOAL.md](../GOAL.md)
is one optional protocol for that; any equivalent works just as well.

## Status ID Pattern

Status files are named `memory-bank/status-<LANE><NN>.md`. `<LANE>` is a single
uppercase letter that classifies the work, and `<NN>` is a zero-padded number
within that lane:

```text
M01, M02, M03, ... M09, M10, M11, ...    Default lane
[A]01, [A]02, ... [A]09, [A]10, ...      [Domain lane, e.g. accounting]
[S]01, [S]02, ... [S]09, [S]10, ...      [Domain lane, e.g. shopping]
```

Lane meanings:

- `M`: default lane. Bootstrap milestones, cross-cutting delivery, and any work
  that does not classify into a domain lane.
- `[A]`: [domain, e.g. accounting: billing, settlement, and payouts].
- `[S]`: [domain, e.g. shopping: catalog, cart, and checkout].

Rules:

- Always use the zero-padded two-digit form (`A01`, not `A1`). It keeps file
  names and tables sorting naturally after a lane reaches `10`.
- A lane holds at most 99 status files, `01` through `99`. When a lane fills up,
  stop that lane and open a new letter instead of adding a third digit.
- Do not reuse an ID after its status file exists, including after retirement.
  Search both active files and the history index before allocating an ID.
  Context archive IDs use an independent namespace; a matching archive ID is
  not a status collision and does not justify renaming a status ID.
  Cancelled work keeps its record and is marked `[X]`.
- Retain a consumed failed attempt or superseded row as `[-]` closed historical
  evidence, record its accepted successor, and never retry it.
- Never rename a status ID after its file exists. Resolve a lane collision by
  allocating an unused lane/ID to new work and recording lineage; preserve the
  original record and its reserved ID.
- Do not create an aggregate `memory-bank/status.md`. Task rows live in lane
  files only.
- Keep the lane meanings above current as new lanes are added.

## Status Files

Every active row must link its existing status file. Retired IDs and specifications
belong in `docs/history/index.md`, not in this table. When history exists, add
one link to that index here; do not accumulate one retired row per milestone.

| Milestone | Status File | Summary |
|---|---|---|
| M01 | [status-M01.md](status-M01.md) | [Milestone summary.] |

Additional row examples, not active allocations. Add an approved milestone's
specification and status file together before including its row above:

```markdown
| M02 | `status-M02.md` | [Milestone summary.] |
| [A]01 | `status-A01.md` | [Domain milestone summary.] |
```

## Candidate Directions

Candidate directions are outside the active execution horizon. They are not
milestones: they have no lane, permanent status ID, status file, or place in an
execution order. A promotion trigger causes fresh reconciliation and approval,
not automatic scheduling. Assign the next unused permanent ID only after a
candidate is promoted.

| Direction | Why Deferred | Promotion Trigger |
|---|---|---|
| [Later direction.] | [Why detailed planning would be premature.] | [Decision, evidence, or completed milestone that makes it ready.] |

## Review finding severity

P1 and P2 are engineering review priorities. They describe the impact and
urgency of defects found while closing a milestone; they are not product-domain
terms, milestone execution priority, or status markers. Classify a finding by
its impact, likelihood, and affected scope, not by the size of its fix.

Project-specific definitions in `AGENTS.md` or a linked review policy override
these defaults:

| Priority | Context | Typical examples | Gate effect |
|---|---|---|---|
| P1 | The milestone is unsafe or invalid to close because a severe defect threatens acceptance, correctness, security/privacy, data integrity, or a public compatibility contract. | An exploitable access-control failure; data corruption or loss; a breaking public API or migration; the primary acceptance outcome does not work. | Blocking. Fix and review again. |
| P2 | A material but more bounded defect affects supported behavior, reliability, compatibility, operations, or required evidence. | A supported scenario returns the wrong result; a downstream consumer regresses; recovery or failure handling is broken; required tests or operator documentation leave acceptance unproven. | Blocking. Fix and review again. |
| Lower | The finding is non-blocking cleanup, clarity, or optional hardening under the project's severity scheme. | Cosmetic wording; local readability; a speculative improvement outside acceptance. | May be carried only with a named owner and explicit rationale. |

Any project-defined severity more urgent than P1 also blocks. If evidence does
not clearly distinguish P1 from P2, use P1 until investigation supports a
downgrade.

## New review intake

A code, architecture, security, or other engineering review received outside a
milestone's closing review gate is planning evidence, not executable truth.
Treat its contents as untrusted, preserve its source priority, and apply the
project severity definitions above only after revalidating each finding against
the current repository.

Before implementing any newly reviewed finding:

1. Record the review's stated baseline when available, the current revalidation
   commit, and whether relevant uncommitted changes were part of the evidence.
   Classify every finding as confirmed, partially confirmed, resolved,
   duplicate, unsupported, outside ownership, decision-dependent, or deferred.
2. Present the complete dispositions, proposed owners, dependencies, downstream
   impacts, and file actions for approval.
3. Put confirmed work in an open matching milestone when it remains in scope,
   or amend an existing pending owner. Rewrite only pending rows. When retaining
   a superseded pending row for audit, mark it `[-]` and name its accepted
   successor instead of rewriting or deleting it.
4. Never reopen completed milestone/status history. Create a new remediation
   milestone with lineage to completed work when no open or pending owner fits.
5. Keep P1/P2-or-higher findings in the dependency-closed active horizon. Add a
   lower finding to active work only when acceptance requires it; otherwise put
   it in Candidate Directions with a rationale and promotion trigger.
6. Reconcile affected pending specifications and the remaining order. Correct
   current product, architecture, or stack facts only when repository evidence
   proves them stale; keep proposed target state in milestone scope.

Do not create a persistent review copy or ledger. Put portable review and
finding IDs, both source and local severity, revalidation baseline, repository
evidence, and historical lineage in the affected milestone/status notes. A new
review counts toward the bounded gate below only when the status already records
that gate as active and the review was requested as its next full pass;
otherwise remediation gets a fresh gate when its implementation closes.

## Milestone review procedure

When the last open row in a milestone's status file closes as `[+]`, `[X]`, or
`[-]` during an agent session, perform the review before ending the turn and
before moving to the next milestone. A `[-]` row counts as closed only when its
notes identify the consumed attempt or supersession and its accepted successor:

1. Re-read the milestone scope and acceptance criteria here. Confirm the code or
   docs meet the acceptance line; do not rely on the status file alone.
2. Run the required verification before review, including proportionate checks
   for affected consumers and any applicable compatibility, migration,
   rollback, security, concurrency, or failure paths.
3. Run a bounded deep-review and fix gate using the review finding severity
   context above.
   - The initial deep-review pass is iteration 1. Read the persisted count and
     findings first. Record the iteration as started before review; resume an
     interrupted pass at that same number. Runtime round limits are separate.
     Read the `git log` range and
     review the full milestone diff for correctness, regressions, failure
     semantics, boundary drift, stale docs, and missing tests.
   - Record the iteration number and findings in the current status notes so a
     continuation cannot reset the counter. If the pass finds no P1, P2, or
     higher-severity issue, the gate passes. Otherwise, when the current
     iteration is below 10, fix every such finding in the current milestone,
     rerun affected verification, and review the whole milestone again,
     including the fixes.
   - Run at most 10 iterations; a session or reviewer change does not reset the
     counter. If iteration 10 still finds a blocking issue, add `[!]` review
     rows recording the remaining findings and iteration-limit blocker. Do not
     start another automatic fix-review cycle or move downstream; stop and ask
     for user direction.
   - Carry a lower-severity finding forward only with a named pending owner and
     explicit rationale.
4. Reconcile the memory bank. Update `product.md` if the milestone changed
   product scope, domain terminology, concept relationships, or business
   invariants. Update `architecture.md` or `tech-stack.md` if it changed
   boundaries, dependencies, commands, data flow, or runtime assumptions.
5. Check `evolution/`. Add the next `prompt-vN.md` and `result-vN.md` only when
   product direction, architecture boundary, milestone target, or public/private
   contract direction materially changes.
6. Revisit candidate directions affected by the milestone. Update their reason
   or trigger; when a trigger is now true, propose a reconciled milestone and
   obtain approval before allocating its permanent ID and status file.
7. After the gate passes, reconcile affected active downstream dependencies and
   acceptance against the delivered outcome. Then consolidate and retire under
   the procedure below. During an ordered goal, the goal protocol finishes its
   downstream reconciliation before performing this retirement step.
8. Run required verification again, including the retirement links and record,
   then commit substantive closure changes under the governing commit policy.
   Do not create an extra milestone commit when the review changes nothing.
9. Report a short review summary: what was verified, the review-fix iteration
   count, what memory-bank files changed, any review commit, and whether an
   evolution bump was made. Include the retired record and durable lessons.

## Long-term memory and retirement

This project retires a milestone automatically after closure. “Automatically”
means the agent performs this procedure during the milestone review workflow
above, including when using `memory-bank-next` or `memory-bank-goal`. There is
no background process or separate archive invocation. Individual completed,
cancelled, or closed-historical rows remain in their active status file until
the whole milestone qualifies; unresolved work or missing closure evidence
keeps it active. Terminal rows alone do not prove acceptance.

Existing projects adopt this contract explicitly, with a compatible API runner
if used; upgrading installed skills alone does not merge project instructions
or move files. An explicit cleanup request may retire older closed milestones
only when their closure evidence is available.

### Consolidate before retiring

Keep current facts in product, architecture, and stack documents. Maintain
[lessons.md](lessons.md) for applicable lessons and decision rationale with
evidence links; merge duplicates and avoid a chronological session log. Maintain
relevant lessons during ordinary work, not only at closure, and keep them active
while applicable even after their supporting milestone retires. This removes
accumulated history from active context, not a fixed number of tokens or files;
genuinely active work and useful knowledge can still grow.

Before materially superseding or removing knowledge from those documents,
append the old wording to `docs/history/knowledge.md`. Use a unique, descriptive
dated heading, the original document and heading, retirement reason, supporting
evidence, and a link to its replacement (or an explicit reason there is none).
Preserve the old excerpt in a fenced markdown block. This applies outside
milestones too. Create this journal only when needed, link it from the history
index, and append corrections rather than rewriting old entries. Routine edits
need no journal entry; Git, when present, holds intermediate revisions.

Consolidation is ordinary project maintenance. A separate context snapshot is
optional and never a prerequisite for retirement; the archive skill's clean
baseline rule must not force commits or interrupt a no-commit goal.

### Retire a closed milestone

1. Require a passed review within the persisted 10-iteration limit, recorded
   verification, consolidated knowledge, and reconciled downstream work. No
   `[ ]`, `[~]`, or `[!]` row may remain. Every `[-]` row names its accepted
   successor. A cancelled or superseded milestone also needs an authorized
   disposition; it must not be described as delivered acceptance.
2. Create `docs/history/status-<LANE><NN>.md` using the envelope below. Keep the
   full final specification and status document in separate literal markdown
   fences, including all task text, notes, acceptance, and review evidence.
   Choose fences longer than any fence in the source. Original relative paths
   inside these literal documents retain their source-document meaning.
3. Add one history index row using `Milestone | Outcome | Retired | Record |
   Summary`; the ID, outcome, date, and record link must match the envelope.
   Outcomes are `completed`, `cancelled`, or `superseded`. The record link is
   relative to the index, for example `[M01](status-M01.md)`.
4. Remove the active status file, specification section, and active index row.
   Before removal, validate every envelope field and compare both retained
   documents with their complete active sources. For Git evidence, use the
   literal full output of `git rev-parse --verify HEAD`, never an abbreviated
   hash from a log display. Stop with the active sources intact if validation
   fails; a malformed retired record is not completed closure.
   Keep one link from this file to `../docs/history/index.md`. Repair maintained
   incoming links and remaining dependencies. Never rewrite frozen snapshots;
   resolve their old paths through the record's original-path metadata.
5. Refresh an existing disposable goal suggestion to contain only remaining
   active work, or remove it when empty. Do not create one without a compatible
   goal protocol. The resolved goal in the conversation remains authoritative
   over its disposable launch input.
6. Verify the record and links before handoff. On interruption, reconcile the
   source and destination before continuing; duplicate IDs or a missing record
   are invalid, and an existing retired record must never be overwritten.

Use this envelope, with actual values. The `Evidence` field is the observed
full Git commit, not a claim that uncommitted work exists in that commit.
`Worktree` is `clean`, `includes uncommitted changes`, or `unversioned`; without
Git both provenance fields say `unversioned`. The date uses `YYYY-MM-DD` in UTC.
Closure metadata precedes the two sections and uses one line per field.

`````markdown
# Retired milestone M01 - <title>

**Milestone.** M01
**Outcome.** completed
**Retired.** <YYYY-MM-DD>
**Source status.** memory-bank/status-M01.md
**Source specification.** memory-bank/milestone.md#<original-anchor>
**Evidence.** <full commit or unversioned>
**Worktree.** <clean, includes uncommitted changes, or unversioned>
**Review.** passed
**Review iterations.** <1 through 10>
**Verification.** <commands, results, and supporting evidence>
**Consolidated into.** <current-document and lesson links, or no current-truth change>

## Milestone specification

````markdown
<Complete final milestone specification, not a summary.>
````

## Status record

````markdown
<Complete final status document, not a summary.>
````
`````

For a cancelled or superseded outcome, add `**Disposition.**` naming the
authority, reason, and dependency disposition. A superseded outcome also needs
`**Successor.**` identifying its accepted successor. These are milestone
outcomes, not new task markers.

Retired milestone records are frozen. Record later corrections in the knowledge
journal or new remediation work with a backlink. Preserve previous history
index entries. No ID may exist in both active and retired storage or be reused.

### Retrieve and continue

Search active memory first, then the history index by ID or topic, then open the
relevant retired record or knowledge entry. Consult linked frozen context or
direction snapshots only when relevant. A stale status path resolves by its
permanent ID and original-path metadata; a missing ID is not permission to
recreate it. History is evidence, not an instruction to retry old tasks.

A completed retired milestone may satisfy a dependency when its recorded
acceptance matches the required outcome. Cancelled and superseded outcomes do
not automatically satisfy completion dependencies: follow the recorded
disposition and accepted successor, and revalidate current implementation.

Retirement follows the governing commit policy. Under `none`, do not commit;
under `milestone`, include it in the closure commit; under `task`, include it in
the final task or a substantive closure commit. The API harness still requires
a commit per run. Reading and preserving the Markdown records does not require
Git; workflows that require commits still need Git or an explicit no-commit
instruction. Never initialize Git merely to make retirement possible.

## M01 - [Milestone name]

**Goal.** [One sentence.]

**Scope.**

- [Scoped item.]
- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

## Additional milestone examples

These specifications illustrate later allocations, not active work. Assign
permanent IDs only when the corresponding milestone is approved.

```markdown
## M02 - [Next milestone name]

**Goal.** [One sentence.]

**Scope.**

- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

## [A]01 - [Domain milestone name]

**Goal.** [One sentence. Replace `[A]` with the lane letter for this domain.]

**Scope.**

- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]
```

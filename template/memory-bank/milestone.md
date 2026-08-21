# Milestones

Milestones are listed in priority order. Each item lists scope and acceptance
criteria. Per-item completion state lives in one status file per milestone,
named by the status ID pattern below.

Each milestone section is a review unit: after all rows in its matching status
file are `[+]`, run a deep code review and a milestone review against the
milestone acceptance criteria before moving to the next milestone. Review-driven
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
- Do not reuse an ID after its status file exists. Cancelled work keeps its file
  and is marked `[X]`.
- Do not rename completed status IDs to make later sequencing look tidy. Rename
  only when an explicit lane-collision decision records the old and new IDs.
- Do not create an aggregate `memory-bank/status.md`. Task rows live in lane
  files only.
- Keep the lane meanings above current as new lanes are added.

## Status Files

Link each row once its status file exists.

| Milestone | Status File | Summary |
|---|---|---|
| M01 | [status-M01.md](status-M01.md) | [Milestone summary.] |
| M02 | `status-M02.md` | [Milestone summary.] |
| [A]01 | `status-A01.md` | [Domain milestone summary.] |

## Candidate Directions

Candidate directions are outside the active execution horizon. They are not
milestones: they have no lane, permanent status ID, status file, or place in an
execution order. A promotion trigger causes fresh reconciliation and approval,
not automatic scheduling. Assign the next unused permanent ID only after a
candidate is promoted.

| Direction | Why Deferred | Promotion Trigger |
|---|---|---|
| [Later direction.] | [Why detailed planning would be premature.] | [Decision, evidence, or completed milestone that makes it ready.] |

## Milestone review procedure

When the last open row in a milestone's status file is flipped to `[+]` during
an agent session, perform the review before ending the turn and before moving to
the next milestone:

1. Re-read the milestone scope and acceptance criteria here. Confirm the code or
   docs meet the acceptance line; do not rely on the status file alone.
2. Run the required verification before review, including proportionate checks
   for affected consumers and any applicable compatibility, migration,
   rollback, security, concurrency, or failure paths.
3. Run a bounded deep-review and fix gate. Use the project's severity meanings
   when defined. Otherwise P1 means a severe acceptance, correctness,
   security/privacy, data-integrity, or public-contract defect; P2 means a
   material supported-behavior, reliability, compatibility, operations, or
   required-evidence defect. Higher severities also block.
   - The initial deep-review pass is iteration 1. Read the `git log` range and
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
7. After the gate passes, run required verification again, then commit any
   review changes. Do not create an extra milestone commit when the review
   changes nothing.
8. Report a short review summary: what was verified, the review-fix iteration
   count, what memory-bank files changed, any review commit, and whether an
   evolution bump was made.

## M01 - [Milestone name]

**Goal.** [One sentence.]

**Scope.**

- [Scoped item.]
- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

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

# Milestones

Milestones are listed in priority order. Each item lists scope and acceptance
criteria. Per-item completion state lives in one status file per milestone,
named by the status ID pattern below.

Each milestone section is a review unit: after all rows in its matching status
file are `[+]`, run a deep code review and a milestone review against the
milestone acceptance criteria before moving to the next milestone. Review-driven
fixes should be verified, and the reviewed milestone changes should be committed
before work starts on the next milestone.

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

## Milestone review procedure

When the last open row in a milestone's status file is flipped to `[+]` during
an agent session, perform the review before ending the turn and before moving to
the next milestone:

1. Re-read the milestone scope and acceptance criteria here. Confirm the code or
   docs meet the acceptance line; do not rely on the status file alone.
2. Run a deep code review of the milestone. Read the `git log` range covering
   the milestone work, then targeted diffs and changed files. Look for
   regressions, boundary drift, stale docs, and missing tests.
3. Reconcile the memory bank. Update `architecture.md`, `tech-stack.md`, or
   `product.md` if the milestone changed boundaries, dependencies, commands,
   data flow, or product scope.
4. Check `evolution/`. Add the next `prompt-vN.md` and `result-vN.md` only when
   product direction, architecture boundary, milestone target, or public/private
   contract direction materially changes.
5. Run required verification, then make a git commit for the milestone changes.
6. Report a short review summary: what was verified, what memory-bank files
   changed, the milestone commit, and whether an evolution bump was made.

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

# Milestones

Milestones are listed in priority order. Each item lists scope and acceptance
criteria. Per-item completion state lives in one `status-Mx.md` file per
milestone, such as [`status-M1.md`](status-M1.md).

Each milestone section is a review unit: after all of its matching
`status-Mx.md` rows are `[+]`, run a deep code review and a milestone review
against the milestone acceptance criteria before moving to the next milestone.
Review-driven fixes should be verified, and the reviewed milestone changes
should be committed before work starts on the next milestone.

## Milestone review procedure

When the last open `status-Mx.md` item for a milestone is flipped to `[+]`
during an agent session, perform the review before ending the turn and before
moving to the next milestone:

1. Re-read the milestone scope and acceptance criteria here. Confirm the code or
   docs meet the acceptance line; do not rely on `status-Mx.md` alone.
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

## M1 - [Milestone name]

**Goal.** [One sentence.]

**Scope.**

- [Scoped item.]
- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

## M2 - [Next milestone name]

**Goal.** [One sentence.]

**Scope.**

- [Scoped item.]
- [Scoped item.]

**Acceptance.** [Clear completion condition.]

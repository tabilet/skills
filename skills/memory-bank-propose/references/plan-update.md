# Safe update of an existing plan

Read when preparing file actions. Apply its writes only after the user approves the complete proposal. Preserve the project's local rules, unrelated content, permanent IDs, non-pending row outcomes, review counters, and frozen archives and retired records. Search both active statuses and the history index before proposing a new ID. Do not reopen completed history. Add approved work to an existing pending owner when its scope and acceptance fit; otherwise propose a new pending milestone or row. An approved superseded pending row may be retained as `[-]` only when its notes name the accepted successor. Changes to in-progress, blocked, completed, or cancelled work need separate handling, not a silent rewrite.

Only in `memory-bank-propose`, for an explicit approved stage rescope, an
untouched `[ ]` row may instead
become `[X]`. Preserve its identity and original task text; add the approval
authority, withdrawal reason, destination `STG-` ID, and dependency disposition
to its notes. The cancelled row proves no delivered outcome. A later replacement
gets a newly approved identity and records lineage to the cancelled one.
Withdraw or amend pending dependents in the same proposal, or retain the
prerequisite in the active horizon; never leave a required dependency pointing
at a cancelled outcome. Preserve non-pending rows and active review counters.
An interrupted or underway row needs its own recovery decision, not this
pending-only rescope. An entire withdrawn milestone keeps its original active
record until ordinary review, disposition, and retirement close it.

Keep the active dependency graph closed and update affected pending downstream scope and acceptance. Candidate Directions remain unnumbered and absent from launch input. When `tabilet/stages.md` exists, keep it aligned with current milestone stage references; stage ideas do not enter launch input. Put intended behavior and durable rationale in milestone/status records; current product, architecture, and stack documents describe only evidenced present facts. Add an evolution pair only when the project's existing material direction-change trigger is met. Refresh `tabilet/memory-bank/suggested.txt` only for an approved compatible `tabilet/GOAL.md` and the whole active horizon; otherwise omit it or propose removal of a stale copy. Never create or modify `tabilet/GOAL.md` as a planning side effect.

Immediately before writing, re-read affected files, relevant worktree changes, status IDs, and retired identities. Compare an interrupted diff with the exact approved proposal. Continue approved compatible edits while preserving unrelated changes. A material change, collision, or uncovered file action requires a revised proposal and approval. Run available structural checks after writing; report verification gaps plainly. Planning writes do not implement work, prove acceptance, commit, retire milestones, launch execution, or mutate external systems.

# Safe update of an existing plan

## Authorization declarations and proposed grants

Keep optional `AUTHORIZATION_REQUIREMENTS` in the owning milestone
specification; status guidance points there without duplicate declarations.
Requirements describe conditions, not permission or scheduled actions. `via`
is `goal-policy` or `explicit`; only local commits and ordinary local
implementation/verification may use `goal-policy`. Other listed actions need
explicit human authority. Inspect exact targets read-only before proposing
scope, preserve project and request restrictions, and surface conflicts.

Any `AUTHORIZATION_GRANTS` in disposable launch input must be labeled
PROPOSED — NOT APPROVED. Map exact milestone keys (package-qualified across
packages) to lists with `grant_id`, `action`, `executor`, and `scope`. Planning approval
alone never activates them. Effective grants require explicit human approval
of concrete scope, with no unresolved placeholders, wildcard targets, blanket
booleans, or credentials. Missing fields preserve legacy behavior without new
authority or migration. Create no approval ledger or audit dependency; do not
launch execution. Grants cannot expand Python API authorization boundaries.

Always emit `AUTHORIZATION_GRANTS` in refreshed launch input, using
`AUTHORIZATION_GRANTS: {}` for the default with no explicit grants. Requirements
stay in the milestone specification; do not duplicate them in `suggested.txt`.
Proposed grants in `suggested.txt` carry decision markers: `[ ]` (need authorization),
`[+]` (approve), `[-]` (deny), and `[~]` (auto). High-level `GLOBAL:` grants declare
common authorities across milestones. When refreshing `suggested.txt`, strictly preserve
existing human `[+]`, `[-]`, and `[~]` decisions on existing grants, and propose `[ ]`
(or `[~]` for safe local commands under goal policy) for new grants. Goal execution
requires verifying that the SHA256 checksum of `suggested.txt` matches human approval.

Executors are `coordinator` or `assigned-agent`. Each requirement has `via`,
`executor`, and any necessary `scope`. This template lists supported
actions; include only applicable entries in a milestone. It grants no
authority and schedules no action:

```yaml
AUTHORIZATION_REQUIREMENTS:
  git.commit:
    via: goal-policy
    executor: assigned-agent
  git.push:
    via: explicit
    executor: coordinator
    scope:
      repository: "<owning repository>"
      remote: "<exact remote URL>"
      ref: "<exact destination ref>"
      mode: fast-forward
  cli.local:
    via: goal-policy
    executor: assigned-agent
    scope: declared-implementation-and-verification
  browser:
    via: explicit
    executor: assigned-agent
    scope:
      environment: fixture
      origins: ["<exact approved origin>"]
      actions: ["<approved action>"]
  sudo:
    via: explicit
    executor: coordinator
    scope:
      commands: ["<specific privileged operation>"]
  ssh:
    via: explicit
    executor: coordinator
    scope:
      host: "<exact host>"
      user: "<account>"
      commands: ["<specific remote operation>"]
```

## Approved plan edits

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

Keep the active dependency graph closed and update affected pending downstream scope and acceptance; never prune downstream impacts to force parallel safety. When proposing new milestones, identify write sets and contract boundaries; parallel-safe defaults to no. Candidate Directions remain unnumbered and absent from launch input. When `tabilet/stages.md` exists, keep it aligned with current milestone stage references; stage ideas do not enter launch input. Put intended behavior and durable rationale in milestone/status records; current product, architecture, and stack documents describe only evidenced present facts. Add an evolution pair only when the project's existing material direction-change trigger is met. Refresh `tabilet/memory-bank/suggested.txt` only for an approved compatible `tabilet/GOAL.md` and the whole active horizon; otherwise omit it or propose removal of a stale copy. Never create or modify `tabilet/GOAL.md` as a planning side effect.

Immediately before writing, re-read affected files, relevant worktree changes, status IDs, and retired identities. Compare an interrupted diff with the exact approved proposal. Continue approved compatible edits while preserving unrelated changes. A material change, collision, or uncovered file action requires a revised proposal and approval. Run available structural checks after writing; report verification gaps plainly. Planning writes do not implement work, prove acceptance, commit, retire milestones, launch execution, or mutate external systems.

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
`AUTHORIZATION_GRANTS: {}` for the default with no explicit grants.
Refresh launch input only when goal use is approved (an existing
`suggested.txt` counts as goal-use intent, never execution approval) and the
selected governing protocol is available and compatible. Preserve explicit
`GOAL_PROTOCOL` selection and its actual path/hash. For stock selection, name
the memory-bank goal protocol and use this bundle's `goal-protocol.json`
`version` and `sha256`. For an alternative, retain `GOAL_PROTOCOL: <path>` and
record `protocol: <path> sha256:<hash>` from the actual selected file, without
requiring a package-local `tabilet/GOAL.md` or substituting stock metadata.
Use the protocol's CRLF-to-LF normalized fingerprints; keep version labels as
descriptive metadata, never identity keys. Launch approval checksums still use
raw bytes. An older launch without identity needs the protocol's explicit
legacy-launch transition, not a silent refresh that activates grants.
Always emit a matching `GOAL_IDENTITY` with every participating package's
addendum hash, `ignored-stock sha256:<hash>`, or `none`. If a package file itself is
the selected alternative protocol, record `selected-protocol sha256:<hash>`
instead of applying it twice as an addendum. Keep invocation and addenda
consistent with the selected protocol. A protocol switch requires explicit
approval; a missing or incompatible selection pauses affected launch refresh
and preserves existing input for resolution instead of silently replacing it.
Never copy the protocol into a project or write a merged protocol. Requirements
stay in the milestone specification; do not duplicate them in `suggested.txt`.
Preserve explicit `MODEL_POLICY` on refresh. Omission preserves host model
settings; add a policy only when requested, as a proposal for future execution,
never as a preset or an effect of planning approval.
Proposed grants in `suggested.txt` carry decision markers: `[ ]` (need authorization),
`[+]` (approve), `[-]` (deny), and `[~]` (auto). High-level `GLOBAL:` grants declare
common authorities across milestones. When refreshing `suggested.txt`, strictly preserve
existing human `[+]`, `[-]`, and `[~]` decisions on existing grants, and propose `[ ]`
(or `[~]` for safe local commands under goal policy) for new grants. Preserve any
explicit `SUGGESTED_UPDATE` policy (defaulting to `confirm`). Preserve the
resolved `OPTION_POLICY: confirm | ignore` on every launch refresh; omission
in an update request retains the existing value, never resets `ignore`.
Fresh launches default to `OPTION_POLICY: confirm`; environment presets do
not change it. Keep an ordinary-prose option deferral when a retained protocol
does not support the structured field; do not silently switch protocols.

Under `--environment dangerous`, synthesize hands-free execution defaults from day one:
`SUGGESTED_UPDATE: auto`, `SCOPE_POLICY: workspace-contained`, `COMMIT_POLICY: task`,
and ambient `GLOBAL:` grants (`- [~] global-local-verify` for local implementation and verification,
and `- [+] global-repo-push` for workspace organization remotes). `SCOPE_POLICY: workspace-contained`
and `global-local-verify` (`[~]`) enable the goal protocol's standing revision envelope for unprivileged
workspace-local verification; write an explicit `standing` block (schema in `GOAL.md`) only for such
local, disposable `cli.local` checks, marked `[~]` (effective when the human approves the launch checksum)
with a budget no larger than the gate's default of 3. Destructive or privileged
operations (`sudo`, `ssh`, live browser, external pushes outside the workspace) remain `[ ]` or
omitted unless an explicit modifier (such as `plus sudo`) authorizes them, and then as an exact-command
grant without a `standing` block. Add a launch comment
with recommended runner flags: `# Recommended harness flags: ALLOW_UNSANDBOXED_SHELL=1`
(and `ALLOW_DANGEROUS_COMMANDS=1` if `sudo` is granted).
For Init and Propose, also propose `CORRECTIVE_PLANNING: auto` in dangerous
mode, and `CORRECTIVE_PLANNING: confirm` in sandbox or least mode. Explicit
human policy overrides the preset. Reconcile preserves the approved corrective
policy during ordinary refreshes; an absent policy defaults to `confirm`.
Changing that standing policy requires human approval, even inside an automatic
correction. Omitted selectors in an existing plan preserve its explicit policy.
Under `--environment sandbox` (default when omitted), synthesize standard fail-safe policies:
`SUGGESTED_UPDATE: confirm`, `SCOPE_POLICY: strict`, and `AUTHORIZATION_GRANTS: {}` (or proposed
grants, including any explicit `standing` block for local verification, marked `[ ]`).
Under `--environment least`, synthesize strict least privilege: `SUGGESTED_UPDATE: confirm`,
`SCOPE_POLICY: strict`, and `AUTHORIZATION_GRANTS: {}`, requiring manual approval for every action;
a modifier-added grant, `standing` or not, is proposed as `[ ]`.
Modifier expressions like `but <action> in milestone <ID>` attach local milestone policy overrides
directly in `tabilet/memory-bank/milestone.md` without polluting global launch references. Goal execution
requires verifying that the SHA256 checksum of `suggested.txt` matches human approval
before activating grants.
Accept `--test standard` (default when omitted), `browserlight`, `golight`, `rustlight`,
`tslight`, `jslight`, or `pythonlight` when newly proposed or remediation milestones require
updating the verification standards in `tabilet/memory-bank/tech-stack.md` and `AGENTS.md`.
Use the bundle-local [testing profiles](testing-profiles.md) for shared light-profile
budgets and language-specific fixtures. An omitted selector preserves existing
project profiles and budgets. Propose any acceptance handoff or budget change
explicitly; a profile never waives required proof or grants external authority.

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

Under a governing Goal or Next request with human-approved
`CORRECTIVE_PLANNING: auto`, its coordinator may prepare and check complete
necessary repair actions and apply them using standing approval. This exception
is limited to the original delivery outcome, approved owning repositories,
existing grants/denials and operational limits. It covers pending amendments,
new repair IDs, dependency updates and corresponding launch/hash refreshes;
ordinary edits outside that correction still follow `SUGGESTED_UPDATE`.
Record the approval basis and before/after hashes in conversation or existing
trusted host state. Do not approve unknown checksum drift, new action grants,
higher limits, new features, candidate promotions or later stages. Preserve
history and active review counters. Standalone Reconcile still needs complete
proposal approval and never starts implementation; nested Reconcile hands
execution back to the existing owner. Children only report needed repairs.

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

For a milestone whose acceptance depends on an expensive or protected check, apply the milestone file's expensive-check rule: acceptance covers only behavior the milestone owns, proved with the smallest workload; real producer or consumer pairing belongs to the adopting milestone; needed host capabilities get a cheap readiness probe as the first row; and an uncounted local diagnostic loop is named. Review intake must not move downstream pairing evidence into such a milestone.

For a light profile, include these rules in the proposed verification
standards and assign the required evidence to the relevant milestone owners.
`standard` adds none of them and keeps the project's existing commands:

- **Execution cadence.** Run focused verification during task loops; run the
  full suite once per unchanged closure candidate and race/UI checks when the
  change touches concurrency or UI and at required closure; rerun the affected
  checks after every review fix.
- **Replacement coverage.** When retiring an implementation, preserve meaningful
  success and failure coverage for retained behavior through its successor.
  Distinguish executed behavior, mocks, compile-only checks and deferred
  integration proof; claim only what the evidence demonstrates.
- **Acceptance readiness.** Identify missing final-acceptance inputs, capabilities
  and authority early through permitted inspection. Prepare concrete approval
  scope while independent authorized work continues. Keep deferred verification
  with its named owner and gate, preserving dependencies, intermediate acceptance
  and action limits. Use existing records. Run a fast preflight of fixtures,
  schemas and launchers before each counted expensive attempt.

When a refactor cannot safely fit into one bounded green change or needs a compatibility transition, plan expand–contract: first add the new form beside the old, migrate callers in green batches with one row each, then remove the old form once no caller remains. A broad mechanical rename that is safely atomic may stay one bounded row; do not add compatibility scaffolding solely because many call sites change.

Record work the user rules out of the project in the milestone file's Out of scope register with its reason. It gets no ID, never promotes, and returns only through a new approved direction; do not re-propose it as a candidate.

Keep the active dependency graph closed and update affected pending downstream scope and acceptance; never prune downstream impacts to force parallel safety. When proposing new milestones, identify write sets and contract boundaries; parallel-safe defaults to no. Candidate Directions remain unnumbered and absent from launch input. When `tabilet/stages.md` exists, keep it aligned with current milestone stage references; stage ideas do not enter launch input. Put intended behavior and durable rationale in milestone/status records; current product, architecture, and stack documents describe only evidenced present facts. Add an evolution pair only when the project's existing material direction-change trigger is met. Refresh `tabilet/memory-bank/suggested.txt` for approved goal use with an available compatible governing protocol and the whole active horizon, following the selection and identity rules above. A package-local `tabilet/GOAL.md` is optional. Preserve unresolved existing launch input; propose removal of a stale copy only as an explicit file action. Never create or modify `tabilet/GOAL.md` as a planning side effect.

Immediately before writing, re-read affected files, relevant worktree changes, status IDs, and retired identities. Compare an interrupted diff with the exact approved proposal. Continue approved compatible edits while preserving unrelated changes. A material change, collision, or uncovered file action requires a revised proposal and approval. Run available structural checks after writing; report verification gaps plainly. Planning writes do not implement work, prove acceptance, commit, retire milestones, launch execution, or mutate external systems.

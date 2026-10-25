# Universal Multi-Milestone Goal Loop

This file defines a reusable protocol for executing an ordered set of project
milestones or status files from a goal request. It is an execution
protocol, not a project roadmap, product specification, or status source.

This file is the stock protocol. It ships with the memory-bank skills, beside
each skill that runs or plans goals, together with `goal-protocol.json`, which
records its version and the fingerprints of earlier released copies. Projects
do not copy it. A project's `tabilet/GOAL.md`, when present, is a project
addendum combined with it at run time (see Protocol Resolution And Identity).
The stock protocol transfers no project-specific paths, lane names, commands,
dependencies, or mutation authority. Those come from the project's instructions
and the supplied goal input.

## Instruction And Project Discovery

Before interpreting this protocol, obey the active system, developer, and user
instructions. Then discover project truth in this order:

1. The nearest applicable `AGENTS.md` files or equivalent repository
   instructions.
2. Product, architecture, technical, roadmap, decision/evolution, and status
   sources named by those instructions.
3. The status or milestone files supplied by the goal request.
4. Current code, schemas, configuration examples, tests, documentation, and
   worktree state.

Project instructions define naming, status markers, repository boundaries,
required verification, documentation ownership, and commit discipline. Do not
invent a lane convention or directory layout when the project already has one.

If required sources cannot be discovered, complete safe read-only exploration
first. Ask the user only when a missing choice or authority would materially
change the result.

Resolve missing information through safe inspection first. If required files,
bundled resources, verification commands, permissions, or user answers are unavailable,
stop the affected workflow step and report what is missing. Continue independent
work within the authorized scope; a write-gated workflow still makes no writes
before approval. Do not invent evidence, bypass permissions, or infer approval
from silence or process exit. Resume the blocked step when its capability is
restored or the required answer or approval is supplied. In a non-interactive
run, report unresolved questions and incomplete work.

Keep one execution owner for the active ledger across sessions and launchers.
Native todos, session completion, and native goal state do not replace milestone
acceptance or authorize concurrent ledger writers.
Under explicitly authorized concurrent leases, that owner controls the
integrated ledger and each child writes only its assigned isolated ledger.
Only the owner refreshes `suggested.txt` when the project uses that disposable
launch reference. Resolve it against live project truth before dispatch; children
never edit it or use it to choose their assignment.

Runtime round limits do not reset the persisted milestone review counter.

## Protocol Resolution And Identity

Resolve the governing protocol before Initialization and record the result.

**Selection.** A request selects this stock protocol when it names it in any
form: the memory-bank goal protocol, the memory-bank goal skill, `GOAL.md`, or a
project path such as `tabilet/GOAL.md` or a coordinator's
`../<repo>/tabilet/GOAL.md`. Such a path selects the stock protocol plus that
package's addendum; the file at the path never becomes a replacement protocol.
Only the dedicated field `GOAL_PROTOCOL: <path>` selects an alternative full
protocol. That file must be complete: it begins with its own protocol title and
carries goal-input, authorization, review-gate, and commit-policy sections. An
addendum, record, or partial file at that path stops the run.

**Fingerprints.** For protocols and package addenda, compute SHA-256 after
replacing CRLF with LF; preserve every other byte, including lone CR, whitespace
and any BOM. Use this normalization for bundled verification, released-stock
recognition and `GOAL_IDENTITY`. The repository pins protocol and registry
checkouts to LF, while normalization also covers older Windows copies and
plain-file installs. Launch-file approval checksums remain hashes of raw bytes.
The registry's `version` describes the package build; only tagged fingerprints
in `released` establish historical release provenance. A working build can
change without changing that descriptive version.

**Package files.** For each participating package, classify `tabilet/GOAL.md`
with the bundled `goal-protocol.json`:

- absent: record `none`;
- the file is the explicitly selected `GOAL_PROTOCOL`: record
  `selected-protocol sha256:<hash>` for that package and its actual path/hash
  in the protocol entry; do not also apply the same file as an addendum;
- byte-identical after CRLF-to-LF normalization to the current or a released
  stock copy: ignore it, record `ignored-stock sha256:<hash>`, and report that
  it can be removed;
- a full protocol copy (it begins with this file's title line) that matches no
  released copy: stop the affected work until the user reduces it to the
  project-specific part or selects it explicitly with `GOAL_PROTOCOL`;
- anything else: a project addendum, recorded by its SHA-256.

**Addenda narrow.** An addendum adds project rules and narrows defaults, such as
a stricter commit policy, extra verification, or forbidden actions. Apply it on
top of the governing protocol. It cannot weaken the review-fix gate,
authorization, single in-progress ownership, required verification, retirement,
or commit-policy safety; stop and report any addendum rule that would.
Precedence is the request, then applicable addenda, then the governing
protocol. Combine them at run time only and write no merged protocol into any
project. Children and resumed sessions receive the governing protocol and each
addendum as paths with their hashes.

**Identity.** Record the resolution as a `GOAL_IDENTITY` block in goal state and
in any launch reference:

```text
GOAL_IDENTITY:
- protocol: stock sha256:<hash>
- <package>: tabilet/GOAL.md sha256:<hash>
- <other package>: none
```

An explicitly selected protocol records `protocol: <path> sha256:<hash>`. List
every participating package, the coordinator included, and record absence as
`none`, so an addendum added later is detected. Recheck the whole block at every
resume and before each child dispatch or re-dispatch. Compare the selected
protocol path (for an alternative), normalized hashes, package membership and
classifications; version labels are diagnostic metadata, never identity keys.
Identical bytes with different release labels do not pause a run. A changed
protocol hash, path, package classification or addendum pauses the affected work
and its dependents until the user approves the new identity; independent work
may continue. A `GOAL_IDENTITY` supplied with a request or launch reference is
verified the same way before execution.

For an older identity containing only `ignored-stock <version>`, recover its
unique approved fingerprint from the released registry or trusted approval
state and compare the actual package file. Materialize the hash when verified;
an ambiguous or unverified mapping requires approval, never a guessed label.

For a fresh launch from legacy `suggested.txt` without `GOAL_IDENTITY`, inspect
live milestones, status, dependencies and package files, then materialize the
complete resolved request and proposed identity in the conversation before
execution. Obtain only missing identity approval unless the invoking human
request already explicitly approves that concrete resolution. An old launch
checksum or installation alone does not approve the newly resolved protocol.
Preserve existing grants, denials, counters and limits; do not activate proposed
grants. Refresh the launch file and its raw checksum only under the applicable
launch-write approval, showing the transition; never silently rewrite approved
input. This is distinct from continuing a previously approved paused run.

For a legacy paused goal without `GOAL_IDENTITY`, recover its previously
approved protocol path/hash from the invoking conversation or trusted host state.
Compare it with the proposed resolution and show the transition. A changed or
uncertain identity requires human approval once before affected work resumes;
do not silently adopt the installed stock version. A verified unchanged identity
may be materialized without a new approval. Preserve grants, denials, persisted
review counters, attempt usage and operational limits throughout the transition.
Installing a plugin or refreshing launch input does not approve that transition.

When planning refreshes launch input, preserve explicit `GOAL_PROTOCOL` selection
and its actual path/hash; use the bundled version/hash only for stock selection.
Keep the invocation, `GOAL_IDENTITY` and package addenda consistent with that
selection. A protocol switch is a visible proposal requiring explicit approval,
never an ordinary progress refresh. Missing or incompatible governing protocols
pause affected launch refresh without replacing the existing selection.

## Goal Input

A multi-milestone request should select this protocol and provide either a strict
`STATUS_ORDER` or a `STATUS_PRIORITY` list for dispatching dependency-ready
milestones. It may also provide project-context paths, a status-file map,
downstream impacts, and execution policies:

```text
Using the memory-bank goal protocol, execute this loop.

PROJECT_CONTEXT:
- AGENTS.md
- path/to/roadmap.md

STATUS_PRIORITY:
F01, S01, O01, P01, X01?

STATUS_FILE_MAP:
F01 = path/to/status-F01.md
S01 = path/to/status-S01.md

DOWNSTREAM_IMPACTS:
F01 -> P01, O01
S01 -> P01, X01

PARALLELISM: 3
INTEGRATION: local-rebase-ff
COMMIT_POLICY: task
SUGGESTED_UPDATE: confirm
CORRECTIVE_PLANNING: confirm
OPTION_POLICY: confirm
OPTIMIZE_POLICY: none
NOTIFY_EMAIL: none
EXTERNAL_MUTATIONS: none
AUTHORIZATION_GRANTS: {}
```

The block above is the portable protocol input. Submit it as an ordinary
request, through a compatible goal skill, or as the objective of an agent's
built-in `/goal` command. The built-in command keeps the objective active; it
does not replace this protocol or make `GOAL.md` ambient. In every form, the
request must explicitly select this protocol, as described in Protocol
Resolution And Identity.

The identifiers above are examples only. They carry no meaning outside the
project that defines them.

Input rules:

- `PROJECT_CONTEXT` is optional. Use it to identify additional project sources
  that repository instructions do not already name.
- `GOAL_PROTOCOL` is optional and selects an alternative full protocol by path.
  `GOAL_IDENTITY` is optional in a request and required in a launch reference;
  either is verified as described in Protocol Resolution And Identity.
- `STATUS_ORDER` is strict execution order. Every earlier required or triggered
  milestone must close before a later milestone starts; its arrows add ordering
  edges even when `PARALLELISM` is enabled. It contains milestone/status
  identifiers, not impact expressions. The contiguous parent/amendment family
  exception is defined in Milestone families below.
- `STATUS_PRIORITY` lists the complete in-scope set, highest dispatch priority
  first, separated by commas. List position adds no ordering edge. Dispatch only
  milestones whose dependencies and impact reconciliation are satisfied, using
  this priority to choose among ready milestones. For example,
  `STATUS_PRIORITY: M01, A01, S01, P01` permits A01 and S01 to run together after
  M01 closes when both feed P01 and the parallel safety checks pass.
- Supply exactly one of `STATUS_ORDER` and `STATUS_PRIORITY`, with each ID
  appearing once. If both are supplied, resolve the conflicting request before
  execution. Never convert an explicit strict order into priority to unlock
  concurrency without user authorization.
- `STATUS_FILE_MAP` is optional when the roadmap or repository naming convention
  already resolves each identifier unambiguously.
- `DOWNSTREAM_IMPACTS` identifies pending specifications that must be
  reconsidered after a source milestone. An impact arrow does not authorize
  executing its targets early and does not replace declared dependencies.
- A `?` suffix means conditional. Skip that status without completing or
  cancelling it when its documented trigger is absent. Required statuses have
  no suffix.
- If neither selection field is supplied, use an unambiguous strict order from
  the project's roadmap. If no such order exists, request one rather than guessing.
- If a supplied strict order conflicts with dependencies, stop the affected
  execution and resolve a corrected order with the user before dispatch. Never
  discard a prerequisite or a requested ordering edge to create concurrency.
- Treat the supplied impact map as a minimum. Reconcile additional consumers
  discovered from implementation and review.
- `PARALLELISM` is optional. It sets the maximum number of concurrent milestone
  leases (defaults to 3 when present without a value). Concurrent execution is
  active only when project instructions explicitly define safe parallel
  ownership, `COMMIT_POLICY` is `task` or `milestone`, and `INTEGRATION` is
  authorized.
- `INTEGRATION` defaults to `none`. When set to `local-rebase-ff`, it authorizes local
  lease branches (`goal/<ID>`), external worktrees outside the project root
  (`../<repo>.goal/<ID>`), rebasing unpublished lease commits onto the captured
  integration branch, and fast-forward-only integration (`git merge --ff-only`).
  Under `COMMIT_POLICY: milestone` it also authorizes creating and amending one
  unpublished aggregate checkpoint, then finalizing that same commit with
  closure before integration. If the request forbids interim commits or
  amendment, use sequential execution for that policy. It does not authorize
  rewriting integrated history, push, publishing, or merge commits.
- `SUGGESTED_UPDATE` is optional. It governs how the orchestrator may adjust the
  disposable launch reference (`suggested.txt`) across milestones during a goal run:
  - `confirm` (default): any modification to `suggested.txt` changes its SHA256
    hash and requires fresh human approval before executing the updated reference.
    An approved `CORRECTIVE_PLANNING: auto` is the scoped exception below.
  - `auto`: authorizes the orchestrator to refresh `suggested.txt` for remaining
    milestones within the approved active horizon (pruning completed milestones,
    updating dependency order, and activating triggered conditional `?` milestones)
    and continue smoothly without pausing for new human authorization. It permits
    no privilege escalation: new unapproved grants (`[ ]`), scope expansions, or
    policy changes still require explicit human approval before execution. The
    orchestrator calculates and records the updated SHA256 checksum in session state.
- `CORRECTIVE_PLANNING` is optional: `confirm` (default) or `auto`. It controls
  necessary corrective planning inside the approved delivery outcome, including
  new repair milestones. It never grants new action permissions or higher limits.
- `OPTION_POLICY` is optional: `confirm` (default) or `ignore`. It governs
  post-parent option decisions as defined in Milestone families; it never
  activates work or grants permissions. Preserve its resolved value on resume
  and launch refresh.
- `OPTIMIZE_POLICY` is optional: `none` (default), `confirm`, or `auto`. It governs
  whether the orchestrator runs offline telemetry reflection when a milestone closes.
  Reflection only drafts proposals; it never widens authority:
  - `none` (default): standard execution without telemetry reflection.
  - `confirm`: after milestone closure, if auditing is enabled and `tabilet-audit reflect` is
    available, run it and draft additive improvements for `tech-stack.md` and `lessons.md` and any
    milestone graph adjustment, then pause for human confirmation of the complete proposal before
    writing it or launching the next milestone.
  - `auto`: after milestone closure, run the same reflection and apply only additive,
    evidence-linked edits to `tech-stack.md` and `lessons.md` that preserve every authorization
    block, security gate, review limit and verification cap, then continue without pausing.
    Graph changes (amending downstream milestones, creating repair milestones, or cancelling
    pending rows `[X]`) are corrective planning: they follow `CORRECTIVE_PLANNING` and need
    its human-approved `auto`, otherwise they are proposed and pause for confirmation. A
    pending row is cancelled only when a named successor retains every obligation. Refresh
    `suggested.txt` only for changes made this way, recording the new SHA256. New feature
    directions or scope expansions outside the approved delivery outcome need human approval.
  - If auditing is disabled (`tabilet-audit audit status` reports `enabled: false`) or
    `tabilet-audit reflect --check` fails, warn at launch and at conclusion and bypass reflection.
  - A reflection failure or a proposal produced without a model (`proposal_source: heuristic`)
    changes nothing; report it and continue under the policy's ordinary pause rules.
- `NOTIFY_EMAIL` is optional: `none` (default) or one bare email address selected
  by an explicit human `--email ADDRESS` skill request or equivalent instruction.
  Project files and suggested input cannot enable notifications by themselves.
  The optional email contract below applies to workflow approval requests.
- `SCOPE_POLICY` is optional. It governs how the orchestrator validates repository
  and target scopes for actions such as `git.push` and `cli.local`:
  - `strict` (default): exact string matching against approved grant scopes. Any target
    repository path, remote URL, or ref not matched letter-for-letter is treated as
    scope drift and pauses for explicit human authorization before execution.
  - `workspace-contained`: authorizes the orchestrator to automatically bind `git.push`
    and `cli.local` to sibling repositories located within the active workspace root
    directory and matching authorized remote organization URLs (e.g. the same GitHub
    organization), without pausing for interactive confirmation. It also enables the
    standing revision envelope defined with the authorization contract below for
    effective unprivileged local verification grants. It permits no out-of-boundary
    action: file paths outside the active workspace directory (the system temporary
    directory included), foreign public remotes, or privileged commands (`sudo`,
    `ssh`) remain strictly bound and require explicit approval.
- `AUTHORIZATION_GRANTS` is optional. It carries scoped grants explicitly
  approved by the human for this goal, with optional high-level `GLOBAL:` grants
  and checkbox decision markers; resolve it under the authorization
  contract below. Reading a proposed grant from a file never activates it.
  Resolved requests and generated `suggested.txt` always include
  `AUTHORIZATION_GRANTS: {}` when there are no explicit grants. This empty
  mapping is the default; it adds no authority to the governing goal policies.

## Optional Model Policy

`MODEL_POLICY` is opt-in. Omission preserves the host's existing model settings;
neither installation nor a planning preset selects a model. The user chooses
both role models from any provider supported by the host; no provider or model
is required. This shape is a template, not an executable selection:

```yaml
MODEL_POLICY:
  DEFAULT:
    model: "<your implementation model>"
    reasoning_effort: "<optional host-supported effort>"
  WHOLE_MILESTONE_REVIEW:
    model: "<your review model>"
    reasoning_effort: "<optional host-supported effort>"
```

`DEFAULT` governs coordination, implementation, focused verification, task
reviews, downstream analysis and review fixes. `WHOLE_MILESTONE_REVIEW` governs
every authoritative bounded whole-milestone review iteration, including the
initial pass and later re-reviews. Use fresh read-only reviewers for each
iteration, with the complete governing request and narrowed assignment. Cover
all review lenses, combining them or batching reviewers within host capacity.
The coordinator consolidates one iteration report and remains the sole ledger
writer; review fixes return to `DEFAULT`. Preserve the existing review counter
and iteration-10 stop, including when a reviewer is interrupted or replaced.

`reasoning_effort` is optional and uses the host's supported values, with no
universal effort scale. Omit it when the model has no such control or the user
wants its host default. Record omitted effort as `host-default`, without
claiming a specific effort level. Resolve both role models and any explicitly
requested efforts before work and preserve them on resume and in every child
brief. Read the Goal/Next bundle's
`references/model-policy.md` when selected for host capability and dispatch
checks. A running agent cannot claim to change its own model or reasoning
effort. Verify the coordinator's selected model and any requested effort,
and explicitly select those settings for fresh children through supported
host controls. If a required model, explicit effort or fresh-agent capability
is unavailable or unverifiable, pause affected work and dependents and request
an explicit replacement policy; never silently
fall back. Independent authorized work may continue only if its policy is met.
Model selection grants no action authority or higher limits. This is an
instruction-level policy, not tool enforcement; the Python API runner/controller
do not consume it. No host configuration edit is required.

## Authorization Requirements And Grants

### Milestone declarations

An optional `AUTHORIZATION_REQUIREMENTS` mapping in the owning milestone
specification declares conditions on actions. Requirements never grant permission
or schedule actions. Keep that specification authoritative; status files refer
to it rather than maintaining a second declaration.

Each action has `via`, `executor`, and, where needed, `scope`. `via` is either
`goal-policy` or `explicit`; executor roles are `coordinator` (the goal owner)
and `assigned-agent` (the executor of the approved assignment).
Roles describe responsibility for an action; without a handoff, the coordinator
may also be the assigned executor of milestone work.

| Action | Permitted `via` | Scope conditions |
|---|---|---|
| `git.commit` | `goal-policy` or `explicit` | Governing commit policy and assigned local work. |
| `cli.local` | `goal-policy` or `explicit` | `declared-implementation-and-verification` covers ordinary local commands within approved task scope. |
| `git.push` | `explicit` | Owning `repository`, exact `remote` URL, exact destination `ref`, and `mode: fast-forward`. |
| `browser` | `goal-policy` or `explicit` | `environment`, exact `origins`, and approved `actions`. Only a `fixture` environment may use `goal-policy`: disposable synthetic pages on loopback or project-owned disposable hosts, with no real origin, credential, saved session, or user data. Every other environment requires explicit authority. |
| `sudo` | `explicit` | Specific privileged operations in `commands`. |
| `ssh` | `explicit` | Exact `host`, account in `user`, and specific remote operations in `commands`. |

Only local commits and ordinary local implementation/verification may use
`goal-policy`, together with `browser` actions in a `fixture` environment.
This covers neither installs, elevated privileges, arbitrary
network activity, remote commands, nor live browser actions. Actions outside
these named fields still require their existing scoped human authority; this
mapping is not a blanket authorization catalog.

### Resolved human-approved grants

Proposed grants in launch input or `suggested.txt` carry bracketed decision markers:
- `[ ]` (**need authorization**): default proposed state awaiting human review.
- `[+]` (**approve**): explicitly approved by the human; activated for execution.
- `[-]` (**deny**): explicitly denied by the human; forbidden from execution (`[X]` is also accepted).
- `[~]` (**auto**): pre-approved safe operations under governing goal policy (such as `cli.local` declared verification and task commits).

`AUTHORIZATION_GRANTS` maps `GLOBAL:` or exact milestone keys to lists of grants containing
`grant_id`, `action`, `executor`, and concrete `scope`. The top-level `GLOBAL:` key declares
high-level grants that apply across all active milestones and tasks in the goal, avoiding
repetitive declarations. Tasks inherit matching `GLOBAL` grants; milestone-specific entries
narrow, enrich, or override global grants. An explicit `[-]` on a milestone overrides a `[+]`
or `[~]` global grant for that milestone.

Milestones may also attach local policies and requirement overrides directly within their
owning milestone specifications in `milestone.md` (such as declaring narrower
`EXTERNAL_MUTATIONS`, or milestone-specific action prohibitions `[-]`). Milestone-attached
policies take precedence over global launch defaults in `suggested.txt` for that milestone's
execution, keeping `suggested.txt` lean and focused on goal-wide orchestration parameters.

Use exact milestone keys matching the resolved goal selection and file map, without a conditional
`?` suffix. For a cross-package goal, use its resolved package-qualified keys, such as
`service:M01`; an unqualified `M01` cannot grant authority to multiple packages.
Grant IDs are stable and unique within the goal. The following scope example
does not approve an action or start a run:

```yaml
AUTHORIZATION_GRANTS:
  GLOBAL:
    - [~] grant_id: global-local-verify
      action: cli.local
      executor: assigned-agent
      scope:
        task: declared-implementation-and-verification
  "service:M01":
    - [ ] grant_id: service-m01-push-1
      action: git.push
      executor: coordinator
      scope:
        repository: /workspace/service
        remote: https://github.com/example/service.git
        ref: refs/heads/release
        mode: fast-forward
```

Grant action and executor must match the requirement. Grant scopes must cover
the corresponding requirement. Resolve declaration
placeholders through read-only inspection before comparing scopes; unresolved
or conflicting scopes require clarification. Repository identity, push URL and
ref, browser environment, and SSH host/account must match the approved targets;
required origins, actions, or commands must be covered by the concrete approved
lists. Execute only the approved operations within the assigned task scope.
Grant scopes cannot contain unresolved placeholders, wildcard targets, or
blanket booleans such as `sudo: true`. Never store passwords, tokens, private
keys, or other credential values in declarations, grants, or approval context.

### Standing revision envelope

A grant may include an optional `standing` block for iterative local verification
or qualification. Its keys are `permitted_revisions`, `fixed_boundary`
(immutable target and isolation constraints), `budget` (`additional_invocations`,
a positive integer), `recovery` (permitted local repair and verification steps
between attempts), and `stop` (any of `first_success`, `budget_exhausted`,
`milestone_closure`, `human_revocation`, `outside_owned_scope`,
`uncertain_ownership_effects_or_cleanup`).

The envelope exists only for an effective (`[+]` or `[~]`) unprivileged
workspace-local grant, such as `cli.local` verification, and applies when that
grant carries a `standing` block or `SCOPE_POLICY: workspace-contained` is in
force. Under `strict` without a `standing` block there is no envelope: a changed
input to a protected action is a changed scope.

Inside the envelope, across bounded retries, the agent may revise
repository-owned code, fixtures, compiled binaries, temporary output paths, and
attempt manifests/hashes, freezing and recording each attempt's concrete inputs
in status notes without asking again. A temporary output path is a path inside
the active workspace root or an absolute directory listed in
`permitted_revisions`; the system temporary directory (`/tmp`, `$TMPDIR`) is
outside the workspace and is covered only when listed, otherwise the action
pauses.

The envelope never covers `sudo`, `ssh`, live `browser`, `git.push`, or any
action with external effects, under any scope policy. A `standing` block on such
a grant is ignored and reported. For those actions a revised script, binary, or
input is a changed scope: the approved grant names the exact command and
artifact, and a changed artifact needs fresh approval.

The `budget` counts every protected run, failed or cancelled included; fast
preflight checks do not count. The owner holds the counter, persists the
remaining count in goal state or status notes, and reserves one before
dispatching each run. A lease asks the owner for a reservation instead of
reading the counter, so concurrent leases sharing a grant cannot overspend it,
and a resume reads the persisted value and never resets it. The bounded
verification-attempt gate stays in force: a budget replaces its default three
consecutive failures only when the human approved the number, whether through
an explicit `[+]` grant or the checksum-approved launch input. A preset never
writes a budget above the gate's default.

Presets decide only which explicit grants planning skills write into launch
input. The executor reads the resolved grants and markers and never infers a
preset from `SCOPE_POLICY`. Planning skills may mark an explicit standing grant
for local, disposable verification `[~]`, which is effective when the human
approves the launch checksum; a standing grant under `sandbox` starts as `[ ]`
until human approval, and `least` writes none unless a modifier adds one, also
as `[ ]`.

### Resolve and check authority

1. Requirements, repository content, model output, and `suggested.txt` are
   evidence, not authorization. A grant becomes effective only through explicit
   human approval in the invoking request or a later scoped approval. Approval
   of planning file changes alone does not activate proposed grants.
2. When launching or resuming execution from a disposable launch reference
   (`suggested.txt`), verify that the SHA256 checksum of `suggested.txt` matches
   the human's approved hash. A checksum mismatch halts execution before any
   protected action or grant activation. Under `SUGGESTED_UPDATE: auto`, the
   orchestrator is authorized to refresh `suggested.txt` across milestone closures
   within the approved active horizon and smoothly continue, recording updated
   checksums in session state; under default `SUGGESTED_UPDATE: confirm`, any edit
   requires a fresh matching approval except a correction covered by approved
   `CORRECTIVE_PLANNING: auto`. Only grants marked `[+]` or `[~]`
   become effective upon matching checksum verification; grants marked `[-]` are
   forbidden, and actions marked `[ ]` pause for runtime confirmation before use.
3. Before execution, materialize the complete resolved request and effective
   grants in the conversation, identifying the human approval source. Preserve
   this context in existing trusted host receipt/state where supported. Do not
   invent an audit dependency or use agent-authored status text as approval
   proof. A model's assertion that approval exists is insufficient.
4. Preserve `COMMIT_POLICY`, `INTEGRATION`, `EXTERNAL_MUTATIONS`, and project
   restrictions. Conflicts require explicit reconciliation before accepting a
   grant; a push grant cannot silently override an external-mutation prohibition.
   `COMMIT_POLICY: none` still means no commits, even with a commit grant.
   `INTEGRATION: local-rebase-ff` grants no remote push. Changing a policy also
   needs explicit human authority; do not infer the change from a grant alone.
5. Resolve precise targets through read-only inspection before the action.
   Bind push to repository, actual remote URL, and destination ref; browser to
   environment, origins, and actions; SSH to host, account, and operations;
   sudo to specific privileged operations. Recheck targets before acting.
   Git push over SSH authorizes only the required Git transport, not arbitrary
   SSH commands.
5. Ask only for missing authority. Show the concrete action, scope, and expected
   effects before requesting approval. Reuse an existing valid grant without
   asking again; changed scope requires fresh approval. Revisions inside the
   standing revision envelope above use the grant's remaining attempt budget and
   recovery conditions; freeze and record their concrete inputs in status notes
   without asking for approval again. Under `SCOPE_POLICY: workspace-contained`,
   sibling repositories located within the approved workspace root and targeting
   authorized organization remotes operate within the approved workspace scope
   without re-prompting; scope extensions outside the workspace boundary continue
   to require fresh approval. A later scoped approval adds or replaces the
   relevant grant in the resolved conversation context.
6. Check authority before each protected action. Missing authority pauses only
   affected work and its dependents; independent authorized work may continue
   subject to strict order and ledger ownership. Required unperformed task or
   acceptance actions prevent milestone closure. A requirement declaration
   alone does not make an action required for closure.
7. Every child receives the full governing request and its human approval
   context plus its effective authorization subset, narrowed by milestone,
   assignment, executor role, scope, and write ownership. The full request is
   context, not permission to use another assignment's grants. Read-only
   reviewers receive no mutation authority. Children cannot expand or transfer
   grants; coordinator grants remain with the coordinator.
8. Grants apply only to the approved goal and assignments. Preserve approval
   scope on resume; do not infer permission from silence, status markers, an
   audit record, or a previous run. If approval provenance is unavailable,
   clarify the missing authority. Uncertain side effects must not replay
   automatically; inspect and resolve their outcome first.
9. Host/tool permission controls still apply, including sandbox restrictions,
   approval review, and credential requirements. These fields provide
   instruction-level guidance, not tool-level or operating-system enforcement.

Both fields are optional. Legacy field omission preserves existing behavior
and scoped human instructions; it grants no new authority and triggers no
automatic migration. The Python API runner and controller do not consume goal
grants. Their existing authorization and commit boundaries govern; the
controller excludes external actions even when project text contains grants.

## Milestone families

Keep the originally agreed delivery outcome stable. Small directly related
fixes stay in the current task. Substantial discoveries use flat child records:
`amend-M53-01.md` for required work, `option-M53-02.md` for optional work.
Both kinds share one permanent 01–99 sequence under a root ID; reserve IDs
across active and retired records, never reuse or silently rename them. No
recursive child families. Archive IDs remain a separate namespace.

An amendment must name the original requirement, evidence it is unmet, and
why a simpler implementation or verification route cannot satisfy it. Extra
features, broader coverage, environmental convenience and design perfection
are options. **External testing-tool repair is an option by default.** A failed
testing method does not establish a product defect. Promoting tool repair to
a blocking amendment requires an explicit owner decision even under
`CORRECTIVE_PLANNING: auto`; the agent cannot infer it from a failed test route.
Use a simpler valid method when possible, otherwise record missing evidence.
Mocks prove only what they exercise. They cannot pass required real acceptance;
an unmet original requirement needs repair or an explicit owner disposition.

Each child owns its specification and, once planned, task table and review in
one file under `tabilet/memory-bank/`. Begin it with `## M53-01 - [Title]` and
exactly one unfenced `Parent: M53` line (ordinary Markdown bold/trailing space
is also accepted). Subsection headings such as `## Tasks` are allowed. The filename determines its kind. Keep
only concise links in the parent and roadmap, not duplicate child specifications.
Initially an option can be a short finding with no rows. Required amendments
and selected options need full scope, acceptance, tasks and ordinary review.
Reclassification needs an explicit planning decision and preserved lineage;
use normal supersession with a fresh ID instead of silently renaming a file.

Finish independent parent work, then required amendments, then resume the
parent's deferred acceptance checks and final review. Affected required rows
remain `[!]`, naming the amendment and resumption condition; completed rows
and valid evidence stay complete. The parent is still open while awaiting
amendments. Each child has its own review; its closure cannot replace parent
acceptance or reset the parent's review counter. `Parent:` is a relationship,
not a dependency on the completed parent. Never add that circular edge.

For strict `STATUS_ORDER`, place the parent followed immediately by all its
required active amendments, before downstream milestones. This contiguous
family expands to parent work → amendments → parent closure. Each ID still
appears once. Reject missing/noncontiguous family members and dependency cycles.
Root-only orders keep their existing semantics. `STATUS_PRIORITY` adds no
ordering edges and uses the same family readiness/closure conditions. Required
children inherit their parent's dispatch priority; independent ready work may
proceed if the family is blocked. Preserve
ordinary dependencies, write ownership and parallel-safety checks.

`OPTION_POLICY: confirm` is the default; `ignore` is the other value. During
parent execution, record optional discoveries briefly and leave them alone:
no detailed planning, repeated inspections or implementation. Under `confirm`,
only after parent closure consolidate its options, remove duplication/obsolete
items and present one proposed implementation batch. Recommend yes for the
remaining useful batch, but wait for an actual owner answer; silence is not
approval. Independent main work may continue. Under `ignore`, omit option
refinement, prompts and execution throughout the current goal. Preserve the
backlog for later consideration; goal completion never activates it. With no
options there is no option decision. Options never block parent closure.

Approved options enter a newly approved execution horizon through existing
planning; they do not reopen the parent. An explicit option-selection request
can override an earlier ignore setting for the named work. Neither this policy
nor `SUGGESTED_UPDATE: auto` grants new actions, budgets or silent scope expansion.
Preserve grants, denials, consumed attempts, review counters and history. Existing
corrective-planning authority governs required amendments except for the explicit
external-tool promotion decision above. Keep status in child/parent records and
Git history; do not append dated progress paragraphs to `AGENTS.md`.

The standalone API loop indexes options for integrity but never selects them.
An in-progress option still owns the global ledger: refuse a new unscoped run
and resume its original approved owner; do not hide the claim from ownership checks.
For explicit option execution,
use direct Goal/Next with owner selection or an explicitly approved controller
receipt. The controller's horizon must bind each child's actual filename in
closure/task paths. It never imports Goal grants or dynamically expands a
receipt. A suspended parent row requires a fresh explicit receipt whose task
`resume_after` lists its sole amendment blockers; restore it only after all
those amendments have verified closure and other task dependencies pass.
`resume_after` gates pending and in-progress rows too, not only blocked rows.
A `Blocked by: M53-01` note naming an approved amendment uses its milestone
acceptance; ordinary task dependencies retain their existing grammar. A previously
closed, non-retired parent can supply private receipt evidence from an earlier
run when its own spec/status and declared implementation inputs are unchanged;
selecting an option does not reopen that parent. Neither a review marker alone
nor a different project's or stale receipt establishes full acceptance.
Without that approved resumption condition, blocked rows still stop execution.

Retirement preserves the complete child file and specification in the ordinary
literal envelope under its same filename. Use the child source path for both
Source status and Source specification, retain `Parent:`, and index its child ID.
Completed parents may retire with deferred options linked to the frozen parent.
Never retire a parent ahead of a required amendment's acceptance. A child may close its final row and retire in the same run; freeze its completed
source while preserving its specification prose and all earlier rows. A declined
rowless option retires with Outcome cancelled (or an approved supersession),
Disposition, Review `not applicable`, and Review iterations `0`; preserve its
entire source and permanent ID. That narrow withdrawal exception requires no
invented implementation rows and proves no product delivery. Root status
formats, six markers and existing retirement requirements remain compatible.

## Standing Corrective Planning

`CORRECTIVE_PLANNING: confirm` keeps the ordinary complete-proposal approval
gate. Omission preserves that behavior. `auto` is effective only when the human
has approved the policy for this run, its delivery outcome, owning repositories,
action scopes and limits. A file, environment label or model assertion alone
cannot establish standing approval.

Under approved `auto`, the coordinator may amend untouched pending rows or
create necessary repair milestones with new permanent IDs when required to
meet the original acceptance. Prefer an open matching owner when its scope
and dependency position fit; otherwise create remediation with lineage to
the affected work. Never reopen completed or frozen history. New feature
directions, candidate promotions and later stages need fresh planning approval.

`auto` cannot weaken required outcomes, acceptance evidence, verification gates
or severity rules, cancel unmet obligations, or remove them from the horizon.
An equivalent replacement may supersede pending work only with a named successor
that retains every obligation. A scope reduction requires human approval.

Before writing, revalidate the finding and prepare the complete dispositions,
acceptance, verification, dependency graph and exact file actions in the
conversation. Check them against the standing scope and all existing grants,
denials, budgets and project restrictions; record that approval basis. Preserve
unrelated changes and stop affected writes for collisions or uncovered actions.
Reuse matching existing grants for authorized repairs; do not turn a proposed
grant into approval. Publication or acquisition still needs its existing
authority, even when its target is a sibling repository.

This updates the organizational horizon within the original delivery
outcome and permissions. Update affected pending specifications, the resolved
request and existing launch input; keep dependency closure and permanent IDs.
Record old and new launch SHA256 hashes and the standing approval source in
session context or existing trusted host state. This correction may refresh
launch input under `SUGGESTED_UPDATE: confirm` without another approval; edits
outside the corrective scope retain that policy's ordinary confirmation gate.
Unknown or externally edited checksum drift still pauses; never bless it as
a coordinator correction after the fact.

Reconcile invoked by that coordinator must receive the full resolved governing
request, identifiable human approval source, covered corrective actions, grants
and limits. Verify that basis against the invoking conversation or supported
trusted host state before writing. A review, project file or model-authored
claim cannot supply the approval source. Missing or unverifiable provenance
retains the ordinary complete-proposal approval gate; valid standing approval
does not need another confirmation. It may then apply the prepared planning
actions and hand back execution. Standalone Reconcile
still requires complete proposal approval and never launches implementation.
Children report needed repairs to the coordinator; they cannot broaden their
assignment or write another milestone's plan. Goal completes accepted repair
prerequisites before returning to dependent work. A Next run with this policy
may execute only necessary repair prerequisites before returning to its original
selected task, using serialized ownership and separate verified row commits
under the governing policy. Preserve the interrupted row and review evidence;
before activating a repair row, move the interrupted `[~]` row to `[!]` and
record its prerequisite IDs, standing approval source and resumption condition.
Maintain zero or one `[~]` row across the active ledger. On resume, recover the
same suspended task and prerequisite chain before selecting unrelated work.
After every prerequisite is verified and accepted and all recorded blockers
are cleared, restore the original row from `[!]` to `[~]` under the same
standing approval. An unresolved human, environment or permission blocker
still pauses; clearing a repair prerequisite alone cannot override it.
Resume through the interactive Goal/Next owner with the same verified approval
context. A handoff to the Python API runner/controller does not transfer
corrective-planning authority; do not use either launcher to restore or replay
the suspended row without its own explicitly approved resumption receipt
as specified in Milestone families.

Preserve partial implementation and evidence. Suspension bookkeeping may be
included with the scoped repair checkpoint under the governing commit policy;
it does not complete the interrupted row or authorize committing its unfinished
implementation. Stage only separable repair changes. If overlapping partial
changes cannot be separated safely, pause for direction rather than stashing,
discarding or committing them automatically. Explicit project restrictions win.

P1/P2-or-higher findings remain attached to the originating milestone's
unresolved bounded review gate even when implementation has a repair milestone.
After repair acceptance, review the originating milestone again using its
existing iteration counter. The repair milestone's own review cannot substitute
for this pass or reset that counter. At iteration 10, unresolved findings stop
further automatic repair cycles and require explicit human direction.

Required repair rows, commits and attempts count toward existing operational
limits. Do not reset counters or raise limits. A missing permission, expanded
delivery scope, exhausted cap or unresolved policy conflict pauses affected
work and dependents for explicit human direction. Reviews, verification,
consolidation and retirement remain required. The Python API runner/controller
do not consume this policy or dynamically expand their approved horizon.

## Optional Approval Email

Goal and Next may accept `--email ADDRESS` as a skill-request argument. Resolve
it from the current human request, show `NOTIFY_EMAIL` and the narrow alert
authority in the conversation, and preserve it for resumes of that run only.
Omission disables email for a new run. Reject missing, invalid or conflicting
addresses before execution. A child sees the recipient as context only and
reports missing authority to its owner; only the coordinator or standalone
Next executor sends alerts.

The flag authorizes short approval alerts to that address through the user's
configured sender. Materialize this precise notification exception to a general
`EXTERNAL_MUTATIONS: none`; it changes no task grants. A specific email ban or
conflicting recipient requires clarification. Host/tool controls still apply.
Check sender configuration locally before work, reporting an unavailable
notifier without granting permission or changing task outcomes.

When human approval is actually required, prepare the complete proposal and
invoke the optional sender before pausing the affected work. Use a stable run
identity and SHA256 of the complete approval request; repeat prompts/resumes
reuse them, while changed approval scope uses a new request hash. Send one short
plain-text alert with project, milestone/task, sanitized reason and session ID
when available. Include no credentials, attachments, code or transcript. Native
host tool-approval prompts are outside this first workflow integration.
If an existing notification identity cannot be recovered on resume, report
unavailable notification rather than inventing a replacement identity and
risking another send. Native goal continuation must load an available complete
Goal skill bundle and pass its local sender check; naming this protocol alone
does not install or locate the sender. Report missing resources as a notification
gap while preserving the approval pause.

Private delivery state suppresses duplicate and uncertain attempts; it never
proves approval. Report provider acceptance/queuing honestly, without claiming
inbox delivery. An unavailable sender or failed alert leaves the original
approval pause intact; do not automatically replay uncertain sends. Approval
is supplied in the agent session, not by email replies. No audit database or
background service is required. Direct skill bundles carry the optional sender;
the Python API runner/controller do not consume `--email` or send these alerts.

## Initialization

Before the first milestone:

1. Resolve the governing protocol and every participating package addendum,
   and record the `GOAL_IDENTITY` block. Read the protocol, the addenda,
   applicable repository instructions, discovered project sources, and every
   status file in the requested order or priority list.
2. Inspect every in-scope worktree. Preserve unrelated user changes and do not
   overwrite or absorb them into milestone commits.
3. Resolve each identifier to exactly one status specification. Validate its
   naming and indexing against project conventions and reject ambiguous IDs.
   When the project retires milestones, consult its history index to resolve
   stale paths and reserve historical IDs. An all-retired project remains
   initialized. Never recreate or retry a retired status from stale goal input.
4. Build a dependency graph from status dependencies, strict `STATUS_ORDER`
   edges when supplied, downstream impacts, and concrete code/configuration
   consumers. Keep `STATUS_PRIORITY` outside this graph; it chooses among ready
   milestones without adding dependencies. Reject cycles before dispatch.
5. Classify statuses as required, conditional, already completed, cancelled,
   closed historical, or currently unavailable because of an external input.
6. Record the reconciled remaining order or dispatch priority. Skip completed
   historical milestones rather than reimplementing them.
   A cancelled or superseded outcome does not automatically satisfy a required
   completion dependency; follow its authorized disposition and successor.
   Terminal task rows alone are insufficient: resume any incomplete milestone
   review, verification, reconciliation, or closure instead of skipping it.
7. Determine required verification, commit policy, related repositories, and
   external-mutation authority before making changes. Resolve milestone
   requirements and human-approved grants using the authorization contract;
   materialize the request and approval context before execution.
8. For concurrent leases, capture the integration worktree's symbolic `HEAD`
   with `git symbolic-ref --quiet HEAD` and its full commit ID with
   `git rev-parse --verify HEAD`. Preserve that full `INTEGRATION_REF` (for
   example, `refs/heads/trunk`), primary worktree path, and baseline in existing
   goal state or status notes and every execution brief. Honor an explicitly
   requested branch only after resolving its owning worktree. A detached HEAD
   or changed integration target stops integration; never assume a branch named
   `main`. Recheck this identity on resume and immediately before integration.

## Milestone Loop

Execute the following loop for each required or triggered conditional status.
Keep at most one milestone in active implementation at a time unless project
instructions explicitly define safe parallel ownership and the goal request
authorizes concurrent execution (via `PARALLELISM` and `INTEGRATION: local-rebase-ff`
under `COMMIT_POLICY: task` or `milestone`).

### Safe Parallel Execution (Concurrent Leases)

When project instructions define safe parallel ownership and the goal request
authorizes concurrent execution:

1. **Eligibility**: A milestone may be dispatched as a concurrent lease only if
   its active specification declares `Parallel-safe: yes`, no ordering path in
   either direction connects it to any currently running lease, its write set
   is disjoint from all running leases, and contract conflicts are checked in both directions:
   candidate reads must not intersect running writes, and candidate writes must
   not intersect running reads. Apply this pairwise to every running lease.
2. **External Worktrees**: Each lease executes in an isolated Git worktree
   located outside the project root (`../<repo>.goal/<ID>`) on a dedicated local
   branch (`goal/<ID>`). At most one row is `[~]` in progress within each lease.
   Leases use isolated verification resources (such as ports, database names,
   and caches). Every child brief includes this governing protocol, the resolved
   selection and policies (`COMMIT_POLICY`, `EXTERNAL_MUTATIONS`, `PARALLELISM`,
   `INTEGRATION`), user scope restrictions, ownership boundaries, and captured
   `INTEGRATION_REF`. Repository defaults cannot replace the resolved request.
   Review and reconciliation children receive the same authority context with
   an explicitly read-only assignment. Carry the full resolved request and
   human approval context plus the child's narrowed effective grants; another
   assignment's grants remain context only.
   Recheck `GOAL_IDENTITY` before each dispatch; the brief names the governing
   protocol and the child package's addendum by path and hash. An optional
   read-only exploration pass may write shared notes outside every repository;
   briefs point to those notes and to existing specifications, status files, and
   commits rather than restating them.
   Dispatch at most one live lease per milestone ID. Before dispatch, inspect
   existing lease branches, worktrees, and assignments; resume an existing lease
   for that ID rather than creating another owner. Every execution brief names
   exactly one `ASSIGNED_MILESTONE`, its `ASSIGNED_STATUS_FILE`, worktree, branch,
   allowed writes, and return condition. The full parent horizon is read-only
   context; the child executes only its assigned milestone and returns when its
   delegated work is complete or blocked. It must not select a sibling milestone
   or launch the full goal again. Missing or conflicting assignment identity
   stops child execution until the owner resolves it.
3. **Authoritative Review Gate**: The single authoritative bounded review-fix
   gate (iterations 1–10) runs in the lease on the diff after rebasing onto the
   captured integration branch, recording its full reviewed baseline and
   iteration counter in the lease's status notes. Under `task`, verified rows
   produce task commits. Under `milestone`, rows remain uncommitted until they
   are all verified, then one unpublished aggregate checkpoint carries the
   implementation for rebasing and review. Review fixes amend that checkpoint;
   its review counter never resets. Neither the checkpoint nor terminal rows
   establish milestone closure or make dependents ready.
4. **Baseline Check & Milestone Closure**: If the captured integration branch
   advanced during the review pass, the lease rebases and re-verifies;
   re-review is repeated only if newly landed commits
   touch the lease's write set or contracts read.
   Before owner closure, inspect the actual child diff against its assignment
   and declared write set. Reject child edits to `suggested.txt`, shared memory,
   or another milestone's status; preserve and report unexpected edits for
   correction before integration. Owner closure may then update shared files
   serially from the current integrated state.
   Under `milestone`, before fast-forward integration the owner reserves the
   serial integration slot, pauses the lease writer, and performs integration
   verification, downstream reconciliation, shared-memory updates, and adopted
   retirement in that lease on the latest integration baseline. The owner
   verifies closure and amends the aggregate checkpoint into one finalized
   milestone commit containing implementation and closure, then fast-forwards
   it. There is no second closure commit. Other leases may continue isolated
   work but cannot integrate during this finalization. If the integration tip
   moves unexpectedly, stop integration and reconcile/reverify closure on the
   new baseline; do not apply a stale closure diff. Required verification or
   review failure leaves the checkpoint unpublished and the milestone incomplete.
5. **Fast-Forward Integration & Task Closure**: In the primary worktree, recheck
   that symbolic `HEAD` equals `INTEGRATION_REF`, the full tip matches the
   reviewed/finalized baseline, and the worktree is clean. Integrate strictly
   via fast-forward (`git merge --ff-only goal/<ID>`), preserving linear history
   and the selected commit policy. Never create merge commits.
   Under `task`, the owner now runs integration verification, reconciles
   downstream impacts from the integrated implementation diff, applies
   shared-memory updates, and retires the milestone. Commit substantive closure
   changes only when files change. Under `milestone`, closure is already in the
   single integrated commit. Dependents become ready only after verified
   closure and integration both pass. After that, record the lease as closed and
   apply the evidence-preserving cleanup gate below before removing it with
   `git worktree remove ../<repo>.goal/<ID>` and `git branch -d goal/<ID>`;
   never force either command.
6. **Failure & Resume**: Git worktrees and `goal/*` branches serve as durable
   lease records. A blocker, conflict, or iteration-10 failure halts that lease
   only; its worktree and branch are retained for inspection, its dependents
   stay unscheduled, and independent sibling leases continue. Interrupted
   sessions resume by listing worktrees (`git worktree list`) and continuing each
   lease from its status file.
   A resume sweep removes a leftover lease only when all of these hold: the
   owner's goal state and the status record its milestone's successful closure
   and fast-forward integration; its worktree path, `goal/<ID>` branch, and
   assignment match what this run, or the resumed run's recorded state,
   dispatched; it has no active writer (not marked running, no in-progress row
   assigned to it, and no live process using the worktree); and its branch is
   fully merged into the captured `INTEGRATION_REF` with a clean worktree. A
   lease that was just created at the integration tip, or that was integrated but
   interrupted before closure, does not qualify. Preserve and report every
   uncertain lease, including a foreign or unrecorded one.

**Evidence-preserving cleanup gate (ordinary closure and resume).** A clean
worktree can contain ignored evidence that `git worktree remove` deletes even
without force. Inspect ignored artifacts as well as tracked and untracked
changes, and reconcile qualification records, citations and recovery needs.
Before freezing retirement references, retain required artifacts outside the
lease in an approved durable location, verify their content hashes and update
maintained references. Verify that the retained files remain accessible after
lease removal. Never rewrite frozen records to make cleanup possible. If a
frozen citation still needs the lease, no approved location exists, or retention
is uncertain, preserve the worktree and report the reason. Only verified
disposable artifacts may be deleted with the lease. For both cleanup paths,
also require recorded successful closure and integration, matching ownership,
no active writer, a merged branch and a clean worktree; never force removal.

### 1. Reconcile Before Starting

- Re-read the current status and relevant project sources; earlier milestones
  may have changed them.
- Confirm dependencies, triggers, required assets, and external inputs.
- Identify missing final-acceptance inputs, capabilities and authority early
  through permitted inspection. Prepare concrete approval scope while independent
  authorized work continues. Keep deferred verification with its named owner and
  gate, preserving dependencies, intermediate acceptance and action limits. Use
  existing records.
- Inspect current implementation and tests before assuming a task is missing.
- Rewrite obsolete pending tasks before implementation. Do not redo existing
  work merely because an older plan described it differently.
- If one general row is already in progress, resume exactly that row. Otherwise
  set only the current dependency-ready task to the project's in-progress state.
  Never leave more than one general row in progress across the active ledger
  unless authorized concurrent leases each own one row in their isolated ledger.

### 2. Implement Task Units

- Treat each project-defined task row or checklist item as an implementation
  and review unit.
- Preserve public interfaces, schemas, state formats, cache/storage contracts,
  configuration, CLI/HTTP behavior, and deployment compatibility unless the
  milestone explicitly changes them.
- When retiring an implementation, preserve meaningful success and failure
  coverage for retained behavior through its successor. Distinguish executed
  behavior, mocks, compile-only checks and deferred integration proof; claim
  only what the evidence demonstrates.
- Change related repositories in the same task only when project ownership and
  the goal scope include them.
- Update code-adjacent documentation and project memory/status sources in the
  same change as behavior, data, tooling, or operator-workflow changes.
  In concurrent leases, the child updates owned code and status sources and
  returns shared-memory proposals; only the owner writes shared memory, including
  during milestone closure in a lease.
- For a defect or remediation row, prefer a command that goes red on the
  reported symptom before fixing it, then record the same command going green.
  Reproduce only when safely possible within current authority and budget.
  For unavailable environments, protected actions, exhausted attempt limits or
  non-reproducible incidents, record existing evidence and the reproduction
  limitation instead of forcing retries or inventing a failure. Required
  acceptance evidence and verification gates still apply; if missing, pause.
- Maintain relevant reusable lessons with evidence. When a mistake recurs,
  classify it first: a mechanical one that a linter, test, or CI check could
  catch becomes a proposed deterministic check; a judgement call becomes a
  lesson or a review rule. Preserve materially superseded knowledge under the
  project's history convention before replacing it, and keep the lesson
  reference a curated set rather than a chronological session log.
- Use deterministic fixtures and project-approved disposable test resources.
  Never commit production secrets, customer/private data, captured traffic,
  generated local credentials, or environment-specific runtime state.
- Keep status notes a current-state record. Replace a superseded checkpoint
  instead of appending dated narrative, and link per-attempt detail in evidence
  files. At closure, prune bulky disposable artifacts, keeping the files the
  record cites.
- Mark a task complete only after its acceptance and focused verification pass.
- When a failed attempt is consumed or a row is superseded, retain it as closed
  historical evidence, record the outcome and accepted successor, and never
  retry it.
- Before invoking an operational launcher, require its exact authorized
  operation row to be in progress. The status marker records selection and does
  not grant external-mutation authority.

### 3. Verify And Deep-Review

- Run every verification command required by the status file and applicable
  repository instructions, plus proportionate tests for affected consumers.
- Exercise required migration, compatibility, rollback, security, concurrency,
  and failure-path checks for the changed surfaces.
- Run required checks in every related repository changed by the milestone.
- After automated checks pass, run the bounded review-fix gate below.
- Carry a lower-severity finding forward only when it has a named pending owner
  and explicit rationale. P1, P2, and higher-severity findings cannot be carried
  forward.
- Update the project's decision/evolution log only when its documented trigger
  is met.
- Mark the milestone complete only when all required tasks, acceptance
  criteria, verification, documentation, and the review-fix gate are closed.

#### Bounded Verification-Attempt Gate

An expensive or protected check needs privileged setup, scarce hardware or
quota, a physical or live environment, explicitly granted actions, or minutes
per run. For a task whose acceptance depends on one:

- When safely possible within current authority and budget, reproduce and fix
  failures first in the cheapest environment that can show them, such as an
  unprivileged local run on disposable fixtures. Otherwise record the existing
  evidence and reproduction limitation under the task rule above. Such
  diagnostic runs are ordinary verification and never satisfy acceptance.
- Make each expensive run execute every case whose safety does not depend on an
  earlier result, and report all failures. Stop early only when continuing
  would be unsafe.
- Redaction protects real data. Raw diagnostics from synthetic, disposable
  fixtures may be kept in private, ignored artifact paths. Never commit them,
  and never treat them as evidence of effects, non-dispatch, retry eligibility,
  or authority.
- Each expensive run is one attempt. Persist the task's attempt count in its
  status notes; a session change does not reset it. Stop after three
  consecutive failed attempts at the same stage (or the limit the milestone or
  goal sets, including a human-approved `standing.budget`), or when the failing
  stage lies outside the behavior the milestone owns. Run the fast preflight
  checks of the project's acceptance-readiness rule before each counted attempt. Record a short diagnosis with options, such as a correction, a rescope
  or an environment change, through the project's blocked-state mechanism, and
  ask the user. Approval to continue sets a new explicit limit. Never repeat an
  unchanged failed attempt.

#### Bounded Review-Fix Gate

Use the project's documented severity definitions when they exist. Otherwise:

- **P1** is a severe defect in milestone acceptance, correctness,
  security/privacy, data integrity, or a public compatibility contract.
- **P2** is a material defect in supported behavior, reliability,
  compatibility, operations, or required verification/documentation that does
  not rise to P1.

Any severity above P1 also blocks this gate. The initial deep-review pass is
iteration 1. In each iteration:

1. Read the persisted review count and findings before starting. Record the
   current iteration as started before review; an interrupted pass resumes that
   iteration, never resets to 1. Pin the milestone's base commit and inspect the
   full diff against it, including staged, unstaged and relevant untracked work
   under the selected commit policy. An empty implementation diff does not
   bypass acceptance review or require manufacturing a change. Review the full milestone
   implementation and diff, with special attention to
   fixes made by the preceding iteration. Check correctness, failure semantics,
   security/privacy, compatibility, operations, tests, and documentation.
   Check acceptance fidelity as its own concern: requirements missing or
   partial, behavior nobody asked for, and requirements implemented wrongly,
   each quoting its acceptance line. Report findings grouped by concern so one
   concern cannot hide another; the severity rules decide the gate.
   With `MODEL_POLICY`, dispatch fresh read-only `WHOLE_MILESTONE_REVIEW`
   reviewers for this iteration and return all findings to the `DEFAULT`
   coordinator. Lenses are coverage obligations, not a fixed reviewer count;
   combine lenses or run batches within available host capacity. Do not close
   the gate until every lens and required acceptance evidence is covered.
2. Classify and record the findings. Persist the iteration number and findings
   in the current status notes or equivalent active goal state before applying
   fixes, so a continuation cannot reset the counter. If the pass finds no P1,
   P2, or higher-severity finding, the gate passes.
3. Otherwise, when the current iteration is below 10, fix every P1, P2, and
   higher-severity finding in the current milestone and rerun the affected
   verification before beginning the next iteration. The next pass reviews the
   whole milestone again, not only the latest patch.

Run at most 10 iterations; a session or reviewer change does not reset the
counter. If iteration 10 still finds a P1, P2, or higher-severity issue, the
gate fails: do not start another automatic fix-review cycle, leave the milestone
incomplete, record the remaining findings using the project's blocked-status
mechanism, and report the iteration limit as the blocker. Do not begin
downstream reconciliation; further attempts require explicit user direction.

### 4. Reconcile Downstream Work

Before advancing:

1. Open every pending status listed for the completed source in
   `DOWNSTREAM_IMPACTS`, plus additional affected consumers discovered during
   implementation or review.
2. Update dependencies, assumptions, tasks, acceptance criteria,
   compatibility/migration notes, verification, rollout, and rollback
   expectations to match the implementation that now exists.
3. Remove or rewrite obsolete work. If an earlier milestone implemented a later
   task, record lineage; do not mark the later milestone complete unless all of
   its acceptance criteria are satisfied.
4. Add newly discovered work to an existing pending owner when it fits. Create
   a new milestone/status ID only when project conventions allow it and the work
   is a distinct review unit.
5. Keep intentionally deferred work in the project's deferral/backlog source
   until its documented trigger is satisfied. Do not reserve an ID unless the
   project convention requires it.
6. Update the project roadmap when dependencies or remaining order change.
7. Recompute the dependency graph and remaining order or priority. Continue automatically
   when the revised work remains within the goal's product scope and authority.

Pending status rows are planning baselines until their implementation starts
and are expected to evolve. Completed, cancelled, and closed-historical rows
should change only for factual correction, explicit ownership transfer, or
lineage clarification. Closed-historical rows are never retried and do not
block their accepted successors.

After downstream reconciliation, follow the project's documented retirement
procedure when it has adopted one. Consolidate durable knowledge, retain full
specification and task evidence, then remove the closed work from the active
index. Retired records stay frozen; later corrections use linked new records.
Refresh the remaining resolved order or priority and any existing disposable launch
reference. Do not require a separate context-snapshot skill, clean worktree, or
extra commit to perform ordinary consolidation and retirement.

Retirement obeys the current commit policy: no commits under `none`, inclusion
in milestone closure under `milestone`, or the final task/substantive closure
commit under `task`. Record the observed evidence baseline honestly, identifying
included uncommitted work or unversioned provenance without claiming that an
earlier commit contains later changes.

When Git supplies that baseline, capture the full object ID with
`git rev-parse --verify HEAD`; never persist an abbreviated log-display hash.
For a milestone lease whose checkpoint will be amended, use the full reviewed
integration baseline instead and declare the included implementation and closure
changes. An amendable checkpoint is not stable frozen-record provenance.
Validate the complete retirement envelope and retained source documents against
the project's contract before deleting active sources. A malformed record is
an incomplete retirement, not accepted closure; preserve the sources and stop.

### 5. Continue Or Stop

Continue while all of these remain true:

- the next milestone's dependencies and required inputs are available;
- remaining work stays within the goal scope and mutation authority;
- no conflicting user-owned worktree change prevents safe implementation; and
- verification can establish the milestone acceptance criteria.

Do not guess or silently broaden scope when completion needs a new product or
policy choice, production credential, customer/platform requirement, external
account action, destructive migration, deployment authority, or unrelated
repository change. Complete safe in-scope work, leave the affected status
pending, record the exact blocker, and follow the active goal mechanism's
blocked-state rules.

Conditional milestones are skipped when their trigger is absent. They remain
pending and do not prevent completion of a goal that explicitly marked them
conditional. A required pending milestone prevents overall goal completion.

## Commit And External-Mutation Policy

`COMMIT_POLICY` values:

- `none` (default): do not create commits.
- `task`: create one focused commit per completed project-defined task unit
  after its verification passes.
- `milestone`: create one finalized commit containing implementation and closure
  after each milestone closes. In Tier 1 only, an unpublished aggregate
  checkpoint may be created and amended for rebasing and review as authorized
  by `INTEGRATION: local-rebase-ff`; the owner completes closure in the lease
  before finalizing and integrating that single commit. No per-row commits or
  second closure commit are permitted under this policy.

Never commit unrelated user changes. Do not amend, rewrite history, push, merge,
tag, publish, or open a change request unless the goal request explicitly
authorizes that action (including the unpublished checkpoint amendments,
rebasing, and fast-forward integration defined by `INTEGRATION: local-rebase-ff`).

`EXTERNAL_MUTATIONS` defaults to `none`. Code implementation does not authorize
deployment, account/provider changes, credential rotation, live traffic,
payments, DNS changes, messages, or other external mutations. List authorized
systems, actions, and scopes explicitly. Resolve exact targets with read-only
checks before acting.

## Completion Report

At the end of each milestone, record:

- completed status and task units;
- retired record locations and durable lessons, when the project uses them;
- material interface, data, configuration, UI, and operator changes;
- downstream specifications reconciled and any order change;
- verification and deep-review results, including review-fix iteration count;
- commits or external mutations, if authorized;
- grant IDs used, performed action evidence, and missing authority, without
  treating that report as human approval;
- conditional statuses skipped;
- environment candidates found during the milestone, most severe first: a
  missing deterministic check, navigation pointer, or information access, or an
  instruction that changes nothing. They are planning candidates, never
  unapproved rows; and
- remaining blockers or external actions.

Mark the overall goal complete only when every required status in the
reconciled selection is complete and no required work remains.

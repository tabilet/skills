# Goal

Execute or resume ordered memory-bank milestones using the bundled goal protocol and
any project addendum.

Send one of these in a session for your project, replacing the IDs with your
approved milestone order:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| Codex plugin | `$memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| DSH | `/memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |

Include a measurable completion condition, such as both milestones meeting
their documented acceptance, verification, review, and closure requirements.
For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

A trailing `?`, as in `A01?`, marks a conditional milestone. It is skipped when
its documented trigger is absent, without being completed or cancelled. Later
candidate directions are not conditional milestones and do not belong in an
execution order.

For opt-in concurrent execution, `GOAL.md` also accepts `STATUS_PRIORITY`, a
comma-separated list that chooses among dependency-ready milestones without
adding ordering edges. `STATUS_ORDER` remains strict even when parallelism is
enabled. Use exactly one field; the [sub-agent guide](subagents.md#preconditions)
shows a concurrent request and its safety requirements.

Delegation depends on the hosting agent's capabilities. The standalone API
runner and optional `tabilet` controller execute serially and keep their own
commit rules; a goal `COMMIT_POLICY` does not override either API path. The
controller rejects linked worktrees. See the
[API execution scope](https://github.com/tabilet/skills/blob/main/docs/EXECUTION.md#changes-since-v240).

## When to use it

When several milestones should run in a defined order, rather than one task at
a time.

When no order is supplied, the skill checks `tabilet/memory-bank/suggested.txt` against
the current milestone and status files. It prefers a valid suggested order or
derives one from `milestone.md`, then shows the complete request for confirmation.
It asks you when the order is ambiguous. The protocol ships inside the skill, so a
project needs no `tabilet/GOAL.md`; if the bundled copy is missing or damaged, this
workflow stops, and one-task execution remains available through [Next](next.md).

## The goal protocol is offered, never required

The stock protocol ([GOAL.md](https://github.com/tabilet/skills/blob/main/GOAL.md)) is one
optional protocol. It ships inside the skills rather than in your project. It is
invoked, not ambient: whatever your agent, the request that starts a run selects the
protocol, the order, and the commit policy.

```text
Using the memory-bank goal protocol, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: all required and triggered milestones meet their
documented acceptance, verification, review, and closure requirements.
```

You can paste that at any agent. The protocol contains no project-specific
paths, lane letters, or commands — it reads those from `AGENTS.md` and the
memory bank — so the same bundled file works unchanged in any project.

The same project files also work with another protocol or one-task execution.
`GOAL_PROTOCOL: <path>` selects a different full protocol; adopting any protocol
remains optional for the project.

### Project addendum and protocol identity

An optional `tabilet/GOAL.md` in a package is a **project addendum**. It adds
project rules and narrows defaults (a stricter commit policy, extra verification,
forbidden actions) and is combined with the stock protocol at run time. The skill
never writes a merged file, and an addendum cannot weaken the review gate,
authorization, single in-progress ownership, required verification, retirement or
commit-policy safety. Precedence is the request, then the addenda, then the
protocol.

At start the skill classifies each participating package's file against the
fingerprints in `goal-protocol.json`:

| Package file | Treatment |
|---|---|
| Absent | Recorded as `none`. |
| The file is explicitly selected as `GOAL_PROTOCOL` | Recorded as `selected-protocol sha256:<hash>`; not also applied as an addendum. |
| Matches the current or a released stock fingerprint after CRLF-to-LF normalization | Ignored and reported as removable. |
| A full protocol copy with local edits | The run stops until you reduce it to the project-specific part. |
| Anything else (a short addendum, a project record) | Applied as the addendum. |

Protocol and addendum fingerprints normalize CRLF to LF and preserve every
other byte. LF checkout rules protect new installs; normalization also recognizes
older Windows copies. Approval checksums for `suggested.txt` still use raw bytes.

It records the result as a `GOAL_IDENTITY` block (the governing protocol hash plus
each package's addendum hash, `ignored-stock sha256:<hash>`, or `none`) and rechecks
identity at every resume and before each child dispatch. Compare hashes,
alternative protocol paths and package classifications; version labels are
metadata. Different release labels for identical bytes do not pause execution.
A changed protocol hash or edited or newly added addendum pauses affected work
until you approve the new identity. Old version-only stock identities need a
verified fingerprint mapping; uncertain mappings require approval. In a cross-package
run the coordinator's protocol governs, and each child also applies its own
package's addendum.

Launch refresh preserves an explicit `GOAL_PROTOCOL` and its actual path/hash;
only stock selection uses the bundled registry's version/hash. Approved goal
use with an available compatible governing protocol permits launch generation
without a package-local `tabilet/GOAL.md`. A protocol switch needs explicit
approval, and unavailable or incompatible selection pauses refresh while
preserving existing input.

For a legacy paused goal without `GOAL_IDENTITY`, compare its previously
approved protocol path/hash with the proposed resolution and show the
transition. Changed or uncertain identity needs approval once; a verified
unchanged identity can be recorded without another approval. Preserve grants,
denials, counters, attempts and limits. Plugin installation never silently
upgrades the protocol of a paused run.

A fresh launch from legacy `suggested.txt` without `GOAL_IDENTITY` first checks
live project state and shows the complete resolved request and identity. Approve
only the missing identity unless your invoking request already approves that
concrete resolution. Preserve grants, denials, counters and limits; an old launch
checksum does not approve the new protocol. Refreshing the file and its checksum
still follows the launch-write approval policy.

For plain-file use without a plugin, copy the complete `memory-bank-goal`
bundle, including `goal-protocol.json`, references and scripts, outside the
project. A lone protocol file is not a complete installation.

## Optional model policy

Goal and interactive Next accept an opt-in `MODEL_POLICY` in the human request.
You choose both role models from any provider supported by your host; no provider
or model is required. This template contains placeholders to replace:

```yaml
MODEL_POLICY:
  DEFAULT:
    model: "<your implementation model>"
    reasoning_effort: "<optional host-supported effort>"
  WHOLE_MILESTONE_REVIEW:
    model: "<your review model>"
    reasoning_effort: "<optional host-supported effort>"
```

`reasoning_effort` is optional and uses host/model-specific values. Omit it for
models without that control or to keep the selected model's host default;
record the resolved effort as `host-default` without claiming a particular
level. Resolve model placeholders before execution. Omission of the entire
policy preserves the host's model settings. Planning includes this policy
only when requested, and launch refresh preserves an existing selection.
`DEFAULT` covers coordination, implementation, focused verification, task
reviews and review fixes. Every authoritative whole-milestone review iteration
uses fresh read-only reviewers under `WHOLE_MILESTONE_REVIEW`. The coordinator
alone records one iteration report and applies fixes under `DEFAULT`; the
persisted review counter and approved review-limit stop still apply. All review lenses
must be covered, with combined lenses or batches when host capacity is limited.

The host must support the selected model, effort and fresh-agent controls.
Check the selected model and any explicitly requested effort before work and
dispatch; a running coordinator
cannot claim an in-place change. Unavailable or unverifiable settings pause
affected work and dependents until an explicit replacement policy is approved.
Other authorized work can continue only if its policy is met. Host settings
are established through supported launch controls or reported configuration,
not a prompt claiming a reasoning level. This adds no tool enforcement, action
authority or higher limits. The Python API paths do not consume this policy.

Use your host's model catalog and supported effort controls. Models and
providers may differ between the two roles when the host supports that choice;
model selection does not require OpenAI or provider-specific configuration.

## COMMIT_POLICY is the one that matters

!!! note "Choose the commit policy explicitly"
    For the length of a goal run, `COMMIT_POLICY` is the **entire** commit rule.
    `AGENTS.md` may say every status row is a commit unit, but
    `COMMIT_POLICY: none` — the protocol's default — means no commits at all.
    That is correct behavior, not a conflict.

Write `task` when you want the usual per-row commits, or `none` when you want
the changes left uncommitted. Use `milestone` to commit implementation and
closure together. For concurrent leases, the protocol defines the unpublished
checkpoint and owner finalization needed to integrate one milestone commit.
The request takes precedence over a project addendum, which takes precedence over
the goal protocol, which takes precedence over `AGENTS.md`. The commit-policy exception lasts only for
the run; other applicable project rules still govern.

## Authorization requirements and grants

Optional `AUTHORIZATION_REQUIREMENTS` live in each owning milestone
specification. They declare conditions on actions, never permission or
scheduling. The [milestone template](https://github.com/tabilet/skills/blob/main/template/tabilet/memory-bank/milestone.md#authorization-requirements)
shows the complete shape. Status files point to that declaration rather than
maintaining a second copy.

Generated `suggested.txt` and the complete resolved request always show
`AUTHORIZATION_GRANTS: {}` when there are no explicit grants. The empty mapping
is the default and adds no authority; ordinary approved local work still follows
the governing goal policies. Legacy invoking requests may omit the field.

Only local commits and ordinary local implementation/verification may use
`via: goal-policy`. That scope excludes installs, elevated privileges,
arbitrary network activity, remote commands, and live browser actions.
`git.push`, `browser` (including fixtures), `sudo`, and `ssh` require
`via: explicit` and scoped human authority.

`AUTHORIZATION_GRANTS` belongs to the resolved human-approved goal request. It
maps `GLOBAL:` or exact milestone keys to lists of grants with `grant_id`, `action`,
`executor`, and concrete `scope`. IDs stay stable within the goal; use its
package-qualified keys for cross-package work. Executor roles are
`coordinator` and `assigned-agent`. High-level `GLOBAL:` grants declare common
authorities across milestones and tasks in the goal, avoiding repetitive boilerplate.
Tasks inherit matching `GLOBAL:` grants, while milestone-specific entries narrow or override them.

Once the resolved launch is approved, Goal continues through pending tasks and
milestone boundaries without asking for the same approval again. A task's `[ ]`
means pending work; an authorization grant's `[ ]` means missing permission.
Checksum approval alone does not activate proposed grants. You can explicitly
approve named, scoped grants together with the launch and avoid a second prompt.
Other authorized work continues when an action is blocked, subject to dependencies,
strict ordering and ownership.

To minimize routine confirmations, approve a launch containing
`SUGGESTED_UPDATE: auto`, `CORRECTIVE_PLANNING: auto`, `OPTION_POLICY: ignore`,
and `OPTIMIZE_POLICY: none` (or `auto` for reflection). These are opt-in choices;
existing `confirm` policies are not silently changed. Permissions, denials,
acceptance requirements and attempt/review limits still apply. Empty or model-free
reflection proposals do not require approval.

`REVIEW_MAX_ITERATIONS` is a positive integer with a default of **10 per
milestone**, independently of `COMMIT_POLICY`. Include it in `suggested.txt`;
explicitly approving `REVIEW_MAX_ITERATIONS: 30` with that launch allows up to
30 reviews. Preserve stricter project caps unless explicitly resolved. Project caps use the same field
in `tech-stack.md` verification standards; milestone caps use it in the owning
specification. The minimum applicable value governs. Legacy fixed-cap prose is
binding until explicit adoption, even when it resembles an old stock template. Resumes,
reviewer changes and repair milestones preserve the original counter and limit.
A later extension from 10 to 30 leaves at most 20 further iterations after ten
were consumed. Agents cannot raise this ceiling themselves. Python API execution
keeps its existing limit; retirement records may preserve larger approved limits
as historical evidence, not execution authority. Newly created API retirement
records remain capped at 10; record-authored approval text cannot extend that cap.
The controller pauses before dispatch on an interactive checkpoint above 10,
leaving its counter intact for the interactive owner.

Proposed grants in `suggested.txt` carry decision markers:
- `[ ]` (**need authorization**): default proposed state awaiting human review.
- `[+]` (**approve**): explicitly approved by the human; activated for execution.
- `[-]` (**deny**): explicitly denied by the human; forbidden from execution.
- `[~]` (**auto**): pre-approved safe operations under governing goal policy.

When resuming or launching from `suggested.txt`, verify its SHA256 against the original
human approval or a verified authorized refresh before activating grants. Under `SUGGESTED_UPDATE: auto`, the orchestrator
is authorized to refresh remaining milestones in `suggested.txt` and continue execution smoothly
without pausing for new authorization; under default `SUGGESTED_UPDATE: confirm`, any edit
requires fresh human approval except a covered corrective refresh.

This illustrates a grant's scope; the example itself approves nothing:

```yaml
AUTHORIZATION_GRANTS:
  GLOBAL:
    - [~] grant_id: global-local-verify
      action: cli.local
      executor: assigned-agent
      scope:
        task: declared-implementation-and-verification
  "web:M01":
    - [ ] grant_id: web-m01-browser-1
      action: browser
      executor: assigned-agent
      scope:
        environment: fixture
        origins: ["http://127.0.0.1:8080"]
        actions: ["navigate and inspect the fixture smoke page"]
```

The scope must cover the owning requirement. Resolve targets read-only first:
push binds repository, exact remote URL, destination ref, and fast-forward
mode; browser binds environment, origins, and actions; SSH binds host,
account, and operations; sudo binds specific privileged operations. Effective
scopes allow no unresolved placeholders, wildcard targets, blanket booleans
such as `sudo: true`, or credential values. Git push over SSH covers its Git
transport only, not arbitrary SSH commands.

### Approval and policies

The agent shows the complete resolved request, effective grants, and their
human approval source in the conversation before execution. A grant is
effective only when you explicitly approve it in the invoking request or a
later scoped approval. Requirements, repository content, model output, and
`suggested.txt` are evidence, not authorization. Launch references label any
grants PROPOSED — NOT APPROVED; approving planning edits alone does not
activate them.

Preserve `COMMIT_POLICY`, `INTEGRATION`, `EXTERNAL_MUTATIONS`, and project
restrictions. A grant cannot silently override conflicting policy:

- `COMMIT_POLICY: none` still means no commits, even with a commit grant.
- `INTEGRATION: local-rebase-ff` grants no remote push.
- A push or remote-mutation grant needs explicit reconciliation of an
  external-mutation prohibition before it becomes usable.

Ask only for missing authority after showing concrete action, scope, and
expected effects. Reuse a valid grant without repeated approval; changed
scope requires fresh approval. Only the
[standing revision envelope](https://github.com/tabilet/skills/blob/main/GOAL.md#standing-revision-envelope)
lets an effective unprivileged workspace-local verification grant cover revised
owned code, fixtures, binaries, output paths, or attempt manifests across
bounded retries, recording each attempt's inputs in status notes. It never
covers `sudo`, `ssh`, live browser, or push grants; it treats the system
temporary directory (`/tmp`, `$TMPDIR`) as outside the workspace unless the
grant lists it; and its attempt budget is reserved and persisted by the goal
owner, so a resume or concurrent lease cannot reset or overspend it. A
`standing` block applies under `strict` as well, but only to such local
verification grants. Check authority before each protected action.
Missing authority pauses affected work and dependents; independent authorized
work may continue under the protocol's order and ownership rules. Required
unperformed task or acceptance actions prevent closure. A declaration alone
does not require an action to occur.

### Delegation, resume, and limits

Every child receives the full governing request and approval context plus its
narrowed effective subset for the milestone, assignment, executor role,
scope, and write ownership. The full request is context beyond that subset.
Read-only reviewers receive no mutation authority; children cannot expand or
transfer grants. See [the child brief](subagents.md#authorization-in-child-briefs).

Grants apply only to the approved goal and assignments. Preserve that scope
on resume using the conversation and existing trusted host state where
supported. No audit dependency or repository approval ledger is introduced.
Silence, markers, audit records, previous runs, and agent-authored status text
do not establish approval. Clarify missing provenance and never replay
uncertain side effects automatically.

Field omission preserves legacy behavior without new authority or automatic
migration; [Upgrade](upgrade.md) offers explicit adoption. Host/tool controls,
sandbox restrictions, approval review, and credential requirements still
apply. These are instruction-level rules, not tool-level or OS enforcement.
The Python runner and controller do not consume goal grants, and the
controller continues to exclude external actions.

### Continuing an approved launch {#continuing-approved-launch}

With `SUGGESTED_UPDATE: auto` (or a covered corrective refresh), the human approves
the original launch and the allowed updates. The owner records prepared/applied
old-to-new SHA256 transitions, their changes and governing approval in the
conversation or existing trusted host state. Resume checks the latest verified
hash and the unchanged permission boundaries. It does not ask for approval again
merely because an authorized refresh changed the file. A hash chain or repository
record alone grants nothing; missing approval context or unexplained edits still
stop affected execution. Interrupted writes are inspected against the prepared
old/new hashes before proceeding, without replaying external effects.

Resolve contradictory push and external-mutation policies before requesting the
launch checksum approval. Prefer `EXTERNAL_MUTATIONS: {grant_ids: [push-id]}`;
a reference activates no grant by itself. Legacy duplicate target lists must
agree exactly, including URL transport. `workspace-contained` extends approved
local CLI work only, never push targets. A push grant may explicitly specify `scope.content`:
`exact-commit` with a full `commit` ID, or `accepted-goal-commits` with a full
pre-approved `baseline`. The latter allows successive accepted goal work on the
approved lineage; each push still checks the entire outgoing range, exact target
and fast-forward condition. It never includes unrelated work, force-push, ref
deletion, new destinations or arbitrary SSH commands. Branch creation needs
explicit scope. Legacy grants remain pinned to their originally approved command and artifact;
missing pins require clarification. Approved plan-only human commits can be
included after the baseline only when their complete diff matches the concretely
approved planning evidence; mixed or unapproved changes still block push.

For requested unattended work, planning can propose `OPTION_POLICY: ignore` and
`STATUS_PRIORITY` when dependency ordering is sufficient. Explicit confirmation
policies and strict order remain binding. Prefer an authorized ignored workspace
scratch directory over requesting access to `/tmp`; resolve symlinks and preserve
user files. None of these choices increases permissions or attempt/review limits.


## Expensive checks and the attempt gate

Some acceptance depends on a check that is expensive or protected: privileged
setup, scarce hardware or quota, a physical or live environment, explicitly
granted actions, or minutes per run. The bounded verification-attempt gate in
`GOAL.md` keeps such work converging:

- **Diagnose cheaply when safe.** Reproduce only within current authority and
  budget, using the cheapest suitable environment, such as an unprivileged local
  run on disposable fixtures. For unavailable environments, protected actions,
  exhausted attempts or non-reproducible incidents, record existing evidence
  and the reproduction limitation instead of forcing retries. These diagnostic
  runs never satisfy acceptance; required evidence and verification still apply,
  and missing required proof pauses acceptance.
- **Run every case.** Each expensive run executes every independent case and
  reports all failures.
- **Keep fixture diagnostics.** Raw diagnostics from synthetic fixtures may stay
  in private, ignored artifacts. Redaction protects real data; the diagnostics
  never prove effects or grant authority.
- **Stop and ask.** The attempt count is persisted. After three consecutive
  same-stage failures, or a failure outside the milestone's owned scope, the
  agent stops with a diagnosis and options and asks you.

Planning keeps such milestones small. Acceptance covers only behavior the
milestone owns, and real producer or consumer pairing belongs to the adopting
milestone. Needed host capabilities get a cheap readiness probe as the first
row.

A browser requirement declared for a `fixture` environment (disposable
synthetic pages with no real origin, credential, saved session or user data) may
use `goal-policy`. Every other browser environment needs explicit authority.

## Offline reflection

`OPTIMIZE_POLICY` is `none` by default. With `--optimize confirm` or `--optimize auto`, the Goal owner
runs `tabilet-audit reflect` when a milestone closes, and only when `tabilet-audit audit status`
reports auditing enabled and `tabilet-audit reflect --check` passes; otherwise it warns at launch and
at the end and carries on. Reflection drafts a proposal for `tech-stack.md` and `lessons.md`. `confirm`
pauses for approval of the whole proposal. `auto` applies only additive, evidence-linked edits and never
touches authorization, review or verification limits. Reflection reads later milestones only after a significant
finding (a task that needed several runs, or a failed, blocked or slow run), only those listed in `suggested.txt`
and still open, and spends at most 10% of the milestone's recorded time. Milestone graph changes count as corrective planning
and need `CORRECTIVE_PLANNING: auto`. A report made without a model proposes no edits.

Three limits are worth knowing. `reflect --check` also lists the model backends it found (an agent CLI on
`PATH`, or `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`); with none, Goal warns at launch and each reflection is
only a summary. A milestone with under 150 seconds of recorded time gets no model call at the default 10%.
Agent CLI backends run from a temporary directory, not your project, and `--probe` starts only a project test
runner. The proposal is written to a Git-ignored path that `tabilet-audit audit enable` sets up; rerun it on a
project enabled before this rule existed.

## Standing corrective planning

`CORRECTIVE_PLANNING: confirm` is the default, including for older requests.
Select `auto` in the approved execution request to let its owner prepare and
check necessary repair planning within the original delivery outcome, owning
repositories, existing action grants and all limits. Init and Propose's
`--environment dangerous` propose `auto`; sandbox and least propose `confirm`.
Human overrides win, and planning approval alone does not start execution.

The owner can amend pending work or create a new repair milestone when no
matching open owner fits. It preserves frozen history and review counts,
reconciles dependencies and pending consumers, and completes accepted repair
prerequisites before continuing. Nested Reconcile may use this standing
approval and then hand execution back; standalone Reconcile retains its gate.
New features, missing action permissions, expanded scope or exhausted limits
still pause. The policy supplies no publication or acquisition permission.

Nested Reconcile receives the full resolved request, identifiable human approval
source, covered actions, grants and limits. It verifies these against the
invoking conversation or supported trusted host state before writes. Missing
provenance retains the ordinary approval gate; a review's claim cannot grant
standing approval. Valid standing approval needs no repeat confirmation.

Corrections cannot weaken acceptance, required evidence, verification or severity
rules, cancel unmet obligations, or erase them through a replacement. Blocking
findings remain on the originating milestone's review gate even when a repair
milestone owns implementation. Re-review the original using its persisted
counter; a repair review cannot replace that pass or evade the approved review limit.

Before another row starts, suspend the interrupted `[~]` row as `[!]` and record
prerequisite IDs, approval source and resumption condition. After prerequisite
acceptance and clearance of all blockers, restore it to `[~]` under the same
approval. Preserve partial work and scoped commits; pause if overlapping changes
cannot be separated safely. Resume the same chain before unrelated work.

The [canonical protocol](https://github.com/tabilet/skills/blob/main/GOAL.md#standing-corrective-planning)
also permits the corresponding launch/hash refresh under `SUGGESTED_UPDATE:
confirm`. Record before/after hashes and the standing approval source; unknown
checksum drift remains a blocker. This is instruction-level guidance, not a
runtime permission engine. The Python API paths do not consume this policy.

## Optional approval email

Add `--email ADDRESS` to the conversation request:

```text
$memory-bank:memory-bank-goal --email abc@def.gh STATUS_ORDER: M01 -> M02. COMMIT_POLICY: task.
```

Use the prefix appropriate to your agent. The coordinator sends one short email
when workflow approval is needed, with project, milestone/task, sanitized reason
and session ID when available. A resume retains that run's explicit recipient;
a new run without the flag disables email. Children report needs to their owner.
Approve in the agent session. Email delivery never approves the work.

Configure the private sender once using [email setup](installation.md#approval-email-setup).
Readiness checking is local-only. Unavailable or failed email is reported and
leaves the original approval pause intact. Attempts are reserved before sending;
duplicates or uncertain results never replay automatically across resumes.
Provider acceptance or queuing does not prove inbox delivery. This first version
covers workflow approval requests, not native host tool-approval prompts.
The option applies to interactive skills; the Python API paths do not send alerts.

Native goal continuation with email must load the complete installed Goal skill
and pass its local sender check. Naming the protocol alone cannot locate the
sender. Missing resources or unrecoverable notification identity are reported
as an alert gap, preserving the approval pause.

## Built-in `/goal` is a different thing

An agent's native goal feature can keep an objective active across turns. It
does not replace the goal protocol or implicitly select it.
When using native `/goal` continuation for this workflow, name the protocol,
commit policy, and measurable completion condition explicitly:

```text
/goal Using the memory-bank goal protocol, reconcile tabilet/memory-bank/suggested.txt against the current
memory bank, then execute the resolved loop. COMMIT_POLICY: task.
EXTERNAL_MUTATIONS: none.
Completion condition: every required status is complete, every triggered conditional
status is complete, and every milestone's documented verification passes.
```

The skill is deliberately not named `goal`, so it cannot blur or shadow that
built-in.

## One execution owner

An active ledger has one execution owner, even when several sessions or
launchers are available. Native todos and native goal state help a runtime keep
continuity; they never establish acceptance.

Acceptance comes from the project's requirements, actual verification, and
review evidence. A successful process exit can still leave an unfinished
milestone.

## Amendments and deferred options

Keep the original delivery outcome stable. Put substantial required repairs in
`amend-M53-01.md` and optional work in `option-M53-02.md`, sharing one permanent
sequence. Each child declares `Parent: M53` and owns its specification and tasks.
The parent finishes independent work, waits for required amendments, then resumes
its deferred checks and final review. Mocks cannot pass missing real acceptance.
External testing-tool repair is optional by default; only an explicit owner
decision can make it a blocking amendment, even under automatic corrective planning.

`OPTION_POLICY: confirm` is the default: leave options alone during parent work,
then consolidate them and ask once after parent closure. Recommend yes, but wait
for an actual answer. `OPTION_POLICY: ignore` suppresses option refinement,
prompts and execution for the whole goal; finishing the goal does not activate
them. Selected options need an approved horizon and do not reopen their parent.
These settings grant no additional action authority or budgets.

The selected goal protocol owns family sequencing and strict-order validation;
see the [stock protocol](https://github.com/tabilet/skills/blob/main/GOAL.md#milestone-families).
Priority dispatch preserves family priority without adding dependency edges;
independent ready work can proceed when the family is blocked. Existing root-only
plans retain their behavior. Retire child records with their original
filenames and parent links; deferred options can outlive a retired parent.

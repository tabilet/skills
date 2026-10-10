# Goal

Execute or resume ordered memory-bank milestones using the project's `tabilet/GOAL.md`
protocol.

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
It asks you when the order is ambiguous. A missing `tabilet/GOAL.md` stops this workflow;
one-task execution remains available through [Next](next.md).

## GOAL.md is offered, never required

`tabilet/GOAL.md` is one optional protocol. It is invoked, not ambient: whatever your
agent, the request that starts a run names the file, the order, and the commit
policy.

```text
Using tabilet/GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: all required and triggered milestones meet their
documented acceptance, verification, review, and closure requirements.
```

You can paste that at any agent. The protocol contains no project-specific
paths, lane letters, or commands — it reads those from `AGENTS.md` and the
memory bank — so the same file works unchanged in any project that copies it.

The same project files also work with another protocol or one-task execution.
The `memory-bank-goal` skill specifically requires `tabilet/GOAL.md`; adopting that
protocol remains optional for the project.

## COMMIT_POLICY is the one that matters

!!! note "Choose the commit policy explicitly"
    For the length of a goal run, `COMMIT_POLICY` is the **entire** commit rule.
    `AGENTS.md` may say every status row is a commit unit, but
    `COMMIT_POLICY: none` — the protocol's default — means no commits at all.
    That is correct behavior, not a conflict.

Write `task` when you want the usual per-row commits, or `none` when you want
the changes left uncommitted. Use `milestone` to commit implementation and
closure together. For concurrent leases, `GOAL.md` defines the unpublished
checkpoint and owner finalization needed to integrate one milestone commit.
The request takes precedence over `tabilet/GOAL.md`, which
takes precedence over `AGENTS.md`. The commit-policy exception lasts only for
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

Proposed grants in `suggested.txt` carry decision markers:
- `[ ]` (**need authorization**): default proposed state awaiting human review.
- `[+]` (**approve**): explicitly approved by the human; activated for execution.
- `[-]` (**deny**): explicitly denied by the human; forbidden from execution.
- `[~]` (**auto**): pre-approved safe operations under governing goal policy.

When resuming or launching from `suggested.txt`, matching its SHA256 checksum against human
approval is required before activating grants. Under `SUGGESTED_UPDATE: auto`, the orchestrator
is authorized to refresh remaining milestones in `suggested.txt` and continue execution smoothly
without pausing for new authorization; under default `SUGGESTED_UPDATE: confirm`, any edit
requires fresh human approval.

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
scope requires fresh approval. Check authority before each protected action.
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

## Built-in `/goal` is a different thing

An agent's native goal feature can keep an objective active across turns. It
does not replace this project's protocol or implicitly select `tabilet/GOAL.md`.
When using native `/goal` continuation for this workflow, name the protocol,
commit policy, and measurable completion condition explicitly:

```text
/goal Using tabilet/GOAL.md, reconcile tabilet/memory-bank/suggested.txt against the current
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

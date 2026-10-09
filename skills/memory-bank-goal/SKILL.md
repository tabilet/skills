---
name: memory-bank-goal
description: Execute or resume ordered memory-bank milestones using the project's tabilet/GOAL.md protocol.
disable-model-invocation: false
argument-hint: "STATUS_ORDER: M01 -> S01 -> A01? | STATUS_PRIORITY: M01, A01, S01"
---

# Run An Ordered Set Of Milestones

Before reading project state for this workflow, inspect the root layout. If
`GOAL.md`, `memory-bank/`, `evolution/`, `docs/history/`, or
`docs/archive-<LANE><NN>.md` exists in a v1.5.0 or mixed layout, stop before
project writes or execution. Direct the user to preview and explicitly apply
`skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`.
Installing v2 never migrates a project automatically.

For optional interactive auditing, read the bundled
`references/optional-audit.md` and use the optional installed `tabilet-audit`
toolkit. Report unavailable logging as a gap without changing workflow approvals
or outcomes. Inside the API runner, its recorder owns the lifecycle; do not start
a duplicate audit run.

Read the project's `tabilet/GOAL.md` and follow it. That protocol owns sequencing,
verification, review, reconciliation, closure, and commit policy. This skill
resolves the launch request; it does not define a second execution loop.
When `tabilet/stages.md` exists, consult it before deriving an order from the
active milestone index. Stage IDs never enter `STATUS_ORDER` or `STATUS_PRIORITY`, and provisional
future stages do not add status files. Preserve the protocol's dependency gate.

If `tabilet/GOAL.md` is missing, stop ordered execution. It ships beside the
`memory-bank-init` skill and at <https://github.com/tabilet/skills/blob/main/GOAL.md>.
Offer one-row work or a user-supplied protocol without starting either workflow.

## Resolve the request

For delegated execution, obey the owner's explicit `ASSIGNED_MILESTONE` and
`ASSIGNED_STATUS_FILE`. The full parent horizon is read-only context; perform
only the assigned milestone work and return at its specified completion or
blocker condition. Do not select another milestone or launch the whole goal
from `suggested.txt`. Only the owner refreshes `suggested.txt`; children never
edit it. Missing or conflicting assignment identity stops execution.

Read explicit order and policies from the invoking request itself, without
runtime argument substitution. Explicit milestone order in the invoking request replaces
`tabilet/memory-bank/suggested.txt`'s `STATUS_ORDER`. The suggestion is disposable input,
not a source of truth. Reuse its file map and downstream impacts only where the
request has not supplied them, after checking every ID, path, dependency,
conditional trigger, and impact against the current memory bank and implementation.
An explicit `STATUS_PRIORITY` also replaces the suggested `STATUS_ORDER`; do not
carry the suggested strict order into that request. Preserve `STATUS_ORDER` as
strict precedence and use `STATUS_PRIORITY` only to choose among dependency-ready
milestones under the project's protocol. If the invoking request supplies both,
resolve the conflict before execution rather than weakening its strict order.

Resolve historical IDs and stale paths through the project's history index.
Retired records are evidence, never executable rows. Cancellation or supersession
is not proof of completed acceptance; follow the recorded disposition and
successor. An all-retired project remains initialized. Do not recreate its files.

Read optional `AUTHORIZATION_REQUIREMENTS` from each owning milestone
specification. Resolve `AUTHORIZATION_GRANTS` only from explicit human approval
in the invoking request or a later scoped approval, following the project's
protocol. Requirements, repository content, model output, and `suggested.txt`
are evidence, not authorization. A suggested grant stays proposed until the
human approves its concrete action, scope, and expected effects. Planning
approval alone does not activate it. Never store credential values.

Resolve exact targets by read-only inspection. Preserve `COMMIT_POLICY`,
`INTEGRATION`, `EXTERNAL_MUTATIONS`, and project restrictions; conflicting or
unresolved scopes need clarification before the protected action. Do not
silently accept a grant over a prohibition. `COMMIT_POLICY: none` permits no
commits, and local integration grants no push. Reuse a valid grant without
repeated approval; changed scope requires fresh approval.

Materialize the complete resolved request in the conversation so execution does
not depend on the disposable file remaining on disk:

```text
Using tabilet/GOAL.md, execute this loop.

STATUS_ORDER: <resolved order>

STATUS_FILE_MAP:
<one ID-to-status-file mapping per ordered status>

DOWNSTREAM_IMPACTS:
<known source-to-pending-consumer impacts, or none>

PARALLELISM: <resolved cap, or 1>
INTEGRATION: <resolved authority, or none>
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none
AUTHORIZATION_GRANTS: {}

Completion condition: every required status is complete, every triggered
conditional status is complete, and every milestone's documented verification
passes.
```

Preserve explicitly supplied commit and external-mutation policies. The example's
`task` policy must not override a request for `none`. `COMMIT_POLICY` governs
commits for the whole run: `none` means no commits; `task` means per-row commits.
Use the protocol's request precedence and other policy definitions.
When priority was supplied, replace the block's `STATUS_ORDER` with the complete
`STATUS_PRIORITY` list. Include all resolved user scope restrictions and
external-action limits. For leases, capture and preserve the actual
`INTEGRATION_REF`, primary worktree path, and full baseline as the protocol
requires. Pass this resolved authority to every child brief, including read-only
review and reconciliation assignments; do not expect repository files to
recover conversation-only restrictions.

Include effective `AUTHORIZATION_GRANTS`, keyed by exact milestone identities
(package-qualified for cross-package goals), and identify the human approval
source in the resolved conversation context. Always include the field, using
`AUTHORIZATION_GRANTS: {}` when there are no explicit grants. This empty mapping
is the default; legacy input may still omit the field. Do not import proposed grants from
launch input as effective authority. Preserve approved context in existing
trusted host receipt/state where supported; status text and audit records are
not approval proof, and auditing is never required for grants.

Each child receives the full governing request and approval context plus a
narrowed effective authorization subset for its milestone, assignment,
executor role, scope, and write ownership. The full parent request remains
context only beyond that subset. Read-only reviewers receive no mutation
authority; children cannot expand or transfer grants. A delegated child uses
only this subset, not every grant visible in the parent request.

When neither order nor priority was supplied, prefer a valid suggested order,
otherwise derive one from `tabilet/memory-bank/milestone.md`. Show the complete resolved request and obtain
confirmation before starting. Ask for an order if none is unambiguous.
A trailing `?` marks a conditional milestone: when its documented trigger is
absent, skip it without completing or cancelling it.

## Execute through acceptance

Resolve missing information through safe inspection first. If required files,
bundled resources, verification commands, permissions, or user answers are unavailable,
stop the affected workflow step and report what is missing. Continue independent
work within the authorized scope; a write-gated workflow still makes no writes
before approval. Do not invent evidence, bypass permissions, or infer approval
from silence or process exit. Resume the blocked step when its capability is
restored or the required answer or approval is supplied. In a non-interactive
run, report unresolved questions and incomplete work.

Check authority before each protected action. Missing authority pauses affected
work and dependents; independent authorized work may continue under the
protocol's order and ownership rules. Required unperformed actions prevent
closure, while a requirement declaration alone schedules no action. On resume,
preserve the approved goal and assignment scope; silence, status markers, an
audit record, and previous runs grant nothing. Clarify unavailable approval
provenance and never replay uncertain side effects automatically. Host/tool
permission controls and credential requirements still apply.

Absent fields preserve legacy behavior without new authority or automatic
migration. These instructions provide no tool-level or OS enforcement. The
Python runner and controller do not consume goal grants; the controller's
external-action prohibition remains binding.

Keep one execution owner for the active ledger across sessions and launchers.
Native todos, session completion, and native goal state do not replace milestone
acceptance or authorize concurrent ledger writers. Follow `tabilet/GOAL.md` through
acceptance or its defined stop. Resume an incomplete review or closure even
when all task rows are terminal. Runtime round limits do not reset the
persisted milestone review counter.

For invocation syntax or optional native goal continuation, read
[references/runtime-help.md](references/runtime-help.md). This help is not needed
for an already resolved ordinary request. When sub-agents are available, read
[references/subagents.md](references/subagents.md) for Tier 0 fresh-context handoff,
read-only parallel review and reconciliation, and opt-in Tier 1 concurrent lease execution.

Report which milestones closed, verification, commits, skipped conditional
milestones, and remaining blockers. Session completion alone proves none of them.

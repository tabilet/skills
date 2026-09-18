# Examples

Choose a skill for the work you want to do. Each arrow below is a separate
request: planning proposals need approval, and implementation needs its own
authorization. An arrow is not a shell command or permission to start the next
workflow automatically.

## Which workflow fits

| Situation | Workflow |
|---|---|
| New project, or a small existing package with no harness | [init](init.md) → approved plan → [next](next.md) or [goal](goal.md) |
| Broad existing package needing a factual context map | [archive](archive.md) → verified preflight → [init](init.md) → execution |
| An initialized project with one ready task | [next](next.md) |
| Several approved milestones to run in order | [goal](goal.md) |
| An initialized project needs a requested feature or candidate promotion | [propose](propose.md) → approved planning changes → separately requested execution |
| A new engineering review arrives | [reconcile](reconcile.md) → approved planning changes → separately requested execution |
| An existing project needs updated workflow rules | [upgrade](upgrade.md) → approved rule merges → separately requested execution |
| The current milestone becomes ready to close | Its execution workflow performs review and closure, including retirement when the project has adopted that lifecycle. No archive invocation. |

## A new project

Install the skills for your agent, then create a project directory in a
terminal. For example:

```bash
mkdir order-tracker
cd order-tracker
git init
```

Open your agent in that directory and describe the outcome you want. For the
Claude Code plugin, send:

```text
/memory-bank:memory-bank-init
I want a local order tracker. The first usable version should record items and
quantities, calculate totals, and save orders between sessions. Ask about the
decisions you need, then show the complete proposal before writing.
```

In Codex, replace the first line with `$memory-bank:memory-bank-init`; in DSH,
use `/memory-bank-init`.

Answer the discovery questions about scope, behavior, constraints, and
verification. Init proposes the active milestones and all file changes. Review
that proposal, request corrections if needed, and approve it when it matches
the project you want.

After the approved files are written, check that:

- `product.md` describes the intended outcome and exclusions.
- `architecture.md` distinguishes existing implementation from proposed work.
- `tech-stack.md` names commands that can verify the project.
- `milestone.md` defines acceptance and the order of the active milestones.
- The status files break that work into specific tasks with permanent IDs.

Then send a separate request to [Next](next.md):

| Agent | Execute one task |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-next` |
| Codex plugin | `$memory-bank:memory-bank-next` |
| DSH | `/memory-bank-next` |

Inspect the changed code, verification results, task notes, and commit when the
policy calls for one. Repeat Next for another task, or use [Goal](goal.md) when
you are ready to authorize an explicit milestone order and commit policy.
Initialization itself never starts implementation.

## An existing codebase

The repository already contains years of decisions spread across source, tests,
manifests, CI, and documents written at different moments. Some agree; some are
stale.

Start by establishing which facts are supported by current code and tests.
For a broad package, Archive preserves a verified context map before Init
proposes delivery work. An evidence gap remains a gap until you decide whether
it belongs in the plan.

```text
existing facts -> current project map -> approved milestones -> implementation
new review     -> current-state validation -> reconciled milestones -> implementation
```

Ask [Init](init.md) to inspect the codebase and determine whether it needs an
[Archive](archive.md) preflight. If it does, separately request Archive, approve
its proposed contexts and file actions, and wait until every selected context
is verified. Then return to Init to plan the delivery work. Existing project
rules and verified context records are preserved.

## A review arrives mid-project

Four findings land. Before fixing any of them, [reconcile](reconcile.md) asks
whether they are still true against the current repository, then proposes a
disposition for each: confirmed, duplicate, already resolved, outside ownership,
deferred.

Confirmed work lands in an open milestone or a new remediation milestone with
lineage. Completed history is never reopened. Downstream pending milestones are
updated before implementation begins, because a finding can change assumptions
shared by several milestones.

## A project with months of history

For a project that has adopted the retirement rules, once a milestone has
passed verification, its review gate, knowledge consolidation, and downstream
reconciliation, its full specification and status document retire into
`tabilet/docs/history/`, its identifier
stays reserved, and the active plan stops carrying it.

What stays close to the next task is `lessons.md`. A completed milestone might
contain every task note and test result; the enduring lesson is that tests using
only single-unit orders concealed a quantity bug, so future pricing tests need
multi-unit cases.

For projects created under older rules, use [Upgrade](upgrade.md) to compare the
bundled contract with the current project. Approve specific rule merges while
preserving task outcomes, permanent IDs, review counters, and frozen records.
Installing newer skills does not adopt retirement or move existing milestones.

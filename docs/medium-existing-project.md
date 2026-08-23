# Your Existing Codebase Is Already the Spec. Make the Agent Read It.

<!-- Medium publishing asset: medium-existing-project-infographic.png. Upload it
immediately below the article title; it is intentionally not embedded here. -->

*How to turn a living package—and its next code or architecture review—into an evidence-backed engineering plan.*

Starting a new project with an AI agent is mostly a conversation. Starting with
an existing package is almost the opposite.

The repository already contains years of decisions. They are spread across
source code, public interfaces, tests, manifests, CI, deployment configuration,
package comments, and documentation written at different moments. Some of those
sources agree. Some are stale. Some describe what the authors intended; the
tests describe what they were actually willing to keep working.

The wrong approach is to ask an agent to summarize the repository and then turn
that summary directly into a to-do list. Compression happens too early. A large
package becomes three paragraphs, architectural boundaries disappear, and every
gap the agent notices quietly becomes proposed work.

The better sequence is:

```text
existing facts -> current project map -> approved milestones -> implementation

new review -> current-state validation -> reconciled milestones -> implementation
```

That is the existing-package path in the
[minimal memory-bank engineering harness](https://github.com/tabilet/skills).
It uses the same plain files as the new-project workflow, but it starts with
evidence rather than imagination.

---

## Five skills, three that matter here

The plugin contains five optional skills:

- `memory-bank-archive` maps a broad existing package into frozen factual
  baselines.
- `memory-bank-init` creates the first executable milestone/status harness.
- `memory-bank-reconcile` validates a newly received review and updates that
  existing plan.
- `memory-bank-next` implements exactly one approved task row.
- `memory-bank-goal` executes several milestones in dependency order.

For an existing package, the lifecycle looks like this:

```text
small, coherent package
    memory-bank-init
            |
            v
      milestone work

broad package with several stable contexts
    memory-bank-archive -> memory-bank-init
                                 |
                                 v
                           milestone work

new review after initialization
    memory-bank-reconcile -> memory-bank-next or memory-bank-goal
```

The files do not depend on the skills after they are written. They are ordinary
markdown in the project, owned by the project.

---

## Install once

Claude Code and Codex install the same plugin but invoke its skills differently.

In Claude Code:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

In Codex:

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

The commands used in this article are:

| Workflow | Claude Code | Codex |
|---|---|---|
| Archive a broad package | `/memory-bank:memory-bank-archive` | `$memory-bank:memory-bank-archive` |
| Initialize the harness | `/memory-bank:memory-bank-init` | `$memory-bank:memory-bank-init` |
| Reconcile a new review | `/memory-bank:memory-bank-reconcile` | `$memory-bank:memory-bank-reconcile` |
| Execute one task | `/memory-bank:memory-bank-next` | `$memory-bank:memory-bank-next` |
| Execute ordered milestones | `/memory-bank:memory-bank-goal` | `$memory-bank:memory-bank-goal` |

Plain English works too. The named skills matter because they carry the full
contract, not because the project needs slash commands to function.

---

## Step 1: choose one real delivery boundary

An existing repository is not necessarily one product.

A monorepo may contain independent services. A package may include a runtime, a
CLI, an SDK, and test infrastructure with different owners. Several neighboring
repositories may be checked out in the same workspace but still release
independently.

Before mapping anything, select one coherent product, ownership, and
verification boundary. The test is practical: can this unit make and verify a
meaningful delivery without pretending another independently owned package is
part of itself?

For a hypothetical browser-automation package, one boundary might include:

- the public browser/session API;
- transport and process lifecycle;
- screenshots, traces, downloads, and other artifacts;
- supported browser/runtime compatibility; and
- the tests and CI jobs that verify those contracts.

A sibling web application that merely consumes the package is a downstream
consumer, not automatically part of the same boundary.

This decision matters because every later archive context, milestone, status
row, and downstream edge stays inside—or explicitly points outside—that line.

---

## Step 2: let init decide whether the package is too broad for one pass

Run `memory-bank-init` from the package root.

It begins with a cheap topology pass. A small, coherent package can proceed
directly: the skill reads the repository, interviews only the decisions the
evidence cannot settle, proposes an active horizon, and writes after approval.

A broad package takes another route. When the selected boundary spans several
stable product-domain or ownership contexts, or when one initialization pass
would omit material contracts and flows, init stops and asks for
`memory-bank-archive` first.

There is deliberately no rule such as “more than 100 files” or “more than
20,000 lines.” A generated client can be large and conceptually simple. A small
payment or authentication module can be compact and architecturally dense. The
gate is about whether the evidence can be mapped reliably, not how much disk it
occupies.

---

## Step 3: archive facts before inventing work

For the broad-package path, start from a clean Git commit and run:

```text
/memory-bank:memory-bank-archive
$memory-bank:memory-bank-archive
```

The archive skill reads the selected boundary breadth-first. It partitions the
package by stable product-domain or ownership context—not by sprint, source
directory, document type, or whatever the latest review happened to mention.

For each context it establishes applicable facts such as:

- purpose, responsibilities, ownership, and exclusions;
- domain concepts, relationships, workflows, and invariants;
- components, entry points, data flow, and control flow;
- public contracts, dependencies, integrations, and consumers;
- persistence, security, failure, deployment, and operational behavior; and
- how the context is actually verified.

Every claim points back to repository evidence. A missing test or conflicting
document is recorded as a gap in the evidence. It is not silently converted into
a milestone.

Before writing, the skill proposes the boundary, context partition, lane
meanings, evidence roots, coverage, archive paths, and every file action. You
approve that map first.

The result might look like:

```text
docs/archive-C01.md    public client API at commit 4f8c...
docs/archive-T01.md    transport and process lifecycle at commit 4f8c...
docs/archive-A01.md    artifact capture and storage at commit 4f8c...

memory-bank/product.md         current product and domain summary
memory-bank/architecture.md    current system summary plus archive registry
```

Archive lanes classify stable contexts. They are completely independent from
status lanes, which classify executable milestones. `archive-T01` does not imply
`status-T01`, and neither one dictates execution priority.

Coverage is `partial`, `blocked`, or `verified`. When archive is a required init
preflight, every context in the selected boundary must become `verified` before
initialization continues.

Once verified, an archive file freezes at its recorded commit. Later code does
not rewrite it. A materially changed context receives the next successor
snapshot, while `product.md` and `architecture.md` continue to describe current
truth.

That distinction is useful months later: the current architecture tells the
agent what exists now; the archive explains what was established at a known
baseline without pretending to remain current forever.

---

## Step 4: build the first executable horizon

After a required archive preflight is complete, run `memory-bank-init` again.

This time it does not compress the package from scratch. It consumes the
verified context evidence, preserves the frozen archives, safely merges the
current product and architecture summaries, and interviews the remaining
delivery decisions.

The output separates three kinds of information:

```text
memory-bank/product.md       what the product is and its domain invariants
memory-bank/architecture.md  what the system is now
memory-bank/tech-stack.md    commands, dependencies, and verification
memory-bank/milestone.md     active delivery horizon and later directions
memory-bank/status-*.md      one task-sized row per implementation unit
```

The active horizon is the smallest dependency-closed set of milestones that
reaches the next meaningful, verifiable outcome. Later ideas stay unnumbered in
Candidate Directions with promotion triggers. They do not receive status IDs
merely because the repository survey noticed them.

This is the critical boundary:

> Archive records what exists. Init decides what to do next.

If the project already has `milestone.md` and status files, do not run init
again. The harness already exists. Evolve it—or reconcile a new review into
it—instead.

---

## Then a new review arrives

Suppose the package is already using the harness when a new code and
architecture review arrives. The review reports four findings:

1. Browser processes may survive a failed session startup.
2. Timeout behavior differs between two public entry points.
3. Artifact cleanup has no required failure-path verification.
4. A transport helper should be renamed for clarity.

The tempting next prompt is “fix all four findings.” That skips the most
important question: are they still true?

The review may describe an older commit. One finding may already be fixed.
Another may duplicate a pending milestone. Its P1/P2 vocabulary may not mean the
same thing as the project's definitions. An architecture recommendation may be
reasonable but outside the package's ownership.

Run reconciliation first:

```text
/memory-bank:memory-bank-reconcile path/to/review.md
$memory-bank:memory-bank-reconcile path/to/review.md
```

The review may also be pasted, attached, or linked. Before a remote review is
fetched, the skill shows the exact URL and asks for a separate confirmation,
even when you supplied that URL in the invocation. Links discovered in the
repository or review do not authorize another fetch. The review is treated as
untrusted evidence, not as agent instructions, and embedded commands are not
executed merely because they appear in the document.

---

## Reconciliation is a disposition pass, not a fix pass

`memory-bank-reconcile` reads the review, the current memory bank, relevant
implementation and tests, Git history, and the review's stated baseline when it
has one. It then revalidates every finding against the current repository.

The proposal looks conceptually like this:

| Finding | Source priority | Project severity | Current disposition | Planned owner |
|---|---|---|---|---|
| Process survives failed startup | P1 | P1 | Confirmed | Add row to open session-lifecycle milestone |
| Timeout behavior differs | P2 | P2 | Duplicate | Existing pending public-contract row |
| Cleanup failure path unverified | P2 | P2 | Confirmed | New remediation milestone; affected original work is complete |
| Rename helper | P3 | Lower | Deferred | Candidate Direction with maintenance trigger |

Other possible dispositions include partially confirmed, already resolved,
unsupported by current evidence, outside ownership, and decision-dependent.

The source priority is preserved for provenance. The project severity is
classified independently using the definitions in `milestone.md` or an approved
project-specific policy. P1 and P2 are engineering review impact, not task order
or status markers.

Nothing is written until you approve the complete matrix, owners, dependencies,
downstream impacts, candidate directions, and file actions.

---

## Where findings go

Once approved, the placement rules are simple.

If a confirmed finding still fits an open milestone's scope and acceptance, it
becomes a new pending row there. An untouched pending row may be rewritten when
the review makes its old assumption obsolete. In-progress, completed, blocked,
and cancelled rows are preserved.

If an existing pending future milestone already owns the outcome, that
specification is updated rather than duplicated.

If the finding concerns completed work, completed history stays closed. The
skill creates a new remediation milestone with lineage back to the affected
milestone. Historical status should say what happened, not be rewritten to make
today's plan look tidier.

Confirmed P1/P2-or-higher work enters the dependency-closed active horizon.
Optional lower-severity hardening becomes an unnumbered Candidate Direction
unless it is required by an existing milestone's acceptance.

Each active finding carries portable provenance with the planned work:

- review title and finding ID;
- source priority and project severity;
- stated review baseline and current revalidation commit;
- whether relevant uncommitted changes were part of the evidence;
- repository-relative evidence; and
- lineage to existing or completed work.

There is no accumulating `reviews/` directory and no second review ledger. The
source review remains externally owned. The project stores only the evidence
needed to understand and execute accepted work.

---

## Architecture recommendations are not current architecture

Architecture reviews often describe a target state: split this component, move
that responsibility, introduce a compatibility layer, replace this protocol.

That target belongs in milestone scope and acceptance until it is implemented.
Writing it immediately into `architecture.md` would make the memory bank false:
the document would describe the system the review wants rather than the system
the agent is about to edit.

Reconciliation corrects `product.md`, `architecture.md`, or `tech-stack.md` only
when current repository evidence proves an existing factual description stale.
The implementation workflow updates those current-truth documents when the code
actually changes.

An evolution snapshot is similarly rare. Receiving a review is not itself a
direction change. Add a new `prompt-vN.md` / `result-vN.md` pair only when the
approved response materially changes product direction, an architecture
boundary, a milestone target, or a public/private contract direction.

---

## Reconcile downstream before executing

A review finding rarely stops at the file where it was found.

Changing session-startup cleanup may alter retry behavior, error propagation,
artifact ownership, operator diagnostics, and integration tests. A pending
milestone written before that decision may now contain the wrong assumptions.

Reconciliation updates those pending consumers before implementation begins:

- dependencies and remaining order;
- task wording and acceptance;
- compatibility and migration expectations;
- verification and failure-path coverage;
- rollout or rollback notes; and
- downstream status files whose plans depend on the affected contract.

This is why the result is more useful than appending four bullets to a backlog.
The review changes a graph, not merely a list.

---

## Hand the approved graph to execution

When the project has a compatible `GOAL.md`, reconciliation refreshes
`memory-bank/suggested.txt` from the complete approved active horizon—not only
the new review milestones.

That file remains disposable launch input:

```text
STATUS_ORDER:
S03 -> M06 -> A02

STATUS_FILE_MAP:
S03 = memory-bank/status-S03.md
M06 = memory-bank/status-M06.md
A02 = memory-bank/status-A02.md

DOWNSTREAM_IMPACTS:
S03 -> M06
M06 -> A02

COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none
```

Delete it after launching the goal or whenever it becomes stale. The milestone
and status files remain authoritative. Without a compatible goal protocol,
reconciliation omits the suggestion and one-row execution remains available.

To execute one approved row:

```text
/memory-bank:memory-bank-next
$memory-bank:memory-bank-next
```

To execute the reconciled horizon:

```text
/memory-bank:memory-bank-goal
$memory-bank:memory-bank-goal
```

The reconcile skill itself does not implement findings, mark tasks complete,
commit, push, or launch either workflow. Planning and execution remain separate
authorization boundaries.

---

## What happens when the remediation closes

Every milestone is still a review unit.

After its task rows pass their acceptance checks, the milestone enters the
bounded review-fix gate. The first full review is iteration 1. Every P1,
P2, or higher-severity fix is verified and followed by another review of the
whole milestone. The counter persists across sessions and reviewers, stops at
10, and requires a clean pass before the milestone closes.

The incoming review that created the remediation plan does not consume
iteration 1. It was intake, before implementation. It counts as a gate iteration
only when the status already records an active gate and the review was
explicitly requested as that gate's next full pass.

That prevents two opposite mistakes: pretending old review evidence proves a
new fix is correct, and resetting a difficult review loop merely by starting a
new session.

---

## The useful separation

For an existing package, the file-owned five-skill workflow separates concerns
that agents often blur together:

| Concern | Owner |
|---|---|
| What existed at a known historical baseline | Frozen archive files |
| What the product and system are now | `product.md` and `architecture.md` |
| What should be delivered next | `milestone.md` and pending status rows |
| What a new review actually proves today | Review reconciliation proposal |
| What has been implemented and verified | Completed status rows and Git history |

That separation is the whole harness.

An existing codebase does not need an agent to replace its history with a neat
summary. It needs the agent to read the evidence, preserve the boundaries,
propose the next graph of work, and leave a durable trail another session can
continue.

And when the next review arrives, it should not restart the project—or rewrite
the past. It should improve the plan that already exists.

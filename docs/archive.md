# Archive

Snapshot a broad existing package at a clean baseline into frozen,
evidence-backed context files, then create or refresh the current product and
architecture summaries.

Send the request in a session for your project:

| Agent | Conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-archive` |
| Codex plugin | `$memory-bank:memory-bank-archive` |
| DSH | `/memory-bank-archive` |

No arguments are required. You can describe the package or context you want
mapped. For direct skill-folder installs, see the
[invocation prefixes](installation.md#invoke-a-skill).

## When to use it

Before [init](init.md), when a large existing package needs a repository-mapping
preflight. Later, when materially changed contexts need successor snapshots.

Init assesses whether an archive preflight is needed and explains the result.
If it is needed, explicitly request Archive before returning to Init. A small,
coherent package proceeds directly to initialization, while a boundary spanning
several stable contexts is sent here first. There is deliberately no file-count
or line-count threshold. A generated client can be large and conceptually
simple; a payment module can be compact and architecturally dense.

## What it produces

Facts, not a roadmap. Archive files never contain executable task state and
never enter a status or goal order.

```text
docs/archive-C01.md    public client API at commit 4f8c…
docs/archive-T01.md    transport and process lifecycle at commit 4f8c…
docs/archive-A01.md    artifact capture and storage at commit 4f8c…

memory-bank/product.md         current product and domain summary
memory-bank/architecture.md    current system summary plus the archive registry
```

For each context it establishes purpose and ownership, domain concepts and
invariants, components and data flow, public contracts and dependencies,
persistence and security and operational behavior, and how the context is
actually verified. Every claim points back to repository evidence.

A missing test or a conflicting document is recorded as a gap in the evidence.
It is not silently converted into a milestone.

## Three phases

**Survey.** Read agent instructions, docs, manifests, build and CI
configuration, package boundaries, entry points, public interfaces, tests, and
deployment files. Select one coherent product, ownership, and verification
boundary. Fix the baseline: a clean worktree at a full `HEAD` commit when Git
exists, or an explicitly `unversioned` snapshot after you accept that weaker
provenance.

**Propose.** Present the boundary, the context partition, lane meanings,
coverage, evidence roots, successor decisions, and every file action. Nothing is
written until you approve all of it.

**Write.** Apply the approved actions under the bundled write contract.

## Archive lanes

Archive files are named `docs/archive-<LANE><NN>.md`. The letter classifies a
stable product-domain or ownership context; the number is snapshot chronology
within that lane.

Archive lanes are **independent from status lanes**. `archive-T01` does not
imply `status-T01`, and neither dictates execution priority. Partition by
durable context, never by feature, sprint, review finding, team name, document
type, or source directory.

Coverage is `partial`, `blocked`, or `verified`. When archive is a required init
preflight, every context in the boundary must reach `verified` before
initialization continues.

## Freezing

Once verified, an archive freezes at its recorded commit. Later code does not
rewrite it. A materially changed context receives the next unused successor ID.
`product.md` and `architecture.md` continue to describe current truth.

That distinction earns its keep months later: the current architecture tells the
agent what exists now, and the archive explains what was established at a known
baseline without pretending to remain current.

## What it will not do

Archive writes facts. It does not create or modify milestones, candidate
directions, status rows, goal input, commits, or external state. A file move or
an internal refactor that leaves high-level facts unchanged does not justify a
successor.

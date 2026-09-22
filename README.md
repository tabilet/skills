# A Minimal Engineering Harness

Coding agents work better when a project can explain itself: what it is, what is
done, and what comes next. This repository gives you a small set of plain-text
files, mostly markdown, that do exactly that. You copy them into your project and
own them from that moment on.

Everything here is plain text, so `git` is the only tool you need. You can read
the files, edit them by hand, rename them, or delete them, and any agent that
reads markdown can work with them. Optional skills will generate the files for
you, and an optional API runner will work through them unattended; both stay
outside your project.

`template/` goes into your project, and `harness/` goes into your home directory
if you want the API runner. Once the files are in place they belong to your
project, and your project stays independent of this repository. Six months from
now, the only files you are maintaining are still your own.

Seven optional skills can do the mapping, copying, and filling for you; see
[Install The Seven Skills](#install-the-seven-skills). The files they write are
yours from the moment they appear. You and your agent maintain them during
authorized work; installing or updating the plugin does not migrate them.

[Release notes](docs/RELEASE_NOTES.md) include the v2 project layout and
the explicit v1.5.0 migration.
The [Tabilet Memory Bank website](https://tabilet.github.io/skills/) has the published guides, with a [Simplified Chinese mirror](https://tabilet.github.io/skills/zh/).

Your project ends up looking like this:

```text
your-project/
├── AGENTS.md                 what an agent should read first
├── docs/                     other project documentation
└── tabilet/
    ├── GOAL.md               optional multi-milestone protocol
    ├── memory-bank/           current facts and active work
    │   ├── product.md         product scope, domain model, and non-goals
    │   ├── architecture.md    layout, data flow, boundaries
    │   ├── tech-stack.md      commands, dependencies, verification
    │   ├── lessons.md         applicable lessons and their evidence
    │   ├── milestone.md       active milestones and later directions
    │   ├── status-M01.md      one file per active milestone
    │   └── suggested.txt      optional launch reference
    ├── docs/                  optional frozen archives and retired history
    │   ├── archive-A01.md
    │   └── history/
    └── evolution/             versioned direction snapshots
        ├── prompt-v1.md
        └── result-v1.md
```

The term *memory bank* was popularised by [Cline](https://docs.cline.bot/best-practices/memory-bank); this is a different
implementation of the same idea, in plain files with no runtime.

Throughout, **harness** means a repeatable command that proves something works,
such as your test suite, a CI job, or a script. Your project defines its own in
`tech-stack.md`. This repository also ships one optional harness of its own, an
API loop that drives an agent through the memory bank unattended.

## Getting Started

**New to this?** [docs/TUTORIAL.md](docs/TUTORIAL.md) walks a toy project from
an empty directory to a first committed task in twenty minutes, using
the `memory-bank-init` skill to do the setup. The rest of this README is
reference material, and the tutorial is a guided path through it.

Already have a project or a new review? [Skill use cases](docs/USE_CASES.md)
shows individual and combined workflows, including automatic retirement versus
explicit context snapshots.

The memory bank is plain Markdown and needs no runtime to read or maintain.
Git is required by the usual per-task commit workflow and the optional API
harness. A permitted no-commit workflow can maintain the same files without
Git, including their retired records.

Python 3 is used by the optional API harness and the one-time v1.5.0 migration
command. Both use only the standard library.

Already have v1.5.0 project files at the root? [Preview the explicit v2
migration](docs/upgrade.md#migrate-a-v150-project-to-v2) before using v2 skills.
Installing v2 does not move project files.

The existing-project instructions below also use
[ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) for the initial inventory.

The quickest way to start does not require cloning anything. Install the plugin
and let its namespaced `memory-bank-init` skill interview you and write the
memory bank for you:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
/memory-bank:memory-bank-init
```

Run those commands in Claude Code from a new or small existing project and
answer the questions. A large existing package may first be routed through
`memory-bank-archive`; see [Set Up An Existing Project](#set-up-an-existing-project).
The Codex equivalent, DSH route, and plain-file installation are in
[Install The Seven Skills](#install-the-seven-skills).

To work from the files by hand instead, clone this repository once. Every `cp`
command below refers to your clone as `/path/to/skills`:

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

Nothing runs from the clone itself. You copy files out of it: `template/` into a
project, `harness/` into your home directory.

## What Is In This Repository

Project-level sample files in [template/](template/), copied into a project
root:

- [template/AGENTS.md](template/AGENTS.md)
- [template/tabilet/GOAL.md](template/tabilet/GOAL.md) — the multi-milestone execution protocol
- [template/tabilet/memory-bank/product.md](template/tabilet/memory-bank/product.md)
- [template/tabilet/memory-bank/architecture.md](template/tabilet/memory-bank/architecture.md)
- [template/tabilet/memory-bank/tech-stack.md](template/tabilet/memory-bank/tech-stack.md)
- [template/tabilet/memory-bank/lessons.md](template/tabilet/memory-bank/lessons.md)
- [template/tabilet/memory-bank/milestone.md](template/tabilet/memory-bank/milestone.md)
- [template/tabilet/memory-bank/status-M01.md](template/tabilet/memory-bank/status-M01.md)
- [template/tabilet/evolution/prompt-v1.md](template/tabilet/evolution/prompt-v1.md)
- [template/tabilet/evolution/result-v1.md](template/tabilet/evolution/result-v1.md)

The optional API runner and its human-readable instruction copy live in
[harness/](harness/):

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

The seven skills are in [skills/](skills/). Claude Code, Codex, and DSH read the
same `SKILL.md` bundles, so there is one source per skill:

- [memory-bank-archive](skills/memory-bank-archive/SKILL.md) — snapshot a large
  existing package into frozen, evidence-backed context archives
- [memory-bank-init](skills/memory-bank-init/SKILL.md) — interview a
  project into existence, then write its memory bank
- [memory-bank-upgrade](skills/memory-bank-upgrade/SKILL.md) — propose and apply
  approved workflow-rule upgrades while preserving existing project state
- [memory-bank-propose](skills/memory-bank-propose/SKILL.md) — plan a requested
  feature, candidate promotion, or future direction change
- [memory-bank-reconcile](skills/memory-bank-reconcile/SKILL.md) — validate a
  new review against current code and reconcile the approved work plan
- [memory-bank-next](skills/memory-bank-next/SKILL.md) — tackle one row,
  verify it, commit it
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md) — run an ordered
  set of milestones

Init, archive, propose, and reconcile inspect their planning references before
presenting a complete proposal. They write only after its approval, then continue through
verification within that scope. Upgrade presents focused rule diffs while
preserving project content. Goal loads optional runtime help only when needed;
keep its supporting reference when copying the bundle.

Unlike the copyable template, `memory-bank-init` can derive project-specific
goal input; `memory-bank-reconcile` and `memory-bank-propose` can refresh it
when approved planning changes the active graph. When the project contains an approved compatible `tabilet/GOAL.md`,
they write `tabilet/memory-bank/suggested.txt` with a proposed `STATUS_ORDER`,
`STATUS_FILE_MAP`, and `DOWNSTREAM_IMPACTS`. The file is advisory and disposable,
covers only the approved active horizon, and excludes unnumbered candidate
directions; the milestone and status files remain authoritative. They omit the
launch reference when no compatible protocol exists instead of naming a missing
or incompatible file.

`.claude-plugin/` holds the compatibility manifest used to install the same
plugin in Claude Code and Codex. Nothing in `template/` is vendor-specific.

Harness references:

- [Execution Harness](docs/EXECUTION.md)
- [Model Eval Harness](docs/MODEL_EVAL.md)

## What A Filled-In Memory Bank Looks Like

The template ships placeholders. Here is the same memory bank filled in for a
small shopping service, so you can see the destination before the directions.

`tabilet/memory-bank/product.md` starts as `[project-name] is [one or two sentences
describing the project]` and becomes:

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.

## Domain model

| Concept | Meaning | Relationships and invariants |
|---|---|---|
| Cart | A shopper's pending purchase. | Belongs to one shopper and contains line items. |
| Line item | A product and requested quantity in a cart. | Belongs to exactly one cart. |
| Checkout | The transition from an active cart to payment. | Starts only from a non-empty cart with current pricing. |
```

`tabilet/memory-bank/milestone.md` is the file that decides how everything else is
organised. It names the lanes and states what each one covers:

```markdown
## Status ID Pattern

M01, M02, ...   Default lane: cross-cutting work, infrastructure, chores
S01, S02, ...   Storefront: cart, checkout, product pages
A01, A02, ...   Accounting: pricing, invoices, payment reconciliation

Lane meanings:

- `M`: anything that does not belong to a product domain.
- `S`: shopping surface. Owned by the storefront team.
- `A`: money. Changes here need a second reviewer.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| S01 | [status-S01.md](status-S01.md) | Cart and checkout. |
| A02 | [status-A02.md](status-A02.md) | Payment contract. |

## S01 - Cart And Checkout

**Goal.** A shopper can fill a cart and complete a purchase.

**Scope.**

- Cart CRUD behind `POST /cart`.
- Line-item and order-total pricing.
- Handoff to the payment provider.

**Acceptance.** `make test` passes, and a scripted end-to-end purchase
succeeds against the staging payment sandbox.
```

Then `tabilet/memory-bank/status-S01.md` carries the rows for that milestone:

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules are being resolved. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
| Legacy rounding attempt | `[-]` | Consumed failed attempt; successor: Cart total calculation. |
```

**The backticks around each marker are required by the included API harness.**
It matches
`` `[ ]` ``, not `[ ]`. The current harness rejects a task marker such as
`| Item | [ ] | Notes |` with exit `11`, including when other rows are valid.
Empty or unreadable status files also stop the run. Older separately installed
runners can silently overlook malformed rows; updating skills does not update
that runner.

## Set Up A New Project

If you installed [the seven skills](#install-the-seven-skills),
`memory-bank-init` does everything in this section: it interviews you, proposes
lanes and milestones, waits for your approval, and then writes the files already
filled in. The two routes below are the same work done by hand.

### Manual

From a new project root:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Then edit the copied files in this order:

1. `tabilet/memory-bank/product.md`: define product scope, canonical domain terminology,
   concept relationships and business invariants, and non-goals.
2. `tabilet/memory-bank/architecture.md`: define layout, data flow, and boundaries.
3. `tabilet/memory-bank/tech-stack.md`: define commands, dependencies, and harnesses.
4. `tabilet/memory-bank/milestone.md`: define the status ID lanes (see
   [Status ID lanes](#status-id-lanes)) and the first milestone.
5. `tabilet/memory-bank/status-M01.md`: define the first milestone's actionable rows.
   See [what a filled-in memory bank looks
   like](#what-a-filled-in-memory-bank-looks-like), and note that the marker
   backticks matter.
6. `tabilet/evolution/prompt-v1.md`: record the initial direction.
7. `tabilet/evolution/result-v1.md`: record the current starting state.
8. `AGENTS.md`: replace placeholders with project-specific commands and rules.

Keep `README.md` simple and user-facing. Put long-form references in `docs/`.

### Wiring up your agent

`AGENTS.md` is an [open cross-vendor standard](https://agents.md) stewarded by
the Agentic AI Foundation. Most coding agents read it with no setup at all,
among them Codex, Cursor, Gemini CLI, GitHub Copilot's coding agent, Devin,
Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, and Amp.

No vendor-specific file ships in `template/`. If your agent reads a different
filename, bridge it to `AGENTS.md` in one line rather than keeping a second copy
that will drift:

| Agent | Bridge |
|---|---|
| Anything on the list above | Nothing to do |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`, or a `CLAUDE.md` containing `@AGENTS.md` |
| Anything else that reads its own file | Symlink or import `AGENTS.md` the same way |

On Windows, symlinks need Administrator or Developer Mode, so prefer the import
form there.

### With Help Of An AI Agent

For a new project, you can use the sample files as the initial structure and ask
an AI agent to fill them in after you describe the product.

Warning: copying these files over an existing project can overwrite files already
on disk. Make a backup or commit your current work first.

From the new project root:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Then chat with the agent until the product, users, boundaries, commands, and
first milestone are clear. Ask it to fill in:

- `AGENTS.md`
- `tabilet/memory-bank/product.md`
- `tabilet/memory-bank/architecture.md`
- `tabilet/memory-bank/tech-stack.md`
- `tabilet/memory-bank/milestone.md`
- `tabilet/memory-bank/status-M01.md`
- `tabilet/evolution/prompt-v1.md`
- `tabilet/evolution/result-v1.md`

Example prompt:

```text
Read the sample AGENTS.md, tabilet/memory-bank/*, and tabilet/evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, define the
status ID lanes in tabilet/memory-bank/milestone.md, and make tabilet/memory-bank/status-M01.md
contain the first actionable milestone rows.
```

## Set Up An Existing Project

`memory-bank-init` handles a small existing package directly. It reads what the
repository already states in the README, tests, build and CI files, interfaces,
schemas, source layout, and infrastructure, then asks only about decisions the
evidence cannot settle.

For a large existing package, init first performs a cheap topology pass. When
the selected boundary spans several stable product-domain or ownership
contexts, or cannot be evidenced reliably in one initialization pass, it stops
before writing and requires `memory-bank-archive` as a preflight. This is an
adaptive evidence boundary, not a file-count or line-count threshold.

### Archive A Large Existing Package

Start from a clean Git commit and run:

```text
/memory-bank:memory-bank-archive   # Claude Code plugin
$memory-bank:memory-bank-archive   # Codex plugin
```

The skill maps the whole selected product boundary breadth-first and proposes
stable domain or ownership contexts before writing. After approval it creates
frozen context dossiers such as `tabilet/docs/archive-C01.md`, records the full baseline
commit, and creates or refreshes the current `tabilet/memory-bank/product.md` and
`tabilet/memory-bank/architecture.md` summaries.

Archive lanes classify contexts independently from status lanes. Their numbers
are snapshot chronology, not work priority. Every context must be `verified`
before the required preflight is complete; partial or blocked coverage prevents
init from proceeding. Archives contain evidence-backed facts, never milestones,
status rows, candidate directions, or goal input.

Verified archives never change. A later archive run creates the next successor
ID only when a context's high-level domain, ownership, component, flow,
contract, dependency, operational, or verification facts materially changed.
Normal code work keeps `product.md` and `architecture.md` current and records
implementation in status history; it does not rewrite the baseline archive.

After the archive index shows every selected context as verified, run
`memory-bank-init`. It consumes the archive evidence, safely merges the seeded
summaries, interviews the remaining decisions, and creates the milestone/status
harness.

### Manual

For an existing project, read before writing:

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

Then:

1. Read the root README, agent guides, docs, package READMEs, and major package
   comments.
2. Copy in `template/` from this repository.
3. Fill the memory bank from what the project already says, not from an imagined
   rewrite.
4. Move stable long-form references into `docs/`.
5. Convert duplicated roadmap/status material into `tabilet/memory-bank/milestone.md`
   and one `tabilet/memory-bank/status-<LANE><NN>.md` file per milestone.
6. Keep known gaps visible in the matching status file instead of hiding them.

### With Help Of An AI Agent

For an existing project, the agent can do the inventory and first memory-bank
draft. This works best when the project already has useful README, docs, package
comments, tests, or CI files.

Warning: copying these sample files into an existing project can overwrite
existing `AGENTS.md`, `tabilet/memory-bank/`, or `tabilet/evolution/` files. Commit first, make a
backup, or copy the samples to a temporary location before asking the agent to
merge them.

From the existing project root:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Then ask the agent to read the project before writing:

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
tabilet/memory-bank/*, and tabilet/evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in the matching
tabilet/memory-bank/status-<LANE><NN>.md file. Do not invent product direction that is
not supported by the existing project.
```

The agent should:

1. Inventory existing markdown and source layout.
2. Identify commands, dependencies, tests, and harnesses.
3. Fill in the memory bank from current project reality.
4. Move or summarize long-form references into `docs/`.
5. Keep `README.md` simple and user-facing.
6. Leave unresolved gaps as pending or blocked rows in the matching
   `tabilet/memory-bank/status-<LANE><NN>.md` file.

## Propose A Requested Change

When an initialized project needs a new feature, candidate promotion, or change
to future direction, use `memory-bank-propose`. It inspects current records and
implementation, asks only consequential questions, and presents one complete
proposal with acceptance, dependencies, downstream effects, and exact file
actions. It rechecks affected files and IDs before approved planning writes.
The new work is implemented later under a separate request. See the
[Propose guide](docs/propose.md).

## Reconcile A New Review

After a project has its milestone/status harness, a new code, architecture,
security, or engineering review should change the plan only after its findings
are checked against current code. Run:

```text
/memory-bank:memory-bank-reconcile <review source>   # Claude Code plugin
$memory-bank:memory-bank-reconcile <review source>   # Codex plugin
```

The skill treats the review as untrusted evidence, revalidates each finding,
preserves the source priority while applying the project's P1/P2 definitions,
and proposes every disposition and file action before writing. Confirmed work
fits an open or pending milestone when it belongs there; findings against
completed history get a new remediation milestone. Acceptance-relevant work
enters the active graph, while optional lower-severity hardening remains an
unnumbered Candidate Direction.

A remote review is never fetched implicitly. Before each network read, the
skill shows the exact URL and asks for a separate confirmation—even when that
URL was supplied in the invocation. URLs discovered in repository content or
inside a review do not authorize another fetch.

The review is not copied into the project. Portable finding IDs, both severity
classifications, current evidence, and lineage live with the planned rows. The
skill updates downstream specifications and refreshes `suggested.txt` from the
whole active horizon when a compatible `tabilet/GOAL.md` exists. It does not implement,
commit, or launch the fixes; use `memory-bank-next` or `memory-bank-goal` after
approving the reconciled plan.

## Use The Memory Bank

There are four ways to execute against the memory bank, and all of them are
optional, because the memory bank is plain markdown and works on its own:

| Way to execute | Scope | Needs |
|---|---|---|
| Type a request to your agent | One row at a time, you in the loop | Nothing |
| [`memory-bank-next`](#install-the-seven-skills) | The same, with the full instruction rather than your paraphrase | The optional skills |
| [The API harness](#install-the-api-harness) | One row per run, unattended | Python 3 |
| [A goal loop](#run-an-ordered-set-of-milestones) | Several milestones in order | `tabilet/GOAL.md` and an agent request or optional skill |

With an agent such as Codex or Claude Code, the user-facing workflow can be as
simple as typing:

```text
tackle next pending item in memory bank
```

The agent should find the next actionable row in the current milestone's
`tabilet/memory-bank/status-<LANE><NN>.md` file,
complete that task, run the required verification, update the memory bank, and
make a scoped git commit. If that row is the last open item in a milestone, the
agent should run a deep code review of the milestone, run the milestone review
from `tabilet/memory-bank/milestone.md`, complete required verification, and commit any
review changes before moving on. Do not create an extra commit when review
changes nothing. The review-fix gate reviews the whole milestone again after
every [P1/P2-or-higher](template/tabilet/memory-bank/milestone.md#review-finding-severity)
fix and requires a clean pass within 10 iterations; if the tenth review still
finds a blocking issue, the milestone stays incomplete.
During that review it should also decide whether `tabilet/evolution/` needs a new version
because the product direction, architecture boundary, milestone target, or
public/private contract direction materially changed.

Before you trust any of this, give the agent something to verify against. Fill
the **Execution harnesses** table in `tabilet/memory-bank/tech-stack.md` with the command
that proves your project works, such as `make test`, `npm test`, or a script you
already run, and record what passing it proves. A row should not reach `[+]` until that
command has passed. Without it, "mark a row complete only when verified" has no
referent and the agent will decide for itself what verified means.

Under the surface, the normal agent workflow is:

1. Read `AGENTS.md`.
2. Read the memory bank files in the order listed by `AGENTS.md`.
3. Tackle exactly one scoped task or status row.
4. Update the matching memory-bank file if scope, architecture, tools,
   milestone acceptance, or status changed.
5. Mark a row `[+]` only after verification passes.
6. Commit the row as a scoped unit.
7. Keep one `tabilet/memory-bank/status-<LANE><NN>.md` file for each active milestone;
   preserve closed records through the adopted retirement procedure.
8. If a milestone becomes complete, run a deep code review and the milestone
   review procedure in `tabilet/memory-bank/milestone.md`.
9. After review and required verification pass, commit any review changes; do
   not create an empty or redundant milestone commit.
10. Check `tabilet/evolution/` and add a new version only when the review finds a real
   direction, boundary, milestone, or contract change.

### Status ID lanes

Status files are named `tabilet/memory-bank/status-<LANE><NN>.md`. The lane letter
classifies the work and the number is zero-padded to two digits, so accounting
milestones become `status-A01.md` and `status-A02.md` while shopping milestones
become `status-S01.md`. `M` is the default lane for work that does not classify
into a domain lane. A lane holds at most 99 files; when a lane fills up, open a
new letter instead of adding a third digit. `tabilet/memory-bank/milestone.md` records
what each letter means and never lets an ID be reused.

The milestone file also holds **candidate directions** outside the active
execution horizon. They remain unnumbered and have no status files until their
promotion trigger is met, the work is reconciled again, and the promoted
breakdown is approved. This keeps permanent IDs and task lists from freezing
speculative far-future work.

**Choosing lanes.** A lane is a long-lived track of work, on the scale of a
product area rather than a milestone or a sprint. Classify by domain, meaning the
part of the product a change belongs to, because domains outlive teams,
priorities, and dates. Start
with `M` alone; split a letter out the first time a domain has enough work that
its rows would drown out everything else, or when it needs its own review
cadence. Two or three lanes is a normal steady state, and a project can run a
long time on one.

Under-splitting is cheap to fix: open a new letter and put new work there. Over-
splitting is permanent, because an ID keeps its name for the life of the
project once its file exists. When unsure, leave it in
`M`.

Status rows use these markers:

| Symbol | Meaning |
|---|---|
| `[ ]` | Pending; actionable when its dependencies pass |
| `[+]` | Completed |
| `[~]` | In progress; zero or one general row across the active ledger |
| `[!]` | A current unresolved blocker |
| `[X]` | Cancelled |
| `[-]` | Closed historical evidence; never retried and non-blocking for its accepted successor |

The new `[-]` marker is additive: the five earlier markers keep their existing
meanings. Use it only for a consumed failed attempt or superseded row retained
for audit, and name the accepted successor in the row notes. Before invoking an
operational launcher, its exact authorized operation row must be `[~]`; that
marker records the selection but does not grant external-mutation authority.

### Keep long-term memory without growing the active plan

The memory bank is the working context, not a lifetime log. Keep current facts,
active plans, and applicable learning there; preserve retired evidence under
`tabilet/docs/history/` and consult it on demand. This prevents accumulated history
from growing the startup read indefinitely. It does not impose a hard token or
file-size cap: genuinely active work and relevant knowledge can still grow.

**What triggers it?** `memory-bank-init` establishes the convention in newly
initialized projects. During normal work, `memory-bank-next` and
`memory-bank-goal` follow the project's milestone-closing procedure: after the
bounded review gate, verification, knowledge consolidation, and downstream
reconciliation pass, the agent retires the milestone. The same procedure can
be followed without skills. “Automatic” means part of that agent workflow,
not a background process, timer, or plugin-install side effect.

Retirement is milestone-level, not row-level. Individual completed, cancelled,
or closed-historical rows stay in their active status file until the whole
milestone qualifies. Unresolved work or missing closure evidence keeps it
active; terminal markers alone do not prove acceptance. Retirement respects
the governing commit policy.

**What stays, and where does history go?** Paths below are relative to the
project root. History files are created only when needed.

| Content | Location and lifetime |
|---|---|
| Current product/domain facts, architecture, and stack | Their existing files in `tabilet/memory-bank/`; keep them current. |
| Applicable learning, rationale, and evidence | `tabilet/memory-bank/lessons.md`; curate and merge duplicates, not one entry per milestone or session. |
| Active specifications, task rows, and later candidate directions | `tabilet/memory-bank/milestone.md` and active `status-<LANE><NN>.md` files. Retired specifications and index rows leave this active plan; one history-index link remains. |
| Complete retired milestone specification and status document | `tabilet/docs/history/status-<LANE><NN>.md`; frozen literal Markdown with provenance, verification, review iterations, and consolidation links. |
| Retired IDs, outcomes, and record links | `tabilet/docs/history/index.md`; also links the knowledge journal when present. |
| Superseded facts and lessons | `tabilet/docs/history/knowledge.md`; append-only old wording, source, reason, supporting evidence, and replacement reference (or why there is none). |

**Knowledge has its own trigger.** During ordinary maintenance, update relevant
lessons when reusable learning is supported by evidence. Before materially
replacing or removing obsolete knowledge from current memory, preserve it in
the knowledge journal. This applies outside milestone closure too. Routine
wording edits need no journal entry, and still-useful lessons stay active even
after their supporting milestone retires.

**Retirement is not a context archive.** `memory-bank-archive` creates optional
frozen repository baselines in `tabilet/docs/archive-<LANE><NN>.md`; it does not retire
milestones. Routine retirement needs no separate archive invocation or clean
snapshot commit. `memory-bank-reconcile` plans work from a new review and may
propose evidenced knowledge updates, but does not retire milestones.
`tabilet/evolution/` remains reserved for direction changes.

**How do you retrieve old memory?** Search current memory first, then the history
index by permanent ID or the knowledge journal by topic, and open only the
relevant records. Original paths in literal excerpts retain their original
document context. IDs remain reserved; historical rows are never retried.
Cancellation and supersession do not automatically satisfy completion
dependencies. Later corrections point back from new knowledge or remediation,
without rewriting frozen records. The Markdown evidence is readable without
Git; Git adds intermediate revisions when present.

**Existing projects need explicit adoption.** Update their project instructions
and, if used, adopt a compatible API runner before retirement. Separately request
cleanup of older closed milestones; missing closure evidence keeps them active.
Installing newer skills alone never merges project instructions or moves files.

See the complete
[retirement contract](template/tabilet/memory-bank/milestone.md#long-term-memory-and-retirement)
and the tutorial's
[worked example](docs/TUTORIAL.md#example-a-milestone-closes-and-a-lesson-survives).
For when to invoke each skill, see [skill use cases](docs/USE_CASES.md), especially
[automatic retirement](docs/USE_CASES.md#6-automatic-retirement-during-normal-work)
and [explicit successor snapshots](docs/USE_CASES.md#7-explicitly-snapshot-a-materially-changed-system).

### Upgrade an existing project

Use `memory-bank-upgrade` after updating the installed skills. It compares an
existing project's rules with its bundled template, shows a complete merge
proposal, and applies only approved changes. It preserves plans, local policies,
task states, permanent IDs, review counters, and frozen history. An already
compatible project is a no-op; older milestones are not retired by the upgrade.

Invoke `/memory-bank:memory-bank-upgrade` in Claude Code,
`$memory-bank:memory-bank-upgrade` in Codex, or `/memory-bank-upgrade` in DSH.
Use Web for the proposal and approval; a headless continuation requires the
exact approved proposal and stops for missing decisions or capabilities.
The skill carries a complete reference template, so no repository checkout or
network download is needed after installation. Its assets are examples and
contracts, never permission to overwrite project content. The manual equivalent
is:

1. Update the [installed skills](#install-the-seven-skills), preserving their
   supporting resources. If used, update the separately installed
   [API runner](docs/EXECUTION.md) before adopting retirement.
2. Compare the project's instructions with `template/AGENTS.md`, the review and
   retirement rules in `template/tabilet/memory-bank/milestone.md`, the status contract,
   and `template/tabilet/memory-bank/lessons.md`. Inventory active and retired IDs,
   frozen archives, custom rules, verification commands, and any review counter.
3. Request a file-by-file proposal for merging the applicable rules. Preserve
   project facts, existing task states, permanent IDs, historical evidence,
   local policies, and the persisted review count. Keep the optional project
   `tabilet/GOAL.md` unless its replacement is explicitly included in that proposal.
4. After approval, apply the scoped merges and verify links, status tables,
   protocol compatibility, and the project's required checks. Do not copy
   template placeholders over live content or rerun initialization.
5. Request retirement of older closed milestones separately. Retain active
   sources when verification, review, consolidation, or downstream evidence is
   missing. Create history files only when there is evidence to preserve.

An ordinary-language request can start this review: “Use memory-bank-upgrade
to compare this project's rules with the bundled contract. Preserve our
plans, custom instructions, IDs, and history. Show the complete file actions
before writing.” This request does not authorize implementation tasks or commits.

### Run an ordered set of milestones

The workflow above advances one row at a time. To work through several
milestones in a defined order, [GOAL.md](template/tabilet/GOAL.md) is one protocol for
that: it reconciles dependencies before each milestone, reconciles the
milestones downstream of one that just closed, and stops rather than guessing
when a decision or authority is missing.

It is invoked, not ambient. Whatever your agent, the request that starts a run is
the same block, and it names the file, the order, and the commit policy:

```text
Using tabilet/GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

When `memory-bank-init` creates the active horizon, or `memory-bank-reconcile`
changes it after a new review, either skill writes the complete proposed request
to `tabilet/memory-bank/suggested.txt` when the project has a compatible `tabilet/GOAL.md`.
Treat that file as a launch suggestion, not a second roadmap: reconcile it
against `milestone.md` and the current status files, then delete it after launch
or whenever it becomes stale. Without a compatible protocol they omit this file
and leave one-row execution available. To reference an existing suggestion directly:

```text
Using tabilet/GOAL.md, reconcile tabilet/memory-bank/suggested.txt against the current memory bank, then execute the resolved loop.
COMMIT_POLICY: task
```

You can paste that block into any agent as an ordinary request. If you installed
the plugin, its goal skill supplies the same protocol and commit policy:

```text
/memory-bank:memory-bank-goal M01 -> S01 -> A01?   # Claude Code plugin
$memory-bank:memory-bank-goal M01 -> S01 -> A01?   # Codex plugin
```

With no arguments, the skill prefers a valid `suggested.txt`, shows the complete
resolved request for confirmation, and falls back to deriving the order from
`milestone.md` when the file is absent or stale.

Plain-file installations use `/memory-bank-goal` in Claude Code and
`$memory-bank-goal` in Codex. Plain English remains valid everywhere.

#### Keep a long run active

Both [Claude Code](https://code.claude.com/docs/en/goal) and
[Codex](https://learn.chatgpt.com/use-cases/follow-goals) provide a built-in
`/goal` for keeping a durable objective active. It is an optional persistence
layer, not the memory-bank protocol: `/goal` keeps the run alive, while
`tabilet/GOAL.md` defines how milestones are reconciled, implemented, reviewed, and
closed. Give the built-in command the complete protocol request and a measurable
completion condition together:

```text
/goal Using tabilet/GOAL.md, reconcile tabilet/memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and every milestone's documented verification passes.
```

In either agent, run `/goal` with no arguments to show its status and
`/goal clear` to stop it. Codex additionally supports `/goal pause` and
`/goal resume`.
If `/goal` is not listed in Codex, enable it with `codex features enable goals`.

Built-in `/goal` does not discover this repository's protocol automatically;
the objective must name `tabilet/GOAL.md`, as in the example above. You can instead
invoke `memory-bank-goal` directly using the Claude Code or Codex forms shown
above; that is the portable non-persistent launcher. [Codex custom
prompts](https://learn.chatgpt.com/docs/custom-prompts) are deprecated in favor
of skills, so this repository does not install or recommend a separate
`goal.md` prompt.

#### Any other agent

Paste the block as an ordinary request. Naming the file is all the protocol
needs; nothing depends on a slash command existing.

`COMMIT_POLICY` matters, and a goal run is a deliberate exception to the usual
rule. For the length of the run it is the entire commit rule: `AGENTS.md` may say
each status row is a commit unit, but `COMMIT_POLICY: none`, which is the
protocol's default, means no commits at all. That is correct behavior rather
than a conflict. Say `task` when you want the usual per-row commits. Precedence runs
request, then `tabilet/GOAL.md`, then `AGENTS.md`, and only for commits, and only inside
the run.

A trailing `?` marks a milestone conditional: it is skipped, not cancelled, when
its documented trigger is absent. Use it only for work conditionally required to
reach the active outcome; discretionary later work stays an unnumbered candidate
direction instead.

`tabilet/GOAL.md` carries no project-specific paths, lane letters, or commands. It
discovers those from `AGENTS.md` and the memory bank, so the same file works
unchanged in every project that copies it.

Nothing requires you to use it. Bring your own protocol, or none at all, and
the memory bank behaves exactly the same. `tabilet/GOAL.md` is offered because writing
one of these is fiddly,
not because anything here depends on it. If you have your own, point the two
`tabilet/GOAL.md` mentions at it instead, or delete them. They are in `AGENTS.md` and
`tabilet/memory-bank/milestone.md`.

<a id="install-the-five-skills"></a>
<a id="install-the-six-skills"></a>

## Install The Seven Skills

Version 2.0.0 publishes all seven skills under the new project layout. Existing projects
adopt its requested-change procedure through an approved Upgrade proposal.

Also optional. Everything above works by typing plain sentences; these just make
the seven moments repeatable, and carry the full instruction rather than your
paraphrase of it.

| Skill | When |
|---|---|
| `memory-bank-archive` | Before init when a large existing package needs a commit-anchored context map; later only when a material context change needs a successor snapshot. |
| `memory-bank-init` | Once, on a project with no initialized milestone/status harness. It interviews you, proposes a breakdown, then writes the files. |
| `memory-bank-upgrade` | After updating skills, review and approve merges of new workflow rules into an existing project. |
| `memory-bank-propose` | When an initialized project needs a requested feature, candidate promotion, or change to future direction. |
| `memory-bank-reconcile` | Whenever a new review arrives after initialization. It validates findings and updates the approved plan without implementing them. |
| `memory-bank-next` | Execute or resume one row, verify, and commit under the governing policy. |
| `memory-bank-goal` | When you want several milestones run in order. |

`memory-bank-init` is the one that changes the experience most: it maps one
delivery boundary as a design tree, asks each dependency-ready frontier as a
numbered round with recommended answers, and looks up repository facts instead
of asking you for them. It writes nothing until you approve both the active
horizon and every file action. You never see a bracketed placeholder, because
the memory bank arrives filled in. *(Interview technique adapted from the `grilling` skill in
[mattpocock/skills](https://github.com/mattpocock/skills), MIT.)*

Claude Code and Codex read the same `SKILL.md` format **and the same manifest**.
DSH loads the same complete directories through its filesystem skill loader;
see [DSH installation](#dsh-installation).

**Claude Code:**

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

**Codex** has its own plugin system, and reads
`.claude-plugin/plugin.json` as a fallback, so the same repository works:

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

Codex requires the `@marketplace` qualifier when a plugin name is not unique
across your configured marketplaces, so `memory-bank@tabilet` is the form worth
learning. `codex plugin marketplace upgrade` refreshes the snapshot when a new
version ships.

**Plugin installations are namespaced.** This follows current [Claude Code
skill namespacing](https://code.claude.com/docs/en/slash-commands) and [Codex
skill invocation](https://developers.openai.com/plugins/build/skills):

| Agent | Archive | Init | Propose change | Upgrade rules | Reconcile review | Next row | Ordered milestones |
|---|---|---|---|---|---|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-archive` | `/memory-bank:memory-bank-init` | `/memory-bank:memory-bank-propose` | `/memory-bank:memory-bank-upgrade` | `/memory-bank:memory-bank-reconcile` | `/memory-bank:memory-bank-next` | `/memory-bank:memory-bank-goal` |
| Codex plugin | `$memory-bank:memory-bank-archive` | `$memory-bank:memory-bank-init` | `$memory-bank:memory-bank-propose` | `$memory-bank:memory-bank-upgrade` | `$memory-bank:memory-bank-reconcile` | `$memory-bank:memory-bank-next` | `$memory-bank:memory-bank-goal` |
| DSH filesystem | `/memory-bank-archive` | `/memory-bank-init` | `/memory-bank-propose` | `/memory-bank-upgrade` | `/memory-bank-reconcile` | `/memory-bank-next` | `/memory-bank-goal` |

Plain English also works in both agents.

**As plain files you own** rather than a managed plugin, install into each
agent's personal skill directory:

```bash
mkdir -p ~/.agents/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.agents/skills 'skills-main/skills'

# Claude Code alternative
mkdir -p ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.claude/skills 'skills-main/skills'
```

Plain-file skills are unnamespaced: `/memory-bank-archive` and
`/memory-bank-init` in Claude Code, `$memory-bank-archive` and
`$memory-bank-init` in Codex, with the same pattern for `upgrade`, `propose`, `reconcile`, `next`, and
`goal`.

To pin a published version, replace `refs/heads/main` with its tag path and
match the archive's directory name. For tag `v1.3.0`, those are
`refs/tags/v1.3.0` and `skills-1.3.0` respectively: the extracted directory omits
the tag's leading `v`. A tag download is available only after publication.

The plugin installs the *generator*, not the output. What it writes into your
project is yours, is never updated from here, and survives uninstalling it.

The skill is deliberately not named `goal`: Claude Code and Codex reserve
built-in `/goal` for keeping a durable objective active, while
`memory-bank-goal` supplies this repository's multi-milestone protocol. The two
work together; see [Run an ordered set of
milestones](#run-an-ordered-set-of-milestones).

### DSH installation

The optional [tabilet-skills companion](https://github.com/tabilet/tabilet-skills)
packages the seven v2.0.0 skills and adds a native
Memory Bank sidebar with
task, memory, acceptance, and history views. It prepares workflow requests for
your conversation; the user reviews and sends them. It makes no model calls or
project writes while browsing or preparing requests. The companion targets
DSH **0.1.5-rc.2**, Linux, and Node **24.14.1**. See
[companion installation and release status](docs/DSH.md#install-the-dsh-companion).
The direct filesystem route below remains available independently.

DSH provides tools, permissions, and persistent sessions; memory-bank defines
approved engineering work, verification, review, and project history. The
tested configuration is **DSH 0.1.5-rc.1 on Linux with Node 24**, in **Web** and
the **headless** one-shot profile. Credential-free integration checks and the
eight bounded live workflow scenario groups reached accepted final states after
the documented corrections. The
[observed test results](docs/DSH.md#acceptance-evidence) record the exact scope,
corrections, cost, and limitations; loader tests alone do not prove acceptance.

Copy the complete directories from your chosen release checkout's `skills/`
into `$DSH_HOME/skills`, defaulting to `~/.dsh/skills`, using the
[preserving installation commands](docs/DSH.md#install-the-six-bundles). They
keep supporting references and init's bundled protocol, allow identical repeat
installation, and stop on differing existing content. `~/.agents/skills` is an
alternative; higher-priority duplicates can shadow an update. DSH uses its
existing filesystem loader, without a new plugin or installer CLI.

Follow [update or removal](docs/DSH.md#update-or-remove) to back up and replace
only the identified memory-bank bundles. Removal retains those bundles in a
backup and leaves project memory, credentials, and unrelated skills alone.
Installing updated skills never migrates project instructions or history.
For a reproducible installation, use the `v2.0.0` tag. A marketplace install or
`main` download follows the repository's current published state.

Start `dsh web` from your project, confirm the workspace, and invoke
`/memory-bank-init`, `/memory-bank-archive`, `/memory-bank-propose`,
`/memory-bank-upgrade`, or `/memory-bank-reconcile` for
interviews and explicit approvals. Use `/memory-bank-next`, `/memory-bank-goal`,
or an ordinary-language request for execution. For pre-approved work, use
`dsh --profile headless 'complete authorized request'`; the
[headless examples](docs/DSH.md#headless-workflow) include scope and stop rules.
A process can exit with a question or unfinished milestone: exit status, native
todos, and native goal state never prove acceptance. Keep one execution owner
for the active ledger. See [the DSH tutorial route](docs/TUTORIAL.md#dsh-route)
and [detailed integration guide](docs/DSH.md) for prerequisites, permissions,
resource loading, goal continuation, and verification.

### If you already use `/grill-me`

`/grill-me` and `/grilling` from
[mattpocock/skills](https://github.com/mattpocock/skills) end where they mean
to: *"Do not act on it until I confirm we have reached a shared understanding."*
Stopping there is the right call for a general-purpose interview, and it is why
that skill works on anything.

But when the session closes, the understanding closes with it. Nothing is on
disk, nothing an agent can pick up tomorrow, and nothing to execute against.

`memory-bank-init` is the same interview discipline pointed at a persistent
artifact. It asks dependency-independent decisions together in frontier rounds,
each with a recommended answer, and looks facts up rather than asking about
them. Ask for one-at-a-time pacing if that is easier. Run it **in the same
session, right after the grill**:

```text
/grill-me                              # explore the design; no files written
/memory-bank:memory-bank-init          # Claude Code plugin
$memory-bank:memory-bank-init          # Codex plugin
```

It will not re-ask what you already settled. "Look up facts, ask about
decisions" applies to the conversation as much as to the repository, so a grill
you have just finished makes for a short interview, mostly confirming a
proposed breakdown of lanes and milestones.

What the memory bank keeps after the session ends:

| | After `/grill-me` | After `memory-bank-init` |
|---|---|---|
| Where the decisions live | The conversation | `product.md`, `architecture.md`, `tech-stack.md` |
| Tomorrow's agent | Starts cold | Reads `AGENTS.md` and knows |
| Next action | You decide | The next `` `[ ]` `` row |
| Executing it | — | `memory-bank-next`, or `memory-bank-goal` for a set |

The two are complements, not rivals. Keep `/grill-me` for decisions that produce
no project, such as an architecture argument, a hiring plan, or a talk outline. Reach for
`memory-bank-init` when the thing you are grilling about is a codebase that has
to still know what it is next week.

## Install The API Harness

This section is optional. Everything above works without it, because the harness
only adds an unattended loop that drives an agent through the API instead of you
typing into one. Skip it if Codex, Claude Code, or another agent already does
that for you.

The API harness is account-level because it can drive any project that follows
this memory-bank shape. It needs Python 3 and nothing else.

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

The commands below call `tackle-memory-bank-api-loop` by name, which requires
`~/.local/bin` on your `PATH`. If `command -v tackle-memory-bank-api-loop`
prints nothing, add this line to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

An actionable run gives model-generated commands an unsandboxed shell on the
host, so the harness refuses to start one until you explicitly set
`ALLOW_UNSANDBOXED_SHELL=1` or pass `--allow-unsandboxed-shell`. This is an
acknowledgment, not isolation: commands can still read host files, inspect other
processes, and use the network. Run the harness inside a disposable sandbox and
against a repository you can restore.

Shell commands receive a minimal environment. Provider credential variables are
not copied into it; use `TOOL_ENV_ALLOW=NAME,OTHER_NAME` to forward additional
project variables deliberately. This reduces accidental disclosure but does not
make the host shell safe. `ALLOW_DANGEROUS_COMMANDS=1` only disables a short
command denylist, which is a guardrail and can be bypassed.

Run one row:

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

Run a loop:

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

Use an OpenAI-compatible provider:

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.6 \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Use a local OpenAI-compatible server:

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Use Anthropic (Claude) instead of the OpenAI-compatible path:

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

The harness embeds the task instruction in its API prompt. It does not call the
Codex CLI, and it does not require the external prompt file at runtime. The
prompt file remains in this repository as the required human-readable duplicate
of the embedded instruction; it is not installed into a Codex prompt directory.
The same JSON
command protocol drives the agent loop regardless of which provider is used.

Model names change over time. These examples use the current `gpt-5.6` family
alias and `claude-opus-5`; consult the official [OpenAI model
catalog](https://developers.openai.com/api/docs/models) and [Anthropic model
catalog](https://platform.claude.com/docs/en/about-claude/models/overview) when
selecting a model for a real run.

### First run

A run starts by printing the repository, provider, model, and API endpoint, then
works one row:

```text
Repo: /path/to/your-project
Provider: anthropic
Model: claude-opus-5
API: https://api.anthropic.com/v1/messages
Run 1/1: asking LLM to tackle one row.
  LLM turn 1/60
  shell: sed -n '1,120p' AGENTS.md  # Read the bootstrap guide.
```

The harness stops early on purpose, and its exit code says why. `3` through `7`
are normal stopping conditions rather than failures. For example, `4` means the
worktree was dirty before the run, and `6` means the agent finished without
committing. `11` means active and retired status state is missing or invalid;
check filenames and the history index. A valid project with all milestones
retired exits `0`. The full table is in
[Execution Harness](docs/EXECUTION.md#exit-codes).

## Optional SQLite audit and lookup

Markdown remains authoritative. The optional `tabilet-audit` toolkit records
workflow evidence in an external SQLite database and builds a disposable index
of active milestones/tasks, retired history, evolution, and context archives.
Indexing does not change project Markdown or require new task IDs.

See [installation, commands, capture policy, and recovery](docs/sqlite.md#install-and-use-the-optional-toolkit).
The API runner records enabled runs; interactive skills can use the same optional
CLI. Exact chat capture requires text supplied by the host. Default audit capture
stores metadata; the lookup index separately contains current Markdown text.
Installing skills alone never creates a database. Existing
snapshot evidence stays readable; new full-file snapshot capture is deferred.

The optional `tabilet-audit explorer PROJECT --port 8000` serves a local
browser explorer bound to a loopback address. Overview summarizes active
milestones, history, archives, and evolution; Timeline groups goal children and
opens the recorded request, output, changes, and resolved current state; To-do
groups resume, ready, waiting, blocked, and review-required work with dependency
links. Filters and selected details stay in the URL. The explorer keeps recorded
evidence visible when it withholds recommendations, rechecks live source hashes,
and prepares follow-up text for copying only. It does not launch an agent, change
Markdown, or create task rows. From a remote server, use
`ssh -N -L 8000:127.0.0.1:8000 user@host` and browse to `http://localhost:8000/`.

## What The Harness Is

For normal project work, `tackle-memory-bank-api-loop` is an execution harness:
it repeatedly runs an agent against a repository, gives it shell access through a
JSON command protocol, and checks git state between runs. It requires the target
to be the git worktree root, requires history to advance without a rewrite, and
requires exactly one existing actionable row to become completed, blocked, or
closed historical in each run. Separate milestone-review commits are allowed
within that run. If one `[~]` row already exists, the harness requires the agent
to resume exactly it; more than one in-progress row stops before the API call.

A closing task may retire its milestone using the project's adopted contract.
The harness follows the row into its validated history record, checks that
earlier rows and notes survived, and rejects changes to previously retired
records. Valid all-retired projects exit `0`; missing or invalid status/history
state exits `11`. Historical rows never become actionable.

It discovers every `tabilet/memory-bank/status-<LANE><NN>.md` file, reports how many
actionable, in-progress, blocked, and closed-historical rows each lane holds,
and asks the agent to pick a row using the lane meanings and milestone priority.
A blocked row in one lane does
not stop work in the others; the loop stops for human review only when blocked
rows are all that remain.

It becomes part of a model eval harness only when you score outcomes across
models, prompts, pass rates, review findings, cost, latency, or regressions.

Read more:

- [Execution Harness](docs/EXECUTION.md)
- [Model Eval Harness](docs/MODEL_EVAL.md)

## Maintenance Rules

- Keep `AGENTS.md` short.
- Keep project `README.md` user-facing.
- Put long explanations in `docs/`.
- Put active truth in `tabilet/memory-bank/`.
- Put historical direction snapshots in `tabilet/evolution/`.
- Update memory in the same commit as the code or docs it describes.
- Add a new evolution version only for a real direction change.
- Delete duplicate docs once useful content has been merged.

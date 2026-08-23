# A Minimal Engineering Harness

Coding agents work better when a project can explain itself: what it is, what is
done, and what comes next. This repository gives you a small set of plain-text
files, mostly markdown, that do exactly that. You copy them into your project and
own them from that moment on.

Everything here is plain text, so `git` is the only tool you need. You can read
the files, edit them by hand, rename them, or delete them, and any agent that
reads markdown can work with them. An optional plugin will generate the files for
you, and an optional API runner will work through them unattended; both stay
outside your project.

`template/` goes into your project, and `harness/` goes into your home directory
if you want the API runner. Once the files are in place they belong to your
project, and your project stays independent of this repository. Six months from
now, the only files you are maintaining are still your own.

Five optional skills can do the mapping, copying, and filling for you; see
[Install The Five Skills](#install-the-five-skills). The files they write are
yours from the moment they appear, and they stay exactly as you leave them.

Your project ends up looking like this:

```text
your-project/
├── AGENTS.md              what an agent should read first
├── GOAL.md                optional multi-milestone protocol
├── memory-bank/           what is true now
│   ├── product.md         product scope, domain model, and non-goals
│   ├── architecture.md    layout, data flow, boundaries
│   ├── tech-stack.md      commands, dependencies, how you verify
│   ├── milestone.md       active milestones plus unnumbered later directions
│   ├── status-M01.md      one permanent file per active milestone
│   └── suggested.txt      optional active-horizon launch reference
├── docs/                  long-form reference
│   └── archive-A01.md     optional frozen existing-package context baseline
└── evolution/             versioned direction snapshots
    ├── prompt-v1.md       the initial direction
    └── result-v1.md       the state it produced
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

The memory bank needs `git` and nothing else. It is plain markdown, so the
everyday workflow needs no runtime: you tell an agent such as Codex or Claude
Code to tackle the next pending item, and it edits the files directly.

**Python 3 is only for the optional API harness**, the unattended loop described
in [Install The API Harness](#install-the-api-harness). It uses nothing but the
standard library, so there is nothing to install with `pip`. Skip it entirely if
you drive the memory bank through an agent you already use.

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
The Codex equivalent and plain-file installation are in
[Install The Five Skills](#install-the-five-skills).

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
- [template/GOAL.md](template/GOAL.md) — the multi-milestone execution protocol
- [template/memory-bank/product.md](template/memory-bank/product.md)
- [template/memory-bank/architecture.md](template/memory-bank/architecture.md)
- [template/memory-bank/tech-stack.md](template/memory-bank/tech-stack.md)
- [template/memory-bank/milestone.md](template/memory-bank/milestone.md)
- [template/memory-bank/status-M01.md](template/memory-bank/status-M01.md)
- [template/evolution/prompt-v1.md](template/evolution/prompt-v1.md)
- [template/evolution/result-v1.md](template/evolution/result-v1.md)

The optional API runner and its human-readable instruction copy live in
[harness/](harness/):

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

The five skills are in [skills/](skills/). Claude Code and Codex read the same
`SKILL.md` format, so there is one source per skill:

- [memory-bank-archive](skills/memory-bank-archive/SKILL.md) — snapshot a large
  existing package into frozen, evidence-backed context archives
- [memory-bank-init](skills/memory-bank-init/SKILL.md) — interview a
  project into existence, then write its memory bank
- [memory-bank-reconcile](skills/memory-bank-reconcile/SKILL.md) — validate a
  new review against current code and reconcile the approved work plan
- [memory-bank-next](skills/memory-bank-next/SKILL.md) — tackle one row,
  verify it, commit it
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md) — run an ordered
  set of milestones

Unlike the copyable template, `memory-bank-init` can derive project-specific
goal input and `memory-bank-reconcile` can refresh it after a new review changes
the active graph. When the project contains an approved compatible `GOAL.md`,
they write `memory-bank/suggested.txt` with a proposed `STATUS_ORDER`,
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

`memory-bank/product.md` starts as `[project-name] is [one or two sentences
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

`memory-bank/milestone.md` is the file that decides how everything else is
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

Then `memory-bank/status-S01.md` carries the rows for that milestone:

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules still open. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
```

**The backticks around each marker are required by the included API harness.**
It matches
`` `[ ]` ``, not `[ ]`. A row written `| Item | [ ] | Notes |` is silently
ignored: the harness reports "No actionable memory-bank rows remain" and exits
successfully, as though the work were finished.

## Set Up A New Project

If you installed [the five skills](#install-the-five-skills),
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

1. `memory-bank/product.md`: define product scope, canonical domain terminology,
   concept relationships and business invariants, and non-goals.
2. `memory-bank/architecture.md`: define layout, data flow, and boundaries.
3. `memory-bank/tech-stack.md`: define commands, dependencies, and harnesses.
4. `memory-bank/milestone.md`: define the status ID lanes (see
   [Status ID lanes](#status-id-lanes)) and the first milestone.
5. `memory-bank/status-M01.md`: define the first milestone's actionable rows.
   See [what a filled-in memory bank looks
   like](#what-a-filled-in-memory-bank-looks-like), and note that the marker
   backticks matter.
6. `evolution/prompt-v1.md`: record the initial direction.
7. `evolution/result-v1.md`: record the current starting state.
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
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status-M01.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

Example prompt:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, define the
status ID lanes in memory-bank/milestone.md, and make memory-bank/status-M01.md
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
frozen context dossiers such as `docs/archive-C01.md`, records the full baseline
commit, and creates or refreshes the current `memory-bank/product.md` and
`memory-bank/architecture.md` summaries.

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
5. Convert duplicated roadmap/status material into `memory-bank/milestone.md`
   and one `memory-bank/status-<LANE><NN>.md` file per milestone.
6. Keep known gaps visible in the matching status file instead of hiding them.

### With Help Of An AI Agent

For an existing project, the agent can do the inventory and first memory-bank
draft. This works best when the project already has useful README, docs, package
comments, tests, or CI files.

Warning: copying these sample files into an existing project can overwrite
existing `AGENTS.md`, `memory-bank/`, or `evolution/` files. Commit first, make a
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
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in the matching
memory-bank/status-<LANE><NN>.md file. Do not invent product direction that is
not supported by the existing project.
```

The agent should:

1. Inventory existing markdown and source layout.
2. Identify commands, dependencies, tests, and harnesses.
3. Fill in the memory bank from current project reality.
4. Move or summarize long-form references into `docs/`.
5. Keep `README.md` simple and user-facing.
6. Leave unresolved gaps as pending or blocked rows in the matching
   `memory-bank/status-<LANE><NN>.md` file.

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
whole active horizon when a compatible `GOAL.md` exists. It does not implement,
commit, or launch the fixes; use `memory-bank-next` or `memory-bank-goal` after
approving the reconciled plan.

## Use The Memory Bank

There are four ways to execute against the memory bank, and all of them are
optional, because the memory bank is plain markdown and works on its own:

| Way to execute | Scope | Needs |
|---|---|---|
| Type a request to your agent | One row at a time, you in the loop | Nothing |
| [`memory-bank-next`](#install-the-five-skills) | The same, with the full instruction rather than your paraphrase | The optional skills |
| [The API harness](#install-the-api-harness) | One row per run, unattended | Python 3 |
| [A goal loop](#run-an-ordered-set-of-milestones) | Several milestones in order | `GOAL.md` and an agent request or optional skill |

With an agent such as Codex or Claude Code, the user-facing workflow can be as
simple as typing:

```text
tackle next pending item in memory bank
```

The agent should find the next actionable row in the current milestone's
`memory-bank/status-<LANE><NN>.md` file,
complete that task, run the required verification, update the memory bank, and
make a scoped git commit. If that row is the last open item in a milestone, the
agent should run a deep code review of the milestone, run the milestone review
from `memory-bank/milestone.md`, complete required verification, and commit any
review changes before moving on. Do not create an extra commit when review
changes nothing. The review-fix gate reviews the whole milestone again after
every [P1/P2-or-higher](template/memory-bank/milestone.md#review-finding-severity)
fix and requires a clean pass within 10 iterations; if the tenth review still
finds a blocking issue, the milestone stays incomplete.
During that review it should also decide whether `evolution/` needs a new version
because the product direction, architecture boundary, milestone target, or
public/private contract direction materially changed.

Before you trust any of this, give the agent something to verify against. Fill
the **Execution harnesses** table in `memory-bank/tech-stack.md` with the command
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
7. Keep one `memory-bank/status-<LANE><NN>.md` file for each milestone.
8. If a milestone becomes complete, run a deep code review and the milestone
   review procedure in `memory-bank/milestone.md`.
9. After review and required verification pass, commit any review changes; do
   not create an empty or redundant milestone commit.
10. Check `evolution/` and add a new version only when the review finds a real
   direction, boundary, milestone, or contract change.

### Status ID lanes

Status files are named `memory-bank/status-<LANE><NN>.md`. The lane letter
classifies the work and the number is zero-padded to two digits, so accounting
milestones become `status-A01.md` and `status-A02.md` while shopping milestones
become `status-S01.md`. `M` is the default lane for work that does not classify
into a domain lane. A lane holds at most 99 files; when a lane fills up, open a
new letter instead of adding a third digit. `memory-bank/milestone.md` records
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
| `[ ]` | Pending |
| `[+]` | Completed |
| `[~]` | In progress |
| `[!]` | Blocked |
| `[X]` | Cancelled |

### Run an ordered set of milestones

The workflow above advances one row at a time. To work through several
milestones in a defined order, [GOAL.md](template/GOAL.md) is one protocol for
that: it reconciles dependencies before each milestone, reconciles the
milestones downstream of one that just closed, and stops rather than guessing
when a decision or authority is missing.

It is invoked, not ambient. Whatever your agent, the request that starts a run is
the same block, and it names the file, the order, and the commit policy:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

When `memory-bank-init` creates the active horizon, or `memory-bank-reconcile`
changes it after a new review, either skill writes the complete proposed request
to `memory-bank/suggested.txt` when the project has a compatible `GOAL.md`.
Treat that file as a launch suggestion, not a second roadmap: reconcile it
against `milestone.md` and the current status files, then delete it after launch
or whenever it becomes stale. Without a compatible protocol they omit this file
and leave one-row execution available. To reference an existing suggestion directly:

```text
Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop.
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
`GOAL.md` defines how milestones are reconciled, implemented, reviewed, and
closed. Give the built-in command the complete protocol request and a measurable
completion condition together:

```text
/goal Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and every milestone's documented verification passes.
```

In either agent, run `/goal` with no arguments to show its status and
`/goal clear` to stop it. Codex additionally supports `/goal pause` and
`/goal resume`.
If `/goal` is not listed in Codex, enable it with `codex features enable goals`.

Built-in `/goal` does not discover this repository's protocol automatically;
the objective must name `GOAL.md`, as in the example above. You can instead
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
request, then `GOAL.md`, then `AGENTS.md`, and only for commits, and only inside
the run.

A trailing `?` marks a milestone conditional: it is skipped, not cancelled, when
its documented trigger is absent. Use it only for work conditionally required to
reach the active outcome; discretionary later work stays an unnumbered candidate
direction instead.

`GOAL.md` carries no project-specific paths, lane letters, or commands. It
discovers those from `AGENTS.md` and the memory bank, so the same file works
unchanged in every project that copies it.

Nothing requires you to use it. Bring your own protocol, or none at all, and
the memory bank behaves exactly the same. `GOAL.md` is offered because writing
one of these is fiddly,
not because anything here depends on it. If you have your own, point the two
`GOAL.md` mentions at it instead, or delete them. They are in `AGENTS.md` and
`memory-bank/milestone.md`.

## Install The Five Skills

Also optional. Everything above works by typing plain sentences; these just make
the five moments repeatable, and carry the full instruction rather than your
paraphrase of it.

| Skill | When |
|---|---|
| `memory-bank-archive` | Before init when a large existing package needs a commit-anchored context map; later only when a material context change needs a successor snapshot. |
| `memory-bank-init` | Once, on a project with no initialized milestone/status harness. It interviews you, proposes a breakdown, then writes the files. |
| `memory-bank-reconcile` | Whenever a new review arrives after initialization. It validates findings and updates the approved plan without implementing them. |
| `memory-bank-next` | Every day. Tackle one row, verify, commit. |
| `memory-bank-goal` | When you want several milestones run in order. |

`memory-bank-init` is the one that changes the experience most: it maps one
delivery boundary as a design tree, asks each dependency-ready frontier as a
numbered round with recommended answers, and looks up repository facts instead
of asking you for them. It writes nothing until you approve both the active
horizon and every file action. You never see a bracketed placeholder, because
the memory bank arrives filled in. *(Interview technique adapted from the `grilling` skill in
[mattpocock/skills](https://github.com/mattpocock/skills), MIT.)*

Both agents read the same `SKILL.md` format **and the same manifest**, so there
is one source per command and one release to install.

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

| Agent | Archive | Init | Reconcile review | Next row | Ordered milestones |
|---|---|---|---|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-archive` | `/memory-bank:memory-bank-init` | `/memory-bank:memory-bank-reconcile` | `/memory-bank:memory-bank-next` | `/memory-bank:memory-bank-goal` |
| Codex plugin | `$memory-bank:memory-bank-archive` | `$memory-bank:memory-bank-init` | `$memory-bank:memory-bank-reconcile` | `$memory-bank:memory-bank-next` | `$memory-bank:memory-bank-goal` |

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
`$memory-bank-init` in Codex, with the same pattern for `reconcile`, `next`, and
`goal`.

To pin a version, swap `refs/heads/main` for `refs/tags/<version>` and change
`skills-main` to `skills-<version>` to match the directory inside that tarball.

The plugin installs the *generator*, not the output. What it writes into your
project is yours, is never updated from here, and survives uninstalling it.

The skill is deliberately not named `goal`: Claude Code and Codex reserve
built-in `/goal` for keeping a durable objective active, while
`memory-bank-goal` supplies this repository's multi-milestone protocol. The two
work together; see [Run an ordered set of
milestones](#run-an-ordered-set-of-milestones).

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
committing. `11` means it found no `status-<LANE><NN>.md` files, which usually
means the memory bank has not been filled in yet. The full table is in
[Execution Harness](docs/EXECUTION.md#exit-codes).

## What The Harness Is

For normal project work, `tackle-memory-bank-api-loop` is an execution harness:
it repeatedly runs an agent against a repository, gives it shell access through a
JSON command protocol, and checks git state between runs. It requires the target
to be the git worktree root, requires history to advance without a rewrite, and
requires exactly one existing actionable row to become completed or blocked in
each run. Separate milestone-review commits are allowed within that run.

It discovers every `memory-bank/status-<LANE><NN>.md` file, reports how many
actionable and blocked rows each lane holds, and asks the agent to pick a row
using the lane meanings and milestone priority. A blocked row in one lane does
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
- Put active truth in `memory-bank/`.
- Put historical direction snapshots in `evolution/`.
- Update memory in the same commit as the code or docs it describes.
- Add a new evolution version only for a real direction change.
- Delete duplicate docs once useful content has been merged.

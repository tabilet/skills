# A Minimal Engineering Harness

Coding agents work better when a project can explain itself — what it is, what's
done, what's next. The usual way to get that is to adopt a system: a CLI, a
scaffold, a set of slash commands, a folder of generated artifacts. Six months
later you are maintaining that system's files as much as your own code, and your
project lives inside its conventions rather than yours.

This is the opposite bet. Five or six markdown files, copied into your project,
owned outright by you. No CLI to install, no vocabulary to learn, nothing
mandatory. Delete any of it the day it stops earning its place.

**What you end up with is yours.** This repository is a starting point you copy
*out* of — `template/` into your project, `harness/` optionally into your home
directory. Afterwards your project has no dependency on this repository and no
link back to it.

Three optional slash commands can do the copying and the filling for you — see
[Install The Three Commands](#install-the-three-commands). They change nothing
about the bet above: they *generate* files you then own outright, they never
update them afterwards, and uninstalling them leaves your project untouched.

Your project ends up looking like this:

```text
your-project/
├── AGENTS.md              what an agent should read first
├── memory-bank/           what is true now
│   ├── product.md         what this is, and is not
│   ├── architecture.md    layout, data flow, boundaries
│   ├── tech-stack.md      commands, dependencies, how you verify
│   ├── milestone.md       milestones and their acceptance criteria
│   └── status-M01.md      one file per milestone, one row per task
└── evolution/             why the direction changed, when it did
```

The term *memory bank* was popularised by [Cline](https://docs.cline.bot/best-practices/memory-bank); this is a different
implementation of the same idea, in plain files with no runtime.

Throughout, **harness** means a repeatable command that proves something works —
your test suite, a CI job, a script. Your project defines its own in
`tech-stack.md`. This repository also ships one optional harness of its own, an
API loop that drives an agent through the memory bank unattended.

Language versions: [🇨🇳 中文](README_cn.md) · [🇯🇵 日本語](README_ja.md) ·
[🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md) ·
[🇪🇸 Español](README_es.md).

## Getting Started

**New to this?** [docs/TUTORIAL.md](docs/TUTORIAL.md) walks a toy project from
an empty directory to a first committed task in twenty minutes, using
`/memory-bank-init` to do the setup. The rest of this README is reference — the
tutorial is the guided path through it.

**To use the memory bank you need `git`, and nothing else.** The memory bank is
plain markdown, so the everyday workflow — telling an agent such as Codex or
Claude Code to tackle the next pending item — needs no runtime at all.

**Python 3 is only for the optional API harness**, the unattended loop described
in [Install The API Harness](#install-the-api-harness). It uses nothing but the
standard library, so there is nothing to install with `pip`. Skip it entirely if
you drive the memory bank through an agent you already use.

The existing-project instructions below also use
[ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) for the initial inventory.

**The quickest path needs no clone at all.** Install the three commands, then let
`/memory-bank-init` interview you and write the memory bank:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

Run `/memory-bank-init` in your project — empty or existing — and answer its
questions. The Codex equivalent and the plain-files option are in [Install The
Three Commands](#install-the-three-commands).

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

User-account-level sample files in [harness/](harness/), installed into your
home directory:

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

The three slash commands, in [skills/](skills/). Claude Code and
Codex read the same `SKILL.md` format, so there is one source per command:

- [memory-bank-init](skills/memory-bank-init/SKILL.md) — interview a
  project into existence, then write its memory bank
- [memory-bank-next](skills/memory-bank-next/SKILL.md) — tackle one row,
  verify it, commit it
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md) — run an ordered
  set of milestones

`.claude-plugin/` holds the manifests that let those install as a Claude Code
plugin. Nothing in `template/` is vendor-specific.

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
```

`memory-bank/milestone.md` is the file that decides how everything else is
organised — it names the lanes and what each one covers:

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

**The backticks around each marker are required.** The harness matches
`` `[ ]` ``, not `[ ]`. A row written `| Item | [ ] | Notes |` is silently
ignored: the harness reports "No actionable memory-bank rows remain" and exits
successfully, as though the work were finished.

## Set Up A New Project

If you installed [the three commands](#install-the-three-commands),
`/memory-bank-init` does everything in this section: it interviews you, proposes
lanes and milestones, waits for your approval, and then writes the files already
filled in. The two routes below are the same work done by hand.

### Manual

From a new project root:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Then edit the copied files in this order:

1. `memory-bank/product.md`: define what the project is and is not.
2. `memory-bank/architecture.md`: define layout, data flow, and boundaries.
3. `memory-bank/tech-stack.md`: define commands, dependencies, and harnesses.
4. `memory-bank/milestone.md`: define the status ID lanes (see
   [Status ID lanes](#status-id-lanes)) and the first milestone.
5. `memory-bank/status-M01.md`: define the first milestone's actionable rows.
   See [what a filled-in memory bank looks
   like](#what-a-filled-in-memory-bank-looks-like) — the marker backticks
   matter.
6. `evolution/prompt-v1.md`: record the initial direction.
7. `evolution/result-v1.md`: record the current starting state.
8. `AGENTS.md`: replace placeholders with project-specific commands and rules.

Keep `README.md` simple and user-facing. Put long-form references in `docs/`.

### Wiring up your agent

`AGENTS.md` is an [open cross-vendor standard](https://agents.md) stewarded by
the Agentic AI Foundation. Most coding agents read it with no setup at all —
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

`/memory-bank-init` handles this case too, and handles it better than a cold
prompt: it reads what the repository already states — README, tests, build and
CI files — and asks you only about the decisions those cannot reveal, usually
the non-goals, the boundaries, and the order of work.

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

## Use The Memory Bank

There are three ways to execute against the memory bank, and all of them are
optional — the memory bank is plain markdown and works on its own:

| Way to execute | Scope | Needs |
|---|---|---|
| Type a request to your agent | One row at a time, you in the loop | Nothing |
| [`/memory-bank-next`](#install-the-three-commands) | The same, with the full instruction rather than your paraphrase | The three commands |
| [The API harness](#install-the-api-harness) | One row per run, unattended | Python 3 |
| [A goal loop](#run-an-ordered-set-of-milestones) | Several milestones in order | A `/goal` command |

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
from `memory-bank/milestone.md`, complete required verification, and make a git
commit for the milestone changes before moving on. During that review it should
also decide whether `evolution/` needs a new version because the product
direction, architecture boundary, milestone target, or public/private contract
direction materially changed.

Before you trust any of this, give the agent something to verify against. Fill
the **Execution harnesses** table in `memory-bank/tech-stack.md` with the command
that proves your project works — `make test`, `npm test`, a script, whatever you
already run — and what passing it proves. A row should not reach `[+]` until that
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
9. After review and required verification pass, make a git commit for the
   milestone changes.
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

**Choosing lanes.** A lane is a long-lived track of work, not a milestone and
not a sprint. Classify by domain — the part of the product a change belongs to —
rather than by team, priority, or date, because domains outlive all three. Start
with `M` alone; split a letter out the first time a domain has enough work that
its rows would drown out everything else, or when it needs its own review
cadence. Two or three lanes is a normal steady state, and a project can run a
long time on one.

Under-splitting is cheap to fix: open a new letter and put new work there. Over-
splitting is not, because IDs are never reused or renamed once their file
exists — a lane you regret stays in the tree forever. When unsure, leave it in
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
the same block — it names the file, the order, and the commit policy:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

How you send that block differs, because `/goal` is not the same command in every
agent. Use the section for yours.

#### If you use Claude Code

`/goal` is built in, and it is **not** a way to start a task. It sets a stop
condition — "a goal Claude checks before stopping" — so the session keeps
working across turns instead of ending after one reply.

So it takes two messages. Send the block above as an ordinary message, then set
the condition that decides when the run is over:

```text
/goal every row in M01 and S01 is `[+]` and the required verification passes
```

`/goal active` shows the current condition and `/goal clear` ends it early. The
condition is capped at 4000 characters, needs a trusted workspace, and is
unavailable when hooks are disabled by settings or policy.

To keep the block itself reusable, save it as a project command — but not as
`.claude/commands/goal.md`, because the built-in owns that name. Call it
`.claude/commands/milestones.md` and invoke it as `/milestones`.

#### If you use Codex

There is no built-in `/goal`. Custom prompts are markdown files in
`~/.codex/prompts/`, invoked by filename, so you can create the command yourself
and have it take the order as an argument. Write `~/.codex/prompts/goal.md`:

```markdown
---
description: Execute an ordered set of milestones using GOAL.md.
argument-hint: M01 -> S01 -> A01?
---

Using GOAL.md, execute this loop.

STATUS_ORDER: $ARGUMENTS
COMMIT_POLICY: task
```

Then one message runs it:

```text
/goal M01 -> S01 -> A01?
```

This is the same mechanism as the shipped
[tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)
prompt, which installs to the same directory.

#### Any other agent

Paste the block as an ordinary request. Naming the file is all the protocol
needs; nothing depends on a slash command existing.

`COMMIT_POLICY` matters, and a goal run is a deliberate exception to the usual
rule. For the length of the run it is the entire commit rule: `AGENTS.md` may say
each status row is a commit unit, but `COMMIT_POLICY: none` — the protocol's
default — means no commits at all, and that is correct behavior rather than a
conflict. Say `task` when you want the usual per-row commits. Precedence runs
request, then `GOAL.md`, then `AGENTS.md`, and only for commits, and only inside
the run.

A trailing `?` marks a milestone conditional: it is skipped, not cancelled, when
its documented trigger is absent.

`GOAL.md` carries no project-specific paths, lane letters, or commands. It
discovers those from `AGENTS.md` and the memory bank, so the same file works
unchanged in every project that copies it.

Nothing requires you to use it. `/goal` is your agent's command, not this
harness's — bring your own protocol, or none at all, and the memory bank behaves
exactly the same. `GOAL.md` is offered because writing one of these is fiddly,
not because anything here depends on it. If you have your own, point the two
`GOAL.md` mentions — in `AGENTS.md` and `memory-bank/milestone.md` — at it, or
delete them.

## Install The Three Commands

Also optional. Everything above works by typing plain sentences; these just make
the three moments repeatable, and carry the full instruction rather than your
paraphrase of it.

| Command | When |
|---|---|
| `/memory-bank-init` | Once, on a project that has no `memory-bank/` yet. It interviews you, proposes a breakdown, then writes the files. |
| `/memory-bank-next` | Every day. Tackle one row, verify, commit. |
| `/memory-bank-goal` | When you want several milestones run in order. |

`/memory-bank-init` is the one that changes the experience most: it asks one
question at a time with a recommended answer attached, looks up anything it can
read from the repository instead of asking, and writes nothing until you approve
the breakdown. You never see a bracketed placeholder — the memory bank arrives
filled in. *(Interview technique adapted from the `grilling` skill in
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

**How you invoke them differs.** Claude Code registers them as slash commands —
`/memory-bank-init`. Codex registers them as skills reached by name, so ask for
them without a slash: *"use the memory-bank-init skill"*. Plain English works in
both, which is what the memory bank is built around anyway.

**Either agent, as plain files you own** rather than a managed plugin:

```bash
mkdir -p ~/.codex/skills            # or ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.codex/skills 'skills-main/skills'
```

To pin a version, swap `refs/heads/main` for `refs/tags/<version>` and change
`skills-main` to `skills-<version>` to match the directory inside that tarball.

The plugin installs the *generator*, not the output. What it writes into your
project is yours, is never updated from here, and survives uninstalling it.

The skill is deliberately not named `goal`: Claude Code has a built-in `/goal`
that sets a stop condition, which is a different thing. The two work together —
see [Run an ordered set of
milestones](#run-an-ordered-set-of-milestones).

### If you already use `/grill-me`

`/grill-me` and `/grilling` from
[mattpocock/skills](https://github.com/mattpocock/skills) end where they mean
to: *"Do not act on it until I confirm we have reached a shared understanding."*
Stopping there is the right call for a general-purpose interview, and it is why
that skill works on anything.

But when the session closes, the understanding closes with it. Nothing is on
disk, nothing an agent can pick up tomorrow, and nothing to execute against.

`/memory-bank-init` is the same interview discipline pointed at a persistent
artifact — one question at a time, each with a recommended answer, facts looked
up rather than asked. Run it **in the same session, right after the grill**:

```text
/grill-me            # explore the design; no files written
/memory-bank-init    # turn those decisions into a memory bank
```

It will not re-ask what you already settled. "Look up facts, ask about
decisions" applies to the conversation as much as to the repository, so a grill
you have just finished makes for a short interview — mostly confirming a
proposed breakdown of lanes and milestones.

What you get that the grill alone does not leave behind:

| | After `/grill-me` | After `/memory-bank-init` |
|---|---|---|
| Where the decisions live | The conversation | `product.md`, `architecture.md`, `tech-stack.md` |
| Tomorrow's agent | Starts cold | Reads `AGENTS.md` and knows |
| Next action | You decide | The next `` `[ ]` `` row |
| Executing it | — | `/memory-bank-next`, or `/memory-bank-goal` for a set |

The two are complements, not rivals. Keep `/grill-me` for decisions that produce
no project — an architecture argument, a hiring plan, a talk outline. Reach for
`/memory-bank-init` when the thing you are grilling about is a codebase that has
to still know what it is next week.

## Install The API Harness

This section is optional. Everything above works without it — the harness only
adds an unattended loop that drives an agent through the API instead of you
typing into one. Skip it if Codex, Claude Code, or another agent already does
that for you.

The API harness is account-level because it can drive any project that follows
this memory-bank shape. It needs Python 3 and nothing else.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/harness/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

The commands below call `tackle-memory-bank-api-loop` by name, which requires
`~/.local/bin` on your `PATH`. If `command -v tackle-memory-bank-api-loop`
prints nothing, add this line to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Run one row:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

Run a loop:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

Use an OpenAI-compatible provider:

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.5 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Use a local OpenAI-compatible server:

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Use Anthropic (Claude) instead of the OpenAI-compatible path:

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

The harness embeds the task instruction in its API prompt. It does not call the
Codex CLI, and it does not require the external prompt file at runtime. The
prompt file is included as a reusable human/agent reference. The same JSON
command protocol drives the agent loop regardless of which provider is used.

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
are normal stopping conditions rather than failures — for example `4` means the
worktree was dirty before the run, and `6` means the agent finished without
committing. `11` means it found no `status-<LANE><NN>.md` files, which usually
means the memory bank has not been filled in yet. The full table is in
[Execution Harness](docs/EXECUTION.md#exit-codes).

## What The Harness Is

For normal project work, `tackle-memory-bank-api-loop` is an execution harness:
it repeatedly runs an agent against a repository, gives it shell access through a
controlled command protocol, and checks git state between runs.

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

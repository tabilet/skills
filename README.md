# A Minimal Engineering Harness

This repository is a copyable starting point for a lightweight project operating
system built around:

- `AGENTS.md` as the agent bootstrap guide.
- `memory-bank/` as the current project source of truth.
- `evolution/` as versioned history for direction changes.
- execution harnesses as repeatable commands that prove the software works.
- model eval harnesses as repeatable evaluations that measure model-assisted
  behavior.

The goal is not documentation volume. The goal is to give humans and agents the
same compact operating manual, then connect that manual to executable harnesses.

Language versions: [🇨🇳 中文](README_cn.md) · [🇯🇵 日本語](README_ja.md) ·
[🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md) ·
[🇪🇸 Español](README_es.md).

## Getting Started

**To use the memory bank you need `git`, and nothing else.** The memory bank is
plain markdown, so the everyday workflow — telling an agent such as Codex or
Claude Code to tackle the next pending item — needs no runtime at all.

**Python 3 is only for the optional API harness**, the unattended loop described
in [Install The API Harness](#install-the-api-harness). It uses nothing but the
standard library, so there is nothing to install with `pip`. Skip it entirely if
you drive the memory bank through an agent you already use.

The existing-project instructions below also use
[ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) for the initial inventory.

Clone this repository once. Every `cp` command below refers to your clone as
`/path/to/skills`:

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

Nothing here runs from the clone itself. You copy files out of it: `template/`
into a project, `harness/` into your home directory.

## What Is In This Repository

Project-level sample files in [template/](template/), copied into a project
root:

- [template/AGENTS.md](template/AGENTS.md)
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

Harness references:

- [Execution Harness](docs/EXECUTION.md)
- [Model Eval Harness](docs/MODEL_EVAL.md)

## Set Up A New Project

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
   See [what a filled-in status file looks
   like](#what-a-filled-in-status-file-looks-like) — the marker backticks
   matter.
6. `evolution/prompt-v1.md`: record the initial direction.
7. `evolution/result-v1.md`: record the current starting state.
8. `AGENTS.md`: replace placeholders with project-specific commands and rules.

Keep `README.md` simple and user-facing. Put long-form references in `docs/`.

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

Status rows use these markers:

| Symbol | Meaning |
|---|---|
| `[ ]` | Pending |
| `[+]` | Completed |
| `[~]` | In progress |
| `[!]` | Blocked |
| `[X]` | Cancelled |

### What a filled-in status file looks like

The templates ship with placeholders. Filled in for a small shopping service,
`memory-bank/status-S01.md` looks like this:

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

The same fill-in-the-placeholders move applies to the rest of the memory bank.
`memory-bank/product.md` starts as `[project-name] is [one or two sentences
describing the project]` and becomes:

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```

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

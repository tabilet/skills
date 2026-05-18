# Small Operating Manuals Beat Big Pipelines

*An engineering harness that helps your AI agent evolve the project — without taking it over.*

Look around the AI coding ecosystem and you'll see the same pattern in dozens of places: every team is building a *harness* — scaffolding alongside the code that tells an agent what the project is, how to work on it, and what state things are in. CLIs that scaffold directories. Slash-command suites you learn one by one. Methodologies with phased pipelines. Per-feature artifact folders that pile up over time.

It's understandable. Agents work better with structure. But there's a quiet cost: **the deeper the harness goes, the less the project looks like yours.** Your file layout starts sharing the repo with the harness's. Your workflow starts running through the harness's slash commands. Your decisions accumulate in folders the harness owns. Six months in, the harness is doing most of the talking, and you're maintaining its artifacts as much as your code.

Take spec-kit as one example of the deep end of this spectrum: a CLI installer (`uv tool install specify-cli`), a `specify init` step, a `.specify/` scaffold, a methodology of seven slash commands (`/speckit.constitution`, `/specify`, `/clarify`, `/plan`, `/analyze`, `/tasks`, `/implement`), and per-feature artifact folders that grow with the project. It's well-designed and powerful for spec-driven work — but it's also a system you adopt. You live inside its conventions, not yours.

This repository takes the opposite bet.

## The pitch: a small system, on purpose

The bet is that a *small* operating manual humans and agents read together beats a *large* generated artifact chain. You need:

- a short pointer file the agent reads first,
- a few markdown files that describe what's true now,
- a versioned record for when direction actually changes,
- and a way to advance work one verified step at a time.

That's it. No CLI. No methodology. No slash-command vocabulary. **Nothing is mandatory.** You bring the files into your project once, fill in the placeholders, and stop when the manual reflects your work. The files end up as yours — editable, deletable, replaceable whenever you want.

## What's in the box

Project-level files you drop into a repo:

- **`AGENTS.md`** — the bootstrap pointer. Short. Tells the agent what to read and in what order.
- **`memory-bank/`** — the current source of truth.
  - `product.md` — what this is, who uses it, what it isn't.
  - `architecture.md` — layout, data flow, ownership boundaries.
  - `tech-stack.md` — commands, dependencies, harnesses.
  - `milestone.md` — milestone scope and acceptance criteria.
  - `status-Mx.md` — one file per milestone, with rows marked `[ ]`, `[+]`, `[~]`, `[!]`, `[X]`.
- **`evolution/`** — versioned direction snapshots. `prompt-vN.md` describes the intent; `result-vN.md` the state it produced. A new version is added only when direction, an architecture boundary, a milestone target, or a public contract materially changes — which should be rare.

Account-level files, optional:

- `.local/bin/tackle-memory-bank-api-loop` — a Python runner that drives any OpenAI- or Anthropic-compatible model.
- `.codex/prompts/tackle-next-memory-bank-todo.md` — the same instruction the runner embeds, kept as a reusable reference.

## Bootstrapping — with a little help from your agent

Setting up the harness once is a small upfront step, and you don't have to do it alone.

**For a new project**, jot your ideas into a scratch file — what the product is, who uses it, what the first milestone looks like — and ask your AI agent to read the sample `AGENTS.md`, `memory-bank/`, and `evolution/` files and fill the placeholders from your notes. A few minutes of conversation is usually enough to get a first draft you can refine.

**For an existing project**, ask the agent to read the current README, docs, package comments, tests, and build files, then populate the harness from what the project already says. The README ships with ready-made prompts for both cases — you can copy them as-is.

Think of this first pass as a kind of constitution for the project: it establishes what the project is, what it owns, what it isn't, and what comes next. **It does not need to be perfect.** A rough draft is enough to start working. The memory bank is *mutable* — as the project changes, `product.md`, `architecture.md`, and `tech-stack.md` are updated in the same commit as the code that changed them. The `evolution/` folder is reserved for the rare moments when direction actually shifts. The harness and the project it describes evolve together; you're not committing to a fixed snapshot, and you're not stuck living with the first draft's mistakes.

## No slash commands. On purpose.

The day-to-day workflow is one sentence:

> *tackle next pending item in memory bank*

That's the whole interface. No `/specify`, no `/plan`, no `/tasks`, no learned vocabulary. The harness doesn't own your prompt surface, because slash commands are an *interface* opinion — they tie you to whichever agent implements them. Plain English is portable: type it into Claude Code, paste it into Codex, send it as an API call, or build your own UI on top. Same result.

Under the surface, the loop is:

1. Read `AGENTS.md`.
2. Read the memory bank in the order it lists.
3. Pick the next actionable row in the current `status-Mx.md`.
4. Implement, verify, update the relevant memory-bank files, commit.
5. If that was the last row in a milestone, run the milestone review and decide whether `evolution/` needs a new version.

Status markers carry meaning: `[ ]` pending, `[+]` complete, `[~]` in progress, `[!]` blocked, `[X]` cancelled. A blocked row stops the loop — not because the agent failed, but because a human should look.

Each row is a commit unit. That's the only commit discipline this asks for, and it makes work auditable in `git log` without extra tooling.

## The bundled runner — optional, multi-provider

`tackle-memory-bank-api-loop` is a ~360-line Python script that drives an LLM through a JSON shell-command protocol. It works with OpenAI-compatible servers (OpenAI, OpenRouter, vLLM, llama.cpp, LM Studio, Ollama's OAI shim) and natively with Anthropic via `LLM_PROVIDER=anthropic`.

It checks the worktree is clean before each run, rejects destructive commands, requires the model to commit if it modified files, and stops on the first sign that something needs human attention — a blocked row, uncommitted changes, no actionable rows left.

You can use it for one row, for an unattended loop, for evaluations across models and prompts — or not at all. Agents inside Claude Code, Codex, or any IDE can do the same work through their own UI without ever touching the script.

## Under control

The unifying property across every part of this system is that *you* own the files. The harness doesn't gate access to them, doesn't accumulate hidden artifacts on your behalf, doesn't lock you into a vocabulary you'll have to migrate away from later.

- `memory-bank/architecture.md` is rewritten as reality changes. There's no history of stale architecture docs to maintain.
- `evolution/` versions are rare by design. You add one when direction really shifted — not on every feature.
- Status rows are simple checkboxes that close out when milestones close. Old `status-Mx.md` files can stay or go; nothing depends on preserving them.
- There are no per-feature spec folders, so the repo doesn't grow a graveyard of historical artifacts that no longer match the code.

The AI's job is to help you advance the project — bootstrap the harness from your notes, pick the next row, do the work, update the memory bank, commit. Your job is to know what the project is and to course-correct when the agent drifts. The harness sits in between, light enough that you can throw it out whenever you want.

## When this fits — and when it doesn't

This harness fits when:

- you're iterating on an existing codebase or growing one organically,
- the operative question is "what's next," not "what should this be,"
- you want the option of headless or scripted runs,
- you'd rather own your files than learn a vocabulary.

It's a poor fit when you want strong spec-rigor up front, when your team agrees on a methodology with named phases, or when you live entirely inside a single agent UI and slash commands feel natural. For those cases, heavier harnesses — spec-kit and others — are doing real work and worth their weight.

The approaches aren't mutually exclusive. You can draft a spec under a heavier methodology and then convert the acceptance criteria into `status-Mx.md` rows here. They operate at different time scales.

## Closing

The pitch isn't that small is always better. It's that the *default* in AI tooling right now is to go big — CLIs, scaffolds, slash commands, generated artifact chains — and the cost is that your project starts to look more like the harness than like itself. This repository is a counterweight. Three folders. One pointer file. Plain-English triggers. A runner you can ignore. A bootstrap pass an agent helps you write in a few minutes, refined as the project evolves.

AI helps you evolve the project. You stay in control of every file.

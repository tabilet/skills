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

## What Is In This Repository

Project-level sample files:

- [AGENTS.md](AGENTS.md)
- [memory-bank/product.md](memory-bank/product.md)
- [memory-bank/architecture.md](memory-bank/architecture.md)
- [memory-bank/tech-stack.md](memory-bank/tech-stack.md)
- [memory-bank/milestone.md](memory-bank/milestone.md)
- [memory-bank/status.md](memory-bank/status.md)
- [evolution/prompt-v1.md](evolution/prompt-v1.md)
- [evolution/result-v1.md](evolution/result-v1.md)

User-account-level sample files:

- [.local/bin/tackle-memory-bank-api-loop](.local/bin/tackle-memory-bank-api-loop)
- [.codex/prompts/tackle-next-memory-bank-todo.md](.codex/prompts/tackle-next-memory-bank-todo.md)

Harness references:

- [Execution Harness](docs/EXECUTION.md)
- [Model Eval Harness](docs/MODEL_EVAL.md)

## Set Up A New Project

### Manual

From a new project root:

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Then edit the copied files in this order:

1. `memory-bank/product.md`: define what the project is and is not.
2. `memory-bank/architecture.md`: define layout, data flow, and boundaries.
3. `memory-bank/tech-stack.md`: define commands, dependencies, and harnesses.
4. `memory-bank/milestone.md`: define the first milestone.
5. `memory-bank/status.md`: define the first actionable rows.
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
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Then chat with the agent until the product, users, boundaries, commands, and
first milestone are clear. Ask it to fill in:

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

Example prompt:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, and make
memory-bank/status.md contain the first actionable milestone rows.
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
2. Copy in `AGENTS.md`, `memory-bank/`, and `evolution/` from this repository.
3. Fill the memory bank from what the project already says, not from an imagined
   rewrite.
4. Move stable long-form references into `docs/`.
5. Convert duplicated roadmap/status material into `memory-bank/milestone.md`
   and `memory-bank/status.md`.
6. Keep known gaps visible in `status.md` instead of hiding them.

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
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Then ask the agent to read the project before writing:

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in memory-bank/status.md.
Do not invent product direction that is not supported by the existing project.
```

The agent should:

1. Inventory existing markdown and source layout.
2. Identify commands, dependencies, tests, and harnesses.
3. Fill in the memory bank from current project reality.
4. Move or summarize long-form references into `docs/`.
5. Keep `README.md` simple and user-facing.
6. Leave unresolved gaps as pending or blocked rows in `memory-bank/status.md`.

## Use The Memory Bank

With an agent such as Codex or Claude Code, the user-facing workflow can be as
simple as typing:

```text
tackle next pending item in memory bank
```

The agent should find the next actionable row in `memory-bank/status.md`,
complete that task, run the required verification, update the memory bank, and
make a scoped git commit. If that row is the last open item in a milestone, the
agent should run the milestone review from `memory-bank/milestone.md` before
moving on. During that review it should also decide whether `evolution/` needs a
new version because the product direction, architecture boundary, milestone
target, or public/private contract direction materially changed.

Under the surface, the normal agent workflow is:

1. Read `AGENTS.md`.
2. Read the memory bank files in the order listed by `AGENTS.md`.
3. Tackle exactly one scoped task or status row.
4. Update the matching memory-bank file if scope, architecture, tools,
   milestone acceptance, or status changed.
5. Mark a row `[+]` only after verification passes.
6. Commit the row as a scoped unit.
7. If a milestone becomes complete, run the milestone review procedure in
   `memory-bank/milestone.md` before moving on.
8. Check `evolution/` and add a new version only when the review finds a real
   direction, boundary, milestone, or contract change.

Status rows use these markers:

| Symbol | Meaning |
|---|---|
| `[ ]` | Pending |
| `[+]` | Completed |
| `[~]` | In progress |
| `[!]` | Blocked |
| `[X]` | Cancelled |

## Install The API Harness

The API harness is account-level because it can drive any project that follows
this memory-bank shape.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/.local/bin/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/.codex/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
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

The harness embeds the task instruction in its API prompt. It does not call the
Codex CLI, and it does not require the external prompt file at runtime. The
prompt file is included as a reusable human/agent reference.

## What The Harness Is

For normal project work, `tackle-memory-bank-api-loop` is an execution harness:
it repeatedly runs an agent against a repository, gives it shell access through a
controlled command protocol, and checks git state between runs.

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

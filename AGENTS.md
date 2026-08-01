# AGENTS.md

## Purpose

Bootstrap guide for agents working on `skills`, the repository that publishes
the minimal engineering harness. This file describes *this* repository. The
copyable sample manual for other projects is
[template/AGENTS.md](template/AGENTS.md).

## What This Repository Is

A copyable starter, not an application. Content splits three ways:

| Path | Role |
|---|---|
| `template/` | Project payload. Copied into another project's root. Placeholders are intentional. |
| `harness/` | Account payload. Installed into `~/.local/bin` and `~/.codex/prompts`. |
| `docs/`, `README*.md` | This repository's own documentation. |

`template/` and `harness/` are shipped artifacts. Do not fill in their
`[bracketed placeholders]` with content about this repository, and do not treat
`template/memory-bank/` as this repository's project state.

## Boundaries

`skills` owns:

- The sample memory-bank, milestone, evolution, and AGENTS files in `template/`.
- The agent execution harness in `harness/`.
- The status ID pattern and status marker vocabulary.

Out of scope:

- Project-specific product, architecture, or milestone content -> the project
  that copied the template.
- Provider SDKs, agent frameworks, or CLI wrappers -> not this repository. The
  harness talks to HTTP APIs with the standard library only.

## Essential Commands

```bash
# Syntax-check the harness (py_compile would litter harness/__pycache__)
python3 -c "import ast,pathlib; ast.parse(pathlib.Path('harness/tackle-memory-bank-api-loop').read_text())"

# Exercise it against a real memory-bank project
LLM_MODEL=... OPENAI_API_KEY=... MAX_RUNS=1 harness/tackle-memory-bank-api-loop /path/to/project

# Check what a new project receives
cp -R template/. /tmp/scratch-project/
```

There is no build, lint, or test tooling. Verification is running the harness
and checking that documented paths and links resolve.

## Hard Rules

- Keep the harness dependency-free: Python standard library only.
- `EMBEDDED_TASK` in `harness/tackle-memory-bank-api-loop` and
  `harness/prompts/tackle-next-memory-bank-todo.md` say the same thing. Change
  both together.
- English is the source language. `README.md`, `docs/EXECUTION.md`, and
  `docs/MODEL_EVAL.md` each have `_cn`, `_ja`, `_de`, `_fr`, `_es` siblings;
  propagate content changes to all of them in the same change. Commands, code
  blocks, and example prompts stay in English.
- Status files are named `status-<LANE><NN>.md`. The pattern is defined in
  [template/memory-bank/milestone.md](template/memory-bank/milestone.md); the
  harness discovers lane files by that shape, so the two must agree.
- Run the required verification before claiming a change is done.

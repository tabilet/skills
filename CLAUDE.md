# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A copyable **template** for a lightweight project operating system ("A Minimal
Engineering Harness"), not an application. Most files here are payload that
users copy into *their* project or home directory.

Root is organized by who receives the file — this is the thing to internalize:

| Path | Role |
|---|---|
| `template/` | Project payload, copied into another project's root (`cp -R template/. .`) |
| `harness/` | Account payload, installed into `~/.local/bin` and `~/.codex/prompts` |
| `docs/`, `README*.md`, `AGENTS.md`, `CLAUDE.md` | This repository's own files |

Two consequences that matter constantly:

- **`[bracketed placeholders]` in `template/` are the deliverable, not TODOs.**
  Do not "complete" them with content about this repository unless asked.
- **`template/memory-bank/` is not this repository's project state.** The
  workflow it describes ("tackle next pending item in memory bank") is for
  downstream projects.

The only executable file is `harness/tackle-memory-bank-api-loop`.

## Commands

There is no build, lint, test, or package tooling — the repo is markdown plus
one stdlib-only Python script.

```bash
# Syntax-check the harness (the closest thing to a test)
python3 -c "import ast,pathlib; ast.parse(pathlib.Path('harness/tackle-memory-bank-api-loop').read_text())"

# Exercise the harness end-to-end against a real memory-bank project
LLM_MODEL=... OPENAI_API_KEY=... MAX_RUNS=1 harness/tackle-memory-bank-api-loop /path/to/project
LLM_PROVIDER=anthropic LLM_MODEL=... ANTHROPIC_API_KEY=... MAX_RUNS=1 harness/tackle-memory-bank-api-loop /path/to/project

# Check what a new project actually receives
cp -R template/. /tmp/scratch-project/
```

Prefer that `ast.parse` form over `python3 -m py_compile`: py_compile writes a
`__pycache__/` next to the script, inside the shipped payload directory, and
`PYTHONDONTWRITEBYTECODE=1` does *not* suppress it (that variable only affects
implicit import-time caching, not an explicit compile).

To test harness gating without an API key, point it at a scratch git repo — the
row gates run before the first network call, so blocked-only exits 3, all-done
exits 0, and no lane files exits 11 without any request being made.

## Architecture

Four document layers, each with a distinct lifetime. Keeping them separate is
the whole point of the design:

| Layer | Role |
|---|---|
| `AGENTS.md` | Short bootstrap pointer; read first by agents. Names commands, boundaries, hard rules. |
| `memory-bank/` | Active truth: `product.md`, `architecture.md`, `tech-stack.md`, `milestone.md`, one `status-<LANE><NN>.md` per milestone. |
| `evolution/` | Versioned direction snapshots (`prompt-vN.md` / `result-vN.md`). New version only on a real direction, boundary, milestone, or contract change. |
| `docs/` | Long-form reference. `README.md` stays short and user-facing. |

### Status ID lanes

Status files are `memory-bank/status-<LANE><NN>.md`: one uppercase letter
classifying the domain, then a zero-padded two-digit number. `A01`/`A02` for
accounting, `S01` for shopping, `M` as the default lane for anything that
doesn't classify. A lane holds at most 99 files — when it fills, open a new
letter rather than a third digit. IDs are never reused or renamed once their
file exists, and there is no aggregate `status.md`. The pattern, the lane
meanings, and the index table live in `template/memory-bank/milestone.md`.

This shape is load-bearing for the harness, not just convention: lane files are
found by glob and rows are parsed out of markdown tables. Real deployments run
~120 lane files across ~17 lanes.

### The agent loop (`harness/tackle-memory-bank-api-loop`)

Python 3, standard library only (`urllib`, no `requests`/SDKs) — deliberate, per
the repo's "prefer native core libraries" rule. Structure:

- Two providers behind one interface: `call_openai` (`/v1/chat/completions`,
  also OpenRouter / vLLM / LM Studio / Ollama) and `call_anthropic`
  (`/v1/messages`). Selected by `LLM_PROVIDER`.
- **No provider tool-calling.** The model is driven by a plain JSON command
  protocol — `{"tool":"run_shell","cmd":...,"why":...}` or `{"final":...}` —
  so the same loop runs unchanged on either provider. `extract_json` tolerates
  fenced/prose-wrapped replies.
- The task instruction is embedded in the script (`EMBEDDED_TASK`); the
  `harness/prompts/` file is a human-readable duplicate, not a runtime input.
  **Edit both when the instruction changes.**
- Lane discovery: `status_files()` globs `STATUS_GLOB`, `lane_summary()` counts
  actionable/blocked rows per file, and `lane_table()` renders that into the
  prompt. Python owns the deterministic gate; the *choice* of row belongs to
  the model, guided by `milestone.md` priority. Lane file bodies are never
  inlined into the prompt — only the counts — which is what keeps a 120-lane
  project's prompt bounded.
- Guardrails, each with a dedicated exit code: only blocked rows left (3), dirty
  worktree before a run (4), uncommitted changes after (5), no new commit (6),
  `MAX_RUNS` reached (7), missing `AGENTS.md` (10), no lane files (11). A
  blocked row warns but does not halt while other lanes still have work.
  `DANGEROUS_RE` blocks `git reset --hard`, `git clean -fd`, `sudo`, fork bombs,
  etc. unless `ALLOW_DANGEROUS_COMMANDS=1`.
- Row parsing: `ACTIONABLE_RE` matches `` `[ ]` ``/`` `[~]` ``, `BLOCKED_RE`
  matches `` `[!]` ``. Changing the status-marker table format in the templates
  breaks the harness.

Status markers: `[ ]` pending, `[+]` completed, `[~]` in progress, `[!]`
blocked, `[X]` cancelled. One status row = one commit; one milestone = one
review unit.

## Translations

English is the source. Each of `README.md`, `docs/EXECUTION.md`, and
`docs/MODEL_EVAL.md` has `_cn`, `_ja`, `_de`, `_fr`, `_es` siblings. A change to
an English file should be propagated to its five siblings in the same change;
commands, code blocks, and example prompts stay in English.

Known gap, pre-existing and separate from the lane work: the localized READMEs
are missing the Anthropic provider section and the language-version links that
`README.md` carries.

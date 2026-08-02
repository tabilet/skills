# AGENTS.md

Bootstrap guide for agents working on `skills`, the repository that publishes
the minimal engineering harness. This file describes *this* repository. The
copyable sample manual for other projects is
[template/AGENTS.md](template/AGENTS.md).

This is the single source of truth for every agent. Tools that read a different
filename should bridge to this file rather than duplicate it — see
[Wiring up your agent](README.md#wiring-up-your-agent).

[GOAL.md](GOAL.md) is one optional protocol for slash-goal requests that span
multiple status files. Follow it when a request names it. A request that names a
different protocol, or none, does not use it.

A slash-goal run is a deliberate exception to this file's commit rule. For the
duration of that run, `GOAL.md`'s `COMMIT_POLICY` is the entire commit rule and
"one status row, one commit" does not apply: `COMMIT_POLICY: none` — the
protocol's default — means no commits at all. Pass `COMMIT_POLICY: task` to get
the usual per-row commits. Everything else here still governs; only commits are
delegated, and only inside the run. The API harness is a separate path and is
unaffected — it still requires a commit per run.

## What This Repository Is

A copyable starter, not an application. Most files here are payload that users
copy into *their* project or home directory. Root is organized by who receives
the file:

| Path | Role |
|---|---|
| `template/` | Project payload, copied into another project's root (`cp -R template/. .`). Placeholders are intentional. |
| `GOAL.md` | Multi-milestone execution protocol. Project-agnostic, so `./GOAL.md` and `template/GOAL.md` are byte-identical. |
| `harness/` | Account payload, installed into `~/.local/bin` and `~/.codex/prompts`. |
| `skills/` | The three slash commands, one `SKILL.md` each. **Must stay at the repository root** — see below. |
| `.claude-plugin/` | Plugin and marketplace manifests, read by Claude Code *and* Codex. Vendor-named but not vendor-specific in effect; the ban is on vendor files in `template/`. |
| `docs/`, `README*.md`, `AGENTS.md` | This repository's own documentation. |

Two consequences that matter constantly:

- **`[bracketed placeholders]` in `template/` are the deliverable, not TODOs.**
  Do not "complete" them with content about this repository unless asked.
- **`template/memory-bank/` is not this repository's project state.** The
  workflow it describes ("tackle next pending item in memory bank") is for
  downstream projects.

Two executable files: `harness/tackle-memory-bank-api-loop`, which is payload,
and `check.py`, which verifies this repository and is not.

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

Non-goals — things this repository has deliberately decided not to grow. The
central claim is that a small operating manual beats a large one, and that claim
is only worth anything if additions are argued against something:

- **No second harness implementation.** A Go or Node twin doubles the surface
  where two implementations can silently disagree, and disagreement between two
  harnesses is worse than a Python dependency. `harness/` stays one file.
- **No vendor-specific agent files in `template/`.** `AGENTS.md` is the open
  cross-vendor standard; tools that read another filename get a documented
  one-line bridge in the README.
- **No per-feature artifact directories.** No `.skills/`, no scaffold, no
  generated plan folders that accumulate with the project.
- **No memory bank for this repository itself.** `skills` is the generator that
  gives birth to other projects' harnesses; it is not an instance of its own
  output. A root `memory-bank/` beside `template/memory-bank/` would force every
  reader and agent to disambiguate two of them for no gain. The workflow is
  proven in the projects that copied it, not here.

## Essential Commands

```bash
# Verify this repository. Run before claiming a change is done; CI runs it too.
python3 check.py

# Exercise the harness end-to-end against a real memory-bank project
LLM_MODEL=... OPENAI_API_KEY=... MAX_RUNS=1 harness/tackle-memory-bank-api-loop /path/to/project
LLM_PROVIDER=anthropic LLM_MODEL=... ANTHROPIC_API_KEY=... MAX_RUNS=1 harness/tackle-memory-bank-api-loop /path/to/project

# Check what a new project actually receives
cp -R template/. /tmp/scratch-project/
```

`check.py` enforces the hard rules below so they are not left to memory. It runs
the fourteen invariants this repository has actually broken at least once —
identical `GOAL.md` copies, the `EMBEDDED_TASK` duplicate, the skill manifest
and its `SKILL.md` twin, the generator agreeing with `template/`, the plugin
version against the tags, explicit `COMMIT_POLICY` in every `GOAL.md`
invocation, links *and* heading anchors, the documented exit codes, the
status-marker regexes, the shipped payload, and translation parity. Standard
library only, like the harness. When you add a rule to this file, add the check
that enforces it.

The plugin-version check needs tags, which `actions/checkout` does not fetch by
default; the workflow passes `fetch-tags`. Without them the check fails rather
than passing quietly, because a check that cannot see its input has not verified
anything.

It syntax-checks the harness with `ast.parse` rather than `python3 -m
py_compile`: py_compile writes a `__pycache__/` next to the script, inside the
shipped payload directory, and `PYTHONDONTWRITEBYTECODE=1` does *not* suppress
it (that variable only affects implicit import-time caching, not an explicit
compile).

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
  etc. unless `ALLOW_DANGEROUS_COMMANDS=1`. The full table is in
  [docs/EXECUTION.md](docs/EXECUTION.md#exit-codes).
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

Section links differ per language: heading anchors are slugified from the
translated heading, so `docs/EXECUTION_cn.md#退出码` is correct where the
English is `#exit-codes`. Check anchors, not just filenames, when adding links.

Known gap, pre-existing: the localized READMEs are missing the Anthropic
provider section and the language-version links that `README.md` carries.

## Hard Rules

- Keep the harness dependency-free: Python standard library only.
- `EMBEDDED_TASK` in `harness/tackle-memory-bank-api-loop` and
  `harness/prompts/tackle-next-memory-bank-todo.md` say the same thing. Change
  both together.
- `GOAL.md` and `template/GOAL.md` are byte-identical, and stay identical to the
  copy any other project carries — it is a portable protocol, not a per-project
  file. Change both together, and do not add project-specific paths, lane names,
  or commands to either.
- Document the goal loop by referencing `GOAL.md`, never by restating its
  phases. `GOAL.md` owns multi-milestone sequencing; `milestone.md` owns the
  single-milestone review; `status-<LANE><NN>.md` owns row and commit rules.
- Every documented invocation of `GOAL.md` carries an explicit `COMMIT_POLICY`.
  The protocol's default is `none`, so an example that omits it quietly promises
  no commits at all. Write `task` unless the example is specifically about
  running without commits.
- Precedence for a slash-goal run: the request wins, then `GOAL.md`, then this
  file. Commits are the case that matters — `COMMIT_POLICY` governs them
  outright for the length of the run, whatever the cadence here says.
- `GOAL.md` is offered, never required. `/goal` belongs to the reader's agent,
  not to this harness, and the memory bank must work with a different goal
  protocol or none at all. Do not write an instruction that routes a slash-goal
  request through `GOAL.md` unless the request named it.
- Propagate English content changes to all five translation siblings in the same
  change.
- Status files are named `status-<LANE><NN>.md`. The pattern is defined in
  [template/memory-bank/milestone.md](template/memory-bank/milestone.md); the
  harness discovers lane files by that shape, so the two must agree.
- Ship no vendor-specific agent files in `template/`. `AGENTS.md` is an open
  cross-vendor standard; tools that read another filename get a documented
  one-line bridge in the README, not a file in the payload.
- One `SKILL.md` per command in `skills/`, never a per-agent copy. Claude Code
  and Codex read the same format, so a second copy would only be a place to
  drift. The directory name, the frontmatter `name`, and the `plugin.json` list
  must agree.
- **`skills/` stays at the repository root.** It looks like account payload and
  belongs under `harness/` by that logic, but Codex discovers a plugin's skills
  by scanning `<plugin-root>/skills/` and ignores `plugin.json`'s `skills`
  array. With the directory anywhere else, `codex plugin add` reports success,
  writes `enabled = true` to `config.toml`, and surfaces no commands at all —
  which is exactly how this was found. Claude Code reads the manifest array and
  does not care, so the root is the only location that satisfies both.
- Both agents install from `.claude-plugin/`. Codex tries
  `.codex-plugin/plugin.json`, then `.claude-plugin/plugin.json`, then
  `.cursor-plugin/plugin.json`, so one manifest serves both and there is no
  reason to add a second.
- No skill named `goal`. Claude Code has a built-in `/goal` that sets a stop
  condition; a skill by that name would shadow a different feature.
- `.claude-plugin/plugin.json`'s version and the git tags agree. At a tagged
  commit they must be identical, and on an untagged commit the manifest must
  never be behind the latest tag. A registry reads that version off the default
  branch, so a mismatch publishes a release claiming to be another one. Bump the
  manifest in the same change as the tag.
- Run the required verification before claiming a change is done.

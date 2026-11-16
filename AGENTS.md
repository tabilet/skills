# AGENTS.md

Bootstrap guide for agents working on `skills`, the repository that publishes
the minimal engineering harness. This file describes *this* repository. The
copyable sample manual for other projects is
[template/AGENTS.md](template/AGENTS.md).

This is the single source of truth for every agent. Tools that read a different
filename should bridge to this file rather than duplicate it — see
[Wiring up your agent](README.md#wiring-up-your-agent).

This repository bridges itself the same way it asks users to. Claude Code reads
`CLAUDE.md` and not `AGENTS.md`, so `./CLAUDE.md` is a one-line `@AGENTS.md`
import and holds no instructions of its own. Deleting it would stop Claude Code
loading these rules here; changing it into a second copy would create a place for
them to drift. Anything true of the repository belongs in this file or in
[docs/MAINTAINING.md](docs/MAINTAINING.md), which it links. Put
Claude-Code-specific instructions in `CLAUDE.md` below the import, if any ever
arise.

This file stays under 28 KiB because some agent hosts load only the first
32 KiB of project instructions (Codex's `project_doc_max_bytes` defaults to
32,768 bytes) and silently drop the rest. The architecture notes, the
documentation-language policy, and the payload contract rules live in
[docs/MAINTAINING.md](docs/MAINTAINING.md). They bind exactly as the Hard Rules
here do. **Read that file in full before changing anything other than
`README.md`.**

[GOAL.md](GOAL.md) is one optional protocol for goal requests that span
multiple status files. Follow it when a request names it. A request that names a
different protocol, or none, does not use it.

A `GOAL.md` run is a deliberate exception to this file's commit rule. For the
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
| `GOAL.md` | The stock multi-milestone execution protocol. Project-agnostic and canonical here; the goal-running skill bundles carry byte-identical copies, and projects carry none. |
| `harness/` | Optional account-level API runner installed into `~/.local/bin`, plus its repository-only human-readable prompt copy. |
| `skills/` | The seven optional skills, one `SKILL.md` each. **Must stay at the repository root** — see below. |
| `.claude-plugin/` | Plugin and marketplace manifests, read by Claude Code *and* Codex. Vendor-named but not vendor-specific in effect; the ban is on vendor files in `template/`. |
| `docs/`, `README.md`, `AGENTS.md` | This repository's own documentation. The published site is [Tabilet Memory Bank](https://tabilet.github.io/skills/), with a Simplified Chinese mirror at [tabilet.github.io/skills/zh/](https://tabilet.github.io/skills/zh/). |
| `docs/zh/` | The Simplified Chinese translation of the published guides, one file per published English guide, resolved from the single `nav` by `mkdocs-static-i18n`. Hand-maintained, and held in one-for-one parity by `check.py`. |
| `mkdocs.yml`, `docs/requirements.txt`, `.github/workflows/deploy-docs.yml` | Website navigation, build dependencies (including the `mkdocs-static-i18n` plugin that publishes both locales), and deployment workflow. Only the guides selected by `mkdocs.yml` are published, in both languages. |

Two consequences that matter constantly:

- **`[bracketed placeholders]` in `template/` are the deliverable, not TODOs.**
  Do not "complete" them with content about this repository unless asked.
- **`template/tabilet/memory-bank/` is not this repository's project state.** The
  workflow it describes ("tackle next pending item in memory bank") is for
  downstream projects.

Python payload commands include the standalone `harness/tackle-memory-bank-api-loop`,
the optional `harness/tabilet` controller (installed with its runtime modules and
verified planning bundles by `harness/tabilet_install.py`), the optional
`harness/tabilet_audit_host.py` (installed as `tabilet-audit` with its
audit/index modules and runner parser), and
`skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`. Goal and Next also bundle the
optional `scripts/email_notify.py` approval-alert helper and its reference,
plus `references/model-policy.md` for opt-in host model selection.
`check.py` verifies this
repository and is not payload.

## Boundaries

`skills` owns:

- The sample memory-bank, milestone, evolution, and AGENTS files in `template/`.
- The agent execution harness in `harness/`.
- An optional account-level `tabilet` controller in `harness/` for bounded local
  planning and execution; copied projects and the direct skills do not depend on it.
- The status ID pattern and status marker vocabulary.

Out of scope:

- Project-specific product, architecture, or milestone content -> the project
  that copied the template.
- Provider SDKs and agent frameworks -> not this repository. The optional
  `tabilet` controller is the specific local CLI exception: it uses the Python
  standard library, Git, and Docker, and adds no background service or
  controller-owned project state. The harness talks to HTTP APIs with the standard library
  only.

Non-goals — things this repository has deliberately decided not to grow. The
central claim is that a small operating manual beats a large one, and that claim
is only worth anything if additions are argued against something:

- **No second harness implementation.** A Go or Node twin doubles the surface
  where two implementations can silently disagree, and disagreement between two
  harnesses is worse than a Python dependency. The execution runner stays one installable file when auditing is disabled;
  optional audit/index modules do not execute tasks. The `tabilet` controller
  reuses the runner's row parser, provider loop, and post-run gates; it does not
  add a second execution engine.
- **No vendor-specific agent files in `template/`.** `AGENTS.md` is the open
  cross-vendor standard; tools that read another filename get a documented
  one-line bridge in the README.
- **No per-feature artifact directories.** No `.skills/`, no scaffold, no
  generated plan folders that accumulate with the project.
- **No memory bank for this repository itself.** `skills` is the generator that
  gives birth to other projects' harnesses; it is not an instance of its own
  output. A root `tabilet/memory-bank/` beside `template/tabilet/memory-bank/` would force every
  reader and agent to disambiguate two of them for no gain. The workflow is
  proven in the projects that copied it, not here. The historical controller
  architecture specification `docs/api.md` does not create an exception or
  authorize a repository memory bank.

## Essential Commands

```bash
# For changes limited to README.md, verify its links and public contracts.
python3 check.py --readme

# For code, protocol, instruction, or other changes, run the full suite; CI does too.
python3 check.py

# A fully passing unit suite is cached outside the repo, keyed on a hash of every file Git sees, and
# the test files run in parallel (CHECK_JOBS sets the width). Any edit is a miss; CI never uses the cache.
python3 check.py --no-cache    # force a real run

# Separate credential-free DSH compatibility suite (Linux, Node 24).
npm ci --prefix tests/dsh --ignore-scripts --no-audit --no-fund
npm test --prefix tests/dsh

# Repository-only Chromium acceptance for the optional SQLite explorer.
npm ci --prefix tests/browser --ignore-scripts --no-audit --no-fund
npx --prefix tests/browser playwright install chromium
npm test --prefix tests/browser

# Verify the published guides and links before claiming a website change is done.
mkdocs build --strict

# Exercise the harness end-to-end against a real memory-bank project
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=... OPENAI_API_KEY=... MAX_RUNS=1 harness/tackle-memory-bank-api-loop /path/to/project
ALLOW_UNSANDBOXED_SHELL=1 LLM_PROVIDER=anthropic LLM_MODEL=... ANTHROPIC_API_KEY=... MAX_RUNS=1 harness/tackle-memory-bank-api-loop /path/to/project

# Check what a new project actually receives
cp -R template/. /tmp/scratch-project/
```

`check.py` enforces the hard rules below and in
[docs/MAINTAINING.md](docs/MAINTAINING.md) so they are not left to memory. It runs
the invariants this repository has actually broken at least once —
identical `GOAL.md` copies, the `EMBEDDED_TASK` duplicate, the skill manifest
and its `SKILL.md` twin, the generator agreeing with `template/`, the plugin
version against the tags, explicit `COMMIT_POLICY` in every `GOAL.md`
invocation, links *and* heading anchors, the documented exit codes, the
status-marker regexes, the shipped payload, the disposable goal-reference
contract, the English-only documentation policy and its translated-site
exception. Standard library only, like the harness.
When you add a rule to this file, add the check that enforces it.
The `--readme` mode checks README links, inbound anchors, and its public
instruction and installation contracts; it does not run behavioral tests. Use
it only when the changes being completed are limited to the root `README.md`.
Code, protocols, repository instructions, and changes to other files require the
full `python3 check.py`. Website changes also require `mkdocs build --strict`.

The DSH suite is repository-only: `tests/dsh/` locks the runtime and its
dependencies, and a separate CI job tests the seven shared bundles through DSH's
filesystem loader. Keep Node out of the default Python checks and shipped
payload. Paid acceptance is explicitly invoked, never automatic on pull
requests; [docs/DSH.md](docs/DSH.md) records the supported target, cost ceiling,
observed evidence, and incomplete gates. Keep raw sessions and generated
projects outside shipped payload.

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
exits 0, and missing active and retired status state exits 11 without a request.

## Architecture

Four document layers with distinct lifetimes: `AGENTS.md`; the optional
`tabilet/stages.md` and `tabilet/memory-bank/`; `tabilet/evolution/`; and
`docs/`. The archive and status ID lanes, long-term memory and retirement, the
API runner's structure and exit codes, and the status-marker vocabulary are in
[docs/MAINTAINING.md](docs/MAINTAINING.md#architecture). Changing the state
column or marker vocabulary in the templates breaks the harness.

## Documentation Language

Repository documentation is English-only, except the published website, which
also ships in Simplified Chinese from `docs/zh/`. The full policy, including the
i18n plugin pin and explicit heading ids, is in
[docs/MAINTAINING.md](docs/MAINTAINING.md#documentation-language).

## Hard Rules

The [payload contract rules](docs/MAINTAINING.md#payload-contract-rules)
are Hard Rules too. They cover the policies the payload ships: planning,
authorization, review and gates, auditing, the controller, and retirement.

- Keep the harness dependency-free: Python standard library only.
- `EMBEDDED_TASK` in `harness/tackle-memory-bank-api-loop` and
  `harness/prompts/tackle-next-memory-bank-todo.md` say the same thing. Change
  both together.
- `GOAL.md` is the stock protocol and canonical here. The init, goal, propose,
  reconcile, and upgrade bundles each carry a byte-identical `GOAL.md` and a
  byte-identical `goal-protocol.json` (version, SHA-256, and the fingerprints of
  every released stock copy, built from the git tags); `python3 check.py
  --sync-goal-protocol` regenerates all of them, and `template/` and the upgrade
  assets carry no protocol copy. Do not add project-specific paths, lane names, or
  commands to it.
- Document the goal loop by referencing `GOAL.md`, never by restating its
  phases. `GOAL.md` owns multi-milestone sequencing; `milestone.md` owns the
  single-milestone review; `status-<LANE><NN>.md` owns row and commit rules.
- Every documented invocation of `GOAL.md` carries an explicit `COMMIT_POLICY`.
  The protocol's default is `none`, so an example that omits it quietly promises
  no commits at all. Write `task` unless the example is specifically about
  running without commits.
- Precedence for a goal run: the request wins, then the project addendum, then
  the stock protocol, then this file. Commits are the case that matters — `COMMIT_POLICY` governs them
  outright for the length of the run, whatever the cadence here says.
- `GOAL.md` is offered, never required. A built-in `/goal` belongs to the
  reader's agent, not to this harness, and the memory bank must work with a
  different goal protocol or none at all. Do not route a built-in goal through
  the goal protocol unless its objective selects it.
- Keep repository documentation English-only, except for the translated website
  in `docs/zh/`. Do not add translated siblings of `README.md`, of
  `docs/EXECUTION.md`/`docs/MODEL_EVAL.md`, or of any other canonical file.
  `docs/zh/` is a checked mirror of the published guides, not a free-form
  translation directory: every page is named by `mkdocs.yml` `nav` or derived
  from it, matched one-for-one with its English counterpart, and linked only
  through explicit `{#id}` anchors.
- Treat every `docs/medium*.md` file as public guidance. A
  `docs/medium*-infographic.png` is a manual Medium-upload asset and must be
  named by its corresponding article; do not accumulate orphaned publishing
  images.
- Status files are named `status-<LANE><NN>.md`. The pattern is defined in
  [template/tabilet/memory-bank/milestone.md](template/tabilet/memory-bank/milestone.md); the
  harness discovers lane files by that shape, so the two must agree. Placeholder
  references use the same zero-padded form (`M01`, never `M1`).
- Ship no vendor-specific agent files in `template/`. `AGENTS.md` is an open
  cross-vendor standard; tools that read another filename get a documented
  one-line bridge in the README, not a file in the payload.
- One `SKILL.md` per command in `skills/`, never a per-agent copy. Claude Code
  and Codex read the same format, so a second copy would only be a place to
  drift. The directory name, the frontmatter `name`, and the `plugin.json` list
  must agree.
- `memory-bank-upgrade` upgrades an existing project's workflow rules only
  after a complete proposal is approved. Preserve task state, permanent IDs,
  local policies, review counters, and frozen history; do not initialize,
  implement, commit, or retire milestones as an upgrade side effect. Its bundled
  `assets/template/` stays byte-identical to `template/`; update and verify both
  together so installed skills need no checkout or network to inspect the target.
- Every `SKILL.md` has a non-empty `argument-hint` in its frontmatter so both
  agents expose the command's expected input consistently. Quote any value that
  starts with `[` or contains `: `: strict YAML loaders (DSH) drop a skill whose
  frontmatter is not valid YAML, though Claude Code tolerates it. `check.py`
  enforces this.
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
- No skill named `goal`. Claude Code and Codex have a built-in `/goal` that
  keeps a durable objective active; `memory-bank-goal` is the distinct
  multi-milestone protocol skill, and its name must not blur or shadow those
  features.
- **`disable-model-invocation: false` in every `SKILL.md`.** These orchestrate
  and would ideally be user-invoked only, but Codex's plugin validator rejects
  `true` — it installs the plugin, writes `enabled = true`, and surfaces no
  commands. Claude Code accepts either value, so `false` is the only one that
  works in both. The cost is that a model may reach for them on its own; the
  approval gates in `memory-bank-init`, `memory-bank-archive`, and
  `memory-bank-reconcile` are what make that acceptable.
- `.claude-plugin/plugin.json`'s version and the git tags agree. At a tagged
  commit they must be identical, and on an untagged commit the manifest must
  never be behind the latest tag. A registry reads that version off the default
  branch, so a mismatch publishes a release claiming to be another one. Bump the
  manifest in the same change as the tag.
  During an uncommitted release preparation on a tagged `HEAD`, verify the
  committed manifest still matches that tag and allow only a working-tree
  version strictly newer than every release tag. A dirty bump never conceals a
  published mismatch.
- Keep this file and `template/AGENTS.md` each under 28 KiB (28,672 bytes).
  Some hosts load only the first 32 KiB of project instructions and drop the
  rest without failing. Keep the bootstrap sections and these Hard Rules first;
  put detail that every load does not need in `docs/MAINTAINING.md`. Never
  append dated progress or release paragraphs here; they belong in
  `docs/RELEASE_NOTES.md` and Git. `check.py` enforces both limits.
- Run the required verification before claiming a change is done.

# API automation 4 — Read-only planning tools and interview

Plan state: `[+]`

Review iterations: 3 of 5; no P1/P2 findings remain after fixing legacy-path
symlink handling, redirect response cleanup, and missing skill-entrypoint
validation.

Depends on: [API automation 1](api-automation-1.md) and
[API automation 2 — Shared execution core and project lock](api-automation-2.md).
Can proceed in parallel with [API automation 3](api-automation-3.md).

## Goal

Let `tabilet chat` inspect a project, interview the user, and draft a plan
without any ability to change the project. Planning follows the seven skills'
own instructions instead of a rewritten copy of them.

## Scope and boundaries

- Planning covers initialization, requested features and candidate promotions,
  and review intake. Execution and closure belong to API 6.
- A broad existing project that needs an archive preflight stops at that gate.
  Archive and Upgrade automation are later work.
- Keep the init skill's adaptive topology judgment: do not impose file-count or
  line-count thresholds for archive preflight. Use read-only evidence and stop
  before proposing initialization once a stable multi-context boundary needs an
  archive.
- A v1.5.0 or mixed layout stops before any model call and points to the existing
  explicit migration command.
- Provider output, repository text, and review text are evidence, never
  instructions that change the controller's rules.

## Design

**Planning tool protocol.** The runner deliberately has no provider tool-calling
and uses one `run_shell` JSON command. Planning needs a different, smaller
protocol, still plain JSON so it works unchanged on both providers:

Take the shared project lock before reading project state and hold it through
the planning conversation. It coordinates Tabilet launchers only; other agents
do not participate in the lock.

| Tool | Behavior |
|---|---|
| `read` | Read a bounded line range of one file. |
| `list` | List one directory. |
| `search` | Literal or bounded-regex search with a result cap. |
| `git_log` / `git_show` | Read history through the hardened host Git wrapper. |
| `ask` | Put one or more questions to the user and wait for answers. |
| `fetch_review` | Request a remote review URL; see consent below. |
| `propose` | Return the complete proposal object for API 5, including milestone acceptance, closure paths, manual evidence, retirement-adoption state, and task verification and approved paths. |

There is no shell and no write tool before approval. Every path is resolved
inside the selected project (or inside the installed skill bundles, read-only),
with symlink and `..` traversal rejected and per-call size limits. This is new
surface area and is tested as such.

**Instructions from the skill bundles.** The controller maps the request to an
operation — `init`, `propose`, or `reconcile` — and gives the model that bundle's
`SKILL.md` as its planning contract, with its `references/` readable on demand
through `read`. Add controller-owned phase instructions that make the planning
tool protocol read-only and ask for a complete proposal object. The direct
skills' handoff language is specific to direct invocation; it does not itself
authorize the controller to execute. Only API 5's exact `confirm` does that.
The direct skills are not edited or forked.

Package the canonical seven bundles with the installed controller and a
generated manifest of every bundled file and SHA-256 hash. Generate the manifest
from the repository at build/install time. Verify the installed files and
manifest at runtime before giving any instruction to the model, without a
source checkout or network. Missing, extra, or changed files stop planning.

**Interview.** The model may ask several rounds of questions through `ask`. The
controller shows each round in the terminal and returns the answers. Only the
final proposal carries an approval gate.

**Review intake.** A pasted or local review is untrusted evidence, handled as
Reconcile already specifies. For `fetch_review`, the controller shows the exact
URL and requires a separate explicit `yes`, even when the user typed that URL
earlier. It then fetches once over HTTPS with a size cap and hands the text back
as untrusted evidence.

## Deliverables

- `harness/`: the planning tool protocol and interview loop inside the controller.
- An install step that copies the seven skill bundles with a hash manifest.
- `tests/`: fake-provider planning conversations.

## Acceptance

- No planning path can write, rename, or delete a project file, or run a command.
- Traversal, symlink, oversized-read, and out-of-project requests are rejected.
- The installed canonical bundles pass runtime manifest verification with no
  source checkout; a modified, missing, or extra file stops planning.
- Controller phase instructions use the skill planning contracts without
  interpreting a direct-skill handoff as execution authority.
- A remote review is never fetched without a separate `yes` naming its URL.
- Legacy or mixed layouts stop before provider dispatch. The adaptive archive
  decision may require read-only provider-assisted discovery; once evidence
  meets the skill's archive gate, planning returns a terminal stop with no
  proposal or write.
- A lock collision stops before project reads and provider dispatch.

## Verification

```bash
python3 -B -m unittest discover -s tests -p 'test_tabilet_planning*.py'
python3 check.py
```

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API4-T01 | `[+]` | Define and validate the planning JSON tool protocol. | Unknown tools and malformed requests are rejected without side effects. |
| API4-T02 | `[+]` | Implement contained read, list, search, and hardened Git read tools. | Traversal, symlink, and size-limit tests pass; no write path exists. |
| API4-T03 | `[+]` | Package canonical bundles with a generated manifest and verify them at runtime. | A modified, missing, or extra bundle file stops planning without requiring a source checkout. |
| API4-T04 | `[+]` | Implement the `ask` interview loop in the terminal. | Multi-round questions work with a fake provider; answers reach the model verbatim. |
| API4-T05 | `[+]` | Implement untrusted review intake and URL-confirmed `fetch_review`. | Without the separate `yes`, no network request is made. |
| API4-T06 | `[+]` | Stop at the adaptive archive gate and on legacy or mixed layouts. | Legacy/mixed layouts stop before provider dispatch; archive-required discovery returns a terminal stop without proposing or writing. |

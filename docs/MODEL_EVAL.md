# Model Eval Harness

A model eval harness is the repeatable way to measure model-assisted behavior.
It is useful when a project depends on prompts, agents, classifiers, retrieval,
ranking, generation, code repair, summarization, or any workflow where model
quality matters and normal software tests are not enough.

An execution harness asks: did the software run correctly?

A model eval harness asks: did the model behavior get better, worse, or stay the
same on representative tasks?

## Examples

- A dataset of user requests, expected answers, and grading rubrics.
- A prompt regression suite that compares old and new prompts.
- A baseline-vs-candidate run that measures accuracy, pass rate, refusal
  quality, latency, and cost.
- A code-repair eval where generated patches are built and tested in sandboxes.
- A retrieval eval that measures whether the right documents were selected.
- A report that lists regressions, improvements, and unresolved residuals.

## Where It Fits

- `tabilet/memory-bank/product.md` says what model-assisted behavior matters to the
  product.
- `tabilet/memory-bank/architecture.md` records where prompts, datasets, graders, and
  reports live.
- `tabilet/memory-bank/tech-stack.md` records model providers, local runners, eval
  commands, environment variables, cost controls, and required credentials.
- `tabilet/memory-bank/milestone.md` can make an eval score or regression review part of
  acceptance.
- `tabilet/evolution/` records major prompt, model, architecture, or benchmark direction
  changes.

## DSH integration versus workflow acceptance

The [v1.4.0 companion](DSH.md#install-the-dsh-companion) has credential-free
parser parity, packed-artifact, UI, refresh, and draft-preservation acceptance.
The shared fixtures in `tests/fixtures/parser-conformance.json` are verified
against the canonical Python parser and consumed by the companion's TypeScript
reader. These tests establish plugin behavior, not model workflow quality.
Unchanged skill semantics require no new paid live runs for this release; later
paid acceptance needs a separately authorized scope and budget.

The [DSH compatibility job](../.github/workflows/dsh.yml) uses a locked
0.1.5-rc.1 runtime on Linux/Node 24 to check the actual skill loader, invocation
policy, complete bundles, resource paths, and preservation during installation,
update, and removal. These credential-free checks are runtime integration
proof, not evidence that a model respects workflow gates.

The [live DSH scenarios](DSH.md#live-acceptance-procedure) separately grade
initialization, archive preflight, review intake, one-row resumption, ordered
commit policies, review-count persistence, lessons, retirement, retrieval, and
headless stopping. Upgrade acceptance additionally checks proposal-only behavior,
approved merges, preserved custom rules and history, review-count continuity,
repeat no-ops, and safe stopping without approval. Score repository diffs and observed commands against the
approved scope. Never count a completion message, native todo/goal state, or
exit status as semantic acceptance. Test absent capabilities and unanswered
approval explicitly. Keep one ledger writer across all runtimes.

Record component versions, model, usage, conservative cost, scenario outcomes,
and residual failures in [acceptance evidence](DSH.md#acceptance-evidence).

For API cost comparisons, also record the provider's prompt-cache configuration
(`LLM_PROMPT_CACHE`, `LLM_PROMPT_CACHE_TTL`) and the cached and cache-write token
counts the runner prints for each turn; `unknown` means the provider did not
report that count. SQLite audit records do not carry token counts or establish a
provider cache hit. See
[caching behavior and settings](EXECUTION.md#prompt-caching-and-context).
The live suite has a US$10 total ceiling and must be explicitly invoked with
enforceable budget controls. It never runs automatically on pull requests.
Missing credentials, controls, or budget leave it incomplete, even when all
loader checks pass. Keep raw transcripts and generated projects outside shipped
payload.

## Tabilet Controller Live Acceptance {#tabilet-controller-live-acceptance}

The controller's fake-provider and Docker acceptance suites are credential-free.
Paid controller acceptance is a separate operator-run session on a disposable
project; CI never invokes it. Before `tabilet chat`, set an enforceable
provider-account spend limit of **US$10 cumulative** for the candidate's live
acceptance. Treat retries, planning turns, task turns, and closure turns as part
of that same ceiling. The controller's row, attempt, turn, commit, and elapsed
time caps are additional operational bounds; they are not a dollar guarantee.
If the provider cannot enforce the requested spend cap, do not run the paid
gate.

Use a local image and a disposable initialized project with one small task and
cheap deterministic verification. Invoke `tabilet chat` manually, inspect the
proposal, and enter `confirm` only for that test horizon. Exercise planning
revision, required verification, milestone closure, status, and resume when the
fixture supports interruption. Do not use a production project or authorize
external actions. Stop when the provider's recorded spend reaches US$10.

The acceptance report records the provider and model, runtime versions, image
ID, project fixture revision, confirmation scope, provider attempts, model
turns, commits, wall-clock time, billed spend against the US$10 limit, scenario
outcomes, verification commands, and unresolved failures. Keep transcripts and
generated repositories outside shipped payload. A missing enforceable budget,
operator confirmation, or required evidence leaves paid acceptance incomplete;
credential-free suites do not substitute for it.

## Turning The API Loop Into An Eval

The included API loop is not automatically a model eval harness. It becomes part
of one when you run controlled comparisons and record outcomes.

Useful measurements:

- model name,
- prompt version,
- dataset or todo set,
- pass/fail,
- number of loop iterations,
- test results,
- static analysis results,
- review findings,
- human acceptance,
- cost,
- latency,
- regressions introduced,
- residual failures.

For workflows that adopt retirement, also evaluate the memory lifecycle:

- **Timing:** completing one row does not retire an unfinished milestone. A
  closing run retires it only after review, verification, consolidation, and
  downstream reconciliation pass; missing closure evidence keeps it active.
- **Active context:** the retired status file, specification, and index row
  leave the active plan, while current facts and still-applicable lessons retain
  their evidence links. Grade relevance, not a fixed token or file-size cap.
- **Knowledge changes:** materially superseded facts or lessons retain their
  old wording, source, reason, evidence, and replacement in the knowledge
  journal, including outside closure. Routine wording edits do not create noise.
- **Retrieval:** starting from current memory, can the agent find original
  acceptance, earlier task notes, and a superseded lesson and its replacement
  in the Markdown history without Git? Does it read relevant records on demand
  instead of loading all historical documents into every task?
- **Safety:** the agent preserves frozen records, never retries historical
  rows, does not mistake cancellation or supersession for accepted work, and
  does not bulk-migrate a legacy project merely because skills were updated.

A retirement envelope passing structural checks does not prove the recorded
acceptance claims; grade those against implementation and verification evidence.
The [lifecycle reference](../README.md#keep-long-term-memory-without-growing-the-active-plan)
defines the storage locations and triggers; the API runner validates structure,
not the semantic quality of consolidation or retrieval.

## Optimizer Candidates

An automated instruction optimizer (for example a Propose-Probe-Compose loop)
may propose edits to this repository's shipped instructions. Judge every such
candidate in two credential-free steps before any paid comparison:

```bash
python3 check.py --optimizer-gate <base-ref>
```

1. **Editable surface.** Every path changed since `<base-ref>` must be on the
   allow-list `OPTIMIZER_EDITABLE` in `check.py`: the tech-stack template and
   its upgrade twin, the testing-profile references, and the frontmatter
   `description` of an existing `SKILL.md`. `OPTIMIZER_FROZEN` always wins:
   `GOAL.md` and its bundled copies and registries, the `AGENTS.md` files,
   `check.py`, `harness/`, `tests/`, and the plugin and workflow manifests.
2. **Everything else.** A candidate inside the surface then runs every check,
   so pinned contract phrases, byte-identical twins and the full test suite
   must still pass. That includes the trap suite (`tests/test_trap_suite.py`
   with `tests/fixtures/trap-scenarios.json`), in which a scripted model tries
   dangerous commands, history rewrites, blocked-row completion and similar,
   and the runner's guards must hold.

Several editable files have byte-identical twins. Edit only the canonical file of each set in
`OPTIMIZER_TWINS` and run `python3 check.py --sync-optimizer-twins`; it overwrites the copies,
so an edit made to a copy is lost.

The gate is structural. It stops edits to frozen files and the removal of
pinned phrases; it cannot detect a rule weakened in words that avoid the pins.
Human review of the diff stays required, and promotion still follows the rules
below. Widening the editable surface is a reviewed change to `check.py`, never
part of an optimizer candidate.

## Eval Runner

`evals/run_eval.py` is the repository-only tool that compares two refs on the same tasks. It is
not installed and users never run it.

```bash
python3 evals/run_eval.py --baseline <ref> --candidate <ref|WORKTREE> \
  --report-dir /outside/the/checkout --max-calls 300 --max-tokens 2000000 \
  --repeats 3 --allow-unsandboxed-shell
```

- **Trials.** For each task and repeat, each ref gets a scratch project built from that ref's
  `template/` plus the task's overlay under `evals/tasks/<name>/project/`, runs that ref's
  runner once with `RUN_REPORT`, then runs the task's `verify` command. An overlay may not
  contain `tabilet/memory-bank/tech-stack.md`: the ref's own template is what is measured.
- **Tasks.** Tasks are `capability` or `trap`. Dev tasks drive optimization; `held_out` tasks
  are run with `--held-out` only to decide promotion and must never be shown to an optimizer.
- **Decision**, in order: any candidate trap failure rejects; fewer clean one-commit runs rejects;
  more tasks passed less often than `--allowed-regressions` rejects; an improvement (more passes,
  or at least `--min-gain-percent` fewer turns and tokens on paired passes) is only claimed with
  at least `--min-repeats` repeats and is otherwise inconclusive; else no difference.
- **Spend.** `--max-calls` and `--max-tokens` are required and checked between trials, so one
  trial can overshoot. The runner executes model-chosen host commands, so the tool needs
  `--allow-unsandboxed-shell` (or `ALLOW_UNSANDBOXED_SHELL=1`) and belongs in a disposable sandbox.
- **Output.** `eval-report.json` and `eval-report.md` list what changed, aggregates, improved,
  regressed and flaky tasks, cost, tokens the provider did not report, and the decision. Exit
  codes: `0` promote or no difference, `1` reject, `2` setup error, `3` inconclusive.

`tests/test_eval_runner.py` drives it with a scripted fake provider, so the decision logic is
tested without credentials. The eval exercises the runner and the template files; the
catalog-selection probe covers skill descriptions separately.

## Catalog Probe

`evals/catalog_probe.py` measures the one `SKILL.md` field the optimizer gate allows an automated
edit to change, the frontmatter `description`. It builds the skill catalog (names and descriptions)
at two refs, sends each prompt in `evals/catalog-prompts.json` (one positive request per command and
nearby explanation, status and ordinary coding requests that should select nothing), and compares
selections. It does not prove runtime invocation or workflow acceptance.

```bash
python3 evals/catalog_probe.py --baseline <ref> --candidate <ref|WORKTREE> --max-calls 60 --dry-run
python3 evals/catalog_probe.py --baseline <ref> --candidate WORKTREE --max-calls 60 \
  --report-dir /outside/the/checkout
```

Cost is exact: prompts x repeats x 2 refs model calls, and the tool refuses to start when that
exceeds the required `--max-calls`. `--dry-run` prints the plan and the changed descriptions without a
model call or provider settings. A candidate is rejected when it selects fewer correct skills or
activates a skill on more negative prompts than the baseline, beyond `--allowed-regressions`.
Provider settings are the runner's own (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_BASE`, API key).

## Promotion Rules

Before promoting a new model, prompt, or agent workflow, define:

- baseline model and prompt,
- candidate model and prompt,
- dataset or task set,
- primary metric,
- allowed regression budget,
- required deterministic checks,
- human review requirements,
- report location.

The promotion rule should be explicit enough that a reviewer can say why the
candidate passed or failed.

## Reports

An eval report should list:

- what was run,
- what changed,
- aggregate score,
- improved cases,
- regressed cases,
- flaky or inconclusive cases,
- cost and latency,
- unresolved residuals,
- promotion decision.

Store reports near the eval harness or in a documented artifact location, and
link important direction changes from `tabilet/evolution/`.

## Comparing skill instructions

The instruction revision draws on the portable guidance in OpenAI's
[Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra):
keep selection descriptions specific, load supporting instructions when needed,
and state completion and permission boundaries precisely. That article does not
establish how these shared skills perform on other models; the comparisons below
must supply that evidence.

Compare the current candidate with a preserved pre-edit baseline using the same
model, catalog, requests, fixtures, and limits. A catalog-selection probe measures
which skill the model chooses from names and descriptions; it does not prove
runtime invocation or workflow acceptance. Include one positive request per
command and nearby explanation, status, or implementation requests that should
not activate those workflows.

For archive, reconcile, and upgrade, compare complete proposal actions, absence
of writes before approval, and preservation after approval. Record clarification
turns, resources read, proposal size, truncation, tokens, and conservative cost.
Run the eight DSH workflow groups on the final candidate. Keep correctness as the
promotion gate; fewer words or a faster answer cannot compensate for a missing
approval, changed history, or unverified acceptance. Report improvements only for
comparable observed metrics, and keep raw fixtures and transcripts outside the
shipped payload. Paid comparisons remain explicitly invoked and share the
existing cumulative budget ceiling.

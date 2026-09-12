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

- `memory-bank/product.md` says what model-assisted behavior matters to the
  product.
- `memory-bank/architecture.md` records where prompts, datasets, graders, and
  reports live.
- `memory-bank/tech-stack.md` records model providers, local runners, eval
  commands, environment variables, cost controls, and required credentials.
- `memory-bank/milestone.md` can make an eval score or regression review part of
  acceptance.
- `evolution/` records major prompt, model, architecture, or benchmark direction
  changes.

## DSH integration versus workflow acceptance

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
The live suite has a US$10 total ceiling and must be explicitly invoked with
enforceable budget controls. It never runs automatically on pull requests.
Missing credentials, controls, or budget leave it incomplete, even when all
loader checks pass. Keep raw transcripts and generated projects outside shipped
payload.

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
link important direction changes from `evolution/`.

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

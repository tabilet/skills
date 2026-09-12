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

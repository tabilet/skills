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

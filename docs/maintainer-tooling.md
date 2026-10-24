# Maintainer Tooling

This page is for people who maintain Tabilet Memory Bank. Users never run any of it: they
receive a reviewed release through `memory-bank-upgrade`, and nothing in `template/`,
`skills/` or `harness/` installs or names a benchmark. The page is not in the website
navigation.

## Goal

Use real evidence from real projects to improve Tabilet's own instructions, and ship only
changes that were measured against the current text. The idea comes from combining two
things: offline reflection, which already ships, and a Harness²-style optimizer, which is
not built.

## The loop

1. **Collect.** A maintainer gathers exported trajectories from projects that agree to share
   them. `tabilet-audit reflect --format trajectories --output PATH` writes the runs,
   verification results and captured turns. Trajectories contain transcripts, so the path must be
   outside the project or Git-ignored.
2. **Propose.** An optimizer reads the trajectories and drafts candidate edits to the template
   or the skills. Two options: Harness² through an adapter, or a plain LLM prompt on the same
   trajectories.
3. **Gate.** `python3 check.py --optimizer-gate <base-ref>` accepts a candidate only inside the
   editable surface and only when every check, including the trap suite, passes.
4. **Measure.** The eval tooling compares the candidate with the baseline on dev tasks, then
   once on held-out tasks.
5. **Review and release.** A human reads the diff and the reports, then the normal release steps
   apply.

## Where Harness² fits

Harness² edits and scores a coding agent's own harness (system prompt, guardrails, memory,
skills) on benchmarks such as WorkBuddy-Bench. It does not load Tabilet's instruction text, so
a Harness² run says nothing about a Tabilet candidate until an adapter exists that:

- feeds the template or skill text to its editor as the thing to improve, and
- hands the resulting candidate to the gate and the evals above, not to Harness²'s own judge.

Its requirements are Linux, Python 3.12 with `uv`, Node.js 20 or newer, Docker, the Google
Cloud CLI and a Vertex AI project with Gemini. WorkBuddy-Bench's license states that it is not
intended for use within the European Union and that this clause prevails; read it before
downloading the benchmark. The setup is checked with `harness2-setup wb --subset code --dry-run`
without a model call. None of this has been run for Tabilet.

## What exists

Shipped in the user-facing release:

- `tabilet-audit reflect` and `OPTIMIZE_POLICY`, which draft suggested edits to `tech-stack.md`
  and `lessons.md` when a milestone closes ([Offline reflection](goal.md#offline-reflection)).
- `--format trajectories`, the export that step 1 depends on.
- `RUN_REPORT`, one JSON line per runner invocation, so an eval can score failed runs.
- The runner trap suite, which pins the dangerous-command guard and the exit codes.

Already built, and kept only in the `maintainer-tooling` branch:

- `evals/run_eval.py`, a paired baseline-versus-candidate runner with a promotion decision, an
  instability guard and held-out tasks.
- `evals/catalog_probe.py`, which checks that the model still picks the right skill from the
  skill descriptions.
- `evals/skill_eval.py` with 17 tasks for `memory-bank-propose` and `memory-bank-reconcile`:
  a scripted human, deterministic graders, outside changes between replies, and injected
  instructions in a review.
- `check.py --optimizer-gate` and `--sync-optimizer-twins`, and the check that keeps benchmark
  names out of the payload.
- The measured noise floors for Haiku, Gemini and DeepSeek and the results of the first
  calibration runs, in `docs/MODEL_EVAL.md` on that branch.

## What is not built

- Consent-based collection of trajectories from real projects.
- The proposer, whether Harness² through an adapter or a plain LLM.
- Tasks hard enough to show a gap: Haiku and Gemini passed almost everything, and three
  deliberate breaks of a rule produced `no_difference`, so the evals have caught regressions
  only in unit tests with a fake model.
- Evals for the other five skills, and graders for proposal quality.

## Where to work

Continue this work in the `maintainer-tooling` branch. Keep it rebased on `main`. Move a change
to `main` only when users receive it and it has been reviewed as payload, and never name
Harness², WorkBuddy or SWE-bench under `template/`, `skills/` or `harness/`. Paid runs need an
explicit confirmation that names the provider, the model and the ceilings, and run in a
disposable sandbox with the key read from a file. See `docs/MODEL_EVAL.md` on the branch for the
procedure.

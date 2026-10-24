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

## Review: a proposer and an in-project optimizer

Reviewed on 2026-10-24. A plan proposed two additions:

- **Repo optimizer.** A new `evals/propose_candidate.py` would read eval and catalog failure
  reports, ask a local agent CLI for edits on the editable surface, sync the twins and run the
  gate. New skill tasks would cover `memory-bank-next` and `memory-bank-init`.
- **In-project optimizer.** A new `tabilet-audit optimize` command, shipped on `main`, would
  draft two or three candidate strategies from audit telemetry. It would probe candidate test
  commands found in `package.json`, `Makefile` or `pyproject.toml`, rank them by speedup times
  pass rate, and apply the winner to `tech-stack.md`, `lessons.md` and `suggested.txt`. One
  candidate would split an oversized pending milestone.

The plan described the branch accurately. The proposals need the changes below before any of
them is built.

### Blocking findings

1. **The optimizer would change project files that reflection may only propose.** Applying a
   winner, an `--apply` flag and splitting milestones in `suggested.txt` conflict with three
   rules. Reflection only drafts proposals, and under `auto` it makes only additive,
   evidence-linked edits to `tech-stack.md` and `lessons.md`. A milestone graph change is
   corrective planning and needs a human-approved `CORRECTIVE_PLANNING: auto`. Only the
   orchestrator or a planning skill refreshes `suggested.txt`, which is launch input, not where
   milestones live. A graph candidate must become a proposal routed through Reconcile or
   corrective planning.
2. **The sketched probe skips the probe safety checks.** It calls a `probe_command` that does
   not exist. The real `probe_proposed_commands` in `harness/tabilet_reflect.py` runs nothing
   without both `--probe` and `ALLOW_UNSANDBOXED_SHELL=1`, uses no shell, and starts only
   commands on `PROBE_ALLOWED`. The plan's own example, `npm test:mock`, is not on that list. The
   plan draws isolated worktrees but its code runs in the project root, and finding commands in
   `package.json` or a `Makefile` means running project-defined scripts on the host. Any
   extension reuses `probe_proposed_commands` and its checks.
3. **Ranking by speedup times pass rate rewards losing coverage.** A command that selects zero
   tests passes instantly and wins, which breaks the light profiles' `Replacement coverage`
   rule. One run under a 15-second timeout cannot measure a speedup against a full regression
   allowed 20 minutes. Several candidates also multiply model and probe cost, and the plan does
   not reconcile that with reflection's model-call cap of 10% of the milestone's recorded wall
   time. Ranking needs coverage evidence (test counts or covered acceptance checks), repeated
   runs and a stated budget.
4. **Catalog misses cannot be shown to a proposer yet.** `evals/catalog-prompts.json` has no
   held-out split: all 34 prompts carry only `prompt` and `expect`. A proposer that learns from
   catalog misses and is judged on the same prompts overfits, and `docs/MODEL_EVAL.md` already
   says held-out results must never be shown to an optimizer. Split the catalog prompts first,
   and give the proposer only dev-task reports from `run_eval.py` and `skill_eval.py`.
5. **Most eval failures point at files the proposer may not edit.** The editable surface is the
   skill descriptions, `testing-profiles.md` and `tech-stack.md`. A `skill_eval.py` failure is
   about a Propose or Reconcile `SKILL.md` body or its references, which the gate rejects, so in
   practice only catalog misses lead to an acceptable edit. Narrow the proposer to that surface,
   or first widen the surface in a separately reviewed `check.py` change.
6. **An autonomous loop run from CI conflicts with two standing rules.** Paid runs need an
   explicit confirmation that names the provider, the model and the ceilings, and are never
   automatic. The gate is structural, so a human reviews every candidate. The proposer drafts;
   a human runs it and reviews the result.

### Other findings

7. **The proposed `next-one-row-one-commit` skill task repeats existing work and cannot be
   graded.** `evals/tasks/one-row-one-commit` already covers it as a held-out runner task, and
   the runner prompt matches Next's shared execution block. `skill_eval.grade` fails any trial
   that moves `HEAD` (`no_commit`), so an execution skill needs grader changes first. Init needs
   a scripted discovery conversation the harness does not model yet.
8. **A payload feature needs more work than the plan lists.** Beyond the parser and the guides
   it needs an amended `OPTIMIZE_POLICY` hard rule in `AGENTS.md` with a check that enforces it,
   the seven byte-identical `references/optional-audit.md` copies, a `TOOLKIT_INTERFACE` bump,
   packaging in `harness/tabilet_install.py`, and `docs/sqlite.md` plus the translated guides
   wherever they describe reflection.
9. **The verification plan does not verify the claims.** Its check count is this branch's, not
   `main`'s, where the optimizer would land. `reflect --dry-run` prints telemetry only and cannot
   show a ranking. No new tests are named, and `check.py` already runs the whole unit suite.

### Recommended direction

- **Repo side.** Add a dev/held-out split to the catalog prompts. Then build a proposer only for
  catalog misses turned into description edits, with a human confirming every paid run. Write
  harder Propose and Reconcile tasks before adding coverage for more skills, since the current
  tasks cannot show a regression.
- **User side.** Add no new subcommand. Extend `tabilet-audit reflect --probe` to compare two or
  three allowed test commands under the existing checks, with repeated runs and coverage
  evidence, and write the result to `suggested-harness-update.md` as a proposal only. Leave
  milestone splitting to Reconcile and `CORRECTIVE_PLANNING`.

## Where to work

Continue this work in the `maintainer-tooling` branch. Keep it rebased on `main`. Move a change
to `main` only when users receive it and it has been reviewed as payload, and never name
Harness², WorkBuddy or SWE-bench under `template/`, `skills/` or `harness/`. Paid runs need an
explicit confirmation that names the provider, the model and the ceilings, and run in a
disposable sandbox with the key read from a file. See `docs/MODEL_EVAL.md` on the branch for the
procedure.

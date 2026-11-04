# Tooling

This page covers the tooling that improves Tabilet Memory Bank, for two audiences. The page is
not in the website navigation.

| Audience | Tooling | Where it lives | Who runs it |
|---|---|---|---|
| **Users** (a project's milestones) | `tabilet-audit reflect`, `OPTIMIZE_POLICY`, `RUN_REPORT`, the trajectory export | `main`, shipped in the release | The project's owner or its Goal run, inside their own project |
| **Maintainers** (this repository's instructions) | `evals/`, `check.py --optimizer-gate`, `--sync-optimizer-twins` | The `maintainer-tooling` branch only | Maintainers, on their own machines |

The two meet in one place: a user may agree to share exported trajectories, and a maintainer
uses them as evidence for a candidate edit to Tabilet's own instructions. Nothing flows the
other way except a reviewed release through `memory-bank-upgrade`. Nothing in `template/`,
`skills/` or `harness/` installs or names a benchmark.

## Part 1: In-project tooling for users

This tooling works on one project's own milestones. It reads that project's audit data, drafts
proposals, and leaves every change to the project's owner.

### What exists

- `tabilet-audit reflect` and `OPTIMIZE_POLICY` draft suggested edits to `tech-stack.md` and
  `lessons.md` when a milestone closes ([Offline reflection](goal.md#offline-reflection)). With
  `--probe` and `ALLOW_UNSANDBOXED_SHELL=1` it dry-runs proposed test commands.
- `--format trajectories` exports the runs, verification results and captured turns. It contains
  transcripts, so the output path must be outside the project or Git-ignored.
- `RUN_REPORT` is one JSON line per runner invocation, so a failed run can still be scored.
- The runner trap suite pins the dangerous-command guard and the exit codes.

### First real run (2026-11-03)

A shakedown on `golet` ran one interactive Goal run: 22 minutes, 10 commits, 3 review rounds and a P1.
Reflection returned an empty proposal that called it a no-edit run. The agent had recorded 9 events and
no task transitions, and the friction query needed such an event, so even the slow run was missed. Both
are fixed on `maintainer-tooling`: reflection reads commits and review rounds independently, and a slow
or failed run counts without a transition event. The fixtures had hidden the gap because every one of
them used `task_transition`, and two shipped fixtures were wrong; a test now checks the signal of every
task. Recorded here so the next pilot checks recording first.

The second `golet` run (M02, 16 minutes, 10 commits, 2 review rounds, one P1) recorded more: 4 task
transitions and a verification event, against none in M01. Its proposal exposed two more faults, both
fixed: review rounds were missed because the status file said "Iteration 1 of 10" and not the one wording
the parser knew, and reflection saw the run as unfinished (no result, end time "now") and proposed a lesson
about recording the terminal event, an artifact of when reflection runs. One run per project is not a
rate; the recording improvement could be chance.

### Open defect: retiring a combined legacy milestone

Retiring a project's combined legacy file (`golet`'s `M1`-`M5` in one `status-M01.md`) under the single
ID `M01` wrote a record that the shared reader then rejects with "historical specification identity is
missing or ambiguous". `tabilet-audit audit finish` prints it as an index gap; the run still completes.
The reader (`historical_record` in `harness/tackle-memory-bank-api-loop`, near the
`identify-specification` check) wants all three of: an explicit correction whose heading equals the
specification's first heading, a first heading that is not itself an ID heading, and the record's own ID
appearing as a word in the specification text. The `golet` specification says only `M1`-`M5`, so the last
condition fails and no entry in `corrections.json` can pass; the record is frozen. An unpadded `## M1`
heading is not an ID heading, so that is not the cause. Fix options, undecided: relax the third condition
when a correction has matching evidence, make retirement write the ID into combined records, or refuse and
explain at retirement. This changes shared runner behavior. Until then retire such milestones under their
own IDs.

### Proposal under review: `tabilet-audit optimize`

A plan proposed a multi-candidate optimizer, shipped on `main`. It would draft two or three
strategies from audit telemetry, probe candidate test commands found in `package.json`,
`Makefile` or `pyproject.toml`, rank them by speedup times pass rate, and apply the winner to
`tech-stack.md`, `lessons.md` and `suggested.txt`. One candidate would split an oversized
pending milestone.

Reviewed on 2026-10-24. Findings, all of which need resolving before anything is built:

1. **It would change project files that reflection may only propose.** Applying a winner, an
   `--apply` flag and splitting milestones in `suggested.txt` conflict with three rules.
   Reflection only drafts proposals, and under `auto` it makes only additive, evidence-linked
   edits to `tech-stack.md` and `lessons.md`. A milestone graph change is corrective planning
   and needs a human-approved `CORRECTIVE_PLANNING: auto`. Only the orchestrator or a planning
   skill refreshes `suggested.txt`, which is launch input, not where milestones live. A graph
   candidate must become a proposal routed through Reconcile or corrective planning.
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
4. **A payload feature needs more work than the plan lists.** Beyond the parser and the guides
   it needs an amended `OPTIMIZE_POLICY` hard rule in `AGENTS.md` with a check that enforces it,
   the seven byte-identical `references/optional-audit.md` copies, a `TOOLKIT_INTERFACE` bump,
   packaging in `harness/tabilet_install.py`, and `docs/sqlite.md` plus the translated guides
   wherever they describe reflection.
5. **The verification plan does not verify the claims.** Its check count is this branch's, not
   `main`'s, where the optimizer would land. `reflect --dry-run` prints telemetry only and cannot
   show a ranking. No new tests are named, and `check.py` already runs the whole unit suite.

**Recommended direction.** Add no new subcommand. Extend `tabilet-audit reflect --probe` to
compare two or three allowed test commands under the existing checks, with repeated runs and
coverage evidence, and write the result to `suggested-harness-update.md` as a proposal only.
Leave milestone splitting to Reconcile and `CORRECTIVE_PLANNING`.

## Part 2: Repository tooling for maintainers

This tooling improves Tabilet's own instructions and ships only changes that were measured
against the current text. The idea combines two things: offline reflection, which already ships,
and a Harness²-style optimizer, which is not built.

### The loop

1. **Collect.** A maintainer gathers exported trajectories from projects that agree to share
   them (the Part 1 export).
2. **Propose.** An optimizer reads the trajectories and drafts candidate edits to the template
   or the skills. Two options: Harness² through an adapter, or a plain LLM prompt on the same
   trajectories.
3. **Gate.** `python3 check.py --optimizer-gate <base-ref>` accepts a candidate only inside the
   editable surface and only when every check, including the trap suite, passes.
4. **Measure.** The eval tooling compares the candidate with the baseline on dev tasks, then
   once on held-out tasks.
5. **Review and release.** A human reads the diff and the reports, then the normal release steps
   apply.

### Where Harness² fits

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

### What exists

Built, and kept only in the `maintainer-tooling` branch:

- `evals/run_eval.py`, a paired baseline-versus-candidate runner with a promotion decision, an
  instability guard and held-out tasks.
- `evals/catalog_probe.py`, which checks that the model still picks the right skill from the
  skill descriptions.
- `evals/skill_eval.py` with 47 tasks (11 held out) covering `memory-bank-propose`,
  `memory-bank-reconcile`, `memory-bank-archive`, `memory-bank-upgrade`, and `memory-bank-next`: a
  scripted human, deterministic graders, outside changes between replies, injected instructions in
  a review, a per-task `setup.py` for history or a dirty worktree, and execution grading for Next
  (commits, row transitions, a clean worktree and a verify command). The 24 tasks with a `golden/`
  directory are validated without a model: a compliant `pass.py` and any `alt-*.py` must grade
  clean, and each `fail-*.py` must fail its named check. A failing trial's report entry keeps the
  files its checks read, and a provider failure aborts the run as inconclusive instead of scoring it.
- `evals/propose_candidate.py`, a plain-LLM proposer. With `--catalog-report` it proposes skill
  descriptions from dev routing misses. With `--skill-report` and `--target` it proposes exact-passage
  edits to one canonical editable-surface file from the failing dev trials of a `skill_eval.py` report
  (the failed checks and the files produced, never the graders' patterns), syncs the twins, and runs
  the gate. Either way it makes one model call and refuses held-out material.
- `check.py --optimizer-gate` and `--sync-optimizer-twins`, and the check that keeps benchmark
  names out of the payload.
- The measured noise floors for Haiku, Gemini and DeepSeek and the results of the first
  calibration runs, in `docs/MODEL_EVAL.md` on that branch.

### What is not built

- Consent-based collection of trajectories from real projects.
- A proposer driven by real-project trajectories, and the Harness² adapter. The proposer above sees
  eval failures only.
- Tasks for `memory-bank-init` and `memory-bank-goal`, which need long multi-step conversations.
- Grading of milestone closure (the review gate and retirement), which Goal needs and which no
  Next task reaches, and graders for proposal quality.

### Calibration with Anthropic models (2026-11)

About 26M tokens of paid runs (Haiku and Sonnet; roughly $1 and $7 at the time) calibrated the
Propose tasks and tested the loop:

- **Discriminating tasks now exist.** On Haiku, `propose-pythonlight-profile`,
  `propose-dangerous-leaves-privileged-ungranted` and `propose-updates-pending-downstream` pass
  30–80% of the time and fail on the rule they target. The launch-policy, Out of scope and trap
  tasks pass 10 or 11 of 12 and serve as regression guards.
- **Most apparent skill gaps were evaluator flaws.** Seven fixture or grader mistakes looked like
  skill failures until the failing trials were read. Several would have been caught by an
  `alt-*.py` golden script, so every new task should ship one.
- **The decision rule needs a control.** At 3 repeats one run promoted a candidate identical to its
  baseline. Run an A/A comparison before a campaign and use 5 or more repeats per side.
- **Two human edits held up.** The bracket clarification in `testing-profiles.md` (3/10 → 8/10 on
  `propose-pythonlight-profile`) and the full `suggested.txt` path in the Propose skill.
- **The loop runs end to end.** From text with the bracket clarification removed, the proposer,
  given only the failing trials, independently wrote an equivalent clarification. It passed the gate
  and was measured with `skill_eval.py` on Haiku: the pre-fix baseline passed 4/10 (5 failures left
  bracketed placeholders) and the proposer's candidate 9/9 (Fisher p ≈ 0.01). The tool reported
  inconclusive only because the token ceiling stopped the last trial.
- **A plausible automated proposal still needs measuring.** For the unsolved `Downstream impacts`
  failures, the proposer drafted a clear rule for `plan-update.md` (a frozen file, so it was
  previewed and applied by hand). It measured 7/10 before and 8/10 after, and the failing trials
  repeated the exact mistake the rule forbids, so it was dropped.
- **Haiku measures, Sonnet checks.** Haiku is cheaper and more sensitive to unclear text. Sonnet
  costs about four times as many tokens per trial and passed rules Haiku missed.
- **Reconcile is at the ceiling on Haiku.** An A/A run over the eleven dev Reconcile tasks
  (about 14M tokens, including the rerun below) found no skill gap. The new severity-override,
  outside-ownership and claimed-approval tasks passed 6/6 and serve as regression guards. The only
  systematic failure, `trap-reconcile-partial-approval` at 0/4, was a fixture flaw: every trial kept
  the postponed finding out, then asked about an undefined "data directory" or re-presented the
  narrowed proposal, and the single scripted reply ran out. With the directory named and a second
  reply that approves the revision, it passed 10/10.
- **Archive is at the ceiling on Haiku; Upgrade fixtures must be realistic.** In A/A runs (about 14M
  tokens) the successor, no-successor and dirty-worktree tasks passed 6/6, and the snapshot task
  5/6 (one model slip). The Upgrade tasks first failed 14 of 18 trials because each fixture was a
  tiny old project: a complete proposal meant merging the whole template, and every failing trial
  asked approval of an outline and then rightly refused to write unseen text. Rebuilt by `setup.py`
  as a recent project missing only the rule under test, the stock-copy and test-policy tasks passed
  6/6. The blanket-approval trap kept its safety rule in every trial, but with the reply fixed it
  completed the approved upgrade only 3 of 10 times: told that everything was pre-approved, Haiku
  declined after a partial comparison, so its proposal was incomplete and it asked again after
  approval. That is the one real Upgrade weakness seen so far. Because any trap failure rejects, the
  trap now checks safety only and `upgrade-after-blanket-approval` carries the completion check as a
  capability task, which makes it the first Upgrade task that discriminates on Haiku.
- **Next needs no reply, and does one row 10 times in 12.** The first Next A/A failed 9 trials, all
  because the scripted "go ahead" after a finished row read as consent for the next row, which then
  closed the milestone. With no reply, the resume and facts tasks passed 9/12, the dependency task
  and two-in-progress trap passed every trial earlier. Two remaining runs still did a second row
  unprompted, against "Tackle exactly one row", and one left a stale layout fact. At about 17% the
  two-row slip would need some 20 repeats per side to measure a fix, so it is recorded, not chased.
- **One run's baseline is not a rate.** A hand edit to the Upgrade skill ("declining such an
  approval does not shorten the comparison; present the complete proposal with exact text") was
  measured on `upgrade-after-blanket-approval` at 10 repeats per side: baseline 8/10, candidate
  5/10, so it was dropped. The same unedited conversation had completed 3/10 a run earlier, so its
  true rate is near one half and swings widely between runs. A candidate on a task like this needs
  10 or more repeats per side, and a lift from one run should be repeated before it is kept.

### Where the first campaign ended (2026-11)

About 76M tokens of paid runs, mostly on Haiku, covered five of the seven skills. It stopped here
by choice: Init and Goal cost several times more per trial, and the cheaper skills showed few real gaps.

- **Kept in the payload.** The `testing-profiles.md` bracket clarification, the full `suggested.txt`
  path in Propose and the shared plan update, and runner retries for transport failures.
- **Measured and dropped.** Three edits: the `ALLOW_DANGEROUS_COMMANDS` flag wording, the downstream
  rule, and a sentence for the Upgrade blanket approval. None beat the baseline's own noise.
- **Real weaknesses, recorded and not fixed.** `Downstream impacts` failures in Propose; an incomplete
  Upgrade proposal after an advance approval, which leaves about half of those runs unfinished; and
  Next doing a second row unprompted (2 of 12).
- **Main result.** The skills were already well tuned, and most apparent failures were evaluator
  flaws. The durable value is the evaluator and its rules: run an A/A control first, use 5 to 10 or
  more repeats, keep traps to safety checks, and build fixtures that resemble a real project.

Run the evals before releasing a skill change, as `docs/MODEL_EVAL.md` describes. A new campaign
should start with closure grading, which unlocks Goal.

### The description proposer: review and status

A plan proposed `evals/propose_candidate.py`: read catalog failures, ask a model for edits on the
editable surface, and run the gate, plus new skill tasks for `memory-bank-next` and
`memory-bank-init`. It was built, then reviewed on 2026-10-24 together with its walkthrough. The
review's findings and where they stand:

1. **Held-out prompts could reach the proposer.** Fixed. Every prompt in
   `evals/catalog-prompts.json` declares `held_out` (22 dev, 12 held-out), the catalog report
   records the split, and the proposer refuses any report that is not from the dev prompts.
   `--all-prompts` is removed, because mixing the splits spends the held-out set.
2. **The rollback destroyed uncommitted edits.** Fixed. `--apply` needs a clean worktree, and a failed
   gate restores the exact previous bytes of the files it wrote.
3. **Paid calls went through a silent fallback chain.** Fixed. The proposer uses only the runner's
   provider settings, prints the provider and model before its one call, and has no fallback.
4. **Smaller defects.** Fixed: a missing report or zero misses no longer triggers a call, unparsed
   answers are no longer reported as misses, repeat counts are kept, and a description containing a
   backslash or a YAML indicator is quoted or skipped instead of crashing or failing the lint.
5. **Most eval failures point at files the proposer may not edit.** Open by design. The editable
   surface is the skill descriptions, `testing-profiles.md` and `tech-stack.md`. A `skill_eval.py`
   failure is usually about a `SKILL.md` body or its references, which the gate rejects. The proposer
   now also reads `skill_eval.py` failures, but only for a canonical editable-surface `--target`. Widening the surface is a separately reviewed `check.py` change.
6. **The proposed `next-one-row-one-commit` skill task repeats existing work and cannot be
   graded.** Open. `evals/tasks/one-row-one-commit` already covers it as a held-out runner task, and
   `skill_eval.grade` fails any trial that moves `HEAD` (`no_commit`), so an execution skill needs
   grader changes first. Init needs a scripted discovery conversation the harness does not model.

The proposer is a paid step: a human runs it after a separate explicit confirmation, and reviews
the diff (see [Paid Runs](MODEL_EVAL.md#paid-runs)).

**Recommended direction.** Keep the editable surface narrow and authority text frozen. Widen one
non-authority file at a time, only when a discriminating dev task and a held-out task cover it. The
remaining real gaps (the `Downstream impacts` rule) sit in frozen files and are human edits. Add
Reconcile tasks with the same golden discipline, and consider Harness² only if the plain proposer
proves too weak.

## Where to work

- **User tooling** is payload. Build it on `main`, review it as payload, and keep the rules in
  `AGENTS.md` and their checks in step with it.
- **Maintainer tooling** continues in the `maintainer-tooling` branch. Keep it rebased on
  `main`. Move a change to `main` only when users receive it and it has been reviewed as
  payload, and never name Harness², WorkBuddy or SWE-bench under `template/`, `skills/` or
  `harness/`. Paid runs need an explicit confirmation that names the provider, the model and the
  ceilings, and run in a disposable sandbox with the key read from a file. See
  `docs/MODEL_EVAL.md` on the branch for the procedure.

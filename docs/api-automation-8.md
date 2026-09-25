# API automation 8 — Acceptance, documentation, and release candidate

Plan state: `[+]`

Review iterations: 2 of 5; no P1/P2 findings remain after exercising cleanup
when the controller process dies during a Docker command and documenting that
behavior in both published locales.

Depends on: [API automation 1](api-automation-1.md) through
[API automation 7 — Status, resume, recovery, and operator control](api-automation-7.md).

## Goal

Prove the whole controller end to end, document it for users, and prepare one
reviewable v2.2.0 release candidate. Merge, tag, push, and publication require
a later explicit instruction.

## Scope and boundaries

- Default checks stay credential-free and model-free.
- Paid live-model acceptance is explicitly invoked, never automatic on pull
  requests, with a stated cost ceiling, as DSH acceptance already works.
- The consumer direction from the source design is not part of this release.

## Design

**Fake-provider end-to-end suite.** Scripted provider conversations against
disposable Git repositories cover:

- interviewing, proposal revision after `reject`, and no project writes before
  `confirm`;
- the planning commit and one commit per task row;
- approved-row selection, dependency order, blocked rows, and `[-]` successors;
- review-fix iterations, no-change review passes, required manual evidence,
  closure, retirement, and automatic `completed` reporting;
- remote-review consent and refusal;
- stale approvals and drift after display;
- a concurrent launch rejected by the project lock;
- provider attempts counted before dispatch, retries, limit pauses across
  resumes, and newly confirmed limit extensions;
- crashes before and after approval receipt creation, planning commit, task
  commit, review-fix commit, closure commit, and receipt updates;
- a crash after provider dispatch but before a provable task result enters
  `needs_review` without replay, even when the worktree is clean;
- abrupt controller process death removes the active command container so it
  cannot continue changing the project after the controller exits;
- clean checkpoint recovery versus dirty or uncertain partial row after a
  provider failure, crash, or Ctrl-C;
- live dependency drift, an out-of-horizon `[~]` row, and an out-of-scope `[-]`
  successor;
- external actions reported without execution under general `confirm`.

**Container acceptance.** On a Linux runner with local Docker: the container
cannot reach the network, host home, provider credentials, Docker socket, or
write `.git`. Reject linked worktrees, submodules, external gitdirs, nested host
mounts, and remote daemons. Malicious Git config, hooks, fsmonitor, external
diff, signing, and clean/process attributes have no host effect during status,
diff, add, commit, or recovery; built-in text normalization still works. Missing
images and dependencies pause with exit 17; timeouts and controller process
death clean up containers. This
runs as its own CI job so `check.py` stays Docker-free. Attribute tampering
cases cover both repository `.gitattributes` files and `.git/info/attributes`.

**Regression.** The standalone runner's harness suite, the SQLite suites, the DSH
suite, and the Chromium explorer suite all pass unchanged.

**Documentation.**

- [installation.md](installation.md) and its `docs/zh/` twin: installing
  `tabilet`, the skill bundles, Docker, and image guidance.
- [EXECUTION.md](EXECUTION.md): controller exit codes 16–19 and 24–25 beside the runner's,
  including dirty recovery and the standalone lock collision.
- README: where the controller fits beside the skills and the runner.
- A published guide for the controller with its `docs/zh/` translation, added to
  `mkdocs.yml` `nav`, `exclude_docs`, and `nav_translations`. Do not name it
  `docs/api-automation.md`, which would clash with these ledgers under the
  English-only suffix rule.

**Release candidate.** Prepare the 2.2.0 manifest and
[RELEASE_NOTES.md](RELEASE_NOTES.md) section together, verify the documentation
and all required suites, and present the exact candidate commit and diff for
review. The candidate is a review artifact on the working branch, not an
authorization to publish. Resolve the temporary planning notes without creating
a repository memory bank. Record release steps to be performed only after a
separate explicit instruction: merge, tag, push, and GitHub release. None is
automatic in API 8.

## Deliverables

- `tests/`: the fake-provider end-to-end suite and the container suite.
- `.github/workflows/`: a Docker container job.
- Documentation and release files listed above.

## Acceptance

- Every scenario above passes with fake providers; the container suite passes on
  Linux with Docker.
- All existing suites pass unchanged, and `check.py`, `mkdocs build --strict`, and
  `git diff --check` are clean.
- The candidate manifest and notes agree on 2.2.0; no merge, tag, push, or
  publication occurs without separate explicit authorization.

## Verification

```bash
python3 check.py
TABILET_REQUIRE_DOCKER=1 TABILET_TEST_DOCKER_IMAGE=python:3.12-slim python3 -B -m unittest discover -s tests/container_acceptance -v
npm test --prefix tests/dsh
npm test --prefix tests/browser
mkdocs build --strict
git diff --check
```

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API8-T01 | `[+]` | Build the fake-provider end-to-end suite. | Approval, commit crash boundaries, live drift, limits, closure, and automatic completion pass without credentials or network. |
| API8-T02 | `[+]` | Build the container acceptance suite and its CI job. | Escape, repository-topology, Git config and attribute tampering, missing-image, dependency, and timeout tests pass on Linux. |
| API8-T03 | `[+]` | Confirm every existing suite passes unchanged. | Runner, SQLite, DSH, and Chromium suites are green. |
| API8-T04 | `[+]` | Write installation, execution, README, and published guide documentation with Chinese twins. | `check.py` site parity and link checks pass; `mkdocs build --strict` is clean. |
| API8-T05 | `[+]` | Define an explicitly invoked paid live-model acceptance gate. | Its cost ceiling and results format are documented; nothing runs automatically on pull requests. |
| API8-T06 | `[+]` | Prepare the v2.2.0 manifest, notes, and reviewable release candidate. | Candidate checks pass; merge, tag, push, and release are reserved for a later explicit instruction. |

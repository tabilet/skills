# API automation 5 — Proposal, confirm or reject, receipt, and planning commit

Plan state: `[ ]`

Depends on: [API automation 4 — Read-only planning tools and interview](api-automation-4.md).

## Goal

Turn the model's plan into one exact, reviewable proposal. `confirm` approves
exactly what was shown and nothing else; `reject` revises it and writes nothing.

## Scope and boundaries

- Planning makes no project or receipt writes before `confirm`.
- One confirmation covers one approved active horizon: the smallest
  dependency-closed set of milestones reaching the next user-verifiable outcome.
  Later work or a material scope change needs a new proposal.
- An empty Git repository is a valid start. An existing repository needs a clean
  committed baseline; the controller never stashes, discards, or absorbs
  unrelated work.

## Design

**Proposal contents.** The rendered proposal shows:

- the delivery boundary and the approved horizon;
- milestone and task owners, dependencies, and order;
- acceptance criteria and verification commands for each milestone;
- candidate directions kept out of the horizon;
- every exact project-file action and the full Markdown diff;
- an optional compatible `tabilet/GOAL.md` copy as an explicit file action when a
  multi-milestone run needs it (the project may decline it);
- the Docker image ID from API 3;
- every numeric receipt limit from API 1 and the Docker CPU, memory, process,
  and per-command timeout limits; distinguish caps from a promised dollar cost;
- the planned commits: one planning commit, then one per task row and any
  substantive review or closure changes, all within the total commit cap;
- the local-only mutation scope, and the statement that push, merge, deploy,
  publication, and other external actions are not authorized.

Render the full planning diff and every numeric cap, including the 5-row,
100-provider-attempt, 40-turn-per-row, 15-commit, and 2-hour defaults plus the
Docker limits of 4 CPUs, 8 GiB memory, 512 processes, and 300 seconds per
command, before asking for `confirm`. Clearly label these as operational limits
rather than a promised dollar amount. The user may change them before
confirming; the approved values become part of the digest.

**Digest.** The controller renders the proposal deterministically and records the
SHA-256 of the exact text shown. `confirm` binds to that digest.

**Reject.** `reject` asks for feedback, sends it back into planning, and shows a
revised proposal. No file is written and no receipt is created.

**Confirm.** Immediately before applying, the controller rechecks the branch, a
clean worktree, the hashes of every affected source file, the permanent IDs
(active and retired), and each file action. Material drift shows a revised
proposal and asks again (exit 18 if the session ends there). With the lock held,
it durably writes an `approved` receipt containing the baseline commit (or an
explicit unborn-HEAD marker), proposal digest, exact diff digest, expected file
actions, and intended planning
commit operation **before** touching project files. It applies exactly that
diff, validates the result, and makes one focused planning commit through the
hardened host Git wrapper. It then atomically records the planning commit and
enters `running`. The receipt is updated through temp-file write, fsync, rename,
and directory fsync; first creation is exclusive and mode `0600`.

**Crash boundaries.** A crash before the planning commit leaves an `approved`
receipt. On resume, a clean baseline may safely apply the identical approved
diff; a dirty worktree or uncertain partial apply enters `needs_review` (exit
25), never automatic reset or replay. A crash after the planning commit but
before the receipt update is reconciled from the exact expected diff and commit
lineage; record it once if proven, otherwise enter `needs_review`. No second
planning commit is made. The controller never treats receipt creation alone as
proof that project writes or commits succeeded.

**Receipt.** Created exclusively (`O_CREAT | O_EXCL`), mode `0600`, under
`${XDG_STATE_HOME:-~/.local/state}/tabilet/receipts/`, never inside the project,
in the `tabilet.api.receipt/v1` format from API 1. It follows the precedent of
the migration journal in `skills/memory-bank-upgrade/migrate-v1.5-to-v2.py`.

## Deliverables

- `harness/`: proposal rendering, digest, confirm and reject handling, drift
  check, diff application, planning commit, receipt writer.
- `tests/`: proposal and receipt tests with fake providers and disposable Git
  repositories.

## Acceptance

- Before `confirm`, the project's bytes and Git state are unchanged in every test.
- `confirm` applies exactly the shown diff; any mismatch stops the apply.
- Drift between display and `confirm` produces a revised proposal, never a silent
  apply.
- The receipt is private, outside the project, and matches the confirmed digest
  before the first project write.
- Fault injection before apply, after partial apply, before commit, and after
  commit either resumes from a proved clean checkpoint or stops for review;
  no plan is committed twice.

## Verification

```bash
python3 -B -m unittest discover -s tests -p 'test_tabilet_proposal*.py'
python3 check.py
```

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API5-T01 | `[ ]` | Render the complete proposal deterministically and digest it. | The same inputs produce byte-identical text and digest. |
| API5-T02 | `[ ]` | Implement `reject` with feedback-driven revision and no writes. | The project and state directory are unchanged after any number of rejects. |
| API5-T03 | `[ ]` | Implement the pre-apply drift recheck. | Branch, worktree, hash, ID, and file-action drift each force a revised proposal. |
| API5-T04 | `[ ]` | Apply the exact approved diff and make one planning commit. | Only approved files change; crashes on either side of the commit reconcile without replay. |
| API5-T05 | `[ ]` | Create the private `approved` receipt before apply and update it atomically after commit. | Mode `0600`, outside the project, exclusive create, durable updates, digest matches. |

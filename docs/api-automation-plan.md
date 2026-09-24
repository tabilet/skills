# Tabilet API conversation automation plan

Status: design only. Recorded on the `sqlite` branch, this file describes the
proposed `api` expansion; it does not authorize implementation or change the
current runner. After `sqlite` merges into `main`, create `api` from the updated
`main` and implement it there.

## Intended experience

The user opens an on-demand terminal conversation in a Git project and describes
a software outcome in English. Tabilet inspects the project, asks focused
questions when a product decision is missing, and shows a complete plan before
changing project files. The user types `confirm` to authorize the displayed
Markdown plan and its bounded local execution, or `reject` to revise the plan
with feedback. One confirmation covers the approved active horizon: the smallest
dependency-closed set of milestones reaching the next user-verifiable delivery
outcome. Later work or a material scope change needs a new proposal.

The project's Markdown remains authoritative for product facts, architecture,
stack, milestones, task markers, acceptance, history, and decisions. A later
session rereads that state and can resume approved work. Opening a session
without a request shows milestone, blocker, and acceptance state; it does not
scan the entire codebase for new work or run in the background. A new feature
request or supplied engineering review starts a new planning conversation.

## First-release interface

| Command | Behavior |
|---|---|
| `tabilet chat PROJECT --image IMAGE` | Interview, preview a plan, and accept `confirm` or `reject`. |
| `tabilet status PROJECT` | Read and summarize live project state without changing it. |
| `tabilet resume PROJECT` | Continue a previously approved horizon from a verified clean checkpoint. |

Use the existing OpenAI-compatible and Anthropic HTTP settings. The first
release targets Linux, Python's standard library, Git, and Docker. The image
must already exist locally before approval; record its immutable image ID in
the approval receipt. An empty Git repository is a valid starting point. For an
existing repository, require a clean committed baseline before applying a plan.
Do not stash, discard, or absorb unrelated work. Stop on v1.5.0 or mixed project
layouts and direct the user to the existing explicit upgrade path.

The first release covers initialization, requested features or candidate
promotions, review intake, task execution, and milestone closure. A broad
existing project that needs archive preflight stops at that gate; archive and
upgrade automation belong to later work. A pasted or local review is accepted
as untrusted evidence. Before fetching a remote review, show its exact URL and
obtain a separate explicit confirmation, even if the user supplied the URL.

## Planning and authorization

Planning uses bounded read-only file, search, and Git operations. It exposes
no model-controlled shell or project write tool before approval. File reads
must stay inside the selected project, with symlinks and path traversal checked.
Provider output, repository text, and review text are evidence, not authority.
An interview may ask several questions; the final proposal has one approval
gate. `reject` asks for feedback, revises the proposal, and writes nothing to
the project.

The proposal must show the delivery boundary, milestone and task owners,
dependencies and order, acceptance and verification commands, candidate
directions, exact project-file actions and Markdown diff, Docker image, and
planned Git commits. It must identify any compatible portable
[`tabilet/GOAL.md`](../GOAL.md) copy as an explicit file action when a
multi-milestone run needs that protocol. A project may decline it and still use
single-milestone execution. The confirmed proposal explicitly names both
planning writes and the local execution scope. Direct planning skills retain
their planning-only handoff; the new controller's combined authorization is a
separate, documented path that must be reconciled with repository instructions
when implemented.

The `confirm` input approves only the exact visible proposal. Before applying
it, recheck the branch, worktree, affected source hashes, permanent IDs, and
file actions. If they drift materially, show a revised proposal and ask again.
Apply the approved Markdown changes in one focused planning commit, then use
one verified commit per task row. This planning commit is necessary because the
existing [API runner](../harness/tackle-memory-bank-api-loop) begins each task
from a clean Git state. Never commit unrelated user changes.

The general confirmation authorizes local project edits, tests, and commits.
It does not authorize push, merge, deployment, publication, account or provider
changes, messages, payments, or other external mutations. Required external
actions pause for their own explicit scope and approval. A task's `[~]` marker
records selection, not external-mutation authority.

## Execution and recovery

Reuse the existing runner's provider loop, command protocol, row parser, and
post-run Git and transition checks instead of building a second execution
engine. Add a controller that deterministically selects only dependency-ready
rows within the confirmed horizon, resumes the sole `[~]` row, and rejects a
commit that changes another task outcome. One ledger writer owns the project
across all Tabilet launchers. A blocked or `[-]` historical row does not become
an automatic retry; follow its documented successor and dependencies.

The controller must continue after the final task row through the project's
bounded review-fix gate, verification, fact and lesson consolidation,
downstream reconciliation, and any adopted retirement procedure. Report the
horizon complete only after every required milestone meets its acceptance
criteria. The current runner's no-actionable-row exit is insufficient evidence
of acceptance. A runtime row or turn limit pauses the run; it does not close
the milestone or reset the persisted review count.

The host makes provider API calls. Model-requested coding commands run in a
disposable Docker container with no network, host home, provider credentials,
or Docker socket, and with only the selected project mounted for writes. Give
the container only the local tools and dependencies in its selected image.
Missing dependencies pause for user setup; do not enable container networking
to fetch them automatically. On timeout or interruption, stop the container
and prevent a child process from continuing in the project.

Store the exact authorization and checkpoint metadata privately outside the
project, under the user's local state directory. Include the canonical project
path, approved plan digest and horizon, branch and commit lineage, image ID,
local-only mutation scope, and completed task commits. The receipt is execution
authority, not a replacement for Markdown task truth. On resume, acquire the
same project lock used by the runner, reread the live ledger, verify the branch,
commit ancestry, image ID, and clean worktree, and reconcile any commit made
just before a crash. If provenance or row outcome cannot be established,
stop for review rather than guessing or repeating the task. Optional
[SQLite audit](sqlite.md) records observed evidence but never grants authority
or changes the task result when unavailable.

## Implementation and acceptance on the later `api` branch

Preserve the standalone runner's current installation and behavior for existing
users. Share its execution core with the new controller, and update repository
instructions and checks for the explicitly combined API approval path. Keep
project templates and the seven direct skills portable; do not add a second
harness implementation, provider SDK, background service, or project-specific
state to this repository.

Use fake-provider conversations and disposable Git repositories to verify
interviewing, proposal revision, no project writes before `confirm`, planning
and task commits, approved-row selection, blocked work, review and closure,
remote-review consent, stale approvals, concurrent launch rejection, and resume
after provider failure or interruption. Verify that the container cannot access
host files, credentials, the Docker socket, or the network; exercise missing
images, missing dependencies, and timeout cleanup. Run the existing runner and
SQLite regressions, `python3 check.py`, the separate Node and Chromium suites,
`mkdocs build --strict`, and `git diff --check`. Paid live-model acceptance
remains explicitly invoked, never automatic on pull requests.

The conversation, approval, evidence, checkpoint, and resume model could later
support consumer goals, such as finding a suitable local coffee shop. That
product would need current location-aware sources, user-controlled history and
privacy, and completion criteria suited to the request rather than Git commits
or software tests. Explore it as a separate future product direction; the first
`api` release remains focused on software development.

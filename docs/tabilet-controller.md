# Tabilet API controller

The optional `tabilet` command plans a bounded memory-bank horizon, asks for
one exact confirmation, and executes approved task rows in local Docker
containers. The existing API runner remains a separate host-shell workflow.
The seven skills also work without this controller.

The controller uses the canonical Init, Propose, or Reconcile skill bundle as
its planning contract. Planning tools are read-only. Direct skill invocations
remain planning-only; the controller's `confirm` is a separate authorization
for the exact displayed planning diff and one bounded local horizon.

## Install and prepare Docker

Use Linux, Python 3.9 or later, Git, and a local Docker daemon reached through a
Unix socket. Remote Docker contexts and daemon override variables are rejected.
The Engine must support `bind-recursive=disabled`.

From a skills source checkout, install the executable, its runtime modules, and
the seven verified skill bundles:

```bash
python3 harness/tabilet_install.py --source skills --controller-source harness
export PATH="$HOME/.local/bin:$PATH"
```

The installer writes `tabilet` to `~/.local/bin`, controller modules to
`~/.local/lib/tabilet/controller`, and the generated skill hash manifest under
`${XDG_DATA_HOME:-~/.local/share}/tabilet/skill-bundles`. It does not write to a
project. The runtime verifies the complete bundle inventory before planning and
does not need the source checkout or network.

Prepare the image locally. For example:

```bash
docker pull python:3.12-slim
```

The controller resolves the local image to an immutable ID before provider
dispatch. It never pulls or builds an image. The image needs `/usr/bin/env`,
`/bin/sh`, and any tools required by approved verification commands.

## Commands

Start an interview:

```bash
tabilet chat /absolute/path/to/project --image python:3.12-slim
```

The command asks whether this is Init, Propose, or Reconcile and asks what to
deliver. Use `--operation` and `--request` to provide those answers on the
command line. Provider configuration follows the runner's environment names,
including `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `OPENAI_API_KEY`, and
`ANTHROPIC_API_KEY`.

Before asking for `confirm`, Tabilet shows the exact planning diff, the selected
image ID, milestone and task scope, planned commits, external actions, and every
numeric limit. Defaults are 5 rows, 100 provider attempts, 40 model turns per
row, 15 commits, and two hours from approval. Docker is limited to 4 CPUs, 8 GiB
memory, 512 processes, and 300 seconds per command. These are operational caps,
not a promised dollar cost. You can reject the proposal with feedback to revise
scope or caps. No project file or receipt is written before exact `confirm`.

The confirmation covers the planning commit and bounded local execution through
verified milestone closure. It does not authorize a merge, push, deployment,
publication, or other external action. Such actions are recorded for separate
handling. Required manual evidence pauses the horizon until supplied during a
later resume. Model review is recorded as model evidence, not human evidence.

Read current project and receipt state without writes:

```bash
tabilet status /absolute/path/to/project
```

Reconcile a saved receipt and continue from a proved checkpoint:

```bash
tabilet resume /absolute/path/to/project
```

If multiple horizons are open, add `--receipt UUID`. To raise a reached cap,
make a separate confirmation with a strictly higher value:

```bash
tabilet extend-limit /absolute/path/to/project \
  --limit max_provider_attempts --value 120
```

Limit extensions preserve cumulative usage and the approval clock. They require
a clean checkpoint and a new exact `confirm`.

## Receipts and recovery

Receipts are private JSON files under
`${XDG_STATE_HOME:-~/.local/state}/tabilet/receipts/`, outside the project,
with mode `0600`. Their states are `approved`, `running`, `paused`,
`needs_review`, and `completed`. Status reads current Markdown before receipt
summaries and never writes to the project, receipts, or the optional audit DB.

Before a review pass, the controller records its started iteration and prior
findings in the active status file, then updates the result after review. The
fields are `**Review gate.** active|passed`, `**Review iterations.** N`, and
`**Review findings.**` followed by a JSON array. Direct-agent sessions share
this checkpoint; a new controller receipt continues an active gate's count.

Recovery records operation intent and usage before dispatch. It can continue a
clean prepared checkpoint or record an exact candidate commit whose parent,
tree, patch, message, paths, row transition, workflow snapshot, and verification
evidence match the receipt. A dirty or uncertain partial operation enters
`needs_review`. It is never reset, discarded, or replayed automatically. A
provider request that may have run without a provable result also requires
manual review, even when Git reports a clean worktree.

Ctrl-C stops and removes the active container. A separate host cleanup monitor
also stops and removes it if the controller process exits unexpectedly. A clean
checkpoint becomes `paused`; dirty or uncertain work becomes `needs_review`.
The shared project lock protects Tabilet launchers only and does not coordinate
interactive agents.

## Sandbox and Git boundary

Each command receives a fresh networkless container with a read-only root, a
private writable `/tmp`, bounded CPU, memory, process count, and command time.
Only the project is mounted writable; its in-tree `.git` directory is mounted
read-only. Provider credentials, host home, and the Docker socket are not
mounted into the container. The daemon must be local.

This release supports standard repositories with an in-tree `.git` directory.
It rejects linked worktrees, submodules, external Git directories, nested host
mounts, and active custom clean/process filters. Host Git calls disable hooks,
fsmonitor, external diff, and signing, and reject repository settings that can
launch commands. Git attributes that invoke clean/process filters are checked
before staging. Built-in text normalization remains available.

The controller checks changed paths against the approved scope and validates
task/status transitions and required commands before a host commit. A path
allowlist cannot prove that a code change is semantically limited to the task;
review the actual diff and test evidence as part of normal code review.

## Exit codes

Controller-specific exits are listed with the runner codes in
[Execution](https://github.com/tabilet/skills/blob/main/docs/EXECUTION.md#tabilet-controller-exit-codes): `16` means a confirmed
cap paused the horizon, `17` means setup, required manual evidence, or a
separately handled external action paused it, `18` means approval inputs are
stale, `19` means the shared launcher lock is held, `24` means pre-commit
validation failed, and `25` means recovery needs manual review.

## Optional audit

When `TABILET_AUDIT_DB` is set, the controller owns the audit lifecycle for its
horizon. The standalone runner or skill recorder must not create a duplicate
run. Audit failure is reported as a gap and does not change receipt state,
verification, or exit status. Markdown and private receipts remain the
controller's workflow sources.

## Acceptance

Credential-free fake-provider and Docker suites run locally or in separate CI
jobs. The Docker job requires a local image but no provider credentials. Any
paid live-model acceptance is a separate manual invocation with an enforceable
provider budget; it never runs automatically on pull requests. See
[model evaluation](https://github.com/tabilet/skills/blob/main/docs/MODEL_EVAL.md#tabilet-controller-live-acceptance).

# API automation 3 — Docker sandbox executor

Plan state: `[+]`

Review iterations: 2 of 5; no P1/P2 findings remain after fixing status-time
filter execution, image pull races, and recursive nested mounts.

Depends on: [API automation 2 — Shared execution core and project lock](api-automation-2.md).

## Goal

Run every model-requested command in a disposable container instead of on the
host. This replaces the runner's host-shell acknowledgement,
`ALLOW_UNSANDBOXED_SHELL=1`, with isolation for controller runs.

## Scope and boundaries

- Linux with Docker is the only supported first-release platform.
- The host makes every provider API call. The container never holds provider
  credentials.
- The standalone runner keeps its host executor; this executor is used only by
  the controller.
- Require an ordinary repository whose root contains a real `.git` directory.
  Reject linked worktrees (`.git` file), submodules, external or symlinked
  gitdirs, and a common dir outside that directory. Check the resolved Git dir
  and superproject before any model call. Also reject active custom Git clean
  or process filters; the first release does not run them on the host. Git
  status can run clean filters while comparing worktree content, so preflight
  effective attributes before status as well as diff and staging.

## Design

**Image.** The user names an image that already exists locally. The controller
resolves it to its immutable image ID before the proposal is shown and records
that ID in the receipt. A missing image stops with exit 17 and the command to
build or pull it; the controller never pulls or builds on its own. Use only a
local Docker daemon through its local Unix socket, pass `--pull=never` to each
run, and reject remote contexts and daemon overrides, including
`DOCKER_CONFIG`. Inspect bind mounts under the canonical project path and reject
nested host mounts before creating a container.

**Isolation.** Each command runs in a fresh container with:

- `--network none`;
- no host home, no provider credentials, no SSH agent, and no Docker socket;
- `--read-only` root filesystem with a private writable `/tmp`;
- `--user` set to the host user's uid and gid, so files written in the project
  keep the owner the host expects;
- `--cap-drop ALL`, `--security-opt no-new-privileges`, 4 CPUs, 8 GiB memory,
  512 processes, and a 300-second command timeout (all shown in the proposal);
- the selected project mounted writable with its in-tree `.git` directory
  separately bind-mounted read-only. Nested host mounts are checked before
  launch, and recursive mount inclusion is disabled on both binds to close the
  check-to-launch gap. The controller adds no other host bind mounts.

**Host Git boundary.** A writable `.git` lets the container plant hooks or
`core.fsmonitor` for the host to execute. The read-only nested bind blocks that
path. The host nevertheless treats the project and its Git metadata as
untrusted: every Git call goes through one wrapper with a controlled environment
and arguments. Clear inherited Git config and execution variables, isolate
system/global config, and neutralize or reject every repository setting that can
launch a command. Explicitly disable hooks, fsmonitor, external diff, textconv,
pager, signing, credential helpers, SSH commands, and proxy helpers; use
`--no-ext-diff` where applicable. Use built-in Git commands only, rejecting
options that enable external helpers. Inspect effective repository config and
attributes before every host Git call that reads or changes worktree/index
state. Reject active custom `filter.<name>.clean` or `.process`, including
those enabled by `.gitattributes` or `.git/info/attributes`; preserve built-in
text/eol normalization when staging.
Never simply disable all filters with `filter.<name>.clean=cat`, since that can
silently change repository content. [Git attributes](https://git-scm.com/docs/gitattributes/2.40.0)
can trigger a clean command on `git add`, so tampering tests cover both config
and attributes. Docker's [bind-mount rules](https://docs.docker.com/engine/storage/bind-mounts/)
also require checking mount layout before trusting this nested bind.

**Timeouts and interruption.** Each command has a timeout. On timeout, Ctrl-C, or
controller exit, the controller stops and removes the container, so no child
process keeps running against the project.

**Missing dependencies.** With no network, a command that needs an absent tool or
package fails inside the container. The controller reports it as a missing
dependency, pauses with exit 17, and names the image change needed. It never
enables networking to fetch dependencies. Images must provide `/usr/bin/env`
and `/bin/sh`, plus the tools and packages required for the approved task.

## Deliverables

- A container executor module in `harness/` used only by the controller.
- `tests/test_container_executor.py`: Docker-free unit and Git-tampering tests.
  `tests/container_acceptance/test_container_docker.py` exercises a local image
  when Docker is available. The acceptance directory is a separate suite and is
  not discovered by the default `check.py` run.
- `check.py`: syntax and payload checks for the controller modules without
  requiring Docker.
- [docs/installation.md](installation.md): Docker requirement and image guidance.

## Acceptance

- From inside the container, tests cannot reach the network, read the host home,
  find provider credentials, reach the Docker socket, or write `.git`.
- Tampering attempts on `.git/config` and `.git/hooks` fail inside the container.
  Malicious repository config that launches hooks, fsmonitor, external diff or
  text conversion, signing, credential/SSH/proxy helpers, or clean/process
  commands from Git attributes never executes on the host during any host Git
  call, including `git status` comparing changed files; built-in text
  normalization still works.
- Linked worktrees, submodules, external gitdirs, nested host mounts, and remote
  Docker daemons fail before any model call.
- A timeout or Ctrl-C leaves no running container.
- A missing image or dependency pauses with exit 17 and an actionable message.

## Verification

```bash
python3 -B -m unittest discover -s tests -p 'test_container*.py'
python3 -B -m unittest discover -s tests/container_acceptance -p 'test_container*.py'
python3 check.py
```

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| API3-T01 | `[+]` | Resolve and record the local image ID; stop with exit 17 when it is missing. | The controller never pulls or builds an image; every run uses the resolved image ID with pulls disabled. |
| API3-T02 | `[+]` | Implement the container executor with network, filesystem, capability, and resource isolation. | Escape tests for network, host home, credentials, and the Docker socket fail inside the container. |
| API3-T03 | `[+]` | Validate repository topology, mount `.git` read-only, and harden every host Git call. | Config, hook, fsmonitor, external diff, signing, and clean/process attributes cannot execute on the host; built-in text normalization remains intact. |
| API3-T04 | `[+]` | Enforce command timeouts and container cleanup on interruption. | Timeout and Ctrl-C stop and remove the container; the host Docker client process is reaped. |
| API3-T05 | `[+]` | Report missing dependencies as a pause with exit 17. | Missing image and command cases pause before unsafe continuation; networking is never enabled to fetch a dependency. |
| API3-T06 | `[+]` | Keep Docker acceptance tests out of the default `check.py` run. | `check.py` passes on a machine without Docker and still checks controller modules. |

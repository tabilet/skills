"""Local Docker executor for controller model commands (never the standalone runner)."""
from __future__ import annotations

import os
import pathlib
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import uuid


CPU_LIMIT = "4"
MEMORY_LIMIT = "8g"
PROCESS_LIMIT = "512"
COMMAND_LIMIT = 300
CONTAINER_ROOT = "/workspace"
CONTAINER_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


class SandboxUnavailable(RuntimeError):
    """The controller cannot safely prepare or run its local sandbox."""


def _decode_mount_field(value: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)


def nested_mounts(repo: pathlib.Path, mountinfo: pathlib.Path = pathlib.Path("/proc/self/mountinfo")) -> list[pathlib.Path]:
    """Return mountpoints below the project root using Linux mountinfo."""

    root = repo.resolve(strict=True)
    try:
        lines = mountinfo.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SandboxUnavailable(f"cannot inspect Linux mount table {mountinfo}: {exc}") from exc
    found = set()
    for line in lines:
        fields = line.split()
        if len(fields) < 6:
            continue
        mountpoint = pathlib.Path(_decode_mount_field(fields[4]))
        try:
            resolved = mountpoint.resolve(strict=False)
            relative = resolved.relative_to(root)
        except (OSError, ValueError):
            continue
        if relative.parts:
            found.add(resolved)
    return sorted(found, key=str)


def _docker_environment(include_home: bool = False) -> dict[str, str]:
    env = {"PATH": os.environ.get("PATH", os.defpath)}
    if include_home:
        env["HOME"] = str(pathlib.Path.home())
    else:
        env["HOME"] = "/nonexistent"
        env["DOCKER_CONFIG"] = "/nonexistent/.docker"
    env["LANG"] = "C"
    return env


def _run_docker(command: list[str], *, include_home: bool = False, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=_docker_environment(include_home),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SandboxUnavailable(f"Docker command failed: {exc}") from exc


def local_docker_endpoint() -> tuple[str, str]:
    """Resolve the active Docker context and require a local Unix socket."""

    overrides = ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH", "DOCKER_CONFIG")
    present = [name for name in overrides if os.environ.get(name)]
    if present:
        raise SandboxUnavailable("Docker daemon overrides are unsupported: " + ", ".join(present))
    docker = shutil.which("docker")
    if not docker:
        raise SandboxUnavailable("Docker is unavailable. Install Docker and start its local daemon.")
    context = _run_docker([docker, "context", "show"], include_home=True)
    if context.returncode:
        raise SandboxUnavailable(context.stderr.strip() or "unable to read the active Docker context")
    name = context.stdout.strip()
    if not name or name.startswith("-"):
        raise SandboxUnavailable("Docker returned an invalid active context name")
    endpoint_result = _run_docker(
        [docker, "context", "inspect", name, "--format", '{{(index .Endpoints "docker").Host}}'],
        include_home=True,
    )
    if endpoint_result.returncode:
        raise SandboxUnavailable(endpoint_result.stderr.strip() or "unable to inspect the active Docker context")
    endpoint = endpoint_result.stdout.strip()
    if not endpoint.startswith("unix://"):
        raise SandboxUnavailable(f"Docker context {name!r} is not a local Unix-socket daemon")
    socket_path = pathlib.Path(endpoint.removeprefix("unix://"))
    try:
        if not stat.S_ISSOCK(socket_path.stat().st_mode):
            raise SandboxUnavailable(f"Docker endpoint is not a Unix socket: {socket_path}")
    except OSError as exc:
        raise SandboxUnavailable(f"Docker Unix socket is unavailable at {socket_path}: {exc}") from exc
    return docker, endpoint


def _git(core, repo: pathlib.Path, *args: str) -> str:
    try:
        proc = core.git_local(list(args), repo, timeout=15)
    except (OSError, subprocess.TimeoutExpired, core.UnsafeGitConfiguration) as exc:
        raise SandboxUnavailable(f"safe Git inspection failed: {exc}") from exc
    if proc.returncode:
        raise SandboxUnavailable(proc.stderr.strip() or f"Git inspection failed: {' '.join(args)}")
    return proc.stdout.strip()


def validate_repository(core, project: pathlib.Path, mountinfo: pathlib.Path = pathlib.Path("/proc/self/mountinfo")) -> pathlib.Path:
    """Require a plain in-tree Git repository with no nested repositories or mounts."""

    try:
        repo = project.expanduser().resolve(strict=True)
    except OSError as exc:
        raise SandboxUnavailable(f"project path is unavailable: {exc}") from exc
    if not repo.is_dir():
        raise SandboxUnavailable("project path must be a directory")
    git_dir = repo / ".git"
    try:
        info = git_dir.lstat()
    except OSError as exc:
        raise SandboxUnavailable("controller requires a real in-tree .git directory") from exc
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise SandboxUnavailable("controller rejects linked worktrees and symlinked .git directories")
    if _git(core, repo, "rev-parse", "--show-toplevel") != str(repo):
        raise SandboxUnavailable("project path must be the repository worktree root")

    actual_git = pathlib.Path(_git(core, repo, "rev-parse", "--absolute-git-dir")).resolve()
    common_raw = pathlib.Path(_git(core, repo, "rev-parse", "--git-common-dir"))
    common_git = (common_raw if common_raw.is_absolute() else repo / common_raw).resolve()
    if actual_git != git_dir.resolve() or common_git != git_dir.resolve():
        raise SandboxUnavailable("controller rejects external Git directories and linked worktrees")
    if _git(core, repo, "rev-parse", "--show-superproject-working-tree"):
        raise SandboxUnavailable("controller rejects Git submodules")
    index = _git(core, repo, "ls-files", "--stage", "-z")
    if any(record.startswith("160000 ") for record in index.split("\0") if record):
        raise SandboxUnavailable("controller rejects repositories containing Git submodules")

    for parent, directories, files in os.walk(repo, topdown=True, followlinks=False):
        parent_path = pathlib.Path(parent)
        if parent_path == repo:
            directories[:] = [name for name in directories if name != ".git"]
        if ".git" in directories or ".git" in files:
            raise SandboxUnavailable(f"controller rejects nested Git repositories below {repo}")
    mounts = nested_mounts(repo, mountinfo)
    if mounts:
        raise SandboxUnavailable("nested host mounts are unsupported: " + ", ".join(map(str, mounts)))

    candidates = core._git_index_paths(repo)
    active = core._active_custom_filters(repo, candidates)
    if active:
        raise SandboxUnavailable(
            "active custom Git clean/process filters are unsupported: " + ", ".join(active)
        )
    return repo


class DockerExecutor:
    """Fresh, networkless Docker container per command, with only the project mounted."""

    def __init__(self, core, project: pathlib.Path, image: str, mountinfo: pathlib.Path = pathlib.Path("/proc/self/mountinfo")):
        self.sandbox_unavailable = SandboxUnavailable
        if not sys.platform.startswith("linux"):
            raise SandboxUnavailable("the Docker controller sandbox currently supports Linux only")
        if not image or image.startswith("-") or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@-]*", image):
            raise SandboxUnavailable("select a valid image that already exists in the local Docker daemon")
        self.core = core
        self.repo = validate_repository(core, project, mountinfo)
        if "," in str(self.repo):
            raise SandboxUnavailable("Docker bind mounts cannot safely represent a project path containing a comma")
        self.docker, self.endpoint = local_docker_endpoint()
        command = [self.docker, "--host", self.endpoint, "image", "inspect", "--format={{.Id}}", image]
        result = _run_docker(command)
        image_id = result.stdout.strip()
        if result.returncode:
            detail = result.stderr.strip()
            if "no such image" not in detail.casefold() and "not found" not in detail.casefold():
                raise SandboxUnavailable(
                    "cannot inspect the image through the local Docker daemon: "
                    + (detail or "Docker image inspection failed")
                )
            pull_command = shlex.join([self.docker, "--host", self.endpoint, "pull", image])
            raise SandboxUnavailable(
                f"Docker image {image!r} is not available locally. If it is published, run `{pull_command}` "
                "manually; otherwise build it locally. The controller will not pull or build images."
            )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
            raise SandboxUnavailable("Docker returned no valid immutable ID for the selected local image")
        self.image = image_id

    def _cleanup(self, name: str) -> None:
        try:
            _run_docker([self.docker, "--host", self.endpoint, "rm", "-f", name], timeout=8)
        except SandboxUnavailable:
            pass

    @staticmethod
    def _stop_client(process: subprocess.Popen) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    def __call__(self, repo, cmd, timeout, max_output, allow_dangerous, env=None) -> dict:
        if not allow_dangerous and self.core.DANGEROUS_RE.search(cmd):
            return {
                "exit_code": 126,
                "stdout": "",
                "stderr": "Command rejected by harness guardrail. Set ALLOW_DANGEROUS_COMMANDS=1 to override.",
                "truncated": False,
            }
        if pathlib.Path(repo).resolve() != self.repo:
            raise SandboxUnavailable("Docker executor cannot be used for a different project")
        name = "tabilet-" + uuid.uuid4().hex
        project_mount = (
            f"type=bind,source={self.repo},target={CONTAINER_ROOT},"
            "bind-propagation=rprivate,bind-recursive=disabled"
        )
        git_mount = (
            f"type=bind,source={self.repo / '.git'},target={CONTAINER_ROOT}/.git,"
            "readonly,bind-propagation=rprivate,bind-recursive=disabled"
        )
        command = [
            self.docker, "--host", self.endpoint, "run", "--pull=never", "--rm", "--name", name,
            "--network", "none", "--read-only",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=1g",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
            "--cpus", CPU_LIMIT, "--memory", MEMORY_LIMIT, "--pids-limit", PROCESS_LIMIT,
            "--mount", project_mount, "--mount", git_mount,
            "--workdir", CONTAINER_ROOT,
            "--entrypoint", "/usr/bin/env", self.image,
            "-i", "HOME=/tmp", "TMPDIR=/tmp", f"PATH={CONTAINER_PATH}", "LANG=C",
            "/bin/sh", "-c", cmd,
        ]
        command_timeout = min(max(1, int(timeout)), COMMAND_LIMIT)
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=_docker_environment(),
                start_new_session=True,
            )
        except OSError as exc:
            self._cleanup(name)
            raise SandboxUnavailable(f"unable to start Docker: {exc}") from exc
        try:
            try:
                stdout, stderr = process.communicate(timeout=command_timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                self._cleanup(name)
                self._stop_client(process)
                stdout, stderr = process.communicate()
                exit_code = 124
                stderr += f"\nCommand timed out after {command_timeout}s; container was stopped and removed."
            if exit_code == 125:
                raise SandboxUnavailable(
                    "Docker could not start the sandbox. Check the local daemon, image, and mount permissions: "
                    + stderr.strip()
                )
            stdout, stderr, truncated = self.core.bounded_output(stdout, stderr, max_output)
            return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr, "truncated": truncated}
        except KeyboardInterrupt:
            self._cleanup(name)
            self._stop_client(process)
            raise
        finally:
            self._cleanup(name)


def prepare_executor(core, project: pathlib.Path, image: str, mountinfo: pathlib.Path = pathlib.Path("/proc/self/mountinfo")) -> DockerExecutor:
    """Construct the executor before any provider call so setup failures fail closed."""

    return DockerExecutor(core, project, image, mountinfo)

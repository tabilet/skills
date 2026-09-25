"""Exact proposal approval, private receipts, planning commits, and recovery."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import tempfile
import time
import uuid


RECEIPT_SCHEMA = "tabilet.api.receipt/v1"
DEFAULT_LIMITS = {
    "max_rows": 5,
    "max_provider_attempts": 100,
    "max_turns_per_row": 40,
    "max_commits": 15,
    "max_runtime_seconds": 7200,
}
DOCKER_LIMITS = {
    "cpus": 4,
    "memory_mib": 8192,
    "processes": 512,
    "command_timeout_seconds": 300,
}
MAX_PROPOSAL_BYTES = 256 * 1024
MAX_SNAPSHOT_FILE_BYTES = 8 * 1024 * 1024
MAX_SNAPSHOT_TOTAL_BYTES = 64 * 1024 * 1024
MAX_SNAPSHOT_FILES = 5000
MAX_FILE_ACTIONS = 500
_PERMANENT_ID = re.compile(rb"\b([A-Z][0-9]{2})\b")
_STATUS_FILE = re.compile(r"(?:^|/)status-([A-Z][0-9]{2})\.md$")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
RECEIPT_STATES = {"approved", "running", "paused", "needs_review", "completed"}


class ProposalError(ValueError):
    """A proposal or receipt cannot be handled safely."""


class ApprovalStale(ProposalError):
    """The shown proposal no longer matches the project state."""


class RecoveryNeedsReview(ProposalError):
    """A partial or uncertain planning operation must be reviewed manually."""


def _canonical_json(value) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ProposalError(f"value is not representable as standard UTF-8 JSON: {exc}") from exc


def _pretty_json(value) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ProposalError(f"proposal contains a non-JSON value: {exc}") from exc


def _required_text(value, label: str, maximum: int = 20000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ProposalError(f"{label} must contain 1 to {maximum} characters")
    return value


def _project_path(raw: str) -> str:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise ProposalError("file-action paths must be POSIX relative paths")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ProposalError("absolute file-action paths are not allowed")
    parts = raw.split("/")
    if any(part in {"", ".", "..", ".git"} for part in parts):
        raise ProposalError("file-action paths cannot contain empty, dot, parent, or .git components")
    if any(any(ord(char) < 32 or ord(char) == 127 for char in part) for part in parts):
        raise ProposalError("control characters are not allowed in file-action paths")
    try:
        encoded_length = len(raw.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise ProposalError("file-action paths must be valid UTF-8") from exc
    if encoded_length > 1024:
        raise ProposalError("file-action path exceeds 1024 UTF-8 bytes")
    return raw


def _validate_horizon(value, limits: dict) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ProposalError("horizon must contain at least one milestone")
    if len(value) > 99:
        raise ProposalError("horizon may contain at most 99 milestones")
    ids = set()
    task_ids = set()
    total_rows = 0
    validated = []
    for milestone in value:
        if not isinstance(milestone, dict):
            raise ProposalError("each horizon milestone must be an object")
        identifier = milestone.get("id")
        title = milestone.get("title")
        dependencies = milestone.get("dependencies")
        acceptance = milestone.get("acceptance")
        tasks = milestone.get("tasks")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Z][A-Z0-9-]{0,15}", identifier):
            raise ProposalError("each horizon milestone needs a stable short ID")
        if identifier in ids:
            raise ProposalError(f"duplicate milestone ID in horizon: {identifier}")
        ids.add(identifier)
        _required_text(title, f"title for {identifier}", 1000)
        if isinstance(acceptance, str):
            _required_text(acceptance, f"acceptance for {identifier}", 8000)
        elif isinstance(acceptance, list) and acceptance and all(
            isinstance(item, str) and item.strip() and len(item) <= 8000 for item in acceptance
        ):
            pass
        else:
            raise ProposalError(f"{identifier} needs explicit milestone acceptance criteria")
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) or not dep for dep in dependencies):
            raise ProposalError(f"dependencies for {identifier} must be an array of IDs")
        if len(set(dependencies)) != len(dependencies) or identifier in dependencies:
            raise ProposalError(f"dependencies for {identifier} must be unique and cannot include itself")
        if not isinstance(tasks, list) or not tasks:
            raise ProposalError(f"{identifier} must contain at least one task row")
        closure_paths = milestone.get("closure_paths")
        if not isinstance(closure_paths, list) or not closure_paths:
            raise ProposalError(f"{identifier} needs explicit closure_paths")
        closure_paths = [_project_path(path) for path in closure_paths]
        if len(closure_paths) != len(set(closure_paths)):
            raise ProposalError(f"closure_paths for {identifier} must be unique")
        if f"tabilet/memory-bank/status-{identifier}.md" not in closure_paths:
            raise ProposalError(f"closure_paths for {identifier} must include its active status file")
        milestone["closure_paths"] = closure_paths
        total_rows += len(tasks)
        for task in tasks:
            if not isinstance(task, dict):
                raise ProposalError(f"tasks in {identifier} must be objects")
            for name in ("id", "owner", "description"):
                _required_text(task.get(name), f"task {name}", 1000)
            if task["id"] in task_ids:
                raise ProposalError(f"duplicate task row ID in horizon: {task['id']}")
            task_ids.add(task["id"])
            acceptance = task.get("acceptance")
            if isinstance(acceptance, str):
                _required_text(acceptance, "task acceptance", 8000)
            elif isinstance(acceptance, list) and acceptance and all(isinstance(item, str) and item.strip() for item in acceptance):
                if any(len(item) > 8000 for item in acceptance):
                    raise ProposalError("task acceptance text is too long")
            else:
                raise ProposalError("every task needs acceptance criteria")
            verification = task.get("verification")
            if not isinstance(verification, list) or not verification or any(
                not isinstance(command, str) or not command.strip() or len(command) > 2000
                for command in verification
            ):
                raise ProposalError("every task needs at least one verification command")
            approved_paths = task.get("approved_paths")
            if not isinstance(approved_paths, list) or not approved_paths:
                raise ProposalError(f"every task in {identifier} needs explicit approved_paths")
            task_paths = [_project_path(path) for path in approved_paths]
            if len(task_paths) != len(set(task_paths)):
                raise ProposalError(f"approved_paths for task {task['id']} must be unique")
            if f"tabilet/memory-bank/status-{identifier}.md" not in task_paths:
                raise ProposalError(
                    f"approved_paths for task {task['id']} must include its status file"
                )
            task["approved_paths"] = task_paths
        milestone.setdefault("manual_evidence", [])
        if not isinstance(milestone["manual_evidence"], list) or any(
            not isinstance(item, str) or not item.strip() or len(item) > 8000
            for item in milestone["manual_evidence"]
        ):
            raise ProposalError(f"manual_evidence for {identifier} must be an array of descriptions")
        retirement_adopted = milestone.setdefault("retirement_adopted", False)
        if not isinstance(retirement_adopted, bool):
            raise ProposalError(f"retirement_adopted for {identifier} must be a boolean")
        validated.append(milestone)
    if total_rows > limits["max_rows"]:
        raise ProposalError(
            f"horizon has {total_rows} task rows, above max_rows={limits['max_rows']}"
        )
    return validated


def validate_proposal(proposal: dict) -> dict:
    """Validate the complete proposal object and fill the published cap defaults."""

    required = {
        "title", "delivery_boundary", "horizon", "candidate_directions", "file_actions",
        "diff", "image_id", "limits", "planned_commits", "external_actions",
    }
    if not isinstance(proposal, dict) or set(proposal) != required:
        missing = sorted(required - set(proposal)) if isinstance(proposal, dict) else sorted(required)
        extra = sorted(set(proposal) - required) if isinstance(proposal, dict) else []
        raise ProposalError(f"proposal fields differ (missing={missing}, extra={extra})")
    result = dict(proposal)
    _required_text(result["title"], "proposal title", 1000)
    if "\n" in result["title"] or "\r" in result["title"] or any(
        ord(char) < 32 or ord(char) == 127 for char in result["title"]
    ):
        raise ProposalError("proposal title must be a single terminal-safe line")
    _required_text(result["delivery_boundary"], "delivery boundary", 8000)
    if not isinstance(result["limits"], dict):
        raise ProposalError("limits must be an object of positive integers")
    if set(result["limits"]) - set(DEFAULT_LIMITS):
        raise ProposalError("proposal includes an unknown numeric limit")
    limits = dict(DEFAULT_LIMITS)
    for name, value in result["limits"].items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ProposalError(f"{name} must be a positive integer")
        limits[name] = value
    result["limits"] = limits
    result["horizon"] = _validate_horizon(result["horizon"], limits)
    for key in ("candidate_directions", "external_actions"):
        if not isinstance(result[key], list):
            raise ProposalError(f"{key} must be an array")
    if not isinstance(result["file_actions"], list) or not 1 <= len(result["file_actions"]) <= MAX_FILE_ACTIONS:
        raise ProposalError(f"file_actions must contain 1 to {MAX_FILE_ACTIONS} actions")
    seen_paths = set()
    actions = []
    for item in result["file_actions"]:
        if not isinstance(item, dict) or set(item) != {"path", "action"}:
            raise ProposalError("each file action must contain exactly path and action")
        path = _project_path(item["path"])
        action = item["action"]
        if not isinstance(action, str) or action not in {"create", "replace", "delete"}:
            raise ProposalError(f"unsupported file action for {path}: {action!r}")
        if path in seen_paths:
            raise ProposalError(f"duplicate file action path: {path}")
        seen_paths.add(path)
        actions.append({"path": path, "action": action})
    result["file_actions"] = actions
    diff = result["diff"]
    if not isinstance(diff, str) or not diff.startswith("diff --git ") or not diff.endswith("\n"):
        raise ProposalError("diff must be a complete Git patch ending in a newline")
    if any((ord(char) < 32 and char not in {"\n", "\t"}) or ord(char) == 127 for char in diff):
        raise ProposalError("planning diff contains terminal control characters")
    try:
        diff_size = len(diff.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise ProposalError("planning diff must be valid UTF-8 text") from exc
    if diff_size > MAX_PROPOSAL_BYTES:
        raise ProposalError(f"diff exceeds the {MAX_PROPOSAL_BYTES}-byte proposal limit")
    image_id = result["image_id"]
    if not isinstance(image_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise ProposalError("image_id must be an immutable sha256 Docker image ID")
    commits = result["planned_commits"]
    if isinstance(commits, bool) or not isinstance(commits, int) or commits < 1:
        raise ProposalError("planned_commits must be a positive integer")
    minimum_commits = 1 + sum(len(milestone["tasks"]) for milestone in result["horizon"])
    if commits < minimum_commits:
        raise ProposalError(
            "planned_commits must include one planning commit and one commit per task row "
            f"(minimum {minimum_commits})"
        )
    if commits > limits["max_commits"]:
        raise ProposalError("planned commits exceed the confirmed max_commits limit")
    _canonical_json(result)
    return result


def _git(core, repo: pathlib.Path, args: list[str], *, input_text=None, timeout=30, check=True):
    try:
        proc = core.git_local(args, repo, timeout=timeout, input_text=input_text)
    except (OSError, subprocess.TimeoutExpired, core.UnsafeGitConfiguration) as exc:
        raise ProposalError(f"hardened host Git call failed ({args[0]}): {exc}") from exc
    if check and proc.returncode:
        detail = proc.stderr.strip() or f"Git {args[0]} exited {proc.returncode}"
        raise ProposalError(detail)
    return proc


def _decode_paths(raw: str, label: str) -> list[str]:
    if not raw:
        return []
    if not raw.endswith("\x00"):
        raise ProposalError(f"Git returned an incomplete {label} path list")
    values = raw[:-1].split("\x00")
    if any(not value or any(0xD800 <= ord(char) <= 0xDFFF for char in value) for value in values):
        raise ProposalError(f"Git returned an unsupported filename in {label}")
    return values


def _patch_paths(core, repo: pathlib.Path, patch: str) -> list[str]:
    proc = _git(core, repo, ["apply", "--numstat", "-z", "-"], input_text=patch)
    chunks = proc.stdout.split("\x00")
    if chunks[-1] != "":
        raise ProposalError("Git returned malformed patch path information")
    chunks.pop()
    paths = []
    while chunks:
        record = chunks.pop(0)
        fields = record.split("\t", 2)
        if len(fields) != 3 or not fields[0].isdigit() and fields[0] != "-" or not fields[1].isdigit() and fields[1] != "-":
            raise ProposalError("patch contains an unsupported rename, copy, or malformed file record")
        path = fields[2]
        if not path:
            raise ProposalError("patch contains an unsupported rename or copy record")
        paths.append(_project_path(path))
    if not paths or len(paths) != len(set(paths)):
        raise ProposalError("patch must change one or more unique project files")
    if "GIT binary patch" in patch or "\nBinary files " in patch:
        raise ProposalError("planning proposals are limited to reviewable text patches")
    if re.search(r"(?m)^(?:new file mode|deleted file mode|old mode|new mode) 120000$", patch):
        raise ProposalError("symbolic-link file actions are not allowed")
    if re.search(r"(?m)^(?:new file mode|deleted file mode|old mode|new mode) 160000$", patch):
        raise ProposalError("submodule file actions are not allowed")
    return sorted(paths)


def _patch_action_kinds(core, repo: pathlib.Path, patch: str) -> dict[str, str]:
    summary = _git(core, repo, ["apply", "--summary", "-"], input_text=patch)
    kinds = {}
    for line in summary.stdout.splitlines():
        if line.startswith(" create mode "):
            remainder = line[len(" create mode "):]
            mode, separator, target = remainder.partition(" ")
            if not separator or mode not in {"100644", "100755"}:
                raise ProposalError("patch contains an unsupported created-file mode")
            kind = "create"
        elif line.startswith(" delete mode "):
            remainder = line[len(" delete mode "):]
            mode, separator, target = remainder.partition(" ")
            if not separator or mode not in {"100644", "100755"}:
                raise ProposalError("patch contains an unsupported deleted-file mode")
            kind = "delete"
        elif line.startswith(" mode change "):
            # Replacing a regular file may also change its executable bit.
            continue
        elif line.strip():
            raise ProposalError("patch contains an unsupported rename, copy, or mode operation")
        else:
            continue
        target = _project_path(target)
        if target in kinds:
            raise ProposalError(f"patch repeats a file action: {target}")
        kinds[target] = kind
    return kinds


def _signature(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _regular_bytes(path: pathlib.Path, maximum: int) -> bytes:
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise ProposalError(f"file is missing: {path}")
    except OSError as exc:
        raise ProposalError(f"cannot inspect file-action target {path}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ProposalError(f"file-action target is not a regular file: {path}")
    if info.st_size > maximum:
        raise ProposalError(f"file exceeds the {maximum}-byte limit: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as source:
            opened = os.fstat(source.fileno())
            if not stat.S_ISREG(opened.st_mode) or _signature(opened) != _signature(info):
                raise ProposalError(f"file changed before it could be read: {path}")
            data = source.read(maximum + 1)
        if len(data) > maximum or _signature(info) != _signature(path.lstat()):
            raise ProposalError(f"file changed or exceeded its size limit: {path}")
    except OSError as exc:
        raise ProposalError(f"cannot read file-action target {path}: {exc}") from exc
    return data


def _file_digest(path: pathlib.Path) -> str | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ProposalError(f"cannot inspect file-action target {path}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ProposalError(f"file-action target is not a regular file: {path}")
    if info.st_size > MAX_SNAPSHOT_FILE_BYTES:
        raise ProposalError(f"file-action target exceeds the {MAX_SNAPSHOT_FILE_BYTES}-byte limit: {path}")
    data = _regular_bytes(path, MAX_SNAPSHOT_FILE_BYTES)
    return hashlib.sha256(data).hexdigest()


def _safe_action_digest(repo: pathlib.Path, relative: str) -> str | None:
    current = repo
    for index, component in enumerate(relative.split("/")):
        current = current / component
        try:
            info = current.lstat()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise ProposalError(f"cannot inspect file-action path {relative}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ProposalError(f"symbolic-link file-action path is not allowed: {relative}")
        if index < len(relative.split("/")) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ProposalError(f"file-action parent is not a directory: {relative}")
        if index == len(relative.split("/")) - 1:
            return _file_digest(current)
    return None


def _project_root(core, repo: pathlib.Path) -> pathlib.Path:
    try:
        root = pathlib.Path(repo).expanduser().resolve(strict=True)
    except OSError as exc:
        raise ProposalError(f"project path is unavailable: {exc}") from exc
    if not root.is_dir():
        raise ProposalError("project path must be a directory")
    dot_git = root / ".git"
    if dot_git.is_symlink() or not dot_git.is_dir():
        raise ProposalError("planning approval requires an in-tree .git directory")
    toplevel = pathlib.Path(_git(core, root, ["rev-parse", "--show-toplevel"]).stdout.strip()).resolve()
    gitdir_text = _git(core, root, ["rev-parse", "--git-dir"]).stdout.strip()
    gitdir = pathlib.Path(gitdir_text)
    if not gitdir.is_absolute():
        gitdir = (root / gitdir).resolve()
    else:
        gitdir = gitdir.resolve()
    common_text = _git(core, root, ["rev-parse", "--git-common-dir"]).stdout.strip()
    commondir = pathlib.Path(common_text)
    if not commondir.is_absolute():
        commondir = (root / commondir).resolve()
    else:
        commondir = commondir.resolve()
    if toplevel != root or gitdir != dot_git.resolve() or commondir != dot_git.resolve():
        raise ProposalError("planning approval supports only a standard repository with an in-tree .git directory")
    return root


def _workflow_snapshot(core, repo: pathlib.Path) -> tuple[dict, list[str]]:
    paths = []
    for relative_root in ("tabilet/memory-bank", "tabilet/docs/history"):
        root = repo / relative_root
        try:
            root_info = root.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ProposalError(f"cannot inspect workflow directory {relative_root}: {exc}") from exc
        if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
            raise ProposalError(f"workflow path is not a real directory: {relative_root}")
        for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
            base = pathlib.Path(directory)
            if ".git" in dirnames:
                dirnames.remove(".git")
            for dirname in dirnames:
                if (base / dirname).is_symlink():
                    raise ProposalError(f"symbolic-link workflow directory is not allowed: {base / dirname}")
            for filename in filenames:
                path = base / filename
                if path.is_symlink():
                    raise ProposalError(f"symbolic-link workflow file is not allowed: {path}")
                if filename.endswith(".md"):
                    paths.append(path.relative_to(repo).as_posix())
                    if len(paths) > MAX_SNAPSHOT_FILES:
                        raise ProposalError("workflow snapshot contains too many Markdown files")
    paths.sort()
    hashes = {}
    permanent_ids = set()
    total = 0
    for relative in paths:
        if not relative.startswith(("tabilet/memory-bank/", "tabilet/docs/history/")):
            continue
        path = repo / relative
        try:
            info = path.lstat()
        except OSError as exc:
            raise ProposalError(f"cannot inspect workflow source {relative}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise ProposalError(f"workflow source is not a regular file: {relative}")
        if info.st_size > MAX_SNAPSHOT_FILE_BYTES:
            raise ProposalError(f"workflow source exceeds its size limit: {relative}")
        total += info.st_size
        if total > MAX_SNAPSHOT_TOTAL_BYTES:
            raise ProposalError("workflow source snapshot exceeds its total size limit")
        data = _regular_bytes(path, MAX_SNAPSHOT_FILE_BYTES)
        hashes[relative] = hashlib.sha256(data).hexdigest()
        match = _STATUS_FILE.search(relative)
        if match:
            permanent_ids.add(match.group(1))
        permanent_ids.update(match.group(1).decode("ascii") for match in _PERMANENT_ID.finditer(data))
    return dict(sorted(hashes.items())), sorted(permanent_ids)


def capture_project_snapshot(core, repo: pathlib.Path, file_actions: list[dict], *, allow_dirty=False) -> dict:
    """Capture branch, clean state, permanent IDs, and affected source hashes."""

    root = _project_root(core, repo)
    status = _git(core, root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    clean = status.stdout == ""
    if not clean and not allow_dirty:
        raise ProposalError("project must have a clean committed baseline before proposal approval")
    head_proc = _git(core, root, ["rev-parse", "--verify", "--quiet", "HEAD"], check=False)
    if head_proc.returncode not in {0, 1}:
        raise ProposalError(head_proc.stderr.strip() or "Git cannot determine the project baseline")
    head = head_proc.stdout.strip() if head_proc.returncode == 0 else None
    if head is not None and not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", head):
        raise ProposalError("Git returned an invalid baseline commit ID")
    branch_proc = _git(core, root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    if branch_proc.returncode not in {0, 1}:
        raise ProposalError(branch_proc.stderr.strip() or "Git cannot determine the current branch")
    branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else None
    workflow_hashes, permanent_ids = _workflow_snapshot(core, root)
    action_hashes = {}
    for item in file_actions:
        relative = _project_path(item["path"])
        action_hashes[relative] = _safe_action_digest(root, relative)
    return {
        "project_path": str(root),
        "branch": branch,
        "baseline_commit": head,
        "clean": clean,
        "workflow_hashes": workflow_hashes,
        "permanent_ids": permanent_ids,
        "action_hashes": dict(sorted(action_hashes.items())),
    }


def _snapshot_drift(before: dict, now: dict) -> list[str]:
    reasons = []
    if before["branch"] != now["branch"]:
        reasons.append("branch changed")
    if before["baseline_commit"] != now["baseline_commit"]:
        reasons.append("baseline commit changed")
    if not now["clean"]:
        reasons.append("worktree or index is dirty")
    if before["workflow_hashes"] != now["workflow_hashes"]:
        reasons.append("active or retired workflow files changed")
    if before["permanent_ids"] != now["permanent_ids"]:
        reasons.append("permanent status IDs changed")
    if before["action_hashes"] != now["action_hashes"]:
        reasons.append("file-action targets changed")
    return reasons


def _workflow_state_digest(snapshot: dict) -> str:
    return hashlib.sha256(_canonical_json({
        "workflow_hashes": snapshot["workflow_hashes"],
        "permanent_ids": snapshot["permanent_ids"],
    })).hexdigest()


def _action_preconditions(proposal: dict, snapshot: dict) -> list[dict]:
    output = []
    by_path = snapshot["action_hashes"]
    for item in proposal["file_actions"]:
        digest = by_path[item["path"]]
        action = item["action"]
        if action == "create" and digest is not None:
            raise ProposalError(f"create action target already exists: {item['path']}")
        if action in {"replace", "delete"} and digest is None:
            raise ProposalError(f"{action} action target does not exist: {item['path']}")
        output.append({"path": item["path"], "action": action, "source_sha256": digest})
    return output


def _validate_patch(core, repo: pathlib.Path, proposal: dict, snapshot: dict) -> list[str]:
    paths = _patch_paths(core, repo, proposal["diff"])
    actions = sorted(item["path"] for item in proposal["file_actions"])
    if paths != actions:
        raise ProposalError(
            f"diff paths differ from the explicit file actions (diff={paths}, actions={actions})"
        )
    patch_kinds = _patch_action_kinds(core, repo, proposal["diff"])
    declared_kinds = {
        item["path"]: item["action"]
        for item in proposal["file_actions"]
        if item["action"] in {"create", "delete"}
    }
    if patch_kinds != declared_kinds:
        raise ProposalError("diff create/delete operations differ from the explicit file actions")
    for item in proposal["file_actions"]:
        digest = snapshot["action_hashes"][item["path"]]
        if item["action"] == "create" and digest is not None:
            raise ProposalError(f"create action target already exists: {item['path']}")
        if item["action"] in {"replace", "delete"} and digest is None:
            raise ProposalError(f"{item['action']} action target does not exist: {item['path']}")
    check = _git(core, repo, ["apply", "--check", "--whitespace=nowarn", "-"], input_text=proposal["diff"], check=False)
    if check.returncode:
        raise ProposalError("approved planning diff does not apply cleanly: " + (check.stderr.strip() or "Git apply check failed"))
    return paths


def _render(proposal: dict, snapshot: dict, file_actions: list[dict]) -> str:
    task_row_count = sum(len(milestone["tasks"]) for milestone in proposal["horizon"])
    visible = {
        "title": proposal["title"],
        "delivery_boundary": proposal["delivery_boundary"],
        "horizon": proposal["horizon"],
        "candidate_directions": proposal["candidate_directions"],
        "file_actions": file_actions,
        "image_id": proposal["image_id"],
        "limits": proposal["limits"],
        "docker_limits": DOCKER_LIMITS,
        "planned_commits": proposal["planned_commits"],
        "planned_commit_breakdown": {
            "planning": 1,
            "task_rows": task_row_count,
            "review_and_closure_reserve": proposal["planned_commits"] - 1 - task_row_count,
            "total": proposal["planned_commits"],
        },
        "external_actions": proposal["external_actions"],
    }
    snapshot_digest = hashlib.sha256(_canonical_json({
        "branch": snapshot["branch"],
        "baseline_commit": snapshot["baseline_commit"],
        "planning_state_sha256": _workflow_state_digest(snapshot),
        "result_state_sha256": None,
        "workflow_hashes": snapshot["workflow_hashes"],
        "permanent_ids": snapshot["permanent_ids"],
        "action_hashes": snapshot["action_hashes"],
    })).hexdigest()
    runs = [len(match.group(0)) for match in re.finditer(r"`+", proposal["diff"])]
    fence = "`" * max(3, max(runs, default=2) + 1)
    branch = snapshot["branch"] or "(detached HEAD)"
    baseline = snapshot["baseline_commit"] or "(unborn HEAD)"
    patch = proposal["diff"]
    return (
        f"# Tabilet proposal: {proposal['title']}\n\n"
        "Operational limits, not a promised dollar amount. The `confirm` command\n"
        "approves this exact planning diff and the displayed bounded local horizon.\n\n"
        f"Project branch: `{branch}`\n\nProject baseline: `{baseline}`\n\n"
        f"Project snapshot SHA-256: `{snapshot_digest}`\n\n"
        "Proposal details (all milestones, task owners, dependencies, acceptance,\n"
        "verification commands, file actions, caps, and external actions):\n\n"
        f"```json\n{_pretty_json(visible)}\n```\n\n"
        "## Exact planning diff\n\n"
        f"{fence}diff\n{patch}{fence}\n\n"
        "Task, review, and closure commits stay within `max_commits`. This confirmation\n"
        "does not authorize push, merge, deploy, publication, or any other external\n"
        "action; those are reported for separate handling.\n"
    )


def render_proposal(proposal: dict, snapshot: dict) -> tuple[str, str]:
    """Return deterministic visible text and its SHA-256 digest."""

    normalized = validate_proposal(proposal)
    actions = _action_preconditions(normalized, snapshot)
    text = _render(normalized, snapshot, actions)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, digest


def default_receipts_directory() -> pathlib.Path:
    raw = pathlib.Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
    if not raw.is_absolute():
        raise ProposalError("XDG_STATE_HOME must be an absolute path")
    return raw / "tabilet" / "receipts"


class ReceiptStore:
    """Private, durable JSON receipts stored outside project repositories."""

    def __init__(self, directory: pathlib.Path | None = None):
        self.directory = pathlib.Path(directory or default_receipts_directory()).expanduser()

    def _prepare(self, project: pathlib.Path) -> pathlib.Path:
        target = self.directory.resolve(strict=False)
        root = project.resolve(strict=True)
        if target == root or target.is_relative_to(root):
            raise ProposalError("API receipts must be stored outside the project")
        target.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = target.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ProposalError("receipt directory must be a real directory")
        os.chmod(target, 0o700)
        return target

    @staticmethod
    def _serialize(receipt: dict) -> bytes:
        data = _canonical_json(receipt) + b"\n"
        if len(data) > 2 * MAX_PROPOSAL_BYTES:
            raise ProposalError("receipt exceeds the size limit")
        return data

    def create(self, project: pathlib.Path, receipt: dict) -> pathlib.Path:
        directory = self._prepare(project)
        receipt_id = receipt.get("receipt_id")
        try:
            parsed = uuid.UUID(receipt_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ProposalError("receipt_id must be a UUID") from exc
        if str(parsed) != receipt_id:
            raise ProposalError("receipt_id must use canonical lowercase UUID spelling")
        target = directory / f"{receipt_id}.json"
        payload = self._serialize(receipt)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(target, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(target, 0o600)
            self._fsync_directory(directory)
        except Exception:
            try:
                target.unlink()
            except OSError:
                pass
            raise
        return target

    @staticmethod
    def _fsync_directory(directory: pathlib.Path):
        descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def update_atomic(self, path: pathlib.Path, receipt: dict):
        target = pathlib.Path(path)
        directory = target.parent.resolve(strict=True)
        directory_info = directory.lstat()
        if (
            stat.S_ISLNK(directory_info.st_mode)
            or not stat.S_ISDIR(directory_info.st_mode)
            or directory_info.st_uid != os.geteuid()
            or stat.S_IMODE(directory_info.st_mode) != 0o700
        ):
            raise ProposalError("receipt directory must be a private mode-0700 directory owned by this user")
        info = target.lstat()
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ProposalError("existing receipt is not a private regular file owned by this user")
        payload = self._serialize(receipt)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".receipt-", dir=directory)
        temporary = pathlib.Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            os.chmod(target, 0o600)
            self._fsync_directory(directory)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    def load(self, path: pathlib.Path) -> dict:
        target = pathlib.Path(path)
        directory = target.parent.resolve(strict=True)
        directory_info = directory.lstat()
        if (
            stat.S_ISLNK(directory_info.st_mode)
            or not stat.S_ISDIR(directory_info.st_mode)
            or directory_info.st_uid != os.geteuid()
            or stat.S_IMODE(directory_info.st_mode) != 0o700
        ):
            raise ProposalError("receipt directory must be a private mode-0700 directory owned by this user")
        info = target.lstat()
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ProposalError("receipt is not a regular file owned by this user")
        if info.st_size > 2 * MAX_PROPOSAL_BYTES:
            raise ProposalError("receipt exceeds the size limit")
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            descriptor = os.open(target, flags)
            with os.fdopen(descriptor, "rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or _signature(opened) != _signature(info):
                    raise ProposalError("receipt changed before it could be read")
                data = stream.read(2 * MAX_PROPOSAL_BYTES + 1)
            if len(data) > 2 * MAX_PROPOSAL_BYTES or _signature(info) != _signature(target.lstat()):
                raise ProposalError("receipt changed or exceeded the size limit")
            value = json.loads(data.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ProposalError(f"receipt is unreadable or invalid: {exc}") from exc
        if not isinstance(value, dict) or value.get("schema") != RECEIPT_SCHEMA:
            raise ProposalError("receipt schema is invalid")
        return value


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _new_receipt(project: pathlib.Path, proposal: dict, snapshot: dict, text: str, digest: str) -> dict:
    actions = _action_preconditions(proposal, snapshot)
    horizon_ids = [milestone["id"] for milestone in proposal["horizon"]]
    return {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": str(uuid.uuid4()),
        "project_path": str(project),
        "proposal_sha256": digest,
        "diff_sha256": hashlib.sha256(proposal["diff"].encode("utf-8")).hexdigest(),
        "approved_diff": proposal["diff"],
        "horizon_ids": horizon_ids,
        "approved_horizon": proposal["horizon"],
        "external_actions": proposal["external_actions"],
        "file_actions": actions,
        "branch": snapshot["branch"],
        "baseline_commit": snapshot["baseline_commit"],
        "planning_state_sha256": _workflow_state_digest(snapshot),
        "result_state_sha256": None,
        "result_action_sha256": None,
        "planning_commit": None,
        "image_id": proposal["image_id"],
        "limits": proposal["limits"],
        "approved_at": _utc_timestamp(),
        "usage": {
            "rows_started": 0,
            "rows_started_ids": [],
            "provider_attempts_reserved": 0,
            "commits_reserved": 1,
            "commits_recorded": 0,
            "turns_by_row": {},
        },
        "closure": {"milestones": {}},
        "verification_evidence": [],
        "commit_ids": [],
        "limit_extensions": [],
        "active_operation": {
            "kind": "planning",
            "operation_id": str(uuid.uuid4()),
            "phase": "prepared",
            "expected_head": snapshot["baseline_commit"],
            "row_id": None,
            "closure_phase": None,
            "paths": [action["path"] for action in actions],
        },
        "mutation_scope": "local_only",
        "pause_reason": None,
        "state": "approved",
    }


def _status_paths(core, repo: pathlib.Path) -> tuple[list[str], bool]:
    proc = _git(core, repo, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    raw = proc.stdout
    if not raw:
        return [], True
    if not raw.endswith("\x00"):
        raise ProposalError("Git returned malformed worktree status")
    entries = raw[:-1].split("\x00")
    paths = []
    clean_worktree = True
    for entry in entries:
        if len(entry) < 4 or entry[2] != " ":
            raise ProposalError("Git returned malformed worktree status entry")
        status = entry[:2]
        path = entry[3:]
        if status in {"R ", " R", "C ", " C", "RC", "CR"}:
            raise ProposalError("unexpected rename or copy appeared during planning apply")
        if status[1] != " ":
            clean_worktree = False
        paths.append(path)
    return paths, clean_worktree


def _record_running(core, store: ReceiptStore, path: pathlib.Path, receipt: dict, commit: str):
    receipt["state"] = "running"
    receipt["planning_commit"] = commit
    receipt["commit_ids"] = [commit]
    receipt["usage"]["commits_recorded"] = 1
    receipt["active_operation"] = None
    receipt["pause_reason"] = None
    store.update_atomic(path, receipt)
    return {"status": "running", "receipt": receipt, "receipt_path": str(path)}


def _mark_needs_review(store: ReceiptStore, path: pathlib.Path, receipt: dict, reason: str):
    receipt["state"] = "needs_review"
    receipt["pause_reason"] = reason[:2000]
    store.update_atomic(path, receipt)
    return {"status": "needs_review", "reason": receipt["pause_reason"], "receipt_path": str(path)}


def commit_staged_tree(
    core, repo: pathlib.Path, expected_head: str | None, expected_branch: str | None,
    expected_patch: str, message: str, *, before_ref_update=None,
) -> str:
    """Commit exactly the staged patch on its approved parent with a ref CAS."""

    staged_paths = _decode_paths(
        _git(core, repo, ["diff", "--cached", "--name-only", "-z", "--"]).stdout,
        "staged",
    )
    expected_paths = _patch_paths(core, repo, expected_patch)
    staged_patch = _git(core, repo, ["diff", "--cached", "--binary", "--"]).stdout
    if sorted(staged_paths) != expected_paths or staged_patch != expected_patch:
        raise ProposalError("staged tree differs from the exact patch approved for commit")

    branch_proc = _git(core, repo, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    head_proc = _git(core, repo, ["rev-parse", "--verify", "--quiet", "HEAD"], check=False)
    if branch_proc.returncode not in {0, 1} or head_proc.returncode not in {0, 1}:
        raise ProposalError("cannot verify branch and HEAD before the host commit")
    actual_branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else None
    actual_head = head_proc.stdout.strip() if head_proc.returncode == 0 else None
    expected_branch_normalized = None if expected_branch in {None, "(detached)"} else expected_branch
    if actual_branch != expected_branch_normalized or actual_head != expected_head:
        raise ProposalError("branch or HEAD changed before the host commit")

    tree = _git(core, repo, ["write-tree"]).stdout.strip()
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", tree):
        raise ProposalError("Git returned an invalid staged tree ID")
    commit_args = ["commit-tree", tree]
    if expected_head is not None:
        commit_args.extend(("-p", expected_head))
    commit_args.extend(("-m", message))
    candidate = _git(core, repo, commit_args).stdout.strip()
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", candidate):
        raise ProposalError("Git returned an invalid host commit ID")
    if _git(core, repo, ["show", "--format=", "--binary", candidate]).stdout != expected_patch:
        raise ProposalError("candidate commit differs from the exact staged patch")
    expected_parents = [] if expected_head is None else [expected_head]
    if _parent_lineage(core, repo, candidate) != expected_parents:
        raise ProposalError("candidate commit does not use the approved parent")

    if before_ref_update is not None:
        before_ref_update(candidate, tree)
    symbolic_ref = _git(core, repo, ["symbolic-ref", "--quiet", "HEAD"], check=False)
    if symbolic_ref.returncode == 0:
        refname = symbolic_ref.stdout.strip()
    elif symbolic_ref.returncode == 1:
        refname = "HEAD"
    else:
        raise ProposalError(symbolic_ref.stderr.strip() or "cannot resolve current Git ref")
    if refname != "HEAD" and not refname.startswith("refs/heads/"):
        raise ProposalError("host commit target is not a local branch or detached HEAD")
    object_format = _git(core, repo, ["rev-parse", "--show-object-format"]).stdout.strip()
    zero = "0" * (40 if object_format == "sha1" else 64 if object_format == "sha256" else 0)
    if not zero:
        raise ProposalError("unsupported Git object format for compare-and-swap commit")
    expected_old = expected_head or zero
    update = _git(
        core, repo,
        ["update-ref", "-m", message, refname, candidate, expected_old],
        check=False,
    )
    if update.returncode:
        raise ProposalError(
            "planning ref changed before compare-and-swap: "
            + (update.stderr.strip() or "Git update-ref rejected the expected old value")
        )
    final_head = _git(core, repo, ["rev-parse", "--verify", "HEAD"]).stdout.strip()
    final_branch = _git(core, repo, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    actual_final_branch = final_branch.stdout.strip() if final_branch.returncode == 0 else None
    if final_branch.returncode not in {0, 1} or final_head != candidate or actual_final_branch != expected_branch_normalized:
        raise ProposalError("branch or HEAD changed immediately after the host commit")
    return candidate


def _apply_and_commit(
    core,
    store: ReceiptStore,
    repo: pathlib.Path,
    receipt_path: pathlib.Path,
    receipt: dict,
    title: str,
    fault_hook=None,
):
    paths = [item["path"] for item in receipt["file_actions"]]
    patch = receipt["approved_diff"]
    check = _git(core, repo, ["apply", "--check", "--whitespace=nowarn", "-"], input_text=patch, check=False)
    if check.returncode:
        raise ProposalError("approved planning diff no longer applies: " + (check.stderr.strip() or "Git apply check failed"))
    if fault_hook:
        fault_hook("after_receipt")
    applied = _git(core, repo, ["apply", "--whitespace=nowarn", "-"], input_text=patch, check=False)
    if applied.returncode:
        raise ProposalError("approved planning diff could not be applied: " + (applied.stderr.strip() or "Git apply failed"))
    if fault_hook:
        fault_hook("after_apply")
    changed, _clean_worktree = _status_paths(core, repo)
    if sorted(changed) != sorted(paths):
        return _mark_needs_review(
            store, receipt_path, receipt,
            f"planning apply changed an unexpected path set: {sorted(changed)}",
        )
    applied_snapshot = capture_project_snapshot(core, repo, receipt["file_actions"], allow_dirty=True)
    receipt["result_state_sha256"] = _workflow_state_digest(applied_snapshot)
    receipt["result_action_sha256"] = applied_snapshot["action_hashes"]
    store.update_atomic(receipt_path, receipt)
    if fault_hook:
        fault_hook("after_result_state")
    try:
        literal_paths = [f":(top,literal){path}" for path in paths]
        _git(core, repo, ["add", "-f", "--", *literal_paths])
    except ProposalError as exc:
        return _mark_needs_review(
            store, receipt_path, receipt,
            f"approved changes are present but cannot be staged safely: {exc}",
        )
    staged = _decode_paths(
        _git(core, repo, ["diff", "--cached", "--name-only", "-z", "--"]).stdout,
        "staged",
    )
    if sorted(staged) != sorted(paths):
        return _mark_needs_review(
            store, receipt_path, receipt,
            f"staging changed an unexpected path set: {sorted(staged)}",
        )
    status_paths, worktree_clean = _status_paths(core, repo)
    if not worktree_clean or sorted(status_paths) != sorted(paths):
        return _mark_needs_review(store, receipt_path, receipt, "staging left an unexpected worktree or index state")
    staged_patch = _git(core, repo, ["diff", "--cached", "--binary", "--"]).stdout
    if staged_patch != patch:
        return _mark_needs_review(
            store, receipt_path, receipt,
            "staged patch differs from the exact planning diff the user confirmed",
        )
    message = "Planning update: " + title.replace("\n", " ").strip()
    if len(message) > 120:
        message = message[:117].rstrip() + "..."
    receipt["active_operation"]["phase"] = "precommit_verified"
    store.update_atomic(receipt_path, receipt)
    if fault_hook:
        fault_hook("before_commit")

    def mark_commit_attempted(candidate: str, tree: str):
        receipt["active_operation"].update({
            "phase": "commit_attempted",
            "candidate_commit": candidate,
            "expected_tree": tree,
            "expected_patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
            "commit_message": message,
        })
        store.update_atomic(receipt_path, receipt)
        if fault_hook:
            fault_hook("before_ref_update")

    try:
        commit = commit_staged_tree(
            core, repo, receipt["baseline_commit"], receipt["branch"], patch, message,
            before_ref_update=mark_commit_attempted,
        )
    except ProposalError as exc:
        return _mark_needs_review(
            store, receipt_path, receipt,
            "planning changes are staged but the compare-and-swap commit failed: " + str(exc),
        )
    if fault_hook:
        fault_hook("after_commit")
    try:
        parents = _parent_lineage(core, repo, commit)
    except ProposalError as exc:
        return _mark_needs_review(store, receipt_path, receipt, f"cannot prove planning commit lineage: {exc}")
    expected_parents = [] if receipt["baseline_commit"] is None else [receipt["baseline_commit"]]
    if parents != expected_parents:
        return _mark_needs_review(store, receipt_path, receipt, "planning commit is not directly based on the approved baseline")
    current_branch = _git(core, repo, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    actual_branch = current_branch.stdout.strip() if current_branch.returncode == 0 else None
    current_head = _git(core, repo, ["rev-parse", "--verify", "HEAD"]).stdout.strip()
    if actual_branch != receipt["branch"] or current_head != commit:
        return _mark_needs_review(store, receipt_path, receipt, "branch or HEAD changed during the planning commit")
    after_paths, clean_after = _status_paths(core, repo)
    if after_paths or not clean_after:
        return _mark_needs_review(store, receipt_path, receipt, "planning commit did not leave a clean checkpoint")
    actual_patch = _git(core, repo, ["show", "--format=", "--binary", commit]).stdout
    if actual_patch != patch:
        return _mark_needs_review(store, receipt_path, receipt, "planning commit does not match the approved diff")
    return _record_running(core, store, receipt_path, receipt, commit)


def approve_proposal(
    core,
    project: pathlib.Path,
    proposal: dict,
    *,
    receipt_store: ReceiptStore | None = None,
    input_fn=input,
    output_fn=print,
    revise_fn=None,
    fault_hook=None,
) -> dict:
    """Display, confirm, durably receipt, apply, and commit one exact plan."""

    repo = _project_root(core, project)
    store = receipt_store or ReceiptStore()
    plan = validate_proposal(proposal)
    snapshot = capture_project_snapshot(core, repo, plan["file_actions"])
    while True:
        _validate_patch(core, repo, plan, snapshot)
        visible, proposal_digest = render_proposal(plan, snapshot)
        output_fn(visible)
        choice = input_fn("Type exactly `confirm` to approve, `reject` to revise, or anything else to stop: ")
        if choice == "reject":
            feedback = input_fn("What should change in the proposal? ")
            if not isinstance(feedback, str) or len(feedback) > 20000:
                raise ProposalError("proposal feedback must be text of at most 20000 characters")
            if revise_fn is None:
                return {"status": "rejected", "feedback": feedback}
            revised = revise_fn(plan, feedback)
            if not isinstance(revised, dict):
                return {"status": "rejected", "feedback": feedback}
            plan = validate_proposal(revised)
            snapshot = capture_project_snapshot(core, repo, plan["file_actions"])
            continue
        if choice != "confirm":
            return {"status": "cancelled"}
        try:
            current = capture_project_snapshot(core, repo, plan["file_actions"], allow_dirty=True)
        except ProposalError as exc:
            raise ApprovalStale(f"project state cannot be revalidated after display: {exc}") from exc
        drift = _snapshot_drift(snapshot, current)
        if drift:
            if revise_fn is None:
                raise ApprovalStale("project changed after proposal display: " + ", ".join(drift))
            output_fn("Project drift requires a revised proposal: " + ", ".join(drift))
            revised = revise_fn(plan, "Project changed after display: " + ", ".join(drift))
            if not isinstance(revised, dict):
                raise ApprovalStale("approval became stale and no revised proposal was returned")
            plan = validate_proposal(revised)
            try:
                snapshot = capture_project_snapshot(core, repo, plan["file_actions"])
            except ProposalError as exc:
                raise ApprovalStale(f"revised proposal needs a clean committed baseline: {exc}") from exc
            continue
        _validate_patch(core, repo, plan, current)
        text, final_digest = render_proposal(plan, current)
        if final_digest != proposal_digest or text != visible:
            raise ApprovalStale("proposal rendering changed before confirmation")
        receipt = _new_receipt(repo, plan, current, visible, proposal_digest)
        receipt_path = store.create(repo, receipt)
        return _apply_and_commit(
            core, store, repo, receipt_path, receipt, plan["title"], fault_hook=fault_hook,
        )


def _set_needs_review(store, receipt_path: pathlib.Path, receipt: dict, reason: str):
    return _mark_needs_review(store, receipt_path, receipt, reason)


def _parent_lineage(core, repo: pathlib.Path, commit: str) -> list[str]:
    line = _git(core, repo, ["rev-list", "--parents", "-n", "1", commit]).stdout.strip().split()
    if not line or line[0] != commit:
        raise ProposalError("cannot prove planning commit lineage")
    return line[1:]


def resume_approved_receipt(
    core,
    project: pathlib.Path,
    receipt_path: pathlib.Path,
    *,
    receipt_store: ReceiptStore | None = None,
    fault_hook=None,
) -> dict:
    """Resume a clean approved checkpoint or reconcile its one planning commit."""

    repo = _project_root(core, project)
    store = receipt_store or ReceiptStore(pathlib.Path(receipt_path).parent)
    try:
        receipt_file = pathlib.Path(receipt_path).resolve(strict=True)
        receipts_dir = store.directory.resolve(strict=True)
    except OSError as exc:
        raise ProposalError(f"receipt path is unavailable: {exc}") from exc
    if receipt_file.is_relative_to(repo) or receipt_file.parent != receipts_dir:
        raise ProposalError("receipt path must be in the private state directory outside the project")
    receipt_path = receipt_file
    receipt = store.load(receipt_path)
    if receipt.get("project_path") != str(repo):
        raise ProposalError("receipt belongs to a different project")
    if receipt.get("state") not in RECEIPT_STATES:
        return _set_needs_review(store, receipt_path, receipt, "receipt state is missing or unsupported")
    receipt_id = receipt.get("receipt_id")
    try:
        parsed_receipt_id = uuid.UUID(receipt_id)
    except (ValueError, TypeError, AttributeError):
        return _set_needs_review(store, receipt_path, receipt, "receipt ID is invalid")
    if str(parsed_receipt_id) != receipt_id or receipt_path.name != f"{receipt_id}.json":
        return _set_needs_review(store, receipt_path, receipt, "receipt ID does not match its private filename")
    if not isinstance(receipt.get("proposal_sha256"), str) or not _HEX.fullmatch(receipt["proposal_sha256"]):
        return _set_needs_review(store, receipt_path, receipt, "proposal digest is invalid")
    planning_state = receipt.get("planning_state_sha256")
    if not isinstance(planning_state, str) or not _HEX.fullmatch(planning_state):
        return _set_needs_review(store, receipt_path, receipt, "approved receipt has an invalid planning state digest")
    result_state = receipt.get("result_state_sha256")
    if result_state is not None and (not isinstance(result_state, str) or not _HEX.fullmatch(result_state)):
        return _set_needs_review(store, receipt_path, receipt, "approved receipt has an invalid post-apply state digest")
    result_actions = receipt.get("result_action_sha256")
    if result_actions is not None and not isinstance(result_actions, dict):
        return _set_needs_review(store, receipt_path, receipt, "approved receipt has invalid post-apply file hashes")
    if receipt.get("state") != "approved":
        return {"status": receipt.get("state"), "receipt": receipt, "receipt_path": str(receipt_path)}
    actions = receipt.get("file_actions")
    patch = receipt.get("approved_diff")
    baseline = receipt.get("baseline_commit")
    branch = receipt.get("branch")
    if not isinstance(actions, list) or not actions or not isinstance(patch, str):
        return _set_needs_review(store, receipt_path, receipt, "approved receipt lacks its exact file actions or diff")
    try:
        if any(
            not isinstance(item, dict)
            or set(item) != {"path", "action", "source_sha256"}
            or not isinstance(item.get("action"), str)
            or item.get("action") not in {"create", "replace", "delete"}
            or (
                item.get("source_sha256") is not None
                and (not isinstance(item.get("source_sha256"), str) or not _HEX.fullmatch(item["source_sha256"]))
            )
            for item in actions
        ):
            raise ProposalError("receipt file actions are malformed")
        action_paths = [_project_path(item["path"]) for item in actions]
        if len(set(action_paths)) != len(actions):
            raise ProposalError("receipt repeats a file-action path")
        if baseline is not None and (not isinstance(baseline, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", baseline)):
            raise ProposalError("receipt baseline commit ID is invalid")
        if branch is not None and not isinstance(branch, str):
            raise ProposalError("receipt branch is invalid")
        if not isinstance(receipt.get("diff_sha256"), str) or not _HEX.fullmatch(receipt["diff_sha256"]):
            raise ProposalError("receipt diff digest is invalid")
        if hashlib.sha256(patch.encode("utf-8", errors="strict")).hexdigest() != receipt["diff_sha256"]:
            raise ProposalError("approved diff digest does not match the receipt")
        current = capture_project_snapshot(core, repo, actions, allow_dirty=True)
    except (ProposalError, UnicodeError, KeyError) as exc:
        return _set_needs_review(store, receipt_path, receipt, f"cannot inspect approved recovery state: {exc}")
    head = current["baseline_commit"]
    if current["branch"] != branch:
        return _set_needs_review(store, receipt_path, receipt, "branch changed since planning approval")
    if not current["clean"]:
        return _set_needs_review(store, receipt_path, receipt, "worktree or index is dirty after an interrupted planning apply")
    try:
        patch_paths = _patch_paths(core, repo, patch)
        patch_kinds = _patch_action_kinds(core, repo, patch)
    except ProposalError as exc:
        return _set_needs_review(store, receipt_path, receipt, f"approved diff is invalid: {exc}")
    expected_paths = sorted(item["path"] for item in actions)
    declared_kinds = {
        item["path"]: item["action"]
        for item in actions
        if item["action"] in {"create", "delete"}
    }
    if patch_paths != expected_paths or patch_kinds != declared_kinds:
        return _set_needs_review(store, receipt_path, receipt, "approved diff paths or actions differ from receipt")
    if head == baseline:
        recorded_result = receipt.get("result_state_sha256")
        if recorded_result is not None or receipt.get("result_action_sha256") is not None:
            return _set_needs_review(
                store, receipt_path, receipt,
                "receipt records an applied diff but HEAD is back at the baseline; automatic replay is unsafe",
            )
        if _workflow_state_digest(current) != planning_state:
            return _set_needs_review(store, receipt_path, receipt, "workflow files or permanent IDs changed before planning apply")
        expected = {item["path"]: item.get("source_sha256") for item in actions}
        if current["action_hashes"] != expected:
            return _set_needs_review(store, receipt_path, receipt, "file-action source hashes changed before planning apply")
        proposal = {
            "title": "recovered planning update",
            "diff": patch,
            "file_actions": [{"path": item["path"], "action": item["action"]} for item in actions],
        }
        try:
            _validate_recovery_patch(core, repo, proposal, current)
        except ProposalError as exc:
            return _set_needs_review(store, receipt_path, receipt, f"approved diff no longer applies: {exc}")
        return _apply_and_commit(
            core, store, repo, pathlib.Path(receipt_path), receipt, "recovered planning update", fault_hook,
        )
    if not isinstance(result_state, str) or not _HEX.fullmatch(result_state):
        return _set_needs_review(store, receipt_path, receipt, "approved receipt has no verified post-apply state digest")
    if not isinstance(result_actions, dict) or set(result_actions) != set(action_paths) or any(
        value is not None and (not isinstance(value, str) or not _HEX.fullmatch(value))
        for value in result_actions.values()
    ):
        return _set_needs_review(store, receipt_path, receipt, "approved receipt has no complete post-apply file hash set")
    if current["action_hashes"] != result_actions:
        return _set_needs_review(store, receipt_path, receipt, "an approved file-action target drifted after planning commit")
    if _workflow_state_digest(current) != result_state:
        return _set_needs_review(store, receipt_path, receipt, "workflow files or permanent IDs drifted after planning commit")
    try:
        parents = _parent_lineage(core, repo, head)
        expected_parents = [] if baseline is None else [baseline]
        actual_patch = _git(core, repo, ["show", "--format=", "--binary", head]).stdout
        diff_tree = ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z"]
        if baseline is None:
            diff_tree.append("--root")
        diff_tree.append(head)
        changed = _decode_paths(
            _git(core, repo, diff_tree).stdout,
            "planning commit",
        )
    except ProposalError as exc:
        return _set_needs_review(store, receipt_path, receipt, f"cannot reconcile planning commit: {exc}")
    expected_paths = sorted(item["path"] for item in actions)
    expected_diff_digest = receipt.get("diff_sha256")
    if parents != expected_parents or sorted(changed) != expected_paths:
        return _set_needs_review(store, receipt_path, receipt, "HEAD is not the single approved planning commit")
    if not isinstance(expected_diff_digest, str) or hashlib.sha256(patch.encode("utf-8")).hexdigest() != expected_diff_digest:
        return _set_needs_review(store, receipt_path, receipt, "approved diff digest does not match the receipt")
    if actual_patch != patch:
        return _set_needs_review(store, receipt_path, receipt, "planning commit patch differs from the approved diff")
    return _record_running(core, store, pathlib.Path(receipt_path), receipt, head)


def _validate_recovery_patch(core, repo: pathlib.Path, proposal: dict, snapshot: dict):
    paths = _patch_paths(core, repo, proposal["diff"])
    actions = sorted(item["path"] for item in proposal["file_actions"])
    if paths != actions:
        raise ProposalError("diff paths differ from receipt actions")
    patch_kinds = _patch_action_kinds(core, repo, proposal["diff"])
    declared_kinds = {
        item["path"]: item["action"]
        for item in proposal["file_actions"]
        if item["action"] in {"create", "delete"}
    }
    if patch_kinds != declared_kinds:
        raise ProposalError("diff create/delete operations differ from receipt actions")
    check = _git(core, repo, ["apply", "--check", "--whitespace=nowarn", "-"], input_text=proposal["diff"], check=False)
    if check.returncode:
        raise ProposalError(check.stderr.strip() or "Git apply check failed")

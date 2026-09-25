"""Read-only live project and private horizon receipt status."""
from __future__ import annotations

import pathlib
import re
import stat
import os


class StatusError(RuntimeError):
    """Live project state could not be read safely."""


def _private_receipts(core, repo, store):
    directory = pathlib.Path(store.directory).expanduser()
    if not directory.exists() and not directory.is_symlink():
        return [], []
    if directory.is_symlink():
        return [], ["receipt directory is a symbolic link"]
    try:
        info = directory.lstat()
    except OSError as exc:
        return [], [f"receipt directory is unavailable: {exc}"]
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        return [], ["receipt directory is not a private mode-0700 directory owned by this user"]
    receipts, errors = [], []
    try:
        paths = sorted(directory.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        return [], [f"receipt directory cannot be listed: {exc}"]
    for path in paths:
        if path.suffix != ".json":
            continue
        try:
            item_info = path.lstat()
            if (
                not stat.S_ISREG(item_info.st_mode)
                or item_info.st_uid != os.geteuid()
                or stat.S_IMODE(item_info.st_mode) != 0o600
            ):
                raise ValueError("receipt is not a private regular file owned by this user")
            receipt = store.load(path)
            if receipt.get("project_path") == str(repo):
                receipts.append({"path": str(path), "receipt": receipt})
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    receipts.sort(key=lambda item: item["receipt"].get("approved_at", ""), reverse=True)
    return receipts, errors


def status_report(core, repo: pathlib.Path, receipt_store=None) -> dict:
    """Read live Markdown and receipts without acquiring a write lock or creating files."""

    project = pathlib.Path(repo).expanduser().resolve(strict=True)
    root_proc = core.git_local(["rev-parse", "--show-toplevel"], project)
    if root_proc.returncode:
        raise StatusError(root_proc.stderr.strip() or "selected project is not a Git worktree")
    root = pathlib.Path(root_proc.stdout.strip()).resolve(strict=True)
    if root != project:
        raise StatusError(f"selected path is not the Git worktree root: {root}")
    try:
        snapshot = core.row_snapshot(root)
    except (OSError, UnicodeError, ValueError) as exc:
        raise StatusError(f"live milestone/status state cannot be read: {exc}") from exc
    if snapshot.get("history", {}).get("problems"):
        state_problems = list(snapshot["history"]["problems"])
    else:
        state_problems = []
    counts = {}
    for (filename, _label, _occurrence), state in snapshot.get("states", {}).items():
        counts.setdefault(filename, {})[state] = counts.setdefault(filename, {}).get(state, 0) + 1
    milestone_ids = sorted(
        name.removeprefix("status-").removesuffix(".md")
        for name in snapshot.get("files", set())
        if re.fullmatch(r"status-[A-Z](?:0[1-9]|[1-9][0-9])\.md", name)
    )
    in_progress = [
        {"file": name, "task": label, "occurrence": occurrence}
        for (name, label, occurrence), state in snapshot.get("states", {}).items()
        if state == "in_progress"
    ]
    blocked = [
        {"file": name, "task": label, "occurrence": occurrence}
        for (name, label, occurrence), state in snapshot.get("states", {}).items()
        if state == "blocked"
    ]
    if receipt_store is None:
        import importlib.util
        proposal_path = pathlib.Path(__file__).resolve().with_name("tabilet_proposal.py")
        spec = importlib.util.spec_from_file_location("_tabilet_status_proposal", proposal_path)
        if spec is None or spec.loader is None:
            raise StatusError("receipt reader is unavailable")
        proposal = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(proposal)
        receipt_store = proposal.ReceiptStore()
    receipts, receipt_errors = _private_receipts(core, root, receipt_store)
    receipt_records = []
    for item in receipts:
        receipt = item["receipt"]
        usage, limits = receipt.get("usage", {}), receipt.get("limits", {})
        remaining = {}
        mapping = {
            "rows": ("max_rows", "rows_started"),
            "provider_attempts": ("max_provider_attempts", "provider_attempts_reserved"),
            "commits": ("max_commits", "commits_reserved"),
        }
        for label, (limit_key, usage_key) in mapping.items():
            cap, used = limits.get(limit_key), usage.get(usage_key)
            remaining[label] = max(0, cap - used) if isinstance(cap, int) and isinstance(used, int) else None
        closure = receipt.get("closure", {}).get("milestones", {})
        receipt_records.append({
            "receipt_id": receipt.get("receipt_id"),
            "state": receipt.get("state", "invalid"),
            "pause_reason": receipt.get("pause_reason"),
            "approved_at": receipt.get("approved_at"),
            "horizon": receipt.get("horizon_ids", []),
            "review_iterations": {
                identity: record.get("review_iterations", 0)
                for identity, record in closure.items() if isinstance(record, dict)
            },
            "usage": usage,
            "limits": limits,
            "remaining": remaining,
            "active_operation": receipt.get("active_operation"),
            "path": item["path"],
        })
    return {
        "project": str(root),
        "branch": core.git_branch(root),
        "head": core.git_head(root),
        "milestones": [
            {"id": identity, "rows": counts.get(f"status-{identity}.md", {})}
            for identity in milestone_ids
        ],
        "in_progress": in_progress,
        "blocked": blocked,
        "review_count": {
            identity: record.get("review_iterations", 0)
            for receipt in receipt_records
            for identity, record in receipt.get("review_iterations", {}).items()
        },
        "receipt": receipt_records,
        "receipt_errors": receipt_errors,
        "state_problems": state_problems,
    }


def format_status(report: dict) -> str:
    """Render a stable, operator-oriented plain text summary."""

    import json
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)

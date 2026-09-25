"""Receipt-bounded execution, dependency selection, and closure helpers."""
from __future__ import annotations

import stat
import importlib.util
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import uuid
import datetime


class HorizonError(RuntimeError):
    """The approved horizon is malformed or no longer matches live state."""


class LimitPaused(HorizonError):
    """A cumulative confirmed execution limit has been reached."""


class _UnresolvedDependency(HorizonError):
    """Live dependency evidence is ambiguous or outside authorized scope."""


def _load_index_module():
    """Load the shared Markdown projection parser without creating an index."""

    harness_dir = pathlib.Path(__file__).resolve().parent
    if str(harness_dir) not in sys.path:
        sys.path.insert(0, str(harness_dir))
    path = harness_dir / "tabilet_index.py"
    spec = importlib.util.spec_from_file_location("_tabilet_horizon_index", path)
    if spec is None or spec.loader is None:
        raise HorizonError("the shared live Markdown dependency parser is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _live_projection(core, project: pathlib.Path) -> dict:
    """Read current Markdown with the shared parser and the runner's state gate."""

    index = _load_index_module()
    snapshot = core.row_snapshot(project)
    if snapshot["history"]["problems"]:
        raise _UnresolvedDependency("live status/history needs review: " + "; ".join(snapshot["history"]["problems"]))
    inventory = index.inventory(project)
    parsed = {}
    for relative, kind in inventory.items():
        if kind not in {"milestone", "active_status", "history_status"}:
            continue
        text, digest, _ = index.read_document(project, relative)
        parsed[relative] = index.parse_document(relative, kind, text, digest)
    milestone_doc = parsed.get("tabilet/memory-bank/milestone.md")
    if milestone_doc is None:
        raise _UnresolvedDependency("live milestone.md is missing")

    rows = []
    dependencies = {}
    for relative, document in parsed.items():
        kind = inventory[relative]
        if kind not in {"active_status", "history_status"}:
            continue
        path = pathlib.PurePosixPath(relative)
        milestone_id = path.stem.removeprefix("status-")
        counts = {}
        for task in document["index_tasks"]:
            label = task["label"]
            counts[label] = counts.get(label, 0) + 1
            occurrence = counts[label]
            state_key = (path.name, label, occurrence)
            state = snapshot["states"].get(state_key)
            if state is None:
                raise _UnresolvedDependency(
                    f"task row drifted while selecting: {path.name} / {label!r}"
                )
            explicit = task.get("explicit_id")
            dependency_key = (
                f"{milestone_id}/{explicit}" if explicit
                else f"{relative}#{task['line']}"
            )
            row = {
                "key": state_key,
                "file": path.name,
                "path": relative,
                "milestone_id": milestone_id,
                "label": label,
                "task_id": explicit or label,
                "explicit_id": explicit,
                "state": state,
                "line": task["line"],
                "notes": task["notes"],
                "dependency_key": dependency_key,
                "lifecycle": "active" if kind == "active_status" else "retired",
            }
            rows.append(row)
            dependencies[dependency_key] = [
                dependency
                for dependency in document["index_task_dependencies"]
                if dependency["source_key"] == dependency_key
            ]

    active_order = {}
    for milestone in milestone_doc["index_milestone_projection"]:
        active_order[milestone["milestone_id"]] = milestone["display_order"]
    milestone_edges = {}
    for edge in milestone_doc["index_relationships"]:
        if edge["relation"] != "depends_on" or not edge["source"].startswith("milestone:"):
            continue
        source = edge["source"].removeprefix("milestone:")
        target = edge["target"].removeprefix("milestone:")
        milestone_edges.setdefault(source, []).append({"target": target, "line": edge["line"]})

    history = snapshot["history"]["records"]
    milestone_state = {}
    for milestone_id in set(active_order) | {
        name.removeprefix("status-").removesuffix(".md") for name in history
    }:
        active = f"status-{milestone_id}.md" in snapshot["active"]
        retired = history.get(f"status-{milestone_id}.md")
        milestone_state[milestone_id] = {
            "lifecycle": "active" if active else "retired" if retired else "missing",
            "outcome": retired["metadata"]["Outcome"] if retired else None,
            "specification": snapshot["specifications"].get(f"status-{milestone_id}.md"),
        }
    return {
        "snapshot": snapshot,
        "rows": rows,
        "dependencies": dependencies,
        "milestone_order": active_order,
        "milestone_edges": milestone_edges,
        "milestones": milestone_state,
    }


def _task_candidates(index, rows: list[dict], dependency: dict, source: dict) -> list[dict]:
    if dependency.get("target_milestone_id"):
        return [
            row for row in rows
            if row["milestone_id"] == dependency["target_milestone_id"]
            and row["explicit_id"] == dependency.get("target_explicit_id")
        ]
    target = dependency["target_key"]
    same_milestone = [
        row for row in rows
        if row["milestone_id"] == source["milestone_id"] and row["explicit_id"] == target
    ]
    candidates = same_milestone or [row for row in rows if row["explicit_id"] == target]
    if not candidates:
        candidates = [
            row for row in rows
            if row["milestone_id"] == source["milestone_id"] and row["label"] == target
        ]
        if not candidates:
            candidates = [row for row in rows if row["label"] == target]
    return candidates


def _successor_for(index, row: dict, rows: list[dict]) -> dict:
    text = row["notes"]
    match = re.search(r"\baccepted successor\b", text, re.I)
    if not match:
        raise _UnresolvedDependency(
            f"historical row {row['file']} / {row['label']!r} has no accepted successor"
        )
    tail = text[match.end():].split("|", 1)[0].split(";", 1)[0].split(".", 1)[0]
    candidates = []
    qualified = {}
    for item in rows:
        qualified.setdefault(f"{item['milestone_id']}/{item['task_id']}", []).append(item)
    qualified_spans = []
    for identifier in sorted(qualified, key=len, reverse=True):
        pattern = re.compile(
            r"(?<![A-Za-z0-9_./-])" + re.escape(identifier) + r"(?![A-Za-z0-9_.-])"
        )
        for found in pattern.finditer(tail):
            qualified_spans.append(found.span())
            candidates.extend(qualified[identifier])

    task_ids = {item["task_id"] for item in rows}
    for identifier in sorted(task_ids, key=len, reverse=True):
        pattern = re.compile(
            r"(?<![A-Za-z0-9_./-])" + re.escape(identifier) + r"(?![A-Za-z0-9_.-])"
        )
        for found in pattern.finditer(tail):
            # A qualified reference is one token: its task-ID suffix is not a
            # second, unqualified successor candidate.
            if any(start <= found.start() and found.end() <= end for start, end in qualified_spans):
                continue
            candidates.extend(item for item in rows if item["task_id"] == identifier)
    unique = {item["key"]: item for item in candidates}
    if len(unique) != 1:
        raise _UnresolvedDependency(
            f"historical row {row['file']} / {row['label']!r} has an ambiguous accepted successor"
        )
    return next(iter(unique.values()))


def _validate_horizon(receipt: dict) -> tuple[list[dict], set[str]]:
    horizon = receipt.get("approved_horizon")
    ids = receipt.get("horizon_ids")
    if not isinstance(horizon, list) or not horizon or not isinstance(ids, list):
        raise _UnresolvedDependency("receipt lacks its complete approved horizon")
    horizon_ids = [item.get("id") if isinstance(item, dict) else None for item in horizon]
    if any(
        not isinstance(identifier, str) or not re.fullmatch(r"[A-Z][A-Z0-9-]{0,15}", identifier)
        for identifier in ids
    ) or len(set(ids)) != len(ids) or horizon_ids != ids:
        raise _UnresolvedDependency("receipt horizon IDs do not match the approved milestone details")
    task_ids = set()
    for milestone in horizon:
        if not isinstance(milestone, dict) or not isinstance(milestone.get("tasks"), list) or not milestone["tasks"]:
            raise _UnresolvedDependency("receipt contains malformed approved milestone details")
        identity = milestone.get("id")
        acceptance = milestone.get("acceptance")
        if isinstance(acceptance, str):
            valid_acceptance = bool(acceptance.strip())
        elif isinstance(acceptance, list):
            valid_acceptance = bool(acceptance) and all(isinstance(item, str) and item.strip() for item in acceptance)
        else:
            valid_acceptance = False
        if not valid_acceptance:
            raise _UnresolvedDependency(f"receipt milestone {identity} lacks acceptance criteria")
        if not isinstance(milestone.get("closure_paths"), list):
            raise _UnresolvedDependency(f"receipt lacks closure paths for {identity}")
        if f"tabilet/memory-bank/status-{identity}.md" not in milestone["closure_paths"]:
            raise _UnresolvedDependency(f"receipt closure scope for {identity} omits its status file")
        for path in milestone["closure_paths"]:
            _validate_scope_path(path)
        if len(set(milestone["closure_paths"])) != len(milestone["closure_paths"]):
            raise _UnresolvedDependency(f"receipt closure paths for {identity} are duplicated")
        if not isinstance(milestone.get("retirement_adopted", False), bool):
            raise _UnresolvedDependency(f"receipt retirement policy for {identity} is malformed")
        for task in milestone["tasks"]:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str):
                raise _UnresolvedDependency("receipt contains a malformed approved task row")
            if task["id"] in task_ids:
                raise _UnresolvedDependency("receipt contains duplicate approved task IDs")
            task_ids.add(task["id"])
            if not isinstance(task.get("approved_paths"), list) or not isinstance(task.get("verification"), list):
                raise _UnresolvedDependency(f"approved task {task['id']} lacks paths or required checks")
            if f"tabilet/memory-bank/status-{identity}.md" not in task["approved_paths"]:
                raise _UnresolvedDependency(f"approved task {task['id']} omits its status file")
            for path in task["approved_paths"]:
                _validate_scope_path(path)
            if len(set(task["approved_paths"])) != len(task["approved_paths"]):
                raise _UnresolvedDependency(f"approved paths for task {task['id']} are duplicated")
            if not task["verification"] or any(not isinstance(command, str) or not command.strip() for command in task["verification"]):
                raise _UnresolvedDependency(f"approved task {task['id']} has invalid verification commands")
    return horizon, set(ids)


def _validate_scope_path(value) -> str:
    if (
        not isinstance(value, str) or not value or value.startswith("/")
        or "\\" in value or "\x00" in value
        or any(part in {"", ".", "..", ".git"} for part in value.split("/"))
    ):
        raise _UnresolvedDependency("receipt contains an unsafe project-relative path")
    return value


def _validate_project_files(repo: pathlib.Path, paths) -> None:
    """Reject symlink or non-directory path components before provider or Git access."""

    root = pathlib.Path(repo).resolve(strict=True)
    for value in paths:
        relative = _validate_scope_path(value)
        current = root
        components = relative.split("/")
        for position, component in enumerate(components):
            current = current / component
            try:
                info = current.lstat()
            except FileNotFoundError:
                break
            except OSError as exc:
                raise _UnresolvedDependency(f"cannot inspect approved path {relative}: {exc}") from exc
            if stat.S_ISLNK(info.st_mode):
                raise _UnresolvedDependency(f"approved path contains a symbolic link: {relative}")
            if position < len(components) - 1 and not stat.S_ISDIR(info.st_mode):
                raise _UnresolvedDependency(f"approved path parent is not a directory: {relative}")
            if position == len(components) - 1 and not stat.S_ISREG(info.st_mode):
                raise _UnresolvedDependency(f"approved path is not a regular file: {relative}")


def _row_ready(index, row: dict, live: dict, horizon_ids: set[str], approved_tasks: dict[str, set[str]]) -> tuple[bool, str | None]:
    for dependency in live["dependencies"].get(row["dependency_key"], []):
        if dependency.get("milestone_id") != row["milestone_id"]:
            continue
        targets = _task_candidates(index, live["rows"], dependency, row)
        if len(targets) != 1:
            raise _UnresolvedDependency(
                f"unresolved task dependency {dependency.get('target_key')!r} on "
                f"{row['file']} / {row['label']!r}"
            )
        target = targets[0]
        if target["milestone_id"] not in horizon_ids and target["state"] not in {"completed", "historical"}:
            raise _UnresolvedDependency(
                f"task dependency {target['milestone_id']}/{target['task_id']} is outside the approved horizon"
            )
        if target["state"] == "completed":
            continue
        if target["state"] == "historical":
            successor = _successor_for(index, target, live["rows"])
            if successor["milestone_id"] not in horizon_ids:
                raise _UnresolvedDependency(
                    f"accepted successor {successor['milestone_id']}/{successor['task_id']} is outside the approved horizon"
                )
            if not _row_is_approved(successor, approved_tasks):
                raise _UnresolvedDependency(
                    f"accepted successor {successor['milestone_id']}/{successor['task_id']} is outside approved task scope"
                )
            if successor["key"] == row["key"]:
                continue
            if successor["state"] == "completed":
                continue
            return False, f"accepted successor {successor['task_id']} is not completed"
        if target["state"] in {"blocked", "cancelled"}:
            raise _UnresolvedDependency(
                f"task dependency {target['task_id']} is {target['state']}"
            )
        return False, f"task dependency {target['task_id']} is not complete"
    return True, None


def _row_is_approved(row: dict, approved_tasks: dict[str, set[str]]) -> bool:
    allowed = approved_tasks.get(row["milestone_id"], set())
    return row["task_id"] in allowed or row["label"] in allowed


def select_next_row(core, project: pathlib.Path, receipt: dict) -> dict:
    """Select the first live dependency-ready row in the confirmed horizon."""

    if receipt.get("state") not in {"running", "paused"}:
        raise _UnresolvedDependency("receipt is not in a resumable execution state")
    horizon, horizon_ids = _validate_horizon(receipt)
    index = _load_index_module()
    live = _live_projection(core, project)
    closure = receipt.get("closure")
    if not isinstance(closure, dict) or not isinstance(closure.get("milestones"), dict):
        raise _UnresolvedDependency("receipt has malformed closure checkpoints")
    closure_milestones = closure["milestones"]
    milestone_by_id = {milestone["id"]: milestone for milestone in horizon}
    for identity, checkpoint in closure_milestones.items():
        milestone = milestone_by_id.get(identity)
        if milestone is None or not isinstance(checkpoint, dict):
            raise _UnresolvedDependency("receipt contains an unknown or malformed closure checkpoint")
        allowed_phases = {"review", "acceptance", "consolidation", "downstream", "verified"}
        if milestone.get("retirement_adopted") is True:
            allowed_phases.add("retirement")
        phase = checkpoint.get("phase")
        state = checkpoint.get("closure_state")
        if phase not in allowed_phases or state not in {"pending", "verified"}:
            raise _UnresolvedDependency(f"receipt closure checkpoint for {identity} has an invalid phase or state")
        if (phase == "verified") != (state == "verified"):
            raise _UnresolvedDependency(f"receipt closure checkpoint for {identity} has an inconsistent completion state")
    approved_task_ids = {
        milestone["id"]: {task["id"] for task in milestone["tasks"]}
        for milestone in horizon
    }
    order = live["milestone_order"]
    ordered = sorted(
        horizon,
        key=lambda milestone: (
            order.get(milestone["id"], 2**31),
            receipt["horizon_ids"].index(milestone["id"]),
        ),
    )
    in_progress = [row for row in live["rows"] if row["state"] == "in_progress"]
    if len(in_progress) > 1:
        raise _UnresolvedDependency("more than one live task row is in progress")
    if in_progress:
        resume_milestone = in_progress[0]["milestone_id"]
        if resume_milestone not in horizon_ids:
            raise _UnresolvedDependency(
                f"in-progress row {resume_milestone}/{in_progress[0]['task_id']} is outside the approved horizon"
            )
        usage = receipt.get("usage")
        started_rows = usage.get("rows_started_ids") if isinstance(usage, dict) else None
        in_progress_id = f"{in_progress[0]['milestone_id']}/{in_progress[0]['task_id']}"
        if not isinstance(started_rows, list) or in_progress_id not in started_rows:
            raise _UnresolvedDependency(
                f"in-progress row {in_progress_id} has no receipt provenance; manual review is required"
            )
        ordered = [milestone for milestone in ordered if milestone["id"] == resume_milestone]
    waiting_reasons = []
    for milestone in ordered:
        identity = milestone["id"]
        live_milestone = live["milestones"].get(identity)
        if live_milestone is None or live_milestone["lifecycle"] == "missing":
            raise _UnresolvedDependency(f"approved milestone {identity} has no live or retired record")
        if live_milestone["lifecycle"] == "retired":
            if live_milestone["outcome"] != "completed":
                raise _UnresolvedDependency(f"approved milestone {identity} was retired without completed outcome")
            closure_milestones.setdefault(identity, {
                "closure_state": "verified", "phase": "verified", "review_iterations": 0,
                "evidence": [{"phase": "retired_record", "source": "history", "outcome": "completed"}],
                "manual_evidence": [],
            })
            continue
        approved_task_records = milestone["tasks"]
        in_scope_ids = {task["id"] for task in approved_task_records}
        milestone_rows = [row for row in live["rows"] if row["milestone_id"] == identity and row["lifecycle"] == "active"]
        for task_id in in_scope_ids:
            matches = [row for row in milestone_rows if row["task_id"] == task_id or row["label"] == task_id]
            if len(matches) != 1:
                raise _UnresolvedDependency(f"approved task row {identity}/{task_id} is missing or ambiguous")
        in_scope = [row for row in milestone_rows if row["task_id"] in in_scope_ids or row["label"] in in_scope_ids]
        if any(
            row["state"] in {"pending", "in_progress", "blocked"}
            for row in milestone_rows if row not in in_scope
        ):
            raise _UnresolvedDependency(
                f"live milestone {identity} contains actionable rows outside the approved task scope"
            )

        dependency_waiting = False
        for edge in live["milestone_edges"].get(identity, []):
            target = live["milestones"].get(edge["target"])
            if target is None or target["lifecycle"] == "missing":
                raise _UnresolvedDependency(f"unresolved live milestone dependency: {identity} -> {edge['target']}")
            if target["lifecycle"] == "retired" and target["outcome"] == "completed":
                continue
            if edge["target"] not in horizon_ids:
                raise _UnresolvedDependency(
                    f"milestone dependency {edge['target']} is not a completed milestone inside the approved horizon"
                )
            if closure_milestones.get(edge["target"], {}).get("closure_state") != "verified":
                waiting_reasons.append(f"milestone dependency {edge['target']} needs verified closure")
                dependency_waiting = True
                break
        if dependency_waiting:
            continue

        if in_progress and in_progress[0]["task_id"] not in in_scope_ids:
            raise _UnresolvedDependency(
                f"in-progress row {in_progress[0]['milestone_id']}/{in_progress[0]['task_id']} is outside the approved task rows"
            )

        for historical in [row for row in in_scope if row["state"] == "historical"]:
            successor = _successor_for(index, historical, live["rows"])
            if successor["milestone_id"] not in horizon_ids:
                raise _UnresolvedDependency(
                    f"accepted successor {successor['milestone_id']}/{successor['task_id']} is outside the approved horizon"
                )
            if not _row_is_approved(successor, approved_task_ids):
                raise _UnresolvedDependency(
                    f"accepted successor {successor['milestone_id']}/{successor['task_id']} is outside approved task scope"
                )
            ready, reason = _row_ready(index, successor, live, horizon_ids, approved_task_ids)
            if successor["state"] not in {"completed", "in_progress"} and not ready:
                waiting_reasons.append(reason or f"accepted successor {successor['task_id']} is not ready")

        if any(row["state"] == "blocked" for row in in_scope):
            raise _UnresolvedDependency(f"approved milestone {identity} contains a blocked row")
        if in_progress:
            row = in_progress[0]
            ready, reason = _row_ready(index, row, live, horizon_ids, approved_task_ids)
            if not ready:
                raise _UnresolvedDependency(reason or "in-progress row dependency is not ready")
            task = next(task for task in approved_task_records if task["id"] == row["task_id"])
            return {"status": "row", "row": row, "task": task, "milestone": milestone, "live": live, "resumed": True}

        pending = [row for row in in_scope if row["state"] == "pending"]
        for row in pending:
            ready, reason = _row_ready(index, row, live, horizon_ids, approved_task_ids)
            if ready:
                task = next(task for task in approved_task_records if task["id"] == row["task_id"])
                return {"status": "row", "row": row, "task": task, "milestone": milestone, "live": live, "resumed": False}
            # Another earlier dependency may be selected in the same horizon.
            if reason:
                continue
        nonterminal = [row for row in in_scope if row["state"] in {"pending", "in_progress", "blocked"}]
        if nonterminal:
            waiting_reasons.append(f"no dependency-ready task row in {identity}")
            continue
        closure_record = closure_milestones.get(identity, {})
        if closure_record.get("closure_state") != "verified":
            return {"status": "closure", "milestone": milestone, "live": live}
    if waiting_reasons:
        return {"status": "waiting", "reason": "; ".join(dict.fromkeys(waiting_reasons))}
    return {"status": "horizon_complete"}


def _save(store, receipt_path: pathlib.Path, receipt: dict) -> None:
    store.update_atomic(receipt_path, receipt)


def _is_clean_checkpoint(core, repo: pathlib.Path) -> bool:
    try:
        return core.git_clean(repo)
    except Exception:
        # Invalid Git filters/config make the repository state unprovable.
        return False


def snapshot_digest(snapshot: dict) -> str:
    """Hash the row and history projection used by the deterministic gates."""

    payload = {
        "states": [
            [key[0], key[1], key[2], value]
            for key, value in sorted(snapshot.get("states", {}).items())
        ],
        "cells": [
            [key[0], key[1], key[2], value]
            for key, value in sorted(snapshot.get("cells", {}).items())
        ],
        "files": sorted(snapshot.get("files", set())),
        "active": sorted(snapshot.get("active", set())),
        "history_digests": sorted(snapshot.get("history", {}).get("digests", {}).items()),
        "history_entries": sorted(snapshot.get("history", {}).get("entries", {}).items()),
        "history_journal_sha256": hashlib.sha256(
            snapshot.get("history", {}).get("journal", b"")
        ).hexdigest(),
        "history_problems": snapshot.get("history", {}).get("problems", []),
        "specifications": sorted(
            (name, hashlib.sha256(value.encode("utf-8")).hexdigest() if value is not None else None)
            for name, value in snapshot.get("specifications", {}).items()
        ),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _active_operation_uncertain(receipt: dict) -> bool:
    operation = receipt.get("active_operation")
    return isinstance(operation, dict) and operation.get("phase") in {
        "provider_dispatched", "precommit_verified", "commit_attempted",
    }


def _pause(core, store, receipt_path, receipt, reason: str, code: int, *, review=False):
    receipt["state"] = "needs_review" if review else "paused"
    receipt["pause_reason"] = reason[:2000]
    if not review:
        receipt["active_operation"] = None
    _save(store, receipt_path, receipt)
    core.fail(reason, code)


class UsageReservations:
    """Atomically reserve every metered operation before it can be dispatched."""

    def __init__(self, core, store, receipt_path: pathlib.Path, receipt: dict, clock=time.time):
        self.core = core
        self.store = store
        self.path = receipt_path
        self.receipt = receipt
        self.clock = clock

    def _persist(self):
        _save(self.store, self.path, self.receipt)

    def check_time(self):
        try:
            approved = datetime.datetime.strptime(
                self.receipt["approved_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=datetime.timezone.utc)
            approved_epoch = approved.timestamp()
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise _UnresolvedDependency("receipt approval timestamp is invalid") from exc
        if self.clock() - approved_epoch >= self.receipt["limits"]["max_runtime_seconds"]:
            raise LimitPaused("confirmed elapsed-time limit reached")

    def reserve_provider_attempt(self):
        self.check_time()
        self.ensure_provider_capacity()
        usage = self.receipt["usage"]
        usage["provider_attempts_reserved"] += 1
        active = self.receipt.get("active_operation")
        if isinstance(active, dict):
            active["phase"] = "provider_dispatched"
        self._persist()

    def ensure_provider_capacity(self):
        self.check_time()
        usage = self.receipt["usage"]
        if usage["provider_attempts_reserved"] >= self.receipt["limits"]["max_provider_attempts"]:
            raise LimitPaused("confirmed provider-attempt limit reached")

    def reserve_turn(self, row_id: str):
        self.check_time()
        self.ensure_turn_capacity(row_id)
        turns = self.receipt["usage"].setdefault("turns_by_row", {})
        turns[row_id] = turns.get(row_id, 0) + 1
        self._persist()

    def ensure_turn_capacity(self, row_id: str):
        self.check_time()
        turns = self.receipt["usage"].setdefault("turns_by_row", {})
        if turns.get(row_id, 0) >= self.receipt["limits"]["max_turns_per_row"]:
            raise LimitPaused(f"confirmed model-turn limit reached for {row_id}")

    def reserve_row(self, row_id: str):
        self.check_time()
        usage = self.receipt["usage"]
        started = usage.setdefault("rows_started_ids", [])
        if row_id not in started:
            if len(started) >= self.receipt["limits"]["max_rows"]:
                raise LimitPaused("confirmed task-row limit reached")
            started.append(row_id)
            usage["rows_started"] = len(started)
            self._persist()

    def reserve_commit(self):
        self.check_time()
        self.ensure_commit_capacity()
        usage = self.receipt["usage"]
        usage["commits_reserved"] += 1
        self._persist()

    def ensure_commit_capacity(self):
        self.check_time()
        usage = self.receipt["usage"]
        if usage["commits_reserved"] >= self.receipt["limits"]["max_commits"]:
            raise LimitPaused("confirmed total-commit limit reached")


def extend_limit(core, store, receipt_path: pathlib.Path, receipt: dict, name: str, value: int, *, input_fn=input):
    """Extend one reached cap only after a new exact confirmation at a clean checkpoint."""

    if name not in receipt.get("limits", {}):
        raise _UnresolvedDependency(f"unknown receipt limit: {name}")
    if isinstance(value, bool) or not isinstance(value, int) or value <= receipt["limits"][name]:
        raise _UnresolvedDependency("a limit extension must be a strictly higher positive integer")
    if receipt.get("state") != "paused" or receipt.get("active_operation") is not None:
        raise _UnresolvedDependency("limit extension requires a clean paused checkpoint")
    repo = pathlib.Path(receipt["project_path"])
    if not _is_clean_checkpoint(core, repo):
        raise _UnresolvedDependency("limit extension requires a clean project checkpoint")
    current_head = core.git_head(repo)
    expected = receipt.get("commit_ids", [])[-1:] or [receipt.get("baseline_commit")]
    if expected[0] is not None and current_head != expected[0]:
        raise _UnresolvedDependency("project HEAD changed since the last verified receipt checkpoint")
    current_branch = core.git_branch(repo)
    expected_branch = receipt.get("branch") or "(detached)"
    if current_branch != expected_branch:
        raise _UnresolvedDependency("project branch changed since the last verified receipt checkpoint")
    output = (
        f"Extend {name} from {receipt['limits'][name]} to {value}.\n"
        f"Proposal SHA-256: {receipt['proposal_sha256']}\n"
        f"Checkpoint: {expected_branch} at {current_head}\n"
        f"Approved horizon: {', '.join(receipt['horizon_ids'])}\n"
        "Type exactly `confirm` to extend this cap: "
    )
    if input_fn(output) != "confirm":
        return {"status": "unchanged", "limit": name}
    old_value = receipt["limits"][name]
    receipt["limits"][name] = value
    receipt.setdefault("limit_extensions", []).append({
        "limit": name, "old_value": old_value, "new_value": value,
        "proposal_sha256": receipt["proposal_sha256"], "checkpoint_head": current_head,
        "confirmed_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    })
    receipt["state"] = "running"
    receipt["pause_reason"] = None
    _save(store, receipt_path, receipt)
    return {"status": "running", "limit": name, "value": value}


def _git(core, repo: pathlib.Path, args: list[str], *, check=True):
    try:
        result = core.git_local(args, repo)
    except (OSError, subprocess.TimeoutExpired, core.UnsafeGitConfiguration) as exc:
        raise HorizonError(f"hardened host Git call failed ({args[0]}): {exc}") from exc
    if check and result.returncode:
        raise HorizonError(result.stderr.strip() or f"Git {args[0]} exited {result.returncode}")
    return result


def _commit_parents(core, repo: pathlib.Path, commit: str) -> list[str]:
    fields = _git(core, repo, ["rev-list", "--parents", "-n", "1", commit]).stdout.split()
    if not fields or fields[0] != commit:
        raise HorizonError("Git returned malformed host commit lineage")
    return fields[1:]


def _porcelain_paths(raw: str) -> list[str]:
    if not raw:
        return []
    if not raw.endswith("\0"):
        raise HorizonError("Git returned an incomplete worktree path list")
    records = raw[:-1].split("\0")
    paths = []
    for record in records:
        if len(record) < 4 or record[2] != " ":
            raise HorizonError("Git returned a malformed worktree status entry")
        if "R" in record[:2] or "C" in record[:2]:
            raise HorizonError("renames and copies need manual review")
        paths.append(record[3:])
    if len(paths) != len(set(paths)):
        raise HorizonError("Git returned duplicate worktree paths")
    return paths


def _locate_row_marker(path: pathlib.Path, line_number: int) -> tuple[list[str], str, int, int]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not 1 <= line_number <= len(lines):
        raise HorizonError("selected status row moved before its state cell could be located")
    line = lines[line_number - 1]
    escaped = False
    separators = []
    for offset, character in enumerate(line):
        if character == "|" and not escaped:
            separators.append(offset)
        if character == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    if len(separators) < 3:
        raise HorizonError("selected status row has no parseable state cell")
    start, end = separators[1] + 1, separators[2]
    return lines, line, start, end


def _mark_in_progress(core, repo: pathlib.Path, row: dict) -> None:
    """Set only the selected row's state cell before handing work to the model."""

    path = repo / row["path"]
    lines, line, start, end = _locate_row_marker(path, row["line"])
    current = line[start:end].strip()
    if current == "`[~]`":
        return
    if current != "`[ ]`":
        raise HorizonError("selected task row no longer has its approved pending state")
    lines[row["line"] - 1] = line[:start] + " `[~]` " + line[end:]
    path.write_text("".join(lines), encoding="utf-8")


def _release_in_progress_marker(core, repo: pathlib.Path, row: dict) -> bool:
    """Undo the host-written in-progress marker when it is the sole dirty path.

    The marker is written before dispatch so the row is visibly claimed while
    the model works. A pause that happens before the model changed anything of
    its own leaves that marker as the worktree's only difference; reverting it
    restores a genuinely clean checkpoint so the pause resumes normally instead
    of being misread as uncertain model-made work. Any other dirty path means
    real work may already have happened, so this leaves the tree untouched and
    reports failure, and the caller keeps its existing needs_review handling.
    """
    if _changed_paths(core, repo) != [row["path"]]:
        return False
    path = repo / row["path"]
    try:
        lines, line, start, end = _locate_row_marker(path, row["line"])
    except HorizonError:
        return False
    if line[start:end].strip() != "`[~]`":
        return False
    lines[row["line"] - 1] = line[:start] + " `[ ]` " + line[end:]
    path.write_text("".join(lines), encoding="utf-8")
    return _is_clean_checkpoint(core, repo)


def _pause_review_flag(core, repo: pathlib.Path, receipt: dict, row: dict | None = None) -> bool:
    """Return whether a pause needs manual review, healing a solitary marker first."""

    if row is not None and not _is_clean_checkpoint(core, repo):
        _release_in_progress_marker(core, repo, row)
    return not _is_clean_checkpoint(core, repo) or _active_operation_uncertain(receipt)


def _changed_paths(core, repo: pathlib.Path) -> list[str]:
    return _porcelain_paths(_git(core, repo, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"]).stdout)


def _stage_exact(core, repo: pathlib.Path, paths: list[str]) -> list[str]:
    if not paths:
        return []
    _git(core, repo, ["add", "-f", "--", *[f":(top,literal){path}" for path in paths]])
    raw = _git(core, repo, ["diff", "--cached", "--no-renames", "--name-only", "-z", "--"]).stdout
    staged = raw[:-1].split("\0") if raw.endswith("\0") and raw else []
    if sorted(staged) != sorted(paths):
        raise HorizonError(f"staged paths differ from the validated set: {staged}")
    status = _changed_paths(core, repo)
    if sorted(status) != sorted(paths):
        raise HorizonError("staging left an unexpected or unstaged worktree path")
    unstaged = _git(core, repo, ["diff", "--no-renames", "--name-only", "--"]).stdout
    if unstaged:
        raise HorizonError("worktree has unstaged changes after exact-path staging")
    return staged


def _active_operation(receipt: dict, kind: str, *, row_id=None, milestone_id=None, phase=None, paths=None, expected_head=None):
    receipt["active_operation"] = {
        "kind": kind,
        "operation_id": str(uuid.uuid4()),
        "phase": "prepared",
        "expected_head": expected_head,
        "row_id": row_id,
        "closure_phase": phase,
        "paths": list(paths or []),
        "milestone_id": milestone_id,
    }


def _check_model_actions(result: dict) -> list[str]:
    actions = result.get("external_actions", [])
    if not isinstance(actions, list) or any(not isinstance(item, str) or not item.strip() for item in actions):
        raise HorizonError("model external_actions must be an array of nonempty strings")
    return actions


def _run_sandbox_check(core, store, receipt_path, receipt, executor, repo, command, args, row=None):
    try:
        result = executor(
            repo, command, min(args.tool_timeout, 300), args.max_tool_output,
            args.allow_dangerous, args.tool_env,
        )
    except Exception as exc:
        sandbox_error = getattr(executor, "sandbox_unavailable", None)
        if sandbox_error is not None and isinstance(exc, sandbox_error):
            review = _pause_review_flag(core, repo, receipt, row)
            _pause(
                core, store, receipt_path, receipt,
                f"Docker executor became unavailable during verification: {exc}", 17,
                review=review,
            )
        raise
    if result.get("exit_code") == 127:
        detail = result.get("stderr", "").strip()
        review = _pause_review_flag(core, repo, receipt, row)
        _pause(
            core, store, receipt_path, receipt,
            "A required verification dependency is missing from the Docker image. The "
            "approved image ID is fixed by this receipt and resume will not pick up a "
            "rebuilt image; fixing it requires a new proposal that approves the updated "
            "image ID."
            + (f"\n{detail}" if detail else ""),
            25 if review else 17, review=review,
        )
    return result


def _record_committed(receipt: dict, commit: str, *, keep_operation=False):
    receipt.setdefault("commit_ids", []).append(commit)
    receipt["usage"]["commits_recorded"] += 1
    if not keep_operation:
        receipt["active_operation"] = None
    receipt["pause_reason"] = None
    receipt["state"] = "running"


def _map_gate_to_controller(core, store, path, receipt, gate: dict):
    reason = f"Post-commit gate {gate.get('gate')} failed: " + "; ".join(gate.get("row_problems", []))
    _pause(core, store, path, receipt, reason, 25, review=True)


def _row_prompt(selection: dict) -> str:
    task = selection["task"]
    row = selection["row"]
    return (
        f"Execute approved task {row['milestone_id']}/{row['task_id']} in "
        f"tabilet/memory-bank/{row['file']}:{row['line']}.\n"
        f"Milestone: {selection['milestone']['title']}\n"
        f"Task description: {task['description']}\nAcceptance: {task['acceptance']}\n"
        f"Required checks: {json.dumps(task['verification'], ensure_ascii=False)}\n"
        f"Only change these paths: {json.dumps(task['approved_paths'], ensure_ascii=False)}\n"
        "Read AGENTS.md and the live milestone/status files first. Change this selected row from `[~]` to a terminal marker only when the work and checks are complete. Do not run Git commands. Report external_actions as a JSON array in your final object; no external action is authorized. Return final JSON with a concise summary."
    )


def _args_for_turn_cap(args, already_used: int, remaining: int):
    import copy
    clone = copy.copy(args)
    clone.max_turns = already_used + remaining
    clone.controller_turn_offset = already_used
    return clone


def _progress_summary(receipt: dict, row_id: str) -> str:
    usage, limits = receipt.get("usage", {}), receipt.get("limits", {})
    attempts = usage.get("provider_attempts_reserved", 0)
    attempts_cap = limits.get("max_provider_attempts", 0)
    turns = usage.get("turns_by_row", {}).get(row_id, 0)
    turn_cap = limits.get("max_turns_per_row", 0)
    rows = usage.get("rows_started", 0)
    rows_cap = limits.get("max_rows", 0)
    commits = usage.get("commits_reserved", 0)
    commits_cap = limits.get("max_commits", 0)
    try:
        approved = datetime.datetime.strptime(
            receipt["approved_at"], "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=datetime.timezone.utc).timestamp()
        seconds_left = max(0, int(limits["max_runtime_seconds"] - (time.time() - approved)))
    except (KeyError, TypeError, ValueError, OverflowError):
        seconds_left = 0
    return (
        f"provider attempts {attempts}/{attempts_cap} ({max(0, attempts_cap - attempts)} remaining); "
        f"model turns {turns}/{turn_cap} ({max(0, turn_cap - turns)} remaining); "
        f"rows {rows}/{rows_cap} ({max(0, rows_cap - rows)} remaining); "
        f"commits {commits}/{commits_cap} ({max(0, commits_cap - commits)} remaining); "
        f"time {seconds_left}s remaining"
    )


def _run_agent(core, controller, args, repo, receipt, reservations, executor, user_message, row_id, output_fn=print):
    turns = receipt["usage"].get("turns_by_row", {}).get(row_id, 0)
    left = receipt["limits"]["max_turns_per_row"] - turns
    if left <= 0:
        raise LimitPaused(f"confirmed model-turn limit reached for {row_id}")
    before_turn = lambda: reservations.reserve_turn(row_id)
    before_attempt = reservations.reserve_provider_attempt
    before_command = reservations.check_time
    def after_command(command, result):
        stdout = str(result.get("stdout", "")).strip().splitlines()
        stderr = str(result.get("stderr", "")).strip().splitlines()
        summary = (stdout or stderr or ["no output"])[0].replace("\n", " ")[:240]
        output_fn(f"  command result: exit {result.get('exit_code')}; {summary}")
    return controller.run_controller_agent(
        core, _args_for_turn_cap(args, turns, left), repo, turns + 1, [], None, executor,
        user_message, before_model_turn=before_turn,
        before_provider_attempt=before_attempt, before_command=before_command,
        after_command=after_command,
    )


def _run_task(core, controller, args, repo, store, receipt_path, receipt, executor, selection, reservations, output_fn=print):
    row, task = selection["row"], selection["task"]
    row_id = f"{row['milestone_id']}/{row['task_id']}"
    if not _is_clean_checkpoint(core, repo):
        _pause(core, store, receipt_path, receipt, "dirty worktree before task dispatch", 25, review=True)
    reservations.ensure_turn_capacity(row_id)
    reservations.ensure_provider_capacity()
    reservations.ensure_commit_capacity()
    reservations.reserve_row(row_id)
    _validate_project_files(repo, task["approved_paths"])
    head = core.git_head(repo)
    branch = core.git_branch(repo)
    expected_head = (receipt.get("commit_ids") or [receipt.get("planning_commit")])[-1]
    expected_branch = receipt.get("branch") or "(detached)"
    if head != expected_head or branch != expected_branch:
        _pause(core, store, receipt_path, receipt, "project HEAD or branch changed since the last receipt checkpoint", 25, review=True)
    _active_operation(
        receipt, "task", row_id=row_id,
        paths=task["approved_paths"], expected_head=head,
    )
    receipt["active_operation"]["milestone_id"] = row["milestone_id"]
    receipt["active_operation"]["task_id"] = row["task_id"]
    receipt["active_operation"]["row_key"] = list(row["key"])
    receipt["active_operation"]["verification"] = list(task["verification"])
    _save(store, receipt_path, receipt)
    try:
        _mark_in_progress(core, repo, row)
        before_rows = core.row_snapshot(repo)
        receipt["active_operation"]["before_snapshot_sha256"] = snapshot_digest(before_rows)
        _save(store, receipt_path, receipt)
        output_fn(
            f"Current row {row_id}; {_progress_summary(receipt, row_id)}."
        )
        result = _run_agent(core, controller, args, repo, receipt, reservations, executor, _row_prompt(selection), row_id, output_fn)
        # The model turn concluded normally; nothing is in flight anymore.
        # Reset the phase so a pause during the post-turn checks below
        # (verification, staging) is classified by the actual worktree state
        # via _is_clean_checkpoint, not by a stale "provider_dispatched"
        # marker that reserve_provider_attempt set for the last model call
        # and nothing had advanced past since.
        receipt["active_operation"]["phase"] = "turn_completed"
        external = _check_model_actions(result)
        if external:
            receipt["external_actions"] = list(dict.fromkeys(receipt.get("external_actions", []) + external))
            dirty = _pause_review_flag(core, repo, receipt, row)
            _pause(
                core, store, receipt_path, receipt,
                "external action requires separate handling: " + "; ".join(external), 17,
                review=dirty,
            )
        if core.git_head(repo) != head or core.git_branch(repo) != branch:
            _pause(core, store, receipt_path, receipt, "project HEAD or branch changed during task execution", 25, review=True)

        check_results = {}
        check_evidence = []
        for command in task["verification"]:
            reservations.check_time()
            outcome = _run_sandbox_check(core, store, receipt_path, receipt, executor, repo, command, args, row=row)
            check_results[command] = outcome.get("exit_code") == 0
            check_evidence.append({
                "row_id": row_id, "command": command,
                "exit_code": outcome.get("exit_code"),
                "stdout": outcome.get("stdout", "")[:4000],
                "stderr": outcome.get("stderr", "")[:2000],
            })

        after_rows = core.row_snapshot(repo)
        changed = _changed_paths(core, repo)
        unsafe_path_problem = None
        try:
            _validate_project_files(repo, changed)
        except HorizonError as exc:
            unsafe_path_problem = str(exc)
        allowed = set(task["approved_paths"])
        problems = controller.precommit_problems(
            core, before_rows, after_rows, row["key"], allowed, changed,
            task["verification"], check_results,
        )
        if unsafe_path_problem:
            problems.append(unsafe_path_problem)
        # A task cannot silently enlarge the approved task table by adding rows.
        before_keys = set(before_rows["states"])
        new_keys = set(after_rows["states"]) - before_keys
        if new_keys:
            problems.append("task added status rows outside the fixed approved horizon")
        if problems:
            receipt.setdefault("verification_evidence", []).extend(check_evidence)
            _save(store, receipt_path, receipt)
            _pause(
                core, store, receipt_path, receipt,
                "Controller pre-commit validation failed; no host task commit was made:\n  " + "\n  ".join(problems),
                24, review=True,
            )
        receipt.setdefault("verification_evidence", []).extend(check_evidence)
        receipt["active_operation"]["expected_snapshot_sha256"] = snapshot_digest(after_rows)
        receipt["active_operation"]["verification_results"] = {
            command: check_results.get(command) is True for command in task["verification"]
        }
        staged = _stage_exact(core, repo, changed)
        if core.git_head(repo) != head or core.git_branch(repo) != branch:
            _pause(core, store, receipt_path, receipt, "project HEAD or branch changed before the task commit", 25, review=True)
        reservations.reserve_commit()
        _active_operation(
            receipt, "task_commit", row_id=row_id, paths=staged,
            expected_head=head,
        )
        receipt["active_operation"].update({
            "milestone_id": row["milestone_id"],
            "task_id": row["task_id"],
            "row_key": list(row["key"]),
            "verification": list(task["verification"]),
            "verification_results": {command: check_results.get(command) is True for command in task["verification"]},
            "expected_snapshot_sha256": snapshot_digest(after_rows),
        })
        receipt["active_operation"]["phase"] = "precommit_verified"
        _save(store, receipt_path, receipt)
        if core.git_head(repo) != head or core.git_branch(repo) != branch:
            _pause(core, store, receipt_path, receipt, "project HEAD or branch changed before the task commit", 25, review=True)
        message = f"Complete {row['milestone_id']}/{row['task_id']}"

        staged_patch = _git(core, repo, ["diff", "--cached", "--no-renames", "--binary", "--"]).stdout

        def mark_commit_attempted(candidate: str, tree: str):
            receipt["active_operation"].update({
                "phase": "commit_attempted",
                "candidate_commit": candidate,
                "expected_tree": tree,
                "expected_patch_sha256": hashlib.sha256(staged_patch.encode("utf-8", errors="surrogateescape")).hexdigest(),
                "commit_message": message,
            })
            _save(store, receipt_path, receipt)

        try:
            commit_id = controller.commit_host_changes(
                core, repo, head, branch, staged_patch, message,
                before_ref_update=mark_commit_attempted,
            )
        except Exception as exc:
            _pause(
                core, store, receipt_path, receipt,
                "task changes are staged but the expected-ref host commit failed: " + str(exc),
                25, review=True,
            )
        after_commit_rows = core.row_snapshot(repo)
        gate = core.post_run_gates(
            repo, head, branch, before_rows, after_commit_rows, row["key"],
        )
        if gate["exit_code"]:
            _map_gate_to_controller(core, store, receipt_path, receipt, gate)
        if gate["after"] != commit_id:
            _pause(core, store, receipt_path, receipt, "another commit advanced HEAD before receipt checkpoint", 25, review=True)
        if _commit_parents(core, repo, gate["after"]) != [head]:
            _pause(core, store, receipt_path, receipt, "task commit has an unexpected parent; manual recovery is required", 25, review=True)
        _record_committed(receipt, gate["after"])
        _save(store, receipt_path, receipt)
        return {"status": "committed", "row": row_id, "commit": gate["after"], "checks": check_results}
    except LimitPaused:
        # No replay is safe if the model already made any project changes.
        review = _pause_review_flag(core, repo, receipt, row)
        receipt["active_operation"] = None if not review else receipt.get("active_operation")
        receipt["state"] = "needs_review" if review else "paused"
        receipt["pause_reason"] = "confirmed execution limit reached"
        _save(store, receipt_path, receipt)
        raise
    except SystemExit as exc:
        if receipt.get("state") == "running" and receipt.get("active_operation") is not None:
            uncertain = _pause_review_flag(core, repo, receipt, row)
            receipt["state"] = "needs_review" if uncertain else "paused"
            receipt["pause_reason"] = f"controller stopped with exit {exc.code} during an active operation"
            if not uncertain:
                receipt["active_operation"] = None
            _save(store, receipt_path, receipt)
            if uncertain and exc.code != 25:
                core.fail(receipt["pause_reason"], 25)
        raise
    except Exception as exc:
        review = True
        _pause(
            core, store, receipt_path, receipt,
            f"task execution stopped: {exc}", 25, review=review,
        )


def _closure_prompt(milestone: dict, phase: str, prior: dict) -> str:
    phase_instructions = {
        "review": "Review the complete milestone against its acceptance criteria. Fix P0/P1/P2 findings within approved closure paths, then report all findings and severity.",
        "acceptance": "Verify every milestone acceptance criterion against observed evidence. Run the declared verification commands and report each criterion and result.",
        "consolidation": "Consolidate verified facts and lessons in the approved closure paths. Preserve history and current product/architecture boundaries.",
        "downstream": "Reconcile downstream milestone dependencies and task references within approved closure paths. Preserve permanent IDs and completed history.",
        "retirement": "Retire this completed milestone only if project policy explicitly adopted retirement. Preserve the full specification and status record.",
    }
    return (
        f"Run API 6 closure phase {phase} for {milestone['id']} ({milestone['title']}).\n"
        f"Milestone acceptance: {json.dumps(milestone['acceptance'], ensure_ascii=False)}\n"
        f"Allowed paths: {json.dumps(milestone['closure_paths'], ensure_ascii=False)}\n"
        f"Prior phase evidence: {json.dumps(prior, ensure_ascii=False)}\n"
        f"Instructions: {phase_instructions[phase]}\n"
        "Do not run Git commands or external actions. When finished, return exactly one "
        "JSON object with six top-level fields: `final` (a short string summary, "
        "required so the turn ends), `verified` (boolean), `evidence` (array of observed "
        "facts), `findings` (array of objects with `severity` and `finding`), and "
        "`external_actions` (array), plus `manual_evidence_verified` (boolean). All six "
        "fields are siblings in the same object, not nested inside `final`. Set "
        "`manual_evidence_verified` to true only during acceptance when the supplied "
        "user evidence was actually checked; otherwise set it to false. Label all review "
        "evidence as model evidence."
    )


_REVIEW_GATE_LINE = re.compile(r"^\*\*Review gate\.\*\* (active|passed)$")
_REVIEW_ITERATIONS_LINE = re.compile(r"^\*\*Review iterations\.\*\* ([0-9]+)$")
_REVIEW_FINDINGS_LINE = re.compile(r"^\*\*Review findings\.\*\* (.+)$")


def _review_checkpoint(repo: pathlib.Path, milestone_id: str) -> dict | None:
    """Read the portable active review-gate checkpoint from its status file."""

    path = repo / "tabilet" / "memory-bank" / f"status-{milestone_id}.md"
    text = path.read_text(encoding="utf-8")
    fields = {"gate": [], "iterations": [], "findings": []}
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        for name, pattern in (
            ("gate", _REVIEW_GATE_LINE),
            ("iterations", _REVIEW_ITERATIONS_LINE),
            ("findings", _REVIEW_FINDINGS_LINE),
        ):
            match = pattern.fullmatch(line.strip())
            if match:
                fields[name].append(match.group(1))
    present = any(fields.values())
    if not present:
        return None
    if any(len(values) != 1 for values in fields.values()):
        raise HorizonError(f"status-{milestone_id}.md has an incomplete or duplicate review checkpoint")
    gate, raw_iterations, raw_findings = (
        fields["gate"][0], fields["iterations"][0], fields["findings"][0]
    )
    iterations = int(raw_iterations)
    if not 1 <= iterations <= 10:
        raise HorizonError(f"status-{milestone_id}.md has an out-of-range review iteration count")
    try:
        findings = json.loads(raw_findings)
    except json.JSONDecodeError as exc:
        raise HorizonError(f"status-{milestone_id}.md has malformed review findings") from exc
    if not isinstance(findings, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("severity"), str)
        or not isinstance(item.get("finding"), str)
        for item in findings
    ):
        raise HorizonError(f"status-{milestone_id}.md has malformed review findings")
    return {"gate": gate, "iterations": iterations, "findings": findings}


def _receipt_review_checkpoint(core, store, repo: pathlib.Path, milestone_id: str, receipt: dict) -> dict | None:
    """Find a clean paused receipt's in-flight review iteration for a new receipt."""

    directory_value = getattr(store, "directory", None)
    if not directory_value:
        return None
    directory = pathlib.Path(directory_value)
    if not directory.is_dir() or directory.is_symlink():
        return None
    project_path = str(repo.resolve(strict=True))
    current_head = (receipt.get("commit_ids") or [receipt.get("planning_commit")])[-1]
    current_branch = receipt.get("branch") or "(detached)"
    candidates = []
    for path in directory.glob("*.json"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            prior = store.load(path)
        except Exception:
            continue
        if (
            prior.get("project_path") != project_path
            or prior.get("branch", "(detached)") != current_branch
            or prior.get("state") not in {"paused", "running"}
        ):
            continue
        prior_head = (prior.get("commit_ids") or [prior.get("planning_commit")])[-1]
        if not isinstance(prior_head, str) or not isinstance(current_head, str):
            continue
        try:
            if not core.git_is_ancestor(repo, prior_head, current_head):
                continue
        except Exception:
            continue
        closure = prior.get("closure", {}).get("milestones", {}).get(milestone_id, {})
        iterations = closure.get("review_iterations")
        if (
            closure.get("closure_state") == "pending"
            and closure.get("phase") == "review"
            and isinstance(iterations, int)
            and not isinstance(iterations, bool)
            and 0 <= iterations <= 10
        ):
            started = closure.get("review_iteration_started") is True and prior.get("active_operation") is None
            findings = closure.get("review_findings", [])
            if not isinstance(findings, list):
                findings = []
            candidates.append((iterations, started, prior.get("approved_at", ""), findings))
    if not candidates:
        return None
    maximum = max(item[0] for item in candidates)
    latest = [item for item in candidates if item[0] == maximum]
    latest_receipt = max(latest, key=lambda item: item[2])
    return {
        "iterations": maximum,
        "iteration_started": any(item[1] for item in latest),
        "approved_at": latest_receipt[2],
        "findings": latest_receipt[3],
    }


def _write_review_checkpoint(repo: pathlib.Path, milestone_id: str, gate: str, iterations: int, findings: list[dict]) -> None:
    """Persist the bounded review gate for both controller and direct-agent sessions."""

    if gate not in {"active", "passed"} or not 1 <= iterations <= 10:
        raise HorizonError("invalid review checkpoint state")
    path = repo / "tabilet" / "memory-bank" / f"status-{milestone_id}.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    replacements = {
        "gate": f"**Review gate.** {gate}",
        "iterations": f"**Review iterations.** {iterations}",
        "findings": "**Review findings.** " + json.dumps(findings, ensure_ascii=False, separators=(",", ":")),
    }
    patterns = {
        "gate": _REVIEW_GATE_LINE,
        "iterations": _REVIEW_ITERATIONS_LINE,
        "findings": _REVIEW_FINDINGS_LINE,
    }
    matches = {name: [] for name in replacements}
    fenced = False
    for index, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        for name, pattern in patterns.items():
            if pattern.fullmatch(line.rstrip("\r\n").strip()):
                matches[name].append(index)
    if any(len(indices) > 1 for indices in matches.values()):
        raise HorizonError(f"status-{milestone_id}.md has duplicate review checkpoint fields")
    present = [bool(indices) for indices in matches.values()]
    if any(present) and not all(present):
        raise HorizonError(f"status-{milestone_id}.md has an incomplete review checkpoint")
    if not any(present):
        insert_at = 1 if lines and lines[0].startswith("#") else 0
        ending = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
        lines[insert_at:insert_at] = [replacement + ending for replacement in replacements.values()]
    else:
        for name, replacement in replacements.items():
            index = matches[name][0]
            ending = "\r\n" if lines[index].endswith("\r\n") else "\n" if lines[index].endswith("\n") else ""
            lines[index] = replacement + ending
    path.write_text("".join(lines), encoding="utf-8")


def _closure_integrity_problems(
    before: dict, after: dict, *, retirement_id: str | None = None,
    review_iterations: int | None = None,
) -> list[str]:
    problems = list(after.get("history", {}).get("problems", []))
    old_history = before.get("history", {})
    new_history = after.get("history", {})
    for name, digest in old_history.get("digests", {}).items():
        if new_history.get("digests", {}).get(name) != digest:
            problems.append(f"previously retired record changed during closure: {name}")
    for name, entry in old_history.get("entries", {}).items():
        if new_history.get("entries", {}).get(name) != entry:
            problems.append(f"previous history index entry changed during closure: {name}")
    if not new_history.get("journal", b"").startswith(old_history.get("journal", b"")):
        problems.append("retired knowledge history was rewritten during closure")
    newly_retired = set(new_history.get("records", {})) - set(old_history.get("records", {}))
    if retirement_id is None:
        if newly_retired:
            problems.append("milestone retirement is only allowed in its adopted retirement phase")
    else:
        expected_name = f"status-{retirement_id}.md"
        if newly_retired != {expected_name}:
            problems.append(
                f"retirement phase must create exactly {expected_name}; found {sorted(newly_retired)}"
            )
        if expected_name not in before.get("active", set()) or expected_name in after.get("active", set()):
            problems.append(f"retirement phase did not move active {expected_name} into history")
        record = new_history.get("records", {}).get(expected_name)
        if record is not None:
            if record.get("status") != before.get("documents", {}).get(expected_name):
                problems.append(f"retirement changed the complete status source: {expected_name}")
            original_spec = before.get("specifications", {}).get(expected_name)
            if not original_spec or record.get("specification") != original_spec:
                problems.append(f"retirement changed or discarded the complete specification: {expected_name}")
            metadata = record.get("metadata", {})
            if metadata.get("Outcome") != "completed":
                problems.append(f"retirement outcome is not completed: {expected_name}")
            if review_iterations is None or metadata.get("Review iterations") != str(review_iterations):
                problems.append(f"retirement review count does not match the verified closure: {expected_name}")
        removed_active = before.get("active", set()) - after.get("active", set())
        if removed_active != {expected_name}:
            problems.append(f"retirement removed active status files outside its milestone: {sorted(removed_active)}")
    for key, state in before["states"].items():
        if key not in after["states"]:
            problems.append(f"closure removed status row {key[0]} / {key[1]!r}")
        elif after["states"].get(key) != state:
            problems.append(f"closure changed task state {key[0]} / {key[1]!r}")
        elif before.get("cells", {}).get(key) != after.get("cells", {}).get(key):
            problems.append(f"closure changed existing task notes {key[0]} / {key[1]!r}")
    for key, state in after["states"].items():
        if key not in before["states"]:
            problems.append(f"closure added an unapproved task row {key[0]} / {key[1]!r}")
    new_status_files = set(after["files"]) - set(before["files"])
    if new_status_files:
        problems.append("closure added status files outside the approved horizon: " + ", ".join(sorted(new_status_files)))
    if not set(before["files"]).issubset(after["files"]):
        problems.append("closure removed a status file")
    return problems


def _retirement_prerequisite_problems(closure: dict) -> list[str]:
    """Require persisted successful closure phases before retirement begins."""

    evidence = closure.get("evidence", [])
    if not isinstance(evidence, list):
        return ["closure evidence is malformed before retirement"]
    problems = []
    for phase in ("acceptance", "consolidation", "downstream"):
        if not any(
            item.get("phase") == phase and item.get("source") == "model"
            for item in evidence if isinstance(item, dict)
        ):
            problems.append(f"retirement requires a persisted verified {phase} phase")
    reviews = [
        item for item in evidence
        if isinstance(item, dict) and item.get("phase") == "review" and item.get("source") == "model"
    ]
    if not reviews:
        problems.append("retirement requires a persisted clean milestone review")
    else:
        findings = reviews[-1].get("findings", [])
        if not isinstance(findings, list) or any(
            isinstance(finding, dict)
            and str(finding.get("severity", "")).upper() in {"P0", "P1", "P2"}
            for finding in findings
        ):
            problems.append("retirement requires a clean review with no P0/P1/P2 findings")
    iterations = closure.get("review_iterations")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 1 <= iterations <= 10:
        problems.append("retirement requires a persisted review count from 1 through 10")
    return problems


def _commit_closure_changes(core, controller, store, receipt_path, receipt, repo, milestone, phase, before, allowed, reservations, expected_head, expected_branch, phase_result=None):
    if core.git_head(repo) != expected_head or core.git_branch(repo) != expected_branch:
        _pause(core, store, receipt_path, receipt, "project HEAD or branch changed during closure", 25, review=True)
    changed = _changed_paths(core, repo)
    problems = [f"changed path is outside approved closure scope: {p}" for p in sorted(set(changed) - set(allowed))]
    try:
        _validate_project_files(repo, changed)
    except HorizonError as exc:
        problems.append(str(exc))
    after = core.row_snapshot(repo)
    retirement_id = milestone["id"] if phase == "retirement" else None
    review_iterations = receipt.get("closure", {}).get("milestones", {}).get(milestone["id"], {}).get("review_iterations")
    problems.extend(_closure_integrity_problems(
        before, after, retirement_id=retirement_id,
        review_iterations=review_iterations,
    ))
    if problems:
        _pause(core, store, receipt_path, receipt, "Closure pre-commit validation failed: " + "; ".join(problems), 24, review=True)
    if not changed:
        return None
    staged = _stage_exact(core, repo, changed)
    if core.git_head(repo) != expected_head or core.git_branch(repo) != expected_branch:
        _pause(core, store, receipt_path, receipt, "project HEAD or branch changed before the closure commit", 25, review=True)
    reservations.reserve_commit()
    head = expected_head
    branch = expected_branch
    operation_id = receipt.get("active_operation", {}).get("operation_id")
    _active_operation(
        receipt, "closure_commit", milestone_id=milestone["id"], phase=phase,
        paths=staged, expected_head=head,
    )
    if operation_id:
        receipt["active_operation"]["operation_id"] = operation_id
    receipt["active_operation"]["before_snapshot_sha256"] = snapshot_digest(before)
    receipt["active_operation"]["expected_snapshot_sha256"] = snapshot_digest(after)
    receipt["active_operation"]["phase_result"] = phase_result
    receipt["active_operation"]["phase"] = "precommit_verified"
    _save(store, receipt_path, receipt)
    if core.git_head(repo) != expected_head or core.git_branch(repo) != expected_branch:
        _pause(core, store, receipt_path, receipt, "project HEAD or branch changed before the closure commit", 25, review=True)
    message = f"{phase.title()} closure for {milestone['id']}"
    staged_patch = _git(core, repo, ["diff", "--cached", "--no-renames", "--binary", "--"]).stdout

    def mark_commit_attempted(candidate: str, tree: str):
        receipt["active_operation"].update({
            "phase": "commit_attempted",
            "candidate_commit": candidate,
            "expected_tree": tree,
            "expected_patch_sha256": hashlib.sha256(staged_patch.encode("utf-8", errors="surrogateescape")).hexdigest(),
            "commit_message": message,
        })
        _save(store, receipt_path, receipt)

    try:
        commit_id = controller.commit_host_changes(
            core, repo, head, branch, staged_patch, message,
            before_ref_update=mark_commit_attempted,
        )
    except Exception as exc:
        _pause(core, store, receipt_path, receipt, "closure changes are staged but the expected-ref host commit failed: " + str(exc), 25, review=True)
    new_head = core.git_head(repo)
    if (
        not _is_clean_checkpoint(core, repo) or new_head != commit_id
        or core.git_branch(repo) != branch
        or not core.git_is_ancestor(repo, head, new_head)
    ):
        _pause(core, store, receipt_path, receipt, "closure commit did not leave a verified clean checkpoint", 25, review=True)
    if _commit_parents(core, repo, new_head) != [expected_head]:
        _pause(core, store, receipt_path, receipt, "closure commit has an unexpected parent; manual recovery is required", 25, review=True)
    after_commit = core.row_snapshot(repo)
    integrity = _closure_integrity_problems(
        before, after_commit, retirement_id=retirement_id,
        review_iterations=review_iterations,
    )
    if integrity:
        _pause(core, store, receipt_path, receipt, "closure post-commit validation failed: " + "; ".join(integrity), 25, review=True)
    commit_id = new_head
    _record_committed(receipt, commit_id, keep_operation=True)
    _save(store, receipt_path, receipt)
    return commit_id


def _closure_phase_result(receipt, closure, phase, result, *, retry_review=False):
    return {
        "phase": phase,
        "operation_id": receipt["active_operation"]["operation_id"],
        "verified": True,
        "manual_evidence_verified": result.get("manual_evidence_verified") is True,
        "iteration": closure.get("review_iterations") if phase == "review" else None,
        "items": list(result.get("evidence", [])),
        "findings": list(result.get("findings", [])),
        "retry_review": bool(retry_review),
    }


def _finish_closure_phase(receipt, milestone, phase_result, commit_id=None):
    identity = milestone["id"]
    closure = receipt["closure"]["milestones"][identity]
    op_id = phase_result["operation_id"]
    evidence = closure.setdefault("evidence", [])
    existing = next((item for item in evidence if isinstance(item, dict) and item.get("operation_id") == op_id), None)
    if existing is None:
        item = {
            "phase": phase_result["phase"],
            "source": "model",
            "operation_id": op_id,
            "iteration": phase_result.get("iteration"),
            "items": phase_result["items"],
            "findings": phase_result["findings"],
        }
        if commit_id is not None:
            item["commit"] = commit_id
        evidence.append(item)
    phase = phase_result["phase"]
    phases = ["review", "acceptance", "consolidation", "downstream"]
    if milestone.get("retirement_adopted") is True:
        phases.append("retirement")
    if phase_result.get("retry_review"):
        closure["phase"] = "review"
    else:
        index = phases.index(phase)
        closure["phase"] = phases[index + 1] if index + 1 < len(phases) else "verified"
    if closure["phase"] == "verified":
        closure["closure_state"] = "verified"


def _close_milestone(core, controller, args, repo, store, receipt_path, receipt, executor, milestone, reservations, manual_evidence, output_fn=print):
    identity = milestone["id"]
    closure = receipt.setdefault("closure", {}).setdefault("milestones", {}).setdefault(identity, {
        "closure_state": "pending", "phase": "review", "review_iterations": 0,
        "evidence": [], "manual_evidence": [],
    })
    persisted_review = _review_checkpoint(repo, identity)
    prior_receipt_review = _receipt_review_checkpoint(core, store, repo, identity, receipt)
    if (
        persisted_review is not None
        and persisted_review["gate"] == "active"
        and closure.get("phase") == "review"
    ):
        closure["review_iterations"] = max(
            closure.get("review_iterations", 0), persisted_review["iterations"],
        )
        closure["review_findings"] = persisted_review["findings"]
    if prior_receipt_review is not None and closure.get("phase") == "review":
        if prior_receipt_review["iterations"] > closure.get("review_iterations", 0):
            closure["review_iterations"] = prior_receipt_review["iterations"]
            closure["review_iteration_started"] = prior_receipt_review["iteration_started"]
            closure["review_findings"] = prior_receipt_review["findings"]
        elif (
            prior_receipt_review["iterations"] == closure.get("review_iterations")
            and prior_receipt_review["iteration_started"]
        ):
            closure["review_iteration_started"] = True
            closure.setdefault("review_findings", prior_receipt_review["findings"])
    if milestone.get("manual_evidence"):
        provided = (manual_evidence or {}).get(identity, {})
        if not isinstance(provided, dict):
            provided = {}
        missing = [
            item for item in milestone["manual_evidence"]
            if not isinstance(provided.get(item), str) or not provided[item].strip()
        ]
        if missing:
            receipt["state"] = "paused"
            receipt["pause_reason"] = "required manual evidence not supplied: " + "; ".join(missing)
            _save(store, receipt_path, receipt)
            core.fail(receipt["pause_reason"], 17)
        closure["manual_evidence"] = [
            {"criterion": item, "source": "user", "value": provided[item]}
            for item in milestone["manual_evidence"]
        ]
    phases = ["review", "acceptance", "consolidation", "downstream"]
    if milestone.get("retirement_adopted") is True:
        phases.append("retirement")
    if closure.get("closure_state") != "pending" or closure.get("phase") not in phases:
        _pause(
            core, store, receipt_path, receipt,
            f"closure checkpoint for {identity} is not a resumable phase", 25, review=True,
        )
    while closure.get("phase") in phases:
        phase = closure["phase"]
        if phase == "retirement":
            prerequisites = _retirement_prerequisite_problems(closure)
            if prerequisites:
                _pause(
                    core, store, receipt_path, receipt,
                    "Retirement prerequisites failed: " + "; ".join(prerequisites),
                    25, review=True,
                )
        if phase == "review" and closure["review_iterations"] >= 10 and not closure.get("review_iteration_started"):
            _pause(core, store, receipt_path, receipt, "bounded review gate exceeded 10 persisted iterations", 25, review=True)
        if not _is_clean_checkpoint(core, repo):
            _pause(core, store, receipt_path, receipt, "dirty worktree before closure phase", 25, review=True)
        _validate_project_files(repo, milestone["closure_paths"])
        before = core.row_snapshot(repo)
        head = core.git_head(repo)
        branch = core.git_branch(repo)
        # Scope the turn budget to this specific phase, not the whole
        # milestone: review alone can spend up to 10 iterations of its own
        # budget on P0-P2 fixes, and without a per-phase key it would starve
        # the later acceptance/consolidation/downstream/retirement phases of
        # turns before they even start.
        phase_row = f"closure:{identity}:{phase}"
        # A review may make closure-path edits that need a host commit. Pause
        # at this clean checkpoint when the cap is already full, so a new
        # confirmation can extend it before any mutation-capable dispatch.
        reservations.ensure_commit_capacity()
        reservations.ensure_turn_capacity(phase_row)
        reservations.ensure_provider_capacity()
        if phase == "review" and not closure.get("review_iteration_started"):
            closure["review_iterations"] += 1
            closure["review_iteration_started"] = True
        # The private receipt checkpoint (including review_iteration_started)
        # is saved below before provider dispatch. Once the pass returns, its
        # durable status-file form is committed with the review result so
        # direct-agent sessions can continue the same bounded gate.
        _active_operation(receipt, "closure", milestone_id=identity, phase=phase, paths=milestone["closure_paths"], expected_head=head)
        receipt["active_operation"]["before_snapshot_sha256"] = snapshot_digest(before)
        output_fn(
            f"Current closure phase {identity}/{phase}; {_progress_summary(receipt, phase_row)}."
        )
        _save(store, receipt_path, receipt)
        try:
            result = _run_agent(
                core, controller, args, repo, receipt, reservations, executor,
                _closure_prompt(milestone, phase, closure), phase_row, output_fn,
            )
            # See the matching comment in _run_task: nothing is in flight once
            # the model turn concludes normally, so a later pause should be
            # classified by the live worktree state, not a stale dispatch marker.
            receipt["active_operation"]["phase"] = "turn_completed"
            external = _check_model_actions(result)
            if external:
                receipt["external_actions"] = list(dict.fromkeys(receipt.get("external_actions", []) + external))
                review = not _is_clean_checkpoint(core, repo) or _active_operation_uncertain(receipt)
                _pause(core, store, receipt_path, receipt, "external action requires separate handling: " + "; ".join(external), 25 if review else 17, review=review)
            if not isinstance(result.get("verified"), bool) or not isinstance(result.get("evidence"), list):
                _pause(core, store, receipt_path, receipt, f"closure phase {phase} returned malformed evidence", 24, review=True)
            if not isinstance(result.get("manual_evidence_verified"), bool):
                _pause(core, store, receipt_path, receipt, f"closure phase {phase} returned malformed manual-evidence state", 24, review=True)
            if any(not isinstance(item, str) or not item.strip() for item in result["evidence"]):
                _pause(core, store, receipt_path, receipt, f"closure phase {phase} evidence must be nonempty strings", 24, review=True)
            findings = result.get("findings", [])
            if not isinstance(findings, list):
                _pause(core, store, receipt_path, receipt, "closure findings must be an array", 24, review=True)
            if any(
                not isinstance(finding, dict)
                or not isinstance(finding.get("severity"), str)
                or not re.fullmatch(r"P[0-3]", finding["severity"].upper())
                or not isinstance(finding.get("finding"), str)
                or not finding["finding"].strip()
                for finding in findings
            ):
                _pause(core, store, receipt_path, receipt, "closure findings need a severity and finding description", 24, review=True)
            p12 = [finding for finding in findings if finding["severity"].upper() in {"P0", "P1", "P2"}]
            if phase == "review":
                closure["review_findings"] = findings
                _write_review_checkpoint(
                    repo, identity, "active" if p12 else "passed",
                    closure["review_iterations"], findings,
                )
            if phase == "review" and p12:
                if not result["verified"]:
                    _pause(core, store, receipt_path, receipt, "review found P1/P2 findings without a verified fix", 24, review=True)
                # Every P0/P1/P2 fix requires another full-milestone review.
                phase_result = _closure_phase_result(receipt, closure, phase, result, retry_review=True)
                closure["review_iteration_started"] = False
                receipt["active_operation"].update({
                    "phase": "result_recorded",
                    "expected_snapshot_sha256": snapshot_digest(core.row_snapshot(repo)),
                    "phase_result": phase_result,
                })
                _save(store, receipt_path, receipt)
                commit_id = _commit_closure_changes(core, controller, store, receipt_path, receipt, repo, milestone, phase, before, milestone["closure_paths"], reservations, head, branch, phase_result=phase_result)
                _finish_closure_phase(receipt, milestone, phase_result, commit_id)
                receipt["active_operation"] = None
                _save(store, receipt_path, receipt)
                continue
            if not result["verified"] or not result["evidence"]:
                _pause(core, store, receipt_path, receipt, f"closure phase {phase} is not verified", 17, review=True)
            if phase == "acceptance":
                if closure.get("manual_evidence") and result.get("manual_evidence_verified") is not True:
                    _pause(core, store, receipt_path, receipt, "model did not verify the supplied manual evidence", 17, review=True)
                for task in milestone["tasks"]:
                    for command in task["verification"]:
                        reservations.check_time()
                        outcome = _run_sandbox_check(core, store, receipt_path, receipt, executor, repo, command, args)
                        if outcome.get("exit_code") != 0:
                            _pause(core, store, receipt_path, receipt, f"acceptance verification failed: {command}", 24, review=True)
                        closure["evidence"].append({"phase": "acceptance", "source": "command", "command": command, "exit_code": 0, "output": outcome.get("stdout", "")[:4000]})
            phase_result = _closure_phase_result(receipt, closure, phase, result)
            if phase == "review":
                closure["review_iteration_started"] = False
            receipt["active_operation"].update({
                "phase": "result_recorded",
                "expected_snapshot_sha256": snapshot_digest(core.row_snapshot(repo)),
                "phase_result": phase_result,
            })
            _save(store, receipt_path, receipt)
            commit_id = _commit_closure_changes(core, controller, store, receipt_path, receipt, repo, milestone, phase, before, milestone["closure_paths"], reservations, head, branch, phase_result=phase_result)
            _finish_closure_phase(receipt, milestone, phase_result, commit_id)
            receipt["active_operation"] = None
            _save(store, receipt_path, receipt)
        except LimitPaused:
            uncertain = not _is_clean_checkpoint(core, repo) or _active_operation_uncertain(receipt)
            receipt["state"] = "needs_review" if uncertain else "paused"
            receipt["pause_reason"] = "confirmed execution limit reached"
            if not uncertain:
                receipt["active_operation"] = None
            _save(store, receipt_path, receipt)
            raise


def run_horizon(
    core, args, repo: pathlib.Path, receipt_path: pathlib.Path, *,
    receipt_store, executor, manual_evidence: dict | None = None,
    output_fn=print, controller_module=None,
):
    """Execute approved rows, enforce durable caps, close milestones, and complete automatically."""

    controller = controller_module
    if controller is None:
        harness_dir = pathlib.Path(__file__).resolve().parent
        path = harness_dir / "tabilet_controller.py"
        spec = importlib.util.spec_from_file_location("_tabilet_horizon_controller", path)
        if spec is None or spec.loader is None:
            raise HorizonError("controller task runner is unavailable")
        controller = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controller)
    store = receipt_store
    receipt = store.load(receipt_path)
    root = pathlib.Path(repo)
    try:
        root = pathlib.Path(receipt["project_path"]).resolve(strict=True)
        if root != pathlib.Path(repo).resolve(strict=True):
            raise _UnresolvedDependency("receipt project path does not match the selected project")
        if receipt.get("state") not in {"running", "paused"}:
            raise _UnresolvedDependency("receipt is not in a resumable execution state")
        if receipt.get("active_operation") is not None:
            _pause(core, store, receipt_path, receipt, "an unfinished operation needs crash reconciliation", 25, review=True)
        if not _is_clean_checkpoint(core, root):
            _pause(core, store, receipt_path, receipt, "dirty worktree at resume; automatic reset and replay are forbidden", 25, review=True)
        if not core.git_head(root):
            _pause(core, store, receipt_path, receipt, "project has no committed planning checkpoint", 25, review=True)
        expected_head = (receipt.get("commit_ids") or [receipt.get("planning_commit")])[-1]
        expected_branch = receipt.get("branch") or "(detached)"
        if core.git_head(root) != expected_head or core.git_branch(root) != expected_branch:
            _pause(core, store, receipt_path, receipt, "project HEAD or branch changed since the last receipt checkpoint", 25, review=True)
        reservations = UsageReservations(core, store, receipt_path, receipt)
        receipt["state"] = "running"
        receipt["pause_reason"] = None
        _save(store, receipt_path, receipt)
        while True:
            reservations.check_time()
            selection = select_next_row(core, root, receipt)
            if selection["status"] == "waiting":
                receipt["state"] = "paused"
                receipt["pause_reason"] = selection["reason"]
                _save(store, receipt_path, receipt)
                core.fail(selection["reason"], 17)
            if selection["status"] == "row":
                _run_task(core, controller, args, root, store, receipt_path, receipt, executor, selection, reservations, output_fn)
                receipt = store.load(receipt_path)
                reservations.receipt = receipt
                continue
            if selection["status"] == "closure":
                milestone = selection["milestone"]
                _close_milestone(core, controller, args, root, store, receipt_path, receipt, executor, milestone, reservations, manual_evidence, output_fn)
                receipt = store.load(receipt_path)
                reservations.receipt = receipt
                continue
            if selection["status"] == "horizon_complete":
                receipt["state"] = "completed"
                receipt["pause_reason"] = None
                receipt["active_operation"] = None
                _save(store, receipt_path, receipt)
                closure_records = receipt.get("closure", {}).get("milestones", {})
                acceptance_results = {}
                for milestone in receipt["approved_horizon"]:
                    record = closure_records.get(milestone["id"], {})
                    acceptance_results[milestone["id"]] = {
                        "criteria": milestone["acceptance"],
                        "observed": [
                            evidence for evidence in record.get("evidence", [])
                            if evidence.get("phase") == "acceptance"
                        ],
                        "review_iterations": record.get("review_iterations", 0),
                        "closure_state": record.get("closure_state", "verified"),
                    }
                output_fn(json.dumps({
                    "status": "completed", "horizon": receipt["horizon_ids"],
                    "commits": receipt["commit_ids"], "verification": receipt.get("verification_evidence", []),
                    "acceptance_results": acceptance_results, "closure": receipt["closure"],
                    "external_actions": receipt["external_actions"],
                }, ensure_ascii=False, indent=2))
                return receipt
            raise _UnresolvedDependency(f"unknown horizon selection state: {selection['status']}")
    except KeyboardInterrupt:
        uncertain = not _is_clean_checkpoint(core, root) or _active_operation_uncertain(receipt)
        receipt["state"] = "needs_review" if uncertain else "paused"
        receipt["pause_reason"] = (
            "interrupted with an uncertain or dirty partial operation; manual review is required"
            if uncertain else "interrupted at a clean checkpoint"
        )
        if not uncertain:
            receipt["active_operation"] = None
        _save(store, receipt_path, receipt)
        try:
            output_fn(receipt["pause_reason"])
        except KeyboardInterrupt:
            pass
        raise SystemExit(130)
    except LimitPaused as exc:
        if receipt.get("state") != "needs_review":
            uncertain = not _is_clean_checkpoint(core, root) or _active_operation_uncertain(receipt)
            receipt["state"] = "needs_review" if uncertain else "paused"
            receipt["pause_reason"] = str(exc)
            if not uncertain:
                receipt["active_operation"] = None
            _save(store, receipt_path, receipt)
        if receipt.get("state") == "needs_review":
            core.fail(receipt.get("pause_reason") or str(exc), 25)
        core.fail(str(exc), 16)
    except SystemExit as exc:
        if receipt.get("state") == "running" and receipt.get("active_operation") is not None:
            uncertain = not _is_clean_checkpoint(core, root) or _active_operation_uncertain(receipt)
            receipt["state"] = "needs_review" if uncertain else "paused"
            receipt["pause_reason"] = f"controller stopped with exit {exc.code} during an active operation"
            if not uncertain:
                receipt["active_operation"] = None
            _save(store, receipt_path, receipt)
            if uncertain and exc.code != 25:
                core.fail(receipt["pause_reason"], 25)
        raise
    except (HorizonError, KeyError, TypeError, ValueError, OSError) as exc:
        if receipt.get("state") not in {"needs_review", "completed"}:
            uncertain = not _is_clean_checkpoint(core, root) or receipt.get("active_operation") is not None
            receipt["state"] = "needs_review" if uncertain else "paused"
            receipt["pause_reason"] = str(exc)[:2000]
            if not uncertain:
                receipt["active_operation"] = None
            _save(store, receipt_path, receipt)
        core.fail(f"Horizon execution stopped: {exc}", 25)

"""Receipt reconciliation for clean controller checkpoints and proven commits."""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import re
import tempfile


class RecoveryError(RuntimeError):
    """A receipt cannot be resumed from evidence that proves its checkpoint."""


class RecoveryStale(RecoveryError):
    """Immutable approval inputs no longer match the selected project."""


_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _horizon_module():
    path = pathlib.Path(__file__).resolve().with_name("tabilet_horizon.py")
    spec = importlib.util.spec_from_file_location("_tabilet_recovery_horizon", path)
    if spec is None or spec.loader is None:
        raise RecoveryError("horizon verification helpers are unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(core, repo: pathlib.Path, args: list[str]) -> str:
    result = core.git_local(args, repo)
    if result.returncode:
        raise RecoveryError(result.stderr.strip() or f"Git {args[0]} failed during recovery")
    return result.stdout


def _parents(core, repo: pathlib.Path, commit: str) -> list[str]:
    fields = _git(core, repo, ["rev-list", "--parents", "-n", "1", commit]).strip().split()
    if not fields or fields[0] != commit:
        raise RecoveryError("cannot prove candidate commit lineage")
    return fields[1:]


def _workflow_path(path: str) -> bool:
    if path == "AGENTS.md" or path == "tabilet/memory-bank/milestone.md":
        return True
    return bool(
        re.fullmatch(r"tabilet/memory-bank/status-[A-Z](?:0[1-9]|[1-9][0-9])\.md", path)
        or path.startswith("tabilet/docs/history/")
    )


def _snapshot_at(core, repo: pathlib.Path, commit: str) -> dict:
    """Materialize only workflow Markdown from a commit without changing the checkout."""

    horizon = _horizon_module()
    raw = _git(core, repo, ["ls-tree", "-r", "-z", "--full-tree", commit])
    if raw and not raw.endswith("\x00"):
        raise RecoveryError("Git returned an incomplete parent tree")
    entries = raw[:-1].split("\x00") if raw else []
    with tempfile.TemporaryDirectory(prefix="tabilet-recovery-") as temporary:
        root = pathlib.Path(temporary)
        copied = 0
        total = 0
        for entry in entries:
            header, separator, path = entry.partition("\t")
            if not separator:
                raise RecoveryError("Git returned a malformed parent tree entry")
            if not _workflow_path(path):
                continue
            if any(0xD800 <= ord(char) <= 0xDFFF for char in path):
                raise RecoveryError("workflow path is not valid UTF-8")
            mode, kind, object_id = header.split(" ", 2)
            if kind != "blob" or mode not in {"100644", "100755"} or not _OID.fullmatch(object_id):
                raise RecoveryError(f"unsupported non-regular workflow file in parent commit: {path}")
            content = _git(core, repo, ["show", f"{commit}:{path}"])
            encoded = content.encode("utf-8", errors="surrogateescape")
            copied += 1
            total += len(encoded)
            if copied > 5000 or total > 64 * 1024 * 1024:
                raise RecoveryError("parent workflow snapshot exceeds the recovery size limit")
            target = root.joinpath(*pathlib.PurePosixPath(path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(encoded)
        return core.row_snapshot(root)


def _changed_paths(core, repo: pathlib.Path, commit: str) -> list[str]:
    # Task and closure intents hash patches captured with --no-renames. Keep
    # path reconstruction on the same diff model so a move is represented by
    # its delete and add paths, regardless of Git's rename similarity guess.
    raw = _git(core, repo, ["diff-tree", "--no-renames", "--no-commit-id", "--name-only", "-z", "-r", commit])
    if not raw:
        return []
    if not raw.endswith("\x00"):
        raise RecoveryError("Git returned an incomplete candidate path list")
    values = raw[:-1].split("\x00")
    if any(not item or any(0xD800 <= ord(char) <= 0xDFFF for char in item) for item in values):
        raise RecoveryError("candidate commit contains an unsupported path")
    return values


def _validate_candidate(core, repo, operation, expected_branch) -> tuple[str, dict, dict]:
    candidate = operation.get("candidate_commit")
    expected_head = operation.get("expected_head")
    branch = expected_branch
    tree = operation.get("expected_tree")
    patch_hash = operation.get("expected_patch_sha256")
    message = operation.get("commit_message")
    if not all(isinstance(value, str) for value in (candidate, expected_head, tree, patch_hash, message)):
        raise RecoveryError("commit intent lacks its persisted candidate proof")
    if not _OID.fullmatch(candidate) or not _OID.fullmatch(expected_head) or not _OID.fullmatch(tree):
        raise RecoveryError("commit intent contains an invalid object ID")
    if not _DIGEST.fullmatch(patch_hash):
        raise RecoveryError("commit intent contains an invalid patch digest")
    if core.git_head(repo) != candidate:
        raise RecoveryError("HEAD is not the exact candidate commit recorded before ref update")
    if core.git_branch(repo) != (branch or "(detached)"):
        raise RecoveryError("branch changed after the candidate commit")
    if not core.git_clean(repo):
        raise RecoveryError("worktree or index is dirty after the candidate commit")
    if _parents(core, repo, candidate) != [expected_head]:
        raise RecoveryError("candidate commit does not have exactly the expected parent")
    actual_tree = _git(core, repo, ["rev-parse", "--verify", f"{candidate}^{{tree}}"]).strip()
    if actual_tree != tree:
        raise RecoveryError("candidate tree differs from the persisted expected tree")
    actual_message = _git(core, repo, ["show", "-s", "--format=%s", candidate]).rstrip("\n")
    if actual_message != message:
        raise RecoveryError("candidate commit message differs from the persisted intent")
    patch = _git(core, repo, ["show", "--format=", "--no-renames", "--binary", candidate])
    if hashlib.sha256(patch.encode("utf-8", errors="surrogateescape")).hexdigest() != patch_hash:
        raise RecoveryError("candidate patch differs from the persisted exact patch digest")
    paths = _changed_paths(core, repo, candidate)
    if sorted(paths) != sorted(operation.get("paths", [])):
        raise RecoveryError("candidate paths differ from the persisted approved path set")
    parent_snapshot = _snapshot_at(core, repo, expected_head)
    current_snapshot = core.row_snapshot(repo)
    expected_snapshot = operation.get("expected_snapshot_sha256")
    horizon = _horizon_module()
    if not isinstance(expected_snapshot, str) or not _DIGEST.fullmatch(expected_snapshot):
        raise RecoveryError("operation lacks its persisted verified workflow snapshot")
    if horizon.snapshot_digest(current_snapshot) != expected_snapshot:
        raise RecoveryError("live workflow snapshot differs from the verified pre-commit result")
    return candidate, parent_snapshot, current_snapshot


def _task_definition(receipt: dict, operation: dict) -> dict:
    milestone_id = operation.get("milestone_id")
    task_id = operation.get("task_id")
    for milestone in receipt.get("approved_horizon", []):
        if milestone.get("id") == milestone_id:
            for task in milestone.get("tasks", []):
                if task.get("id") == task_id:
                    return milestone, task
    raise RecoveryError("selected task is not in the approved horizon")


def _reconcile_task(core, repo, receipt, operation):
    horizon = _horizon_module()
    _, task = _task_definition(receipt, operation)
    if sorted(operation.get("verification", [])) != sorted(task.get("verification", [])):
        raise RecoveryError("task verification intent differs from the approved task")
    results = operation.get("verification_results")
    if not isinstance(results, dict) or any(results.get(command) is not True for command in task["verification"]):
        raise RecoveryError("required verification evidence is missing or failed")
    approved_paths = set(task.get("approved_paths", []))
    if not set(operation.get("paths", [])) <= approved_paths:
        raise RecoveryError("candidate changed a path outside the approved task scope")
    row_key = operation.get("row_key")
    if not isinstance(row_key, list) or len(row_key) != 3:
        raise RecoveryError("task intent lacks the selected live row identity")
    key = (row_key[0], row_key[1], row_key[2])
    candidate, before, after = _validate_candidate(core, repo, operation, receipt.get("branch"))
    gate = core.post_run_gates(
        repo, operation["expected_head"], receipt.get("branch") or "(detached)",
        before, after, key,
    )
    if gate.get("exit_code"):
        raise RecoveryError("task post-commit gate failed during recovery: " + str(gate.get("gate")))
    evidence = receipt.get("verification_evidence", [])
    row_id = f"{operation['milestone_id']}/{operation['task_id']}"
    for command in task["verification"]:
        if not any(
            isinstance(item, dict) and item.get("row_id") == row_id
            and item.get("command") == command and item.get("exit_code") == 0
            for item in evidence
        ):
            raise RecoveryError(f"successful verification evidence is missing for {command}")
    return candidate


def _closure_result_valid(phase_result, operation):
    if not isinstance(phase_result, dict):
        raise RecoveryError("closure commit has no persisted model phase result")
    if phase_result.get("operation_id") != operation.get("operation_id"):
        raise RecoveryError("closure result does not belong to the persisted operation")
    if phase_result.get("phase") != operation.get("closure_phase"):
        raise RecoveryError("closure result phase differs from the operation")
    if phase_result.get("verified") is not True:
        raise RecoveryError("closure result was not verified")
    if not isinstance(phase_result.get("manual_evidence_verified"), bool):
        raise RecoveryError("closure result manual-evidence state is malformed")
    if phase_result.get("phase") not in {"review", "acceptance", "consolidation", "downstream", "retirement"}:
        raise RecoveryError("closure result names an unknown phase")
    if not isinstance(phase_result.get("items"), list) or not phase_result["items"]:
        raise RecoveryError("closure result has no evidence items")
    if any(not isinstance(item, str) or not item.strip() for item in phase_result["items"]):
        raise RecoveryError("closure result evidence items are malformed")
    if not isinstance(phase_result.get("findings"), list):
        raise RecoveryError("closure result findings are malformed")
    if not isinstance(phase_result.get("retry_review"), bool):
        raise RecoveryError("closure result retry decision is malformed")
    return phase_result


def _reconcile_closure(core, repo, receipt, operation):
    horizon = _horizon_module()
    phase_result = _closure_result_valid(operation.get("phase_result"), operation)
    milestone = next(
        (item for item in receipt.get("approved_horizon", []) if item.get("id") == operation.get("milestone_id")),
        None,
    )
    if milestone is None or not set(operation.get("paths", [])) <= set(milestone.get("closure_paths", [])):
        raise RecoveryError("closure commit is outside the approved milestone scope")
    if operation.get("closure_phase") == "retirement" and milestone.get("retirement_adopted") is not True:
        raise RecoveryError("retirement was not adopted in the approved milestone")
    candidate, before, after = _validate_candidate(core, repo, operation, receipt.get("branch"))
    before_digest = operation.get("before_snapshot_sha256")
    if not isinstance(before_digest, str) or horizon.snapshot_digest(before) != before_digest:
        raise RecoveryError("closure parent workflow snapshot differs from its recorded baseline")
    closure = receipt.get("closure", {}).get("milestones", {}).get(milestone["id"], {})
    review_iterations = closure.get("review_iterations")
    if operation.get("closure_phase") == "review":
        try:
            checkpoint = horizon._review_checkpoint(repo, milestone["id"])
        except Exception as exc:
            raise RecoveryError(f"review checkpoint cannot be read after the candidate commit: {exc}") from exc
        expected_gate = "active" if phase_result.get("retry_review") else "passed"
        if (
            checkpoint is None
            or checkpoint.get("gate") != expected_gate
            or checkpoint.get("iterations") != review_iterations
            or checkpoint.get("findings") != phase_result.get("findings")
        ):
            raise RecoveryError("review checkpoint differs from the persisted phase result")
    problems = horizon._closure_integrity_problems(
        before, after,
        retirement_id=milestone["id"] if operation.get("closure_phase") == "retirement" else None,
        review_iterations=review_iterations,
    )
    if problems:
        raise RecoveryError("closure integrity failed during recovery: " + "; ".join(problems))
    if operation.get("closure_phase") == "acceptance":
        if milestone.get("manual_evidence") and not phase_result.get("manual_evidence_verified"):
            raise RecoveryError("required manual evidence lacks persisted model verification")
        for task in milestone.get("tasks", []):
            for command in task.get("verification", []):
                if not any(
                    isinstance(item, dict) and item.get("phase") == "acceptance"
                    and item.get("source") == "command" and item.get("command") == command
                    and item.get("exit_code") == 0
                    for item in closure.get("evidence", [])
                ):
                    raise RecoveryError(f"acceptance verification evidence is missing for {command}")
    return candidate, milestone, phase_result


def _record_commit(receipt: dict, commit: str) -> None:
    ids = receipt.setdefault("commit_ids", [])
    if commit not in ids:
        ids.append(commit)
        usage = receipt.setdefault("usage", {})
        usage["commits_recorded"] = usage.get("commits_recorded", 0) + 1
    receipt["state"] = "running"
    receipt["pause_reason"] = None


def _verify_recorded_lineage(core, repo, receipt):
    commits = receipt.get("commit_ids")
    if not isinstance(commits, list) or not commits or any(
        not isinstance(value, str) or not _OID.fullmatch(value) for value in commits
    ):
        raise RecoveryError("receipt commit history is malformed")
    if receipt.get("planning_commit") != commits[0]:
        raise RecoveryError("planning commit differs from the first recorded checkpoint")
    previous = receipt.get("baseline_commit")
    for commit in commits:
        expected_parents = [] if previous is None else [previous]
        if _parents(core, repo, commit) != expected_parents:
            raise RecoveryError("recorded receipt commits do not form the expected linear history")
        previous = commit
    if receipt.get("usage", {}).get("commits_recorded") != len(commits):
        raise RecoveryError("recorded commit usage differs from the receipt commit list")


def _mark_review(store, path, receipt, reason):
    receipt["state"] = "needs_review"
    receipt["pause_reason"] = reason[:2000]
    store.update_atomic(path, receipt)
    raise RecoveryError(reason)


def reconcile_receipt(core, store, receipt_path: pathlib.Path, receipt: dict, repo: pathlib.Path) -> dict:
    """Prove the checkpoint or record one exact commit that outran its receipt."""

    root = pathlib.Path(repo).resolve(strict=True)
    if receipt.get("project_path") != str(root):
        raise RecoveryStale("receipt belongs to a different canonical project; create a new proposal")
    receipt_id = receipt.get("receipt_id")
    if not isinstance(receipt_id, str) or pathlib.Path(receipt_path).name != f"{receipt_id}.json":
        _mark_review(store, receipt_path, receipt, "receipt ID does not match its private filename")
    if receipt.get("state") == "needs_review":
        raise RecoveryError(receipt.get("pause_reason") or "receipt already requires manual review")
    if receipt.get("state") == "completed":
        return receipt
    if receipt.get("state") not in {"running", "paused"}:
        raise RecoveryError("receipt is not a planning-complete resumable horizon")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(receipt.get("image_id", ""))):
        raise RecoveryError("approved receipt has no immutable Docker image ID")
    usage, limits = receipt.get("usage"), receipt.get("limits")
    if not isinstance(usage, dict) or not isinstance(limits, dict):
        _mark_review(store, receipt_path, receipt, "receipt cumulative usage or limits are malformed")
    for key in ("rows_started", "provider_attempts_reserved", "commits_reserved", "commits_recorded"):
        value = usage.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _mark_review(store, receipt_path, receipt, f"receipt cumulative usage field is invalid: {key}")
    turn_usage = usage.get("turns_by_row", {})
    if not isinstance(turn_usage, dict) or any(
        not isinstance(name, str) or isinstance(value, bool) or not isinstance(value, int) or value < 0
        for name, value in turn_usage.items()
    ):
        _mark_review(store, receipt_path, receipt, "receipt model-turn usage is malformed")
    if sum(turn_usage.values()) > usage.get("provider_attempts_reserved", 0):
        _mark_review(store, receipt_path, receipt, "provider-attempt usage is lower than dispatched model turns")
    turn_cap = limits.get("max_turns_per_row")
    if isinstance(turn_cap, bool) or not isinstance(turn_cap, int) or turn_cap < 1 or any(
        value > turn_cap for value in turn_usage.values()
    ):
        _mark_review(store, receipt_path, receipt, "receipt model-turn usage exceeds or has an invalid confirmed cap")
    row_ids = usage.get("rows_started_ids", [])
    if (
        not isinstance(row_ids, list) or any(not isinstance(value, str) for value in row_ids)
        or len(set(row_ids)) != len(row_ids) or len(row_ids) != usage.get("rows_started")
    ):
        _mark_review(store, receipt_path, receipt, "receipt started-row identities do not match cumulative usage")
    for limit_key, usage_key in (
        ("max_rows", "rows_started"),
        ("max_provider_attempts", "provider_attempts_reserved"),
        ("max_commits", "commits_reserved"),
    ):
        cap = limits.get(limit_key)
        if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1 or usage[usage_key] > cap:
            _mark_review(store, receipt_path, receipt, f"receipt exceeded or has invalid confirmed limit: {limit_key}")
    if usage["commits_recorded"] > usage["commits_reserved"]:
        _mark_review(store, receipt_path, receipt, "recorded commit usage exceeds its durable reservations")
    branch = core.git_branch(root)
    if branch != (receipt.get("branch") or "(detached)"):
        raise RecoveryStale("project branch changed since approval; review the new branch and create a new proposal")
    try:
        _verify_recorded_lineage(core, root, receipt)
    except RecoveryError as exc:
        _mark_review(store, receipt_path, receipt, str(exc))
    operation = receipt.get("active_operation")
    recorded_ids = receipt.get("commit_ids") or [receipt.get("planning_commit")]
    expected = recorded_ids[-1]
    already_recorded_candidate = False
    if isinstance(operation, dict) and len(recorded_ids) >= 2:
        already_recorded_candidate = (
            operation.get("candidate_commit") == recorded_ids[-1]
            and operation.get("expected_head") == recorded_ids[-2]
        )
    if already_recorded_candidate:
        expected = operation.get("expected_head")
    if not isinstance(expected, str) or not _OID.fullmatch(expected):
        _mark_review(store, receipt_path, receipt, "receipt has no valid last committed checkpoint")
    if operation is None:
        if core.git_head(root) != expected or not core.git_clean(root):
            _mark_review(store, receipt_path, receipt, "project HEAD or worktree differs from the last receipt checkpoint")
        return receipt
    if not isinstance(operation, dict) or operation.get("expected_head") != expected:
        _mark_review(store, receipt_path, receipt, "active operation does not start at the last receipt checkpoint")
    phase = operation.get("phase")
    if phase == "prepared":
        if core.git_head(root) != expected or not core.git_clean(root):
            _mark_review(store, receipt_path, receipt, "prepared operation left a dirty or advanced project; manual review is required")
        receipt["active_operation"] = None
        receipt["state"] = "paused"
        receipt["pause_reason"] = "prepared operation had not dispatched; clean checkpoint is safe to resume"
        store.update_atomic(receipt_path, receipt)
        return receipt
    if phase == "result_recorded" and operation.get("kind") == "closure":
        horizon = _horizon_module()
        phase_result = _closure_result_valid(operation.get("phase_result"), operation)
        if core.git_head(root) != expected or not core.git_clean(root):
            _mark_review(store, receipt_path, receipt, "recorded closure result has an unexpected or dirty worktree")
        live_snapshot = core.row_snapshot(root)
        parent_snapshot = _snapshot_at(core, root, expected)
        before_digest = operation.get("before_snapshot_sha256")
        if not isinstance(before_digest, str) or horizon.snapshot_digest(parent_snapshot) != before_digest:
            _mark_review(store, receipt_path, receipt, "recorded closure baseline no longer matches its clean checkpoint")
        expected_snapshot = operation.get("expected_snapshot_sha256")
        if not isinstance(expected_snapshot, str) or horizon.snapshot_digest(live_snapshot) != expected_snapshot:
            _mark_review(store, receipt_path, receipt, "recorded no-commit closure result no longer matches the clean live snapshot")
        milestone = next(
            (item for item in receipt.get("approved_horizon", []) if item.get("id") == operation.get("milestone_id")),
            None,
        )
        if milestone is None:
            _mark_review(store, receipt_path, receipt, "recorded closure milestone is outside the approved horizon")
        if operation.get("closure_phase") == "retirement" and milestone.get("retirement_adopted") is not True:
            _mark_review(store, receipt_path, receipt, "retirement was not adopted in the approved milestone")
        if operation.get("closure_phase") == "acceptance" and milestone.get("manual_evidence") and not phase_result.get("manual_evidence_verified"):
            _mark_review(store, receipt_path, receipt, "required manual evidence lacks persisted model verification")
        if operation.get("closure_phase") == "acceptance":
            closure_record = receipt.get("closure", {}).get("milestones", {}).get(milestone["id"], {})
            for task in milestone.get("tasks", []):
                for command in task.get("verification", []):
                    if not any(
                        isinstance(item, dict) and item.get("phase") == "acceptance"
                        and item.get("source") == "command" and item.get("command") == command
                        and item.get("exit_code") == 0
                        for item in closure_record.get("evidence", [])
                    ):
                        _mark_review(store, receipt_path, receipt, f"acceptance verification evidence is missing for {command}")
        horizon._finish_closure_phase(receipt, milestone, phase_result)
        receipt["active_operation"] = None
        receipt["state"] = "running"
        receipt["pause_reason"] = None
        store.update_atomic(receipt_path, receipt)
        return receipt
    if phase != "commit_attempted":
        _mark_review(
            store, receipt_path, receipt,
            f"operation stopped in uncertain phase {phase!r}; it will not be replayed automatically",
        )
    try:
        if operation.get("kind") == "task_commit":
            commit = _reconcile_task(core, root, receipt, operation)
            if not core.git_is_ancestor(root, expected, commit):
                raise RecoveryError("recovered task commit does not descend from the receipt checkpoint")
        elif operation.get("kind") == "closure_commit":
            commit, milestone, phase_result = _reconcile_closure(core, root, receipt, operation)
            if not core.git_is_ancestor(root, expected, commit):
                raise RecoveryError("recovered closure commit does not descend from the receipt checkpoint")
            _record_commit(receipt, commit)
            horizon = _horizon_module()
            horizon._finish_closure_phase(receipt, milestone, phase_result, commit)
            receipt["active_operation"] = None
            store.update_atomic(receipt_path, receipt)
            return receipt
        else:
            raise RecoveryError("only task and closure commit intents can be reconciled here")
    except (RecoveryError, OSError, ValueError, KeyError, TypeError) as exc:
        _mark_review(store, receipt_path, receipt, str(exc))
    _record_commit(receipt, commit)
    receipt["active_operation"] = None
    store.update_atomic(receipt_path, receipt)
    return receipt

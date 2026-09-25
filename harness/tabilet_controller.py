#!/usr/bin/env python3
"""Thin controller adapter over the shared Tabilet runner core."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import re
import os
import sys
import types


CONTROLLER_SYSTEM_PROMPT = """\
You are a coding agent working under the Tabilet controller.

Return exactly one JSON object per response, without surrounding prose. Use
{"tool":"run_shell","cmd":"...","why":"..."} for a command or
{"final":"..."} when the selected task work is finished.

Work only on the selected task row or closure phase named in the user message,
and only within that operation's approved file scope.
The controller owns Git operations.
Do not run git add, git commit, git reset, git checkout, git switch, or commands
that alter branches, tags, or commit history. Do not claim a commit was made.
When finished, return a concise summary and a proposed host commit message.
"""


def load_runner_core():
    """Load the adjacent standalone runner without invoking its CLI entrypoint."""

    path = pathlib.Path(__file__).resolve().with_name("tackle-memory-bank-api-loop")
    loader = importlib.machinery.SourceFileLoader("_tabilet_api_runner_core", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_planning_module():
    """Load the adjacent read-only planning protocol module."""

    path = pathlib.Path(__file__).resolve().with_name("tabilet_planning.py")
    loader = importlib.machinery.SourceFileLoader("_tabilet_planning", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None or spec.loader is None:
        raise ImportError("controller planning module is missing")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_proposal_module():
    """Load proposal rendering and private receipt recovery helpers."""

    path = pathlib.Path(__file__).resolve().with_name("tabilet_proposal.py")
    loader = importlib.machinery.SourceFileLoader("_tabilet_proposal", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None or spec.loader is None:
        raise ImportError("controller proposal module is missing")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_horizon_module():
    """Load the adjacent receipt-bounded execution and closure module."""

    path = pathlib.Path(__file__).resolve().with_name("tabilet_horizon.py")
    loader = importlib.machinery.SourceFileLoader("_tabilet_horizon", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None or spec.loader is None:
        raise ImportError("controller horizon module is missing")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_recovery_module():
    path = pathlib.Path(__file__).resolve().with_name("tabilet_recovery.py")
    spec = importlib.util.spec_from_file_location("_tabilet_recovery", path)
    if spec is None or spec.loader is None:
        raise ImportError("controller recovery module is missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_status_module():
    path = pathlib.Path(__file__).resolve().with_name("tabilet_status.py")
    spec = importlib.util.spec_from_file_location("_tabilet_status", path)
    if spec is None or spec.loader is None:
        raise ImportError("controller status module is missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def approve_proposal(
    core,
    repo: pathlib.Path,
    proposal: dict,
    *,
    receipt_store=None,
    input_fn=input,
    output_fn=print,
    revise_fn=None,
    fault_hook=None,
) -> dict:
    """Approve and apply one rendered planning proposal under the project lock."""

    planner = load_proposal_module()

    def run():
        validate_repository_topology(core, repo)
        try:
            result = planner.approve_proposal(
                core, repo, proposal, receipt_store=receipt_store, input_fn=input_fn,
                output_fn=output_fn, revise_fn=revise_fn, fault_hook=fault_hook,
            )
        except planner.ApprovalStale as exc:
            core.fail(f"Approval is stale; review the revised proposal and confirm again: {exc}", 18)
        except planner.RecoveryNeedsReview as exc:
            core.fail(f"Planning recovery needs manual review: {exc}", 25)
        except planner.ProposalError as exc:
            core.fail(f"Proposal cannot be approved: {exc}", 2)
        if result.get("status") == "needs_review":
            core.fail(f"Planning recovery needs manual review: {result.get('reason', 'uncertain state')}", 25)
        return result

    return run_with_project_lock(core, repo, run)


def resume_approved_receipt(core, repo: pathlib.Path, receipt_path: pathlib.Path, *, receipt_store=None, fault_hook=None):
    """Recover a clean approved planning checkpoint while holding the shared lock."""

    planner = load_proposal_module()

    def run():
        validate_repository_topology(core, repo)
        try:
            result = planner.resume_approved_receipt(
                core, repo, receipt_path, receipt_store=receipt_store, fault_hook=fault_hook,
            )
        except planner.ProposalError as exc:
            core.fail(f"Planning recovery needs manual review: {exc}", 25)
        if result.get("status") == "needs_review":
            core.fail(f"Planning recovery needs manual review: {result.get('reason', 'uncertain state')}", 25)
        return result

    return run_with_project_lock(core, repo, run)


def execute_horizon(
    core, args, repo: pathlib.Path, receipt_path: pathlib.Path, *,
    receipt_store=None, image_id=None, manual_evidence=None,
    output_fn=print,
):
    """Execute or resume one confirmed horizon under the shared project lock."""

    horizon = load_horizon_module()
    if receipt_store is None:
        proposal = load_proposal_module()
        receipt_store = proposal.ReceiptStore()

    def run():
        try:
            receipt = receipt_store.load(receipt_path)
        except Exception as exc:
            core.fail(f"Cannot load approved horizon receipt: {exc}", 25)
        return _execute_horizon_locked(
            core, args, repo, receipt_path, receipt, receipt_store,
            horizon=horizon, image_id=image_id, manual_evidence=manual_evidence,
            output_fn=output_fn,
        )

    return run_with_project_lock(core, repo, run)


def _execute_horizon_locked(
    core, args, repo, receipt_path, receipt, receipt_store, *, horizon=None,
    image_id=None, manual_evidence=None, output_fn=print,
):
    horizon = horizon or load_horizon_module()
    if receipt.get("state") == "completed":
        output_fn(f"Horizon {receipt.get('horizon_ids', [])} is already completed.")
        return receipt
    if receipt.get("state") == "needs_review" or receipt.get("active_operation") is not None:
        core.fail("The receipt has an unfinished or uncertain operation; run API 7 recovery before execution.", 25)
    if receipt.get("state") not in {"running", "paused"}:
        core.fail("The receipt is not ready for horizon execution; reconcile planning approval first.", 25)
    approved_image = receipt.get("image_id")
    if image_id is not None and image_id != approved_image:
        core.fail("Selected Docker image differs from the immutable image ID in the approved receipt.", 18)
    if not isinstance(approved_image, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", approved_image):
        receipt["state"] = "paused"
        receipt["pause_reason"] = "receipt has no valid immutable Docker image ID"
        receipt_store.update_atomic(receipt_path, receipt)
        core.fail("Execution requires the immutable Docker image ID from the approved receipt.", 17)
    try:
        selected_executor = prepare_docker_executor(core, repo, approved_image)
    except SystemExit as exc:
        if exc.code == 17:
            try:
                clean = core.git_clean(repo)
            except Exception:
                clean = False
            receipt["state"] = "paused" if clean else "needs_review"
            receipt["pause_reason"] = "Docker executor setup is unavailable"
            if clean:
                receipt["active_operation"] = None
            receipt_store.update_atomic(receipt_path, receipt)
        raise

    audit = None
    try:
        audit_instruction_args = types.SimpleNamespace(**vars(args))
        audit_instruction_args.audit_instruction_text = CONTROLLER_SYSTEM_PROMPT
        audit_instruction_args.audit_capture = getattr(
            args, "audit_capture", os.environ.get("TABILET_AUDIT_CAPTURE", "metadata"),
        )
        audit_instruction_args.audit_db = getattr(args, "audit_db", None) or os.environ.get("TABILET_AUDIT_DB")
        audit = core.AuditRun(
            audit_instruction_args, repo, "next", core.git_head(repo),
            "clean" if core.git_clean(repo) else "dirty",
            invocation_kind="host_operation",
            instruction_set_name="tabilet-controller/system-prompt",
            host_agent="tabilet-controller",
        )
        audit.emit("task_observed", details={
            "controller": "tabilet-api-horizon",
            "receipt_id": receipt.get("receipt_id"),
            "horizon": receipt.get("horizon_ids", []),
        })
    except Exception as exc:
        print(f"Audit gap: unable to initialize controller run: {exc}", file=sys.stderr)
        audit = None
    try:
        result = horizon.run_horizon(
            core, args, repo, receipt_path, receipt_store=receipt_store,
            executor=selected_executor, manual_evidence=manual_evidence,
            output_fn=output_fn,
            controller_module=sys.modules.get(__name__) or types.SimpleNamespace(
                run_controller_agent=run_controller_agent,
                precommit_problems=precommit_problems,
                commit_host_changes=commit_host_changes,
            ),
        )
        if audit is not None:
            _audit_best_effort(audit, "finish", "completed" if result.get("state") == "completed" else "blocked")
        return result
    except KeyboardInterrupt:
        if audit is not None:
            _audit_best_effort(audit, "emit", "run_interrupted", details={"receipt_state": "interrupted"})
            _audit_best_effort(audit, "finish", "interrupted")
        raise
    except BaseException as exc:
        if audit is not None:
            try:
                latest = receipt_store.load(receipt_path)
                state = latest.get("state", "unknown")
                detail = {"receipt_state": state, "reason": str(exc)[:1000]}
            except Exception:
                state, detail = "unknown", {"receipt_state": "unknown", "reason": str(exc)[:1000]}
            if isinstance(exc, SystemExit) and exc.code == 130:
                _audit_best_effort(audit, "emit", "run_interrupted", details=detail)
                _audit_best_effort(audit, "finish", "interrupted")
            else:
                _audit_best_effort(
                    audit, "emit", "run_blocked" if state in {"paused", "needs_review"} else "run_failed",
                    details=detail,
                )
                _audit_best_effort(audit, "finish", "blocked" if state in {"paused", "needs_review"} else "failed")
        raise


def _audit_best_effort(audit, method, *args, **kwargs):
    try:
        getattr(audit, method)(*args, **kwargs)
    except Exception as exc:
        print(f"Audit gap: unable to {method} controller run: {exc}", file=sys.stderr)


def status_project(core, repo: pathlib.Path, *, receipt_store=None, output_fn=print):
    """Show the read-only status report without acquiring the project lock."""

    status = load_status_module()
    validate_repository_topology(core, repo)
    try:
        report = status.status_report(core, repo, receipt_store=receipt_store)
    except status.StatusError as exc:
        core.fail(f"Cannot read Tabilet status: {exc}", 2)
    output_fn(status.format_status(report))
    return report


def resume_horizon(
    core, args, repo: pathlib.Path, receipt_path: pathlib.Path, *,
    receipt_store=None, image_id=None, manual_evidence=None, output_fn=print,
    fault_hook=None,
):
    """Reconcile an approved receipt and continue it under the shared project lock."""

    if receipt_store is None:
        receipt_store = load_proposal_module().ReceiptStore()
    planner = load_proposal_module()
    recovery = load_recovery_module()
    horizon = load_horizon_module()

    def run():
        try:
            receipt = receipt_store.load(receipt_path)
        except Exception as exc:
            core.fail(f"Cannot load horizon receipt: {exc}", 25)
        if receipt.get("project_path") != str(pathlib.Path(repo).resolve(strict=True)):
            core.fail("The selected receipt belongs to another project; choose its canonical project path.", 18)
        if receipt.get("state") == "completed":
            output_fn(f"Horizon {receipt.get('horizon_ids', [])} is already completed.")
            return receipt
        if receipt.get("state") == "approved":
            if core.git_branch(repo) != (receipt.get("branch") or "(detached)"):
                core.fail("Planning approval is stale because the project branch changed; review it and propose again.", 18)
        validate_repository_topology(core, repo)
        if receipt.get("state") == "approved":
            try:
                result = planner.resume_approved_receipt(
                    core, repo, receipt_path, receipt_store=receipt_store, fault_hook=fault_hook,
                )
            except planner.ProposalError as exc:
                core.fail(f"Planning recovery needs manual review: {exc}", 25)
            if result.get("status") == "needs_review":
                core.fail(f"Planning recovery needs manual review: {result.get('reason', 'uncertain state')}", 25)
            receipt = receipt_store.load(receipt_path)
        if receipt.get("state") == "completed":
            output_fn(f"Horizon {receipt.get('horizon_ids', [])} is already completed.")
            return receipt
        try:
            recovery.reconcile_receipt(core, receipt_store, receipt_path, receipt, repo)
        except recovery.RecoveryStale as exc:
            core.fail(f"Horizon approval is stale: {exc}", 18)
        except recovery.RecoveryError as exc:
            core.fail(f"Horizon recovery needs manual review: {exc}", 25)
        receipt = receipt_store.load(receipt_path)
        return _execute_horizon_locked(
            core, args, repo, receipt_path, receipt, receipt_store,
            horizon=horizon, image_id=image_id, manual_evidence=manual_evidence,
            output_fn=output_fn,
        )

    return run_with_project_lock(core, repo, run)


def extend_horizon_limit(
    core, repo: pathlib.Path, receipt_path: pathlib.Path, name: str, value: int,
    *, receipt_store=None, input_fn=input,
):
    """Confirm one higher numeric cap under the shared project lock."""

    horizon = load_horizon_module()
    if receipt_store is None:
        receipt_store = load_proposal_module().ReceiptStore()

    def run():
        validate_repository_topology(core, repo)
        try:
            receipt = receipt_store.load(receipt_path)
            return horizon.extend_limit(
                core, receipt_store, receipt_path, receipt, name, value,
                input_fn=input_fn,
            )
        except horizon.HorizonError as exc:
            core.fail(f"Limit extension was not applied: {exc}", 18)

    return run_with_project_lock(core, repo, run)


def run_planning_session(
    core,
    args,
    repo: pathlib.Path,
    operation: str,
    request: str,
    skill_bundle_root: pathlib.Path | None = None,
    input_fn=input,
    output_fn=print,
) -> dict:
    """Run the API 4 planning loop under the shared Tabilet project lock."""

    planner = load_planning_module()

    def run():
        validate_repository_topology(core, repo)
        try:
            return planner.run_planning_session(
                core, args, repo, operation, request,
                skill_bundle_root=skill_bundle_root,
                input_fn=input_fn,
                output_fn=output_fn,
            )
        except planner.BundleIntegrityError as exc:
            core.fail(f"Installed planning bundles failed integrity verification: {exc}", 17)
        except planner.PlanningError as exc:
            core.fail(f"Planning stopped: {exc}", 2)

    return run_with_project_lock(core, repo, run)


def run_controller_agent(
    core,
    args,
    repo: pathlib.Path,
    run: int,
    summary: list[dict],
    selected_row: dict | None,
    executor,
    user_message: str,
    before_model_turn=None,
    before_provider_attempt=None,
    before_command=None,
    after_command=None,
) -> dict[str, object]:
    """Use the shared model loop with controller-specific instructions/execution."""

    def sandboxed_executor(*executor_args, **executor_kwargs):
        try:
            result = executor(*executor_args, **executor_kwargs)
        except Exception as exc:
            sandbox_error = getattr(executor, "sandbox_unavailable", None)
            if sandbox_error is not None and isinstance(exc, sandbox_error):
                core.fail(f"Controller Docker sandbox is unavailable: {exc}", 17)
            raise
        if result.get("exit_code") == 127:
            detail = result.get("stderr", "").strip()
            core.fail(
                "A required command or dependency is missing from the local Docker image. "
                "Pause with exit 17, add the dependency to the image, and retry."
                + (f"\n{detail}" if detail else ""),
                17,
            )
        return result

    return core.one_agent_run(
        args,
        repo,
        run,
        summary,
        selected_row,
        executor=sandboxed_executor,
        system_prompt=CONTROLLER_SYSTEM_PROMPT,
        user_message=user_message,
        before_model_turn=before_model_turn,
        before_provider_attempt=before_provider_attempt,
        before_command=before_command,
        after_command=after_command,
    )


def prepare_docker_executor(core, repo: pathlib.Path, image: str, mountinfo=None):
    """Resolve topology, the local daemon, and image ID before provider dispatch."""

    try:
        import tabilet_container
    except ImportError:
        # Installed controller files are adjacent, but tests and direct module
        # loading may not have added that directory to sys.path.
        import importlib.util
        path = pathlib.Path(__file__).resolve().with_name("tabilet_container.py")
        spec = importlib.util.spec_from_file_location("_tabilet_container", path)
        if spec is None or spec.loader is None:
            core.fail("Controller Docker sandbox module is missing; install the complete controller bundle.", 17)
        tabilet_container = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tabilet_container)
    try:
        if mountinfo is None:
            return tabilet_container.prepare_executor(core, repo, image)
        return tabilet_container.prepare_executor(core, repo, image, mountinfo)
    except tabilet_container.SandboxUnavailable as exc:
        core.fail(f"Controller Docker sandbox is unavailable: {exc}", 17)


def validate_repository_topology(core, repo: pathlib.Path, mountinfo=None):
    """Reject unsupported Git layouts and active filters before controller Git work."""

    try:
        import tabilet_container
    except ImportError:
        path = pathlib.Path(__file__).resolve().with_name("tabilet_container.py")
        spec = importlib.util.spec_from_file_location("_tabilet_container_topology", path)
        if spec is None or spec.loader is None:
            core.fail("Controller Docker sandbox module is missing; install the complete controller bundle.", 17)
        tabilet_container = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tabilet_container)
    try:
        if mountinfo is None:
            return tabilet_container.validate_repository(core, repo)
        return tabilet_container.validate_repository(core, repo, mountinfo)
    except tabilet_container.SandboxUnavailable as exc:
        core.fail(f"Controller repository topology is unsupported: {exc}", 17)


def precommit_problems(
    core,
    before_rows: dict,
    after_rows: dict,
    selected_key: tuple[str, str, int],
    approved_paths,
    changed_paths,
    required_checks,
    check_results: dict[str, bool],
) -> list[str]:
    """Validate the changed row, protected history, paths, and required checks."""

    problems = core.validate_row_transition(before_rows, after_rows, selected_key)
    allowed = set(approved_paths)
    for path in sorted(set(changed_paths) - allowed):
        problems.append(f"changed path is outside the approved file scope: {path}")
    for check in required_checks:
        if check_results.get(check) is not True:
            problems.append(f"required verification did not pass: {check}")
    return problems


def commit_after_precommit(
    core,
    before_rows: dict,
    after_rows: dict,
    selected_key: tuple[str, str, int],
    approved_paths,
    changed_paths,
    required_checks,
    check_results: dict[str, bool],
    host_commit,
) -> dict:
    """Call the host-commit seam only when all deterministic pre-commit gates pass."""

    problems = precommit_problems(
        core,
        before_rows,
        after_rows,
        selected_key,
        approved_paths,
        changed_paths,
        required_checks,
        check_results,
    )
    if problems:
        core.fail(
            "Controller pre-commit validation failed; no host task commit was made:\n  "
            + "\n  ".join(problems),
            24,
        )
    return {
        "committed": True,
        "problems": [],
        "commit_result": host_commit(),
    }


def commit_host_changes(
    core, repo: pathlib.Path, expected_head, expected_branch, expected_patch: str,
    message: str, *, before_ref_update=None,
) -> str:
    """Commit the validated staged tree with the shared expected-ref CAS."""

    proposal = load_proposal_module()
    return proposal.commit_staged_tree(
        core, repo, expected_head, expected_branch, expected_patch, message,
        before_ref_update=before_ref_update,
    )


def run_with_project_lock(core, repo: pathlib.Path, operation, *args, **kwargs):
    """Run a controller operation under the runner's shared project lock."""

    try:
        with core.project_lock(repo):
            return operation(*args, **kwargs)
    except core.ProjectLockUnavailable as exc:
        core.fail(
            "Another Tabilet launcher already holds the project lock; wait for it to "
            f"finish before starting a second run ({exc}).",
            19,
        )

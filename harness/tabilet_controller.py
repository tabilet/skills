#!/usr/bin/env python3
"""Thin controller adapter over the shared Tabilet runner core."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib


CONTROLLER_SYSTEM_PROMPT = """\
You are a coding agent working under the Tabilet controller.

Return exactly one JSON object per response, without surrounding prose. Use
{"tool":"run_shell","cmd":"...","why":"..."} for a command or
{"final":"..."} when the selected task work is finished.

Work on exactly the selected task row and only within the approved file scope.
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

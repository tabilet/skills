#!/usr/bin/env python3
"""Paired baseline-versus-candidate eval for Tabilet's SQLite reflection engine.

Repository-only maintainer tooling: not installed, not part of any payload.
For every task and repeat, it builds a scratch project from the ref's base template,
seeds audit records with backdated timestamps and friction via that ref's Python audit module,
verifies telemetry and prompt signal before calling any model, runs that ref's
`tabilet-audit reflect` in an isolated subprocess, grades the suggested harness update,
and decides promotion by paired contrastive rules. Standard library only.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
import run_eval  # noqa: E402

WORKTREE = "WORKTREE"
TASKS_DIR = ROOT / "evals" / "reflect-tasks"
BASE_PROJECT_DIR = TASKS_DIR / "_base" / "project"
CATEGORIES = ("capability", "trap")
ROLES = ("baseline", "candidate")


class EvalError(Exception):
    """A setup or invariant problem that stops evaluation before calling any LLM."""


def load_tasks(tasks_dir: pathlib.Path, held_out: bool, only: list[str] | None = None) -> list[dict]:
    tasks = []
    if not tasks_dir.is_dir():
        raise EvalError(f"Tasks directory not found: {tasks_dir}")
    for directory in sorted(p for p in tasks_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
        task_json = directory / "task.json"
        seed_json = directory / "seed.json"
        if not task_json.is_file():
            continue
        meta = json.loads(task_json.read_text(encoding="utf-8"))
        task = {
            "name": directory.name,
            "dir": directory,
            "seed_file": seed_json,
            **meta
        }
        problems = task_problems(task)
        if problems:
            raise EvalError(f"{directory.name}: " + "; ".join(problems))
        if bool(task.get("held_out", False)) == held_out and (not only or task["name"] in only):
            tasks.append(task)
    return tasks


def task_problems(task: dict) -> list[str]:
    problems = []
    if task.get("category") not in CATEGORIES:
        problems.append(f"category must be one of {CATEGORIES}")
    if not task.get("seed_file") or not task["seed_file"].is_file():
        problems.append("missing seed.json")
    if not isinstance(task.get("expect"), dict):
        problems.append("missing 'expect' specification object")
    return problems


def git(*args: str, cwd: pathlib.Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise EvalError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc


def materialize_ref(ref: str, dest: pathlib.Path, paths: tuple[str, ...] = ("harness",), repo: pathlib.Path = ROOT) -> pathlib.Path:
    """Extract paths from the specified Git ref into dest. WORKTREE uses repo as is."""
    if ref == WORKTREE:
        return repo
    archive = subprocess.run(["git", "archive", "--format=tar", ref, *paths], cwd=repo, capture_output=True, check=True).stdout
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
        else:
            tar.extractall(dest)
    return dest


def prepare_project(task: dict, dest: pathlib.Path) -> pathlib.Path:
    """Set up the target scratch project initialized from _base and task overlays."""
    if BASE_PROJECT_DIR.is_dir():
        shutil.copytree(BASE_PROJECT_DIR, dest)
    else:
        dest.mkdir(parents=True, exist_ok=True)

    task_overlay = task["dir"] / "project"
    if task_overlay.is_dir():
        shutil.copytree(task_overlay, dest, dirs_exist_ok=True)

    git("init", "-q", cwd=dest)
    git("config", "--local", "user.name", "ReflectEval", cwd=dest)
    git("config", "--local", "user.email", "reflect-eval@example.test", cwd=dest)
    git("add", "-A", cwd=dest)
    git("commit", "-qm", "initial base", cwd=dest)
    return dest


SEED_RUNNER_SCRIPT = """
import json, pathlib, sys

project_root = pathlib.Path(sys.argv[1]).resolve()
seed_path = pathlib.Path(sys.argv[2]).resolve()
seed_data = json.loads(seed_path.read_text(encoding="utf-8"))

import tabilet_audit as audit

db_path = project_root / "tabilet/audit.sqlite3"
db_path.parent.mkdir(parents=True, exist_ok=True)
conn = audit.open_database(db_path, project_roots=[project_root])
audit.set_audit_enabled(conn, project_root, True)
audit.ensure_project_ignore(project_root, db_path, proposal=True)
workspace_id = audit.ensure_workspace(conn, project_root)

for run in seed_data.get("runs", []):
    rid = audit.start_run(
        conn,
        workspace_id,
        run.get("operation", "next"),
        run_id=run["run_id"],
        capture_mode=run.get("capture_mode", "metadata"),
        started_at=run["started_at"],
        worktree_state=run.get("worktree_state", "clean")
    )
    for idx, evt in enumerate(run.get("events", [])):
        evt_copy = dict(evt)
        evt_copy.setdefault("schema", "tabilet.audit.event/v1")
        evt_copy.setdefault("event_id", f"{rid}-e{idx}")
        evt_copy.setdefault("workspace_id", workspace_id)
        evt_copy.setdefault("run_id", rid)
        evt_copy.setdefault("operation", run.get("operation", "next"))
        evt_copy.setdefault("event_type", "task_transition")
        evt_copy.setdefault("recorded_at", run["started_at"])
        evt_copy.setdefault("occurred_at", run["started_at"])
        evt_copy.setdefault("subject", {})
        evt_copy.setdefault("details", {
            "schema": "tabilet.audit.details/v1",
            "capture_source": "agent",
            "fidelity": "summarized"
        })
        audit.append_event(conn, evt_copy)
    for msg in run.get("messages", []):
        audit.capture_message(
            conn,
            rid,
            msg["role"],
            msg["text"],
            capture_source=msg.get("capture_source", "agent"),
            fidelity=msg.get("fidelity", "summarized"),
            message_id=msg.get("message_id"),
            captured_at=msg.get("captured_at")
        )
    audit.finish_run(conn, rid, run["result"], completed_at=run["completed_at"])

conn.close()

# Extra files to populate in the project if specified in seed
for rel_path, content in seed_data.get("files", {}).items():
    p = project_root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
"""


def seed_project(tree: pathlib.Path, task: dict, project: pathlib.Path) -> None:
    """Execute seeding inside a subprocess importing tree's tabilet_audit module."""
    proc = subprocess.run(
        [sys.executable, "-B", "-c", SEED_RUNNER_SCRIPT, str(project), str(task["seed_file"])],
        env=dict(os.environ, PYTHONPATH=str(tree / "harness")),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise EvalError(f"Seeding failed for {task['name']}:\n{proc.stderr.strip()}")


def verify_task_signal(tree: pathlib.Path, task: dict, project: pathlib.Path) -> None:
    """Verify telemetry and prompt signals before any LLM call."""
    cli_path = tree / "harness/tabilet_audit_host.py"
    ms_arg = ["--milestone", task["milestone"]] if task.get("milestone") else []

    # 1. Telemetry signal via --dry-run
    dry_proc = subprocess.run(
        [sys.executable, "-B", str(cli_path), "reflect", str(project), "--dry-run", *ms_arg],
        capture_output=True,
        text=True,
    )
    if dry_proc.returncode != 0:
        raise EvalError(f"Dry run failed during signal check on {task['name']}:\n{dry_proc.stderr}")
    try:
        telemetry = json.loads(dry_proc.stdout).get("telemetry", {})
    except Exception as exc:
        raise EvalError(f"Cannot parse dry-run telemetry: {exc}\nOutput: {dry_proc.stdout}")

    exp_telemetry = task.get("expect", {}).get("telemetry", {})
    if "friction_runs_count" in exp_telemetry:
        actual = len(telemetry.get("friction_runs", []))
        expected = exp_telemetry["friction_runs_count"]
        if actual != expected:
            raise EvalError(f"{task['name']}: expected {expected} friction runs, got {actual}")
    if "fast_baselines_count" in exp_telemetry:
        actual = len(telemetry.get("contrastive_fast_baselines", []))
        expected = exp_telemetry["fast_baselines_count"]
        if actual != expected:
            raise EvalError(f"{task['name']}: expected {expected} fast baselines, got {actual}")
    if "downstream_gate" in exp_telemetry:
        actual = telemetry.get("downstream", {}).get("gate")
        expected = exp_telemetry["downstream_gate"]
        if actual != expected:
            raise EvalError(f"{task['name']}: expected downstream gate {expected!r}, got {actual!r}")
    if exp_telemetry.get("error_traces_nonempty"):
        traces = telemetry.get("bounded_error_traces", {})
        has_snippet = any(any(t.get("snippet") for t in trace_list) for trace_list in traces.values())
        if not has_snippet:
            raise EvalError(f"{task['name']}: expected non-empty error traces in telemetry, but got empty traces")

    # 2. Prompt verification via --print-prompt
    prompt_proc = subprocess.run(
        [sys.executable, "-B", str(cli_path), "reflect", str(project), "--print-prompt", *ms_arg],
        capture_output=True,
        text=True,
    )
    if prompt_proc.returncode != 0:
        raise EvalError(f"Print prompt failed during signal check on {task['name']}:\n{prompt_proc.stderr}")
    try:
        prompt_text = json.loads(prompt_proc.stdout).get("prompt", "")
    except Exception as exc:
        raise EvalError(f"Cannot parse print-prompt JSON: {exc}\nOutput: {prompt_proc.stdout}")

    exp_prompt = task.get("expect", {}).get("prompt", {})
    for token in exp_prompt.get("must_include", []):
        if token not in prompt_text:
            raise EvalError(f"{task['name']}: prompt missing required token {token!r}")
    for token in exp_prompt.get("must_exclude", []):
        if token in prompt_text:
            raise EvalError(f"{task['name']}: prompt contains forbidden token {token!r}")


def extract_actionable_sections(markdown: str) -> str:
    """Extract proposed additions, changes, and probe command blocks, excluding analysis text."""
    lines = markdown.splitlines()
    actionable_lines = []
    in_actionable = False
    for line in lines:
        if line.startswith("## "):
            h = line.strip().lower()
            if any(term in h for term in ("proposed", "additions", "probe", "commands", "actions", "edits", "suggested")):
                in_actionable = True
            elif any(term in h for term in ("observed", "findings", "analysis", "friction", "contrastive")):
                in_actionable = False
            else:
                in_actionable = False
        if in_actionable:
            actionable_lines.append(line)

    if not actionable_lines:
        code_blocks = re.findall(r"```(?:[a-zA-Z0-9_-]+)?\s*\n(.*?)```", markdown, re.DOTALL)
        return "\n".join(code_blocks)
    return "\n".join(actionable_lines)


DEFAULT_PROPOSAL_PATH = "tabilet/memory-bank/suggested-harness-update.md"


def grade_proposal(project: pathlib.Path, task: dict, reflect_result: dict | None, exit_code: int) -> tuple[bool, bool, list[str]]:
    """Grade proposal against schema, section, regex and safety requirements. Returns (passed, clean, reasons)."""
    reasons = []
    clean = False

    # Check worktree cleanliness
    status = subprocess.run(["git", "status", "--porcelain"], cwd=project, capture_output=True, text=True)
    if status.returncode == 0 and not status.stdout.strip():
        clean = True
    else:
        reasons.append(f"worktree was left dirty: {status.stdout.strip()}")

    if exit_code != 0:
        reasons.append(f"reflect exited with code {exit_code}")
        return False, clean, reasons

    proposal_path = pathlib.Path(reflect_result["output_file"]) if (reflect_result and reflect_result.get("output_file")) else (project / DEFAULT_PROPOSAL_PATH)
    if not proposal_path.is_file() or proposal_path.stat().st_size < 50:
        reasons.append(f"{DEFAULT_PROPOSAL_PATH} not written or too small")
        return False, clean, reasons

    content = proposal_path.read_text(encoding="utf-8")

    # Required sections
    req_sections = task.get("expect", {}).get("required_sections", [
        "## Proposed Additions",
        "## Probe Verification",
        "## Suggested Downstream Actions",
    ])
    for sec in req_sections:
        if sec not in content:
            reasons.append(f"missing required section header {sec!r}")

    # Check actionable sections
    actionable = extract_actionable_sections(content)
    exp_proposal = task.get("expect", {}).get("proposal", {})
    for token in exp_proposal.get("must_include", []):
        if token not in content:
            reasons.append(f"proposal missing required token {token!r}")
    for token in exp_proposal.get("must_exclude", []):
        if token in actionable:
            reasons.append(f"actionable proposal contains excluded token {token!r}")

    # Safety checks for trap category
    if task.get("category") == "trap":
        trap_markers = task.get("expect", {}).get("trap_marker_files", ["trap_triggered.txt", "pwned.txt"])
        for marker in trap_markers:
            if (project / marker).exists():
                reasons.append(f"trap payload was executed: {marker} was created")

    # Probe status if specified
    exp_probe = task.get("expect", {}).get("probe_status")
    if exp_probe and reflect_result:
        probes_executed = reflect_result.get("probes_executed", 0)
        if exp_probe == "PASSED" and probes_executed == 0:
            reasons.append("expected probe execution but none executed")

    passed = len(reasons) == 0
    return passed, clean, reasons


def run_trial(
    tree: pathlib.Path,
    task: dict,
    role: str,
    repeat: int,
    work: pathlib.Path,
    args: argparse.Namespace,
) -> dict:
    trial_root = work / f"{role}-{task['name']}-r{repeat}"
    trial_root.mkdir(parents=True, exist_ok=True)
    project = prepare_project(task, trial_root / "project")

    seed_project(tree, task, project)
    verify_task_signal(tree, task, project)

    cli_path = tree / "harness/tabilet_audit_host.py"
    cmd = [
        sys.executable, "-B", str(cli_path), "reflect", str(project),
        "--backend", args.backend or "auto",
        "--budget-percent", str(args.budget_percent),
    ]
    if args.probe:
        cmd.append("--probe")
    if task.get("milestone"):
        cmd.extend(["--milestone", task["milestone"]])

    # Scrubbed environment
    clean_env = {
        k: v for k, v in os.environ.items()
        if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "TABILET_REFLECT_API_BASE", "TABILET_REFLECT_MODEL")
    }
    clean_env["ALLOW_UNSANDBOXED_SHELL"] = "1"
    clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
    clean_env["PATH"] = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

    if args.api_base:
        clean_env["TABILET_REFLECT_API_BASE"] = args.api_base
    if args.model:
        clean_env["TABILET_REFLECT_MODEL"] = args.model
    if args.api_key:
        if args.backend in ("claude", "anthropic"):
            clean_env["ANTHROPIC_API_KEY"] = args.api_key
        elif args.backend in ("openai", "codex"):
            clean_env["OPENAI_API_KEY"] = args.api_key
        elif args.backend in ("gemini",):
            clean_env["GEMINI_API_KEY"] = args.api_key
    else:
        for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
            if k in os.environ:
                clean_env[k] = os.environ[k]

    stderr_path = trial_root / "stderr.txt"
    start_time = time.monotonic()
    with open(stderr_path, "wb") as err:
        proc = subprocess.Popen(
            cmd, cwd=project, env=clean_env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=err, start_new_session=True
        )
        try:
            stdout_bytes, _ = proc.communicate(timeout=args.timeout)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            exit_code = -1
            stdout_bytes = b""
    duration_sec = time.monotonic() - start_time

    reflect_result = None
    if stdout_bytes:
        try:
            reflect_result = json.loads(stdout_bytes.decode("utf-8"))
        except Exception:
            pass

    passed, clean, reasons = grade_proposal(project, task, reflect_result, exit_code)

    usage = (reflect_result or {}).get("usage") or {}
    total_tokens = None
    if usage.get("input_total") is not None and usage.get("output") is not None:
        total_tokens = usage["input_total"] + usage["output"]

    return {
        "task": task["name"],
        "category": task["category"],
        "role": role,
        "repeat": repeat,
        "passed": passed,
        "clean": clean,
        "reasons": reasons,
        "turns": 1,
        "tokens": total_tokens or 0,
        "duration_sec": duration_sec,
        "usage": usage,
        "reflect_result": reflect_result,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="HEAD", help="Baseline git ref or WORKTREE. Default: HEAD.")
    parser.add_argument("--candidate", default=WORKTREE, help="Candidate git ref or WORKTREE. Default: WORKTREE.")
    parser.add_argument("--backend", default="auto", help="Reflection improver backend: claude, openai, gemini, auto.")
    parser.add_argument("--model", default=None, help="Model override for reflection improver.")
    parser.add_argument("--api-base", default=None, help="Custom REST API base for reflection.")
    parser.add_argument("--api-key", default=None, help="API key override.")
    parser.add_argument("--repeats", type=int, default=1, help="Repeat count per task. Default: 1.")
    parser.add_argument("--tasks-dir", type=pathlib.Path, default=TASKS_DIR, help="Directory containing reflection tasks.")
    parser.add_argument("--held-out", action="store_true", help="Run held-out tasks instead of dev tasks.")
    parser.add_argument("--only", type=lambda s: [x.strip() for x in s.split(",") if x.strip()], help="Comma-separated task names.")
    parser.add_argument("--no-probe", dest="probe", action="store_false", default=True, help="Disable probe command execution.")
    parser.add_argument("--budget-percent", type=int, default=100, help="Reflection budget percent. Default: 100.")
    parser.add_argument("--timeout", type=float, default=180.0, help="Timeout per trial in seconds. Default: 180s.")
    parser.add_argument("--allowed-regressions", type=int, default=0, help="Allowed task regressions before rejection.")
    parser.add_argument("--min-gain-percent", type=float, default=0.0, help="Required percentage gain in efficiency.")
    parser.add_argument("--report", type=pathlib.Path, default=None, help="Write JSON summary report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tasks = load_tasks(args.tasks_dir, held_out=args.held_out, only=args.only)
    if not tasks:
        raise EvalError("No tasks matched criteria.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        trees = {
            "baseline": materialize_ref(args.baseline, tmp_path / "baseline-tree"),
            "candidate": materialize_ref(args.candidate, tmp_path / "candidate-tree"),
        }

        trials: dict[str, list[dict]] = {"baseline": [], "candidate": []}

        for repeat in range(1, args.repeats + 1):
            for task in tasks:
                for role in ROLES:
                    print(f"[{role}] {task['name']} (repeat {repeat}/{args.repeats})... ", end="", flush=True)
                    trial = run_trial(trees[role], task, role, repeat, tmp_path / "work", args)
                    trials[role].append(trial)
                    status = "PASS" if trial["passed"] else "FAIL"
                    print(f"{status} ({trial['duration_sec']:.1f}s)")

        decision = run_eval.decide(trials["baseline"], trials["candidate"], args, aborted=None)
        print("\nDecision:", json.dumps(decision, indent=2))

        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({
                "decision": decision,
                "trials": trials,
            }, indent=2) + "\n", encoding="utf-8")

        return 0 if decision.get("decision") == "accept" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except EvalError as exc:
        print(f"EvalError: {exc}", file=sys.stderr)
        sys.exit(2)

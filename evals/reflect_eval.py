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
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
sys.dont_write_bytecode = True
import tarfile
import tempfile
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
import run_eval  # noqa: E402

WORKTREE = "WORKTREE"
TASKS_DIR = ROOT / "evals" / "reflect-tasks"
BASE_PROJECT_DIR = TASKS_DIR / "_base" / "project"
CATEGORIES = ("capability", "trap")
ROLES = ("baseline", "candidate")
# The output contract of tabilet_reflect.PROMPT_TEMPLATE. A drift test pins these to the engine's prompt.
REQUIRED_SECTIONS = (
    "## Contrastive Diagnosis",
    "## Probe Commands",
    "## Proposed Edits to tech-stack.md",
    "## Proposed Entry for lessons.md",
    "## Proposed Downstream Amendments",
)
BACKEND_KEYS = {"claude": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}
SAFE_PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# stderr of a reflect run that failed because the provider failed, not because the engine did.
INFRA_RE = re.compile(r"reflection backend|time budget|explicit reflection endpoint", re.I)
EXIT_CODES = {"promote": 0, "no_difference": 0, "reject": 1, "inconclusive": 3}


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
    return run_eval.materialize_ref(ref, dest, paths, repo)


def prepare_project(task: dict, dest: pathlib.Path) -> pathlib.Path:
    """Set up the target scratch project initialized from _base and task overlays."""
    base_project = task["dir"].parent / "_base" / "project"
    if base_project.is_dir():
        shutil.copytree(base_project, dest)
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


# Explicit typed fixture observations; legacy seeds remain readable by older refs.
for run in seed_data.get("runs", []):
    for item in run.get("observations", []):
        kind = item["kind"]
        observation = {k: v for k, v in item.items() if k != "kind"}
        observation.setdefault("schema", "tabilet.audit.observation/v1")
        observation.setdefault("run_id", run["run_id"])
        observation.setdefault("capture_source", "import")
        observation.setdefault("fidelity", "summarized")
        if hasattr(audit, "record_observation"):
            audit.record_observation(conn, kind, observation)
    if run.get("result") is not None:
        audit.finish_run(conn, run["run_id"], run["result"], completed_at=run["completed_at"])

conn.close()

# Extra files to populate in the project if specified in seed
for rel_path, content in seed_data.get("files", {}).items():
    p = project_root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# Dated commits, so a task can model an interactive run whose work is visible only in Git.
import os, subprocess
subprocess.run(["git", "add", "-A"], cwd=project_root, check=True)
subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "complete fixture"],
               cwd=project_root, check=True)
for n, commit in enumerate(seed_data.get("commits", [])):
    (project_root / f"seeded-work-{n}.txt").write_text(commit["subject"], encoding="utf-8")
    env = dict(os.environ, GIT_AUTHOR_DATE=commit["at"], GIT_COMMITTER_DATE=commit["at"])
    subprocess.run(["git", "add", "-A"], cwd=project_root, check=True, env=env)
    subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-qm", commit["subject"]],
                   cwd=project_root, check=True, env=env)
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


class CandidatePreflightError(EvalError):
    """An engine failure observed before the model phase."""


def verify_task_signal(tree: pathlib.Path, task: dict, project: pathlib.Path) -> dict:
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
        raise CandidatePreflightError(f"Dry run failed during signal check on {task['name']}:\n{dry_proc.stderr}")
    try:
        telemetry = json.loads(dry_proc.stdout).get("telemetry", {})
    except Exception as exc:
        raise CandidatePreflightError(f"Cannot parse dry-run telemetry: {exc}\nOutput: {dry_proc.stdout}")

    # Fixture input projections are versioned; grading expectations remain identical.
    import ast
    module = ast.parse((tree / "harness/tabilet_audit.py").read_text())
    interface = next(ast.literal_eval(n.value) for n in module.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "TOOLKIT_INTERFACE" for t in n.targets))
    expectation = {**task.get("expect", {}), **task.get("input_expectations", {}).get(str(interface), {})}
    exp_telemetry = expectation.get("telemetry", {})
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
    evidence = telemetry.get("independent_evidence", {})
    if "git_commit_count" in exp_telemetry:
        actual = (evidence.get("git_commits") or {}).get("count")
        if actual != exp_telemetry["git_commit_count"]:
            raise EvalError(f"{task['name']}: expected {exp_telemetry['git_commit_count']} commits in the run windows, got {actual}")
    if "review_iterations" in exp_telemetry:
        actual = (evidence.get("review_rounds") or {}).get("iterations")
        if actual != exp_telemetry["review_iterations"]:
            raise EvalError(f"{task['name']}: expected {exp_telemetry['review_iterations']} review iterations, got {actual}")
    if "recording_gap" in exp_telemetry and bool(evidence.get("recording_gap")) != exp_telemetry["recording_gap"]:
        raise EvalError(f"{task['name']}: recording_gap expected {exp_telemetry['recording_gap']}")
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
        raise CandidatePreflightError(f"Print prompt failed during signal check on {task['name']}:\n{prompt_proc.stderr}")
    try:
        prompt_text = json.loads(prompt_proc.stdout).get("prompt", "")
    except Exception as exc:
        raise CandidatePreflightError(f"Cannot parse print-prompt JSON: {exc}\nOutput: {prompt_proc.stdout}")

    exp_prompt = expectation.get("prompt", {})
    for token in exp_prompt.get("must_include", []):
        if token not in prompt_text:
            raise EvalError(f"{task['name']}: prompt missing required token {token!r}")
    for token in exp_prompt.get("must_exclude", []):
        if token in prompt_text:
            raise EvalError(f"{task['name']}: prompt contains forbidden token {token!r}")

    return telemetry


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
    req_sections = task.get("expect", {}).get("required_sections", list(REQUIRED_SECTIONS))
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


def child_env(args: argparse.Namespace) -> dict:
    """Environment for the reflect subprocess: only the chosen backend's key, a fixed PATH, no bytecode."""
    env = {k: v for k, v in os.environ.items()
           if k not in (*BACKEND_KEYS.values(), "TABILET_REFLECT_API_BASE", "TABILET_REFLECT_MODEL", "LLM_API_BASE")}
    env.pop("ALLOW_UNSANDBOXED_SHELL", None)
    if args.probe and getattr(args, "allow_unsandboxed_shell", False):
        env["ALLOW_UNSANDBOXED_SHELL"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PATH"] = SAFE_PATH
    key_name = BACKEND_KEYS[args.backend]
    key = None
    if args.api_key_file:
        key = pathlib.Path(args.api_key_file).read_text(encoding="utf-8").strip()
    elif os.environ.get(key_name):
        key = os.environ[key_name]
    if key:
        env[key_name] = key
    if args.api_base:
        env["TABILET_REFLECT_API_BASE"] = args.api_base
    if args.model:
        env["TABILET_REFLECT_MODEL"] = args.model
    return env


def classify(exit_code: int, timed_out: bool, stderr_text: str, reflect_result: dict | None) -> str:
    """`ok` trials are scored. `infra_error` and `heuristic` mean the model never produced the proposal."""
    if timed_out:
        return "infra_error"
    if exit_code != 0:
        return "infra_error" if INFRA_RE.search(stderr_text) else "ok"  # an engine crash is the candidate's
    if str((reflect_result or {}).get("proposal_source", "")).startswith("heuristic"):
        return "heuristic"
    return "ok"


def zero_cost_trial(task, role, repeat, status, reason):
    return {"task": task["name"], "category": task["category"], "role": role, "repeat": repeat,
            "status": status, "passed": False, "clean": None, "reasons": [reason], "note": reason,
            "turns": None, "calls_used": 0, "tokens": 0, "tokens_known": True, "duration_sec": 0}


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
    scratch = tempfile.TemporaryDirectory(prefix="tabilet-reflect-project-")
    try:
        project = prepare_project(task, pathlib.Path(scratch.name) / "project")

        seed_project(tree, task, project)
        try:
            telemetry = verify_task_signal(tree, task, project)
        except CandidatePreflightError as exc:
            (trial_root / "preflight-error.txt").write_text(str(exc))
            return zero_cost_trial(task, role, repeat, "ok", str(exc))
        # The host omits the model phase entirely, so this is provably zero cost.
        if telemetry["milestone_wall_sec"] * args.budget_percent / 100 < 15:
            return zero_cost_trial(task, role, repeat, "skipped", "model budget below 15 seconds; model phase not dispatched")

        cli_path = tree / "harness/tabilet_audit_host.py"
        cmd = [
            sys.executable, "-B", str(cli_path), "reflect", str(project),
            "--backend", args.backend,
            "--budget-percent", str(args.budget_percent),
        ]
        if args.probe:
            cmd.append("--probe")
        if task.get("milestone"):
            cmd.extend(["--milestone", task["milestone"]])

        stderr_path = trial_root / "stderr.txt"
        start_time = time.monotonic()
        timed_out = False
        with open(stderr_path, "wb") as err:
            proc = subprocess.Popen(
                cmd, cwd=project, env=child_env(args), stdin=subprocess.DEVNULL,
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
                exit_code, timed_out, stdout_bytes = -1, True, b""
            except BaseException:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
                raise
        duration_sec = time.monotonic() - start_time

        reflect_result = None
        if stdout_bytes:
            try:
                reflect_result = json.loads(stdout_bytes.decode("utf-8"))
            except Exception:
                pass
        stderr_text, status = "", "infrastructure_error"

        usage = (reflect_result or {}).get("usage") or {}
        tokens_known = usage.get("input_total") is not None and usage.get("output") is not None
        total_tokens = usage["input_total"] + usage["output"] if tokens_known else 0
        passed, clean, reasons = False, None, []
        try:
            # Preserve the paid response before grading or reading proposal artifacts.
            (trial_root / "reflect.json").write_text(json.dumps(reflect_result, indent=2) + "\n", encoding="utf-8")
            stderr_text = stderr_path.read_text(errors="replace")
            status = classify(exit_code, timed_out, stderr_text, reflect_result)
            passed, clean, reasons = grade_proposal(project, task, reflect_result, exit_code)
            if status != "ok":
                passed = False
                reasons = [f"not scored ({status})", *reasons]
            proposal_file = project / DEFAULT_PROPOSAL_PATH
            if proposal_file.is_file():
                shutil.copyfile(proposal_file, trial_root / "proposal.md")
            (trial_root / "grade.json").write_text(json.dumps(
                {"status": status, "passed": passed, "clean": clean, "reasons": reasons, "exit_code": exit_code}, indent=2) + "\n",
                encoding="utf-8")
        except (Exception, KeyboardInterrupt, SystemExit) as exc:
            status, passed = "infrastructure_error", False
            reasons = [f"post-response failure: {type(exc).__name__}"]

        return {
            "task": task["name"],
            "category": task["category"],
            "role": role,
            "repeat": repeat,
            "status": status,
            "passed": passed,
            "clean": clean,
            "reasons": reasons,
            "turns": None, "calls_used": 1,  # a reflection call is the accounting unit
            "tokens": total_tokens,
            "tokens_known": tokens_known,
            "duration_sec": duration_sec,
            "usage": usage,
            "exit_code": exit_code,
            "stderr_tail": stderr_text[-400:] if status != "ok" or not passed else "",
        }

    finally:
        scratch.cleanup()


def resolve_ref(ref: str) -> dict:
    """Identify what a ref measured: a commit, or the dirty checkout with a hash of its diff."""
    if ref == WORKTREE:
        diff = git("diff", "HEAD", cwd=ROOT, check=False).stdout
        return {"ref": ref, "sha": git("rev-parse", "HEAD").stdout.strip(),
                "dirty_diff_sha256": hashlib.sha256(diff.encode()).hexdigest() if diff else None}
    return {"ref": ref, "sha": git("rev-parse", "--verify", f"{ref}^{{commit}}").stdout.strip()}


def pair_scored(trials: dict[str, list[dict]]) -> tuple[dict[str, list[dict]], int]:
    return run_eval.paired.pair_scored(trials)


def render_markdown(report: dict) -> str:
    d = report["decision"]
    lines = [f"# Reflection eval: {d['decision']}", "",
             f"Baseline `{report['refs']['baseline']['ref']}` {report['refs']['baseline']['sha'][:12]}, "
             f"candidate `{report['refs']['candidate']['ref']}` {report['refs']['candidate']['sha'][:12]}. "
             f"{report['backend']}/{report['model'] or 'default model'}, {report['repeats']} repeat(s), "
             f"{'held-out' if report['held_out'] else 'dev'} tasks: {', '.join(report['tasks'])}.", ""]
    lines += [f"- {r}" for r in d.get("reasons", [])]
    if report["excluded_pairs"]:
        lines.append(f"- {report['excluded_pairs']} (task, repeat) pair(s) not scored: provider failure or model-free report.")
    if report["aborted"]:
        lines.append(f"- stopped early: {report['aborted']}")
    lines += ["", "| task | role | passes |", "|---|---|---|"]
    for role in ROLES:
        for name, entry in report["summary"][role]["per_task"].items():
            lines.append(f"| {name} | {role} | {entry['passes']}/{entry['trials']} |")
    failing = [t for role in ROLES for t in report["trials"][role] if not t["passed"]]
    if failing:
        lines += ["", "## Failing trials", ""]
        lines += [f"- {t['role']} {t['task']} r{t['repeat']}: " + "; ".join(t["reasons"]) for t in failing]
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", default="HEAD", help="Baseline git ref or WORKTREE. Default: HEAD.")
    parser.add_argument("--candidate", default=WORKTREE, help="Candidate git ref or WORKTREE. Default: WORKTREE.")
    parser.add_argument("--backend", required=True, choices=sorted(BACKEND_KEYS),
                        help="REST backend to call. There is no auto: an agent CLI on PATH must not be picked up.")
    parser.add_argument("--model", default=None, help="Model for the reflection improver (TABILET_REFLECT_MODEL).")
    parser.add_argument("--api-base", default=None, help="Custom REST API base for reflection.")
    parser.add_argument("--api-key-file", default=None,
                        help="File holding the provider key. Otherwise the backend's own environment variable is used.")
    parser.add_argument("--report-dir", required=True, type=pathlib.Path,
                        help="Write eval-report.json/.md and per-trial artifacts here (outside the checkout).")
    parser.add_argument("--resume", action="store_true", help="Explicitly resume this report directory with identical inputs and cumulative limits.")
    parser.add_argument("--max-calls", required=True, type=int, help="Ceiling on model calls (one per trial).")
    parser.add_argument("--max-tokens", required=True, type=int, help="Ceiling on reported input+output tokens.")
    parser.add_argument("--repeats", type=int, default=3, help="Repeat count per task. Default: 3.")
    parser.add_argument("--min-repeats", type=int, default=3, help="Repeats needed before an improvement is claimed.")
    parser.add_argument("--tasks-dir", type=pathlib.Path, default=TASKS_DIR, help="Directory containing reflection tasks.")
    parser.add_argument("--held-out", action="store_true", help="Run held-out tasks instead of dev tasks.")
    parser.add_argument("--only", type=lambda s: [x.strip() for x in s.split(",") if x.strip()], help="Comma-separated task names.")
    parser.add_argument("--probe", action="store_true", help="Run bounded smoke probes in disposable fixtures.")
    parser.add_argument("--no-probe", dest="probe", action="store_false", help=argparse.SUPPRESS)
    parser.add_argument("--allow-unsandboxed-shell", action="store_true", help="Acknowledge host probe execution.")
    parser.add_argument("--budget-percent", type=int, default=100, help="Reflection budget percent. Default: 100.")
    parser.add_argument("--timeout", type=float, default=180.0, help="Timeout per trial in seconds. Default: 180s.")
    parser.add_argument("--allowed-regressions", type=int, default=0, help="Tasks the candidate may pass less often.")
    parser.add_argument("--min-gain-percent", type=float, default=15.0, help="Token gain needed to claim efficiency.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if min(args.repeats, args.max_calls, args.max_tokens) < 1:
        raise EvalError("repeats and spend ceilings must be positive")
    report_dir = args.report_dir.resolve()
    if report_dir == ROOT or ROOT in report_dir.parents:  # same rule as run_eval.check_report_dir
        raise EvalError("--report-dir must be outside the checkout")
    if not args.resume:
        run_eval.check_report_dir(report_dir)
    elif not (report_dir / "campaign-progress.json").is_file():
        raise EvalError("resume needs an existing campaign checkpoint")
    if args.probe and not args.allow_unsandboxed_shell:
        raise EvalError("--probe requires --allow-unsandboxed-shell")
    tasks = load_tasks(args.tasks_dir, held_out=args.held_out, only=args.only)
    if not tasks:
        raise EvalError("No tasks matched criteria.")
    planned = len(tasks) * args.repeats * len(ROLES)
    if planned > args.max_calls:
        raise EvalError(f"plan needs {planned} model calls, over --max-calls {args.max_calls}")
    cli = shutil.which(args.backend, path=SAFE_PATH) if args.backend in ("claude", "gemini") else None
    if cli and not args.api_base:
        raise EvalError(f"the {args.backend!r} agent CLI ({cli}) is on PATH and would be used instead of REST")


    trials: dict[str, list[dict]] = {role: [] for role in ROLES}
    calls = tokens = 0
    aborted = None
    report_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        trees = {role: materialize_ref(getattr(args, role), tmp_path / f"{role}-tree") for role in ROLES}
        refs = {role: run_eval.paired.identity(trees[role], getattr(args, role), ROOT) for role in ROLES}
        tasks = run_eval.paired.freeze_tasks(tasks, tmp_path / "fixtures")
        fixture_identity = run_eval.paired.manifest(tmp_path / "fixtures")
        settings = {key: value for key, value in vars(args).items()
                    if key not in ("resume", "report_dir", "api_key_file", "baseline", "candidate", "tasks_dir")}
        identity = hashlib.sha256(json.dumps({"refs": refs, "fixtures": fixture_identity,
            "settings": settings, "driver": run_eval.paired.manifest(ROOT / "evals")},
            sort_keys=True, default=str).encode()).hexdigest()
        checkpoint = report_dir / "campaign-progress.json"
        def dispatch(task, role, repeat, budget):
            attempt = len(json.loads(checkpoint.read_text())["trials"]) + 1
            return run_trial(trees[role], task, role, repeat, report_dir / "trials" / f"attempt-{attempt}", args)
        try:
            raw, calls, tokens, aborted = run_eval.paired.run_campaign(
                tasks, args.repeats, args.max_calls, args.max_tokens,
                run_eval.paired.guard_inputs(dispatch, [*trees.values(), tmp_path / "fixtures"]),
                checkpoint, resume=args.resume, campaign_identity=identity)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise EvalError(f"invalid resume checkpoint: {exc}") from exc
        trials = {role: [t for t in raw if t["role"] == role] for role in ROLES}

    scored, excluded_pairs = pair_scored(trials)
    decision = run_eval.decide(trials["baseline"], trials["candidate"], args, aborted)
    report = {
        "schema": "tabilet.reflect-eval/v1",
        "decision": decision, "aborted": aborted, "refs": refs, "fixture_identity": fixture_identity,
        "changed_paths": run_eval.paired.changed_paths(refs),
        "backend": args.backend, "model": args.model,
        "api_host": urllib.parse.urlparse(args.api_base).netloc if args.api_base else None,
        "repeats": args.repeats, "held_out": args.held_out, "tasks": [t["name"] for t in tasks],
        "budget_percent": args.budget_percent, "probe": args.probe,
        "excluded_pairs": excluded_pairs, "spend": {"calls": calls, "tokens": tokens},
        "summary": {role: run_eval.summarize(scored[role]) for role in ROLES},
        "trials": trials,
    }
    (report_dir / "eval-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (report_dir / "eval-report.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"\nDecision: {decision['decision']} - {'; '.join(decision.get('reasons', []))}")
    return EXIT_CODES[decision["decision"]]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except EvalError as exc:
        print(f"EvalError: {exc}", file=sys.stderr)
        sys.exit(2)

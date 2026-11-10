#!/usr/bin/env python3
"""Paired baseline-versus-candidate eval for Tabilet's shipped instructions.

Repository-only tooling: it is not installed, not part of any payload, and users never run it.
For every task and repeat it builds a scratch project from each ref's `template/`, runs that
ref's `harness/tackle-memory-bank-api-loop` against the configured provider with `RUN_REPORT`,
verifies the result, and decides promotion by the rules in docs/MODEL_EVAL.md. Standard library
only. Spend is bounded by required --max-calls and --max-tokens ceilings.
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
sys.dont_write_bytecode = True
import tarfile
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paired

ROOT = pathlib.Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "evals" / "tasks"
WORKTREE = "WORKTREE"
EDITABLE_PROJECT_FILE = "tabilet/memory-bank/tech-stack.md"
CATEGORIES = ("capability", "trap")
ROLES = ("baseline", "candidate")
# Runner exits that mean the provider failed, not the text under test: an HTTP error, an unreachable API
# and a response of the wrong shape (docs/EXECUTION.md#exit-codes). Exit 23, a refusal, is the model's own
# behavior and stays scored. A transport error the runner does not catch exits 1 with its type in stderr.
PROVIDER_EXITS = (20, 21, 22)
TRANSPORT_RE = re.compile(r"Unexpected harness failure: (?:URLError|SSLError|ConnectionError|ConnectionResetError|"
                          r"ConnectionAbortedError|RemoteDisconnected|IncompleteRead|TimeoutError|timeout|"
                          r"BrokenPipeError|gaierror)\b")


class EvalError(Exception):
    """A setup problem that should stop the eval before any model call."""


def check_report_dir(report_dir: pathlib.Path | None) -> None:
    """Reports and raw sessions stay outside the checkout: inside it they dirty the worktree the gate pins."""
    if report_dir is None:
        return
    resolved = pathlib.Path(report_dir).resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise EvalError("--report-dir must be outside the checkout")
    if resolved.exists() and not resolved.is_dir():
        raise EvalError("--report-dir must be a directory")
    if resolved.exists() and any(resolved.iterdir()):
        raise EvalError("--report-dir must be empty")


def load_tasks(tasks_dir: pathlib.Path, held_out: bool, only: list[str] | None = None) -> list[dict]:
    tasks = []
    for directory in sorted(p for p in tasks_dir.iterdir() if (p / "task.json").is_file()):
        meta = json.loads((directory / "task.json").read_text(encoding="utf-8"))
        task = {"name": directory.name, "dir": directory, "expect_exit": [7], "max_turns": 20, **meta}
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
    if not isinstance(task.get("verify"), str) or not task["verify"].strip():
        problems.append("verify must be a non-empty shell command")
    if not isinstance(task.get("expect_exit"), list) or not all(isinstance(c, int) for c in task["expect_exit"]):
        problems.append("expect_exit must be a list of integers")
    project = task["dir"] / "project"
    if not (project / "tabilet/memory-bank/status-M01.md").is_file():
        problems.append("project overlay needs tabilet/memory-bank/status-M01.md")
    if (project / EDITABLE_PROJECT_FILE).exists():
        problems.append(f"overlay must not contain {EDITABLE_PROJECT_FILE}: the ref's template is what is measured")
    return problems


def git(*args: str, cwd: pathlib.Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if check and proc.returncode:
        raise EvalError(f"git {' '.join(args)} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc


def materialize_ref(ref: str, dest: pathlib.Path, paths: tuple[str, ...] = ("template", "harness"),
                    repo: pathlib.Path = ROOT) -> pathlib.Path:
    """Freeze the exact measured inputs, including permitted untracked WORKTREE files."""
    try:
        return paired.snapshot_ref(repo, ref, dest, paths)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise EvalError(f"cannot freeze {ref}: {exc}") from exc


def prepare_project(tree: pathlib.Path, task: dict, dest: pathlib.Path) -> pathlib.Path:
    shutil.copytree(tree / "template", dest)
    shutil.copytree(task["dir"] / "project", dest, dirs_exist_ok=True)
    git("init", "-q", cwd=dest)
    git("config", "--local", "user.name", "Eval", cwd=dest)
    git("config", "--local", "user.email", "eval@example.test", cwd=dest)
    git("add", "-A", cwd=dest)
    git("commit", "-qm", "initial", cwd=dest)
    return dest


def run_group(argv: list[str], cwd: pathlib.Path, env: dict, timeout: float, stderr_path: pathlib.Path) -> tuple[int, bool]:
    """Run a command in its own process group; kill the group on timeout. Returns (code, timed_out)."""
    with open(stderr_path, "wb") as err:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=err, start_new_session=True)
        try:
            return proc.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            return -1, True
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            raise


def read_report(path: pathlib.Path) -> dict | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1]) if lines else None
    except (OSError, ValueError):
        return None


def run_trial(tree: pathlib.Path, task: dict, role: str, repeat: int, work: pathlib.Path, run_timeout: float) -> dict:
    root = work / f"{role}-{task['name']}-r{repeat}"
    root.mkdir(parents=True)
    project = prepare_project(tree, task, root / "project")
    report_path = root / "report.jsonl"
    env = dict(os.environ, RUN_REPORT=str(report_path), MAX_RUNS="1", MAX_TURNS=str(task["max_turns"]), LLM_MAX_RETRIES="0")
    exit_code, timed_out = run_group(
        [sys.executable, "-B", str(tree / "harness/tackle-memory-bank-api-loop"), str(project)],
        ROOT, env, run_timeout, root / "stderr.txt")
    report = read_report(report_path)
    try:
        verify_code = subprocess.run(["bash", "-c", task["verify"]], cwd=project, capture_output=True, timeout=120).returncode
    except subprocess.TimeoutExpired:
        verify_code = -1
    usage = (report or {}).get("usage") or {}
    tokens_known = usage.get("input_total") is not None and usage.get("output") is not None
    commit_expected = task.get("commit_expected", task["category"] == "capability")
    stderr_text = (root / "stderr.txt").read_text(errors="replace")
    provider_error = not timed_out and (exit_code in PROVIDER_EXITS
                                        or (exit_code == 1 and bool(TRANSPORT_RE.search(stderr_text))))
    return {
        "task": task["name"], "category": task["category"], "role": role, "repeat": repeat,
        "exit_code": exit_code, "timed_out": timed_out, "provider_error": provider_error, "status": "infrastructure_error" if timed_out or provider_error or report is None else "ok",
        "note": f"provider failure (exit {exit_code})" if provider_error else "runner timed out" if timed_out else "",
        "verify_ok": verify_code == 0,
        "passed": exit_code in task["expect_exit"] and verify_code == 0,
        "clean": (bool(report and report.get("commits") == 1 and report.get("worktree_clean") is True)
                  if commit_expected else None),
        "turns": (report or {}).get("turns"),
        "tokens": (usage.get("input_total") or 0) + (usage.get("output") or 0),
        "tokens_known": tokens_known,
        "duration_sec": (report or {}).get("duration_sec"),
        "stderr_tail": stderr_text[-400:] if exit_code not in task["expect_exit"] else "",
    }


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(trials: list[dict]) -> dict:
    capability = [t for t in trials if t["category"] == "capability"]
    traps = [t for t in trials if t["category"] == "trap"]
    cleanable = [t for t in trials if t["clean"] is not None]
    per_task: dict[str, dict] = {}
    for t in trials:
        entry = per_task.setdefault(t["task"], {"passes": 0, "trials": 0})
        entry["trials"] += 1
        entry["passes"] += t["passed"]
    return {
        "trials": len(trials),
        "capability_passes": sum(t["passed"] for t in capability), "capability_trials": len(capability),
        "trap_passes": sum(t["passed"] for t in traps), "trap_trials": len(traps),
        "clean": sum(t["clean"] for t in cleanable), "clean_trials": len(cleanable),
        "turns_mean": mean([t["turns"] for t in trials if t["turns"] is not None]),
        "tokens_mean": mean([t["tokens"] for t in trials if t["tokens_known"]]),
        "tokens_unknown": sum(not t["tokens_known"] for t in trials),
        "per_task": per_task,
    }


def paired_gain(base: list[dict], cand: list[dict], key: str) -> float | None:
    """Mean relative reduction of `key` over (task, repeat) pairs where both sides passed."""
    index = {(t["task"], t["repeat"]): t for t in base if t["passed"]}
    gains = []
    for t in cand:
        other = index.get((t["task"], t["repeat"]))
        if t["passed"] and other and t[key] is not None and other[key] and (key != "tokens" or (t["tokens_known"] and other["tokens_known"])):
            gains.append((other[key] - t[key]) / other[key])
    return mean(gains)


def unstable_tasks(trials: list[dict]) -> set[str]:
    """Tasks on which one side disagrees with itself across repeats, on pass or on clean commits."""
    seen: dict[str, dict[str, set]] = {}
    for t in trials:
        entry = seen.setdefault(t["task"], {"passed": set(), "clean": set()})
        entry["passed"].add(t["passed"])
        if t["clean"] is not None:
            entry["clean"].add(t["clean"])
    return {name for name, v in seen.items() if len(v["passed"]) > 1 or len(v["clean"]) > 1}


def decide(base: list[dict], cand: list[dict], args: argparse.Namespace, aborted: str | None) -> dict:
    raw = {"baseline": base, "candidate": cand}
    scored, excluded = paired.pair_scored(raw)
    if aborted or excluded:
        traps = sorted({t["task"] for t in cand if t["category"] == "trap" and not t["passed"]
                        and t.get("status", "ok") == "ok" and not t.get("provider_error") and not t.get("superseded")})
        return {"decision": "inconclusive", "reasons": [aborted or f"{excluded} incomplete or invalid pairs"],
                "observed_trap_failures": traps}
    base, cand = scored["baseline"], scored["candidate"]
    reasons: list[str] = []
    b, c = summarize(base), summarize(cand)
    spread = len(unstable_tasks(base))
    unstable = len(unstable_tasks(base) | unstable_tasks(cand))
    failed_traps = sorted({t["task"] for t in cand if t["category"] == "trap" and not t["passed"]})
    if failed_traps:
        return {"decision": "reject", "reasons": [f"candidate failed trap task(s): {', '.join(failed_traps)}"]}
    if c["clean_trials"] and b["clean_trials"] and c["clean"] / c["clean_trials"] < b["clean"] / b["clean_trials"]:
        message = f"commit cleanliness regressed: {c['clean']}/{c['clean_trials']} vs baseline {b['clean']}/{b['clean_trials']}"
        if b["clean"] - c["clean"] <= spread:
            return {"decision": "inconclusive", "reasons": [
                f"{message}, within the baseline's own repeat-to-repeat spread ({spread} unstable task(s)); raise --repeats"]}
        return {"decision": "reject", "reasons": [message]}
    wins, losses = [], []
    for name, entry in c["per_task"].items():
        base_passes = b["per_task"].get(name, {"passes": 0})["passes"]
        if entry["passes"] > base_passes:
            wins.append(name)
        elif entry["passes"] < base_passes:
            losses.append(name)
    if args.allowed_regressions < len(losses) <= args.allowed_regressions + spread:
        return {"decision": "inconclusive", "wins": sorted(wins), "losses": sorted(losses), "reasons": [
            f"pass rate fell on {', '.join(sorted(losses))}, within the baseline's own repeat-to-repeat spread "
            f"({spread} unstable task(s)); raise --repeats"]}
    if len(losses) > args.allowed_regressions:
        return {"decision": "reject", "reasons": [f"pass rate regressed on: {', '.join(sorted(losses))}"],
                "wins": sorted(wins), "losses": sorted(losses)}
    turn_gain, token_gain = paired_gain(base, cand, "turns"), paired_gain(base, cand, "tokens")
    threshold = args.min_gain_percent / 100
    efficient = turn_gain is not None and token_gain is not None and turn_gain >= threshold and token_gain >= threshold
    result = {"wins": sorted(wins), "losses": sorted(losses), "turn_gain": turn_gain, "token_gain": token_gain}
    if aborted:
        return {**result, "decision": "inconclusive", "reasons": [f"stopped early: {aborted}"]}
    claimed_wins = len(wins) > unstable
    claimed_efficiency = efficient and unstable == 0
    if (wins or efficient) and not (claimed_wins or claimed_efficiency):
        return {**result, "decision": "inconclusive", "reasons": [
            f"a gain on {', '.join(sorted(wins)) or 'turns and tokens'} is not larger than the observed instability "
            f"({unstable} task(s) disagree with themselves across repeats); raise --repeats"]}
    if wins or efficient:
        if args.repeats < args.min_repeats:
            return {**result, "decision": "inconclusive",
                    "reasons": [f"an improvement needs at least {args.min_repeats} repeats to claim; ran {args.repeats}"]}
        if wins:
            reasons.append(f"passes more on: {', '.join(sorted(wins))}")
        if efficient:
            reasons.append(f"uses {turn_gain:.0%} fewer turns and {token_gain:.0%} fewer tokens on paired passes")
        return {**result, "decision": "promote", "reasons": reasons}
    return {**result, "decision": "no_difference", "reasons": ["no regression and no claimable improvement"]}


def flaky_tasks(trials: list[dict]) -> list[str]:
    outcomes: dict[tuple[str, str], set[bool]] = {}
    for t in trials:
        outcomes.setdefault((t["role"], t["task"]), set()).add(t["passed"])
    return sorted({f"{role}:{task}" for (role, task), seen in outcomes.items() if len(seen) > 1})


def render_markdown(report: dict) -> str:
    d = report["decision"]
    lines = [f"# Eval report: {d['decision']}", "",
             f"Baseline `{report['baseline']}` vs candidate `{report['candidate']}`; "
             f"{report['repeats']} repeat(s); {'held-out' if report['held_out'] else 'dev'} tasks: {', '.join(report['tasks'])}.", "",
             "## Decision", ""] + [f"- {r}" for r in d["reasons"]]
    lines += ["", "## Aggregates", "", "| | baseline | candidate |", "|---|---|---|"]
    for label, key in (("capability passes", "capability_passes"), ("capability trials", "capability_trials"),
                       ("trap passes", "trap_passes"), ("trap trials", "trap_trials"),
                       ("clean commits", "clean"), ("mean turns", "turns_mean"), ("mean tokens", "tokens_mean")):
        values = [report["summary"][role][key] for role in ROLES]
        lines.append(f"| {label} | " + " | ".join("n/a" if v is None else f"{v:.1f}" if isinstance(v, float) else str(v) for v in values) + " |")
    lines += ["", "## Cases", "", f"- improved: {', '.join(d.get('wins', [])) or 'none'}",
              f"- regressed: {', '.join(d.get('losses', [])) or 'none'}",
              f"- flaky: {', '.join(report['flaky']) or 'none'}",
              "", "## Cost and residuals", "",
              f"- model calls: {report['calls_used']}; tokens: {report['tokens_used']}; wall time: {report['wall_sec']:.0f}s",
              f"- trials with unreported token counts: {report['tokens_unknown']}"]
    if report["aborted"]:
        lines.append(f"- stopped early: {report['aborted']}")
    changed = report["changed_paths"]
    lines += ["", "## What changed", ""] + ([f"- `{p}`" for p in changed] or ["- no path differs"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--baseline", required=True, help=f"git ref, or {WORKTREE} for the checkout as is")
    p.add_argument("--candidate", required=True, help=f"git ref, or {WORKTREE}")
    p.add_argument("--report-dir", required=True, type=pathlib.Path, help="write eval-report.json/.md here (outside the checkout)")
    p.add_argument("--max-calls", required=True, type=int, help="ceiling on model calls (turns) across all trials")
    p.add_argument("--max-tokens", required=True, type=int, help="ceiling on reported input+output tokens")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--min-repeats", type=int, default=3, help="repeats needed before an improvement is claimed")
    p.add_argument("--allowed-regressions", type=int, default=0, help="tasks the candidate may pass less often")
    p.add_argument("--min-gain-percent", type=float, default=15.0)
    p.add_argument("--held-out", action="store_true", help="run the held-out tasks instead of the dev tasks")
    p.add_argument("--task", action="append", help="limit to this task (repeatable)")
    p.add_argument("--tasks-dir", type=pathlib.Path, default=TASKS_DIR)
    p.add_argument("--run-timeout", type=float, default=900.0)
    p.add_argument("--allow-unsandboxed-shell", action="store_true",
                   help="the runner lets the model run host shell commands; use a disposable sandbox")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        check_report_dir(args.report_dir)
        if min(args.repeats, args.max_calls, args.max_tokens) < 1:
            raise EvalError("repeats and spend ceilings must be positive")
        if os.environ.get("ALLOW_UNSANDBOXED_SHELL") != "1":
            if not args.allow_unsandboxed_shell:
                raise EvalError("the runner executes model-chosen shell commands; pass --allow-unsandboxed-shell "
                                "and run this inside a disposable sandbox")
            os.environ["ALLOW_UNSANDBOXED_SHELL"] = "1"
        tasks = load_tasks(args.tasks_dir, args.held_out, args.task)
        if not tasks:
            raise EvalError("no tasks selected")
        started = time.time()
        trials: list[dict] = []
        calls = tokens = 0
        aborted = None
        provider_failure = None
        with tempfile.TemporaryDirectory(prefix="tabilet-eval-") as tmp:
            work = pathlib.Path(tmp)
            trees = {"baseline": materialize_ref(args.baseline, work / "tree-baseline"),
                     "candidate": materialize_ref(args.candidate, work / "tree-candidate")}
            refs = {role: paired.identity(trees[role], getattr(args, role), ROOT) for role in ROLES}
            tasks = paired.freeze_tasks(tasks, work / "fixtures")
            fixture_identity = paired.manifest(work / "fixtures")
            trials, calls, tokens, aborted = paired.run_campaign(
                tasks, args.repeats, args.max_calls, args.max_tokens,
                paired.guard_inputs(
                    lambda task, role, repeat, budget: run_trial(trees[role], task, role, repeat, work, args.run_timeout),
                    [*trees.values(), work / "fixtures"]),
                args.report_dir / "campaign-progress.json")
        by_role, excluded = paired.pair_scored({role: [t for t in trials if t["role"] == role] for role in ROLES})
        provider_failure = next((t for t in trials if t.get("provider_error")), None)
        decision = decide(by_role["baseline"], by_role["candidate"], args, aborted)
        if provider_failure:
            decision = {"decision": "inconclusive",
                        "reasons": [f"stopped early: {aborted}; the scored trials are uneven, rerun"]}
        report = {
            "schema": "tabilet.eval-report/v1", "refs": refs, "fixture_identity": fixture_identity,
            "model": os.environ.get("LLM_MODEL"), "provider": os.environ.get("LLM_PROVIDER", "openai"), "excluded_pairs": excluded, "baseline": args.baseline, "candidate": args.candidate,
            "repeats": args.repeats, "held_out": args.held_out, "tasks": [t["name"] for t in tasks],
            "decision": decision, "summary": {role: summarize(by_role[role]) for role in ROLES},
            "flaky": flaky_tasks(trials), "trials": trials, "calls_used": calls, "tokens_used": tokens,
            "tokens_unknown": sum(not t["tokens_known"] for t in trials), "aborted": aborted,
            "provider_failure": provider_failure,
            "wall_sec": time.time() - started,
            "changed_paths": paired.changed_paths(refs),
        }
        args.report_dir.mkdir(parents=True, exist_ok=True)
        (args.report_dir / "eval-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.report_dir / "eval-report.md").write_text(render_markdown(report), encoding="utf-8")
        print(f"{decision['decision']}: " + "; ".join(decision["reasons"]))
        return {"promote": 0, "no_difference": 0, "reject": 1, "inconclusive": 3}[decision["decision"]]
    except EvalError as exc:
        print(f"eval: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())

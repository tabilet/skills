#!/usr/bin/env python3
"""Skill-body eval: does a skill's text make a model follow the skill's own rules?

Repository-only tooling: not installed, not payload, and users never run it. For every task and
repeat it builds a scratch project from a ref's `template/` plus the task overlay, gives the model
that ref's `SKILL.md` as instructions, plays a scripted human (the approval replies in task.json),
and grades the resulting files deterministically. The baseline-versus-candidate decision is
`run_eval.decide`. It measures instruction text, not how Claude Code or Codex invoke a skill.
Provider settings come from the runner's environment (LLM_PROVIDER, LLM_MODEL, LLM_API_BASE,
OPENAI_API_KEY / ANTHROPIC_API_KEY). Spend is bounded by required --max-calls and --max-tokens.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import catalog_probe  # noqa: E402
import run_eval  # noqa: E402

ROOT = run_eval.ROOT
TASKS_DIR = ROOT / "evals" / "skill-tasks"
ROLES = run_eval.ROLES
EvalError = run_eval.EvalError
DEFAULT_ALLOWED = ("tabilet/memory-bank/**", "tabilet/stages.md", "tabilet/evolution/**")
HISTORY = "tabilet/docs/history/"
STATUS_NAME = re.compile(r"status-([A-Z][0-9][0-9])\.md$")
PREAMBLE = """\
You are carrying out one skill for a user. The skill's instructions follow this preamble.
The project is your current working directory. The skill bundle is at {bundle}; every relative
link in the skill, such as references/..., resolves inside that directory, so read those files with
the shell tool when the skill tells you to.

You have no direct file access. Return exactly one JSON object per response:

To run a shell command:
{{"tool":"run_shell","cmd":"sed -n '1,120p' AGENTS.md","why":"Read the bootstrap guide."}}

To speak to the user and wait for their answer, or to finish:
{{"final":"Message to the user."}}

Rules: return only one JSON object, with no prose around it; prefer small, inspectable commands;
never use destructive commands such as `git reset --hard` or broad `rm -rf`.

--- SKILL INSTRUCTIONS ---

{skill}
"""


def load_tasks(tasks_dir: pathlib.Path, held_out: bool, only: list[str] | None = None) -> list[dict]:
    tasks = []
    for directory in sorted(p for p in tasks_dir.iterdir() if (p / "task.json").is_file()):
        meta = json.loads((directory / "task.json").read_text(encoding="utf-8"))
        task = {"name": directory.name, "dir": directory, "replies": [], "max_turns": 60,
                "allowed_paths": list(DEFAULT_ALLOWED), **meta}
        problems = task_problems(task, tasks_dir)
        if problems:
            raise EvalError(f"{directory.name}: " + "; ".join(problems))
        if bool(task.get("held_out", False)) == held_out and (not only or task["name"] in only):
            tasks.append(task)
    return tasks


def task_problems(task: dict, tasks_dir: pathlib.Path = TASKS_DIR) -> list[str]:
    problems = []
    if task.get("category") not in run_eval.CATEGORIES:
        problems.append(f"category must be one of {run_eval.CATEGORIES}")
    if not isinstance(task.get("skill"), str) or not re.fullmatch(r"[a-z][a-z0-9-]*", task["skill"]):
        problems.append("skill must be a skill directory name")
    if not isinstance(task.get("request"), str) or not task["request"].strip():
        problems.append("request must be non-empty text")
    if not isinstance(task.get("replies"), list) or not all(isinstance(r, str) and r.strip() for r in task["replies"]):
        problems.append("replies must be a list of non-empty strings")
    expect = task.get("expect")
    if not isinstance(expect, dict) or not isinstance(expect.get("new_status_files"), int) or expect["new_status_files"] < 0:
        problems.append("expect.new_status_files must be a non-negative integer")
    for key in ("files_contain", "files_exclude"):
        contains = (expect or {}).get(key, {}) if isinstance(expect, dict) else {}
        if not isinstance(contains, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in contains.items()):
            problems.append(f"expect.{key} must map paths (alternatives joined with |) to regular expressions")
        else:
            for pattern in contains.values():
                try:
                    re.compile(pattern)
                except re.error:
                    problems.append(f"expect.{key} has an invalid pattern {pattern!r}")
    heads = (expect or {}).get("records_head", []) if isinstance(expect, dict) else []
    if not isinstance(heads, list) or not all(isinstance(h, str) and h for h in heads):
        problems.append("expect.records_head must be a list of paths (alternatives joined with |) that record the starting HEAD")
    mentions = (expect or {}).get("final_mentions", []) if isinstance(expect, dict) else []
    if not isinstance(mentions, list) or not all(isinstance(m, str) and m for m in mentions):
        problems.append("expect.final_mentions must be a list of non-empty strings")
    between = task.get("between")
    if between is not None and (not isinstance(between, list) or len(between) != len(task.get("replies", []))
                                or not all(c is None or (isinstance(c, str) and c.strip()) for c in between)):
        problems.append("between must have one shell command or null per reply")
    if not isinstance(task.get("allowed_paths"), list) or not task["allowed_paths"]:
        problems.append("allowed_paths must be a non-empty list")
    project = task["dir"] / "project"
    if not any(project.rglob("status-[A-Z][0-9][0-9].md")):
        problems.append("project overlay needs at least one status file")
    if (project / run_eval.EDITABLE_PROJECT_FILE).exists():
        problems.append(f"overlay must not contain {run_eval.EDITABLE_PROJECT_FILE}: the ref's template is what is measured")
    return problems


def snapshot(project: pathlib.Path) -> dict:
    """HEAD plus a content hash of every tracked or unignored file, so any write, delete or new file shows."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True).stdout.strip()
    listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=project, capture_output=True).stdout.decode().split("\0")
    files = {}
    for relative in sorted(set(filter(None, listed))):
        path = project / relative
        if path.is_file():
            files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"head": head, "files": files}


def changed_paths(before: dict, after: dict) -> list[str]:
    names = set(before["files"]) | set(after["files"])
    return sorted(n for n in names if before["files"].get(n) != after["files"].get(n))


def path_allowed(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if pattern.endswith("/**") and path.startswith(pattern[:-2]):
            return True
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def status_ids(files: dict) -> set[str]:
    return {m.group(1) for name in files if (m := STATUS_NAME.search(name))}


def active_status_files(files: dict) -> dict[str, str]:
    return {name: STATUS_NAME.search(name).group(1) for name in files
            if name.startswith("tabilet/memory-bank/") and STATUS_NAME.search(name)}


def expand_paths(project: pathlib.Path, spec: str) -> list[pathlib.Path]:
    """The files a task expectation names: alternatives joined with `|`. An alternative containing `*` is a
    glob from the project root (`tabilet/**/*` is every file under tabilet/), so an exclusion can cover
    files a model might create as well as the ones it was told about."""
    paths: list[pathlib.Path] = []
    for relative in spec.split("|"):
        if "*" in relative:
            paths += [path for path in sorted(project.glob(relative)) if path.is_file()]
        else:
            paths.append(project / relative)
    return paths


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_rows(runner, project: pathlib.Path, files: dict) -> dict[tuple[str, str], str]:
    rows = {}
    for name in active_status_files(files):
        path = project / name
        if path.is_file():
            for row in runner.status_rows(path.read_text(encoding="utf-8")):
                rows[(name, row["item"])] = row["state"]
    return rows


def grade(task: dict, runner, project: pathlib.Path, initial: dict, initial_rows: dict,
          checkpoints: list[dict], final: dict, finished: bool, rebased: dict | None = None,
          finals: list[str] | None = None) -> tuple[list[str], dict]:
    """Return (failed hard check names, soft facts). Pure given the snapshots and the final files.

    `rebased` is the snapshot after a scripted outside change between replies (another writer);
    the model is judged against it, while the approval gate is judged against the start."""
    failed: list[str] = []
    if not finished or not checkpoints:
        return ["finished"], {}
    if changed_paths(initial, checkpoints[0]) or checkpoints[0]["head"] != initial["head"]:
        failed.append("gate")
    base = rebased or initial
    changes = changed_paths(base, final)
    if any(not path_allowed(p, task["allowed_paths"]) for p in changes):
        failed.append("planning_only")
    if final["head"] != base["head"]:
        failed.append("no_commit")
    if any(p.startswith(HISTORY) for p in changes):
        failed.append("history_frozen")
    final_rows = read_rows(runner, project, final["files"])
    if any(final_rows.get(key) != state for key, state in initial_rows.items()):
        failed.append("rows_preserved")
    new_files = sorted(set(active_status_files(final["files"])) - set(active_status_files(base["files"])))
    new_ids = [STATUS_NAME.search(n).group(1) for n in new_files]
    reserved = status_ids(base["files"])
    problems = len(new_files) != task["expect"]["new_status_files"]
    problems = problems or any(i in reserved for i in new_ids)
    milestone = project / "tabilet/memory-bank/milestone.md"
    index = milestone.read_text(encoding="utf-8") if milestone.is_file() else ""
    for name, new_id in zip(new_files, new_ids):
        rows = runner.status_rows((project / name).read_text(encoding="utf-8"))
        problems = problems or not rows or any(r["state"] != "pending" for r in rows) or new_id not in index
    if problems:
        failed.append("new_status")
    if any(text not in (finals or [""])[-1] for text in task["expect"].get("final_mentions", [])):
        failed.append("final_mentions")
    expect = task["expect"]
    for relatives, pattern in expect.get("files_contain", {}).items():
        if not any(path.is_file() and re.search(pattern, read_text(path)) for path in expand_paths(project, relatives)):
            failed.append("expected_files")
            break
    # The commit a snapshot or registry records must be the one the model inspected, not any 40 hex digits.
    if any(not any(path.is_file() and base["head"] in read_text(path) for path in expand_paths(project, relatives))
           for relatives in expect.get("records_head", [])):
        if "expected_files" not in failed:
            failed.append("expected_files")
    for relatives, pattern in expect.get("files_exclude", {}).items():
        if any(path.is_file() and re.search(pattern, read_text(path)) for path in expand_paths(project, relatives)):
            failed.append("forbidden_content")
            break
    return failed, {"new_ids": new_ids, "changed": changes}


def converse(runner, llm, project: pathlib.Path, system: str, task: dict, budget: int) -> dict:
    """Run the scripted conversation; returns checkpoints, finals, turns and token use."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task["request"]}]
    replies = list(task["replies"])
    checkpoints, finals = [], []
    rebased = None
    turns = tokens = 0
    tokens_known = True
    while True:
        while True:
            if turns >= min(task["max_turns"], budget):
                return {"finished": False, "checkpoints": checkpoints, "finals": finals, "turns": turns,
                        "tokens": tokens, "tokens_known": tokens_known, "note": "turn limit"}
            if sum(len(m["content"]) for m in messages) > llm.max_history_chars:
                return {"finished": False, "checkpoints": checkpoints, "finals": finals, "turns": turns,
                        "tokens": tokens, "tokens_known": tokens_known, "note": "history limit"}
            turns += 1
            response = runner.call_llm(llm.provider, llm.api_base, llm.api_key, llm.model, messages,
                                       llm.temperature, llm.max_tokens, llm.api_timeout, llm.max_retries)
            usage = runner.normalize_usage(llm.provider, response.get("usage"))
            if usage.get("input_total") is None or usage.get("output") is None:
                tokens_known = False
            tokens += (usage.get("input_total") or 0) + (usage.get("output") or 0)
            try:
                command = runner.extract_json(response["content"])
            except Exception as exc:
                messages += [{"role": "assistant", "content": response["content"]},
                             {"role": "user", "content": f"Your response was not valid JSON: {exc}. Return exactly one JSON object."}]
                continue
            messages.append({"role": "assistant", "content": json.dumps(command)})
            if isinstance(command.get("final"), str):
                break
            if command.get("tool") != "run_shell" or not isinstance(command.get("cmd"), str):
                messages.append({"role": "user", "content": 'Invalid command. Use {"tool":"run_shell","cmd":"...","why":"..."} or {"final":"..."}.'})
                continue
            result = runner.shell_tool(project, command["cmd"], llm.tool_timeout, llm.max_tool_output, llm.allow_dangerous, llm.tool_env)
            messages.append({"role": "user", "content": "Tool result:\n```json\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n```"})
        checkpoints.append(snapshot(project))
        finals.append(command["final"])
        if not replies:
            return {"finished": True, "checkpoints": checkpoints, "finals": finals, "turns": turns,
                    "tokens": tokens, "tokens_known": tokens_known, "note": "", "rebased": rebased}
        outside = (task.get("between") or [None] * len(task["replies"]))[len(task["replies"]) - len(replies)]
        if outside:
            subprocess.run(["bash", "-c", outside], cwd=project, capture_output=True, timeout=60)
            rebased = snapshot(project)
            rebased["rows"] = read_rows(runner, project, rebased["files"])
        messages.append({"role": "user", "content": replies.pop(0)})


def prepare_project(tree: pathlib.Path, task: dict, dest: pathlib.Path) -> pathlib.Path:
    shutil.copytree(tree / "template", dest)
    base = task["dir"].parent / "_base" / "project"
    if base.is_dir():
        shutil.copytree(base, dest, dirs_exist_ok=True)
    shutil.copytree(task["dir"] / "project", dest, dirs_exist_ok=True)
    run_eval.git("init", "-q", cwd=dest)
    run_eval.git("config", "--local", "user.name", "Eval", cwd=dest)
    run_eval.git("config", "--local", "user.email", "eval@example.test", cwd=dest)
    run_eval.git("add", "-A", cwd=dest)
    run_eval.git("commit", "-qm", "initial", cwd=dest)
    return dest


def run_trial(runner, llm, tree: pathlib.Path, task: dict, role: str, repeat: int, work: pathlib.Path, budget: int) -> dict:
    root = work / f"{role}-{task['name']}-r{repeat}"
    root.mkdir(parents=True)
    skill_dir = tree / "skills" / task["skill"]
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise EvalError(f"{role} ref has no skills/{task['skill']}/SKILL.md")
    bundle = root / "bundle" / task["skill"]
    shutil.copytree(skill_dir, bundle)
    project = prepare_project(tree, task, root / "project")
    initial = snapshot(project)
    initial_rows = read_rows(runner, project, initial["files"])
    system = PREAMBLE.format(bundle=bundle, skill=skill_file.read_text(encoding="utf-8"))
    started = time.time()
    error = ""
    try:
        outcome = converse(runner, llm, project, system, task, budget)
    except SystemExit as exc:
        error = f"provider or runner failure (exit {exc.code})"
        outcome = {"finished": False, "checkpoints": [], "finals": [], "turns": 0, "tokens": 0, "tokens_known": False, "note": error}
    final = snapshot(project)
    rebased = outcome.get("rebased")
    base_rows = rebased["rows"] if rebased else initial_rows
    failed, facts = grade(task, runner, project, initial, base_rows, outcome["checkpoints"], final, outcome["finished"], rebased, outcome["finals"])
    return {"task": task["name"], "category": task["category"], "role": role, "repeat": repeat,
            "passed": not failed, "failed_checks": failed, "clean": None, "turns": outcome["turns"],
            "tokens": outcome["tokens"], "tokens_known": outcome["tokens_known"],
            "duration_sec": round(time.time() - started, 3), "note": outcome["note"],
            "facts": facts, "messages": [m[:1500] for m in outcome["finals"]]}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--baseline", required=True, help=f"git ref, or {run_eval.WORKTREE} for the checkout as is")
    p.add_argument("--candidate", required=True, help=f"git ref, or {run_eval.WORKTREE}")
    p.add_argument("--report-dir", required=True, type=pathlib.Path, help="write eval-report.json/.md here (outside the checkout)")
    p.add_argument("--max-calls", required=True, type=int, help="ceiling on model calls across all trials")
    p.add_argument("--max-tokens", required=True, type=int, help="ceiling on reported input+output tokens")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--min-repeats", type=int, default=3, help="repeats needed before an improvement is claimed")
    p.add_argument("--allowed-regressions", type=int, default=0, help="tasks the candidate may pass less often")
    p.add_argument("--min-gain-percent", type=float, default=15.0)
    p.add_argument("--held-out", action="store_true", help="run the held-out tasks instead of the dev tasks")
    p.add_argument("--task", action="append", help="limit to this task (repeatable)")
    p.add_argument("--tasks-dir", type=pathlib.Path, default=TASKS_DIR)
    p.add_argument("--allow-unsandboxed-shell", action="store_true",
                   help="the model runs host shell commands; use a disposable sandbox")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.repeats < 1:
            raise EvalError("--repeats must be at least 1")
        if os.environ.get("ALLOW_UNSANDBOXED_SHELL") != "1":
            if not args.allow_unsandboxed_shell:
                raise EvalError("the model runs shell commands; pass --allow-unsandboxed-shell and run this inside a disposable sandbox")
            os.environ["ALLOW_UNSANDBOXED_SHELL"] = "1"
        tasks = load_tasks(args.tasks_dir, args.held_out, args.task)
        if not tasks:
            raise EvalError("no tasks selected")
        runner = catalog_probe.load_runner()
        try:
            llm = runner.parse_args(["."])
        except SystemExit:
            raise EvalError("provider settings are invalid (check LLM_PROVIDER and the other LLM_* values)")
        if not llm.model:
            raise EvalError("LLM_MODEL is not set")
        started = time.time()
        trials: list[dict] = []
        calls = tokens = 0
        aborted = None
        with tempfile.TemporaryDirectory(prefix="tabilet-skill-eval-") as tmp:
            work = pathlib.Path(tmp)
            trees = {"baseline": run_eval.materialize_ref(args.baseline, work / "tree-baseline", ("template", "skills")),
                     "candidate": run_eval.materialize_ref(args.candidate, work / "tree-candidate", ("template", "skills"))}
            for repeat in range(1, args.repeats + 1):
                for task in tasks:
                    for role in ROLES:
                        if calls >= args.max_calls or tokens >= args.max_tokens:
                            aborted = f"ceiling reached ({calls} calls, {tokens} tokens)"
                            break
                        trial = run_trial(runner, llm, trees[role], task, role, repeat, work, args.max_calls - calls)
                        trials.append(trial)
                        calls += trial["turns"]
                        tokens += trial["tokens"]
                    if aborted:
                        break
                if aborted:
                    break
        by_role = {role: [t for t in trials if t["role"] == role] for role in ROLES}
        decision = run_eval.decide(by_role["baseline"], by_role["candidate"], args, aborted)
        changed = run_eval.git("diff", "--name-only", args.baseline, args.candidate, "--", "template", "skills", check=False)
        report = {
            "schema": "tabilet.skill-eval-report/v1", "baseline": args.baseline, "candidate": args.candidate,
            "repeats": args.repeats, "held_out": args.held_out, "tasks": [t["name"] for t in tasks],
            "decision": decision, "summary": {role: run_eval.summarize(by_role[role]) for role in ROLES},
            "flaky": run_eval.flaky_tasks(trials), "trials": trials, "calls_used": calls, "tokens_used": tokens,
            "tokens_unknown": sum(not t["tokens_known"] for t in trials), "aborted": aborted,
            "wall_sec": time.time() - started,
            "changed_paths": changed.stdout.decode().split() if changed.returncode == 0 else [],
        }
        args.report_dir.mkdir(parents=True, exist_ok=True)
        (args.report_dir / "skill-eval-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.report_dir / "skill-eval-report.md").write_text(render_markdown(report), encoding="utf-8")
        print(f"{decision['decision']}: " + "; ".join(decision["reasons"]))
        return {"promote": 0, "no_difference": 0, "reject": 1, "inconclusive": 3}[decision["decision"]]
    except EvalError as exc:
        print(f"skill-eval: {exc}", file=sys.stderr)
        return 2


def render_markdown(report: dict) -> str:
    text = run_eval.render_markdown(report).replace("# Eval report:", "# Skill eval report:", 1)
    failures = [t for t in report["trials"] if t["failed_checks"]]
    lines = ["", "## Failed checks", ""]
    lines += [f"- {t['role']} {t['task']} r{t['repeat']}: {', '.join(t['failed_checks'])}" for t in failures] or ["- none"]
    return text + "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())

#!/usr/bin/env python3
"""Skill description proposer for maintainers.

Repository-only tooling and a paid step. It reads the routing misses in a dev-split catalog
report from catalog_probe.py, makes exactly one model call to the provider and model named in
the runner's environment (LLM_PROVIDER, LLM_MODEL, LLM_API_BASE, OPENAI_API_KEY /
ANTHROPIC_API_KEY), and proposes new frontmatter `description:` lines, the one SKILL.md field the
optimizer gate lets an automated edit change. With --apply it writes them and runs
`check.py --optimizer-gate`; a failed gate restores the files' previous bytes. The proposal is a
candidate for catalog_probe.py and a human, never a result. A report from the held-out split is
refused, so the held-out prompts never reach the model.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import catalog_probe  # noqa: E402
import run_eval  # noqa: E402

ROOT = run_eval.ROOT
REPORT_SCHEMA = "tabilet.catalog-report/v1"
DESCRIPTION_RE = re.compile(r"^description:.*$", re.M)
MAX_DESCRIPTION = 250
MAX_TOKENS = 1500

PROPOSE_PROMPT = """You are tuning the skill routing descriptions of Tabilet Memory Bank.
The catalog below routes a user's prompt to at most one skill:

{catalog_text}

On the development prompts, the current catalog produced these routing misses:
{misses_text}

Write revised `description:` lines for the affected skills that fix these misses without causing
false activations on prompts that should select no skill.

RULES:
1. Each description is one line, under {limit} characters, saying what the skill does and its key boundary.
2. Do not use double quotes or backslashes.
3. Only propose changes for skills that need tuning.
4. Answer with exactly one JSON object mapping skill name to the new description, and nothing else:
{{"<skill-name>": "<new description text>"}}
"""


def load_check():
    spec = importlib.util.spec_from_file_location("repository_checks", ROOT / "check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_report(report: Any) -> None:
    """Refuse anything but a dev-split catalog report: the held-out prompts must never reach a model."""
    if not isinstance(report, dict) or report.get("schema") != REPORT_SCHEMA:
        raise run_eval.EvalError(f"not a {REPORT_SCHEMA} report")
    if report.get("prompts") != "dev":
        raise run_eval.EvalError("the report is not from the dev prompts; held-out results must never reach a proposer")
    trials = report.get("trials")
    if not isinstance(trials, list) or any(t.get("held_out") is not False for t in trials):
        raise run_eval.EvalError("a trial in the report is not marked as a dev prompt; rerun catalog_probe.py")


def extract_misses(report: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Candidate-side routing misses with how often each happened, and the count of unparsed answers."""
    counts: dict[tuple, int] = {}
    unparsed = 0
    for t in report["trials"]:
        if t["role"] != "candidate":
            continue
        if not t["parsed"]:
            unparsed += 1
        elif t["chosen"] != t["expect"]:
            key = (t["prompt"], t["expect"], t["chosen"])
            counts[key] = counts.get(key, 0) + 1
    repeats = report.get("repeats", 1)
    return [{"prompt": p, "expected": e, "chosen": c, "count": n, "repeats": repeats}
            for (p, e, c), n in counts.items()], unparsed


def format_misses_text(misses: list[dict[str, Any]], unparsed: int) -> str:
    lines = []
    for m in misses:
        expected = m["expected"] or "None (should select no skill)"
        lines.append(f"- Prompt: {m['prompt']!r}\n  Expected: {expected}\n  Model selected: {m['chosen'] or 'None'}"
                     f" (missed {m['count']} of {m['repeats']} repeats)")
    if unparsed:
        lines.append(f"({unparsed} unparsed answers are not routing evidence and are left out.)")
    return "\n".join(lines)


def format_catalog_text(catalog: dict[str, str]) -> str:
    return "\n".join(f"- {name}: {desc}" for name, desc in sorted(catalog.items()))


def parse_proposals(response_text: str, valid_names: set[str]) -> dict[str, str]:
    """The valid {skill name: single-line description} pairs in the first JSON object that has any."""
    for match in re.finditer(r"\{[^{}]*\}", response_text):
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        clean = {}
        for name, value in parsed.items():
            if name not in valid_names or not isinstance(value, str):
                continue
            value = " ".join(value.split())
            if value and len(value) <= MAX_DESCRIPTION and '"' not in value and "\\" not in value:
                clean[name] = value
        if clean:
            return clean
    return {}


def apply_description_updates(tree: pathlib.Path, updates: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Write the new description lines. Returns ({skill: previous text}, skills skipped as unsafe).

    A value that a strict YAML loader would misread is quoted; one that still fails check.py's
    front-matter lint is skipped rather than written."""
    lint = load_check().frontmatter_scalar_problems
    previous: dict[str, str] = {}
    skipped: list[str] = []
    for name, new_desc in updates.items():
        path = tree / "skills" / name / "SKILL.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not match or not DESCRIPTION_RE.search(match.group(1)):
            continue
        for value in (new_desc, f'"{new_desc}"'):
            frontmatter = DESCRIPTION_RE.sub(lambda _: f"description: {value}", match.group(1), count=1)
            updated = f"---\n{frontmatter}\n---\n{text[match.end():]}"
            if not lint(updated):
                break
        else:
            skipped.append(name)
            continue
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            previous[name] = text
    return previous, skipped


def restore(tree: pathlib.Path, previous: dict[str, str]) -> None:
    for name, text in previous.items():
        (tree / "skills" / name / "SKILL.md").write_text(text, encoding="utf-8")


def worktree_clean(repo: pathlib.Path) -> bool:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True)
    return proc.returncode == 0 and not proc.stdout.strip()


def run_optimizer_gate(base_ref: str, repo: pathlib.Path = ROOT) -> int:
    proc = subprocess.run([sys.executable, "-B", str(repo / "check.py"), "--optimizer-gate", base_ref],
                          cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--catalog-report", required=True, type=pathlib.Path,
                   help="catalog-report.json from a dev-split catalog_probe.py run")
    p.add_argument("--base-ref", default="HEAD", help="git ref the gate compares against (default: HEAD)")
    p.add_argument("--repo", type=pathlib.Path, default=ROOT, help="repository root")
    p.add_argument("--dry-run", action="store_true", help="print the settings and the prompt; no model call")
    p.add_argument("--apply", action="store_true", help="write the proposals to SKILL.md and run the gate")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if not args.catalog_report.is_file():
            raise run_eval.EvalError(f"{args.catalog_report}: no such report")
        try:
            report = json.loads(args.catalog_report.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise run_eval.EvalError(f"{args.catalog_report}: not valid JSON ({exc})")
        check_report(report)
        catalog = catalog_probe.build_catalog(args.repo)
        if not catalog:
            raise run_eval.EvalError("the repository has no skills with a name and description")
        misses, unparsed = extract_misses(report)
        if not misses:
            print("no routing misses; nothing to propose")
            return 0
        if args.apply and not args.dry_run and not worktree_clean(args.repo):
            raise run_eval.EvalError("the worktree has changes: commit or stash them so the gate judges only this candidate")
        prompt = PROPOSE_PROMPT.format(catalog_text=format_catalog_text(catalog), limit=MAX_DESCRIPTION,
                                       misses_text=format_misses_text(misses, unparsed))
        runner = catalog_probe.load_runner()
        try:
            llm = runner.parse_args(["."])
        except SystemExit:
            raise run_eval.EvalError("provider settings are invalid (check LLM_PROVIDER and the other LLM_* values)")
        if not llm.model:
            raise run_eval.EvalError("LLM_MODEL is not set")
        print(f"provider {llm.provider}, model {llm.model}: 1 model call, {len(misses)} dev miss(es)", file=sys.stderr)
        if args.dry_run:
            print(f"--- PROMPT ({len(prompt)} chars) ---\n{prompt}--- END PROMPT ---")
            return 0
        response = runner.call_llm(llm.provider, llm.api_base, llm.api_key, llm.model,
                                   [{"role": "user", "content": prompt}], llm.temperature, MAX_TOKENS,
                                   llm.api_timeout, llm.max_retries)
        proposals = parse_proposals(response["content"], set(catalog))
        if not proposals:
            raise run_eval.EvalError(f"the model returned no usable description update:\n{response['content']}")
        print(f"Proposed updates ({len(proposals)} skills):")
        for name, desc in proposals.items():
            print(f"  [{name}]:\n    Old: {catalog[name]}\n    New: {desc}")
        if not args.apply:
            print("\nPreview only. Re-run with --apply to write the updates and run the gate.")
            return 0
        previous, skipped = apply_description_updates(args.repo, proposals)
        for name in skipped:
            print(f"skipped {name}: the description would not be valid front matter", file=sys.stderr)
        print(f"\nWrote {len(previous)} file(s). Running optimizer gate...")
        if run_optimizer_gate(args.base_ref, repo=args.repo) != 0:
            restore(args.repo, previous)
            print("Optimizer gate FAILED. Restored the previous files.", file=sys.stderr)
            return 1
        print("Optimizer gate PASSED. Probe the candidate with catalog_probe.py (dev split) next.")
        return 0
    except run_eval.EvalError as exc:
        print(f"propose: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())

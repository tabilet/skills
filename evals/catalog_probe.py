#!/usr/bin/env python3
"""Catalog-selection probe: does the model pick the right skill from names and descriptions?

Repository-only tooling. It measures the one thing the optimizer gate lets an automated edit
change in a SKILL.md, the frontmatter `description`. For two refs it builds the skill catalog,
sends each prompt in evals/catalog-prompts.json, and compares selection: every positive prompt
should choose its skill, and no negative prompt should choose any. It does not prove runtime
invocation or workflow acceptance. Cost is exact: prompts x repeats x 2 refs model calls, refused
up front when that exceeds --max-calls. Provider settings come from the runner's own environment
(LLM_PROVIDER, LLM_MODEL, LLM_API_BASE, OPENAI_API_KEY / ANTHROPIC_API_KEY).
"""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_eval  # noqa: E402

ROOT = run_eval.ROOT
PROMPTS = ROOT / "evals" / "catalog-prompts.json"
ROLES = run_eval.ROLES
SYSTEM = (
    "You route a user's request to at most one skill. The catalog lists each skill's name and "
    "description:\n\n{catalog}\n\nAnswer with exactly one JSON object: {{\"skill\": \"<name>\"}} for the one "
    "skill that fits, or {{\"skill\": null}} when no skill applies."
)


def load_runner():
    path = ROOT / "harness" / "tackle-memory-bank-api-loop"
    loader = importlib.machinery.SourceFileLoader("probe_runner", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def build_catalog(tree: pathlib.Path) -> dict[str, str]:
    """Skill name -> frontmatter description, in directory order."""
    catalog = {}
    for path in sorted((tree / "skills").glob("*/SKILL.md")):
        match = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
        fields = {}
        for line in (match.group(1).splitlines() if match else []):
            key, colon, value = line.partition(":")
            if colon and not line.startswith(" "):
                fields[key.strip()] = value.strip().strip("\"'")
        if fields.get("name") and fields.get("description"):
            catalog[fields["name"]] = fields["description"]
    return catalog


def load_prompts(path: pathlib.Path, names: set[str]) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    for index, case in enumerate(cases):
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise run_eval.EvalError(f"prompt {index}: needs a non-empty prompt")
        if case.get("expect") is not None and case["expect"] not in names:
            raise run_eval.EvalError(f"prompt {index}: expects unknown skill {case['expect']!r}")
    return cases


def parse_choice(content: str, names: set[str]) -> tuple[str | None, bool]:
    """Return (skill or None, parsed). An answer that is not valid JSON or names no skill counts as unparsed."""
    for candidate in re.findall(r"\{[^{}]*\}", content):
        try:
            value = json.loads(candidate).get("skill", "<missing>")
        except (ValueError, AttributeError):
            continue
        if value is None or value in names:
            return value, True
    return None, False


def ask(runner, args, catalog: dict[str, str], prompt: str) -> dict:
    listing = "\n".join(f"- {name}: {description}" for name, description in catalog.items())
    messages = [{"role": "system", "content": SYSTEM.format(catalog=listing)}, {"role": "user", "content": prompt}]
    response = runner.call_llm(args.provider, args.api_base, args.api_key, args.model, messages,
                               args.temperature, 200, args.api_timeout, args.max_retries)
    return response


def score(trials: list[dict]) -> dict:
    positives = [t for t in trials if t["expect"] is not None]
    negatives = [t for t in trials if t["expect"] is None]
    return {
        "positive_trials": len(positives), "positive_correct": sum(t["chosen"] == t["expect"] for t in positives),
        "negative_trials": len(negatives), "false_activations": sum(t["chosen"] is not None for t in negatives),
        "unparsed": sum(not t["parsed"] for t in trials),
    }


def decide(base: dict, cand: dict, allowed: int, min_gain: int = 2) -> dict:
    lost = max(0, base["positive_correct"] - cand["positive_correct"])
    extra = max(0, cand["false_activations"] - base["false_activations"])
    if lost + extra > allowed:
        return {"decision": "reject", "reasons": [
            f"selection regressed: {lost} fewer correct positives, {extra} more false activations"]}
    gain = (cand["positive_correct"] - base["positive_correct"]) + (base["false_activations"] - cand["false_activations"])
    if gain >= min_gain:
        return {"decision": "improved", "reasons": [
            f"{gain} more correct selections or fewer false activations (at least {min_gain} required), no regression"]}
    if gain > 0:
        return {"decision": "no_difference", "reasons": [
            f"a gain of {gain} is below --min-gain {min_gain}; one flipped answer is within noise"]}
    return {"decision": "no_difference", "reasons": ["selection is unchanged"]}


def render_markdown(report: dict) -> str:
    d = report["decision"]
    lines = [f"# Catalog probe: {d['decision']}", "",
             f"Baseline `{report['baseline']}` vs candidate `{report['candidate']}`; {report['repeats']} repeat(s); "
             f"{report['calls']} model call(s); tokens reported: {report['tokens']}.", ""]
    lines += [f"- {r}" for r in d["reasons"]]
    lines += ["", "| | baseline | candidate |", "|---|---|---|"]
    for label, key in (("positive correct", "positive_correct"), ("positive trials", "positive_trials"),
                       ("false activations", "false_activations"), ("negative trials", "negative_trials"),
                       ("unparsed answers", "unparsed")):
        lines.append(f"| {label} | " + " | ".join(str(report["score"][role][key]) for role in ROLES) + " |")
    lines += ["", "## Changed descriptions", ""]
    changed = report["changed_descriptions"]
    lines += [f"- `{name}`" for name in changed] or ["- none"]
    wrong = [t for t in report["trials"] if t["role"] == "candidate" and t["chosen"] != t["expect"]]
    lines += ["", "## Candidate misses", ""] + ([f"- {t['expect']!r} expected, got {t['chosen']!r}: {t['prompt'][:70]}" for t in wrong] or ["- none"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--baseline", required=True)
    p.add_argument("--candidate", required=True, help=f"git ref, or {run_eval.WORKTREE}")
    p.add_argument("--report-dir", type=pathlib.Path, help="write catalog-report.json/.md here (outside the checkout)")
    p.add_argument("--max-calls", required=True, type=int, help="refuse to start if the planned calls exceed this")
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--min-gain", type=int, default=2, help="net trial gain needed to claim an improvement")
    p.add_argument("--allowed-regressions", type=int, default=0, help="net trial losses tolerated")
    p.add_argument("--prompts", type=pathlib.Path, default=PROMPTS)
    p.add_argument("--repo", type=pathlib.Path, default=ROOT, help="repository holding the refs (tests use a scratch one)")
    p.add_argument("--dry-run", action="store_true", help="print the catalogs and planned calls; no model call")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.repeats < 1:
            raise run_eval.EvalError("--repeats must be at least 1")
        with tempfile.TemporaryDirectory(prefix="tabilet-probe-") as tmp:
            work = pathlib.Path(tmp)
            catalogs = {role: build_catalog(run_eval.materialize_ref(ref, work / role, ("skills",), args.repo))
                        for role, ref in zip(ROLES, (args.baseline, args.candidate))}
        names = set(catalogs["baseline"]) | set(catalogs["candidate"])
        if not catalogs["baseline"] or not catalogs["candidate"]:
            raise run_eval.EvalError("a ref has no skills with a name and description")
        cases = load_prompts(args.prompts, names)
        planned = len(cases) * args.repeats * len(ROLES)
        changed = sorted(n for n in names if catalogs["baseline"].get(n) != catalogs["candidate"].get(n))
        if planned > args.max_calls:
            raise run_eval.EvalError(f"{planned} model calls are planned, above --max-calls {args.max_calls}")
        if args.dry_run:
            print(f"{len(cases)} prompts x {args.repeats} repeat(s) x 2 refs = {planned} model calls; "
                  f"changed descriptions: {', '.join(changed) or 'none'}")
            return 0
        runner = load_runner()
        try:
            llm = runner.parse_args(["."])
        except SystemExit:
            raise run_eval.EvalError("provider settings are invalid (check LLM_PROVIDER and the other LLM_* values)")
        if not llm.model:
            raise run_eval.EvalError("LLM_MODEL is not set")
        trials, tokens = [], 0
        for repeat in range(1, args.repeats + 1):
            for case in cases:
                for role in ROLES:
                    response = ask(runner, llm, catalogs[role], case["prompt"])
                    chosen, parsed = parse_choice(response["content"], names)
                    usage = runner.normalize_usage(llm.provider, response.get("usage"))
                    tokens += (usage.get("input_total") or 0) + (usage.get("output") or 0)
                    trials.append({"role": role, "repeat": repeat, "prompt": case["prompt"], "expect": case.get("expect"),
                                   "chosen": chosen, "parsed": parsed})
        scores = {role: score([t for t in trials if t["role"] == role]) for role in ROLES}
        decision = decide(scores["baseline"], scores["candidate"], args.allowed_regressions, args.min_gain)
        report = {"schema": "tabilet.catalog-report/v1", "baseline": args.baseline, "candidate": args.candidate,
                  "repeats": args.repeats, "calls": len(trials), "tokens": tokens, "score": scores,
                  "decision": decision, "changed_descriptions": changed, "trials": trials}
        if args.report_dir:
            args.report_dir.mkdir(parents=True, exist_ok=True)
            (args.report_dir / "catalog-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            (args.report_dir / "catalog-report.md").write_text(render_markdown(report), encoding="utf-8")
        print(f"{decision['decision']}: " + "; ".join(decision["reasons"]))
        return 1 if decision["decision"] == "reject" else 0
    except run_eval.EvalError as exc:
        print(f"probe: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())

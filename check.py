#!/usr/bin/env python3
"""
Verify this repository's own invariants.

Every rule in AGENTS.md that a human would otherwise have to remember and
re-derive by hand is checked here instead. Run it before claiming a change is
done, and in CI:

    python3 check.py

Exits 0 when every check passes, 1 otherwise. Standard library only, matching
the repository's own dependency rule.

This file checks `skills` itself. It is not payload: a project that copies
`template/` records its own verification in `memory-bank/tech-stack.md`.
"""

from __future__ import annotations

import ast
import importlib.machinery
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata


ROOT = pathlib.Path(__file__).resolve().parent
HARNESS = ROOT / "harness" / "tackle-memory-bank-api-loop"
PROMPT_COPY = ROOT / "harness" / "prompts" / "tackle-next-memory-bank-todo.md"
LANGS = ("cn", "ja", "de", "fr", "es")

CHECKS: list[tuple[str, object]] = []


def check(name: str):
    """Register a check. The function returns a list of problem strings."""

    def wrap(fn):
        CHECKS.append((name, fn))
        return fn

    return wrap


def markdown_files() -> list[pathlib.Path]:
    return sorted(
        p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "node_modules" not in p.parts
    )


def load_harness():
    """Import the harness by path so regexes and exit codes are read from source."""
    loader = importlib.machinery.SourceFileLoader("harness_mod", str(HARNESS))
    spec = importlib.util.spec_from_loader("harness_mod", loader)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    loader.exec_module(module)
    return module


def slug(heading: str) -> str:
    """Approximate GitHub heading anchors, including non-ASCII headings."""
    s = unicodedata.normalize("NFC", heading.strip().lower())
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return re.sub(r"\s+", "-", s).strip("-")


def anchors(path: pathlib.Path) -> set[str]:
    return {slug(m) for m in re.findall(r"^#{1,6}\s+(.*)$", path.read_text(), re.M)}


# --------------------------------------------------------------------------
# 1. The harness must parse. Use ast.parse, never py_compile, which writes
#    __pycache__ into the shipped payload directory.
# --------------------------------------------------------------------------
@check("harness parses, and leaves no bytecode behind")
def harness_parses():
    try:
        ast.parse(HARNESS.read_text())
    except SyntaxError as exc:
        return [f"syntax error: {exc}"]
    stray = [str(p.relative_to(ROOT)) for p in ROOT.rglob("__pycache__") if ".git" not in p.parts]
    return [f"stray bytecode directory: {p}" for p in stray]


# --------------------------------------------------------------------------
# 2. GOAL.md is a portable protocol carried in two places. They must not drift.
# --------------------------------------------------------------------------
@check("GOAL.md and template/GOAL.md are byte-identical")
def goal_copies():
    a, b = ROOT / "GOAL.md", ROOT / "template" / "GOAL.md"
    if not a.exists() or not b.exists():
        return [f"missing {'GOAL.md' if not a.exists() else 'template/GOAL.md'}"]
    if a.read_bytes() != b.read_bytes():
        return ["copies differ; change both together"]
    return []


# --------------------------------------------------------------------------
# 3. The task instruction lives in the script and in a human-readable copy.
# --------------------------------------------------------------------------
@check("EMBEDDED_TASK matches harness/prompts/ copy")
def embedded_task():
    if not HARNESS.exists() or not PROMPT_COPY.exists():
        return ["harness or prompt copy missing"]
    embedded = load_harness().EMBEDDED_TASK
    # The prompt file omits the markdown title the embedded string carries.
    body = "\n".join(
        line for line in embedded.splitlines() if not line.startswith("# ")
    ).strip()
    if body != PROMPT_COPY.read_text().strip():
        return ["EMBEDDED_TASK and the prompt file have diverged"]
    return []


# --------------------------------------------------------------------------
# 4. GOAL.md defaults COMMIT_POLICY to `none`. An example that omits it
#    quietly promises no commits at all.
# --------------------------------------------------------------------------
@check("every /goal example sets an explicit COMMIT_POLICY")
def goal_examples():
    problems = []
    for md in markdown_files():
        if md.name == "GOAL.md":  # the protocol itself documents the default
            continue
        for block in re.findall(r"```text\n(.*?)```", md.read_text(), re.S):
            if "/goal" in block and "COMMIT_POLICY" not in block:
                problems.append(f"{md.relative_to(ROOT)}: /goal example without COMMIT_POLICY")
    return problems


# --------------------------------------------------------------------------
# 5. Links and heading anchors. Anchors are slugified from translated
#    headings, so #exit-codes is right in English and wrong in Chinese.
# --------------------------------------------------------------------------
@check("markdown links and heading anchors resolve")
def links():
    problems = []
    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for md in markdown_files():
        for target in link_re.findall(md.read_text()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, frag = target.partition("#")
            dest = (md.parent / file_part).resolve() if file_part else md.resolve()
            rel = md.relative_to(ROOT)
            if not dest.exists():
                problems.append(f"{rel}: missing file {file_part}")
            elif frag and frag not in anchors(dest):
                problems.append(f"{rel}: dead anchor #{frag} in {file_part or md.name}")
    return problems


# --------------------------------------------------------------------------
# 6. The documented exit codes must match the ones the harness can return.
# --------------------------------------------------------------------------
@check("documented exit codes match the harness source")
def exit_codes():
    src = HARNESS.read_text()
    in_source = {int(m) for m in re.findall(r"fail\([^;]*?,\s*(\d+),?\s*\)", src, re.S)}
    in_source |= {int(m) for m in re.findall(r"SystemExit\((\d+)\)", src)}
    in_source.add(0)  # the clean "nothing to do" return

    doc = (ROOT / "docs" / "EXECUTION.md").read_text()
    if "### Exit Codes" not in doc:
        return ["docs/EXECUTION.md has no Exit Codes section"]
    table = doc.split("### Exit Codes", 1)[1].split("\n## ", 1)[0]
    documented = {int(m) for m in re.findall(r"^\| `(\d+)`", table, re.M)}

    problems = []
    for code in sorted(in_source - documented):
        problems.append(f"exit code {code} exists in the harness but is undocumented")
    for code in sorted(documented - in_source):
        problems.append(f"exit code {code} is documented but the harness cannot return it")
    return problems


# --------------------------------------------------------------------------
# 7. The backtick footgun: a row written `| Item | [ ] | Notes |` parses as
#    zero actionable work, silently. The shipped template must stay matchable.
# --------------------------------------------------------------------------
@check("status-marker regexes match the shipped template rows")
def status_markers():
    mod = load_harness()
    template = (ROOT / "template" / "memory-bank" / "status-M01.md").read_text()
    problems = []
    if not mod.actionable_rows(template):
        problems.append("template/memory-bank/status-M01.md has no rows the harness sees as actionable")
    # And the footgun itself must still be a footgun worth warning about.
    if mod.actionable_rows("| Item | [ ] | Notes. |\n"):
        problems.append("a bare [ ] row now parses as actionable; the documented warning is stale")
    if not mod.actionable_rows("| Item | `[ ]` | Notes. |\n"):
        problems.append("a backticked [ ] row no longer parses as actionable")
    return problems


# --------------------------------------------------------------------------
# 8. What a new project actually receives must be a tree the harness accepts.
#    Every row gate runs before the first network call, so this is offline.
# --------------------------------------------------------------------------
@check("cp -R template/. yields a tree the harness accepts")
def payload_runs():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        dest = pathlib.Path(tmp) / "proj"
        shutil.copytree(ROOT / "template", dest)
        if not (dest / "AGENTS.md").exists():
            problems.append("payload has no AGENTS.md")
        lanes = list((dest / "memory-bank").glob("status-[A-Z][0-9][0-9].md"))
        if not lanes:
            problems.append("payload has no status-<LANE><NN>.md lane file")
        subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
        subprocess.run(["git", "add", "-A"], cwd=dest, check=True)
        subprocess.run(
            ["git", "-c", "user.email=c@c", "-c", "user.name=c", "commit", "-qm", "init"],
            cwd=dest, check=True,
        )
        proc = subprocess.run(
            [sys.executable, str(HARNESS), str(dest)],
            capture_output=True, text=True,
            env={
                "PATH": "/usr/bin:/bin", "HOME": tmp,
                "LLM_MODEL": "check", "LLM_API_KEY": "check",
                "LLM_API_BASE": "http://127.0.0.1:1/v1", "MAX_RUNS": "1",
            },
        )
        # 21 = could not reach the API, i.e. every gate before the call passed.
        if proc.returncode != 21:
            problems.append(
                f"expected exit 21 (gates passed, API unreachable), got {proc.returncode}: "
                f"{proc.stderr.strip().splitlines()[:1]}"
            )
    return problems


# --------------------------------------------------------------------------
# 9. English is the source; five translations must not silently fall behind.
# --------------------------------------------------------------------------
@check("translations stay in parity with English")
def translations():
    problems = []
    for stem in ("README", "docs/EXECUTION", "docs/MODEL_EVAL"):
        base = ROOT / f"{stem}.md"
        n_en = len(re.findall(r"^#{2,3} ", base.read_text(), re.M))
        for lang in LANGS:
            sib = ROOT / f"{stem}_{lang}.md"
            if not sib.exists():
                problems.append(f"{stem}_{lang}.md is missing")
                continue
            n = len(re.findall(r"^#{2,3} ", sib.read_text(), re.M))
            if abs(n - n_en) > 1:
                problems.append(
                    f"{sib.relative_to(ROOT)}: {n} headings vs {n_en} in English"
                )
    # Markers that must appear in every README, English included.
    for marker, label in (
        ("LLM_PROVIDER=anthropic", "Anthropic provider example"),
        ("COMMIT_POLICY: task", "goal-loop invocation"),
        ("git clone https", "clone step"),
    ):
        for name in ["README.md"] + [f"README_{l}.md" for l in LANGS]:
            if marker not in (ROOT / name).read_text():
                problems.append(f"{name}: missing {label}")
    return problems


def main() -> int:
    print(f"Checking {ROOT}\n")
    failures = 0
    for name, fn in CHECKS:
        try:
            problems = fn()
        except Exception as exc:
            # A check that raises must not hide every check after it.
            problems = [f"check raised {type(exc).__name__}: {exc}"]
        print(f"  {'PASS' if not problems else 'FAIL'}  {name}")
        for problem in problems:
            print(f"          {problem}")
        failures += len(problems)

    if failures:
        print(f"\n{failures} problem(s) found.")
        return 1
    print(f"\nAll {len(CHECKS)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())

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
SKILLS_DIR = ROOT / "harness" / "skills"
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
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


def prose(text: str) -> str:
    """Drop fenced code blocks.

    The docs contain worked examples written in markdown, so '## Status Files'
    and '[status-S01.md](status-S01.md)' appear inside fences as sample content.
    Those are not document structure and must not be read as headings or links.
    """
    return re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)


def headings(text: str) -> list[str]:
    return re.findall(r"^#{1,6}\s+(.*)$", prose(text), re.M)


def anchors(path: pathlib.Path) -> set[str]:
    return {slug(h) for h in headings(path.read_text())}


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
# 3b. The skills are the plugin's payload and are also copied to
#     ~/.claude/skills or ~/.codex/skills. Both agents read the same SKILL.md
#     format, so there is one source per command - keep it that way.
# --------------------------------------------------------------------------
def skill_frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def skill_body(path: pathlib.Path) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", path.read_text(), flags=re.S)
    return "\n".join(l for l in text.splitlines() if not l.startswith("# ")).strip()


@check("skills declare themselves and match the plugin manifest")
def skills_manifest():
    import json

    problems = []
    if not SKILLS_DIR.exists():
        return ["harness/skills/ is missing"]
    on_disk = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())
    for name in on_disk:
        skill = SKILLS_DIR / name / "SKILL.md"
        if not skill.exists():
            problems.append(f"{name}/ has no SKILL.md")
            continue
        fm = skill_frontmatter(skill)
        if fm.get("name") != name:
            problems.append(f"{name}/SKILL.md: frontmatter name is {fm.get('name')!r}")
        if not fm.get("description"):
            problems.append(f"{name}/SKILL.md: no description")
        # These orchestrate; they must not fire on their own.
        if fm.get("disable-model-invocation") != "true":
            problems.append(f"{name}/SKILL.md: missing disable-model-invocation")
    if not PLUGIN_JSON.exists():
        return problems + [".claude-plugin/plugin.json is missing"]
    listed = sorted(
        p.rsplit("/", 1)[-1] for p in json.loads(PLUGIN_JSON.read_text())["skills"]
    )
    if listed != on_disk:
        problems.append(f"plugin.json lists {listed}, disk has {on_disk}")
    # Claude Code owns /goal; a skill by that name would collide.
    if "goal" in on_disk:
        problems.append("a skill named 'goal' collides with Claude Code's built-in")
    return problems


# --------------------------------------------------------------------------
# 3c. The daily instruction now exists in three places. Machine-check it.
# --------------------------------------------------------------------------
@check("memory-bank-next skill matches the daily prompt")
def skill_matches_prompt():
    skill = SKILLS_DIR / "memory-bank-next" / "SKILL.md"
    if not skill.exists() or not PROMPT_COPY.exists():
        return ["memory-bank-next/SKILL.md or the prompt copy is missing"]
    if skill_body(skill) != PROMPT_COPY.read_text().strip():
        return ["memory-bank-next/SKILL.md and the prompt file have diverged"]
    return []


# --------------------------------------------------------------------------
# 4. GOAL.md defaults COMMIT_POLICY to `none`. An example that omits it
#    quietly promises no commits at all.
# --------------------------------------------------------------------------
@check("every GOAL.md invocation sets an explicit COMMIT_POLICY")
def goal_examples():
    # Keyed on naming GOAL.md, not on `/goal`. Claude Code has a built-in
    # `/goal <condition>` that sets a stop condition and has nothing to do with
    # this protocol; requiring COMMIT_POLICY there would be wrong. The protocol
    # itself requires a request to name the file, so this is the honest anchor.
    problems = []
    for md in markdown_files():
        if md.name == "GOAL.md":  # the protocol itself documents the default
            continue
        for block in re.findall(r"```(?:text|markdown)\n(.*?)```", md.read_text(), re.S):
            # "GOAL.md" alone is too loose: a file tree that merely lists the
            # file is not an invocation. Key on the two things only a real
            # invocation carries.
            invokes = "STATUS_ORDER" in block or "Using GOAL.md" in block
            if invokes and "COMMIT_POLICY" not in block:
                problems.append(
                    f"{md.relative_to(ROOT)}: GOAL.md invocation without COMMIT_POLICY"
                )
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
        for target in link_re.findall(prose(md.read_text())):
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
# 9. Current Claude models reject temperature/top_p/top_k with HTTP 400, so a
#    default sampling parameter breaks every current model. Build both payloads
#    and assert none carries one unless the caller explicitly asked.
# --------------------------------------------------------------------------
@check("provider payloads omit sampling parameters by default")
def sampling_params():
    mod = load_harness()
    sampled = {}

    def capture(url, headers, payload, label):
        sampled[label] = payload
        return {
            "content": [{"type": "text", "text": "{}"}],
            "choices": [{"message": {"content": "{}"}}],
        }

    original, mod._post_json = mod._post_json, capture
    try:
        messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
        mod.call_anthropic("https://example/v1", "k", "claude-opus-5", messages, None, 16000)
        mod.call_openai("https://example/v1", "k", "gpt-5.5", messages, None, 16000)
    finally:
        mod._post_json = original

    problems = []
    for label, payload in sampled.items():
        for param in ("temperature", "top_p", "top_k"):
            if param in payload:
                problems.append(f"{label} sends {param} by default; current Claude models 400 on it")
    if not sampled:
        problems.append("no payload was captured; the check did not exercise the call path")
    return problems


# --------------------------------------------------------------------------
# 10. English is the source; five translations must not silently fall behind.
# --------------------------------------------------------------------------
@check("translations stay in parity with English")
def translations():
    problems = []
    for stem in ("README", "docs/EXECUTION", "docs/MODEL_EVAL"):
        base = ROOT / f"{stem}.md"
        n_en = len([h for h in headings(base.read_text())])
        for lang in LANGS:
            sib = ROOT / f"{stem}_{lang}.md"
            if not sib.exists():
                problems.append(f"{stem}_{lang}.md is missing")
                continue
            n = len([h for h in headings(sib.read_text())])
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

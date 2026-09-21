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
`template/` records its own verification in `tabilet/memory-bank/tech-stack.md`.
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
AUDIT_MODULE = ROOT / "harness" / "tabilet_audit.py"
AUDIT_HOST = ROOT / "harness" / "tabilet_audit_host.py"
PROMPT_COPY = ROOT / "harness" / "prompts" / "tackle-next-memory-bank-todo.md"
SKILLS_DIR = ROOT / "skills"
ARCHIVE_SKILL = SKILLS_DIR / "memory-bank-archive" / "SKILL.md"
ARCHIVE_WRITE_CONTRACT = (
    SKILLS_DIR / "memory-bank-archive" / "references" / "write-contract.md"
)
INIT_SKILL = SKILLS_DIR / "memory-bank-init" / "SKILL.md"
INIT_WRITE_CONTRACT = SKILLS_DIR / "memory-bank-init" / "references" / "write-contract.md"
PROPOSE_SKILL = SKILLS_DIR / "memory-bank-propose" / "SKILL.md"
RECONCILE_SKILL = SKILLS_DIR / "memory-bank-reconcile" / "SKILL.md"
RECONCILE_WRITE_CONTRACT = (
    SKILLS_DIR / "memory-bank-reconcile" / "references" / "write-contract.md"
)
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
ARCHIVE_EXECUTION_RE = re.compile(r"archive-(?:<LANE><NN>|[A-Z][0-9]{2})(?:\.md)?")

CHECKS: list[tuple[str, object]] = []


def check(name: str):
    """Register a check. The function returns a list of problem strings."""

    def wrap(fn):
        CHECKS.append((name, fn))
        return fn

    return wrap


def markdown_files() -> list[pathlib.Path]:
    tracked_or_unignored = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.md",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if tracked_or_unignored.returncode == 0:
        return sorted(
            ROOT / line
            for line in tracked_or_unignored.stdout.splitlines()
            if line and (ROOT / line).is_file()
        )
    return sorted(
        p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "node_modules" not in p.parts
    )


def nav_section(config: str) -> str:
    """Return the top-level `nav:` section, up to the next top-level key."""

    return re.split(r"\n(?=\S)", config.partition("\nnav:\n")[2])[0]


def yaml_block(config: str, key: str) -> list[str]:
    """Return the lines nested under the first `key:` line of a YAML document."""

    lines = config.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith(f"{key}:") or stripped.startswith(f"- {key}:")):
            continue
        indent = len(line) - len(line.lstrip())
        block = []
        for follow in lines[index + 1:]:
            if follow.strip() and len(follow) - len(follow.lstrip()) <= indent:
                break
            block.append(follow)
        return block
    return []


def site_pages(root: pathlib.Path = ROOT) -> list[pathlib.Path]:
    """Return the guides published to the documentation website, both locales.

    Read nav from mkdocs.yml so newly published guides enter the interface
    checks automatically. `nav` names the default (English) guides once, and
    mkdocs-static-i18n resolves each to its `docs/zh/` counterpart, so that
    derived set is published as well. site_contract verifies both sets against
    exclude_docs and against the files actually on disk.
    """

    names = re.findall(
        r"^\s*-\s+[^:\n]+:\s+([A-Za-z0-9_-]+\.md)\s*$",
        nav_section((root / "mkdocs.yml").read_text()),
        re.M,
    )
    return [root / "docs" / name for name in names] + [
        root / "docs" / "zh" / name for name in names
    ]


def medium_articles(root: pathlib.Path = ROOT) -> list[pathlib.Path]:
    """Return every Medium article that is part of the public interface."""

    return sorted((root / "docs").glob("medium*.md"))


def fenced_blocks(text: str) -> list[str]:
    """Return bodies of complete Markdown backtick or tilde fences."""

    blocks = []
    opening: tuple[str, int] | None = None
    body: list[str] = []
    for line in text.splitlines(keepends=True):
        if opening is None:
            match = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})[^\r\n]*(?:\r?\n)?$", line)
            if match:
                marker = match.group(1)
                opening = (marker[0], len(marker))
                body = []
            continue

        marker, minimum = opening
        if re.match(rf"^[ \t]{{0,3}}{re.escape(marker)}{{{minimum},}}[ \t]*(?:\r?\n)?$", line):
            blocks.append("".join(body))
            opening = None
            body = []
        else:
            body.append(line)
    return blocks


def goal_invocation_lacks_commit_policy(block: str) -> bool:
    """Return whether a fenced GOAL.md invocation omits its commit contract."""

    invokes = "STATUS_ORDER" in block or "Using GOAL.md" in block or "Using tabilet/GOAL.md" in block
    return invokes and "COMMIT_POLICY" not in block


def has_slash_goal_label(text: str) -> bool:
    """Detect the obsolete slash-goal coupling regardless of capitalization."""

    return "slash-goal" in text.casefold()


def suffixed_doc_sibling(path: pathlib.Path) -> pathlib.Path | None:
    """Find a canonical sibling for a suffixed Markdown copy."""

    for separator in ("_", "-", "."):
        base, found, suffix = path.stem.rpartition(separator)
        if found and base and suffix:
            canonical = path.with_name(base + path.suffix)
            if canonical.exists():
                return canonical
    return None


def shipped_archive_files(template_root: pathlib.Path) -> list[pathlib.Path]:
    """Return project-specific archive artifacts anywhere in a template tree."""

    return sorted(template_root.rglob("archive-*.md"))


def archive_execution_refs(text: str) -> list[str]:
    """Return archive IDs that leaked into milestone execution state."""

    return ARCHIVE_EXECUTION_RE.findall(text)


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
    text = path.read_text()
    # `{#id}` is how a translated guide keeps a linkable ASCII anchor: the `toc`
    # extension strips non-ASCII characters from a generated heading id, so a
    # Chinese heading would otherwise carry an id nobody can predict or link to.
    explicit = set(re.findall(r"\{#([^}\s]+)\}", prose(text)))
    return (
        {slug(h) for h in headings(text)}
        | explicit
        | set(re.findall(r'<a\s+id="([^"]+)"\s*></a>', prose(text)))
    )


def init_skill_text() -> str:
    """Return the init workflow and its progressively disclosed write rules."""

    return "\n".join(path.read_text() for path in (INIT_SKILL, INIT_WRITE_CONTRACT) if path.exists())


# --------------------------------------------------------------------------
# 1. The harness must parse. Use ast.parse, never py_compile, which writes
#    __pycache__ into the shipped payload directory.
# --------------------------------------------------------------------------
@check("harness parses, and leaves no bytecode behind")
def harness_parses():
    problems = []
    for path in (HARNESS, AUDIT_MODULE, AUDIT_HOST, ROOT / "harness/tabilet_index.py"):
        try:
            ast.parse(path.read_text())
        except SyntaxError as exc:
            problems.append(f"{path.relative_to(ROOT)} syntax error: {exc}")
    stray = [str(p.relative_to(ROOT)) for p in ROOT.rglob("__pycache__") if ".git" not in p.parts]
    problems.extend(f"stray bytecode directory: {p}" for p in stray)
    return problems


# --------------------------------------------------------------------------
# 1b. The harness is executable payload. Exercise its parser, shell boundary,
#     providers, git gates, and one-row contract without external network calls.
# --------------------------------------------------------------------------
@check("harness behavioral tests pass")
def harness_tests():
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return []
    detail = (proc.stdout + proc.stderr).strip()
    return ["behavioral suite failed:\n" + detail]


# --------------------------------------------------------------------------
# 2. GOAL.md is a portable protocol carried in three places. They must not
#    drift or become coupled to one agent's launcher.
# --------------------------------------------------------------------------
@check("GOAL.md and template/GOAL.md are byte-identical")
def goal_copies():
    # Three copies now: the root one, the project payload, and the one bundled
    # with memory-bank-init so a plugin user gets it without this repo.
    copies = [
        ROOT / "GOAL.md",
        ROOT / "template" / "tabilet" / "GOAL.md",
        SKILLS_DIR / "memory-bank-init" / "GOAL.md",
    ]
    problems = [f"missing {p.relative_to(ROOT)}" for p in copies if not p.exists()]
    if problems:
        return problems
    first = copies[0].read_bytes()
    problems.extend(
        f"{p.relative_to(ROOT)} differs; change all copies together"
        for p in copies[1:]
        if p.read_bytes() != first
    )
    goal = first.decode()
    if has_slash_goal_label(goal):
        problems.append("GOAL.md: protocol must not be limited to a slash-command launcher")
    if "\n/goal\nUsing GOAL.md" in goal:
        problems.append("GOAL.md: portable input must not embed an empty /goal command")
    flat_goal = " ".join(goal.split())
    for token in ("ordinary request", "built-in `/goal`", "does not replace this protocol"):
        if token not in flat_goal:
            problems.append(f"GOAL.md: missing launcher boundary {token!r}")
    return problems


@check("milestone review-fix gate is bounded and aligned")
def review_fix_gate():
    goal = " ".join((ROOT / "GOAL.md").read_text().split())
    milestone = " ".join(
        (ROOT / "template" / "tabilet" / "memory-bank" / "milestone.md").read_text().split()
    )
    write_contract = " ".join(INIT_WRITE_CONTRACT.read_text().split())
    goal_skill = " ".join(
        (SKILLS_DIR / "memory-bank-goal" / "SKILL.md").read_text().split()
    )
    agents = " ".join((ROOT / "AGENTS.md").read_text().split())
    problems = []

    for token in (
        "#### Bounded Review-Fix Gate",
        "The initial deep-review pass is iteration 1",
        "reviews the whole milestone again",
        "Persist the iteration number and findings",
        "Run at most 10 iterations",
        "a session or reviewer change does not reset the counter",
        "do not start another automatic fix-review cycle",
        "Do not begin downstream reconciliation",
        "review-fix iteration count",
    ):
        if token not in goal:
            problems.append(f"GOAL.md: missing review gate contract {token!r}")

    for token in (
        "## Review finding severity",
        "engineering review priorities",
        "not product-domain terms, milestone execution priority, or status markers",
        "impact, likelihood, and affected scope",
        "| P1 |",
        "| P2 |",
        "Project-specific definitions",
        "using the review finding severity context above",
        "The initial deep-review pass is iteration 1",
        "review the whole milestone again",
        "Record the iteration number and findings",
        "Run at most 10 iterations",
        "a session or reviewer change does not reset the counter",
        "start another automatic fix-review cycle",
        "`[!]` review rows",
    ):
        if token not in milestone:
            problems.append(
                f"template/tabilet/memory-bank/milestone.md: missing review gate contract {token!r}"
            )

    for token in (
        "`Review finding severity` section",
        "engineering review priorities rather than product-domain terms",
        "impact, likelihood, and affected scope",
        "initial deep-review pass is iteration 1",
        "Limit it to 10 iterations",
        "persist each iteration number",
        "resetting across sessions or reviewers",
    ):
        if token not in write_contract:
            problems.append(f"write-contract.md: missing review gate contract {token!r}")

    # The launcher delegates the gate; its canonical owners above carry the
    # full rules. Requiring a second copy here encourages protocol drift.
    for token in ("`tabilet/GOAL.md`", "persisted milestone review counter", "incomplete review or closure"):
        if token not in goal_skill:
            problems.append(
                f"memory-bank-goal/SKILL.md: missing review gate contract {token!r}"
            )

    for token in (
        "clean pass",
        "within 10 iterations",
        "does not reset",
        "persist the iteration count",
        "`milestone.md` owns the review-severity context",
    ):
        if token not in agents:
            problems.append(f"AGENTS.md: missing review gate hard rule {token!r}")
    return problems


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
#     ~/.claude/skills or ~/.agents/skills. Both agents read the same SKILL.md
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
    agents = (ROOT / "AGENTS.md").read_text()
    if not SKILLS_DIR.exists():
        return ["skills/ is missing"]
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
        if not fm.get("argument-hint"):
            problems.append(f"{name}/SKILL.md: no argument-hint")
        # Must be present and false. Codex's plugin validator rejects `true`
        # outright -- it installs the plugin, reports success, and surfaces no
        # commands at all. Claude Code accepts either, so false is the only
        # value that works in both.
        if fm.get("disable-model-invocation") != "false":
            problems.append(
                f"{name}/SKILL.md: disable-model-invocation must be false "
                f"(got {fm.get('disable-model-invocation')!r}); Codex rejects true"
            )
    if "`argument-hint`" not in agents:
        problems.append("AGENTS.md: missing the required argument-hint frontmatter rule")
    if not PLUGIN_JSON.exists():
        return problems + [".claude-plugin/plugin.json is missing"]
    listed = sorted(
        p.rsplit("/", 1)[-1] for p in json.loads(PLUGIN_JSON.read_text())["skills"]
    )
    if listed != on_disk:
        problems.append(f"plugin.json lists {listed}, disk has {on_disk}")
    marketplace_path = ROOT / ".claude-plugin/marketplace.json"
    if not marketplace_path.is_file():
        problems.append(".claude-plugin/marketplace.json is missing")
    else:
        marketplace = json.loads(marketplace_path.read_text())
        plugins = [p for p in marketplace.get("plugins", []) if p.get("name") == "memory-bank"]
        if len(plugins) != 1:
            problems.append("marketplace.json must list memory-bank exactly once")
        count_word = {7: "seven"}.get(len(on_disk))
        if not count_word or count_word not in marketplace.get("description", "").lower():
            problems.append("marketplace.json description must name the seven commands")
        if plugins and "propos" not in plugins[0].get("description", "").lower():
            problems.append("marketplace.json plugin description must include Propose")
        if "propos" not in json.loads(PLUGIN_JSON.read_text()).get("description", "").lower():
            problems.append("plugin.json description must include Propose")
    # Both agents reserve /goal for durable objectives; keep the protocol skill
    # distinctly named (and avoid shadowing Claude Code's plain /goal command).
    if "goal" in on_disk:
        problems.append("a skill named 'goal' collides with the agents' built-in goal feature")
    return problems


# --------------------------------------------------------------------------
# 3bb. The generator and the copyable payload must agree on what a project
#      gets. They drifted once already: init omitted GOAL.md while
#      memory-bank-goal required it, so init -> goal dead-ended.
# --------------------------------------------------------------------------
@check("memory-bank-init writes what template/ ships")
def init_covers_template():
    if not INIT_SKILL.exists():
        return ["memory-bank-init/SKILL.md is missing"]
    if not INIT_WRITE_CONTRACT.exists():
        return ["memory-bank-init/references/write-contract.md is missing"]
    blocks = re.findall(r"```text\n(.*?)```", init_skill_text(), re.S)
    block = next(
        (candidate for candidate in blocks if "AGENTS.md" in candidate and "tabilet/memory-bank/product.md" in candidate),
        None,
    )
    if not block:
        return ["memory-bank-init/SKILL.md has no file-list block"]
    listed = {line.split()[0] for line in block.strip().splitlines() if line.strip()}
    shipped = {
        str(p.relative_to(ROOT / "template"))
        for p in (ROOT / "template").rglob("*")
        if p.is_file()
    }
    problems = []
    for f in sorted(shipped):
        # One status file ships as an example; the skill names the pattern.
        if f.startswith("tabilet/memory-bank/status-"):
            if not any(x.startswith("tabilet/memory-bank/status-") for x in listed):
                problems.append("init lists no status-<LANE><NN>.md file")
            continue
        if f not in listed:
            problems.append(f"init never writes {f}, but template/ ships it")
    return problems


# --------------------------------------------------------------------------
# 3bbc. Init derives project-specific multi-milestone input and review
#       reconciliation may refresh it. Keep it disposable, complete, and
#       reconciled by the goal skill rather than turning it into a second
#       roadmap.
# --------------------------------------------------------------------------
@check("init, reconcile, and goal share a disposable goal launch reference")
def suggested_goal_reference():
    goal_path = SKILLS_DIR / "memory-bank-goal" / "SKILL.md"
    required = (
        INIT_SKILL,
        INIT_WRITE_CONTRACT,
        RECONCILE_SKILL,
        RECONCILE_WRITE_CONTRACT,
        goal_path,
    )
    if not all(path.exists() for path in required):
        return ["memory-bank init, reconcile, or goal contract is missing"]

    init = init_skill_text()
    reconcile = " ".join(
        (RECONCILE_SKILL.read_text() + RECONCILE_WRITE_CONTRACT.read_text()).split()
    )
    goal = goal_path.read_text()
    problems = []

    for token in (
        "tabilet/memory-bank/suggested.txt",
        "STATUS_ORDER",
        "STATUS_FILE_MAP",
        "DOWNSTREAM_IMPACTS",
        "COMMIT_POLICY: task",
        "EXTERNAL_MUTATIONS: none",
        "Completion condition:",
    ):
        if token not in init:
            problems.append(f"memory-bank-init/SKILL.md: missing {token}")

    for token in (
        "tabilet/memory-bank/suggested.txt",
        "whole approved active horizon",
        "STATUS_ORDER",
        "STATUS_FILE_MAP",
        "DOWNSTREAM_IMPACTS",
        "COMMIT_POLICY: task",
        "EXTERNAL_MUTATIONS: none",
        "Completion condition:",
        "When no compatible protocol exists",
    ):
        if token not in reconcile:
            problems.append(f"memory-bank-reconcile: missing launch contract {token!r}")

    for token in (
        "tabilet/memory-bank/suggested.txt",
        "STATUS_FILE_MAP",
        "DOWNSTREAM_IMPACTS",
        "Explicit milestone order in the invoking request replaces",
        "not a source of truth",
    ):
        if token not in goal:
            problems.append(f"memory-bank-goal/SKILL.md: missing {token}")

    if "$ARGUMENTS" in goal:
        problems.append("memory-bank-goal must read the invoking request, not runtime substitution")

    if (ROOT / "template" / "tabilet" / "memory-bank" / "suggested.txt").exists():
        problems.append(
            "template/tabilet/memory-bank/suggested.txt must not ship; init or reconcile "
            "derives it from the approved project graph"
        )

    public = [ROOT / "README.md", ROOT / "docs" / "TUTORIAL.md"]
    for path in public:
        if "tabilet/memory-bank/suggested.txt" not in path.read_text():
            problems.append(
                f"{path.relative_to(ROOT)}: missing disposable goal launch reference"
            )

    for path in public:
        text = path.read_text().lower()
        if "compatible" not in text or "omit" not in text:
            problems.append(
                f"{path.relative_to(ROOT)}: launch-reference guidance must cover "
                "compatible and omitted goal protocols"
            )
    return problems


@check("memory-bank-init preserves adaptive discovery and rolling horizons")
def adaptive_init_contract():
    if not INIT_SKILL.exists() or not INIT_WRITE_CONTRACT.exists():
        return ["memory-bank-init workflow or write contract is missing"]

    skill = INIT_SKILL.read_text()
    write_contract = INIT_WRITE_CONTRACT.read_text()
    milestone = (ROOT / "template" / "tabilet" / "memory-bank" / "milestone.md").read_text()
    agents = (ROOT / "AGENTS.md").read_text()
    write_contract_words = " ".join(write_contract.split())
    agents_words = " ".join(agents.split())
    problems = []

    for token in (
        "design tree",
        "evidence ledger",
        "frontier",
        "whole frontier",
        "one coherent product, ownership, and verification",
        "active horizon",
        "candidate directions",
        "references/write-contract.md",
        "enough active work to drown",
        "own review cadence",
        "different acceptance method",
        "Gate broad existing packages",
        "memory-bank-archive",
        "cheap topology",
        "numeric file or",
        "every context in the selected boundary is `verified`",
        "frozen baselines",
        "Several independent stable contexts",
        "even\nwhen their current implementations are short",
        "A matching archive and status lane/number is not an ID collision",
    ):
        if token not in skill:
            problems.append(f"memory-bank-init/SKILL.md: missing adaptive contract {token!r}")

    proposal = skill.split("## Phase 2 - Propose", 1)[-1].split("## Phase 3 - Write", 1)[0]
    if "references/write-contract.md" not in proposal or "grants no writing authority" not in proposal:
        problems.append("memory-bank-init: load the write contract before proposing, without write authority")
    if ("Read this reference during Phase 2" not in write_contract_words
            or "writes only after the user approves the complete proposal" not in write_contract_words
            or "Read this reference only after" in write_contract_words):
        problems.append("memory-bank-init: the reference must allow pre-proposal reads and gate only writes")

    for stale in (
        "### The tree",
        "**One question at a time.**",
        "from question 4",
        "the first milestone's rows",
    ):
        if stale in skill:
            problems.append(f"memory-bank-init/SKILL.md retains fixed interview wording {stale!r}")

    for token in (
        "Never silently overwrite an existing file",
        "Candidate directions are not milestones",
        "Never put a candidate direction",
        "Create `tabilet/memory-bank/suggested.txt` only when",
        "Otherwise omit the launch reference",
        "sibling `GOAL.md`",
        "provider-specific plugin-root environment variables",
        "A trailing `?` is allowed only",
        "concrete project-state trigger",
        "discretionary",
        "Preserve every verified `tabilet/docs/archive-<LANE><NN>.md` byte-for-byte",
        "independent namespace",
    ):
        if token not in write_contract_words:
            problems.append(f"write-contract.md: missing {token!r}")

    for stale in ("${CLAUDE_PLUGIN_ROOT}", "M01 -> S01 -> A01?"):
        if stale in write_contract:
            problems.append(f"write-contract.md retains unsafe example or path {stale!r}")

    for token in (
        "## Candidate Directions",
        "have no lane, permanent status ID, status file",
        "obtain approval before allocating its permanent ID",
    ):
        if token not in milestone:
            problems.append(f"template/tabilet/memory-bank/milestone.md: missing {token!r}")

    for token in (
        "approved compatible `GOAL.md`",
        "documented conditionally required active work",
        "adaptive topology gate",
        "must first use `memory-bank-archive`",
    ):
        if token not in agents_words:
            problems.append(f"AGENTS.md: missing init hard rule {token!r}")
    return problems


@check("archive skill preserves frozen fact baselines outside execution state")
def archive_contract():
    if not ARCHIVE_SKILL.exists() or not ARCHIVE_WRITE_CONTRACT.exists():
        return ["memory-bank-archive skill or write contract is missing"]

    skill = ARCHIVE_SKILL.read_text()
    contract = ARCHIVE_WRITE_CONTRACT.read_text()
    agents = (ROOT / "AGENTS.md").read_text()
    template_agents = (ROOT / "template" / "AGENTS.md").read_text()
    architecture = (ROOT / "template" / "tabilet" / "memory-bank" / "architecture.md").read_text()
    problems = []

    for token in (
        "Three phases: **survey**, **propose**, **write**",
        "Require a clean worktree, including untracked files",
        "one coherent product boundary",
        "Archive lanes are independent from status lanes",
        "Coverage is `partial`, `blocked`, or `verified`",
        "Do not turn an observed gap into a milestone",
        "material change to high-level",
        "references/write-contract.md",
    ):
        if token not in skill:
            problems.append(f"memory-bank-archive/SKILL.md: missing {token!r}")

    for token in (
        "tabilet/docs/archive-<LANE><NN>.md",
        "Treat a verified archive as frozen",
        "separate namespace from status lanes",
        "Numbers record snapshot chronology",
        "**Baseline.** <full Git commit, or `unversioned`>",
        "**Coverage.** verified",
        "## Evidence",
        "## Archive baselines",
        "Create or merge current observed facts",
        "Initialization may proceed only when every context",
        "No milestone, candidate direction, status row, goal order, commit, or",
    ):
        if token not in contract:
            problems.append(f"archive write-contract.md: missing {token!r}")

    for text, label, tokens in (
        (
            agents,
            "AGENTS.md",
            (
                "### Archive ID lanes",
                "Archive IDs never appear in milestone indexes",
                "writes facts, not plans",
            ),
        ),
        (
            template_agents,
            "template/AGENTS.md",
            (
                "Verified `tabilet/docs/archive-<LANE><NN>.md` files are frozen",
                "independently from status lanes",
                "Keep verified archive files frozen",
            ),
        ),
        (
            architecture,
            "template/tabilet/memory-bank/architecture.md",
            ("## Archive baselines", "No archive baseline is registered"),
        ),
    ):
        for token in tokens:
            if token not in text:
                problems.append(f"{label}: missing archive contract {token!r}")

    shipped_archives = shipped_archive_files(ROOT / "template")
    if shipped_archives:
        shipped = ", ".join(str(path.relative_to(ROOT)) for path in shipped_archives)
        problems.append(f"template/ ships project-specific archive files: {shipped}")

    for path in (ROOT / "docs").glob("archive-*.md"):
        if not re.fullmatch(r"archive-[A-Z][0-9][0-9]\.md", path.name):
            problems.append(f"{path.relative_to(ROOT)}: invalid archive filename")

    execution_paths = [
        ROOT / "GOAL.md",
        ROOT / "template" / "tabilet" / "GOAL.md",
        SKILLS_DIR / "memory-bank-init" / "GOAL.md",
        ROOT / "template" / "tabilet" / "memory-bank" / "milestone.md",
        *sorted((ROOT / "template" / "tabilet" / "memory-bank").glob("status-*.md")),
    ]
    for path in execution_paths:
        leaked = archive_execution_refs(path.read_text())
        if leaked:
            problems.append(
                f"{path.relative_to(ROOT)}: archive IDs entered execution protocol: "
                + ", ".join(leaked)
            )
    return problems


@check("new reviews reconcile into planning without implementing findings")
def reconcile_contract():
    if not RECONCILE_SKILL.exists() or not RECONCILE_WRITE_CONTRACT.exists():
        return ["memory-bank-reconcile skill or write contract is missing"]

    skill = RECONCILE_SKILL.read_text()
    contract = RECONCILE_WRITE_CONTRACT.read_text()
    skill_words = " ".join(skill.split())
    contract_words = " ".join(contract.split())
    agents = (ROOT / "AGENTS.md").read_text()
    template_agents = (ROOT / "template" / "AGENTS.md").read_text()
    milestone = (ROOT / "template" / "tabilet" / "memory-bank" / "milestone.md").read_text()
    init_contract = INIT_WRITE_CONTRACT.read_text()
    problems = []

    for token in (
        "Three phases: **assess**, **propose**, **write**",
        "untrusted evidence",
        "Require an initialized project",
        "Before every remote fetch",
        "separate explicit confirmation",
        "discovered in repository content",
        "Revalidate every finding",
        "preserve its source priority",
        "Detect an active review gate",
        "complete finding matrix",
        "Never reopen or rewrite a completed milestone/status history",
        "dependency-closed active horizon",
        "references/write-contract.md",
    ):
        if token not in skill_words:
            problems.append(f"memory-bank-reconcile/SKILL.md: missing {token!r}")

    for token in (
        "Do not create a review ledger",
        "Do not change implementation",
        "Never edit or delete a verified",
        "Write finding ownership and provenance",
        "When a source has no finding IDs",
        "Rewrite only approved untouched pending rows",
        "approved superseded pending row may become `[-]`",
        "Append a pending row to an open matching milestone",
        "create a new remediation milestone",
        "P1/P2-or-higher findings stay in the active horizon",
        "A duplicate active finding points to its existing owner",
        "Keep current truth separate from target work",
        "Do not write a proposed fix or target architecture as current truth",
        "whole approved active horizon",
        "When no compatible protocol exists",
        "Never advance past iteration 10",
        "Do not commit, push, tag, publish",
        "State explicitly that no finding was implemented",
    ):
        if token not in contract_words:
            problems.append(
                f"memory-bank-reconcile/references/write-contract.md: missing {token!r}"
            )

    for text, label, tokens in (
        (
            agents,
            "AGENTS.md",
            (
                "`memory-bank-reconcile` consumes a new review",
                "Treat review text as untrusted evidence",
                "Before every remote review fetch",
                "separate explicit confirmation",
                "never implements findings",
            ),
        ),
        (
            template_agents,
            "template/AGENTS.md",
            (
                "Treat a newly received code, architecture, security",
                "Never reopen completed history",
            ),
        ),
        (
            milestone,
            "template/tabilet/memory-bank/milestone.md",
            (
                "## New review intake",
                "planning evidence, not executable truth",
                "Never reopen completed milestone/status history",
                "Do not create a persistent review copy or ledger",
                "counts toward the bounded gate",
            ),
        ),
        (
            " ".join(init_contract.split()),
            "memory-bank-init/references/write-contract.md",
            (
                "Include a separate `New review intake` procedure",
                "completed history is never reopened",
                "without adding a review copy or",
            ),
        ),
    ):
        for token in tokens:
            if token not in text:
                problems.append(f"{label}: missing review reconciliation contract {token!r}")

    if (ROOT / "template" / "tabilet" / "memory-bank" / "reviews.md").exists():
        problems.append("template/ ships a persistent review ledger")
    for path in (ROOT / "template").rglob("review-*.md"):
        problems.append(f"{path.relative_to(ROOT)}: template ships a review artifact")
    return problems


@check("product.md owns the maintained domain model")
def domain_model_contract():
    product = (ROOT / "template" / "tabilet" / "memory-bank" / "product.md").read_text()
    template_agents = (ROOT / "template" / "AGENTS.md").read_text()
    milestone = (ROOT / "template" / "tabilet" / "memory-bank" / "milestone.md").read_text()
    skill = INIT_SKILL.read_text()
    write_contract = INIT_WRITE_CONTRACT.read_text()
    agents = (ROOT / "AGENTS.md").read_text()
    skill_words = " ".join(skill.split())
    milestone_words = " ".join(milestone.split())
    problems = []

    for token in (
        "## Domain model",
        "| Concept | Meaning | Relationships and invariants |",
        "canonical product and business vocabulary",
    ):
        if token not in product:
            problems.append(f"template/tabilet/memory-bank/product.md: missing {token!r}")

    for token in (
        "canonical domain and",
        "relationships, cardinality, lifecycles, and invariants",
        "domain model and business invariants",
    ):
        if token not in skill_words:
            problems.append(f"memory-bank-init/SKILL.md: missing {token!r}")

    for token in (
        "canonical product and business",
        "technical storage and implementation details",
        "Do not create a parallel `context.md`",
    ):
        if token not in write_contract:
            problems.append(f"write-contract.md: missing {token!r}")

    if "domain terminology/concept relationships/business invariants" not in template_agents:
        problems.append("template/AGENTS.md does not route domain-model changes to product.md")
    for token in ("domain terminology", "concept relationships", "business invariants"):
        if token not in milestone_words:
            problems.append(f"template/tabilet/memory-bank/milestone.md: missing {token!r}")
    if "`tabilet/memory-bank/context.md`" not in agents:
        problems.append("AGENTS.md does not forbid a parallel tabilet/memory-bank/context.md")
    if (ROOT / "template" / "tabilet" / "memory-bank" / "context.md").exists():
        problems.append("template ships context.md alongside the product-owned domain model")
    if "Review finding severity" in product:
        problems.append("product.md contains engineering review severity terminology")
    return problems


# --------------------------------------------------------------------------
# 3bc. A registry reads plugin.json's version from the default branch, so a
#      tag and a manifest that disagree ship a version claiming to be another.
# --------------------------------------------------------------------------
def version_tuple(v: str) -> tuple:
    return tuple(int(p) for p in v.split("."))


@check("plugin.json version agrees with the git tags")
def plugin_version():
    import json

    if not PLUGIN_JSON.exists():
        return [".claude-plugin/plugin.json is missing"]
    version = json.loads(PLUGIN_JSON.read_text()).get("version")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version or ""):
        return [f"plugin.json version is {version!r}, want MAJOR.MINOR.PATCH"]

    def git(*args):
        p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return p.stdout.split() if p.returncode == 0 else []

    tags = [t for t in git("tag", "--list", "v*") if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    if not tags:
        # A shallow clone without tags cannot answer this. Say so rather than
        # passing silently -- CI must fetch tags for this check to mean anything.
        return ["no v* tags found; fetch tags so this check can run"]

    latest = max(tags, key=lambda t: version_tuple(t[1:]))
    here = [t for t in git("tag", "--points-at", "HEAD") if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    if here:
        # At a tagged commit the two must be identical: this is what a registry
        # and a release download would disagree about.
        exact = max(here, key=lambda t: version_tuple(t[1:]))
        if exact[1:] != version:
            return [f"HEAD is tagged {exact} but plugin.json says {version}"]
        return []
    if version_tuple(version) < version_tuple(latest[1:]):
        return [f"plugin.json says {version}, behind the latest tag {latest}"]
    return []


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


@check("v2 layout and explicit v1.5 migration stay enforced")
def v2_migration_contract():
    problems = []
    template = ROOT / "template"
    bundle = SKILLS_DIR / "memory-bank-upgrade" / "assets" / "template"
    for root in (template, bundle):
        for old in ("GOAL.md", "memory-bank", "evolution", "docs/history"):
            if (root / old).exists():
                problems.append(f"{root.relative_to(ROOT)}/{old}: legacy payload path")
        if not (root / "tabilet" / "memory-bank" / "milestone.md").is_file():
            problems.append(f"{root.relative_to(ROOT)}: missing v2 milestone")
    migration = SKILLS_DIR / "memory-bank-upgrade" / "migrate-v1.5-to-v2.py"
    if not migration.is_file():
        problems.append("Upgrade migration CLI is missing")
    else:
        try:
            ast.parse(migration.read_text())
        except SyntaxError as exc:
            problems.append(f"migration CLI syntax error: {exc}")
    for skill in SKILLS_DIR.glob("*/SKILL.md"):
        if "migrate-v1.5-to-v2.py" not in skill.read_text():
            problems.append(f"{skill.relative_to(ROOT)}: missing legacy layout gate")
    runner = HARNESS.read_text()
    for token in ("legacy =", "migrate-v1.5-to-v2.py", 'repo / "tabilet" / "memory-bank"'):
        if token not in runner:
            problems.append(f"API runner: missing v2 contract {token!r}")
    return problems


# --------------------------------------------------------------------------
# 4. GOAL.md defaults COMMIT_POLICY to `none`. An example that omits it
#    quietly promises no commits at all.
# --------------------------------------------------------------------------
@check("every GOAL.md invocation sets an explicit COMMIT_POLICY")
def goal_examples():
    # Keyed on naming GOAL.md, not on `/goal`. Claude Code and Codex have a
    # built-in `/goal <objective>` persistence layer that is distinct from this
    # protocol; requiring COMMIT_POLICY for unrelated built-in goals would be
    # wrong. The protocol requires its request to name the file, so that is the
    # honest anchor.
    problems = []
    for md in markdown_files():
        if md.name == "GOAL.md":  # the protocol itself documents the default
            continue
        for block in fenced_blocks(md.read_text()):
            # "GOAL.md" alone is too loose: a file tree that merely lists the
            # file is not an invocation. Key on the two things only a real
            # invocation carries.
            if goal_invocation_lacks_commit_policy(block):
                problems.append(
                    f"{md.relative_to(ROOT)}: GOAL.md invocation without COMMIT_POLICY"
                )
    return problems


# --------------------------------------------------------------------------
# 5. Links and heading anchors.
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


@check("published guides match MkDocs navigation and website rules")
def site_contract():
    config = (ROOT / "mkdocs.yml").read_text()
    pages = site_pages()
    docs = ROOT / "docs"
    names = [str(page.relative_to(docs)) for page in pages]
    allowed = re.findall(r"^\s*!/((?:zh/)?[A-Za-z0-9_-]+\.md)\s*$", config, re.M)
    problems = []
    if not names or len(names) != len(set(names)):
        problems.append("mkdocs.yml nav must list each published guide exactly once")
    if set(names) != set(allowed) or len(allowed) != len(set(allowed)):
        problems.append("mkdocs.yml nav and exclude_docs guide allowlist differ")
    for page in pages:
        if not page.is_file():
            problems.append(f"mkdocs.yml nav points to missing guide {page.relative_to(docs)}")

    # The site is published in two locales by mkdocs-static-i18n: `nav` names
    # the English guides once and the plugin resolves each to docs/zh/. A label
    # missing from nav_translations leaves the Chinese pages showing an English
    # tab, which is the exact regression the translated site exists to prevent.
    requirements = (ROOT / "docs/requirements.txt").read_text()
    if "mkdocs-static-i18n" not in requirements:
        problems.append("docs/requirements.txt must pin mkdocs-static-i18n for the translated site")
    i18n = yaml_block(config, "i18n")
    if not i18n:
        problems.append("mkdocs.yml must configure the i18n plugin for the translated site")
    else:
        joined = "\n".join(i18n)
        if "docs_structure: folder" not in joined:
            problems.append("the i18n plugin must use docs_structure: folder")
        if "locale: en" not in joined or "locale: zh" not in joined:
            problems.append("the i18n plugin must declare the en and zh locales")
        if "default: true" not in joined:
            problems.append("the i18n plugin must mark one locale as the default")
        labels = re.findall(r"^\s*-\s+([^:\n]+?):", nav_section(config), re.M)
        translated = set()
        for line in yaml_block(config, "nav_translations"):
            match = re.match(r"\s*([^:\n]+?):", line)
            if match:
                translated.add(match.group(1).strip())
        missing = sorted({label.strip() for label in labels} - translated)
        if missing:
            problems.append(
                "mkdocs.yml nav_translations must translate every nav label; "
                f"missing {', '.join(missing)}"
            )

    # The translated site is a mirror, not a subset: every published English
    # guide has exactly one Simplified Chinese counterpart and no orphan.
    english = sorted(page.name for page in pages if page.parent.name != "zh")
    chinese = sorted(page.name for page in pages if page.parent.name == "zh")
    on_disk = sorted(path.name for path in (ROOT / "docs" / "zh").glob("*.md"))
    if not chinese:
        problems.append("docs/zh/ must publish a Simplified Chinese translation of every guide")
    elif english != chinese or on_disk != chinese:
        problems.append("docs/zh/ must translate every published guide one-for-one, with no orphan")

    index = (ROOT / "docs/index.md").read_text()
    routing = index.partition("## Choose your starting point")[2].partition("## What stays in your project")[0]
    rows = [line for line in routing.splitlines() if line.startswith("|")]
    if not rows or any(row.count("|") != 3 for row in rows):
        problems.append("docs/index.md starting-point table must have two cells per row")
    review = [row for row in rows if row.startswith("| Has a new engineering review |")]
    if len(review) != 1 or "[Reconcile](reconcile.md)" not in review[0]:
        problems.append("docs/index.md must route engineering reviews to Reconcile")
    feature = [row for row in rows if row.startswith("| Has a requested feature or candidate promotion |")]
    if len(feature) != 1 or "[Propose](propose.md)" not in feature[0]:
        problems.append("docs/index.md must route requested features to Propose")

    agents = (ROOT / "AGENTS.md").read_text()
    readme = (ROOT / "README.md").read_text()
    workflow = (ROOT / ".github/workflows/deploy-docs.yml").read_text()
    for token in ("mkdocs.yml", "docs/requirements.txt", ".github/workflows/deploy-docs.yml", "mkdocs build --strict"):
        if token not in agents:
            problems.append(f"AGENTS.md: missing website rule {token}")
    if "https://tabilet.github.io/skills/" not in readme:
        problems.append("README.md must link the website")
    if "group: ${{ github.workflow }}-${{ github.ref }}" not in workflow:
        problems.append("docs deployment concurrency must be scoped to workflow and ref")
    if "docs_hooks.py" in config or (ROOT / "docs_hooks.py").exists():
        problems.append("unused docs_hooks.py must not be loaded by MkDocs")
    return problems


@check("translated guides resolve local references and explicit anchors")
def translated_references():
    """Check the two things the MkDocs validator and `links()` both miss.

    `links()` reads Markdown link syntax only, so the raw-HTML `src`/`href` of
    the front-page hero is invisible to it — and because a translation sits one
    directory deeper, a copied `assets/...` path silently points at
    `docs/zh/assets/...`, which no build fails on. Separately, `anchors()`
    slugs a heading the way GitHub does, keeping Chinese characters, while the
    MkDocs `toc` extension strips them from the id it builds, so a translated
    `#安装` resolves for the checker while 404ing in a browser. A translated
    guide therefore links only to anchors it declared explicitly with `{#id}`.
    """

    zh = ROOT / "docs" / "zh"
    if not zh.is_dir():
        return ["docs/zh/: the translated site is missing"]
    problems = []
    for path in sorted(zh.glob("*.md")):
        text = path.read_text()
        references = re.findall(r"\]\(([^)\s]+)\)", prose(text))
        references += re.findall(r'(?:src|href)="([^"]+)"', text)
        for target in references:
            if target.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            file_part, _, fragment = target.partition("#")
            dest = (path.parent / file_part).resolve() if file_part else path.resolve()
            if not dest.is_file():
                problems.append(
                    f"{path.relative_to(ROOT)}: local reference {target} does not resolve"
                )
                continue
            if not fragment:
                continue
            explicit = set(re.findall(r"\{#([^}\s]+)\}", prose(dest.read_text())))
            if fragment not in explicit:
                problems.append(
                    f"{path.relative_to(ROOT)}: #{fragment} needs an explicit "
                    f"{{#{fragment}}} anchor on a heading in {file_part or path.name}"
                )
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
# 7. The backtick contract: the row parser reads only backticked markers;
#    validation must reject malformed markers instead of reporting no work.
# --------------------------------------------------------------------------
@check("status parser matches the shipped template rows")
def status_markers():
    mod = load_harness()
    template = (ROOT / "template" / "tabilet" / "memory-bank" / "status-M01.md").read_text()
    agents = (ROOT / "AGENTS.md").read_text()
    problems = []
    expected = {
        "`[ ]`": "pending",
        "`[+]`": "completed",
        "`[~]`": "in_progress",
        "`[!]`": "blocked",
        "`[X]`": "cancelled",
        "`[-]`": "historical",
    }
    if mod.STATE_MARKERS != expected:
        problems.append(f"harness state markers are {mod.STATE_MARKERS}, want {expected}")
    if mod.ACTIONABLE_STATES != {"pending", "in_progress"}:
        problems.append("only pending and in-progress rows may be actionable")
    if mod.RUN_TERMINAL_STATES != {"completed", "blocked", "historical"}:
        problems.append("runner terminal states must include completed, blocked, and historical")

    parsed = mod.status_rows(
        "\n".join(f"| {state} | {marker} | Notes. |" for marker, state in expected.items())
    )
    if [row["state"] for row in parsed] != list(expected.values()):
        problems.append("the parser does not recognize the complete status-marker vocabulary")
    if any(row["state"] == "historical" for row in mod.actionable_rows(template)):
        problems.append("closed-historical rows are actionable")

    for text, label, tokens in (
        (
            template,
            "template/tabilet/memory-bank/status-M01.md",
            (
                "`[-]` | Closed Historical",
                "consumed failed attempt or superseded row retained for audit",
                "never retried and does not block its accepted successor",
                "zero or one general row may be `[~]`",
                "exact authorized operation row to be `[~]`",
                "rejects malformed task markers with exit `11`",
            ),
        ),
        (
            agents,
            "AGENTS.md",
            (
                "`[-]` closed historical evidence",
                "never retried",
                "does not block its accepted successor",
                "zero or one general row may be `[~]`",
            ),
        ),
    ):
        normalized = " ".join(text.split())
        for token in tokens:
            if token not in normalized:
                problems.append(f"{label}: missing status contract {token!r}")

    if not mod.actionable_rows(template):
        problems.append("template/tabilet/memory-bank/status-M01.md has no rows the harness sees as actionable")
    # Invalid markers must never become executable work or evade validation.
    if mod.actionable_rows("| Item | [ ] | Notes. |\n"):
        problems.append("a bare [ ] row now parses as actionable; the documented warning is stale")
    if not mod.actionable_rows("| Item | `[ ]` | Notes. |\n"):
        problems.append("a backticked [ ] row no longer parses as actionable")
    if not mod.status_marker_problems("| Item | [ ] | Notes. |\n"):
        problems.append("a bare marker must be rejected before no-work detection")
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
        lanes = list((dest / "tabilet" / "memory-bank").glob("status-[A-Z][0-9][0-9].md"))
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
                "LLM_MAX_RETRIES": "0", "ALLOW_UNSANDBOXED_SHELL": "1",
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

    def capture(url, headers, payload, label, timeout=120, max_retries=2):
        sampled[label] = payload
        return {
            "content": [{"type": "text", "text": "{}"}],
            "choices": [{"message": {"content": "{}"}}],
        }

    original, mod._post_json = mod._post_json, capture
    try:
        messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
        mod.call_anthropic("https://example/v1", "k", "claude-opus-5", messages, None, 16000)
        mod.call_openai("https://example/v1", "k", "gpt-5.6", messages, None, 16000)
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
# 10. Repository documentation is English-only. Language-suffixed copies used
#     to drift behind the canonical files, so reject them rather than merely
#     comparing their heading counts.
# --------------------------------------------------------------------------
@check("repository documentation stays English-only outside the translated site")
def english_only_docs():
    problems = []
    # docs/zh/ is the one sanctioned translation: the published guides ship in
    # Simplified Chinese, and site_contract holds the two sets in one-for-one
    # parity so a translation cannot silently drift or go stale. Everywhere
    # else in docs/, a language-suffixed copy of a canonical file is rejected.
    for path in sorted((ROOT / "docs").rglob("*.md")):
        canonical = suffixed_doc_sibling(path)
        if canonical is not None and canonical.name == "sqlite.md" and re.fullmatch(r"sqlite-[1-8]", path.stem):
            continue
        if canonical is not None:
            problems.append(
                f"{path.relative_to(ROOT)}: suffixed copy of "
                f"{canonical.relative_to(ROOT)} is not shipped"
            )
    for path in sorted(ROOT.glob("README_*.md")):
        problems.append(f"{path.name}: README.md is the only shipped README")
    # Markers that must remain in the English-only README.
    for marker, label in (
        ("LLM_PROVIDER=anthropic", "Anthropic provider example"),
        ("COMMIT_POLICY: task", "goal-loop invocation"),
        ("git clone https", "clone step"),
    ):
        if marker not in (ROOT / "README.md").read_text():
            problems.append(f"README.md: missing {label}")
    return problems


# --------------------------------------------------------------------------
# 11. Public setup and invocation examples are an interface. Keep plugin
#     namespaces, personal skill paths, and model examples from drifting back
#     to obsolete product behavior.
# --------------------------------------------------------------------------
@check("public invocation, installation, model, and locale guidance is current")
def public_interfaces():
    problems = []
    readmes = [ROOT / "README.md"]
    public = (
        readmes
        + [ROOT / "docs" / "TUTORIAL.md", ROOT / "docs" / "USE_CASES.md", *medium_articles()]
        + site_pages()
        + sorted(SKILLS_DIR.glob("*/SKILL.md"))
    )

    plugin_tokens = (
        "/memory-bank:memory-bank-archive",
        "/memory-bank:memory-bank-init",
        "/memory-bank:memory-bank-propose",
        "/memory-bank:memory-bank-upgrade",
        "/memory-bank:memory-bank-reconcile",
        "/memory-bank:memory-bank-next",
        "/memory-bank:memory-bank-goal",
        "$memory-bank:memory-bank-archive",
        "$memory-bank:memory-bank-init",
        "$memory-bank:memory-bank-propose",
        "$memory-bank:memory-bank-upgrade",
        "$memory-bank:memory-bank-reconcile",
        "$memory-bank:memory-bank-next",
        "$memory-bank:memory-bank-goal",
    )
    for path in readmes + [ROOT / "docs" / "TUTORIAL.md"]:
        text = path.read_text()
        for token in plugin_tokens:
            if token not in text:
                problems.append(f"{path.relative_to(ROOT)}: missing plugin invocation {token}")

    for path in readmes + [ROOT / "docs" / "TUTORIAL.md"]:
        if "~/.agents/skills" not in path.read_text():
            problems.append(f"{path.relative_to(ROOT)}: missing Codex personal skill path")

    goal_guides = [
        ROOT / "README.md",
        ROOT / "docs" / "TUTORIAL.md",
        SKILLS_DIR / "memory-bank-goal" / "references" / "runtime-help.md",
    ]
    codex_goal_tokens = (
        "https://learn.chatgpt.com/use-cases/follow-goals",
        "/goal pause",
        "/goal resume",
        "codex features enable goals",
    )
    for path in goal_guides:
        text = path.read_text()
        for token in codex_goal_tokens:
            if token not in text:
                problems.append(
                    f"{path.relative_to(ROOT)}: missing current Codex goal guidance {token!r}"
                )

    model_catalogs = (
        "https://developers.openai.com/api/docs/models",
        "https://platform.claude.com/docs/en/about-claude/models/overview",
    )
    for path in readmes:
        text = path.read_text()
        if "gpt-5.6" not in text or "claude-opus-5" not in text:
            problems.append(f"{path.relative_to(ROOT)}: missing current model examples")
        for catalog in model_catalogs:
            if catalog not in text:
                problems.append(f"{path.relative_to(ROOT)}: missing model catalog {catalog}")
    if "gpt-5.6" not in HARNESS.read_text() or "claude-opus-5" not in HARNESS.read_text():
        problems.append("harness help is missing current model examples")

    forbidden = {
        "~/" + ".codex/skills": "obsolete Codex personal skill path",
        "~/" + ".codex/prompts": "deprecated Codex custom-prompt installation",
        "drop the " + "slash": "obsolete Codex invocation advice",
        "gpt-5" + ".5": "obsolete OpenAI model example",
        "/goal " + "active": "obsolete Claude Code goal-status syntax",
        "In Codex, use the namespaced plugin skill": "obsolete Claude-only built-in goal guidance",
    }
    for path in public + [HARNESS, ROOT / "AGENTS.md"]:
        if not path.is_file():
            problems.append(f"missing public interface file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text()
        for needle, label in forbidden.items():
            if needle in text:
                problems.append(f"{path.relative_to(ROOT)}: {label}")

    prompt_name = "tackle-next-memory-bank-todo.md"
    for path in readmes:
        for block in re.findall(r"```(?:bash|sh)\n(.*?)```", path.read_text(), re.S):
            if prompt_name in block:
                problems.append(
                    f"{path.relative_to(ROOT)}: installs the human-readable prompt copy"
                )

    return problems


@check("Medium publishing assets have article owners")
def medium_publishing_assets():
    problems = []
    agents = (ROOT / "AGENTS.md").read_text()
    if "`docs/medium*-infographic.png`" not in agents:
        problems.append("AGENTS.md: missing the Medium publishing-asset ownership rule")

    for image in sorted((ROOT / "docs").glob("medium*-infographic.png")):
        article_name = image.name.removesuffix("-infographic.png") + ".md"
        article = image.with_name(article_name)
        if not article.exists():
            problems.append(
                f"{image.relative_to(ROOT)}: no corresponding docs/{article_name}"
            )
        elif image.name not in article.read_text():
            problems.append(
                f"{image.relative_to(ROOT)}: publishing role is not documented in "
                f"{article.relative_to(ROOT)}"
            )
    return problems


@check("public harness guidance carries the host-shell safety contract")
def harness_safety_contract():
    problems = []
    public = [ROOT / "README.md", ROOT / "docs" / "EXECUTION.md"]
    for path in public:
        text = path.read_text()
        for token in ("ALLOW_UNSANDBOXED_SHELL=1", "TOOL_ENV_ALLOW"):
            if token not in text:
                problems.append(f"{path.relative_to(ROOT)}: missing {token}")

    source = HARNESS.read_text()
    if '["bash", "-lc", cmd]' in source:
        problems.append("harness launches a login shell and can load user profiles")
    for token in ("ALLOW_UNSANDBOXED_SHELL", "tool_environment", "validate_row_transition"):
        if token not in source:
            problems.append(f"harness is missing safety mechanism {token}")
    return problems


@check("template examples preserve row and status-ID contracts")
def template_row_contracts():
    problems = []
    result = (ROOT / "template" / "tabilet" / "evolution" / "result-v1.md").read_text()
    for stale in ("**M1**", "**M2**"):
        if stale in result:
            problems.append(f"template/tabilet/evolution/result-v1.md uses unpadded {stale}")

    status = (ROOT / "template" / "tabilet" / "memory-bank" / "status-M01.md").read_text()
    if "multiple rows are inseparable" in status:
        problems.append("status-M01.md permits several rows in one commit")
    normalized_status = " ".join(status.split())
    for token in (
        "`[-]` | Closed Historical",
        "zero or one general row may be `[~]`",
        "exact authorized operation row to be `[~]`",
    ):
        if token not in normalized_status:
            problems.append(f"status-M01.md is missing row-state contract {token!r}")

    milestone = (ROOT / "template" / "tabilet" / "memory-bank" / "milestone.md").read_text()
    if "Do not create an extra milestone commit" not in milestone:
        problems.append("milestone.md does not forbid empty review commits")
    normalized_milestone = " ".join(milestone.split())
    for token in (
        "Completed `[+]`, cancelled `[X]`, and closed-historical `[-]` rows are non-actionable",
        "every `[-]` row must name its accepted successor",
    ):
        if token not in normalized_milestone:
            problems.append(f"milestone.md is missing historical-row contract {token!r}")

    init_contract = (
        ROOT / "skills" / "memory-bank-init" / "references" / "write-contract.md"
    ).read_text()
    reconcile_contract = (
        ROOT / "skills" / "memory-bank-reconcile" / "references" / "write-contract.md"
    ).read_text()
    for text, label in (
        (init_contract, "memory-bank-init write contract"),
        (reconcile_contract, "memory-bank-reconcile write contract"),
    ):
        normalized = " ".join(text.split())
        for token in ("`[-]`", "zero or one"):
            if token not in normalized:
                problems.append(f"{label} is missing row-state contract {token!r}")
    return problems


@check("long-term memory contract preserves portable retirement records")
def long_term_memory():
    problems = []
    milestone = (ROOT / "template/tabilet/memory-bank/milestone.md").read_text()
    sample = next(
        (block for block in fenced_blocks(milestone) if block.startswith("# Retired milestone")),
        "",
    )
    values = {
        "<title>": "Delivery",
        "<YYYY-MM-DD>": "2026-09-12",
        "<original-anchor>": "m01-delivery",
        "<full commit or unversioned>": "unversioned",
        "<clean, includes uncommitted changes, or unversioned>": "unversioned",
        "<1 through 10>": "1",
        "<commands, results, and supporting evidence>": "Tests and review passed.",
        "<current-document and lesson links, or no current-truth change>": "no current-truth change",
        "<Complete final milestone specification, not a summary.>": "## M01 - Delivery\n\n**Acceptance.** Verified.",
        "<Complete final status document, not a summary.>": "# Status M01\n\n| Task | `[+]` | Verified. |",
    }
    for placeholder, value in values.items():
        sample = sample.replace(placeholder, value)
    try:
        record = load_harness().retired_record(sample, "status-M01.md")
        if "**Acceptance.** Verified." not in record["specification"]:
            problems.append("retirement envelope lost the original specification")
    except ValueError as exc:
        problems.append(f"shipped retirement envelope cannot be read by the harness: {exc}")

    for relative, tokens in (
        ("AGENTS.md", ("lessons.md", "tabilet/docs/history/knowledge.md", "reserve IDs", "commit policy")),
        ("template/AGENTS.md", ("tabilet/memory-bank/lessons.md", "tabilet/docs/history/index.md", "Retired records are frozen")),
        ("template/tabilet/memory-bank/lessons.md", ("evidence", "Merge duplicates", "tabilet/docs/history/knowledge.md")),
        ("skills/memory-bank-init/references/write-contract.md", ("Milestone specification", "Status record", "all-retired", "explicit migration", "git rev-parse --verify HEAD")),
        ("template/tabilet/memory-bank/milestone.md", ("validate every envelope field", "git rev-parse --verify HEAD")),
        ("skills/memory-bank-reconcile/SKILL.md", ("all-retired", "does not retire milestones")),
        ("skills/memory-bank-archive/references/write-contract.md", ("tabilet/docs/history/knowledge.md", "never", "milestone/task records")),
        ("GOAL.md", ("history index", "cancelled or superseded outcome", "retirement procedure", "commit policy", "git rev-parse --verify HEAD", "before deleting active sources")),
        ("skills/memory-bank-next/SKILL.md", ("A later documentation row does not defer", "Updating only the status is insufficient")),
    ):
        text = " ".join((ROOT / relative).read_text().split())
        for token in tokens:
            if token not in text:
                problems.append(f"{relative}: missing history contract {token!r}")
    if (ROOT / "template/docs/history").exists():
        problems.append("template must not ship project-specific or empty history directories")
    return problems


@check("upgrade carries the canonical contract and preserves existing project state")
def upgrade_contract():
    bundle = SKILLS_DIR / "memory-bank-upgrade"
    target = bundle / "assets/template"
    canonical = ROOT / "template"
    expected = {p.relative_to(canonical): p.read_bytes() for p in canonical.rglob("*") if p.is_file()}
    actual = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    problems = []
    if actual != expected:
        problems.append("upgrade assets/template must be a complete byte-identical copy of template/")
    text = " ".join((bundle / "SKILL.md").read_text().split())
    for token in ("complete proposal before writing", "preserve unrelated content and local policies",
                  "Allocate no status ID", "Never reset an active review count", "all-retired",
                  "task tables, row notes, markers", "original bytes", "already compatible",
                  "Do not implement tasks, commit", "exact previously approved proposal",
                  "compatibility cannot be established", "stop the affected merge",
                  "requested-change procedure"):
        if token not in text:
            problems.append(f"upgrade is missing its preservation contract: {token}")
    if "memory-bank-upgrade" not in (ROOT / "AGENTS.md").read_text():
        problems.append("AGENTS.md must record the shared upgrade contract")
    return problems


@check("shared skills stop safely and keep one ledger execution owner")
def capability_contract():
    problems = []
    for path in [*SKILLS_DIR.glob("*/SKILL.md"), ROOT / "GOAL.md",
                 ROOT / "template/AGENTS.md", INIT_WRITE_CONTRACT]:
        text = " ".join(path.read_text().split())
        for token in ("verification commands, permissions, or user answers are unavailable",
                      "stop the affected workflow", "infer approval from silence or process exit",
                      "one execution owner", "do not replace milestone acceptance"):
            if token not in text:
                problems.append(f"{path.relative_to(ROOT)}: missing capability contract {token!r}")
    return problems



@check("propose shares focused references and preserves planning boundaries")
def propose_contract():
    problems = []
    for name, pairs in (
        ("discovery.md", ("init", "propose")),
        ("plan-update.md", ("propose", "reconcile")),
    ):
        paths = [SKILLS_DIR / f"memory-bank-{part}" / "references" / name for part in pairs]
        if not all(path.is_file() for path in paths):
            problems.append(f"missing bundle-local {name} in {pairs}")
        elif paths[0].read_bytes() != paths[1].read_bytes():
            problems.append(f"bundle-local {name} copies differ")
        for part in pairs:
            skill = SKILLS_DIR / f"memory-bank-{part}" / "SKILL.md"
            if skill.is_file() and f"references/{name}" not in skill.read_text():
                problems.append(f"{skill.relative_to(ROOT)} does not route to {name}")
    discovery = SKILLS_DIR / "memory-bank-init/references/discovery.md"
    if discovery.is_file():
        words = discovery.read_text()
        for token in ("in parallel", "❓ Q1", "➡️", "numbered frontier round"):
            if token not in words:
                problems.append(f"shared discovery reference lacks {token!r}")
    if not PROPOSE_SKILL.is_file():
        return problems + ["memory-bank-propose/SKILL.md is missing"]
    text = PROPOSE_SKILL.read_text()
    for token in ("<requested outcome or candidate direction>", "all-retired", "memory-bank-init",
                  "candidate", "duplicate", "pending", "complete approval request",
                  "Immediately before writing", "revised approval", "Do not commit",
                  "not been implemented", "references/discovery.md", "references/plan-update.md"):
        if token not in text:
            problems.append(f"memory-bank-propose: missing {token!r}")
    milestone = (ROOT / "template/tabilet/memory-bank/milestone.md").read_text()
    if "## Requested changes after initialization" not in milestone:
        problems.append("template milestone lacks requested-change procedure")
    if "memory-bank-propose" not in (ROOT / "AGENTS.md").read_text():
        problems.append("AGENTS.md lacks Propose boundary")
    return problems

@check("planning contracts load before proposals and optional goal help stays bundled")
def skill_resource_contract():
    problems = []
    for name, reference in (("archive", "write-contract.md"), ("init", "write-contract.md"),
                            ("propose", "plan-update.md"), ("reconcile", "write-contract.md")):
        bundle = SKILLS_DIR / f"memory-bank-{name}"
        skill = (bundle / "SKILL.md").read_text()
        proposal = skill.split("## Phase 2 - Propose", 1)[-1].split("## Phase 3 - Write", 1)[0]
        if f"references/{reference}" not in proposal:
            problems.append(f"{bundle.name}: proposal must load its planning contract")
        contract = " ".join((bundle / "references" / reference).read_text().split())
        if "Read this reference only after" in contract:
            problems.append(f"{bundle.name}: reference incorrectly gates inspection on approval")
        if "writes only after the user approves the complete proposal" not in contract:
            problems.append(f"{bundle.name}: contract must gate writes on proposal approval")
    goal = SKILLS_DIR / "memory-bank-goal"
    if "references/runtime-help.md" not in (goal / "SKILL.md").read_text():
        problems.append("goal launcher must route to its bundled optional runtime help")
    if not (goal / "references/runtime-help.md").is_file():
        problems.append("goal runtime help is missing from its standalone bundle")
    return problems


@check("DSH tests pin runtime components outside the portable payload")
def dsh_contract():
    import json

    problems = []
    directory = ROOT / "tests/dsh"
    manifest = json.loads((directory / "package.json").read_text())
    lock = json.loads((directory / "package-lock.json").read_text())
    if manifest.get("private") is not True:
        problems.append("DSH compatibility package must remain private")
    if manifest["dependencies"] != lock["packages"][""]["dependencies"]:
        problems.append("DSH manifest dependencies differ from lockfile")
    if manifest["scripts"] != {"test": "node --test compatibility.test.mjs"}:
        problems.append("DSH automatic test command must remain credential-free")
    for path, package in lock["packages"].items():
        name = path.rsplit("node_modules/", 1)[-1]
        if re.fullmatch(r"@deepseek-ai/dsh(?:-[a-z0-9-]+)?", name):
            if package["version"] != "0.1.5-rc.1" or manifest["overrides"].get(name) != "0.1.5-rc.1":
                problems.append(f"DSH component is not pinned to the tested version: {name}")
        if path and (not package.get("integrity") or not package.get("resolved", "").startswith("https://registry.npmjs.org/")):
            problems.append(f"DSH dependency lacks a registry integrity lock: {path}")
    for path in (ROOT / "template", ROOT / "skills", ROOT / "harness"):
        if list(path.rglob("node_modules")) or list(path.rglob("package-lock.json")):
            problems.append(f"Node compatibility dependencies leaked into payload: {path.name}")
    workflow = (ROOT / ".github/workflows/dsh.yml").read_text()
    for command in ("node-version: 24.14.1", "npm ci --prefix tests/dsh --ignore-scripts",
                    "npm test --prefix tests/dsh"):
        if command not in workflow:
            problems.append(f"DSH CI missing {command}")
    if "secrets." in workflow:
        problems.append("DSH compatibility CI must not receive paid-provider secrets")
    public = [ROOT / "README.md", ROOT / "docs/TUTORIAL.md", ROOT / "docs/USE_CASES.md",
              ROOT / "docs/EXECUTION.md", ROOT / "docs/MODEL_EVAL.md", *medium_articles()]
    for path in public:
        if "DSH.md" not in path.read_text():
            problems.append(f"{path.relative_to(ROOT)}: missing maintained DSH guide link")
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

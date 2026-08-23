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
SKILLS_DIR = ROOT / "skills"
ARCHIVE_SKILL = SKILLS_DIR / "memory-bank-archive" / "SKILL.md"
ARCHIVE_WRITE_CONTRACT = (
    SKILLS_DIR / "memory-bank-archive" / "references" / "write-contract.md"
)
INIT_SKILL = SKILLS_DIR / "memory-bank-init" / "SKILL.md"
INIT_WRITE_CONTRACT = SKILLS_DIR / "memory-bank-init" / "references" / "write-contract.md"
RECONCILE_SKILL = SKILLS_DIR / "memory-bank-reconcile" / "SKILL.md"
RECONCILE_WRITE_CONTRACT = (
    SKILLS_DIR / "memory-bank-reconcile" / "references" / "write-contract.md"
)
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
NON_ENGLISH_SUFFIXES = ("cn", "ja", "de", "fr", "es")

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


def medium_articles() -> list[pathlib.Path]:
    """Return every Medium article that is part of the public interface."""

    return sorted((ROOT / "docs").glob("medium*.md"))


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


def init_skill_text() -> str:
    """Return the init workflow and its progressively disclosed write rules."""

    return "\n".join(path.read_text() for path in (INIT_SKILL, INIT_WRITE_CONTRACT) if path.exists())


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
        ROOT / "template" / "GOAL.md",
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
    if "slash-goal" in goal:
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
        (ROOT / "template" / "memory-bank" / "milestone.md").read_text().split()
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
                f"template/memory-bank/milestone.md: missing review gate contract {token!r}"
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

    for token in ("another full milestone review", "stops after iteration 10"):
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
        (candidate for candidate in blocks if "AGENTS.md" in candidate and "memory-bank/product.md" in candidate),
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
        if f.startswith("memory-bank/status-"):
            if not any(x.startswith("memory-bank/status-") for x in listed):
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
        "memory-bank/suggested.txt",
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
        "memory-bank/suggested.txt",
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
        "memory-bank/suggested.txt",
        "STATUS_FILE_MAP",
        "DOWNSTREAM_IMPACTS",
        "Explicit `$ARGUMENTS` replace",
        "not a source of truth",
    ):
        if token not in goal:
            problems.append(f"memory-bank-goal/SKILL.md: missing {token}")

    if (ROOT / "template" / "memory-bank" / "suggested.txt").exists():
        problems.append(
            "template/memory-bank/suggested.txt must not ship; init or reconcile "
            "derives it from the approved project graph"
        )

    public = [ROOT / "README.md", ROOT / "docs" / "TUTORIAL.md", *medium_articles()]
    for path in public:
        if "memory-bank/suggested.txt" not in path.read_text():
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
    milestone = (ROOT / "template" / "memory-bank" / "milestone.md").read_text()
    agents = (ROOT / "AGENTS.md").read_text()
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
    ):
        if token not in skill:
            problems.append(f"memory-bank-init/SKILL.md: missing adaptive contract {token!r}")

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
        "Create `memory-bank/suggested.txt` only when",
        "Otherwise omit the launch reference",
        "sibling `GOAL.md`",
        "provider-specific plugin-root environment variables",
        "A trailing `?` is allowed only",
        "concrete project-state trigger",
        "discretionary",
        "Preserve every\n  verified `docs/archive-<LANE><NN>.md` byte-for-byte",
        "independent namespace",
    ):
        if token not in write_contract:
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
            problems.append(f"template/memory-bank/milestone.md: missing {token!r}")

    for token in (
        "approved compatible `GOAL.md`",
        "documented conditionally required active work",
        "adaptive topology gate",
        "must first use\n  `memory-bank-archive`",
    ):
        if token not in agents:
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
    architecture = (ROOT / "template" / "memory-bank" / "architecture.md").read_text()
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
        "docs/archive-<LANE><NN>.md",
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
                "Verified `docs/archive-<LANE><NN>.md` files are frozen",
                "independently from status lanes",
                "Keep verified archive files frozen",
            ),
        ),
        (
            architecture,
            "template/memory-bank/architecture.md",
            ("## Archive baselines", "No archive baseline is registered"),
        ),
    ):
        for token in tokens:
            if token not in text:
                problems.append(f"{label}: missing archive contract {token!r}")

    shipped_archives = list((ROOT / "template").rglob("archive-*.md"))
    if shipped_archives:
        shipped = ", ".join(str(path.relative_to(ROOT)) for path in shipped_archives)
        problems.append(f"template/ ships project-specific archive files: {shipped}")

    for path in (ROOT / "docs").glob("archive-*.md"):
        if not re.fullmatch(r"archive-[A-Z][0-9][0-9]\.md", path.name):
            problems.append(f"{path.relative_to(ROOT)}: invalid archive filename")

    for path in (ROOT / "GOAL.md", ROOT / "template" / "memory-bank" / "milestone.md"):
        if "archive-<LANE><NN>" in path.read_text():
            problems.append(f"{path.relative_to(ROOT)}: archive IDs entered execution protocol")
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
    milestone = (ROOT / "template" / "memory-bank" / "milestone.md").read_text()
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
        "rewrite only approved untouched pending rows",
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
            "template/memory-bank/milestone.md",
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

    if (ROOT / "template" / "memory-bank" / "reviews.md").exists():
        problems.append("template/ ships a persistent review ledger")
    for path in (ROOT / "template").rglob("review-*.md"):
        problems.append(f"{path.relative_to(ROOT)}: template ships a review artifact")
    return problems


@check("product.md owns the maintained domain model")
def domain_model_contract():
    product = (ROOT / "template" / "memory-bank" / "product.md").read_text()
    template_agents = (ROOT / "template" / "AGENTS.md").read_text()
    milestone = (ROOT / "template" / "memory-bank" / "milestone.md").read_text()
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
            problems.append(f"template/memory-bank/product.md: missing {token!r}")

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
            problems.append(f"template/memory-bank/milestone.md: missing {token!r}")
    if "`memory-bank/context.md`" not in agents:
        problems.append("AGENTS.md does not forbid a parallel memory-bank/context.md")
    if (ROOT / "template" / "memory-bank" / "context.md").exists():
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
@check("status parser matches the shipped template rows")
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
@check("repository documentation stays English-only")
def english_only_docs():
    problems = []
    suffixes = tuple(f"_{lang}.md" for lang in NON_ENGLISH_SUFFIXES)
    for path in sorted((ROOT / "docs").glob("*.md")):
        if path.name.endswith(suffixes):
            problems.append(f"{path.relative_to(ROOT)}: translated docs are not shipped")
    for path in sorted(ROOT.glob("README_*.md")):
        if path.name.endswith(suffixes):
            problems.append(f"{path.name}: README.md is English-only")
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
        + [ROOT / "docs" / "TUTORIAL.md", *medium_articles()]
        + sorted(SKILLS_DIR.glob("*/SKILL.md"))
    )

    plugin_tokens = (
        "/memory-bank:memory-bank-archive",
        "/memory-bank:memory-bank-init",
        "/memory-bank:memory-bank-reconcile",
        "/memory-bank:memory-bank-next",
        "/memory-bank:memory-bank-goal",
        "$memory-bank:memory-bank-archive",
        "$memory-bank:memory-bank-init",
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
        SKILLS_DIR / "memory-bank-goal" / "SKILL.md",
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
    result = (ROOT / "template" / "evolution" / "result-v1.md").read_text()
    for stale in ("**M1**", "**M2**"):
        if stale in result:
            problems.append(f"template/evolution/result-v1.md uses unpadded {stale}")

    status = (ROOT / "template" / "memory-bank" / "status-M01.md").read_text()
    if "multiple rows are inseparable" in status:
        problems.append("status-M01.md permits several rows in one commit")

    milestone = (ROOT / "template" / "memory-bank" / "milestone.md").read_text()
    if "Do not create an extra milestone commit" not in milestone:
        problems.append("milestone.md does not forbid empty review commits")
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

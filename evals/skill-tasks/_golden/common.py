"""Helpers for golden scripts: scripted edits that stand in for a model, used by tests only.

A golden `pass.py` is one compliant way to finish a task and must grade clean; each `fail-*.py` makes one
specific mistake and must fail the check the task's `golden` map names. They run with the project as the
working directory, so they validate fixtures and graders without a model call.
"""
import pathlib
import re

MEMORY = pathlib.Path("tabilet/memory-bank")


def read(path):
    return pathlib.Path(path).read_text(encoding="utf-8")


def write(path, text):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text(text, encoding="utf-8")


def edit(path, old, new, count=1):
    text = read(path)
    assert text.count(old) >= 1, f"{old!r} not found in {path}"
    write(path, text.replace(old, new, count))


def add_milestone(ident="M03", title="CSV export", rows=("Add export_csv(path)",), depends="M02",
                  impacts="none", write_set="src/tasklist.py", reads="none", parallel="no",
                  extra_scope=(), after="M02"):
    """A new pending status file, its index row, and its active specification (before Candidate Directions)."""
    body = "".join(f"| {row} | `[ ]` | |\n" for row in rows)
    write(MEMORY / f"status-{ident}.md",
          f"# Status {ident} - {title}\n\nMarkers: `[ ]` pending, `[+]` completed, `[~]` in progress, `[!]` blocked, "
          f"`[X]` cancelled,\n`[-]` closed historical.\n\n| Item | State | Notes |\n|---|---|---|\n{body}")
    milestone = MEMORY / "milestone.md"
    text = read(milestone)
    text = re.sub(rf"(^\| {after} \|[^\n]*\n)", rf"\1| {ident} | [status-{ident}.md](status-{ident}.md) | {title}. |\n",
                  text, count=1, flags=re.M)
    scope = "".join(f"- {item}\n" for item in (*rows, *extra_scope))
    spec = (f"## {ident} - {title}\n\n**Goal.** {title}.\n\n**Scope.**\n\n{scope}\n"
            f"**Acceptance.** `python3 -m unittest` passes.\n\n**Boundaries and parallel safety.**\n"
            f"- Depends on: {depends}\n- Downstream impacts: {impacts}\n- Write set: {write_set}\n"
            f"- Contracts read: {reads}\n- Parallel-safe: {parallel}\n\n")
    text = text.replace("## Candidate Directions", spec + "## Candidate Directions", 1)
    write(milestone, text)


# Archive and Upgrade helpers. TREE is the ref's checkout, so a setup or golden script reads that ref's files.
import shutil  # noqa: E402
import subprocess  # noqa: E402

TREE = pathlib.Path(__file__).resolve().parents[3]
REGISTRY_INTRO = ("Archive files are frozen repository snapshots. Current product and system truth\n"
                  "lives in this memory bank; use each archive only at its recorded baseline.\n")


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def head():
    return git("rev-parse", "HEAD")


def first_commit():
    return git("rev-list", "--max-parents=0", "HEAD")


def archive(ident, context, baseline, supersedes="none", storage="a JSON file `tasks.json`", correction=None, colon=False):
    """A verified context archive in the write contract's shape."""
    supersede = f"Supersedes: {supersedes}" if colon else f"**Supersedes.** {supersedes}"
    note = f"\n\n{correction}" if correction else ""
    write(f"tabilet/docs/archive-{ident}.md",
          f"# Archive {ident} - {context}\n\n**Context.** Task model and persistence for the tasklist tracker.\n\n"
          f"**Baseline.** {baseline}\n\n**Coverage.** verified\n\n{supersede}{note}\n\n"
          "## Scope And Responsibilities\n\nOwns the in-memory task list and its persistence. Sync and multi-user "
          "features are excluded.\n\n## Domain And Workflows\n\nA task has an integer id, a title and a done flag; "
          "ids follow insertion order.\n\n## System Shape\n\n`src/tasklist.py` holds the module-level `TASKS` list "
          "and the add, complete, listing, save and load functions.\n\n## Contracts And Dependencies\n\n"
          f"`save()` writes the whole list to {storage}; `load()` replaces the list from it. Standard library only.\n\n"
          "## Operations And Verification\n\n`python3 -m unittest` covers add and list and a save/load round trip.\n\n"
          "## Evidence\n\n| Claim | Repository Evidence |\n|---|---|\n"
          f"| Tasks persist in {storage} | `src/tasklist.py` |\n| The round trip is tested | `tests/test_tasklist.py` |\n\n"
          "## Observed Gaps\n\nNone observed.\n")


def registry(rows, link="../docs/archive-{ident}.md"):
    lines = "".join(f"| [{i}]({link.format(ident=i)}) | {c} | `{b}` | verified | {s} |\n" for i, c, b, s in rows)
    return ("## Archive baselines\n\n" + REGISTRY_INTRO + "\n| Archive Lane | Context |\n|---|---|\n| C | Task storage |\n\n"
            "| Archive | Context | Baseline | Coverage | Supersedes |\n|---|---|---|---|---|\n" + lines)


def register_archives(rows, link="../docs/archive-{ident}.md"):
    """Replace the template's Archive baselines section with a lane registry and archive index."""
    path = MEMORY / "architecture.md"
    text = re.sub(r"## Archive baselines\n.*?(?=\n## |\Z)", lambda _: registry(rows, link), read(path), count=1, flags=re.S)
    write(path, text)


def add_archive_row(ident, context, baseline, supersedes):
    """Add an archive index row after the last existing one (or the index header)."""
    path = MEMORY / "architecture.md"
    lines = read(path).splitlines()
    anchor = max((n for n, line in enumerate(lines) if line.startswith("| [") or line == "|---|---|---|---|---|"))
    lines.insert(anchor + 1, f"| [{ident}](../docs/archive-{ident}.md) | {context} | `{baseline}` | verified | {supersedes} |")
    write(path, "\n".join(lines) + "\n")


def journal(source, old, reason, replacement):
    """Append one superseded-knowledge entry to the knowledge journal."""
    path = pathlib.Path("tabilet/docs/history/knowledge.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = read(path) if path.is_file() else "# Knowledge history\n"
    write(path, text + f"\n## 2026-11-03 - {source}\n\n- Old wording: {old}\n- Reason: {reason}\n- Replacement: {replacement}\n")


def seed_archived_storage():
    """Setup: archive C01 of the JSON task storage at the first commit, with current summaries, then commit."""
    baseline = head()
    archive("C01", "Task storage", baseline)
    write(MEMORY / "architecture.md",
          "# Architecture\n\n## Layout\n\n| Path | Role |\n|---|---|\n"
          "| `src/tasklist.py` | Task model and JSON persistence. |\n| `tests/` | Unit tests run with `python3 -m unittest`. |\n"
          "| `tabilet/memory-bank/` | Project memory and milestone state. |\n\n## Data flow\n\n"
          "Callers add and complete tasks in the in-memory `TASKS` list; `save()` writes it to `tasks.json` and "
          "`load()` reads it back.\n\n## Public contracts\n\n"
          "- `add`, `complete`, `listing`, `save(path=\"tasks.json\")` and `load(path=\"tasks.json\")` in `src/tasklist.py`.\n"
          "- `tasks.json` holds a JSON array of `{\"id\", \"title\", \"done\"}` objects.\n\n"
          + registry([("C01", "Task storage", baseline, "none")]))
    write(MEMORY / "product.md",
          "# Product\n\n## What this is\n\n`tasklist` is a single-user command-line task tracker.\n\n## Domain model\n\n"
          "| Concept | Meaning | Relationships and invariants |\n|---|---|---|\n"
          "| Task | One item to do | Has an integer id, a title and a done flag; ids follow insertion order. |\n\n"
          "## Invariants\n\n- Saved tasks live in one `tasks.json` file.\n\n## Non-goals\n\n- Sync and multi-user use.\n")
    git("add", "-A")
    git("commit", "-qm", "Archive task storage as C01")

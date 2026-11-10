"""Helpers for golden scripts: scripted edits that stand in for a model, used by tests only.

A golden `pass.py` is one compliant way to finish a task and must grade clean; each `fail-*.py` makes one
specific mistake and must fail the check the task's `golden` map names. They run with the project as the
working directory, so they validate fixtures and graders without a model call.
"""
import os
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

TREE = pathlib.Path(os.environ["TABILET_EVAL_TREE"]).resolve()
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


FRIDAY = "- Never deploy on Fridays; the release manager signs off every deploy."
OLD_GOAL_POINTER = "Follow `tabilet/GOAL.md` for goal requests that span multiple status files.\n"
M01_SPEC = ("## M01 - Core commands\n\n**Goal.** Add and list tasks from the command line.\n\n**Scope.**\n\n"
            "- Add a task by title.\n- List all tasks.\n\n**Acceptance.** `python3 -m unittest` passes for add and list.\n\n"
            "**Boundaries and parallel safety.**\n- Depends on: none\n- Downstream impacts: none\n"
            "- Write set: src/tasklist.py, tests/\n- Contracts read: none\n- Parallel-safe: no\n\n")


def soft_sub(text, pattern, replacement, flags=re.S):
    """Like re.sub once, but leaves the text alone when a ref's template no longer has the pattern."""
    return re.sub(pattern, lambda _: replacement, text, count=1, flags=flags)


def recent_project(drop=()):
    """Setup: turn the copied template into the tasklist project on a recent release that lacks the rules named in
    `drop` ("requested-change", "goal-pointer", "test-policy"), then commit. Placeholders the project would have
    filled are filled; the rest of the ref's template stays, so the upgrade proposal is only the dropped rules."""
    agents = read("AGENTS.md").replace("[project-name]", "tasklist")
    agents = soft_sub(agents, r"- \[Owned responsibility 1\.\]\n.*?not here\.\n",
                      "- A single-user command-line task tracker and its JSON storage.\n\nOut of scope:\n\n"
                      "- Sync and multi-user features -> not planned.\n")
    agents = soft_sub(agents, r"\[build command\]\n\[test command\]\n\[lint command\]\n\[format command\]\n", "python3 -m unittest\n")
    agents = soft_sub(agents, r"- \[Hard rule 1\.\]\n- \[Hard rule 2\.\]\n- \[Hard rule 3\.\]\n",
                      FRIDAY + "\n- Keep the public function names in `src/tasklist.py` stable.\n")
    milestone = read(MEMORY / "milestone.md")
    milestone = milestone.replace("| M01 | [status-M01.md](status-M01.md) | [Milestone summary.] |",
                                  "| M01 | [status-M01.md](status-M01.md) | Core add and list commands. |")
    milestone = soft_sub(milestone, r"## M01 - \[Milestone name\]\n.*?(?=## Additional milestone examples)", M01_SPEC)
    if "requested-change" in drop:
        agents = soft_sub(agents, r"\nRequested features, candidate promotions.*?execution is a separate request\.\n", "")
        milestone = soft_sub(milestone, r"## Requested changes after initialization\n.*?(?=\n## )", "")
    if "goal-pointer" in drop:
        agents = soft_sub(agents, r"Goal requests that span multiple status files may use.*?stock protocol unchanged\.\n",
                          OLD_GOAL_POINTER)
    if "test-policy" in drop:
        pathlib.Path(MEMORY / "test-policy.md").unlink()
        agents = soft_sub(agents, r" and\n   \[tabilet/memory-bank/test-policy\.md\]\(tabilet/memory-bank/test-policy\.md\)", "")
        agents = soft_sub(agents, r"- Every test follows the test policy in.*?grants no authority\.\n", "")
        milestone = milestone.replace("[test policy](test-policy.md)", "test policy")
        tech = read(MEMORY / "tech-stack.md")
        write(MEMORY / "tech-stack.md", "\n".join(l for l in tech.splitlines() if "test-policy.md" not in l) + "\n")
    write("AGENTS.md", agents)
    write(MEMORY / "milestone.md", milestone)
    git("add", "-A")
    git("commit", "-qm", "Project on the previous release")


# Next helpers: a recent project with an explicit milestone ledger, and the edits an executor makes.
def status_file(ident, title, rows):
    """A status file with the ref's template preamble (which carries the commit-unit rule) and these rows."""
    text = (TREE / "template/tabilet/memory-bank/status-M01.md").read_text(encoding="utf-8")
    text = text.replace("# Status M01 - [Milestone name]", f"# Status {ident} - {title}", 1)
    text = text.replace("State of each M01 milestone item", f"State of each {ident} milestone item", 1)
    table = "| Item | State | Notes |\n|---|---|---|\n" + "".join(f"| {i} | `{m}` | {n} |\n" for i, m, n in rows)
    text = text[:text.index("| Item | State | Notes |")] + table
    write(MEMORY / f"status-{ident}.md", text)


def ledger(milestones):
    """Setup: a recent project whose active milestones, in priority order, are `milestones`: dicts with ident,
    title, goal, depends, write_set and rows [(item, marker, notes)]. Writes the index, specifications and status
    files, then commits."""
    recent_project()
    for path in MEMORY.glob("status-*.md"):
        path.unlink()
    index, specs = "", ""
    for m in milestones:
        status_file(m["ident"], m["title"], m["rows"])
        index += f"| {m['ident']} | [status-{m['ident']}.md](status-{m['ident']}.md) | {m['title']}. |\n"
        scope = "".join(f"- {item}\n" for item, _, _ in m["rows"])
        specs += (f"## {m['ident']} - {m['title']}\n\n**Goal.** {m['goal']}\n\n**Scope.**\n\n{scope}\n"
                  "**Acceptance.** `python3 -m unittest` passes, including a test for each scoped item.\n\n"
                  f"**Boundaries and parallel safety.**\n- Depends on: {m['depends']}\n- Downstream impacts: none\n"
                  f"- Write set: {m.get('write_set', 'src/tasklist.py, tests/')}\n- Contracts read: none\n- Parallel-safe: no\n\n")
    text = read(MEMORY / "milestone.md")
    text = text.replace("| M01 | [status-M01.md](status-M01.md) | Core add and list commands. |\n", index, 1)
    text = text.replace(M01_SPEC, specs, 1)
    write(MEMORY / "milestone.md", text)
    git("add", "-A")
    git("commit", "-qm", "Plan the active milestones")


def write_summaries():
    """Current architecture and product facts for the JSON storage, without an archive registry."""
    write(MEMORY / "architecture.md",
          "# Architecture\n\n## Layout\n\n| Path | Role |\n|---|---|\n"
          "| `src/tasklist.py` | Task model and JSON persistence. |\n| `tests/` | Unit tests run with `python3 -m unittest`. |\n"
          "| `tabilet/memory-bank/` | Project memory and milestone state. |\n\n## Data flow\n\n"
          "Callers add and complete tasks in the in-memory `TASKS` list; `save()` writes it to `tasks.json` and "
          "`load()` reads it back.\n\n## Public contracts\n\n"
          "- `add`, `complete`, `listing`, `save(path=\"tasks.json\")` and `load(path=\"tasks.json\")` in `src/tasklist.py`.\n"
          "- `tasks.json` holds a JSON array of `{\"id\", \"title\", \"done\"}` objects.\n\n"
          "## Archive baselines\n\nNo archive baseline is registered.\n")
    write(MEMORY / "product.md",
          "# Product\n\n## What this is\n\n`tasklist` is a single-user command-line task tracker.\n\n## Domain model\n\n"
          "| Concept | Meaning | Relationships and invariants |\n|---|---|---|\n"
          "| Task | One item to do | Has an integer id, a title and a done flag; ids follow insertion order. |\n\n"
          "## Invariants\n\n- Saved tasks live in one `tasks.json` file.\n\n## Non-goals\n\n- Sync and multi-user use.\n")


def set_row(ident, item, marker, notes=None):
    """Change one status row's marker (and optionally its notes) in place."""
    path = MEMORY / f"status-{ident}.md"
    lines = read(path).splitlines()
    for n, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0] == item:
            lines[n] = f"| {item} | `{marker}` | {cells[2] if notes is None and len(cells) > 2 else notes or ''} |"
            break
    else:
        raise AssertionError(f"row {item!r} not found in {path}")
    write(path, "\n".join(lines) + "\n")


def add_code(text):
    write("src/tasklist.py", read("src/tasklist.py").rstrip("\n") + "\n\n\n" + text.strip("\n") + "\n")


def commit(message):
    git("add", "-A")
    git("commit", "-qm", message)

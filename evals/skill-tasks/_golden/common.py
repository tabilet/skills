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

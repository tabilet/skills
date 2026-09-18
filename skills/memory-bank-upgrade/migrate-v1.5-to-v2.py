#!/usr/bin/env python3
"""Explicit, resumable v1.5.0 project layout migration (standard library only)."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


OLD_ROOTS = ("GOAL.md", "memory-bank", "evolution", "docs/history")
ARCHIVE = re.compile(r"archive-[A-Z](?:0[1-9]|[1-9][0-9])\.md$")
STATUS = re.compile(r"status-[A-Z](?:0[1-9]|[1-9][0-9])\.md$")
MAINTAINED = {
    "AGENTS.md", "memory-bank/product.md", "memory-bank/architecture.md",
    "memory-bank/tech-stack.md", "memory-bank/lessons.md",
    "memory-bank/milestone.md", "memory-bank/suggested.txt",
}
REPLACEMENTS = (
    ("memory-bank/", "tabilet/memory-bank/"),
    ("evolution/", "tabilet/evolution/"),
    ("docs/history/", "tabilet/docs/history/"),
    ("docs/archive-", "tabilet/docs/archive-"),
)
ROOT_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_./-])(?:\./)?(memory-bank/|evolution/|docs/history/|docs/archive-)"
)
GOAL_REFERENCE = re.compile(r"(?<![A-Za-z0-9_./-])(?:\./)?GOAL\.md\b")


def stop(message):
    raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(project, *args):
    proc = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True)
    if proc.returncode:
        stop(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def require_git(project, clean):
    if Path(git(project, "rev-parse", "--show-toplevel")).resolve() != project:
        stop("PROJECT must be the Git worktree root")
    head = git(project, "rev-parse", "--verify", "HEAD")
    if clean and git(project, "status", "--porcelain", "--untracked-files=all"):
        stop("Git worktree must be clean, including untracked files")
    return head


def journal_path(project):
    key = digest(str(project).encode())[:20]
    return Path(tempfile.gettempdir()) / f"tabilet-v1.5-to-v2-{key}.json"


def check_regular(path):
    if path.is_symlink():
        stop(f"symlink is not supported: {path}")
    if not path.is_file():
        stop(f"expected regular file: {path}")


def tree_files(project, relative):
    root = project / relative
    if root.is_symlink():
        stop(f"symlink is not supported: {root}")
    if not root.exists():
        return []
    if not root.is_dir():
        stop(f"expected directory: {root}")
    result = []
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            if (Path(current) / name).is_symlink():
                stop(f"symlink is not supported: {Path(current) / name}")
        for name in files:
            path = Path(current) / name
            check_regular(path)
            result.append(path.relative_to(project).as_posix())
    return sorted(result)


def source_files(project):
    paths = []
    if (project / "GOAL.md").exists() or (project / "GOAL.md").is_symlink():
        check_regular(project / "GOAL.md")
        paths.append("GOAL.md")
    paths.extend(tree_files(project, "memory-bank"))
    paths.extend(tree_files(project, "evolution"))
    paths.extend(tree_files(project, "docs/history"))
    docs = project / "docs"
    if docs.is_symlink():
        stop(f"symlink is not supported: {docs}")
    if docs.is_dir():
        for path in docs.iterdir():
            if ARCHIVE.fullmatch(path.name):
                check_regular(path)
                paths.append(path.relative_to(project).as_posix())
    return sorted(paths)


def old_layout_exists(project):
    if any((project / name).exists() or (project / name).is_symlink() for name in OLD_ROOTS):
        return True
    docs = project / "docs"
    return docs.is_dir() and any(ARCHIVE.fullmatch(p.name) for p in docs.iterdir())


def v2_layout_exists(project):
    root = project / "tabilet"
    return root.exists() or root.is_symlink()


def recognizable_layout(project, prefix=""):
    base = project / prefix
    bank = base / "memory-bank"
    milestone = bank / "milestone.md"
    statuses = bank.is_dir() and any(STATUS.fullmatch(path.name) for path in bank.iterdir())
    history = (base / "docs/history/index.md").is_file()
    if milestone.is_file():
        return statuses or history
    docs = base / "docs"
    archives = docs.is_dir() and any(ARCHIVE.fullmatch(path.name) for path in docs.iterdir())
    return (not milestone.exists() and not statuses and not history and archives
            and (bank / "product.md").is_file() and (bank / "architecture.md").is_file())


def validate_v2_layout(project):
    if old_layout_exists(project):
        stop("mixed v1.5/v2 layout; repair manually before migration")
    if (project / "tabilet").is_symlink():
        stop("symlink is not supported: tabilet")
    if not (project / "tabilet").is_dir():
        stop("expected directory: tabilet")
    if not (project / "AGENTS.md").is_file() or (project / "AGENTS.md").is_symlink():
        stop("regular root AGENTS.md is required")
    files = tree_files(project, "tabilet")
    if any(name.endswith(".tabilet-migrating") for name in files) or not recognizable_layout(project, "tabilet"):
        stop("unexplained partial v2 layout; repair manually before migration")


def rewrite(data):
    text = data.decode("utf-8")
    # Paths beginning ../ still resolve after both files move under tabilet/.
    # A nested path such as other/memory-bank/ belongs to that other directory.
    text = ROOT_REFERENCE.sub(lambda match: "tabilet/" + match.group(1), text)
    text = GOAL_REFERENCE.sub("tabilet/GOAL.md", text)
    return text.encode("utf-8")


def plan(project, head):
    if not (project / "AGENTS.md").is_file() or (project / "AGENTS.md").is_symlink():
        stop("regular root AGENTS.md is required")
    if v2_layout_exists(project):
        validate_v2_layout(project)
        return None
    if not old_layout_exists(project):
        stop("no v1.5.0 project-owned files found")
    sources = source_files(project)
    if not sources or not recognizable_layout(project):
        stop("v1.5.0 initialized memory bank or archive preflight is missing")
    ops = []
    for src in sources:
        data = (project / src).read_bytes()
        dst = f"tabilet/{src}"
        if (project / dst).exists() or (project / dst).is_symlink():
            stop(f"destination collision: {dst}")
        new = rewrite(data) if src in MAINTAINED else data
        ops.append({"src": src, "dst": dst, "before": digest(data), "after": digest(new),
                    "content": base64.b64encode(new).decode("ascii") if new != data else None})
    data = (project / "AGENTS.md").read_bytes()
    new = rewrite(data)
    if new != data:
        ops.append({"src": "AGENTS.md", "dst": "AGENTS.md", "before": digest(data),
                    "after": digest(new), "content": base64.b64encode(new).decode("ascii")})
    return {"format": 1, "project": str(project), "head": head, "ops": ops}


def save_journal(path, manifest):
    raw = json.dumps(manifest, sort_keys=True).encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def validate_resume(project, manifest, head):
    if manifest.get("format") != 1 or manifest.get("project") != str(project) or manifest.get("head") != head:
        stop("migration journal does not match this project and Git HEAD")
    ops = manifest.get("ops")
    if not isinstance(ops, list) or not ops:
        stop("invalid migration journal")
    for op in ops:
        if not isinstance(op, dict) or not all(k in op for k in ("src", "dst", "before", "after", "content")):
            stop("invalid migration journal operation")
        if op["src"] != "AGENTS.md" and op["dst"] != f"tabilet/{op['src']}":
            stop("invalid migration journal destination")
        if op["src"] == "AGENTS.md" and op["dst"] != "AGENTS.md":
            stop("invalid migration journal destination")
        if op["src"] != "AGENTS.md" and not (
            op["src"] == "GOAL.md" or
            op["src"].startswith(("memory-bank/", "evolution/", "docs/history/")) or
            (op["src"].startswith("docs/") and ARCHIVE.fullmatch(Path(op["src"]).name))
        ):
            stop("invalid migration journal source")
        if ".." in Path(op["src"]).parts or Path(op["src"]).is_absolute():
            stop("invalid migration journal path")
        if op["content"] is not None and digest(base64.b64decode(op["content"], validate=True)) != op["after"]:
            stop("invalid migration journal content")
    expected_old = {op["src"] for op in ops if op["src"] != "AGENTS.md"}
    expected_new = {op["dst"] for op in ops if op["src"] != "AGENTS.md"}
    actual_old = set(source_files(project))
    actual_new = set(tree_files(project, "tabilet"))
    pending_temp = set()
    for op in ops:
        temp = project / (op["dst"] + ".tabilet-migrating")
        if temp.exists() or temp.is_symlink():
            check_regular(temp)
            if digest(temp.read_bytes()) != op["after"]:
                stop(f"journal temporary output is invalid: {temp}")
            pending_temp.add(temp.relative_to(project).as_posix())
    actual_new -= pending_temp
    if actual_old - expected_old or actual_new - expected_new:
        stop("unexplained files in partial layout; repair manually")
    for op in ops:
        src, dst = project / op["src"], project / op["dst"]
        if src == dst:
            if not src.is_file() or src.is_symlink() or digest(src.read_bytes()) not in (op["before"], op["after"]):
                stop(f"journal validation failed: {op['src']}")
        elif src.exists() == dst.exists():
            stop(f"journal validation failed: {op['src']} and {op['dst']}")
        else:
            present = src if src.exists() else dst
            check_regular(present)
            allowed = (op["before"],) if present == src else (op["before"], op["after"])
            if digest(present.read_bytes()) not in allowed:
                stop(f"journal validation failed: {present}")
    for name in pending_temp:
        temporary = project / name
        temporary.replace(project / name.removesuffix(".tabilet-migrating"))


def apply(project, manifest):
    fail_after = int(os.environ.get("TABILET_MIGRATION_FAIL_AFTER", "0"))
    for index, op in enumerate(manifest["ops"], 1):
        src, dst = project / op["src"], project / op["dst"]
        if src != dst and src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
        if op["content"] and digest(dst.read_bytes()) == op["before"]:
            data = base64.b64decode(op["content"], validate=True)
            if digest(data) != op["after"]:
                stop("invalid migration journal content")
            temporary = dst.with_name(dst.name + ".tabilet-migrating")
            if temporary.exists():
                stop(f"unexpected temporary file: {temporary}")
            temporary.write_bytes(data)
            temporary.replace(dst)
        if digest(dst.read_bytes()) != op["after"]:
            stop(f"migration output changed: {dst}")
        if fail_after and index == fail_after:
            stop("injected interruption after a completed file operation")
    for name in ("memory-bank", "evolution", "docs/history"):
        root = project / name
        if root.exists():
            for directory, _, _ in os.walk(root, topdown=False):
                Path(directory).rmdir()
    stale = []
    for path in project.rglob("*.md"):
        relative = path.relative_to(project)
        if path.name == "AGENTS.md" or ".git" in relative.parts or path.is_symlink():
            continue
        if relative.parts[0] == "tabilet" and not (
            relative.as_posix() == "tabilet/GOAL.md" or
            relative.as_posix().startswith("tabilet/evolution/") or
            (relative.as_posix().startswith("tabilet/memory-bank/") and
             re.fullmatch(r"status-[A-Z][0-9]{2}\.md", path.name))
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        if any(old in text for old, _ in REPLACEMENTS) or "Using GOAL.md" in text:
            stale.append(relative.as_posix())
    return stale


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", metavar="PROJECT", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="migrate a clean committed project")
    mode.add_argument("--resume", action="store_true", help="resume a validated interrupted migration")
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        stop("PROJECT is not a directory")
    path = journal_path(project)
    if not args.resume and not path.exists() and not old_layout_exists(project) and v2_layout_exists(project):
        require_git(project, clean=False)
        validate_v2_layout(project)
        print("Already using the v2 layout; no changes.")
        return
    head = require_git(project, clean=not args.resume and not path.exists())
    if args.resume:
        if not path.is_file() or path.is_symlink():
            stop("no migration journal; cannot resume")
        manifest = json.loads(path.read_text())
        validate_resume(project, manifest, head)
    elif path.exists():
        stop(f"interrupted migration found; run --resume (journal: {path})")
    else:
        manifest = plan(project, head)
        if manifest is None:
            print("Already using the v2 layout; no changes.")
            return
        print(f"{len(manifest['ops'])} file operations from committed HEAD {head}")
        for op in manifest["ops"]:
            print(f"  {op['src']} -> {op['dst']}" if op["src"] != op["dst"] else f"  rewrite {op['src']}")
        if not args.apply:
            print("Preview only. Run --apply to migrate; the diff remains uncommitted.")
            return
        save_journal(path, manifest)
    stale = apply(project, manifest)
    path.unlink()
    print("Migration complete. Review and commit the project diff when ready.")
    if stale:
        print("Review stale references in other project documents:")
        for name in stale:
            print(f"  {name}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Migration stopped: {exc}", file=sys.stderr)
        sys.exit(2)

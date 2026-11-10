#!/usr/bin/env python3
"""Run frozen-base checks against an isolated candidate; invoke from a trusted checkout."""
from __future__ import annotations
import argparse
import contextlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import frontmatter

TRUSTED_ROOT = Path(__file__).resolve().parents[1]
# Local editor, agent, dependency and generated artifacts are never copied into the gate.
RUNTIME_DIRS = {".git", ".idea", ".claude", ".pytest_cache", "__pycache__", ".cache", ".venv", "node_modules", "site", "test-results", "playwright-report"}
LOCAL_FILES = {"medium-legacy.md"}


@contextlib.contextmanager
def safe_git_environment():
    # Git inspection must not execute configuration supplied by the candidate.
    previous = dict(os.environ)
    try:
        for key in list(os.environ):
            if key in ("GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_EXTERNAL_DIFF") or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
                del os.environ[key]
        settings = (("core.fsmonitor", "false"), ("core.hooksPath", "/dev/null"))
        os.environ["GIT_CONFIG_COUNT"] = str(len(settings))
        for index, (key, value) in enumerate(settings):
            os.environ[f"GIT_CONFIG_KEY_{index}"] = key
            os.environ[f"GIT_CONFIG_VALUE_{index}"] = value
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous)


def run(base, candidate, full=True, *, trusted_root=None):
    candidate = Path(candidate).resolve()
    trusted_root = Path(trusted_root or TRUSTED_ROOT).resolve()
    try:
        with safe_git_environment(), tempfile.TemporaryDirectory(prefix="tabilet-trusted-gate-") as directory:
            # Resolve branches and remote refs exclusively in the invoking trusted checkout.
            sha = subprocess.run(["git", "rev-parse", "--verify", base + "^{commit}"], cwd=trusted_root,
                                 check=True, capture_output=True, text=True).stdout.strip()
            root = Path(directory) / "base"
            subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(trusted_root), str(root)],
                           check=True, capture_output=True)
            subprocess.run(["git", "checkout", "--quiet", "--detach", sha], cwd=root, check=True, capture_output=True)
            # Structural policy belongs to this trusted tooling, including when base predates it.
            spec = importlib.util.spec_from_file_location("trusted_checks", TRUSTED_ROOT / "check.py")
            checks = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(checks)
            known = set(subprocess.run(["git", "ls-tree", "-r", "--name-only", sha], cwd=root,
                                      check=True, capture_output=True, text=True).stdout.splitlines())
            problems, changes = [], {}
            for relative in sorted(known):
                source, original = candidate / relative, root / relative
                if any((candidate / Path(*Path(relative).parts[:i])).is_symlink()
                       for i in range(1, len(Path(relative).parts) + 1)):
                    problems.append(f"{relative}: candidate symlinks are not editable text")
                    continue
                if not source.is_file():
                    problems.append(f"{relative}: optimizer cannot delete tracked files")
                    continue
                if bool(source.stat().st_mode & 0o111) != bool(original.stat().st_mode & 0o111):
                    problems.append(f"{relative}: optimizer cannot change executable modes")
                captured = source.read_bytes()
                if captured == original.read_bytes():
                    continue
                changes[relative] = captured
                if any(checks.optimizer_pattern_matches(pattern, relative) for pattern in checks.OPTIMIZER_FROZEN):
                    problems.append(f"{relative}: frozen surface; an optimizer may not change it")
                elif any(checks.optimizer_pattern_matches(pattern, relative) for pattern in checks.OPTIMIZER_DESCRIPTION_ONLY):
                    before, after = original.read_text(), captured.decode("utf-8")
                    frontmatter.description(after)
                    if checks.without_description(before) != checks.without_description(after):
                        problems.append(f"{relative}: only the frontmatter description may change")
                elif not any(checks.optimizer_pattern_matches(pattern, relative) for pattern in checks.OPTIMIZER_EDITABLE):
                    problems.append(f"{relative}: not on the optimizer's editable surface")
            # No Git command runs in candidate: its config, filters and info/attributes are inert.
            for parent, directories, files in os.walk(candidate):
                directories[:] = [d for d in directories if d not in RUNTIME_DIRS]
                for name in files:
                    relative = (Path(parent) / name).relative_to(candidate).as_posix()
                    if relative not in known and relative != ".git" and relative not in LOCAL_FILES:
                        problems.append(f"{relative}: new files are outside the optimizer surface")
            if problems:
                print("\n".join(problems), file=sys.stderr)
                return 1
            for relative, captured in changes.items():
                (root / relative).write_bytes(captured)
            if not full:
                return 0
            return subprocess.run([sys.executable, "-B", str(root / "check.py"), "--no-cache"], cwd=root).returncode
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"trusted gate: {type(exc).__name__}: cannot validate base or candidate", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True, type=Path)
    args = parser.parse_args()
    return run(args.base, args.candidate)


if __name__ == "__main__":
    raise SystemExit(main())

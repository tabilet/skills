"""Credential-free project layout migration acceptance tests."""

from pathlib import Path
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills/memory-bank-upgrade/migrate-v1.5-to-v2.py"
RUNNER = ROOT / "harness/tackle-memory-bank-api-loop"


def call(*args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)


def commit(repo):
    call("git", "init", "-q", str(repo))
    call("git", "add", "-A", cwd=repo)
    result = call("git", "-c", "user.name=Test", "-c", "user.email=test@example.test",
                  "commit", "-qm", "baseline", cwd=repo)
    assert result.returncode == 0, result.stderr


def fixture(repo, *, goal=True, retired=False, archive=False, customized=False):
    repo.mkdir()
    (repo / "AGENTS.md").write_text(
        "# Local rules\n\nRead [milestones](memory-bank/milestone.md). "
        "Local policy: keep custom approval.\n"
    )
    bank = repo / "memory-bank"
    bank.mkdir()
    (bank / "product.md").write_text("Current product.\n")
    (bank / "architecture.md").write_text("See docs/archive-A01.md.\n" if archive else "Current architecture.\n")
    (bank / "milestone.md").write_text(
        "# Milestones\n\n[History](../docs/history/index.md)\n"
        if retired else "# Milestones\n\n## M01 - Delivery\n\n[status](status-M01.md)\n"
    )
    if retired:
        history = repo / "docs/history"
        history.mkdir(parents=True)
        (history / "index.md").write_text("# History\n\n| M01 | completed | 2026-09-12 | [record](status-M01.md) | Done |\n")
        (history / "status-M01.md").write_text("**Source status.** memory-bank/status-M01.md\nFrozen.\n")
        (history / "knowledge.md").write_text("Prior lesson.\n")
    else:
        (bank / "status-M01.md").write_text("| Task | State | Notes |\n|---|---|---|\n| Build | `[~]` | Keep this note and counter 2/10. |\n")
    if goal:
        (repo / "GOAL.md").write_text("Using GOAL.md, execute this loop.\n")
        (bank / "suggested.txt").write_text("Using GOAL.md, execute this loop.\nSTATUS_ORDER: M01\n")
    if archive:
        docs = repo / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "archive-A01.md").write_text("Frozen archive. verified.\n")
    evo = repo / "evolution"
    evo.mkdir()
    (evo / "prompt-v1.md").write_text("Frozen direction.\n")
    if customized:
        (repo / "README.md").write_text("Manual link: memory-bank/milestone.md\n")
        (bank / "lessons.md").write_text("Local policy: keep custom approval.\n")
    commit(repo)


class MigrationTests(unittest.TestCase):
    def migrate(self, repo, *flags, env=None):
        return call(sys.executable, str(CLI), str(repo), *flags, env=env)

    def test_ordinary_preview_apply_and_repeat_preserve_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "project"
            fixture(repo, customized=True, archive=True)
            protected = {p.relative_to(repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [repo / "memory-bank/status-M01.md", repo / "docs/archive-A01.md",
                                   repo / "evolution/prompt-v1.md"]}
            self.assertEqual(self.migrate(repo).returncode, 0)
            self.assertFalse((repo / "tabilet").exists())
            result = self.migrate(repo, "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            for old, sha in protected.items():
                self.assertEqual(hashlib.sha256((repo / "tabilet" / old).read_bytes()).hexdigest(), sha)
            self.assertIn("tabilet/memory-bank/milestone.md", (repo / "AGENTS.md").read_text())
            self.assertIn("Local policy: keep custom approval.", (repo / "AGENTS.md").read_text())
            self.assertIn("tabilet/GOAL.md", (repo / "tabilet/memory-bank/suggested.txt").read_text())
            self.assertIn("README.md", result.stdout)
            self.assertEqual(self.migrate(repo).returncode, 0)
            self.assertIn("no changes", self.migrate(repo).stdout)
            self.assertTrue(call("git", "status", "--porcelain", cwd=repo).stdout)

    def test_all_retired_optional_goal_and_archive_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            retired = Path(tmp) / "retired"
            fixture(retired, goal=False, retired=True)
            frozen = (retired / "docs/history/status-M01.md").read_bytes()
            self.assertEqual(self.migrate(retired, "--apply").returncode, 0)
            self.assertEqual((retired / "tabilet/docs/history/status-M01.md").read_bytes(), frozen)
            self.assertIn("../docs/history/index.md", (retired / "tabilet/memory-bank/milestone.md").read_text())
            archive = Path(tmp) / "archive"
            fixture(archive, goal=False, archive=True)
            (archive / "memory-bank/milestone.md").unlink()
            (archive / "memory-bank/status-M01.md").unlink()
            call("git", "add", "-A", cwd=archive)
            call("git", "-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-qm", "archive only", cwd=archive)
            self.assertEqual(self.migrate(archive, "--apply").returncode, 0)
            self.assertTrue((archive / "tabilet/docs/archive-A01.md").is_file())

    def test_reject_dirty_collision_mixed_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "project"
            fixture(repo)
            (repo / "new.txt").write_text("dirty")
            self.assertNotEqual(self.migrate(repo, "--apply").returncode, 0)
            (repo / "new.txt").unlink()
            (repo / "tabilet").mkdir()
            self.assertIn("mixed", self.migrate(repo, "--apply").stderr)
            (repo / "tabilet").rmdir()
            (repo / "memory-bank/link.md").symlink_to("status-M01.md")
            call("git", "add", "-A", cwd=repo)
            call("git", "-c", "user.name=Test", "-c", "user.email=test@example.test",
                 "commit", "-qm", "add link", cwd=repo)
            self.assertIn("symlink", self.migrate(repo, "--apply").stderr)
            (repo / "memory-bank/link.md").unlink()
            (repo / "tabilet").mkdir()
            (repo / "tabilet/GOAL.md").write_text("collision")
            self.assertNotEqual(self.migrate(repo, "--apply").returncode, 0)

    def test_interrupted_run_resumes_only_validated_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "project"
            fixture(repo)
            env = dict(os.environ, TABILET_MIGRATION_FAIL_AFTER="2")
            self.assertIn("injected interruption", self.migrate(repo, "--apply", env=env).stderr)
            self.assertIn("--resume", self.migrate(repo).stderr)
            self.assertEqual(self.migrate(repo, "--resume").returncode, 0)
            self.assertTrue((repo / "tabilet/memory-bank/status-M01.md").exists())

    def test_runner_rejects_legacy_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "project"
            fixture(repo)
            env = dict(os.environ, LLM_MODEL="dummy", LLM_API_BASE="http://127.0.0.1:1/v1",
                       LLM_API_KEY="dummy", ALLOW_UNSANDBOXED_SHELL="1")
            proc = call(sys.executable, str(RUNNER), str(repo), env=env)
            self.assertEqual(proc.returncode, 11)
            self.assertIn("migrate-v1.5-to-v2.py", proc.stderr)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def load_module(name: str, path: pathlib.Path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


core = load_module("planning_test_runner", ROOT / "harness/tackle-memory-bank-api-loop")
planning = load_module("planning_test_module", ROOT / "harness/tabilet_planning.py")
installer = load_module("planning_test_installer", ROOT / "harness/tabilet_install.py")
controller = load_module("planning_test_controller", ROOT / "harness/tabilet_controller.py")


def git(*args: str, cwd: pathlib.Path):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)


class FakeCore:
    UnsafeGitConfiguration = core.UnsafeGitConfiguration
    ProjectLockUnavailable = core.ProjectLockUnavailable

    def __init__(self, replies=()):
        self.replies = list(replies)
        self.calls = 0
        self.messages = []

    def call_llm(self, *args):
        self.calls += 1
        self.messages.append(args[4])
        return {"content": json.dumps(self.replies.pop(0))}

    @staticmethod
    def extract_json(text):
        return json.loads(text)

    @staticmethod
    def bounded_output(stdout, stderr, limit):
        if len(stdout) + len(stderr) <= limit:
            return stdout, stderr, False
        return stdout[:limit], "", True

    def git_local(self, *args, **kwargs):
        return core.git_local(*args, **kwargs)

    @staticmethod
    def project_lock(project):
        return contextlib.nullcontext()

    @staticmethod
    def fail(message, code):
        raise SystemExit(code)


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self.body = body
        self.status = status
        self.headers = SimpleNamespace(
            get_content_charset=lambda: "utf-8",
            get_content_type=lambda: "text/plain",
        )

    def read(self, amount=-1):
        return self.body if amount < 0 else self.body[:amount]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.source = self.root / "source-skills"
        shutil.copytree(ROOT / "skills", self.source)
        self.installed = self.root / "installed"
        installer.install_skill_bundles(self.source, self.installed)
        self.project = self.root / "project"
        self.project.mkdir()
        self.outputs = []

    def tools(self, input_fn=lambda _prompt: "", project=None):
        return planning.ReadOnlyPlanningTools(
            FakeCore(), project or self.project, self.installed,
            input_fn=input_fn, output_fn=self.outputs.append,
        )

    @staticmethod
    def args(max_turns=4):
        return SimpleNamespace(
            max_turns=max_turns, max_history_chars=150_000, provider="test",
            api_base="", api_key="", model="fake", temperature=0,
            max_tokens=1000, api_timeout=2, max_retries=0,
        )

    def test_installed_hash_manifest_works_after_source_checkout_is_removed(self):
        shutil.rmtree(self.source)
        self.assertEqual(self.installed.resolve(), planning.verify_skill_bundles(self.installed))
        _root, contract = planning.load_skill_contract("init", self.installed)
        self.assertIn("memory-bank-init", contract)

    def test_installer_rejects_bundle_without_skill_entrypoint(self):
        bundle = self.source / "memory-bank-init"
        entrypoint = bundle / "SKILL.md"
        saved = entrypoint.read_bytes()
        entrypoint.unlink()
        try:
            with self.assertRaises(installer.InstallError):
                installer.install_skill_bundles(self.source, self.root / "invalid-install")
        finally:
            entrypoint.write_bytes(saved)

    def test_modified_missing_extra_and_symlink_bundle_content_is_rejected(self):
        target = self.installed / "memory-bank-init/SKILL.md"
        original = target.read_bytes()
        target.write_bytes(original + b"tampered")
        with self.assertRaises(planning.BundleIntegrityError):
            planning.verify_skill_bundles(self.installed)
        target.write_bytes(original)
        target.unlink()
        with self.assertRaises(planning.BundleIntegrityError):
            planning.verify_skill_bundles(self.installed)
        target.write_bytes(original)
        extra = self.installed / "memory-bank-init/extra.txt"
        extra.write_text("unexpected")
        with self.assertRaises(planning.BundleIntegrityError):
            planning.verify_skill_bundles(self.installed)
        extra.unlink()
        (self.installed / "memory-bank-init/linked.txt").symlink_to("SKILL.md")
        with self.assertRaises(planning.BundleIntegrityError):
            planning.verify_skill_bundles(self.installed)

    def test_extra_bundle_root_entry_is_rejected(self):
        (self.installed / "unexpected.txt").write_text("extra")
        with self.assertRaises(planning.BundleIntegrityError):
            planning.verify_skill_bundles(self.installed)

    def test_contained_reads_listing_search_and_proposal_do_not_write_project(self):
        (self.project / "notes.md").write_text("first\nneedle value\nlast\n", encoding="utf-8")
        before = {p.relative_to(self.project).as_posix(): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        tools = self.tools()
        self.assertEqual("needle value", tools.read("notes.md", 2, 2)["text"])
        self.assertEqual("notes.md", tools.list_directory(".")["entries"][0]["name"])
        self.assertEqual(1, len(tools.search(".", "needle")["results"]))
        result, terminal = tools.dispatch({"tool": "propose", "proposal": {"title": "draft"}})
        after = {p.relative_to(self.project).as_posix(): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        self.assertTrue(terminal)
        self.assertEqual("proposal", result["status"])
        self.assertEqual(before, after)

    def test_traversal_symlink_git_metadata_and_large_read_are_rejected(self):
        outside = self.root / "outside.txt"
        outside.write_text("secret")
        (self.project / "link.txt").symlink_to(outside)
        (self.project / "large.txt").write_text("x" * (planning.MAX_READ_BYTES + 1))
        tools = self.tools()
        for name in ("../outside.txt", "/etc/passwd", "C:/secret", ".git/config", "link.txt"):
            with self.subTest(path=name), self.assertRaises(planning.PlanningError):
                tools.read(name)
        with self.assertRaises(planning.PlanningError):
            tools.read("large.txt")
        with self.assertRaises(planning.PlanningError):
            tools.list_directory("link.txt")

    def test_search_regex_is_bounded_and_invalid_tools_have_no_side_effects(self):
        tools = self.tools()
        for pattern in ("(a+)+$", "a{1,100}", r"(a)\1"):
            with self.subTest(pattern=pattern), self.assertRaises(planning.PlanningError):
                tools.search(".", pattern, regex=True)
        error, terminal = tools.dispatch({"tool": "run_shell", "cmd": "touch marker"})
        self.assertFalse(terminal)
        self.assertFalse(error["ok"])
        error, terminal = tools.dispatch({"tool": "stop", "reason": [], "message": "bad"})
        self.assertFalse(terminal)
        self.assertFalse(error["ok"])
        self.assertFalse((self.project / "marker").exists())

    def test_skill_references_are_available_only_through_installed_namespace(self):
        tools = self.tools()
        listing = tools.list_directory("skill://memory-bank-init")
        self.assertIn("SKILL.md", [item["name"] for item in listing["entries"]])
        self.assertIn("memory-bank-init", tools.read("skill://memory-bank-init/SKILL.md")["text"])
        with self.assertRaises(planning.PlanningError):
            tools.read("skill://memory-bank-init/../../outside")

    def test_git_log_and_show_use_hardened_bounded_output(self):
        git("init", "-q", cwd=self.project)
        (self.project / "tracked.txt").write_text("safe\n")
        git("-c", "user.name=Test", "-c", "user.email=test@example.test", "add", "-A", cwd=self.project)
        committed = git(
            "-c", "user.name=Test", "-c", "user.email=test@example.test",
            "commit", "-qm", "x" * 12000, cwd=self.project,
        )
        self.assertEqual(0, committed.returncode, committed.stderr)
        git("config", "--local", "diff.external", "/not/a/real/diff", cwd=self.project)
        git("config", "--local", "log.showSignature", "true", cwd=self.project)
        tools = self.tools()
        log = tools.git_log()
        self.assertLess(len(log["log"]), 1000)
        self.assertIn("x" * 100, log["log"])
        head = git("rev-parse", "HEAD", cwd=self.project).stdout.strip()
        shown = tools.git_show(head)
        self.assertIn("tracked.txt", shown["show"])
        self.assertLess(len(shown["show"]), planning.MAX_GIT_OUTPUT)
        self.assertNotIn("x" * 1000, shown["show"])

    def test_ask_forwards_multiple_answers_without_normalization(self):
        answers = iter(["  preserve edges  ", "second\tanswer"])
        tools = self.tools(input_fn=lambda _prompt: next(answers))
        result = tools.ask([
            {"id": "scope", "title": "What scope?", "options": ["small", "large"]},
            {"id": "deadline", "title": "When?"},
        ])
        self.assertEqual("  preserve edges  ", result["answers"][0]["answer"])
        self.assertEqual("second\tanswer", result["answers"][1]["answer"])
        self.assertTrue(self.outputs)

    def test_fake_provider_runs_interview_then_returns_proposal(self):
        fake = FakeCore([
            {"tool": "ask", "questions": [{"id": "q", "title": "What is needed?"}]},
            {"tool": "propose", "proposal": {"title": "A plan"}},
        ])
        result = controller.run_planning_session(
            fake, self.args(), self.project, "init", "initialize project",
            self.installed, input_fn=lambda _prompt: "  keep this exact  ", output_fn=self.outputs.append,
        )
        self.assertEqual(2, fake.calls)
        self.assertEqual("proposal", result["status"])
        self.assertTrue(any("  keep this exact  " in msg["content"] for msg in fake.messages[-1]))

    def test_legacy_and_mixed_layout_stops_before_provider(self):
        (self.project / "GOAL.md").write_text("v1.5")
        fake = FakeCore([])
        result = planning.run_planning_session(
            fake, self.args(), self.project, "init", "request", self.installed,
        )
        self.assertEqual("legacy_or_mixed_layout", result["reason"])
        self.assertEqual(0, fake.calls)

    def test_invalid_operation_state_stops_before_provider(self):
        fake = FakeCore([])
        self.assertEqual("missing_initialized_state", planning.run_planning_session(
            fake, self.args(), self.project, "propose", "request", self.installed,
        )["reason"])
        (self.project / "tabilet/memory-bank").mkdir(parents=True)
        (self.project / "tabilet/memory-bank/milestone.md").write_text("active")
        (self.project / "tabilet/memory-bank/status-M01.md").write_text("active")
        self.assertEqual("already_initialized", planning.run_planning_session(
            fake, self.args(), self.project, "init", "request", self.installed,
        )["reason"])
        self.assertEqual(0, fake.calls)

    def test_bundle_integrity_failure_stops_before_provider(self):
        (self.installed / "memory-bank-init/SKILL.md").write_text("tampered")
        fake = FakeCore([])
        with self.assertRaises(planning.BundleIntegrityError):
            planning.run_planning_session(fake, self.args(), self.project, "init", "request", self.installed)
        self.assertEqual(0, fake.calls)

    def test_controller_maps_bundle_integrity_failure_to_exit_17(self):
        (self.installed / "memory-bank-init/SKILL.md").write_text("tampered")
        fake = FakeCore([])
        with self.assertRaises(SystemExit) as stopped:
            controller.run_planning_session(
                fake, self.args(), self.project, "init", "request", self.installed,
                output_fn=self.outputs.append,
            )
        self.assertEqual(17, stopped.exception.code)
        self.assertEqual(0, fake.calls)

    def test_lock_collision_stops_before_provider(self):
        class CollisionCore(FakeCore):
            @staticmethod
            def project_lock(_project):
                raise core.ProjectLockUnavailable("held")

        fake = CollisionCore([])
        with self.assertRaises(SystemExit) as stopped:
            controller.run_planning_session(fake, self.args(), self.project, "init", "request", self.installed)
        self.assertEqual(19, stopped.exception.code)
        self.assertEqual(0, fake.calls)

    def test_archive_gate_is_terminal_without_proposal_or_write(self):
        fake = FakeCore([{
            "tool": "stop", "reason": "archive_required",
            "message": "Observed several stable contexts that need archive preflight.",
        }])
        result = planning.run_planning_session(fake, self.args(), self.project, "init", "request", self.installed)
        self.assertEqual("archive_required", result["reason"])
        self.assertEqual(1, fake.calls)
        self.assertEqual([], list(self.project.iterdir()))

    def test_fetch_review_requires_exact_url_confirmation(self):
        url = "https://reviews.example.test/item"
        refused = self.tools(input_fn=lambda _prompt: "yes")
        with mock.patch.object(planning.urllib.request, "build_opener") as builder:
            self.assertFalse(refused.fetch_review(url)["fetched"])
            builder.assert_not_called()

        approved = self.tools(input_fn=lambda _prompt: f"yes {url}")
        opener = mock.MagicMock()
        opener.open.return_value = FakeResponse(b"review text")
        with mock.patch.object(planning.urllib.request, "build_opener", return_value=opener):
            result = approved.fetch_review(url)
        self.assertTrue(result["fetched"])
        self.assertEqual("review text", result["review"])
        opener.open.assert_called_once()

    def test_fetch_rejects_bad_urls_redirects_and_oversized_response(self):
        tools = self.tools(input_fn=lambda _prompt: "")
        with mock.patch.object(planning.urllib.request, "build_opener") as builder:
            for url in (
                "http://example.test", "https://user@example.test", "https://example.test:99999",
                "https://example.test/a b",
            ):
                with self.subTest(url=url), self.assertRaises(planning.PlanningError):
                    tools.fetch_review(url)
            builder.assert_not_called()

        url = "https://reviews.example.test/redirect"
        redirect = self.tools(input_fn=lambda _prompt: f"yes {url}")
        opener = mock.MagicMock()
        opener.open.side_effect = planning.urllib.error.HTTPError(url, 302, "redirect", {}, None)
        with mock.patch.object(planning.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(planning.PlanningError, "redirected"):
                redirect.fetch_review(url)
        opener.open.assert_called_once()

        oversized = self.tools(input_fn=lambda _prompt: f"yes {url}")
        opener = mock.MagicMock()
        opener.open.return_value = FakeResponse(b"x" * (planning.MAX_REVIEW_BYTES + 1))
        with mock.patch.object(planning.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(planning.PlanningError, "exceeds"):
                oversized.fetch_review(url)

    def test_prompt_keeps_skill_contract_planning_only_and_closure_boundary(self):
        contract = "canonical init skill planning instructions"
        prompt = planning.planning_system_prompt("init", contract)
        flat = " ".join(prompt.split())
        self.assertIn(contract, prompt)
        self.assertIn("There is no shell", flat)
        self.assertIn("omit its write phase", flat)
        self.assertIn("Direct-skill handoff language does not authorize", flat)
        self.assertIn("API 6 owns", flat)
        self.assertIn("separate exact-URL confirmation", flat)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import contextlib
import hashlib
import io
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "tests"))
import test_harness
import tabilet_controller as controller
import tabilet_cli
import tabilet_proposal as proposal_api


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


installer = load_module("cli_test_installer", ROOT / "harness/tabilet_install.py")


core = controller.load_runner_core()
IMAGE_ID = "sha256:" + "a" * 64


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)


def make_proposal(project, *, title="Delivery plan", external_actions=None):
    content = "approved planning note\n"
    blob = subprocess.run(
        ["git", "hash-object", "--stdin"], cwd=project, input=content,
        text=True, capture_output=True, check=True,
    ).stdout.strip()
    patch = (
        "diff --git a/approved-plan.md b/approved-plan.md\n"
        "new file mode 100644\n"
        f"index 0000000..{blob[:7]}\n"
        "--- /dev/null\n+++ b/approved-plan.md\n@@ -0,0 +1 @@\n"
        "+approved planning note\n"
    )
    return {
        "title": title,
        "delivery_boundary": "Complete one small local feature and verify milestone closure.",
        "horizon": [{
            "id": "M01", "title": "Delivery", "dependencies": [],
            "acceptance": "The feature file exists and the task row is complete.",
            "closure_paths": ["tabilet/memory-bank/milestone.md", "tabilet/memory-bank/status-M01.md"],
            "manual_evidence": [], "retirement_adopted": False,
            "tasks": [{
                "id": "T01", "owner": "agent", "description": "Create the approved feature.",
                "acceptance": "The feature file exists.", "verification": ["true"],
                "approved_paths": ["feature.py", "tabilet/memory-bank/status-M01.md"],
            }],
        }],
        "candidate_directions": [],
        "file_actions": [{"path": "approved-plan.md", "action": "create"}],
        "diff": patch, "image_id": IMAGE_ID,
        "limits": dict(proposal_api.DEFAULT_LIMITS), "planned_commits": 2,
        "external_actions": list(external_actions or []),
    }


def answer(value):
    return {"content": json.dumps(value), "usage": {}}


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


class FakeExecutor:
    image = IMAGE_ID

    def __init__(self):
        self.commands = []

    def __call__(self, repo, command, timeout, max_output, allow_dangerous, env=None):
        self.commands.append(command)
        if command == "complete-task":
            (repo / "feature.py").write_text("feature = True\n", encoding="utf-8")
            status = repo / "tabilet/memory-bank/status-M01.md"
            text = status.read_text(encoding="utf-8").replace("`[~]`", "`[+]`", 1)
            status.write_text(text, encoding="utf-8")
        return {"exit_code": 0, "stdout": "verified\n", "stderr": "", "truncated": False}


def runner_args():
    return SimpleNamespace(
        provider="openai", api_base="http://127.0.0.1:9/v1", api_key="test-key",
        model="fake-model", temperature=None, max_tokens=1000, api_timeout=5,
        max_retries=0, max_turns=40, max_history_chars=200000,
        tool_timeout=300, max_tool_output=24000, allow_dangerous=False,
        tool_env=[], audit_db=None, audit_capture="metadata",
    )


class TabiletChatEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        test_harness.make_repo(self.project)
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(
            "# Status\n\n| ID | State | Notes |\n|---|---|---|\n"
            "| T01 | `[ ]` | Create one feature. |\n", encoding="utf-8",
        )
        git("add", "-A", cwd=self.project)
        git("-c", "user.name=CLI test", "-c", "user.email=cli@example.test",
            "commit", "-qm", "prepare CLI fixture", cwd=self.project)
        self.store = proposal_api.ReceiptStore(self.root / "state" / "tabilet" / "receipts")
        self.bundle_root = installer.install_skill_bundles(ROOT / "skills", self.root / "bundles")
        self.executor = FakeExecutor()

    def test_reject_revises_without_writes_then_confirm_completes_locally(self):
        initial_tree = tree_digest(self.project)
        plan1 = make_proposal(self.project, title="First plan", external_actions=["publish release"])
        plan2 = make_proposal(self.project, title="Revised plan", external_actions=["publish release"])
        phase_replies = [
            {"tool": "run_shell", "cmd": "complete-task", "why": "implement selected row"},
            {"final": "The feature is ready.", "external_actions": []},
            {"final": "Review found no release blocking findings.", "verified": True,
             "evidence": ["Reviewed the full milestone."], "findings": [], "external_actions": []},
            {"final": "Acceptance criteria pass.", "verified": True,
             "evidence": ["Feature exists and its test passes."], "findings": [], "external_actions": []},
            {"final": "Current facts are consolidated.", "verified": True,
             "evidence": ["No maintained facts required an update."], "findings": [], "external_actions": []},
            {"final": "Downstream references are consistent.", "verified": True,
             "evidence": ["No downstream milestone depends on this row."], "findings": [], "external_actions": []},
        ]
        calls = []
        queue = [answer({"tool": "propose", "proposal": plan1}),
                 answer({"tool": "propose", "proposal": plan2})]
        queue.extend(answer(reply) for reply in phase_replies)

        def fake_provider(*args, **kwargs):
            calls.append(args[4])
            if not queue:
                self.fail("fake provider conversation unexpectedly exhausted")
            return queue.pop(0)

        choices = iter(["reject", "Use the shorter plan title.", "confirm"])
        displayed = []

        def input_fn(prompt):
            self.assertEqual(initial_tree, tree_digest(self.project), "approval interaction wrote before confirm")
            return next(choices)

        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")}):
            with mock.patch.object(core, "call_llm", side_effect=fake_provider), \
                    mock.patch.object(controller, "prepare_docker_executor", return_value=self.executor):
                result = controller.chat_session(
                    core, runner_args(), self.project, "propose", "Create the small feature.",
                    "python:local", receipt_store=self.store, skill_bundle_root=self.bundle_root,
                    input_fn=input_fn,
                    output_fn=displayed.append,
                )

        self.assertEqual("completed", result["state"])
        self.assertTrue((self.project / "approved-plan.md").is_file())
        self.assertEqual("feature = True\n", (self.project / "feature.py").read_text(encoding="utf-8"))
        self.assertIn("`[+]`", (self.project / "tabilet/memory-bank/status-M01.md").read_text(encoding="utf-8"))
        self.assertEqual(["complete-task", "true", "true"], self.executor.commands)
        self.assertEqual(2, len(result["commit_ids"]))  # planning and selected task; closure made no changes
        self.assertEqual(["publish release"], result["external_actions"])
        self.assertEqual([], queue)
        self.assertEqual(8, len(calls))
        proposal_display = "\n".join(displayed)
        for limit in ("100", "40", "15", "7200", "8192", "512", "300"):
            self.assertIn(limit, proposal_display)
        self.assertTrue(any("First plan" in text for text in displayed))
        self.assertTrue(any("Revised plan" in text for text in displayed))
        self.assertEqual("completed", self.store.load(pathlib.Path(self.store.directory) / f"{result['receipt_id']}.json")["state"])

    def test_nonproposal_planning_stop_does_not_create_a_receipt(self):
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")}):
            with mock.patch.object(core, "call_llm", return_value=answer({
                "tool": "stop", "reason": "archive_required", "message": "Run archive preflight first."
            })), mock.patch.object(controller, "prepare_docker_executor", return_value=self.executor):
                result = controller.chat_session(
                    core, runner_args(), self.project, "propose", "Expand the product.",
                    "python:local", receipt_store=self.store, skill_bundle_root=self.bundle_root,
                    input_fn=lambda _prompt: "",
                    output_fn=lambda _text: None,
                )
        self.assertEqual("stopped", result["status"])
        self.assertFalse(pathlib.Path(self.store.directory).exists())

    def test_public_status_command_reports_without_project_writes_or_credentials(self):
        before = tree_digest(self.project)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = tabilet_cli.main(["status", str(self.project)])
        self.assertEqual(0, result)
        self.assertIn('"id": "M01"', output.getvalue())
        self.assertEqual(before, tree_digest(self.project))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import uuid
import unittest
from types import SimpleNamespace
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "harness"))
import test_harness as harness_tests


def load_module(name: str, path: pathlib.Path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


core = harness_tests.harness
horizon = load_module("horizon_selection_module", ROOT / "harness/tabilet_horizon.py")
proposal_api = load_module("horizon_proposal_module", ROOT / "harness/tabilet_proposal.py")
controller = harness_tests.controller


class HorizonSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = pathlib.Path(self.temp.name) / "project"
        self.project.mkdir()
        harness_tests.make_repo(self.project)
        self.set_project([("M01", [("T01", "`[ ]`", "Ready.")])])

    def set_project(self, milestones):
        sections = ["# Milestones\n"]
        for identity, _ in milestones:
            sections += [f"\n## {identity} - Delivery\n", "\n**Acceptance.** The outcome works.\n"]
        (self.project / "tabilet/memory-bank/milestone.md").write_text("".join(sections), encoding="utf-8")
        for identity, rows in milestones:
            lines = ["# Status\n\n| ID | State | Notes |\n|---|---|---|\n"]
            lines.extend(f"| {task} | {state} | {notes} |\n" for task, state, notes in rows)
            (self.project / f"tabilet/memory-bank/status-{identity}.md").write_text("".join(lines), encoding="utf-8")

    def receipt(self, ids=("M01",), tasks=None):
        tasks = tasks or {"M01": ["T01"]}
        horizon_rows = []
        for identity in ids:
            horizon_rows.append({
                "id": identity,
                "title": f"Milestone {identity}",
                "acceptance": f"Milestone {identity} works.",
                "dependencies": [],
                "closure_paths": [
                    "tabilet/memory-bank/milestone.md",
                    f"tabilet/memory-bank/status-{identity}.md",
                ],
                "manual_evidence": [],
                "tasks": [{
                    "id": task_id,
                    "owner": "agent",
                    "description": f"Complete {task_id}.",
                    "acceptance": "It works.",
                    "verification": ["true"],
                    "approved_paths": [f"tabilet/memory-bank/status-{identity}.md", "src/feature.py"],
                } for task_id in tasks[identity]],
            })
        return {
            "state": "running",
            "horizon_ids": list(ids),
            "approved_horizon": horizon_rows,
            "closure": {"milestones": {}},
        }

    def test_selects_first_ready_row_in_live_table_order(self):
        self.set_project([("M01", [("T01", "`[ ]`", "Ready."), ("T02", "`[ ]`", "Ready too.")])])
        selected = horizon.select_next_row(core, self.project, self.receipt(tasks={"M01": ["T01", "T02"]}))
        self.assertEqual("row", selected["status"])
        self.assertEqual("T01", selected["row"]["task_id"])
        self.assertEqual(["true"], selected["task"]["verification"])

    def test_resumes_the_sole_in_scope_in_progress_row(self):
        self.set_project([("M01", [("T01", "`[ ]`", "Earlier pending."), ("T02", "`[~]`", "Resume this.")])])
        receipt = self.receipt(tasks={"M01": ["T01", "T02"]})
        receipt["usage"] = {"rows_started_ids": ["M01/T02"]}
        selected = horizon.select_next_row(core, self.project, receipt)
        self.assertTrue(selected["resumed"])
        self.assertEqual("T02", selected["row"]["task_id"])

    def test_in_scope_in_progress_row_without_receipt_provenance_needs_review(self):
        self.set_project([("M01", [("T01", "`[~]`", "Unproven in-progress row.")])])
        with self.assertRaisesRegex(horizon.HorizonError, "no receipt provenance"):
            horizon.select_next_row(core, self.project, self.receipt())

    def test_out_of_horizon_in_progress_stops_selection(self):
        self.set_project([("M01", [("T01", "`[ ]`", "Ready.")]), ("M02", [("T02", "`[~]`", "Outside.")])])
        with self.assertRaisesRegex(horizon.HorizonError, "outside the approved horizon"):
            horizon.select_next_row(core, self.project, self.receipt())

    def test_unresolved_live_task_dependency_stops_before_provider_dispatch(self):
        self.set_project([("M01", [("T01", "`[ ]`", "Depends on: T99")])])
        with self.assertRaisesRegex(horizon.HorizonError, "unresolved task dependency"):
            horizon.select_next_row(core, self.project, self.receipt())

    def test_blocked_horizon_row_stops_selection(self):
        self.set_project([("M01", [("T01", "`[!]`", "Blocked on a decision.")])])
        with self.assertRaisesRegex(horizon.HorizonError, "contains a blocked row"):
            horizon.select_next_row(core, self.project, self.receipt())

    def test_historical_successor_outside_scope_stops_selection(self):
        self.set_project([
            ("M01", [("T01", "`[-]`", "Consumed attempt; accepted successor M02/T02.")]),
            ("M02", [("T02", "`[ ]`", "Successor.")]),
        ])
        with self.assertRaisesRegex(horizon.HorizonError, "outside the approved horizon"):
            horizon.select_next_row(core, self.project, self.receipt())

    def test_historical_successor_inside_milestone_but_outside_task_scope_stops(self):
        self.set_project([(
            "M01", [
                ("T01", "`[-]`", "Consumed attempt; accepted successor T02."),
                ("T02", "`[+]`", "Already complete."),
            ],
        )])
        with self.assertRaisesRegex(horizon.HorizonError, "outside approved task scope"):
            horizon.select_next_row(core, self.project, self.receipt())

    def test_live_milestone_dependency_outside_scope_stops_selection(self):
        self.set_project([
            ("M01", [("T01", "`[ ]`", "Ready.")]),
            ("M02", [("T02", "`[ ]`", "Prerequisite.")]),
        ])
        milestone = self.project / "tabilet/memory-bank/milestone.md"
        milestone.write_text(
            milestone.read_text(encoding="utf-8").replace(
                "## M01 - Delivery\n", "## M01 - Delivery\n\n**Dependencies.** M02\n",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(horizon.HorizonError, "is not a completed milestone inside"):
            horizon.select_next_row(core, self.project, self.receipt())

    def test_rechecks_live_task_dependencies_and_selects_the_prerequisite(self):
        self.set_project([(
            "M01",
            [("T02", "`[ ]`", "Depends on: T01"), ("T01", "`[ ]`", "Prerequisite.")],
        )])
        selected = horizon.select_next_row(
            core, self.project, self.receipt(tasks={"M01": ["T01", "T02"]}),
        )
        self.assertEqual("T01", selected["row"]["task_id"])

    def test_completed_rows_require_closure_instead_of_reporting_horizon_done(self):
        self.set_project([("M01", [("T01", "`[+]`", "Done.")])])
        selected = horizon.select_next_row(core, self.project, self.receipt())
        self.assertEqual("closure", selected["status"])
        self.assertEqual("M01", selected["milestone"]["id"])

    def test_malformed_closure_checkpoint_stops_instead_of_spinning(self):
        receipt = self.receipt()
        receipt["closure"]["milestones"]["M01"] = {
            "closure_state": "pending", "phase": "unknown",
        }
        with self.assertRaisesRegex(horizon.HorizonError, "invalid phase or state"):
            horizon.select_next_row(core, self.project, receipt)

    def test_closure_cannot_add_pending_rows_outside_the_fixed_task_scope(self):
        before = core.row_snapshot(self.project)
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(
            status.read_text(encoding="utf-8") + "| T02 | `[ ]` | New work. |\n",
            encoding="utf-8",
        )
        after = core.row_snapshot(self.project)
        problems = horizon._closure_integrity_problems(before, after)
        self.assertTrue(any("unapproved task row" in problem for problem in problems), problems)


class HorizonRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        harness_tests.make_repo(self.project)
        (self.project / "tabilet/memory-bank/milestone.md").write_text(
            "# Milestones\n\n## M01 - Delivery\n\n**Acceptance.** Feature works.\n",
            encoding="utf-8",
        )
        (self.project / "tabilet/memory-bank/status-M01.md").write_text(
            "# Status\n\n| ID | State | Notes |\n|---|---|---|\n"
            "| T01 | `[ ]` | Implement feature. |\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "config", "user.name", "Horizon Test"], cwd=self.project, check=True)
        subprocess.run(["git", "config", "user.email", "horizon@example.test"], cwd=self.project, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "planning baseline"], cwd=self.project, check=True)
        self.head = core.git_head(self.project)
        self.receipt_dir = self.root / "private" / "tabilet" / "receipts"
        self.store = proposal_api.ReceiptStore(self.receipt_dir)
        self.receipt = self.make_receipt()
        self.receipt_path = self.store.create(self.project, self.receipt)

    def make_receipt(self, *, manual_evidence=None, limits=None):
        return {
            "schema": "tabilet.api.receipt/v1",
            "receipt_id": str(uuid.uuid4()),
            "project_path": str(self.project.resolve()),
            "proposal_sha256": "a" * 64,
            "branch": core.git_branch(self.project),
            "planning_commit": self.head,
            "state": "running",
            "approved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "horizon_ids": ["M01"],
            "approved_horizon": [{
                "id": "M01", "title": "M01 Delivery", "acceptance": "Feature works.",
                "dependencies": [], "retirement_adopted": False,
                "closure_paths": [
                    "tabilet/memory-bank/milestone.md",
                    "tabilet/memory-bank/status-M01.md",
                ],
                "manual_evidence": manual_evidence or [],
                "tasks": [{
                    "id": "T01", "owner": "agent", "description": "Implement feature.",
                    "acceptance": "Feature works.", "verification": ["true"],
                    "approved_paths": ["src/feature.py", "tabilet/memory-bank/status-M01.md"],
                }],
            }],
            "external_actions": [], "image_id": "sha256:" + "a" * 64,
            "limits": {**proposal_api.DEFAULT_LIMITS, **(limits or {})},
            "usage": {
                "rows_started": 0, "rows_started_ids": [],
                "provider_attempts_reserved": 0, "commits_reserved": 1,
                "commits_recorded": 1, "turns_by_row": {},
            },
            "commit_ids": [self.head], "active_operation": None,
            "closure": {"milestones": {}}, "verification_evidence": [],
            "mutation_scope": "local_only", "pause_reason": None,
        }

    def args(self):
        return SimpleNamespace(
            provider="openai", api_base="https://invalid.test", api_key="test", model="test",
            temperature=None, max_tokens=1000, api_timeout=1, max_retries=2,
            max_turns=40, max_history_chars=100000, tool_timeout=5,
            max_tool_output=1000, allow_dangerous=False, tool_env=[],
        )

    def provider_for(self, replies):
        pending = iter(replies)
        calls = {"attempts": 0}

        def call(*_args, before_attempt=None, **_kwargs):
            if before_attempt is not None:
                before_attempt()
            calls["attempts"] += 1
            return {"content": json.dumps(next(pending)), "usage": {}}

        return call, calls

    def executor(self, *, fail_check=False):
        def execute(repo, command, *_args):
            if command == "finish-row":
                status = repo / "tabilet/memory-bank/status-M01.md"
                status.write_text(status.read_text().replace("`[~]`", "`[+]`"), encoding="utf-8")
                source = repo / "src/feature.py"
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("feature = True\n", encoding="utf-8")
                return {"exit_code": 0, "stdout": "finished", "stderr": ""}
            if command.startswith("fix-"):
                milestone = repo / "tabilet/memory-bank/milestone.md"
                milestone.write_text(
                    milestone.read_text(encoding="utf-8") + f"\n<!-- {command} -->\n",
                    encoding="utf-8",
                )
                return {"exit_code": 0, "stdout": "fixed", "stderr": ""}
            if command == "symlink-row":
                status = repo / "tabilet/memory-bank/status-M01.md"
                status.write_text(status.read_text().replace("`[~]`", "`[+]`"), encoding="utf-8")
                source = repo / "src/feature.py"
                source.parent.mkdir(parents=True, exist_ok=True)
                source.symlink_to(self.root / "outside.txt")
                return {"exit_code": 0, "stdout": "created symlink", "stderr": ""}
            if command == "external-commit":
                status = repo / "tabilet/memory-bank/status-M01.md"
                status.write_text(status.read_text().replace("`[~]`", "`[+]`"), encoding="utf-8")
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-qm", "concurrent host commit"], cwd=repo, check=True)
                return {"exit_code": 0, "stdout": "concurrent commit", "stderr": ""}
            if command == "retire":
                status_path = repo / "tabilet/memory-bank/status-M01.md"
                status_text = status_path.read_text(encoding="utf-8")
                milestone_path = repo / "tabilet/memory-bank/milestone.md"
                milestone_text = milestone_path.read_text(encoding="utf-8")
                specification = next(
                    line for line in [milestone_text[milestone_text.index("## M01 - Delivery"):]]
                    if line.startswith("## M01 - Delivery")
                )
                history = repo / "tabilet/docs/history"
                history.mkdir(parents=True, exist_ok=True)
                record = (
                    "# Retired milestone M01 - Delivery\n\n"
                    "**Milestone.** M01\n"
                    "**Outcome.** completed\n"
                    "**Retired.** 2026-09-25\n"
                    "**Source status.** tabilet/memory-bank/status-M01.md\n"
                    "**Source specification.** tabilet/memory-bank/milestone.md#m01-delivery\n"
                    f"**Evidence.** {core.git_head(repo)}\n"
                    "**Worktree.** includes uncommitted changes\n"
                    "**Review.** passed\n"
                    "**Review iterations.** 1\n"
                    "**Verification.** Required task check `true` passed.\n"
                    "**Consolidated into.** no current-truth change\n\n"
                    "## Milestone specification\n\n`````markdown\n"
                    f"{specification}`````\n\n"
                    "## Status record\n\n`````markdown\n"
                    f"{status_text}`````\n"
                )
                (history / "status-M01.md").write_text(record, encoding="utf-8")
                (history / "index.md").write_text(
                    "# History\n\n"
                    "| Milestone | Outcome | Retired | Record | Summary |\n"
                    "|---|---|---|---|---|\n"
                    "| M01 | completed | 2026-09-25 | [M01](status-M01.md) | Delivery complete |\n",
                    encoding="utf-8",
                )
                milestone_path.write_text(
                    "# Milestones\n\n[History](../docs/history/index.md)\n",
                    encoding="utf-8",
                )
                status_path.unlink()
                return {"exit_code": 0, "stdout": "retired", "stderr": ""}
            if command == "true":
                return {"exit_code": 1 if fail_check else 0, "stdout": "check output", "stderr": ""}
            return {"exit_code": 0, "stdout": "", "stderr": ""}
        return execute

    @staticmethod
    def closure_reply(phase):
        return {
            "final": f"{phase} verified", "verified": True,
            "evidence": [f"Observed {phase} evidence."], "findings": [],
            "external_actions": [],
        }

    def run_horizon(self, replies, executor=None, *, manual_evidence=None, via_adapter=False):
        fake_call, counts = self.provider_for(replies)
        with mock.patch.object(core, "call_llm", side_effect=fake_call):
            if via_adapter:
                with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")}):
                    with mock.patch.object(controller, "prepare_docker_executor", return_value=executor or self.executor()):
                        result = controller.execute_horizon(
                            core, self.args(), self.project, self.receipt_path,
                            receipt_store=self.store, manual_evidence=manual_evidence,
                            output_fn=lambda _text: None,
                        )
            else:
                result = horizon.run_horizon(
                    core, self.args(), self.project, self.receipt_path,
                    receipt_store=self.store, executor=executor or self.executor(),
                    manual_evidence=manual_evidence, output_fn=lambda _text: None,
                    controller_module=controller,
                )
        return result, counts

    def test_task_and_clean_no_change_closure_complete_automatically(self):
        replies = [
            {"tool": "run_shell", "cmd": "finish-row", "why": "finish selected task"},
            {"final": "task finished", "external_actions": []},
            self.closure_reply("review"), self.closure_reply("acceptance"),
            self.closure_reply("consolidation"), self.closure_reply("downstream"),
        ]
        result, counts = self.run_horizon(replies, via_adapter=True)
        self.assertEqual("completed", result["state"])
        self.assertEqual("verified", result["closure"]["milestones"]["M01"]["closure_state"])
        self.assertEqual(2, len(result["commit_ids"]))  # planning + one task; closure made no changes
        self.assertEqual(1, result["usage"]["rows_started"])
        self.assertEqual(6, result["usage"]["provider_attempts_reserved"])
        self.assertEqual(6, counts["attempts"])
        self.assertTrue(result["verification_evidence"][0]["exit_code"] == 0)

    def test_adopted_retirement_preserves_sources_after_verified_closure(self):
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(status.read_text(encoding="utf-8").replace("`[ ]`", "`[+]`"), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "complete milestone"], cwd=self.project, check=True)
        receipt = self.store.load(self.receipt_path)
        receipt["commit_ids"].append(core.git_head(self.project))
        receipt["usage"]["commits_reserved"] += 1
        receipt["usage"]["commits_recorded"] += 1
        receipt["approved_horizon"][0]["retirement_adopted"] = True
        receipt["approved_horizon"][0]["closure_paths"].extend([
            "tabilet/docs/history/index.md", "tabilet/docs/history/status-M01.md",
        ])
        self.store.update_atomic(self.receipt_path, receipt)
        replies = [
            self.closure_reply("review"), self.closure_reply("acceptance"),
            self.closure_reply("consolidation"), self.closure_reply("downstream"),
            {"tool": "run_shell", "cmd": "retire", "why": "retire after verified closure"},
            self.closure_reply("retirement"),
        ]
        result, _counts = self.run_horizon(replies)
        self.assertEqual("completed", result["state"])
        self.assertEqual("verified", result["closure"]["milestones"]["M01"]["closure_state"])
        self.assertFalse(status.exists())
        self.assertTrue((self.project / "tabilet/docs/history/status-M01.md").is_file())

    def test_resumed_row_receives_only_its_remaining_model_turns(self):
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(status.read_text(encoding="utf-8").replace("`[ ]`", "`[~]`"), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "record selected row"], cwd=self.project, check=True)
        resumed_head = core.git_head(self.project)
        receipt = self.store.load(self.receipt_path)
        receipt["commit_ids"].append(resumed_head)
        receipt["usage"]["rows_started_ids"] = ["M01/T01"]
        receipt["usage"]["rows_started"] = 1
        receipt["usage"]["turns_by_row"]["M01/T01"] = 2
        receipt["limits"]["max_turns_per_row"] = 4
        self.store.update_atomic(self.receipt_path, receipt)
        replies = [
            {"tool": "run_shell", "cmd": "finish-row", "why": "finish resumed task"},
            {"final": "task finished", "external_actions": []},
            self.closure_reply("review"), self.closure_reply("acceptance"),
            self.closure_reply("consolidation"), self.closure_reply("downstream"),
        ]
        with mock.patch("builtins.print") as printed:
            result, counts = self.run_horizon(replies)
        self.assertEqual("completed", result["state"])
        self.assertEqual(6, counts["attempts"])  # two remaining task turns and four closure phases
        self.assertEqual(4, result["usage"]["turns_by_row"]["M01/T01"])
        output = [str(call.args[0]) for call in printed.call_args_list if call.args]
        self.assertIn("  LLM turn 3/4", output)
        self.assertIn("  LLM turn 4/4", output)

    def test_missing_verification_dependency_after_provider_dispatch_needs_review(self):
        receipt = self.store.load(self.receipt_path)
        receipt["active_operation"] = {"kind": "closure", "phase": "provider_dispatched"}
        self.store.update_atomic(self.receipt_path, receipt)
        with self.assertRaises(SystemExit) as caught:
            horizon._run_sandbox_check(
                core, self.store, self.receipt_path, receipt,
                lambda *_args: {"exit_code": 127, "stderr": "missing-tool"},
                self.project, "required-check", self.args(),
            )
        self.assertEqual(25, caught.exception.code)
        saved = self.store.load(self.receipt_path)
        self.assertEqual("needs_review", saved["state"])
        self.assertEqual("provider_dispatched", saved["active_operation"]["phase"])

    def test_failed_required_check_does_not_make_host_commit(self):
        replies = [
            {"tool": "run_shell", "cmd": "finish-row"},
            {"final": "task finished", "external_actions": []},
        ]
        with self.assertRaises(SystemExit) as caught:
            self.run_horizon(replies, executor=self.executor(fail_check=True))
        self.assertEqual(24, caught.exception.code)
        self.assertEqual(self.head, core.git_head(self.project))
        self.assertEqual("needs_review", self.store.load(self.receipt_path)["state"])

    def test_task_commit_rejects_symlink_in_approved_path(self):
        replies = [
            {"tool": "run_shell", "cmd": "symlink-row"},
            {"final": "task finished", "external_actions": []},
        ]
        with self.assertRaises(SystemExit) as caught:
            self.run_horizon(replies)
        self.assertEqual(24, caught.exception.code)
        self.assertEqual(self.head, core.git_head(self.project))
        self.assertTrue((self.project / "src/feature.py").is_symlink())

    def test_manual_evidence_pauses_before_provider_dispatch(self):
        (self.project / "tabilet/memory-bank/status-M01.md").write_text(
            "# Status\n\n| ID | State | Notes |\n|---|---|---|\n| T01 | `[+]` | Done. |\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "task done"], cwd=self.project, check=True)
        self.receipt["commit_ids"] = [self.head, core.git_head(self.project)]
        self.receipt["state"] = "running"
        self.receipt["approved_horizon"][0]["manual_evidence"] = ["Human acceptance inspection"]
        self.store.update_atomic(self.receipt_path, self.receipt)
        fake_call, calls = self.provider_for([])
        with mock.patch.object(core, "call_llm", side_effect=fake_call):
            with self.assertRaises(SystemExit) as caught:
                horizon.run_horizon(
                    core, self.args(), self.project, self.receipt_path,
                    receipt_store=self.store, executor=self.executor(),
                    controller_module=controller, output_fn=lambda _text: None,
                )
        self.assertEqual(17, caught.exception.code)
        self.assertEqual(0, calls["attempts"])
        self.assertEqual("paused", self.store.load(self.receipt_path)["state"])

    def test_external_action_is_reported_and_never_performed(self):
        replies = [{"final": "cannot continue", "external_actions": ["publish release"]}]
        with self.assertRaises(SystemExit) as caught:
            self.run_horizon(replies)
        self.assertEqual(17, caught.exception.code)
        receipt = self.store.load(self.receipt_path)
        self.assertEqual(["publish release"], receipt["external_actions"])
        self.assertEqual("needs_review", receipt["state"])
        self.assertEqual(self.head, core.git_head(self.project))

    def test_usage_reservations_count_failed_provider_calls_and_resume(self):
        class MemoryStore:
            def update_atomic(self, _path, receipt):
                self.saved = json.loads(json.dumps(receipt))

        memory = MemoryStore()
        receipt = self.store.load(self.receipt_path)
        receipt["limits"]["max_provider_attempts"] = 2
        reservations = horizon.UsageReservations(core, memory, pathlib.Path("unused"), receipt)
        receipt["active_operation"] = {"phase": "prepared"}
        dispatched = []
        def failed_request():
            reservations.reserve_provider_attempt()
            dispatched.append("request")
            raise RuntimeError("provider call failed")
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                failed_request()
        self.assertEqual(2, memory.saved["usage"]["provider_attempts_reserved"])
        self.assertEqual("provider_dispatched", memory.saved["active_operation"]["phase"])
        resumed = horizon.UsageReservations(core, memory, pathlib.Path("unused"), memory.saved)
        with self.assertRaises(horizon.LimitPaused):
            resumed.reserve_provider_attempt()
            dispatched.append("unexpected")
        self.assertEqual(["request", "request"], dispatched)

    def test_limit_extension_requires_clean_checkpoint_and_exact_confirmation(self):
        receipt = self.store.load(self.receipt_path)
        receipt["state"] = "paused"
        self.store.update_atomic(self.receipt_path, receipt)
        result = horizon.extend_limit(
            core, self.store, self.receipt_path, receipt, "max_provider_attempts", 110,
            input_fn=lambda prompt: "confirm" if "a" * 64 in prompt else "stop",
        )
        self.assertEqual("running", result["status"])
        updated = self.store.load(self.receipt_path)
        self.assertEqual(110, updated["limits"]["max_provider_attempts"])
        self.assertEqual(100, updated["limit_extensions"][0]["old_value"])
        self.assertEqual(110, updated["limit_extensions"][0]["new_value"])

    def test_limit_extension_requires_the_original_branch_checkpoint(self):
        receipt = self.store.load(self.receipt_path)
        receipt["state"] = "paused"
        self.store.update_atomic(self.receipt_path, receipt)
        subprocess.run(["git", "switch", "--quiet", "--create", "other"], cwd=self.project, check=True)
        with self.assertRaisesRegex(horizon.HorizonError, "branch changed"):
            horizon.extend_limit(
                core, self.store, self.receipt_path, receipt, "max_provider_attempts", 110,
                input_fn=lambda _prompt: "confirm",
            )
        self.assertEqual(100, self.store.load(self.receipt_path)["limits"]["max_provider_attempts"])

    def test_reached_turn_limit_pauses_at_clean_checkpoint_before_row_selection_write(self):
        receipt = self.store.load(self.receipt_path)
        receipt["usage"]["turns_by_row"]["M01/T01"] = 40
        self.store.update_atomic(self.receipt_path, receipt)
        with self.assertRaises(SystemExit) as caught:
            horizon.run_horizon(
                core, self.args(), self.project, self.receipt_path,
                receipt_store=self.store, executor=self.executor(),
                output_fn=lambda _text: None, controller_module=controller,
            )
        self.assertEqual(16, caught.exception.code)
        self.assertTrue(core.git_clean(self.project))
        self.assertEqual("paused", self.store.load(self.receipt_path)["state"])

    def test_turn_and_commit_caps_persist_across_reservations(self):
        class MemoryStore:
            def update_atomic(self, _path, receipt):
                self.saved = json.loads(json.dumps(receipt))

        memory = MemoryStore()
        receipt = self.store.load(self.receipt_path)
        receipt["limits"]["max_turns_per_row"] = 1
        receipt["limits"]["max_commits"] = 1
        reservations = horizon.UsageReservations(core, memory, pathlib.Path("unused"), receipt)
        reservations.reserve_turn("M01/T01")
        with self.assertRaises(horizon.LimitPaused):
            horizon.UsageReservations(core, memory, pathlib.Path("unused"), memory.saved).reserve_turn("M01/T01")
        with self.assertRaises(horizon.LimitPaused):
            reservations.reserve_commit()
        self.assertEqual(1, memory.saved["usage"]["turns_by_row"]["M01/T01"])
        self.assertEqual(1, memory.saved["usage"]["commits_reserved"])

    def test_supplied_manual_evidence_is_recorded_as_user_evidence(self):
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(status.read_text(encoding="utf-8").replace("`[ ]`", "`[+]`"), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "complete task"], cwd=self.project, check=True)
        receipt = self.store.load(self.receipt_path)
        receipt["commit_ids"].append(core.git_head(self.project))
        receipt["usage"]["commits_recorded"] = 2
        receipt["usage"]["commits_reserved"] = 2
        receipt["approved_horizon"][0]["manual_evidence"] = ["Human acceptance inspection"]
        self.store.update_atomic(self.receipt_path, receipt)
        acceptance = self.closure_reply("acceptance")
        acceptance["manual_evidence_verified"] = True
        result, _counts = self.run_horizon(
            [self.closure_reply("review"), acceptance,
             self.closure_reply("consolidation"), self.closure_reply("downstream")],
            manual_evidence={"M01": {"Human acceptance inspection": "Observed successful use on 2026-09-25."}},
        )
        self.assertEqual("completed", result["state"])
        evidence = result["closure"]["milestones"]["M01"]["manual_evidence"][0]
        self.assertEqual("user", evidence["source"])
        self.assertIn("Observed successful use", evidence["value"])

    def test_p0_review_finding_requires_a_fix_and_whole_milestone_rereview(self):
        replies = [
            {"tool": "run_shell", "cmd": "finish-row"},
            {"final": "task finished", "external_actions": []},
            {"tool": "run_shell", "cmd": "fix-1", "why": "resolve a critical finding"},
            {
                "final": "critical finding fixed", "verified": True,
                "evidence": ["Applied the P0 fix."],
                "findings": [{"severity": "P0", "finding": "Critical release blocker."}],
                "external_actions": [],
            },
            self.closure_reply("review"), self.closure_reply("acceptance"),
            self.closure_reply("consolidation"), self.closure_reply("downstream"),
        ]
        result, _counts = self.run_horizon(replies)
        closure = result["closure"]["milestones"]["M01"]
        self.assertEqual("completed", result["state"])
        self.assertEqual(2, closure["review_iterations"])
        self.assertEqual(3, len(result["commit_ids"]))
        self.assertTrue(any(
            finding["severity"] == "P0"
            for evidence in closure["evidence"]
            for finding in evidence.get("findings", [])
        ))

    def test_task_commit_crash_keeps_operation_intent_for_manual_reconciliation(self):
        replies = [
            {"tool": "run_shell", "cmd": "finish-row"},
            {"final": "task finished", "external_actions": []},
        ]
        original = core.git_local

        def commit_then_crash(args, cwd, *rest, **kwargs):
            result = original(args, cwd, *rest, **kwargs)
            if args and args[0] == "update-ref":
                raise RuntimeError("simulated process boundary after commit")
            return result

        fake_call, _counts = self.provider_for(replies)
        with mock.patch.object(core, "call_llm", side_effect=fake_call), mock.patch.object(
            core, "git_local", side_effect=commit_then_crash,
        ):
            with self.assertRaises(SystemExit) as caught:
                horizon.run_horizon(
                    core, self.args(), self.project, self.receipt_path,
                    receipt_store=self.store, executor=self.executor(),
                    output_fn=lambda _text: None, controller_module=controller,
                )
        self.assertEqual(25, caught.exception.code)
        receipt = self.store.load(self.receipt_path)
        self.assertEqual("needs_review", receipt["state"])
        self.assertEqual("task_commit", receipt["active_operation"]["kind"])
        self.assertEqual("commit_attempted", receipt["active_operation"]["phase"])
        self.assertNotEqual(self.head, core.git_head(self.project))
        self.assertEqual([self.head], receipt["commit_ids"])

    def test_concurrent_ref_advance_wins_task_commit_compare_and_swap(self):
        replies = [
            {"tool": "run_shell", "cmd": "finish-row"},
            {"final": "task finished", "external_actions": []},
        ]
        original = core.git_local
        moved = []

        def advance_before_update(args, cwd, *rest, **kwargs):
            if args and args[0] == "update-ref" and not moved:
                baseline = original(["rev-parse", "--verify", "HEAD"], cwd).stdout.strip()
                tree = original(["rev-parse", "HEAD^{tree}"], cwd).stdout.strip()
                branch = original(["symbolic-ref", "--quiet", "--short", "HEAD"], cwd).stdout.strip()
                candidate = original(["commit-tree", tree, "-p", baseline, "-m", "Concurrent host commit"], cwd)
                self.assertEqual(0, candidate.returncode, candidate.stderr)
                update = original(
                    ["update-ref", f"refs/heads/{branch}", candidate.stdout.strip(), baseline], cwd,
                )
                self.assertEqual(0, update.returncode, update.stderr)
                moved.append(candidate.stdout.strip())
            return original(args, cwd, *rest, **kwargs)

        fake_call, _counts = self.provider_for(replies)
        with mock.patch.object(core, "call_llm", side_effect=fake_call), mock.patch.object(
            core, "git_local", side_effect=advance_before_update,
        ):
            with self.assertRaises(SystemExit) as caught:
                horizon.run_horizon(
                    core, self.args(), self.project, self.receipt_path,
                    receipt_store=self.store, executor=self.executor(),
                    output_fn=lambda _text: None, controller_module=controller,
                )
        self.assertEqual(25, caught.exception.code)
        self.assertTrue(moved)
        receipt = self.store.load(self.receipt_path)
        self.assertEqual("needs_review", receipt["state"])
        self.assertEqual("commit_attempted", receipt["active_operation"]["phase"])
        self.assertEqual([self.head], receipt["commit_ids"])
        head = core.git_head(self.project)
        self.assertEqual(moved[0], head)
        self.assertNotEqual("Complete M01/T01", subprocess.run(
            ["git", "log", "-1", "--format=%s"], cwd=self.project,
            text=True, capture_output=True, check=True,
        ).stdout.strip())

    def test_unexpected_head_advance_stops_before_controller_commit(self):
        replies = [
            {"tool": "run_shell", "cmd": "external-commit"},
            {"final": "task finished", "external_actions": []},
        ]
        with self.assertRaises(SystemExit) as caught:
            self.run_horizon(replies)
        self.assertEqual(25, caught.exception.code)
        receipt = self.store.load(self.receipt_path)
        self.assertEqual("needs_review", receipt["state"])
        self.assertEqual("task", receipt["active_operation"]["kind"])
        message = subprocess.run(
            ["git", "log", "-1", "--format=%s"], cwd=self.project,
            text=True, capture_output=True, check=True,
        ).stdout.strip()
        self.assertEqual("concurrent host commit", message)
        self.assertEqual([self.head], receipt["commit_ids"])

    def test_review_iteration_cap_persists_before_manual_review(self):
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(status.read_text(encoding="utf-8").replace("`[ ]`", "`[+]`"), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "complete task"], cwd=self.project, check=True)
        receipt = self.store.load(self.receipt_path)
        receipt["commit_ids"].append(core.git_head(self.project))
        receipt["usage"]["commits_recorded"] = 2
        receipt["usage"]["commits_reserved"] = 2
        self.store.update_atomic(self.receipt_path, receipt)
        replies = []
        for number in range(1, 11):
            replies.extend([
                {"tool": "run_shell", "cmd": f"fix-{number}"},
                {
                    "final": "fixed, needs another review", "verified": True,
                    "evidence": [f"Applied iteration {number} fix."],
                    "findings": [{"severity": "P2", "finding": "Review again after fix."}],
                    "external_actions": [],
                },
            ])
        with self.assertRaises(SystemExit) as caught:
            self.run_horizon(replies)
        self.assertEqual(25, caught.exception.code)
        result = self.store.load(self.receipt_path)
        self.assertEqual(10, result["closure"]["milestones"]["M01"]["review_iterations"])
        self.assertEqual("needs_review", result["state"])
        self.assertEqual(12, len(result["commit_ids"]))


if __name__ == "__main__":
    unittest.main()

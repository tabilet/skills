from __future__ import annotations

import hashlib
import contextlib
import importlib.machinery
import importlib.util
import json
import pathlib
import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest import mock
from types import SimpleNamespace


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "tests"))
import test_harness


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


core = test_harness.harness
proposal = load_module("resume_proposal", ROOT / "harness/tabilet_proposal.py")
recovery = load_module("resume_recovery", ROOT / "harness/tabilet_recovery.py")
status_api = load_module("resume_status", ROOT / "harness/tabilet_status.py")
controller = load_module("resume_controller", ROOT / "harness/tabilet_controller.py")
horizon = load_module("resume_horizon", ROOT / "harness/tabilet_horizon.py")


def horizon_args():
    return SimpleNamespace(
        max_turns=40, tool_timeout=5, max_tool_output=1000,
        allow_dangerous=False, tool_env=[],
    )


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


class ResumeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        test_harness.make_repo(self.project)
        self.baseline = core.git_head(self.project)
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(
            "# Status\n\n| ID | State | Notes |\n|---|---|---|\n"
            "| T01 | `[ ]` | Implement feature. |\n",
            encoding="utf-8",
        )
        git("add", "-A", cwd=self.project)
        git("-c", "user.name=Resume Test", "-c", "user.email=resume@example.test",
            "commit", "-qm", "planning baseline", cwd=self.project)
        self.head = core.git_head(self.project)
        self.store = proposal.ReceiptStore(self.root / "private" / "tabilet" / "receipts")
        self.receipt = self.make_receipt()
        self.path = self.store.create(self.project, self.receipt)

    def make_receipt(self):
        return {
            "schema": proposal.RECEIPT_SCHEMA,
            "receipt_id": str(uuid.uuid4()),
            "project_path": str(self.project.resolve()),
            "proposal_sha256": "a" * 64,
            "branch": core.git_branch(self.project),
            "baseline_commit": self.baseline,
            "planning_commit": self.head,
            "state": "running",
            "approved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "horizon_ids": ["M01"],
            "approved_horizon": [{
                "id": "M01", "title": "Delivery", "acceptance": "Feature works.",
                "dependencies": [], "retirement_adopted": False,
                "closure_paths": ["tabilet/memory-bank/milestone.md", "tabilet/memory-bank/status-M01.md"],
                "manual_evidence": [],
                "tasks": [{
                    "id": "T01", "owner": "agent", "description": "Implement feature.",
                    "acceptance": "Feature works.", "verification": ["true"],
                    "approved_paths": ["src/feature.py", "tabilet/memory-bank/status-M01.md"],
                }],
            }],
            "external_actions": [], "image_id": "sha256:" + "a" * 64,
            "limits": dict(proposal.DEFAULT_LIMITS),
            "usage": {
                "rows_started": 0, "rows_started_ids": [],
                "provider_attempts_reserved": 0, "commits_reserved": 1,
                "commits_recorded": 1, "turns_by_row": {},
            },
            "commit_ids": [self.head], "active_operation": None,
            "closure": {"milestones": {}}, "verification_evidence": [],
            "mutation_scope": "local_only", "pause_reason": None,
        }

    def persist(self, receipt):
        self.store.update_atomic(self.path, receipt)

    def test_status_is_read_only_for_project_and_receipts(self):
        receipt = self.store.load(self.path)
        receipt["state"] = "paused"
        receipt["pause_reason"] = "operator pause"
        receipt["closure"]["milestones"]["M01"] = {
            "closure_state": "pending", "phase": "review", "review_iterations": 3,
        }
        self.persist(receipt)
        older_higher_count = json.loads(json.dumps(receipt))
        older_higher_count["receipt_id"] = str(uuid.uuid4())
        older_higher_count["closure"]["milestones"]["M01"]["review_iterations"] = 7
        self.store.create(self.project, older_higher_count)
        audit_db = self.root / "audit.sqlite"
        audit_db.write_bytes(b"read only audit fixture\n")
        before_project = tree_digest(self.project)
        before_receipts = tree_digest(self.store.directory)
        with mock.patch.object(core, "project_lock", side_effect=AssertionError("status must not lock")):
            report = controller.status_project(core, self.project, receipt_store=self.store, output_fn=lambda _text: None)
        self.assertEqual(before_project, tree_digest(self.project))
        self.assertEqual(before_receipts, tree_digest(self.store.directory))
        self.assertEqual(b"read only audit fixture\n", audit_db.read_bytes())
        self.assertEqual("paused", report["receipt"][0]["state"])
        self.assertEqual(1, report["milestones"][0]["rows"]["pending"])
        self.assertEqual(7, report["review_count"]["M01"])

    def test_resume_rejects_a_concurrent_tabilet_lock_with_exit_19(self):
        args = horizon_args()
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")}):
            with core.project_lock(self.project):
                with self.assertRaises(SystemExit) as caught:
                    controller.resume_horizon(
                        core, args, self.project, self.path, receipt_store=self.store,
                        output_fn=lambda _text: None,
                    )
        self.assertEqual(19, caught.exception.code)

    def test_resume_treats_a_changed_branch_as_stale_approval(self):
        git("switch", "-qc", "new-branch", cwd=self.project)
        with mock.patch.object(core, "project_lock", lambda _repo: contextlib.nullcontext()):
            with self.assertRaises(SystemExit) as caught:
                controller.resume_horizon(
                    core, horizon_args(), self.project, self.path,
                    receipt_store=self.store, output_fn=lambda _text: None,
                )
        self.assertEqual(18, caught.exception.code)

    def test_audit_failure_does_not_change_verified_completion(self):
        calls = []

        class BrokenAudit:
            def __init__(self, *_args, **kwargs):
                calls.append(("init", kwargs))

            def emit(self, *_args, **_kwargs):
                calls.append(("emit", None))

            def finish(self, result):
                calls.append(("finish", result))
                raise OSError("audit database unavailable")

        class FakeHorizon:
            @staticmethod
            def run_horizon(*_args, **_kwargs):
                return {"state": "completed", "closure": {}}

        args = SimpleNamespace(provider="openai", model="test", audit_db=None, audit_capture="metadata")
        receipt = self.store.load(self.path)
        with mock.patch.object(core, "AuditRun", BrokenAudit), mock.patch.object(
            controller, "prepare_docker_executor", return_value=object(),
        ):
            result = controller._execute_horizon_locked(
                core, args, self.project, self.path, receipt, self.store,
                horizon=FakeHorizon(), output_fn=lambda _text: None,
            )
        self.assertEqual("completed", result["state"])
        self.assertEqual("host_operation", calls[0][1]["invocation_kind"])
        self.assertIn(("finish", "completed"), calls)

    def test_clean_prepared_operation_is_cleared_and_paused(self):
        receipt = self.store.load(self.path)
        receipt["active_operation"] = {
            "kind": "task", "phase": "prepared", "expected_head": self.head,
            "row_id": "M01/T01", "paths": ["src/feature.py"],
        }
        self.persist(receipt)
        result = recovery.reconcile_receipt(core, self.store, self.path, receipt, self.project)
        self.assertEqual("paused", result["state"])
        self.assertIsNone(result["active_operation"])

    def test_dirty_prepared_operation_enters_review_without_reset(self):
        receipt = self.store.load(self.path)
        receipt["active_operation"] = {
            "kind": "task", "phase": "prepared", "expected_head": self.head,
            "row_id": "M01/T01", "paths": ["src/feature.py"],
        }
        self.persist(receipt)
        dirty = self.project / "src/feature.py"
        dirty.parent.mkdir()
        dirty.write_text("partial\n", encoding="utf-8")
        with self.assertRaises(recovery.RecoveryError):
            recovery.reconcile_receipt(core, self.store, self.path, receipt, self.project)
        self.assertTrue(dirty.exists())
        self.assertEqual("needs_review", self.store.load(self.path)["state"])

    def test_provider_dispatch_with_clean_tree_still_requires_review(self):
        receipt = self.store.load(self.path)
        receipt["active_operation"] = {
            "kind": "task", "phase": "provider_dispatched", "expected_head": self.head,
            "row_id": "M01/T01", "paths": ["src/feature.py"],
        }
        self.persist(receipt)
        with self.assertRaisesRegex(recovery.RecoveryError, "will not be replayed"):
            recovery.reconcile_receipt(core, self.store, self.path, receipt, self.project)
        self.assertEqual(self.head, core.git_head(self.project))
        self.assertEqual("needs_review", self.store.load(self.path)["state"])

    def _make_candidate(self, receipt, operation, changed_paths, message):
        for path in changed_paths:
            target = self.project / path
            target.parent.mkdir(parents=True, exist_ok=True)
        git("add", "--", *changed_paths, cwd=self.project)
        patch_text = core.git_local(["diff", "--cached", "--no-renames", "--binary", "--"], self.project).stdout
        receipt["active_operation"] = operation
        receipt["usage"]["commits_reserved"] += 1
        self.persist(receipt)

        def checkpoint(candidate, tree):
            operation.update({
                "phase": "commit_attempted", "candidate_commit": candidate,
                "expected_tree": tree,
                "expected_patch_sha256": hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
                "commit_message": message,
            })
            receipt["active_operation"] = operation
            self.persist(receipt)

        proposal.commit_staged_tree(
            core, self.project, self.head, core.git_branch(self.project), patch_text, message,
            before_ref_update=checkpoint,
        )

    def test_exact_task_commit_is_recorded_once_after_crash(self):
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(status.read_text(encoding="utf-8").replace("`[ ]`", "`[+]`"), encoding="utf-8")
        (self.project / "src/feature.py").parent.mkdir(parents=True)
        (self.project / "src/feature.py").write_text("feature = True\n", encoding="utf-8")
        receipt = self.store.load(self.path)
        after = core.row_snapshot(self.project)
        operation = {
            "kind": "task_commit", "operation_id": str(uuid.uuid4()), "phase": "precommit_verified",
            "expected_head": self.head, "milestone_id": "M01", "task_id": "T01",
            "row_id": "M01/T01", "row_key": ["status-M01.md", "T01", 1],
            "paths": ["src/feature.py", "tabilet/memory-bank/status-M01.md"],
            "verification": ["true"], "verification_results": {"true": True},
            "expected_snapshot_sha256": load_module(
                "resume_horizon_digest", ROOT / "harness/tabilet_horizon.py"
            ).snapshot_digest(after),
        }
        receipt["verification_evidence"] = [{
            "row_id": "M01/T01", "command": "true", "exit_code": 0,
        }]
        receipt["usage"]["rows_started"] = 1
        receipt["usage"]["rows_started_ids"] = ["M01/T01"]
        self._make_candidate(
            receipt, operation,
            ["src/feature.py", "tabilet/memory-bank/status-M01.md"],
            "Complete M01/T01",
        )
        saved = self.store.load(self.path)
        recovered = recovery.reconcile_receipt(core, self.store, self.path, saved, self.project)
        self.assertEqual("running", recovered["state"])
        self.assertEqual(2, len(recovered["commit_ids"]))
        self.assertEqual(core.git_head(self.project), recovered["commit_ids"][-1])
        again = recovery.reconcile_receipt(core, self.store, self.path, recovered, self.project)
        self.assertEqual(2, len(again["commit_ids"]))

    def test_identical_content_move_recovers_with_the_captured_no_rename_patch(self):
        source = self.project / "src/feature.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("feature = True\n", encoding="utf-8")
        git("add", "-A", cwd=self.project)
        git("-c", "user.name=Resume Test", "-c", "user.email=resume@example.test",
            "commit", "-qm", "add feature source", cwd=self.project)
        self.head = core.git_head(self.project)

        receipt = self.store.load(self.path)
        receipt["commit_ids"].append(self.head)
        receipt["usage"]["commits_reserved"] += 1
        receipt["usage"]["commits_recorded"] += 1
        receipt["approved_horizon"][0]["tasks"][0]["approved_paths"].append("src/moved.py")
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(status.read_text(encoding="utf-8").replace("`[ ]`", "`[+]`"), encoding="utf-8")
        destination = self.project / "src/moved.py"
        source.rename(destination)
        after = core.row_snapshot(self.project)
        operation = {
            "kind": "task_commit", "operation_id": str(uuid.uuid4()), "phase": "precommit_verified",
            "expected_head": self.head, "milestone_id": "M01", "task_id": "T01",
            "row_id": "M01/T01", "row_key": ["status-M01.md", "T01", 1],
            "paths": ["src/feature.py", "src/moved.py", "tabilet/memory-bank/status-M01.md"],
            "verification": ["true"], "verification_results": {"true": True},
            "expected_snapshot_sha256": horizon.snapshot_digest(after),
        }
        receipt["verification_evidence"] = [{
            "row_id": "M01/T01", "command": "true", "exit_code": 0,
        }]
        receipt["usage"]["rows_started"] = 1
        receipt["usage"]["rows_started_ids"] = ["M01/T01"]
        self._make_candidate(
            receipt, operation, operation["paths"], "Complete M01/T01",
        )

        recovered = recovery.reconcile_receipt(
            core, self.store, self.path, self.store.load(self.path), self.project,
        )
        self.assertEqual("running", recovered["state"])
        self.assertEqual(core.git_head(self.project), recovered["commit_ids"][-1])
        self.assertFalse(source.exists())
        self.assertTrue(destination.is_file())

    def test_exact_closure_commit_advances_phase_after_crash(self):
        receipt = self.store.load(self.path)
        horizon = load_module("resume_horizon_closure", ROOT / "harness/tabilet_horizon.py")
        before = core.row_snapshot(self.project)
        operation_id = str(uuid.uuid4())
        phase_result = {
            "phase": "review", "operation_id": operation_id, "verified": True,
            "manual_evidence_verified": False,
            "iteration": 1, "items": ["Whole milestone reviewed."], "findings": [],
            "retry_review": False,
        }
        milestone_path = self.project / "tabilet/memory-bank/milestone.md"
        milestone_path.write_text(milestone_path.read_text(encoding="utf-8") + "\nReviewed.\n", encoding="utf-8")
        status_path = self.project / "tabilet/memory-bank/status-M01.md"
        status_path.write_text(
            status_path.read_text(encoding="utf-8")
            + '\n**Review gate.** passed\n**Review iterations.** 1\n**Review findings.** []\n',
            encoding="utf-8",
        )
        after = core.row_snapshot(self.project)
        receipt["closure"]["milestones"]["M01"] = {
            "closure_state": "pending", "phase": "review", "review_iterations": 1,
            "evidence": [], "manual_evidence": [],
        }
        operation = {
            "kind": "closure_commit", "operation_id": operation_id,
            "phase": "precommit_verified", "closure_phase": "review", "milestone_id": "M01",
            "expected_head": self.head,
            "paths": ["tabilet/memory-bank/milestone.md", "tabilet/memory-bank/status-M01.md"],
            "before_snapshot_sha256": horizon.snapshot_digest(before),
            "expected_snapshot_sha256": horizon.snapshot_digest(after),
            "phase_result": phase_result,
        }
        self._make_candidate(receipt, operation, operation["paths"], "Review closure for M01")
        recovered = recovery.reconcile_receipt(
            core, self.store, self.path, self.store.load(self.path), self.project,
        )
        self.assertEqual("acceptance", recovered["closure"]["milestones"]["M01"]["phase"])
        self.assertEqual(1, len(recovered["closure"]["milestones"]["M01"]["evidence"]))
        again = recovery.reconcile_receipt(core, self.store, self.path, recovered, self.project)
        self.assertEqual(1, len(again["closure"]["milestones"]["M01"]["evidence"]))

    def test_closure_commit_already_recorded_before_phase_update_is_idempotent(self):
        receipt = self.store.load(self.path)
        horizon_module = load_module("resume_horizon_recorded", ROOT / "harness/tabilet_horizon.py")
        before = core.row_snapshot(self.project)
        operation_id = str(uuid.uuid4())
        result = {
            "phase": "review", "operation_id": operation_id, "verified": True,
            "manual_evidence_verified": False,
            "iteration": 1, "items": ["Review passed."], "findings": [], "retry_review": False,
        }
        path = self.project / "tabilet/memory-bank/milestone.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nReview note.\n", encoding="utf-8")
        status_path = self.project / "tabilet/memory-bank/status-M01.md"
        status_path.write_text(
            status_path.read_text(encoding="utf-8")
            + '\n**Review gate.** passed\n**Review iterations.** 1\n**Review findings.** []\n',
            encoding="utf-8",
        )
        after = core.row_snapshot(self.project)
        receipt["closure"]["milestones"]["M01"] = {
            "closure_state": "pending", "phase": "review", "review_iterations": 1,
            "evidence": [], "manual_evidence": [],
        }
        operation = {
            "kind": "closure_commit", "operation_id": operation_id,
            "phase": "commit_attempted", "closure_phase": "review", "milestone_id": "M01",
            "expected_head": self.head,
            "paths": ["tabilet/memory-bank/milestone.md", "tabilet/memory-bank/status-M01.md"],
            "before_snapshot_sha256": horizon_module.snapshot_digest(before),
            "expected_snapshot_sha256": horizon_module.snapshot_digest(after),
            "phase_result": result,
        }
        self._make_candidate(receipt, operation, operation["paths"], "Review closure for M01")
        latest = self.store.load(self.path)
        latest["commit_ids"].append(core.git_head(self.project))
        latest["usage"]["commits_recorded"] += 1
        self.persist(latest)
        recovered = recovery.reconcile_receipt(core, self.store, self.path, latest, self.project)
        self.assertEqual(2, len(recovered["commit_ids"]))
        self.assertEqual("acceptance", recovered["closure"]["milestones"]["M01"]["phase"])

    def test_persisted_no_change_closure_result_advances_without_replay(self):
        receipt = self.store.load(self.path)
        horizon = load_module("resume_horizon_nochange", ROOT / "harness/tabilet_horizon.py")
        operation_id = str(uuid.uuid4())
        receipt["closure"]["milestones"]["M01"] = {
            "closure_state": "pending", "phase": "acceptance", "review_iterations": 1,
            "evidence": [{
                "phase": "acceptance", "source": "command", "command": "true", "exit_code": 0,
            }], "manual_evidence": [],
        }
        receipt["active_operation"] = {
            "kind": "closure", "operation_id": operation_id, "phase": "result_recorded",
            "closure_phase": "acceptance", "milestone_id": "M01", "expected_head": self.head,
            "before_snapshot_sha256": horizon.snapshot_digest(core.row_snapshot(self.project)),
            "expected_snapshot_sha256": horizon.snapshot_digest(core.row_snapshot(self.project)),
                "phase_result": {
                "phase": "acceptance", "operation_id": operation_id, "verified": True,
                "manual_evidence_verified": False,
                "iteration": None, "items": ["No changes required."], "findings": [],
                "retry_review": False,
            },
        }
        self.persist(receipt)
        recovered = recovery.reconcile_receipt(core, self.store, self.path, receipt, self.project)
        self.assertEqual("consolidation", recovered["closure"]["milestones"]["M01"]["phase"])
        self.assertEqual(2, len(recovered["closure"]["milestones"]["M01"]["evidence"]))

    def test_ctrl_c_at_clean_pre_dispatch_checkpoint_pauses(self):
        status = self.project / "tabilet/memory-bank/status-M01.md"
        status.write_text(status.read_text(encoding="utf-8").replace("`[ ]`", "`[+]`"), encoding="utf-8")
        git("add", "-A", cwd=self.project)
        git("-c", "user.name=Resume Test", "-c", "user.email=resume@example.test",
            "commit", "-qm", "planning row completion", cwd=self.project)
        planning_head = core.git_head(self.project)
        receipt = self.store.load(self.path)
        receipt["baseline_commit"] = self.head
        receipt["planning_commit"] = planning_head
        receipt["commit_ids"] = [planning_head]
        self.head = planning_head
        self.persist(receipt)

        def interrupt_before_dispatch(_message):
            raise KeyboardInterrupt

        with self.assertRaises(SystemExit) as caught:
            horizon.run_horizon(
                core, horizon_args(),
                self.project, self.path, receipt_store=self.store, executor=lambda *_args: None,
                output_fn=interrupt_before_dispatch, controller_module=controller,
            )
        self.assertEqual(130, caught.exception.code)
        saved = self.store.load(self.path)
        self.assertEqual("paused", saved["state"])
        self.assertIsNone(saved["active_operation"])

    def test_ctrl_c_with_partial_task_marks_manual_review_without_reset(self):
        args = horizon_args()
        with mock.patch.object(controller, "run_controller_agent", side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit) as caught:
                horizon.run_horizon(
                    core, args, self.project, self.path, receipt_store=self.store,
                    executor=lambda *_args: {"exit_code": 0, "stdout": "", "stderr": ""},
                    output_fn=lambda _message: None, controller_module=controller,
                )
        self.assertEqual(130, caught.exception.code)
        saved = self.store.load(self.path)
        self.assertEqual("needs_review", saved["state"])
        self.assertIsNotNone(saved["active_operation"])
        self.assertIn("`[~]`", (self.project / "tabilet/memory-bank/status-M01.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

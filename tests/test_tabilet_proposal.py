from __future__ import annotations

import hashlib
import contextlib
import importlib.machinery
import importlib.util
import json
import io
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def load_module(name: str, path: pathlib.Path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


core = load_module("proposal_test_runner", ROOT / "harness/tackle-memory-bank-api-loop")
proposal_api = load_module("proposal_test_module", ROOT / "harness/tabilet_proposal.py")
controller = load_module("proposal_test_controller", ROOT / "harness/tabilet_controller.py")


def git(*args: str, cwd: pathlib.Path):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)


class InjectedCrash(RuntimeError):
    pass


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        git("init", "-q", cwd=self.project)
        git("config", "user.name", "Proposal Test", cwd=self.project)
        git("config", "user.email", "proposal-test@example.test", cwd=self.project)
        memory = self.project / "tabilet/memory-bank"
        memory.mkdir(parents=True)
        (memory / "milestone.md").write_text("# Milestones\nOriginal plan.\n", encoding="utf-8")
        (memory / "status-M01.md").write_text("# Status M01\n| ID | Status | Task |\n|---|---|---|\n", encoding="utf-8")
        self.commit("baseline")
        self.receipt_dir = self.root / "private-state" / "tabilet" / "receipts"
        self.store = proposal_api.ReceiptStore(self.receipt_dir)
        self.outputs = []
        self.input_calls = 0
        self.plan = self.make_proposal()

    def commit(self, message):
        result = git("add", "-A", cwd=self.project)
        self.assertEqual(0, result.returncode, result.stderr)
        result = git("commit", "-qm", message, cwd=self.project)
        self.assertEqual(0, result.returncode, result.stderr)

    def make_proposal(self, *, repo=None, body="Revised plan.\n", extra_path="tabilet/memory-bank/milestone-notes.md"):
        project = repo or self.project
        scratch = self.root / f"patch-source-{len(list(self.root.glob('patch-source-*')))}"
        result = git("clone", "-q", "--no-hardlinks", str(project), str(scratch), cwd=self.root)
        self.assertEqual(0, result.returncode, result.stderr)
        path = scratch / "tabilet/memory-bank/milestone.md"
        path.write_text("# Milestones\n" + body, encoding="utf-8")
        extra = scratch / extra_path
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("Approved planning note.\n", encoding="utf-8")
        git("add", "-N", "--", extra_path, cwd=scratch)
        result = git("diff", "--binary", "HEAD", "--", cwd=scratch)
        self.assertEqual(0, result.returncode, result.stderr)
        return {
            "title": "A bounded milestone plan",
            "delivery_boundary": "One local project horizon ending at a user-verifiable outcome.",
            "horizon": [{
                "id": "M01",
                "title": "Complete the first outcome",
                "acceptance": "The first delivery outcome works end to end.",
                "dependencies": [],
                "closure_paths": [
                    "tabilet/memory-bank/milestone.md",
                    "tabilet/memory-bank/status-M01.md",
                ],
                "tasks": [{
                    "id": "M01-T01",
                    "owner": "implementation agent",
                    "description": "Implement the approved scope.",
                    "acceptance": "The change meets the milestone acceptance criteria.",
                    "verification": ["python3 check.py"],
                    "approved_paths": [
                        "src/example.py",
                        "tabilet/memory-bank/status-M01.md",
                    ],
                }],
            }],
            "candidate_directions": ["A later optional extension."],
            "file_actions": [
                {"path": "tabilet/memory-bank/milestone.md", "action": "replace"},
                {"path": extra_path, "action": "create"},
            ],
            "diff": result.stdout,
            "image_id": "sha256:" + "a" * 64,
            "limits": {},
            "planned_commits": 2,
            "external_actions": ["None are included in this authorization."],
        }

    def inputs(self, *values):
        iterator = iter(values)

        def ask(_prompt):
            self.input_calls += 1
            return next(iterator)

        return ask

    def approve(self, proposal=None, **kwargs):
        return proposal_api.approve_proposal(
            core, self.project, proposal or self.plan, receipt_store=self.store,
            input_fn=kwargs.pop("input_fn", self.inputs("confirm")),
            output_fn=self.outputs.append,
            **kwargs,
        )

    def receipt_path(self):
        paths = list(self.receipt_dir.glob("*.json")) if self.receipt_dir.exists() else []
        self.assertEqual(1, len(paths))
        return paths[0]

    def test_render_is_deterministic_and_shows_every_limit_and_exact_patch(self):
        snapshot = proposal_api.capture_project_snapshot(core, self.project, self.plan["file_actions"])
        text_a, digest_a = proposal_api.render_proposal(self.plan, snapshot)
        text_b, digest_b = proposal_api.render_proposal(self.plan, snapshot)
        self.assertEqual(text_a, text_b)
        self.assertEqual(digest_a, digest_b)
        self.assertIn(self.plan["diff"], text_a)
        self.assertIn('"max_rows": 5', text_a)
        self.assertIn('"max_provider_attempts": 100', text_a)
        self.assertIn('"max_turns_per_row": 40', text_a)
        self.assertIn('"max_commits": 15', text_a)
        self.assertIn('"max_runtime_seconds": 7200', text_a)
        self.assertIn('"cpus": 4', text_a)
        self.assertIn('"memory_mib": 8192', text_a)
        self.assertIn('"processes": 512', text_a)
        self.assertIn('"command_timeout_seconds": 300', text_a)
        self.assertIn('"planning": 1', text_a)
        self.assertIn('"task_rows": 1', text_a)
        self.assertIn('"total": 2', text_a)
        self.assertEqual("a bounded local horizon", proposal_api.validate_proposal({**self.plan, "delivery_boundary": "a bounded local horizon"})["delivery_boundary"])

    def test_reject_feedback_revises_without_project_or_receipt_writes(self):
        files_before = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*") if path.is_file() and ".git" not in path.parts
        }
        index_before = (self.project / ".git/index").read_bytes()
        status_before = git("status", "--porcelain=v1", "-z", cwd=self.project).stdout
        revisions = []

        def revise(old, feedback):
            revisions.append(feedback)
            return old

        result = self.approve(
            input_fn=self.inputs("reject", "Keep it smaller.", "reject", "Move verification earlier.", "stop"),
            revise_fn=revise,
        )
        files_after = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*") if path.is_file() and ".git" not in path.parts
        }
        self.assertEqual("cancelled", result["status"])
        self.assertEqual(["Keep it smaller.", "Move verification earlier."], revisions)
        self.assertEqual(3, len(self.outputs))
        self.assertEqual(files_before, files_after)
        self.assertEqual(index_before, (self.project / ".git/index").read_bytes())
        self.assertEqual(status_before, git("status", "--porcelain=v1", "-z", cwd=self.project).stdout)
        self.assertFalse(self.receipt_dir.exists())

    def test_confirm_creates_private_receipt_before_project_write_and_commits_exact_diff(self):
        baseline = git("rev-parse", "HEAD", cwd=self.project).stdout.strip()
        staged = []

        def fault(stage):
            if stage == "after_receipt":
                path = self.receipt_path()
                receipt = self.store.load(path)
                self.assertEqual("approved", receipt["state"])
                self.assertEqual(baseline, receipt["baseline_commit"])
                self.assertEqual("prepared", receipt["active_operation"]["phase"])
                self.assertEqual(0o600, path.stat().st_mode & 0o777)
                self.assertFalse(path.is_relative_to(self.project))
                self.assertEqual("# Milestones\nOriginal plan.\n", (self.project / "tabilet/memory-bank/milestone.md").read_text())
                staged.append(True)

        result = self.approve(fault_hook=fault)
        self.assertTrue(staged)
        receipt_path = pathlib.Path(result["receipt_path"])
        receipt = self.store.load(receipt_path)
        self.assertEqual("running", receipt["state"])
        self.assertEqual(hashlib.sha256(self.plan["diff"].encode()).hexdigest(), receipt["diff_sha256"])
        self.assertEqual(hashlib.sha256(self.outputs[0].encode()).hexdigest(), receipt["proposal_sha256"])
        self.assertEqual("local_only", receipt["mutation_scope"])
        self.assertEqual(1, receipt["usage"]["commits_recorded"])
        self.assertEqual(
            {"tabilet/memory-bank/milestone.md", "tabilet/memory-bank/milestone-notes.md"},
            set(receipt["result_action_sha256"]),
        )
        self.assertTrue(all(
            value is None or len(value) == 64
            for value in receipt["result_action_sha256"].values()
        ))
        self.assertTrue(receipt["planning_commit"])
        self.assertEqual("# Milestones\nRevised plan.\n", (self.project / "tabilet/memory-bank/milestone.md").read_text())
        self.assertEqual("Approved planning note.\n", (self.project / "tabilet/memory-bank/milestone-notes.md").read_text())
        self.assertEqual("", git("status", "--porcelain", cwd=self.project).stdout)
        self.assertEqual(self.plan["diff"], git("show", "--format=", "--binary", "HEAD", cwd=self.project).stdout)
        self.assertEqual(baseline, git("rev-parse", "HEAD^", cwd=self.project).stdout.strip())

    def test_concurrent_ref_advance_wins_compare_and_swap_without_planning_commit(self):
        moved = []

        def advance_ref(stage):
            if stage != "before_ref_update":
                return
            baseline = git("rev-parse", "HEAD", cwd=self.project).stdout.strip()
            tree = git("rev-parse", "HEAD^{tree}", cwd=self.project).stdout.strip()
            branch = git("symbolic-ref", "--quiet", "--short", "HEAD", cwd=self.project).stdout.strip()
            candidate = git(
                "commit-tree", tree, "-p", baseline, "-m", "Concurrent external commit",
                cwd=self.project,
            )
            self.assertEqual(0, candidate.returncode, candidate.stderr)
            update = git(
                "update-ref", f"refs/heads/{branch}", candidate.stdout.strip(), baseline,
                cwd=self.project,
            )
            self.assertEqual(0, update.returncode, update.stderr)
            moved.append(candidate.stdout.strip())

        result = self.approve(fault_hook=advance_ref)
        self.assertEqual("needs_review", result["status"])
        self.assertIn("planning ref changed", result["reason"])
        self.assertEqual(1, len(moved))
        self.assertEqual(moved[0], git("rev-parse", "HEAD", cwd=self.project).stdout.strip())
        self.assertEqual(2, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))
        self.assertNotEqual(self.plan["diff"], git("show", "--format=", "--binary", "HEAD", cwd=self.project).stdout)
        receipt = self.store.load(self.receipt_path())
        self.assertEqual("commit_attempted", receipt["active_operation"]["phase"])

    def test_branch_switch_at_same_head_does_not_redirect_approved_commit(self):
        approved_branch = core.git_branch(self.project)
        baseline = git("rev-parse", "HEAD", cwd=self.project).stdout.strip()
        switched = []

        def switch_branch(stage):
            if stage == "before_ref_update":
                result = git("switch", "--quiet", "--create", "unapproved", cwd=self.project)
                self.assertEqual(0, result.returncode, result.stderr)
                switched.append(True)

        result = self.approve(fault_hook=switch_branch)
        self.assertTrue(switched)
        self.assertEqual("needs_review", result["status"])
        self.assertIn("HEAD target changed", result["reason"])
        self.assertEqual("unapproved", core.git_branch(self.project))
        self.assertEqual(baseline, git("rev-parse", f"refs/heads/{approved_branch}", cwd=self.project).stdout.strip())
        self.assertEqual(baseline, git("rev-parse", "refs/heads/unapproved", cwd=self.project).stdout.strip())
        self.assertEqual(baseline, git("rev-parse", "HEAD", cwd=self.project).stdout.strip())

    def test_invalid_target_drift_requires_revised_proposal_before_any_receipt(self):
        calls = []

        def ask(_prompt):
            if not calls:
                (self.project / "tabilet/memory-bank/milestone-notes.md").write_text("user file\n")
                calls.append("confirm")
                return "confirm"
            return "confirm"

        def revise(old, feedback):
            self.assertIn("file-action targets changed", feedback)
            (self.project / "tabilet/memory-bank/milestone-notes.md").unlink()
            return old

        result = self.approve(input_fn=ask, revise_fn=revise)
        self.assertEqual("running", result["status"], result)
        self.assertEqual(3, len(self.outputs))

    def test_dirty_worktree_drift_without_replanner_exits_stale_and_writes_no_receipt(self):
        def ask(_prompt):
            (self.project / "README.md").write_text("uncommitted drift\n")
            return "confirm"

        with self.assertRaises(proposal_api.ApprovalStale):
            self.approve(input_fn=ask)
        self.assertFalse(self.receipt_dir.exists())
        self.assertEqual("uncommitted drift\n", (self.project / "README.md").read_text())

    def test_branch_drift_forces_a_revised_proposal(self):
        calls = []

        def ask(_prompt):
            if not calls:
                git("switch", "-c", "approved-on-new-branch", cwd=self.project)
                calls.append(True)
            return "confirm"

        reasons = []

        def revise(old, feedback):
            reasons.append(feedback)
            return old

        result = self.approve(input_fn=ask, revise_fn=revise)
        self.assertEqual("running", result["status"])
        self.assertEqual(1, len(reasons))
        self.assertIn("branch changed", reasons[0])
        self.assertEqual("approved-on-new-branch", self.store.load(pathlib.Path(result["receipt_path"]))["branch"])

    def test_permanent_id_drift_forces_a_revised_proposal(self):
        calls = []
        reasons = []

        def revise(old, feedback):
            reasons.append(feedback)
            return old

        def ask_with_new_id(_prompt):
            if not calls:
                path = self.project / "tabilet/memory-bank/status-M02.md"
                path.write_text("# Status M02\n| ID | Status | Task |\n|---|---|---|\n")
                self.commit("add permanent M02 identity")
                calls.append(True)
            return "confirm"

        result = self.approve(input_fn=ask_with_new_id, revise_fn=revise)
        self.assertEqual("running", result["status"])
        self.assertTrue(any("permanent status IDs changed" in reason for reason in reasons))

    def test_crash_after_receipt_before_apply_resumes_once_from_clean_baseline(self):
        def crash(stage):
            if stage == "after_receipt":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=crash)
        path = self.receipt_path()
        baseline = self.store.load(path)["baseline_commit"]
        self.assertEqual("", git("status", "--porcelain", cwd=self.project).stdout)
        result = proposal_api.resume_approved_receipt(core, self.project, path, receipt_store=self.store)
        self.assertEqual("running", result["status"], result)
        receipt = self.store.load(path)
        self.assertEqual("running", receipt["state"])
        self.assertEqual(2, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))
        self.assertEqual(baseline, git("rev-parse", "HEAD^", cwd=self.project).stdout.strip())

    def test_unsupported_receipt_state_enters_manual_review(self):
        def crash(stage):
            if stage == "after_receipt":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=crash)
        path = self.receipt_path()
        receipt = self.store.load(path)
        receipt["state"] = "awaiting_acceptance"
        self.store.update_atomic(path, receipt)
        result = proposal_api.resume_approved_receipt(core, self.project, path, receipt_store=self.store)
        self.assertEqual("needs_review", result["status"])
        self.assertIn("state is missing or unsupported", result["reason"])

    def test_crash_before_planning_commit_leaves_dirty_receipt_for_manual_review(self):
        def crash(stage):
            if stage == "before_commit":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=crash)
        result = proposal_api.resume_approved_receipt(
            core, self.project, self.receipt_path(), receipt_store=self.store,
        )
        self.assertEqual("needs_review", result["status"])
        self.assertIn("dirty", result["reason"])
        self.assertEqual(1, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))

    def test_dirty_partial_apply_crash_is_needs_review_and_never_replayed(self):
        def partial(stage):
            if stage == "after_apply":
                (self.project / "tabilet/memory-bank/milestone-notes.md").unlink()
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=partial)
        path = self.receipt_path()
        result = proposal_api.resume_approved_receipt(core, self.project, path, receipt_store=self.store)
        self.assertEqual("needs_review", result["status"])
        self.assertFalse((self.project / "tabilet/memory-bank/milestone-notes.md").exists())
        self.assertEqual(1, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))

    def test_crash_after_commit_reconciles_the_exact_commit_without_replaying(self):
        def crash(stage):
            if stage == "after_commit":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=crash)
        path = self.receipt_path()
        head = git("rev-parse", "HEAD", cwd=self.project).stdout.strip()
        result = proposal_api.resume_approved_receipt(core, self.project, path, receipt_store=self.store)
        self.assertEqual("running", result["status"], result)
        receipt = self.store.load(path)
        self.assertEqual(head, receipt["planning_commit"])
        self.assertEqual(2, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))
        self.assertEqual(self.plan["diff"], git("show", "--format=", "--binary", "HEAD", cwd=self.project).stdout)

    def test_ignored_workflow_file_drift_after_commit_needs_review(self):
        ignore = self.project / ".gitignore"
        ignore.write_text("tabilet/memory-bank/status-M02.md\n", encoding="utf-8")
        self.commit("ignore an untracked status file")
        self.plan = self.make_proposal()

        def crash(stage):
            if stage == "after_commit":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=crash)
        ignored = self.project / "tabilet/memory-bank/status-M02.md"
        ignored.write_text("# Status M02\n", encoding="utf-8")
        self.assertEqual("", git("status", "--porcelain", cwd=self.project).stdout)
        result = proposal_api.resume_approved_receipt(
            core, self.project, self.receipt_path(), receipt_store=self.store,
        )
        self.assertEqual("needs_review", result["status"])
        self.assertIn("workflow files or permanent IDs drifted", result["reason"])
        self.assertEqual(3, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))

    def test_hidden_nonworkflow_action_drift_after_commit_needs_review(self):
        self.plan = self.make_proposal(extra_path="project-notes.txt")

        def crash(stage):
            if stage == "after_commit":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=crash)
        git("update-index", "--assume-unchanged", "--", "project-notes.txt", cwd=self.project)
        (self.project / "project-notes.txt").write_text("hidden drift\n", encoding="utf-8")
        self.assertEqual("", git("status", "--porcelain", cwd=self.project).stdout)
        result = proposal_api.resume_approved_receipt(
            core, self.project, self.receipt_path(), receipt_store=self.store,
        )
        self.assertEqual("needs_review", result["status"])
        self.assertIn("approved file-action target drifted", result["reason"])
        self.assertEqual(2, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))

    def test_wildcard_filename_stages_only_the_literal_approved_path(self):
        sibling = self.project / "a-other.txt"
        sibling.write_text("baseline sibling\n", encoding="utf-8")
        self.commit("add a pathspec sibling")
        self.plan = self.make_proposal(extra_path="a*.txt")
        git("update-index", "--assume-unchanged", "--", "a-other.txt", cwd=self.project)
        sibling.write_text("unapproved hidden change\n", encoding="utf-8")

        result = self.approve()

        self.assertEqual("running", result["status"], result)
        committed_paths = git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", cwd=self.project).stdout.splitlines()
        self.assertEqual(["a*.txt", "tabilet/memory-bank/milestone.md"], sorted(committed_paths))
        self.assertEqual("baseline sibling\n", git("show", "HEAD:a-other.txt", cwd=self.project).stdout)

    def test_receipt_that_records_apply_is_never_replayed_from_baseline(self):
        def crash(stage):
            if stage == "after_result_state":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            self.approve(fault_hook=crash)
        path = self.receipt_path()
        receipt = self.store.load(path)
        self.assertRegex(receipt["result_state_sha256"], r"^[0-9a-f]{64}$")
        baseline = receipt["baseline_commit"]
        git("reset", "--hard", baseline, cwd=self.project)
        git("clean", "-fd", cwd=self.project)
        result = proposal_api.resume_approved_receipt(core, self.project, path, receipt_store=self.store)
        self.assertEqual("needs_review", result["status"])
        self.assertIn("automatic replay is unsafe", result["reason"])
        self.assertEqual(1, len(git("rev-list", "--all", cwd=self.project).stdout.splitlines()))

    def test_unborn_repository_can_make_and_recover_its_first_planning_commit(self):
        empty = self.root / "empty-project"
        empty.mkdir()
        git("init", "-q", cwd=empty)
        git("config", "user.name", "Proposal Test", cwd=empty)
        git("config", "user.email", "proposal-test@example.test", cwd=empty)
        scratch = self.root / "empty-patch-source"
        scratch.mkdir()
        git("init", "-q", cwd=scratch)
        git("config", "user.name", "Proposal Test", cwd=scratch)
        git("config", "user.email", "proposal-test@example.test", cwd=scratch)
        git("commit", "--allow-empty", "-qm", "empty tree baseline", cwd=scratch)
        (scratch / "tabilet/memory-bank").mkdir(parents=True)
        (scratch / "tabilet/memory-bank/milestone.md").write_text("# Initial plan\n", encoding="utf-8")
        (scratch / "tabilet/memory-bank/status-M01.md").write_text(
            "# Status M01\n| ID | Status | Task |\n|---|---|---|\n", encoding="utf-8",
        )
        git("add", "-N", "--", "tabilet/memory-bank/milestone.md", "tabilet/memory-bank/status-M01.md", cwd=scratch)
        patch = git("diff", "--binary", "HEAD", "--", cwd=scratch).stdout
        plan = {
            **self.plan,
            "file_actions": [
                {"path": "tabilet/memory-bank/milestone.md", "action": "create"},
                {"path": "tabilet/memory-bank/status-M01.md", "action": "create"},
            ],
            "diff": patch,
        }
        state = self.root / "empty-state" / "tabilet" / "receipts"
        store = proposal_api.ReceiptStore(state)

        def crash(stage):
            if stage == "after_commit":
                raise InjectedCrash(stage)

        with self.assertRaises(InjectedCrash):
            proposal_api.approve_proposal(
                core, empty, plan, receipt_store=store,
                input_fn=lambda _prompt: "confirm", output_fn=lambda _text: None,
                fault_hook=crash,
            )
        receipt_path, = state.glob("*.json")
        result = proposal_api.resume_approved_receipt(core, empty, receipt_path, receipt_store=store)
        self.assertEqual("running", result["status"])
        self.assertEqual(1, len(git("rev-list", "--all", cwd=empty).stdout.splitlines()))
        self.assertEqual(patch, git("show", "--format=", "--binary", "HEAD", cwd=empty).stdout)

    def test_invalid_proposal_diff_path_or_limit_is_rejected(self):
        with self.assertRaises(proposal_api.ProposalError):
            proposal_api.validate_proposal({**self.plan, "file_actions": [{"path": "../escape", "action": "create"}]})
        with self.assertRaises(proposal_api.ProposalError):
            proposal_api.validate_proposal({**self.plan, "limits": {"max_rows": 0}})
        with self.assertRaises(proposal_api.ProposalError):
            proposal_api.validate_proposal({**self.plan, "image_id": "latest"})
        with self.assertRaisesRegex(proposal_api.ProposalError, "minimum 2"):
            proposal_api.validate_proposal({**self.plan, "planned_commits": 1})
        duplicate = json.loads(json.dumps(self.plan))
        duplicate["horizon"][0]["tasks"].append(dict(duplicate["horizon"][0]["tasks"][0]))
        duplicate["planned_commits"] = 3
        with self.assertRaisesRegex(proposal_api.ProposalError, "duplicate task row ID"):
            proposal_api.validate_proposal(duplicate)
        with self.assertRaisesRegex(proposal_api.ProposalError, "create/delete"):
            proposal_api.approve_proposal(
                core, self.project,
                {**self.plan, "file_actions": [
                    {"path": "tabilet/memory-bank/milestone.md", "action": "delete"},
                    {"path": "tabilet/memory-bank/milestone-notes.md", "action": "create"},
                ]},
                receipt_store=self.store, input_fn=lambda _prompt: "stop", output_fn=lambda _text: None,
            )

    def test_receipt_creation_is_exclusive_private_and_atomic_updates_stay_private(self):
        store = proposal_api.ReceiptStore(self.receipt_dir)
        receipt = {"schema": proposal_api.RECEIPT_SCHEMA, "receipt_id": "11111111-1111-4111-8111-111111111111"}
        path = store.create(self.project, receipt)
        self.assertEqual(0o700, path.parent.stat().st_mode & 0o777)
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        with self.assertRaises(FileExistsError):
            store.create(self.project, receipt)
        store.update_atomic(path, {**receipt, "state": "running"})
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertEqual("running", store.load(path)["state"])

    def test_controller_maps_stale_approval_to_exit_18(self):
        def ask(_prompt):
            (self.project / "README.md").write_text("drift\n")
            return "confirm"

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                controller.approve_proposal(
                    core, self.project, self.plan, receipt_store=self.store,
                    input_fn=ask, output_fn=self.outputs.append,
                )
        self.assertEqual(18, stopped.exception.code)
        self.assertFalse(self.receipt_dir.exists())


if __name__ == "__main__":
    unittest.main()

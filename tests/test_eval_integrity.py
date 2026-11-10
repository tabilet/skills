"""Decision integrity, immutable inputs and trusted gate regression coverage."""
import argparse
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import paired
import run_eval
import skill_eval
import catalog_probe
import frontmatter
import trusted_gate


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def trial(self, role, repeat=1, **fields):
        return {"task": "task", "category": "capability", "role": role, "repeat": repeat,
                "passed": True, "clean": None, "turns": 1, "tokens": 5, "tokens_known": True, **fields}

    def test_missing_pair_cannot_reject_or_promote(self):
        args = argparse.Namespace(repeats=2, min_repeats=1, allowed_regressions=0, min_gain_percent=15)
        base = [self.trial("baseline"), self.trial("baseline", 2)]
        cand = [self.trial("candidate")]
        for reason in (None, "ceiling"):
            result = run_eval.decide(base, cand, args, reason)
            self.assertEqual(result["decision"], "inconclusive")
        scored, excluded = paired.pair_scored({"baseline": base, "candidate": cand})
        self.assertEqual((len(scored["baseline"]), len(scored["candidate"]), excluded), (1, 1, 1))

    def test_unknown_spend_stops_before_second_dispatch_and_preserves_trial(self):
        dispatch = mock.Mock(return_value=self.trial("baseline", tokens_known=False, turns=None))
        trials, calls, tokens, aborted = paired.run_campaign(
            [{"name": "task", "category": "capability"}], 2, 20, 100, dispatch, self.root / "progress.json")
        dispatch.assert_called_once()
        self.assertEqual(len(trials), 1)
        self.assertEqual(calls, 0)  # No count was observed; the unknown reservation stops dispatch.
        self.assertIn("unknown consumption", aborted)
        self.assertTrue((self.root / "progress.json").is_file())

    def test_ceiling_never_forces_second_half_of_pair(self):
        dispatch = mock.Mock(return_value=self.trial("baseline"))
        trials, calls, _, aborted = paired.run_campaign(
            [{"name": "task", "category": "capability"}], 1, 1, 100, dispatch, self.root / "progress.json")
        self.assertEqual(calls, 1)
        dispatch.assert_called_once()
        self.assertIn("ceiling", aborted)

    def test_interrupt_and_setup_failure_preserve_prior_paid_evidence(self):
        for error in (KeyboardInterrupt(), OSError("setup")):
            dispatch = mock.Mock(side_effect=[self.trial("baseline"), error])
            trials, calls, _, aborted = paired.run_campaign(
                [{"name": "task", "category": "capability"}], 1, 10, 100, dispatch, self.root / "progress.json")
            self.assertEqual(len(trials), 2)
            self.assertEqual(trials[1]["status"], "infrastructure_error")
            self.assertIsNotNone(aborted)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.root, check=True, capture_output=True, text=True)

    def repo(self):
        repo = self.root / "repo"
        repo.mkdir()
        self.git("init", "-q", cwd=repo)
        self.git("config", "user.name", "Test", cwd=repo)
        self.git("config", "user.email", "test@example.test", cwd=repo)
        (repo / "skills").mkdir()
        (repo / "skills/a").write_bytes(b"original\0binary")
        self.git("add", ".", cwd=repo)
        self.git("commit", "-qm", "base", cwd=repo)
        return repo

    def test_worktree_snapshot_includes_untracked_bytes_modes_and_is_immutable(self):
        repo = self.repo()
        new = repo / "skills/untracked"
        new.write_bytes(b"\x00one")
        new.chmod(0o755)
        tree = paired.snapshot_ref(repo, "WORKTREE", self.root / "tree", ("skills",))
        identity = paired.identity(tree, "WORKTREE", repo)
        self.assertEqual(identity["files"]["skills/untracked"]["mode"], 0o755)
        new.write_bytes(b"two")
        self.assertEqual((tree / "skills/untracked").read_bytes(), b"\x00one")
        self.assertNotEqual(paired.manifest(tree), paired.manifest(repo / "skills"))

    def test_nonempty_report_destination_is_refused(self):
        (self.root / "old-report").write_text("evidence")
        with self.assertRaisesRegex(run_eval.EvalError, "empty"):
            run_eval.check_report_dir(self.root)

    def test_old_ref_setup_cannot_copy_live_protocol(self):
        task = skill_eval.load_tasks(skill_eval.TASKS_DIR, False, ["upgrade-removes-stock-goal-copy"])[0]
        tree = run_eval.materialize_ref("v2.22.2", self.root / "old", ("template", "skills", "GOAL.md"))
        project = skill_eval.prepare_project(tree, task, self.root / "project")
        self.assertEqual((project / "tabilet/GOAL.md").read_bytes(), (tree / "GOAL.md").read_bytes())

    def test_routing_arrays_are_unparsed(self):
        for content in ('{"skill":[]}', '{"skill":{}}', '{"skill":true}', '{"skill":42}'):
            self.assertEqual(catalog_probe.parse_choice(content, {"x"}), (None, False))

    def test_description_readers_handle_continuations_and_bound_length(self):
        text = "---\nname: x\ndescription: First line\n  second line\n---\nBody\n"
        self.assertEqual(frontmatter.description(text), "First line second line")
        self.assertEqual(frontmatter.description(frontmatter.replace_description(text, "New text")), "New text")
        with self.assertRaises(ValueError):
            frontmatter.description("---\ndescription: " + "x" * 251 + "\n---\n")

    def test_trusted_gate_never_executes_candidate_check_and_sees_ignored_source(self):
        root = Path(__file__).resolve().parents[1]
        repo = self.root / "gate"
        self.git("clone", "--quiet", "--shared", str(root), str(repo))
        (repo / "check.py").write_text("raise AssertionError('candidate code executed')\n")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(trusted_gate.run("HEAD", repo, full=False), 1)
        self.git("checkout", "--", "check.py", cwd=repo)
        exclude = repo / ".git/info/exclude"
        exclude.write_text(exclude.read_text() + "\nconcealed.py\n")
        (repo / "concealed.py").write_text("print('hidden source')\n")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(trusted_gate.run("HEAD", repo, full=False), 1)

    def test_cli_help_leaves_no_bytecode(self):
        root = Path(__file__).resolve().parents[1]
        copy = self.root / "cli"
        import shutil
        shutil.copytree(root / "evals", copy)
        environment = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
        for name in ("run_eval.py", "skill_eval.py", "catalog_probe.py", "reflect_eval.py", "propose_candidate.py"):
            proc = subprocess.run([sys.executable, str(copy / name), "--help"], env=environment, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(list(copy.rglob("__pycache__")), [])

    def test_fixture_between_failure_retains_known_provider_usage(self):
        import types
        runner = mock.Mock()
        runner.call_llm.return_value = {"content": '{"final":"proposal"}', "usage": {}}
        runner.normalize_usage.return_value = {"input_total": 3, "output": 4}
        runner.extract_json.return_value = {"final": "proposal"}
        llm = types.SimpleNamespace(max_history_chars=10000, provider="openai", api_base="unused",
                                    api_key="", model="fake", temperature=None, max_tokens=100, api_timeout=1)
        task = {"request": "plan", "replies": ["approved"], "max_turns": 3, "between": ["false"]}
        for error in (subprocess.CalledProcessError(1, "false"), subprocess.TimeoutExpired("false", 1)):
            with mock.patch.object(skill_eval, "snapshot", return_value={}), \
                 mock.patch.object(skill_eval.subprocess, "run", side_effect=error):
                outcome = skill_eval.converse(runner, llm, self.root, "instructions", task, 3)
            self.assertEqual(outcome["status"], "infrastructure_error")
            self.assertEqual((outcome["turns"], outcome["tokens"], outcome["tokens_known"]), (1, 7, True))
            self.assertIn("fixture failure", outcome["note"])

    def test_proposer_interrupt_and_concurrent_edit_never_overwrite_original(self):
        import propose_candidate as proposer
        repo = self.repo()
        path = repo / "skills/a"
        before = path.read_bytes()
        with mock.patch.object(proposer, "run_optimizer_gate", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                proposer.apply_isolated(repo, {"skills/a": b"proposal"}, "HEAD")
        self.assertEqual(path.read_bytes(), before)
        def owner_edit(*args, **kwargs):
            path.write_bytes(b"owner edit")
            return 0
        with mock.patch.object(proposer, "run_optimizer_gate", side_effect=owner_edit):
            with self.assertRaisesRegex(run_eval.EvalError, "checkout changed"):
                proposer.apply_isolated(repo, {"skills/a": b"proposal"}, "HEAD")
        self.assertEqual(path.read_bytes(), b"owner edit")

    def test_frozen_input_drift_invalidates_trial_without_losing_accounting(self):
        inputs = self.root / "inputs"
        inputs.mkdir()
        (inputs / "data").write_text("before")
        def dispatch(*args):
            (inputs / "data").write_text("changed")
            return self.trial("baseline")
        guarded = paired.guard_inputs(dispatch, [inputs])
        result = guarded()
        self.assertEqual(result["status"], "input_changed")
        self.assertEqual(result["tokens"], 5)

    def test_held_out_archive_trap_accepts_waiting_and_rejects_rewriting(self):
        task = skill_eval.load_tasks(skill_eval.TASKS_DIR, True, ["held-out-trap-archive-unapproved-successor"])[0]
        project = skill_eval.prepare_project(skill_eval.ROOT, task, self.root / "project")
        runner = catalog_probe.load_runner()
        before = skill_eval.snapshot(project)
        rows = skill_eval.read_rows(runner, project, before["files"])
        def grade():
            return skill_eval.grade(task, runner, project, before, rows, [before],
                                    skill_eval.snapshot(project), True, None, ["Awaiting approval."])[0]
        self.assertEqual(grade(), [])
        (project / "tabilet/docs/archive-C01.md").write_text("rewritten")
        self.assertIn("unchanged", grade())

    def test_snapshot_identity_keeps_commit_when_source_head_moves(self):
        repo = self.repo()
        sha = self.git("rev-parse", "HEAD", cwd=repo).stdout.strip()
        tree = paired.snapshot_ref(repo, "HEAD", self.root / "tree", ("skills",))
        self.git("commit", "--allow-empty", "-qm", "later", cwd=repo)
        self.assertEqual(paired.identity(tree, "HEAD", repo)["sha"], sha)

    def test_stale_or_legacy_report_cannot_supply_proposal_evidence(self):
        import propose_candidate as proposer
        repo = self.repo()
        with self.assertRaisesRegex(run_eval.EvalError, "exact measured inputs"):
            proposer.verify_report_inputs({}, "candidate", repo)
        tree = paired.snapshot_ref(repo, "WORKTREE", self.root / "tree", ("skills",))
        report = {"refs": {"candidate": paired.identity(tree, "WORKTREE", repo)}}
        proposer.verify_report_inputs(report, "candidate", repo)
        (repo / "skills/a").write_bytes(b"changed")
        with self.assertRaisesRegex(run_eval.EvalError, "stale"):
            proposer.verify_report_inputs(report, "candidate", repo)

    def test_final_snapshot_failure_retains_known_usage(self):
        import types
        task = skill_eval.load_tasks(skill_eval.TASKS_DIR, False, ["upgrade-removes-stock-goal-copy"])[0]
        original_snapshot = skill_eval.snapshot
        snapshots = 0
        def snapshot(project):
            nonlocal snapshots
            snapshots += 1
            if snapshots > 1:
                raise OSError("cannot read final worktree")
            return original_snapshot(project)
        outcome = {"finished": True, "checkpoints": [], "finals": [], "turns": 2,
                   "tokens": 17, "tokens_known": True, "note": ""}
        runner = catalog_probe.load_runner()
        with mock.patch.object(skill_eval, "snapshot", side_effect=snapshot), \
             mock.patch.object(skill_eval, "converse", return_value=outcome):
            result = skill_eval.run_trial(runner, types.SimpleNamespace(tool_env={}), skill_eval.ROOT,
                                         task, "baseline", 1, self.root, 5)
        self.assertEqual(result["status"], "infrastructure_error")
        self.assertEqual((result["turns"], result["tokens"], result["tokens_known"]), (2, 17, True))

    def test_trusted_gate_disables_candidate_fsmonitor(self):
        import shlex
        source = Path(__file__).resolve().parents[1]
        repo = self.root / "candidate"
        self.git("clone", "--quiet", "--shared", str(source), str(repo))
        marker = self.root / "executed"
        hook = repo / ".git/hooks/candidate-monitor"
        hook.write_text("#!/bin/sh\nprintf executed > " + shlex.quote(str(marker)) + "\nprintf 'token\\0'\n")
        hook.chmod(0o755)
        self.git("config", "core.fsmonitor", str(hook), cwd=repo)
        self.assertEqual(trusted_gate.run("HEAD", repo, full=False), 0)
        self.assertFalse(marker.exists())

    def test_atomic_publication_interrupt_preserves_original_and_rolls_back_twins(self):
        import propose_candidate as p
        repo = self.repo()
        original = (repo / "skills/a").read_bytes()
        (repo / "skills/b").write_bytes(original)
        self.git("add", ".", cwd=repo)
        self.git("commit", "-qm", "twin", cwd=repo)
        real = p.os.replace
        calls = 0
        def fail_second(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return real(source, target)
        with mock.patch.object(p, "run_optimizer_gate", return_value=0), mock.patch.object(p.os, "replace", side_effect=fail_second):
            with self.assertRaises(KeyboardInterrupt):
                p.apply_isolated(repo, {"skills/a": b"proposal", "skills/b": b"proposal"}, "HEAD")
        self.assertEqual((repo / "skills/a").read_bytes(), original)
        self.assertEqual((repo / "skills/b").read_bytes(), original)
        self.assertEqual(list(repo.rglob(".tabilet-proposal-*")), [])

    def test_proposer_rejects_committed_concurrent_change(self):
        import propose_candidate as p
        repo = self.repo()
        before = (repo / "skills/a").read_bytes()
        head = self.git("rev-parse", "HEAD", cwd=repo).stdout.strip()
        def advance(*args, **kwargs):
            self.git("commit", "--allow-empty", "-qm", "concurrent change", cwd=repo)
            return 0
        with mock.patch.object(p, "run_optimizer_gate", side_effect=advance):
            with self.assertRaisesRegex(run_eval.EvalError, "checkout changed"):
                p.apply_isolated(repo, {"skills/a": b"proposal"}, "HEAD")
        self.assertEqual((repo / "skills/a").read_bytes(), before)
        with self.assertRaisesRegex(run_eval.EvalError, "generation"):
            p.apply_isolated(repo, {"skills/a": b"proposal"}, "HEAD", expected_head=head)

    def test_zero_cost_skip_continues_and_drops_the_pair(self):
        tasks = [{"name": n, "category": "capability"} for n in ("skip", "work")]
        def dispatch(task, role, repeat, budget):
            return {**self.trial(role), "task": task["name"], "calls_used": 0 if task["name"] == "skip" else 1,
                    "tokens": 0 if task["name"] == "skip" else 5,
                    "status": "skipped" if task["name"] == "skip" else "ok"}
        dispatch = mock.Mock(side_effect=dispatch)
        raw, calls, tokens, aborted = paired.run_campaign(tasks, 1, 5, 100, dispatch, self.root / "progress.json")
        self.assertEqual(dispatch.call_count, 3)
        self.assertEqual((calls, tokens, aborted), (2, 10, None))
        scored, excluded = paired.pair_scored({r: [t for t in raw if t["role"] == r] for r in paired.ROLES})
        self.assertEqual(excluded, 1)
        self.assertEqual([t["task"] for t in scored["candidate"]], ["work"])

    def test_nonzero_or_unknown_skip_cannot_continue(self):
        for fields in ({"calls_used": 1, "tokens": 5}, {"calls_used": 0, "tokens": 0, "tokens_known": False}):
            dispatch = mock.Mock(return_value=self.trial("baseline", status="skipped", **fields))
            _, _, _, aborted = paired.run_campaign([{"name": "task", "category": "capability"}], 1, 10, 100, dispatch, self.root / "p.json")
            self.assertIsNotNone(aborted)
            dispatch.assert_called_once()

    def test_resume_retries_known_infrastructure_cost_and_retains_spend(self):
        tasks = [{"name": "task", "category": "capability"}]
        path = self.root / "p.json"
        failed = self.trial("baseline", status="infrastructure_error", calls_used=1)
        paired.run_campaign(tasks, 1, 4, 100, mock.Mock(return_value=failed), path, campaign_identity="same")
        def dispatch(task, role, repeat, budget):
            return self.trial(role, calls_used=1)
        raw, calls, tokens, aborted = paired.run_campaign(tasks, 1, 4, 100, dispatch, path, resume=True, campaign_identity="same")
        self.assertEqual((calls, tokens, aborted), (3, 15, None))
        self.assertTrue(raw[0]["superseded"])
        scored, excluded = paired.pair_scored({r: [t for t in raw if t["role"] == r] for r in paired.ROLES})
        self.assertEqual(excluded, 0)
        self.assertEqual(len(scored["baseline"]), 1)
        no_dispatch = mock.Mock(side_effect=AssertionError("completed trial repeated"))
        self.assertEqual(paired.run_campaign(tasks, 1, 4, 100, no_dispatch, path, resume=True, campaign_identity="same")[1], 3)

    def test_resume_rejects_identity_limits_and_unknown_without_rewriting(self):
        import json
        tasks = [{"name": "task", "category": "capability"}]
        path = self.root / "p.json"
        paired.run_campaign(tasks, 1, 4, 100, mock.Mock(return_value=self.trial("baseline", tokens_known=False)), path, campaign_identity="same")
        before = path.read_bytes()
        for identity, calls in (("changed", 4), ("same", 5), ("same", 4)):
            with self.assertRaises(ValueError):
                paired.run_campaign(tasks, 1, calls, 100, mock.Mock(), path, resume=True, campaign_identity=identity)
            self.assertEqual(path.read_bytes(), before)
        checkpoint = json.loads(path.read_text())
        checkpoint["trials"] = []
        checkpoint["active_trial"] = {"usage": "unknown"}
        path.write_text(json.dumps(checkpoint))
        with self.assertRaisesRegex(ValueError, "unknown"):
            paired.run_campaign(tasks, 1, 4, 100, mock.Mock(), path, resume=True, campaign_identity="same")

    def test_resume_keeps_original_ceiling(self):
        tasks = [{"name": "task", "category": "capability"}]
        path = self.root / "p.json"
        paired.run_campaign(tasks, 1, 1, 100, lambda t, r, n, b: self.trial(r), path, campaign_identity="same")
        dispatch = mock.Mock()
        _, calls, _, aborted = paired.run_campaign(tasks, 1, 1, 100, dispatch, path, resume=True, campaign_identity="same")
        dispatch.assert_not_called()
        self.assertEqual(calls, 1)
        self.assertIn("ceiling", aborted)

    def test_checkpoint_allows_only_one_writer(self):
        tasks = [{"name": "task", "category": "capability"}]
        path = self.root / "p.json"
        def dispatch(task, role, repeat, budget):
            with self.assertRaisesRegex(ValueError, "active writer"):
                paired.run_campaign(tasks, 1, 10, 100, mock.Mock(), path, resume=True, campaign_identity="same")
            return self.trial(role)
        paired.run_campaign(tasks, 1, 10, 100, dispatch, path, campaign_identity="same")

    def test_skipped_trap_is_not_an_observed_safety_failure(self):
        args = argparse.Namespace(repeats=1, min_repeats=1, allowed_regressions=0, min_gain_percent=15)
        trial = self.trial("candidate", category="trap", status="skipped", passed=False, calls_used=0, tokens=0)
        result = run_eval.decide([], [trial], args, None)
        self.assertEqual(result["decision"], "inconclusive")
        self.assertEqual(result["observed_trap_failures"], [])

    def test_gate_allows_local_artifacts_but_rejects_new_source(self):
        source = Path(__file__).resolve().parents[1]
        repo = self.root / "candidate"
        self.git("clone", "--quiet", "--shared", str(source), str(repo))
        for name in (".idea/workspace.xml", ".claude/settings.local.json", ".pytest_cache/state", "tests/browser/test-results/result", "medium-legacy.md"):
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("local artifact")
        self.assertEqual(trusted_gate.run("HEAD", repo, full=False), 0)
        (repo / "concealed.py").write_text("print('new code')")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(trusted_gate.run("HEAD", repo, full=False), 1)

    def test_gate_uses_trusted_refs_and_supports_base_without_old_gate(self):
        source = Path(__file__).resolve().parents[1]
        trusted = self.root / "trusted"
        candidate = self.root / "candidate"
        self.git("clone", "--quiet", "--shared", str(source), str(trusted))
        self.git("branch", "trusted-base", "HEAD", cwd=trusted)
        self.git("branch", "main", "origin/main", cwd=trusted)
        self.git("clone", "--quiet", "--shared", str(trusted), str(candidate))
        self.git("config", "user.name", "test", cwd=candidate)
        self.git("config", "user.email", "test@example.test", cwd=candidate)
        (candidate / "harness/tabilet_reflect.py").write_text("# forbidden committed change")
        self.git("add", ".", cwd=candidate)
        self.git("commit", "-qm", "frozen change", cwd=candidate)
        self.git("branch", "trusted-base", "HEAD", cwd=candidate)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(trusted_gate.run("trusted-base", candidate, full=False, trusted_root=trusted), 1)
        self.git("checkout", "--quiet", "--detach", "origin/main", cwd=trusted)
        self.git("checkout", "--quiet", "--detach", "origin/main", cwd=candidate)
        self.assertEqual(trusted_gate.run("origin/main", candidate, full=False, trusted_root=trusted), 0)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(trusted_gate.run("missing-base", candidate, full=False, trusted_root=trusted), 1)

    def test_gate_never_invokes_candidate_clean_filter(self):
        import shlex
        source = Path(__file__).resolve().parents[1]
        repo = self.root / "candidate"
        self.git("clone", "--quiet", "--shared", str(source), str(repo))
        marker = self.root / "executed"
        script = repo / ".git/hooks/clean"
        script.write_text("#!/bin/sh\nprintf executed > " + shlex.quote(str(marker)) + "\ncat\n")
        script.chmod(0o755)
        (repo / ".git/info/attributes").write_text("README.md filter=review\n")
        self.git("config", "filter.review.clean", str(script), cwd=repo)
        self.assertEqual(trusted_gate.run("HEAD", repo, full=False), 0)
        self.assertFalse(marker.exists())

    def test_manifest_normalizes_umask_but_preserves_executable_changes(self):
        repo = self.repo()
        path = repo / "skills/a"
        path.chmod(0o644)
        a = paired.snapshot_ref(repo, "HEAD", self.root / "a", ("skills",))
        b = paired.snapshot_ref(repo, "WORKTREE", self.root / "b", ("skills",))
        self.assertEqual(paired.manifest(a), paired.manifest(b))
        path.chmod(0o664)
        c = paired.snapshot_ref(repo, "WORKTREE", self.root / "c", ("skills",))
        self.assertEqual(paired.manifest(b), paired.manifest(c))
        path.chmod(0o755)
        d = paired.snapshot_ref(repo, "WORKTREE", self.root / "d", ("skills",))
        self.assertNotEqual(paired.manifest(c), paired.manifest(d))

    def test_git_safety_environment_keeps_normal_diff_working(self):
        repo = self.repo()
        (repo / "skills/a").write_bytes(b"changed")
        with trusted_gate.safe_git_environment():
            result = self.git("diff", cwd=repo)
        self.assertIn("diff --git", result.stdout)

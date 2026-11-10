"""Typed observation and conservative reflection regressions, without provider calls."""
import contextlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import test_harness as h
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import tabilet_audit as audit
import tabilet_reflect as reflect


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = h.make_repo(Path(self.tmp.name) / "project")
        self.db = self.repo / "tabilet/audit.sqlite3"
        self.conn = audit.open_database(self.db, project_roots=[self.repo])
        self.addCleanup(self.conn.close)
        workspace = audit.ensure_workspace(self.conn, self.repo)
        audit.start_run(self.conn, workspace, "goal", run_id="goal", started_at="2025-01-01T00:00:00Z")
        self.common = {"schema": audit.OBSERVATION_SCHEMA, "run_id": "goal", "milestone_id": "M01",
                       "capture_source": "agent", "fidelity": "summarized"}

    def observe(self, kind, event, **fields):
        return audit.record_observation(self.conn, kind, {**self.common, "event_id": event, **fields})

    def start(self, attempt="a", **fields):
        return self.observe("task-start", attempt + ":start", attempt_id=attempt, task_label="Implement",
                            status_path="tabilet/memory-bank/status-M01.md", **fields)

    def finish(self, attempt="a", **fields):
        return self.observe("task-finish", attempt + ":finish", attempt_id=attempt, task_label="Implement",
                            status_path="tabilet/memory-bank/status-M01.md", old_state="in_progress",
                            new_state="completed", result="completed", **fields)

    def test_live_boundaries_retry_without_new_timestamp_and_conflicts_fail(self):
        a = self.start(live=True)
        self.assertEqual(a, self.start(live=True))
        with self.assertRaises(audit.AuditConflict):
            self.start(occurred_at="2026-11-10T00:00:00Z")
        self.finish(live=True)
        self.finish(live=True)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM events").fetchone()[0], 3)

    def test_finish_requires_start_identity_and_time_order(self):
        with self.assertRaises(audit.AuditValidationError):
            self.finish()
        self.start(occurred_at="2026-11-10T00:01:00Z")
        with self.assertRaises(audit.AuditValidationError):
            self.finish(occurred_at="2026-11-10T00:00:00Z")
        with self.assertRaises(audit.AuditConflict):
            self.observe("task-finish", "wrong", attempt_id="a", task_label="Other", status_path="x",
                         old_state="in_progress", new_state="completed", result="completed")

    def test_missing_time_is_unknown_and_old_open_goal_adds_no_duration(self):
        self.start()
        self.finish()
        t = reflect.extract_telemetry(self.repo, "M01")
        self.assertEqual(t["milestone_wall_sec"], 0)
        self.assertEqual(t["downstream"]["gate"], "closed")
        self.assertIsNone(t["task_attempts"][0]["duration_sec"])
        self.assertIn("outcome unknown", t["independent_evidence"]["open_runs"])
        self.assertIsNone(self.conn.execute("SELECT result FROM runs").fetchone()[0])

    def test_intervals_are_scoped_and_overlaps_are_not_double_counted(self):
        self.start(occurred_at="2026-11-10T00:00:00Z")
        self.finish(occurred_at="2026-11-10T00:02:00Z")
        self.observe("verification", "v", command="python3 -m unittest", result="passed",
                     started_at="2026-11-10T00:01:00Z", finished_at="2026-11-10T00:02:00Z",
                     duration_sec=60, timing_basis="monotonic")
        self.observe("verification", "other", milestone_id="M02", command="other", result="passed",
                     started_at="2026-11-10T01:00:00Z", finished_at="2026-11-10T02:00:00Z",
                     duration_sec=3600, timing_basis="reported")
        self.assertEqual(reflect.extract_telemetry(self.repo, "M01")["milestone_wall_sec"], 120)
        self.assertEqual(reflect.extract_telemetry(self.repo, "M02")["milestone_wall_sec"], 3600)

    def test_duration_validation_and_nonexecuting_verification(self):
        for value in (-1, True, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(audit.AuditValidationError):
                self.observe("verification", "bad", command="touch forbidden", result="passed",
                             duration_sec=value, timing_basis="reported")
        self.observe("verification", "v", command="touch forbidden", result="unknown")
        self.assertFalse((self.repo / "forbidden").exists())

    def test_observation_ids_match_root_and_child_lanes(self):
        for ident in ("M00", "M001", "M01-00", "M01-100"):
            with self.subTest(ident=ident), self.assertRaises(audit.AuditValidationError):
                self.observe("verification", ident, milestone_id=ident, command="check", result="unknown")
        for ident in ("M01", "M100", "M01-01", "M100-99"):
            self.observe("verification", ident, milestone_id=ident, command="check", result="unknown")

    def test_review_observation_does_not_change_markdown(self):
        before = (self.repo / "tabilet/memory-bank/status-M01.md").read_bytes()
        self.observe("review", "r2", round=2, result="passed", findings={"P1": 0, "P2": 0})
        t = reflect.extract_telemetry(self.repo, "M01")
        self.assertEqual(t["independent_evidence"]["review_rounds"]["iterations"], 2)
        self.assertEqual(t["downstream"]["gate"], "closed")
        self.assertEqual((self.repo / "tabilet/memory-bank/status-M01.md").read_bytes(), before)

    def test_terminal_reason_idempotence_and_missing_legacy_reason(self):
        audit.finish_run(self.conn, "goal", "blocked", reason="owner input")
        audit.finish_run(self.conn, "goal", "blocked", reason="owner input")
        with self.assertRaises(audit.AuditConflict):
            audit.finish_run(self.conn, "goal", "blocked", reason="other")
        with self.assertRaises(audit.AuditValidationError):
            self.start()

    def test_review_uses_observed_duration_for_significance(self):
        self.observe("review", "r1", round=1, result="passed", findings={},
                     duration_sec=180, timing_basis="monotonic",
                     started_at="2026-11-10T00:00:00Z", finished_at="2026-11-10T00:03:00Z")
        telemetry = reflect.extract_telemetry(self.repo, "M01")
        self.assertEqual(telemetry["downstream"]["gate"], "open")
        self.assertEqual(telemetry["milestone_wall_sec"], 180)
        self.assertEqual(telemetry["friction_runs"][0]["scope"], "review")

    def test_no_time_window_git_inference_and_sha_is_checked(self):
        self.start()
        t = reflect.extract_telemetry(self.repo, "M01")
        self.assertEqual(t["independent_evidence"]["git_commits"]["count"], 0)
        sha = h.run("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        result = reflect.observed_commits(self.repo, [sha, sha])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["commits"][0]["sha"], sha)

    def test_checkpoint_forms_and_conflicting_counters(self):
        for text in ("Persisted review count: **2/10**", "persisted iteration count: 2.", "**Review iterations.** 2"):
            self.assertEqual(reflect._active_counts(text), [2])
        self.assertEqual(reflect._active_counts("Example: Iteration 9 of 10"), [])
        self.assertEqual(reflect._active_counts("\x60\x60\x60\nPersisted review count: 9/10\n\x60\x60\x60"), [])

    def test_proxy_cli_runs_without_dns_veto(self):
        with mock.patch.dict("os.environ", {"HTTPS_PROXY": "http://proxy.invalid"}, clear=True), \
             mock.patch.object(reflect.shutil, "which", return_value="/fake/cli"), \
             mock.patch.object(reflect, "_host_resolves", return_value=False), \
             mock.patch.object(reflect, "_run_cli", return_value=(0, "proposal")) as call:
            result = reflect.invoke_improver_llm(reflect.extract_telemetry(self.repo), self.repo, backend="codex")
        self.assertEqual(result.source, "cli:codex")
        call.assert_called_once()

    def test_explicit_endpoint_without_key_is_configuration_error(self):
        with mock.patch.dict("os.environ", {"TABILET_REFLECT_API_BASE": "http://localhost"}, clear=True):
            with self.assertRaisesRegex(audit.AuditError, "credential"):
                reflect.invoke_improver_llm(reflect.extract_telemetry(self.repo), self.repo, backend="codex")

    def test_smoke_counts_cannot_recommend_replacement_and_tap_is_not_go(self):
        note = "\n".join(reflect._compare_to_baseline([
            {"command": "unrelated", "status": "PASSED", "duration_sec": .999,
             "coverage": {"tests_run": 50, "has_coverage": True}}]))
        self.assertIn("do not establish", note)
        self.assertNotIn("Recommended Test Profile", note)
        self.assertIsNone(reflect.extract_coverage_evidence("ok 1 - name", runner="npm")["tests_run"])
        self.assertIsNone(reflect.extract_coverage_evidence("FAIL pkg\n? empty [no test files]", runner="go")["tests_run"])

    def test_generic_events_cannot_bypass_typed_observation_validation(self):
        self.start()
        payload = json.loads(self.conn.execute(
            "SELECT payload_json FROM events WHERE event_id='a:start'").fetchone()[0])
        payload["event_id"] = "unvalidated"
        payload["details"]["observation"]["attempt_id"] = "different"
        with self.assertRaisesRegex(audit.AuditValidationError, "typed observations"):
            audit.append_event(self.conn, payload)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM events").fetchone()[0], 1)


    def test_legacy_trajectory_uses_latest_transition(self):
        workspace = self.conn.execute("SELECT workspace_id FROM runs WHERE run_id='goal'").fetchone()[0]
        for index, (old, new) in enumerate((("pending", "in_progress"), ("in_progress", "completed"))):
            audit.append_event(self.conn, {"schema": "tabilet.audit.event/v1", "event_id": str(index),
                "run_id": "goal", "workspace_id": workspace, "operation": "goal",
                "event_type": "task_transition", "recorded_at": audit.utc_now(),
                "subject": {"milestone_id": "M01", "task_label": "Implement", "old_state": old, "new_state": new},
                "details": {"schema": "tabilet.audit.details/v1"}})
        audit.finish_run(self.conn, "goal", "completed")
        tasks = reflect.export_trajectories(self.repo, "M01")["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["status"], "completed")
        self.assertIsNone(tasks[0]["duration_sec"])

    def test_interval_only_check_is_significant(self):
        for kind, extra in (("verification", {"command": "test suite"}), ("review", {"round": 1, "findings": {}})):
            self.observe(kind, kind, result="passed", timing_basis="recorded_boundary",
                         started_at="2026-11-10T00:00:00Z", finished_at="2026-11-10T00:05:00Z", **extra)
        telemetry = reflect.extract_telemetry(self.repo, "M01")
        self.assertEqual(telemetry["milestone_wall_sec"], 300)
        self.assertEqual(telemetry["downstream"]["gate"], "open")
        self.assertEqual(len(telemetry["friction_runs"]), 2)

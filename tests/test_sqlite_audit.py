from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import stat
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
loader = importlib.machinery.SourceFileLoader(
    "tabilet_audit_under_test", str(ROOT / "harness" / "tabilet_audit.py")
)
spec = importlib.util.spec_from_loader("tabilet_audit_under_test", loader)
audit = importlib.util.module_from_spec(spec)
loader.exec_module(audit)


def event(**overrides: object) -> dict:
    value = {
        "schema": "tabilet.audit.event/v1",
        "event_id": "event-1",
        "run_id": "run-1",
        "workspace_id": "workspace-1",
        "operation": "next",
        "event_type": "task_transition",
        "recorded_at": "2026-09-21T12:00:00Z",
        "occurred_at": None,
        "subject": {
            "milestone_id": "M01",
            "task_label": "Implement recorder",
            "status_path": "tabilet/memory-bank/status-M01.md",
            "old_state": "in_progress",
            "new_state": "completed",
        },
        "details": {"schema": "tabilet.audit.details/v1"},
    }
    value.update(overrides)
    return value


class SqliteAuditContractTests(unittest.TestCase):
    def test_schema_creates_frozen_v1_tables_and_indexes(self) -> None:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.executescript(audit.SCHEMA_SQL)
        self.assertEqual(
            audit.schema_tables(connection),
            {"schema_meta", "workspaces", "runs", "events", "captured_messages", "snapshots", "run_snapshots"},
        )
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
            )
        }
        self.assertIn("events_run_sequence", indexes)
        self.assertIn("events_milestone", indexes)
        self.assertIn("runs_workspace_started", indexes)
        self.assertIn("snapshots_source", indexes)

    def test_valid_event_is_normalized_without_reassigning_subject_details(self) -> None:
        original = event()
        normalized = audit.validate_event(original)
        self.assertEqual(normalized["subject"]["task_label"], "Implement recorder")
        self.assertEqual(normalized["subject"]["status_path"], "tabilet/memory-bank/status-M01.md")
        self.assertEqual(normalized["details"], {"schema": "tabilet.audit.details/v1"})
        self.assertEqual(json.loads(audit.canonical_json(normalized))["event_id"], "event-1")

    def test_invalid_event_contracts_are_rejected(self) -> None:
        cases = [
            ("schema", "wrong"),
            ("operation", "unknown"),
            ("event_type", "unknown"),
            ("recorded_at", "2026-09-21 12:00:00"),
            ("details", []),
            ("details", {"changed": True}),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(audit.AuditValidationError):
                    audit.validate_event(event(**{field: value}))

    def test_state_and_subject_shape_are_validated(self) -> None:
        with self.assertRaisesRegex(audit.AuditValidationError, "unknown subject state"):
            audit.validate_event(
                event(subject={"old_state": "done", "new_state": "completed"})
            )
        with self.assertRaisesRegex(audit.AuditValidationError, "subject must"):
            audit.validate_event(event(subject="task"))

    def test_open_database_creates_secure_v1_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "state" / "tabilet" / "audit.sqlite3"
            connection = audit.open_database(database)
            self.addCleanup(connection.close)
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(
                connection.execute("SELECT value FROM schema_meta WHERE key = 'schema'").fetchone()[0],
                audit.SCHEMA_NAME,
            )
            connection.close()
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(database.parent.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE(database.stat().st_mode), 0o600)
            reopened = audit.open_database(database)
            reopened.close()

    def test_open_database_rejects_symlinks_and_newer_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.sqlite3"
            target.write_bytes(b"not a database")
            link = root / "link.sqlite3"
            link.symlink_to(target)
            with self.assertRaisesRegex(audit.AuditError, "symlink"):
                audit.open_database(link)

            newer = root / "newer.sqlite3"
            connection = sqlite3.connect(newer)
            self.addCleanup(connection.close)
            connection.execute("PRAGMA user_version = 99")
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(audit.AuditError, "unsupported"):
                audit.open_database(newer)

    def test_workspaces_keep_separate_checkout_and_unversioned_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            connection = audit.open_database(Path(temporary) / "audit.sqlite3")
            self.addCleanup(connection.close)
            first = audit.ensure_workspace(connection, Path(temporary) / "one")
            second = audit.ensure_workspace(connection, Path(temporary) / "two")
            self.assertNotEqual(first, second)
            run_id = audit.start_run(
                connection,
                second,
                "goal",
                worktree_state="unversioned",
                git_head=None,
            )
            row = connection.execute(
                "SELECT git_head, worktree_state, result FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            self.assertEqual(row, (None, "unversioned", None))
            audit.finish_run(connection, run_id, "interrupted", completed_at="2026-09-21T12:00:00Z")
            self.assertEqual(
                connection.execute("SELECT result FROM runs WHERE run_id = ?", (run_id,)).fetchone()[0],
                "interrupted",
            )

    def test_database_path_must_be_regular_and_owner_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "audit.sqlite3"
            directory.mkdir()
            with self.assertRaises(audit.AuditError):
                audit.open_database(directory)

    def test_host_adapter_accepts_structured_host_event(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "audit.sqlite3"
            connection = audit.open_database(database)
            self.addCleanup(connection.close)
            workspace_id = audit.ensure_workspace(connection, Path(temporary) / "project")
            run_id = audit.start_run(connection, workspace_id, "archive", run_id="run-1")
            connection.close()
            payload = json.dumps({
                "schema": "tabilet.audit.event/v1",
                "run_id": run_id,
                "workspace_id": workspace_id,
                "operation": "archive",
                "event_type": "verification_observed",
                "subject": {},
                "details": {"schema": "tabilet.audit.details/v1", "capture_source": "host", "fidelity": "summarized"},
            })
            process = subprocess.run(
                [sys.executable, str(ROOT / "harness/tabilet_audit_host.py"), "--audit-db", str(database), "--event", payload],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)

    def test_workspace_run_event_message_and_finish_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            connection = audit.open_database(Path(temporary) / "audit.sqlite3")
            self.addCleanup(connection.close)
            workspace_id = audit.ensure_workspace(
                connection, Path(temporary) / "project", repository_id="repo", branch="sqlite"
            )
            self.assertEqual(
                audit.ensure_workspace(connection, Path(temporary) / "project"), workspace_id
            )
            run_id = audit.start_run(
                connection, workspace_id, "next", capture_mode="relevant", git_head="abc123", worktree_state="clean"
            )
            self.assertEqual(
                audit.append_event(connection, event(run_id=run_id, workspace_id=workspace_id)), 1
            )
            message_id = audit.capture_message(
                connection,
                run_id,
                "assistant",
                "Completed the recorder task.",
                capture_source="agent",
                fidelity="summarized",
            )
            self.assertTrue(message_id)
            audit.finish_run(connection, run_id, "completed")
            row = connection.execute(
                "SELECT operation, git_head, worktree_state, result FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            self.assertEqual(row, ("next", "abc123", "clean", "completed"))
            self.assertEqual(
                connection.execute("SELECT task_label FROM events WHERE run_id = ?", (run_id,)).fetchone()[0],
                "Implement recorder",
            )
            self.assertEqual(
                connection.execute("SELECT text FROM captured_messages WHERE message_id = ?", (message_id,)).fetchone()[0],
                "Completed the recorder task.",
            )

    def test_foreign_keys_reject_unknown_run_and_workspace(self) -> None:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(audit.SCHEMA_SQL)
        with self.assertRaises(audit.AuditValidationError):
            audit.start_run(connection, "missing", "next")
        with self.assertRaises(audit.AuditValidationError):
            audit.append_event(connection, event())

    def test_event_message_and_run_delivery_are_idempotent_but_conflicts_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            connection = audit.open_database(Path(temporary) / "audit.sqlite3")
            self.addCleanup(connection.close)
            workspace_id = audit.ensure_workspace(connection, Path(temporary) / "project")
            run_id = audit.start_run(connection, workspace_id, "next", run_id="run-1", capture_mode="relevant")
            original = event(run_id=run_id, workspace_id=workspace_id, event_id="event-1")
            self.assertEqual(audit.append_event(connection, original), 1)
            self.assertEqual(audit.append_event(connection, original, sequence=99), 1)
            with self.assertRaises(audit.AuditConflict):
                audit.append_event(connection, {**original, "details": {"schema": "tabilet.audit.details/v1", "changed": True}})

            captured_at = "2026-09-21T12:00:00Z"
            message = dict(
                run_id=run_id,
                role="user",
                text="Run the next task.",
                capture_source="host",
                fidelity="exact",
                message_id="message-1",
                captured_at=captured_at,
            )
            self.assertEqual(audit.capture_message(connection, **message), "message-1")
            self.assertEqual(audit.capture_message(connection, **message, sequence=1), "message-1")
            with self.assertRaises(audit.AuditConflict):
                audit.capture_message(connection, **{**message, "text": "Changed."})

            audit.finish_run(connection, run_id, "completed", completed_at=captured_at)
            audit.finish_run(connection, run_id, "completed", completed_at=captured_at)
            with self.assertRaises(audit.AuditConflict):
                audit.finish_run(connection, run_id, "failed", completed_at=captured_at)

    def test_event_keeps_observed_task_details_independent_of_later_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            connection = audit.open_database(Path(temporary) / "audit.sqlite3")
            self.addCleanup(connection.close)
            workspace_id = audit.ensure_workspace(connection, Path(temporary) / "project")
            run_id = audit.start_run(connection, workspace_id, "next", run_id="run-1", capture_mode="relevant")
            observed = event(run_id=run_id, workspace_id=workspace_id, event_id="event-1")
            audit.append_event(connection, observed)
            connection.execute("CREATE TABLE unrelated_rows(name TEXT)")
            connection.execute("INSERT INTO unrelated_rows VALUES ('renamed later')")
            connection.commit()
            stored = connection.execute(
                "SELECT milestone_id, task_label, status_path, old_state, new_state FROM events WHERE event_id = 'event-1'"
            ).fetchone()
            self.assertEqual(
                stored,
                ("M01", "Implement recorder", "tabilet/memory-bank/status-M01.md", "in_progress", "completed"),
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import stat
import sqlite3
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
        connection.executescript(audit.SCHEMA_SQL)
        self.assertEqual(
            audit.schema_tables(connection),
            {"schema_meta", "workspaces", "runs", "events", "captured_messages"},
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
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
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
            connection.execute("PRAGMA user_version = 99")
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(audit.AuditError, "newer"):
                audit.open_database(newer)


if __name__ == "__main__":
    unittest.main()

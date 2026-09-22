from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import sqlite3
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("sqlite13_audit", ROOT / "harness" / "tabilet_audit.py")
audit = importlib.util.module_from_spec(loader)
loader.loader.exec_module(audit)


class Sqlite13Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.connection = audit.open_database(pathlib.Path(self.tmp.name) / "audit.sqlite3")
        self.addCleanup(self.connection.close)
        self.workspace = audit.ensure_workspace(self.connection, pathlib.Path(self.tmp.name) / "project")
        self.run = audit.start_run(self.connection, self.workspace, "next", capture_mode="relevant")

    def test_fingerprint_is_canonical_and_retries_are_idempotent(self):
        resources = [
            {"name": "b", "sha256": hashlib.sha256(b"b").hexdigest()},
            {"name": "a", "sha256": hashlib.sha256(b"a").hexdigest()},
        ]
        ordered = sorted(resources, key=lambda item: item["name"].encode("utf-8"))
        provenance = {
            "invocation_kind": "interactive_skill",
            "instruction_set_name": "memory-bank-next",
            "capture_method": "instruction_driven",
            "fingerprint_fidelity": "exact",
            "resources": resources,
            "aggregate_sha256": hashlib.sha256(audit.canonical_json(ordered).encode()).hexdigest(),
        }
        first = audit.record_provenance(self.connection, self.run, provenance)
        second = audit.record_provenance(self.connection, self.run, {**provenance, "resources": list(reversed(resources))})
        self.assertEqual(first["run_id"], second["run_id"])
        with self.assertRaises(audit.AuditValidationError):
            audit.validate_provenance({**provenance, "resources": [{"name": "/absolute/SKILL.md", "sha256": resources[0]["sha256"]}]})
        for session_ref in ("../private/session", "C:private", "C:\\private\\session", "\\\\host\\share\\session"):
            with self.subTest(session_ref=session_ref), self.assertRaises(audit.AuditValidationError):
                audit.validate_provenance({**provenance, "host_session_ref": session_ref})
        with self.assertRaises(audit.AuditConflict):
            audit.record_provenance(self.connection, self.run, {**provenance, "model": "conflict"})

    def test_coverage_retry_and_purge_keep_envelope_and_exclude_text(self):
        audit.record_provenance(self.connection, self.run, {
            "invocation_kind": "interactive_skill", "instruction_set_name": "memory-bank-next",
            "capture_method": "instruction_driven", "fingerprint_fidelity": "unavailable",
        })
        with self.assertRaisesRegex(audit.AuditValidationError, "fidelity counts"):
            audit.record_coverage(self.connection, {
                "coverage_id": "unsupported-complete", "run_id": self.run,
                "scope": "skill_conversation", "coverage": "complete", "content_state": "available",
                "exact_count": 1, "capture_method": "instruction_driven",
            })
        audit.capture_message(self.connection, self.run, "user", "private text", capture_source="host", fidelity="exact", message_id="message-1")
        coverage = {"coverage_id": "coverage-1", "run_id": self.run, "scope": "skill_conversation",
                    "coverage": "complete", "content_state": "available", "exact_count": 1,
                    "capture_method": "instruction_driven"}
        self.assertEqual(audit.record_coverage(self.connection, coverage), audit.record_coverage(self.connection, coverage))
        imported = audit.record_coverage(self.connection, {
            **coverage, "coverage_id": "coverage-imported", "capture_method": "imported",
        })
        self.assertEqual(imported["capture_method"], "imported")
        self.assertEqual(
            self.connection.execute("SELECT text FROM captured_messages WHERE message_id='message-1'").fetchone()[0],
            "",
        )
        tombstone = audit.purge_message(self.connection, "message-1", "privacy request", "message-1")
        self.assertEqual(tombstone["message_id"], "message-1")
        self.assertNotIn("private text", audit.export_json(self.connection, include_content=True))
        message = audit.query_messages(self.connection, self.run, include_content=True)[0]
        self.assertEqual(message["content_state"], "purged")
        self.assertIsNone(message["text"])
        with self.assertRaisesRegex(audit.AuditValidationError, "content state"):
            audit.record_coverage(self.connection, {**coverage, "coverage_id": "post-purge-available"})
        with self.assertRaises(sqlite3.DatabaseError):
            self.connection.execute("DELETE FROM events")

    def test_v3_message_bytes_migrate_to_v4_content(self):
        legacy_path = pathlib.Path(self.tmp.name) / "legacy.sqlite3"
        legacy = sqlite3.connect(legacy_path)
        legacy.executescript(audit.SCHEMA_SQL + audit.INDEX_SQL + audit.EXPLORER_SQL)
        legacy.execute("INSERT INTO schema_meta VALUES ('schema','tabilet.audit/v3')")
        legacy.execute("INSERT INTO schema_meta VALUES ('recorder_version','tabilet-audit/3')")
        legacy.execute("PRAGMA user_version=3")
        legacy.execute("INSERT INTO workspaces VALUES ('w','/tmp/legacy-project',NULL,NULL,?,?)", ("2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        legacy.execute("INSERT INTO runs(run_id,workspace_id,operation,started_at,recorder_version,capture_mode,worktree_state) VALUES ('r','w','next',?,'tabilet-audit/3','relevant','clean')", ("2026-01-01T00:00:00Z",))
        legacy.execute("INSERT INTO captured_messages VALUES ('m','r',1,'user',?,'legacy bytes','host','exact',NULL)", ("2026-01-01T00:00:00Z",))
        legacy.commit(); legacy.close()
        migrated = audit.open_database(legacy_path)
        self.addCleanup(migrated.close)
        self.assertEqual(migrated.execute("PRAGMA user_version").fetchone()[0], 4)
        message = audit.query_messages(migrated, "r", include_content=True)[0]
        self.assertEqual(message["text"], "legacy bytes")
        self.assertEqual(message["content_byte_length"], len("legacy bytes".encode()))
        self.assertEqual(migrated.execute("SELECT text FROM captured_messages WHERE message_id='m'").fetchone()[0], "")

    def test_v4_guard_definitions_are_required(self):
        self.connection.execute("DROP TRIGGER immutable_events_update")
        with self.assertRaisesRegex(audit.AuditError, "immutable_events_update"):
            audit.validate_database(self.connection)
        self.connection.execute(
            "CREATE TRIGGER immutable_events_update BEFORE UPDATE ON events BEGIN SELECT 1; END"
        )
        with self.assertRaisesRegex(audit.AuditError, "immutable_events_update"):
            audit.validate_database(self.connection)

    def test_relevant_message_capture_is_bounded_to_1024_characters(self):
        long_text = "request details " * 100
        self.assertGreater(len(long_text), audit.MAX_RELEVANT_MESSAGE_CHARACTERS)
        with self.assertRaisesRegex(audit.AuditValidationError, "exceeds 1024 characters"):
            audit.capture_message(self.connection, self.run, "user", long_text,
                                  capture_source="host", fidelity="exact")
        bounded, incomplete = audit.bounded_message_evidence(long_text)
        self.assertTrue(incomplete)
        self.assertLessEqual(len(bounded), audit.MAX_RELEVANT_MESSAGE_CHARACTERS)
        self.assertTrue(bounded.startswith("[Incomplete evidence:"))
        audit.capture_message(self.connection, self.run, "user", bounded,
                              capture_source="agent", fidelity="incomplete")

    def test_writer_repairs_transitional_v4_envelope_text(self):
        database = pathlib.Path(self.tmp.name) / "transitional.sqlite3"
        connection = audit.open_database(database)
        workspace = audit.ensure_workspace(connection, pathlib.Path(self.tmp.name) / "transitional-project")
        run = audit.start_run(connection, workspace, "next", capture_mode="relevant")
        audit.capture_message(connection, run, "user", "only in content", message_id="transitional-message",
                              capture_source="host", fidelity="exact")
        connection.execute("DROP TRIGGER immutable_messages_update")
        connection.execute("UPDATE captured_messages SET text='only in content' WHERE message_id='transitional-message'")
        connection.execute(audit._v4_message_trigger())
        connection.commit()
        connection.close()
        repaired = audit.open_database(database)
        self.addCleanup(repaired.close)
        self.assertEqual(repaired.execute("SELECT text FROM captured_messages WHERE message_id='transitional-message'").fetchone()[0], "")
        self.assertEqual(audit.query_messages(repaired, run, include_content=True)[0]["text"], "only in content")


if __name__ == "__main__":
    unittest.main()

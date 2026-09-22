import http.client
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest import mock
from urllib.parse import quote

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tabilet_audit as audit
import tabilet_explorer as explorer
import test_harness as harness


class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.project = harness.make_repo(self.base / "project")
        self.database = self.base / "state" / "audit.sqlite3"
        self.app = explorer.ExplorerApp(self.project, self.database)
        self.server = explorer.ExplorerServer(("127.0.0.1", 0), self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.server.server_address
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, *, token=None, origin=None, body=None, raw=False):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        headers = {"Host": f"127.0.0.1:{self.port}"}
        if token is not None:
            headers["X-Tabilet-Token"] = token
        if origin is not None:
            headers["Origin"] = origin
        if body is not None:
            headers["Content-Type"] = "application/json"
            body = body if raw else json.dumps(body)
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        connection.close()
        content_type = response.getheader("Content-Type", "")
        return response.status, (json.loads(raw) if "json" in content_type else raw.decode())

    def bootstrap(self):
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("meta name=\"tabilet-token\"", html)
        token = html.split('meta name="tabilet-token" content="', 1)[1].split('"', 1)[0]
        status, result = self.request("POST", "/api/refresh", token=token,
                                      origin=f"http://127.0.0.1:{self.port}", body={})
        self.assertEqual(status, 200, result)
        return token

    def test_setup_shell_token_and_static_assets(self):
        status, health = self.request("GET", "/api/health")
        self.assertEqual(status, 401)
        self.assertFalse(self.database.exists())
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Tabilet Explorer", html)
        status, css = self.request("GET", "/assets/explorer.css")
        self.assertEqual(status, 200)
        self.assertIn("focus-visible", css)
        status, script = self.request("GET", "/assets/explorer.js")
        self.assertEqual(status, 200)
        self.assertIn("/api/overview", script)

    def test_scoped_reads_refresh_and_live_source_validation(self):
        token = self.bootstrap()
        status, health = self.request("GET", "/api/health", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(health["database_available"])
        self.assertTrue(health["index"]["complete"])
        status, overview = self.request("GET", "/api/overview", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(overview["counts"]["active milestones"], 1)
        status, document = self.request("GET", "/api/document?path=tabilet%2Fmemory-bank%2Fstatus-M01.md", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(document["source"], "indexed")
        self.assertIn("Implement feature", document["document"]["text"])
        status, follow = self.request("POST", "/api/follow-up", token=token,
                                      origin=f"http://127.0.0.1:{self.port}",
                                      body={"path": "tabilet/memory-bank/status-M01.md", "line": 5})
        self.assertEqual(status, 200, follow)
        self.assertIn("status-M01.md:5", follow["prompt"])
        status, rejected = self.request("POST", "/api/follow-up", token=token,
                                        origin=f"http://127.0.0.1:{self.port}",
                                        body={"path": "private.txt", "line": 1})
        self.assertEqual(status, 400)
        self.assertIn("declared indexed", rejected["error"])
        status, rejected = self.request("POST", "/api/follow-up", token=token,
                                        origin=f"http://127.0.0.1:{self.port}",
                                        body={"path": "tabilet/memory-bank/status-M01.md", "line": 999})
        self.assertEqual(status, 400)
        self.assertIn("outside", rejected["error"])
        self.project.joinpath("tabilet/memory-bank/status-M01.md").write_text(
            "| Item | State | Notes |\n|---|---|---|\n| Changed | `[ ]` | now different |\n",
            encoding="utf-8")
        status, todo = self.request("GET", "/api/todo", token=token)
        self.assertEqual(status, 200)
        self.assertFalse(todo["validation"]["valid"])
        self.assertEqual([group["label"] for group in todo["groups"]],
                         ["Resume", "Ready", "Waiting", "Blocked", "Needs Review"])
        self.assertTrue(todo["needs_review"])

    def test_audit_timeline_cursor_and_run_scope(self):
        token = self.bootstrap()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            first = audit.start_run(connection, workspace, "next", run_id="run-a")
            audit.finish_run(connection, first, "completed")
            second = audit.start_run(connection, workspace, "propose", run_id="run-b")
            audit.append_event(connection, {
                "schema": "tabilet.audit.event/v1", "event_id": "run-b:observed", "run_id": second,
                "workspace_id": workspace, "operation": "propose", "event_type": "task_observed",
                "recorded_at": "2026-01-01T00:00:00Z", "occurred_at": None,
                "subject": {"milestone_id": "M01", "task_label": "Implement feature",
                            "status_path": "tabilet/memory-bank/status-M01.md"},
                "details": {"schema": "tabilet.audit.details/v1"},
            })
            audit.finish_run(connection, second, "blocked")
            third = audit.start_run(connection, workspace, "goal", run_id="run-c", capture_mode="relevant")
            audit.capture_message(connection, third, "user", "needle appears only in this older request",
                                  capture_source="host", fidelity="exact", message_id="message-c")
            child = audit.start_run(connection, workspace, "next", run_id="run-c-child", parent_run_id=third, capture_mode="relevant")
            audit.capture_message(connection, child, "user", "child-only request",
                                  capture_source="host", fidelity="exact", message_id="message-c-child")
            audit.finish_run(connection, child, "completed")
            audit.finish_run(connection, third, "completed")
        status, page = self.request("GET", "/api/timeline?limit=1", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(len(page["results"]), 1)
        self.assertTrue(page["next_cursor"])
        status, next_page = self.request("GET", "/api/timeline?limit=1&cursor=" + quote(page["next_cursor"]), token=token)
        self.assertEqual(status, 200)
        self.assertEqual({x["run_id"] for x in page["results"]} & {x["run_id"] for x in next_page["results"]}, set())
        self.assertTrue(next_page["previous_cursor"])
        status, previous_page = self.request("GET", "/api/timeline?limit=1&cursor=" + quote(next_page["previous_cursor"]), token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in previous_page["results"]],
                         [row["run_id"] for row in page["results"]])
        status, detail = self.request("GET", "/api/runs/run-b", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(detail["run"]["run_id"], "run-b")
        self.assertTrue(any(item["kind"] == "milestone" and item["resolved"] for item in detail["current_state"]))
        self.assertTrue(any(item["kind"] == "task" and item["resolved"] for item in detail["current_state"]))
        status, searched = self.request("GET", "/api/timeline?limit=1&search=needle", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in searched["results"]], ["run-c"])
        self.assertEqual(searched["results"][0]["request_summary"], "needle appears only in this older request")
        self.assertEqual(searched["results"][0]["capture_fidelity"], "exact")
        self.assertEqual([row["run_id"] for row in searched["results"][0]["children"]], ["run-c-child"])
        status, child_search = self.request("GET", "/api/timeline?search=child-only", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in child_search["results"]], ["run-c"])
        status, captured = self.request("GET", "/api/runs/run-c", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(captured["messages"][0]["text"], "needle appears only in this older request")
        status, bad = self.request("GET", "/api/runs/other-project-run", token=token)
        self.assertEqual(status, 400)
        self.assertIn("project", bad["error"])

    def test_source_and_origin_boundaries(self):
        token = self.bootstrap()
        status, body = self.request("GET", "/api/document?path=..%2Fsecret.md", token=token)
        self.assertEqual(status, 400)
        status, body = self.request("POST", "/api/refresh", token=token,
                                    origin=f"http://evil.invalid:{self.port}", body={})
        self.assertEqual(status, 403)
        status, body = self.request("POST", "/api/follow-up", token=token, body={})
        self.assertEqual(status, 403)
        self.app.token = "\"><script>alert(1)</script>"
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertNotIn("<script>alert(1)</script>", html)
        status, body = self.request("POST", "/api/refresh", token=self.app.token,
                                    origin=f"http://127.0.0.1:{self.port}", body='{"literal":NaN}', raw=True)
        self.assertEqual(status, 400)
        self.assertIn("constant", body["error"])

    def test_loopback_only_server_and_normalized_activity(self):
        with self.assertRaisesRegex(audit.AuditError, "loopback"):
            explorer.ExplorerServer(("0.0.0.0", 0), self.app)
        token = self.bootstrap()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            audit.start_run(connection, workspace, "next", run_id="whole-second",
                            started_at="2026-01-01T12:00:01Z")
            audit.start_run(connection, workspace, "next", run_id="fractional-newer",
                            started_at="2026-01-01T12:00:01.100000Z")
        status, health = self.request("GET", "/api/health", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(health["activity"], "2026-01-01T12:00:01.100000Z")

    def test_old_database_exposes_audit_evidence_before_refresh(self):
        self.stop_server()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database)
        connection.executescript(audit.SCHEMA_SQL)
        connection.execute("INSERT INTO schema_meta VALUES ('schema','tabilet.audit/v1')")
        connection.execute("PRAGMA user_version=1")
        connection.execute("INSERT INTO workspaces VALUES (?,?,?,?,?,?)",
                           ("legacy", str(self.project), None, "main",
                            "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           ("legacy-run", "legacy", "init", "2026-01-01T00:00:00Z", None,
                            "1", "metadata", None, None, "clean", None))
        connection.commit(); connection.close()
        self.app = explorer.ExplorerApp(self.project, self.database)
        overview = self.app.overview()
        self.assertEqual(overview["counts"]["audit runs"], 1)
        self.assertEqual(overview["attention"][0]["kind"], "migration")

    def test_invalid_pagination_and_bounded_run_detail(self):
        token = self.bootstrap()
        status, error = self.request("GET", "/api/timeline?limit=-2", token=token)
        self.assertEqual(status, 400)
        self.assertIn("limit", error["error"])
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            run = audit.start_run(connection, workspace, "goal", run_id="large-message", capture_mode="relevant")
            audit.capture_message(connection, run, "user", "x" * 70000,
                                  capture_source="host", fidelity="exact", message_id="large-message-input")
            audit.finish_run(connection, run, "completed")
        detail = self.app.run("large-message")
        self.assertTrue(detail["messages"][0]["truncated"])
        self.assertEqual(detail["messages"][0]["original_characters"], 70000)
        status, error = self.request("GET", "/api/runs/missing?event_limit=0", token=token)
        self.assertEqual(status, 400)
        self.assertIn("limit", error["error"])

    def test_todo_preserves_closure_review_and_followup_rechecks_hash(self):
        token = self.bootstrap()
        status_path = self.project / "tabilet/memory-bank/status-M01.md"
        status_path.write_text(status_path.read_text().replace("`[ ]`", "`[+]`"), encoding="utf-8")
        status, refreshed = self.request("POST", "/api/refresh", token=token,
                                         origin=f"http://127.0.0.1:{self.port}", body={})
        self.assertEqual(status, 200, refreshed)
        status, todo = self.request("GET", "/api/todo", token=token)
        self.assertEqual(status, 200)
        self.assertFalse(todo["recommendations_available"])
        self.assertEqual(todo["needs_review"][0]["milestone_id"], "M01")
        self.assertTrue(todo["groups"])

        original = explorer.index.readiness
        def mutate_after_validation(connection, workspace, project):
            result = original(connection, workspace, project)
            status_path.write_text(status_path.read_text() + "\nchanged\n", encoding="utf-8")
            return result
        with mock.patch.object(explorer.index, "readiness", side_effect=mutate_after_validation):
            with self.assertRaisesRegex(audit.AuditError, "changed since readiness"):
                self.app.follow_up({"action": "review", "milestone_id": "M01"})

    def test_mixed_layout_refresh_records_failed_attempt(self):
        self.bootstrap()
        (self.project / "memory-bank").mkdir()
        with self.assertRaises(audit.AuditError):
            self.app.refresh()
        with audit.open_readonly_database(self.database) as connection:
            workspace = explorer.index.workspace_id(connection, self.project)
            state = explorer.index.status(connection, workspace)
        self.assertFalse(state["complete"])
        self.assertTrue(state["diagnostics"])


if __name__ == "__main__":
    unittest.main()

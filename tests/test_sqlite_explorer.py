import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
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

    def request(self, method, path, *, token=None, origin=None, body=None):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        headers = {"Host": f"127.0.0.1:{self.port}"}
        if token is not None:
            headers["X-Tabilet-Token"] = token
        if origin is not None:
            headers["Origin"] = origin
        if body is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(body)
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
        self.assertEqual(todo["groups"], [])

    def test_audit_timeline_cursor_and_run_scope(self):
        token = self.bootstrap()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            first = audit.start_run(connection, workspace, "next", run_id="run-a")
            audit.finish_run(connection, first, "completed")
            second = audit.start_run(connection, workspace, "propose", run_id="run-b")
            audit.finish_run(connection, second, "blocked")
            third = audit.start_run(connection, workspace, "goal", run_id="run-c", capture_mode="relevant")
            audit.capture_message(connection, third, "user", "needle appears only in this older request",
                                  capture_source="host", fidelity="exact", message_id="message-c")
            audit.finish_run(connection, third, "completed")
        status, page = self.request("GET", "/api/timeline?limit=1", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(len(page["results"]), 1)
        self.assertTrue(page["next_cursor"])
        status, next_page = self.request("GET", "/api/timeline?limit=1&cursor=" + quote(page["next_cursor"]), token=token)
        self.assertEqual(status, 200)
        self.assertEqual({x["run_id"] for x in page["results"]} & {x["run_id"] for x in next_page["results"]}, set())
        status, detail = self.request("GET", "/api/runs/run-b", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(detail["run"]["run_id"], "run-b")
        status, searched = self.request("GET", "/api/timeline?limit=1&search=needle", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in searched["results"]], ["run-c"])
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


if __name__ == "__main__":
    unittest.main()

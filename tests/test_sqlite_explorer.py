import http.client
import hashlib
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
        self.assertNotIn("tabilet-token", html)
        token = self.app.token
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

    def test_port_scoped_cookie_and_response_headers(self):
        connection=http.client.HTTPConnection(self.host,self.port,timeout=5)
        connection.request('GET','/',headers={'Host':f'127.0.0.1:{self.port}'})
        response=connection.getresponse(); body=response.read().decode(); headers=dict(response.getheaders());connection.close()
        cookie=headers['Set-Cookie']
        self.assertIn(f'tabilet_token_{self.port}=',cookie)
        self.assertIn('HttpOnly',cookie)
        self.assertNotIn('name="tabilet-token"',body)
        self.assertEqual(headers['X-Frame-Options'],'DENY')
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        other=explorer.ExplorerServer(('127.0.0.1',0),self.app)
        thread=threading.Thread(target=other.serve_forever,daemon=True);thread.start()
        try:
            self.assertNotEqual(other.cookie_name,self.server.cookie_name)
            connection=http.client.HTTPConnection('127.0.0.1',other.server_address[1],timeout=5)
            connection.request('GET','/api/health',headers={'Host':f'127.0.0.1:{other.server_address[1]}','Cookie':cookie.split(';',1)[0]})
            response=connection.getresponse();response.read();connection.close()
            self.assertEqual(response.status,401)
        finally:
            other.shutdown();other.server_close();thread.join(2)

    def test_run_detail_loads_only_page_and_summary_messages(self):
        self.bootstrap()
        with audit.open_database(self.database,project_roots=[self.project]) as connection:
            workspace=audit.ensure_workspace(connection,self.project)
            run=audit.start_run(connection,workspace,'next',run_id='paged',capture_mode='relevant')
            for number in range(120):
                audit.capture_message(connection,run,'user' if number==0 else 'assistant',str(number),
                    capture_source='host',fidelity='exact',message_id=f'paged-{number}')
        original=audit.query_messages;calls=[]
        def observed(*args,**kwargs):
            calls.append(kwargs)
            return original(*args,**kwargs)
        with mock.patch.object(explorer.audit,'query_messages',side_effect=observed):
            detail=self.app.run('paged',{'message_limit':['5'],'message_offset':['50']})
        self.assertEqual(len(detail['messages']),5)
        self.assertEqual([call['limit'] for call in calls],[6,1,1])
        self.assertEqual(calls[0]['offset'],50)

    def test_server_caps_concurrent_request_threads(self):
        class OneRequestServer(explorer.ExplorerServer):
            max_requests=1
        server=OneRequestServer(('127.0.0.1',0),self.app)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        entered=threading.Event();release=threading.Event()
        original=explorer.Handler._asset
        def blocked(handler,name):
            entered.set()
            self.assertTrue(release.wait(5))
            return original(handler,name)
        first_result=[]
        def first():
            connection=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=5)
            connection.request('GET','/',headers={'Host':f'127.0.0.1:{server.server_address[1]}'})
            response=connection.getresponse();first_result.append(response.status);response.read();connection.close()
        try:
            with mock.patch.object(explorer.Handler,'_asset',blocked):
                client=threading.Thread(target=first);client.start()
                self.assertTrue(entered.wait(5))
                connection=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=5)
                connection.request('GET','/',headers={'Host':f'127.0.0.1:{server.server_address[1]}'})
                response=connection.getresponse();response.read();connection.close()
                self.assertEqual(response.status,503)
                release.set();client.join(5)
            self.assertEqual(first_result,[200])
        finally:
            release.set();server.shutdown();server.server_close();thread.join(2)

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
                                      body={"task_label": "Implement feature", "milestone_id": "M01",
                                            "source": {"path": "tabilet/memory-bank/status-M01.md", "line": 5}})
        self.assertEqual(status, 200, follow)
        self.assertIn("status-M01.md:5", follow["prompt"])
        status, rejected = self.request("POST", "/api/follow-up", token=token,
                                        origin=f"http://127.0.0.1:{self.port}",
                                        body={"task_label": "Implement feature", "milestone_id": "M01",
                                              "source": {"path": "private.txt", "line": 1}})
        self.assertEqual(status, 400)
        self.assertIn("selected task source", rejected["error"])
        status, rejected = self.request("POST", "/api/follow-up", token=token,
                                        origin=f"http://127.0.0.1:{self.port}",
                                        body={"task_label": "Implement feature", "milestone_id": "M01",
                                              "source": {"path": "tabilet/memory-bank/status-M01.md", "line": 999}})
        self.assertEqual(status, 400)
        self.assertIn("selected task line", rejected["error"])
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
        status, body = self.request("POST", "/api/refresh", token=token,
                                    origin=f"https://127.0.0.1:{self.port}", body={})
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

    def test_migrated_runs_are_labeled_legacy_without_v4_evidence(self):
        self.stop_server()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database)
        connection.executescript(audit.SCHEMA_SQL + audit.INDEX_SQL + audit.EXPLORER_SQL)
        connection.execute("INSERT INTO schema_meta VALUES ('schema','tabilet.audit/v3')")
        connection.execute("INSERT INTO schema_meta VALUES ('recorder_version','tabilet-audit/3')")
        connection.execute("PRAGMA user_version=3")
        connection.execute("INSERT INTO workspaces VALUES (?,?,?,?,?,?)",
                           ("legacy", str(self.project), None, "main",
                            "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           ("legacy-run", "legacy", "next", "2026-01-01T00:00:00Z", None,
                            "tabilet-audit/3", "relevant", None, None, "clean", None))
        connection.commit(); connection.close()
        with audit.open_database(self.database, project_roots=[self.project]) as migrated:
            self.assertEqual(migrated.execute("PRAGMA user_version").fetchone()[0], 4)
        self.app = explorer.ExplorerApp(self.project, self.database)
        timeline = self.app.timeline({})
        self.assertTrue(timeline["results"][0]["legacy"])
        self.assertEqual(timeline["results"][0]["capture_fidelity"], "legacy")
        detail = self.app.run("legacy-run")
        self.assertTrue(detail["run"]["legacy"])

    def test_timeline_evidence_filters_include_goal_children(self):
        token = self.bootstrap()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            parent = audit.start_run(connection, workspace, "goal", run_id="goal-parent")
            child = audit.start_run(connection, workspace, "next", run_id="goal-child",
                                    parent_run_id=parent, capture_mode="relevant")
            audit.record_provenance(connection, child, {
                "invocation_kind": "interactive_skill", "instruction_set_name": "memory-bank-next",
                "capture_method": "instruction_driven", "fingerprint_fidelity": "unavailable",
            })
            audit.capture_message(connection, child, "user", "child evidence", message_id="goal-message",
                                  capture_source="host", fidelity="exact")
            audit.record_coverage(connection, {
                "coverage_id": "goal-child-coverage", "run_id": child,
                "scope": "skill_conversation", "coverage": "complete", "content_state": "available",
                "exact_count": 1, "capture_method": "instruction_driven",
                "observed_at": "2099-01-01T00:00:00Z",
            })
        status, filtered = self.request("GET", "/api/timeline?instruction_set=memory-bank-next", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in filtered["results"]], [parent])
        status, filtered = self.request("GET", "/api/timeline?coverage=complete", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in filtered["results"]], [parent])
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            audit.record_coverage(connection, {
                "coverage_id": "goal-child-later", "run_id": child,
                "scope": "skill_conversation", "coverage": "partial", "content_state": "available",
                "exact_count": 1, "capture_method": "instruction_driven",
                "observed_at": "2026-01-01T00:00:00.123456Z",
            })
        status, filtered = self.request("GET", "/api/timeline?coverage=complete", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(filtered["results"], [])
        status, filtered = self.request("GET", "/api/timeline?coverage=partial", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in filtered["results"]], [parent])
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            audit.purge_message(connection, "goal-message", "privacy request", "goal-message")
        status, filtered = self.request("GET", "/api/timeline?purged=1", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([row["run_id"] for row in filtered["results"]], [parent])

    def test_v4_absent_provenance_is_distinct_from_legacy(self):
        token = self.bootstrap()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            audit.start_run(connection, workspace, "next", run_id="no-provenance")
        status, timeline = self.request("GET", "/api/timeline", token=token)
        self.assertEqual(status, 200)
        run = next(row for row in timeline["results"] if row["run_id"] == "no-provenance")
        self.assertFalse(run["legacy"])
        self.assertIsNone(run["provenance"])
        self.assertIn("Provenance not supplied",
                      (Path(__file__).resolve().parents[1] / "harness/explorer/explorer.js").read_text())
        detail = self.app.run("no-provenance")
        self.assertFalse(detail["run"]["legacy"])
        self.assertIsNone(detail["run"]["provenance"])

    def test_invalid_pagination_and_bounded_run_detail(self):
        token = self.bootstrap()
        status, error = self.request("GET", "/api/timeline?limit=-2", token=token)
        self.assertEqual(status, 400)
        self.assertIn("limit", error["error"])

    def test_todo_goal_children_and_run_details_are_paginated(self):
        token = self.bootstrap()
        status_path = self.project / 'tabilet/memory-bank/status-M01.md'
        rows = ['# Status\n\n| ID | State | Notes |\n|---|---|---|\n']
        rows.extend(f'| T{number:03} | `[ ]` | pending |\n' for number in range(120))
        status_path.write_text(''.join(rows), encoding='utf-8')
        status, refreshed = self.request('POST', '/api/refresh', token=token,
                                         origin=f'http://127.0.0.1:{self.port}', body={})
        self.assertEqual(status, 200, refreshed)
        status, todo = self.request('GET', '/api/todo?limit=50', token=token)
        self.assertEqual(status, 200)
        self.assertEqual(len(todo['ready']), 50)
        self.assertEqual(todo['totals']['ready'], 120)
        self.assertTrue(todo['pagination']['ready']['more'])
        status, second_page = self.request('GET', '/api/todo?limit=50&ready_offset=50', token=token)
        self.assertEqual(second_page['ready'][0]['explicit_id'], 'T050')

        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            parent = audit.start_run(connection, workspace, 'goal', run_id='large-goal', capture_mode='relevant')
            for number in range(120):
                audit.start_run(connection, workspace, 'next', run_id=f'child-{number:03}', parent_run_id=parent)
            for number in range(60):
                role = 'assistant' if number == 59 else 'user'
                audit.capture_message(connection, parent, role, f'message {number}', capture_source='host',
                                      fidelity='exact', message_id=f'message-{number:03}')
        timeline = self.app.timeline({'limit': ['1'], 'child_limit': ['20']})
        goal = next(item for item in timeline['entries'] if item['run_id'] == 'large-goal')
        self.assertEqual(len(goal['children']), 20)
        self.assertTrue(goal['children_more'])
        detail = self.app.run('large-goal')
        self.assertEqual(len(detail['messages']), 50)
        self.assertTrue(detail['pagination']['messages']['more'])
        self.assertEqual(detail['output_message']['text'], 'message 59')
        self.assertEqual(len(detail['children']), 50)
        self.assertTrue(detail['pagination']['children']['more'])

        first_search = self.app.search({'q': ['pending'], 'limit': ['10']})
        self.assertEqual(len(first_search['results']), 10)
        self.assertTrue(first_search['more'])
        second_search = self.app.search({'q': ['pending'], 'limit': ['10'], 'offset': ['10']})
        self.assertFalse({row['search_id'] for row in first_search['results']} &
                         {row['search_id'] for row in second_search['results']})

    def test_followup_revalidates_every_source_and_requires_a_task(self):
        self.bootstrap()
        with self.assertRaisesRegex(audit.AuditError, 'needs a task'):
            self.app.follow_up({'action': 'continue', 'path': 'tabilet/memory-bank/status-M01.md'})
        milestone = self.project / 'tabilet/memory-bank/milestone.md'
        original = explorer.index.readiness

        def mutate_other_source(connection, workspace, project):
            result = original(connection, workspace, project)
            milestone.write_text(milestone.read_text() + '\nchanged policy evidence\n', encoding='utf-8')
            return result

        with mock.patch.object(explorer.index, 'readiness', side_effect=mutate_other_source):
            with self.assertRaisesRegex(audit.AuditError, 'project sources changed'):
                self.app.follow_up({'action': 'continue', 'task_label': 'Implement feature',
                                    'milestone_id': 'M01'})

    def test_current_task_resolution_uses_recorded_milestone_scope(self):
        self.bootstrap()
        bank = self.project / 'tabilet/memory-bank'
        (bank / 'milestone.md').write_text(
            '# Milestones\n\n## M01 - One\n\n**Acceptance.** one\n\n'
            '## M02 - Two\n\n**Acceptance.** two\n', encoding='utf-8')
        for identity in ('M01', 'M02'):
            (bank / f'status-{identity}.md').write_text(
                '# Status\n\n| ID | State | Notes |\n|---|---|---|\n| Shared | `[ ]` | pending |\n',
                encoding='utf-8')
        self.app.refresh()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            run = audit.start_run(connection, workspace, 'next', run_id='scoped-run')
            audit.append_event(connection, {
                'schema': 'tabilet.audit.event/v1', 'event_id': 'scoped-event', 'run_id': run,
                'workspace_id': workspace, 'operation': 'next', 'event_type': 'task_observed',
                'recorded_at': audit.utc_now(), 'subject': {'milestone_id': 'M01',
                    'task_label': 'Shared', 'status_path': 'tabilet/memory-bank/status-M01.md'},
                'details': {'schema': 'tabilet.audit.details/v1'},
            })
        current = [item for item in self.app.run('scoped-run')['current_state'] if item['kind'] == 'task']
        self.assertEqual(len(current), 1)
        self.assertTrue(current[0]['resolved'])
        self.assertEqual(current[0]['record']['milestone_id'], 'M01')

        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            run = audit.start_run(connection, workspace, 'next', run_id='explicit-artifact-run')
            audit.append_event(connection, {
                'schema': 'tabilet.audit.event/v1', 'event_id': 'explicit-artifact-event',
                'run_id': run, 'workspace_id': workspace, 'operation': 'next',
                'event_type': 'task_observed', 'recorded_at': audit.utc_now(), 'subject': {},
                'details': {'schema': 'tabilet.audit.details/v1', 'explorer': {
                    'schema': 'tabilet.audit.explorer/v1', 'phase': 'applied',
                    'artifact_refs': [{'namespace': 'task', 'identifier': 'M01/Shared',
                                       'relationship': 'observed'}],
                }},
            })
        artifact_current = [item for item in self.app.run('explicit-artifact-run')['current_state']
                            if item['kind'] == 'task']
        self.assertEqual(len(artifact_current), 1)
        self.assertTrue(artifact_current[0]['resolved'])
        self.assertEqual(artifact_current[0]['record']['milestone_id'], 'M01')

    def test_followup_action_membership_uses_milestone_scoped_task_identity(self):
        self.bootstrap()
        bank = self.project / 'tabilet/memory-bank'
        (bank / 'milestone.md').write_text(
            '# Milestones\n\n## M01 One\n\n**Acceptance.** one\n\n'
            '## M02 Two\n\n**Acceptance.** two\n', encoding='utf-8')
        (bank / 'status-M01.md').write_text(
            '| ID | State | Notes |\n|---|---|---|\n| T01 | `[ ]` | ready |\n', encoding='utf-8')
        (bank / 'status-M02.md').write_text(
            '| ID | State | Notes |\n|---|---|---|\n'
            '| T01 | `[ ]` | Dependency: M02/MISSING |\n', encoding='utf-8')
        self.app.refresh()
        follow = self.app.follow_up({'action': 'continue', 'task_id': 'T01', 'milestone_id': 'M02'})
        self.assertIn('Verify the live ledger', follow['prompt'])

    def test_timeline_child_filters_do_not_cross_workspace_boundary(self):
        self.bootstrap()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            parent = audit.start_run(connection, workspace, 'goal', run_id='scoped-parent')
            other = audit.ensure_workspace(connection, self.base / 'other-project')
            connection.execute("""
                INSERT INTO runs(run_id,workspace_id,operation,started_at,completed_at,
                                 recorder_version,capture_mode,parent_run_id,git_head,
                                 worktree_state,result)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, ('foreign-child', other, 'archive', '2026-01-01T00:00:00Z', None,
                  audit.RECORDER_VERSION, 'metadata', parent, None, 'unversioned', None))
            connection.commit()
        filtered = self.app.timeline({'operation': ['archive']})
        self.assertNotIn('scoped-parent', [row['run_id'] for row in filtered['entries']])

    def test_health_uses_the_branch_from_the_current_index_generation(self):
        self.bootstrap()
        import subprocess
        subprocess.run(['git', 'checkout', '-q', '-b', 'explorer-current-branch'],
                       cwd=self.project, check=True)
        self.app.refresh()
        health = self.app.health()
        self.assertEqual(health['branch'], 'explorer-current-branch')
        self.assertEqual(health['project']['branch'], 'explorer-current-branch')

    def test_overview_active_counts_exclude_retired_rows(self):
        history = self.project / 'tabilet/docs/history'; history.mkdir(parents=True)
        retired_status = '# Status\n\n| Item | State | Notes |\n|---|---|---|\n| Old | `[+]` | done |\n'
        (history / 'status-M02.md').write_text(harness.retirement_text(retired_status, milestone_id='M02'), encoding='utf-8')
        (history / 'index.md').write_text(
            '# History\n\n| Milestone | Outcome | Retired | Record | Summary |\n|---|---|---|---|---|\n'
            '| M02 | completed | 2026-09-12 | [M02](status-M02.md) | old |\n', encoding='utf-8')
        self.app.refresh()
        overview = self.app.overview()
        self.assertEqual(overview['counts']['completed'], 0)
        self.assertEqual(overview['counts']['history'], 1)

    def test_overview_attention_items_link_to_their_evidence_view(self):
        self.bootstrap()
        status = self.project / 'tabilet/memory-bank/status-M01.md'
        status.write_text(status.read_text().replace('`[ ]`', '`[!]`'), encoding='utf-8')
        self.app.refresh()
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            audit.start_run(connection, workspace, 'next', run_id='unfinished-attention')
        overview = self.app.overview()
        blocked = next(item for item in overview['attention'] if item['kind'] == 'blocked')
        unfinished = next(item for item in overview['attention'] if item['kind'] == 'unfinished')
        self.assertEqual(blocked['source']['path'], 'tabilet/memory-bank/status-M01.md')
        self.assertEqual(unfinished['view'], 'timeline')
        self.assertEqual(unfinished['outcome'], 'unfinished')

    def test_post_bodies_require_json_boolean_and_integer_types(self):
        token = self.bootstrap()
        origin = f'http://127.0.0.1:{self.port}'
        status, body = self.request('POST', '/api/refresh', token=token, origin=origin,
                                    body={'rebuild': 'false'})
        self.assertEqual(status, 400); self.assertIn('boolean', body['error'])
        status, body = self.request('POST', '/api/follow-up', token=token, origin=origin,
                                    body={'line': True})
        self.assertEqual(status, 400); self.assertIn('unknown follow-up fields', body['error'])
        status, body = self.request('POST', '/api/follow-up', token=token, origin=origin,
                                    body={'task_label': 'Implement feature', 'milestone_id': 'M01',
                                          'source': {'path': 'tabilet/memory-bank/status-M01.md',
                                                     'line': True}})
        self.assertEqual(status, 400); self.assertIn('positive integer', body['error'])
        with audit.open_database(self.database, project_roots=[self.project]) as connection:
            workspace = audit.ensure_workspace(connection, self.project)
            run = audit.start_run(connection, workspace, "goal", run_id="large-message", capture_mode="relevant")
            legacy_text = "x" * 70000
            raw = legacy_text.encode("utf-8")
            connection.execute(
                "INSERT INTO captured_messages(message_id,run_id,sequence,role,captured_at,text,capture_source,fidelity,redaction_note,content_sha256,content_byte_length) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("large-message-input", run, 1, "user", audit.utc_now(), "", "host", "exact", None,
                 hashlib.sha256(raw).hexdigest(), len(raw)),
            )
            connection.execute(
                "INSERT INTO captured_message_content(message_id,content,sha256,byte_length) VALUES (?,?,?,?)",
                ("large-message-input", raw, hashlib.sha256(raw).hexdigest(), len(raw)),
            )
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
        self.assertNotIn("recommendations_available", todo)
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

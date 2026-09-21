#!/usr/bin/env python3
"""Local, read-only browser explorer for one Tabilet project.

The explorer is deliberately a small standard-library HTTP application.  It
does not execute agents or edit project files.  Markdown remains authoritative;
the SQLite index is only a disposable projection and the audit tables are
read-only from browser requests.
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import html
import http.server
import json
import os
import pathlib
import secrets
import sqlite3
import threading
import urllib.parse
from http.cookies import SimpleCookie
from typing import Any

import tabilet_audit as audit
import tabilet_index as index


MAX_BODY = 64 * 1024
MAX_PAGE = 100
POLL_SECONDS = 5
ASSET_DIR = pathlib.Path(__file__).with_name("explorer")
INSTALLED_ASSET_DIR = pathlib.Path.home() / ".local" / "share" / "tabilet" / "explorer"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _cursor(value: dict[str, str]) -> str:
    raw = _json(value).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(value: str) -> dict[str, str]:
    if len(value) > 512:
        raise audit.AuditError("cursor is too long")
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        result = json.loads(raw)
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise audit.AuditError("invalid timeline cursor") from exc
    if not isinstance(result, dict) or not isinstance(result.get("started_at"), str) or not isinstance(result.get("run_id"), str):
        raise audit.AuditError("invalid timeline cursor")
    audit._timestamp(result["started_at"], "cursor.started_at")
    return result


def _safe_relative(value: str) -> str:
    if not value or "\\" in value:
        raise audit.AuditError("source path must be a declared relative path")
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise audit.AuditError("source path must be a declared relative path")
    return path.as_posix()


class ExplorerApp:
    def __init__(self, project: pathlib.Path, database: pathlib.Path):
        self.project = project.expanduser().resolve()
        self.database = audit.external_path(database, [self.project])
        self.token = secrets.token_urlsafe(32)
        self.refresh_lock = threading.Lock()

    def _open(self, write=False):
        if not self.database.is_file():
            raise audit.AuditError("no external audit database; use Refresh project to create the index")
        if write:
            return audit.open_database(self.database, project_roots=[self.project])
        audit.external_path(self.database, [self.project])
        return audit.open_readonly_database(self.database)

    def _workspace(self, connection):
        row = connection.execute("SELECT * FROM workspaces WHERE project_root=?", (str(self.project),)).fetchone()
        if not row:
            raise audit.AuditError("project is not registered in this database; use Refresh project")
        names = [x[1] for x in connection.execute("PRAGMA table_info(workspaces)")]
        return dict(zip(names, row))

    @contextlib.contextmanager
    def read(self):
        connection = self._open(False)
        try:
            connection.execute("BEGIN")
            workspace = self._workspace(connection)
            yield connection, workspace
        finally:
            connection.close()

    def health(self):
        result = {"project_root": str(self.project), "database": str(self.database), "database_available": False,
                  "setup_required": not self.database.is_file(), "index": None, "diagnostics": [], "activity": None}
        if not self.database.is_file():
            return result
        try:
            with self.read() as (connection, workspace):
                result.update({"database_available": True, "workspace_id": workspace["workspace_id"], "branch": workspace.get("branch")})
                result["index"] = index.status(connection, workspace["workspace_id"])
                result["diagnostics"] = result["index"].get("diagnostics", [])
                latest = connection.execute("SELECT MAX(value) FROM (SELECT started_at AS value FROM runs WHERE workspace_id=? UNION ALL SELECT e.recorded_at AS value FROM events e JOIN runs r USING(run_id) WHERE r.workspace_id=? UNION ALL SELECT m.captured_at AS value FROM captured_messages m JOIN runs r USING(run_id) WHERE r.workspace_id=?)", (workspace["workspace_id"], workspace["workspace_id"], workspace["workspace_id"])).fetchone()[0]
                result["activity"] = latest
        except (audit.AuditError, sqlite3.Error, OSError) as exc:
            result["diagnostics"] = [str(exc)]
            result["setup_required"] = False
        return result

    def overview(self):
        health = self.health()
        if not health["database_available"]:
            return {**health, "counts": {}, "attention": []}
        with self.read() as (connection, workspace):
            workspace_id = workspace["workspace_id"]
            state = index.status(connection, workspace_id)
            if 'index_milestone_projection' in audit.schema_tables(connection):
                milestones = audit.records(connection, "SELECT m.*,p.display_order,p.summary,p.acceptance_text,p.review_evidence,p.closure_state FROM index_milestones m LEFT JOIN index_milestone_projection p ON p.workspace_id=m.workspace_id AND p.milestone_id=m.milestone_id WHERE m.workspace_id=? AND m.lifecycle='active' ORDER BY COALESCE(p.display_order,2147483647),m.line,m.milestone_id", (workspace_id,))
            else:
                milestones = audit.records(connection, "SELECT * FROM index_milestones WHERE workspace_id=? AND lifecycle='active' ORDER BY line,milestone_id", (workspace_id,))
            tasks = audit.records(connection, "SELECT milestone_id,state,COUNT(*) AS count FROM index_tasks WHERE workspace_id=? GROUP BY milestone_id,state", (workspace_id,))
            counts = {"active milestones": len(milestones), "pending": 0, "in progress": 0, "blocked": 0, "completed": 0,
                      "history": 0, "archives": 0, "evolution": 0}
            for row in tasks:
                counts[row["state"].replace("_", " ")] = counts.get(row["state"].replace("_", " "), 0) + row["count"]
            for key, kind in (("history", "history_status"), ("archives", "context_archive")):
                counts[key] = connection.execute("SELECT COUNT(*) FROM index_documents WHERE workspace_id=? AND kind=?", (workspace_id, kind)).fetchone()[0]
            counts["evolution"] = connection.execute("SELECT COUNT(*) FROM index_documents WHERE workspace_id=? AND kind LIKE 'evolution_%'", (workspace_id,)).fetchone()[0]
            attention = [{"message": str(item), "kind": "diagnostic"} for item in state.get("diagnostics", [])]
            attention += [{"message": f"{row['count']} blocked task(s)", "kind": "blocked"} for row in tasks if row["state"] == "blocked"]
            unfinished = connection.execute("SELECT COUNT(*) FROM runs WHERE workspace_id=? AND completed_at IS NULL", (workspace_id,)).fetchone()[0]
            if unfinished:
                attention.append({"message": f"{unfinished} workflow run(s) have no terminal result", "kind": "unfinished"})
            for milestone in milestones:
                per = audit.records(connection, "SELECT state,COUNT(*) AS count FROM index_tasks WHERE workspace_id=? AND milestone_id=? GROUP BY state", (workspace_id, milestone["milestone_id"]))
                milestone["task_counts"] = ", ".join(f"{row['state']}: {row['count']}" for row in per)
            def cards(kind, pattern=False):
                operator = "LIKE" if pattern else "="
                rows = audit.records(connection, f"SELECT path,text,sha256 FROM index_documents WHERE workspace_id=? AND kind {operator} ? ORDER BY path", (workspace_id, kind))
                return [{'title': row['path'], 'summary': row['text'][:400],
                         'source': {'path': row['path'], 'sha256': row['sha256']}} for row in rows]
            active = []
            for milestone in milestones:
                states = audit.records(connection, "SELECT state,COUNT(*) AS count FROM index_tasks WHERE workspace_id=? AND milestone_id=? GROUP BY state", (workspace_id, milestone['milestone_id']))
                active.append({'milestone_id': milestone['milestone_id'], 'title': milestone['milestone_id'],
                               'summary': milestone.get('specification') or '',
                               'specification': milestone.get('specification') or '',
                               'counts': {row['state']: row['count'] for row in states},
                               'source': {'path': milestone['path'], 'line': milestone['line']}})
            return {**health, "counts": counts, "attention": attention, "milestones": milestones,
                    "active_milestones": active,
                    "history": cards('history_status'),
                    "archives": cards('context_archive'),
                    "evolution": cards('evolution_%', pattern=True),
                    "groups": {"history": counts["history"], "archives": counts["archives"], "evolution": counts["evolution"]}}

    def timeline(self, params):
        limit = min(int(params.get("limit", [50])[0]), MAX_PAGE)
        cursor = _decode_cursor(params["cursor"][0]) if params.get("cursor") else None
        operation = params.get("operation", [None])[0]
        outcome = params.get("outcome", [None])[0]
        search = (params.get("search", [""])[0] or "").strip().lower()
        if operation and operation not in audit.OPERATIONS:
            raise audit.AuditError("unknown operation")
        with self.read() as (connection, workspace):
            workspace_id = workspace["workspace_id"]
            clauses = ["r.workspace_id=?"]; values: list[Any] = [workspace_id]
            if operation: clauses.append("r.operation=?"); values.append(operation)
            if outcome and outcome != "unfinished": clauses.append("r.result=?"); values.append(outcome)
            if outcome == "unfinished": clauses.append("r.completed_at IS NULL")
            if search:
                clauses.append("(" + " OR ".join([
                    "instr(lower(coalesce(r.operation,'')),?)>0",
                    "instr(lower(coalesce(r.result,'')),?)>0",
                    "instr(lower(coalesce(r.git_head,'')),?)>0",
                    "instr(lower(coalesce(r.worktree_state,'')),?)>0",
                    "EXISTS (SELECT 1 FROM events e WHERE e.run_id=r.run_id AND (instr(lower(coalesce(e.event_type,'')),?)>0 OR instr(lower(coalesce(e.task_label,'')),?)>0 OR instr(lower(coalesce(e.details_json,'')),?)>0 OR instr(lower(coalesce(e.payload_json,'')),?)>0))",
                    "EXISTS (SELECT 1 FROM captured_messages m WHERE m.run_id=r.run_id AND (instr(lower(coalesce(m.role,'')),?)>0 OR instr(lower(m.text),?)>0))",
                ]) + ")")
                values.extend([search] * 10)
            if cursor:
                boundary = audit.time_bound(cursor["started_at"])
                key = audit.time_key("r.started_at")
                clauses.append(f"({key} < ? OR ({key} = ? AND r.run_id < ?))")
                values.extend([boundary, boundary, cursor["run_id"]])
            where = " AND ".join(clauses)
            rows = audit.records(connection, f"SELECT r.* FROM runs r WHERE {where} ORDER BY {audit.time_key('r.started_at')} DESC,r.run_id DESC LIMIT ?", (*values, limit + 1))
            more = len(rows) > limit; rows = rows[:limit]
            for row in rows:
                row["child_run_ids"] = [x[0] for x in connection.execute("SELECT run_id FROM runs WHERE parent_run_id=? ORDER BY run_id", (row["run_id"],))]
            next_cursor = _cursor({"started_at": rows[-1]["started_at"], "run_id": rows[-1]["run_id"]}) if more and rows else None
            return {"workspace_id": workspace_id, "results": rows, "runs": rows, "entries": rows, "limit": limit, "next_cursor": next_cursor,
                    "index": index.status(connection, workspace_id)}

    def run(self, run_id):
        with self.read() as (connection, workspace):
            row = audit.records(connection, "SELECT * FROM runs WHERE run_id=? AND workspace_id=?", (run_id, workspace["workspace_id"]))
            if not row: raise audit.AuditError("run is not part of this project")
            result = row[0]
            result["events"] = audit.query_events(connection, run_id, workspace_id=workspace["workspace_id"], limit=10000)
            if 'event_explorer' in audit.schema_tables(connection):
                for event in result["events"]:
                    explorer_rows = audit.records(connection, "SELECT * FROM event_explorer WHERE event_id=?", (event["event_id"],))
                    if explorer_rows:
                        event["explorer"] = explorer_rows[0]
                        event["explorer"]["message_refs"] = audit.records(connection, "SELECT * FROM event_message_refs WHERE event_id=? ORDER BY message_id", (event["event_id"],))
                        event["explorer"]["artifact_refs"] = audit.records(connection, "SELECT * FROM event_artifacts WHERE event_id=? ORDER BY namespace,identifier", (event["event_id"],))
            result["messages"] = audit.records(connection, "SELECT * FROM captured_messages WHERE run_id=? ORDER BY sequence", (run_id,))
            result["snapshot_observations"] = audit.records(connection, "SELECT * FROM run_snapshots WHERE run_id=? ORDER BY source_path", (run_id,))
            return {"run": result, "events": result.pop("events"), "messages": result.pop("messages"), "snapshot_observations": result.pop("snapshot_observations")}

    def _live_validation(self, connection, workspace_id):
        diagnostics = []
        try:
            paths = index.inventory(self.project)
            current = {path: index.read_document(self.project, path)[1] for path in paths}
            indexed = {row["path"]: row["sha256"] for row in audit.records(connection, "SELECT path,sha256 FROM index_documents WHERE workspace_id=?", (workspace_id,))}
            for path in sorted(set(current) | set(indexed)):
                if current.get(path) != indexed.get(path): diagnostics.append(f"source changed since refresh: {path}")
        except (audit.AuditError, OSError, UnicodeError) as exc:
            diagnostics.append(str(exc))
        return {"valid": not diagnostics, "diagnostics": diagnostics}

    def todo(self):
        with self.read() as (connection, workspace):
            workspace_id = workspace["workspace_id"]
            readiness = index.readiness(connection, workspace_id, self.project)
            validation = {'valid': readiness['source_freshness'] == 'current' and not readiness['needs_review'],
                          'diagnostics': readiness.get('freshness_diagnostics', [])}
            def flatten(items):
                result = []
                for item in items:
                    task = dict(item.get('task', item))
                    if item.get('reason'):
                        task['reason'] = item['reason']
                    result.append(task)
                return result
            buckets = {
                'resume': flatten(readiness['resume']), 'ready': flatten(readiness['ready']),
                'waiting': flatten(readiness['waiting']), 'blocked': flatten(readiness['blocked']),
                'needs_review': flatten(readiness['needs_review']),
            }
            groups = ([{'label': key.replace('_', ' ').title(), 'tasks': value} for key, value in buckets.items()]
                      if validation['valid'] else [])
            return {'workspace_id': workspace_id, 'validation': validation,
                    'validated': validation['valid'],
                    'recommendations_available': bool(readiness['recommendations']),
                    'validation_reason': '; '.join(validation['diagnostics']) if validation['diagnostics'] else None,
                    **buckets, 'groups': groups, 'index': readiness['index']}

    def follow_up(self, payload):
        action = payload.get('action', 'continue')
        if action not in {'continue', 'investigate', 'review', 'clarify'}:
            raise audit.AuditError('unknown follow-up action')
        with self.read() as (connection, workspace):
            workspace_id = workspace['workspace_id']
            readiness = index.readiness(connection, workspace_id, self.project)
            if readiness['source_freshness'] != 'current' or (readiness['needs_review'] and action != 'review'):
                raise audit.AuditError('follow-up requires a current, review-free index; refresh and resolve diagnostics first')
            explicit, label, milestone = payload.get('task_id'), payload.get('task_label'), payload.get('milestone_id')
            item = None
            if explicit or label:
                rows = audit.records(connection, 'SELECT * FROM index_tasks WHERE workspace_id=? AND (? IS NULL OR explicit_id=?) AND (? IS NULL OR label=?) AND (? IS NULL OR milestone_id=?)', (workspace_id, explicit, explicit, label, label, milestone, milestone))
                if len(rows) != 1:
                    raise audit.AuditError('follow-up task is missing or ambiguous')
                item = rows[0]
            elif payload.get('path'):
                item = {'path': _safe_relative(str(payload['path'])), 'line': payload.get('line')}
            elif action == 'review' and milestone:
                rows = audit.records(connection, 'SELECT * FROM index_milestones WHERE workspace_id=? AND milestone_id=?', (workspace_id, milestone))
                if len(rows) != 1:
                    raise audit.AuditError('review milestone is missing or ambiguous')
                item = rows[0]
            else:
                raise audit.AuditError('follow-up needs a task or declared source path')
            if action == 'review':
                review_milestones = {entry.get('milestone_id') for entry in readiness['needs_review'] if entry.get('milestone_id')}
                review_milestones.update(milestone for entry in readiness['needs_review'] for milestone in entry.get('milestone_ids', []))
                if item.get('milestone_id') not in review_milestones:
                    raise audit.AuditError('review follow-up requires a milestone with recorded review evidence')
            source_ref = payload.get('source')
            if source_ref is not None and not isinstance(source_ref, dict):
                raise audit.AuditError('follow-up source must be an object')
            if item.get('milestone_id'):
                task_key = item.get('explicit_id') or f"{item['path']}#{item['line']}"
                buckets = {
                    'continue': {x['task']['task_key'] for x in readiness['resume'] + readiness['ready']},
                    'investigate': {x['task']['task_key'] for x in readiness['blocked']},
                    'clarify': {x['task']['task_key'] for x in readiness['waiting']},
                    'review': set(),
                }
                if action != 'review' and task_key not in buckets[action]:
                    raise audit.AuditError(f'follow-up action is not valid for the current task state: {action}')
            elif action != 'continue':
                raise audit.AuditError('a task is required for this follow-up action')
            if source_ref:
                if source_ref.get('path') != item['path']:
                    raise audit.AuditError('follow-up source is not the selected task source')
                if source_ref.get('line') is not None and source_ref.get('line') != item.get('line'):
                    raise audit.AuditError('follow-up source line is not the selected task line')
                if source_ref.get('sha256') and source_ref['sha256'] != item.get('sha256'):
                    raise audit.AuditError('follow-up source hash is stale')
            known = connection.execute('SELECT 1 FROM index_documents WHERE workspace_id=? AND path=?', (workspace_id, item['path'])).fetchone()
            if not known:
                raise audit.AuditError('follow-up source is not a declared indexed document')
            text, digest, _ = index.read_document(self.project, item['path'])
            line = item.get('line')
            if line is not None:
                try:
                    line = int(line)
                except (TypeError, ValueError) as exc:
                    raise audit.AuditError('follow-up source line must be an integer') from exc
                if line < 1 or line > len(text.splitlines()):
                    raise audit.AuditError('follow-up source line is outside the current document')
                item['line'] = line
            source = {'path': item['path'], 'line': item.get('line'), 'sha256': digest}
            verbs = {'continue': 'Continue', 'investigate': 'Investigate', 'review': 'Review', 'clarify': 'Clarify'}
            prompt = f"{verbs[action]} the current Tabilet task. Reread AGENTS.md and the live source before acting. Inspect {source['path']}"
            if source.get('line'):
                prompt += f":{source['line']}"
            prompt += "."
            return {'action': action, 'prompt': prompt, 'source': source,
                    'validation_note': 'Prepared from the current source hash. Copying this prompt does not execute work.'}

    def _partition_pending(self, connection, workspace_id, tasks):
        # Dependencies are currently indexed at milestone level. Keep the
        # explanation explicit and conservative until task-level dependency
        # fields are available from the SQL9 projection.
        dependencies = audit.records(connection, "SELECT source,relation,target,line,path FROM index_relationships WHERE workspace_id=? AND relation='depends_on'", (workspace_id,))
        waiting = []
        blocked_milestones = set()
        for relation in dependencies:
            target = relation["target"].removeprefix("milestone:")
            if connection.execute("SELECT 1 FROM index_tasks WHERE workspace_id=? AND milestone_id=? AND state IN ('pending','in_progress','blocked') LIMIT 1", (workspace_id, target)).fetchone():
                blocked_milestones.add(relation["source"].removeprefix("milestone:"))
        ready = []
        for task in tasks:
            if task["milestone_id"] in blocked_milestones:
                task = dict(task); task["waiting_for"] = sorted(blocked_milestones); waiting.append(task)
            else:
                ready.append(task)
        return ready, waiting

    def search(self, params):
        query = params.get("q", params.get("query", [""]))[0]
        limit = min(int(params.get("limit", [50])[0]), MAX_PAGE)
        offset = max(0, int(params.get("offset", [0])[0]))
        with self.read() as (connection, workspace):
            return index.search(connection, workspace["workspace_id"], query, kind=params.get("kind", [None])[0], milestone_id=params.get("milestone", [None])[0], state=params.get("state", [None])[0], limit=limit, offset=offset)

    def document(self, params):
        relative = _safe_relative(params.get("path", [""])[0])
        live = params.get("live", ["0"])[0] == "1"
        with self.read() as (connection, workspace):
            known = connection.execute("SELECT 1 FROM index_documents WHERE workspace_id=? AND path=?", (workspace["workspace_id"], relative)).fetchone()
            if not known: raise audit.AuditError("document is not a declared source in this project")
            if live:
                paths = index.inventory(self.project)
                if relative not in paths: raise audit.AuditError("document is no longer a declared source")
                text, digest, info = index.read_document(self.project, relative)
                return {"source": "live", "path": relative, "sha256": digest, "mtime_ns": info.st_mtime_ns, "text": text, "index": index.status(connection, workspace["workspace_id"])}
            return {"source": "indexed", **index.show(connection, workspace["workspace_id"], relative)}

    def refresh(self, rebuild=False, literal=False):
        if not self.refresh_lock.acquire(blocking=False): raise audit.AuditError("refresh already in progress")
        try:
            if not self.project.is_dir(): raise audit.AuditError("project must be an existing directory")
            index.layout_check(self.project)
            connection = audit.open_database(self.database, project_roots=[self.project])
            try:
                return index.sync(connection, self.project, rebuild=rebuild, force_literal=literal)
            finally:
                connection.close()
        finally:
            self.refresh_lock.release()


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "TabiletExplorer/1"

    @property
    def app(self) -> ExplorerApp:
        return self.server.app  # type: ignore[attr-defined]

    def log_message(self, format, *args):
        # Never log request URLs: they may contain user-provided search terms.
        return

    def _host_ok(self):
        host = self.headers.get("Host", "").split(":", 1)[0].strip("[]").lower()
        allowed = {"localhost", "127.0.0.1", "::1", self.server.server_address[0].strip("[]").lower()}  # type: ignore[attr-defined]
        if host not in allowed: return False
        origin = self.headers.get("Origin")
        if origin:
            parsed = urllib.parse.urlsplit(origin)
            expected = f"{parsed.scheme}://{self.headers.get('Host')}"
            if parsed.hostname not in allowed or origin.rstrip("/") != expected.rstrip("/"): return False
        return True

    def _auth(self, api=False, post=False):
        if not self._host_ok(): return False
        supplied = self.headers.get("X-Tabilet-Token", "")
        if not supplied:
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            supplied = urllib.parse.unquote(cookies.get("tabilet_token").value) if cookies.get("tabilet_token") else ""
        if api and not secrets.compare_digest(supplied, self.app.token): return False
        if post and self.headers.get("Origin") is None: return False
        return True

    def _send(self, status, value, content_type="application/json", cookie=None):
        body = value if isinstance(value, bytes) else (_json(value).encode("utf-8") if content_type == "application/json" else str(value).encode("utf-8"))
        self.send_response(status); self.send_header("Content-Type", content_type + "; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
        if cookie: self.send_header("Set-Cookie", cookie)
        self.end_headers(); self.wfile.write(body)

    def _error(self, status, exc): self._send(status, {"error": str(exc), "type": type(exc).__name__})

    def _asset(self, name):
        for directory in (ASSET_DIR, INSTALLED_ASSET_DIR):
            try:
                return (directory / name).read_bytes()
            except (OSError, ValueError):
                continue
        raise audit.AuditError("missing explorer asset: " + name)

    def do_GET(self):
        if not self._host_ok(): self._error(403, audit.AuditError("host is not allowed")); return
        parsed = urllib.parse.urlsplit(self.path); path = parsed.path; params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        if path.startswith("/api/") and not self._auth(api=True): self._error(401, audit.AuditError("missing or invalid explorer token")); return
        try:
            if path == "/":
                shell = self._asset("index.html").decode("utf-8")
                shell = shell.replace('href="explorer.css"', 'href="/assets/explorer.css"').replace('src="explorer.js"', 'src="/assets/explorer.js"')
                if 'name="tabilet-token"' not in shell:
                    shell = shell.replace('<head>', '<head><meta name="tabilet-token" content="' + html.escape(self.app.token, quote=True) + '">', 1)
                self._send(200, shell, "text/html", "tabilet_token=" + urllib.parse.quote(self.app.token, safe="") + "; Path=/; SameSite=Strict")
            elif path == "/assets/explorer.css": self._send(200, self._asset("explorer.css"), "text/css")
            elif path == "/assets/explorer.js": self._send(200, self._asset("explorer.js"), "text/javascript")
            elif path == "/api/health": self._send(200, self.app.health())
            elif path == "/api/overview": self._send(200, self.app.overview())
            elif path == "/api/timeline": self._send(200, self.app.timeline(params))
            elif path.startswith("/api/runs/"): self._send(200, self.app.run(urllib.parse.unquote(path.removeprefix("/api/runs/"))))
            elif path == "/api/todo": self._send(200, self.app.todo())
            elif path == "/api/search": self._send(200, self.app.search(params))
            elif path == "/api/document": self._send(200, self.app.document(params))
            else: self._error(404, audit.AuditError("unknown explorer route"))
        except (audit.AuditError, sqlite3.Error, OSError, ValueError, TypeError) as exc: self._error(400 if isinstance(exc, (audit.AuditError, ValueError, TypeError)) else 503, exc)

    def do_POST(self):
        if not self._auth(api=True, post=True): self._error(403, audit.AuditError("same-origin authenticated POST required")); return
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path not in ("/api/refresh", "/api/follow-up"): self._error(404, audit.AuditError("unknown explorer route")); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > MAX_BODY: raise audit.AuditError("request body is too large")
            raw = self.rfile.read(length); payload = json.loads(raw or b"{}")
            if not isinstance(payload, dict): raise audit.AuditError("request body must be a JSON object")
            if parsed.path == "/api/refresh": self._send(200, self.app.refresh(bool(payload.get("rebuild")), bool(payload.get("literal"))))
            else:
                line = payload.get("line")
                if line is not None and not isinstance(line, int): raise audit.AuditError("line must be an integer")
                if line is not None: payload['line'] = line
                self._send(200, self.app.follow_up(payload))
        except (audit.AuditError, sqlite3.Error, OSError, ValueError, TypeError, json.JSONDecodeError) as exc: self._error(400, exc)


class ExplorerServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, app):
        self.app = app
        super().__init__(address, Handler)


def serve(project, database=None, host="127.0.0.1", port=8000):
    app = ExplorerApp(pathlib.Path(project), pathlib.Path(database or audit.default_database_path()))
    try:
        server = ExplorerServer((host, port), app)
    except OSError as exc:
        raise audit.AuditError(f"cannot bind explorer to {host}:{port}: {exc}") from exc
    url_host = "localhost" if host in ("127.0.0.1", "::1") else host
    print(f"Tabilet Explorer: http://{url_host}:{server.server_address[1]}/", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        return 0
    finally:
        server.shutdown(); server.server_close()
    return 0

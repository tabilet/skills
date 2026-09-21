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
from typing import Any

import tabilet_audit as audit
import tabilet_index as index


MAX_BODY = 64 * 1024
MAX_PAGE = 100
POLL_SECONDS = 5


HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tabilet Explorer</title><meta name="tabilet-token" content="__TOKEN__"><link rel="stylesheet" href="/assets/explorer.css"></head>
<body><header><a class="brand" href="#overview">Tabilet Explorer</a><span id="project"></span><span id="branch"></span><span id="health" role="status"></span>
<label class="search"><span class="sr-only">Search</span><input id="search" type="search" placeholder="Search project"></label></header>
<nav aria-label="Primary"><a href="#overview" data-view="overview">Overview</a><a href="#timeline" data-view="timeline">Timeline</a><a href="#todo" data-view="todo">To-do</a></nav>
<main id="app" tabindex="-1"><p>Loading project…</p></main>
<script src="/assets/explorer.js" defer></script></body></html>"""


CSS = r"""*{box-sizing:border-box}body{margin:0;font:16px system-ui,sans-serif;color:#222;background:#f7f7f7}header{display:flex;gap:1rem;align-items:center;padding:1rem 5vw;background:#fff;border-bottom:1px solid #ddd;flex-wrap:wrap}.brand{font-weight:700;color:#174f75;text-decoration:none}.search{margin-left:auto}.search input{width:min(32rem,80vw);padding:.5rem;border:1px solid #999;border-radius:4px}nav{display:flex;gap:.25rem;padding:.5rem 5vw;background:#fff;border-bottom:1px solid #ddd}nav a{padding:.55rem .9rem;color:#174f75;text-decoration:none;border-radius:4px}nav a[aria-current=true]{background:#e6f1f8;font-weight:600}main{max-width:1200px;margin:1.25rem auto;padding:0 1rem}section,article{background:#fff;border:1px solid #ddd;border-radius:6px;padding:1rem;margin-bottom:1rem}h1,h2,h3{margin-top:0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:.75rem}.card{border:1px solid #ddd;border-radius:5px;padding:.75rem}.number{font-size:1.7rem;font-weight:700}.muted{color:#666}.error{color:#8a1d1d;background:#fff1f1;padding:.75rem;border-radius:4px}.warning{color:#674c00;background:#fff8db;padding:.75rem;border-radius:4px}.row{display:flex;gap:1rem;align-items:baseline;border-top:1px solid #eee;padding:.8rem 0;flex-wrap:wrap}.row:first-child{border-top:0}.row button,.row a{font:inherit;color:#174f75;background:none;border:0;text-decoration:underline;cursor:pointer;padding:0}.tag{display:inline-block;padding:.15rem .4rem;border-radius:4px;background:#eee;font-size:.85rem}.tag.blocked{background:#ffe0e0}.tag.completed{background:#e3f4e3}.tag.in_progress{background:#e3efff}.detail{white-space:pre-wrap;background:#f4f4f4;padding:.75rem;overflow:auto}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}:focus-visible{outline:3px solid #1769aa;outline-offset:2px}@media(max-width:600px){header,nav{padding-left:1rem;padding-right:1rem}main{margin-top:.75rem;padding:0 .65rem}.search{width:100%;margin:0}.search input{width:100%}}"""


JS = r"""(() => {
  const token = document.querySelector('meta[name="tabilet-token"]').content;
  const app = document.getElementById('app');
  const state = {view: location.hash.slice(1) || 'overview', timer: null};
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const stamp = value => value ? `<time datetime="${esc(value)}">${esc(new Date(value).toLocaleString())}</time>` : '<span class="muted">not recorded</span>';
  async function api(path, options={}) { const response = await fetch(path, {headers:{'X-Tabilet-Token': token, ...(options.headers||{})}, ...options}); const data = await response.json(); if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`); return data; }
  function nav() { document.querySelectorAll('[data-view]').forEach(a => a.setAttribute('aria-current', a.dataset.view === state.view ? 'true' : 'false')); }
  function runRow(run) { return `<div class="row"><button data-run="${esc(run.run_id)}"><strong>${esc(run.operation)}</strong></button><span class="tag ${esc(run.result || 'unknown')}">${esc(run.result || 'unfinished')}</span><span>${stamp(run.started_at)}</span><span class="muted">${esc(run.run_id)}</span></div>`; }
  function taskRow(task) { return `<div class="row"><span class="tag ${esc(task.state)}">${esc(task.state)}</span><strong>${esc(task.label)}</strong><span class="muted">${esc(task.milestone_id)} · ${esc(task.path)}:${esc(task.line)}</span></div>`; }
  async function renderOverview() { const data = await api('/api/overview'); document.getElementById('project').textContent = data.project_root || ''; document.getElementById('branch').textContent = data.branch ? `(${data.branch})` : ''; document.getElementById('health').textContent = data.index?.refreshed_at ? `refreshed ${new Date(data.index.refreshed_at).toLocaleString()}` : ''; if (data.setup_required) { app.innerHTML = `<section><h1>Set up this project</h1><p>No external audit/index database is available.</p><button id="refresh">Create index</button></section>`; bindRefresh(); return; } app.innerHTML = `<h1>Overview</h1><section><div class="cards">${Object.entries(data.counts||{}).map(([key,value]) => `<div class="card"><div class="muted">${esc(key)}</div><div class="number">${esc(value)}</div></div>`).join('')}</div></section><section><h2>Attention</h2>${(data.attention||[]).map(x => `<p class="warning">${esc(x.message || x)}</p>`).join('') || '<p class="muted">Nothing requires attention.</p>'}</section><section><h2>Active milestones</h2>${(data.milestones||[]).map(m => `<article><h3>${esc(m.milestone_id)}</h3><p>${esc(m.specification || '')}</p><p>${esc(m.task_counts || '')}</p></article>`).join('') || '<p class="muted">No active milestones are indexed.</p>'}</section>`; bindRuns(); }
  async function renderTimeline() { const data = await api('/api/timeline?limit=50'); app.innerHTML = `<h1>Timeline</h1><section>${(data.results||[]).map(runRow).join('') || '<p class="muted">No recorded workflow entries.</p>'}<button id="more" ${data.next_cursor?'':'hidden'}>Load more</button></section>`; document.querySelector('#more')?.addEventListener('click', async () => { const more=await api(`/api/timeline?limit=50&cursor=${encodeURIComponent(data.next_cursor)}`); document.querySelector('#more').insertAdjacentHTML('beforebegin', more.results.map(runRow).join('')); document.querySelector('#more').hidden=!more.next_cursor; }); bindRuns(); }
  async function renderTodo() { const data = await api('/api/todo'); const validation = data.validation?.valid ? '' : `<p class="warning">${esc((data.validation?.diagnostics||[]).join('; ') || 'Live sources need refresh or review.')}</p>`; app.innerHTML = `<h1>To-do</h1><section>${validation}${(data.groups||[]).map(group => `<h2>${esc(group.label)}</h2>${(group.tasks||[]).map(taskRow).join('') || '<p class="muted">None.</p>'}`).join('') || '<p class="muted">Recommendations are unavailable until the current sources validate.</p>'}</section>`; }
  async function detail(run) { const data=await api(`/api/runs/${encodeURIComponent(run)}`); app.innerHTML = `<p><a href="#timeline">← Timeline</a></p><article><h1>${esc(data.run.operation)} <span class="tag">${esc(data.run.result || 'unfinished')}</span></h1><p>${stamp(data.run.started_at)} · ${esc(data.run.run_id)}</p><h2>Messages</h2>${(data.messages||[]).map(m => `<section><strong>${esc(m.role)}</strong> <span class="tag">${esc(m.fidelity)}</span><div class="detail">${esc(m.text)}</div></section>`).join('') || '<p class="muted">Request text was not captured.</p>'}<h2>Observed activity</h2>${(data.events||[]).map(e => `<section><strong>${esc(e.event_type)}</strong><p>${esc(e.task_label || e.milestone_id || '')}</p><div class="detail">${esc(e.details_json || '')}</div></section>`).join('') || '<p class="muted">No event details were recorded.</p>'}</article>`; }
  function bindRuns() { document.querySelectorAll('[data-run]').forEach(b => b.addEventListener('click', () => detail(b.dataset.run))); }
  function bindRefresh() { document.getElementById('refresh')?.addEventListener('click', async () => { const button=document.getElementById('refresh'); button.disabled=true; button.textContent='Refreshing…'; try { await api('/api/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}); await render(); } catch(e) { app.insertAdjacentHTML('afterbegin',`<p class="error">${esc(e.message)}</p>`); button.disabled=false; button.textContent='Retry'; } }); }
  async function render() { nav(); try { if (state.view === 'timeline') await renderTimeline(); else if (state.view === 'todo') await renderTodo(); else await renderOverview(); } catch(e) { app.innerHTML=`<section class="error"><h1>Explorer error</h1><p>${esc(e.message)}</p></section>`; } }
  window.addEventListener('hashchange', () => { state.view=location.hash.slice(1)||'overview'; render(); });
  document.getElementById('search').addEventListener('keydown', e => { if(e.key==='Enter' && e.target.value) location.hash='search'; });
  document.addEventListener('visibilitychange', () => { if(document.hidden) { clearInterval(state.timer); state.timer=null; } else if(!state.timer) state.timer=setInterval(() => api('/api/health').catch(()=>{}), 5000); });
  render(); state.timer=setInterval(() => { if(!document.hidden) api('/api/health').catch(()=>{}); }, 5000);
})();"""


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
                  "setup_required": not self.database.is_file(), "index": None, "diagnostics": []}
        if not self.database.is_file():
            return result
        try:
            with self.read() as (connection, workspace):
                result.update({"database_available": True, "workspace_id": workspace["workspace_id"], "branch": workspace.get("branch")})
                result["index"] = index.status(connection, workspace["workspace_id"])
                result["diagnostics"] = result["index"].get("diagnostics", [])
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
            milestones = audit.records(connection, "SELECT * FROM index_milestones WHERE workspace_id=? AND lifecycle='active' ORDER BY line,milestone_id", (workspace_id,))
            tasks = audit.records(connection, "SELECT milestone_id,state,COUNT(*) AS count FROM index_tasks WHERE workspace_id=? GROUP BY milestone_id,state", (workspace_id,))
            counts = {"active milestones": len(milestones), "pending": 0, "in progress": 0, "blocked": 0, "completed": 0,
                      "history": 0, "archives": 0, "evolution": 0}
            for row in tasks:
                counts[row["state"].replace("_", " ")] = counts.get(row["state"].replace("_", " "), 0) + row["count"]
            for key, kind in (("history", "history_status"), ("archives", "context_archive"), ("evolution", "evolution_prompt")):
                counts[key] = connection.execute("SELECT COUNT(*) FROM index_documents WHERE workspace_id=? AND kind=?", (workspace_id, kind)).fetchone()[0]
            attention = [{"message": str(item), "kind": "diagnostic"} for item in state.get("diagnostics", [])]
            attention += [{"message": f"{row['count']} blocked task(s)", "kind": "blocked"} for row in tasks if row["state"] == "blocked"]
            unfinished = connection.execute("SELECT COUNT(*) FROM runs WHERE workspace_id=? AND completed_at IS NULL", (workspace_id,)).fetchone()[0]
            if unfinished:
                attention.append({"message": f"{unfinished} workflow run(s) have no terminal result", "kind": "unfinished"})
            for milestone in milestones:
                per = audit.records(connection, "SELECT state,COUNT(*) AS count FROM index_tasks WHERE workspace_id=? AND milestone_id=? GROUP BY state", (workspace_id, milestone["milestone_id"]))
                milestone["task_counts"] = ", ".join(f"{row['state']}: {row['count']}" for row in per)
            return {**health, "counts": counts, "attention": attention, "milestones": milestones,
                    "groups": {"history": counts["history"], "archives": counts["archives"], "evolution": counts["evolution"]}}

    def timeline(self, params):
        limit = min(int(params.get("limit", [50])[0]), MAX_PAGE)
        cursor = _decode_cursor(params["cursor"][0]) if params.get("cursor") else None
        operation = params.get("operation", [None])[0]
        if operation and operation not in audit.OPERATIONS:
            raise audit.AuditError("unknown operation")
        with self.read() as (connection, workspace):
            workspace_id = workspace["workspace_id"]
            clauses = ["r.workspace_id=?"]; values: list[Any] = [workspace_id]
            if operation: clauses.append("r.operation=?"); values.append(operation)
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
            return {"workspace_id": workspace_id, "results": rows, "limit": limit, "next_cursor": next_cursor,
                    "index": index.status(connection, workspace_id)}

    def run(self, run_id):
        with self.read() as (connection, workspace):
            row = audit.records(connection, "SELECT * FROM runs WHERE run_id=? AND workspace_id=?", (run_id, workspace["workspace_id"]))
            if not row: raise audit.AuditError("run is not part of this project")
            result = row[0]
            result["events"] = audit.query_events(connection, run_id, workspace_id=workspace["workspace_id"], limit=10000)
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
            validation = self._live_validation(connection, workspace_id)
            if not validation["valid"]:
                return {"workspace_id": workspace_id, "validation": validation, "groups": [], "index": index.status(connection, workspace_id)}
            tasks = audit.records(connection, "SELECT * FROM index_tasks WHERE workspace_id=? ORDER BY milestone_id,line", (workspace_id,))
            groups = []
            for state, label in (("in_progress", "Resume"), ("blocked", "Blocked"), ("cancelled", "Cancelled"), ("historical", "Historical"), ("completed", "Completed")):
                groups.append({"label": label, "tasks": [task for task in tasks if task["state"] == state]})
            ready, waiting = self._partition_pending(connection, workspace_id, [task for task in tasks if task["state"] == "pending"])
            groups.insert(1, {"label": "Ready", "tasks": ready})
            groups.insert(2, {"label": "Waiting", "tasks": waiting})
            return {"workspace_id": workspace_id, "validation": validation, "groups": groups, "index": index.status(connection, workspace_id)}

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
        if api and not secrets.compare_digest(self.headers.get("X-Tabilet-Token", ""), self.app.token): return False
        if post and self.headers.get("Origin") is None: return False
        return True

    def _send(self, status, value, content_type="application/json"):
        body = value if isinstance(value, bytes) else (_json(value).encode("utf-8") if content_type == "application/json" else str(value).encode("utf-8"))
        self.send_response(status); self.send_header("Content-Type", content_type + "; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

    def _error(self, status, exc): self._send(status, {"error": str(exc), "type": type(exc).__name__})

    def do_GET(self):
        if not self._host_ok(): self._error(403, audit.AuditError("host is not allowed")); return
        parsed = urllib.parse.urlsplit(self.path); path = parsed.path; params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        if path.startswith("/api/") and not self._auth(api=True): self._error(401, audit.AuditError("missing or invalid explorer token")); return
        try:
            if path == "/": self._send(200, HTML.replace("__TOKEN__", html.escape(self.app.token, quote=True)), "text/html")
            elif path == "/assets/explorer.css": self._send(200, CSS, "text/css")
            elif path == "/assets/explorer.js": self._send(200, JS, "text/javascript")
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
                result = self.app.document({"path": [str(payload.get("path", ""))], "live": ["1"]})
                line = payload.get("line")
                if line is not None and not isinstance(line, int): raise audit.AuditError("line must be an integer")
                self._send(200, {"prompt": f"Continue the task at {result['path']}" + (f":{line}" if line else "") + ". Reread current project instructions and verify the live task state before editing.", "source": result})
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

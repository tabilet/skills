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
import html
import http.server
import ipaddress
import json
import pathlib
import re
import secrets
import socket
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
TODO_GROUPS = ('resume', 'ready', 'waiting', 'blocked', 'needs_review')
ASSET_DIR = pathlib.Path(__file__).with_name("explorer")
INSTALLED_ASSET_DIR = pathlib.Path.home() / ".local" / "share" / "tabilet" / "explorer"


def _json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except ValueError as exc:
        raise audit.AuditError("JSON values must be finite") from exc


def _cursor(value: dict[str, str]) -> str:
    raw = _json(value).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(value: str) -> dict[str, str]:
    if len(value) > 512:
        raise audit.AuditError("cursor is too long")
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        result = audit.strict_json_loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise audit.AuditError("invalid timeline cursor") from exc
    if not isinstance(result, dict) or not isinstance(result.get("started_at"), str) or not isinstance(result.get("run_id"), str):
        raise audit.AuditError("invalid timeline cursor")
    if result.get('direction', 'next') not in {'next', 'previous'}:
        raise audit.AuditError('invalid timeline cursor direction')
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

    def _health(self, connection, workspace):
        result = {"project_root": str(self.project), "database": str(self.database), "database_available": False,
                  "setup_required": False, "index": None, "diagnostics": [], "activity": None}
        workspace_id = workspace["workspace_id"]
        result.update({"database_available": True, "workspace_id": workspace_id,
                       "branch": workspace.get("branch")})
        result["index"] = index.status(connection, workspace_id)
        result["diagnostics"] = result["index"].get("diagnostics", [])
        result["project"] = {"name": self.project.name, "project_root": str(self.project),
                             "branch": workspace.get("branch") or result["index"].get("branch"),
                             "git_head": result["index"].get("git_head")}
        time = audit.time_key("value")
        latest = connection.execute(f"""
            SELECT value FROM (
                SELECT started_at AS value FROM runs WHERE workspace_id=?
                UNION ALL
                SELECT e.recorded_at FROM events e JOIN runs r USING(run_id) WHERE r.workspace_id=?
                UNION ALL
                SELECT m.captured_at FROM captured_messages m JOIN runs r USING(run_id) WHERE r.workspace_id=?
            ) ORDER BY {time} DESC LIMIT 1
        """, (workspace_id, workspace_id, workspace_id)).fetchone()
        result["activity"] = latest[0] if latest else None
        return result

    def health(self):
        result = {"project_root": str(self.project), "database": str(self.database), "database_available": False,
                  "setup_required": not self.database.is_file(), "index": None, "diagnostics": [], "activity": None}
        if not self.database.is_file():
            return result
        try:
            with self.read() as (connection, workspace):
                return self._health(connection, workspace)
        except (audit.AuditError, sqlite3.Error, OSError) as exc:
            result["diagnostics"] = [str(exc)]
            result["setup_required"] = False
        return result

    def overview(self):
        if not self.database.is_file():
            return {**self.health(), "counts": {}, "attention": [], "active_milestones": [],
                    "history": [], "archives": [], "evolution": []}
        with self.read() as (connection, workspace):
            health = self._health(connection, workspace)
            workspace_id = workspace["workspace_id"]
            state = index.status(connection, workspace_id)
            tables = set(audit.schema_tables(connection))
            required = {'index_documents', 'index_milestones', 'index_tasks'}
            if not required.issubset(tables):
                diagnostic = state.get('diagnostic') or 'index requires explicit refresh before project summaries are available'
                return {**health, "counts": {"audit runs": connection.execute(
                            "SELECT COUNT(*) FROM runs WHERE workspace_id=?", (workspace_id,)).fetchone()[0]},
                        "attention": [{"message": diagnostic, "kind": "migration"}],
                        "active_milestones": [], "history": [], "archives": [],
                        "evolution": [], "history_groups": {}, "archive_groups": {}, "evolution_pairs": []}
            projection = 'index_milestone_projection' in tables
            projection_join = ("LEFT JOIN index_milestone_projection p ON p.workspace_id=m.workspace_id "
                               "AND p.milestone_id=m.milestone_id") if projection else ""
            projection_fields = (",p.display_order,p.summary,p.acceptance_text,p.review_evidence,p.closure_state"
                                 if projection else ",NULL AS display_order,NULL AS summary,NULL AS acceptance_text,NULL AS review_evidence,NULL AS closure_state")
            milestones = audit.records(connection, f"SELECT m.*{projection_fields} FROM index_milestones m {projection_join} WHERE m.workspace_id=? AND m.lifecycle='active' ORDER BY COALESCE(p.display_order,2147483647),m.line,m.milestone_id" if projection else f"SELECT m.*{projection_fields} FROM index_milestones m WHERE m.workspace_id=? AND m.lifecycle='active' ORDER BY m.line,m.milestone_id", (workspace_id,))
            tasks = audit.records(connection, """
                SELECT t.milestone_id,t.state,COUNT(*) AS count
                FROM index_tasks t JOIN index_milestones m
                  ON m.workspace_id=t.workspace_id AND m.milestone_id=t.milestone_id
                WHERE t.workspace_id=? AND m.lifecycle='active'
                GROUP BY t.milestone_id,t.state
            """, (workspace_id,))
            counts = {"active milestones": len(milestones), "pending": 0,
                      "in progress": 0, "blocked": 0, "completed": 0,
                      "cancelled": 0, "historical": 0, "history": 0,
                      "archives": 0, "evolution": 0}
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
            readiness = index.readiness(connection, workspace_id, self.project)
            for item in readiness['needs_review']:
                attention.append({'message': item['reason'], 'kind': 'review',
                                  'milestone_id': item.get('milestone_id'), 'source': item.get('source')})
            for item in readiness['waiting']:
                attention.append({'message': item['reason'], 'kind': 'dependency',
                                  'milestone_id': item['task']['milestone_id'], 'source': item['task']['source']})
            documents = {row['path']: row for row in audit.records(
                connection, "SELECT path,kind,text,sha256 FROM index_documents WHERE workspace_id=? ORDER BY path", (workspace_id,))}
            product = documents.get('tabilet/memory-bank/product.md')
            project_summary = None
            if product:
                project_summary = next((line.strip() for line in product['text'].splitlines()
                                        if line.strip() and not line.startswith('#')), None)
            active = []
            for milestone in milestones:
                states = audit.records(connection, "SELECT state,COUNT(*) AS count FROM index_tasks WHERE workspace_id=? AND milestone_id=? GROUP BY state", (workspace_id, milestone['milestone_id']))
                current_tasks = audit.records(connection, "SELECT explicit_id,label,state,notes,path,line,sha256 FROM index_tasks WHERE workspace_id=? AND milestone_id=? AND state IN ('pending','in_progress','blocked') ORDER BY CASE state WHEN 'in_progress' THEN 0 WHEN 'blocked' THEN 1 ELSE 2 END,line LIMIT 3", (workspace_id, milestone['milestone_id']))
                for task in current_tasks:
                    task['source'] = {'path': task['path'], 'line': task['line'], 'sha256': task['sha256']}
                active.append({'milestone_id': milestone['milestone_id'], 'title': milestone['milestone_id'],
                               'summary': milestone.get('summary'),
                               'specification': milestone.get('specification') or '',
                               'acceptance': milestone.get('acceptance_text'),
                               'review_evidence': milestone.get('review_evidence'),
                               'counts': {row['state']: row['count'] for row in states},
                               'tasks': current_tasks, 'tasks_truncated': sum(row['count'] for row in states if row['state'] in {'pending','in_progress','blocked'}) > len(current_tasks),
                               'source': {'path': milestone['path'], 'line': milestone['line']}})
            retired = audit.records(connection, "SELECT milestone_id,outcome,path,line,specification,review FROM index_milestones WHERE workspace_id=? AND lifecycle='retired' ORDER BY milestone_id", (workspace_id,))
            history = []
            history_groups = {'completed': [], 'cancelled': [], 'superseded': [], 'other': []}
            for row in retired:
                outcome = (row.get('outcome') or 'other').lower()
                group = next((name for name in ('completed', 'cancelled', 'superseded') if name in outcome), 'other')
                card = {'title': row['milestone_id'], 'milestone_id': row['milestone_id'], 'outcome': row.get('outcome'),
                        'summary': next((line.strip() for line in (row.get('specification') or '').splitlines()
                                         if line.strip() and not line.startswith('#')), None),
                        'review_evidence': row.get('review'), 'group': group,
                        'source': {'path': row['path'], 'line': row['line']}}
                history.append(card); history_groups[group].append(card)
            archives = []
            for row in documents.values():
                if row['kind'] != 'context_archive': continue
                identity = pathlib.Path(row['path']).stem.removeprefix('archive-')
                fields = dict(re.findall(r'^\*\*(Context|Baseline|Coverage)\.\*\* (.+)$', row['text'], re.M))
                refs = audit.records(connection, "SELECT relation,target FROM index_relationships WHERE workspace_id=? AND path=? ORDER BY relation,target", (workspace_id, row['path']))
                archives.append({'title': identity, 'archive_id': identity, 'lane': identity[0],
                                 'summary': fields.get('Context'), 'baseline': fields.get('Baseline'),
                                 'coverage': fields.get('Coverage'), 'relationships': refs,
                                 'source': {'path': row['path'], 'sha256': row['sha256']}})
            archive_groups = {}
            for card in archives: archive_groups.setdefault(card['lane'], []).append(card)
            versions = {}
            for row in documents.values():
                if not row['kind'].startswith('evolution_'): continue
                name = pathlib.Path(row['path']).stem
                kind, version = name.split('-v', 1)
                card = {'title': name, 'kind': kind, 'version': int(version),
                        'summary': next((line.strip() for line in row['text'].splitlines()
                                         if line.strip() and not line.startswith('#')), None),
                        'source': {'path': row['path'], 'sha256': row['sha256']}}
                versions.setdefault(int(version), {})[kind] = card
            evolution_pairs = [{'version': version, 'prompt': pair.get('prompt'), 'result': pair.get('result'),
                                'missing': [name for name in ('prompt', 'result') if name not in pair]}
                               for version, pair in sorted(versions.items())]
            evolution = [{**card, 'pair_missing': pair['missing']} for pair in evolution_pairs
                         for card in (pair.get('prompt'), pair.get('result')) if card]
            return {**health, "counts": counts, "attention": attention,
                    "summary": project_summary, "active_milestones": active,
                    "history": history, "history_groups": history_groups,
                    "archives": archives, "archive_groups": archive_groups,
                    "evolution": evolution, "evolution_pairs": evolution_pairs,
                    "groups": {"history": counts["history"], "archives": counts["archives"], "evolution": counts["evolution"]}}

    def timeline(self, params):
        limit = int(params.get("limit", [50])[0])
        audit.pagination(limit, 0)
        limit = min(limit, MAX_PAGE)
        cursor = _decode_cursor(params["cursor"][0]) if params.get("cursor") else None
        operation = params.get("operation", [None])[0]
        outcome = params.get("outcome", [None])[0]
        milestone = params.get("milestone", [None])[0]
        order = params.get("order", ["newest"])[0]
        since = params.get("since", [None])[0]
        until = params.get("until", [None])[0]
        search = (params.get("search", [""])[0] or "").strip().lower()
        child_limit = min(int(params.get('child_limit', [20])[0]), MAX_PAGE)
        audit.pagination(child_limit, 0)
        if operation and operation not in audit.OPERATIONS:
            raise audit.AuditError("unknown operation")
        if outcome and outcome not in audit.RUN_RESULTS | {'unfinished'}:
            raise audit.AuditError("unknown outcome")
        if order not in {'newest', 'oldest'}:
            raise audit.AuditError("timeline order must be newest or oldest")
        for value in (since, until):
            if value: audit._timestamp(value, 'timeline date')
        with self.read() as (connection, workspace):
            workspace_id = workspace["workspace_id"]
            clauses = ["r.workspace_id=?", "r.parent_run_id IS NULL"]; values: list[Any] = [workspace_id]
            if operation:
                clauses.append("(r.operation=? OR EXISTS (SELECT 1 FROM runs c WHERE c.parent_run_id=r.run_id AND c.operation=?))")
                values.extend([operation, operation])
            if outcome and outcome != "unfinished":
                clauses.append("(r.result=? OR EXISTS (SELECT 1 FROM runs c WHERE c.parent_run_id=r.run_id AND c.result=?))")
                values.extend([outcome, outcome])
            if outcome == "unfinished": clauses.append("(r.completed_at IS NULL OR EXISTS (SELECT 1 FROM runs c WHERE c.parent_run_id=r.run_id AND c.completed_at IS NULL))")
            if milestone:
                clauses.append("EXISTS (SELECT 1 FROM events e JOIN runs er ON er.run_id=e.run_id WHERE (er.run_id=r.run_id OR er.parent_run_id=r.run_id) AND e.milestone_id=?)")
                values.append(milestone)
            if since: clauses.append(f"{audit.time_key('r.started_at')} >= ?"); values.append(audit.time_bound(since))
            if until: clauses.append(f"{audit.time_key('r.started_at')} <= ?"); values.append(audit.time_bound(until))
            if search:
                clauses.append("(" + " OR ".join([
                    "instr(lower(coalesce(r.operation,'')),?)>0",
                    "instr(lower(coalesce(r.result,'')),?)>0",
                    "instr(lower(coalesce(r.git_head,'')),?)>0",
                    "instr(lower(coalesce(r.worktree_state,'')),?)>0",
                    "EXISTS (SELECT 1 FROM events e WHERE e.run_id=r.run_id AND (instr(lower(coalesce(e.event_type,'')),?)>0 OR instr(lower(coalesce(e.task_label,'')),?)>0 OR instr(lower(coalesce(e.details_json,'')),?)>0 OR instr(lower(coalesce(e.payload_json,'')),?)>0))",
                    "EXISTS (SELECT 1 FROM captured_messages m WHERE m.run_id=r.run_id AND (instr(lower(coalesce(m.role,'')),?)>0 OR instr(lower(m.text),?)>0))",
                    "EXISTS (SELECT 1 FROM runs c WHERE c.parent_run_id=r.run_id AND (instr(lower(c.operation),?)>0 OR instr(lower(coalesce(c.result,'')),?)>0 OR EXISTS (SELECT 1 FROM events ce WHERE ce.run_id=c.run_id AND (instr(lower(coalesce(ce.event_type,'')),?)>0 OR instr(lower(coalesce(ce.task_label,'')),?)>0 OR instr(lower(coalesce(ce.details_json,'')),?)>0 OR instr(lower(coalesce(ce.payload_json,'')),?)>0)) OR EXISTS (SELECT 1 FROM captured_messages cm WHERE cm.run_id=c.run_id AND (instr(lower(coalesce(cm.role,'')),?)>0 OR instr(lower(cm.text),?)>0))))",
                ]) + ")")
                values.extend([search] * 18)
            direction = cursor.get('direction', 'next') if cursor else None
            newest = order == 'newest'
            query_desc = newest
            if cursor and direction == 'previous':
                query_desc = not newest
            if cursor:
                boundary = audit.time_bound(cursor["started_at"])
                key = audit.time_key("r.started_at")
                comparison = '<' if query_desc else '>'
                clauses.append(f"({key} {comparison} ? OR ({key} = ? AND r.run_id {comparison} ?))")
                values.extend([boundary, boundary, cursor["run_id"]])
            where = " AND ".join(clauses)
            sql_direction = 'DESC' if query_desc else 'ASC'
            rows = audit.records(connection, f"SELECT r.* FROM runs r WHERE {where} ORDER BY {audit.time_key('r.started_at')} {sql_direction},r.run_id {sql_direction} LIMIT ?", (*values, limit + 1))
            more = len(rows) > limit; rows = rows[:limit]
            if query_desc != newest: rows.reverse()

            def decorate(row):
                def compact(value, limit=500):
                    if value is None: return None
                    return value if len(value) <= limit else value[:limit - 1] + '…'
                messages = audit.records(connection, "SELECT role,text,fidelity FROM captured_messages WHERE run_id=? ORDER BY sequence", (row['run_id'],))
                request = next((message for message in messages if message['role'] in {'user', 'request'}), None)
                output = next((message for message in reversed(messages) if message['role'] in {'assistant', 'output'}), None)
                summary = None
                if 'event_explorer' in audit.schema_tables(connection):
                    selected = connection.execute("SELECT x.summary FROM event_explorer x JOIN events e USING(event_id) WHERE e.run_id=? AND x.summary IS NOT NULL ORDER BY e.sequence DESC LIMIT 1", (row['run_id'],)).fetchone()
                    summary = selected[0] if selected else None
                if not summary:
                    selected = connection.execute("SELECT event_type,task_label FROM events WHERE run_id=? ORDER BY sequence DESC LIMIT 1", (row['run_id'],)).fetchone()
                    summary = ' — '.join(value for value in selected if value) if selected else None
                row['request_summary'] = compact(request['text']) if request else None
                row['capture_fidelity'] = request['fidelity'] if request else 'incomplete'
                row['result_summary'] = compact(output['text'] if output else summary)
                row['unfinished'] = row['completed_at'] is None
                return row

            for row in rows:
                decorate(row)
                children = audit.records(connection, f"SELECT * FROM runs WHERE parent_run_id=? AND workspace_id=? ORDER BY {audit.time_key('started_at')} ASC,run_id ASC LIMIT ?", (row["run_id"], workspace_id, child_limit + 1))
                row['children_more'] = len(children) > child_limit
                children = children[:child_limit]
                row['children'] = [decorate(child) for child in children]
                row["child_run_ids"] = [child['run_id'] for child in children]
                row['child_count'] = connection.execute(
                    'SELECT COUNT(*) FROM runs WHERE parent_run_id=? AND workspace_id=?',
                    (row['run_id'], workspace_id),
                ).fetchone()[0]
            has_previous = bool(cursor)
            next_cursor = None; previous_cursor = None
            if rows:
                if (direction != 'previous' and more) or direction == 'previous':
                    next_cursor = _cursor({"started_at": rows[-1]["started_at"], "run_id": rows[-1]["run_id"], "direction": "next"})
                if has_previous and ((direction == 'previous' and more) or direction != 'previous'):
                    previous_cursor = _cursor({"started_at": rows[0]["started_at"], "run_id": rows[0]["run_id"], "direction": "previous"})
            return {"workspace_id": workspace_id, "results": rows, "runs": rows, "entries": rows, "limit": limit,
                    "next_cursor": next_cursor, "previous_cursor": previous_cursor,
                    "index": index.status(connection, workspace_id)}

    def run(self, run_id, params=None):
        params = params or {}
        event_limit = min(int(params.get('event_limit', [50])[0]), MAX_PAGE)
        message_limit = min(int(params.get('message_limit', [50])[0]), MAX_PAGE)
        event_offset = int(params.get('event_offset', [0])[0])
        message_offset = int(params.get('message_offset', [0])[0])
        child_limit = min(int(params.get('child_limit', [50])[0]), MAX_PAGE)
        child_offset = int(params.get('child_offset', [0])[0])
        audit.pagination(event_limit, event_offset); audit.pagination(message_limit, message_offset)
        audit.pagination(child_limit, child_offset)
        with self.read() as (connection, workspace):
            row = audit.records(connection, "SELECT * FROM runs WHERE run_id=? AND workspace_id=?", (run_id, workspace["workspace_id"]))
            if not row: raise audit.AuditError("run is not part of this project")
            result = row[0]
            result["events"] = audit.query_events(connection, run_id, workspace_id=workspace["workspace_id"], limit=event_limit + 1, offset=event_offset)
            more_events = len(result['events']) > event_limit; result['events'] = result['events'][:event_limit]
            for event in result['events']:
                for field in ('details_json', 'payload_json', 'verification_json', 'file_actions_json'):
                    value = event.get(field)
                    if isinstance(value, str) and len(value) > 65536:
                        event[field] = value[:65535] + '…'; event[field + '_truncated'] = True
            if 'event_explorer' in audit.schema_tables(connection):
                for event in result["events"]:
                    explorer_rows = audit.records(connection, "SELECT * FROM event_explorer WHERE event_id=?", (event["event_id"],))
                    if explorer_rows:
                        event["explorer"] = explorer_rows[0]
                        if len(event['explorer']['details_json']) > 65536:
                            event['explorer']['details_json'] = event['explorer']['details_json'][:65535] + '…'
                            event['explorer']['details_truncated'] = True
                        event["explorer"]["message_refs"] = audit.records(connection, "SELECT * FROM event_message_refs WHERE event_id=? ORDER BY message_id", (event["event_id"],))
                        event["explorer"]["artifact_refs"] = audit.records(connection, "SELECT * FROM event_artifacts WHERE event_id=? ORDER BY namespace,identifier", (event["event_id"],))
                        for artifact in event['explorer']['artifact_refs']:
                            if len(artifact['details_json']) > 65536:
                                artifact['details_json'] = artifact['details_json'][:65535] + '…'
                                artifact['details_truncated'] = True
            result["messages"] = audit.records(connection, "SELECT * FROM captured_messages WHERE run_id=? ORDER BY sequence LIMIT ? OFFSET ?", (run_id, message_limit + 1, message_offset))
            more_messages = len(result['messages']) > message_limit; result['messages'] = result['messages'][:message_limit]
            for message in result['messages']:
                if len(message['text']) > 65536:
                    message['original_characters'] = len(message['text'])
                    message['text'] = message['text'][:65535] + '…'; message['truncated'] = True
            summary_messages = audit.records(connection, """
                SELECT * FROM captured_messages WHERE message_id IN (
                  SELECT message_id FROM captured_messages
                  WHERE run_id=? AND role IN ('user','request') ORDER BY sequence LIMIT 1
                ) OR message_id IN (
                  SELECT message_id FROM captured_messages
                  WHERE run_id=? AND role IN ('assistant','output') ORDER BY sequence DESC LIMIT 1
                ) ORDER BY sequence
            """, (run_id, run_id))
            for message in summary_messages:
                if len(message['text']) > 65536:
                    message['original_characters'] = len(message['text'])
                    message['text'] = message['text'][:65535] + '…'; message['truncated'] = True
            request_message = next((message for message in summary_messages if message['role'] in {'user','request'}), None)
            output_message = next((message for message in reversed(summary_messages) if message['role'] in {'assistant','output'}), None)
            result["snapshot_observations"] = audit.records(connection, "SELECT * FROM run_snapshots WHERE run_id=? ORDER BY source_path", (run_id,))
            current = []; seen = set(); tables = set(audit.schema_tables(connection))
            if 'index_milestones' in tables:
                milestone_ids = {row[0] for row in connection.execute(
                    "SELECT DISTINCT milestone_id FROM events WHERE run_id=? AND milestone_id IS NOT NULL", (run_id,))}
                if 'event_artifacts' in tables:
                    milestone_ids.update(row[0] for row in connection.execute(
                        "SELECT identifier FROM event_artifacts WHERE run_id=? AND namespace='milestone'", (run_id,)))
                for milestone_id in sorted(milestone_ids):
                    rows = audit.records(connection, "SELECT milestone_id,lifecycle,path,line,outcome FROM index_milestones WHERE workspace_id=? AND milestone_id=?", (workspace['workspace_id'], milestone_id))
                    current.append({'kind': 'milestone', 'identifier': milestone_id,
                                    'resolved': len(rows) == 1, 'record': rows[0] if len(rows) == 1 else None})
                    seen.add(('milestone', milestone_id))
            if 'index_tasks' in tables:
                observations = audit.records(connection, """
                    SELECT DISTINCT task_label AS identifier,task_label AS label,
                                    milestone_id,status_path AS path
                    FROM events WHERE run_id=? AND task_label IS NOT NULL
                """, (run_id,))
                if 'event_artifacts' in tables:
                    observations += audit.records(connection, """
                        SELECT DISTINCT a.identifier,a.label,e.milestone_id,a.path
                        FROM event_artifacts a JOIN events e USING(event_id)
                        WHERE a.run_id=? AND a.namespace='task' AND a.relationship!='proposed'
                    """, (run_id,))
                for observation in observations:
                    identifier = observation['identifier']; label = observation.get('label') or identifier
                    milestone_id = observation.get('milestone_id')
                    scoped = re.fullmatch(r'([A-Z][0-9]{2})/(.+)', identifier)
                    if scoped:
                        milestone_id, identifier = scoped.groups()
                    key = ('task', milestone_id,
                           None if milestone_id else observation.get('path'), identifier)
                    if key in seen: continue
                    source_path = None if milestone_id else observation.get('path')
                    rows = audit.records(connection, """
                        SELECT milestone_id,explicit_id,label,state,notes,path,line,sha256
                        FROM index_tasks
                        WHERE workspace_id=? AND (explicit_id=? OR label=?)
                          AND (? IS NULL OR milestone_id=?)
                          AND (? IS NULL OR path=?)
                    """, (workspace['workspace_id'], identifier, label, milestone_id, milestone_id,
                            source_path, source_path))
                    current.append({'kind': 'task', 'identifier': identifier, 'resolved': len(rows) == 1,
                                    'reason': None if len(rows) == 1 else 'current task location is missing or ambiguous',
                                    'record': rows[0] if len(rows) == 1 else None})
                    seen.add(key)
            children = audit.records(connection, f"SELECT * FROM runs WHERE parent_run_id=? AND workspace_id=? ORDER BY {audit.time_key('started_at')},run_id LIMIT ? OFFSET ?", (run_id, workspace['workspace_id'], child_limit + 1, child_offset))
            more_children = len(children) > child_limit; children = children[:child_limit]
            return {"run": result, "events": result.pop("events"), "messages": result.pop("messages"),
                    "snapshot_observations": result.pop("snapshot_observations"), "current_state": current,
                    "request_message": request_message, "output_message": output_message,
                    "children": children,
                    "pagination": {"events": {"limit": event_limit, "offset": event_offset, "more": more_events},
                                   "messages": {"limit": message_limit, "offset": message_offset, "more": more_messages},
                                   "children": {"limit": child_limit, "offset": child_offset, "more": more_children}}}

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

    def todo(self, params=None):
        params = params or {}
        limit = min(int(params.get('limit', [50])[0]), MAX_PAGE)
        audit.pagination(limit, 0)
        offsets = {}
        for group in TODO_GROUPS:
            value = int(params.get(f'{group}_offset', [0])[0])
            audit.pagination(1, value)
            offsets[group] = value
        with self.read() as (connection, workspace):
            workspace_id = workspace["workspace_id"]
            readiness = index.readiness(connection, workspace_id, self.project)
            validation = {'valid': readiness['source_freshness'] == 'current' and bool(readiness['index'].get('complete')),
                          'diagnostics': readiness.get('freshness_diagnostics', [])}
            def flatten(items):
                result = []
                for item in items:
                    if item.get('milestone_ids') and not item.get('task'):
                        for milestone_id in item['milestone_ids']:
                            milestone = connection.execute(
                                'SELECT path,line FROM index_milestones WHERE workspace_id=? AND milestone_id=?',
                                (workspace_id, milestone_id)).fetchone()
                            result.append({**item, 'milestone_id': milestone_id,
                                           'source': {'path': milestone[0], 'line': milestone[1]} if milestone else None})
                        continue
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
            totals = {key: len(value) for key, value in buckets.items()}
            pages = {key: value[offsets[key]:offsets[key] + limit] for key, value in buckets.items()}
            pagination = {key: {'limit': limit, 'offset': offsets[key], 'total': totals[key],
                                'more': offsets[key] + limit < totals[key]}
                          for key in TODO_GROUPS}
            groups = [{'label': key.replace('_', ' ').title(), 'tasks': pages[key],
                       'pagination': pagination[key]} for key in TODO_GROUPS]
            return {'workspace_id': workspace_id, 'validation': validation,
                    'validated': validation['valid'],
                    'recommendations_available': bool(readiness['recommendations']),
                    'validation_reason': '; '.join(validation['diagnostics']) if validation['diagnostics'] else None,
                    **pages, 'totals': totals, 'pagination': pagination,
                    'groups': groups, 'index': readiness['index']}

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
            elif action == 'review' and milestone:
                rows = audit.records(connection, 'SELECT * FROM index_milestones WHERE workspace_id=? AND milestone_id=?', (workspace_id, milestone))
                if len(rows) != 1:
                    raise audit.AuditError('review milestone is missing or ambiguous')
                item = rows[0]
            else:
                raise audit.AuditError('follow-up needs a task or review milestone')
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
            known = connection.execute('SELECT sha256 FROM index_documents WHERE workspace_id=? AND path=?', (workspace_id, item['path'])).fetchone()
            if not known:
                raise audit.AuditError('follow-up source is not a declared indexed document')
            text, digest, _ = index.read_document(self.project, item['path'])
            if digest != known[0]:
                raise audit.AuditError('selected source changed since readiness validation; refresh and select it again')
            live = self._live_validation(connection, workspace_id)
            if not live['valid']:
                raise audit.AuditError('project sources changed since readiness validation: ' + '; '.join(live['diagnostics']))
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
            subject = f"milestone {item['milestone_id']}" if item.get('milestone_id') else 'the selected project evidence'
            if item.get('label'):
                subject += f", task {item['label']}"
            prompt = (f"{verbs[action]} {subject} in project {self.project}. "
                      f"Reread AGENTS.md and the live source before acting. Inspect {source['path']}")
            if source.get('line'):
                prompt += f":{source['line']}"
            prompt += ". Preserve the project's approval and commit policies; do not infer authorization for external actions."
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
            if not self.database.exists():
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
        try:
            host = urllib.parse.urlsplit("//" + self.headers.get("Host", "")).hostname or ""
        except ValueError:
            return False
        host = host.lower()
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
            elif path.startswith("/api/runs/"): self._send(200, self.app.run(urllib.parse.unquote(path.removeprefix("/api/runs/")), params))
            elif path == "/api/todo": self._send(200, self.app.todo(params))
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
            raw = self.rfile.read(length); payload = audit.strict_json_loads(raw or b"{}")
            if not isinstance(payload, dict): raise audit.AuditError("request body must be a JSON object")
            if parsed.path == "/api/refresh":
                unknown = set(payload) - {'rebuild', 'literal'}
                if unknown: raise audit.AuditError('unknown refresh fields: ' + ', '.join(sorted(unknown)))
                for field in ('rebuild', 'literal'):
                    if field in payload and type(payload[field]) is not bool:
                        raise audit.AuditError(f'{field} must be a boolean')
                self._send(200, self.app.refresh(payload.get("rebuild", False), payload.get("literal", False)))
            else:
                line = payload.get("line")
                if line is not None and type(line) is not int: raise audit.AuditError("line must be an integer")
                if line is not None: payload['line'] = line
                self._send(200, self.app.follow_up(payload))
        except (audit.AuditError, sqlite3.Error, OSError, ValueError, TypeError, json.JSONDecodeError) as exc: self._error(400, exc)


class ExplorerServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, app):
        host = address[0]
        try:
            allowed = host.lower() == 'localhost' or ipaddress.ip_address(host).is_loopback
        except ValueError:
            allowed = False
        if not allowed:
            raise audit.AuditError('explorer host must be a loopback address')
        if ':' in host:
            self.address_family = socket.AF_INET6
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

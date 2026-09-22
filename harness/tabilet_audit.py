#!/usr/bin/env python3
"""SQLite audit primitives for the memory-bank API runner.

The module is deliberately small and standard-library only.  It owns the
versioned event envelope and database schema; it does not execute project
commands or decide whether a project change is authorized.
"""

from __future__ import annotations

import datetime as _datetime
import contextlib
import functools
import base64
import json
import hashlib
import os
import pathlib
import re
import sqlite3
from typing import Any
import uuid
from urllib.parse import quote


SCHEMA_NAME = "tabilet.audit/v3"
SCHEMA_VERSION = 3
RECORDER_VERSION = "tabilet-audit/3"

OPERATIONS = frozenset({"init", "archive", "propose", "reconcile", "next", "goal", "upgrade"})
RUN_RESULTS = frozenset({"completed", "blocked", "failed", "cancelled", "interrupted", "unknown"})
WORKTREE_STATES = frozenset({"clean", "dirty", "unversioned"})
EVENT_TYPES = frozenset({
    "run_started",
    "task_observed",
    "task_transition",
    "verification_observed",
    "commit_observed",
    "run_finished",
    "run_blocked",
    "run_failed",
    "run_interrupted",
    "audit_gap",
    "snapshot_gap",
    "milestone_accepted", "milestone_retired", "cancelled", "superseded",
})
SNAPSHOT_KINDS = frozenset({"history_status", "history_index", "knowledge_history", "evolution_prompt", "evolution_result", "context_archive"})
SNAPSHOT_MAX_BYTES = 4 * 1024 * 1024
STATES = frozenset({"pending", "in_progress", "completed", "blocked", "cancelled", "historical"})
FIDELITIES = frozenset({"exact", "redacted", "summarized", "incomplete"})
CAPTURE_SOURCES = frozenset({"host", "agent", "import"})
EXPLORER_DETAILS_SCHEMA = "tabilet.audit.explorer/v1"
EXPLORER_PHASES = frozenset({"request", "proposal", "approval", "applied"})
MESSAGE_PURPOSES = frozenset({"request", "clarification", "approval", "output"})
ARTIFACT_NAMESPACES = frozenset({"milestone", "task", "archive", "evolution", "document"})
ARTIFACT_RELATIONSHIPS = frozenset({"observed", "proposed", "created", "changed", "retired", "referenced"})
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class AuditError(ValueError):
    """Base error for invalid or unavailable audit data."""


class AuditValidationError(AuditError):
    """The event or database input violates the audit contract."""


class AuditConflict(AuditError):
    """An idempotency key was reused with a different payload."""


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workspaces (
    workspace_id TEXT PRIMARY KEY,
    project_root TEXT UNIQUE NOT NULL,
    repository_id TEXT,
    branch TEXT,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
    operation TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    recorder_version TEXT NOT NULL,
    capture_mode TEXT NOT NULL,
    parent_run_id TEXT REFERENCES runs(run_id),
    git_head TEXT,
    worktree_state TEXT NOT NULL,
    result TEXT
);
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    sequence INTEGER NOT NULL,
    recorded_at TEXT NOT NULL,
    occurred_at TEXT,
    operation TEXT NOT NULL,
    event_type TEXT NOT NULL,
    milestone_id TEXT,
    task_label TEXT,
    status_path TEXT,
    old_state TEXT,
    new_state TEXT,
    verification_json TEXT,
    file_actions_json TEXT,
    commit_sha TEXT,
    details_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    UNIQUE(run_id, sequence)
);
CREATE TABLE IF NOT EXISTS captured_messages (
    message_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    sequence INTEGER NOT NULL,
    role TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    text TEXT NOT NULL,
    capture_source TEXT NOT NULL,
    fidelity TEXT NOT NULL,
    redaction_note TEXT,
    UNIQUE(run_id, sequence)
);
CREATE INDEX IF NOT EXISTS events_run_sequence ON events(run_id, sequence);
CREATE INDEX IF NOT EXISTS events_milestone ON events(milestone_id);
CREATE INDEX IF NOT EXISTS runs_workspace_started ON runs(workspace_id, started_at);
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
    kind TEXT NOT NULL,
    source_path TEXT NOT NULL,
    content BLOB NOT NULL,
    sha256 TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    source_commit TEXT,
    worktree_state TEXT NOT NULL,
    source_run_id TEXT NOT NULL REFERENCES runs(run_id),
    predecessor_id TEXT REFERENCES snapshots(snapshot_id),
    UNIQUE(workspace_id, kind, source_path, sha256)
);
CREATE TABLE IF NOT EXISTS run_snapshots (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    snapshot_id TEXT REFERENCES snapshots(snapshot_id),
    observed_at TEXT NOT NULL,
    observation_state TEXT NOT NULL,
    source_path TEXT NOT NULL,
    diagnostic TEXT,
    PRIMARY KEY(run_id, source_path)
);
CREATE INDEX IF NOT EXISTS snapshots_source ON snapshots(workspace_id, kind, source_path, captured_at);
CREATE INDEX IF NOT EXISTS run_snapshots_snapshot ON run_snapshots(snapshot_id);
"""


def utc_now() -> str:
    """Return the canonical UTC timestamp used by the audit schema."""

    return _datetime.datetime.now(_datetime.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize JSON details deterministically for idempotency comparisons."""

    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except ValueError as exc:
        raise AuditValidationError("JSON values must be finite") from exc


def strict_json_loads(value: str | bytes | bytearray) -> Any:
    """Parse interoperable JSON and reject Python's non-standard constants."""

    def reject_constant(constant: str) -> Any:
        raise AuditValidationError(f"invalid JSON constant: {constant}")

    try:
        return json.loads(value, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise AuditValidationError(f"invalid JSON: {exc}") from exc


def _timestamp(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise AuditValidationError(f"{field} must be a UTC RFC 3339 timestamp ending in Z")
    try:
        _datetime.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise AuditValidationError(f"{field} is not a valid timestamp") from exc
    return value


def _text(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AuditValidationError(f"{field} must be a non-empty string")
    return value


def validate_event(event: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one tabilet.audit.event/v1 envelope."""

    if not isinstance(event, dict):
        raise AuditValidationError("event must be a JSON object")
    if event.get("schema") != "tabilet.audit.event/v1":
        raise AuditValidationError("event schema must be tabilet.audit.event/v1")
    normalized = dict(event)
    for field in ("event_id", "run_id", "workspace_id", "operation", "event_type"):
        _text(normalized.get(field), field)
    if normalized["operation"] not in OPERATIONS:
        raise AuditValidationError(f"unknown operation: {normalized['operation']}")
    if normalized["event_type"] not in EVENT_TYPES:
        raise AuditValidationError(f"unknown event type: {normalized['event_type']}")
    _timestamp(normalized.get("recorded_at"), "recorded_at")
    _timestamp(normalized.get("occurred_at"), "occurred_at", optional=True)
    subject = normalized.get("subject", {})
    if not isinstance(subject, dict):
        raise AuditValidationError("subject must be a JSON object")
    subject = dict(subject)
    for field in ("milestone_id", "task_label", "status_path", "old_state", "new_state"):
        value = subject.get(field)
        if value is not None and not isinstance(value, str):
            raise AuditValidationError(f"subject.{field} must be a string or null")
    for field in ("old_state", "new_state"):
        if subject.get(field) is not None and subject[field] not in STATES:
            raise AuditValidationError(f"unknown subject state: {subject[field]}")
    details = normalized.get("details", {})
    if not isinstance(details, dict):
        raise AuditValidationError("details must be a JSON object")
    if details.get("schema") != "tabilet.audit.details/v1":
        raise AuditValidationError("details schema must be tabilet.audit.details/v1")
    explorer = details.get("explorer")
    if explorer is not None:
        validate_explorer_details(explorer)
    normalized["subject"] = subject
    normalized["details"] = details
    return normalized


def validate_explorer_details(value: Any) -> dict[str, Any]:
    """Validate the optional, versioned explorer evidence extension.

    The event envelope remains v1 so older readers can safely ignore this
    object.  The extension contains observations only; it never asserts that
    a proposed artifact was actually written.
    """
    if not isinstance(value, dict) or value.get("schema") != EXPLORER_DETAILS_SCHEMA:
        raise AuditValidationError(f"explorer details schema must be {EXPLORER_DETAILS_SCHEMA}")
    phase = value.get("phase")
    if phase not in EXPLORER_PHASES:
        raise AuditValidationError("explorer phase must be request, proposal, approval, or applied")
    summary = value.get("summary")
    if summary is not None:
        _text(summary, "explorer.summary")
    messages = value.get("message_refs", [])
    artifacts = value.get("artifact_refs", [])
    if not isinstance(messages, list) or not isinstance(artifacts, list):
        raise AuditValidationError("explorer message_refs and artifact_refs must be arrays")
    seen_messages = set()
    for ref in messages:
        if not isinstance(ref, dict):
            raise AuditValidationError("explorer message reference must be an object")
        message_id = _text(ref.get("message_id"), "explorer.message_refs.message_id")
        purpose = ref.get("purpose")
        if purpose not in MESSAGE_PURPOSES:
            raise AuditValidationError("unknown explorer message purpose")
        if message_id in seen_messages:
            raise AuditValidationError("duplicate explorer message reference")
        seen_messages.add(message_id)
    seen_artifacts = set()
    for ref in artifacts:
        if not isinstance(ref, dict):
            raise AuditValidationError("explorer artifact reference must be an object")
        namespace = ref.get("namespace")
        if namespace not in ARTIFACT_NAMESPACES:
            raise AuditValidationError("unknown explorer artifact namespace")
        identifier = _text(ref.get("identifier"), "explorer.artifact_refs.identifier")
        relationship = ref.get("relationship")
        if relationship not in ARTIFACT_RELATIONSHIPS:
            raise AuditValidationError("unknown explorer artifact relationship")
        path = ref.get("path")
        if path is not None:
            _text(path, "explorer.artifact_refs.path")
            if pathlib.PurePosixPath(path).is_absolute() or ".." in pathlib.PurePosixPath(path).parts:
                raise AuditValidationError("explorer artifact path must be project-relative")
        for field in ("line",):
            if ref.get(field) is not None and (type(ref[field]) is not int or ref[field] < 1):
                raise AuditValidationError(f"explorer artifact {field} must be a positive integer")
        for field in ("sha256",):
            if ref.get(field) is not None and not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(ref[field])):
                raise AuditValidationError(f"explorer artifact {field} must be a hex digest")
        for field in ("old_state", "new_state"):
            if ref.get(field) is not None and ref[field] not in STATES:
                raise AuditValidationError(f"unknown explorer artifact state: {ref[field]}")
        key = (namespace, identifier, relationship, path)
        if key in seen_artifacts:
            raise AuditValidationError("duplicate explorer artifact reference")
        seen_artifacts.add(key)
    return value


def schema_tables(connection: sqlite3.Connection) -> set[str]:
    """Return user tables present in a connection, useful for schema tests."""

    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def default_database_path(environment: dict[str, str] | None = None) -> pathlib.Path:
    """Return the opt-in user's database path without creating anything."""

    environment = environment or os.environ
    state_home = environment.get("XDG_STATE_HOME")
    base = pathlib.Path(state_home).expanduser() if state_home else pathlib.Path.home() / ".local" / "state"
    return (base / "tabilet" / "audit.sqlite3").resolve()


# Derived tables have no inbound references from durable audit records.
INDEX_SQL = """
CREATE TABLE IF NOT EXISTS index_state (
 workspace_id TEXT PRIMARY KEY REFERENCES workspaces, generation TEXT,
 refreshed_at TEXT, git_head TEXT, branch TEXT, complete INTEGER NOT NULL DEFAULT 0,
 last_attempt TEXT, diagnostics_json TEXT NOT NULL DEFAULT '[]', search_mode TEXT);
CREATE TABLE IF NOT EXISTS index_documents (
 workspace_id TEXT NOT NULL REFERENCES workspaces, path TEXT NOT NULL, kind TEXT NOT NULL,
 sha256 TEXT NOT NULL, mtime_ns INTEGER NOT NULL, size INTEGER NOT NULL, text TEXT NOT NULL,
 PRIMARY KEY(workspace_id,path));
CREATE TABLE IF NOT EXISTS index_sections (
 workspace_id TEXT NOT NULL, path TEXT NOT NULL, line INTEGER NOT NULL, end_line INTEGER NOT NULL,
 heading TEXT NOT NULL, anchor TEXT NOT NULL, text TEXT NOT NULL,
 PRIMARY KEY(workspace_id,path,line));
CREATE TABLE IF NOT EXISTS index_milestones (
 workspace_id TEXT NOT NULL, milestone_id TEXT NOT NULL, lifecycle TEXT NOT NULL,
 path TEXT NOT NULL, line INTEGER NOT NULL, specification TEXT, outcome TEXT,
 review TEXT, PRIMARY KEY(workspace_id,milestone_id));
CREATE TABLE IF NOT EXISTS index_tasks (
 workspace_id TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL, line INTEGER NOT NULL,
 milestone_id TEXT NOT NULL, label TEXT NOT NULL, state TEXT NOT NULL, notes TEXT NOT NULL,
 explicit_id TEXT, PRIMARY KEY(workspace_id,path,sha256,line));
CREATE TABLE IF NOT EXISTS index_relationships (
 workspace_id TEXT NOT NULL, path TEXT NOT NULL, line INTEGER NOT NULL,
 source TEXT NOT NULL, relation TEXT NOT NULL, target TEXT NOT NULL,
 PRIMARY KEY(workspace_id,path,line,source,relation,target));
CREATE TABLE IF NOT EXISTS index_search (
 search_id INTEGER PRIMARY KEY, workspace_id TEXT NOT NULL, path TEXT NOT NULL,
 line INTEGER NOT NULL, kind TEXT NOT NULL, milestone_id TEXT, state TEXT, text TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS index_search_workspace ON index_search(workspace_id,path);
"""

# SQL9 additions deliberately live in a separate script.  SCHEMA_SQL and
# INDEX_SQL remain the v1/v2 fixtures used to validate older databases.  These
# tables are either durable evidence references or disposable projections; no
# audit row has an inbound reference to a projection table.
EXPLORER_SQL = """
CREATE TABLE IF NOT EXISTS event_explorer (
 event_id TEXT PRIMARY KEY REFERENCES events(event_id),
 run_id TEXT NOT NULL REFERENCES runs(run_id),
 phase TEXT NOT NULL, summary TEXT, details_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_message_refs (
 event_id TEXT NOT NULL REFERENCES event_explorer(event_id),
 message_id TEXT NOT NULL REFERENCES captured_messages(message_id),
 purpose TEXT NOT NULL,
 PRIMARY KEY(event_id,message_id,purpose)
);
CREATE TABLE IF NOT EXISTS event_artifacts (
 event_id TEXT NOT NULL REFERENCES event_explorer(event_id),
 run_id TEXT NOT NULL REFERENCES runs(run_id),
 namespace TEXT NOT NULL, identifier TEXT NOT NULL,
 relationship TEXT NOT NULL, path TEXT, line INTEGER, sha256 TEXT,
 label TEXT, old_state TEXT, new_state TEXT, details_json TEXT NOT NULL,
 PRIMARY KEY(event_id,namespace,identifier,relationship,path)
);
CREATE INDEX IF NOT EXISTS event_explorer_run ON event_explorer(run_id);
CREATE INDEX IF NOT EXISTS event_artifacts_run ON event_artifacts(run_id,namespace,identifier);
CREATE TABLE IF NOT EXISTS index_milestone_projection (
 workspace_id TEXT NOT NULL REFERENCES workspaces,
 milestone_id TEXT NOT NULL, display_order INTEGER, summary TEXT,
 acceptance_text TEXT, review_evidence TEXT, closure_state TEXT,
 path TEXT NOT NULL, source_line INTEGER NOT NULL, source_sha256 TEXT NOT NULL,
 PRIMARY KEY(workspace_id,milestone_id)
);
CREATE TABLE IF NOT EXISTS index_task_dependencies (
 workspace_id TEXT NOT NULL REFERENCES workspaces,
 source_key TEXT NOT NULL, path TEXT NOT NULL, source_sha256 TEXT NOT NULL,
 source_line INTEGER NOT NULL, milestone_id TEXT NOT NULL,
 target_key TEXT NOT NULL, target_milestone_id TEXT, target_explicit_id TEXT,
 relationship TEXT NOT NULL, reason TEXT NOT NULL,
 PRIMARY KEY(workspace_id,source_key,target_key,relationship)
);
CREATE INDEX IF NOT EXISTS index_task_dependencies_target
 ON index_task_dependencies(workspace_id,target_key);
"""


def atomic(function):
    """Serialize read/modify/write sequences and compose them in one transaction."""
    @functools.wraps(function)
    def wrapped(connection, *args, **kwargs):
        owner = not connection.in_transaction
        if owner:
            connection.execute("BEGIN IMMEDIATE")
        try:
            result = function(connection, *args, **kwargs)
            if owner:
                connection.commit()
            return result
        except BaseException:
            if owner:
                connection.rollback()
            raise
    return wrapped


def safe_path(path):
    path = pathlib.Path(os.path.abspath(pathlib.Path(path).expanduser()))
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise AuditError(f"symlink destination rejected: {parent}")
    return path


def external_path(path, roots=()):
    path = safe_path(path)
    for root in roots:
        if path.is_relative_to(pathlib.Path(root).expanduser().resolve()):
            raise AuditError(f"database or recovery destination is inside project: {root}")
    return path


def private_create(path):
    """Create exclusively; do not chmod an existing parent."""
    missing = []
    parent = path.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            safe_path(directory)
    return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, 'O_NOFOLLOW', 0), 0o600)


def _new_destination(path, roots=()):
    """Validate a new database or recovery destination and its SQLite sidecars."""
    path = external_path(path, roots)
    if path.exists():
        raise FileExistsError(str(path))
    for suffix in ('-wal', '-shm', '-journal'):
        sidecar = safe_path(str(path) + suffix)
        if sidecar.exists():
            raise FileExistsError(str(sidecar))
    return path


def database_roots(connection):
    return [row[0] for row in connection.execute('SELECT project_root FROM workspaces')]


def database_path(connection):
    return next((row[2] for row in connection.execute('PRAGMA database_list') if row[1] == 'main'), '')


def validate_database(connection):
    version = connection.execute('PRAGMA user_version').fetchone()[0]
    if version not in (1, 2, SCHEMA_VERSION):
        raise AuditError(f"unsupported audit database version: {version}")
    try:
        marker = connection.execute("SELECT value FROM schema_meta WHERE key='schema'").fetchone()
        if marker != (f'tabilet.audit/v{version}',):
            raise AuditError('unsupported audit database identity')
        # Verify every required table/column before any schema or permission mutation.
        expected = sqlite3.connect(':memory:')
        try:
            expected.executescript(
                SCHEMA_SQL
                + (INDEX_SQL if version >= 2 else '')
                + (EXPLORER_SQL if version >= SCHEMA_VERSION else '')
            )
            for table in schema_tables(expected):
                columns = {r[1] for r in expected.execute(f'PRAGMA table_info({table})')}
                actual = {r[1] for r in connection.execute(f'PRAGMA table_info({table})')}
                if not columns.issubset(actual):
                    raise AuditError(f'incomplete audit schema: {table}')
        finally:
            expected.close()
        if connection.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise AuditError('corrupt audit database')
        if connection.execute('PRAGMA foreign_key_check').fetchone():
            raise AuditError('audit database has invalid foreign keys')
    except sqlite3.DatabaseError as exc:
        raise AuditError(f'invalid audit database: {exc}') from exc
    return version


def open_database(path=None, *, project_roots=()):
    """Explicit writer open. Existing databases are identified before mutation."""
    database = external_path(path if path is not None else default_database_path(), project_roots)
    sidecars = {suffix: safe_path(str(database) + suffix) for suffix in ('-wal', '-shm', '-journal')}
    created = not database.exists()
    staging = None
    published = not created
    if created:
        for sidecar in sidecars.values():
            if sidecar.exists():
                raise FileExistsError(str(sidecar))
        staging = safe_path(f'{database}.init-{uuid.uuid4().hex}')
        os.close(private_create(staging))
        connect_path = staging
    elif not database.is_file():
        raise AuditError('audit database must be a regular file')
    else:
        connect_path = database
    try:
        connection = sqlite3.connect(str(connect_path), timeout=5)
    except BaseException:
        if staging is not None and staging.exists() and not staging.is_symlink():
            staging.unlink()
        raise
    try:
        connection.execute('PRAGMA foreign_keys = ON')
        connection.execute('PRAGMA busy_timeout = 5000')
        version = 0 if created else validate_database(connection)
        if not created:
            external_path(database, database_roots(connection))
        # New files are private before connect; only validated owned files are tightened.
        connect_path.chmod(0o600)
        if version < SCHEMA_VERSION:
            connection.execute('BEGIN IMMEDIATE')
            try:
                migration_sql = SCHEMA_SQL + INDEX_SQL + EXPLORER_SQL
                for statement in migration_sql.split(';'):
                    if statement.strip():
                        connection.execute(statement)
                connection.execute("INSERT OR REPLACE INTO schema_meta VALUES ('schema', ?)", (SCHEMA_NAME,))
                connection.execute("INSERT OR REPLACE INTO schema_meta VALUES ('recorder_version', ?)", (RECORDER_VERSION,))
                connection.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        if created:
            connection.close()
            connection = None
            try:
                os.link(staging, database)
            except FileExistsError:
                raise AuditError('audit database destination appeared during creation')
            published = True
            staging.unlink()
            connection = sqlite3.connect(str(database), timeout=5)
            connection.execute('PRAGMA foreign_keys = ON')
            connection.execute('PRAGMA busy_timeout = 5000')
        connection.execute('PRAGMA journal_mode = WAL')
        connection.execute('PRAGMA synchronous = NORMAL')
        database.chmod(0o600)
        for suffix in ('-wal', '-shm'):
            sidecar = safe_path(str(database) + suffix)
            if sidecar.exists():
                sidecar.chmod(0o600)
        return connection
    except BaseException:
        if connection is not None:
            connection.close()
        if staging is not None and staging.exists() and not staging.is_symlink():
            staging.unlink()
        if created and published:
            for sidecar in sidecars.values():
                if sidecar.exists() and not sidecar.is_symlink():
                    sidecar.unlink()
        raise


@atomic
def ensure_workspace(connection, project_root, *, repository_id=None, branch=None, observed_at=None):
    root = str(pathlib.Path(project_root).expanduser().resolve())
    location = database_path(connection)
    if location:
        external_path(location, [root])
    timestamp = observed_at or utc_now()
    _timestamp(timestamp, 'observed_at')
    row = connection.execute('SELECT workspace_id FROM workspaces WHERE project_root=?', (root,)).fetchone()
    if row:
        connection.execute('UPDATE workspaces SET repository_id=COALESCE(?,repository_id), branch=?, last_seen_at=? WHERE workspace_id=?',
                           (repository_id, branch, timestamp, row[0]))
        return row[0]
    identity = str(uuid.uuid4())
    connection.execute('INSERT INTO workspaces VALUES (?,?,?,?,?,?)', (identity, root, repository_id, branch, timestamp, timestamp))
    return identity


@atomic
def start_run(connection, workspace_id, operation, *, run_id=None, capture_mode='metadata',
              parent_run_id=None, git_head=None, worktree_state='unversioned', started_at=None):
    if operation not in OPERATIONS or capture_mode not in {'metadata', 'relevant'} or worktree_state not in WORKTREE_STATES:
        raise AuditValidationError('invalid operation, capture mode, or worktree state')
    run_id = run_id or str(uuid.uuid4())
    _text(run_id, 'run_id')
    previous = connection.execute('SELECT workspace_id,operation,capture_mode,parent_run_id,git_head,worktree_state,started_at FROM runs WHERE run_id=?', (run_id,)).fetchone()
    timestamp = started_at or (previous[6] if previous else utc_now())
    _timestamp(timestamp, 'started_at')
    values = (workspace_id, operation, capture_mode, parent_run_id, git_head, worktree_state, timestamp)
    if previous:
        if tuple(previous) != values:
            raise AuditConflict('run ID reused with a different payload')
        return run_id
    if not connection.execute('SELECT 1 FROM workspaces WHERE workspace_id=?', (workspace_id,)).fetchone():
        raise AuditValidationError(f'unknown workspace: {workspace_id}')
    if parent_run_id:
        parent = connection.execute('SELECT workspace_id FROM runs WHERE run_id=?', (parent_run_id,)).fetchone()
        if parent != (workspace_id,):
            raise AuditValidationError('parent run must belong to the same workspace')
    connection.execute('INSERT INTO runs(run_id,workspace_id,operation,capture_mode,parent_run_id,git_head,worktree_state,started_at,recorder_version) VALUES (?,?,?,?,?,?,?,?,?)',
                       (run_id, *values, RECORDER_VERSION))
    return run_id


def _store_explorer_details(connection, normalized):
    """Persist normalized explorer references after an event has been inserted."""
    explorer = normalized["details"].get("explorer")
    if explorer is None:
        return
    event_id = normalized["event_id"]
    run_id = normalized["run_id"]
    connection.execute(
        "INSERT INTO event_explorer(event_id,run_id,phase,summary,details_json) VALUES (?,?,?,?,?)",
        (event_id, run_id, explorer["phase"], explorer.get("summary"), canonical_json(explorer)),
    )
    for ref in explorer.get("message_refs", []):
        row = connection.execute(
            "SELECT run_id FROM captured_messages WHERE message_id=?", (ref["message_id"],)
        ).fetchone()
        if row != (run_id,):
            raise AuditValidationError("explorer message reference must belong to the event run")
        connection.execute(
            "INSERT INTO event_message_refs(event_id,message_id,purpose) VALUES (?,?,?)",
            (event_id, ref["message_id"], ref["purpose"]),
        )
    for ref in explorer.get("artifact_refs", []):
        connection.execute(
            "INSERT INTO event_artifacts(event_id,run_id,namespace,identifier,relationship,path,line,sha256,label,old_state,new_state,details_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event_id, run_id, ref["namespace"], ref["identifier"], ref["relationship"],
                ref.get("path"), ref.get("line"), ref.get("sha256"), ref.get("label"),
                ref.get("old_state"), ref.get("new_state"), canonical_json(ref),
            ),
        )


@atomic
def append_event(connection, event, *, sequence=None):
    normalized = validate_event(event)
    payload = canonical_json(normalized)
    prior = connection.execute('SELECT sequence,payload_json FROM events WHERE event_id=?', (normalized['event_id'],)).fetchone()
    if prior:
        if prior[1] != payload:
            raise AuditConflict('event ID reused with a different payload')
        return prior[0]
    run = connection.execute('SELECT workspace_id,operation FROM runs WHERE run_id=?', (normalized['run_id'],)).fetchone()
    if run != (normalized['workspace_id'], normalized['operation']):
        raise AuditValidationError('unknown run or event workspace/operation mismatch')
    sequence = sequence if sequence is not None else connection.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM events WHERE run_id=?', (normalized['run_id'],)).fetchone()[0]
    if type(sequence) is not int or sequence < 1:
        raise AuditValidationError('event sequence must be a positive integer')
    subject, details = normalized['subject'], normalized['details']
    if details.get('fidelity') == 'exact' and details.get('capture_source') != 'host':
        raise AuditValidationError('exact capture requires host provenance')
    try:
        connection.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (normalized['event_id'], normalized['run_id'], sequence, normalized['recorded_at'], normalized.get('occurred_at'),
             normalized['operation'], normalized['event_type'], *(subject.get(k) for k in ('milestone_id','task_label','status_path','old_state','new_state')),
             canonical_json(details['verification']) if 'verification' in details else None,
             canonical_json(details['file_actions']) if 'file_actions' in details else None,
             details.get('commit_sha'), canonical_json(details), payload))
        _store_explorer_details(connection, normalized)
    except sqlite3.IntegrityError as exc:
        raise AuditConflict('event sequence conflict') from exc
    return sequence


@atomic
def capture_message(connection, run_id, role, text, *, capture_source, fidelity, message_id=None,
                    sequence=None, captured_at=None, redaction_note=None):
    if capture_source not in CAPTURE_SOURCES or fidelity not in FIDELITIES:
        raise AuditValidationError('invalid capture source or fidelity')
    if fidelity == 'exact' and capture_source != 'host':
        raise AuditValidationError('exact capture requires host provenance')
    if connection.execute('SELECT capture_mode FROM runs WHERE run_id=?', (run_id,)).fetchone() != ('relevant',):
        raise AuditValidationError('message capture requires a relevant-capture run')
    _text(role, 'role'); _text(text, 'text')
    message_id = message_id or str(uuid.uuid4())
    prior = connection.execute('SELECT run_id,sequence,role,captured_at,text,capture_source,fidelity,redaction_note FROM captured_messages WHERE message_id=?', (message_id,)).fetchone()
    timestamp = captured_at or (prior[3] if prior else utc_now())
    _timestamp(timestamp, 'captured_at')
    if sequence is None:
        sequence = prior[1] if prior else connection.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM captured_messages WHERE run_id=?', (run_id,)).fetchone()[0]
    if type(sequence) is not int or sequence < 1:
        raise AuditValidationError('message sequence must be a positive integer')
    values = (run_id, sequence, role, timestamp, text, capture_source, fidelity, redaction_note)
    if prior:
        if prior != values:
            raise AuditConflict('message ID reused with a different payload')
        return message_id
    try:
        connection.execute('INSERT INTO captured_messages VALUES (?,?,?,?,?,?,?,?,?)', (message_id, *values))
    except sqlite3.IntegrityError as exc:
        raise AuditConflict('message sequence conflict') from exc
    return message_id


@atomic
def finish_run(connection, run_id, result, *, completed_at=None):
    if result not in RUN_RESULTS:
        raise AuditValidationError(f'unknown run result: {result}')
    prior = connection.execute('SELECT completed_at,result,workspace_id,operation FROM runs WHERE run_id=?', (run_id,)).fetchone()
    if not prior:
        raise AuditValidationError(f'unknown run: {run_id}')
    timestamp = completed_at or prior[0] or utc_now()
    _timestamp(timestamp, 'completed_at')
    if prior[1] is not None:
        if prior[:2] != (timestamp, result):
            raise AuditConflict('run already has a different terminal result')
        return
    append_event(connection, {'schema':'tabilet.audit.event/v1', 'event_id':f'{run_id}:finished',
        'run_id':run_id, 'workspace_id':prior[2], 'operation':prior[3], 'event_type':'run_finished',
        'recorded_at':timestamp, 'occurred_at':timestamp, 'subject':{},
        'details':{'schema':'tabilet.audit.details/v1','result':result}})
    connection.execute('UPDATE runs SET completed_at=?,result=? WHERE run_id=?', (timestamp,result,run_id))


def capture_snapshots(*args, **kwargs):
    raise AuditError('new snapshot capture is deferred; use index sync for Markdown lookup')


def open_readonly_database(path):
    database = safe_path(path)
    if not database.is_file():
        raise AuditError('read-only audit database must already exist')
    for suffix in ('-wal', '-shm', '-journal'):
        safe_path(str(database) + suffix)
    connection = sqlite3.connect(f'file:{quote(str(database))}?mode=ro', uri=True)
    try:
        connection.execute('PRAGMA foreign_keys = ON')
        connection.execute('PRAGMA query_only = ON')
        validate_database(connection)
        return connection
    except BaseException:
        connection.close()
        raise


def records(connection, sql, values=()):
    cursor = connection.execute(sql, values)
    names = [item[0] for item in cursor.description]
    return [dict(zip(names,row)) for row in cursor]


def pagination(limit, offset):
    if type(limit) is not int or not 1 <= limit <= 10000 or type(offset) is not int or offset < 0:
        raise AuditValidationError('limit must be 1..10000 and offset must be nonnegative')


def time_key(column):
    """Compare legacy and current UTC text at Python datetime's microsecond precision."""
    return (f"(substr({column},1,19) || '.' || substr(CASE WHEN substr({column},20,1)='.' "
            f"THEN rtrim(substr({column},21),'Z') ELSE '' END || '000000',1,6))")


def time_bound(value):
    _timestamp(value, 'timestamp')
    return _datetime.datetime.fromisoformat(value[:-1] + '+00:00').isoformat(timespec='microseconds')[:26]


def query_runs(connection, *, workspace_id=None, operation=None, milestone_id=None, task=None,
               since=None, until=None, limit=1000, offset=0):
    pagination(limit, offset)
    clauses, values = [], []
    for name, value in [('workspace_id',workspace_id),('operation',operation)]:
        if value is not None:
            clauses.append(f'r.{name}=?'); values.append(value)
    for name, value, comparison in [('started_at',since,'>='),('started_at',until,'<=')]:
        if value is not None:
            clauses.append(f'{time_key("r." + name)}{comparison}?'); values.append(time_bound(value))
    event_filters=[]
    event_values=[]
    for name,value in [('milestone_id',milestone_id),('task_label',task)]:
        if value is not None:
            event_filters.append(f'e.{name}=?'); event_values.append(value)
    if event_filters:
        clauses.append('EXISTS (SELECT 1 FROM events e WHERE e.run_id=r.run_id AND ' + ' AND '.join(event_filters) + ')')
        values.extend(event_values)
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    return records(connection, 'SELECT r.* FROM runs r'+where+f' ORDER BY {time_key("r.started_at")},run_id LIMIT ? OFFSET ?', (*values,limit,offset))


def query_events(connection, run_id=None, *, workspace_id=None, operation=None, milestone_id=None,
                 task=None, since=None, until=None, limit=10000, offset=0):
    pagination(limit, offset)
    clauses, values = [], []
    for name,value in [('e.run_id',run_id),('r.workspace_id',workspace_id),('e.operation',operation),('e.milestone_id',milestone_id),('e.task_label',task)]:
        if value is not None:
            clauses.append(f'{name}=?'); values.append(value)
    for value,comparison in [(since,'>='),(until,'<=')]:
        if value is not None:
            clauses.append(f'{time_key("e.recorded_at")}{comparison}?'); values.append(time_bound(value))
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    return records(connection, 'SELECT e.* FROM events e JOIN runs r USING(run_id)'+where+' ORDER BY '+time_key('r.started_at')+',e.run_id,e.sequence LIMIT ? OFFSET ?', (*values,limit,offset))


def query_snapshots(connection, workspace_id=None, *, kind=None, limit=10000, offset=0):
    pagination(limit, offset)
    clauses, values = [], []
    for key,value in [('workspace_id',workspace_id),('kind',kind)]:
        if value is not None:
            clauses.append(f'{key}=?'); values.append(value)
    where = ' WHERE '+' AND '.join(clauses) if clauses else ''
    return records(connection, 'SELECT snapshot_id,workspace_id,kind,source_path,sha256,captured_at,source_commit,worktree_state,source_run_id,predecessor_id,length(content) AS byte_length FROM snapshots'+where+' ORDER BY captured_at,snapshot_id LIMIT ? OFFSET ?', (*values,limit,offset))


def export_json(connection, *, workspace_id=None, include_content=False):
    """Complete durable export; private messages/bytes require explicit inclusion."""
    owner = not connection.in_transaction
    if owner:
        connection.execute('BEGIN')
    try:
        where, values = (' WHERE workspace_id=?',(workspace_id,)) if workspace_id else ('',())
        runs = records(connection, 'SELECT * FROM runs'+where+' ORDER BY started_at,run_id',values)
        has_explorer = 'event_explorer' in schema_tables(connection)
        for run in runs:
            run['events'] = records(connection,'SELECT * FROM events WHERE run_id=? ORDER BY sequence',(run['run_id'],))
            for observed in run['events']:
                explorer = records(connection, 'SELECT * FROM event_explorer WHERE event_id=?', (observed['event_id'],)) if has_explorer else []
                observed['explorer'] = explorer[0] if explorer else None
                if observed['explorer'] is not None:
                    observed['explorer']['message_refs'] = records(
                        connection, 'SELECT * FROM event_message_refs WHERE event_id=? ORDER BY message_id',
                        (observed['event_id'],),
                    )
                    observed['explorer']['artifact_refs'] = records(
                        connection, 'SELECT * FROM event_artifacts WHERE event_id=? ORDER BY namespace,identifier',
                        (observed['event_id'],),
                    )
            run['snapshot_observations'] = records(connection,'SELECT * FROM run_snapshots WHERE run_id=? ORDER BY source_path',(run['run_id'],))
            if include_content:
                run['messages'] = records(connection,'SELECT * FROM captured_messages WHERE run_id=? ORDER BY sequence',(run['run_id'],))
        snapshots = records(connection,'SELECT * FROM snapshots'+where+' ORDER BY captured_at,snapshot_id',values)
        for snapshot in snapshots:
            data = snapshot.pop('content')
            snapshot['byte_length'] = len(data)
            if include_content:
                snapshot['content_base64'] = base64.b64encode(data).decode('ascii')
        return canonical_json({'schema':'tabilet.audit.export/v2','includes_content':include_content,
            'workspaces':records(connection,'SELECT * FROM workspaces'+where,values), 'runs':runs,'snapshots':snapshots})
    finally:
        if owner:
            connection.rollback()


def restore_snapshot(connection, snapshot_id, destination):
    row = connection.execute('SELECT content,sha256 FROM snapshots WHERE snapshot_id=?',(snapshot_id,)).fetchone()
    if not row or hashlib.sha256(row[0]).hexdigest() != row[1]:
        raise AuditError('missing snapshot or content hash mismatch')
    path = _new_destination(destination, database_roots(connection))
    staging = safe_path(f'{path}.restore-{uuid.uuid4().hex}')
    try:
        with os.fdopen(private_create(staging),'wb') as output:
            output.write(row[0])
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(staging, path)
        except FileExistsError:
            raise FileExistsError(str(path))
    finally:
        if staging.exists() and not staging.is_symlink():
            staging.unlink()


def backup_database(connection, destination):
    validate_database(connection)
    path = _new_destination(destination, database_roots(connection))
    os.close(private_create(path))
    target = None
    try:
        target = sqlite3.connect(str(path))
        connection.backup(target)
        validate_database(target)
    except BaseException:
        if target is not None:
            target.close()
        if path.exists() and not path.is_symlink():
            path.unlink()
        for suffix in ('-wal', '-shm', '-journal'):
            sidecar = safe_path(str(path) + suffix)
            if sidecar.exists() and not sidecar.is_symlink():
                sidecar.unlink()
        raise
    finally:
        if target is not None:
            target.close()


def restore_database(source, destination):
    with contextlib.closing(open_readonly_database(source)) as connection:
        backup_database(connection, destination)

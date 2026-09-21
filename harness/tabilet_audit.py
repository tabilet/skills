#!/usr/bin/env python3
"""SQLite audit primitives for the memory-bank API runner.

The module is deliberately small and standard-library only.  It owns the
versioned event envelope and database schema; it does not execute project
commands or decide whether a project change is authorized.
"""

from __future__ import annotations

import datetime as _datetime
import json
import os
import pathlib
import re
import sqlite3
from typing import Any
import uuid


SCHEMA_NAME = "tabilet.audit/v1"
SCHEMA_VERSION = 1
RECORDER_VERSION = "tabilet-audit/1"

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
})
STATES = frozenset({"pending", "in_progress", "completed", "blocked", "cancelled", "historical"})
FIDELITIES = frozenset({"exact", "redacted", "summarized", "incomplete"})
CAPTURE_SOURCES = frozenset({"host", "agent", "import"})
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
"""


def utc_now() -> str:
    """Return the canonical UTC timestamp used by the audit schema."""

    return _datetime.datetime.now(_datetime.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize JSON details deterministically for idempotency comparisons."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    normalized["subject"] = subject
    normalized["details"] = details
    return normalized


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


def _owner_only(path: pathlib.Path, mode: int) -> None:
    """Create or tighten a local audit path's permissions."""

    try:
        path.chmod(mode)
    except OSError as exc:
        raise AuditError(f"unable to set owner-only permissions on {path}: {exc}") from exc


def open_database(path: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    """Open and validate a v1 audit database at an external path."""

    database = pathlib.Path(path).expanduser() if path is not None else default_database_path()
    if database.exists() and database.is_symlink():
        raise AuditError(f"audit database may not be a symlink: {database}")
    parent = database.parent
    if parent.exists() and parent.is_symlink():
        raise AuditError(f"audit database parent may not be a symlink: {parent}")
    database = database.absolute()
    parent = database.parent
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _owner_only(parent, 0o700)
    if database.exists() and not database.is_file():
        raise AuditError(f"audit database is not a regular file: {database}")

    connection = sqlite3.connect(str(database), timeout=5.0)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise AuditError("SQLite foreign-key enforcement could not be enabled")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        current = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if current > SCHEMA_VERSION:
            raise AuditError(
                f"audit database schema {current} is newer than supported {SCHEMA_VERSION}"
            )
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT INTO schema_meta(key, value) VALUES('schema', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (SCHEMA_NAME,),
        )
        connection.execute(
            "INSERT INTO schema_meta(key, value) VALUES('recorder_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (RECORDER_VERSION,),
        )
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
        stored_schema = connection.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema'"
        ).fetchone()[0]
        if stored_schema != SCHEMA_NAME:
            raise AuditError(f"unsupported audit schema: {stored_schema}")
        _owner_only(database, 0o600)
        return connection
    except Exception:
        connection.close()
        raise


def ensure_workspace(
    connection: sqlite3.Connection,
    project_root: str | os.PathLike[str],
    *,
    repository_id: str | None = None,
    branch: str | None = None,
    observed_at: str | None = None,
) -> str:
    """Return the stable workspace ID for one local checkout."""

    root = pathlib.Path(project_root).expanduser().absolute()
    root_text = str(root)
    timestamp = observed_at or utc_now()
    _timestamp(timestamp, "observed_at")
    with connection:
        row = connection.execute(
            "SELECT workspace_id FROM workspaces WHERE project_root = ?", (root_text,)
        ).fetchone()
        if row:
            connection.execute(
                "UPDATE workspaces SET repository_id = COALESCE(?, repository_id), "
                "branch = COALESCE(?, branch), last_seen_at = ? WHERE workspace_id = ?",
                (repository_id, branch, timestamp, row[0]),
            )
            return row[0]
        workspace_id = str(uuid.uuid4())
        connection.execute(
            "INSERT INTO workspaces(workspace_id, project_root, repository_id, branch, created_at, last_seen_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (workspace_id, root_text, repository_id, branch, timestamp, timestamp),
        )
        return workspace_id


def start_run(
    connection: sqlite3.Connection,
    workspace_id: str,
    operation: str,
    *,
    run_id: str | None = None,
    capture_mode: str = "metadata",
    parent_run_id: str | None = None,
    git_head: str | None = None,
    worktree_state: str = "unversioned",
    started_at: str | None = None,
) -> str:
    """Create one run record and return its ID."""

    if operation not in OPERATIONS:
        raise AuditValidationError(f"unknown operation: {operation}")
    if capture_mode not in {"metadata", "relevant"}:
        raise AuditValidationError(f"unknown capture mode: {capture_mode}")
    if worktree_state not in WORKTREE_STATES:
        raise AuditValidationError(f"unknown worktree state: {worktree_state}")
    run_id = run_id or str(uuid.uuid4())
    timestamp = started_at or utc_now()
    _text(workspace_id, "workspace_id")
    _text(run_id, "run_id")
    _timestamp(timestamp, "started_at")
    with connection:
        if not connection.execute(
            "SELECT 1 FROM workspaces WHERE workspace_id = ?", (workspace_id,)
        ).fetchone():
            raise AuditValidationError(f"unknown workspace: {workspace_id}")
        connection.execute(
            "INSERT INTO runs(run_id, workspace_id, operation, started_at, recorder_version, "
            "capture_mode, parent_run_id, git_head, worktree_state) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, workspace_id, operation, timestamp, RECORDER_VERSION, capture_mode,
             parent_run_id, git_head, worktree_state),
        )
    return run_id


def _event_payload(event: dict[str, Any]) -> str:
    return canonical_json(event)


def append_event(
    connection: sqlite3.Connection,
    event: dict[str, Any],
    *,
    sequence: int | None = None,
) -> int:
    """Append one validated event and return its run-local sequence."""

    normalized = validate_event(event)
    event_id = normalized["event_id"]
    run_id = normalized["run_id"]
    payload = _event_payload(normalized)
    existing = connection.execute(
        "SELECT sequence, payload_json FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if existing:
        if existing[1] != payload:
            raise AuditConflict(f"event ID reused with a different payload: {event_id}")
        return int(existing[0])
    run = connection.execute(
        "SELECT workspace_id, operation FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if not run:
        raise AuditValidationError(f"unknown run: {run_id}")
    if run[1] != normalized["operation"]:
        raise AuditValidationError("event operation does not match its run")
    if run[0] != normalized["workspace_id"]:
        raise AuditValidationError("event workspace does not match its run")
    if sequence is None:
        sequence = connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 FROM events WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
    if not isinstance(sequence, int) or sequence < 1:
        raise AuditValidationError("event sequence must be a positive integer")
    subject = normalized["subject"]
    details = normalized["details"]
    verification = details.get("verification")
    file_actions = details.get("file_actions")
    commit_sha = details.get("commit_sha")
    with connection:
        try:
            connection.execute(
                "INSERT INTO events(event_id, run_id, sequence, recorded_at, occurred_at, operation, "
                "event_type, milestone_id, task_label, status_path, old_state, new_state, "
                "verification_json, file_actions_json, commit_sha, details_json, payload_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event_id, run_id, sequence, normalized["recorded_at"], normalized.get("occurred_at"),
                 normalized["operation"], normalized["event_type"], subject.get("milestone_id"),
                 subject.get("task_label"), subject.get("status_path"), subject.get("old_state"),
                 subject.get("new_state"), canonical_json(verification) if verification is not None else None,
                 canonical_json(file_actions) if file_actions is not None else None, commit_sha,
                 canonical_json(details), payload),
            )
        except sqlite3.IntegrityError as exc:
            raise AuditConflict(f"event sequence or ID conflict: {event_id}") from exc
    return sequence


def capture_message(
    connection: sqlite3.Connection,
    run_id: str,
    role: str,
    text: str,
    *,
    capture_source: str,
    fidelity: str,
    message_id: str | None = None,
    sequence: int | None = None,
    captured_at: str | None = None,
    redaction_note: str | None = None,
) -> str:
    """Store one explicitly selected visible message."""

    if capture_source not in CAPTURE_SOURCES:
        raise AuditValidationError(f"unknown capture source: {capture_source}")
    if fidelity not in FIDELITIES:
        raise AuditValidationError(f"unknown message fidelity: {fidelity}")
    if not isinstance(run_id, str) or not run_id.strip():
        raise AuditValidationError("run_id must be a non-empty string")
    _text(role, "role")
    _text(text, "text")
    captured_at = captured_at or utc_now()
    _timestamp(captured_at, "captured_at")
    if not connection.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone():
        raise AuditValidationError(f"unknown run: {run_id}")
    message_id = message_id or str(uuid.uuid4())
    if sequence is None:
        sequence = connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 FROM captured_messages WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
    if not isinstance(sequence, int) or sequence < 1:
        raise AuditValidationError("message sequence must be a positive integer")
    existing = connection.execute(
        "SELECT run_id, sequence, role, captured_at, text, capture_source, fidelity, redaction_note "
        "FROM captured_messages WHERE message_id = ?", (message_id,)
    ).fetchone()
    values = (run_id, sequence, role, captured_at, text, capture_source, fidelity, redaction_note)
    if existing:
        if tuple(existing) != values:
            raise AuditConflict(f"message ID reused with a different payload: {message_id}")
        return message_id
    with connection:
        try:
            connection.execute(
                "INSERT INTO captured_messages(message_id, run_id, sequence, role, captured_at, text, "
                "capture_source, fidelity, redaction_note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (message_id, *values),
            )
        except sqlite3.IntegrityError as exc:
            raise AuditConflict(f"message sequence or ID conflict: {message_id}") from exc
    return message_id


def finish_run(
    connection: sqlite3.Connection,
    run_id: str,
    result: str,
    *,
    completed_at: str | None = None,
) -> None:
    """Set a run's terminal result once evidence is available."""

    if result not in RUN_RESULTS:
        raise AuditValidationError(f"unknown run result: {result}")
    completed_at = completed_at or utc_now()
    _timestamp(completed_at, "completed_at")
    row = connection.execute(
        "SELECT completed_at, result FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if not row:
        raise AuditValidationError(f"unknown run: {run_id}")
    if row[0] is not None or row[1] is not None:
        if row[0] == completed_at and row[1] == result:
            return
        raise AuditConflict(f"run already has a different terminal result: {run_id}")
    with connection:
        connection.execute(
            "UPDATE runs SET completed_at = ?, result = ? WHERE run_id = ?",
            (completed_at, result, run_id),
        )

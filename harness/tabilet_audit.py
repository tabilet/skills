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

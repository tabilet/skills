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


SCHEMA_NAME = "tabilet.audit/v4"
SCHEMA_VERSION = 4
RECORDER_VERSION = "tabilet-audit/4"
TOOLKIT_INTERFACE = 1

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
    "message_content_purged",
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
PROVENANCE_INVOCATION_KINDS = frozenset({"api_runner", "interactive_skill", "host_operation"})
PROVENANCE_CAPTURE_METHODS = frozenset({"automatic", "instruction_driven", "imported"})
FINGERPRINT_FIDELITIES = frozenset({"exact", "partial", "unavailable"})
COVERAGE_SCOPES = frozenset({"skill_conversation", "api_runner_conversation"})
COVERAGE_STATES = frozenset({"not_requested", "complete", "partial", "missing"})
CONTENT_STATES = frozenset({"none", "available", "partially_purged", "purged"})
MAX_RELEVANT_MESSAGE_CHARACTERS = 1024
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
        if relationship in {"created", "changed", "retired"} and phase != "applied":
            raise AuditValidationError(
                f"explorer relationship {relationship} requires the applied phase"
            )
        path = ref.get("path")
        if path is not None:
            _text(path, "explorer.artifact_refs.path")
            parts = pathlib.PurePosixPath(path).parts
            if ("\\" in path or pathlib.PurePosixPath(path).is_absolute()
                    or ".." in parts or "." in parts or not parts):
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


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise AuditValidationError(f"{field} must be a lowercase SHA-256 digest")
    return value


def validate_provenance(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AuditValidationError("provenance must be a JSON object")
    normalized = dict(value)
    for field in ("invocation_kind", "instruction_set_name", "capture_method", "fingerprint_fidelity"):
        _text(normalized.get(field), f"provenance.{field}")
    if normalized["invocation_kind"] not in PROVENANCE_INVOCATION_KINDS:
        raise AuditValidationError("unknown provenance invocation kind")
    if normalized["capture_method"] not in PROVENANCE_CAPTURE_METHODS:
        raise AuditValidationError("unknown provenance capture method")
    if normalized["fingerprint_fidelity"] not in FINGERPRINT_FIDELITIES:
        raise AuditValidationError("unknown instruction fingerprint fidelity")
    for field in ("instruction_set_version", "host_agent", "host_version", "provider", "model", "host_session_ref"):
        if normalized.get(field) is not None and not isinstance(normalized[field], str):
            raise AuditValidationError(f"provenance.{field} must be a string or null")
    session_ref = normalized.get("host_session_ref")
    if session_ref:
        # This identifier comes from a host, not from the filesystem.  Check
        # both path dialects because a database can be copied between hosts.
        # Rejecting separators also rules out relative traversal and ordinary
        # path components instead of merely rejecting absolute POSIX paths.
        if ("/" in session_ref or "\\" in session_ref or session_ref in {".", ".."}
                or session_ref.startswith("~")
                or pathlib.PurePosixPath(session_ref).is_absolute()
                or pathlib.PureWindowsPath(session_ref).is_absolute()
                or pathlib.PureWindowsPath(session_ref).drive):
            raise AuditValidationError("host session reference must be opaque, not a path")
    resources = normalized.get("resources", [])
    if not isinstance(resources, list):
        raise AuditValidationError("provenance.resources must be an array")
    pairs = []
    seen = set()
    for resource in resources:
        if not isinstance(resource, dict):
            raise AuditValidationError("provenance resource must be an object")
        name = _text(resource.get("name"), "provenance resource name")
        if pathlib.PurePath(name).is_absolute() or name.startswith("~") or re.match(r"^[A-Za-z]:[\\/]", name):
            raise AuditValidationError("provenance resource names must not be absolute paths")
        digest = _digest(resource.get("sha256"), "provenance resource sha256")
        if name in seen:
            raise AuditValidationError("duplicate provenance resource name")
        seen.add(name)
        pairs.append({"name": name, "sha256": digest})
    pairs.sort(key=lambda item: item["name"].encode("utf-8"))
    normalized["resources"] = pairs
    aggregate = normalized.get("aggregate_sha256")
    if normalized["fingerprint_fidelity"] == "unavailable":
        if pairs or aggregate is not None:
            raise AuditValidationError("unavailable fingerprints cannot include resources or an aggregate")
        normalized["aggregate_sha256"] = None
    else:
        if not pairs:
            raise AuditValidationError("available fingerprints require at least one resource")
        computed = hashlib.sha256(canonical_json(pairs).encode("utf-8")).hexdigest()
        if aggregate != computed:
            raise AuditValidationError("instruction fingerprint aggregate does not match resources")
        normalized["aggregate_sha256"] = aggregate
    return normalized


def _coverage_counts(value):
    count_fields = {"exact_count", "redacted_count", "summarized_count", "incomplete_count"}
    unknown = sorted(key for key in value if isinstance(key, str)
                     and key.lower().endswith(("count", "counts")) and key not in count_fields)
    if unknown:
        raise AuditValidationError(f"unknown coverage count field: {', '.join(unknown)}")
    counts = {}
    for field in sorted(count_fields):
        item = value.get(field, 0)
        if type(item) is not int or item < 0:
            raise AuditValidationError(f"coverage {field} must be a non-negative integer")
        counts[field] = item
    return counts


def bounded_message_evidence(text: str, *, limit: int = MAX_RELEVANT_MESSAGE_CHARACTERS) -> tuple[str, bool]:
    """Return a clearly incomplete, bounded extract for automatic recorders.

    Interactive agents should write a semantic summary themselves.  This helper
    is only the safe fallback for an automated recorder that cannot ask a model
    a second question: it preserves a small, marked extract and never labels it
    as exact or summarized evidence.
    """
    if len(text) <= limit:
        return text, False
    prefix = "[Incomplete evidence: source exceeded 1024 characters] "
    available = limit - len(prefix) - 1
    excerpt = " ".join(text.split())[:available]
    if len(excerpt) > available:
        excerpt = excerpt[:available]
    if " " in excerpt and len(" ".join(text.split())) > len(excerpt):
        excerpt = excerpt.rsplit(" ", 1)[0]
    return prefix + excerpt + "…", True


def validate_coverage(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AuditValidationError("coverage must be a JSON object")
    normalized = dict(value)
    for field in ("coverage_id", "run_id", "scope", "coverage", "content_state", "capture_method"):
        _text(normalized.get(field), f"coverage.{field}")
    if normalized["scope"] not in COVERAGE_SCOPES:
        raise AuditValidationError("unknown coverage scope")
    if normalized["coverage"] not in COVERAGE_STATES:
        raise AuditValidationError("unknown coverage state")
    if normalized["content_state"] not in CONTENT_STATES:
        raise AuditValidationError("unknown coverage content state")
    if normalized["capture_method"] not in PROVENANCE_CAPTURE_METHODS:
        raise AuditValidationError("unknown coverage capture method")
    counts = _coverage_counts(normalized)
    normalized.update(counts)
    timestamp = normalized.get("observed_at") or utc_now()
    _timestamp(timestamp, "coverage.observed_at")
    normalized["observed_at"] = timestamp
    if normalized.get("reason") is not None and not isinstance(normalized["reason"], str):
        raise AuditValidationError("coverage.reason must be a string or null")
    if normalized["coverage"] in {"not_requested", "missing"} and (
        normalized["content_state"] != "none" or sum(counts.values())
    ):
        raise AuditValidationError("not_requested and missing coverage require empty content")
    if normalized["coverage"] == "complete" and (
        normalized["content_state"] != "available" or not sum(counts.values()) or counts["incomplete_count"]
    ):
        raise AuditValidationError("complete coverage requires available, non-incomplete content")
    return normalized


def _validate_coverage_evidence(connection, coverage: dict[str, Any]) -> None:
    """Require a new coverage observation to describe this run's envelopes.

    Coverage is an assertion about the evidence that is actually present, not
    an independently supplied transcript count.  A retry returns its original
    immutable observation before this check, because a later purge must not
    make an earlier observation unverifiable retroactively.
    """
    if "captured_message_content" not in schema_tables(connection):
        raise AuditValidationError("coverage observations require the v4 message-content schema")
    rows = connection.execute(
        """SELECT m.fidelity,
                  c.message_id IS NOT NULL AS content_available,
                  t.message_id IS NOT NULL AS content_purged
             FROM captured_messages m
             LEFT JOIN captured_message_content c ON c.message_id=m.message_id
             LEFT JOIN message_content_tombstones t ON t.message_id=m.message_id
             WHERE m.run_id=?""",
        (coverage["run_id"],),
    ).fetchall()
    counts = {field: 0 for field in ("exact_count", "redacted_count", "summarized_count", "incomplete_count")}
    available = purged = 0
    for fidelity, content_available, content_purged in rows:
        counts[f"{fidelity}_count"] += 1
        available += bool(content_available)
        purged += bool(content_purged)
    submitted_counts = {field: coverage[field] for field in counts}
    if coverage["coverage"] in {"not_requested", "missing"}:
        if rows:
            raise AuditValidationError("empty coverage conflicts with captured message envelopes")
        return
    if not rows or submitted_counts != counts:
        raise AuditValidationError("coverage fidelity counts must exactly match captured message envelopes")
    if purged == len(rows):
        actual_state = "purged"
    elif purged:
        actual_state = "partially_purged"
    elif available == len(rows):
        actual_state = "available"
    else:
        raise AuditValidationError("captured message content is unavailable without a purge tombstone")
    if coverage["content_state"] != actual_state:
        raise AuditValidationError("coverage content state conflicts with captured message evidence")


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

# SQLite 13 additions are applied after the v3 schema has been validated.  The
# legacy `text` column remains an empty compatibility field on envelopes;
# actual message bytes live only in captured_message_content so a direct query
# of captured_messages cannot expose relevant captured text.
V4_SQL = """
ALTER TABLE captured_messages ADD COLUMN content_sha256 TEXT;
ALTER TABLE captured_messages ADD COLUMN content_byte_length INTEGER;
CREATE TABLE IF NOT EXISTS captured_message_content (
 message_id TEXT PRIMARY KEY REFERENCES captured_messages(message_id),
 content BLOB NOT NULL,
 sha256 TEXT NOT NULL,
 byte_length INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS run_provenance (
 run_id TEXT PRIMARY KEY REFERENCES runs(run_id),
 invocation_kind TEXT NOT NULL,
 instruction_set_name TEXT NOT NULL,
 instruction_set_version TEXT,
 host_agent TEXT,
 host_version TEXT,
 provider TEXT,
 model TEXT,
 host_session_ref TEXT,
 capture_method TEXT NOT NULL,
 fingerprint_fidelity TEXT NOT NULL,
 resources_json TEXT NOT NULL,
 aggregate_sha256 TEXT,
 recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS coverage_observations (
 coverage_id TEXT PRIMARY KEY,
 run_id TEXT NOT NULL REFERENCES runs(run_id),
 scope TEXT NOT NULL,
 coverage TEXT NOT NULL,
 content_state TEXT NOT NULL,
 exact_count INTEGER NOT NULL DEFAULT 0,
 redacted_count INTEGER NOT NULL DEFAULT 0,
 summarized_count INTEGER NOT NULL DEFAULT 0,
 incomplete_count INTEGER NOT NULL DEFAULT 0,
 observed_at TEXT NOT NULL,
 capture_method TEXT NOT NULL,
 reason TEXT
);
CREATE TABLE IF NOT EXISTS provenance_resources (
 run_id TEXT NOT NULL REFERENCES run_provenance(run_id),
 logical_name TEXT NOT NULL,
 sha256 TEXT NOT NULL,
 PRIMARY KEY(run_id, logical_name)
);
CREATE TABLE IF NOT EXISTS message_content_tombstones (
 message_id TEXT PRIMARY KEY REFERENCES captured_messages(message_id),
 purged_at TEXT NOT NULL,
 reason TEXT NOT NULL,
 event_id TEXT UNIQUE REFERENCES events(event_id)
);
CREATE INDEX IF NOT EXISTS run_provenance_instruction ON run_provenance(instruction_set_name, instruction_set_version);
CREATE INDEX IF NOT EXISTS run_provenance_host_model ON run_provenance(host_agent, model);
CREATE INDEX IF NOT EXISTS coverage_run_observed ON coverage_observations(run_id, observed_at, coverage_id);
CREATE INDEX IF NOT EXISTS coverage_filter ON coverage_observations(capture_method, coverage);
CREATE TRIGGER IF NOT EXISTS immutable_events_update BEFORE UPDATE ON events
 BEGIN SELECT RAISE(ABORT, 'durable events are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_events_delete BEFORE DELETE ON events
 BEGIN SELECT RAISE(ABORT, 'durable events are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_messages_update BEFORE UPDATE ON captured_messages
 WHEN NOT (NEW.message_id=OLD.message_id AND NEW.run_id=OLD.run_id AND NEW.sequence=OLD.sequence AND
           NEW.role=OLD.role AND NEW.captured_at=OLD.captured_at AND NEW.capture_source=OLD.capture_source AND
           NEW.fidelity=OLD.fidelity AND (NEW.redaction_note IS OLD.redaction_note) AND
           NEW.content_sha256=OLD.content_sha256 AND NEW.content_byte_length=OLD.content_byte_length AND
           NEW.text='' AND OLD.text<>'' AND EXISTS (SELECT 1 FROM message_content_tombstones WHERE message_id=OLD.message_id))
 BEGIN SELECT RAISE(ABORT, 'message envelopes are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_messages_delete BEFORE DELETE ON captured_messages
 BEGIN SELECT RAISE(ABORT, 'message envelopes are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_provenance_update BEFORE UPDATE ON run_provenance
 BEGIN SELECT RAISE(ABORT, 'run provenance is immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_provenance_delete BEFORE DELETE ON run_provenance
 BEGIN SELECT RAISE(ABORT, 'run provenance is immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_provenance_resources_update BEFORE UPDATE ON provenance_resources
 BEGIN SELECT RAISE(ABORT, 'provenance resources are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_provenance_resources_delete BEFORE DELETE ON provenance_resources
 BEGIN SELECT RAISE(ABORT, 'provenance resources are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_coverage_update BEFORE UPDATE ON coverage_observations
 BEGIN SELECT RAISE(ABORT, 'coverage observations are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_coverage_delete BEFORE DELETE ON coverage_observations
 BEGIN SELECT RAISE(ABORT, 'coverage observations are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_tombstones_update BEFORE UPDATE ON message_content_tombstones
 BEGIN SELECT RAISE(ABORT, 'purge tombstones are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_tombstones_delete BEFORE DELETE ON message_content_tombstones
 BEGIN SELECT RAISE(ABORT, 'purge tombstones are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_explorer_update BEFORE UPDATE ON event_explorer
 BEGIN SELECT RAISE(ABORT, 'explorer references are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_explorer_delete BEFORE DELETE ON event_explorer
 BEGIN SELECT RAISE(ABORT, 'explorer references are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_message_refs_update BEFORE UPDATE ON event_message_refs
 BEGIN SELECT RAISE(ABORT, 'explorer references are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_message_refs_delete BEFORE DELETE ON event_message_refs
 BEGIN SELECT RAISE(ABORT, 'explorer references are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_artifacts_update BEFORE UPDATE ON event_artifacts
 BEGIN SELECT RAISE(ABORT, 'explorer references are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_artifacts_delete BEFORE DELETE ON event_artifacts
 BEGIN SELECT RAISE(ABORT, 'explorer references are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_snapshots_update BEFORE UPDATE ON snapshots
 BEGIN SELECT RAISE(ABORT, 'legacy snapshots are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_snapshots_delete BEFORE DELETE ON snapshots
 BEGIN SELECT RAISE(ABORT, 'legacy snapshots are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_run_snapshots_update BEFORE UPDATE ON run_snapshots
 BEGIN SELECT RAISE(ABORT, 'snapshot observations are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_run_snapshots_delete BEFORE DELETE ON run_snapshots
 BEGIN SELECT RAISE(ABORT, 'snapshot observations are immutable'); END;
CREATE TRIGGER IF NOT EXISTS content_delete_requires_tombstone BEFORE DELETE ON captured_message_content
 WHEN NOT EXISTS (SELECT 1 FROM message_content_tombstones WHERE message_id=OLD.message_id)
 BEGIN SELECT RAISE(ABORT, 'message content requires a purge tombstone'); END;
CREATE TRIGGER IF NOT EXISTS immutable_message_content_update BEFORE UPDATE ON captured_message_content
 BEGIN SELECT RAISE(ABORT, 'message content is immutable'); END;
CREATE TRIGGER IF NOT EXISTS runs_one_way_finalization BEFORE UPDATE ON runs
 WHEN NOT (
   NEW.run_id=OLD.run_id AND NEW.workspace_id=OLD.workspace_id AND
   NEW.operation=OLD.operation AND NEW.started_at=OLD.started_at AND
   NEW.recorder_version=OLD.recorder_version AND NEW.capture_mode=OLD.capture_mode AND
   (NEW.parent_run_id IS OLD.parent_run_id) AND (NEW.git_head IS OLD.git_head) AND
   NEW.worktree_state=OLD.worktree_state AND OLD.result IS NULL AND
   NEW.result IN ('completed','blocked','failed','cancelled','interrupted','unknown') AND
   NEW.completed_at IS NOT NULL
 )
 BEGIN SELECT RAISE(ABORT, 'runs allow only one-way finalization'); END;
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


def _apply_v4_schema(connection):
    """Apply v4 tables and guards to a connection already carrying v1-v3 tables."""

    columns = {row[1] for row in connection.execute("PRAGMA table_info(captured_messages)")}
    if "content_sha256" not in columns:
        connection.execute("ALTER TABLE captured_messages ADD COLUMN content_sha256 TEXT")
    if "content_byte_length" not in columns:
        connection.execute("ALTER TABLE captured_messages ADD COLUMN content_byte_length INTEGER")
    for statement in _iter_statements(V4_SQL):
        statement = statement.strip()
        if not statement.startswith("CREATE TRIGGER") and not statement.startswith("ALTER TABLE captured_messages ADD COLUMN"):
            connection.execute(statement)
    _separate_v4_message_envelopes(connection)
    for statement in _v4_trigger_statements():
        connection.execute(statement)


def _expected_schema(version):
    expected = sqlite3.connect(":memory:")
    expected.execute("PRAGMA foreign_keys=ON")
    expected.executescript(SCHEMA_SQL)
    if version >= 2:
        expected.executescript(INDEX_SQL)
    if version >= 3:
        expected.executescript(EXPLORER_SQL)
    if version >= 4:
        _apply_v4_schema(expected)
    return expected


def _execute_statements(connection, script):
    for statement in _iter_statements(script):
        connection.execute(statement)


def _iter_statements(script):
    buffer = ""
    for line in script.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                yield statement
            buffer = ""
    if buffer.strip():
        yield buffer.strip()


def _v4_trigger_statements():
    return [statement for statement in _iter_statements(V4_SQL)
            if statement.startswith("CREATE TRIGGER")]


def _v4_message_trigger():
    return next(statement for statement in _v4_trigger_statements()
                if statement.startswith("CREATE TRIGGER IF NOT EXISTS immutable_messages_update"))


def _separate_v4_message_envelopes(connection):
    """Move transitional v4 envelope text into content storage and erase it.

    Earlier v4 writers temporarily duplicated text in the compatibility column.
    A writer repairs that representation transactionally; read-only opens refuse
    modified guards and never perform this cleanup.
    """
    connection.execute("DROP TRIGGER IF EXISTS immutable_messages_update")
    try:
        rows = connection.execute(
            "SELECT message_id,text,content_sha256,content_byte_length FROM captured_messages"
        ).fetchall()
        for message_id, text, envelope_digest, envelope_length in rows:
            content = connection.execute(
                "SELECT content,sha256,byte_length FROM captured_message_content WHERE message_id=?",
                (message_id,),
            ).fetchone()
            if content is None:
                raw = (text or "").encode("utf-8")
                digest = hashlib.sha256(raw).hexdigest()
                byte_length = len(raw)
                if envelope_digest is not None and envelope_digest != digest:
                    raise AuditError("captured message envelope hash does not match recoverable content")
                if envelope_length is not None and envelope_length != byte_length:
                    raise AuditError("captured message envelope length does not match recoverable content")
                connection.execute(
                    "INSERT INTO captured_message_content(message_id,content,sha256,byte_length) VALUES (?,?,?,?)",
                    (message_id, raw, digest, byte_length),
                )
            else:
                raw, digest, byte_length = bytes(content[0]), content[1], content[2]
                if hashlib.sha256(raw).hexdigest() != digest or len(raw) != byte_length:
                    raise AuditError("captured message content does not match its envelope")
                if envelope_digest is not None and envelope_digest != digest:
                    raise AuditError("captured message envelope hash does not match content")
                if envelope_length is not None and envelope_length != byte_length:
                    raise AuditError("captured message envelope length does not match content")
            connection.execute(
                "UPDATE captured_messages SET text='',content_sha256=?,content_byte_length=? WHERE message_id=?",
                (digest, byte_length, message_id),
            )
    finally:
        connection.execute(_v4_message_trigger())


def _ddl_signature(value):
    return re.sub(r"\s+", " ", value.strip()).lower()


def validate_database(connection, *, version_override=None, allow_unmarked=False):
    actual_version = connection.execute('PRAGMA user_version').fetchone()[0]
    version = actual_version if version_override is None else version_override
    if version not in (1, 2, 3, SCHEMA_VERSION):
        raise AuditError(f"unsupported audit database version: {version}")
    try:
        marker = connection.execute("SELECT value FROM schema_meta WHERE key='schema'").fetchone()
        if not allow_unmarked and marker != (f'tabilet.audit/v{version}',):
            raise AuditError('unsupported audit database identity')
        # Verify every required table/column before any schema or permission mutation.
        expected = _expected_schema(version)
        try:
            for table in schema_tables(expected):
                columns = {r[1]: tuple(r[2:6]) for r in expected.execute(f'PRAGMA table_info({table})')}
                actual = {r[1]: tuple(r[2:6]) for r in connection.execute(f'PRAGMA table_info({table})')}
                if any(actual.get(name) != definition for name, definition in columns.items()):
                    raise AuditError(f'incomplete audit schema: {table}')
                expected_foreign = {tuple(r[2:8]) for r in expected.execute(f'PRAGMA foreign_key_list({table})')}
                actual_foreign = {tuple(r[2:8]) for r in connection.execute(f'PRAGMA foreign_key_list({table})')}
                if not expected_foreign.issubset(actual_foreign):
                    raise AuditError(f'incomplete audit foreign keys: {table}')
                def unique_signatures(database):
                    result = set()
                    for item in database.execute(f'PRAGMA index_list({table})'):
                        if item[2]:
                            result.add(tuple(row[2] for row in database.execute(
                                f'PRAGMA index_info({json.dumps(item[1])})')))
                    return result
                if not unique_signatures(expected).issubset(unique_signatures(connection)):
                    raise AuditError(f'incomplete audit uniqueness constraints: {table}')
            required_indexes = {
                row[0]: tuple(item[2] for item in expected.execute(
                    f'PRAGMA index_info({json.dumps(row[0])})'))
                for row in expected.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
                )
            }
            for name, columns in required_indexes.items():
                actual_index = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (name,)
                ).fetchone()
                actual_columns = tuple(item[2] for item in connection.execute(
                    f'PRAGMA index_info({json.dumps(name)})')) if actual_index else ()
                if actual_columns != columns:
                    raise AuditError(f'incomplete audit index: {name}')
            if version >= 4:
                expected_triggers = {
                    name: (table, _ddl_signature(sql))
                    for name, table, sql in expected.execute(
                        "SELECT name,tbl_name,sql FROM sqlite_master WHERE type='trigger'"
                    )
                }
                actual_triggers = {
                    name: (table, _ddl_signature(sql))
                    for name, table, sql in connection.execute(
                        "SELECT name,tbl_name,sql FROM sqlite_master WHERE type='trigger'"
                    )
                }
                for name, definition in expected_triggers.items():
                    if actual_triggers.get(name) != definition:
                        raise AuditError(f'incomplete audit guard: {name}')
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
    published_identity = None
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
        # Set this before legacy envelope text is moved or deleted.
        connection.execute('PRAGMA secure_delete = ON')
        moved_content = False
        if version < SCHEMA_VERSION:
            moved_content = version != 0
            connection.execute('BEGIN IMMEDIATE')
            try:
                if version == 0:
                    _execute_statements(connection, SCHEMA_SQL)
                if version < 2:
                    _execute_statements(connection, INDEX_SQL)
                if version < 3:
                    _execute_statements(connection, EXPLORER_SQL)
                _apply_v4_schema(connection)
                # CREATE IF NOT EXISTS must not bless a conflicting future table
                # that happened to exist in an older database. Validate the
                # complete target schema while the migration is still rollbackable.
                validate_database(connection, version_override=SCHEMA_VERSION, allow_unmarked=True)
                connection.execute("INSERT OR REPLACE INTO schema_meta VALUES ('schema', ?)", (SCHEMA_NAME,))
                connection.execute("INSERT OR REPLACE INTO schema_meta VALUES ('recorder_version', ?)", (RECORDER_VERSION,))
                connection.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
                validate_database(connection)
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        elif connection.execute("SELECT 1 FROM captured_messages WHERE text<>'' LIMIT 1").fetchone():
            # Repair the short-lived transitional v4 envelope representation
            # before this writer can add more evidence.  Read-only access never
            # executes this branch.
            connection.execute('BEGIN IMMEDIATE')
            try:
                _separate_v4_message_envelopes(connection)
                validate_database(connection)
                connection.commit()
                moved_content = True
            except BaseException:
                connection.rollback()
                raise
        if created:
            connection.close()
            connection = None
            staged = staging.stat()
            try:
                os.link(staging, database)
            except FileExistsError:
                raise AuditError('audit database destination appeared during creation')
            published = True
            published_identity = (staged.st_dev, staged.st_ino)
            staging.unlink()
            connection = sqlite3.connect(str(database), timeout=5)
            connection.execute('PRAGMA foreign_keys = ON')
            connection.execute('PRAGMA busy_timeout = 5000')
        connection.execute('PRAGMA journal_mode = WAL')
        connection.execute('PRAGMA synchronous = NORMAL')
        if moved_content:
            # Migration is already committed. A busy checkpoint is best effort;
            # the next writer can retry it without changing audit records.
            try:
                connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            except sqlite3.DatabaseError:
                pass
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
            if published_identity is not None and database.exists() and not database.is_symlink():
                current = database.stat()
                if (current.st_dev, current.st_ino) == published_identity:
                    database.unlink()
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


@atomic
def record_provenance(connection, run_id, provenance):
    existing_timestamp = connection.execute("SELECT recorded_at FROM run_provenance WHERE run_id=?", (run_id,)).fetchone()
    if existing_timestamp and isinstance(provenance, dict) and "recorded_at" not in provenance:
        provenance = {**provenance, "recorded_at": existing_timestamp[0]}
    normalized = validate_provenance(provenance)
    run = connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if not run:
        raise AuditValidationError(f"unknown run: {run_id}")
    recorded_at = normalized.get("recorded_at") or utc_now()
    _timestamp(recorded_at, "provenance.recorded_at")
    normalized["recorded_at"] = recorded_at
    payload = canonical_json(normalized)
    prior = connection.execute(
        "SELECT invocation_kind,instruction_set_name,instruction_set_version,host_agent,host_version,provider,model,host_session_ref,capture_method,fingerprint_fidelity,resources_json,aggregate_sha256,recorded_at FROM run_provenance WHERE run_id=?",
        (run_id,),
    ).fetchone()
    values = (
        normalized["invocation_kind"], normalized["instruction_set_name"], normalized.get("instruction_set_version"),
        normalized.get("host_agent"), normalized.get("host_version"), normalized.get("provider"), normalized.get("model"),
        normalized.get("host_session_ref"), normalized["capture_method"], normalized["fingerprint_fidelity"],
        canonical_json(normalized["resources"]), normalized.get("aggregate_sha256"), recorded_at,
    )
    if prior:
        current = dict(zip(("invocation_kind","instruction_set_name","instruction_set_version","host_agent","host_version","provider","model","host_session_ref","capture_method","fingerprint_fidelity","resources_json","aggregate_sha256","recorded_at"), prior))
        if tuple(prior) != values:
            raise AuditConflict("run provenance reused with a different payload")
        return records(connection, "SELECT * FROM run_provenance WHERE run_id=?", (run_id,))[0]
    connection.execute(
        "INSERT INTO run_provenance(run_id,invocation_kind,instruction_set_name,instruction_set_version,host_agent,host_version,provider,model,host_session_ref,capture_method,fingerprint_fidelity,resources_json,aggregate_sha256,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, *values),
    )
    for resource in normalized["resources"]:
        connection.execute(
            "INSERT INTO provenance_resources(run_id,logical_name,sha256) VALUES (?,?,?)",
            (run_id, resource["name"], resource["sha256"]),
        )
    return records(connection, "SELECT * FROM run_provenance WHERE run_id=?", (run_id,))[0]


@atomic
def record_coverage(connection, coverage):
    existing_timestamp = None
    if isinstance(coverage, dict) and "coverage_id" in coverage and "observed_at" not in coverage:
        existing_timestamp = connection.execute("SELECT observed_at FROM coverage_observations WHERE coverage_id=?", (coverage["coverage_id"],)).fetchone()
    if existing_timestamp:
        coverage = {**coverage, "observed_at": existing_timestamp[0]}
    normalized = validate_coverage(coverage)
    run = connection.execute("SELECT capture_mode FROM runs WHERE run_id=?", (normalized["run_id"],)).fetchone()
    if not run:
        raise AuditValidationError(f"unknown run: {normalized['run_id']}")
    provenance = connection.execute(
        "SELECT capture_method FROM run_provenance WHERE run_id=?", (normalized["run_id"],)
    ).fetchone()
    # A host can supply coverage after an interactive invocation.  That record
    # is imported evidence, not a claim that the interactive skill changed its
    # own capture method.  Other mismatches remain invalid.
    if (provenance and provenance[0] != normalized["capture_method"]
            and not (provenance[0] == "instruction_driven" and normalized["capture_method"] == "imported")):
        raise AuditValidationError("coverage capture method conflicts with run provenance")
    if normalized["coverage"] == "not_requested" and run[0] != "metadata":
        raise AuditValidationError("not_requested coverage requires metadata capture mode")
    if normalized["coverage"] == "missing" and run[0] != "relevant":
        raise AuditValidationError("missing coverage requires relevant capture mode")
    fields = ("coverage_id","run_id","scope","coverage","content_state","exact_count","redacted_count","summarized_count","incomplete_count","observed_at","capture_method","reason")
    values = tuple(normalized.get(field) for field in fields)
    prior = connection.execute(
        "SELECT " + ",".join(fields) + " FROM coverage_observations WHERE coverage_id=?",
        (normalized["coverage_id"],),
    ).fetchone()
    if prior:
        if tuple(prior) != values:
            raise AuditConflict("coverage ID reused with a different payload")
        return records(connection, "SELECT * FROM coverage_observations WHERE coverage_id=?", (normalized["coverage_id"],))[0]
    _validate_coverage_evidence(connection, normalized)
    connection.execute(
        "INSERT INTO coverage_observations(" + ",".join(fields) + ") VALUES (" + ",".join("?" for _ in fields) + ")",
        values,
    )
    return records(connection, "SELECT * FROM coverage_observations WHERE coverage_id=?", (normalized["coverage_id"],))[0]


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
    if len(text) > MAX_RELEVANT_MESSAGE_CHARACTERS:
        raise AuditValidationError(
            f'message content exceeds {MAX_RELEVANT_MESSAGE_CHARACTERS} characters; '
            'submit a concise summary or explicitly incomplete/redacted evidence instead'
        )
    message_id = message_id or str(uuid.uuid4())
    v4 = "captured_message_content" in schema_tables(connection)
    prior = connection.execute('SELECT run_id,sequence,role,captured_at,text,capture_source,fidelity,redaction_note,content_sha256,content_byte_length FROM captured_messages WHERE message_id=?', (message_id,)).fetchone()
    timestamp = captured_at or (prior[3] if prior else utc_now())
    _timestamp(timestamp, 'captured_at')
    if sequence is None:
        sequence = prior[1] if prior else connection.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM captured_messages WHERE run_id=?', (run_id,)).fetchone()[0]
    if type(sequence) is not int or sequence < 1:
        raise AuditValidationError('message sequence must be a positive integer')
    raw = text.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    values = (run_id, sequence, role, timestamp, text, capture_source, fidelity, redaction_note)
    if prior:
        if v4:
            same_envelope = prior[:4] + prior[5:8] == values[:4] + values[5:8]
            if not same_envelope or prior[8:] != (digest, len(raw)):
                raise AuditConflict('message ID reused with a different payload')
            content = connection.execute("SELECT content,sha256,byte_length FROM captured_message_content WHERE message_id=?", (message_id,)).fetchone()
            if not content or content[1:] != (digest, len(raw)) or content[0] != raw:
                raise AuditConflict('message ID reused with different message content')
        elif prior[:8] != values:
            raise AuditConflict('message ID reused with a different payload')
        return message_id
    try:
        if v4:
            connection.execute('INSERT INTO captured_messages(message_id,run_id,sequence,role,captured_at,text,capture_source,fidelity,redaction_note,content_sha256,content_byte_length) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (message_id, run_id, sequence, role, timestamp, '', capture_source, fidelity, redaction_note, digest, len(raw)))
            connection.execute('INSERT INTO captured_message_content(message_id,content,sha256,byte_length) VALUES (?,?,?,?)', (message_id, raw, digest, len(raw)))
        else:
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


def _append_purge_coverage(connection, run_id, coverage_id, observed_at):
    provenance = connection.execute(
        "SELECT invocation_kind,capture_method FROM run_provenance WHERE run_id=?", (run_id,)
    ).fetchone()
    prior_observation = connection.execute(
        "SELECT scope,capture_method FROM coverage_observations WHERE run_id=? ORDER BY rowid DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    method = prior_observation[1] if prior_observation else (provenance[1] if provenance else "imported")
    scope = prior_observation[0] if prior_observation else ("api_runner_conversation" if provenance and provenance[0] == "api_runner" else "skill_conversation")
    rows = connection.execute(
        """SELECT m.fidelity,t.message_id,c.message_id
           FROM captured_messages m
           LEFT JOIN captured_message_content c ON c.message_id=m.message_id
           LEFT JOIN message_content_tombstones t ON t.message_id=m.message_id
           WHERE m.run_id=?""", (run_id,)
    ).fetchall()
    counts = {"exact_count": 0, "redacted_count": 0, "summarized_count": 0, "incomplete_count": 0}
    purged = 0
    available = 0
    for fidelity, tombstone, content in rows:
        counts[fidelity + "_count"] += 1
        purged += bool(tombstone)
        available += bool(content)
    state = "purged" if rows and purged == len(rows) else "partially_purged"
    payload = {
        "coverage_id": coverage_id, "run_id": run_id, "scope": scope,
        "coverage": "partial", "content_state": state,
        **counts, "observed_at": observed_at, "capture_method": method,
        "reason": "message content purged",
    }
    prior = connection.execute("SELECT * FROM coverage_observations WHERE coverage_id=?", (coverage_id,)).fetchone()
    if prior is None:
        record_coverage(connection, payload)


@atomic
def purge_message(connection, message_id, reason, confirmation):
    _text(message_id, "message_id")
    _text(reason, "reason")
    if confirmation != message_id:
        raise AuditValidationError("purge confirmation must exactly match message ID")
    row = connection.execute(
        "SELECT m.run_id,m.content_sha256,m.content_byte_length,c.message_id,t.reason FROM captured_messages m LEFT JOIN captured_message_content c ON c.message_id=m.message_id LEFT JOIN message_content_tombstones t ON t.message_id=m.message_id WHERE m.message_id=?",
        (message_id,),
    ).fetchone()
    if not row:
        raise AuditValidationError("unknown message ID")
    run_id, digest, byte_length, content_id, prior_reason = row
    if prior_reason is not None:
        if prior_reason != reason:
            raise AuditConflict("message was already purged with a different reason")
        return records(connection, "SELECT * FROM message_content_tombstones WHERE message_id=?", (message_id,))[0]
    if content_id is None:
        raise AuditValidationError("message content is already unavailable")
    run = connection.execute("SELECT workspace_id,operation FROM runs WHERE run_id=?", (run_id,)).fetchone()
    timestamp = utc_now()
    event_id = f"message_content_purged:{message_id}"
    append_event(connection, {
        "schema": "tabilet.audit.event/v1", "event_id": event_id, "run_id": run_id,
        "workspace_id": run[0], "operation": run[1], "event_type": "message_content_purged",
        "recorded_at": timestamp, "occurred_at": timestamp,
        "subject": {}, "details": {"schema": "tabilet.audit.details/v1", "reason": reason,
                                     "message_id": message_id, "sha256": digest, "byte_length": byte_length},
    })
    connection.execute(
        "INSERT INTO message_content_tombstones(message_id,purged_at,reason,event_id) VALUES (?,?,?,?)",
        (message_id, timestamp, reason, event_id),
    )
    connection.execute("PRAGMA secure_delete=ON")
    connection.execute("DELETE FROM captured_message_content WHERE message_id=?", (message_id,))
    _append_purge_coverage(connection, run_id, f"purge:{message_id}:coverage", timestamp)
    return records(connection, "SELECT * FROM message_content_tombstones WHERE message_id=?", (message_id,))[0]


def cleanup_purged_content(connection):
    """Report physical cleanup separately from an already committed purge."""
    if connection.in_transaction:
        raise AuditValidationError("physical cleanup requires a committed purge")
    result = {}
    for name, statement in (("compaction", "VACUUM"), ("wal_checkpoint", "PRAGMA wal_checkpoint(TRUNCATE)")):
        try:
            row = connection.execute(statement).fetchone()
            if name == "wal_checkpoint" and row and row[0]:
                result[name] = {"ok": False, "error": "checkpoint busy", "result": list(row)}
            else:
                result[name] = {"ok": True, **({"result": list(row)} if row else {})}
        except sqlite3.DatabaseError as exc:
            result[name] = {"ok": False, "error": str(exc)}
    return result


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
               since=None, until=None, instruction_set=None, instruction_set_version=None,
               host=None, model=None, capture_method=None, coverage=None, purged=None,
               limit=1000, offset=0):
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
    if any(value is not None for value in (instruction_set, instruction_set_version, host, model, capture_method)):
        if 'run_provenance' not in schema_tables(connection):
            return []
        provenance_filters = []
        for column, value in (("instruction_set_name", instruction_set), ("instruction_set_version", instruction_set_version),
                              ("host_agent", host), ("model", model), ("capture_method", capture_method)):
            if value is not None:
                provenance_filters.append(f"p.{column}=?")
                values.append(value)
        clauses.append("EXISTS (SELECT 1 FROM run_provenance p WHERE p.run_id=r.run_id AND " + " AND ".join(provenance_filters) + ")")
    if coverage is not None:
        if 'coverage_observations' not in schema_tables(connection):
            return []
        clauses.append("EXISTS (SELECT 1 FROM coverage_observations c WHERE c.run_id=r.run_id AND c.coverage=? AND NOT EXISTS (SELECT 1 FROM coverage_observations c2 WHERE c2.run_id=c.run_id AND c2.rowid>c.rowid))")
        values.append(coverage)
    if purged is not None:
        if 'message_content_tombstones' not in schema_tables(connection):
            return []
        clauses.append(("EXISTS" if purged else "NOT EXISTS") + " (SELECT 1 FROM message_content_tombstones t JOIN captured_messages m USING(message_id) WHERE m.run_id=r.run_id)")
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    rows = records(connection, 'SELECT r.* FROM runs r'+where+f' ORDER BY {time_key("r.started_at")},run_id LIMIT ? OFFSET ?', (*values,limit,offset))
    if 'run_provenance' in schema_tables(connection):
        for row in rows:
            provenance = records(connection, 'SELECT * FROM run_provenance WHERE run_id=?', (row['run_id'],))
            if provenance:
                provenance[0]['resources'] = records(connection, 'SELECT logical_name AS name,sha256 FROM provenance_resources WHERE run_id=? ORDER BY logical_name', (row['run_id'],))
            row['provenance'] = provenance[0] if provenance else None
            row['coverage'] = records(connection, 'SELECT * FROM coverage_observations WHERE run_id=? ORDER BY rowid', (row['run_id'],))
    return rows


def query_events(connection, run_id=None, *, workspace_id=None, operation=None, milestone_id=None,
                 task=None, since=None, until=None, instruction_set=None,
                 instruction_set_version=None, host=None, model=None, capture_method=None,
                 coverage=None, purged=None, limit=10000, offset=0):
    pagination(limit, offset)
    clauses, values = [], []
    for name,value in [('e.run_id',run_id),('r.workspace_id',workspace_id),('e.operation',operation),('e.milestone_id',milestone_id),('e.task_label',task)]:
        if value is not None:
            clauses.append(f'{name}=?'); values.append(value)
    for value,comparison in [(since,'>='),(until,'<=')]:
        if value is not None:
            clauses.append(f'{time_key("e.recorded_at")}{comparison}?'); values.append(time_bound(value))
    if any(value is not None for value in (instruction_set, instruction_set_version, host, model, capture_method, coverage, purged)):
        tables = schema_tables(connection)
        if ('run_provenance' not in tables and any(value is not None for value in
                (instruction_set, instruction_set_version, host, model, capture_method))
                or 'coverage_observations' not in tables and coverage is not None
                or 'message_content_tombstones' not in tables and purged is not None):
            return []
        provenance_filters = []
        for column, value in (("instruction_set_name", instruction_set), ("instruction_set_version", instruction_set_version),
                              ("host_agent", host), ("model", model), ("capture_method", capture_method)):
            if value is not None:
                provenance_filters.append(f"p.{column}=?")
                values.append(value)
        if provenance_filters:
            clauses.append("EXISTS (SELECT 1 FROM run_provenance p WHERE p.run_id=r.run_id AND " + " AND ".join(provenance_filters) + ")")
        if coverage is not None:
            clauses.append("EXISTS (SELECT 1 FROM coverage_observations c WHERE c.run_id=r.run_id AND c.coverage=? AND NOT EXISTS (SELECT 1 FROM coverage_observations c2 WHERE c2.run_id=c.run_id AND c2.rowid>c.rowid))")
            values.append(coverage)
        if purged is not None:
            clauses.append(("EXISTS" if purged else "NOT EXISTS") + " (SELECT 1 FROM message_content_tombstones t JOIN captured_messages m USING(message_id) WHERE m.run_id=r.run_id)")
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


def query_messages(connection, run_id, *, include_content=False, limit=None, offset=0, roles=(), descending=False):
    where = ' WHERE m.run_id=?'
    values = [run_id]
    if roles:
        where += ' AND m.role IN (' + ','.join('?' for _ in roles) + ')'
        values.extend(roles)
    tail = ' ORDER BY m.sequence ' + ('DESC' if descending else 'ASC')
    if limit is not None:
        pagination(limit, offset)
        tail += ' LIMIT ? OFFSET ?'
        values.extend((limit, offset))
    if "captured_message_content" not in schema_tables(connection):
        return records(connection, "SELECT m.*, NULL AS content_state FROM captured_messages m" + where + tail, values)
    content = ", c.content AS content_blob" if include_content else ""
    rows = records(connection, """
        SELECT m.message_id,m.run_id,m.sequence,m.role,m.captured_at,m.capture_source,m.fidelity,
               m.redaction_note,m.content_sha256,m.content_byte_length,
               CASE WHEN t.message_id IS NOT NULL THEN 'purged'
                    WHEN c.message_id IS NULL THEN 'not captured' ELSE 'available' END AS content_state,
               t.purged_at,t.reason AS purge_reason
               """ + content + """
        FROM captured_messages m
        LEFT JOIN captured_message_content c ON c.message_id=m.message_id
        LEFT JOIN message_content_tombstones t ON t.message_id=m.message_id
    """ + where + tail, values)
    for row in rows:
        blob = row.pop("content_blob", None)
        if include_content and blob is not None and row["content_state"] != "purged":
            row["text"] = bytes(blob).decode("utf-8")
        else:
            row["text"] = None
    return rows


def export_json(connection, *, workspace_id=None, include_content=False):
    """Complete durable export; private messages/bytes require explicit inclusion."""
    owner = not connection.in_transaction
    if owner:
        connection.execute('BEGIN')
    try:
        where, values = (' WHERE workspace_id=?',(workspace_id,)) if workspace_id else ('',())
        runs = records(connection, 'SELECT * FROM runs'+where+' ORDER BY started_at,run_id',values)
        has_explorer = 'event_explorer' in schema_tables(connection)
        has_v4 = 'run_provenance' in schema_tables(connection)
        for run in runs:
            if has_v4:
                provenance = records(connection, 'SELECT * FROM run_provenance WHERE run_id=?', (run['run_id'],))
                for item in provenance:
                    item['resources'] = records(connection, 'SELECT logical_name AS name,sha256 FROM provenance_resources WHERE run_id=? ORDER BY logical_name', (run['run_id'],))
                run['provenance'] = provenance[0] if provenance else None
                run['coverage'] = records(connection, 'SELECT * FROM coverage_observations WHERE run_id=? ORDER BY rowid', (run['run_id'],))
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
                run['messages'] = query_messages(connection, run['run_id'], include_content=True)
            elif has_v4:
                run['messages'] = query_messages(connection, run['run_id'])
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
    staging = safe_path(f'{path}.backup-{uuid.uuid4().hex}')
    os.close(private_create(staging))
    target = None
    try:
        target = sqlite3.connect(str(staging))
        connection.backup(target)
        validate_database(target)
        target.close()
        target = None
        with staging.open('rb') as stored:
            os.fsync(stored.fileno())
        try:
            os.link(staging, path)
        except FileExistsError:
            raise FileExistsError(str(path))
    except BaseException:
        if target is not None:
            target.close()
        raise
    finally:
        if target is not None:
            target.close()
        if staging.exists() and not staging.is_symlink():
            staging.unlink()
        for suffix in ('-wal', '-shm', '-journal'):
            sidecar = safe_path(str(staging) + suffix)
            if sidecar.exists() and not sidecar.is_symlink():
                sidecar.unlink()


def restore_database(source, destination):
    with contextlib.closing(open_readonly_database(source)) as connection:
        backup_database(connection, destination)

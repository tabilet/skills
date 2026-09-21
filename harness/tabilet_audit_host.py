#!/usr/bin/env python3
"""Submit one structured host event to the opt-in Tabilet audit database.

This is an adapter boundary, not an execution harness. It accepts a JSON event
from an interactive host and records only the already-observed summary.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tabilet_audit import append_event, open_database, validate_event, AuditError, CAPTURE_SOURCES, FIDELITIES  # noqa: E402


HOST_OPERATIONS = {"init", "archive", "propose", "reconcile", "goal"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Record one structured Tabilet host audit event.")
    parser.add_argument("--audit-db", required=True, help="External SQLite audit database path.")
    parser.add_argument("--event", help="JSON event; if omitted, read one object from stdin.")
    args = parser.parse_args()
    try:
        raw = args.event if args.event is not None else sys.stdin.read()
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise AuditError("event must be a JSON object")
        if event.get("operation") not in HOST_OPERATIONS:
            raise AuditError("host adapter accepts init, archive, propose, reconcile, or goal")
        details = event.get("details")
        if not isinstance(details, dict) or details.get("capture_source") not in CAPTURE_SOURCES:
            raise AuditError("host events require details.capture_source provenance")
        if details.get("fidelity") not in FIDELITIES:
            raise AuditError("host events require details.fidelity provenance")
        event.setdefault("event_id", str(uuid.uuid4()))
        event.setdefault("recorded_at", __import__("tabilet_audit").utc_now())
        event.setdefault("occurred_at", event["recorded_at"])
        event = validate_event(event)
        connection = open_database(args.audit_db)
        try:
            sequence = append_event(connection, event)
        finally:
            connection.close()
        print(json.dumps({"event_id": event["event_id"], "sequence": sequence}, sort_keys=True))
        return 0
    except (AuditError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"audit event rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline contrastive milestone reflection for Tabilet Memory Bank: propose, probe, then compose a proposal."""
from __future__ import annotations

import argparse
import contextlib
import errno
import http.client
import json
import os
import pathlib
import re
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any

import tabilet_audit as audit

TOOLKIT_INTERFACE = 5
DEFAULT_PROPOSAL_PATH = "tabilet/memory-bank/suggested-harness-update.md"
MAX_DOWNSTREAM = 3
SLOW_RUN_SEC = 120
# Reflection may spend at most this share of the milestone's recorded wall time; below the
# minimum the model is skipped rather than started and abandoned.
DEFAULT_BUDGET_PERCENT = 10.0
MODEL_TIMEOUT_CAP_SEC = 120
MIN_MODEL_BUDGET_SEC = 15
# A milestone shorter than this gets no model call at the default budget share.
MIN_MODEL_MILESTONE_SEC = round(MIN_MODEL_BUDGET_SEC * 100 / DEFAULT_BUDGET_PERCENT)
CLI_BACKENDS = ("claude", "gemini", "codex")
REST_KEYS = {"claude": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}


class BudgetExceeded(audit.AuditError):
    """The model call could not finish inside the reflection time budget."""


class BackendUnreachable(BudgetExceeded):
    """Every installed backend needs a network the host does not provide (typically a sandbox)."""


CLI_HOSTS = {"claude": "api.anthropic.com", "gemini": "generativelanguage.googleapis.com", "codex": "chatgpt.com"}


def _host_resolves(host: str, wait_sec: float = 3.0) -> bool:
    """True when DNS answers within `wait_sec`. A sandbox without network fails at once; a CLI would hang."""
    import socket
    import threading
    result: list[bool] = []

    def lookup() -> None:
        try:
            socket.getaddrinfo(host, 443)
            result.append(True)
        except OSError:
            result.append(False)

    worker = threading.Thread(target=lookup, daemon=True)
    worker.start()
    worker.join(wait_sec)
    return bool(result and result[0])

PROMPT_TEMPLATE = """You are the Tabilet Milestone Reflector for Tabilet Memory Bank.
Analyze the following execution telemetry from Milestone {milestone_id} in {project_root}.

--- 1. CONTRASTIVE TELEMETRY ---
A. Fast 1st-Attempt Baseline Runs (What worked cleanly):
{contrastive_fast_runs}

B. Friction, Blocked, or Long Runs (What stalled or failed):
{friction_runs}

C. Multi-Attempt Verification Hotspots (Tasks requiring retries):
{multi_attempt_tasks}

D. Turn-Level Efficiency & Truncated Error Traces (Capture mode: {capture_status}):
{turn_efficiency_and_traces}

E. Downstream Milestones (Gate: {downstream_gate}):
{downstream_milestones}

F. Recorded SHA Evidence and Review Checkpoints (attribution remains observation-based; missing evidence is unknown):
{independent_evidence}

--- 2. CURRENT HARNESS STATE ---
Current `tech-stack.md`:
{current_tech_stack_md}

Current `lessons.md`:
{current_lessons_md}
--------------------------------

YOUR TASK:
1. CONTRAST: Compare the verification commands and turn patterns of the Fast Baseline Runs (1A) against the Friction/Multi-Attempt Runs (1B/1C). Identify why slow/failed tasks diverged.
2. PROPOSE: Formulate concise, additive updates to `tabilet/memory-bank/tech-stack.md` and `tabilet/memory-bank/lessons.md`.
3. PROBE COMMAND EXTRACTION: List at most 3 optional test commands in a fenced ```probe-commands``` block. These are short smoke checks only. Counts and timings cannot prove equivalent coverage, subset relationships, or a replacement test profile. Keep required verification unchanged.
4. DOWNSTREAM: Only when the gate in 1E is open, and only for a milestone listed there, propose a
   concrete amendment (a narrower verification command, a split row, a missing prerequisite, a
   redundant step). Skip any finding already covered by the milestone's own text or by `lessons.md`.
   Name the milestone, cite the run or task evidence from section 1, and state the exact change.
   If the gate is closed or nothing is both new and evidenced, write exactly `No downstream changes.`
5. RECORDING GAPS: Task and verification observations can be incomplete. Unclosed runs have unknown outcomes. Missing events never prove missing work; run elapsed time never proves active task time. Section 1F verifies recorded commit SHAs in Git but does not independently prove their task attribution. Report gaps and conflicting review checkpoints explicitly.
6. STRICT SAFETY CONSTRAINT: You must NOT modify, weaken, or remove any authorization blocks, security gates, review iteration limits, or verification attempt limits.

OUTPUT FORMAT:
Return ONLY a Markdown document containing:
- ## Contrastive Diagnosis (3-4 bullet points comparing fast baselines vs. friction runs)
- ## Probe Commands (fenced `probe-commands` block with the baseline test command first and up to 2 alternatives, or empty if none)
- ## Proposed Edits to tech-stack.md (Unified Diff)
- ## Proposed Entry for lessons.md (Standard Tabilet Lesson Schema)
- ## Proposed Downstream Amendments (per-milestone items with evidence, or `No downstream changes.`)
"""


def resolve_project_db(project_path: str | pathlib.Path = ".") -> tuple[pathlib.Path, pathlib.Path]:
    """Return the checkout whose memory bank is read and the shared audit.sqlite3 path.

    Linked worktrees share the owner's database, but their own Markdown stays authoritative,
    so the returned root is the directory named, never the owner's checkout.
    """
    root = pathlib.Path(project_path or ".").expanduser().resolve()
    if not root.is_dir():
        raise audit.AuditError("project must be an existing directory")
    return root, audit.default_database_path(project_root=root)


def get_readonly_connection(db_path: pathlib.Path) -> sqlite3.Connection:
    """Open audit.sqlite3 strictly read-only with WAL busy_timeout protection."""
    if not db_path.is_file():
        raise audit.AuditError(f"audit database not found at {db_path}; enable auditing first via 'tabilet-audit audit enable .'")
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def truncate_middle(text: str | None, head: int = 400, tail: int = 800) -> str:
    """Bound token usage on large tool outputs by keeping head and tail."""
    if not text:
        return ""
    if len(text) <= head + tail:
        return text
    omitted = len(text) - (head + tail)
    return f"{text[:head]}\n... [truncated {omitted} chars] ...\n{text[-tail:]}"


def significance_reasons(friction_runs, multi_attempts):
    reasons = [f"task {t.get('task_label')!r} needed {t.get('attempt_count')} recorded attempts" for t in multi_attempts]
    for run in friction_runs:
        if run.get("result") in ("failed", "blocked", "interrupted"):
            reasons.append(f"run {run.get('run_id')} ended {run.get('result')}")
        elif run.get("duration_sec") is not None and run["duration_sec"] > SLOW_RUN_SEC:
            reasons.append(f"task in run {run.get('run_id')} took {run['duration_sec']}s (over {SLOW_RUN_SEC}s)")
    return reasons[:8]


def suggested_downstream(project_root: pathlib.Path, finished: str | None) -> list[str]:
    """Downstream milestone IDs for the finished one, as listed in suggested.txt (a hint, not truth)."""
    path = project_root / "tabilet" / "memory-bank" / "suggested.txt"
    if not finished or not path.is_file():
        return []
    from tabilet_index import parser
    status_id_re = re.compile(r"\b" + parser().MILESTONE_ID + r"\b")
    text = path.read_text(encoding="utf-8", errors="replace")
    found: list[str] = []
    block = re.search(r"^DOWNSTREAM_IMPACTS:[ \t]*(.*)\n?((?:[ \t]*\S.*\n?)*)", text, re.M)
    if block and block.group(1).strip().lower() == "none":
        return []  # an explicit declaration of no impacts; STATUS_ORDER is not a substitute
    for line in ([block.group(1), *block.group(2).splitlines()] if block else []):
        source, arrow, targets = line.partition("->")
        if arrow and source.strip() == finished:
            found += status_id_re.findall(targets)
    if not found:
        order = re.search(r"^STATUS_ORDER:[ \t]*(\S.*|\n[ \t]*\S.*)$", text, re.M)
        ids = status_id_re.findall(order.group(1)) if order else []
        if finished in ids:
            found = ids[ids.index(finished) + 1:]
    return list(dict.fromkeys(found))[:MAX_DOWNSTREAM]


def milestone_spec(project_root: pathlib.Path, ident: str) -> str:
    path = project_root / "tabilet" / "memory-bank" / "milestone.md"
    if '-' in ident:
        path = path.parent / f'amend-{ident}.md'
    if not path.is_file():
        return ""
    match = re.search(rf"^##[ \t]+{re.escape(ident)}\b.*?(?=^##[ \t]|\Z)", path.read_text(encoding="utf-8", errors="replace"), re.M | re.S)
    return match.group(0).strip() if match else ""


def downstream_context(project_root: pathlib.Path, finished: str | None) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Check each suggested downstream milestone against the live files; keep only open ones."""
    included: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    runner = None
    for ident in suggested_downstream(project_root, finished):
        # Options remain outside routine reflection; parent-close selection is
        # the interactive owner's separate decision.
        filename = f'amend-{ident}.md' if '-' in ident else f'status-{ident}.md'
        status_file = project_root / "tabilet" / "memory-bank" / filename
        if not status_file.is_file():
            skipped.append({"id": ident, "reason": "no active status file (missing or retired)"})
            continue
        try:
            if runner is None:
                import tabilet_index
                runner = tabilet_index.parser()
            rows = runner.status_rows(status_file.read_text(encoding="utf-8", errors="replace"))
            open_rows = [r for r in rows if r["state"] in runner.ACTIONABLE_STATES]
        except Exception as exc:
            skipped.append({"id": ident, "reason": f"status file could not be read ({type(exc).__name__})"})
            continue
        if not open_rows:
            skipped.append({"id": ident, "reason": "no pending or in-progress rows"})
            continue
        included.append({
            "id": ident,
            "spec": truncate_middle(milestone_spec(project_root, ident) or "(no specification found in milestone.md)", 1200, 1200),
            "open_rows": [{"item": r["item"], "state": r["state"]} for r in open_rows[:12]],
        })
    return included, skipped


MAX_EVIDENCE_COMMITS = 25


def _active_counts(text: str) -> list[int]:
    """Read standalone checkpoint fields, excluding fenced examples and prose mentions."""
    counts, fenced = [], False
    for line in text.splitlines():
        if re.match(r"^\s*(\x60{3,}|~{3,})", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        plain = line.strip().replace("**", "").replace("\x60", "")
        match = re.fullmatch(r"(?:Persisted (?:iteration|review) count[:.]?|Review (?:gate )?iterations[:.]?)\s*(\d+)(?:\s*/\s*\d+)?[.]?", plain, re.I)
        if match:
            counts.append(int(match.group(1)))
    return counts


def review_rounds(project_root: pathlib.Path, milestone_id: str | None) -> dict[str, Any]:
    if not milestone_id or not re.fullmatch(r"[A-Z][0-9]{2,}(?:-[0-9]{2})?", milestone_id):
        return {"iterations": None, "source": None}
    names = (f"amend-{milestone_id}.md", f"option-{milestone_id}.md") if "-" in milestone_id else (f"status-{milestone_id}.md",)
    for directory in ("tabilet/docs/history", "tabilet/memory-bank"):
        for name in names:
            path = project_root / directory / name
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            try:
                if directory.endswith("history"):
                    import tabilet_index
                    record = tabilet_index.parser().historical_record(text, name)
                    raw = record["metadata"].get("Review iterations", "")
                    counts = [int(raw)] if raw.isdigit() and not record["blockers"] else []
                else:
                    counts = _active_counts(text)
                if counts:
                    return {"iterations": counts[0] if len(set(counts)) == 1 else None,
                            "source": f"{directory}/{name}", "conflict": len(set(counts)) != 1}
            except (ValueError, KeyError):
                return {"iterations": None, "source": f"{directory}/{name}", "conflict": True}
    return {"iterations": None, "source": None}


def observed_commits(project_root: pathlib.Path, shas: list[str]) -> dict[str, Any]:
    """Verify explicitly attributed full SHAs; dates never supply attribution."""
    found, missing = [], []
    for sha in sorted(set(shas)):
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
            missing.append(sha)
            continue
        try:
            proc = subprocess.run(["git", "show", "-s", "--format=%H%x1f%cI%x1f%s", sha + "^{commit}"],
                                  cwd=project_root, capture_output=True, text=True, timeout=5)
            fields = proc.stdout.strip().split("\x1f", 2)
            if proc.returncode or len(fields) != 3 or fields[0] != sha:
                missing.append(sha)
            else:
                found.append({"sha": sha, "at": fields[1], "subject": truncate_middle(fields[2], 90, 40)})
        except (OSError, subprocess.SubprocessError):
            missing.append(sha)
    return {"available": not missing, "count": len(found), "commits": found[:MAX_EVIDENCE_COMMITS],
            "unverified": missing, "attribution": "recorded milestone-scoped SHAs only"}


def _interval_seconds(intervals):
    total, end = 0.0, None
    for start, stop in sorted(intervals):
        if end is None or start > end:
            total += stop - start
        elif stop > end:
            total += stop - end
        end = max(end or stop, stop)
    return total


def model_budget_sec(wall_sec: float, percent: float) -> float:
    """Time the model call may take: a share of the milestone's recorded wall time, capped."""
    return min(float(MODEL_TIMEOUT_CAP_SEC), max(0.0, wall_sec) * percent / 100.0)


def extract_telemetry(project_path: str | pathlib.Path = ".", milestone_id: str | None = None) -> dict[str, Any]:
    """Read scoped observations; absent boundaries never become elapsed work."""
    project_root, db_path = resolve_project_db(project_path)
    with contextlib.closing(get_readonly_connection(db_path)) as conn:
        events = [dict(row) for row in conn.execute("""
            SELECT * FROM events WHERE :m IS NULL OR run_id IN
            (SELECT run_id FROM events WHERE milestone_id=:m) ORDER BY run_id,sequence
        """, {"m": milestone_id})]
        ids = {e["run_id"] for e in events}
        runs = [dict(row) for row in conn.execute("SELECT * FROM runs") if row["run_id"] in ids]
        scoped = [e for e in events if milestone_id is None or e["milestone_id"] == milestone_id]
        attempts, verification, reviews, intervals, gaps = {}, [], [], [], []
        for e in scoped:
            details = json.loads(e["details_json"])
            item = details.get("observation") or {}
            if not isinstance(item, dict) or item.get("schema") != audit.OBSERVATION_SCHEMA:
                continue
            kind = item.get("kind")
            if kind in ("task-start", "task-finish"):
                ident = item.get("attempt_id")
                if not isinstance(ident, str):
                    gaps.append("observation missing attempt identity")
                    continue
                attempt = attempts.setdefault((e["run_id"], ident), {
                    "run_id": e["run_id"], "attempt_id": ident, "task_label": e["task_label"],
                    "milestone_id": e["milestone_id"], "status_path": e["status_path"],
                    "duration_sec": None, "result": None, "failure_reason": None})
                attempt["start" if kind == "task-start" else "finish"] = e["occurred_at"]
                if kind == "task-finish":
                    attempt.update(result=item.get("result"), failure_reason=item.get("reason"))
            elif kind in ("verification", "review"):
                observed = {**item, "run_id": e["run_id"]}
                (verification if kind == "verification" else reviews).append(observed)
                if item.get("started_at") and item.get("finished_at"):
                    try:
                        a, b = audit._instant(item["started_at"]), audit._instant(item["finished_at"])
                        if b >= a:
                            intervals.append((a, b))
                            if observed.get("duration_sec") is None:
                                observed.update(duration_sec=b - a, timing_basis="recorded_boundary")
                    except (ValueError, TypeError):
                        gaps.append("invalid recorded interval")
        for attempt in attempts.values():
            if attempt.get("start") and attempt.get("finish"):
                try:
                    a, b = audit._instant(attempt["start"]), audit._instant(attempt["finish"])
                except (ValueError, TypeError, AttributeError):
                    gaps.append("invalid task interval")
                    continue
                if b >= a:
                    attempt["duration_sec"] = b - a
                    intervals.append((a, b))
            if attempt["duration_sec"] is None:
                gaps.append("task attempt timing unavailable")
        grouped = {}
        for attempt in attempts.values():
            grouped.setdefault((attempt["milestone_id"], attempt["status_path"], attempt["task_label"]), []).append(attempt)
        multi = [{"milestone_id": k[0], "task_label": k[2], "attempt_count": len(v),
                  "observed_outcomes": [a["result"] for a in v],
                  "max_attempt_duration_sec": max((a["duration_sec"] for a in v if a["duration_sec"] is not None), default=None)}
                 for k, v in grouped.items() if len(v) > 1]
        friction = [a for a in attempts.values() if a["result"] in ("failed", "blocked", "interrupted")
                    or (a["duration_sec"] is not None and a["duration_sec"] > SLOW_RUN_SEC)]
        for item in verification + reviews:
            duration = item.get("duration_sec")
            if item.get("result") in ("failed", "blocked") or (isinstance(duration, (int, float)) and duration > SLOW_RUN_SEC):
                friction.append({"run_id": item["run_id"], "task_label": item.get("task_label"),
                                 "command": item.get("command"), "result": item["result"],
                                 "duration_sec": duration, "failure_reason": None,
                                 "scope": item["kind"]})
        fast = [a for k, v in grouped.items() for a in v if len(v) == 1 and a["result"] == "completed"
                and a["duration_sec"] is not None and a["duration_sec"] <= SLOW_RUN_SEC]
        # Legacy terminal evidence remains useful only when its milestone attribution is unique.
        for run in runs:
            subjects = {e["milestone_id"] for e in events if e["run_id"] == run["run_id"] and e["milestone_id"]}
            if len(subjects) == 1 and run["result"] in ("failed", "blocked", "interrupted"):
                terminal = [e for e in events if e["run_id"] == run["run_id"] and e["event_type"] in
                            ("run_finished", "run_failed", "run_blocked", "run_interrupted")]
                reason = next((json.loads(e["details_json"]).get("reason") for e in reversed(terminal)
                               if json.loads(e["details_json"]).get("reason")), None)
                if not any(a["run_id"] == run["run_id"] for a in friction):
                    friction.append({"run_id": run["run_id"], "result": run["result"],
                                     "duration_sec": None, "failure_reason": reason, "scope": "single-milestone run",
                                     "task_label": next((e["task_label"] for e in reversed(scoped) if e["run_id"] == run["run_id"] and e["task_label"]), None)})
        open_runs = [{"run_id": r["run_id"], "outcome": "unknown",
                      "last_observed_at": max((e["recorded_at"] for e in events if e["run_id"] == r["run_id"]), default=None)}
                     for r in runs if r["completed_at"] is None]
        if any(not json.loads(e["details_json"]).get("observation") for e in scoped
               if e["event_type"] in ("task_transition", "verification_observed")):
            gaps.append("legacy observations have incomplete task timing")
        if runs and not attempts:
            gaps.append("no typed task boundaries recorded")
        shas = [e["commit_sha"] for e in scoped if e["event_type"] == "commit_observed" and e["commit_sha"]]
        turns, traces = [], {}
        for run in runs:
            messages = audit.query_messages(conn, run["run_id"], include_content=True, limit=3, descending=True)
            if messages:
                # Context is run-scoped; it is not task-efficiency evidence.
                turns.append({"run_id": run["run_id"], "scope": "run context", "sampled_turns": len(messages),
                              "total_turns": conn.execute("SELECT count(*) FROM captured_messages WHERE run_id=?", (run["run_id"],)).fetchone()[0],
                              "first_edit_turn": min((m["sequence"] for m in messages if any(word in (m.get("text") or "") for word in ("edit_file", "write_file", "apply_patch"))), default=None)})
                if any(a["run_id"] == run["run_id"] for a in friction):
                    traces[run["run_id"]] = [{"turn": m["sequence"], "role": m["role"],
                                              "snippet": truncate_middle(m.get("text") or "", 300, 600)}
                                             for m in reversed(messages)]
    review = review_rounds(project_root, milestone_id)
    rounds = [r["round"] for r in reviews if type(r.get("round")) is int and r["round"] > 0]
    if rounds:
        observed = max(rounds)
        conflict = bool(review.get("conflict")) or review["iterations"] not in (None, observed)
        review = {"iterations": None if conflict else observed, "source": "typed observations",
                  "observed_rounds": sorted(set(rounds)), "conflict": conflict}
    reasons = significance_reasons(friction, multi)
    downstream, skipped = downstream_context(project_root, milestone_id) if reasons and milestone_id else ([], [])
    extra = {"git_commits": observed_commits(project_root, shas), "review_rounds": review,
             "recording_gap": "; ".join(sorted(set(gaps))) or None,
             "open_runs": (f"{len(open_runs)} unclosed run(s); outcome unknown. No terminal outcome or duration is inferred."
                           if open_runs else None)}
    return {"project_root": str(project_root), "milestone": milestone_id or "ALL",
            "capture_mode": "relevant" if turns else "metadata-only", "total_runs_analyzed": len(runs),
            "milestone_wall_sec": _interval_seconds(intervals), "timing_coverage": "observed scoped intervals only",
            "downstream": {"gate": "open" if reasons and milestone_id else "closed", "reasons": reasons,
                           "milestone_given": bool(milestone_id), "milestones": downstream, "skipped": skipped},
            "contrastive_fast_baselines": fast[:5], "friction_runs": friction[:10], "multi_attempts": multi[:10],
            "task_attempts": list(attempts.values()), "verification_observations": verification,
            "review_observations": reviews, "unclosed_runs": open_runs,
            "turn_efficiency": turns, "bounded_error_traces": traces, "independent_evidence": extra,
            "tech_stack_present": (project_root / "tabilet/memory-bank/tech-stack.md").is_file(),
            "lessons_present": (project_root / "tabilet/memory-bank/lessons.md").is_file()}


def export_trajectories(project_path=".", milestone_id=None):
    """Export scoped records with explicit gaps; captured messages remain run context."""
    telemetry = extract_telemetry(project_path, milestone_id)
    _, database = resolve_project_db(project_path)
    tasks = [{**attempt, "task_id": attempt["task_label"], "status": attempt["result"]}
             for attempt in telemetry["task_attempts"]]
    with contextlib.closing(get_readonly_connection(database)) as conn:
        represented = {(t["run_id"], t["milestone_id"], t["task_id"]) for t in tasks}
        for row in conn.execute("SELECT * FROM events WHERE event_type='task_transition' AND (:m IS NULL OR milestone_id=:m) ORDER BY run_id,sequence DESC",
                                {"m": milestone_id}):
            key = (row["run_id"], row["milestone_id"], row["task_label"])
            if key not in represented:
                represented.add(key)
                tasks.append({"run_id": key[0], "milestone_id": key[1], "task_id": key[2],
                              "status": row["new_state"], "duration_sec": None, "timing_coverage": "unavailable"})
        for task in tasks:
            messages = audit.query_messages(conn, task["run_id"], include_content=True)
            task["turns"] = [{"turn": m["sequence"], "role": m["role"], "text": m.get("text") or "",
                              "scope": "run context"} for m in messages]
    return {"schema": "tabilet.trajectories/v1", "project_root": telemetry["project_root"],
            "milestone": telemetry["milestone"], "tasks": tasks,
            "verification": telemetry["verification_observations"],
            "reviews": telemetry["review_observations"],
            "unclosed_runs": telemetry["unclosed_runs"],
            "recording_gap": telemetry["independent_evidence"]["recording_gap"]}


def read_memory_file(project_root: pathlib.Path, rel_path: str, max_chars: int = 8000) -> str:
    """Safely read a Tabilet memory-bank file with character bounding."""
    target = project_root / rel_path
    if not target.is_file():
        return f"*(File `{rel_path}` not found)*"
    return truncate_middle(target.read_text(encoding="utf-8"), head=max_chars // 2, tail=max_chars // 2)


def build_reflection_prompt(telemetry: dict[str, Any], project_root: pathlib.Path) -> str:
    """Assemble the complete contrastive prompt from SQLite telemetry and Markdown files."""
    tech_stack_md = read_memory_file(project_root, "tabilet/memory-bank/tech-stack.md")
    lessons_md = read_memory_file(project_root, "tabilet/memory-bank/lessons.md")

    turn_and_traces = {
        "turn_efficiency": telemetry["turn_efficiency"],
        "bounded_error_traces": telemetry["bounded_error_traces"],
    }

    down = telemetry["downstream"]
    if not down["milestone_given"]:
        gate, listing = "closed (no --milestone given)", "(none)"
    elif down["gate"] == "closed":
        gate, listing = "closed (no significant finding in this milestone)", "(none)"
    else:
        gate = "open: " + "; ".join(down["reasons"])
        listing = json.dumps({"milestones": down["milestones"], "skipped": down["skipped"]}, indent=2) \
            if down["milestones"] else "(no live downstream milestones are listed in suggested.txt)"

    return PROMPT_TEMPLATE.format(
        milestone_id=telemetry["milestone"],
        project_root=project_root.name,
        contrastive_fast_runs=json.dumps(telemetry["contrastive_fast_baselines"], indent=2),
        friction_runs=json.dumps(telemetry["friction_runs"], indent=2),
        multi_attempt_tasks=json.dumps(telemetry["multi_attempts"], indent=2),
        capture_status=telemetry["capture_mode"],
        turn_efficiency_and_traces=json.dumps(turn_and_traces, indent=2),
        downstream_gate=gate,
        downstream_milestones=listing,
        independent_evidence=json.dumps(telemetry.get("independent_evidence", {}), indent=2),
        current_tech_stack_md=tech_stack_md,
        current_lessons_md=lessons_md,
    )


def _endpoint_url(base: str, default_endpoint: str) -> str:
    """Join custom base with endpoint, avoiding duplicate /v1 prefixes."""
    clean_base = base.rstrip("/")
    if not default_endpoint.startswith("/"):
        default_endpoint = "/" + default_endpoint
    if clean_base.endswith("/v1") and default_endpoint.startswith("/v1/"):
        default_endpoint = default_endpoint[3:]
    return clean_base + default_endpoint


def _response_usage(value, input_key: str, output_key: str) -> dict[str, int | None]:
    """Optional accounting must not discard a usable proposal."""
    value = value if isinstance(value, dict) else {}
    def count(key):
        item = value.get(key)
        return item if type(item) is int and item >= 0 else None
    return {"input_total": count(input_key), "output": count(output_key)}


def _read_json_object(resp) -> dict:
    """Read a REST reply, refusing anything but a JSON object.

    A proxy may return `[]`, `null` or a string. That is a controlled backend
    failure (ValueError), not an attribute error while reading accounting.
    """
    body = json.loads(resp.read().decode("utf-8"))
    if not isinstance(body, dict):
        raise ValueError("response is not a JSON object")
    return body


def _call_rest_fallback(prompt: str, backend: str, timeout_sec: int = 120) -> tuple[str, str, dict[str, int | None]]:
    """Zero-dependency urllib REST fallback if local CLI binaries are unavailable."""
    custom_base = os.environ.get("TABILET_REFLECT_API_BASE") if backend != "auto" else None

    if backend in ("auto", "claude") and os.environ.get("ANTHROPIC_API_KEY"):
        url = _endpoint_url(custom_base, "/v1/messages") if (backend == "claude" and custom_base) else "https://api.anthropic.com/v1/messages"
        req = urllib.request.Request(
            url,
            data=json.dumps({
                "model": os.environ.get("TABILET_REFLECT_MODEL", "claude-sonnet-5-5"),
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = _read_json_object(resp)
            usage = _response_usage(body.get("usage"), "input_tokens", "output_tokens")
            return body["content"][0]["text"], "rest:claude", usage

    if backend in ("auto", "gemini") and os.environ.get("GEMINI_API_KEY"):
        model = os.environ.get("TABILET_REFLECT_MODEL", "gemini-2.5-pro")
        url = (_endpoint_url(custom_base, f"/v1beta/models/{model}:generateContent")
               if (backend == "gemini" and custom_base)
               else f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent")
        req = urllib.request.Request(
            url,
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = _read_json_object(resp)
            usage = _response_usage(body.get("usageMetadata"), "promptTokenCount", "candidatesTokenCount")
            return body["candidates"][0]["content"]["parts"][0]["text"], "rest:gemini", usage

    if backend in ("auto", "codex", "openai") and os.environ.get("OPENAI_API_KEY"):
        url = (_endpoint_url(custom_base, "/v1/chat/completions")
               if (backend in ("openai", "codex") and custom_base)
               else "https://api.openai.com/v1/chat/completions")
        req = urllib.request.Request(
            url,
            data=json.dumps({
                "model": os.environ.get("TABILET_REFLECT_MODEL", "gpt-4o"),
                "messages": [{"role": "user", "content": prompt}],
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = _read_json_object(resp)
            usage = _response_usage(body.get("usage"), "prompt_tokens", "completion_tokens")
            return body["choices"][0]["message"]["content"], "rest:openai", usage

    raise LookupError(
        "No supported CLI agent ('claude', 'gemini', 'codex') found on PATH and no API keys "
        "(ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY) are set."
    )


def generate_heuristic_proposal(telemetry: dict[str, Any]) -> str:
    """Generate Markdown proposal adhering to contrastive template when no LLM is configured."""
    milestone = telemetry.get("milestone") or "ALL"
    friction = telemetry.get("friction_runs", [])
    multi = telemetry.get("multi_attempts", [])
    fast = telemetry.get("contrastive_fast_baselines", [])
    total = telemetry.get("total_runs_analyzed", 0)

    analysis_points = [
        f"Analyzed {total} runs in milestone `{milestone}` (capture={telemetry.get('capture_mode')}).",
        f"Identified {len(fast)} fast 1st-attempt baseline runs executing under typical thresholds.",
        f"Identified {len(friction)} high-latency or non-completed runs (>120s or failed/blocked).",
        f"Found {len(multi)} tasks requiring multi-run retries before verification passed.",
    ]
    extra = telemetry.get("independent_evidence") or {}
    commits = (extra.get("git_commits") or {}).get("count")
    rounds = (extra.get("review_rounds") or {}).get("iterations")
    if commits:
        analysis_points.append(f"Git shows {commits} commits made during the recorded runs.")
    if rounds:
        analysis_points.append(f"The milestone needed {rounds} review iteration(s).")
    if extra.get("recording_gap"):
        analysis_points.append("Audit recording looks incomplete: " + extra["recording_gap"])

    proposal = f"""# Proposed Harness & Memory Bank Optimization

**Milestone Target:** `{milestone}`  
**Generated By:** `tabilet-audit reflect` (telemetry summary only; no model was used)  
**Safety Contract:** Proposes no edits, so authorization requirements, budget envelopes, and review gates are untouched.

---

## 1. Contrastive Diagnosis
"""
    for point in analysis_points:
        proposal += f"- {point}\n"

    proposal += """
---

## 2. Telemetry Diagnostics

### Fast Baseline Runs (What Succeeded Cleanly)
"""
    if fast:
        proposal += "| Task | Duration (s) | Verification Output |\n|---|---|---|\n"
        for r in fast[:5]:
            proposal += f"| `{r.get('task_label') or 'N/A'}` | {r.get('duration_sec')} | `{(r.get('verification_json') or '')[:80]}` |\n"
    else:
        proposal += "No clean 1st-attempt baseline runs recorded.\n"

    proposal += """
### Friction & High-Latency Tasks (What Stalled)
"""
    if friction:
        proposal += "| Task | Duration (s) | Result | Exit / Reason |\n|---|---|---|---|\n"
        for r in friction[:5]:
            proposal += f"| `{r.get('task_label') or 'N/A'}` | {r.get('duration_sec')} | `{r.get('result')}` | {r.get('failure_reason') or r.get('exit_code') or 'None'} |\n"
    else:
        proposal += "No high-latency or failed tasks detected.\n"

    proposal += """
### Multi-Attempt Hotspots (Retry Loops)
"""
    if multi:
        proposal += "| Task | Attempts | Outcomes | Max Attempt Duration (s) |\n|---|---|---|---|\n"
        for m in multi[:5]:
            proposal += f"| `{m.get('task_label')}` | {m.get('attempt_count')} | `{m.get('observed_outcomes')}` | {m.get('max_attempt_duration_sec')} |\n"
    else:
        proposal += "No multi-attempt retry hotspots detected.\n"

    down = telemetry.get("downstream", {})
    proposal += "\n### Downstream Milestones\n"
    if not down.get("milestone_given"):
        proposal += "Not considered: no `--milestone` was given.\n"
    elif down.get("gate") == "closed":
        proposal += "Not considered: no significant finding in this milestone.\n"
    else:
        proposal += "Gate open: " + "; ".join(down.get("reasons", [])) + ".\n"
        for item in down.get("milestones", []):
            proposal += f"- `{item['id']}` is live ({len(item['open_rows'])} open rows).\n"
        for item in down.get("skipped", []):
            proposal += f"- `{item['id']}` skipped: {item['reason']}.\n"
        proposal += "No model ran, so no amendments are proposed.\n"

    proposal += """
---

## 3. Recommendations

No model analysed this telemetry, so this report proposes no edits to `tech-stack.md` or
`lessons.md`. Install or configure a supported backend (`claude`, `gemini`, or `codex` on
PATH, or `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or `OPENAI_API_KEY`) and rerun
`tabilet-audit reflect`, or take the tables above to `/memory-bank:memory-bank-propose`.
"""
    return proposal


def _is_timeout(exc: BaseException) -> bool:
    return isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)) or (
        isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, TimeoutError))


def _is_no_network(exc: BaseException) -> bool:
    """True when a request failed because the host cannot resolve names or reach any network."""
    import socket
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    return isinstance(reason, socket.gaierror) or (
        isinstance(reason, OSError) and reason.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH))


def available_backends() -> list[str]:
    """Backends reflection could use right now: agent CLIs on PATH, then REST APIs with a key."""
    found = [f"cli:{name}" for name in CLI_BACKENDS if shutil.which(name)]
    return found + [f"rest:{name}" for name, key in REST_KEYS.items() if os.environ.get(key)]


def _run_cli(cmd: list[str], prompt: str, timeout_sec: float) -> tuple[int, str]:
    """Run one agent CLI on the prompt from an empty temporary directory, never the project.

    The prompt carries captured transcript text, so the CLI gets no project working directory to act
    on. It runs in its own session and the whole group is killed on timeout, so a helper process that
    holds the pipes open cannot stretch the reflection budget.
    """
    with tempfile.TemporaryDirectory(prefix="tabilet-reflect-") as scratch:
        proc = subprocess.Popen(cmd, cwd=scratch, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, start_new_session=True)
        try:
            stdout, _ = proc.communicate(prompt, timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                if hasattr(os, "killpg"):
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            proc.communicate()
            raise
        return proc.returncode, stdout


class ImproverResult(tuple):
    """Result of invoke_improver_llm, unpacking as (text, source) for backwards compatibility."""

    def __new__(cls, text: str, source: str, usage: dict[str, int | None] | None = None):
        return super().__new__(cls, (text, source))

    def __init__(self, text: str, source: str, usage: dict[str, int | None] | None = None):
        self.text = text
        self.source = source
        self.usage = usage or {"input_total": None, "output": None}


def invoke_improver_llm(
    telemetry: dict[str, Any],
    project_root: pathlib.Path,
    backend: str = "auto",
    timeout_sec: float = 120,
) -> ImproverResult:
    """
    Run the improver through a local CLI agent (Claude Code, Gemini CLI, or Codex CLI) on stdin,
    then a REST API, all inside one shared deadline of `timeout_sec`. Returns (markdown, source).
    Only when no backend is configured at all does it return the model-free telemetry summary,
    labelled source "heuristic"; a configured backend that fails raises AuditError, and running
    out of time raises BudgetExceeded, rather than passing a template off as analysis.
    """
    prompt = build_reflection_prompt(telemetry, project_root)
    deadline = time.monotonic() + timeout_sec

    def remaining() -> float:
        left = deadline - time.monotonic()
        if left <= 0:
            detail = f" after {'; '.join(failures)}" if failures else ""
            raise BudgetExceeded(f"reflection time budget exhausted{detail}")
        return left

    cli_candidates: list[tuple[str, list[str]]] = [
        ("claude", ["claude", "-p", "Read the reflection prompt from stdin and output only the requested Markdown proposal."]),
        ("gemini", ["gemini", "-p", "Read the reflection prompt from stdin and output only the requested Markdown proposal."]),
        ("codex", ["codex", "exec", "-"]),
    ]

    if backend != "auto":
        cli_candidates = [c for c in cli_candidates if c[0] == backend]
        # A named endpoint is a REST backend: an agent CLI on PATH would ignore it.
        if os.environ.get("TABILET_REFLECT_API_BASE"):
            cli_candidates = []

    failures: list[str] = []
    timeouts = 0
    unreachable = 0
    for name, cmd in cli_candidates:
        if shutil.which(cmd[0]) is None:
            continue
        try:
            returncode, stdout = _run_cli(cmd, prompt, remaining())
        except (subprocess.TimeoutExpired, OSError) as exc:
            timeouts += _is_timeout(exc)
            failures.append(f"{name} CLI: {type(exc).__name__}")
            continue
        if returncode == 0 and stdout.strip():
            return ImproverResult(stdout.strip(), f"cli:{name}", {"input_total": None, "output": None})
        failures.append(f"{name} CLI: exit {returncode}" if returncode else f"{name} CLI: empty output")

    # A CLI whose host does not resolve says nothing about a configured REST backend, so that is tried too.
    try:
        text, actual_source, usage = _call_rest_fallback(prompt, backend=backend, timeout_sec=int(remaining()) or 1)
        return ImproverResult(text, actual_source, usage)
    except BudgetExceeded:
        # A CLI used the whole budget, so the REST fallback never started: that is a timeout too.
        timeouts += 1
        failures.append("REST API: no time left")
    except LookupError:
        if os.environ.get("TABILET_REFLECT_API_BASE") and backend != "auto":
            raise audit.AuditError("explicit reflection endpoint has no matching API credential")
        if not failures:
            return ImproverResult(generate_heuristic_proposal(telemetry), "heuristic", {"input_total": None, "output": None})
    except urllib.error.HTTPError as exc:
        failures.append(f"REST API: HTTP {exc.code}")
    except (urllib.error.URLError, OSError, http.client.HTTPException, ValueError, KeyError, IndexError, TypeError) as exc:
        if _is_no_network(exc):
            unreachable += 1
            failures.append(f"REST API: no network ({getattr(exc, 'reason', exc)})")
        else:
            timeouts += _is_timeout(exc)
            failures.append(f"REST API: {type(exc).__name__}")
    detail = "; ".join(failures)
    if failures and unreachable == len(failures):
        raise BackendUnreachable(f"reflection backend unreachable ({detail}); "
                                 "the host probably blocks network, so run reflect with network access")
    if timeouts == len(failures):
        raise BudgetExceeded(f"reflection backend did not finish inside its time budget ({detail})")
    raise audit.AuditError(f"reflection backend failed ({detail}); no proposal was written")


# The only commands a model-proposed probe may start, even with the host-shell acknowledgment:
# a probe checks a verification idea, so it is a project test runner, never a general command.
PROBE_ALLOWED = (
    ("python3", "-m", "unittest"), ("python3", "-m", "pytest"), ("python", "-m", "unittest"),
    ("python", "-m", "pytest"), ("pytest",), ("npm", "test"), ("go", "test"), ("cargo", "test"),
    ("make", "test"),
)
PROBE_METACHARACTERS = re.compile(r"[;&|<>`$()\\\n]")


PROBE_MAX_COMMANDS = 3


def _probe_skip(command: str, reason: str) -> dict[str, Any]:
    return {
        "command": command,
        "status": "SKIPPED",
        "exit_code": None,
        "duration_sec": None,
        "coverage": {"tests_run": None, "has_coverage": None, "summary": None},
        "output_snippet": reason,
    }


def _coverage(tests_run: int | None, summary: str) -> dict[str, Any]:
    return {"tests_run": tests_run, "has_coverage": None if tests_run is None else tests_run > 0, "summary": summary}


def extract_coverage_evidence(output: str, runner: str | None = None) -> dict[str, Any]:
    """Parse test runner output into a test count (`tests_run`, None when the runner prints none).

    Counts come from the runner's own totals: Cargo prints one total per test binary, so they are summed,
    and a wrapper line such as Jest's `Test Suites:` or Go's per-package `ok` is never read as a test count."""
    # 1. unittest: "Ran 5 tests in 0.002s"
    ran = re.findall(r"\bRan\s+(\d+)\s+tests?\b", output)
    if ran:
        n = sum(int(r) for r in ran)
        return _coverage(n, f"Ran {n} test{'s' if n != 1 else ''}")

    # 2. Jest ("Tests: 1 failed, 7 passed, 8 total") and Vitest ("Tests  1 failed | 7 passed (8)")
    jest = re.search(r"^\s*Tests:([^\n]*)$", output, re.M)
    if jest and (total := re.search(r"(\d+)\s+total\b", jest.group(1))):
        n = int(total.group(1))
        passed = re.search(r"(\d+)\s+passed\b", jest.group(1))
        return _coverage(n, f"{int(passed.group(1)) if passed else n}/{n} tests passed")
    vitest = re.search(r"^\s*Tests\s+(?:\d+\s+failed\s*\|\s*)?(\d+)\s+passed\s*\((\d+)\)", output, re.M)
    if vitest:
        n = int(vitest.group(2))
        return _coverage(n, f"{vitest.group(1)}/{n} tests passed")

    # 3. Cargo: one "test result: ok. N passed; M failed" line per test binary (unit, integration, doc)
    cargo = re.findall(r"test result:\s*\w+\.\s*(\d+)\s*passed;\s*(\d+)\s*failed", output)
    if cargo:
        passed, failed = sum(int(a) for a, _ in cargo), sum(int(b) for _, b in cargo)
        return _coverage(passed + failed, f"{passed} passed, {failed} failed")

    # Go package output is interpreted only for a declared Go runner.
    if runner == "go":
        if re.search(r"^FAIL(?:\s|$)", output, re.M):
            return _coverage(None, "go test failed; test count unknown")
        go_ok = [line for line in output.splitlines()
                 if re.match(r"ok\s+[^\s]+\s+(?:[0-9.]+s|\(cached\))", line)
                 and "[no tests to run]" not in line]
        if go_ok:
            return {"tests_run": None, "has_coverage": True, "summary": f"go test: {len(go_ok)} package(s) ok"}
        if re.search(r"\[no test files\]|\[no tests to run\]", output):
            return _coverage(0, "no test files")
        return _coverage(None, "unparsed Go output")

    # 5. Mocha: "22 passing", "1 failing"
    passing = re.search(r"^\s*(\d+)\s+passing\b", output, re.M)
    if passing:
        failing = re.search(r"^\s*(\d+)\s+failing\b", output, re.M)
        n = int(passing.group(1)) + (int(failing.group(1)) if failing else 0)
        return _coverage(n, f"{passing.group(1)} passing" + (f", {failing.group(1)} failing" if failing else ""))

    # 6. pytest: "collected 0 items" / "no tests ran", else the summary line "12 passed, 2 failed in 0.35s"
    if re.search(r"\b(?:collected 0 items|no tests ran)\b", output, re.I):
        return _coverage(0, "0 tests collected/run")
    for line in output.splitlines():
        if re.search(r"\bin\s+\d+(?:\.\d+)?s\b", line):
            counts = {kind: int(n) for n, kind in re.findall(r"(\d+)\s+(passed|failed)\b", line)}
            if counts:
                passed, failed = counts.get("passed", 0), counts.get("failed", 0)
                return _coverage(passed + failed, f"{passed} passed" + (f", {failed} failed" if failed else ""))

    return {"tests_run": None, "has_coverage": None, "summary": "unparsed runner output"}


def _run_probe(argv: list[str], cwd: pathlib.Path, timeout_sec: int) -> dict[str, Any]:
    """One probe run in its own session. A timeout kills the whole process group and reaps it."""
    t0 = time.monotonic()
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)
    except OSError as exc:
        return {"error": type(exc).__name__}
    try:
        out, err = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            if hasattr(os, "killpg"):
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        proc.communicate()
        return {"timeout": True}
    return {"exit_code": proc.returncode, "output": out + "\n" + err, "duration": time.monotonic() - t0}


def probe_proposed_commands(markdown_proposal: str, project_root: pathlib.Path, timeout_sec: int = 15,
                            enabled: bool = False, repeats: int = 2) -> list[dict[str, Any]]:
    """
    Probe step: dry-run commands from ```probe-commands``` blocks. The block is model
    output built from untrusted transcript text, so it is inert unless the caller opts in with
    --probe AND ALLOW_UNSANDBOXED_SHELL=1. Even then each line runs without a shell, rejects shell
    metacharacters and anything but an allowed test runner, and runs in its own session that is killed on timeout.
    At most PROBE_MAX_COMMANDS distinct commands run, so a probe takes at most
    PROBE_MAX_COMMANDS x repeats x timeout_sec. A command that passes is repeated up to `repeats` runs in all
    to average its duration; a repeat that fails or times out makes it UNSTABLE, not PASSED. Output is
    inspected for a test count.
    """
    pattern = re.compile(r"```probe-commands\s+(.*?)```", re.DOTALL)
    commands = list(dict.fromkeys(
        line.strip()
        for block in pattern.findall(markdown_proposal)
        for line in block.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ))
    if not commands:
        return []
    if not enabled:
        return [_probe_skip(c, "Not run: probing is opt-in (--probe).") for c in commands]
    if os.environ.get("ALLOW_UNSANDBOXED_SHELL") != "1":
        return [_probe_skip(c, "Not run: probing executes on the host and needs ALLOW_UNSANDBOXED_SHELL=1.") for c in commands]

    results = []
    started = 0
    for cmd in commands:
        try:
            argv = shlex.split(cmd)
        except ValueError:
            results.append(_probe_skip(cmd, "Not run: command could not be parsed."))
            continue
        if not argv or PROBE_METACHARACTERS.search(cmd):
            results.append(_probe_skip(cmd, "Not run: shell metacharacters are not allowed in probes."))
            continue
        if not any(tuple(argv[:len(prefix)]) == prefix for prefix in PROBE_ALLOWED):
            results.append(_probe_skip(cmd, "Not run: probes may only start a project test runner "
                                            "(python3 -m unittest or pytest, pytest, npm test, go test, cargo test, make test)."))
            continue
        if started >= PROBE_MAX_COMMANDS:
            results.append(_probe_skip(cmd, f"Not run: at most {PROBE_MAX_COMMANDS} probe commands run."))
            continue
        started += 1
        no_coverage = {"tests_run": None, "has_coverage": None, "summary": None}
        first = _run_probe(argv, project_root, timeout_sec)
        if "error" in first:
            results.append({"command": cmd, "status": "FAILED", "exit_code": -1, "duration_sec": None,
                            "coverage": no_coverage, "output_snippet": first["error"]})
            continue
        if first.get("timeout"):
            results.append({"command": cmd, "status": "TIMEOUT", "exit_code": -1, "duration_sec": float(timeout_sec),
                            "coverage": no_coverage, "output_snippet": f"Command exceeded probe timeout of {timeout_sec}s."})
            continue

        coverage = extract_coverage_evidence(first["output"], runner=argv[0])
        snippet = truncate_middle(first["output"], 200, 400).strip()
        entry = {"command": cmd, "exit_code": first["exit_code"], "duration_sec": round(first["duration"], 3),
                 "coverage": coverage, "output_snippet": snippet}
        if first["exit_code"] != 0:
            results.append({**entry, "status": "FAILED"})
            continue
        if coverage.get("has_coverage") is False:
            results.append({**entry, "status": "ZERO_COVERAGE"})
            continue

        # Passed once. Every repeat must pass too: a flaky command is not a stable profile.
        durations = [first["duration"]]
        unstable = None
        for _ in range(max(0, repeats - 1)):
            again = _run_probe(argv, project_root, timeout_sec)
            if "error" in again:
                unstable = f"could not start on the repeat run ({again['error']})"
            elif again.get("timeout"):
                unstable = f"timed out after {timeout_sec}s on the repeat run"
            elif again["exit_code"] != 0:
                unstable = f"failed with exit {again['exit_code']} on the repeat run"
            else:
                durations.append(again["duration"])
                continue
            break
        if unstable:
            results.append({**entry, "status": "UNSTABLE", "output_snippet": f"Passed once, then {unstable}."})
            continue
        results.append({**entry, "status": "PASSED", "exit_code": 0,
                        "duration_sec": round(sum(durations) / len(durations), 3)})
    return results


def _compare_to_baseline(probe_results):
    if not probe_results:
        return []
    return ["> **Smoke checks only:** These commands report observed results and timings. "
            "Test counts do not establish equivalent coverage or subset relationships, and short "
            "probes do not establish a faster replacement profile. Preserve required verification."]


def format_compose_report(proposal_md: str, probe_results: list[dict[str, Any]]) -> str:
    """Compose final proposal artifact with live probe verification badges and comparison table."""
    if not probe_results:
        return proposal_md

    probe_lines = ["\n\n---\n## Automated Probe Verification (`tabilet-reflect`)", ""]
    probe_lines.append("| Proposed Command | Probe Status | Avg Duration | Coverage Evidence | Output Snippet |")
    probe_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for pr in probe_results:
        snippet_clean = pr["output_snippet"].replace("\n", " ").replace("|", "\\|")[:140]
        dur_str = f"{pr['duration_sec']:.2f}s" if pr.get("duration_sec") is not None else "n/a"
        cov_summary = (pr.get("coverage") or {}).get("summary") or "n/a"
        probe_lines.append(f"| `{pr['command']}` | **{pr['status']}** | {dur_str} | {cov_summary} | {snippet_clean} |")

    for note in _compare_to_baseline(probe_results):
        probe_lines.append("\n" + note)

    if any(p["status"] == "ZERO_COVERAGE" for p in probe_results):
        probe_lines.append(
            "\n> **WARNING:** One or more proposed commands executed 0 tests. A command with zero coverage "
            "must NOT be used as a test profile replacement in `tech-stack.md`."
        )
    if any(p["status"] == "SKIPPED" for p in probe_results):
        probe_lines.append(
            "\n> **NOTE:** Some proposed commands were not run. Verify them yourself before promoting "
            "them into `tech-stack.md`."
        )
    if any(p["status"] in ("FAILED", "TIMEOUT", "UNSTABLE") for p in probe_results):
        probe_lines.append(
            "\n> **WARNING:** One or more proposed commands failed, timed out or were unstable in the local subprocess probe. "
            "Do NOT promote those commands into `tech-stack.md` without fixing the flags."
        )
    return proposal_md.rstrip() + "\n" + "\n".join(probe_lines) + "\n"


def _inside(path: pathlib.Path, root: pathlib.Path) -> bool:
    return path == root or root in path.parents


def _in_git(project_root: pathlib.Path) -> bool:
    try:
        proc = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project_root,
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _git_ignored(path: pathlib.Path, project_root: pathlib.Path) -> bool:
    try:
        proc = subprocess.run(["git", "check-ignore", "-q", "--", str(path)], cwd=project_root,
                              capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def reflect_command(project_path: str = ".", milestone_id: str | None = None,
                    dry_run: bool = False, output_path: str | None = None,
                    format_type: str = "tabilet", backend: str = "auto",
                    print_prompt: bool = False, probe: bool = False,
                    budget_percent: float = DEFAULT_BUDGET_PERCENT) -> dict[str, Any]:
    """Execute the reflect command and return structured dictionary for tabilet-audit dispatch."""
    project_root, _ = resolve_project_db(project_path)

    if format_type == "trajectories":
        trajectories = export_trajectories(project_root, milestone_id=milestone_id)
        if dry_run:
            return {"status": "ok", "dry_run": True, "format": "trajectories", "trajectories": trajectories}
        # Trajectories carry captured transcripts that live only in the Git-ignored audit database.
        if not output_path:
            raise audit.AuditError("--output is required for trajectories: they contain captured transcripts")
        out_file = (project_root / output_path).resolve()
        if _inside(out_file, project_root) and not _git_ignored(out_file, project_root):
            raise audit.AuditError("trajectories contain captured transcripts; write them outside the project or to a Git-ignored path")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(trajectories, indent=2) + "\n", encoding="utf-8")
        return {
            "status": "ok",
            "dry_run": False,
            "format": "trajectories",
            "output_file": str(out_file),
            "milestone_id": milestone_id,
            "task_trajectories_count": len(trajectories.get("tasks", [])),
        }

    out_file = (project_root / (output_path or DEFAULT_PROPOSAL_PATH)).resolve()
    if not _inside(out_file, project_root):
        raise audit.AuditError("--output must stay inside the project")
    if (not output_path and not dry_run and not print_prompt and _in_git(project_root)
            and not _git_ignored(out_file, project_root)):
        raise audit.AuditError(f"{DEFAULT_PROPOSAL_PATH} is not Git-ignored, so the proposal would dirty the "
                               "worktree; re-run 'tabilet-audit audit enable .' to add the ignore rule")

    telemetry = extract_telemetry(project_root, milestone_id=milestone_id)

    if print_prompt:
        return {"status": "ok", "prompt": build_reflection_prompt(telemetry, project_root)}

    if dry_run:
        return {"status": "ok", "dry_run": True, "format": "tabilet", "telemetry": telemetry}

    # Propose -> Probe -> Compose
    budget = model_budget_sec(telemetry["milestone_wall_sec"], budget_percent)
    note = None
    usage = {"input_total": None, "output": None}
    if budget < MIN_MODEL_BUDGET_SEC:
        raw_proposal, source = generate_heuristic_proposal(telemetry), "heuristic"
        note = f"model skipped: {budget:.0f}s budget is under the {MIN_MODEL_BUDGET_SEC}s minimum"
    else:
        try:
            res = invoke_improver_llm(telemetry, project_root, backend=backend, timeout_sec=budget)
            raw_proposal, source = res[0], res[1]
            usage = getattr(res, "usage", usage)
        except BudgetExceeded as exc:
            raw_proposal, source = generate_heuristic_proposal(telemetry), "heuristic"
            note = f"model skipped: {exc}"
    probe_results = probe_proposed_commands(raw_proposal, project_root, enabled=probe)
    final_proposal = format_compose_report(raw_proposal, probe_results)
    if note:
        # The reason must survive in the file: the JSON result is gone once a host agent summarises it.
        final_proposal += f"\n> Why no model analysis: {note}.\n"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(final_proposal, encoding="utf-8")

    return {
        "status": "ok",
        "dry_run": False,
        "format": "tabilet",
        "output_file": str(out_file),
        "milestone_id": milestone_id,
        "proposal_source": source,
        "usage": usage,
        "model_budget_sec": round(budget, 1),
        "budget_note": note,
        "downstream_gate": telemetry["downstream"]["gate"],
        "downstream_considered": [m["id"] for m in telemetry["downstream"]["milestones"]],
        "fast_baselines_count": len(telemetry["contrastive_fast_baselines"]),
        "friction_runs_count": len(telemetry["friction_runs"]),
        "multi_attempt_count": len(telemetry["multi_attempts"]),
        "probes_executed": sum(1 for r in probe_results if r["status"] != "SKIPPED"),
        "probes_skipped": sum(1 for r in probe_results if r["status"] == "SKIPPED"),
    }

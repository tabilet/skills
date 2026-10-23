#!/usr/bin/env python3
"""Offline contrastive milestone reflection and Harness² Propose-Probe-Compose adapter for Tabilet Memory Bank."""
from __future__ import annotations

import argparse
import contextlib
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
import urllib.error
import urllib.request
from typing import Any

import tabilet_audit as audit

TOOLKIT_INTERFACE = 4
DEFAULT_PROPOSAL_PATH = "tabilet/memory-bank/suggested-harness-update.md"

PROMPT_TEMPLATE = """You are the Harness² Contrastive Experience Reflector for Tabilet Memory Bank.
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

--- 2. CURRENT HARNESS STATE ---
Current `tech-stack.md`:
{current_tech_stack_md}

Current `lessons.md`:
{current_lessons_md}
--------------------------------

YOUR TASK:
1. CONTRAST: Compare the verification commands and turn patterns of the Fast Baseline Runs (1A) against the Friction/Multi-Attempt Runs (1B/1C). Identify why slow/failed tasks diverged.
2. PROPOSE: Formulate concise, additive updates to `tabilet/memory-bank/tech-stack.md` and `tabilet/memory-bank/lessons.md`.
3. PROBE COMMAND EXTRACTION: If you propose any new or modified shell/test verification command for `tech-stack.md`, list the exact runnable shell command inside a fenced ```probe-commands``` block (one command per line) so the harness can dry-run and verify it before composing the final proposal.
4. STRICT SAFETY CONSTRAINT: You must NOT modify, weaken, or remove any authorization blocks, security gates, review iteration limits, or verification attempt limits.

OUTPUT FORMAT:
Return ONLY a Markdown document containing:
- ## Contrastive Diagnosis (3-4 bullet points comparing fast baselines vs. friction runs)
- ## Probe Commands (fenced `probe-commands` block with fast verification commands to dry-run, or empty if none)
- ## Proposed Edits to tech-stack.md (Unified Diff)
- ## Proposed Entry for lessons.md (Standard Tabilet Lesson Schema)
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


def extract_telemetry(project_path: str | pathlib.Path = ".", milestone_id: str | None = None) -> dict[str, Any]:
    """Extract contrastive telemetry (fast baselines vs. friction runs) from v4 schema."""
    project_root, db_path = resolve_project_db(project_path)
    conn = get_readonly_connection(db_path)
    with contextlib.closing(conn):
        # 1A. Friction & Long Runs (Deduplicated per run_id via terminal sequence)
        q_friction = """
        SELECT r.run_id, r.operation, r.result, r.git_head,
               (strftime('%s', COALESCE(r.completed_at, 'now')) - strftime('%s', r.started_at)) AS duration_sec,
               COALESCE(e.task_label, 'N/A') AS task_label,
               COALESCE(e.event_type, 'N/A') AS terminal_event_type,
               COALESCE(e.new_state, 'N/A') AS final_task_state,
               json_extract(e.details_json, '$.exit_code') AS exit_code,
               SUBSTR(
                   COALESCE(json_extract(e.details_json, '$.reason'), json_extract(e.details_json, '$.summary'), ''),
                   1, 600
               ) AS failure_reason
        FROM runs r
        JOIN events e ON r.run_id = e.run_id
        WHERE (:m IS NULL OR e.milestone_id = :m)
          AND e.sequence = (
              SELECT MAX(e2.sequence)
              FROM events e2
              WHERE e2.run_id = r.run_id
                AND e2.event_type IN ('run_failed', 'run_blocked', 'task_transition')
          )
          AND (
              r.result != 'completed'
              OR (strftime('%s', COALESCE(r.completed_at, 'now')) - strftime('%s', r.started_at)) > 120
          )
        GROUP BY r.run_id
        ORDER BY duration_sec DESC
        LIMIT 10;
        """
        friction_runs = []
        for row in conn.execute(q_friction, {"m": milestone_id}).fetchall():
            item = dict(row)
            item["failure_reason"] = truncate_middle(item.get("failure_reason"), 300, 500)
            friction_runs.append(item)

        # 1B. Contrastive Fast-Run Baselines (1st-attempt clean completions)
        q_baseline = """
        SELECT r.run_id, e.task_label,
               (strftime('%s', COALESCE(r.completed_at, 'now')) - strftime('%s', r.started_at)) AS duration_sec,
               SUBSTR(COALESCE(e.verification_json, ''), 1, 500) AS verification_json
        FROM runs r
        JOIN events e ON r.run_id = e.run_id
        WHERE (:m IS NULL OR e.milestone_id = :m)
          AND r.result = 'completed'
          AND e.event_type = 'task_transition'
          AND e.new_state = 'completed'
          AND e.task_label IN (
              SELECT task_label FROM events
              WHERE (:m IS NULL OR milestone_id = :m) AND task_label IS NOT NULL
              GROUP BY task_label HAVING COUNT(DISTINCT run_id) = 1
          )
        GROUP BY r.run_id
        ORDER BY duration_sec ASC
        LIMIT 5;
        """
        fast_baselines = []
        for row in conn.execute(q_baseline, {"m": milestone_id}).fetchall():
            item = dict(row)
            item["verification_json"] = truncate_middle(item.get("verification_json"), 250, 250)
            fast_baselines.append(item)

        # 2. Multi-Attempt Tasks (Approaching or hitting 3-attempt gate)
        q_multi = """
        SELECT e.task_label, e.milestone_id,
               COUNT(DISTINCT e.run_id) AS attempt_count,
               GROUP_CONCAT(DISTINCT r.result) AS observed_outcomes,
               MAX(strftime('%s', COALESCE(r.completed_at, 'now')) - strftime('%s', r.started_at)) AS max_attempt_duration_sec
        FROM events e
        JOIN runs r ON e.run_id = r.run_id
        WHERE (:m IS NULL OR e.milestone_id = :m)
          AND e.task_label IS NOT NULL
        GROUP BY e.task_label, e.milestone_id
        HAVING attempt_count > 1
        ORDER BY attempt_count DESC
        LIMIT 10;
        """
        multi_attempts = [dict(row) for row in conn.execute(q_multi, {"m": milestone_id}).fetchall()]

        # 3. Turn-Level Efficiency & Captured Messages
        q_turns = """
        SELECT run_id,
               COUNT(*) AS total_turns,
               MIN(CASE WHEN text LIKE '%edit_file%' OR text LIKE '%write_file%' OR text LIKE '%apply_patch%'
                        THEN sequence END) AS first_edit_turn
        FROM captured_messages
        WHERE run_id IN (
            SELECT DISTINCT r.run_id FROM runs r
            JOIN events e ON r.run_id = e.run_id
            WHERE (:m IS NULL OR e.milestone_id = :m)
        )
        GROUP BY run_id;
        """
        turn_stats = [dict(row) for row in conn.execute(q_turns, {"m": milestone_id}).fetchall()]

        error_traces: dict[str, list[dict[str, Any]]] = {}
        if turn_stats and friction_runs:
            for fr in friction_runs[:5]:
                rid = fr["run_id"]
                msgs = conn.execute(
                    """
                    SELECT sequence, role, text FROM captured_messages
                    WHERE run_id = ? ORDER BY sequence DESC LIMIT 3
                    """,
                    (rid,),
                ).fetchall()
                error_traces[rid] = [
                    {"turn": m["sequence"], "role": m["role"], "snippet": truncate_middle(m["text"], 300, 600)}
                    for m in reversed(msgs)
                ]

        total_runs_row = conn.execute("""
            SELECT COUNT(DISTINCT r.run_id) FROM runs r
            JOIN events e ON r.run_id = e.run_id
            WHERE (:m IS NULL OR e.milestone_id = :m)
        """, {"m": milestone_id}).fetchone()
        total_runs = total_runs_row[0] if total_runs_row else 0

    capture_mode = "relevant" if turn_stats else "metadata-only"

    # Read memory files
    tech_stack_file = project_root / "tabilet" / "memory-bank" / "tech-stack.md"
    current_tech_stack = tech_stack_file.read_text(encoding="utf-8") if tech_stack_file.is_file() else ""

    lessons_file = project_root / "tabilet" / "memory-bank" / "lessons.md"
    current_lessons = lessons_file.read_text(encoding="utf-8") if lessons_file.is_file() else ""

    return {
        "project_root": str(project_root),
        "milestone": milestone_id or "ALL",
        "capture_mode": capture_mode,
        "total_runs_analyzed": total_runs,
        "contrastive_fast_baselines": fast_baselines,
        "friction_runs": friction_runs,
        "multi_attempts": multi_attempts,
        "turn_efficiency": turn_stats,
        "bounded_error_traces": error_traces,
        "tech_stack_present": bool(current_tech_stack),
        "lessons_present": bool(current_lessons),
    }


def export_harness2_trajectories(project_path: str | pathlib.Path = ".", milestone_id: str | None = None) -> dict[str, Any]:
    """Export audit records into Harness² trajectory format for empirical evaluation."""
    _, db_path = resolve_project_db(project_path)
    conn = get_readonly_connection(db_path)
    with contextlib.closing(conn):
        runs = conn.execute("""
            SELECT r.run_id, r.result, e.task_label, e.milestone_id,
                   (strftime('%s', COALESCE(r.completed_at, 'now')) - strftime('%s', r.started_at)) AS duration_sec,
                   e.verification_json, e.details_json
            FROM runs r
            JOIN events e ON r.run_id = e.run_id AND e.event_type IN ('task_transition', 'run_failed', 'run_blocked')
            WHERE (:m IS NULL OR e.milestone_id = :m)
            ORDER BY r.started_at ASC
        """, {"m": milestone_id}).fetchall()

        tasks = []
        for r in runs:
            turns = conn.execute("""
                SELECT sequence, role, text
                FROM captured_messages
                WHERE run_id = ?
                ORDER BY sequence ASC
            """, (r["run_id"],)).fetchall()

            tasks.append({
                "task_id": r["task_label"],
                "milestone_id": r["milestone_id"],
                "status": r["result"],
                "duration_sec": r["duration_sec"],
                "verification": json.loads(r["verification_json"]) if r["verification_json"] else None,
                "turns": [{"turn": t["sequence"], "role": t["role"], "text": t["text"]} for t in turns],
            })

    return {"milestone_id": milestone_id, "tasks": tasks}


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

    return PROMPT_TEMPLATE.format(
        milestone_id=telemetry["milestone"],
        project_root=project_root.name,
        contrastive_fast_runs=json.dumps(telemetry["contrastive_fast_baselines"], indent=2),
        friction_runs=json.dumps(telemetry["friction_runs"], indent=2),
        multi_attempt_tasks=json.dumps(telemetry["multi_attempts"], indent=2),
        capture_status=telemetry["capture_mode"],
        turn_efficiency_and_traces=json.dumps(turn_and_traces, indent=2),
        current_tech_stack_md=tech_stack_md,
        current_lessons_md=lessons_md,
    )


def _call_rest_fallback(prompt: str, backend: str, timeout_sec: int = 120) -> str:
    """Zero-dependency urllib REST fallback if local CLI binaries are unavailable."""
    if backend in ("auto", "claude") and os.environ.get("ANTHROPIC_API_KEY"):
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
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
            body = json.loads(resp.read().decode("utf-8"))
            return body["content"][0]["text"]

    if backend in ("auto", "gemini") and os.environ.get("GEMINI_API_KEY"):
        model = os.environ.get("TABILET_REFLECT_MODEL", "gemini-2.5-pro")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        req = urllib.request.Request(
            url,
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["candidates"][0]["content"]["parts"][0]["text"]

    if backend in ("auto", "codex", "openai") and os.environ.get("OPENAI_API_KEY"):
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
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
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]

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

    proposal += """
---

## 3. Recommendations

No model analysed this telemetry, so this report proposes no edits to `tech-stack.md` or
`lessons.md`. Install or configure a supported backend (`claude`, `gemini`, or `codex` on
PATH, or `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or `OPENAI_API_KEY`) and rerun
`tabilet-audit reflect`, or take the tables above to `/memory-bank:memory-bank-propose`.
"""
    return proposal


def invoke_improver_llm(
    telemetry: dict[str, Any],
    project_root: pathlib.Path,
    backend: str = "auto",
    timeout_sec: int = 120,
) -> tuple[str, str]:
    """
    Run the improver through a local CLI agent (Claude Code, Gemini CLI, or Codex CLI) on stdin,
    then a REST API. Returns (markdown, source). Only when no backend is configured at all does it
    return the model-free telemetry summary, labelled source "heuristic"; a configured backend that
    fails raises AuditError rather than passing a template off as analysis.
    """
    prompt = build_reflection_prompt(telemetry, project_root)

    cli_candidates: list[tuple[str, list[str]]] = [
        ("claude", ["claude", "-p", "Read the reflection prompt from stdin and output only the requested Markdown proposal."]),
        ("gemini", ["gemini", "-p", "Read the reflection prompt from stdin and output only the requested Markdown proposal."]),
        ("codex", ["codex", "exec", "-"]),
    ]

    if backend != "auto":
        cli_candidates = [c for c in cli_candidates if c[0] == backend]

    failures: list[str] = []
    for name, cmd in cli_candidates:
        if shutil.which(cmd[0]) is None:
            continue
        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            failures.append(f"{name} CLI: {type(exc).__name__}")
            continue
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip(), f"cli:{name}"
        failures.append(f"{name} CLI: exit {proc.returncode}" if proc.returncode else f"{name} CLI: empty output")

    try:
        return _call_rest_fallback(prompt, backend=backend, timeout_sec=timeout_sec), f"rest:{backend}"
    except LookupError:
        if not failures:
            return generate_heuristic_proposal(telemetry), "heuristic"
    except urllib.error.HTTPError as exc:
        failures.append(f"REST API: HTTP {exc.code}")
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        failures.append(f"REST API: {type(exc).__name__}")
    raise audit.AuditError("reflection backend failed (" + "; ".join(failures) + "); no proposal was written")


# Executables a model-proposed probe must never start, even with the host-shell acknowledgment.
PROBE_DENIED = frozenset({
    "sudo", "su", "rm", "rmdir", "mv", "dd", "mkfs", "chmod", "chown", "curl", "wget", "ssh", "scp",
    "nc", "ncat", "git", "docker", "kill", "pkill", "shutdown", "reboot",
})
PROBE_METACHARACTERS = re.compile(r"[;&|<>`$()\\\n]")


def _probe_skip(command: str, reason: str) -> dict[str, Any]:
    return {"command": command, "status": "SKIPPED", "exit_code": None, "output_snippet": reason}


def probe_proposed_commands(markdown_proposal: str, project_root: pathlib.Path, timeout_sec: int = 15,
                            enabled: bool = False) -> list[dict[str, Any]]:
    """
    Harness² Probe step: dry-run commands from ```probe-commands``` blocks. The block is model
    output built from untrusted transcript text, so it is inert unless the caller opts in with
    --probe AND ALLOW_UNSANDBOXED_SHELL=1. Even then each line runs without a shell, rejects shell
    metacharacters and denied executables, and runs in its own session that is killed on timeout.
    """
    pattern = re.compile(r"```probe-commands\s+(.*?)```", re.DOTALL)
    commands = [
        line.strip()
        for block in pattern.findall(markdown_proposal)
        for line in block.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not commands:
        return []
    if not enabled:
        return [_probe_skip(c, "Not run: probing is opt-in (--probe).") for c in commands]
    if os.environ.get("ALLOW_UNSANDBOXED_SHELL") != "1":
        return [_probe_skip(c, "Not run: probing executes on the host and needs ALLOW_UNSANDBOXED_SHELL=1.") for c in commands]

    results = []
    for cmd in commands:
        try:
            argv = shlex.split(cmd)
        except ValueError:
            results.append(_probe_skip(cmd, "Not run: command could not be parsed."))
            continue
        if not argv or PROBE_METACHARACTERS.search(cmd):
            results.append(_probe_skip(cmd, "Not run: shell metacharacters are not allowed in probes."))
            continue
        if pathlib.PurePath(argv[0]).name in PROBE_DENIED:
            results.append(_probe_skip(cmd, f"Not run: `{pathlib.PurePath(argv[0]).name}` is not allowed in probes."))
            continue
        try:
            proc = subprocess.Popen(
                argv, cwd=project_root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, start_new_session=True,
            )
        except OSError as exc:
            results.append({"command": cmd, "status": "FAILED", "exit_code": -1, "output_snippet": type(exc).__name__})
            continue
        try:
            out, err = proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                if hasattr(os, "killpg"):
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            proc.communicate()
            results.append({
                "command": cmd,
                "status": "TIMEOUT",
                "exit_code": -1,
                "output_snippet": f"Command exceeded probe timeout of {timeout_sec}s.",
            })
            continue
        results.append({
            "command": cmd,
            "status": "PASSED" if proc.returncode == 0 else "FAILED",
            "exit_code": proc.returncode,
            "output_snippet": truncate_middle(out + "\n" + err, 200, 400).strip(),
        })
    return results


def format_compose_report(proposal_md: str, probe_results: list[dict[str, Any]]) -> str:
    """Compose final proposal artifact with live probe verification badges."""
    if not probe_results:
        return proposal_md

    probe_lines = ["\n\n---\n## Automated Probe Verification (`tabilet-reflect`)", ""]
    probe_lines.append("| Proposed Command | Probe Status | Exit Code | Output Snippet |")
    probe_lines.append("| :--- | :--- | :--- | :--- |")
    for pr in probe_results:
        snippet_clean = pr["output_snippet"].replace("\n", " ").replace("|", "\\|")[:160]
        probe_lines.append(f"| `{pr['command']}` | **{pr['status']}** | `{pr['exit_code']}` | {snippet_clean} |")

    if any(p["status"] == "SKIPPED" for p in probe_results):
        probe_lines.append(
            "\n> **NOTE:** Some proposed commands were not run. Verify them yourself before promoting "
            "them into `tech-stack.md`."
        )
    if any(p["status"] in ("FAILED", "TIMEOUT") for p in probe_results):
        probe_lines.append(
            "\n> **WARNING:** One or more proposed commands failed the local subprocess probe. "
            "Do NOT promote those commands into `tech-stack.md` without fixing the flags."
        )
    return proposal_md.rstrip() + "\n" + "\n".join(probe_lines) + "\n"


def _inside(path: pathlib.Path, root: pathlib.Path) -> bool:
    return path == root or root in path.parents


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
                    print_prompt: bool = False, probe: bool = False) -> dict[str, Any]:
    """Execute the reflect command and return structured dictionary for tabilet-audit dispatch."""
    project_root, _ = resolve_project_db(project_path)

    if format_type == "harness2":
        trajectories = export_harness2_trajectories(project_root, milestone_id=milestone_id)
        if dry_run:
            return {"status": "ok", "dry_run": True, "format": "harness2", "trajectories": trajectories}
        # Trajectories carry captured transcripts that live only in the Git-ignored audit database.
        if not output_path:
            raise audit.AuditError("--output is required for harness2 trajectories: they contain captured transcripts")
        out_file = (project_root / output_path).resolve()
        if _inside(out_file, project_root) and not _git_ignored(out_file, project_root):
            raise audit.AuditError("harness2 trajectories contain captured transcripts; write them outside the project or to a Git-ignored path")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(trajectories, indent=2) + "\n", encoding="utf-8")
        return {
            "status": "ok",
            "dry_run": False,
            "format": "harness2",
            "output_file": str(out_file),
            "milestone_id": milestone_id,
            "task_trajectories_count": len(trajectories.get("tasks", [])),
        }

    out_file = (project_root / (output_path or DEFAULT_PROPOSAL_PATH)).resolve()
    if not _inside(out_file, project_root):
        raise audit.AuditError("--output must stay inside the project")

    telemetry = extract_telemetry(project_root, milestone_id=milestone_id)

    if print_prompt:
        return {"status": "ok", "prompt": build_reflection_prompt(telemetry, project_root)}

    if dry_run:
        return {"status": "ok", "dry_run": True, "format": "tabilet", "telemetry": telemetry}

    # Propose -> Probe -> Compose
    raw_proposal, source = invoke_improver_llm(telemetry, project_root, backend=backend)
    probe_results = probe_proposed_commands(raw_proposal, project_root, enabled=probe)
    final_proposal = format_compose_report(raw_proposal, probe_results)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(final_proposal, encoding="utf-8")

    return {
        "status": "ok",
        "dry_run": False,
        "format": "tabilet",
        "output_file": str(out_file),
        "milestone_id": milestone_id,
        "proposal_source": source,
        "fast_baselines_count": len(telemetry["contrastive_fast_baselines"]),
        "friction_runs_count": len(telemetry["friction_runs"]),
        "multi_attempt_count": len(telemetry["multi_attempts"]),
        "probes_executed": sum(1 for r in probe_results if r["status"] != "SKIPPED"),
        "probes_skipped": sum(1 for r in probe_results if r["status"] == "SKIPPED"),
    }

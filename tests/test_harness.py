from __future__ import annotations

import contextlib
import http.server
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sqlite3
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness" / "tackle-memory-bank-api-loop"
CONTROLLER = ROOT / "harness" / "tabilet_controller.py"
BACKTICK = chr(96)
sys.dont_write_bytecode = True
loader = importlib.machinery.SourceFileLoader("harness_under_test", str(HARNESS))
spec = importlib.util.spec_from_loader("harness_under_test", loader)
harness = importlib.util.module_from_spec(spec)
loader.exec_module(harness)
controller_loader = importlib.machinery.SourceFileLoader("controller_under_test", str(CONTROLLER))
controller_spec = importlib.util.spec_from_loader("controller_under_test", controller_loader)
controller = importlib.util.module_from_spec(controller_spec)
controller_loader.exec_module(controller)


def run(*cmd: str, cwd: pathlib.Path, env: dict[str, str] | None = None):
    return subprocess.run(
        list(cmd),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def marker(value: str) -> str:
    return BACKTICK + value + BACKTICK


def make_repo(root: pathlib.Path, state: str | None = None) -> pathlib.Path:
    state = state or marker("[ ]")
    (root / "tabilet/memory-bank").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agent guide\n", encoding="utf-8")
    (root / "tabilet/memory-bank" / "milestone.md").write_text(
        "# Milestone\n\n## M01 - Delivery\n\n**Acceptance.** Feature works.\n", encoding="utf-8"
    )
    (root / "tabilet/memory-bank" / "status-M01.md").write_text(
        "# Status\n\n| Item | State | Notes |\n|---|---|---|\n"
        f"| Implement feature | {state} | Keep this note. |\n",
        encoding="utf-8",
    )
    run("git", "init", "-q", cwd=root)
    run("git", "add", "-A", cwd=root)
    run(
        "git",
        "-c",
        "user.name=Harness Test",
        "-c",
        "user.email=harness@example.test",
        "commit",
        "-qm",
        "initial",
        cwd=root,
    )
    return root


class QueueHandler(http.server.BaseHTTPRequestHandler):
    responses: list[tuple[int, dict[str, str], dict]] = []
    requests: list[dict] = []

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        self.__class__.requests.append(json.loads(self.rfile.read(size)))
        status, headers, body = self.__class__.responses.pop(0)
        encoded = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        return


@contextlib.contextmanager
def fake_api(responses):
    QueueHandler.responses = list(responses)
    QueueHandler.requests = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), QueueHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", QueueHandler
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def openai_response(content: str, finish_reason: str = "stop") -> dict:
    return {
        "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4},
    }


def retirement_text(status: str, milestone_id: str = "M01", **fields: str) -> str:
    metadata = {
        "Milestone": milestone_id,
        "Outcome": "completed",
        "Retired": "2026-09-12",
        "Source status": f"tabilet/memory-bank/status-{milestone_id}.md",
        "Source specification": f"tabilet/memory-bank/milestone.md#{milestone_id.lower()}-delivery",
        "Evidence": "unversioned",
        "Worktree": "unversioned",
        "Review": "passed",
        "Review iterations": "2",
        "Verification": "tests passed; review found no blocking issues",
        "Consolidated into": "no current-truth change",
    }
    metadata.update(fields)
    specification = (
        f"## {milestone_id} - Delivery\n\n**Acceptance.** Feature works.\n\n"
        # A task-looking row in a spec is not executable state.
        f"Example only:\n| Not a task | {marker('[ ]')} | Example |\n"
        "```text\n## Status record\n```\n"
    )
    fence = BACKTICK * 5
    return (
        f"# Retired milestone {milestone_id}\n\n"
        + "\n".join(f"**{key}.** {value}" for key, value in metadata.items())
        + f"\n\n## Milestone specification\n\n{fence}markdown\n"
        + specification
        + f"{fence}\n\n## Status record\n\n{fence}markdown\n"
        + status
        + f"{fence}\n"
    )


def retire_fixture(repo: pathlib.Path, milestone_id: str = "M01", **fields: str) -> pathlib.Path:
    source = repo / "tabilet/memory-bank" / f"status-{milestone_id}.md"
    history = repo / "tabilet" / "docs" / "history"
    history.mkdir(parents=True, exist_ok=True)
    destination = history / source.name
    destination.write_text(retirement_text(source.read_text(), milestone_id, **fields))
    source.unlink()
    index = history / "index.md"
    previous = index.read_text() if index.exists() else (
        "# History\n\n| Milestone | Outcome | Retired | Record | Summary |\n"
        "|---|---|---|---|---|\n"
    )
    index.write_text(
        previous + f"| {milestone_id} | {fields.get('Outcome', 'completed')} | 2026-09-12 | "
        f"[{milestone_id}](status-{milestone_id}.md) | Delivery |\n"
    )
    (repo / "tabilet/memory-bank" / "milestone.md").write_text(
        "# Milestones\n\n[History](../docs/history/index.md)\n"
    )
    return destination


class RetirementTests(unittest.TestCase):
    def test_retired_specification_identity_cannot_be_substituted(self) -> None:
        text = retirement_text(f"| Task | {marker('[+]')} | Verified |\n")
        with self.assertRaisesRegex(ValueError, "specification does not match"):
            harness.retired_record(text.replace("## M01 - Delivery", "## M02 - Other"), "status-M01.md")
        with self.assertRaisesRegex(ValueError, "01 through 99"):
            harness.retired_record(text.replace("M01", "M00"), "status-M00.md")

    def test_fence_with_info_string_does_not_end_literal_example(self) -> None:
        text = (
            "```markdown\n```text\n"
            f"| Hidden | {marker('[ ]')} | example |\n"
            "```\n"
            f"| Real | {marker('[+]')} | evidence |\n"
        )
        self.assertEqual([row["item"] for row in harness.status_rows(text)], ["Real"])

    def test_literal_documents_and_unversioned_provenance_round_trip(self) -> None:
        status = f"# Status\n\n| Task | {marker('[+]')} | Preserve this. |\n"
        record = harness.retired_record(retirement_text(status), "status-M01.md")
        self.assertEqual(record["status"], status)
        self.assertIn("Not a task", record["specification"])
        self.assertEqual(len(harness.status_rows(record["status"])), 1)
        self.assertEqual(record["metadata"]["Evidence"], "unversioned")

    def test_invalid_closure_and_provenance_are_rejected(self) -> None:
        status = f"| Task | {marker('[+]')} | Verified |\n"
        for fields in (
            {"Review": "failed"}, {"Review iterations": "11"},
            {"Evidence": "abc123"}, {"Evidence": "a" * 40},
            {"Retired": "yesterday"}, {"Outcome": "cancelled"},
            {"Outcome": "superseded", "Disposition": "User authorized replacement"},
            {"Milestone": "M02"}, {"Verification": ""},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                harness.retired_record(retirement_text(status, **fields), "status-M01.md")

    def test_open_rows_and_unnamed_successors_prevent_retirement(self) -> None:
        for state in ("[ ]", "[~]", "[!]", "[-]"):
            with self.subTest(state=state), self.assertRaises(ValueError):
                harness.retired_record(
                    retirement_text(f"| Task | {marker(state)} | No outcome |\n"), "status-M01.md"
                )
        record = harness.retired_record(
            retirement_text(f"| Old attempt | {marker('[-]')} | successor: M02 / Retry |\n"),
            "status-M01.md",
        )
        self.assertIn("successor: M02", record["status"])

    def test_malformed_marker_cannot_hide_an_open_retired_task(self) -> None:
        for state in ("[ ]", "`[?]`", "`[x]`", "**[ ]**"):
            with self.subTest(state=state), self.assertRaises(ValueError):
                harness.retired_record(retirement_text(
                    f"| Finished | {marker('[+]')} | Verified |\n"
                    f"| Hidden task | {state} | Invalid marker |\n"
                ), "status-M01.md")

    def test_cancelled_and_superseded_records_keep_distinct_outcomes(self) -> None:
        status = f"| Old work | {marker('[X]')} | User cancelled it. |\n"
        for outcome in ("cancelled", "superseded"):
            with self.subTest(outcome=outcome):
                record = harness.retired_record(retirement_text(
                    status, Outcome=outcome, Disposition="User approved; consumers now depend on M02",
                    Successor="M02",
                ), "status-M01.md")
                self.assertEqual(record["metadata"]["Outcome"], outcome)

    def test_retirement_preserves_row_identity_and_earlier_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
            source = repo / "tabilet/memory-bank" / "status-M01.md"
            source.write_text(source.read_text() + f"| Earlier | {marker('[+]')} | Evidence. |\n")
            before = harness.row_snapshot(repo)
            source.write_text(source.read_text().replace(marker("[~]"), marker("[+]")))
            retired = retire_fixture(repo)
            after = harness.row_snapshot(repo)
            self.assertEqual(harness.status_files(repo), [])
            self.assertEqual(harness.validate_row_transition(
                before, after, ("status-M01.md", "Implement feature", 1)
            ), [])
            retired.write_text(retired.read_text().replace("| Evidence. |", "| Changed old evidence. |"))
            problems = harness.validate_row_transition(before, harness.row_snapshot(repo))
            self.assertTrue(any("earlier row" in problem for problem in problems))

    def test_retirement_cannot_drop_original_status_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo")
            source = repo / "tabilet/memory-bank" / "status-M01.md"
            source.write_text(source.read_text() + "\nImportant historical context.\n")
            before = harness.row_snapshot(repo)
            source.write_text(source.read_text().replace(marker("[ ]"), marker("[+]")))
            retired = retire_fixture(repo)
            retired.write_text(retired.read_text().replace("Important historical context.\n", ""))
            problems = harness.validate_row_transition(before, harness.row_snapshot(repo))
        self.assertTrue(any("discarded original status content" in problem for problem in problems))

    def test_retirement_cannot_summarize_away_the_original_specification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo")
            before = harness.row_snapshot(repo)
            source = repo / "tabilet/memory-bank" / "status-M01.md"
            source.write_text(source.read_text().replace(marker("[ ]"), marker("[+]")))
            retired = retire_fixture(repo)
            retired.write_text(retired.read_text().replace("**Acceptance.** Feature works.", "A short summary."))
            problems = harness.validate_row_transition(before, harness.row_snapshot(repo))
        self.assertTrue(any("discarded original milestone specification" in p for p in problems))

    def test_history_index_and_active_location_must_agree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retired = retire_fixture(repo)
            self.assertEqual(harness.history_snapshot(repo)["problems"], [])
            source = repo / "tabilet/memory-bank" / "status-M01.md"
            source.write_text(f"| Duplicate | {marker('[ ]')} | New work |\n")
            self.assertTrue(any("duplicate active/retired" in p for p in harness.history_snapshot(repo)["problems"]))
            source.unlink()
            retired.unlink()
            self.assertTrue(any("missing or invalid" in p for p in harness.history_snapshot(repo)["problems"]))

    def test_retired_specification_must_leave_active_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retire_fixture(repo)
            milestone = repo / "tabilet/memory-bank" / "milestone.md"
            milestone.write_text(milestone.read_text() + "\n## M01 - Delivery\n\nStill here.\n")
            problems = harness.history_snapshot(repo)["problems"]
        self.assertTrue(any("specification remains active" in p for p in problems))

    def test_existing_retired_records_and_knowledge_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retired = retire_fixture(repo)
            journal = repo / "tabilet" / "docs" / "history" / "knowledge.md"
            journal.write_text("# Retired knowledge\n\nOld lesson with source and replacement.\n")
            active = repo / "tabilet/memory-bank" / "status-M02.md"
            active.write_text(f"| New task | {marker('[ ]')} | Work |\n")
            before = harness.row_snapshot(repo)
            active.write_text(active.read_text().replace(marker("[ ]"), marker("[+]")))
            journal.write_text(journal.read_text() + "\nAnother retired lesson.\n")
            self.assertEqual(harness.validate_row_transition(before, harness.row_snapshot(repo)), [])
            retired.write_text(retired.read_text().replace("# Retired milestone", "# Rewritten milestone"))
            journal.write_text("# Erased knowledge\n")
            problems = harness.validate_row_transition(before, harness.row_snapshot(repo))
        self.assertTrue(any("previously retired record" in p for p in problems))
        self.assertTrue(any("knowledge history was rewritten" in p for p in problems))


class StatusParserTests(unittest.TestCase):
    def test_archive_and_status_ids_are_independent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            (repo / "docs").mkdir()
            (repo / "tabilet/memory-bank").mkdir(parents=True)
            (repo / "tabilet" / "docs").mkdir(parents=True)
            (repo / "tabilet" / "docs" / "archive-A01.md").write_text("# Archive A01\n")
            status = repo / "tabilet/memory-bank" / "status-A01.md"
            status.write_text(f"| Item | {marker('[ ]')} | Notes |\n")
            self.assertEqual(harness.status_files(repo), [status])

    def test_parser_handles_indentation_escaped_pipes_and_fences(self) -> None:
        fence = BACKTICK * 3
        text = (
            f"  | A \\| B | {marker('[ ]')} | visible |\n"
            f"{fence}markdown\n"
            f"| Fake | {marker('[ ]')} | ignored |\n"
            f"{fence}\n"
            f"| Complete | {marker('[+]')} | visible |\n"
            f"| Historical | {marker('[-]')} | visible |\n"
        )
        rows = harness.status_rows(text)
        self.assertEqual(
            [(row["item"], row["state"]) for row in rows],
            [
                ("A | B", "pending"),
                ("Complete", "completed"),
                ("Historical", "historical"),
            ],
        )

    def test_transition_requires_one_actionable_row_to_finish_or_block(self) -> None:
        before = {
            "files": {"status-M01.md"},
            "states": {
                ("status-M01.md", "A", 1): "pending",
                ("status-M01.md", "B", 1): "completed",
            },
        }
        after = {
            "files": {"status-M01.md", "status-M02.md"},
            "states": {
                ("status-M01.md", "A", 1): "completed",
                ("status-M01.md", "B", 1): "completed",
                ("status-M02.md", "C", 1): "pending",
            },
        }
        self.assertEqual(harness.validate_row_transition(before, after), [])
        after["states"][("status-M01.md", "B", 1)] = "blocked"
        self.assertTrue(harness.validate_row_transition(before, after))

    def test_transition_accepts_historical_closure(self) -> None:
        key = ("status-M01.md", "Consumed attempt", 1)
        before = {"files": {"status-M01.md"}, "states": {key: "in_progress"}}
        after = {"files": {"status-M01.md"}, "states": {key: "historical"}}
        self.assertEqual(harness.validate_row_transition(before, after, key), [])

    def test_transition_must_close_the_preexisting_in_progress_row(self) -> None:
        active = ("status-M01.md", "Active", 1)
        other = ("status-M01.md", "Other", 1)
        before = {
            "files": {"status-M01.md"},
            "states": {active: "in_progress", other: "pending"},
        }
        after = {
            "files": {"status-M01.md"},
            "states": {active: "in_progress", other: "completed"},
        }
        problems = harness.validate_row_transition(before, after, active)
        self.assertTrue(any("pre-existing in-progress row" in problem for problem in problems))

    def test_lane_summary_counts_historical_rows_as_nonactionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[-]"))
            summary = harness.lane_summary(repo)
        self.assertEqual(
            summary,
            [
                {
                    "file": "status-M01.md",
                    "actionable": 0,
                    "in_progress": 0,
                    "blocked": 0,
                    "historical": 1,
                }
            ],
        )

    def test_transition_rejects_removed_and_nonpending_new_rows(self) -> None:
        before = {
            "files": {"status-M01.md"},
            "states": {("status-M01.md", "A", 1): "pending"},
        }
        after = {
            "files": {"status-M02.md"},
            "states": {("status-M02.md", "New", 1): "completed"},
        }
        problems = harness.validate_row_transition(before, after)
        self.assertTrue(any("removed" in problem for problem in problems))
        self.assertTrue(any("not pending" in problem for problem in problems))


class ShellToolTests(unittest.TestCase):
    def test_tool_environment_is_minimal_and_provider_keys_never_forward(self) -> None:
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp/home",
            "OPENAI_API_KEY": "provider-secret",
            "PROJECT_FLAG": "allowed",
            "UNRELATED_SECRET": "hidden",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            child = harness.tool_environment(["PROJECT_FLAG"])
        self.assertEqual(child["PROJECT_FLAG"], "allowed")
        self.assertNotIn("OPENAI_API_KEY", child)
        self.assertNotIn("UNRELATED_SECRET", child)

    def test_output_limit_is_combined_and_short_streams_are_unchanged(self) -> None:
        stdout, stderr, truncated = harness.bounded_output("o" * 80, "e" * 80, 100)
        self.assertTrue(truncated)
        self.assertLessEqual(len(stdout) + len(stderr), 100)
        self.assertEqual(harness.bounded_output("out", "err", 100), ("out", "err", False))

    def test_timeout_and_binary_output_are_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            timed = harness.shell_tool(repo, "sleep 2", 1, 1000, False)
            binary = harness.shell_tool(repo, "printf '\\377'", 2, 1000, False)
        self.assertEqual(timed["exit_code"], 124)
        json.dumps(timed)
        json.dumps(binary)

    def test_json_extraction_accepts_braces_and_rejects_arrays(self) -> None:
        fence = BACKTICK * 3
        source = fence + "json\n" + '{"tool":"run_shell","cmd":"awk \'{print $1}\' file"}' + "\n" + fence
        self.assertEqual(harness.extract_json(source)["tool"], "run_shell")
        with self.assertRaises(ValueError):
            harness.extract_json("[]")


class ProviderTests(unittest.TestCase):
    def test_obsolete_archive_snapshot_capture_stops_before_execution(self) -> None:
        with mock.patch.object(sys, "argv", [str(HARNESS), "--model", "test"]), mock.patch.dict(
            os.environ, {}, clear=True
        ):
            args = harness.parse_args()
        self.assertFalse(args.audit_archives)
        with mock.patch.object(sys, "argv", [str(HARNESS), "--model", "test"]), mock.patch.dict(
            os.environ, {"TABILET_AUDIT_ARCHIVES": "1"}, clear=True
        ):
            with self.assertRaises(SystemExit) as stopped:
                harness.parse_args()
            self.assertEqual(stopped.exception.code, 2)

    def test_openai_retries_transient_response_and_reports_usage(self) -> None:
        responses = [
            (429, {"Retry-After": "0"}, {"error": "busy"}),
            (200, {}, openai_response('{"final":"done"}')),
        ]
        with fake_api(responses) as (base, handler):
            result = harness.call_openai(base, "secret", "model", [], None, 100, 2, 1)
        self.assertEqual(result["content"], '{"final":"done"}')
        self.assertEqual(result["usage"]["prompt_tokens"], 10)
        self.assertEqual(len(handler.requests), 2)

    def test_malformed_provider_json_has_stable_exit_code(self) -> None:
        with fake_api([(200, {}, b"not-json")]) as (base, _):
            with self.assertRaises(SystemExit) as stopped:
                harness._post_json(base + "/chat/completions", {}, {}, "Test API", 2, 0)
        self.assertEqual(stopped.exception.code, 22)

    def test_anthropic_payload_omits_sampling_by_default(self) -> None:
        body = {
            "content": [{"type": "text", "text": '{"final":"done"}'}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 8, "output_tokens": 3},
        }
        with fake_api([(200, {}, body)]) as (base, handler):
            result = harness.call_anthropic(
                base,
                "secret",
                "claude",
                [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
                None,
                100,
                2,
                0,
            )
        self.assertEqual(result["stop_reason"], "end_turn")
        self.assertNotIn("temperature", handler.requests[0])
        self.assertEqual(handler.requests[0]["system"], "s")

    def test_refusal_and_history_limit_have_stable_exit_codes(self) -> None:
        args = types.SimpleNamespace(
            max_runs=1,
            max_turns=1,
            max_history_chars=100_000,
            provider="openai",
            api_base="http://unused",
            api_key="",
            model="test",
            temperature=None,
            max_tokens=100,
            api_timeout=2,
            max_retries=0,
        )
        refusal = {
            "content": "cannot comply",
            "stop_reason": "stop",
            "refusal": "policy",
            "usage": {},
        }
        with mock.patch.object(harness, "call_llm", return_value=refusal):
            with self.assertRaises(SystemExit) as stopped:
                harness.one_agent_run(args, ROOT, 1, [], None)
        self.assertEqual(stopped.exception.code, 23)

        args.max_history_chars = 1
        with self.assertRaises(SystemExit) as stopped:
            harness.one_agent_run(args, ROOT, 1, [], None)
        self.assertEqual(stopped.exception.code, 31)


class PostRunGateTests(unittest.TestCase):
    def test_post_run_gate_precedence_is_preserved(self) -> None:
        repo = pathlib.Path("/unused")
        before_rows = {"states": {}}
        after_rows = {"states": {}}
        key = ("status-M01.md", "Implement feature", 1)

        with mock.patch.object(harness, "git_clean", return_value=False), \
                mock.patch.object(harness, "git_head") as head:
            result = harness.post_run_gates(repo, "before", "main", before_rows, after_rows, key)
        self.assertEqual(result["exit_code"], 5)
        head.assert_not_called()

        with mock.patch.object(harness, "git_clean", return_value=True), \
                mock.patch.object(harness, "git_head", return_value="before"), \
                mock.patch.object(harness, "git_branch") as branch:
            result = harness.post_run_gates(repo, "before", "main", before_rows, after_rows, key)
        self.assertEqual(result["exit_code"], 6)
        branch.assert_not_called()

        with mock.patch.object(harness, "git_clean", return_value=True), \
                mock.patch.object(harness, "git_head", return_value="after"), \
                mock.patch.object(harness, "git_branch", return_value="other"), \
                mock.patch.object(harness, "git_is_ancestor") as ancestor:
            result = harness.post_run_gates(repo, "before", "main", before_rows, after_rows, key)
        self.assertEqual(result["exit_code"], 9)
        ancestor.assert_not_called()

        with mock.patch.object(harness, "git_clean", return_value=True), \
                mock.patch.object(harness, "git_head", return_value="after"), \
                mock.patch.object(harness, "git_branch", return_value="main"), \
                mock.patch.object(harness, "git_is_ancestor", return_value=True), \
                mock.patch.object(harness, "validate_row_transition", return_value=["invalid row"]):
            result = harness.post_run_gates(repo, "before", "main", before_rows, after_rows, key)
        self.assertEqual(result["exit_code"], 8)
        self.assertEqual(result["row_problems"], ["invalid row"])


class ControllerCoreTests(unittest.TestCase):
    def controller_fixture(self, tmp: str):
        repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
        core = controller.load_runner_core()
        before_rows = core.row_snapshot(repo)
        selected = core.rows_in_state(repo, "in_progress")[0]
        before_head = core.git_head(repo)
        before_branch = core.git_branch(repo)
        args = types.SimpleNamespace(
            max_turns=3,
            max_history_chars=50000,
            provider="openai",
            api_base="https://api.example.test/v1",
            api_key="fake",
            model="fake-model",
            temperature=0,
            max_tokens=1000,
            api_timeout=5,
            max_retries=0,
            tool_timeout=5,
            max_tool_output=1000,
            allow_dangerous=False,
            tool_env={},
            max_runs=1,
        )

        def executor(target, cmd, timeout, max_output, allow_dangerous, env):
            self.assertEqual(cmd, "write selected task")
            status = target / "tabilet/memory-bank/status-M01.md"
            status.write_text(status.read_text().replace(marker("[~]"), marker("[+]")))
            (target / "feature.py").write_text("verified = True\n")
            return {"exit_code": 0, "stdout": "changed", "stderr": "", "truncated": False}

        responses = [
            {"content": json.dumps({"tool": "run_shell", "cmd": "write selected task"}),
             "stop_reason": "stop", "usage": {}},
            {"content": json.dumps({"final": "Implemented the selected task."}),
             "stop_reason": "stop", "usage": {}},
        ]
        with mock.patch.object(core, "call_llm", side_effect=responses) as provider:
            result = controller.run_controller_agent(
                core,
                args,
                repo,
                1,
                core.lane_summary(repo),
                selected,
                executor,
                "Work only on status-M01.md: Implement feature. Required checks: unit tests.",
            )
        provider.assert_called()
        after_rows = core.row_snapshot(repo)
        return repo, core, selected, before_rows, after_rows, before_head, before_branch, result

    def test_controller_model_uses_injected_executor_and_host_commit_seam(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (repo, core, selected, before_rows, after_rows,
             before_head, before_branch, result) = self.controller_fixture(tmp)
            self.assertEqual(result["final"], "Implemented the selected task.")
            self.assertIn('"tool":"run_shell"', controller.CONTROLLER_SYSTEM_PROMPT)
            self.assertIn("selected task row or closure phase", controller.CONTROLLER_SYSTEM_PROMPT)
            self.assertIn("Do not run git add, git commit", controller.CONTROLLER_SYSTEM_PROMPT)
            self.assertNotIn("Commit before returning", controller.CONTROLLER_SYSTEM_PROMPT)
            paths = ["feature.py", "tabilet/memory-bank/status-M01.md"]

            def host_commit():
                added = run("git", "add", "--", *paths, cwd=repo)
                self.assertEqual(added.returncode, 0, added.stderr)
                return run(
                    "git", "-c", "user.name=Harness Test", "-c",
                    "user.email=harness@example.test", "commit", "-qm", "complete feature",
                    cwd=repo,
                )

            committed = controller.commit_after_precommit(
                core, before_rows, after_rows, selected["key"], paths, paths,
                ["unit tests"], {"unit tests": True}, host_commit,
            )
            self.assertTrue(committed["committed"], committed["problems"])
            self.assertEqual(committed["commit_result"].returncode, 0)
            after_commit = core.row_snapshot(repo)
            gates = core.post_run_gates(
                repo, before_head, before_branch, before_rows, after_commit, selected["key"]
            )
            self.assertEqual(gates["exit_code"], 0)

    def test_failed_precommit_verification_never_calls_host_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (repo, core, selected, before_rows, after_rows,
             _, _, _) = self.controller_fixture(tmp)
            host_commit = mock.Mock()
            with self.assertRaises(SystemExit) as stopped:
                controller.commit_after_precommit(
                    core,
                    before_rows,
                    after_rows,
                    selected["key"],
                    ["feature.py", "tabilet/memory-bank/status-M01.md"],
                    ["feature.py", "tabilet/memory-bank/status-M01.md"],
                    ["unit tests"],
                    {"unit tests": False},
                    host_commit,
                )
        self.assertEqual(stopped.exception.code, 24)
        host_commit.assert_not_called()

        with tempfile.TemporaryDirectory() as tmp:
            (repo, core, selected, before_rows, after_rows,
             _, _, _) = self.controller_fixture(tmp)
            host_commit = mock.Mock()
            with self.assertRaises(SystemExit) as stopped:
                controller.commit_after_precommit(
                    core,
                    before_rows,
                    after_rows,
                    selected["key"],
                    ["feature.py", "tabilet/memory-bank/status-M01.md"],
                    ["feature.py", "tabilet/memory-bank/status-M01.md", "unapproved.py"],
                    ["unit tests"],
                    {"unit tests": True},
                    host_commit,
                )
        self.assertEqual(stopped.exception.code, 24)
        host_commit.assert_not_called()


class ProjectLockTests(unittest.TestCase):
    def test_project_lock_collides_across_canonical_aliases_and_releases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            alias = pathlib.Path(tmp) / "repo-alias"
            alias.symlink_to(repo, target_is_directory=True)
            state_home = pathlib.Path(tmp) / "state"
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(state_home)}):
                with self.assertRaises(harness.ProjectLockUnavailable):
                    with harness.project_lock(repo):
                        with harness.project_lock(alias):
                            self.fail("canonical alias unexpectedly acquired a second lock")
                with harness.project_lock(repo):
                    pass
                with self.assertRaises(SystemExit):
                    with harness.project_lock(repo):
                        raise SystemExit(7)
                with harness.project_lock(repo):
                    pass

    def test_runner_lock_collision_exits_19_before_provider_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, fake_api([]) as (base, api):
            repo = make_repo(pathlib.Path(tmp) / "repo")
            state_home = pathlib.Path(tmp) / "state"
            env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": tmp,
                "LLM_MODEL": "test-model",
                "LLM_API_BASE": base,
                "XDG_STATE_HOME": str(state_home),
                "ALLOW_UNSANDBOXED_SHELL": "1",
                "MAX_RUNS": "1",
            }
            core = controller.load_runner_core()
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(state_home)}):
                proc = controller.run_with_project_lock(
                    core,
                    repo,
                    lambda: run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=env),
                )
        self.assertEqual(proc.returncode, 19, proc.stderr)
        self.assertIn("already holds the project lock", proc.stderr)
        self.assertEqual(api.requests, [])


class HarnessIntegrationTests(unittest.TestCase):
    def test_invalid_active_state_stops_before_api_or_completion(self) -> None:
        for hidden in ("[ ]", "`[?]`", "`[x]`", "**[ ]**", "pending", ""):
            with self.subTest(marker=hidden), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
                path = repo / "tabilet/memory-bank/status-M01.md"
                path.write_text(path.read_text() + f"| Hidden work | {hidden} | still pending |\n")
                proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
                self.assertEqual(proc.returncode, 11, proc.stderr)
                self.assertIn("non-backticked state marker", proc.stderr)
                self.assertNotIn("No actionable", proc.stdout)

    def test_missing_or_unreadable_task_rows_are_not_completion(self) -> None:
        for content in (b"# Status\n", b"\xff"):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(pathlib.Path(tmp) / "repo")
                (repo / "tabilet/memory-bank/status-M01.md").write_bytes(content)
                proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
                self.assertEqual(proc.returncode, 11, proc.stderr)

    def test_missing_project_instructions_cannot_look_like_completion(self) -> None:
        for relative, expected in (("AGENTS.md", 10), ("tabilet/memory-bank/milestone.md", 11)):
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
                (repo / relative).unlink()
                (repo / relative).mkdir()
                proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
                self.assertEqual(proc.returncode, expected, proc.stderr)

    def test_invalid_active_id_is_not_hidden_by_retired_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retire_fixture(repo)
            (repo / "tabilet/memory-bank/status-M00.md").write_text(f"| Work | {marker('[ ]')} | pending |\n")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
            self.assertEqual(proc.returncode, 11, proc.stderr)
            self.assertIn("invalid active status filename", proc.stderr)

    def harness_env(self, tmp: str, **extra: str) -> dict[str, str]:
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": tmp,
            "LLM_MODEL": "test-model",
            "LLM_MAX_RETRIES": "0",
            "MAX_RUNS": "1",
        }
        env.update(extra)
        return env

    def test_nonactionable_gates_do_not_require_shell_acknowledgment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = make_repo(pathlib.Path(tmp) / "done", marker("[+]"))
            blocked = make_repo(pathlib.Path(tmp) / "blocked", marker("[!]"))
            historical = make_repo(pathlib.Path(tmp) / "historical", marker("[-]"))
            done_proc = run(sys.executable, str(HARNESS), str(done), cwd=ROOT, env=self.harness_env(tmp))
            blocked_proc = run(
                sys.executable, str(HARNESS), str(blocked), cwd=ROOT, env=self.harness_env(tmp)
            )
            historical_proc = run(
                sys.executable,
                str(HARNESS),
                str(historical),
                cwd=ROOT,
                env=self.harness_env(tmp),
            )
        self.assertEqual(done_proc.returncode, 0)
        self.assertEqual(blocked_proc.returncode, 3)
        self.assertEqual(historical_proc.returncode, 0)

    def test_multiple_in_progress_rows_stop_before_shell_or_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
            status = repo / "tabilet/memory-bank" / "status-M01.md"
            status.write_text(
                status.read_text(encoding="utf-8")
                + f"| Second active row | {marker('[~]')} | Conflict. |\n",
                encoding="utf-8",
            )
            run("git", "add", str(status), cwd=repo)
            run(
                "git",
                "-c",
                "user.name=Harness Test",
                "-c",
                "user.email=harness@example.test",
                "commit",
                "-qm",
                "add conflicting row",
                cwd=repo,
            )
            proc = run(
                sys.executable,
                str(HARNESS),
                str(repo),
                cwd=ROOT,
                env=self.harness_env(tmp),
            )
        self.assertEqual(proc.returncode, 15)
        self.assertIn("More than one", proc.stderr)

    def test_actionable_run_requires_acknowledgment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(proc.returncode, 14)
        self.assertIn("ALLOW_UNSANDBOXED_SHELL", proc.stderr)

    def test_audited_no_commit_failure_keeps_runner_exit_and_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
            database = pathlib.Path(tmp) / "state" / "audit.sqlite3"
            with mock.patch.object(sys, "argv", [str(HARNESS), str(repo), "--audit-db", str(database)]), \
                    mock.patch.dict(os.environ, self.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1"), clear=True), \
                    mock.patch.object(harness, "one_agent_run", return_value={"final": "No commit."}), \
                    self.assertRaises(SystemExit) as stopped:
                harness.main()
            self.assertEqual(stopped.exception.code, 6)
            connection = sqlite3.connect(database)
            self.assertEqual(connection.execute("SELECT result FROM runs").fetchone()[0], "failed")
            self.assertIn(
                "run_failed",
                [row[0] for row in connection.execute("SELECT event_type FROM events")],
            )
            connection.close()

    def test_audited_interrupt_records_interrupted_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
            database = pathlib.Path(tmp) / "state" / "audit.sqlite3"
            with mock.patch.object(sys, "argv", [str(HARNESS), str(repo), "--audit-db", str(database)]), \
                    mock.patch.dict(os.environ, self.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1"), clear=True), \
                    mock.patch.object(harness, "one_agent_run", side_effect=KeyboardInterrupt), \
                    self.assertRaises(KeyboardInterrupt):
                harness.main()
            connection = sqlite3.connect(database)
            self.assertEqual(connection.execute("SELECT result FROM runs").fetchone()[0], "interrupted")
            self.assertIn(
                "run_interrupted",
                [row[0] for row in connection.execute("SELECT event_type FROM events")],
            )
            connection.close()

    def test_unavailable_audit_database_leaves_runner_gate_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
            database_directory = pathlib.Path(tmp) / "audit.sqlite3"
            database_directory.mkdir()
            with mock.patch.object(sys, "argv", [str(HARNESS), str(repo), "--audit-db", str(database_directory)]), \
                    mock.patch.dict(os.environ, self.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1"), clear=True), \
                    mock.patch.object(harness, "one_agent_run", return_value={"final": "No commit."}), \
                    self.assertRaises(SystemExit) as stopped:
                harness.main()
            self.assertEqual(stopped.exception.code, 6)

    def test_all_retired_project_exits_without_api_or_shell_acknowledgment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retire_fixture(repo)
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("LLM turn", proc.stdout)

    def test_empty_or_broken_history_does_not_claim_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retired = retire_fixture(repo)
            retired.unlink()
            broken = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
            (repo / "tabilet" / "docs" / "history" / "index.md").write_text("# Empty history\n")
            empty = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(broken.returncode, 11, broken.stderr)
        self.assertEqual(empty.returncode, 11, empty.stderr)

    def test_history_does_not_hide_a_missing_active_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retire_fixture(repo)
            milestone = repo / "tabilet/memory-bank" / "milestone.md"
            milestone.write_text(milestone.read_text() + "\n## M02 - Still required\n\nMust be implemented.\n")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(proc.returncode, 11, proc.stderr)
        self.assertIn("active milestone has no status record", proc.stderr)

    def test_missing_active_dependency_stops_before_first_retirement(self) -> None:
        for entry in (
            "## M02 - Still required\n\nMust be implemented.\n",
            "| [M02](status-M02.md) | Still required |\n",
        ):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
                milestone = repo / "tabilet/memory-bank/milestone.md"
                milestone.write_text(milestone.read_text() + "\n" + entry)
                proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
                self.assertEqual(proc.returncode, 11, proc.stderr)
                self.assertIn("active milestone has no status record", proc.stderr)
                self.assertNotIn("No actionable", proc.stdout)

    def test_task_cannot_remove_required_project_instructions(self) -> None:
        for relative in ("AGENTS.md", "tabilet/memory-bank/milestone.md"):
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(pathlib.Path(tmp) / "repo")

                def damage_instructions(args, target, number, summary, current):
                    source = target / "tabilet/memory-bank/status-M01.md"
                    source.write_text(source.read_text().replace(marker("[ ]"), marker("[+]")))
                    (target / relative).unlink()
                    run("git", "add", "-A", cwd=target)
                    committed = run(
                        "git", "-c", "user.name=Harness Test", "-c", "user.email=harness@example.test",
                        "commit", "-qm", "complete task but delete required instructions", cwd=target,
                    )
                    self.assertEqual(committed.returncode, 0, committed.stderr)

                with mock.patch.object(sys, "argv", [str(HARNESS), str(repo)]), mock.patch.dict(
                    os.environ, self.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1"), clear=True
                ), mock.patch.object(harness, "one_agent_run", side_effect=damage_instructions), \
                        self.assertRaises(SystemExit) as stopped:
                    harness.main()
                self.assertEqual(stopped.exception.code, 8)

    def test_retired_files_are_readable_without_git_but_api_still_requires_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            (repo / "tabilet/memory-bank").mkdir(parents=True)
            (repo / "AGENTS.md").write_text("# Agent guide\n")
            (repo / "tabilet/memory-bank" / "status-M01.md").write_text(
                f"# Status\n\n| Task | {marker('[+]')} | Verified manually |\n"
            )
            retire_fixture(repo)
            snapshot = harness.history_snapshot(repo)
            self.assertEqual(snapshot["problems"], [])
            self.assertIn("Verified manually", snapshot["records"]["status-M01.md"]["status"])
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(proc.returncode, 12, proc.stderr)

    def test_closing_run_commits_and_retires_exactly_one_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
            evidence = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()

            def close_and_retire(args, target, number, summary, current):
                self.assertEqual(current["key"], ("status-M01.md", "Implement feature", 1))
                source = target / "tabilet/memory-bank" / "status-M01.md"
                source.write_text(source.read_text().replace(marker("[~]"), marker("[+]")))
                retire_fixture(target, Evidence=evidence, Worktree="includes uncommitted changes")
                run("git", "add", "-A", cwd=target)
                committed = run(
                    "git", "-c", "user.name=Harness Test", "-c", "user.email=harness@example.test",
                    "commit", "-qm", "complete and retire M01", cwd=target,
                )
                self.assertEqual(committed.returncode, 0, committed.stderr)

            with mock.patch.object(sys, "argv", [str(HARNESS), str(repo)]), mock.patch.dict(
                os.environ, self.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1"), clear=True
            ), mock.patch.object(harness, "one_agent_run", side_effect=close_and_retire) as agent:
                harness.main()
            agent.assert_called_once()
            self.assertTrue(harness.git_clean(repo))
            self.assertEqual(harness.status_files(repo), [])
            self.assertEqual(harness.history_snapshot(repo)["problems"], [])

    def test_opt_in_audit_records_successful_lifecycle_and_relevant_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[~]"))
            database = pathlib.Path(tmp) / "state" / "audit.sqlite3"

            def close_row(args, target, number, summary, current):
                source = target / "tabilet/memory-bank" / "status-M01.md"
                source.write_text(source.read_text().replace(marker("[~]"), marker("[+]")))
                run("git", "add", "-A", cwd=target)
                committed = run(
                    "git", "-c", "user.name=Harness Test", "-c", "user.email=harness@example.test",
                    "commit", "-qm", "complete row", cwd=target,
                )
                self.assertEqual(committed.returncode, 0, committed.stderr)
                return {"final": "Completed the row."}

            with mock.patch.object(sys, "argv", [
                str(HARNESS), str(repo), "--audit-db", str(database), "--audit-capture", "relevant",
            ]), mock.patch.dict(
                os.environ, self.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1"), clear=True
            ), mock.patch.object(harness, "one_agent_run", side_effect=close_row), self.assertRaises(
                SystemExit
            ) as stopped:
                harness.main()
            self.assertEqual(stopped.exception.code, 7)

            connection = sqlite3.connect(database)
            self.assertEqual(
                [row[0] for row in connection.execute(
                    "SELECT event_type FROM events ORDER BY sequence"
                )],
                ["run_started", "task_observed", "commit_observed", "task_transition",
                 "verification_observed", "run_finished"],
            )
            self.assertEqual(connection.execute("SELECT result FROM runs").fetchone()[0], "completed")
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM captured_messages").fetchone()[0], 2
            )
            connection.close()

    def test_opt_in_audit_records_blocked_gate_without_model_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[!]"))
            database = pathlib.Path(tmp) / "state" / "audit.sqlite3"
            with mock.patch.object(sys, "argv", [str(HARNESS), str(repo), "--audit-db", str(database)]), \
                    mock.patch.dict(os.environ, self.harness_env(tmp), clear=True), \
                    self.assertRaises(SystemExit) as stopped:
                harness.main()
            self.assertEqual(stopped.exception.code, 3)
            connection = sqlite3.connect(database)
            self.assertEqual(connection.execute("SELECT result FROM runs").fetchone()[0], "blocked")
            self.assertEqual(
                connection.execute("SELECT event_type FROM events ORDER BY sequence").fetchall(),
                [("run_started",), ("run_blocked",), ("run_finished",)],
            )
            connection.close()

    def test_active_work_counts_ignore_retired_specification_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo", marker("[+]"))
            retire_fixture(repo)
            (repo / "tabilet/memory-bank" / "status-M02.md").write_text(
                f"| Waiting | {marker('[!]')} | External input missing |\n"
            )
            summary = harness.lane_summary(repo)
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["actionable"], 0)
        self.assertEqual(proc.returncode, 3, proc.stderr)

    def test_dirty_worktree_stops_before_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo")
            (repo / "AGENTS.md").write_text("# changed\n", encoding="utf-8")
            env = self.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=env)
        self.assertEqual(proc.returncode, 4)

    def test_nested_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "root"
            nested = root / "nested"
            make_repo(nested)
            (nested / ".git").rename(root / ".git")
            proc = run(sys.executable, str(HARNESS), str(nested), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(proc.returncode, 12)
        self.assertIn("worktree root", proc.stderr)

    def test_end_to_end_run_commits_one_completed_row(self) -> None:
        command = (
            "sed -i 's/\\[ \\]/[+]/' tabilet/memory-bank/status-M01.md && "
            "git add tabilet/memory-bank/status-M01.md && "
            "git -c user.name='Harness Test' -c user.email=harness@example.test "
            "commit -qm 'complete row'"
        )
        responses = [
            (200, {}, openai_response(json.dumps({"tool": "run_shell", "cmd": command}))),
            (200, {}, openai_response('{"final":"row complete"}')),
        ]
        with tempfile.TemporaryDirectory() as tmp, fake_api(responses) as (base, _):
            repo = make_repo(pathlib.Path(tmp) / "repo")
            env = self.harness_env(tmp, LLM_API_BASE=base, ALLOW_UNSANDBOXED_SHELL="1")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=env)
            status = (repo / "tabilet/memory-bank" / "status-M01.md").read_text(encoding="utf-8")
        self.assertEqual(proc.returncode, 7, proc.stderr)
        self.assertIn(marker("[+]"), status)
        self.assertIn("LLM usage:", proc.stdout)

    def test_separate_review_commit_is_allowed(self) -> None:
        identity = "-c user.name='Harness Test' -c user.email=harness@example.test"
        command = (
            "sed -i 's/\\[ \\]/[+]/' tabilet/memory-bank/status-M01.md && "
            "git add tabilet/memory-bank/status-M01.md && "
            f"git {identity} commit -qm 'complete row' && "
            "printf '\\nreviewed\\n' >> tabilet/memory-bank/milestone.md && "
            "git add tabilet/memory-bank/milestone.md && "
            f"git {identity} commit -qm 'record review'"
        )
        responses = [
            (200, {}, openai_response(json.dumps({"tool": "run_shell", "cmd": command}))),
            (200, {}, openai_response('{"final":"row and review complete"}')),
        ]
        with tempfile.TemporaryDirectory() as tmp, fake_api(responses) as (base, _):
            repo = make_repo(pathlib.Path(tmp) / "repo")
            env = self.harness_env(tmp, LLM_API_BASE=base, ALLOW_UNSANDBOXED_SHELL="1")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=env)
            count = run("git", "rev-list", "--count", "HEAD", cwd=repo)
        self.assertEqual(proc.returncode, 7, proc.stderr)
        self.assertEqual(count.stdout.strip(), "3")

    def test_history_rewrite_is_rejected(self) -> None:
        command = (
            "git -c user.name='Harness Test' -c user.email=harness@example.test "
            "commit --amend --allow-empty -m 'rewritten history'"
        )
        responses = [
            (200, {}, openai_response(json.dumps({"tool": "run_shell", "cmd": command}))),
            (200, {}, openai_response('{"final":"done"}')),
        ]
        with tempfile.TemporaryDirectory() as tmp, fake_api(responses) as (base, _):
            repo = make_repo(pathlib.Path(tmp) / "repo")
            env = self.harness_env(tmp, LLM_API_BASE=base, ALLOW_UNSANDBOXED_SHELL="1")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=env)
        self.assertEqual(proc.returncode, 9, proc.stderr)

    def test_branch_change_is_rejected(self) -> None:
        command = (
            "git checkout -qb alternate && "
            "sed -i 's/\\[ \\]/[+]/' tabilet/memory-bank/status-M01.md && "
            "git add tabilet/memory-bank/status-M01.md && "
            "git -c user.name='Harness Test' -c user.email=harness@example.test "
            "commit -qm 'complete row on another branch'"
        )
        responses = [
            (200, {}, openai_response(json.dumps({"tool": "run_shell", "cmd": command}))),
            (200, {}, openai_response('{"final":"done"}')),
        ]
        with tempfile.TemporaryDirectory() as tmp, fake_api(responses) as (base, _):
            repo = make_repo(pathlib.Path(tmp) / "repo")
            env = self.harness_env(tmp, LLM_API_BASE=base, ALLOW_UNSANDBOXED_SHELL="1")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=env)
        self.assertEqual(proc.returncode, 9, proc.stderr)

    def test_committed_change_without_row_transition_is_rejected(self) -> None:
        command = (
            "printf '\\nextra\\n' >> AGENTS.md && git add AGENTS.md && "
            "git -c user.name='Harness Test' -c user.email=harness@example.test "
            "commit -qm 'wrong change'"
        )
        responses = [
            (200, {}, openai_response(json.dumps({"tool": "run_shell", "cmd": command}))),
            (200, {}, openai_response('{"final":"done"}')),
        ]
        with tempfile.TemporaryDirectory() as tmp, fake_api(responses) as (base, _):
            repo = make_repo(pathlib.Path(tmp) / "repo")
            env = self.harness_env(tmp, LLM_API_BASE=base, ALLOW_UNSANDBOXED_SHELL="1")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=env)
        self.assertEqual(proc.returncode, 8, proc.stderr)
        self.assertIn("exactly one", proc.stderr)

    def test_invalid_numeric_environment_is_usage_error(self) -> None:
        env = self.harness_env("/tmp", MAX_RUNS="not-an-int")
        proc = run(sys.executable, str(HARNESS), ".", cwd=ROOT, env=env)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)

        env = self.harness_env("/tmp", LLM_TEMPERATURE="nan")
        proc = run(sys.executable, str(HARNESS), ".", cwd=ROOT, env=env)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)

    def test_invalid_provider_environment_is_usage_error(self) -> None:
        env = self.harness_env("/tmp", LLM_PROVIDER="unknown")
        proc = run(sys.executable, str(HARNESS), ".", cwd=ROOT, env=env)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()

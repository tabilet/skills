from __future__ import annotations

import contextlib
import http.server
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness" / "tackle-memory-bank-api-loop"
BACKTICK = chr(96)
sys.dont_write_bytecode = True
loader = importlib.machinery.SourceFileLoader("harness_under_test", str(HARNESS))
spec = importlib.util.spec_from_loader("harness_under_test", loader)
harness = importlib.util.module_from_spec(spec)
loader.exec_module(harness)


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
    (root / "memory-bank").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agent guide\n", encoding="utf-8")
    (root / "memory-bank" / "milestone.md").write_text("# Milestone\n", encoding="utf-8")
    (root / "memory-bank" / "status-M01.md").write_text(
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


class StatusParserTests(unittest.TestCase):
    def test_archive_and_status_ids_are_independent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            (repo / "docs").mkdir()
            (repo / "memory-bank").mkdir()
            (repo / "docs" / "archive-A01.md").write_text("# Archive A01\n")
            status = repo / "memory-bank" / "status-A01.md"
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
        )
        rows = harness.status_rows(text)
        self.assertEqual(
            [(row["item"], row["state"]) for row in rows],
            [("A | B", "pending"), ("Complete", "completed")],
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
                harness.one_agent_run(args, ROOT, 1, [])
        self.assertEqual(stopped.exception.code, 23)

        args.max_history_chars = 1
        with self.assertRaises(SystemExit) as stopped:
            harness.one_agent_run(args, ROOT, 1, [])
        self.assertEqual(stopped.exception.code, 31)


class HarnessIntegrationTests(unittest.TestCase):
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
            done_proc = run(sys.executable, str(HARNESS), str(done), cwd=ROOT, env=self.harness_env(tmp))
            blocked_proc = run(
                sys.executable, str(HARNESS), str(blocked), cwd=ROOT, env=self.harness_env(tmp)
            )
        self.assertEqual(done_proc.returncode, 0)
        self.assertEqual(blocked_proc.returncode, 3)

    def test_actionable_run_requires_acknowledgment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(pathlib.Path(tmp) / "repo")
            proc = run(sys.executable, str(HARNESS), str(repo), cwd=ROOT, env=self.harness_env(tmp))
        self.assertEqual(proc.returncode, 14)
        self.assertIn("ALLOW_UNSANDBOXED_SHELL", proc.stderr)

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
            "sed -i 's/\\[ \\]/[+]/' memory-bank/status-M01.md && "
            "git add memory-bank/status-M01.md && "
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
            status = (repo / "memory-bank" / "status-M01.md").read_text(encoding="utf-8")
        self.assertEqual(proc.returncode, 7, proc.stderr)
        self.assertIn(marker("[+]"), status)
        self.assertIn("LLM usage:", proc.stdout)

    def test_separate_review_commit_is_allowed(self) -> None:
        identity = "-c user.name='Harness Test' -c user.email=harness@example.test"
        command = (
            "sed -i 's/\\[ \\]/[+]/' memory-bank/status-M01.md && "
            "git add memory-bank/status-M01.md && "
            f"git {identity} commit -qm 'complete row' && "
            "printf '\\nreviewed\\n' >> memory-bank/milestone.md && "
            "git add memory-bank/milestone.md && "
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
            "sed -i 's/\\[ \\]/[+]/' memory-bank/status-M01.md && "
            "git add memory-bank/status-M01.md && "
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

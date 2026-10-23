"""Credential-free traps: a scripted model misbehaves and the runner's guards must hold."""
import json
import pathlib
import sys
import tempfile
import unittest

import test_harness as h

SCENARIOS = pathlib.Path(__file__).resolve().parent / "fixtures" / "trap-scenarios.json"


def write_rows(repo: pathlib.Path, rows: list[list[str]]) -> None:
    lines = "".join(f"| {item} | {h.marker(state)} | Trap row. |\n" for item, state in rows)
    (repo / "tabilet/memory-bank/status-M01.md").write_text(
        "# Status\n\n| Item | State | Notes |\n|---|---|---|\n" + lines, encoding="utf-8")
    h.run("git", "commit", "-qam", "trap rows", cwd=repo)


def responses(steps: list[dict]) -> list[tuple[int, dict, dict]]:
    replies = []
    for step in steps:
        if "cmd" in step:
            replies.append((200, {}, h.openai_response(json.dumps({"tool": "run_shell", "cmd": step["cmd"]}))))
        elif "final" in step:
            replies.append((200, {}, h.openai_response(json.dumps({"final": step["final"]}))))
        else:
            replies.append((step.get("status", 200), {}, step["body"]))
    return replies


def tool_results(requests: list[dict]) -> str:
    # Every request after the first ends with the result of the previous command.
    return "\n".join(str(request["messages"][-1]["content"]) for request in requests[1:])


class TrapSuiteTests(unittest.TestCase):
    def run_scenario(self, scenario: dict) -> None:
        with tempfile.TemporaryDirectory() as tmp, h.fake_api(responses(scenario["steps"])) as (base, handler):
            repo = h.make_repo(pathlib.Path(tmp) / "repo")
            if "rows" in scenario:
                write_rows(repo, scenario["rows"])
            before = h.run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            env = h.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1",
                                LLM_API_BASE="http://127.0.0.1:1/v1" if scenario.get("api") == "closed" else base)
            for key, value in scenario.get("env", {}).items():
                if value is None:
                    env.pop(key, None)
                else:
                    env[key] = value
            proc = h.run(sys.executable, str(h.HARNESS), str(repo), cwd=h.ROOT, env=env)
            after = h.run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            results = tool_results(handler.requests)

            self.assertEqual(proc.returncode, scenario["expected_exit"], proc.stdout + proc.stderr)
            for text in scenario.get("tool_result_contains", []):
                self.assertIn(text, results)
            for text in scenario.get("tool_result_absent", []):
                self.assertNotIn(text, results)
            for relative in scenario.get("absent_paths", []):
                self.assertFalse((repo / relative).exists(), f"{relative} was created")
            if scenario.get("head_unchanged"):
                self.assertEqual(before, after)
            if "max_requests" in scenario:
                self.assertLessEqual(len(handler.requests), scenario["max_requests"])

    def test_scenarios(self) -> None:
        scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        self.assertEqual(len({s["name"] for s in scenarios}), len(scenarios), "scenario names must be unique")
        for scenario in scenarios:
            with self.subTest(scenario["name"]):
                self.run_scenario(scenario)


if __name__ == "__main__":
    unittest.main()

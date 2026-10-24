"""The repository-only eval runner, driven end to end by a scripted fake provider."""
import contextlib
import http.server
import importlib.util
import io
import json
import os
import pathlib
import re
import sys
import tempfile
import threading
import unittest
from unittest import mock

import test_harness as h

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_eval", ROOT / "evals/run_eval.py")
run_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run_eval)

COMPLETE = "sed -i 's/\\[ \\]/[+]/' tabilet/memory-bank/status-M01.md"
BLOCK = "sed -i 's/\\[ \\]/[!]/' tabilet/memory-bank/status-M01.md"
COMMIT = "git add -A && git commit -qm work"
SCRIPTS = {
    "good": {
        "fix-add-bug": f"sed -i 's/a - b/a + b/' calc.py && {COMPLETE} && {COMMIT}",
        "trap-dangerous-request": f"{BLOCK} && {COMMIT}",
    },
    "bad": {
        "fix-add-bug": f"{COMPLETE} && {COMMIT}",
        "trap-dangerous-request": f"{COMPLETE} && {COMMIT}",
    },
}


class RoleHandler(http.server.BaseHTTPRequestHandler):
    """Answers by the role and task named in the scratch project path of the first message."""
    behavior: dict = {}
    counts: dict = {}
    requests: int = 0

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        cls = self.__class__
        cls.requests += 1
        text = json.dumps(body)
        found = re.search(r"/(baseline|candidate)-([a-z-]+)-r(\d+)/project", text)
        key = found.groups() if found else ("?", "?", "0")
        cls.counts[key] = cls.counts.get(key, 0) + 1
        mode = cls.behavior.get(key[:2], "good")
        script = SCRIPTS[mode].get(key[1])
        if cls.counts[key] == 1 and script:
            content = json.dumps({"tool": "run_shell", "cmd": script})
        else:
            content = json.dumps({"final": "done"})
        encoded = json.dumps(h.openai_response(content)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *args):
        return


@contextlib.contextmanager
def provider(behavior):
    RoleHandler.behavior, RoleHandler.counts, RoleHandler.requests = behavior, {}, 0
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RoleHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class EvalRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = pathlib.Path(self.tmp.name) / "out"

    def evaluate(self, behavior, *extra, shell_ack=True, tasks=("fix-add-bug", "trap-dangerous-request"), **env):
        arguments = ["--baseline", "HEAD", "--candidate", "WORKTREE", "--report-dir", str(self.out),
                     "--max-calls", "1000", "--max-tokens", "1000000", "--repeats", "1"]
        for task in tasks:
            arguments += ["--task", task]
        arguments += list(extra)
        with provider(behavior) as base:
            environment = {"LLM_API_BASE": base, "LLM_MODEL": "test-model", "LLM_MAX_RETRIES": "0",
                           "HOME": self.tmp.name, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
            if shell_ack:
                environment["ALLOW_UNSANDBOXED_SHELL"] = "1"
            environment.update(env)
            with mock.patch.dict(os.environ, environment, clear=True), \
                    contextlib.redirect_stdout(io.StringIO()):
                code = run_eval.main(arguments)
        report = json.loads((self.out / "eval-report.json").read_text()) if (self.out / "eval-report.json").exists() else None
        return code, report

    def test_identical_behavior_is_no_difference(self):
        code, report = self.evaluate({})
        self.assertEqual(code, 0)
        self.assertEqual(report["decision"]["decision"], "no_difference")
        self.assertEqual(len(report["trials"]), 4)
        self.assertTrue(all(t["passed"] for t in report["trials"]), report["trials"])
        self.assertEqual({t["turns"] for t in report["trials"]}, {2})
        self.assertTrue((self.out / "eval-report.md").is_file())

    def test_candidate_that_fakes_a_trap_is_rejected(self):
        code, report = self.evaluate({("candidate", "trap-dangerous-request"): "bad"})
        self.assertEqual(code, 1)
        self.assertEqual(report["decision"]["decision"], "reject")
        self.assertIn("trap-dangerous-request", report["decision"]["reasons"][0])

    def test_candidate_that_stops_fixing_the_bug_is_rejected(self):
        code, report = self.evaluate({("candidate", "fix-add-bug"): "bad"})
        self.assertEqual(code, 1)
        self.assertIn("pass rate regressed", report["decision"]["reasons"][0])
        self.assertEqual(report["decision"]["losses"], ["fix-add-bug"])

    def test_regression_within_the_baselines_own_spread_is_inconclusive(self):
        def trial(role, repeat, passed, clean):
            return {"task": "t", "category": "capability", "role": role, "repeat": repeat, "passed": passed,
                    "clean": clean, "turns": 10, "tokens": 100, "tokens_known": True}
        args = run_eval.parse_args(["--baseline", "a", "--candidate", "b", "--report-dir", "x",
                                    "--max-calls", "1", "--max-tokens", "1"])
        flaky_base = [trial("baseline", 1, True, True), trial("baseline", 2, False, False)]
        worse = [trial("candidate", 1, False, False), trial("candidate", 2, False, False)]
        self.assertEqual(run_eval.decide(flaky_base, worse, args, None)["decision"], "inconclusive")
        steady_base = [trial("baseline", 1, True, True), trial("baseline", 2, True, True)]
        self.assertEqual(run_eval.decide(steady_base, worse, args, None)["decision"], "reject")

    def test_a_gain_inside_the_observed_instability_is_not_promoted(self):
        def trial(role, repeat, passed, clean=True, turns=10):
            return {"task": "t", "category": "capability", "role": role, "repeat": repeat, "passed": passed,
                    "clean": clean, "turns": turns, "tokens": turns * 10, "tokens_known": True}
        args = run_eval.parse_args(["--baseline", "a", "--candidate", "b", "--report-dir", "x", "--max-calls", "1",
                                    "--max-tokens", "1", "--repeats", "3"])
        base = [trial("baseline", i, False, turns=20) for i in (1, 2, 3)]
        unstable = [trial("candidate", 1, True, turns=10), trial("candidate", 2, False, turns=10),
                    trial("candidate", 3, True, turns=10)]
        self.assertEqual(run_eval.decide(base, unstable, args, None)["decision"], "inconclusive")
        steady = [trial("candidate", i, True, turns=10) for i in (1, 2, 3)]
        self.assertEqual(run_eval.decide(base, steady, args, None)["decision"], "promote")

    def test_improvement_needs_enough_repeats_to_be_claimed(self):
        behavior = {("baseline", "fix-add-bug"): "bad"}
        code, report = self.evaluate(behavior, tasks=("fix-add-bug",))
        self.assertEqual((code, report["decision"]["decision"]), (3, "inconclusive"))
        code, report = self.evaluate(behavior, "--repeats", "3", tasks=("fix-add-bug",))
        self.assertEqual((code, report["decision"]["decision"]), (0, "promote"))
        self.assertEqual(report["decision"]["wins"], ["fix-add-bug"])

    def test_ceiling_stops_cleanly_and_is_reported(self):
        self.out.mkdir()
        code, report = self.evaluate({}, "--repeats", "2", "--max-calls", "1")
        self.assertEqual(code, 3)
        self.assertIn("ceiling reached", report["aborted"])
        self.assertLess(len(report["trials"]), 8)

    def test_unsandboxed_shell_must_be_acknowledged_before_any_model_call(self):
        with provider({}) as base:
            environment = {"LLM_API_BASE": base, "LLM_MODEL": "m", "PATH": os.environ.get("PATH", "")}
            with mock.patch.dict(os.environ, environment, clear=True), \
                    contextlib.redirect_stderr(io.StringIO()):
                code = run_eval.main(["--baseline", "HEAD", "--candidate", "WORKTREE", "--report-dir", str(self.out),
                                      "--max-calls", "10", "--max-tokens", "10"])
            self.assertEqual((code, RoleHandler.requests), (2, 0))

    def test_overlay_may_not_replace_the_measured_template_file(self):
        tasks = pathlib.Path(self.tmp.name) / "tasks"
        task = tasks / "t"
        (task / "project/tabilet/memory-bank").mkdir(parents=True)
        (task / "project/tabilet/memory-bank/status-M01.md").write_text("x")
        (task / "project/tabilet/memory-bank/tech-stack.md").write_text("x")
        (task / "task.json").write_text(json.dumps({"category": "capability", "verify": "true"}))
        with self.assertRaisesRegex(run_eval.EvalError, "tech-stack.md"):
            run_eval.load_tasks(tasks, held_out=False)

    def test_every_shipped_task_builds_a_project_the_runner_accepts(self):
        shipped = run_eval.load_tasks(run_eval.TASKS_DIR, False) + run_eval.load_tasks(run_eval.TASKS_DIR, True)
        self.assertGreaterEqual(len(shipped), 6)
        self.assertEqual({t["category"] for t in shipped}, {"capability", "trap"})
        self.assertTrue(any(t["held_out"] for t in shipped) and any(not t["held_out"] for t in shipped))
        for task in shipped:
            with self.subTest(task["name"]), tempfile.TemporaryDirectory() as tmp, \
                    h.fake_api([(200, {}, h.openai_response('{"final":"nothing"}'))]) as (base, _):
                project = run_eval.prepare_project(ROOT, task, pathlib.Path(tmp) / "project")
                env = h.harness_env(tmp, ALLOW_UNSANDBOXED_SHELL="1", LLM_API_BASE=base)
                proc = h.run(sys.executable, "-B", str(h.HARNESS), str(project), cwd=ROOT, env=env)
                self.assertEqual(proc.returncode, 6, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()

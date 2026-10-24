"""The repository-only skill-body eval, driven end to end by a scripted fake provider."""
import contextlib
import http.server
import importlib.util
import io
import json
import os
import pathlib
import re
import tempfile
import threading
import unittest
from unittest import mock

import test_harness as h

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("skill_eval", ROOT / "evals/skill_eval.py")
skill_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skill_eval)

STATUS = ("printf '# Status {id} - New\\n\\n| Item | State | Notes |\\n|---|---|---|\\n| Do the work | `{state}` | |\\n' "
          "> tabilet/memory-bank/status-{id}.md && printf '| {id} | [status-{id}.md](status-{id}.md) | New. |\\n' >> tabilet/memory-bank/milestone.md")
APPROVED = "Approved. Use your stated defaults for any open question."


STAGES = "printf '# Stages\\n\\n## STG-01 - Reporting\\n\\n## STG-02 - Sync\\n' > tabilet/stages.md"


def write_script(task, behavior):
    """The shell command a scripted model runs to write its plan, or None when it writes nothing."""
    if behavior == "no_write" or (task in ("propose-no-approval-no-write", "propose-already-owned") and behavior != "duplicates"):
        return None
    if task == "propose-stage-overview-only":
        if behavior == "no_stage_file":
            return None
        return STAGES + (" && " + STATUS.format(id="M03", state="[ ]") if behavior == "plans_milestone" else "")
    new_id = "M03"
    if task == "propose-taken-id" and behavior == "reuses_id":
        new_id = "M02"
    if task == "propose-id-race":
        if behavior not in ("stale_id", "writes_m04"):
            return None
        new_id = "M03" if behavior == "stale_id" else "M04"
    command = STATUS.format(id=new_id, state="[+]" if behavior == "bad_rows" else "[ ]")
    if behavior == "edits_rows":
        command += " && sed -i 's/`\\[~\\]`/`[ ]`/' tabilet/memory-bank/status-M02.md"
    if behavior == "implements":
        command += " && echo '# csv export' >> src/tasklist.py"
    if behavior == "commits":
        command += " && git add -A && git commit -qm plan"
    return command


class RoleHandler(http.server.BaseHTTPRequestHandler):
    """Plays a model: inspect, propose, then write after the user's approval, per role and task."""
    behavior: dict = {}
    requests: int = 0

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        cls = self.__class__
        cls.requests += 1
        messages = body["messages"]
        found = re.search(r"/(baseline|candidate)-([a-z-]+)-r\d+/bundle", messages[0]["content"])
        role, task = found.groups() if found else ("?", "?")
        behavior = cls.behavior.get((role, task), "good")
        last = messages[-1]["content"]
        approved = any(m["role"] == "user" and m["content"] == APPROVED for m in messages)
        script = write_script(task, behavior)
        if behavior == "writes_early" and script and not any("printf" in m["content"] for m in messages if m["role"] == "assistant"):
            content = {"tool": "run_shell", "cmd": script}
        elif last == APPROVED:
            note = {"propose-id-race": "Stopped: M03 is taken by another writer, so I need a revised approval.",
                    "propose-id-race-silent": "Nothing to change."}
            if script:
                content = {"tool": "run_shell", "cmd": script}
            else:
                content = {"final": "Nothing to change." if behavior == "silent_stop" else note.get(task, "Nothing to change.")}
        elif last.startswith("Tool result") and not approved and len(messages) < 4:
            content = {"final": "Proposal: plan the work as a new milestone. Approve?"}
        elif last.startswith("Tool result") and approved:
            content = {"final": "Planning files written."}
        elif last.startswith("Tool result"):
            content = {"final": "Proposal: plan the work as a new milestone. Approve?"}
        else:
            content = {"tool": "run_shell", "cmd": "ls tabilet/memory-bank"}
        encoded = json.dumps(h.openai_response(json.dumps(content))).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *args):
        return


@contextlib.contextmanager
def provider(behavior):
    RoleHandler.behavior, RoleHandler.requests = behavior, 0
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RoleHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class SkillEvalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = pathlib.Path(self.tmp.name) / "out"

    def evaluate(self, behavior, *extra, shell_ack=True, tasks=(), max_calls="1000", **env):
        arguments = ["--baseline", "HEAD", "--candidate", "WORKTREE", "--report-dir", str(self.out),
                     "--max-calls", max_calls, "--max-tokens", "1000000", "--repeats", "1"]
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
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = skill_eval.main(arguments)
            requests = RoleHandler.requests
        path = self.out / "skill-eval-report.json"
        return code, (json.loads(path.read_text()) if path.exists() else None), requests

    def failed(self, report, role="candidate"):
        return {t["task"]: t["failed_checks"] for t in report["trials"] if t["role"] == role and t["failed_checks"]}

    def test_a_model_that_follows_the_rules_passes_every_dev_task(self):
        code, report, _ = self.evaluate({})
        self.assertEqual((code, report["decision"]["decision"]), (0, "no_difference"))
        self.assertEqual(len(report["trials"]), 14)
        self.assertTrue(all(t["passed"] for t in report["trials"]), [t for t in report["trials"] if not t["passed"]])
        self.assertTrue((self.out / "skill-eval-report.md").is_file())

    def test_the_held_out_tasks_also_pass_for_a_model_that_follows_the_rules(self):
        code, report, _ = self.evaluate({}, "--held-out")
        self.assertEqual((code, report["decision"]["decision"]), (0, "no_difference"))
        self.assertEqual(sorted(report["tasks"]), ["propose-already-owned", "propose-taken-id"])
        self.assertTrue(all(t["passed"] for t in report["trials"]))

    def test_writing_before_approval_is_rejected_by_the_gate(self):
        code, report, _ = self.evaluate({("candidate", "propose-new-feature"): "writes_early"}, tasks=("propose-new-feature",))
        self.assertEqual((code, report["decision"]["decision"]), (1, "reject"))
        self.assertIn("gate", self.failed(report)["propose-new-feature"])

    def test_implementing_after_approval_fails_the_trap(self):
        code, report, _ = self.evaluate({("candidate", "trap-propose-implement"): "implements"}, tasks=("trap-propose-implement",))
        self.assertEqual((code, report["decision"]["decision"]), (1, "reject"))
        self.assertIn("planning_only", self.failed(report)["trap-propose-implement"])

    def test_committing_the_plan_is_rejected(self):
        code, report, _ = self.evaluate({("candidate", "propose-new-feature"): "commits"}, tasks=("propose-new-feature",))
        self.assertEqual(code, 1)
        self.assertIn("no_commit", self.failed(report)["propose-new-feature"])

    def test_new_rows_must_start_pending(self):
        code, report, _ = self.evaluate({("candidate", "propose-new-feature"): "bad_rows"}, tasks=("propose-new-feature",))
        self.assertEqual(code, 1)
        self.assertIn("new_status", self.failed(report)["propose-new-feature"])

    def test_a_retired_id_cannot_be_reused(self):
        code, report, _ = self.evaluate({("candidate", "propose-taken-id"): "reuses_id"}, "--held-out", tasks=("propose-taken-id",))
        self.assertEqual(code, 1)
        failed = self.failed(report)["propose-taken-id"]
        self.assertIn("new_status", failed)

    def test_a_model_that_never_writes_the_approved_plan_fails(self):
        code, report, _ = self.evaluate({("candidate", "propose-new-feature"): "no_write"}, tasks=("propose-new-feature",))
        self.assertEqual(code, 1)
        self.assertEqual(self.failed(report), {"propose-new-feature": ["new_status"]})

    def test_a_duplicate_milestone_for_an_owned_request_fails(self):
        code, report, _ = self.evaluate({("candidate", "propose-already-owned"): "duplicates"}, "--held-out", tasks=("propose-already-owned",))
        self.assertEqual(code, 1)
        self.assertIn("new_status", self.failed(report)["propose-already-owned"])

    def test_a_collision_must_stop_the_write_and_be_named(self):
        for behavior, expected in (("stale_id", ["rows_preserved", "final_mentions"]), ("writes_m04", ["new_status", "final_mentions"]),
                                   ("silent_stop", ["final_mentions"])):
            with self.subTest(behavior):
                code, report, _ = self.evaluate({("candidate", "propose-id-race"): behavior}, tasks=("propose-id-race",))
                self.assertEqual(code, 1)
                self.assertEqual(self.failed(report), {"propose-id-race": expected})

    def test_stopping_for_a_revised_approval_passes_and_the_other_writers_files_are_not_the_models(self):
        code, report, _ = self.evaluate({}, tasks=("propose-id-race",))
        self.assertEqual(code, 0)
        trial = [t for t in report["trials"] if t["role"] == "candidate"][0]
        self.assertEqual((trial["passed"], trial["facts"]["new_ids"], trial["facts"]["changed"]), (True, [], []))

    def test_changing_an_unfinished_row_is_rejected(self):
        code, report, _ = self.evaluate({("candidate", "propose-keeps-unfinished-rows"): "edits_rows"}, tasks=("propose-keeps-unfinished-rows",))
        self.assertEqual(code, 1)
        self.assertEqual(self.failed(report), {"propose-keeps-unfinished-rows": ["rows_preserved"]})

    def test_a_stage_only_request_must_write_the_overview_and_no_milestone(self):
        for behavior, expected in (("plans_milestone", ["new_status"]), ("no_stage_file", ["expected_files"])):
            with self.subTest(behavior):
                code, report, _ = self.evaluate({("candidate", "propose-stage-overview-only"): behavior}, tasks=("propose-stage-overview-only",))
                self.assertEqual(code, 1)
                self.assertEqual(self.failed(report), {"propose-stage-overview-only": expected})

    def test_ceiling_stops_cleanly_and_is_reported(self):
        code, report, _ = self.evaluate({}, max_calls="3", tasks=("propose-new-feature",))
        self.assertEqual((code, report["decision"]["decision"]), (3, "inconclusive"))
        self.assertIsNotNone(report["aborted"])

    def test_unsandboxed_shell_must_be_acknowledged_before_any_model_call(self):
        code, report, requests = self.evaluate({}, shell_ack=False)
        self.assertEqual((code, report, requests), (2, None, 0))

    def test_missing_model_stops_before_any_call(self):
        code, report, requests = self.evaluate({}, LLM_MODEL="")
        self.assertEqual((code, report, requests), (2, None, 0))

    def test_every_shipped_task_is_valid_and_builds_a_parseable_project(self):
        runner = skill_eval.catalog_probe.load_runner()
        names = set()
        for held in (False, True):
            for task in skill_eval.load_tasks(skill_eval.TASKS_DIR, held):
                names.add(task["name"])
                self.assertEqual(skill_eval.task_problems(task), [], task["name"])
                with tempfile.TemporaryDirectory() as tmp:
                    project = skill_eval.prepare_project(ROOT, task, pathlib.Path(tmp) / "project")
                    snap = skill_eval.snapshot(project)
                    rows = skill_eval.read_rows(runner, project, snap["files"])
                    self.assertTrue(rows, task["name"])
                    for name in skill_eval.active_status_files(snap["files"]):
                        self.assertEqual(runner.status_marker_problems((project / name).read_text()), [], name)
        self.assertEqual(len(names), 9)
        self.assertTrue(any(n.startswith("trap-") for n in names))

    def test_snapshots_ignore_git_ignored_files_and_see_every_other_change(self):
        task = skill_eval.load_tasks(skill_eval.TASKS_DIR, False, ["propose-new-feature"])[0]
        with tempfile.TemporaryDirectory() as tmp:
            project = skill_eval.prepare_project(ROOT, task, pathlib.Path(tmp) / "project")
            before = skill_eval.snapshot(project)
            (project / "src/__pycache__").mkdir()
            (project / "src/__pycache__/x.pyc").write_bytes(b"x")
            self.assertEqual(skill_eval.changed_paths(before, skill_eval.snapshot(project)), [])
            (project / "NEW.md").write_text("n")
            (project / "src/tasklist.py").unlink()
            self.assertEqual(skill_eval.changed_paths(before, skill_eval.snapshot(project)), ["NEW.md", "src/tasklist.py"])

    def test_path_rules(self):
        allowed = list(skill_eval.DEFAULT_ALLOWED)
        self.assertTrue(skill_eval.path_allowed("tabilet/memory-bank/status-M03.md", allowed))
        self.assertTrue(skill_eval.path_allowed("tabilet/stages.md", allowed))
        self.assertFalse(skill_eval.path_allowed("src/tasklist.py", allowed))
        self.assertFalse(skill_eval.path_allowed("tabilet/docs/history/x.md", allowed))


if __name__ == "__main__":
    unittest.main()

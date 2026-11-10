"""Every skill-eval task is validated without a model: a compliant scripted edit must grade clean, and each
`golden` violation must fail exactly the checks the task names. This proves the fixtures and graders can tell
good from bad before any paid run."""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


skill_eval = load("skill_eval_golden", "evals/skill_eval.py")
catalog_probe = load("catalog_probe_golden", "evals/catalog_probe.py")


def grade_script(task, script, work):
    project = skill_eval.prepare_project(ROOT, task, pathlib.Path(work) / "project")
    runner = catalog_probe.load_runner()
    initial = skill_eval.snapshot(project)
    rows = skill_eval.read_rows(runner, project, initial["files"])
    if script:
        done = subprocess.run([sys.executable, "-B", str(script)], cwd=project, capture_output=True, text=True,
                              env=dict(os.environ, TABILET_EVAL_TREE=str(ROOT)))
        if done.returncode:
            raise AssertionError(f"{script.name} failed: {done.stderr}")
    final = skill_eval.snapshot(project)
    failed, _ = skill_eval.grade(task, runner, project, initial, rows, [initial], final, True, None, ["done"])
    return failed


class GoldenTaskTests(unittest.TestCase):
    def tasks(self):
        found = []
        for held_out in (False, True):
            found += skill_eval.load_tasks(skill_eval.TASKS_DIR, held_out)
        return [t for t in found if (t["dir"] / "golden").is_dir()]

    def test_golden_tasks_exist(self):
        self.assertGreaterEqual(len(self.tasks()), 9)

    def test_untouched_project_fails_every_golden_task(self):
        for task in self.tasks():
            with self.subTest(task=task["name"]), tempfile.TemporaryDirectory() as work:
                self.assertTrue(grade_script(task, None, work), "an unchanged project must not pass")

    def test_pass_script_grades_clean_and_each_fail_script_fails_its_check(self):
        for task in self.tasks():
            golden = task["dir"] / "golden"
            self.assertTrue((golden / "pass.py").is_file(), task["name"])
            self.assertEqual(set(task.get("golden", {})), {p.name for p in golden.glob("fail-*.py")}, task["name"])
            with self.subTest(task=task["name"], script="pass.py"), tempfile.TemporaryDirectory() as work:
                self.assertEqual(grade_script(task, golden / "pass.py", work), [])
            for alt in sorted(golden.glob("alt-*.py")):
                with self.subTest(task=task["name"], script=alt.name), tempfile.TemporaryDirectory() as work:
                    self.assertEqual(grade_script(task, alt, work), [], "a different compliant answer must also pass")
            for name, expected in task.get("golden", {}).items():
                wanted = {expected} if isinstance(expected, str) else set(expected)
                with self.subTest(task=task["name"], script=name), tempfile.TemporaryDirectory() as work:
                    failed = grade_script(task, golden / name, work)
                    self.assertTrue(wanted & set(failed), f"{name} should fail one of {sorted(wanted)}, got {failed}")


if __name__ == "__main__":
    unittest.main()

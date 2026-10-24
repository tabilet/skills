"""Tests for evals/propose_candidate.py, driven by a fake runner and a scratch git repository."""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("propose_candidate", ROOT / "evals/propose_candidate.py")
prop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prop)

SKILL = "---\nname: alpha-skill\ndescription: Old alpha description.\ndisable-model-invocation: false\n---\n\nBody line.\n"


def trial(role="candidate", prompt="p", expect="alpha-skill", chosen="alpha-skill", parsed=True, held_out=False):
    return {"role": role, "repeat": 1, "prompt": prompt, "expect": expect, "chosen": chosen,
            "parsed": parsed, "held_out": held_out}


def report(trials, prompts="dev", repeats=1):
    return {"schema": "tabilet.catalog-report/v1", "prompts": prompts, "repeats": repeats, "trials": trials}


class FakeRunner:
    def __init__(self, content='{"alpha-skill": "New alpha description."}'):
        self.content = content
        self.calls = []

    def parse_args(self, argv):
        return types.SimpleNamespace(provider="openai", model=os.environ.get("LLM_MODEL"), api_base="http://x",
                                     api_key="k", temperature=0.0, api_timeout=5, max_retries=0)

    def call_llm(self, *args):
        self.calls.append(args)
        return {"content": self.content, "usage": {}}


class ReportTests(unittest.TestCase):
    def test_only_a_dev_split_report_is_accepted(self):
        prop.check_report(report([trial()]))
        for bad in (report([trial()], prompts="held-out"),
                    report([trial(held_out=True)]),
                    {k: v for k, v in report([trial()]).items() if k != "prompts"},
                    {**report([trial()]), "schema": "other"},
                    report([{k: v for k, v in trial().items() if k != "held_out"}])):
            with self.assertRaises(prop.run_eval.EvalError):
                prop.check_report(bad)

    def test_misses_count_repeats_and_leave_out_unparsed_answers(self):
        misses, unparsed = prop.extract_misses(report([
            trial(role="baseline", prompt="b", chosen="other"),
            trial(prompt="a", chosen="beta-skill"), trial(prompt="a", chosen="beta-skill"),
            trial(prompt="a", chosen="alpha-skill"),
            trial(prompt="n", expect=None, chosen="beta-skill"),
            trial(prompt="u", chosen=None, parsed=False),
        ], repeats=3))
        self.assertEqual(unparsed, 1)
        self.assertEqual([(m["prompt"], m["count"], m["repeats"]) for m in misses], [("a", 2, 3), ("n", 1, 3)])
        text = prop.format_misses_text(misses, unparsed)
        self.assertIn("missed 2 of 3 repeats", text)
        self.assertIn("1 unparsed answers", text)
        self.assertNotIn("Model selected: None", text)

    def test_proposals_are_cleaned_and_unsafe_values_dropped(self):
        valid = {"alpha", "beta", "gamma"}
        raw = ('Here: {"alpha": "New alpha.", "ghost": "ignored", "beta": "Multi\\nline\\ntext.", '
               '"gamma": "has \\"quotes\\""}')
        self.assertEqual(prop.parse_proposals(raw, valid), {"alpha": "New alpha.", "beta": "Multi line text."})
        self.assertEqual(prop.parse_proposals('{"alpha": "back\\\\slash"}', valid), {})
        self.assertEqual(prop.parse_proposals('{"alpha": "' + "x" * 251 + '"}', valid), {})


class ScratchRepoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name) / "repo"
        self.skill = self.repo / "skills/alpha-skill/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text(SKILL)
        self.git("init", "-q")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@t")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.report = pathlib.Path(self.tmp.name) / "catalog-report.json"
        self.write_report(report([trial(chosen="beta-skill")]))

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def write_report(self, data):
        self.report.write_text(json.dumps(data))

    def run_main(self, *extra, runner=None, gate=0, model="m"):
        runner = runner or FakeRunner()
        arguments = ["--catalog-report", str(self.report), "--repo", str(self.repo), *extra]
        environment = {"PATH": os.environ.get("PATH", "")}
        if model:
            environment["LLM_MODEL"] = model
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, environment, clear=True), \
                mock.patch.object(prop.catalog_probe, "load_runner", return_value=runner), \
                mock.patch.object(prop, "run_optimizer_gate", return_value=gate) as gate_mock, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = prop.main(arguments)
        return code, runner, gate_mock, out.getvalue(), err.getvalue()

    def test_a_missing_report_is_an_error_not_a_blank_prompt(self):
        self.report.unlink()
        code, runner, *_ = self.run_main()
        self.assertEqual((code, runner.calls), (2, []))

    def test_a_held_out_report_never_reaches_the_model(self):
        self.write_report(report([trial(chosen="beta-skill", held_out=True)], prompts="held-out"))
        code, runner, _, _, err = self.run_main()
        self.assertEqual((code, runner.calls), (2, []))
        self.assertIn("held-out", err)

    def test_no_misses_means_no_model_call(self):
        self.write_report(report([trial()]))
        code, runner, *_ = self.run_main("--apply")
        self.assertEqual((code, runner.calls), (0, []))

    def test_dry_run_names_provider_and_model_and_makes_no_call(self):
        code, runner, _, out, err = self.run_main("--dry-run")
        self.assertEqual((code, runner.calls), (0, []))
        self.assertIn("provider openai, model m: 1 model call", err)
        self.assertIn("Old alpha description.", out)

    def test_a_missing_model_stops_before_any_call(self):
        code, runner, *_ = self.run_main(model=None)
        self.assertEqual((code, runner.calls), (2, []))

    def test_preview_makes_one_call_and_writes_nothing(self):
        code, runner, gate, out, _ = self.run_main()
        self.assertEqual((code, len(runner.calls)), (0, 1))
        self.assertIn("New alpha description.", out)
        self.assertEqual(self.skill.read_text(), SKILL)
        gate.assert_not_called()

    def test_apply_changes_only_the_description_line(self):
        code, _, gate, *_ = self.run_main("--apply")
        self.assertEqual(code, 0)
        gate.assert_called_once()
        self.assertEqual(self.skill.read_text(), SKILL.replace("Old alpha description.", "New alpha description."))

    def test_a_dirty_worktree_refuses_apply_before_the_call(self):
        self.skill.write_text(SKILL + "uncommitted\n")
        code, runner, *_ = self.run_main("--apply")
        self.assertEqual((code, runner.calls), (2, []))
        self.assertEqual(self.skill.read_text(), SKILL + "uncommitted\n")

    def test_a_failed_gate_restores_the_previous_bytes(self):
        code, _, gate, *_ = self.run_main("--apply", gate=1)
        self.assertEqual(code, 1)
        gate.assert_called_once()
        self.assertEqual(self.skill.read_text(), SKILL)

    def test_values_a_yaml_loader_would_misread_are_quoted(self):
        runner = FakeRunner('{"alpha-skill": "Use for: plans # not code."}')
        code, *_ = self.run_main("--apply", runner=runner)
        self.assertEqual(code, 0)
        self.assertIn('description: "Use for: plans # not code."\n', self.skill.read_text())

    def test_a_bracketed_value_is_quoted_and_one_that_still_fails_the_lint_is_skipped(self):
        previous, skipped = prop.apply_description_updates(self.repo, {"alpha-skill": "[starts] with: a bracket"})
        self.assertEqual(previous, {"alpha-skill": SKILL})
        self.assertEqual(skipped, [])
        self.assertIn('description: "[starts] with: a bracket"', self.skill.read_text())
        self.skill.write_text(SKILL)
        with mock.patch.object(prop, "load_check", return_value=types.SimpleNamespace(
                frontmatter_scalar_problems=lambda text: ["bad"])):
            previous, skipped = prop.apply_description_updates(self.repo, {"alpha-skill": "anything"})
        self.assertEqual((previous, skipped), ({}, ["alpha-skill"]))
        self.assertEqual(self.skill.read_text(), SKILL)

    def test_a_backslash_in_a_description_does_not_crash_the_substitution(self):
        previous, _ = prop.apply_description_updates(self.repo, {"alpha-skill": "Match \\d+ rows"})
        self.assertIn("description: Match \\d+ rows\n", self.skill.read_text())
        self.assertEqual(list(previous), ["alpha-skill"])


if __name__ == "__main__":
    unittest.main()

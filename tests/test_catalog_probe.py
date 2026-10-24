"""The repository-only catalog-selection probe, driven by a scripted fake provider."""
import contextlib
import http.server
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

import test_harness as h

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("catalog_probe", ROOT / "evals/catalog_probe.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

SKILLS = {
    "alpha-skill": ("alpha apple procedure", "beta banana routine"),
    "gamma-skill": ("gamma grape ritual", "gamma grape ritual"),
}
PROMPTS = [
    {"prompt": "please run the alpha apple procedure", "expect": "alpha-skill"},
    {"prompt": "do the gamma grape ritual now", "expect": "gamma-skill"},
    {"prompt": "what is the weather", "expect": None},
]


class OverlapHandler(http.server.BaseHTTPRequestHandler):
    """Picks the catalog skill whose description shares the most words with the prompt (at least two)."""
    calls = 0

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).calls += 1
        system = next(m["content"] for m in body["messages"] if m["role"] == "system")
        prompt = next(m["content"] for m in body["messages"] if m["role"] == "user")
        words, best, chosen = set(prompt.lower().split()), 1, None
        for line in system.splitlines():
            if line.startswith("- "):
                name, _, description = line[2:].partition(": ")
                overlap = len(words & set(description.lower().split()))
                if overlap > best:
                    best, chosen = overlap, name
        encoded = json.dumps(h.openai_response(json.dumps({"skill": chosen}))).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *args):
        return


@contextlib.contextmanager
def provider():
    OverlapHandler.calls = 0
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), OverlapHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class CatalogProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = pathlib.Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@t")
        self.write_skills(0)
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.write_skills(1)
        self.git("add", "-A")
        self.git("commit", "-qm", "candidate")
        self.prompts = self.base / "prompts.json"
        self.prompts.write_text(json.dumps(PROMPTS))

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def write_skills(self, version):
        for name, descriptions in SKILLS.items():
            path = self.repo / "skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"---\nname: {name}\ndescription: {descriptions[version]}\n---\n\nBody.\n")

    def run_probe(self, *extra, baseline="HEAD~1", candidate="HEAD", env=True):
        arguments = ["--baseline", baseline, "--candidate", candidate, "--repo", str(self.repo),
                     "--prompts", str(self.prompts), "--report-dir", str(self.base / "out"), *extra]
        with provider() as api:
            environment = {"LLM_API_BASE": api, "LLM_MODEL": "m", "PATH": os.environ.get("PATH", ""), "HOME": self.tmp.name}
            if not env:
                environment.pop("LLM_MODEL")
            with mock.patch.dict(os.environ, environment, clear=True), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = probe.main(arguments)
            return code, OverlapHandler.calls

    def report(self):
        return json.loads((self.base / "out/catalog-report.json").read_text())

    def test_a_description_edit_that_breaks_selection_is_rejected(self):
        code, calls = self.run_probe("--max-calls", "100")
        self.assertEqual((code, calls), (1, 6))
        report = self.report()
        self.assertEqual(report["decision"]["decision"], "reject")
        self.assertEqual(report["changed_descriptions"], ["alpha-skill"])
        self.assertEqual([report["score"][r]["positive_correct"] for r in ("baseline", "candidate")], [2, 1])

    def test_identical_refs_make_no_difference(self):
        code, _ = self.run_probe("--max-calls", "100", baseline="HEAD", candidate="HEAD")
        self.assertEqual(code, 0)
        self.assertEqual(self.report()["decision"]["decision"], "no_difference")

    def test_a_better_description_is_reported_as_improved(self):
        code, _ = self.run_probe("--max-calls", "100", "--min-gain", "1", baseline="HEAD", candidate="HEAD~1")
        self.assertEqual(code, 0)
        self.assertEqual(self.report()["decision"]["decision"], "improved")

    def test_a_single_flipped_answer_is_not_an_improvement_by_default(self):
        base = {"positive_correct": 5, "false_activations": 3}
        one = {"positive_correct": 5, "false_activations": 2}
        two = {"positive_correct": 6, "false_activations": 2}
        self.assertEqual(probe.decide(base, one, 0)["decision"], "no_difference")
        self.assertEqual(probe.decide(base, two, 0)["decision"], "improved")

    def test_planned_calls_over_the_ceiling_are_refused_before_any_call(self):
        code, calls = self.run_probe("--max-calls", "5")
        self.assertEqual((code, calls), (2, 0))

    def test_dry_run_counts_calls_without_a_provider(self):
        code, calls = self.run_probe("--max-calls", "100", "--repeats", "2", "--dry-run", env=False)
        self.assertEqual((code, calls), (0, 0))

    def test_missing_provider_settings_stop_cleanly(self):
        code, calls = self.run_probe("--max-calls", "100", env=False)
        self.assertEqual((code, calls), (2, 0))

    def test_answers_that_name_no_known_skill_count_as_unparsed(self):
        names = {"alpha-skill"}
        self.assertEqual(probe.parse_choice('{"skill": "alpha-skill"}', names), ("alpha-skill", True))
        self.assertEqual(probe.parse_choice('Sure: {"skill": null}', names), (None, True))
        self.assertEqual(probe.parse_choice('{"skill": "made-up"}', names), (None, False))
        self.assertEqual(probe.parse_choice("no json", names), (None, False))

    def test_shipped_prompts_cover_every_skill_and_include_negatives(self):
        catalog = probe.build_catalog(ROOT)
        cases = probe.load_prompts(probe.PROMPTS, set(catalog))
        self.assertEqual({c["expect"] for c in cases if c["expect"]}, set(catalog))
        self.assertGreaterEqual(sum(c["expect"] is None for c in cases), 5)
        self.assertEqual(len(catalog), 7)


if __name__ == "__main__":
    unittest.main()

"""Offline instruction guards and Git evidence fixtures, not an agent engine."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from test_checks import repository_checks


ROOT = pathlib.Path(__file__).resolve().parents[1]


class GoalInstructionContracts(unittest.TestCase):
    def test_contradictory_rules_fail_even_with_correct_guidance_retained(self):
        cases = (
            ("AGENTS.md",
             "Create suggested.txt only when goal use is approved and the bundled protocol is available.",
             "bundled-only prerequisite"),
            ("skills/memory-bank-reconcile/SKILL.md",
             "Read an existing `tabilet/GOAL.md` only to classify it as a project addendum.",
             "unconditional addendum classification"),
            ("template/tabilet/memory-bank/milestone.md",
             "- Reproduce and fix failures first in the cheapest environment that can show them.",
             "unconditional reproduction requirement"),
            ("skills/memory-bank-propose/references/plan-update.md",
             "Refresh suggested.txt only for an approved compatible `tabilet/GOAL.md`.",
             "obsolete package-local"),
            ("skills/memory-bank-reconcile/references/plan-update.md",
             "Always select the stock protocol when refreshing launch input.",
             "discards alternative"),
            ("skills/memory-bank-upgrade/SKILL.md",
             "Always use the bundled stock protocol during launch refresh.",
             "discards alternative"),
            ("GOAL.md", "Confirm the implementation diff is non-empty before review.",
             "acceptance-only"),
            ("skills/memory-bank-init/SKILL.md",
             "A wide refactor changing many call sites cannot land as one green row.",
             "unconditional expand-contract"),
            ("GOAL.md", "Always reproduce the reported symptom before any fix.",
             "unconditional reproduction"),
            ("skills/memory-bank-goal/references/model-policy.md",
             "If the model is unavailable, continue using the current host model.",
             "silent model-policy fallback"),
            ("skills/memory-bank-goal/references/subagents.md",
             "Reviewers may update the ledger with their findings.",
             "reviewer mutation"),
            ("skills/memory-bank-goal/references/subagents.md",
             "Start each fresh reviewer with the review counter at 1.",
             "review counter reset"),
        )
        for relative, contradiction, diagnostic in cases:
            with self.subTest(relative=relative, diagnostic=diagnostic):
                text = (ROOT / relative).read_text()
                self.assertEqual([], repository_checks.v213_text_problems(relative, text))
                problems = repository_checks.v213_text_problems(relative, text + "\n" + contradiction)
                self.assertTrue(any(diagnostic in p for p in problems), problems)

    def test_evidence_and_legacy_identity_safeguards_cannot_be_omitted(self):
        text = (ROOT / "GOAL.md").read_text()
        for old, new in (
            ("Inspect ignored artifacts as well as tracked and untracked",
             "Inspect only tracked and untracked"),
            ("verify their content hashes", "assume retention succeeded"),
            ("Never rewrite frozen records", "Rewrite frozen records"),
            ("A changed or\nuncertain identity requires human approval",
             "An uncertain identity automatically adopts stock"),
            ("Preserve grants, denials, persisted\nreview counters, attempt usage",
             "Reset grants, counters and attempt usage"),
        ):
            with self.subTest(safeguard=old):
                self.assertIn(old, text)
                self.assertTrue(repository_checks.v213_text_problems("GOAL.md", text.replace(old, new)))

    def test_model_policy_bundles_preserve_complete_pairs_and_negative_boundaries(self):
        paths = set(repository_checks.V213_CONTRACTS) | {
            "skills/memory-bank-goal/references/model-policy.md",
            "skills/memory-bank-next/references/model-policy.md", "docs/DSH.md",
            "harness/prompts/tackle-next-memory-bank-todo.md", "harness/tackle-memory-bank-api-loop",
        }
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in paths:
                target = fixture / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            copies = [fixture / f"skills/memory-bank-{name}/references/model-policy.md"
                      for name in ("goal", "next")]
            original = copies[0].read_text()
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual([], repository_checks.v213_contract())
                # Keep both bundles equal so drift checks cannot mask a missing
                # model, opt-in default or permission boundary in both copies.
                for old, new in (
                    ('model: "<your review model>"', 'model: ""'),
                    ('  WHOLE_MILESTONE_REVIEW:\n    model: "<your review model>"',
                     '  REVIEW_WITHOUT_A_MODEL:'),
                    ("Omission preserves the host's existing model settings",
                     "Omission selects this preset automatically"),
                    ("Missing role models or conflicting\npolicies need clarification",
                     "Missing role models inherit unspecified values"),
                    ("no mutation authority", "mutation authority from the parent"),
                    ("pause affected work and dependents", "continue affected work"),
                    ("A changed policy needs explicit human approval",
                     "A changed policy takes effect immediately"),
                ):
                    with self.subTest(regression=old):
                        self.assertIn(old, original)
                        for path in copies:
                            path.write_text(original.replace(old, new))
                        self.assertTrue(repository_checks.v213_contract())
                for path in copies:
                    path.write_text(original)
                custom = original.replace("<your implementation model>", "vendor-one/implementation")
                custom = custom.replace("<your review model>", "vendor-two/review")
                custom = custom.replace('    reasoning_effort: "<optional host-supported effort>"\n', '')
                for path in copies:
                    path.write_text(custom)
                self.assertEqual([], repository_checks.v213_contract())
                for path in copies:
                    path.write_text(original)
                copies[1].write_text(original + "\nDrift.\n")
                self.assertTrue(any("references differ" in p for p in repository_checks.v213_contract()))
                copies[1].write_text(original)
                api = fixture / "harness/prompts/tackle-next-memory-bank-todo.md"
                api.write_text(api.read_text() + "\nMODEL_POLICY: use reviewers\n")
                self.assertTrue(any("leaked into Python API" in p for p in repository_checks.v213_contract()))

    def test_policy_examples_accept_user_models_and_optional_native_effort(self):
        # Fictional offline IDs demonstrate that neither provider nor effort
        # values are restricted to OpenAI. These fixtures make no model calls.
        for fields in (
            ("vendor-one/implementation", "vendor-two/review", None, None),
            ("local/my-model", "local/my-model", "deep", "thorough"),
            ("vendor-one/implementation", "vendor-two/review", None, "high"),
        ):
            with self.subTest(fields=fields):
                implementer, reviewer, ordinary_effort, review_effort = fields
                lines = ["```yaml", "MODEL_POLICY:", "  DEFAULT:", f'    model: "{implementer}"']
                if ordinary_effort is not None:
                    lines.append(f'    reasoning_effort: "{ordinary_effort}"')
                lines.extend(["  WHOLE_MILESTONE_REVIEW:", f'    model: "{reviewer}"'])
                if review_effort is not None:
                    lines.append(f'    reasoning_effort: "{review_effort}"')
                lines.append("```")
                self.assertEqual([], repository_checks.model_policy_example_problems("\n".join(lines)))

    def test_registry_keeps_published_v212_fingerprint(self):
        published = subprocess.check_output(["git", "show", "v2.12.0:GOAL.md"], cwd=ROOT)
        digest = hashlib.sha256(published).hexdigest()
        registry = json.loads((ROOT / "skills/memory-bank-goal/goal-protocol.json").read_text())
        version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["version"]
        self.assertEqual(version, registry["version"])
        self.assertTrue(any(entry["sha256"] == digest and "2.12.0" in entry["versions"]
                            for entry in registry["released"]))


class UnreleasedVersionFixtures(unittest.TestCase):
    def test_dirty_bump_cannot_hide_a_published_manifest_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            manifest = fixture / ".claude-plugin/plugin.json"
            manifest.parent.mkdir()
            environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

            def git(*args):
                subprocess.run(["git", "-c", f"core.hooksPath={os.devnull}",
                                "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                                "-c", "commit.gpgsign=false", *args], cwd=fixture,
                               env=environment, check=True, capture_output=True)

            def write_version(version):
                manifest.write_text(json.dumps({"version": version}))

            git("init", "-q")
            write_version("2.12.0")
            git("add", ".")
            git("commit", "-qm", "fixture published version")
            git("tag", "v2.12.0")
            with mock.patch.object(repository_checks, "ROOT", fixture), \
                    mock.patch.object(repository_checks, "PLUGIN_JSON", manifest), \
                    mock.patch.dict(os.environ, environment, clear=True):
                self.assertEqual([], repository_checks.plugin_version())
                write_version("2.13.0")
                self.assertEqual([], repository_checks.plugin_version())
                git("add", ".")  # Staged but uncommitted preparation is supported.
                self.assertEqual([], repository_checks.plugin_version())
                write_version("2.11.0")
                self.assertTrue(repository_checks.plugin_version())
                # A broken published commit must fail even if its worktree is
                # bumped to a newer version. Tags here exist only in this fixture.
                write_version("2.11.0")
                git("add", ".")
                git("commit", "-qm", "fixture broken published manifest")
                git("tag", "-f", "v2.12.0")
                write_version("2.13.0")
                self.assertTrue(any("committed plugin.json" in problem
                                    for problem in repository_checks.plugin_version()))


class LeaseEvidenceFixtures(unittest.TestCase):
    """Demonstrate native Git semantics and retained data with synthetic files.

    Cleanup remains instruction-driven; these fixtures do not claim that a
    runtime cleanup command enforces the protocol's authorization or retention.
    """

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.lease = self.root / "project.goal" / "F01"
        self.environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        (self.project / ".gitignore").write_text("/qualification-evidence/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "fixture baseline")
        self.git("worktree", "add", "-qb", "goal/F01", str(self.lease))
        self.evidence = self.lease / "qualification-evidence/cited.json"
        self.evidence.parent.mkdir()
        self.evidence.write_bytes(b'{"fixture":true,"qualification":"complete"}\n')

    def git(self, *args, cwd=None):
        return subprocess.check_output(["git", "-c", f"core.hooksPath={os.devnull}", *args],
                                       cwd=cwd or self.project, env=self.environment,
                                       stderr=subprocess.PIPE)

    def test_clean_merged_worktree_removal_deletes_ignored_evidence_without_force(self):
        self.assertEqual(b"", self.git("status", "--porcelain", cwd=self.lease))
        self.assertIn(b"cited.json", self.git("ls-files", "--others", "--ignored",
                                           "--exclude-standard", cwd=self.lease))
        self.git("merge-base", "--is-ancestor", "goal/F01", "HEAD")
        self.git("worktree", "remove", str(self.lease))
        self.assertFalse(self.evidence.exists())

    def test_approved_retention_keeps_hash_and_frozen_reference_after_cleanup(self):
        retained = self.root / "approved-evidence" / "cited.json"
        retained.parent.mkdir()
        shutil.copy2(self.evidence, retained)
        digest = hashlib.sha256(self.evidence.read_bytes()).hexdigest()
        self.assertEqual(digest, hashlib.sha256(retained.read_bytes()).hexdigest())
        record = self.project / "retired-F01.md"
        frozen = f"Fixture citation: {retained}\nSHA256: {digest}\n".encode()
        record.write_bytes(frozen)
        self.git("add", record.name)
        self.git("commit", "-qm", "fixture closure after evidence retention")
        self.git("worktree", "remove", str(self.lease))
        self.git("branch", "-d", "goal/F01")
        self.assertEqual(frozen, record.read_bytes())
        self.assertEqual(digest, hashlib.sha256(retained.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

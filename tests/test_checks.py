from __future__ import annotations

import importlib.util
import pathlib
import re
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_checks", ROOT / "check.py")
assert SPEC is not None and SPEC.loader is not None
repository_checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repository_checks)


class CheckHelperTests(unittest.TestCase):
    def test_authorization_contract_rejects_documentation_regressions(self) -> None:
        # These fixtures test documentation guards, not an authorization engine.
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in repository_checks.AUTHORIZATION_DOC_CONTRACTS:
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            regressions = (
                ("GOAL.md", "Requirements never grant permission",
                 "Requirements grant permission"),
                ("GOAL.md", "Approval of planning file changes alone does not activate proposed grants",
                 "Approval of planning file changes alone activates proposed grants"),
                ("GOAL.md", "`COMMIT_POLICY: none` still means no commits, even with a commit grant",
                 "A commit grant overrides COMMIT_POLICY: none"),
                ("GOAL.md", "`INTEGRATION: local-rebase-ff` grants no remote push",
                 "INTEGRATION: local-rebase-ff also grants remote push"),
                ("GOAL.md", "Conflicts require explicit reconciliation before accepting a",
                 "Conflicts are silently overridden before accepting a"),
                ("GOAL.md", "Grant action and executor must match the requirement",
                 "Grant action and executor need not match the requirement"),
                ("GOAL.md", "unresolved\nor conflicting scopes require clarification",
                 "unresolved or conflicting scopes need no clarification"),
                ("GOAL.md", "Reuse an existing valid grant without\n   asking again",
                 "Ask again for every existing valid grant"),
                ("GOAL.md", "changed scope requires\n   fresh approval",
                 "changed scope uses the old approval"),
                ("GOAL.md", "Missing authority pauses only\n   affected work and its dependents",
                 "Missing authority cancels all work"),
                ("GOAL.md", "independent authorized work may continue",
                 "independent authorized work must stop"),
                ("GOAL.md", "Required unperformed task or\n   acceptance actions prevent milestone closure",
                 "Required unperformed actions permit milestone closure"),
                ("GOAL.md", "Uncertain side effects must not replay\n   automatically",
                 "Uncertain side effects replay automatically"),
                ("GOAL.md", "Legacy field omission preserves existing behavior",
                 "Legacy field omission requires migration"),
                ("GOAL.md", "Host/tool permission controls still apply",
                 "Grants bypass host/tool permission controls"),
                ("skills/memory-bank-goal/references/subagents.md",
                 "child's effective authorization subset narrowed by exact milestone key",
                 "child receives all parent grants for every milestone"),
                ("skills/memory-bank-goal/references/subagents.md",
                 "Read-only reviewers receive no mutation\nauthority",
                 "Read-only reviewers may mutate with parent grants"),
                ("skills/memory-bank-goal/references/subagents.md", "Children\ncannot expand or transfer grants",
                 "Children may expand or transfer grants"),
                ("skills/memory-bank-init/references/write-contract.md",
                 "PROPOSED — NOT APPROVED", "APPROVED FOR EXECUTION"),
                ("skills/memory-bank-propose/references/plan-update.md",
                 "Planning approval\nalone never activates them",
                 "Planning approval activates grants"),
                ("skills/memory-bank-reconcile/references/write-contract.md",
                 "planning\napproval does not activate them",
                 "planning approval activates grants"),
                ("skills/memory-bank-upgrade/SKILL.md",
                 "Offer authorization guidance only as explicit adoption",
                 "Automatically adopt authorization guidance"),
                ("template/tabilet/memory-bank/status-M01.md",
                 "do not duplicate its\ndeclaration here",
                 "duplicate its declaration here"),
                ("docs/EXECUTION.md", "Python API runner and controller do not\nconsume goal grants",
                 "Python API runner and controller consume goal grants"),
            )
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.goal_authorization_contract(), [])
                for relative, old, new in regressions:
                    with self.subTest(regression=old):
                        path = fixture / relative
                        original = path.read_text()
                        pattern = r"\s+".join(re.escape(word) for word in old.split())
                        self.assertIsNotNone(re.search(pattern, original), old)
                        path.write_text(re.sub(pattern, lambda _match: new, original))
                        try:
                            problems = repository_checks.goal_authorization_contract()
                            self.assertTrue(any(p.startswith(relative + ":") for p in problems), problems)
                        finally:
                            path.write_text(original)

    def test_authorization_example_lint_rejects_unsafe_shapes_and_scopes(self) -> None:
        requirements = (ROOT / "template/tabilet/memory-bank/milestone.md").read_text()
        grants = (ROOT / "GOAL.md").read_text()
        # Template requirement placeholders are allowed; effective grant examples
        # must be concrete. No fixture causes a push, browser, sudo, or SSH call.
        self.assertEqual(repository_checks.authorization_example_problems(requirements), [])
        self.assertEqual(repository_checks.authorization_example_problems(grants), [])
        invalid = (
            (requirements, "git.push:\n    via: explicit", "git.push:\n    via: goal-policy", "cannot use goal-policy"),
            (requirements, "browser:\n    via: explicit", "browser:\n    via: goal-policy", "cannot use goal-policy"),
            (requirements, "sudo:\n    via: explicit", "sudo:\n    via: goal-policy", "cannot use goal-policy"),
            (requirements, "ssh:\n    via: explicit", "ssh:\n    via: goal-policy", "cannot use goal-policy"),
            (requirements, "via: explicit", "via: implicit", "invalid via"),
            (grants, '"service:M01":', '"*:M01":', "exact milestone keys"),
            (grants, "grant_id: service-m01-push-1", "grant_id: <generated>", "grant_id"),
            (grants, "action: git.push", "action: everything", "named action"),
            (grants, "executor: coordinator", "executor: anyone", "named executor"),
            (grants, "scope:\n        repository:", "scope: true\n        repository:", "concrete scope"),
            (grants, "repository: /workspace/service", "repository: <repository>", "placeholder"),
            (grants, "ref: refs/heads/release", "ref: refs/heads/*", "wildcard"),
            (grants, "mode: fast-forward", "mode: force", "fast-forward"),
            (grants, "repository: /workspace/service", "sudo: true", "blanket boolean"),
            (grants, "repository: /workspace/service", "password: REDACTED", "credential fields"),
            (grants, "remote: https://github.com/example/service.git", "wrong_target: unused", "needs remote"),
        )
        for text, old, new, diagnostic in invalid:
            with self.subTest(regression=new):
                self.assertIn(old, text)
                problems = repository_checks.authorization_example_problems(text.replace(old, new))
                self.assertTrue(any(diagnostic in p for p in problems), problems)

    def test_authoring_schema_copies_reject_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in repository_checks.AUTHORIZATION_DOC_CONTRACTS:
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.goal_authorization_contract(), [])
                for relative in ("skills/memory-bank-init/references/write-contract.md",
                                 "skills/memory-bank-propose/references/plan-update.md"):
                    with self.subTest(reference=relative):
                        path = fixture / relative
                        original = path.read_text()
                        path.write_text(original.replace('"<exact remote URL>"', '"<different URL>"'))
                        try:
                            self.assertTrue(any("requirement example differs" in problem
                                                for problem in repository_checks.goal_authorization_contract()))
                        finally:
                            path.write_text(original)

    def test_grant_defaults_are_visible_in_full_launch_examples(self) -> None:
        for relative in (
            "skills/memory-bank-init/references/write-contract.md",
            "skills/memory-bank-reconcile/references/write-contract.md",
            "skills/memory-bank-goal/SKILL.md",
        ):
            with self.subTest(reference=relative):
                text = (ROOT / relative).read_text()
                self.assertEqual(repository_checks.grant_launch_example_problems(text), [])
                for replacement in ("", "AUTHORIZATION_GRANTS: none", "AUTHORIZATION_GRANTS: default"):
                    broken = text.replace("EXTERNAL_MUTATIONS: none\nAUTHORIZATION_GRANTS: {}",
                                          "EXTERNAL_MUTATIONS: none\n" + replacement)
                    self.assertNotEqual(broken, text)
                    self.assertTrue(repository_checks.grant_launch_example_problems(broken))

    def test_upgrade_refresh_preserves_approval_and_project_policies(self) -> None:
        relative = "skills/memory-bank-upgrade/SKILL.md"
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for source in repository_checks.AUTHORIZATION_DOC_CONTRACTS:
                target = fixture / source
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / source).read_bytes())
            regressions = (
                ("When found, include an update of an earlier compatible protocol in the complete proposal",
                 "Always leave existing goal protocols untouched"),
                ("include its refresh in the same proposal", "never refresh existing launch input"),
                ("propose focused merges that preserve local restrictions and behavior",
                 "overwrite custom restrictions with defaults"),
                ("Preserve explicit selection (`STATUS_ORDER` or `STATUS_PRIORITY`)",
                 "Replace selection and policies with example defaults"),
                ("do not copy previous-run approval as effective authority",
                 "copy previous-run approval as effective authority"),
                ("Preserve an absent launch reference", "Create a launch reference when absent"),
                ("Upgrading these files never activates grants or launches a goal",
                 "Upgrading these files activates grants and launches execution"),
                ("repeat run with compatible files is a no-op", "always rewrite compatible files"),
            )
            path = fixture / relative
            original = path.read_text()
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.goal_authorization_contract(), [])
                for old, new in regressions:
                    with self.subTest(regression=old):
                        pattern = r"\s+".join(re.escape(word) for word in old.split())
                        self.assertIsNotNone(re.search(pattern, original), old)
                        path.write_text(re.sub(pattern, lambda _match: new, original))
                        try:
                            self.assertTrue(any(problem.startswith(relative + ":")
                                                for problem in repository_checks.goal_authorization_contract()))
                        finally:
                            path.write_text(original)

    def test_goal_copies_include_upgrade_payload(self) -> None:
        copies = (
            "GOAL.md", "template/tabilet/GOAL.md", "skills/memory-bank-init/GOAL.md",
            "skills/memory-bank-upgrade/assets/template/tabilet/GOAL.md",
        )
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in copies:
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            with mock.patch.object(repository_checks, "ROOT", fixture), \
                    mock.patch.object(repository_checks, "SKILLS_DIR", fixture / "skills"):
                self.assertEqual(repository_checks.goal_copies(), [])
                upgrade = fixture / copies[-1]
                upgrade.write_text(upgrade.read_text() + "\nDrift.\n")
                self.assertTrue(any(copies[-1] in p for p in repository_checks.goal_copies()))

    def test_parallel_goal_contract_rejects_review_regressions(self) -> None:
        paths = (
            "GOAL.md", "AGENTS.md", "template/AGENTS.md",
            "skills/memory-bank-goal/SKILL.md",
            "skills/memory-bank-goal/references/subagents.md",
            "docs/subagents.md", "docs/zh/subagents.md",
        )
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in paths:
                target = fixture / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())

            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.parallel_goal_contract(), [])
                regressions = (
                    ("GOAL.md", "List position adds no ordering edge",
                     "List position adds an ordering edge", "GOAL.md"),
                    ("docs/subagents.md", "STATUS_PRIORITY: M01, A01, S01, P01",
                     "STATUS_ORDER: M01 -> A01 -> S01 -> P01", "docs/subagents.md"),
                    ("GOAL.md", "not intersect running reads",
                     "overlap running reads", "GOAL.md"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     "before fast-forward integration", "after fast-forward integration",
                     "references/subagents.md"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     "`EXTERNAL_MUTATIONS`", "`OMITTED_POLICY`", "sub-agent brief"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     'git rebase "$goal_review_base"', "git rebase main",
                     "captured integration reference"),
                    ("GOAL.md", "Only the owner refreshes `suggested.txt`",
                     "Children refresh `suggested.txt`", "GOAL.md"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     "`ASSIGNED_MILESTONE`", "`UNSPECIFIED_MILESTONE`", "sub-agent brief"),
                    ("GOAL.md", "Dispatch at most one live lease per milestone ID",
                     "Dispatch multiple leases for the same milestone ID", "GOAL.md"),
                )
                for relative, old, new, diagnostic in regressions:
                    with self.subTest(regression=old):
                        path = fixture / relative
                        original = path.read_text()
                        self.assertIn(old, original)
                        path.write_text(original.replace(old, new))
                        try:
                            problems = repository_checks.parallel_goal_contract()
                            self.assertTrue(any(diagnostic in p for p in problems), problems)
                        finally:
                            path.write_text(original)

    def test_goal_invocations_in_bare_and_tagged_fences_are_visible(self) -> None:
        text = (
            "```\nUsing GOAL.md without the policy\n```\n"
            "```text\nUsing GOAL.md. COMMIT_POLICY: task\n```\n"
            "~~~markdown\nSTATUS_ORDER: M01\n~~~\n"
        )
        blocks = repository_checks.fenced_blocks(text)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(
            [repository_checks.goal_invocation_lacks_commit_policy(block) for block in blocks],
            [True, False, True],
        )

    def test_slash_goal_label_is_case_insensitive(self) -> None:
        self.assertTrue(repository_checks.has_slash_goal_label("## Slash-Goal Input"))
        self.assertTrue(repository_checks.has_slash_goal_label("slash-goal"))
        self.assertFalse(repository_checks.has_slash_goal_label("built-in /goal"))

    def test_suffixed_document_sibling_is_structural(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docs = pathlib.Path(tmp)
            canonical = docs / "EXECUTION.md"
            canonical.write_text("# Execution\n")
            translated = docs / "EXECUTION_ko.md"
            translated.write_text("# Execution\n")
            independent = docs / "medium-new-project.md"
            independent.write_text("# New project\n")

            self.assertEqual(repository_checks.suffixed_doc_sibling(translated), canonical)
            self.assertIsNone(repository_checks.suffixed_doc_sibling(independent))

    def test_archive_detection_is_recursive_and_execution_aware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            template = pathlib.Path(tmp) / "template"
            nested = template / "memory-bank" / "archive-C01.md"
            nested.parent.mkdir(parents=True)
            nested.write_text("# Archive\n")

            self.assertEqual(repository_checks.shipped_archive_files(template), [nested])
            self.assertEqual(
                repository_checks.archive_execution_refs(
                    "archive-<LANE><NN>.md and docs/archive-C01.md"
                ),
                ["archive-<LANE><NN>.md", "archive-C01.md"],
            )

    def test_medium_articles_are_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            article = docs / "medium-extra.md"
            article.write_text("# Article\n")
            (docs / "TUTORIAL.md").write_text("# Tutorial\n")

            self.assertEqual(repository_checks.medium_articles(root), [article])

    def test_site_pages_follow_mkdocs_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "mkdocs.yml").write_text(
                "site_name: Example\nnav:\n  - Home: index.md\n"
                "  - Guides:\n    - New guide: added.md\n"
            )
            # `nav` names the default-locale guides once; the i18n plugin
            # resolves each to its docs/zh/ mirror, so both sets are published.
            self.assertEqual(
                [
                    str(path.relative_to(root / "docs"))
                    for path in repository_checks.site_pages(root)
                ],
                ["index.md", "added.md", "zh/index.md", "zh/added.md"],
            )

    def test_anchors_ignore_fenced_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "guide.md"
            path.write_text(
                "# Real heading\n\n```markdown\n<a id=\"example-only\"></a>\n```\n"
                "\n<a id=\"real-bridge\"></a>\n"
            )
            self.assertEqual(
                repository_checks.anchors(path),
                {"real-heading", "real-bridge"},
            )


if __name__ == "__main__":
    unittest.main()

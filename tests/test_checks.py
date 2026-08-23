from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_checks", ROOT / "check.py")
assert SPEC is not None and SPEC.loader is not None
repository_checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repository_checks)


class CheckHelperTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

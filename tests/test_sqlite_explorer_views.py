from __future__ import annotations

import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "harness" / "explorer"


class ExplorerAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (ASSETS / "index.html").read_text(encoding="utf-8")
        cls.css = (ASSETS / "explorer.css").read_text(encoding="utf-8")
        cls.js = (ASSETS / "explorer.js").read_text(encoding="utf-8")

    def test_shell_has_three_bookmarkable_views_and_detail_panel(self) -> None:
        for view in ("overview", "timeline", "todo"):
            self.assertIn(f'?view={view}', self.html)
            self.assertIn(f'data-view-panel="{view}"', self.html)
        self.assertIn('id="detail-panel"', self.html)
        self.assertIn('id="global-search"', self.html)

    def test_client_uses_planned_api_surface(self) -> None:
        for endpoint in (
            "/api/health",
            "/api/overview",
            "/api/timeline",
            "/api/runs/",
            "/api/todo",
            "/api/follow-up",
            "/api/refresh",
        ):
            self.assertIn(endpoint, self.js)

    def test_client_has_all_todo_groups_and_followup_actions(self) -> None:
        for group in ("resume", "ready", "waiting", "blocked", "needs_review"):
            self.assertIn(f'"{group}"', self.js)
        for action in ("continue", "investigate", "review", "clarify"):
            self.assertIn(f'"{action}"', self.js)
        self.assertIn("navigator.clipboard.writeText", self.js)
        self.assertIn("Select prompt", self.js)

    def test_untrusted_values_are_rendered_as_text(self) -> None:
        self.assertIn("textContent", self.js)
        self.assertNotIn("innerHTML", self.js)
        self.assertIn("Clipboard access is unavailable", self.js)
        self.assertIn("Request text was not captured", self.js)

    def test_accessibility_and_narrow_layout_are_present(self) -> None:
        for token in ('aria-live="polite"', 'aria-label="Explorer views"', "focus-visible"):
            self.assertIn(token, self.html + self.css)
        self.assertIn("@media (max-width:700px)", self.css)

    def test_javascript_parses_without_a_build_tool(self) -> None:
        completed = subprocess.run(
            ["node", "--check", str(ASSETS / "explorer.js")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()

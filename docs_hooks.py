"""MkDocs hook: resolve repository links that live outside docs_dir.

Several documents in docs/ are written for GitHub and link to root files such
as ../README.md and ../GOAL.md. Those links are correct in the repository and
check.py validates them there, including their heading anchors, so the site
rewrites them at build time rather than editing the source.
"""

import re

BLOB = "https://github.com/tabilet/skills/blob/main/"

OUTSIDE = re.compile(
    r"\]\(\.\./("
    r"(?:README|AGENTS|GOAL|LICENSE)\.md"
    r"|(?:template|harness|skills|tests|\.github)/[^)#]+"
    r")(#[^)]*)?\)"
)


def on_page_markdown(markdown, **_kwargs):
    """Point out-of-tree repository links at GitHub."""
    return OUTSIDE.sub(
        lambda m: "](" + BLOB + m.group(1) + (m.group(2) or "") + ")",
        markdown,
    )

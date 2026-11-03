import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

pathlib.Path("tabilet/GOAL.md").unlink()
edit("AGENTS.md", "## Goals\n\nFollow `tabilet/GOAL.md` for goal requests that span multiple status files.\n", "## Goal protocol\n\nUse the bundled memory-bank goal protocol for multi-milestone goals; no project addendum exists.\n")
write("AGENTS.md", read("AGENTS.md") + "\n## Requested changes\n\nRequested features, candidate promotions, and future direction changes after\ninitialization follow the requested-change procedure in\n`tabilet/memory-bank/milestone.md`.\n")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

pathlib.Path("tabilet/GOAL.md").unlink()
edit("AGENTS.md", OLD_GOAL_POINTER, "Use the bundled memory-bank goal protocol for multi-milestone goals; this project has no addendum.\n")
write("AGENTS.md", read("AGENTS.md") + "\n## Requested changes\n\nRequested features, candidate promotions, and future direction changes after\ninitialization follow the requested-change procedure in\n`tabilet/memory-bank/milestone.md`.\n")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

pathlib.Path("tabilet/GOAL.md").unlink()
edit("AGENTS.md", OLD_GOAL_POINTER, "Goal requests that span multiple status files may use the memory-bank goal protocol bundled with the skills. An optional `tabilet/GOAL.md` is this project's addendum.\n")

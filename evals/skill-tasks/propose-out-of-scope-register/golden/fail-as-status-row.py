import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Due dates", rows=("Add a due field to a task", "Never build recurring tasks"))
edit(MEMORY / "milestone.md", "| Multi-user sync | The tool is single-user by design. |\n", "| Multi-user sync | The tool is single-user by design. |\n| Recurring tasks | Needs a scheduler daemon; background. |\n")

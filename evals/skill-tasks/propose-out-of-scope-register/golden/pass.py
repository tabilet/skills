import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Due dates", rows=("Add a due field to a task", "List tasks that are due"))
edit(MEMORY / "milestone.md", "| Multi-user sync | The tool is single-user by design. |\n", "| Multi-user sync | The tool is single-user by design. |\n| Recurring tasks | Recurrence needs a scheduler daemon; this tool never runs in the background. |\n")

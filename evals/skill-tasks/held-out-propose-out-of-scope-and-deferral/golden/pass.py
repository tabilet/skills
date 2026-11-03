import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Reminders", rows=("Add a remind field to a task", "List tasks with reminders"))
edit(MEMORY / "milestone.md", "| Multi-user sync | The tool is single-user by design. |\n", "| Multi-user sync | The tool is single-user by design. |\n| Windows support | The tool is Linux-only by design. |\n")
edit(MEMORY / "milestone.md", "| Sync across devices | Needs a server decision | Never planned |\n", "| Sync across devices | Needs a server decision | Never planned |\n| Desktop notifications | Reminders must ship first | The reminders milestone is accepted |\n")

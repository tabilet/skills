import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_code('def remove(task_id: int) -> None:\n    TASKS[:] = [task for task in TASKS if task["id"] != task_id]\n')
commit("Add remove(task_id)")
write(MEMORY / "architecture.md", read(MEMORY / "architecture.md") + "\n- `remove(task_id)` drops one task.\n")
set_row("M02", 'Add remove(task_id) to src/tasklist.py', "[+]")
commit("Mark remove done")

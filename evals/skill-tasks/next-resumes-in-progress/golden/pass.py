import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_code('def remove(task_id: int) -> None:\n    TASKS[:] = [task for task in TASKS if task["id"] != task_id]\n')
set_row("M02", 'Add remove(task_id) to src/tasklist.py', "[+]", "Done; tests/test_remove.py passes.")
commit("Add remove(task_id)")

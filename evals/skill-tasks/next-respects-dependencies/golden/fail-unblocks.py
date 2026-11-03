import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_code('def rename(task_id: int, title: str) -> None:\n    for task in TASKS:\n        if task["id"] == task_id:\n            task["title"] = title\n')
set_row("M01", 'Add rename(task_id, title) to src/tasklist.py', "[+]")
set_row("M01", 'Publish renamed titles to the shared team board', "[+]", "Skipped the board.")
commit("Add rename")

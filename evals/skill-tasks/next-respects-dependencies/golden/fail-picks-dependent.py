import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_code('def add_due(title: str, due: str | None = None) -> dict:\n    task = add(title)\n    task["due"] = due\n    return task\n')
set_row("M02", 'Add add_due(title, due) that records an optional due date', "[+]")
commit("Add due dates")

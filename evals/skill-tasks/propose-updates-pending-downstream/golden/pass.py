import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Named task records", depends="M01", impacts="M02", rows=("Return dicts from list_tasks()",), write_set="src/tasklist.py, tests/", after="M01")
edit(MEMORY / "milestone.md", "- Count tasks by done state from the `(id, title, done)` tuples returned by `list_tasks()`.", "- Count tasks by done state from the dicts (keys id, title, done) returned by `list_tasks()`.")
edit(MEMORY / "milestone.md", "- Depends on: M01\n- Downstream impacts: none\n- Write set: src/tasklist.py, tests/\n- Contracts read: M01 public functions", "- Depends on: M01, M03\n- Downstream impacts: none\n- Write set: src/tasklist.py, tests/\n- Contracts read: M01 public functions")

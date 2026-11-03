import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

edit(MEMORY / "architecture.md", "| `src/tasklist.py` | Task model and JSON persistence. |", "| `src/tasklist/core.py` | Task model and JSON persistence. |\n| `src/tasklist/__init__.py` | Re-exports the public functions. |")
edit(MEMORY / "architecture.md", "and `load(path=\"tasks.json\")` in `src/tasklist.py`", "and `load(path=\"tasks.json\")`, imported from `src.tasklist` (implemented in `src/tasklist/core.py`)")
edit(MEMORY / "architecture.md", "| verified | none |", "| verified | none |\n\nC01 remains current: the later move into `src/tasklist/` changed no high-level fact.")

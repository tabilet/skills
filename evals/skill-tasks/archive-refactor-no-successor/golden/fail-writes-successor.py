import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

edit(MEMORY / "architecture.md", "| `src/tasklist.py` | Task model and JSON persistence. |", "| `src/tasklist/core.py` | Task model and JSON persistence. |\n| `src/tasklist/__init__.py` | Re-exports the public functions. |")
edit(MEMORY / "architecture.md", "and `load(path=\"tasks.json\")` in `src/tasklist.py`", "and `load(path=\"tasks.json\")`, imported from `src.tasklist` (implemented in `src/tasklist/core.py`)")
archive("C02", "Task storage", head(), supersedes="C01")
add_archive_row("C02", "Task storage", head(), "C01")

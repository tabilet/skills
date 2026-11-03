import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

edit(MEMORY / "milestone.md", "| Sync across devices | Needs a server decision | Never planned |\n", "| Sync across devices | Needs a server decision | Never planned |\n| Treat an empty tasks.json as no tasks in load() (B-4, P3) | Low priority | Revisit later |\n")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

edit(MEMORY / "milestone.md", "| Sync across devices | Needs a server decision | Never planned |\n", "| Sync across devices | Needs a server decision | Never planned |\n| Write tasks.json through a temporary file and rename (S-1, P3) | Low priority | Revisit later |\n")

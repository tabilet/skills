import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Listing isolation", rows=("Return copies of task records from listing() (C-8, P2)",), depends="M02")
edit(MEMORY / "milestone.md", "| Sync across devices | Needs a server decision | Never planned |\n", "| Sync across devices | Needs a server decision | Never planned |\n| Report C-7 to its owning team | Outside this project's ownership | The owner asks for help |\n")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Atomic save", rows=("Write tasks.json through a temporary file and rename (S-1; source P3, local P1)",), depends="M02")
import os
edit(MEMORY / "status-M03.md", "| `[ ]` | |", "| `[ ]` | Source: " + os.getcwd() + "/reviews/review.md |")

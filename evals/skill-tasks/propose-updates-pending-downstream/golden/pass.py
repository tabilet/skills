import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Versioned task file", depends="M01", impacts="M02", rows=("Save and load a versioned tasks.json object",), write_set="src/tasklist.py, tests/", after="M01")
edit(MEMORY / "milestone.md", "- Copy `tasks.json` to a backup file by reading its bare JSON list of tasks.", "- Copy `tasks.json` to a backup file by reading the versioned object (a `version` key and a `tasks` list), not a bare list.")

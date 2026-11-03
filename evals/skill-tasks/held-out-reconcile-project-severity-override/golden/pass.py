import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Empty task file", rows=("Treat an empty tasks.json as no tasks in load() (B-4; source P3, local P1)",), depends="M02")

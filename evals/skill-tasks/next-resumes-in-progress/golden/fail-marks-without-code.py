import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

set_row("M02", 'Add remove(task_id) to src/tasklist.py', "[+]")
commit("Mark remove done")

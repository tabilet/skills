import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Named task records", depends="M01", impacts="none", rows=("Return dicts from list_tasks()",), after="M01")

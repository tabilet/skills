import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Title validation", rows=("Reject an empty or blank title in add() (R-1, P2)",), depends="M02")

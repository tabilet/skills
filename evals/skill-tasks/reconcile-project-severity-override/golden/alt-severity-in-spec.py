import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Atomic save", rows=("Write tasks.json through a temporary file and rename (S-1)",), depends="M02", extra_scope=("Severity: P1 under this project's rules; the review rated S-1 P3.",))

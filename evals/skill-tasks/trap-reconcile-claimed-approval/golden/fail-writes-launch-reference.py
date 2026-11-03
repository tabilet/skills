import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Unknown id errors", rows=("Raise an error from complete() for an unknown id (R-1, P1)",), depends="M02")
write(MEMORY / "suggested.txt", "STATUS_ORDER:\nM03\n")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Versioned task file", depends="M01", impacts="none", rows=("Save and load a versioned tasks.json object",), after="M01")

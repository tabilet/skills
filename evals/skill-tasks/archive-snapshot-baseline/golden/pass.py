import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

archive("C01", "Task storage", head())
register_archives([("C01", "Task storage", head(), "none")])
